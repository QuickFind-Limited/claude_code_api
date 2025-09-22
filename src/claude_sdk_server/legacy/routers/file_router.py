"""FastAPI router for secure file serving endpoints.

This router provides secure file serving functionality for files created during 
Claude Code conversations. It includes:
- File serving from attachment directories
- Security checks and access controls
- Content-type detection and proper HTTP headers
- File listing for conversation directories
- Error handling for edge cases

All endpoints validate file paths to prevent directory traversal attacks
and only serve files from authorized conversation directories.
"""

import mimetypes
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Path as FastAPIPath, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from src.claude_sdk_server.utils.logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/files", tags=["files"])

# Security configuration
ALLOWED_BASE_DIR = Path("./tmp")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit
ALLOWED_EXTENSIONS = {
    # Text files
    '.txt', '.md', '.json', '.csv', '.log', '.xml', '.html', '.css', '.js',
    # Code files
    '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs',
    '.php', '.rb', '.sh', '.sql', '.yaml', '.yml',
    # Documents
    '.pdf', '.docx', '.xlsx', '.pptx',
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp',
    # Archives
    '.zip', '.tar', '.gz', '.bz2',
    # Data
    '.parquet', '.arrow', '.feather'
}


class FileInfo(BaseModel):
    """Information about a file."""
    name: str
    path: str
    size: int
    modified: datetime
    content_type: str
    is_directory: bool = False


class DirectoryListing(BaseModel):
    """Response model for directory listings."""
    conversation_id: str
    directory: str
    files: List[FileInfo]
    total_files: int


def validate_and_resolve_path(conversation_id: str, file_path: str = "", directory: str = "attachments") -> Path:
    """
    Validate and resolve file path to prevent directory traversal attacks.
    
    Args:
        conversation_id: The conversation ID
        file_path: The file path within the directory (optional)
        directory: The directory type ('attachments' or 'utils')
    
    Returns:
        Resolved Path object
        
    Raises:
        HTTPException: If path is invalid or unsafe
    """
    # Validate conversation_id
    if not conversation_id or '..' in conversation_id or '/' in conversation_id:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
    
    # Validate directory type
    if directory not in ['attachments', 'utils']:
        raise HTTPException(status_code=400, detail="Invalid directory type. Must be 'attachments' or 'utils'")
    
    # Build the base path
    base_path = ALLOWED_BASE_DIR / conversation_id / directory
    
    # If no file_path provided, return the directory
    if not file_path:
        return base_path
    
    # Normalize and validate file path
    normalized_path = os.path.normpath(file_path)
    
    # Check for directory traversal attempts
    if normalized_path.startswith('..') or '/../' in normalized_path or normalized_path.startswith('/'):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    # Resolve the full path
    full_path = base_path / normalized_path
    
    # Ensure the resolved path is still within the allowed directory
    try:
        full_path.resolve().relative_to(base_path.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Path traversal detected")
    
    return full_path


def get_content_type(file_path: Path) -> str:
    """
    Determine the content type of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME content type string
    """
    # Use mimetypes to guess the content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    
    if content_type:
        return content_type
    
    # Fallback based on file extension
    suffix = file_path.suffix.lower()
    
    if suffix in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs']:
        return 'text/plain'
    elif suffix in ['.json']:
        return 'application/json'
    elif suffix in ['.csv']:
        return 'text/csv'
    elif suffix in ['.xml']:
        return 'application/xml'
    elif suffix in ['.html']:
        return 'text/html'
    elif suffix in ['.css']:
        return 'text/css'
    elif suffix in ['.yaml', '.yml']:
        return 'application/x-yaml'
    elif suffix in ['.sql']:
        return 'application/sql'
    elif suffix in ['.parquet']:
        return 'application/octet-stream'
    elif suffix in ['.arrow', '.feather']:
        return 'application/octet-stream'
    else:
        return 'application/octet-stream'


def check_file_security(file_path: Path) -> None:
    """
    Check if a file is safe to serve.
    
    Args:
        file_path: Path to the file
        
    Raises:
        HTTPException: If file is unsafe to serve
    """
    # Check if file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if it's a file (not a directory)
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    # Check file size
    try:
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB")
    except OSError:
        raise HTTPException(status_code=500, detail="Could not access file")
    
    # Check file extension
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=403, detail="File type not allowed")


