import hashlib
import os
import subprocess
from pathlib import Path
from uuid import UUID

import pytest

from app.core.bootstrap import BootstrapConfig
from app.core.exceptions import AppError
from app.models import AppSetting
from app.repositories.base import BaseRepository
from app.services.storage import LocalStorageProvider, StorageProvider


@pytest.fixture
def storage(workspace):
    return LocalStorageProvider(workspace.get_storage_path())


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "原始 参考.png"
    path.write_bytes(b"sample-file-content\x00\x01")
    return path


def make_directory_link(link, target):
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, check=True
        )
    else:
        link.symlink_to(target, target_is_directory=True)


def test_bootstrap_uses_physical_directory_for_atomic_replace(tmp_path):
    physical = tmp_path / "physical-config"
    physical.mkdir()
    alias = tmp_path / "redirected-config"
    make_directory_link(alias, physical)
    config = BootstrapConfig(alias / "config.json")
    assert config.path == physical / "config.json"
    config.save(tmp_path / "first-workspace")
    config.save(tmp_path / "second-workspace")
    assert config.load() == tmp_path / "second-workspace"
    assert list(physical.glob("*.tmp")) == []


def test_copy_is_independent_and_metadata_is_portable(storage, source):
    content = source.read_bytes()
    stored = storage.save_file(source)
    assert isinstance(storage, StorageProvider)
    assert stored.original_filename == source.name
    assert UUID(Path(stored.stored_filename).stem)
    assert not Path(stored.relative_path).is_absolute()
    assert "\\" not in stored.relative_path
    assert stored.file_size == len(content)
    assert stored.checksum == hashlib.sha256(content).hexdigest()
    source.unlink()
    assert storage.exists(stored.relative_path)
    with storage.get_file(stored.relative_path) as handle:
        assert handle.read() == content
    storage.delete_file(stored.relative_path)
    assert not storage.exists(stored.relative_path)
    storage.delete_file(stored.relative_path)


def test_repeated_names_get_unique_keys(storage, source):
    first = storage.save_file(source)
    second = storage.save_file(source)
    assert first.original_filename == second.original_filename
    assert first.relative_path != second.relative_path
    assert storage.exists(first.relative_path) and storage.exists(second.relative_path)


@pytest.mark.parametrize(
    "path",
    [
        "../outside.txt",
        "assets/../../outside.txt",
        "assets/../outside.txt",
        "/tmp/outside.txt",
        "C:/outside.txt",
        "C:outside.txt",
        "\\\\server\\share\\file",
        "assets\\..\\outside.txt",
        "assets/file:stream",
        "assets/CON.txt",
        "assets/dir./file",
        "assets//file",
        "assets",
        "assets/.",
        "assets/..",
        "assets/file\x00",
        "data/workspace.db",
        "",
        "assets/a/../../../outside.txt",
    ],
)
def test_path_escape_rejected_by_all_operations(storage, source, path):
    saved = storage.save_file(source)
    operations = [
        lambda: storage.delete_file(path),
        lambda: storage.exists(path),
        lambda: storage.get_absolute_path(path),
        lambda: storage.get_file(path),
        lambda: storage.move_file(saved.relative_path, path),
        lambda: storage.move_file(path, "assets/valid.txt"),
    ]
    for operation in operations:
        with pytest.raises(AppError) as failure:
            operation()
        assert failure.value.code == "PATH_UNSAFE"
    assert storage.exists(saved.relative_path)


def test_absolute_outside_file_is_not_deleted(storage, tmp_path):
    outside = tmp_path / "important.txt"
    outside.write_text("keep")
    with pytest.raises(AppError):
        storage.delete_file(str(outside))
    assert outside.read_text() == "keep"


def test_junction_or_symlink_escape_cannot_read_delete_move_or_save(
    storage, source, tmp_path, monkeypatch
):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    link = storage.root / "assets" / "12"
    make_directory_link(link, outside)
    for operation in [
        lambda: storage.delete_file("assets/12/keep.txt"),
        lambda: storage.get_file("assets/12/keep.txt"),
        lambda: storage.move_file("assets/12/keep.txt", "assets/moved.txt"),
    ]:
        with pytest.raises(AppError):
            operation()
    monkeypatch.setattr(
        "app.services.storage.local.uuid4", lambda: UUID("12345678-1234-1234-1234-123456789abc")
    )
    with pytest.raises(AppError):
        storage.save_file(source)
    assert (outside / "keep.txt").read_text() == "keep"
    assert len(list(outside.iterdir())) == 1


