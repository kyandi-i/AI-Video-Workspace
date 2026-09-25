from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ai import (
    PromptGenerate,
    PromptPreview,
    PromptPreviewRequest,
    PromptRead,
    ProviderRead,
    ProviderUpdate,
)
from app.services.ai.service import AIService

router = APIRouter(tags=["AI Prompts"])


def get_ai_service(request: Request, db: Annotated[Session, Depends(get_db)]):
    return AIService(db, request.app.state.ai_provider, request.app.state.ai_settings)


AI = Annotated[AIService, Depends(get_ai_service)]


@router.get("/settings/ai", response_model=ProviderRead)
def read_settings(request: Request):
    return request.app.state.ai_settings.read()


@router.put("/settings/ai", response_model=ProviderRead)
def update_settings(data: ProviderUpdate, request: Request):
    return request.app.state.ai_settings.update(data)


@router.post("/shots/{shot_id}/prompts/preview", response_model=PromptPreview)
def preview(shot_id: UUID, data: PromptPreviewRequest, service: AI):
    return service.preview(shot_id, data.template_id)


@router.post("/shots/{shot_id}/prompts/generate", response_model=PromptRead)
def generate(shot_id: UUID, data: PromptGenerate, service: AI):
    return service.generate(shot_id, data)


@router.get("/shots/{shot_id}/prompts/latest", response_model=PromptRead | None)
def latest(shot_id: UUID, service: AI):
    return service.latest(shot_id)


@router.get("/prompts/{identifier}", response_model=PromptRead)
def detail(identifier: UUID, service: AI):
    return service.detail(identifier)
