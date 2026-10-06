import hashlib
import io
import json
from pathlib import PurePosixPath
from uuid import UUID, uuid4
from zipfile import ZipFile

import pytest
from test_ai import post
from test_assets import picture, upload
from test_prompt_versioning import setup
from test_storyboards import client as client
from test_storyboards import imported as import_storyboard
from test_video_results import imported as import_video

from app.models import Asset, PromptRecord
from app.models.base import utc_now
from app.services.storage.local import LocalStorageProvider


def export(client, project):
    response = client.post(f"/api/projects/{project['id']}/export")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/zip"
    with ZipFile(io.BytesIO(response.content)) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == len(set(names))
        assert all(
            not PurePosixPath(n).is_absolute()
            and ".." not in PurePosixPath(n).parts
            and "\\" not in n
            and ":" not in n
            for n in names
        )
        result = {n: json.loads(archive.read(n)) for n in names if n.endswith(".json")}
        result["media"] = {
            n: archive.read(n) for n in names if n.startswith("assets/") and not n.endswith("/")
        }
    assert list(client.app.state.workspace.get_temp_path().iterdir()) == []
    assert list(client.app.state.workspace.get_export_path().iterdir()) == []
    return result


def test_export_graph_media_snapshots_and_secrets(client):
    project, _, shot, template, prompt = setup(client)
    post(client, "/projects", name="UNRELATED PROJECT")
    project_template = post(
        client,
        "/prompt-templates",
        name="项目模板",
        scope="PROJECT",
        project_id=project["id"],
        category="OTHER",
        template_content="模板正文",
    )
    storyboard = import_storyboard(client, shot, prompt, notes="六宫格备注").json()
    video = import_video(
        client,
        shot,
        source_storyboard_id=storyboard["id"],
        source_prompt_record_id=prompt["id"],
        notes="视频备注",
    ).json()
    character = post(client, f"/projects/{project['id']}/characters", name="角色", notes="角色备注")
    state = post(client, f"/characters/{character['id']}/states", name="PPE")
    for endpoint in (f"characters/{character['id']}", f"character-states/{state['id']}"):
        post(client, f"/{endpoint}/assets", asset_id=storyboard["asset_id"])
    post(client, f"/shots/{shot['id']}/character-states", character_state_id=state["id"])
    tag = post(client, "/tags", name="防护")
    post(client, f"/assets/{storyboard['asset_id']}/tags/{tag['id']}")
    client.patch(f"/api/prompts/{prompt['id']}", json={"edited_content": "  中文\n编辑\n"})
    data = export(client, project)
    manifest = data["manifest.json"]
    assert manifest["format_version"] == 1
    assert manifest["source_schema_revision"] == "0010_video_results"
    assert manifest["project_id"] == project["id"]
    assert data["project.json"]["id"] == project["id"]
    assert [t["id"] for t in data["prompts/templates.json"]] == [project_template["id"]]
    record = data["prompts/records.json"][0]
    for field in (
        "id",
        "shot_id",
        "template_content",
        "context_json",
        "rendered_input",
        "input_hash",
        "generated_content",
        "version",
        "is_selected",
        "provider",
        "model_name",
    ):
        assert record[field] == prompt[field]
    assert record["edited_content"] == "  中文\n编辑\n"
    assert record["template_id"] is None
    assert record["source_references"]["template_id"]["original_id"] == template["id"]
    entities = data["metadata/entities.json"]
    assert len(entities["assets"]) == len(data["media"]) == 2
    assert entities["storyboards"][0]["source_prompt_record_id"] == prompt["id"]
    assert entities["video_results"][0]["source_storyboard_id"] == storyboard["id"]
    assert entities["video_results"][0]["source_prompt_record_id"] == prompt["id"]
    assert entities["video_results"][0]["id"] == video["id"]
    assert entities["tags"][0]["id"] == tag["id"]
    assert all(
        data["metadata/relations.json"][name]
        for name in (
            "project_asset_links",
            "shot_asset_links",
            "character_asset_links",
            "character_state_asset_links",
            "shot_character_state_links",
            "asset_tags",
        )
    )
    for asset in entities["assets"]:
        assert hashlib.sha256(data["media"][asset["media_path"]]).hexdigest() == asset["checksum"]
        assert "storage_path" not in asset and "thumbnail_path" not in asset
    text = json.dumps({k: v for k, v in data.items() if k != "media"})
    for forbidden in (
        "UNRELATED PROJECT",
        "api_key",
        "ai-provider.json",
        "workspace.db",
        str(client.app.state.workspace.get_workspace_root()),
    ):
        assert forbidden not in text


def test_active_only_deleted_provenance_is_identity_not_dangling_fk(client):
    project, _, shot, _, prompt = setup(client)
    storyboard = import_storyboard(client, shot, prompt).json()
    video = import_video(client, shot, source_storyboard_id=storyboard["id"]).json()
    assert client.delete(f"/api/storyboards/{storyboard['id']}").status_code == 204
    data = export(client, project)
    entities = data["metadata/entities.json"]
    assert entities["storyboards"] == []
    record = entities["video_results"][0]
    assert record["id"] == video["id"] and record["source_storyboard_id"] is None
    assert record["source_references"]["source_storyboard_id"] == {
        "original_id": storyboard["id"],
        "entity_type": "storyboards",
        "resolution": "external_identity",
    }
    # Independent active Project/Shot links still legitimately require the image.
    assert len(data["media"]) == 2
    with client.app.state.workspace.session() as session:
        r = session.get(PromptRecord, UUID(prompt["id"]))
        r.deleted_at, r.is_selected = utc_now(), False
    assert export(client, project)["prompts/records.json"] == []