def test_workspace_rejects_linked_internal_directory(workspace, tmp_path):
    target = tmp_path / "outside-dir"
    target.mkdir()
    new_root = tmp_path / "linked-workspace"
    new_root.mkdir()
    make_directory_link(new_root / "storage", target)
    with pytest.raises(AppError) as failure:
        workspace.set_workspace_root(new_root)
    assert failure.value.code == "WORKSPACE_INVALID"
    assert list(target.iterdir()) == []


def test_cached_provider_rejects_replaced_workspace_ancestor(storage, workspace, tmp_path):
    original_root = workspace.get_workspace_root()
    workspace.close()
    original_root.rename(tmp_path / "original-workspace")
    outside = tmp_path / "replacement"
    (outside / "storage/assets").mkdir(parents=True)
    marker = outside / "storage/assets/keep.txt"
    marker.write_text("outside content")
    make_directory_link(original_root, outside)
    with pytest.raises(AppError) as failure:
        storage.delete_file("assets/keep.txt")
    assert failure.value.code == "PATH_UNSAFE"
    assert marker.read_text() == "outside content"


def test_copy_failure_leaves_no_published_or_partial_file(storage, source, monkeypatch):
    def fail_copy(input_file, output_file):
        output_file.write(b"partial")
        raise OSError("simulated full disk")

    monkeypatch.setattr(storage, "_copy", fail_copy)
    with pytest.raises(AppError) as failure:
        storage.save_file(source)
    assert failure.value.code == "FILE_WRITE_FAILED"
    assert not [p for p in storage.root.rglob("*") if p.is_file()]
    assert source.exists()


def test_publish_collision_does_not_overwrite(storage, source, monkeypatch):
    monkeypatch.setattr("app.services.storage.local.uuid4", lambda: UUID(int=1))
    stored = storage.save_file(source)
    before = storage.get_absolute_path(stored.relative_path).read_bytes()
    source.write_bytes(b"new version")
    with pytest.raises(AppError) as failure:
        storage.save_file(source)
    assert failure.value.status_code == 409
    assert storage.get_absolute_path(stored.relative_path).read_bytes() == before
    assert list((storage.root / "temp").iterdir()) == []


def test_move_and_no_overwrite(storage, source):
    first, second = storage.save_file(source), storage.save_file(source)
    with pytest.raises(AppError) as failure:
        storage.move_file(first.relative_path, second.relative_path)
    assert failure.value.code == "FILE_CONFLICT"
    moved = storage.move_file(first.relative_path, "assets/renamed/file.png")
    assert moved == "assets/renamed/file.png"
    assert storage.exists(moved)
    assert not storage.exists(first.relative_path)
    assert storage.exists(second.relative_path)
    assert storage.move_file(moved, moved) == moved


def test_directory_deletion_and_missing_source_are_rejected(storage, tmp_path):
    directory = storage.root / "assets" / "folder"
    directory.mkdir()
    with pytest.raises(AppError):
        storage.delete_file("assets/folder")
    assert directory.is_dir()
    with pytest.raises(AppError) as failure:
        storage.save_file(tmp_path / "missing")
    assert failure.value.code == "FILE_NOT_FOUND"


def test_compensation_cleans_up_after_db_rollback(source, workspace):
    with pytest.raises(RuntimeError):
        with workspace.resources() as (database, storage):
            with storage.save_with_compensation(source) as stored:
                with database.session() as session:
                    BaseRepository(session, AppSetting).add(
                        AppSetting(key="failed-import", value=stored.relative_path)
                    )
                    raise RuntimeError("reject import")
    assert not storage.exists(stored.relative_path)
    with workspace.session() as session:
        assert BaseRepository(session, AppSetting).list() == []


def test_thumbnail_is_explicitly_deferred(storage, source):
    stored = storage.save_file(source)
    with pytest.raises(NotImplementedError):
        storage.create_thumbnail(stored.relative_path)
