from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.workflow import enum_type


class TemplateScope(StrEnum):
    GLOBAL = "GLOBAL"
    PROJECT = "PROJECT"


class TemplateCategory(StrEnum):
    STORYBOARD_6GRID = "STORYBOARD_6GRID"
    VIDEO_GENERATION = "VIDEO_GENERATION"
    CHARACTER_IMAGE = "CHARACTER_IMAGE"
    SCENE_IMAGE = "SCENE_IMAGE"
    IMAGE_REFERENCE = "IMAGE_REFERENCE"
    START_END_FRAME = "START_END_FRAME"
    OTHER = "OTHER"


class PromptTemplate(BaseModel):
    __tablename__ = "prompt_templates"
    __table_args__ = (
        CheckConstraint(
            "(scope = 'GLOBAL' AND project_id IS NULL) OR "
            "(scope = 'PROJECT' AND project_id IS NOT NULL)",
            name="scope_project",
        ),
        CheckConstraint("length(trim(name)) BETWEEN 1 AND 255", name="name_required"),
        CheckConstraint(
            "length(trim(template_content)) > 0 AND length(template_content) <= 100000",
            name="content_required",
        ),
        Index(
            "uq_template_global_name",
            "name",
            unique=True,
            sqlite_where=text("scope = 'GLOBAL'"),
            postgresql_where=text("scope = 'GLOBAL'"),
        ),
        Index("uq_template_project_name", "project_id", "name", unique=True),
    )
    scope: Mapped[TemplateScope] = mapped_column(enum_type(TemplateScope), index=True)
    project_id: Mapped[UUID | None] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[TemplateCategory] = mapped_column(enum_type(TemplateCategory), index=True)
    template_content: Mapped[str] = mapped_column(Text)
