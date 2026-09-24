from uuid import uuid4

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.core.database import Database, migration_config
from app.main import create_app
from app.models.templates import PromptTemplate, TemplateCategory
from app.services.template_placeholders import PLACEHOLDERS, render_content


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as value:
        yield value


def create(client, **changes):
    return client.post(
        "/api/prompt-templates",
        json={
            "scope": "GLOBAL",
            "name": "风淋 Template",
            "category": "VIDEO_GENERATION",
            "template_content": "【镜头】\n{{shot_code}} {{ main_action }}\n全角：约束。",
            **changes,
        },
    )


def project(client, name="Project"):
    return client.post("/api/projects", json={"name": name}).json()["id"]


def test_crud_filters_and_reserved_names(client):
    result = create(client)
    assert result.status_code == 201, result.text
    template = result.json()
    url = f"/api/prompt-templates/{template['id']}"
    assert client.get(url).json() == template
    updated = client.patch(url, json={"name": "  Edited  ", "description": "关键词 SEARCH"}).json()
    assert updated["name"] == "Edited"
    assert updated["template_content"] == template["template_content"]
    assert client.get(
        "/api/prompt-templates?search=search&scope=GLOBAL&category=VIDEO_GENERATION"
    ).json() == [updated]
    assert client.get("/api/prompt-templates?category=OTHER").json() == []
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404
    assert client.get("/api/prompt-templates").json() == []
    assert client.get("/api/prompt-templates?include_deleted=true").json()[0]["deleted_at"]
    assert create(client, name="Edited").json()["code"] == "PROMPT_TEMPLATE_NAME_CONFLICT"
    assert client.post(url + "/restore").json()["deleted_at"] is None
    assert client.get(url).json()["template_content"] == template["template_content"]


def test_project_names_scope_and_lifecycle(client):
    a, b = project(client), project(client, "B")
    global_template = create(client).json()
    item = create(client, scope="PROJECT", project_id=a).json()
    assert create(client, scope="PROJECT", project_id=a).status_code == 409
    assert create(client, scope="PROJECT", project_id=b).status_code == 201
    assert create(client).status_code == 409
    visible = client.get(f"/api/prompt-templates?project_id={a}&include_global=true").json()
    assert {t["id"] for t in visible} == {global_template["id"], item["id"]}
    url = f"/api/prompt-templates/{item['id']}"
    assert client.delete(url).status_code == 204
    assert client.delete(f"/api/projects/{a}").status_code == 204
    assert client.post(url + "/restore").status_code == 404
    assert client.get(f"/api/prompt-templates/{global_template['id']}").status_code == 200
    assert client.post(f"/api/projects/{a}/restore").status_code == 200
    assert client.get(url).status_code == 404  # independently deleted stays deleted
    assert client.post(url + "/restore").status_code == 200
    assert client.delete(f"/api/projects/{a}").status_code == 204
    assert item["id"] not in {t["id"] for t in client.get("/api/prompt-templates").json()}
    assert client.get(url).status_code == 404
    assert client.patch(url, json={"name": "x"}).status_code == 404
    assert client.post(f"/api/projects/{a}/restore").status_code == 200
    assert client.get(url).status_code == 200


@pytest.mark.parametrize(
    "changes,status",
    [
        ({"scope": "PROJECT"}, 400),
        ({"scope": "GLOBAL", "project_id": str(uuid4())}, 400),
        ({"scope": "PROJECT", "project_id": str(uuid4())}, 404),
        ({"scope": "invalid"}, 422),
        ({"category": "invalid"}, 422),
        ({"name": "   "}, 422),
        ({"template_content": ""}, 422),
        ({"template_content": " \n "}, 422),
        ({"template_content": "x" * 100001}, 422),
    ],
)
def test_invalid_input(client, changes, status):
    assert create(client, **changes).status_code == status


@pytest.mark.parametrize("category", list(TemplateCategory))
def test_categories(client, category):
    assert create(client, category=category).status_code == 201


@pytest.mark.parametrize(
    "content",
    [
        "{{main_aciton}}",
        "{{__class__}}",
        "{{foo.bar}}",
        "{{characters[0].name}}",
        "{{#each}}",
        "{{open('file')}}",
        "{{ main_action",
        "main_action}}",
        "{{{shot_code}}}",
    ],
)
def test_unknown_rejected_by_save_update_and_preview(client, content):
    item = create(client).json()
    for response in (
        create(client, name="Other", template_content=content),
        client.patch(f"/api/prompt-templates/{item['id']}", json={"template_content": content}),
        client.post("/api/prompt-templates/preview", json={"template_content": content}),
    ):
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_TEMPLATE_PLACEHOLDER"
        assert response.json()["details"]["unknown_placeholders"]
    assert client.get(f"/api/prompt-templates/{item['id']}").json() == item


