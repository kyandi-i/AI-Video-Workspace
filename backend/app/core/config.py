import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def user_config_path() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home() / ".config"))
    return base / "AI-Video-Workspace" / "config.json"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AVW_", env_file=REPOSITORY_ROOT / "backend" / ".env", extra="ignore"
    )

    # Only seeds a missing bootstrap config; a saved selection wins on restart.
    workspace_root: Path = Path.home() / "AI-Video-Workspace"
    bootstrap_config_path: Path = user_config_path()
    frontend_dist: Path = REPOSITORY_ROOT / "frontend" / "dist"

    @property
    def resolved_workspace_root(self) -> Path:
        path = self.workspace_root.expanduser()
        if not path.is_absolute():
            path = REPOSITORY_ROOT / path
        return path.resolve()
