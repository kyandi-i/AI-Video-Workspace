from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_workspace
from app.core.database import get_db
from app.models.assets import AssetType
from app.schemas.storyboards import StoryboardCreate, StoryboardRead
from app.services.storage.service import StorageService
from app.services.storyboards import StoryboardService
from app.services.workspace import WorkspaceService

router = APIRouter(tags=["Storyboards"])
DB = Annotated[Session, Depends(get_db)]
Workspace = Annotated[WorkspaceService, Depends(get_workspace)]


@router.get("/shots/{shot_id}/storyboards", response_model=list[StoryboardRead])
def history(shot_id: UUID, db: DB, include_deleted: bool = False):
    return StoryboardService(db).history(shot_id, include_deleted)


@router.post("/shots/{shot_id}/storyboards", response_model=StoryboardRead, status_code=201)
def create(shot_id: UUID, data: StoryboardCreate, db: DB):
    return StoryboardService(db).create(shot_id, data)


@router.post("/shots/{shot_id}/storyboards/import", response_model=StoryboardRead, status_code=201)
async def import_storyboard(
    shot_id: UUID,
    request: Request,
    workspace: Workspace,
    filename: str,
    source_prompt_record_id: UUID | None = None,
    notes: str | None = Query(None, max_length=10000),
):
    return await StorageService(workspace).upload(
        request.stream(),
        filename,
        AssetType.STORYBOARD_6GRID,
        storyboard=(shot_id, source_prompt_record_id, notes),
    )


@router.get("/storyboards/{identifier}", response_model=StoryboardRead)
def detail(identifier: UUID, db: DB, include_deleted: bool = False):
    return StoryboardService(db).detail(identifier, include_deleted)


@router.post("/storyboards/{identifier}/select", response_model=StoryboardRead)
def select(identifier: UUID, db: DB):
    return StoryboardService(db).select(identifier)


@router.delete("/storyboards/{identifier}", status_code=204)
def delete(identifier: UUID, db: DB):
    StoryboardService(db).delete(identifier)
    return Response(status_code=204)


@router.post("/storyboards/{identifier}/restore", response_model=StoryboardRead)
def restore(identifier: UUID, db: DB):
    return StoryboardService(db).restore(identifier)
