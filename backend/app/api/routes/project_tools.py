from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import get_workspace
from app.core.database import get_db
from app.schemas.recycle_bin import EntityType, RecycleBinPage
from app.services.project_export import ProjectExportService
from app.services.recycle_bin import RecycleBinService
from app.services.workspace import WorkspaceService

router = APIRouter(tags=["Export / Recycle Bin"])


class ExportResponse(StreamingResponse):
    """Close provider staging even on disconnect or failed ASGI send."""

    def __init__(self, context, source, name):
        self.export_context = context
        super().__init__(
            iter(lambda: source.read(1024 * 1024), b""),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}",
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            await run_in_threadpool(self.export_context.__exit__, None, None, None)


@router.post("/projects/{project_id}/export")
def export_project(
    project_id: UUID, workspace: Annotated[WorkspaceService, Depends(get_workspace)]
):
    context = ProjectExportService(workspace).archive(project_id)
    source, name = context.__enter__()
    try:
        return ExportResponse(context, source, name)
    except BaseException:
        context.__exit__(None, None, None)
        raise


@router.get("/recycle-bin", response_model=RecycleBinPage)
def recycle_bin(
    db: Annotated[Session, Depends(get_db)],
    entity_type: EntityType | None = None,
    search: str | None = Query(None, max_length=255),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    return RecycleBinService(db).list(entity_type, search, offset, limit)
