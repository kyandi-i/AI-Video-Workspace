"""Test-only app entry point. Production launcher cannot enable this provider."""

from pathlib import Path

from app.core.config import REPOSITORY_ROOT, Settings
from app.main import create_app
from app.services.workspace import WorkspaceService
from test_support.fake_ai import FakeAIProvider

settings = Settings()
workspace = WorkspaceService(settings)
boundary = (REPOSITORY_ROOT / ".workspace" / "e2e").resolve()
if not (
    workspace.resolve_bootstrap_root().resolve().is_relative_to(boundary)
    and Path(settings.bootstrap_config_path).resolve().is_relative_to(boundary)
):
    raise RuntimeError("Fake AI browser app requires an isolated E2E workspace and bootstrap")
app = create_app(settings)
app.state.ai_provider = FakeAIProvider()