def test_deleted_tree_assets_and_template_excluded(client):
    project, scene, shot, _, _ = setup(client)
    storyboard = import_storyboard(client, shot).json()
    assert client.delete(f"/api/scenes/{scene['id']}").status_code == 204
    assert (
        client.delete(f"/api/projects/{project['id']}/assets/{storyboard['asset_id']}").status_code
        == 200
    )
    data = export(client, project)
    entities = data["metadata/entities.json"]
    assert entities["scenes"] == entities["shots"] == entities["storyboards"] == []
    assert data["prompts/records.json"] == [] and data["media"] == {}
    asset = upload(client, picture(), "deleted.png").json()
    assert client.delete(f"/api/assets/{asset['id']}").status_code == 204
    assert export(client, project)["metadata/entities.json"]["assets"] == []


@pytest.mark.parametrize("problem", ["missing", "changed", "traversal", "absolute", "io"])
def test_media_failure_cleans_partial_archive(client, monkeypatch, problem):
    project, _, shot, _, _ = setup(client)
    storyboard = import_storyboard(client, shot).json()
    workspace = client.app.state.workspace
    with workspace.session() as session:
        asset = session.get(Asset, UUID(storyboard["asset_id"]))
        if problem == "changed":
            asset.checksum = "0" * 64
        elif problem == "missing":
            asset.storage_path = "storage/assets/missing.png"
        elif problem == "traversal":
            asset.storage_path = "storage/assets/../../data/workspace.db"
        elif problem == "absolute":
            asset.storage_path = "D:/private/file.png"
    if problem == "io":

        def fail(*args):
            raise OSError("injected")

        monkeypatch.setattr(LocalStorageProvider, "get_file", fail)
    response = client.post(f"/api/projects/{project['id']}/export")
    assert response.status_code >= 400
    assert set(response.json()) == {"code", "message", "details"}
    assert not list(workspace.get_temp_path().iterdir())
    assert not list(workspace.get_export_path().iterdir())


def test_unsafe_names_stream_reads_and_missing_project(client, monkeypatch):
    project, _, shot, _, _ = setup(client)
    client.patch(f"/api/projects/{project['id']}", json={"name": "../中文:项目"})
    storyboard = import_storyboard(client, shot).json()
    with client.app.state.workspace.session() as session:
        session.get(
            Asset, UUID(storyboard["asset_id"])
        ).original_filename = "C:\\secret\\../name.png"
    original = LocalStorageProvider.get_file
    sizes = []

    class Reader:
        def __init__(self, source):
            self.source = source

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.source.close()

        def read(self, size):
            assert 0 < size <= 1024 * 1024
            sizes.append(size)
            return self.source.read(size)

    monkeypatch.setattr(
        LocalStorageProvider, "get_file", lambda self, key: Reader(original(self, key))
    )
    data = export(client, project)
    assert sizes and data["metadata/entities.json"]["assets"][0]["original_filename"] == "name.png"
    assert client.post(f"/api/projects/{uuid4()}/export").status_code == 404
    client.delete(f"/api/projects/{project['id']}")
    assert client.post(f"/api/projects/{project['id']}/export").status_code == 404


@pytest.mark.parametrize(
    "kind",
    [
        "projects",
        "scripts",
        "scenes",
        "shots",
        "assets",
        "characters",
        "character-states",
        "prompt-templates",
        "storyboards",
        "video-results",
    ],
)
def test_recycle_supported_types_restore_identity(client, kind):
    project, scene, shot, template, _ = setup(client)
    if kind == "projects":
        entity = project
    elif kind == "scripts":
        entity = client.get(f"/api/projects/{project['id']}/scripts").json()[0]
    elif kind == "scenes":
        entity = scene
    elif kind == "shots":
        entity = shot
    elif kind == "assets":
        entity = upload(client, picture(), "回收.png").json()
    elif kind in {"characters", "character-states"}:
        entity = post(client, f"/projects/{project['id']}/characters", name="角色")
        if kind == "character-states":
            entity = post(client, f"/characters/{entity['id']}/states", name="状态")
    elif kind == "prompt-templates":
        entity = template
    elif kind == "storyboards":
        entity = import_storyboard(client, shot).json()
    else:
        entity = import_video(client, shot).json()
    url = f"/api/{kind}/{entity['id']}"
    assert client.get(f"/api/recycle-bin?entity_type={kind}").json()["items"] == []
    assert client.delete(url).status_code == 204
    items = client.get(f"/api/recycle-bin?entity_type={kind}").json()["items"]
    assert len(items) == 1 and items[0]["entity_id"] == entity["id"]
    assert items[0]["display_name"] and items[0]["context"] and items[0]["deleted_at"]
    restored = client.post(url + "/restore")
    assert restored.status_code == 200, restored.text
    assert restored.json()["id"] == entity["id"]
    assert client.get(f"/api/recycle-bin?entity_type={kind}").json()["items"] == []


def test_recycle_parent_failure_filter_and_no_purge(client):
    project, _, shot, _, _ = setup(client)
    client.delete(f"/api/projects/{project['id']}")
    assert client.post(f"/api/shots/{shot['id']}/restore").status_code == 404
    items = client.get("/api/recycle-bin?entity_type=shots").json()["items"]
    assert items[0]["entity_id"] == shot["id"]
    assert client.get("/api/recycle-bin?search=NEVER-MATCH-THIS").json()["items"] == []
    assert client.get("/api/recycle-bin?entity_type=tags").status_code == 422
    paths = client.get("/api/openapi.json").json()["paths"]
    assert not any("permanent" in p or "purge" in p for p in paths)
