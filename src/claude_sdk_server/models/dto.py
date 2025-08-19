"""Minimal Data Transfer Objects for Claude SDK Server."""

from typing import Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    """Request model for Claude queries."""
    prompt: str = Field(..., min_length=1, description="The prompt to send to Claude")
    session_id: Optional[str] = Field(None, description="Session ID to resume a conversation")
    max_turns: Optional[int] = Field(None, description="Maximum number of turns to allow Claude to use")

class QueryResponse(BaseModel):
    """Response model for Claude queries."""
    response: str = Field(..., description="Claude's response")
    session_id: str = Field(..., description="Session ID for future use")
