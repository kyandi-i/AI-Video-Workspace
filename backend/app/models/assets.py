from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.workflow import enum_type


class AssetType(StrEnum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    STORYBOARD_6GRID = "STORYBOARD_6GRID"
    OTHER = "OTHER"


class Asset(BaseModel):
    __tablename__ = "assets"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="name_required"),
        CheckConstraint("file_size > 0", name="size_positive"),
        CheckConstraint("width > 0 AND height > 0", name="dimensions_positive"),
        CheckConstraint("duration_seconds >= 0", name="duration_nonnegative"),
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    asset_type: Mapped[AssetType] = mapped_column(enum_type(AssetType))
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(512), unique=True)
    thumbnail_path: Mapped[str] = mapped_column(String(512), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int]
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    width: Mapped[int | None]
    height: Mapped[int | None]
    duration_seconds: Mapped[float | None]


class Tag(BaseModel):
    __tablename__ = "tags"
    __table_args__ = (CheckConstraint("length(trim(name)) > 0", name="name_required"),)
    name: Mapped[str] = mapped_column(String(80))
    normalized_name: Mapped[str] = mapped_column(String(160), unique=True)


class AssetTag(BaseModel):
    __tablename__ = "asset_tags"
    __table_args__ = (UniqueConstraint("asset_id", "tag_id"),)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), index=True)
    tag_id: Mapped[UUID] = mapped_column(ForeignKey("tags.id"), index=True)


class ProjectAssetLink(BaseModel):
    __tablename__ = "project_asset_links"
    __table_args__ = (UniqueConstraint("project_id", "asset_id"),)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), index=True)


class ShotAssetLink(BaseModel):
    __tablename__ = "shot_asset_links"
    __table_args__ = (UniqueConstraint("shot_id", "asset_id"),)
    shot_id: Mapped[UUID] = mapped_column(ForeignKey("shots.id"), index=True)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), index=True)
