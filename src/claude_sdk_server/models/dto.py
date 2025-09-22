"""Minimal Data Transfer Objects for Claude SDK Server."""

import os
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for Claude queries."""

    prompt: str = Field(..., min_length=1, description="The prompt to send to Claude")
    system_prompt: Optional[str] = Field(
        None, description="System prompt to set context for Claude"
    )
    session_id: Optional[str] = Field(
        None, description="Session ID to resume a conversation"
    )
    max_turns: Optional[int] = Field(
        30, description="Maximum number of turns to allow Claude to use"
    )
    model: Optional[str] = Field(
        "claude-sonnet-4-20250514",
        description="The model to use for Claude: claude-opus-4-1-20250805 or claude-sonnet-4-20250514",
    )
    max_thinking_tokens: Optional[int] = Field(
        32000, description="Maximum number of tokens to allow Claude to think"
    )


class FileInfo(BaseModel):
    """Information about a file in the attachments directory."""
    
    path: str = Field(..., description="Relative path from attachments directory")
    absolute_path: str = Field(..., description="Complete absolute path to the file")
    size: int = Field(..., description="File size in bytes")
    modified: datetime = Field(..., description="Last modified timestamp")
    is_new: bool = Field(..., description="Whether this file was created during the request")
    is_updated: bool = Field(..., description="Whether this file was modified during the request")


class QueryResponse(BaseModel):
    """Response model for Claude queries."""

    response: str = Field(..., description="Claude's response")
    session_id: str = Field(..., description="Session ID for future use")
    attachments: List[FileInfo] = Field(default_factory=list, description="Files created or modified in attachments directory")
    new_files: List[str] = Field(default_factory=list, description="List of newly created file paths")
    updated_files: List[str] = Field(default_factory=list, description="List of updated file paths")
