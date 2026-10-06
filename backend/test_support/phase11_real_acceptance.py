"""Accept an already copied real workspace, never open production for writing."""

import hashlib
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from uuid import UUID, uuid4
from zipfile import ZipFile

from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from app.core.config import REPOSITORY_ROOT, Settings
from app.main import create_app
from app.models.base import Base
from test_support.fake_ai import FakeAIProvider
from test_support.phase11_artifacts import validate


def augment(client, project, workspace):
    # Reuse existing in-memory test media builders; no external AI or media API.
    from test_assets import movie, picture

    def post(path, **data):
        response = client.post(f"/api{path}", json=data)
        assert response.is_success, response.text
        return response.json()

    shot = next(
        s
        for s in client.get(f"/api/projects/{project['id']}/shots").json()
        if s["shot_code"] == "S13"
    )
    assets = client.get("/api/assets").json()
    assert len(assets) == 1
    real = assets[0]
    assert real["asset_type"] == "IMAGE" and real["mime_type"] == "image/png"
    real_bytes = (workspace / real["storage_path"]).read_bytes()
    assert hashlib.sha256(real_bytes).hexdigest() == real["checksum"]
    post(f"/projects/{project['id']}/assets", asset_id=real["id"])
    post(f"/shots/{shot['id']}/assets", asset_id=real["id"])
    configured = client.put(
        "/api/settings/ai",
        json={
            "api_base_url": "https://unused.invalid/v1",
            "model": "acceptance-test-only",
            "api_key": "acceptance-only-secret-never-export",
        },
    )
    assert configured.is_success
    prompts = []
    for category, scope in (("STORYBOARD_6GRID", "GLOBAL"), ("VIDEO_GENERATION", "PROJECT")):
        template = post(
            "/prompt-templates",
            name=f"acceptance / test-only {category}",
            scope=scope,
            project_id=project["id"] if scope == "PROJECT" else None,
            category=category,
            template_content="acceptance / test-only\n{{shot_context}}",
        )
        preview = post(f"/shots/{shot['id']}/prompts/preview", template_id=template["id"])
        prompt = post(
            f"/shots/{shot['id']}/prompts/generate",
            template_id=template["id"],
            input_hash=preview["input_hash"],
            operation_id=str(uuid4()),
        )
        edited = client.patch(
            f"/api/prompts/{prompt['id']}",
            json={
                "edited_content": "  acceptance / test-only edited\n保留空白\n",
            },
        )
        assert edited.is_success
        prompts.append(edited.json())
    storyboard_response = client.post(
        f"/api/shots/{shot['id']}/storyboards/import",
        params={
            "filename": "acceptance-test-only-storyboard.png",
            "source_prompt_record_id": prompts[0]["id"],
            "notes": "acceptance / test-only",
        },
        content=picture(),
    )
    assert storyboard_response.status_code == 201, storyboard_response.text
    storyboard = storyboard_response.json()
    video_response = client.post(
        f"/api/shots/{shot['id']}/video-results/import",
        params={
            "filename": "acceptance-test-only-video.mp4",
            "source_storyboard_id": storyboard["id"],
            "source_prompt_record_id": prompts[1]["id"],
            "notes": "acceptance / test-only",
        },
        content=movie(),
    )
    assert video_response.status_code == 201, video_response.text
    video = video_response.json()
    deleted = post(
        f"/projects/{project['id']}/characters", name="acceptance / test-only deleted exclusion"
    )
    assert client.delete(f"/api/characters/{deleted['id']}").status_code == 204
    assert client.get(f"/api/assets/{real['id']}").json()["asset_type"] == real["asset_type"]
    return real, real_bytes, prompts, storyboard, video, deleted


