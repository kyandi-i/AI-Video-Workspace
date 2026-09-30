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

from app.core.database import migration_config
from app.main import create_app
from app.models.assets import Asset, ProjectAssetLink, ShotAssetLink
from app.models.storyboards import Storyboard
from app.repositories.storyboards import StoryboardRepository
from test_support.fake_ai import FakeAIProvider


@pytest.fixture
def client(settings):
    app = create_app(settings)
    app.state.ai_provider = FakeAIProvider()
    with TestClient(app, raise_server_exceptions=False) as value:
        yield value


def imported(client, shot, prompt=None, **params):
    return client.post(
        f"/api/shots/{shot['id']}/storyboards/import",
        params={
            "filename": "grid.png",
            **({"source_prompt_record_id": prompt["id"]} if prompt else {}),
            **params,
        },
        content=picture(),
    )


def history(client, shot):
    r = client.get(f"/api/shots/{shot['id']}/storyboards")
    assert r.status_code == 200, r.text
    return r.json()


def create(client, shot, asset_id, prompt=None):
    return post(
        client,
        f"/shots/{shot['id']}/storyboards",
        asset_id=asset_id,
        source_prompt_record_id=prompt["id"] if prompt else None,
    )


def test_import_versions_sources_selection_and_restart(client, settings):
    project, _, shot, template, p1 = setup(client)
    first_response = imported(client, shot, p1, notes="第一版")
    assert first_response.status_code == 201, first_response.text
    v1 = first_response.json()
    p2 = generated(client, shot, template)
    v2 = imported(client, shot, p2).json()
    assert [r["version"] for r in history(client, shot)] == [2, 1]
    assert v1["is_selected"] and v2["is_selected"]
    assert not history(client, shot)[1]["is_selected"]
    assert v1["source_prompt_record_id"] == p1["id"]
    assert v2["source_prompt_record_id"] == p2["id"]
    asset = client.get("/api/assets/" + v1["asset_id"]).json()
    assert [p["id"] for p in asset["projects"]] == [project["id"]]
    assert [s["id"] for s in asset["shots"]] == [shot["id"]]
    assert asset["asset_type"] == "STORYBOARD_6GRID"
    assert client.get("/api/assets/" + v1["asset_id"] + "/thumbnail").status_code == 200
    client.post("/api/prompts/" + p1["id"] + "/select")
    client.patch("/api/prompts/" + p1["id"], json={"edited_content": "人工修改"})
    changed = client.post("/api/storyboards/" + v1["id"] + "/select")
    assert changed.status_code == 200
    assert changed.json()["source_prompt"]["is_edited"]
    for key in ["id", "shot_id", "asset_id", "source_prompt_record_id", "version", "created_at"]:
        assert changed.json()[key] == v1[key]
    before = history(client, shot)
    assert sum(r["is_selected"] for r in before) == 1
    with TestClient(create_app(settings)) as restarted:
        assert history(restarted, shot) == before
        assert restarted.get("/api/assets/" + v1["asset_id"] + "/file").content == picture()


