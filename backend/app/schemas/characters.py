from uuid import UUID

from pydantic import model_validator

from app.schemas.assets import AssetRead
from app.schemas.workflow import Input, Name, Read, Update


class CharacterCreate(Input):
    name: Name
    description: str = ""
    notes: str | None = None


class CharacterUpdate(Input):
    name: Name | None = None
    description: str | None = None
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_required_null(cls, value):
        if isinstance(value, dict) and any(
            value[k] is None for k in ("name", "description") if k in value
        ):
            raise ValueError("名称和描述不能为 null。")
        return value


class StateCreate(Input):
    name: Name
    description: str = ""


class StateUpdate(Update):
    name: Name | None = None
    description: str | None = None


class CharacterRead(Read):
    project_id: UUID
    name: str
    description: str
    notes: str | None
    state_count: int = 0
    asset_count: int = 0
    assets: list[AssetRead] = []


class StateRead(Read):
    character_id: UUID
    name: str
    description: str
    order_index: int
    shot_usage_count: int = 0
    assets: list[AssetRead] = []


class ShotStateRead(StateRead):
    character_name: str


class ShotStateCreate(Input):
    character_state_id: UUID