def main(directory):
    root = Path(directory).resolve(strict=True)
    assert root.parent == (REPOSITORY_ROOT / ".workspace").resolve()
    assert root.name.startswith("phase11-real-")
    workspace = root / "workspace"
    database = workspace / "data/workspace.db"
    assert not (root / "config.json").exists()
    (root / "config.json").write_text(
        json.dumps({"workspace_root": str(workspace)}), encoding="utf-8"
    )
    settings = Settings(
        _env_file=None, workspace_root=workspace, bootstrap_config_path=root / "config.json"
    )
    app = create_app(settings)
    app.state.ai_provider = FakeAIProvider(result="acceptance / test-only generated content")
    with TestClient(app, raise_server_exceptions=False) as client:
        projects = client.get("/api/projects").json()
        assert len(projects) == 1 and "SPF" in projects[0]["name"]
        # Snapshot all production-derived facts before augmentation.
        with app.state.workspace.session() as session:
            originals = []
            for mapper in Base.registry.mappers:
                from sqlalchemy import select

                for row in session.scalars(select(mapper.class_)):
                    originals.append(
                        (
                            mapper.class_,
                            row.id,
                            jsonable_encoder(
                                {c.name: getattr(row, c.name) for c in row.__table__.columns}
                            ),
                        )
                    )
        real, real_bytes, prompts, storyboard, video, deleted = augment(
            client, projects[0], workspace
        )
        before = hashlib.sha256(database.read_bytes()).hexdigest()
        for project in projects:
            response = client.post(f"/api/projects/{project['id']}/export")
            assert response.status_code == 200, response.text
            path = root / f"{project['id']}.zip"
            path.write_bytes(response.content)
            tables = validate(path)
            assert tables["projects"][0]["id"] == project["id"]
            assert len(tables["assets"]) == 3
            assert len(tables["prompt_records"]) == 2
            assert len(tables["storyboards"]) == len(tables["video_results"]) == 1
            assert deleted["id"] not in {row["id"] for row in tables["characters"]}
            exported_assets = {row["id"]: row for row in tables["assets"]}
            assert exported_assets[real["id"]]["asset_type"] == real["asset_type"]
            with ZipFile(path) as archive:
                assert archive.read(exported_assets[real["id"]]["media_path"]) == real_bytes
                assert "acceptance-only-secret-never-export" not in str(tables)
                assert str(root) not in str(tables)
            for table, expected in (("storyboards", storyboard), ("video_results", video)):
                actual = tables[table][0]
                for key in (
                    "id",
                    "shot_id",
                    "asset_id",
                    "version",
                    "is_selected",
                    "notes",
                    "source_prompt_record_id",
                ):
                    assert actual[key] == expected[key]
            assert tables["video_results"][0]["source_storyboard_id"] == storyboard["id"]
            assert storyboard["source_prompt_record_id"] != video["source_prompt_record_id"]
            exported_prompts = {row["id"]: row for row in tables["prompt_records"]}
            for expected in prompts:
                for key in (
                    "version",
                    "is_selected",
                    "template_content",
                    "context_json",
                    "rendered_input",
                    "generated_content",
                    "edited_content",
                    "input_hash",
                ):
                    assert exported_prompts[expected["id"]][key] == expected[key]
            assert prompts[0]["template_id"] not in {
                row["id"] for row in tables["prompt_templates"]
            }
            assert prompts[1]["template_id"] in {row["id"] for row in tables["prompt_templates"]}
            # Compare every exported persisted field against the copied database.
            with app.state.workspace.session() as session:
                for table, rows in tables.items():
                    model = next(
                        m.class_ for m in Base.registry.mappers if m.local_table.name == table
                    )
                    for row in rows:
                        source = session.get(model, UUID(row["id"]))
                        assert source is not None
                        original = jsonable_encoder(
                            {c.name: getattr(source, c.name) for c in source.__table__.columns}
                        )
                        for key, value in original.items():
                            if key in {"storage_path", "thumbnail_path", "original_filename"}:
                                continue
                            if key in row.get("source_references", {}):
                                assert row["source_references"][key]["original_id"] == value
                            else:
                                assert row[key] == value, (table, key)
            print(
                json.dumps(
                    {
                        "project_id": project["id"],
                        "counts": {k: len(v) for k, v in tables.items()},
                        "zip": str(path),
                        "field_identity": "PASS",
                    }
                )
            )
        assert not list(app.state.workspace.get_temp_path().iterdir())
        assert not list(app.state.workspace.get_export_path().iterdir())
        assert hashlib.sha256(database.read_bytes()).hexdigest() == before
        with app.state.workspace.session() as session:
            for model, identifier, original in originals:
                row = session.get(model, identifier)
                assert (
                    jsonable_encoder({c.name: getattr(row, c.name) for c in row.__table__.columns})
                    == original
                )
        # The copied real project supplies context; only this isolated copy is mutated.
        identifier = projects[0]["id"]
        response = client.post(
            f"/api/projects/{identifier}/characters", json={"name": "Phase11 isolated restore"}
        )
        assert response.status_code == 201
        character = response.json()
        url = f"/api/characters/{character['id']}"
        assert client.delete(url).status_code == 204
        items = client.get("/api/recycle-bin?search=Phase11%20isolated%20restore").json()["items"]
        assert [i["entity_id"] for i in items] == [character["id"]]
        assert client.post(url + "/restore").status_code == 200
        assert (
            client.get("/api/recycle-bin?search=Phase11%20isolated%20restore").json()["items"] == []
        )
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == (
            "0010_video_results"
        )
    print(
        "PASS: production-derived original rows and real IMAGE bytes unchanged; "
        "synthetic prompts/storyboard/video dual provenance and media verified; "
        "artifact/security/restore/integrity verified. Cleanup still required."
    )


if __name__ == "__main__":
    main(sys.argv[1])