def test_reused_asset_independent_links_and_delete(client):
    project, _, shot, _, prompt = setup(client)
    asset = upload(client, asset_type="STORYBOARD_6GRID").json()
    for kind, owner in [("projects", project), ("shots", shot)]:
        post(client, f"/{kind}/{owner['id']}/assets", asset_id=asset["id"])
    before_files = files(client)
    v1 = create(client, shot, asset["id"], prompt)
    v2 = create(client, shot, asset["id"], prompt)
    assert files(client) == before_files
    with client.app.state.workspace.session() as session:
        for model in [ProjectAssetLink, ShotAssetLink]:
            assert (
                len(list(session.scalars(select(model).where(model.asset_id == UUID(asset["id"])))))
                == 1
            )
    assert client.delete("/api/storyboards/" + v1["id"]).status_code == 204
    assert history(client, shot) == [v2]
    detail = client.get("/api/assets/" + asset["id"]).json()
    assert len(detail["shots"]) == len(detail["projects"]) == 1
    assert client.delete(f"/api/shots/{shot['id']}/assets/{asset['id']}").status_code == 200
    assert client.delete(f"/api/projects/{project['id']}/assets/{asset['id']}").status_code == 200
    assert history(client, shot) == [v2]
    assert client.get("/api/assets/" + asset["id"] + "/file").status_code == 200
    response = client.delete("/api/assets/" + asset["id"])
    assert response.status_code == 409
    assert response.json()["code"] == "ASSET_IN_USE"
    assert "请先解除绑定" in response.json()["message"]
    assert response.json()["details"]["storyboards"] == 1
    assert (
        client.patch("/api/assets/" + asset["id"], json={"asset_type": "IMAGE"}).status_code == 409
    )
    assert client.delete("/api/storyboards/" + v2["id"]).status_code == 204
    assert history(client, shot) == []
    assert client.get("/api/assets/" + asset["id"]).status_code == 200
    assert client.delete("/api/assets/" + asset["id"]).status_code == 204
    assert client.post("/api/storyboards/" + v2["id"] + "/restore").status_code == 404
    assert files(client) == before_files
    post(client, "/assets/" + asset["id"] + "/restore")
    restored = post(client, "/storyboards/" + v2["id"] + "/restore")
    assert not restored["is_selected"]
    assert client.get("/api/assets/" + asset["id"]).json()["shots"] == []
    assert client.get("/api/assets/" + asset["id"]).json()["projects"] == []
    assert create(client, shot, asset["id"])["version"] == 3


def test_delete_selected_preserves_others_and_links(client):
    _, _, shot, _, prompt = setup(client)
    v1 = imported(client, shot, prompt).json()
    v2 = create(client, shot, v1["asset_id"])
    client.delete("/api/storyboards/" + v2["id"])
    remaining = history(client, shot)
    assert len(remaining) == 1 and not remaining[0]["is_selected"]
    detail = client.get("/api/assets/" + v1["asset_id"]).json()
    assert len(detail["shots"]) == len(detail["projects"]) == 1


@pytest.mark.parametrize("kind", ["IMAGE", "VIDEO", "OTHER", "missing", "deleted"])
def test_invalid_assets(client, kind):
    _, _, shot, _, prompt = setup(client)
    if kind == "missing":
        asset_id = str(uuid4())
    else:
        asset = upload(
            client,
            movie() if kind == "VIDEO" else picture(),
            "movie.mp4" if kind == "VIDEO" else "image.png",
            asset_type="STORYBOARD_6GRID" if kind == "deleted" else kind,
        ).json()
        asset_id = asset["id"]
        if kind == "deleted":
            client.delete("/api/assets/" + asset_id)
    response = client.post(
        f"/api/shots/{shot['id']}/storyboards",
        json={"asset_id": asset_id, "source_prompt_record_id": prompt["id"]},
    )
    assert response.status_code == (404 if kind in ["missing", "deleted"] else 422)
    assert history(client, shot) == []


