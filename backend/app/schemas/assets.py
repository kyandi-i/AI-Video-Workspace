from typing import Annotated
from uuid import UUID

from pydantic import StringConstraints

from app.models.assets import AssetType
from app.schemas.workflow import Input, Name, ProjectRead, Read, ShotRead, Update


class AssetUpdate(Update):
    name: Name | None = None
    description: str | None = None
    asset_type: AssetType | None = None


class TagCreate(Input):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class TagRead(Read):
    name: str


class AssetRead(Read):
    name: str
    description: str
    asset_type: AssetType
    original_filename: str
    storage_path: str
    thumbnail_path: str
    mime_type: str
    file_size: int
    checksum: str
    width: int | None
    height: int | None
    duration_seconds: float | None
    tags: list[TagRead] = []


class CharacterReference(Read):
    project_id: UUID
    name: str


class StateReference(Read):
    character_id: UUID
    name: str


class StoryboardReference(Read):
    shot_id: UUID
    version: int
    is_selected: bool


class AssetDetail(AssetRead):
    projects: list[ProjectRead] = []
    shots: list[ShotRead] = []
    characters: list[CharacterReference] = []
    character_states: list[StateReference] = []
    storyboards: list[StoryboardReference] = []


class AssetLinkCreate(Input):
    asset_id: UUID
