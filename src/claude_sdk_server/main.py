"""Minimal Claude SDK Server."""

from fastapi import FastAPI
from src.claude_sdk_server.api.routers.claude_router import router as claude_router

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