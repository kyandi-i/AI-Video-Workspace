import shutil
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest
from alembic import command
from sqlalchemy import inspect, select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.schema import CreateTable

from app.core.database import Database, migration_config
from app.models import AppSetting
from app.repositories.base import BaseRepository


def test_migration_upgrade_downgrade_and_autogenerate(tmp_path):
    database = Database(tmp_path / "migration.db")
    config = migration_config()
    # Generate into an isolated copy; acceptance checks must not modify tracked revisions.
    migrations = tmp_path / "migrations"
    shutil.copytree(config.get_main_option("script_location"), migrations)
    config.set_main_option("script_location", str(migrations))
    try:
        with database.engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            assert set(inspect(connection).get_table_names()) == {
                "characters",
                "character_states",
                "character_asset_links",
                "character_state_asset_links",
                "shot_character_state_links",
                "alembic_version",
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
                "assets",
                "tags",
                "asset_tags",
                "project_asset_links",
                "shot_asset_links",
            }
            assert (
                connection.scalar(text("select version_num from alembic_version"))
                == "0004_characters"
            )
            command.check(config)
            revision = command.revision(
                config, message="test metadata discovery", autogenerate=True
            )
            assert revision.down_revision == "0004_characters"
            command.upgrade(config, "head")
            command.downgrade(config, "base")
            assert "app_settings" not in inspect(connection).get_table_names()
            command.upgrade(config, "head")
            assert "app_settings" in inspect(connection).get_table_names()
    finally:
        database.dispose()


def test_uuid_timestamps_and_soft_delete(workspace):
    with workspace.session() as session:
        repo = BaseRepository(session, AppSetting)
        # A controlled older timestamp avoids depending on Windows clock resolution.
        initial_time = datetime.now(UTC) - timedelta(seconds=1)
        record = repo.add(
            AppSetting(
                key="theme",
                value={"mode": "light"},
                created_at=initial_time,
                updated_at=initial_time,
            )
        )
        identifier = record.id
        assert isinstance(identifier, UUID)
        created = record.created_at
        assert created.tzinfo is UTC
        repo.update(record, value={"mode": "dark"})
        assert record.updated_at > created
    with workspace.session() as session:
        repo = BaseRepository(session, AppSetting)
        record = repo.get(identifier)
        assert record.id == identifier
        assert record.created_at == created
        assert record.created_at.tzinfo is UTC
        repo.soft_delete(record)
        assert repo.get(identifier) is None
        assert repo.list() == []
        assert repo.get(identifier, include_deleted=True) is record
        assert repo.list(include_deleted=True) == [record]
    with workspace.session() as session:
        repo = BaseRepository(session, AppSetting)
        record = repo.get(identifier, include_deleted=True)
        assert record.deleted_at.tzinfo is UTC
        repo.restore(record)
        assert repo.get(identifier) is record
        assert record.deleted_at is None


def test_utc_normalization_and_naive_timestamp_rejection(workspace):
    value = datetime(2026, 9, 20, 16, tzinfo=timezone(timedelta(hours=8)))
    with workspace.session() as session:
        record = BaseRepository(session, AppSetting).add(
            AppSetting(key="utc", value=True, created_at=value)
        )
        identifier = record.id
    with workspace.session() as session:
        assert session.get(AppSetting, identifier).created_at == datetime(
            2026, 9, 20, 8, tzinfo=UTC
        )
    with pytest.raises(StatementError):
        with workspace.session() as session:
            BaseRepository(session, AppSetting).add(
                AppSetting(key="naive", value=True, created_at=datetime(2026, 9, 20))
            )


def test_transaction_rollback_and_unique_key(workspace):
    with pytest.raises(RuntimeError):
        with workspace.session() as session:
            BaseRepository(session, AppSetting).add(AppSetting(key="rolled-back", value=True))
            raise RuntimeError("rollback")
    with workspace.session() as session:
        assert BaseRepository(session, AppSetting).list() == []
    with pytest.raises(IntegrityError):
        with workspace.session() as session:
            repo = BaseRepository(session, AppSetting)
            repo.add(AppSetting(key="same", value=1))
            repo.add(AppSetting(key="same", value=2))
    with workspace.session() as session:
        assert session.scalar(select(AppSetting)) is None


def test_repository_rejects_managed_fields_and_bad_pagination(workspace):
    from app.core.exceptions import AppError

    with workspace.session() as session:
        repo = BaseRepository(session, AppSetting)
        record = repo.add(AppSetting(key="read-only-id", value=None))
        with pytest.raises(AppError):
            repo.update(record, id=record.id)
        with pytest.raises(AppError):
            repo.list(limit=-1)


def test_model_compiles_for_postgresql():
    ddl = str(CreateTable(AppSetting.__table__).compile(dialect=postgresql.dialect()))
    assert "UUID" in ddl
    assert "AUTOINCREMENT" not in ddl


def test_phase2_upgrade_preserves_settings_and_populated_downgrade(tmp_path):
    from app.models import Base
    from app.schemas.workflow import ProjectCreate, SceneCreate, ScriptCreate, ShotCreate
    from app.services.workflow import ProjectService, SceneService, ScriptService, ShotService

    database = Database(tmp_path / "existing-phase1.db")
    config = migration_config()
    try:
        with database.engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "0001_app_settings")
        with database.session() as session:
            setting = BaseRepository(session, AppSetting).add(
                AppSetting(key="existing", value={"preserve": True})
            )
            setting_id = setting.id
        database.upgrade()
        with database.session() as session:
            assert session.get(AppSetting, setting_id).value == {"preserve": True}
            project = ProjectService(session).create_project(ProjectCreate(name="Migration test"))
            script = ScriptService(session).create_script(project.id, ScriptCreate(name="Script"))
            scene = SceneService(session).create_scene(
                project.id, SceneCreate(script_id=script.id, name="Scene")
            )
            ShotService(session).create_shot(
                scene.id, ShotCreate(project_id=project.id, shot_code="S01", title="Shot")
            )
        with database.engine.begin() as connection:
            config.attributes["connection"] = connection
            command.check(config)
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
            command.downgrade(config, "0001_app_settings")
            assert set(inspect(connection).get_table_names()) == {"alembic_version", "app_settings"}
            command.upgrade(config, "head")
            command.check(config)
        with database.session() as session:
            assert session.get(AppSetting, setting_id).value == {"preserve": True}
        for table in Base.metadata.sorted_tables:
            assert "AUTOINCREMENT" not in str(
                CreateTable(table).compile(dialect=postgresql.dialect())
            )
    finally:
        database.dispose()
