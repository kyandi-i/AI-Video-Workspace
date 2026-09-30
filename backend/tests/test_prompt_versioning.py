from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import event, inspect
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from test_ai import configure, operation, post, preview, seed

from app.core.database import migration_config
from app.core.exceptions import AppError
from app.main import create_app
from app.models.prompts import PromptRecord
from app.repositories.prompts import PromptRepository
from test_support.fake_ai import FakeAIProvider


@pytest.fixture
def client(settings):
    app = create_app(settings)
    app.state.ai_provider = FakeAIProvider()
    with TestClient(app) as instance:
        yield instance


def generated(client, shot, template):
    return post(
        client, f"/shots/{shot['id']}/prompts/generate", **operation(client, shot, template)
    )


def history(client, shot):
    response = client.get(f"/api/shots/{shot['id']}/prompts")
    assert response.status_code == 200
    return response.json()


def setup(client):
    project, scene, shot, template = seed(client)
    configure(client)
    return project, scene, shot, template, generated(client, shot, template)


FACTS = (
    "id",
    "shot_id",
    "template_id",
    "template_name",
    "template_content",
    "prompt_type",
    "context_json",
    "rendered_input",
    "input_hash",
    "generated_content",
    "provider",
    "model_name",
    "created_at",
    "version",
)


@pytest.mark.parametrize(
    "content",
    ["中文，全文标点！\n第二行", "", "  \n ", "长文本\n" * 20000, None],
    ids=["chinese", "empty", "whitespace", "long", "reset"],
)
def test_edit_preserves_generation_facts_and_restart(client, settings, content):
    _, _, shot, _, first = setup(client)
    response = client.patch("/api/prompts/" + first["id"], json={"edited_content": content})
    assert response.status_code == 200, response.text
    edited = response.json()
    assert {k: first[k] for k in FACTS} == {k: edited[k] for k in FACTS}
    assert edited["effective_content"] == (
        content if content is not None else first["generated_content"]
    )
    with TestClient(create_app(settings)) as restarted:
        assert history(restarted, shot) == [edited]


@pytest.mark.parametrize(
    "field",
    [
        "generated_content",
        "context_json",
        "template_content",
        "rendered_input",
        "input_hash",
        "provider",
        "model_name",
        "created_at",
        "version",
        "is_selected",
    ],
)
def test_edit_cannot_overwrite_facts_or_selection(client, field):
    _, _, shot, _, first = setup(client)
    response = client.patch(
        "/api/prompts/" + first["id"], json={"edited_content": "edit", field: "forbidden"}
    )
    assert response.status_code == 422
    assert history(client, shot) == [first]
    with client.app.state.workspace.session() as session:
        if field != "is_selected":
            with pytest.raises(AppError):
                PromptRepository(session).update(
                    session.get(PromptRecord, UUID(first["id"])), **{field: "forbidden"}
                )


def test_regenerate_fresh_snapshots_model_selection_and_retry(client):
    _, _, shot, template, first = setup(client)
    assert first["version"] == 1 and first["is_selected"]
    client.patch(
        "/api/prompts/" + first["id"], json={"edited_content": "人工编辑绝不作为 AI 上下文"}
    )
    client.patch("/api/shots/" + shot["id"], json={"main_action": "新的镜头动作"})
    client.patch(
        "/api/prompt-templates/" + template["id"],
        json={"template_content": "新模板 {{main_action}}"},
    )
    configure(client, model="fake-second-model")
    client.app.state.ai_provider = FakeAIProvider(result="第二次生成")
    client.app.state.ai_provider.name = "fake-second-provider"
    data = {
        "operation_id": str(uuid4()),
        "input_hash": preview(client, shot, template)["input_hash"],
    }
    second = post(client, "/prompts/" + first["id"] + "/regenerate", **data)
    assert second["version"] == 2 and second["id"] != first["id"] and second["is_selected"]
    assert second["edited_content"] is None
    assert second["context_json"]["main_action"] == "新的镜头动作"
    assert second["template_content"] == "新模板 {{main_action}}"
    assert second["rendered_input"] == "新模板 新的镜头动作"
    assert (
        second["model_name"] == "fake-second-model" and second["provider"] == "fake-second-provider"
    )
    old = client.get("/api/prompts/" + first["id"]).json()
    assert {k: old[k] for k in FACTS} == {k: first[k] for k in FACTS}
    assert old["edited_content"] == "人工编辑绝不作为 AI 上下文" and not old["is_selected"]
    assert post(client, "/prompts/" + first["id"] + "/regenerate", **data) == second
    assert len(client.app.state.ai_provider.calls) == 1
    assert [r["version"] for r in history(client, shot)] == [2, 1]
    for target in [first, second, first]:
        post(client, "/prompts/" + target["id"] + "/select")
        assert [r["id"] for r in history(client, shot) if r["is_selected"]] == [target["id"]]
    # Replaying completed generation must not change a later manual selection.
    post(client, "/prompts/" + first["id"] + "/regenerate", **data)
    assert [r["id"] for r in history(client, shot) if r["is_selected"]] == [first["id"]]


