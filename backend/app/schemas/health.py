from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    app: Literal["ai-video-workspace"] = "ai-video-workspace"
    version: str = "0.1.0"
    phase: int = 3
    storage_initialized: bool = False
