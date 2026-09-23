from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ProjectStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class NodeType(StrEnum):
    CHAPTER = "CHAPTER"
    SEQUENCE = "SEQUENCE"
    SCENE = "SCENE"
    OTHER = "OTHER"


class ShotStatus(StrEnum):
    DRAFT = "DRAFT"
    ASSET_PREPARING = "ASSET_PREPARING"
    STORYBOARD_PROMPT_READY = "STORYBOARD_PROMPT_READY"
    STORYBOARD_READY = "STORYBOARD_READY"
    VIDEO_PROMPT_READY = "VIDEO_PROMPT_READY"
    VIDEO_GENERATING = "VIDEO_GENERATING"
    REVIEW = "REVIEW"
    DONE = "DONE"


def enum_type(cls):
    return Enum(cls, native_enum=False, create_constraint=True, name=cls.__name__.lower())


class Project(BaseModel):
    __tablename__ = "projects"
    __table_args__ = (CheckConstraint("length(trim(name)) > 0", name="name_required"),)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ProjectStatus] = mapped_column(
        enum_type(ProjectStatus), default=ProjectStatus.DRAFT
    )


class Script(BaseModel):
    __tablename__ = "scripts"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")


class ScriptNode(BaseModel):
    __tablename__ = "script_nodes"
    __table_args__ = (CheckConstraint("order_index >= 0", name="order_nonnegative"),)

    script_id: Mapped[UUID] = mapped_column(ForeignKey("scripts.id"), index=True)
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("script_nodes.id"), nullable=True)
    node_type: Mapped[NodeType] = mapped_column(enum_type(NodeType))
    # SCENE nodes leave title/description empty: Scene owns business content.
    title: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(default=0)


class Scene(BaseModel):
    __tablename__ = "scenes"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    script_node_id: Mapped[UUID] = mapped_column(ForeignKey("script_nodes.id"), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    fixed_constraints: Mapped[str] = mapped_column(Text, default="")
    negative_constraints: Mapped[str] = mapped_column(Text, default="")


class Shot(BaseModel):
    __tablename__ = "shots"
    __table_args__ = (
        UniqueConstraint("project_id", "shot_code"),
        CheckConstraint("duration_seconds >= 0", name="duration_nonnegative"),
        CheckConstraint("order_index >= 0", name="order_nonnegative"),
        CheckConstraint("length(trim(shot_code)) > 0", name="code_required"),
        CheckConstraint("length(trim(title)) > 0", name="title_required"),
    )

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    scene_id: Mapped[UUID] = mapped_column(ForeignKey("scenes.id"), index=True)
    shot_code: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    duration_seconds: Mapped[float] = mapped_column(default=0)
    order_index: Mapped[int] = mapped_column(default=0)
    status: Mapped[ShotStatus] = mapped_column(enum_type(ShotStatus), default=ShotStatus.DRAFT)
    creative_requirement: Mapped[str] = mapped_column(Text, default="")
    main_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    negative_constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    free_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
