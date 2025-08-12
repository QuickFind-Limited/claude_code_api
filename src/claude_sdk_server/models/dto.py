"""Data Transfer Objects for Claude SDK Server."""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class Attachment(BaseModel):
    """File attachment for Claude queries."""
    
    filename: str = Field(..., description="Name of the file")
    content: str = Field(..., description="Base64 encoded file content")
    mime_type: Optional[str] = Field(None, description="MIME type of the file")


class QueryRequest(BaseModel):
    """Request model for Claude queries."""
    
    prompt: str = Field(..., min_length=1, description="The prompt to send to Claude")
    model: Literal["opus", "sonnet"] = Field(
        default="sonnet",
        description="Claude model to use: 'opus' (claude-opus-4-1-20250805) or 'sonnet' (claude-sonnet-4-20250514)"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=1000,
        ge=1,
        le=4096,
        description="Maximum tokens to generate"
    )
    stream: bool = Field(
        default=False,
        description="Enable streaming response"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Conversation ID for context"
    )
    attachments: Optional[List[Attachment]] = Field(
        None,
        description="File attachments"
    )
    tools: Optional[List[str]] = Field(
        None,
        description="Tools to enable for this query"
    )
    
    @field_validator('max_tokens')
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max_tokens is within acceptable range."""
        if v > 4096:
            raise ValueError("max_tokens cannot exceed 4096")
        return v


class QueryResponse(BaseModel):
    """Response model for Claude queries."""
    
    response: str = Field(..., description="Claude's response")
    conversation_id: str = Field(..., description="Conversation ID")
    model: str = Field(..., description="Model used")
    usage: Optional[Dict[str, int]] = Field(
        None,
        description="Token usage statistics"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata"
    )


class StreamChunk(BaseModel):
    """Stream chunk for SSE responses."""
    
    chunk: str = Field(..., description="Response chunk")
    finished: bool = Field(default=False, description="Whether streaming is complete")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk metadata")


class SessionRequest(BaseModel):
    """Request model for session creation."""
    
    conversation_id: Optional[str] = Field(
        None,
        description="Custom conversation ID"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Session metadata"
    )


class SessionResponse(BaseModel):
    """Response model for session operations."""
    
    session_id: str = Field(..., description="Session ID")
    created_at: str = Field(..., description="Session creation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Session metadata"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service health status")
    version: Optional[str] = Field(None, description="Service version")
    timestamp: Optional[str] = Field(None, description="Current timestamp")