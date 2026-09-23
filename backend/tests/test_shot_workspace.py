from uuid import UUID, uuid4

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from test_characters import asset, post, setup

from app.core.database import Database, migration_config
from app.main import create_app
from app.models.characters import ShotCharacterStateLink
from app.services.characters import CharacterService


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as value:
        yield value


FIELDS = ("main_action", "key_constraints", "negative_constraints", "free_notes")


@pytest.mark.parametrize("field", FIELDS)
def test_structured_create_update_clear_and_legacy(client, field):
    p, _, scene, _, _, _, _ = setup(client)
    shot = post(
        client,
        f"/scenes/{scene['id']}/shots",
        {
            "project_id": p["id"],
            "shot_code": "S9",
            "title": "Action",
            field: "first\nsecond",
            "creative_requirement": "preserve legacy",
        },
    )
    assert shot[field] == "first\nsecond"
    path = f"/api/shots/{shot['id']}"
    for value in ["updated", "", None]:
        response = client.patch(path, json={field: value})
        assert response.status_code == 200
        assert response.json()[field] == value
        assert response.json()["creative_requirement"] == "preserve legacy"
    assert client.patch(path, json={"title": None}).status_code == 422


def test_workspace_full_context_and_single_patch(client):
    _, _, scene, shot, character, state, _ = setup(client)
    media = asset(client)
    for path in [
        f"/shots/{shot['id']}",
        f"/characters/{character['id']}",
        f"/character-states/{state['id']}",
    ]:
        post(client, path + "/assets", {"asset_id": media["id"]})
    post(client, f"/shots/{shot['id']}/character-states", {"character_state_id": state["id"]})
    client.patch(
        f"/api/scenes/{scene['id']}",
        json={"fixed_constraints": "fixed", "negative_constraints": "scene negative"},
    )
    payload = {key: key + " text" for key in FIELDS}
    payload.update(
        title="Production", description="brief", duration_seconds=10, status="ASSET_PREPARING"
    )
    assert client.patch(f"/api/shots/{shot['id']}", json=payload).status_code == 200
    data = client.get(f"/api/shots/{shot['id']}/workspace").json()
    assert all(data["shot"][key] == value for key, value in payload.items())
    assert data["scene"]["fixed_constraints"] == "fixed"
    assert data["scene"]["negative_constraints"] == "scene negative"
    assert data["assets"][0]["id"] == media["id"]
    context = data["character_states"][0]
    assert context["character_name"] == character["name"]
    assert context["character_description"] == "长期身份"
    assert context["assets"][0]["id"] == context["character_assets"][0]["id"] == media["id"]


def test_navigation_project_scene_order_not_code(client):
    p, script, scene, first, _, _, _ = setup(client)
    second = post(
        client,
        f"/scenes/{scene['id']}/shots",
        {"project_id": p["id"], "shot_code": "S9", "title": "Second"},
    )
    other_scene = post(
        client, f"/projects/{p['id']}/scenes", {"script_id": script["id"], "name": "Later"}
    )
    last = post(
        client,
        f"/scenes/{other_scene['id']}/shots",
        {"project_id": p["id"], "shot_code": "S10", "title": "Last"},
    )
    setup(client, "other project")

    def workspace(s):
        return client.get(f"/api/shots/{s['id']}/workspace").json()

    assert workspace(first)["previous_shot"] is None
    assert workspace(first)["next_shot"]["id"] == second["id"]
    assert workspace(last)["next_shot"] is None
    assert workspace(last)["previous_shot"]["id"] == second["id"]
    assert workspace(last)["total"] == 3
    post(client, f"/shots/{second['id']}/move", {"direction": "up"})
    assert workspace(second)["position"] == 1
    assert workspace(second)["next_shot"]["id"] == first["id"]
    client.delete(f"/api/shots/{first['id']}")
    assert workspace(second)["next_shot"]["id"] == last["id"]


