from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient

from app.core.config import REPOSITORY_ROOT, Settings
from app.core.database import Base
from app.main import create_app


def test_construction_is_lazy_and_lifespan_initializes_workspace(tmp_path):
    root = tmp_path / "workspace"
    app = create_app(Settings(workspace_root=root, frontend_dist=tmp_path))
    assert not root.exists()
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "app": "ai-video-workspace",
            "version": "0.1.0",
            "phase": 3,
            "storage_initialized": True,
        }
    assert (root / "data" / "workspace.db").is_file()


def test_spa_and_api_routes_are_separate(tmp_path):
    (tmp_path / "index.html").write_text("<html>workspace</html>")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('ready')")
    with TestClient(create_app(Settings(frontend_dist=tmp_path))) as client:
        assert "workspace" in client.get("/").text
        assert "workspace" in client.get("/future-route").text
        assert client.get("/assets/app.js").status_code == 200
        for path in ["/api", "/api/missing", "/assets/missing.js"]:
            response = client.get(path)
            assert response.status_code == 404
            assert set(response.json()) == {"code", "message", "details"}
        assert client.get("/api/openapi.json").status_code == 200


def test_missing_frontend_has_actionable_error(tmp_path):
    with TestClient(create_app(Settings(frontend_dist=tmp_path))) as client:
        response = client.get("/")
        assert response.status_code == 503
        assert "npm run build" in response.json()["message"]
        assert client.get("/api/health").status_code == 200


def test_phase3_has_only_authorized_business_schema():
    config = Config(str(REPOSITORY_ROOT / "backend" / "alembic.ini"))
    assert ScriptDirectory.from_config(config).get_heads() == ["0003_asset_library"]
    assert set(Base.metadata.tables) == {
        "app_settings",
        "projects",
        "scripts",
        "script_nodes",
        "scenes",
        "shots",
        "assets",
        "tags",
        "asset_tags",
        "project_asset_links",
        "shot_asset_links",
    }
