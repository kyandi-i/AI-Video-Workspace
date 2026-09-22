from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Character(BaseModel):
    __tablename__ = "characters"
    __table_args__ = (
        UniqueConstraint("project_id", "name"),
        CheckConstraint("length(trim(name)) > 0", name="name_required"),
    )
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CharacterState(BaseModel):
    __tablename__ = "character_states"
    __table_args__ = (
        UniqueConstraint("character_id", "name"),
        CheckConstraint("length(trim(name)) > 0", name="name_required"),
        CheckConstraint("order_index >= 0", name="order_nonnegative"),
    )
    character_id: Mapped[UUID] = mapped_column(ForeignKey("characters.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(default=0)


class CharacterAssetLink(BaseModel):
    __tablename__ = "character_asset_links"
    __table_args__ = (UniqueConstraint("character_id", "asset_id"),)
    character_id: Mapped[UUID] = mapped_column(ForeignKey("characters.id"), index=True)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), index=True)


class CharacterStateAssetLink(BaseModel):
    __tablename__ = "character_state_asset_links"
    __table_args__ = (UniqueConstraint("character_state_id", "asset_id"),)
    character_state_id: Mapped[UUID] = mapped_column(ForeignKey("character_states.id"), index=True)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), index=True)


class ShotCharacterStateLink(BaseModel):
    __tablename__ = "shot_character_state_links"
    __table_args__ = (
        UniqueConstraint("shot_id", "character_state_id"),
        Index(
            "uq_shot_active_character",
            "shot_id",
            "character_id",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
    shot_id: Mapped[UUID] = mapped_column(ForeignKey("shots.id"), index=True)
    character_state_id: Mapped[UUID] = mapped_column(ForeignKey("character_states.id"), index=True)
    # Derived by the service; enables database protection against concurrent conflicts.
    character_id: Mapped[UUID] = mapped_column(ForeignKey("characters.id"), index=True)
