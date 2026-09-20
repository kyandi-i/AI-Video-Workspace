from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_workspace
from app.schemas.workspace import WorkspaceResponse, WorkspaceUpdate
from app.services.workspace import WorkspaceService

router = APIRouter(prefix="/settings", tags=["workspace"])
Workspace = Annotated[WorkspaceService, Depends(get_workspace)]


@router.get("/workspace", response_model=WorkspaceResponse)
def get_workspace_settings(workspace: Workspace) -> dict:
    return workspace.get_info()


@router.put("/workspace", response_model=WorkspaceResponse)
def switch_workspace(body: WorkspaceUpdate, workspace: Workspace) -> dict:
    return workspace.set_workspace_root(body.workspace_root)
