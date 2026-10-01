from uuid import UUID

from pydantic import Field

from app.schemas.assets import AssetRead
from app.schemas.storyboards import StoryboardSource
from app.schemas.workflow import Input, Read


class VideoResultCreate(Input):
    asset_id: UUID
    source_storyboard_id: UUID | None = None
    source_prompt_record_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=10000)


class VideoStoryboardSource(Input):
    id: UUID
    version: int
    is_deleted: bool


class VideoResultRead(Read):
    shot_id: UUID
    asset_id: UUID
    source_storyboard_id: UUID | None
    source_prompt_record_id: UUID | None
    version: int
    is_selected: bool
    notes: str | None
    asset: AssetRead
    source_storyboard: VideoStoryboardSource | None
    source_prompt: StoryboardSource | None
