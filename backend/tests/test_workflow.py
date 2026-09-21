from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppError
from app.main import create_app
from app.models.workflow import NodeType, Scene
from app.repositories.workflow import SceneRepository, ScriptNodeRepository
from app.schemas.workflow import ProjectCreate, SceneCreate, ScriptCreate, ShotCreate
from app.services.workflow import ProjectService, SceneService, ScriptService, ShotService


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        yield client


def create_tree(client, suffix=""):
    project = client.post("/api/projects", json={"name": f"  Project{suffix}  "}).json()
    script = client.post(f"/api/projects/{project['id']}/scripts", json={"name": "Script"}).json()
    scene = client.post(
        f"/api/projects/{project['id']}/scenes",
        json={
            "script_id": script["id"],
            "name": "Scene",
            "fixed_constraints": "Door left",
        },
    ).json()
    return project, script, scene


def add_shot(client, project, scene, code="S01", **fields):
    return client.post(
        f"/api/scenes/{scene['id']}/shots",
        json={
            "project_id": project["id"],
            "shot_code": code,
            "title": "Opening",
            **fields,
        },
    )


def test_full_crud_and_persistence(client):
    project, script, scene = create_tree(client)
    assert project["name"] == "Project"
    assert script["project_id"] == project["id"]
    assert scene["script_id"] == script["id"]
    assert UUID(scene["script_node_id"])
    shot = add_shot(client, project, scene).json()
    for resource, entity, field in [
        ("projects", project, "name"),
        ("scripts", script, "name"),
        ("scenes", scene, "name"),
        ("shots", shot, "title"),
    ]:
        path = f"/api/{resource}/{entity['id']}"
        assert client.get(path).status_code == 200
        response = client.patch(path, json={field: "Edited"})
        assert response.status_code == 200, response.text
        assert client.get(path).json()[field] == "Edited"
    assert client.get(f"/api/projects/{project['id']}/stats").json() == {
        "scripts": 1,
        "scenes": 1,
        "shots": 1,
    }
    assert client.get(f"/api/projects/{project['id']}/scenes").json()[0]["shot_count"] == 1
    # Delete leaves physical records intact and hides all descendants.
    assert client.delete(f"/api/projects/{project['id']}").status_code == 204
    assert client.get("/api/projects").json() == []
    for resource, entity in [
        ("projects", project),
        ("scripts", script),
        ("scenes", scene),
        ("shots", shot),
    ]:
        path = f"/api/{resource}/{entity['id']}"
        assert client.get(path).status_code == 404
        assert client.get(path + "?include_deleted=true").json()["deleted_at"]
    assert client.post(f"/api/projects/{project['id']}/restore").status_code == 200
    assert client.get(f"/api/shots/{shot['id']}").status_code == 200


@pytest.mark.parametrize("resource", ["projects", "scripts", "scenes", "shots"])
def test_not_found(client, resource):
    path = f"/api/{resource}/{uuid4()}"
    for response in [client.get(path), client.patch(path, json={}), client.delete(path)]:
        assert response.status_code == 404
        assert response.json()["code"] == resource[:-1].upper() + "_NOT_FOUND"


def test_shot_conflicts_validation_filter_and_move(client):
    project, _, scene = create_tree(client)
    other_project, _, other_scene = create_tree(client, "other")
    a = add_shot(client, project, scene, "S01").json()
    b = add_shot(client, project, scene, "S02", status="DONE").json()
    assert add_shot(client, other_project, other_scene).status_code == 201
    assert add_shot(client, project, scene).status_code == 409
    assert (
        add_shot(client, other_project, scene, "S03").json()["code"] == "INVALID_PROJECT_RELATION"
    )
    for fields in [
        {"duration_seconds": -1},
        {"shot_code": " "},
        {"title": " "},
        {"status": "BAD"},
        {"order_index": -1},
    ]:
        assert add_shot(client, project, scene, "S03", **fields).status_code == 422
    assert client.patch(f"/api/shots/{b['id']}", json={"shot_code": "S01"}).status_code == 409
    result = client.post(f"/api/shots/{b['id']}/move", json={"direction": "up"}).json()
    assert [s["id"] for s in result] == [b["id"], a["id"]]
    assert [s["order_index"] for s in result] == [0, 1]
    assert client.post(f"/api/shots/{b['id']}/move", json={"direction": "up"}).json() == result
    result = client.post(f"/api/shots/{b['id']}/move", json={"direction": "down"}).json()
    assert [s["id"] for s in result] == [a["id"], b["id"]]
    path = f"/api/projects/{project['id']}/shots"
    assert (
        len(
            client.get(
                path, params={"status": "DONE", "search": "s02", "scene_id": scene["id"]}
            ).json()
        )
        == 1
    )
    assert client.get(path, params={"search": "%"}).json() == []
    assert client.delete(f"/api/shots/{a['id']}").status_code == 204
    assert client.get(f"/api/scenes/{scene['id']}/shots").json()[0]["order_index"] == 0
    assert add_shot(client, project, scene).status_code == 409
    assert client.post(f"/api/shots/{a['id']}/restore").json()["order_index"] == 1


