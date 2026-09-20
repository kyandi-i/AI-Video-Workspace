from fastapi import Request

from app.services.workspace import WorkspaceService


def get_workspace(request: Request) -> WorkspaceService:
    return request.app.state.workspace
