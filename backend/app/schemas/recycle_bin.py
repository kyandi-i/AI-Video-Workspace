from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

EntityType = Literal[
    "projects",
    "scripts",
    "scenes",
    "shots",
    "assets",
    "characters",
    "character-states",
    "prompt-templates",
    "storyboards",
    "video-results",
]


class RecycleBinItem(BaseModel):
    entity_type: EntityType
    entity_id: UUID
    display_name: str
    deleted_at: datetime
    project_id: UUID | None
    context: str


class RecycleBinPage(BaseModel):
    items: list[RecycleBinItem]
    total: int
