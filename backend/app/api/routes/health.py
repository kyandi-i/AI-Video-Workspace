from fastapi import APIRouter, Request

from app.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    return HealthResponse(storage_initialized=request.app.state.workspace.get_info()["initialized"])
