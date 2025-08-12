"""CORS middleware configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ...core.config import settings
from ...core.logging import logger


def setup_cors(app: FastAPI) -> None:
    """Configure CORS middleware."""
    logger.info("Setting up CORS middleware")
    logger.info(f"CORS origins: {settings.cors_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    logger.info("CORS middleware configured successfully")