@router.get("/conversations/{conversation_id}/info")
async def get_conversation_info(
    conversation_id: str = FastAPIPath(..., description="The conversation ID")
) -> dict:
    """
    Get information about a conversation's files.
    
    Returns summary information about files in both attachments and utils directories.
    
    Parameters:
    - conversation_id: The unique conversation identifier
    """
    try:
        logger.info(f"Getting conversation info for {conversation_id}")
        
        base_path = ALLOWED_BASE_DIR / conversation_id
        
        if not base_path.exists():
            raise HTTPException(status_code=404, detail=f"Conversation not found: {conversation_id}")
        
        info = {
            "conversation_id": conversation_id,
            "directories": {},
            "total_files": 0,
            "total_size": 0
        }
        
        # Check each directory type
        for dir_type in ['attachments', 'utils']:
            dir_path = base_path / dir_type
            dir_info = {
                "exists": dir_path.exists(),
                "file_count": 0,
                "total_size": 0,
                "files": []
            }
            
            if dir_path.exists() and dir_path.is_dir():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            stat_info = file_path.stat()
                            file_size = stat_info.st_size
                            
                            dir_info["file_count"] += 1
                            dir_info["total_size"] += file_size
                            
                            relative_path = file_path.relative_to(dir_path)
                            dir_info["files"].append({
                                "name": file_path.name,
                                "path": str(relative_path),
                                "size": file_size,
                                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                                "content_type": get_content_type(file_path)
                            })
                        except Exception as e:
                            logger.warning(f"Could not process file {file_path}: {e}")
            
            info["directories"][dir_type] = dir_info
            info["total_files"] += dir_info["file_count"]
            info["total_size"] += dir_info["total_size"]
        
        logger.info(f"Conversation {conversation_id} has {info['total_files']} files totaling {info['total_size']} bytes")
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation info for {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while getting conversation info")


@router.get("/conversations/{conversation_id}/{directory}")
async def list_conversation_files(
    conversation_id: str = FastAPIPath(..., description="The conversation ID"),
    directory: str = FastAPIPath(..., description="Directory to list (attachments or utils)"),
    include_subdirs: bool = Query(False, description="Include files from subdirectories")
) -> DirectoryListing:
    """
    List files in a conversation directory.
    
    Returns a list of all files in the specified conversation directory,
    with metadata including file size, modification time, and content type.
    
    Parameters:
    - conversation_id: The unique conversation identifier
    - directory: The directory to list ('attachments' or 'utils')
    - include_subdirs: Whether to recursively include subdirectory files
    """
    try:
        # Validate and resolve the directory path
        dir_path = validate_and_resolve_path(conversation_id, "", directory)
        
        logger.info(f"Listing files in {dir_path} for conversation {conversation_id}")
        
        # Check if directory exists
        if not dir_path.exists():
            raise HTTPException(status_code=404, detail=f"Conversation directory not found: {conversation_id}/{directory}")
        
        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        files = []
        
        # Collect files
        if include_subdirs:
            file_paths = dir_path.rglob("*")
        else:
            file_paths = dir_path.iterdir()
        
        for file_path in file_paths:
            try:
                if file_path.is_file():
                    # Get file stats
                    stat_info = file_path.stat()
                    relative_path = file_path.relative_to(dir_path)
                    
                    file_info = FileInfo(
                        name=file_path.name,
                        path=str(relative_path),
                        size=stat_info.st_size,
                        modified=datetime.fromtimestamp(stat_info.st_mtime),
                        content_type=get_content_type(file_path),
                        is_directory=False
                    )
                    files.append(file_info)
                elif file_path.is_dir() and not include_subdirs:
                    # Include directory info if not recursing
                    stat_info = file_path.stat()
                    relative_path = file_path.relative_to(dir_path)
                    
                    dir_info = FileInfo(
                        name=file_path.name,
                        path=str(relative_path),
                        size=0,
                        modified=datetime.fromtimestamp(stat_info.st_mtime),
                        content_type="inode/directory",
                        is_directory=True
                    )
                    files.append(dir_info)
            except Exception as e:
                logger.warning(f"Could not process file {file_path}: {e}")
                continue
        
        # Sort files by name
        files.sort(key=lambda x: (x.is_directory, x.name))
        
        logger.info(f"Found {len(files)} files in {conversation_id}/{directory}")
        
        return DirectoryListing(
            conversation_id=conversation_id,
            directory=directory,
            files=files,
            total_files=len([f for f in files if not f.is_directory])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing files in {conversation_id}/{directory}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while listing files")


@router.get("/conversations/{conversation_id}/{directory}/{file_path:path}")
async def serve_conversation_file(
    conversation_id: str = FastAPIPath(..., description="The conversation ID"),
    directory: str = FastAPIPath(..., description="Directory containing the file (attachments or utils)"),
    file_path: str = FastAPIPath(..., description="Path to the file within the directory"),
    download: bool = Query(False, description="Force download instead of inline display")
):
    """
    Serve a file from a conversation directory.
    
    Serves files securely with proper content-type headers and security checks.
    Supports both inline display and forced download.
    
    Parameters:
    - conversation_id: The unique conversation identifier
    - directory: The directory containing the file ('attachments' or 'utils')
    - file_path: The path to the file within the directory
    - download: If true, force download with Content-Disposition header
    """
    try:
        # Validate and resolve the file path
        resolved_path = validate_and_resolve_path(conversation_id, file_path, directory)
        
        logger.info(f"Serving file {resolved_path} for conversation {conversation_id}")
        
        # Security checks
        check_file_security(resolved_path)
        
        # Get content type
        content_type = get_content_type(resolved_path)
        
        # Prepare headers
        headers = {}
        if download:
            headers["Content-Disposition"] = f'attachment; filename="{resolved_path.name}"'
        else:
            # For certain file types, suggest inline display
            if content_type.startswith(('text/', 'image/', 'application/json', 'application/xml')):
                headers["Content-Disposition"] = f'inline; filename="{resolved_path.name}"'
        
        # Log successful file access
        logger.info(f"Successfully serving {resolved_path} as {content_type}")
        
        return FileResponse(
            path=str(resolved_path),
            media_type=content_type,
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file {conversation_id}/{directory}/{file_path}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while serving file")


@router.get("/health")
async def files_health_check():
    """Health check endpoint for file serving functionality."""
    return {
        "status": "healthy",
        "service": "file_router",
        "base_directory": str(ALLOWED_BASE_DIR.resolve()),
        "max_file_size_mb": MAX_FILE_SIZE // 1024 // 1024,
        "allowed_extensions_count": len(ALLOWED_EXTENSIONS)
    }


@router.get("/")
async def list_conversations() -> dict:
    """
    List all available conversations with files.
    
    Returns a list of conversation IDs that have file directories.
    """
    try:
        logger.info("Listing all conversations with files")
        
        conversations = []
        
        if ALLOWED_BASE_DIR.exists():
            for conv_dir in ALLOWED_BASE_DIR.iterdir():
                if conv_dir.is_dir():
                    # Check if conversation has either attachments or utils directories
                    has_attachments = (conv_dir / "attachments").exists()
                    has_utils = (conv_dir / "utils").exists()
                    
                    if has_attachments or has_utils:
                        conversations.append({
                            "conversation_id": conv_dir.name,
                            "has_attachments": has_attachments,
                            "has_utils": has_utils
                        })
        
        conversations.sort(key=lambda x: x["conversation_id"])
        
        logger.info(f"Found {len(conversations)} conversations with files")
        
        return {
            "conversations": conversations,
            "total_count": len(conversations)
        }
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while listing conversations")