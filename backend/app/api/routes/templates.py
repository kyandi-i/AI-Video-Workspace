from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.templates import TemplateCategory, TemplateScope
from app.schemas.templates import (
    TemplateCopy,
    TemplateCreate,
    TemplatePreview,
    TemplateRead,
    TemplateUpdate,
)
from app.services.template_placeholders import PLACEHOLDERS, SAMPLE_CONTEXT, render_content
from app.services.templates import PromptTemplateService

router = APIRouter(prefix="/prompt-templates", tags=["Prompt Templates"])
DB = Annotated[Session, Depends(get_db)]


@router.get("/placeholders")
def placeholders():
    return PLACEHOLDERS


@router.post("/preview")
def preview(data: TemplatePreview):
    return {"rendered_content": render_content(data.template_content, SAMPLE_CONTEXT)}


@router.get("", response_model=list[TemplateRead])
def list_templates(
    db: DB,
    scope: TemplateScope | None = None,
    project_id: UUID | None = None,
    category: TemplateCategory | None = None,
    search: Annotated[str | None, Query(max_length=255)] = None,
    include_deleted: bool = False,
    include_global: bool = False,
):
    return PromptTemplateService(db).list_templates(
        scope=scope,
        project_id=project_id,
        category=category,
        search=search,
        include_deleted=include_deleted,
        include_global=include_global,
    )


@router.post("", response_model=TemplateRead, status_code=201)
def create(data: TemplateCreate, db: DB):
    return PromptTemplateService(db).create(data)


@router.get("/{identifier}", response_model=TemplateRead)
def detail(identifier: UUID, db: DB, include_deleted: bool = False):
    return PromptTemplateService(db).detail(identifier, include_deleted)


@router.patch("/{identifier}", response_model=TemplateRead)
def update(identifier: UUID, data: TemplateUpdate, db: DB):
    return PromptTemplateService(db).update(identifier, data)


@router.delete("/{identifier}", status_code=204)
def delete(identifier: UUID, db: DB):
    PromptTemplateService(db).delete(identifier)
    return Response(status_code=204)


@router.post("/{identifier}/restore", response_model=TemplateRead)
def restore(identifier: UUID, db: DB):
    return PromptTemplateService(db).restore(identifier)


@router.post("/{identifier}/duplicate", response_model=TemplateRead, status_code=201)
def duplicate(identifier: UUID, db: DB):
    return PromptTemplateService(db).duplicate(identifier)


@router.post("/{identifier}/copy-to-project", response_model=TemplateRead, status_code=201)
def copy_to_project(identifier: UUID, data: TemplateCopy, db: DB):
    return PromptTemplateService(db).copy_to_project(identifier, data.project_id)
