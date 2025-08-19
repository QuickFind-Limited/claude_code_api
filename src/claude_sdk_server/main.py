"""Minimal Claude SDK Server."""

# Configure logging
import logging
import os
import sys

import atla_insights
import logfire
from atla_insights import instrument_claude_code_sdk
from fastapi import FastAPI

from src.claude_sdk_server.api.routers.claude_router import router as claude_router

logfire.configure(token=os.environ["LOGFIRE_API_KEY"])

atla_insights.configure(
    token=os.environ["ATLA_INSIGHTS_API_KEY"],
    metadata={"environment": os.environ["ATLA_ENVIRONMENT"]},
)
instrument_claude_code_sdk()

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,  # Ensure logs go to stdout for Docker
)

# Create FastAPI application
app = FastAPI(
    title="Claude SDK Server",
    version="1.0.0",
    description="Minimal REST API server for Claude Code SDK",
)

# Include router
app.include_router(claude_router)

# Export app for uvicorn
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.claude_sdk_server.main:app", host="0.0.0.0", port=8000, reload=True
    )
