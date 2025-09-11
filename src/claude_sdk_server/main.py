"""Minimal Claude SDK Server."""

import os

from dotenv import load_dotenv
import atla_insights

# Load environment variables from .env file
load_dotenv()
import logfire
from atla_insights import instrument_claude_code_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.claude_sdk_server.api.routers.claude_router import router as claude_router
from src.claude_sdk_server.api.routers.streaming_router import (
    router as streaming_router,
)
from src.claude_sdk_server.api.routers.file_router import router as file_router
from src.claude_sdk_server.api.routers.files_router import router as files_router
from src.claude_sdk_server.utils.logging_config import get_logger

# Initialize logger with clean loguru configuration
logger = get_logger(__name__)

# Configure third-party integrations
atla_insights.configure(
    token=os.environ["ATLA_INSIGHTS_API_KEY"],
    metadata={"environment": os.environ["ATLA_ENVIRONMENT"]},
)
instrument_claude_code_sdk()

# Create FastAPI application
logger.reasoning("Initializing FastAPI application with clean architecture")
app = FastAPI(
    title="Claude SDK Server",
    version="1.0.0",
    description="Minimal REST API server for Claude Code SDK",
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8081",
        "*",
    ],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

logger.context(
    "FastAPI application created with CORS enabled",
    context_data={
        "title": "Claude SDK Server",
        "version": "1.0.0",
        "environment": os.environ.get("ATLA_ENVIRONMENT", "development"),
        "cors_enabled": True,
    },
)

# Configure logfire monitoring
logger.analysis("Configuring logfire for application monitoring")
logfire.configure()
logfire.instrument_fastapi(app, capture_headers=True)

# Include routers
logger.structured("router_registration", router_name="claude_router")
app.include_router(claude_router)

logger.structured("router_registration", router_name="streaming_router")
app.include_router(streaming_router)

logger.structured("router_registration", router_name="file_router")
app.include_router(file_router)

logger.structured("router_registration", router_name="files_router")
app.include_router(files_router)

logger.info("🚀 Claude SDK Server initialized successfully")

# Export app for uvicorn
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    logger.reasoning("Starting development server with uvicorn")

    server_config = {"host": "0.0.0.0", "port": 8000, "reload": True}

    logger.structured(
        "server_startup", **server_config, app_module="src.claude_sdk_server.main:app"
    )

    logger.info("🌟 Starting Claude SDK Server in development mode")

    uvicorn.run("src.claude_sdk_server.main:app", **server_config)
