import hashlib
import io
import shutil
from uuid import UUID, uuid4

import av
import pytest
from alembic import command
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.core.database import Database, migration_config
from app.main import create_app
from app.models.assets import Asset, ProjectAssetLink, ShotAssetLink
from app.models.workflow import Project
from app.repositories.assets import AssetRepository
from app.schemas.workflow import ProjectCreate
from app.services.storage.local import LocalStorageProvider
from app.services.workflow import ProjectService


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings), raise_server_exceptions=False) as value:
        yield value


def picture(format="PNG", size=(640, 360)):
    output = io.BytesIO()
    Image.new("RGB", size, (25, 130, 110)).save(output, format=format)
    return output.getvalue()


def movie(format="mp4", codec="libx264"):
    output = io.BytesIO()
    with av.open(output, "w", format=format) as container:
        stream = container.add_stream(codec, rate=24)
        stream.width, stream.height, stream.pix_fmt = 64, 48, "yuv420p"
        stream.thread_count = 1
        for i in range(12):
            frame = av.VideoFrame.from_image(Image.new("RGB", (64, 48), (20 + i, 80, 120)))
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return output.getvalue()


def upload(client, data=None, filename="reference.png", **params):
    return client.post(
        "/api/assets/upload",
        params={"filename": filename, **params},
        content=picture() if data is None else data,
        headers={"Content-Type": "application/octet-stream"},
    )


def files(client):
    root = client.app.state.workspace.get_storage_path()
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


@pytest.mark.parametrize(
    "format,suffix", [("PNG", "png"), ("JPEG", "jpg"), ("JPEG", "jpeg"), ("WEBP", "webp")]
)
def test_image_import_metadata_copy_thumbnail(client, format, suffix):
    data = picture(format)
    response = upload(client, data, "人物." + suffix)
    assert response.status_code == 201, response.text
    asset = response.json()
    assert UUID(asset["id"])
    assert asset["width"] == 640 and asset["height"] == 360
    assert asset["file_size"] == len(data) and asset["duration_seconds"] is None
    assert asset["storage_path"].startswith("storage/assets/")
    assert asset["thumbnail_path"].startswith("storage/thumbnails/")
    assert client.get(f"/api/assets/{asset['id']}/file").content == data
    thumbnail = client.get(f"/api/assets/{asset['id']}/thumbnail")
    with Image.open(io.BytesIO(thumbnail.content)) as image:
        assert image.size == (512, 288)
    assert len(files(client)) == 2
    assert not any(name.startswith("temp/") for name in files(client))
    duplicate = upload(client, data, "人物." + suffix).json()
    assert duplicate["id"] != asset["id"]
    assert duplicate["storage_path"] != asset["storage_path"]
    assert duplicate["checksum"] == asset["checksum"]


@pytest.mark.parametrize(
    "format,codec", [("mp4", "libx264"), ("mov", "libx264"), ("webm", "libvpx-vp9")]
)
def test_video_metadata_thumbnail_and_range(client, format, codec):
    data = movie(format, codec)
    response = upload(client, data, "video." + format)
    assert response.status_code == 201, response.text
    asset = response.json()
    assert asset["asset_type"] == "VIDEO"
    assert asset["width"] == 64 and asset["height"] == 48
    assert asset["duration_seconds"] == pytest.approx(0.5, abs=0.05)
    assert client.get(f"/api/assets/{asset['id']}/thumbnail").status_code == 200
    chunk = client.get(f"/api/assets/{asset['id']}/file", headers={"Range": "bytes=0-15"})
    assert chunk.status_code == 206 and chunk.content == data[:16]


@pytest.mark.parametrize(
    "name,data",
    [
        ("bad.png", b"not image"),
        ("a.exe", b"exe"),
        ("empty.mp4", b""),
        ("bad.mp4", b"\0\0\0 ftypbroken"),
        ("a.svg", b"<svg/>"),
        ("a.png", picture()[:40]),
    ],
)
def test_bad_upload_cleans_everything(client, name, data):
    response = upload(client, data, name)
    assert response.status_code == 422
    assert response.json()["message"] and response.json()["code"]
    assert client.get("/api/assets").json() == []
    assert files(client) == []


