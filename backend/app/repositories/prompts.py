from sqlalchemy import func, select, update

from app.core.exceptions import AppError
from app.models.prompts import PromptRecord
from app.repositories.base import BaseRepository


class PromptRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, PromptRecord)

    def history(self, shot_id, prompt_type=None):
        query = select(PromptRecord).where(
            PromptRecord.shot_id == shot_id, PromptRecord.deleted_at.is_(None)
        )
        if prompt_type is not None:
            query = query.where(PromptRecord.prompt_type == prompt_type)
        return list(
            self.session.scalars(
                query.order_by(
                    PromptRecord.version.desc(),
                    PromptRecord.created_at.desc(),
                    PromptRecord.id.desc(),
                )
            )
        )

    def max_version(self, shot_id, prompt_type):
        # Include deleted records: version numbers are never reused.
        return (
            self.session.scalar(
                select(func.max(PromptRecord.version)).where(
                    PromptRecord.shot_id == shot_id, PromptRecord.prompt_type == prompt_type
                )
            )
            or 0
        )

    def clear_selection(self, shot_id, prompt_type):
        self.session.execute(
            update(PromptRecord)
            .where(
                PromptRecord.shot_id == shot_id,
                PromptRecord.prompt_type == prompt_type,
                PromptRecord.is_selected.is_(True),
            )
            .values(is_selected=False)
        )

    def update(self, entity, **changes):
        if set(changes) - {"edited_content", "is_selected"}:
            raise AppError("IMMUTABLE_PROMPT_FACT", "原始生成事实不可修改。", 400)
        return super().update(entity, **changes)

    def soft_delete(self, entity):
        entity.is_selected = False
        return super().soft_delete(entity)

    def latest(self, shot_id):
        return self.session.scalar(
            select(PromptRecord)
            .where(PromptRecord.shot_id == shot_id, PromptRecord.deleted_at.is_(None))
            .order_by(PromptRecord.created_at.desc(), PromptRecord.id.desc())
            .limit(1)
        )
