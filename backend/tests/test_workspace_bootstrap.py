"""Phase 5.1 — bootstrap config resolution, fallback hardening and isolation.

The bootstrap config answers exactly one question: which workspace root did the
user explicitly choose? A missing file therefore means "never chosen" and must
never be upgraded into a persisted selection by a plain application start.
"""

import json
from pathlib import Path

import pytest

from app.core.config import Settings, user_config_path
from app.core.exceptions import AppError
from app.services.workspace import WorkspaceService


def build_settings(bootstrap: Path, seed: Path) -> Settings:
    """Explicit kwargs outrank both APPDATA and inherited AVW_* overrides."""
    return Settings(_env_file=None, bootstrap_config_path=bootstrap, workspace_root=seed)


def test_a_missing_config_uses_default_root_without_persisting(tmp_path):
    bootstrap = tmp_path / "bootstrap" / "config.json"
    seed = tmp_path / "default-workspace"
    settings = build_settings(bootstrap, seed)

    service = WorkspaceService(settings)
    try:
        assert not bootstrap.exists()
        info = service.initialize_workspace()
        assert info["initialized"] is True
        assert Path(info["workspace_root"]) == settings.resolved_workspace_root
        assert Path(info["database_path"]).is_file()
        # The default root lives in memory only: no bootstrap config is written.
        assert not bootstrap.exists()
    finally:
        service.close()

    restarted = WorkspaceService(settings)
    try:
        assert restarted.initialize_workspace()["workspace_root"] == str(
            settings.resolved_workspace_root
        )
        assert not bootstrap.exists()
    finally:
        restarted.close()


def test_b_explicit_selection_is_persisted_and_survives_restart(tmp_path):
    bootstrap = tmp_path / "bootstrap" / "config.json"
    settings = build_settings(bootstrap, tmp_path / "seed-workspace")
    chosen = tmp_path / "chosen-workspace"

    service = WorkspaceService(settings)
    try:
        service.initialize_workspace()
        assert not bootstrap.exists()

        info = service.set_workspace_root(chosen)
        assert Path(info["workspace_root"]) == chosen.resolve()
        assert json.loads(bootstrap.read_text(encoding="utf-8")) == {
            "workspace_root": str(chosen.resolve())
        }
    finally:
        service.close()

    restarted = WorkspaceService(settings)
    try:
        assert restarted.resolve_bootstrap_root() == chosen.resolve()
        assert restarted.initialize_workspace()["workspace_root"] == str(chosen.resolve())
    finally:
        restarted.close()


def test_c_bootstrap_path_override_outranks_appdata(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata-a"
    shared = tmp_path / "shared-config" / "config.json"
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setenv("AVW_BOOTSTRAP_CONFIG_PATH", str(shared))

    settings = Settings(_env_file=None)

    assert settings.bootstrap_config_path == shared
    # APPDATA is still honoured by the default helper; the env var simply wins.
    assert user_config_path() == appdata / "AI-Video-Workspace" / "config.json"


def test_d_two_appdata_environments_share_one_config(tmp_path, monkeypatch):
    """Models Windows %APPDATA% versus the Codex redirected %APPDATA%."""
    shared = tmp_path / "shared-config" / "config.json"
    chosen = tmp_path / "authoritative-workspace"
    shared.parent.mkdir(parents=True)
    shared.write_text(json.dumps({"workspace_root": str(chosen)}), encoding="utf-8")
    monkeypatch.setenv("AVW_BOOTSTRAP_CONFIG_PATH", str(shared))

    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata-a"))
    first = Settings(_env_file=None)
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata-b"))
    second = Settings(_env_file=None)

    assert first.bootstrap_config_path == second.bootstrap_config_path == shared
    assert first.bootstrap_config_path != user_config_path()
    assert WorkspaceService(first).resolve_bootstrap_root() == chosen.resolve()
    assert WorkspaceService(second).resolve_bootstrap_root() == chosen.resolve()


@pytest.mark.parametrize(
    "invalid",
    [
        "broken json",
        '{"workspace_root": ""}',
        '{"workspace_root": "relative/path"}',
        '{"workspace_root": "C:/x", "extra": 1}',
    ],
)
def test_e_invalid_config_fails_loudly_without_falling_back(tmp_path, monkeypatch, invalid):
    shared = tmp_path / "shared-config" / "config.json"
    shared.parent.mkdir(parents=True)
    shared.write_text(invalid, encoding="utf-8")
    monkeypatch.setenv("AVW_BOOTSTRAP_CONFIG_PATH", str(shared))

    settings = Settings(_env_file=None)
    service = WorkspaceService(settings)

    with pytest.raises(AppError) as failure:
        service.initialize_workspace()

    assert failure.value.code == "BOOTSTRAP_INVALID"
    # The invalid file is preserved and no fallback workspace is materialized.
    assert shared.read_text(encoding="utf-8") == invalid
    assert not settings.resolved_workspace_root.exists()


def test_f_test_overrides_keep_every_path_inside_the_test_root(settings, tmp_path):
    # `settings` comes from the shared autouse fixture, which injects explicit
    # AVW_* overrides instead of inheriting the machine's bootstrap config.
    assert settings.bootstrap_config_path.is_relative_to(tmp_path)
    assert settings.resolved_workspace_root.is_relative_to(tmp_path)

    service = WorkspaceService(settings)
    try:
        info = service.initialize_workspace()
        assert Path(info["workspace_root"]).is_relative_to(tmp_path)
        assert Path(info["database_path"]).is_relative_to(tmp_path)
        assert Path(info["database_path"]).name == "workspace.db"

        service.set_workspace_root(tmp_path / "second-workspace")
        persisted = json.loads(settings.bootstrap_config_path.read_text(encoding="utf-8"))
        assert settings.bootstrap_config_path.is_relative_to(tmp_path)
        assert Path(persisted["workspace_root"]).is_relative_to(tmp_path)
    finally:
        service.close()
