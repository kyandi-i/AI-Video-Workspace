from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import event, inspect, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from test_ai import post
from test_assets import files, movie, picture, upload
from test_prompt_versioning import generated, setup
from test_storyboards import client as client
from test_storyboards import imported as storyboard_import

from app.core.database import migration_config
from app.main import create_app
from app.models.assets import Asset, ProjectAssetLink, ShotAssetLink
from app.models.video_results import VideoResult
from app.repositories.video_results import VideoResultRepository


def imported(client, shot, **sources):
    return client.post(
        f"/api/shots/{shot['id']}/video-results/import",
        params={"filename": "video.mp4", **sources},
        content=movie(),
    )


def history(client, shot, deleted=False):
    response = client.get(
        f"/api/shots/{shot['id']}/video-results", params={"include_deleted": deleted}
    )
    assert response.status_code == 200, response.text
    return response.json()


def create(client, shot, asset_id, **sources):
    return post(client, f"/shots/{shot['id']}/video-results", asset_id=asset_id, **sources)


@pytest.mark.parametrize(
    "storyboard_source,prompt_source", [(False, False), (True, False), (False, True), (True, True)]
)
def test_provenance_combinations_and_stability(client, storyboard_source, prompt_source):
    _, _, shot, template, p1 = setup(client)
    storyboard = storyboard_import(client, shot, p1).json()
    p2 = generated(client, shot, template)
    sources = {}
    if storyboard_source:
        sources["source_storyboard_id"] = storyboard["id"]
    if prompt_source:
        sources["source_prompt_record_id"] = p2["id"]
    response = imported(client, shot, notes="视频评审", **sources)
    assert response.status_code == 201, response.text
    record = response.json()
    assert record["source_storyboard_id"] == sources.get("source_storyboard_id")
    assert record["source_prompt_record_id"] == sources.get("source_prompt_record_id")
    assert record["notes"] == "视频评审"
    storyboard_import(client, shot, p2)
    client.post(f"/api/prompts/{p1['id']}/select")
    client.delete(f"/api/storyboards/{storyboard['id']}")
    current = history(client, shot)[0]
    assert current["source_storyboard_id"] == record["source_storyboard_id"]
    assert current["source_prompt_record_id"] == record["source_prompt_record_id"]
    if storyboard_source:
        assert current["source_storyboard"]["is_deleted"]


def test_versions_restore_and_restart(client, settings):
    _, _, shot, _, _ = setup(client)
    response = imported(client, shot)
    assert response.status_code == 201, response.text
    v1 = response.json()
    assert v1["version"] == 1 and v1["is_selected"] and v1["notes"] is None
    v2 = create(client, shot, v1["asset_id"])
    assert v2["version"] == 2 and v2["is_selected"]
    assert not history(client, shot)[1]["is_selected"]
    for r in [v1, v2]:
        assert client.post(f"/api/video-results/{r['id']}/select").status_code == 200
        assert [v["id"] for v in history(client, shot) if v["is_selected"]] == [r["id"]]
    assert client.delete(f"/api/video-results/{v2['id']}").status_code == 204
    assert not history(client, shot)[0]["is_selected"]
    v3 = create(client, shot, v1["asset_id"])
    assert v3["version"] == 3
    restored = post(client, f"/video-results/{v2['id']}/restore")
    assert not restored["is_selected"]
    assert [r["id"] for r in history(client, shot) if r["is_selected"]] == [v3["id"]]
    before = history(client, shot)
    with TestClient(create_app(settings)) as restarted:
        assert history(restarted, shot) == before
        assert restarted.get(f"/api/assets/{v1['asset_id']}/file").content == movie()


def test_existing_asset_links_and_protection(client):
    project, _, shot, _, _ = setup(client)
    asset = upload(client, movie(), "video.mp4").json()
    before = files(client)
    v1 = create(client, shot, asset["id"])
    v2 = create(client, shot, asset["id"])
    assert files(client) == before
    with client.app.state.workspace.session() as session:
        for model in [ProjectAssetLink, ShotAssetLink]:
            assert (
                len(list(session.scalars(select(model).where(model.asset_id == UUID(asset["id"])))))
                == 1
            )
    client.delete(f"/api/video-results/{v1['id']}")
    detail = client.get(f"/api/assets/{asset['id']}").json()
    assert len(detail["projects"]) == len(detail["shots"]) == 1
    for kind, owner in [("projects", project), ("shots", shot)]:
        assert client.delete(f"/api/{kind}/{owner['id']}/assets/{asset['id']}").status_code == 200
    assert history(client, shot) == [v2]
    response = client.delete(f"/api/assets/{asset['id']}")
    assert response.status_code == 409 and response.json()["code"] == "ASSET_IN_USE"
    assert response.json()["details"]["video_results"] == 1
    for kind in ["IMAGE", "OTHER", "STORYBOARD_6GRID"]:
        assert (
            client.patch(f"/api/assets/{asset['id']}", json={"asset_type": kind}).status_code == 409
        )
    client.delete(f"/api/video-results/{v2['id']}")
    assert client.delete(f"/api/assets/{asset['id']}").status_code == 204
    assert client.post(f"/api/video-results/{v2['id']}/restore").status_code == 404
    post(client, f"/assets/{asset['id']}/restore")
    assert not post(client, f"/video-results/{v2['id']}/restore")["is_selected"]
    detail = client.get(f"/api/assets/{asset['id']}").json()
    assert detail["projects"] == detail["shots"] == []
    assert files(client) == before


