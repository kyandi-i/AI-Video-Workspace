from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Storyboard(BaseModel):
    __tablename__ = "storyboards"
    __table_args__ = (
        UniqueConstraint("shot_id", "version", name="uq_storyboard_version"),
        CheckConstraint("version > 0", name="storyboard_version_positive"),
        CheckConstraint("storyboard_type = 'GRID_6'", name="storyboard_type_grid6"),
        Index(
            "uq_storyboard_selected",
            "shot_id",
            unique=True,
            sqlite_where=text("is_selected = 1 AND deleted_at IS NULL"),
            postgresql_where=text("is_selected = true AND deleted_at IS NULL"),
        ),
    )
    shot_id: Mapped[UUID] = mapped_column(ForeignKey("shots.id"), index=True)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), index=True)
    source_prompt_record_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("prompt_records.id"), index=True
    )
    storyboard_type: Mapped[str] = mapped_column(String(20), default="GRID_6")
    version: Mapped[int] = mapped_column(Integer)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
