from sqlalchemy import func, select, update

from app.core.exceptions import AppError
from app.models.storyboards import Storyboard
from app.repositories.base import BaseRepository


class StoryboardRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, Storyboard)

    def history(self, shot_id, include_deleted=False):
        query = select(Storyboard).where(Storyboard.shot_id == shot_id)
        if not include_deleted:
            query = query.where(Storyboard.deleted_at.is_(None))
        return list(self.session.scalars(query.order_by(Storyboard.version.desc())))

    def max_version(self, shot_id):
        return (
            self.session.scalar(
                select(func.max(Storyboard.version)).where(Storyboard.shot_id == shot_id)
            )
            or 0
        )

    def clear_selection(self, shot_id):
        # Acquire SQLite's writer lock before allocating the next integer version.
        self.session.execute(
            update(Storyboard)
            .where(Storyboard.shot_id == shot_id, Storyboard.is_selected.is_(True))
            .values(is_selected=False)
        )

    def for_asset(self, asset_id):
        # Deleted parent Shots do not release live business references.
        return list(
            self.session.scalars(
                select(Storyboard).where(
                    Storyboard.asset_id == asset_id, Storyboard.deleted_at.is_(None)
                )
            )
        )

    def update(self, entity, **changes):
        if set(changes) - {"is_selected"}:
            raise AppError("IMMUTABLE_STORYBOARD_FACT", "分镜历史事实不可覆盖，请导入新版本。", 400)
        return super().update(entity, **changes)

    def soft_delete(self, entity):
        entity.is_selected = False
        return super().soft_delete(entity)
