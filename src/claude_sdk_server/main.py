"""Minimal Claude SDK Server."""

import logging
import os
from fastapi import FastAPI
from src.claude_sdk_server.api.routers.claude_router import router as claude_router
from atla_insights import configure, instrument_claude_code_sdk

configure(
    token=os.environ["ATLA_INSIGHTS_API_KEY"],
    metadata={"environment": os.environ["ATLA_ENVIRONMENT"]}
)
instrument_claude_code_sdk()

# Configure logging
import sys
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Ensure logs go to stdout for Docker
)

# Create FastAPI application
app = FastAPI(
    title="Claude SDK Server",
    version="1.0.0",
    description="Minimal REST API server for Claude Code SDK"
)

# Include router
app.include_router(claude_router)

# Export app for uvicorn
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.claude_sdk_server.main:app", host="0.0.0.0", port=8000, reload=True)
