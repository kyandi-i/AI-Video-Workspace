from uuid import UUID

from sqlalchemy import (
    JSON,
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


class PromptRecord(BaseModel):
    """Generation facts plus a mutable human edit and selection."""

    __tablename__ = "prompt_records"
    __table_args__ = (
        UniqueConstraint("shot_id", "prompt_type", "version", name="uq_prompt_version"),
        CheckConstraint("version > 0", name="prompt_version_positive"),
        Index(
            "uq_prompt_selected",
            "shot_id",
            "prompt_type",
            unique=True,
            sqlite_where=text("is_selected = 1 AND deleted_at IS NULL"),
            postgresql_where=text("is_selected = true AND deleted_at IS NULL"),
        ),
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    edited_content: Mapped[str | None] = mapped_column(Text)
    is_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    @property
    def effective_content(self) -> str:
        return self.edited_content if self.edited_content is not None else self.generated_content

    shot_id: Mapped[UUID] = mapped_column(ForeignKey("shots.id"), index=True)
    template_id: Mapped[UUID] = mapped_column(ForeignKey("prompt_templates.id"), index=True)
    template_name: Mapped[str] = mapped_column(String(255))
    template_content: Mapped[str] = mapped_column(Text)
    prompt_type: Mapped[str] = mapped_column(String(40))
    context_json: Mapped[dict] = mapped_column(JSON)
    rendered_input: Mapped[str] = mapped_column(Text)
    input_hash: Mapped[str] = mapped_column(String(64))
    generated_content: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(80))
    model_name: Mapped[str] = mapped_column(String(255))