def test_crud_tags_filters_types_soft_delete_restore(client):
    asset = upload(client, filename="original-reference.png").json()
    url = f"/api/assets/{asset['id']}"
    assert (
        client.patch(
            url, json={"name": "  SPF 场景  ", "asset_type": "STORYBOARD_6GRID"}
        ).status_code
        == 200
    )
    assert client.patch(url, json={"asset_type": "VIDEO"}).status_code == 422
    assert client.patch(url, json={"name": " "}).status_code == 422
    assert client.patch(url, json={"mime_type": "fake"}).status_code == 422
    tag = client.post("/api/tags", json={"name": "  SPF  "}).json()
    same = client.post("/api/tags", json={"name": "ｓｐｆ"}).json()
    assert tag["id"] == same["id"]
    relation = f"{url}/tags/{tag['id']}"
    assert client.post(relation).status_code == 200
    assert len(client.post(relation).json()["tags"]) == 1
    for query in (
        {"search": "场景"},
        {"search": "original"},
        {"tag_id": tag["id"]},
        {"asset_type": "STORYBOARD_6GRID"},
    ):
        assert len(client.get("/api/assets", params=query).json()) == 1
    assert client.get("/api/assets", params={"asset_type": "VIDEO"}).json() == []
    assert client.delete(relation).json()["tags"] == []
    assert len(client.post(relation).json()["tags"]) == 1
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404
    assert client.get(url + "/file").status_code == 404
    assert client.get("/api/assets").json() == []
    assert len(client.get("/api/assets?include_deleted=true").json()) == 1
    assert len(files(client)) == 2  # Soft delete preserves original and thumbnail.
    assert client.post(url + "/restore").status_code == 200
    assert client.get(url + "/thumbnail").status_code == 200
    assert client.get(f"/api/assets/{uuid4()}").status_code == 404
    assert client.get("/api/assets?limit=0").status_code == 422


def test_project_shot_links_unique_restorable_and_owner_delete_safe(client):
    project = client.post("/api/projects", json={"name": "SPF"}).json()
    script = client.post(f"/api/projects/{project['id']}/scripts", json={"name": "Script"}).json()
    scene = client.post(
        f"/api/projects/{project['id']}/scenes", json={"name": "Scene", "script_id": script["id"]}
    ).json()
    shot = client.post(
        f"/api/scenes/{scene['id']}/shots",
        json={"project_id": project["id"], "shot_code": "S13", "title": "入口"},
    ).json()
    asset = upload(client).json()
    project_url = f"/api/projects/{project['id']}/assets"
    shot_url = f"/api/shots/{shot['id']}/assets"
    for url, key in ((project_url, "projects"), (shot_url, "shots")):
        assert len(client.post(url, json={"asset_id": asset["id"]}).json()[key]) == 1
        assert len(client.post(url, json={"asset_id": asset["id"]}).json()[key]) == 1
    assert len(files(client)) == 2
    assert len(client.get("/api/assets", params={"shot_id": shot["id"]}).json()) == 1
    assert client.delete(f"/api/assets/{asset['id']}").json()["code"] == "ASSET_IN_USE"
    client.delete(f"/api/projects/{project['id']}")
    assert client.get(f"/api/assets/{asset['id']}/file").status_code == 200
    assert client.delete(f"/api/assets/{asset['id']}").status_code == 409
    for url in (project_url, shot_url):
        assert client.delete(f"{url}/{asset['id']}").status_code == 200
    assert client.delete(f"/api/assets/{asset['id']}").status_code == 204
    with client.app.state.workspace.session() as session:
        for model in (ProjectAssetLink, ShotAssetLink):
            links = session.scalars(select(model)).all()
            assert len(links) == 1 and links[0].deleted_at is not None


@pytest.mark.parametrize("failure", ["copy", "thumbnail", "repository", "commit"])
def test_import_compensation_covers_commit(client, monkeypatch, failure):
    def fail(*args, **kwargs):
        raise RuntimeError("Injected failure")

    if failure == "copy":
        monkeypatch.setattr(LocalStorageProvider, "_copy", fail)
    elif failure == "thumbnail":
        monkeypatch.setattr(LocalStorageProvider, "create_thumbnail", fail)
    elif failure == "repository":
        monkeypatch.setattr(AssetRepository, "add", fail)
    else:
        from sqlalchemy import event

        event.listen(Session, "before_commit", fail)
    try:
        assert upload(client).status_code == 500
    finally:
        if failure == "commit":
            event.remove(Session, "before_commit", fail)
    assert files(client) == []
    assert client.get("/api/assets").json() == []


