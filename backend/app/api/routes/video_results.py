from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_workspace
from app.core.database import get_db
from app.models.assets import AssetType
from app.schemas.video_results import VideoResultCreate, VideoResultRead
from app.services.storage.service import StorageService
from app.services.video_results import VideoResultService
from app.services.workspace import WorkspaceService

router = APIRouter(tags=["Video Results"])
DB = Annotated[Session, Depends(get_db)]
Workspace = Annotated[WorkspaceService, Depends(get_workspace)]


@router.get("/shots/{shot_id}/video-results", response_model=list[VideoResultRead])
def history(shot_id: UUID, db: DB, include_deleted: bool = False):
    return VideoResultService(db).history(shot_id, include_deleted)


@router.post("/shots/{shot_id}/video-results", response_model=VideoResultRead, status_code=201)
def create(shot_id: UUID, data: VideoResultCreate, db: DB):
    return VideoResultService(db).create(shot_id, data)


@router.post(
    "/shots/{shot_id}/video-results/import", response_model=VideoResultRead, status_code=201
)
async def import_video(
    shot_id: UUID,
    request: Request,
    workspace: Workspace,
    filename: str,
    source_storyboard_id: UUID | None = None,
    source_prompt_record_id: UUID | None = None,
    notes: str | None = Query(None, max_length=10000),
):
    def create_result(session, asset_id):
        return VideoResultService(session).create(
            shot_id,
            VideoResultCreate(
                asset_id=asset_id,
                source_storyboard_id=source_storyboard_id,
                source_prompt_record_id=source_prompt_record_id,
                notes=notes,
            ),
        )

    return await StorageService(workspace).upload(
        request.stream(), filename, AssetType.VIDEO, create_result=create_result
    )


@router.get("/video-results/{identifier}", response_model=VideoResultRead)
def detail(identifier: UUID, db: DB, include_deleted: bool = False):
    return VideoResultService(db).detail(identifier, include_deleted)


@router.post("/video-results/{identifier}/select", response_model=VideoResultRead)
def select(identifier: UUID, db: DB):
    return VideoResultService(db).select(identifier)


@router.delete("/video-results/{identifier}", status_code=204)
def delete(identifier: UUID, db: DB):
    VideoResultService(db).delete(identifier)
    return Response(status_code=204)


@router.post("/video-results/{identifier}/restore", response_model=VideoResultRead)
def restore(identifier: UUID, db: DB):
    return VideoResultService(db).restore(identifier)
