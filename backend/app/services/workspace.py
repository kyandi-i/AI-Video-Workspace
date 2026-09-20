import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import Lock

from alembic.util.exc import CommandError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.bootstrap import BootstrapConfig
from app.core.config import Settings
from app.core.database import Database
from app.core.exceptions import AppError
from app.core.paths import managed_path, reject_link
from app.services.storage import LocalStorageProvider, StorageProvider

DIRECTORIES = (
    "data",
    "storage",
    "storage/assets",
    "storage/thumbnails",
    "storage/temp",
    "exports",
    "backups",
)


class WorkspaceService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.bootstrap = BootstrapConfig(settings.bootstrap_config_path)
        self._root: Path | None = None
        self._database: Database | None = None
        self._lock = Lock()

    def validate_workspace(self, path: str | Path) -> Path:
        raw = str(path)
        if not raw.strip() or "\x00" in raw:
            raise AppError("WORKSPACE_INVALID", "工作空间目录不能为空或包含无效字符。")
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute() or ".." in candidate.parts:
            raise AppError("WORKSPACE_INVALID", "工作空间必须使用不包含 .. 的绝对路径。")
        try:
            reject_link(candidate, "WORKSPACE_INVALID")
            root = candidate.resolve()
            if root == Path(root.anchor):
                raise AppError("WORKSPACE_INVALID", "不能把磁盘根目录作为工作空间。")
            if root.exists() and not root.is_dir():
                raise AppError("WORKSPACE_INVALID", "工作空间路径指向文件，请选择目录。")
            if self.bootstrap.path.resolve().is_relative_to(root):
                raise AppError("WORKSPACE_INVALID", "启动配置必须保存在工作空间之外。")
            for directory in DIRECTORIES:
                target = managed_path(root, directory, "WORKSPACE_INVALID")
                if target.exists() and not target.is_dir():
                    raise AppError("WORKSPACE_INVALID", f"内部目录 {directory} 已被同名文件占用。")
            for name in (
                "workspace.db",
                "workspace.db-wal",
                "workspace.db-shm",
                "workspace.db-journal",
            ):
                target = managed_path(root, f"data/{name}", "WORKSPACE_INVALID")
                if target.exists() and not target.is_file():
                    raise AppError("WORKSPACE_INVALID", "数据库路径不是普通文件。")
            return root
        except (OSError, ValueError) as exc:
            raise AppError("WORKSPACE_INVALID", "工作空间路径无效或无法访问。") from exc

    def prepare_directories(self, path: str | Path) -> Path:
        """Used by the app and Alembic CLI; does not modify the bootstrap selection."""
        root = self.validate_workspace(path)
        try:
            root.mkdir(parents=True, exist_ok=True)
            for directory in DIRECTORIES:
                target = managed_path(root, directory, "WORKSPACE_INVALID")
                target.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryFile(dir=root):
                pass
        except OSError as exc:
            raise AppError("WORKSPACE_INVALID", "无法创建或写入工作空间，请检查目录权限。") from exc
        return root

    def resolve_bootstrap_root(self) -> Path:
        return self.bootstrap.load() or self.settings.resolved_workspace_root

    def _prepare_database(self, root: Path) -> Database:
        database = Database(managed_path(root, "data/workspace.db", "WORKSPACE_INVALID"))
        try:
            database.upgrade()
        except (CommandError, SQLAlchemyError, OSError) as exc:
            database.dispose()
            raise AppError(
                "WORKSPACE_DATABASE_ERROR",
                "工作空间数据库初始化失败，请检查文件与迁移版本。",
                409,
            ) from exc
        return database

    def initialize_workspace(self) -> dict:
        with self._lock:
            if self._database is not None:
                return self._info()
            root = self.prepare_directories(self.resolve_bootstrap_root())
            database = self._prepare_database(root)
            try:
                self.bootstrap.save(root)
            except Exception:
                database.dispose()
                raise
            self._root, self._database = root, database
            return self._info()

    def set_workspace_root(self, path: str | Path) -> dict:
        with self._lock:
            root = self.validate_workspace(path)
            if root == self._root:
                return self._info()
            if self._root and (root.is_relative_to(self._root) or self._root.is_relative_to(root)):
                raise AppError("WORKSPACE_INVALID", "新旧工作空间不能互相嵌套，请选择独立目录。")
            root = self.prepare_directories(root)
            database = self._prepare_database(root)
            try:
                self.bootstrap.save(root)
            except Exception:
                database.dispose()
                raise
            previous = self._database
            self._root, self._database = root, database
            if previous:
                previous.dispose()
            return self._info()

    def get_workspace_root(self) -> Path:
        if self._root is None:
            raise AppError("WORKSPACE_NOT_READY", "工作空间尚未初始化。", 503)
        return self._root

    def _path(self, relative: str) -> Path:
        return managed_path(self.get_workspace_root(), relative, "WORKSPACE_INVALID")

    def get_database_path(self) -> Path:
        return self._path("data/workspace.db")

    def get_storage_path(self) -> Path:
        return self._path("storage")

    def get_thumbnail_path(self) -> Path:
        return self._path("storage/thumbnails")

    def get_temp_path(self) -> Path:
        return self._path("storage/temp")

    def get_export_path(self) -> Path:
        return self._path("exports")

    def get_backup_path(self) -> Path:
        return self._path("backups")

    def _info(self) -> dict:
        return {
            "workspace_root": str(self.get_workspace_root()),
            "database_path": str(self.get_database_path()),
            "initialized": True,
        }

    def get_info(self) -> dict:
        with self._lock:
            return self._info()

    @contextmanager
    def resources(self) -> Iterator[tuple[Database, StorageProvider]]:
        """Pin a matching DB/storage pair until a service finishes its operation."""
        with self._lock:
            if self._database is None:
                raise AppError("WORKSPACE_NOT_READY", "工作空间尚未初始化。", 503)
            yield self._database, LocalStorageProvider(self.get_storage_path())

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self._lock:
            if self._database is None:
                raise AppError("WORKSPACE_NOT_READY", "工作空间尚未初始化。", 503)
            with self._database.session() as session:
                yield session

    def close(self) -> None:
        with self._lock:
            if self._database:
                self._database.dispose()
            self._database = None
            self._root = None