@pytest.mark.parametrize(
    "case",
    [
        "missing-shot",
        "missing-prompt",
        "cross-shot",
        "cross-project",
        "deleted-shot",
        "deleted-project",
    ],
)
def test_invalid_relations_import_cleans_files_and_database(client, case):
    project, scene, shot, _, prompt = setup(client)
    target = shot
    if case == "missing-shot":
        target = {"id": str(uuid4())}
    if case == "missing-prompt":
        prompt = {"id": str(uuid4())}
    if case == "cross-shot":
        target = post(
            client,
            f"/scenes/{scene['id']}/shots",
            project_id=project["id"],
            shot_code="S14",
            title="Other",
        )
    if case == "cross-project":
        other = post(client, "/projects", name="Other")
        script = post(client, f"/projects/{other['id']}/scripts", name="Other")
        other_scene = post(
            client, f"/projects/{other['id']}/scenes", name="Other", script_id=script["id"]
        )
        target = post(
            client,
            f"/scenes/{other_scene['id']}/shots",
            project_id=other["id"],
            shot_code="S13",
            title="Other",
        )
    if case == "deleted-shot":
        client.delete("/api/shots/" + shot["id"])
    if case == "deleted-project":
        client.delete("/api/projects/" + project["id"])
    before = files(client)
    response = imported(client, target, prompt)
    assert response.status_code == (400 if case in ["cross-shot", "cross-project"] else 404), (
        response.text
    )
    assert files(client) == before
    with client.app.state.workspace.session() as session:
        for model in [Asset, Storyboard, ProjectAssetLink, ShotAssetLink]:
            assert list(session.scalars(select(model))) == []


@pytest.mark.parametrize(
    "point",
    ["after-asset", "after-project-link", "after-shot-link", "after-storyboard", "before-commit"],
)
def test_import_failure_compensation_restores_selection(client, point):
    _, _, shot, _, prompt = setup(client)
    v1 = imported(client, shot, prompt).json()
    before = history(client, shot)
    before_files = files(client)
    engine = client.app.state.workspace._database.engine
    table = {
        "after-asset": "assets",
        "after-project-link": "project_asset_links",
        "after-shot-link": "shot_asset_links",
        "after-storyboard": "storyboards",
    }.get(point)

    def fail_sql(conn, cursor, statement, parameters, context, executemany):
        if table and statement.startswith("INSERT INTO " + table + " "):
            raise OperationalError("synthetic", {}, Exception("injected"))

    def fail_commit(session):
        # Only the outer commit, after the nested creation savepoint has completed.
        if not session.in_nested_transaction():
            raise OperationalError("synthetic", {}, Exception("injected"))

    target, name, callback = (
        (Session, "before_commit", fail_commit)
        if point == "before-commit"
        else (engine, "after_cursor_execute", fail_sql)
    )
    event.listen(target, name, callback)
    try:
        response = imported(client, shot, prompt)
        assert response.status_code >= 400
    finally:
        event.remove(target, name, callback)
    assert files(client) == before_files
    assert history(client, shot) == before
    assert before[0]["id"] == v1["id"] and before[0]["is_selected"]
    with client.app.state.workspace.session() as session:
        for model in [Asset, Storyboard, ProjectAssetLink, ShotAssetLink]:
            assert len(list(session.scalars(select(model)))) == 1


@pytest.mark.parametrize("violation", ["version", "selected", "zero", "foreign-key", "type"])
def test_database_constraints_real_conflict(client, violation):
    _, _, shot, _, prompt = setup(client)
    v1 = imported(client, shot, prompt).json()
    fields = dict(
        shot_id=UUID(shot["id"]), asset_id=UUID(v1["asset_id"]), version=2, is_selected=False
    )
    fields.update(
        {"version": 1}
        if violation == "version"
        else {"is_selected": True}
        if violation == "selected"
        else {"version": 0}
        if violation == "zero"
        else {"asset_id": uuid4()}
        if violation == "foreign-key"
        else {"storyboard_type": "GRID_9"}
    )
    with pytest.raises(IntegrityError), client.app.state.workspace.session() as session:
        StoryboardRepository(session).add(Storyboard(**fields))
    assert history(client, shot) == [v1]


def test_concurrent_create_and_select(client):
    _, _, shot, _, prompt = setup(client)
    v1 = imported(client, shot, prompt).json()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: create(client, shot, v1["asset_id"], prompt), range(4)))
    assert sorted(r["version"] for r in results) == [2, 3, 4, 5]
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(
            pool.map(lambda r: client.post("/api/storyboards/" + r["id"] + "/select"), results)
        )
    assert all(r.status_code == 200 for r in responses)
    assert sum(r["is_selected"] for r in history(client, shot)) == 1


