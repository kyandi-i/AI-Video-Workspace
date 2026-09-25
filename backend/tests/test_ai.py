import io
import json
from urllib.error import HTTPError, URLError
from uuid import UUID, uuid4

import pytest
from alembic import command
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import SecretStr
from sqlalchemy import event, inspect, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.database import Database, migration_config
from app.core.exceptions import AppError
from app.main import create_app
from app.models.prompts import PromptRecord
from app.schemas.ai import ProviderUpdate
from app.services.ai.context import build_shot_context
from app.services.ai.provider import NoRedirect, OpenAICompatibleProvider
from app.services.template_placeholders import KEYS, render_content
from test_support.fake_ai import FakeAIProvider


@pytest.fixture
def client(settings):
    app = create_app(settings)
    app.state.ai_provider = FakeAIProvider()
    with TestClient(app) as client:
        yield client


def post(client, path, **data):
    result = client.post("/api" + path, json=data)
    assert result.status_code in (200, 201), result.text
    return result.json()


def seed(client, template_content="{{shot_context}}", **shot_values):
    project = post(client, "/projects", name="SPF")
    script = post(client, f"/projects/{project['id']}/scripts", name="Script")
    scene = post(
        client,
        f"/projects/{project['id']}/scenes",
        script_id=script["id"],
        name="风淋室",
        description="场景描述",
        fixed_constraints="门位置固定",
        negative_constraints="禁止设备漂移",
    )
    shot = post(
        client,
        f"/scenes/{scene['id']}/shots",
        project_id=project["id"],
        shot_code="S13",
        title="风淋",
        duration_seconds=10,
        main_action="人物从二更进入风淋室",
        key_constraints="双门互锁",
        negative_constraints="禁止两门同时开启",
        free_notes="自然步态",
        **shot_values,
    )
    template = post(
        client,
        "/prompt-templates",
        name="Video",
        scope="GLOBAL",
        category="VIDEO_GENERATION",
        template_content=template_content,
    )
    return project, scene, shot, template


def configure(client, **changes):
    return client.put(
        "/api/settings/ai",
        json={
            "api_base_url": "https://unused.invalid/v1",
            "model": "fake-model",
            "api_key": "test-credential-" + uuid4().hex,
            **changes,
        },
    )


def preview(client, shot, template):
    return post(client, f"/shots/{shot['id']}/prompts/preview", template_id=template["id"])


def operation(client, shot, template):
    rendered = preview(client, shot, template)
    return {
        "template_id": template["id"],
        "operation_id": str(uuid4()),
        "input_hash": rendered["input_hash"],
    }


def test_settings_persistence_masking_keep_clear_and_invalid_secret(client, settings, caplog):
    assert client.get("/api/settings/ai").json()["api_key_configured"] is False
    key = "test-credential-" + uuid4().hex
    response = configure(client, api_key=key)
    assert response.status_code == 200
    assert key not in response.text
    assert "api_key" not in response.json()
    stored = client.app.state.ai_settings.storage.path
    assert not stored.is_relative_to(client.app.state.workspace.get_workspace_root())
    assert stored.name == "ai-provider.json"
    assert json.loads(stored.read_text())["api_key"] == key
    update = {"api_base_url": "http://127.0.0.1:9999/v1", "model": "changed"}
    assert client.put("/api/settings/ai", json=update).json()["api_key_configured"] is True
    assert json.loads(stored.read_text())["api_key"] == key
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get("/api/settings/ai").json()["model"] == "changed"
        assert key not in restarted.get("/api/settings/ai").text
    assert (
        client.put("/api/settings/ai", json={**update, "api_key": ""}).json()["api_key_configured"]
        is False
    )
    bad = configure(client, api_key=key + "\n")
    assert bad.status_code == 422 and key not in bad.text
    assert key not in caplog.text


@pytest.mark.parametrize(
    "url",
    [
        "",
        "ftp://host/v1",
        "https://user:password@host/v1",
        "https://host/v1?key=x",
        "https://host/#x",
        "https://host:bad",
        "https://bad host/v1",
    ],
)
def test_invalid_base_url(client, url):
    assert configure(client, api_base_url=url).status_code == 422
    assert client.get("/api/settings/ai").json()["api_key_configured"] is False


@pytest.mark.parametrize("model", ["", " ", "bad\nmodel"])
def test_invalid_model(client, model):
    assert configure(client, model=model).status_code == 422


