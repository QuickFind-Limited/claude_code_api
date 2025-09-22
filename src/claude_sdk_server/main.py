"""Minimal Claude SDK Server."""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import atla_insights
from atla_insights import instrument_claude_code_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from src.claude_sdk_server.api.routers.attachments_router import (
    router as attachments_router,
)
from src.claude_sdk_server.api.routers.claude_router import router as claude_router
from src.claude_sdk_server.utils.logging_config import get_logger

# Initialize logger with clean loguru configuration
logger = get_logger(__name__)

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

# Configure observability exporters
logger.analysis("Configuring logfire exporter for application monitoring")
logfire_exporter = OTLPSpanExporter(
    endpoint="https://logfire-eu.pydantic.dev/v1/traces",
    headers={"Authorization": f"Bearer {os.environ['LOGFIRE_TOKEN']}"},
)
logfire_span_processor = BatchSpanProcessor(logfire_exporter)
FastAPIInstrumentor.instrument_app(app)

# Configure third-party integrations
atla_insights.configure(
    token=os.environ["ATLA_INSIGHTS_API_KEY"],
    metadata={"environment": os.environ["ATLA_ENVIRONMENT"]},
    additional_span_processors=[logfire_span_processor],
)
instrument_claude_code_sdk()

# Include routers
logger.structured("router_registration", router_name="claude_router")
app.include_router(claude_router)

logger.structured("router_registration", router_name="attachments_router")
app.include_router(attachments_router)

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
