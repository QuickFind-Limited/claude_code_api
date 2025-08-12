"""Main entry point for Claude SDK Server."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from loguru import logger

from .api.routers.claude_router import router as claude_router, health_router
from .api.middleware.cors import setup_cors
from .api.middleware.logging import setup_logging_middleware
from .core.config import settings
from .core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API server wrapping Claude Code SDK for easy HTTP access",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Setup middleware
setup_cors(app)
setup_logging_middleware(app)


# Include routers
app.include_router(health_router)
app.include_router(claude_router)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to documentation."""
    return RedirectResponse(url="/docs")


@app.get("/api", include_in_schema=False)
async def api_root():
    """API root information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/health"
    }


# Export app for uvicorn
__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.claude_sdk_server.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1,
        log_level=settings.log_level.lower()
    )