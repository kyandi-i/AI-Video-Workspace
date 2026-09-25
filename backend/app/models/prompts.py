from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class PromptRecord(BaseModel):
    """Immutable successful generation fact; no versioning/selection/edit APIs."""

    __tablename__ = "prompt_records"
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