@pytest.mark.parametrize("resource", ["scripts", "scenes"])
def test_parent_delete_restore_preserves_individually_deleted_shots(client, resource):
    project, script, scene = create_tree(client)
    a = add_shot(client, project, scene, "S01").json()
    b = add_shot(client, project, scene, "S02").json()
    client.delete(f"/api/shots/{a['id']}")
    parent = script if resource == "scripts" else scene
    path = f"/api/{resource}/{parent['id']}"
    assert client.delete(path).status_code == 204
    assert client.get(f"/api/shots/{b['id']}").status_code == 404
    assert client.post(f"/api/shots/{b['id']}/restore").status_code == 404
    assert client.post(path + "/restore").status_code == 200
    shots = client.get(f"/api/scenes/{scene['id']}/shots").json()
    assert [s["id"] for s in shots] == [b["id"]]
    assert shots[0]["order_index"] == 0


@pytest.mark.parametrize("body", [{"name": " "}, {"name": None}, {"name": "ok", "status": "BAD"}])
def test_invalid_project(client, body):
    assert client.post("/api/projects", json=body).status_code == 422


def test_null_patch_and_cross_project_scene(client):
    project, script, _ = create_tree(client)
    other, _, _ = create_tree(client, "other")
    assert client.patch(f"/api/projects/{project['id']}", json={"name": None}).status_code == 422
    response = client.post(
        f"/api/projects/{other['id']}/scenes", json={"script_id": script["id"], "name": "Wrong"}
    )
    assert response.json()["code"] == "INVALID_PROJECT_RELATION"


def test_scene_atomicity_unique_node_and_delete(workspace, monkeypatch):
    with workspace.session() as session:
        project = ProjectService(session).create_project(ProjectCreate(name="Project"))
        script = ScriptService(session).create_script(project.id, ScriptCreate(name="Script"))
        service = SceneService(session)
        data = SceneCreate(script_id=script.id, name="Scene")
        original = SceneRepository.add

        def fail_after_node(*args):
            raise RuntimeError("injected scene failure")

        monkeypatch.setattr(SceneRepository, "add", fail_after_node)
        with pytest.raises(RuntimeError):
            service.create_scene(project.id, data)
        assert ScriptNodeRepository(session).matching() == []
        monkeypatch.setattr(SceneRepository, "add", original)
        scene = service.create_scene(project.id, data)
        node = ScriptNodeRepository(session).get(scene.script_node_id)
        assert node.node_type == NodeType.SCENE and node.parent_id is None
        assert node.title == ""  # Scene owns the name; no shadow copy.
        with pytest.raises(IntegrityError), session.begin_nested():
            SceneRepository(session).add(
                Scene(project_id=project.id, script_node_id=node.id, name="Duplicate")
            )
        service.delete_scene(scene.id)
        assert ScriptNodeRepository(session).get(node.id) is None
        assert node.deleted_at is not None
        service.restore_scene(scene.id)
        assert ScriptNodeRepository(session).get(node.id) is node


