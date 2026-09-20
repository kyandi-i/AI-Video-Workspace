import pytest

from app.core.config import Settings
from app.services.workspace import WorkspaceService


@pytest.fixture(autouse=True)
def isolated_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("AVW_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    monkeypatch.setenv("AVW_BOOTSTRAP_CONFIG_PATH", str(tmp_path / "bootstrap" / "config.json"))


@pytest.fixture
def settings(isolated_environment):
    return Settings(_env_file=None)


@pytest.fixture
def workspace(settings):
    service = WorkspaceService(settings)
    service.initialize_workspace()
    try:
        yield service
    finally:
        service.close()
