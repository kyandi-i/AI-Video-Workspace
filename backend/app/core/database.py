from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import Request
from sqlalchemy import URL, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import REPOSITORY_ROOT
from app.models import Base

__all__ = ["Base", "Database", "get_db", "migration_config", "database_url"]


def database_url(path: Path) -> URL:
    return URL.create("sqlite+pysqlite", database=str(path))


def migration_config() -> Config:
    return Config(str(REPOSITORY_ROOT / "backend" / "alembic.ini"))


class Database:
    """One engine/session factory per workspace; no mutable global database binding."""

    def __init__(self, path: Path):
        self.engine = create_engine(
            database_url(path),
            connect_args={"check_same_thread": False, "timeout": 15},
        )

        @event.listens_for(self.engine, "connect")
        def configure_sqlite(connection, record):
            connection.isolation_level = None
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=15000")

        @event.listens_for(self.engine, "begin")
        def begin_sqlite(connection):
            connection.exec_driver_sql("BEGIN")

        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

    def upgrade(self) -> None:
        config = migration_config()
        with self.engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self.SessionLocal.begin() as session:
            yield session

    def dispose(self) -> None:
        self.engine.dispose()


def get_db(request: Request) -> Iterator[Session]:
    # The lease lasts through commit/rollback so switching cannot split a transaction.
    with request.app.state.workspace.session() as session:
        yield session