def test_integer_order_isolation_and_concurrent_generation(client):
    _, scene, shot, template, _ = setup(client)
    data = [operation(client, shot, template) for _ in range(10)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(
                lambda d: client.post(f"/api/shots/{shot['id']}/prompts/generate", json=d), data
            )
        )
    assert all(r.status_code == 200 for r in results)
    assert [r["version"] for r in history(client, shot)] == list(range(11, 0, -1))
    assert sum(r["is_selected"] for r in history(client, shot)) == 1
    other_type = post(
        client,
        "/prompt-templates",
        name="Other",
        scope="GLOBAL",
        category="OTHER",
        template_content="Other prompt",
    )
    other = generated(client, shot, other_type)
    another_shot = post(
        client,
        f"/scenes/{scene['id']}/shots",
        project_id=shot["project_id"],
        shot_code="S14",
        title="Other shot",
    )
    separate = generated(client, another_shot, template)
    assert other["version"] == separate["version"] == 1
    post(client, "/prompts/" + other["id"] + "/select")
    assert sum(r["is_selected"] for r in history(client, shot)) == 2
    assert history(client, another_shot) == [separate]
    filtered = client.get(f"/api/shots/{shot['id']}/prompts?prompt_type=OTHER").json()
    assert filtered == [client.get("/api/prompts/" + other["id"]).json()]


@pytest.mark.parametrize("violation", ["duplicate-version", "multiple-selected", "zero-version"])
def test_database_enforces_constraints(client, violation):
    _, _, shot, template, first = setup(client)
    second = generated(client, shot, template)
    with pytest.raises(IntegrityError):
        with client.app.state.workspace.session() as session:
            record = session.get(PromptRecord, UUID(first["id"]))
            if violation == "duplicate-version":
                record.version = second["version"]
            elif violation == "multiple-selected":
                record.is_selected = True
            else:
                record.version = 0
            session.flush()
    assert [r["version"] for r in history(client, shot)] == [2, 1]
    assert sum(r["is_selected"] for r in history(client, shot)) == 1