@pytest.mark.parametrize(
    "content",
    [
        "{{ main_action }}\n{{main_action}}",
        "请严格按照企业培训格式输出。",
        "{% for %} <script>alert(1)</script>",
        "\n中文 EN，全角：\n{{shot_context}}\n",
    ],
)
def test_valid_content_preserved_and_preview_read_only(client, content):
    item = create(client, template_content=content).json()
    assert item["template_content"] == content
    preview = client.post("/api/prompt-templates/preview", json={"template_content": content})
    assert preview.status_code == 200
    assert (
        preview.json()
        == client.post("/api/prompt-templates/preview", json={"template_content": content}).json()
    )
    assert client.get(f"/api/prompt-templates/{item['id']}").json() == item
    if "{{" not in content:
        assert preview.json()["rendered_content"] == content


def test_registry_and_nonrecursive_render(client):
    registry = client.get("/api/prompt-templates/placeholders").json()
    assert registry == PLACEHOLDERS
    assert len({p["key"] for p in registry}) == 15
    assert all(set(p) == {"key", "label", "description", "group", "example"} for p in registry)
    assert (
        render_content(
            "中{{ main_action }}\n{{main_action}}|{{free_notes}}|{{duration_seconds}}",
            {"main_action": "{{shot_code}}", "free_notes": None, "duration_seconds": 0},
        )
        == "中{{shot_code}}\n{{shot_code}}||0"
    )
    assert render_content("{{free_notes}}", {}) == ""


def test_duplicate_copy_independence_and_targets(client):
    source = create(client).json()
    url = f"/api/prompt-templates/{source['id']}"
    one = client.post(url + "/duplicate").json()
    assert one["name"] == source["name"] + " Copy"
    client.delete(f"/api/prompt-templates/{one['id']}")
    assert client.post(url + "/duplicate").json()["name"] == source["name"] + " Copy 2"
    p = project(client)
    copy = client.post(url + "/copy-to-project", json={"project_id": p}).json()
    assert copy["scope"] == "PROJECT" and copy["project_id"] == p
    assert copy["name"] == source["name"]
    copy_url = f"/api/prompt-templates/{copy['id']}"
    duplicate = client.post(copy_url + "/duplicate").json()
    assert duplicate["project_id"] == p and duplicate["name"].endswith(" Copy")
    assert (
        client.post(url + "/copy-to-project", json={"project_id": p})
        .json()["name"]
        .endswith(" Copy 2")
    )
    client.patch(copy_url, json={"template_content": "独立副本"})
    assert client.get(url).json() == source
    assert client.post(copy_url + "/copy-to-project", json={"project_id": p}).status_code == 400
    assert (
        client.post(url + "/copy-to-project", json={"project_id": str(uuid4())}).status_code == 404
    )
    client.delete(f"/api/projects/{p}")
    assert client.post(url + "/copy-to-project", json={"project_id": p}).status_code == 404
    assert create(client, scope="PROJECT", project_id=p).status_code == 404


@pytest.mark.parametrize(
    "change",
    [
        {"scope": None},
        {"category": None},
        {"name": None},
        {"template_content": None},
        {"scope": "PROJECT"},
    ],
)
def test_update_cannot_break_scope_or_required_fields(client, change):
    item = create(client).json()
    url = f"/api/prompt-templates/{item['id']}"
    assert client.patch(url, json=change).status_code in (400, 422)
    assert client.get(url).json() == item


@pytest.mark.parametrize(
    "changes",
    [
        {"scope": "PROJECT"},
        {"scope": "GLOBAL", "project_id": uuid4()},
        {"category": "BAD"},
        {"template_content": ""},
        {"name": " "},
    ],
)
def test_database_constraints(workspace, changes):
    with pytest.raises(IntegrityError), workspace.session() as session:
        session.add(
            PromptTemplate(
                scope="GLOBAL",
                project_id=None,
                name="DB",
                description=None,
                category="OTHER",
                template_content="text",
                **{},
            )
        )
        entity = session.new.pop()
        for key, value in changes.items():
            setattr(entity, key, value)
        session.add(entity)
        session.flush()


def test_migration_preserves_existing_data(tmp_path):
    db = Database(tmp_path / "phase6.db")
    cfg = migration_config()
    try:
        with db.engine.begin() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "0005_shot_workspace")
            connection.exec_driver_sql(
                "INSERT INTO projects (id,name,description,status,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?)",
                (uuid4().hex, "Existing", "保留", "DRAFT", "2026-09-24", "2026-09-24"),
            )
            before = connection.exec_driver_sql("SELECT * FROM projects").all()
            command.upgrade(cfg, "head")
            assert connection.exec_driver_sql("SELECT count(*) FROM prompt_templates").scalar() == 0
            assert connection.exec_driver_sql("SELECT * FROM projects").all() == before
            command.check(cfg)
            command.downgrade(cfg, "0005_shot_workspace")
            assert "prompt_templates" not in inspect(connection).get_table_names()
            command.upgrade(cfg, "head")
            assert connection.exec_driver_sql("SELECT * FROM projects").all() == before
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
    finally:
        db.dispose()
