import hashlib
import json
import re
from contextlib import contextmanager
from zipfile import ZIP_STORED, ZipFile

from fastapi.encoders import jsonable_encoder

from app.core.exceptions import AppError
from app.models import PromptRecord, PromptTemplate, Storyboard
from app.models.base import utc_now
from app.repositories.project_export import ProjectExportRepository


def safe_name(value):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]', "_", value).strip(" .")[:100]
    if not name or name.split(".")[0].upper() in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }:
        name = "project"
    return name


class ProjectExportService:
    def __init__(self, workspace):
        self.workspace = workspace

    @staticmethod
    def serialize(graph, repository):
        data = {
            table: [
                jsonable_encoder({c.name: getattr(row, c.name) for c in row.__table__.columns})
                for row in rows
            ]
            for table, rows in graph.items()
        }
        # Source identities are historical facts, not necessarily archive-local FKs.
        # Keep excluded source UUIDs without exporting any excluded entity content.
        identities = {table: {r["id"] for r in rows} for table, rows in data.items()}
        source_fields = {
            "prompt_records": [("template_id", "prompt_templates", PromptTemplate)],
            "storyboards": [("source_prompt_record_id", "prompt_records", PromptRecord)],
            "video_results": [
                ("source_prompt_record_id", "prompt_records", PromptRecord),
                ("source_storyboard_id", "storyboards", Storyboard),
            ],
        }
        for table, fields in source_fields.items():
            for row, entity in zip(data[table], graph[table], strict=True):
                row["source_references"] = {}
                for field, target, model in fields:
                    original = row[field]
                    if original is None:
                        continue
                    source = repository.source(model, getattr(entity, field))
                    if source is None:
                        raise AppError("EXPORT_BROKEN_REFERENCE", "导出来源记录缺失。", 409)
                    if model is not PromptTemplate and source.shot_id != entity.shot_id:
                        raise AppError("EXPORT_BROKEN_REFERENCE", "导出来源不属于同一镜头。", 409)
                    included = original in identities[target]
                    row["source_references"][field] = {
                        "original_id": original,
                        "entity_type": target,
                        "resolution": "included" if included else "external_identity",
                    }
                    row[field] = original if included else None
        # All remaining foreign keys must resolve within the archive.
        for table, rows in data.items():
            for row, entity in zip(rows, graph[table], strict=True):
                for column in entity.__table__.columns:
                    for foreign_key in column.foreign_keys:
                        target = foreign_key.column.table.name
                        if (
                            row[column.name] is not None
                            and row[column.name] not in identities[target]
                        ):
                            raise AppError(
                                "EXPORT_BROKEN_REFERENCE", "项目关系不完整，无法导出。", 409
                            )
        for asset in data["assets"]:
            asset.pop("storage_path")
            asset.pop("thumbnail_path")
            asset["original_filename"] = (
                asset["original_filename"].replace("\\", "/").split("/")[-1]
            )
            asset["media_path"] = f"assets/{asset['id']}/original"
        return data

    @contextmanager
    def archive(self, project_id):
        # Provider staging owns the file and cleanup, including response disconnects.
        # The workspace lease pins both the DB snapshot and media root until ZIP closes.
        with self.workspace.resources() as (database, storage):
            with storage.stage_upload() as (_, output):
                try:
                    with database.session() as session:
                        repository = ProjectExportRepository(session)
                        graph, revision = repository.graph(project_id)
                        data = self.serialize(graph, repository)
                        name = safe_name(data["projects"][0]["name"]) + ".zip"
                        with ZipFile(
                            output, "w", compression=ZIP_STORED, allowZip64=True
                        ) as archive:
                            archive.writestr("assets/", b"")
                            for asset, metadata in zip(
                                graph["assets"], data["assets"], strict=True
                            ):
                                if not asset.storage_path.startswith("storage/assets/"):
                                    raise AppError("PATH_UNSAFE", "资产路径不属于托管媒体。", 409)
                                digest, size = hashlib.sha256(), 0
                                with storage.get_file(
                                    asset.storage_path.removeprefix("storage/")
                                ) as source:
                                    with archive.open(
                                        metadata["media_path"], "w", force_zip64=True
                                    ) as target:
                                        while chunk := source.read(1024 * 1024):
                                            target.write(chunk)
                                            digest.update(chunk)
                                            size += len(chunk)
                                if size != asset.file_size or digest.hexdigest() != asset.checksum:
                                    raise AppError(
                                        "EXPORT_MEDIA_CHANGED",
                                        "资产文件校验失败，导出已取消。",
                                        409,
                                    )
                            manifest = {
                                "format_version": 1,
                                "exported_at": utc_now().isoformat(),
                                "project_id": str(project_id),
                                "project_name": data["projects"][0]["name"],
                                "application_version": "0.1.0",
                                "source_schema_revision": revision,
                                "record_policy": "active_only",
                                "global_templates": "snapshots_only",
                                "thumbnails": "regenerate_on_import",
                            }
                            relations = {
                                k: data.pop(k)
                                for k in list(data)
                                if k.endswith("_links") or k == "asset_tags"
                            }
                            documents = {
                                "manifest.json": manifest,
                                "project.json": data.pop("projects")[0],
                                "prompts/templates.json": data.pop("prompt_templates"),
                                "prompts/records.json": data.pop("prompt_records"),
                                "metadata/entities.json": data,
                                "metadata/relations.json": relations,
                            }
                            for path, value in documents.items():
                                archive.writestr(
                                    path,
                                    json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8"),
                                )
                    output.flush()
                    output.seek(0)
                    yield output, name
                except OSError as exc:
                    raise AppError(
                        "EXPORT_IO_FAILED", "导出文件读写失败，请检查磁盘空间与权限。", 500
                    ) from exc