def test_corrupt_config_safe_error_and_explicit_repair(client):
    configure(client)
    path = client.app.state.ai_settings.storage.path
    path.write_text("{bad private content", encoding="utf-8")
    result = client.get("/api/settings/ai")
    assert result.status_code == 503 and "private" not in result.text
    assert configure(client).status_code == 200


def test_actual_context_assets_characters_requirements_renderer(client):
    project, _, shot, template = seed(client)
    character = post(
        client,
        f"/projects/{project['id']}/characters",
        name="SPF培训女员工",
        description="角色身份描述",
        notes="长期备注",
    )
    state = post(
        client,
        f"/characters/{character['id']}/states",
        name="黄色 PPE + 双层手套",
        description="状态描述",
    )
    post(client, f"/shots/{shot['id']}/character-states", character_state_id=state["id"])
    output = io.BytesIO()
    Image.new("RGB", (16, 16)).save(output, format="PNG")
    for owner, identifier, name in [
        ("characters", character["id"], "角色图"),
        ("character-states", state["id"], "状态图"),
        ("shots", shot["id"], "场景图"),
    ]:
        uploaded = client.post(
            "/api/assets/upload",
            params={"filename": name + ".png"},
            content=output.getvalue(),
            headers={"Content-Type": "application/octet-stream"},
        )
        assert uploaded.status_code == 201
        asset = uploaded.json()
        assert (
            client.patch(
                "/api/assets/" + asset["id"], json={"description": name + "描述"}
            ).status_code
            == 200
        )
        post(client, f"/{owner}/{identifier}/assets", asset_id=asset["id"])
    actual = preview(client, shot, template)
    assert actual == preview(client, shot, template)
    assert set(actual["context"]) == KEYS
    for term in [
        "SPF培训女员工",
        "双层手套",
        "角色身份描述",
        "长期备注",
        "状态描述",
        "角色图描述",
        "状态图描述",
        "场景图描述",
        "双门互锁",
        "自然步态",
        "门位置固定",
        "禁止设备漂移",
        "人物从二更",
    ]:
        assert term in actual["rendered_input"]
    assert actual["context"]["duration_seconds"] == "10"
    assert actual["rendered_input"] == render_content(
        template["template_content"], actual["context"]
    )
    assert client.get(f"/api/shots/{shot['id']}/prompts/latest").json() is None


def test_empty_context_nonrecursive_and_stable_order(client):
    _, _, shot, template = seed(
        client, template_content="{{main_action}}|{{free_notes}}|{{reference_assets_context}}"
    )
    client.patch(
        "/api/shots/" + shot["id"], json={"free_notes": None, "main_action": "{{shot_code}}"}
    )
    result = preview(client, shot, template)
    assert result["rendered_input"] == "{{shot_code}}||"
    assert result["context"]["characters_context"] == ""
    assert all(v not in result["context"]["shot_context"] for v in ("None", "null", "undefined"))
    with client.app.state.workspace.session() as session:
        _, direct = build_shot_context(session, UUID(shot["id"]))
        assert direct == result["context"]


def test_generation_fact_retry_latest_restart_and_snapshot(client, settings):
    _, _, shot, template = seed(client)
    configure(client)
    data = operation(client, shot, template)
    url = f"/api/shots/{shot['id']}/prompts/generate"
    generated = client.post(url, json=data)
    assert generated.status_code == 200, generated.text
    record = generated.json()
    assert record["id"] == data["operation_id"]
    assert record["provider"] == "fake-test-provider" and record["model_name"] == "fake-model"
    assert record["template_content"] == template["template_content"]
    assert record["context_json"]["main_action"] == shot["main_action"]
    assert record["generated_content"].startswith("FAKE")
    assert not {"version", "edited_content", "is_selected"} & set(record)
    assert client.post(url, json=data).json() == record
    assert len(client.app.state.ai_provider.calls) == 1
    assert client.app.state.ai_provider.calls[0][0] == record["rendered_input"]
    client.patch("/api/prompt-templates/" + template["id"], json={"template_content": "new body"})
    client.patch("/api/shots/" + shot["id"], json={"main_action": "changed"})
    client.delete("/api/prompt-templates/" + template["id"])
    assert client.get("/api/prompts/" + record["id"]).json() == record
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get(f"/api/shots/{shot['id']}/prompts/latest").json() == record
    with client.app.state.workspace.session() as session:
        assert len(list(session.scalars(select(PromptRecord)))) == 1
    client.delete("/api/shots/" + shot["id"])
    assert client.get("/api/prompts/" + record["id"]).status_code == 404