def test_phase3_upgrade_preserves_phase2_data_and_downgrades(tmp_path):
    from app.schemas.workflow import SceneCreate, ScriptCreate
    from app.services.assets import AssetService
    from app.services.workflow import SceneService, ScriptService, ShotService

    database = Database(tmp_path / "phase2.db")
    config = migration_config()
    try:
        with database.engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "0002_core_workflow")
        with database.session() as session:
            identifier = (
                ProjectService(session).create_project(ProjectCreate(name="Existing SPF")).id
            )
            script = ScriptService(session).create_script(
                identifier, ScriptCreate(name="Existing script")
            )
            scene = SceneService(session).create_scene(
                identifier, SceneCreate(script_id=script.id, name="Existing scene")
            )
            # Seed the historical schema with its reflected table, not the current ORM.
            from types import SimpleNamespace

            from sqlalchemy import MetaData, Table

            from app.models.base import utc_now

            shot = SimpleNamespace(id=uuid4())
            old_shots = Table("shots", MetaData(), autoload_with=session.connection())
            session.execute(
                old_shots.insert().values(
                    id=shot.id.hex,
                    project_id=identifier.hex,
                    scene_id=scene.id.hex,
                    shot_code="S13",
                    title="Existing shot",
                    description="",
                    duration_seconds=0,
                    order_index=0,
                    status="DRAFT",
                    creative_requirement="",
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
            )
        database.upgrade()
        with database.session() as session:
            assert session.get(Project, identifier).name == "Existing SPF"
            assert ShotService(session).shot(shot.id).title == "Existing shot"
            asset = AssetRepository(session).add(
                Asset(
                    name="Migration fixture",
                    asset_type="IMAGE",
                    original_filename="a.png",
                    storage_path="storage/assets/a.png",
                    thumbnail_path="storage/thumbnails/a.jpg",
                    file_size=10,
                    checksum="0" * 64,
                    mime_type="image/png",
                    width=2,
                    height=2,
                )
            )
            AssetService(session).bind(asset.id, identifier, "project")
            AssetService(session).bind(asset.id, shot.id, "shot")
        with database.engine.begin() as connection:
            config.attributes["connection"] = connection
            command.check(config)
            command.downgrade(config, "0002_core_workflow")
            assert "assets" not in inspect(connection).get_table_names()
            command.upgrade(config, "head")
            command.check(config)
            assert connection.scalar(text("select count(*) from projects")) == 1
        with database.session() as session:
            assert ShotService(session).shot(shot.id).title == "Existing shot"
            assert SceneService(session).scene(scene.id).name == "Existing scene"
            assert ScriptService(session).script(script.id).name == "Existing script"
    finally:
        database.dispose()


def test_mime_comes_from_bytes_and_classification_is_separate(client):
    asset = upload(client, picture("JPEG"), "renamed.png", asset_type="OTHER").json()
    assert asset["mime_type"] == "image/jpeg" and asset["asset_type"] == "OTHER"
    assert (
        client.patch(f"/api/assets/{asset['id']}", json={"asset_type": "IMAGE"}).status_code == 200
    )
    assert upload(client, movie(), "video.mp4", asset_type="STORYBOARD_6GRID").status_code == 422
    assert len(files(client)) == 2


def test_upload_limits_and_pixel_limits_cleanup(client, monkeypatch):
    from app.services.storage import media, service

    monkeypatch.setattr(service, "MAX_UPLOAD_SIZE", 20)
    assert upload(client).status_code == 413
    assert files(client) == []
    monkeypatch.setattr(service, "MAX_UPLOAD_SIZE", 512 * 1024 * 1024)
    monkeypatch.setattr(media, "MAX_PIXELS", 10)
    assert upload(client).status_code == 422
    assert files(client) == []


@pytest.mark.parametrize("mode", ["disconnect", "switch"])
def test_interrupted_or_switched_upload_has_no_orphans(workspace, tmp_path, mode):
    import asyncio

    from app.core.exceptions import AppError
    from app.services.storage.service import StorageService

    old_root = workspace.get_storage_path()

    async def chunks():
        yield picture()
        if mode == "disconnect":
            raise RuntimeError("Disconnected")
        workspace.set_workspace_root(tmp_path / "switched")

    with pytest.raises((RuntimeError, AppError)) as error:
        asyncio.run(StorageService(workspace).upload(chunks(), "reference.png"))
    if mode == "switch":
        assert error.value.code == "WORKSPACE_CHANGED"
    assert not [p for p in old_root.rglob("*") if p.is_file()]
    with workspace.session() as session:
        assert session.scalars(select(Asset)).all() == []


def test_thumbnail_publish_failure_preserves_existing_file(client, monkeypatch):
    from app.services.storage import local

    identifier = uuid4()
    root = client.app.state.workspace.get_storage_path()
    existing = root / "thumbnails" / f"{identifier}.jpg"
    existing.write_bytes(b"existing thumbnail")
    sequence = iter((uuid4(), uuid4(), identifier, uuid4()))
    monkeypatch.setattr(local, "uuid4", lambda: next(sequence))
    assert upload(client).status_code == 500
    assert existing.read_bytes() == b"existing thumbnail"
    assert files(client) == [f"thumbnails/{identifier}.jpg"]


def test_upload_temp_name_collision_never_deletes_another_file(client, monkeypatch):
    from app.services.storage import local

    identifier = uuid4()
    existing = client.app.state.workspace.get_temp_path() / f"{identifier}.partial"
    existing.write_bytes(b"another import")
    monkeypatch.setattr(local, "uuid4", lambda: identifier)
    assert upload(client).status_code == 500
    assert existing.read_bytes() == b"another import"


def test_asset_pagination_literal_search_and_missing_links(client):
    a = upload(client, filename="a%one.png").json()
    b = upload(client, filename="btwo.png").json()
    assert len(client.get("/api/assets?limit=1").json()) == 1
    assert client.get("/api/assets?limit=1&offset=1").json()[0]["id"] == a["id"]
    assert client.get("/api/assets", params={"search": "%"}).json()[0]["id"] == a["id"]
    assert (
        client.post(f"/api/projects/{uuid4()}/assets", json={"asset_id": b["id"]}).status_code
        == 404
    )
    assert client.post(f"/api/assets/{b['id']}/tags/{uuid4()}").status_code == 404


def test_delete_original_source_does_not_affect_import(workspace, tmp_path):
    import asyncio

    from app.services.storage.service import StorageService

    source = tmp_path / "original.png"
    data = picture()
    source.write_bytes(data)

    async def chunks():
        yield source.read_bytes()

    result = asyncio.run(StorageService(workspace).upload(chunks(), source.name))
    source.unlink()
    path, _ = StorageService(workspace).file(result.id)
    assert path.read_bytes() == data


@pytest.mark.parametrize("restart", [False, True])
def test_copied_workspace_switch_preserves_assets_and_routes_new_writes(
    settings, tmp_path, restart
):
    """Exercise the real switch API against two isolated, fully copied workspaces."""
    source = settings.resolved_workspace_root
    target = tmp_path / "copied-workspace"
    assert source.is_relative_to(tmp_path)
    assert settings.bootstrap_config_path.is_relative_to(tmp_path)
    with TestClient(create_app(settings)) as client:
        original = upload(client).json()
        project = client.post("/api/projects", json={"name": "Migration"}).json()
        script = client.post(
            f"/api/projects/{project['id']}/scripts", json={"name": "Script"}
        ).json()
        scene = client.post(
            f"/api/projects/{project['id']}/scenes",
            json={"name": "Scene", "script_id": script["id"]},
        ).json()
        shot = client.post(
            f"/api/scenes/{scene['id']}/shots",
            json={"project_id": project["id"], "shot_code": "S01", "title": "Shot"},
        ).json()
        tag = client.post("/api/tags", json={"name": "Preserved"}).json()
        url = f"/api/assets/{original['id']}"
        assert client.post(f"{url}/tags/{tag['id']}").status_code == 200
        for owner, entity in (("projects", project), ("shots", shot)):
            assert (
                client.post(
                    f"/api/{owner}/{entity['id']}/assets", json={"asset_id": original["id"]}
                ).status_code
                == 200
            )
        detail = client.get(url).json()
        thumbnail = client.get(url + "/thumbnail").content
    for relative in ("exports/unknown.custom", "backups/snapshot.bin", "storage/temp/keep.partial"):
        (source / relative).write_bytes(b"managed content")

    def snapshot(root):
        return {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*")
            if p.is_file()
        }

    before = snapshot(source)
    shutil.copytree(source, target)
    assert snapshot(target) == before
    with TestClient(create_app(settings)) as client:
        response = client.put("/api/settings/workspace", json={"workspace_root": str(target)})
        assert response.status_code == 200
        assert response.json()["database_path"] == str(target / "data/workspace.db")

        def verify(active):
            workspace = active.app.state.workspace
            assert workspace.get_workspace_root() == target
            with workspace.session() as session:
                actual = session.execute(text("PRAGMA database_list")).one()[2]
                assert actual.replace("\\", "/") == (target / "data/workspace.db").as_posix()
            assert workspace.get_temp_path() == target / "storage/temp"
            assert workspace.get_export_path() == target / "exports"
            assert workspace.get_backup_path() == target / "backups"
            assert active.get(url).json() == detail
            assert active.get(url + "/file").content == picture()
            assert active.get(url + "/thumbnail").content == thumbnail
            from app.services.storage.service import StorageService

            storage = StorageService(workspace)
            assert storage.file(UUID(original["id"]))[0] == target / original["storage_path"]
            assert (
                storage.file(UUID(original["id"]), thumbnail=True)[0]
                == target / original["thumbnail_path"]
            )
            new = upload(active, filename="after-switch.png").json()
            for field in ("storage_path", "thumbnail_path"):
                assert new[field].startswith("storage/")
                assert (target / new[field]).is_file()
                assert not (source / new[field]).exists()
            assert snapshot(source) == before

        if not restart:
            verify(client)
    if restart:
        # The original Settings seed still points to A; persisted bootstrap must win.
        with TestClient(create_app(settings)) as client:
            verify(client)
    assert snapshot(source) == before
