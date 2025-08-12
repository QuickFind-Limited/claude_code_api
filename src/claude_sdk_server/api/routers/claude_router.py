"""Claude API router."""

from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from loguru import logger

from ...models.dto import (
    QueryRequest,
    QueryResponse,
    SessionRequest,
    SessionResponse,
    HealthResponse
)
from ...models.errors import (
    ClaudeSDKError,
    ErrorResponse
)
from ...services.claude_service import get_claude_service, ClaudeService
from ...core.config import settings


router = APIRouter(
    prefix="/api/v1/claude",
    tags=["claude"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate Limited"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    }
)


@router.post("/query", response_model=QueryResponse)
async def query_claude(
    request: QueryRequest,
    service: ClaudeService = Depends(get_claude_service)
) -> QueryResponse:
    """Send a query to Claude."""
    try:
        logger.info(f"Processing query request: {request.prompt[:50]}...")
        
        # Handle streaming response
        if request.stream:
            return StreamingResponse(
                _stream_response(request, service),
                media_type="text/event-stream"
            )
        
        # Regular response
        response = await service.query(request)
        return response
        
    except ClaudeSDKError as e:
        logger.error(f"Claude SDK error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_response().model_dump()
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"message": str(e), "type": "internal_error", "code": "INTERNAL_ERROR"}}
        )


async def _stream_response(
    request: QueryRequest,
    service: ClaudeService
) -> AsyncGenerator[str, None]:
    """Generate streaming response."""
    try:
        async for chunk in service.stream_query(request):
            yield f"data: {chunk.model_dump_json()}\n\n"
            
            if chunk.finished:
                yield "data: [DONE]\n\n"
                
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_data = {"error": str(e)}
        yield f"data: {error_data}\n\n"


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionRequest = None,
    service: ClaudeService = Depends(get_claude_service)
) -> SessionResponse:
    """Create a new conversation session."""
    try:
        session = await service.create_session(
            conversation_id=request.conversation_id if request else None
        )
        return SessionResponse(
            session_id=session["id"],
            created_at=session["created_at"],
            metadata=session.get("metadata")
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"message": str(e), "type": "session_error", "code": "SESSION_ERROR"}}
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    service: ClaudeService = Depends(get_claude_service)
) -> SessionResponse:
    """Get session information."""
    session = await service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"message": f"Session {session_id} not found", "type": "not_found", "code": "NOT_FOUND"}}
        )
    
    return SessionResponse(
        session_id=session["id"],
        created_at=session["created_at"],
        metadata=session.get("metadata")
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    service: ClaudeService = Depends(get_claude_service)
) -> None:
    """Delete a conversation session."""
    if not await service.is_session_active(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"message": f"Session {session_id} not found", "type": "not_found", "code": "NOT_FOUND"}}
        )
    
    await service.close_session(session_id)


# Health check endpoint
health_router = APIRouter()


@health_router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat()
    )


# Import datetime for health check
from datetime import datetime