@pytest.mark.parametrize("kind", ["IMAGE", "OTHER", "STORYBOARD_6GRID", "missing", "deleted"])
def test_invalid_asset(client, kind):
    _, _, shot, _, _ = setup(client)
    asset_id = str(uuid4())
    if kind != "missing":
        asset_id = upload(
            client,
            movie() if kind == "deleted" else picture(),
            "video.mp4" if kind == "deleted" else "image.png",
            asset_type="VIDEO" if kind == "deleted" else kind,
        ).json()["id"]
        if kind == "deleted":
            client.delete(f"/api/assets/{asset_id}")
    response = client.post(f"/api/shots/{shot['id']}/video-results", json={"asset_id": asset_id})
    assert response.status_code == (404 if kind in ["missing", "deleted"] else 422)
    assert history(client, shot) == []


@pytest.mark.parametrize("field", ["source_storyboard_id", "source_prompt_record_id"])
@pytest.mark.parametrize("missing", [False, True])
def test_invalid_provenance_compensation(client, field, missing):
    project, scene, shot, _, prompt = setup(client)
    storyboard = storyboard_import(client, shot, prompt).json()
    other = post(
        client,
        f"/scenes/{scene['id']}/shots",
        project_id=project["id"],
        shot_code="S14",
        title="Other",
    )
    source = (
        str(uuid4())
        if missing
        else (storyboard["id"] if field == "source_storyboard_id" else prompt["id"])
    )
    before = files(client)
    response = imported(client, other, **{field: source})
    assert response.status_code == (404 if missing else 400), response.text
    assert files(client) == before and history(client, other) == []


@pytest.mark.parametrize(
    "point", ["assets", "project_asset_links", "shot_asset_links", "video_results", "commit"]
)
def test_transaction_compensation(client, point):
    _, _, shot, _, _ = setup(client)
    assert imported(client, shot).status_code == 201
    before, media = history(client, shot), files(client)
    engine = client.app.state.workspace._database.engine

    def fail_sql(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO " + point + " "):
            raise OperationalError("synthetic", {}, Exception("injected"))

    def fail_commit(session):
        if not session.in_nested_transaction():
            raise OperationalError("synthetic", {}, Exception("injected"))

    target, name, callback = (
        (Session, "before_commit", fail_commit)
        if point == "commit"
        else (engine, "after_cursor_execute", fail_sql)
    )
    event.listen(target, name, callback)
    try:
        assert imported(client, shot).status_code >= 400
    finally:
        event.remove(target, name, callback)
    assert history(client, shot) == before and files(client) == media
    with client.app.state.workspace.session() as session:
        for model in [Asset, VideoResult, ProjectAssetLink, ShotAssetLink]:
            assert len(list(session.scalars(select(model)))) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"version": 1},
        {"version": 0},
        {"is_selected": True},
        {"asset_id": uuid4()},
        {"source_storyboard_id": uuid4()},
        {"source_prompt_record_id": uuid4()},
    ],
    ids=["duplicate-version", "zero", "selected", "asset-fk", "storyboard-fk", "prompt-fk"],
)
def test_database_constraints(client, changes):
    _, _, shot, _, _ = setup(client)
    v1 = imported(client, shot).json()
    fields = {
        "shot_id": UUID(shot["id"]),
        "asset_id": UUID(v1["asset_id"]),
        "version": 2,
        "is_selected": False,
        **changes,
    }
    with pytest.raises(IntegrityError), client.app.state.workspace.session() as session:
        VideoResultRepository(session).add(VideoResult(**fields))
    assert history(client, shot) == [v1]


def test_concurrent_versions(client):
    _, _, shot, _, _ = setup(client)
    v1 = imported(client, shot).json()
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda _: create(client, shot, v1["asset_id"]), range(3)))
    assert sorted(r["version"] for r in results) == [2, 3, 4]
    assert sum(r["is_selected"] for r in history(client, shot)) == 1


def test_populated_migration(client):
    _, _, shot, _, prompt = setup(client)
    storyboard = storyboard_import(client, shot, prompt).json()
    asset = upload(client, movie(), "video.mp4").json()
    db = client.app.state.workspace._database
    config = migration_config()
    with db.engine.begin() as conn:
        config.attributes["connection"] = conn
        command.downgrade(config, "0009_storyboards")
        tables = set(inspect(conn).get_table_names()) - {"alembic_version"}
        before = {t: conn.exec_driver_sql(f'SELECT * FROM "{t}" ORDER BY id').all() for t in tables}
        command.upgrade(config, "head")
        command.check(config)
    with db.session() as session:
        VideoResultRepository(session).add(
            VideoResult(
                shot_id=UUID(shot["id"]),
                asset_id=UUID(asset["id"]),
                source_storyboard_id=UUID(storyboard["id"]),
                source_prompt_record_id=UUID(prompt["id"]),
                version=1,
                is_selected=True,
            )
        )
    with db.engine.begin() as conn:
        config.attributes["connection"] = conn
        command.downgrade(config, "0009_storyboards")
        assert "video_results" not in inspect(conn).get_table_names()
        command.upgrade(config, "head")
        command.check(config)
        assert {
            t: conn.exec_driver_sql(f'SELECT * FROM "{t}" ORDER BY id').all() for t in tables
        } == before
        assert conn.exec_driver_sql("select count(*) from video_results").scalar() == 0
        assert conn.exec_driver_sql("pragma integrity_check").scalar() == "ok"
        assert conn.exec_driver_sql("pragma foreign_key_check").all() == []