def test_distinct_connections_stale_allocation_conflicts(client):
    _, _, shot, _, prompt = setup(client)
    v1 = imported(client, shot, prompt).json()
    database = client.app.state.workspace._database
    # Two callers independently allocate the same next version; the DB rejects the loser.
    with database.SessionLocal() as one, database.SessionLocal() as two:
        version1 = StoryboardRepository(one).max_version(UUID(shot["id"])) + 1
        version2 = StoryboardRepository(two).max_version(UUID(shot["id"])) + 1
        assert version1 == version2 == 2
        one.rollback()
        two.rollback()
        StoryboardRepository(one).add(
            Storyboard(shot_id=UUID(shot["id"]), asset_id=UUID(v1["asset_id"]), version=version1)
        )
        one.commit()
        with pytest.raises(IntegrityError):
            StoryboardRepository(two).add(
                Storyboard(
                    shot_id=UUID(shot["id"]), asset_id=UUID(v1["asset_id"]), version=version2
                )
            )
        two.rollback()
    assert [r["version"] for r in history(client, shot)] == [2, 1]


def test_missing_endpoints_immutable_request_and_parent_restore(client):
    project, _, shot, _, prompt = setup(client)
    v1 = imported(client, shot, prompt).json()
    for suffix in ["", "/select", "/restore"]:
        response = (
            client.get("/api/storyboards/" + str(uuid4()))
            if not suffix
            else client.post("/api/storyboards/" + str(uuid4()) + suffix)
        )
        assert response.status_code == 404
    assert client.delete("/api/storyboards/" + str(uuid4())).status_code == 404
    assert (
        client.patch("/api/storyboards/" + v1["id"], json={"asset_id": str(uuid4())}).status_code
        == 405
    )
    response = client.post(
        f"/api/shots/{shot['id']}/storyboards", json={"asset_id": v1["asset_id"], "version": 42}
    )
    assert response.status_code == 422
    client.delete("/api/projects/" + project["id"])
    assert client.get("/api/storyboards/" + v1["id"]).status_code == 404
    post(client, "/projects/" + project["id"] + "/restore")
    assert history(client, shot) == [v1]


def test_populated_migration_preserves_every_old_table(client):
    _, _, shot, _, prompt = setup(client)
    asset = upload(client, asset_type="STORYBOARD_6GRID").json()
    database = client.app.state.workspace._database
    config = migration_config()
    with database.engine.begin() as conn:
        config.attributes["connection"] = conn
        command.downgrade(config, "0008_prompt_versioning")
        tables = set(inspect(conn).get_table_names()) - {"alembic_version"}
        before = {t: conn.exec_driver_sql(f'SELECT * FROM "{t}" ORDER BY id').all() for t in tables}
        command.upgrade(config, "head")
        command.check(config)
    # Exercise actual version creation without adding old-table convenience links.
    with database.session() as session:
        for version in [1, 2]:
            StoryboardRepository(session).add(
                Storyboard(
                    shot_id=UUID(shot["id"]),
                    asset_id=UUID(asset["id"]),
                    source_prompt_record_id=UUID(prompt["id"]),
                    version=version,
                    is_selected=version == 2,
                )
            )
    with database.engine.begin() as conn:
        config.attributes["connection"] = conn
        command.downgrade(config, "0008_prompt_versioning")
        assert "storyboards" not in inspect(conn).get_table_names()
        assert {
            t: conn.exec_driver_sql(f'SELECT * FROM "{t}" ORDER BY id').all() for t in tables
        } == before
        command.upgrade(config, "head")
        command.check(config)
        assert conn.exec_driver_sql("select count(*) from storyboards").scalar() == 0
        assert conn.exec_driver_sql("pragma integrity_check").scalar() == "ok"
        assert conn.exec_driver_sql("pragma foreign_key_check").all() == []
