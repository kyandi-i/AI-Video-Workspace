from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AppSetting(BaseModel):
    """Ordinary per-workspace settings only; not credentials or bootstrap selection."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(
        JSON, nullable=False
    )
