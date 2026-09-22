"""Mapped models for Alembic metadata discovery."""

from app.models.app_setting import AppSetting
from app.models.assets import Asset, AssetTag, ProjectAssetLink, ShotAssetLink, Tag
from app.models.base import Base, BaseModel, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.characters import (
    Character,
    CharacterAssetLink,
    CharacterState,
    CharacterStateAssetLink,
    ShotCharacterStateLink,
)
from app.models.workflow import Project, Scene, Script, ScriptNode, Shot

__all__ = [
    "Character",
    "CharacterState",
    "CharacterAssetLink",
    "CharacterStateAssetLink",
    "ShotCharacterStateLink",
    "AppSetting",
    "Base",
    "BaseModel",
    "SoftDeleteMixin",
    "TimestampMixin",
    "UUIDMixin",
    "Project",
    "Scene",
    "Script",
    "ScriptNode",
    "Shot",
    "Asset",
    "AssetTag",
    "ProjectAssetLink",
    "ShotAssetLink",
    "Tag",
]
