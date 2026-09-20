from alembic import context

from app.core.config import Settings
from app.core.database import Database, database_url
from app.models import Base
from app.models.base import UTCDateTime
from app.services.workspace import WorkspaceService

target_metadata = Base.metadata


def render_item(kind, item, autogen_context):
    # Freeze the actual storage type into revisions, not a live application class import.
    if kind == "type" and isinstance(item, UTCDateTime):
        return "sa.DateTime()"
    return False


def run_migrations_offline() -> None:
    workspace = WorkspaceService(Settings())
    root = workspace.validate_workspace(workspace.resolve_bootstrap_root())
    context.configure(
        url=database_url(root / "data" / "workspace.db"),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    supplied = context.config.attributes.get("connection")
    if supplied is not None:
        configure_connection(supplied)
        return
    workspace = WorkspaceService(Settings())
    root = workspace.prepare_directories(workspace.resolve_bootstrap_root())
    database = Database(root / "data" / "workspace.db")
    try:
        with database.engine.begin() as connection:
            configure_connection(connection)
    finally:
        database.dispose()


def configure_connection(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=True,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
