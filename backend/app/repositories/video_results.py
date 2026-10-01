from sqlalchemy import func, select, update

from app.core.exceptions import AppError
from app.models.video_results import VideoResult
from app.repositories.base import BaseRepository


class VideoResultRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, VideoResult)

    def history(self, shot_id, include_deleted=False):
        query = select(VideoResult).where(VideoResult.shot_id == shot_id)
        if not include_deleted:
            query = query.where(VideoResult.deleted_at.is_(None))
        return list(self.session.scalars(query.order_by(VideoResult.version.desc())))

    def max_version(self, shot_id):
        return (
            self.session.scalar(
                select(func.max(VideoResult.version)).where(VideoResult.shot_id == shot_id)
            )
            or 0
        )

    def clear_selection(self, shot_id):
        # Acquire the writer lock before MAX+1, as in Storyboard.
        self.session.execute(
            update(VideoResult)
            .where(VideoResult.shot_id == shot_id, VideoResult.is_selected.is_(True))
            .values(is_selected=False)
        )

    def for_asset(self, asset_id):
        return list(
            self.session.scalars(
                select(VideoResult).where(
                    VideoResult.asset_id == asset_id, VideoResult.deleted_at.is_(None)
                )
            )
        )

    def update(self, entity, **changes):
        if set(changes) - {"is_selected"}:
            raise AppError(
                "IMMUTABLE_VIDEO_RESULT_FACT", "视频历史事实不可覆盖，请导入新版本。", 400
            )
        return super().update(entity, **changes)

    def soft_delete(self, entity):
        entity.is_selected = False
        return super().soft_delete(entity)
