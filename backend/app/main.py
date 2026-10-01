from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.assets import router as assets_router
from app.api.routes.characters import router as characters_router
from app.api.routes.health import router as health_router
from app.api.routes.prompts import router as prompts_router
from app.api.routes.settings import router as settings_router
from app.api.routes.storyboards import router as storyboards_router
from app.api.routes.templates import router as templates_router
from app.api.routes.video_results import router as video_results_router
from app.api.routes.workflow import router as workflow_router
from app.core.config import Settings
from app.core.exceptions import register_exception_handlers
from app.services.ai.provider import OpenAICompatibleProvider
from app.services.ai.settings import AISettingsService, LocalAISettingsStorageProvider
from app.services.workspace import WorkspaceService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    workspace = WorkspaceService(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        workspace.initialize_workspace()
        try:
            yield
        finally:
            workspace.close()

    app = FastAPI(
        title="AI Video Workspace",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.state.workspace = workspace
    app.state.ai_provider = OpenAICompatibleProvider()
    app.state.ai_settings = AISettingsService(
        LocalAISettingsStorageProvider(workspace.bootstrap.path)
    )
    register_exception_handlers(app)
    app.include_router(health_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(workflow_router, prefix="/api")
    app.include_router(assets_router, prefix="/api")
    app.include_router(characters_router, prefix="/api")
    app.include_router(templates_router, prefix="/api")
    app.include_router(prompts_router, prefix="/api")
    app.include_router(storyboards_router, prefix="/api")
    app.include_router(video_results_router, prefix="/api")

    dist = settings.frontend_dist.resolve()

    @app.get("/assets", include_in_schema=False)
    def asset_library_page():
        index = dist / "index.html"
        if not index.is_file():
            raise HTTPException(status_code=503, detail="前端尚未构建，请运行 npm run build。")
        return FileResponse(index, headers={"Cache-Control": "no-cache"})

    if (dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="frontend-assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path == "api" or path.startswith("api/") or path.startswith("assets/"):
            raise HTTPException(status_code=404, detail="接口或资源不存在。")
        index = dist / "index.html"
        if not index.is_file():
            raise HTTPException(
                status_code=503, detail="前端尚未构建，请先在 frontend 运行 npm run build。"
            )
        return FileResponse(index, headers={"Cache-Control": "no-cache"})

    return app


app = create_app()
