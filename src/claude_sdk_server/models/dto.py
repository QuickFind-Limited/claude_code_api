"""Minimal Data Transfer Objects for Claude SDK Server."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request body for query endpoint."""

    prompt: str = Field(..., description="Prompt to send to Claude")
    session_id: Optional[str] = Field(
        default=None, description="Optional session ID for conversation continuity"
    )
    max_turns: Optional[int] = Field(
        default=None, description="Maximum turns before stopping conversation"
    )
    max_thinking_tokens: Optional[int] = Field(
        default=None,
        description="Maximum thinking tokens Claude can use while reasoning",
    )
    model: Optional[str] = Field(
        default="claude-3.5-sonnet", description="Claude model identifier"
    )


class FileInfo(BaseModel):
    """Information about a file in the attachments directory."""

    path: str = Field(..., description="Relative path from attachments directory")
    absolute_path: str = Field(..., description="Complete absolute path to the file")
    size: int = Field(..., description="File size in bytes")
    modified: datetime = Field(..., description="Last modified timestamp")
    is_new: bool = Field(
        ..., description="Whether this file was created during the request"
    )
    is_updated: bool = Field(
        ..., description="Whether this file was modified during the request"
    )


class QueryResponse(BaseModel):
    """Response body for query endpoint."""

    response: str = Field(..., description="Claude's response")
    session_id: str = Field(..., description="Session ID for future use")
    attachments: List[FileInfo] = Field(
        default_factory=list,
        description="Files created or modified in attachments directory",
    )
    new_files: List[str] = Field(
        default_factory=list, description="List of newly created file paths"
    )
    updated_files: List[str] = Field(
        default_factory=list, description="List of updated file paths"
    )
