from pydantic import BaseModel

from app.schemas.assets import AssetRead
from app.schemas.characters import ShotStateRead
from app.schemas.workflow import SceneRead, ShotRead


class ShotWorkspaceRead(BaseModel):
    shot: ShotRead
    scene: SceneRead
    character_states: list[ShotStateRead]
    assets: list[AssetRead]
    previous_shot: ShotRead | None
    next_shot: ShotRead | None
    position: int
    total: int
