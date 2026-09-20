from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.base import BaseModel, utc_now


class BaseRepository[Model: BaseModel]:
    """Flush only. The service owns the transaction and commit/rollback boundary."""

    def __init__(self, session: Session, model: type[Model]):
        self.session = session
        self.model = model

    def get(self, entity_id: UUID, *, include_deleted: bool = False) -> Model | None:
        query = select(self.model).where(self.model.id == entity_id)
        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        return self.session.scalar(query)

    def list(
        self, *, include_deleted: bool = False, offset: int = 0, limit: int = 100
    ) -> list[Model]:
        if offset < 0 or not 1 <= limit <= 1000:
            raise AppError("INVALID_PAGINATION", "分页参数无效。")
        query = select(self.model)
        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        query = query.order_by(self.model.created_at, self.model.id).offset(offset).limit(limit)
        return list(self.session.scalars(query))

    def add(self, entity: Model) -> Model:
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: Model, **changes) -> Model:
        allowed = set(self.model.__table__.columns.keys()) - {
            "id",
            "created_at",
            "updated_at",
            "deleted_at",
        }
        if set(changes) - allowed:
            raise AppError("INVALID_FIELDS", "包含不允许更新的字段。")
        for key, value in changes.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity

    def soft_delete(self, entity: Model) -> Model:
        if entity.deleted_at is None:
            entity.deleted_at = utc_now()
            self.session.flush()
        return entity

    def restore(self, entity: Model) -> Model:
        entity.deleted_at = None
        self.session.flush()
        return entity
