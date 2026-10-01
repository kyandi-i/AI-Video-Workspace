from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class VideoResult(BaseModel):
    __tablename__ = "video_results"
    __table_args__ = (
        UniqueConstraint("shot_id", "version", name="uq_video_result_version"),
        CheckConstraint("version > 0", name="video_result_version_positive"),
        Index(
            "uq_video_result_selected",
            "shot_id",
            unique=True,
            sqlite_where=text("is_selected = 1 AND deleted_at IS NULL"),
            postgresql_where=text("is_selected = true AND deleted_at IS NULL"),
        ),
    )
    shot_id: Mapped[UUID] = mapped_column(ForeignKey("shots.id"), index=True)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), index=True)
    source_storyboard_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("storyboards.id"), index=True
    )
    source_prompt_record_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("prompt_records.id"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
