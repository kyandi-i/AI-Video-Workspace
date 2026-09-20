"""Import all mapped models here so Alembic discovers their metadata."""

from app.models.app_setting import AppSetting
from app.models.base import Base, BaseModel, SoftDeleteMixin, TimestampMixin, UUIDMixin

__all__ = ["AppSetting", "Base", "BaseModel", "SoftDeleteMixin", "TimestampMixin", "UUIDMixin"]
