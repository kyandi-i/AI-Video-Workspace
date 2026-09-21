from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_workspace
from app.core.database import get_db
from app.models.assets import AssetType
from app.schemas.assets import (
    AssetDetail,
    AssetLinkCreate,
    AssetRead,
    AssetUpdate,
    TagCreate,
    TagRead,
)
from app.services.assets import AssetService
from app.services.storage.service import StorageService
from app.services.workspace import WorkspaceService

router = APIRouter(tags=["Assets"])
DB = Annotated[Session, Depends(get_db)]
Workspace = Annotated[WorkspaceService, Depends(get_workspace)]


@router.post("/assets/upload", response_model=AssetDetail, status_code=201)
async def upload(
    request: Request, workspace: Workspace, filename: str, asset_type: AssetType | None = None
):
    return await StorageService(workspace).upload(request.stream(), filename, asset_type)


@router.get("/assets", response_model=list[AssetRead])
def list_assets(
    db: DB,
    search: str | None = None,
    asset_type: AssetType | None = None,
    tag_id: UUID | None = None,
    project_id: UUID | None = None,
    shot_id: UUID | None = None,
    include_deleted: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    return AssetService(db).list_assets(
        search=search,
        asset_type=asset_type,
        tag_id=tag_id,
        project_id=project_id,
        shot_id=shot_id,
        include_deleted=include_deleted,
        offset=offset,
        limit=limit,
    )


@router.get("/assets/{identifier}", response_model=AssetDetail)
def detail(identifier: UUID, db: DB, include_deleted: bool = False):
    return AssetService(db).detail(identifier, include_deleted)


@router.patch("/assets/{identifier}", response_model=AssetDetail)
def update(identifier: UUID, data: AssetUpdate, db: DB):
    return AssetService(db).update_asset(identifier, data)


@router.delete("/assets/{identifier}", status_code=204)
def delete(identifier: UUID, db: DB):
    AssetService(db).delete_asset(identifier)
    return Response(status_code=204)


@router.post("/assets/{identifier}/restore", response_model=AssetDetail)
def restore(identifier: UUID, db: DB):
    return AssetService(db).restore_asset(identifier)


@router.get("/assets/{identifier}/file")
def original(identifier: UUID, workspace: Workspace):
    path, mime = StorageService(workspace).file(identifier)
    return FileResponse(path, media_type=mime, headers={"X-Content-Type-Options": "nosniff"})


@router.get("/assets/{identifier}/thumbnail")
def thumbnail(identifier: UUID, workspace: Workspace):
    path, mime = StorageService(workspace).file(identifier, True)
    return FileResponse(path, media_type=mime, headers={"X-Content-Type-Options": "nosniff"})


@router.get("/tags", response_model=list[TagRead])
def tags(db: DB):
    return AssetService(db).list_tags()


@router.post("/tags", response_model=TagRead, status_code=201)
def create_tag(data: TagCreate, db: DB):
    return AssetService(db).create_tag(data)


@router.post("/assets/{identifier}/tags/{tag_id}", response_model=AssetDetail)
def tag_asset(identifier: UUID, tag_id: UUID, db: DB):
    return AssetService(db).tag_asset(identifier, tag_id)


@router.delete("/assets/{identifier}/tags/{tag_id}", response_model=AssetDetail)
def untag_asset(identifier: UUID, tag_id: UUID, db: DB):
    return AssetService(db).tag_asset(identifier, tag_id, True)


@router.post("/projects/{project_id}/assets", response_model=AssetDetail)
def bind_project(project_id: UUID, data: AssetLinkCreate, db: DB):
    return AssetService(db).bind(data.asset_id, project_id, "project")


@router.delete("/projects/{project_id}/assets/{identifier}", response_model=AssetDetail)
def unbind_project(project_id: UUID, identifier: UUID, db: DB):
    return AssetService(db).bind(identifier, project_id, "project", True)


@router.post("/shots/{shot_id}/assets", response_model=AssetDetail)
def bind_shot(shot_id: UUID, data: AssetLinkCreate, db: DB):
    return AssetService(db).bind(data.asset_id, shot_id, "shot")


@router.delete("/shots/{shot_id}/assets/{identifier}", response_model=AssetDetail)
def unbind_shot(shot_id: UUID, identifier: UUID, db: DB):
    return AssetService(db).bind(identifier, shot_id, "shot", True)
