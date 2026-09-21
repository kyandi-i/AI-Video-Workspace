from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.workflow import ShotStatus
from app.schemas.workflow import (
    ProjectCreate,
    ProjectRead,
    ProjectStats,
    ProjectUpdate,
    SceneCreate,
    SceneRead,
    SceneUpdate,
    ScriptCreate,
    ScriptRead,
    ScriptUpdate,
    ShotCreate,
    ShotMove,
    ShotRead,
    ShotUpdate,
)
from app.services.workflow import ProjectService, SceneService, ScriptService, ShotService

router = APIRouter(tags=["Project workflow"])
DB = Annotated[Session, Depends(get_db)]


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(db: DB, include_deleted: bool = False):
    return ProjectService(db).list_projects(include_deleted)


@router.post("/projects", response_model=ProjectRead, status_code=201)
def create_project(data: ProjectCreate, db: DB):
    return ProjectService(db).create_project(data)


@router.get("/projects/{identifier}", response_model=ProjectRead)
def get_project(identifier: UUID, db: DB, include_deleted: bool = False):
    service = ProjectService(db)
    entity = service.project(identifier, include_deleted)
    return entity


@router.patch("/projects/{identifier}", response_model=ProjectRead)
def update_project(identifier: UUID, data: ProjectUpdate, db: DB):
    return ProjectService(db).update_project(identifier, data)


@router.delete("/projects/{identifier}", status_code=204)
def delete_project(identifier: UUID, db: DB):
    ProjectService(db).delete_project(identifier)
    return Response(status_code=204)


@router.post("/projects/{identifier}/restore", response_model=ProjectRead)
def restore_project(identifier: UUID, db: DB):
    return ProjectService(db).restore_project(identifier)


@router.get("/projects/{project_id}/scripts", response_model=list[ScriptRead])
def list_scripts(project_id: UUID, db: DB, include_deleted: bool = False):
    return ScriptService(db).list_scripts(project_id, include_deleted)


@router.post("/projects/{project_id}/scripts", response_model=ScriptRead, status_code=201)
def create_script(project_id: UUID, data: ScriptCreate, db: DB):
    return ScriptService(db).create_script(project_id, data)


@router.get("/scripts/{identifier}", response_model=ScriptRead)
def get_script(identifier: UUID, db: DB, include_deleted: bool = False):
    service = ScriptService(db)
    entity = service.script(identifier, include_deleted)
    return entity


@router.patch("/scripts/{identifier}", response_model=ScriptRead)
def update_script(identifier: UUID, data: ScriptUpdate, db: DB):
    return ScriptService(db).update_script(identifier, data)


@router.delete("/scripts/{identifier}", status_code=204)
def delete_script(identifier: UUID, db: DB):
    ScriptService(db).delete_script(identifier)
    return Response(status_code=204)


@router.post("/scripts/{identifier}/restore", response_model=ScriptRead)
def restore_script(identifier: UUID, db: DB):
    return ScriptService(db).restore_script(identifier)


@router.get("/projects/{project_id}/scenes", response_model=list[SceneRead])
def list_scenes(project_id: UUID, db: DB, include_deleted: bool = False):
    return SceneService(db).list_scenes(project_id, include_deleted)


@router.post("/projects/{project_id}/scenes", response_model=SceneRead, status_code=201)
def create_scene(project_id: UUID, data: SceneCreate, db: DB):
    return SceneService(db).create_scene(project_id, data)


@router.get("/scenes/{identifier}", response_model=SceneRead)
def get_scene(identifier: UUID, db: DB, include_deleted: bool = False):
    service = SceneService(db)
    entity = service.scene(identifier, include_deleted)
    return service.read(entity)


@router.patch("/scenes/{identifier}", response_model=SceneRead)
def update_scene(identifier: UUID, data: SceneUpdate, db: DB):
    return SceneService(db).update_scene(identifier, data)


@router.delete("/scenes/{identifier}", status_code=204)
def delete_scene(identifier: UUID, db: DB):
    SceneService(db).delete_scene(identifier)
    return Response(status_code=204)


@router.post("/scenes/{identifier}/restore", response_model=SceneRead)
def restore_scene(identifier: UUID, db: DB):
    return SceneService(db).restore_scene(identifier)


@router.post("/scenes/{scene_id}/shots", response_model=ShotRead, status_code=201)
def create_shot(scene_id: UUID, data: ShotCreate, db: DB):
    return ShotService(db).create_shot(scene_id, data)


@router.get("/shots/{identifier}", response_model=ShotRead)
def get_shot(identifier: UUID, db: DB, include_deleted: bool = False):
    service = ShotService(db)
    entity = service.shot(identifier, include_deleted)
    return entity


@router.patch("/shots/{identifier}", response_model=ShotRead)
def update_shot(identifier: UUID, data: ShotUpdate, db: DB):
    return ShotService(db).update_shot(identifier, data)


@router.delete("/shots/{identifier}", status_code=204)
def delete_shot(identifier: UUID, db: DB):
    ShotService(db).soft_delete_shot(identifier)
    return Response(status_code=204)


@router.post("/shots/{identifier}/restore", response_model=ShotRead)
def restore_shot(identifier: UUID, db: DB):
    return ShotService(db).restore_shot(identifier)


@router.get("/projects/{project_id}/stats", response_model=ProjectStats)
def project_stats(project_id: UUID, db: DB):
    return ProjectService(db).stats(project_id)


@router.get("/projects/{project_id}/shots", response_model=list[ShotRead])
def project_shots(
    project_id: UUID,
    db: DB,
    scene_id: UUID | None = None,
    status: ShotStatus | None = None,
    search: Annotated[str | None, Query(max_length=255)] = None,
    include_deleted: bool = False,
):
    return ShotService(db).list_shots(
        project_id, scene_id=scene_id, status=status, search=search, include_deleted=include_deleted
    )


@router.get("/scenes/{scene_id}/shots", response_model=list[ShotRead])
def scene_shots(scene_id: UUID, db: DB, include_deleted: bool = False):
    service = ShotService(db)
    scene = service.scene(scene_id, include_deleted)
    return service.list_shots(scene.project_id, scene_id=scene_id, include_deleted=include_deleted)


@router.post("/shots/{identifier}/move", response_model=list[ShotRead])
def move_shot(identifier: UUID, data: ShotMove, db: DB):
    return ShotService(db).move_shot(identifier, data.direction)
