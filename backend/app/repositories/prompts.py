from sqlalchemy import select

from app.models.prompts import PromptRecord
from app.repositories.base import BaseRepository


class PromptRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, PromptRecord)

    def latest(self, shot_id):
        return self.session.scalar(
            select(PromptRecord)
            .where(PromptRecord.shot_id == shot_id, PromptRecord.deleted_at.is_(None))
            .order_by(PromptRecord.created_at.desc(), PromptRecord.id.desc())
            .limit(1)
        )
