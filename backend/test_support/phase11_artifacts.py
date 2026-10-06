"""Read-only validation of real browser downloads and isolated-copy exports."""

import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from uuid import UUID
from zipfile import ZipFile

from app.models.base import Base


def validate(path):
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == len(set(names))
        for name in names:
            assert not PurePosixPath(name).is_absolute()
            assert ".." not in PurePosixPath(name).parts
            assert "\\" not in name and ":" not in name
        documents = {
            name: json.loads(archive.read(name)) for name in names if name.endswith(".json")
        }
        assert set(documents) == {
            "manifest.json",
            "project.json",
            "prompts/templates.json",
            "prompts/records.json",
            "metadata/entities.json",
            "metadata/relations.json",
        }
        manifest = documents["manifest.json"]
        assert manifest["format_version"] == 1
        assert manifest["record_policy"] == "active_only"
        assert manifest["global_templates"] == "snapshots_only"
        project = documents["project.json"]
        assert manifest["project_id"] == project["id"]
        tables = {
            **documents["metadata/entities.json"],
            **documents["metadata/relations.json"],
            "projects": [project],
            "prompt_templates": documents["prompts/templates.json"],
            "prompt_records": documents["prompts/records.json"],
        }
        identities = {table: {r["id"] for r in rows} for table, rows in tables.items()}
        for table, rows in tables.items():
            assert len(identities[table]) == len(rows)
            for row in rows:
                UUID(row["id"])
                assert row.get("deleted_at") is None
                for column in Base.metadata.tables[table].columns:
                    for fk in column.foreign_keys:
                        value = row[column.name]
                        assert value is None or value in identities[fk.column.table.name]
                for source in row.get("source_references", {}).values():
                    UUID(source["original_id"])
                    if source["resolution"] == "included":
                        assert source["original_id"] in identities[source["entity_type"]]
        assert all(t["scope"] == "PROJECT" for t in tables["prompt_templates"])
        media = {n for n in names if n.startswith("assets/") and not n.endswith("/")}
        assert media == {a["media_path"] for a in tables["assets"]}
        for asset in tables["assets"]:
            payload = archive.read(asset["media_path"])
            assert len(payload) == asset["file_size"]
            assert hashlib.sha256(payload).hexdigest() == asset["checksum"]
            assert "storage_path" not in asset and "thumbnail_path" not in asset
        serialized = json.dumps(documents, ensure_ascii=False)
        for forbidden in (
            "api_key",
            "ai-provider.json",
            "config.json",
            "workspace.db",
            "fake-phase11-key",
            "fake-browser-credential",
            "fake-video-key",
        ):
            assert forbidden not in serialized and not any(forbidden in n for n in names)
        assert not re.search(r"[A-Za-z]:[/\\]", serialized)
        assert not re.search(r"/(?:home|Users|tmp)/", serialized)
    return tables


if __name__ == "__main__":
    paths = list(Path(sys.argv[1]).rglob("project.zip"))
    assert len(paths) == 4, f"Expected four actual browser downloads, got {len(paths)}"
    for path in paths:
        tables = validate(path)
        assert len(tables["prompt_records"]) == len(tables["storyboards"]) == 1
        assert len(tables["video_results"]) == 1 and len(tables["assets"]) == 2
        prompt = tables["prompt_records"][0]
        video = tables["video_results"][0]
        assert video["source_prompt_record_id"] == prompt["id"]
        assert video["source_storyboard_id"] == tables["storyboards"][0]["id"]
        for row in [prompt, video, tables["storyboards"][0]]:
            assert row["version"] == 1 and row["is_selected"] is True
        print(f"PASS {path.parent.name}: integrity, graph, media, provenance, secrets, paths")
