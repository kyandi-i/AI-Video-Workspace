from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.assets import AssetRead
from app.schemas.workflow import Input, Read


class StoryboardCreate(Input):
    asset_id: UUID
    source_prompt_record_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=10000)


class StoryboardSource(Input):
    id: UUID
    version: int
    prompt_type: str
    is_edited: bool


class StoryboardRead(Read):
    shot_id: UUID
    asset_id: UUID
    source_prompt_record_id: UUID | None
    storyboard_type: Literal["GRID_6"]
    version: int
    is_selected: bool
    notes: str | None
    asset: AssetRead
    source_prompt: StoryboardSource | None