@pytest.mark.parametrize(
    "mode,code", [("unconfigured", "AI_NOT_CONFIGURED"), ("emptykey", "AI_KEY_MISSING")]
)
def test_missing_settings(client, mode, code):
    _, _, shot, template = seed(client)
    if mode == "emptykey":
        configure(client, api_key="")
    result = client.post(
        f"/api/shots/{shot['id']}/prompts/generate", json=operation(client, shot, template)
    )
    assert result.json()["code"] == code
    assert client.app.state.ai_provider.calls == []


@pytest.mark.parametrize(
    "result,error,code",
    [
        ("", None, "AI_EMPTY_RESPONSE"),
        (" \n", None, "AI_EMPTY_RESPONSE"),
        (None, None, "AI_INVALID_RESPONSE"),
        ("x" * 500001, None, "AI_INVALID_RESPONSE"),
        ("", TimeoutError("sensitive"), "AI_TIMEOUT"),
        ("", RuntimeError("sensitive"), "AI_PROVIDER_ERROR"),
        ("", AppError("AI_MODEL_ERROR", "sensitive", 502, {"raw": "sensitive"}), "AI_MODEL_ERROR"),
    ],
    ids=["empty", "whitespace", "nontext", "oversize", "timeout", "exception", "provider-error"],
)
def test_failure_does_not_persist_or_leak(client, caplog, result, error, code):
    _, _, shot, template = seed(client)
    configure(client)
    client.app.state.ai_provider = FakeAIProvider(result=result, error=error)
    data = operation(client, shot, template)
    response = client.post(f"/api/shots/{shot['id']}/prompts/generate", json=data)
    assert response.json()["code"] == code
    assert set(response.json()) == {"code", "message", "details"}
    assert "sensitive" not in response.text + caplog.text
    assert client.get(f"/api/shots/{shot['id']}/prompts/latest").json() is None
    client.app.state.ai_provider = FakeAIProvider()
    assert client.post(f"/api/shots/{shot['id']}/prompts/generate", json=data).status_code == 200


def test_echoed_key_not_persisted(client, caplog):
    _, _, shot, template = seed(client)
    key = "test-credential-" + uuid4().hex
    configure(client, api_key=key)
    client.app.state.ai_provider = FakeAIProvider(result=key)
    response = client.post(
        f"/api/shots/{shot['id']}/prompts/generate", json=operation(client, shot, template)
    )
    assert response.json()["code"] == "AI_INVALID_RESPONSE"
    assert key not in response.text + caplog.text
    assert client.get(f"/api/shots/{shot['id']}/prompts/latest").json() is None


