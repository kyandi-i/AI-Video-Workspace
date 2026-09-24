from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest

from app.core.exceptions import AppError
from app.models import AppSetting
from app.repositories.base import BaseRepository
from app.services.workspace import DIRECTORIES, WorkspaceService


def test_initialization_is_idempotent_and_bootstrap_is_not_persisted(settings):
    service = WorkspaceService(settings)
    assert not settings.bootstrap_config_path.exists()
    first = service.initialize_workspace()
    try:
        assert first == service.initialize_workspace()
        root = service.get_workspace_root()
        assert all((root / directory).is_dir() for directory in DIRECTORIES)
        assert service.get_database_path().is_file()
        # Phase 5.1: booting from a missing config only seeds an in-memory default
        # root; it must never persist a bootstrap selection by itself.
        assert not settings.bootstrap_config_path.exists()
        assert service.get_storage_path() == root / "storage"
        assert service.get_thumbnail_path().is_dir()
        assert service.get_temp_path().is_dir()
        assert service.get_export_path().is_dir()
        assert service.get_backup_path().is_dir()
    finally:
        service.close()


def test_switch_preserves_old_workspace_and_survives_restart(workspace, settings, tmp_path):
    old = workspace.get_workspace_root()
    marker = old / "storage" / "assets" / "keep.txt"
    marker.write_text("old workspace content")
    with workspace.session() as session:
        BaseRepository(session, AppSetting).add(AppSetting(key="old-setting", value=1))
    new = tmp_path / "新 工作空间"
    workspace.set_workspace_root(new)
    assert marker.read_text() == "old workspace content"
    assert not (new / "storage/assets/keep.txt").exists()
    with workspace.session() as session:
        assert BaseRepository(session, AppSetting).list() == []
    workspace.close()
    restarted = WorkspaceService(settings)
    try:
        restarted.initialize_workspace()
        assert restarted.get_workspace_root() == new
        restarted.set_workspace_root(old)
        with restarted.session() as session:
            assert BaseRepository(session, AppSetting).list()[0].key == "old-setting"
    finally:
        restarted.close()


@pytest.mark.parametrize("invalid", ["", "   ", "relative/path", "../workspace", "bad\x00path"])
def test_invalid_path_is_readable_and_does_not_switch(workspace, invalid):
    before = workspace.get_info()
    with pytest.raises(AppError) as failure:
        workspace.set_workspace_root(invalid)
    assert failure.value.code == "WORKSPACE_INVALID"
    assert workspace.get_info() == before


def test_file_conflicting_directory_and_nested_root_are_rejected(workspace, tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("untouched")
    conflict = tmp_path / "conflict"
    conflict.mkdir()
    (conflict / "storage").write_text("untouched")
    for path in [file, conflict, workspace.get_workspace_root() / "nested", Path(file.anchor)]:
        with pytest.raises(AppError):
            workspace.set_workspace_root(path)
    assert file.read_text() == "untouched"


def test_config_failure_does_not_switch(workspace, tmp_path, monkeypatch):
    # An explicit selection is what creates the bootstrap config (Phase 5.1).
    workspace.set_workspace_root(tmp_path / "first-root")
    previous = workspace.get_info()
    config = workspace.bootstrap.path.read_bytes()

    def fail_replace(*args):
        raise PermissionError("simulated read-only config")

    monkeypatch.setattr("app.core.bootstrap.os.replace", fail_replace)
    with pytest.raises(AppError) as failure:
        workspace.set_workspace_root(tmp_path / "new-root")
    assert failure.value.code == "BOOTSTRAP_WRITE_FAILED"
    assert workspace.get_info() == previous
    assert workspace.bootstrap.path.read_bytes() == config
    assert list(workspace.bootstrap.path.parent.glob("*.tmp")) == []


def test_corrupt_config_is_not_silently_replaced(settings):
    settings.bootstrap_config_path.parent.mkdir(parents=True)
    settings.bootstrap_config_path.write_text("broken json")
    with pytest.raises(AppError) as failure:
        WorkspaceService(settings).initialize_workspace()
    assert failure.value.code == "BOOTSTRAP_INVALID"
    assert settings.bootstrap_config_path.read_text() == "broken json"


def test_corrupt_database_does_not_switch(workspace, tmp_path):
    before = workspace.get_info()
    invalid = tmp_path / "bad-db"
    (invalid / "data").mkdir(parents=True)
    (invalid / "data/workspace.db").write_bytes(b"not a database")
    with pytest.raises(AppError) as failure:
        workspace.set_workspace_root(invalid)
    assert failure.value.status_code == 409
    assert workspace.get_info() == before


def test_switch_waits_for_transaction(workspace, tmp_path):
    started, switching = Event(), Event()
    with ThreadPoolExecutor(max_workers=1) as executor:
        with workspace.session() as session:
            BaseRepository(session, AppSetting).add(AppSetting(key="in-flight", value=True))

            def switch():
                started.set()
                workspace.set_workspace_root(tmp_path / "after-transaction")
                switching.set()

            future = executor.submit(switch)
            assert started.wait(2)
            assert not switching.is_set()
        future.result(timeout=10)
        assert switching.is_set()
