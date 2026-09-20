import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.exceptions import AppError
from app.main import create_app


def test_workspace_api_get_switch_and_invalid_input(settings, tmp_path):
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/settings/workspace")
        assert response.status_code == 200
        assert response.json() == {
            "workspace_root": str(settings.resolved_workspace_root),
            "database_path": str(settings.resolved_workspace_root / "data" / "workspace.db"),
            "initialized": True,
        }
        target = tmp_path / "api-workspace"
        response = client.put("/api/settings/workspace", json={"workspace_root": str(target)})
        assert response.status_code == 200
        assert response.json()["workspace_root"] == str(target)
        assert (target / "data/workspace.db").is_file()
        for payload, status in [
            ({}, 422),
            ({"workspace_root": "../escape"}, 400),
            ({"workspace_root": str(target), "unknown": True}, 422),
        ]:
            error = client.put("/api/settings/workspace", json=payload)
            assert error.status_code == status
            assert set(error.json()) == {"code", "message", "details"}
        assert client.get("/api/settings/workspace").json()["workspace_root"] == str(target)


@pytest.mark.parametrize("status", [400, 404, 409, 422, 500])
def test_error_schema_for_all_required_statuses(settings, status):
    app = create_app(settings)

    @app.get("/test-error")
    def failure():
        if status == 500:
            raise RuntimeError("private internal exception detail")
        if status == 409:
            raise AppError("ASSET_IN_USE", "对象仍被引用。", 409, {"references": 3})
        raise HTTPException(status, "测试错误")

    # Registered after SPA fallback: place this test-only endpoint first.
    app.router.routes.insert(0, app.router.routes.pop())
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-error")
        assert response.status_code == status
        assert set(response.json()) == {"code", "message", "details"}
        assert "private internal" not in response.text


def test_invalid_schema_maps_to_409_and_preserves_selection(settings, tmp_path):
    invalid = tmp_path / "invalid"
    (invalid / "data").mkdir(parents=True)
    (invalid / "data/workspace.db").write_bytes(b"invalid sqlite")
    with TestClient(create_app(settings)) as client:
        before = client.get("/api/settings/workspace").json()
        response = client.put("/api/settings/workspace", json={"workspace_root": str(invalid)})
        assert response.status_code == 409
        assert response.json()["code"] == "WORKSPACE_DATABASE_ERROR"
        assert client.get("/api/settings/workspace").json() == before