@pytest.mark.parametrize("failure_point", ["after-insert", "before-commit"])
def test_database_write_failure_rolls_back_generation_fact(client, failure_point):
    _, _, shot, template = seed(client)
    configure(client)
    data = operation(client, shot, template)
    url = f"/api/shots/{shot['id']}/prompts/generate"
    engine = client.app.state.workspace._database.engine
    reached = []

    def fail_after_insert(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO prompt_records"):
            reached.append("inserted")
            raise OperationalError("acceptance write failure", {}, RuntimeError("fake disk error"))

    def fail_before_commit(session):
        if session.get_bind() is engine:
            assert session.scalar(select(PromptRecord.id)) == UUID(data["operation_id"])
            reached.append("commit")
            raise OperationalError("acceptance commit failure", {}, RuntimeError("fake disk error"))

    target, name, handler = (
        (engine, "after_cursor_execute", fail_after_insert)
        if failure_point == "after-insert"
        else (Session, "before_commit", fail_before_commit)
    )
    event.listen(target, name, handler)
    try:
        with pytest.raises(OperationalError):
            client.post(url, json=data)
    finally:
        event.remove(target, name, handler)
    assert reached
    # A fresh connection observes no row, including after an INSERT actually ran.
    with engine.connect() as connection:
        assert connection.execute(select(PromptRecord.id)).all() == []
    assert client.get(f"/api/shots/{shot['id']}/prompts/latest").json() is None
    assert client.post(url, json=data).status_code == 200
    with engine.connect() as connection:
        assert connection.execute(select(PromptRecord.id)).scalars().all() == [
            UUID(data["operation_id"])
        ]


def test_key_in_unused_context_never_enters_generation_record(client):
    _, _, shot, template = seed(client, template_content="Static instructions")
    key = "test-credential-" + uuid4().hex
    configure(client, api_key=key)
    client.patch("/api/shots/" + shot["id"], json={"free_notes": key})
    result = client.post(
        f"/api/shots/{shot['id']}/prompts/generate", json=operation(client, shot, template)
    )
    assert result.json()["code"] == "AI_SENSITIVE_INPUT"
    assert key not in result.text
    assert client.app.state.ai_provider.calls == []
    assert client.get(f"/api/shots/{shot['id']}/prompts/latest").json() is None


def test_actual_preview_reuses_validation_even_for_corrupt_stored_template(client):
    from app.models.templates import PromptTemplate

    _, _, shot, template = seed(client)
    with client.app.state.workspace.session() as session:
        session.get(PromptTemplate, UUID(template["id"])).template_content = "{{unknown}}"
    result = client.post(
        f"/api/shots/{shot['id']}/prompts/preview", json={"template_id": template["id"]}
    )
    assert result.json()["code"] == "INVALID_TEMPLATE_PLACEHOLDER"
    assert client.app.state.ai_provider.calls == []


def test_populated_generation_downgrade_preserves_all_old_tables(client):
    _, _, shot, template = seed(client)
    configure(client)
    assert (
        client.post(
            f"/api/shots/{shot['id']}/prompts/generate", json=operation(client, shot, template)
        ).status_code
        == 200
    )
    database = client.app.state.workspace._database
    config = migration_config()
    with database.engine.begin() as connection:
        config.attributes["connection"] = connection
        tables = set(inspect(connection).get_table_names()) - {"prompt_records", "alembic_version"}
        before = {
            t: connection.exec_driver_sql(f'SELECT * FROM "{t}" ORDER BY id').all() for t in tables
        }
        assert connection.exec_driver_sql("SELECT count(*) FROM prompt_records").scalar() == 1
        command.downgrade(config, "0006_prompt_templates")
        assert "prompt_records" not in inspect(connection).get_table_names()
        command.upgrade(config, "head")
        command.check(config)
        assert connection.exec_driver_sql("SELECT count(*) FROM prompt_records").scalar() == 0
        assert {
            t: connection.exec_driver_sql(f'SELECT * FROM "{t}" ORDER BY id').all() for t in tables
        } == before
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []


def test_stale_preview_cross_project_missing_deleted_template_and_operation_conflict(client):
    project, _, shot, template = seed(client)
    configure(client)
    data = operation(client, shot, template)
    client.patch("/api/shots/" + shot["id"], json={"main_action": "changed"})
    url = f"/api/shots/{shot['id']}/prompts/generate"
    assert client.post(url, json=data).json()["code"] == "AI_INPUT_CHANGED"
    other = post(client, "/projects", name="Other")
    cross = post(
        client,
        "/prompt-templates",
        name="Private",
        scope="PROJECT",
        project_id=other["id"],
        category="OTHER",
        template_content="body",
    )
    assert (
        client.post(
            f"/api/shots/{shot['id']}/prompts/preview", json={"template_id": cross["id"]}
        ).status_code
        == 400
    )
    for identifier in (str(uuid4()),):
        assert (
            client.post(
                f"/api/shots/{shot['id']}/prompts/preview", json={"template_id": identifier}
            ).status_code
            == 404
        )
    data = operation(client, shot, template)
    assert client.post(url, json=data).status_code == 200
    assert client.post(url, json={**data, "input_hash": "a" * 64}).status_code == 409
    client.delete("/api/prompt-templates/" + template["id"])
    assert (
        client.post(
            f"/api/shots/{shot['id']}/prompts/preview", json={"template_id": template["id"]}
        ).status_code
        == 404
    )
    client.delete("/api/projects/" + project["id"])
    assert client.get(f"/api/shots/{shot['id']}/prompts/latest").status_code == 404


def test_empty_render_rejected(client):
    _, _, shot, template = seed(client, template_content="{{reference_assets_context}}")
    result = client.post(
        f"/api/shots/{shot['id']}/prompts/preview", json={"template_id": template["id"]}
    )
    assert result.json()["code"] == "AI_EMPTY_INPUT"


class StubOpener:
    def __init__(self, body=None, error=None):
        self.body, self.error = body, error

    def open(self, request, timeout):
        self.request, self.timeout = request, timeout
        if self.error:
            raise self.error
        return io.BytesIO(self.body)


def test_compatible_transport_payload_and_no_redirect():
    config = ProviderUpdate(
        api_base_url="https://unused.invalid/v1", model="demo", api_key=SecretStr("fake-only")
    )
    opener = StubOpener(json.dumps({"choices": [{"message": {"content": "result"}}]}).encode())
    assert (
        OpenAICompatibleProvider(opener).generate("actual input", config, "operation") == "result"
    )
    assert opener.request.full_url == "https://unused.invalid/v1/chat/completions"
    assert json.loads(opener.request.data) == {
        "model": "demo",
        "messages": [{"role": "user", "content": "actual input"}],
        "stream": False,
    }
    assert opener.request.get_header("Authorization") == "Bearer fake-only"
    assert opener.timeout == 45
    assert NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid") is None


@pytest.mark.parametrize(
    "body",
    [
        b"not json",
        b"{}",
        b"null",
        b'{"choices":[]}',
        b'{"choices":[{"message":{"content":null}}]}',
        b"x" * 1_000_001,
    ],
    ids=["not-json", "missing-choices", "null-body", "empty-choices", "null-content", "oversize"],
)
def test_invalid_transport_response(body):
    config = ProviderUpdate(
        api_base_url="https://unused.invalid", model="demo", api_key=SecretStr("fake-only")
    )
    with pytest.raises(AppError) as result:
        OpenAICompatibleProvider(StubOpener(body)).generate("input", config, "operation")
    assert result.value.code == "AI_INVALID_RESPONSE"


@pytest.mark.parametrize(
    "status,code",
    [
        (401, "AI_AUTH_ERROR"),
        (403, "AI_AUTH_ERROR"),
        (400, "AI_MODEL_ERROR"),
        (404, "AI_MODEL_ERROR"),
        (422, "AI_MODEL_ERROR"),
        (429, "AI_PROVIDER_ERROR"),
        (500, "AI_PROVIDER_ERROR"),
        (302, "AI_PROVIDER_ERROR"),
    ],
)
def test_transport_http_errors(status, code):
    error = HTTPError("https://unused.invalid", status, "sensitive", {}, io.BytesIO(b"sensitive"))
    config = ProviderUpdate(
        api_base_url="https://unused.invalid", model="demo", api_key=SecretStr("fake-only")
    )
    with pytest.raises(AppError) as result:
        OpenAICompatibleProvider(StubOpener(error=error)).generate("input", config, "operation")
    assert result.value.code == code and "sensitive" not in str(result.value)


@pytest.mark.parametrize(
    "error,code",
    [
        (TimeoutError(), "AI_TIMEOUT"),
        (URLError(TimeoutError()), "AI_TIMEOUT"),
        (URLError("sensitive"), "AI_CONNECTION_ERROR"),
        (ConnectionResetError(), "AI_CONNECTION_ERROR"),
    ],
)
def test_transport_network_errors(error, code):
    config = ProviderUpdate(
        api_base_url="https://unused.invalid", model="demo", api_key=SecretStr("fake-only")
    )
    with pytest.raises(AppError) as result:
        OpenAICompatibleProvider(StubOpener(error=error)).generate("input", config, "operation")
    assert result.value.code == code


def test_phase7_migration_preserves_old_rows_and_roundtrip(tmp_path):
    database = Database(tmp_path / "isolated.db")
    config = migration_config()
    try:
        with database.engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "0006_prompt_templates")
            connection.exec_driver_sql(
                "INSERT INTO projects (id,name,description,status,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?)",
                (uuid4().hex, "Keep", "Old SPF", "DRAFT", "2026-09-25", "2026-09-25"),
            )
            before = connection.exec_driver_sql("SELECT * FROM projects").all()
            command.upgrade(config, "head")
            assert "prompt_records" in inspect(connection).get_table_names()
            command.check(config)
            command.downgrade(config, "0006_prompt_templates")
            assert "prompt_records" not in inspect(connection).get_table_names()
            assert connection.exec_driver_sql("SELECT * FROM projects").all() == before
            command.upgrade(config, "head")
            command.check(config)
            assert connection.exec_driver_sql("SELECT * FROM projects").all() == before
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
    finally:
        database.dispose()
