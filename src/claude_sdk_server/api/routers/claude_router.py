"""Minimal Claude API router."""

from fastapi import APIRouter, HTTPException, Depends
from src.claude_sdk_server.models.dto import QueryRequest, QueryResponse
from src.claude_sdk_server.services.claude_service import get_claude_service, ClaudeService

router = APIRouter(prefix="/api/v1", tags=["claude"])

@router.post("/query")
async def query_claude(
    request: QueryRequest,
    service: ClaudeService = Depends(get_claude_service)
) -> QueryResponse:
    """Send a query to Claude Code."""
    try:
        response = await service.query(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}