def test_atomic_replace_idempotence_and_isolation(client):
    _, _, _, shot, _, a, b = setup(client)
    _, _, _, _, _, foreign, _ = setup(client, "foreign")
    path = f"/api/shots/{shot['id']}/character-states"
    post(client, path.removeprefix("/api"), {"character_state_id": a["id"]})
    assert client.put(path, json={"character_state_id": foreign["id"]}).status_code == 400
    assert client.get(path).json()[0]["id"] == a["id"]
    for state in [b, b, a]:
        response = client.put(path, json={"character_state_id": state["id"]})
        assert response.status_code == 200
        assert [item["id"] for item in response.json()] == [state["id"]]
    assert client.get(f"/api/shots/{uuid4()}/workspace").status_code == 404


def test_replace_rolls_back_on_bind_failure(client, monkeypatch):
    _, _, _, shot, _, a, b = setup(client)
    post(client, f"/shots/{shot['id']}/character-states", {"character_state_id": a["id"]})

    def fail(*args, **kwargs):
        raise RuntimeError("injected failure")

    with client.app.state.workspace.session() as session:
        service = CharacterService(session)
        monkeypatch.setattr(service, "bind_shot", fail)
        with pytest.raises(RuntimeError):
            service.replace_shot_state(UUID(shot["id"]), UUID(b["id"]))
        active = service.shot_links.matching(shot_id=UUID(shot["id"]))
        assert len(active) == 1 and active[0].character_state_id == UUID(a["id"])


def test_workspace_rejects_corrupt_cross_project_relation(client):
    _, _, _, shot, _, _, _ = setup(client)
    _, _, _, _, character, state, _ = setup(client, "foreign")
    with client.app.state.workspace.session() as session:
        session.add(
            ShotCharacterStateLink(
                shot_id=UUID(shot["id"]),
                character_id=UUID(character["id"]),
                character_state_id=UUID(state["id"]),
            )
        )
    assert client.get(f"/api/shots/{shot['id']}/workspace").status_code == 400


@pytest.mark.parametrize("owner", ["shots", "scenes"])
def test_workspace_deleted_owner_returns_friendly_error(client, owner):
    _, _, scene, shot, _, state, _ = setup(client)
    post(client, f"/shots/{shot['id']}/character-states", {"character_state_id": state["id"]})
    identifier = shot["id"] if owner == "shots" else scene["id"]
    assert client.delete(f"/api/{owner}/{identifier}").status_code == 204
    response = client.get(f"/api/shots/{shot['id']}/workspace")
    assert response.status_code == 404
    assert "message" in response.json()


def test_populated_phase5_migration_preserves_all_old_columns(client):
    _, _, _, shot, character, state, _ = setup(client)
    media = asset(client)
    post(client, f"/shots/{shot['id']}/assets", {"asset_id": media["id"]})
    post(client, f"/characters/{character['id']}/assets", {"asset_id": media["id"]})
    post(client, f"/shots/{shot['id']}/character-states", {"character_state_id": state["id"]})
    client.patch(
        f"/api/shots/{shot['id']}", json={"creative_requirement": "legacy", "main_action": "new"}
    )
    database = Database(client.app.state.workspace.get_database_path())
    try:
        with database.engine.begin() as conn:
            config = migration_config()
            config.attributes["connection"] = conn
            before = {}
            for table in inspect(conn).get_table_names():
                if table == "alembic_version":
                    continue
                columns = [
                    c["name"]
                    for c in inspect(conn).get_columns(table)
                    if not (table == "shots" and c["name"] in FIELDS)
                ]
                sql = f"SELECT {', '.join(columns)} FROM {table} ORDER BY id"
                before[sql] = conn.exec_driver_sql(sql).all()
            command.downgrade(config, "0004_characters")
            command.upgrade(config, "head")
            command.check(config)
            for sql, rows in before.items():
                assert conn.exec_driver_sql(sql).all() == rows
            assert conn.exec_driver_sql("PRAGMA foreign_key_check").all() == []
            assert conn.exec_driver_sql("SELECT main_action FROM shots").scalar() is None
    finally:
        database.dispose()


def test_requirements_survive_application_restart(settings):
    with TestClient(create_app(settings)) as client:
        _, _, _, shot, _, _, _ = setup(client)
        payload = {key: "persist " + key for key in FIELDS}
        client.patch(f"/api/shots/{shot['id']}", json=payload)
    with TestClient(create_app(settings)) as client:
        data = client.get(f"/api/shots/{shot['id']}/workspace").json()
        assert all(data["shot"][k] == v for k, v in payload.items())