def test_service_relations_and_duration(workspace):
    with workspace.session() as session:
        a = ProjectService(session).create_project(ProjectCreate(name="A"))
        b = ProjectService(session).create_project(ProjectCreate(name="B"))
        script = ScriptService(session).create_script(a.id, ScriptCreate(name="Script"))
        with pytest.raises(AppError, match="不属于"):
            SceneService(session).create_scene(b.id, SceneCreate(script_id=script.id, name="Bad"))
        scene = SceneService(session).create_scene(
            a.id, SceneCreate(script_id=script.id, name="Scene")
        )
        with pytest.raises(AppError, match="不属于"):
            ShotService(session).create_shot(
                scene.id, ShotCreate(project_id=b.id, shot_code="S01", title="Title")
            )
        with pytest.raises(ValidationError):
            ShotCreate(project_id=a.id, shot_code="S01", title="Title", duration_seconds=-1)


def test_concurrent_creates_keep_order_and_unique_codes(client):
    project, _, scene = create_tree(client)
    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(
            executor.map(lambda index: add_shot(client, project, scene, f"S{index:02}"), range(8))
        )
    assert all(response.status_code == 201 for response in responses)
    shots = client.get(f"/api/scenes/{scene['id']}/shots").json()
    assert [shot["order_index"] for shot in shots] == list(range(8))
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(lambda _: add_shot(client, project, scene, "CONFLICT"), range(2))
        )
    assert sorted(response.status_code for response in responses) == [201, 409]


def test_data_persists_across_service_restart(settings):
    with TestClient(create_app(settings)) as client:
        project, _, scene = create_tree(client)
        shot = add_shot(client, project, scene).json()
    with TestClient(create_app(settings)) as client:
        assert client.get(f"/api/shots/{shot['id']}").json() == shot
        assert client.get(f"/api/projects/{project['id']}/stats").json() == {
            "scripts": 1,
            "scenes": 1,
            "shots": 1,
        }


def test_scene_service_rejects_invalid_node_type_and_project(workspace):
    with workspace.session() as session:
        service = SceneService(session)
        project = ProjectService(session).create_project(ProjectCreate(name="Project"))
        other = ProjectService(session).create_project(ProjectCreate(name="Other"))
        script = ScriptService(session).create_script(project.id, ScriptCreate(name="Script"))
        scene = service.create_scene(project.id, SceneCreate(script_id=script.id, name="Scene"))
        node = service.nodes.get(scene.script_node_id)
        service.nodes.update(node, node_type=NodeType.OTHER)
        with pytest.raises(AppError) as error:
            service.scene(scene.id)
        assert error.value.code == "INVALID_PROJECT_RELATION"
        service.nodes.update(node, node_type=NodeType.SCENE)
        entity = service.scenes.get(scene.id)
        service.scenes.update(entity, project_id=other.id)
        with pytest.raises(AppError) as error:
            service.scene(scene.id)
        assert error.value.code == "INVALID_PROJECT_RELATION"


def test_scene_order_is_node_owned_and_contiguous_after_delete_restore(client):
    project, script, first = create_tree(client)
    second = client.post(
        f"/api/projects/{project['id']}/scenes", json={"script_id": script["id"], "name": "Second"}
    ).json()
    assert second["order_index"] == 1
    client.delete(f"/api/scenes/{first['id']}")
    assert client.get(f"/api/scenes/{second['id']}").json()["order_index"] == 0
    assert client.post(f"/api/scenes/{first['id']}/restore").json()["order_index"] == 1
    assert client.post(f"/api/scenes/{first['id']}/restore").json()["order_index"] == 1


def test_coarse_clock_does_not_restore_previously_deleted_children(client, monkeypatch):
    from datetime import UTC, datetime

    monkeypatch.setattr("app.services.workflow.utc_now", lambda: datetime(2026, 1, 1, tzinfo=UTC))
    project, _, scene = create_tree(client)
    shot = add_shot(client, project, scene).json()
    client.delete(f"/api/shots/{shot['id']}")
    client.delete(f"/api/scenes/{scene['id']}")
    client.post(f"/api/scenes/{scene['id']}/restore")
    assert client.get(f"/api/scenes/{scene['id']}/shots").json() == []
    assert client.get(f"/api/shots/{shot['id']}").status_code == 404
