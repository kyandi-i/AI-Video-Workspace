import io
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

import pytest
from alembic import command
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import Database, migration_config
from app.main import create_app
from app.models.characters import ShotCharacterStateLink


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as value:
        yield value


def post(client, url, data):
    response = client.post("/api" + url, json=data)
    assert response.status_code in (200, 201), response.text
    return response.json()


def setup(client, suffix=""):
    p = post(client, "/projects", {"name": "SPF" + suffix})
    script = post(client, f"/projects/{p['id']}/scripts", {"name": "培训"})
    scene = post(client, f"/projects/{p['id']}/scenes", {"name": "风淋", "script_id": script["id"]})
    shot = post(
        client,
        f"/scenes/{scene['id']}/shots",
        {"project_id": p["id"], "shot_code": "S13", "title": "风淋"},
    )
    c = post(
        client, f"/projects/{p['id']}/characters", {"name": "女员工", "description": "长期身份"}
    )
    a = post(client, f"/characters/{c['id']}/states", {"name": "基础状态"})
    b = post(client, f"/characters/{c['id']}/states", {"name": "黄色 PPE + 双层手套"})
    return p, script, scene, shot, c, a, b


def asset(client, asset_type="IMAGE"):
    buffer = io.BytesIO()
    Image.new("RGB", (16, 16)).save(buffer, format="PNG")
    response = client.post(
        "/api/assets/upload",
        params={"filename": "reference.png", "asset_type": asset_type},
        content=buffer.getvalue(),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 201
    return response.json()


def test_character_crud_scope_search_restore(client):
    p, _, _, _, c, a, b = setup(client)
    assert UUID(c["id"])
    path = f"/api/characters/{c['id']}"
    assert client.get(path).json()["state_count"] == 2
    response = client.patch(path, json={"name": " 员工 ", "notes": "固定脸部"})
    assert response.json()["name"] == "员工"
    assert client.patch(path, json={"notes": None}).json()["notes"] is None
    assert (
        len(client.get(f"/api/projects/{p['id']}/characters", params={"search": "长期"}).json())
        == 1
    )
    assert client.get(f"/api/projects/{p['id']}/characters", params={"search": "%"}).json() == []
    p2 = post(client, "/projects", {"name": "other"})
    assert client.get(f"/api/projects/{p2['id']}/characters").json() == []
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    assert client.get(path, params={"include_deleted": True}).json()["deleted_at"]
    assert client.post(path + "/restore").json()["state_count"] == 2
    assert [s["id"] for s in client.get(path + "/states").json()] == [a["id"], b["id"]]


@pytest.mark.parametrize("kind", ["character", "state"])
def test_names_unique_in_scope_including_deleted(client, kind):
    p, _, _, _, c, a, _ = setup(client)
    url = (
        f"/projects/{p['id']}/characters"
        if kind == "character"
        else f"/characters/{c['id']}/states"
    )
    entity = c if kind == "character" else a
    path = f"/api/{'characters' if kind == 'character' else 'character-states'}/{entity['id']}"
    code = "CHARACTER_NAME_CONFLICT" if kind == "character" else "CHARACTER_STATE_NAME_CONFLICT"
    assert client.post("/api" + url, json={"name": entity["name"]}).json()["code"] == code
    assert client.delete(path).status_code == 204
    assert client.post("/api" + url, json={"name": entity["name"]}).json()["code"] == code
    assert client.post(path + "/restore").status_code == 200
    # Same name in a different owning scope is valid.
    p2 = post(client, "/projects", {"name": "other"})
    c2 = post(client, f"/projects/{p2['id']}/characters", {"name": c["name"]})
    post(client, f"/characters/{c2['id']}/states", {"name": a["name"]})


def test_state_crud_order_and_restore_at_end(client):
    _, _, _, _, c, a, b = setup(client)
    path = f"/api/character-states/{a['id']}"
    assert client.patch(path, json={"description": "白色短袖"}).json()["description"] == "白色短袖"
    assert client.get(path).json()["character_id"] == c["id"]
    assert (
        client.patch(path, json={"name": b["name"]}).json()["code"]
        == "CHARACTER_STATE_NAME_CONFLICT"
    )
    moved = client.post(path + "/move", json={"direction": "down"}).json()
    assert [s["id"] for s in moved] == [b["id"], a["id"]]
    assert [s["order_index"] for s in moved] == [0, 1]
    assert client.post(path + "/move", json={"direction": "down"}).json() == moved
    assert client.post(path + "/move", json={"direction": "wrong"}).status_code == 422
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    assert client.get(f"/api/characters/{c['id']}/states").json()[0]["order_index"] == 0
    assert client.post(path + "/restore").json()["order_index"] == 1


@pytest.mark.parametrize("kind", ["characters", "character-states"])
@pytest.mark.parametrize("asset_type", ["IMAGE", "OTHER", "STORYBOARD_6GRID"])
def test_asset_bind_unbind_and_usage_protection(client, kind, asset_type):
    _, _, _, _, c, a, _ = setup(client)
    item = c if kind == "characters" else a
    media = asset(client, asset_type)
    path = f"/api/{kind}/{item['id']}/assets"
    for _ in range(2):
        response = client.post(path, json={"asset_id": media["id"]})
        assert len(response.json()["assets"]) == 1
    detail = client.get(f"/api/assets/{media['id']}").json()
    field = "characters" if kind == "characters" else "character_states"
    assert detail[field][0]["id"] == item["id"]
    blocked = client.delete(f"/api/assets/{media['id']}")
    assert blocked.status_code == 409 and blocked.json()["details"][field] == 1
    assert client.delete(path + "/" + media["id"]).status_code == 200
    assert client.delete(f"/api/assets/{media['id']}").status_code == 204
    assert client.post(path, json={"asset_id": media["id"]}).status_code == 404
    assert client.post(f"/api/assets/{media['id']}/restore").status_code == 200
    assert len(client.post(path, json={"asset_id": media["id"]}).json()["assets"]) == 1


def test_shot_conflicts_multiple_characters_project_and_usage(client):
    p, _, _, shot, c, a, b = setup(client)
    path = f"/api/shots/{shot['id']}/character-states"
    for _ in range(2):
        assert len(client.post(path, json={"character_state_id": a["id"]}).json()) == 1
    blocked = client.post(path, json={"character_state_id": b["id"]})
    assert blocked.status_code == 409 and blocked.json()["code"] == "SHOT_CHARACTER_STATE_CONFLICT"
    used = client.delete(f"/api/character-states/{a['id']}")
    assert used.json()["code"] == "CHARACTER_STATE_IN_USE" and used.json()["details"]["shots"] == 1
    c2 = post(client, f"/projects/{p['id']}/characters", {"name": "主管"})
    s2 = post(client, f"/characters/{c2['id']}/states", {"name": "基础"})
    assert len(client.post(path, json={"character_state_id": s2["id"]}).json()) == 2
    *_, foreign, _ = setup(client, "other")
    assert (
        client.post(path, json={"character_state_id": foreign["id"]}).json()["code"]
        == "INVALID_PROJECT_RELATION"
    )
    assert client.delete(path + "/" + a["id"]).status_code == 200
    assert len(client.post(path, json={"character_state_id": b["id"]}).json()) == 2
    assert client.delete(f"/api/character-states/{a['id']}").status_code == 204
    assert client.post(path, json={"character_state_id": a["id"]}).status_code == 404


@pytest.mark.parametrize("owner", ["characters", "projects", "scripts", "scenes", "shots"])
def test_delete_lifecycle_has_no_active_orphans(client, owner):
    p, script, scene, shot, c, a, b = setup(client)
    media = asset(client)
    post(client, f"/characters/{c['id']}/assets", {"asset_id": media["id"]})
    post(client, f"/character-states/{b['id']}/assets", {"asset_id": media["id"]})
    post(client, f"/shots/{shot['id']}/character-states", {"character_state_id": b["id"]})
    client.delete(f"/api/character-states/{a['id']}")
    entity = {"characters": c, "projects": p, "scripts": script, "scenes": scene, "shots": shot}[
        owner
    ]
    path = f"/api/{owner}/{entity['id']}"
    assert client.delete(path).status_code == 204
    with client.app.state.workspace.session() as session:
        assert (
            list(
                session.scalars(
                    select(ShotCharacterStateLink).where(
                        ShotCharacterStateLink.deleted_at.is_(None)
                    )
                )
            )
            == []
        )
    assert client.post(path + "/restore").status_code == 200
    assert client.get(f"/api/shots/{shot['id']}/character-states").json() == []
    assert client.get(f"/api/character-states/{a['id']}").status_code == 404
    assert client.get(f"/api/character-states/{b['id']}").status_code == 200
    if owner in ("characters", "projects"):
        assert client.get(f"/api/characters/{c['id']}").json()["assets"] == []
        assert client.get(f"/api/character-states/{b['id']}").json()["assets"] == []
        assert client.delete(f"/api/assets/{media['id']}").status_code == 204
    else:
        assert client.delete(f"/api/assets/{media['id']}").status_code == 409


def test_restore_requires_active_parent(client):
    p, _, _, _, c, a, _ = setup(client)
    client.delete(f"/api/projects/{p['id']}")
    assert client.post(f"/api/characters/{c['id']}/restore").status_code == 404
    assert client.post(f"/api/character-states/{a['id']}/restore").status_code == 404


@pytest.mark.parametrize(
    "payload", [{"name": "  "}, {"name": None}, {"description": None}, {"project_id": "bad"}]
)
def test_validation_does_not_leak_database_errors(client, payload):
    _, _, _, _, c, _, _ = setup(client)
    response = client.patch(f"/api/characters/{c['id']}", json=payload)
    assert response.status_code == 422
    assert set(response.json()) == {"code", "message", "details"}


def test_concurrent_binding_and_db_unique_constraint(client):
    _, _, _, shot, c, a, b = setup(client)
    url = f"/api/shots/{shot['id']}/character-states"
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda state: client.post(url, json={"character_state_id": state["id"]}), [a, b]
            )
        )
    assert sorted(r.status_code for r in responses) == [200, 409]
    selected = client.get(url).json()[0]
    other = b if selected["id"] == a["id"] else a
    with pytest.raises(IntegrityError), client.app.state.workspace.session() as session:
        session.add(
            ShotCharacterStateLink(
                shot_id=UUID(shot["id"]),
                character_id=UUID(c["id"]),
                character_state_id=UUID(other["id"]),
            )
        )
        session.flush()


