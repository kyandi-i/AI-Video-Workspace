from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.assets import AssetLinkCreate
from app.schemas.characters import (
    CharacterCreate,
    CharacterRead,
    CharacterUpdate,
    ShotStateCreate,
    ShotStateRead,
    StateCreate,
    StateRead,
    StateUpdate,
)
from app.schemas.workflow import ShotMove
from app.services.characters import CharacterService

router = APIRouter(tags=["Characters"])
DB = Annotated[Session, Depends(get_db)]


@router.get("/projects/{project_id}/characters", response_model=list[CharacterRead])
def list_characters(
    project_id: UUID,
    db: DB,
    search: Annotated[str | None, Query(max_length=255)] = None,
    include_deleted: bool = False,
):
    return CharacterService(db).list_characters(project_id, search, include_deleted)


@router.post("/projects/{project_id}/characters", response_model=CharacterRead, status_code=201)
def create_character(project_id: UUID, data: CharacterCreate, db: DB):
    return CharacterService(db).create_character(project_id, data)


@router.get("/characters/{character_id}/states", response_model=list[StateRead])
def list_states(character_id: UUID, db: DB, include_deleted: bool = False):
    return CharacterService(db).list_states(character_id, include_deleted)


@router.post("/characters/{character_id}/states", response_model=StateRead, status_code=201)
def create_state(character_id: UUID, data: StateCreate, db: DB):
    return CharacterService(db).create_state(character_id, data)


@router.get("/characters/{identifier}", response_model=CharacterRead)
def get_character(identifier: UUID, db: DB, include_deleted: bool = False):
    service = CharacterService(db)
    return service.read_character(service.character(identifier, include_deleted))


@router.patch("/characters/{identifier}", response_model=CharacterRead)
def update_character(identifier: UUID, data: CharacterUpdate, db: DB):
    return CharacterService(db).update_character(identifier, data)


@router.delete("/characters/{identifier}", status_code=204)
def delete_character(identifier: UUID, db: DB):
    CharacterService(db).delete_character(identifier)
    return Response(status_code=204)


@router.post("/characters/{identifier}/restore", response_model=CharacterRead)
def restore_character(identifier: UUID, db: DB):
    return CharacterService(db).restore_character(identifier)


@router.post("/characters/{identifier}/assets", response_model=CharacterRead)
def bind_character_asset(identifier: UUID, data: AssetLinkCreate, db: DB):
    return CharacterService(db).bind_asset(identifier, data.asset_id, state=False)


@router.delete("/characters/{identifier}/assets/{asset_id}", response_model=CharacterRead)
def unbind_character_asset(identifier: UUID, asset_id: UUID, db: DB):
    return CharacterService(db).bind_asset(identifier, asset_id, state=False, remove=True)


@router.get("/character-states/{identifier}", response_model=StateRead)
def get_state(identifier: UUID, db: DB, include_deleted: bool = False):
    service = CharacterService(db)
    return service.read_state(service.state(identifier, include_deleted))


@router.patch("/character-states/{identifier}", response_model=StateRead)
def update_state(identifier: UUID, data: StateUpdate, db: DB):
    return CharacterService(db).update_state(identifier, data)


@router.delete("/character-states/{identifier}", status_code=204)
def delete_state(identifier: UUID, db: DB):
    CharacterService(db).delete_state(identifier)
    return Response(status_code=204)


@router.post("/character-states/{identifier}/restore", response_model=StateRead)
def restore_state(identifier: UUID, db: DB):
    return CharacterService(db).restore_state(identifier)


@router.post("/character-states/{identifier}/assets", response_model=StateRead)
def bind_state_asset(identifier: UUID, data: AssetLinkCreate, db: DB):
    return CharacterService(db).bind_asset(identifier, data.asset_id, state=True)


@router.delete("/character-states/{identifier}/assets/{asset_id}", response_model=StateRead)
def unbind_state_asset(identifier: UUID, asset_id: UUID, db: DB):
    return CharacterService(db).bind_asset(identifier, asset_id, state=True, remove=True)


@router.post("/character-states/{identifier}/move", response_model=list[StateRead])
def move_state(identifier: UUID, data: ShotMove, db: DB):
    return CharacterService(db).move_state(identifier, data.direction)


@router.get("/shots/{shot_id}/character-states", response_model=list[ShotStateRead])
def shot_states(shot_id: UUID, db: DB):
    return CharacterService(db).list_shot_states(shot_id)


@router.post("/shots/{shot_id}/character-states", response_model=list[ShotStateRead])
def bind_shot(shot_id: UUID, data: ShotStateCreate, db: DB):
    return CharacterService(db).bind_shot(shot_id, data.character_state_id)


@router.delete("/shots/{shot_id}/character-states/{state_id}", response_model=list[ShotStateRead])
def unbind_shot(shot_id: UUID, state_id: UUID, db: DB):
    return CharacterService(db).bind_shot(shot_id, state_id, remove=True)


@router.put("/shots/{shot_id}/character-states", response_model=list[ShotStateRead])
def replace_shot_state(shot_id: UUID, data: ShotStateCreate, db: DB):
    return CharacterService(db).replace_shot_state(shot_id, data.character_state_id)
