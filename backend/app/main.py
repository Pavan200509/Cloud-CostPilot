from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import get_settings
from app.logging_setup import RequestLogMiddleware, configure_logging
from app.services.pipeline import run_pipeline
from app.services.scheduler import scheduler

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()

    def _job(project_id: str) -> None:
        run_pipeline(get_settings(), project_id)

    scheduler.configure(settings.refresh_interval_seconds, _job)
    yield


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="2.0.0",
        description="Cloud CostPilot — intelligent cloud cost recommendations (read-only).",
        lifespan=lifespan,
    )
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLogMiddleware)
    app.include_router(router)

    # Product UI at /  — Swagger stays at /docs for developers only.
    # Serve production React/Vite frontend.
    # API routes are registered before this fallback.
    if STATIC_DIR.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=STATIC_DIR, html=True),
            name="frontend",
        )

    return app


app = create_app()