@pytest.mark.parametrize("action", ["select", "regenerate", "edit"])
def test_mid_write_rolls_back_every_change(client, action):
    _, _, shot, template, first = setup(client)
    generated(client, shot, template)
    before = history(client, shot)
    engine = client.app.state.workspace._database.engine
    reached = []
    data = {
        "operation_id": str(uuid4()),
        "input_hash": preview(client, shot, template)["input_hash"],
    }

    def fail(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("UPDATE prompt_records"):
            reached.append(True)
            raise OperationalError("injected", {}, RuntimeError("injected"))

    event.listen(engine, "after_cursor_execute", fail)
    try:
        with pytest.raises(OperationalError):
            if action == "edit":
                client.patch("/api/prompts/" + first["id"], json={"edited_content": "rollback"})
            else:
                client.post(
                    "/api/prompts/" + first["id"] + "/" + action,
                    json=data if action == "regenerate" else None,
                )
    finally:
        event.remove(engine, "after_cursor_execute", fail)
    assert reached and history(client, shot) == before


@pytest.mark.parametrize("response", ["error", "empty", "provider-error"])
def test_regenerate_failure_no_phantom_and_retry(client, response):
    _, _, shot, template, first = setup(client)
    error = {
        "error": TimeoutError(),
        "provider-error": AppError("AI_MODEL_ERROR", "Fake provider error", 502),
        "empty": None,
    }[response]
    client.app.state.ai_provider = FakeAIProvider(result="", error=error)
    data = {
        "operation_id": str(uuid4()),
        "input_hash": preview(client, shot, template)["input_hash"],
    }
    url = "/api/prompts/" + first["id"] + "/regenerate"
    assert client.post(url, json=data).status_code in (502, 504)
    assert history(client, shot) == [first]
    client.app.state.ai_provider = FakeAIProvider()
    assert client.post(url, json=data).json()["version"] == 2


def test_unknown_deleted_and_cross_project_safety(client):
    project, _, shot, template, first = setup(client)
    for identifier in [str(uuid4()), first["id"]]:
        if identifier == first["id"]:
            client.delete("/api/projects/" + project["id"])
        assert client.get("/api/prompts/" + identifier).status_code == 404
        assert (
            client.patch("/api/prompts/" + identifier, json={"edited_content": "x"}).status_code
            == 404
        )
        assert client.post("/api/prompts/" + identifier + "/select").status_code == 404
        assert (
            client.post(
                "/api/prompts/" + identifier + "/regenerate",
                json={"operation_id": str(uuid4()), "input_hash": "a" * 64},
            ).status_code
            == 404
        )
    assert client.get(f"/api/shots/{shot['id']}/prompts").status_code == 404
    post(client, "/projects/" + project["id"] + "/restore")
    other_project = post(client, "/projects", name="Private project")
    private = post(
        client,
        "/prompt-templates",
        name="Private template",
        scope="PROJECT",
        project_id=other_project["id"],
        category="OTHER",
        template_content="private",
    )
    assert (
        client.post(
            f"/api/shots/{shot['id']}/prompts/generate",
            json={
                "operation_id": str(uuid4()),
                "template_id": private["id"],
                "input_hash": "a" * 64,
            },
        ).status_code
        == 400
    )
    assert history(client, shot) == [first]


def test_deleted_version_not_reused_no_automatic_selection(client):
    _, _, shot, template, first = setup(client)
    second = generated(client, shot, template)
    with client.app.state.workspace.session() as session:
        repo = PromptRepository(session)
        repo.soft_delete(repo.get(UUID(second["id"])))
    assert not any(r["is_selected"] for r in history(client, shot))
    assert generated(client, shot, template)["version"] == 3


@pytest.mark.parametrize("count", [0, 1, 5])
def test_populated_phase7_migration_stable_and_reversible(client, count):
    _, _, shot, template = seed(client)
    configure(client)
    for _ in range(count):
        generated(client, shot, template)
    database = client.app.state.workspace._database
    config = migration_config()
    with database.engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "0007_prompt_generation")
        # Identical timestamps exercise the UUID tie-break, with soft-deleted history.
        connection.exec_driver_sql("UPDATE prompt_records SET created_at='2026-09-25 00:00:00'")
        tables = set(inspect(connection).get_table_names()) - {"alembic_version"}
        before = {
            t: connection.exec_driver_sql(f'SELECT * FROM "{t}" ORDER BY id').all() for t in tables
        }
        columns = [c["name"] for c in inspect(connection).get_columns("prompt_records")]
        command.upgrade(config, "head")
        command.check(config)

        rows = connection.exec_driver_sql(
            "SELECT id, version, is_selected, edited_content FROM prompt_records ORDER BY id"
        ).all()
        assert [r[1] for r in rows] == list(range(1, count + 1))
        assert sum(r[2] for r in rows) == min(count, 1)
        assert all(r[3] is None for r in rows)
        projection = ",".join(columns)
        assert (
            connection.exec_driver_sql(f"SELECT {projection} FROM prompt_records ORDER BY id").all()
            == before["prompt_records"]
        )
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        command.downgrade(config, "0007_prompt_generation")
        assert {
            t: connection.exec_driver_sql(f'SELECT * FROM "{t}" ORDER BY id').all() for t in tables
        } == before
        command.upgrade(config, "head")
        command.check(config)


@pytest.mark.parametrize("point", ["after-insert", "before-commit"])
def test_regenerate_persistence_failure_restores_previous_selected(client, point):
    _, _, shot, template, first = setup(client)
    engine = client.app.state.workspace._database.engine
    data = {
        "operation_id": str(uuid4()),
        "input_hash": preview(client, shot, template)["input_hash"],
    }
    reached = []

    def after_insert(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO prompt_records"):
            reached.append(True)
            raise OperationalError("injected", {}, RuntimeError("injected"))

    def before_commit(session):
        if session.get_bind() is engine:
            reached.append(True)
            raise OperationalError("injected", {}, RuntimeError("injected"))

    target, name, handler = (
        (engine, "after_cursor_execute", after_insert)
        if point == "after-insert"
        else (Session, "before_commit", before_commit)
    )
    event.listen(target, name, handler)
    try:
        with pytest.raises(OperationalError):
            client.post("/api/prompts/" + first["id"] + "/regenerate", json=data)
    finally:
        event.remove(target, name, handler)
    assert reached and history(client, shot) == [first]
    assert post(client, "/prompts/" + first["id"] + "/regenerate", **data)["version"] == 2
