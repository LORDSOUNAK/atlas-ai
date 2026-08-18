from __future__ import annotations

from fastapi import FastAPI

from aetheros.api.routers.agents import router as agents_router
from aetheros.api.routers.health import router as health_router
from aetheros.api.routers.hooks import router as hooks_router
from aetheros.api.routers.memory import router as memory_router
from aetheros.api.routers.tools import router as tools_router
from aetheros.api.routers.workflows import router as workflows_router
from aetheros.config.settings import load_settings
from aetheros.container import Container


def create_app() -> FastAPI:
    """Create the FastAPI application instance."""
    settings = load_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(health_router)
    app.include_router(agents_router, prefix=settings.api_prefix)
    app.include_router(workflows_router, prefix=settings.api_prefix)
    app.include_router(hooks_router, prefix=settings.api_prefix)
    app.include_router(memory_router, prefix=settings.api_prefix)
    app.include_router(tools_router, prefix=settings.api_prefix)
    return app


def create_container() -> Container:
    """Create a configured dependency injection container."""
    return Container()


app = create_app()