def test_spf_six_states_and_restart_persistence(settings):
    with TestClient(create_app(settings)) as client:
        p, _, _, shot, c, _, b = setup(client)
        for name in ["发帽 + 口罩", "黄色 PPE", "黄色 PPE + 第一层手套", "退出状态"]:
            post(client, f"/characters/{c['id']}/states", {"name": name})
        media = asset(client)
        post(client, f"/character-states/{b['id']}/assets", {"asset_id": media["id"]})
        post(client, f"/shots/{shot['id']}/character-states", {"character_state_id": b["id"]})
    with TestClient(create_app(settings)) as client:
        assert len(client.get(f"/api/characters/{c['id']}/states").json()) == 6
        bound = client.get(f"/api/shots/{shot['id']}/character-states").json()
        assert bound[0]["id"] == b["id"] and bound[0]["assets"][0]["id"] == media["id"]
        assert str(client.app.state.workspace.get_workspace_root()) != "D:\\AI-Video-Workspace"


def test_populated_phase4_migration_roundtrip(client):
    p, _, _, shot, _, _, _ = setup(client)
    media = asset(client)
    post(client, f"/projects/{p['id']}/assets", {"asset_id": media["id"]})
    post(client, f"/shots/{shot['id']}/assets", {"asset_id": media["id"]})
    database = Database(client.app.state.workspace.get_database_path())
    config = migration_config()
    with database.engine.begin() as conn:
        config.attributes["connection"] = conn
        before = {
            table: conn.exec_driver_sql(f"SELECT * FROM {table}").all()
            for table in [
                "projects",
                "scripts",
                "script_nodes",
                "scenes",
                "shots",
                "assets",
                "project_asset_links",
                "shot_asset_links",
            ]
        }
        command.downgrade(config, "0003_asset_library")
        command.upgrade(config, "head")
        command.check(config)
        for table, rows in before.items():
            assert conn.exec_driver_sql(f"SELECT * FROM {table}").all() == rows
        assert conn.exec_driver_sql("PRAGMA foreign_key_check").all() == []
