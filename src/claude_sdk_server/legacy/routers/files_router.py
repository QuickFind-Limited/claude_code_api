"""FastAPI router for secure file serving from attachments directory.

This router provides secure file serving functionality for Claude-generated files
stored in the tmp/{conversationId}/attachments/ directory structure.

Features:
- Secure path validation to prevent directory traversal attacks
- Proper content-type detection and headers
- Session-based access control
- File existence validation
- Performance optimized streaming
- Comprehensive error handling
"""

import os
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Path as PathParam, Query
from fastapi.responses import FileResponse, Response
from fastapi.security.utils import get_authorization_scheme_param

from ...models.dto import FileInfo
from ...utils.logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/files/legacy", tags=["files-legacy"])

# Constants
ATTACHMENTS_BASE_DIR = Path("./tmp")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit
ALLOWED_FILE_EXTENSIONS = {
    # Documents
    '.txt', '.md', '.pdf', '.doc', '.docx', '.rtf',
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.bmp', '.webp',
    # Code
    '.py', '.js', '.ts', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
    # Data
    '.csv', '.xlsx', '.xls',
    # Archives
    '.zip', '.tar', '.gz',
    # Media
    '.mp3', '.mp4', '.avi', '.mov', '.wav'
}


def validate_session_id(session_id: str) -> bool:
    """Validate session ID format to prevent path traversal."""
    if not session_id:
        return False
    
    # Basic alphanumeric + hyphen validation
    if not session_id.replace('-', '').replace('_', '').isalnum():
        return False
    
    # Length check
    if len(session_id) < 8 or len(session_id) > 64:
        return False
    
    return True


def validate_file_path(file_path: str) -> bool:
    """Validate file path to prevent directory traversal attacks."""
    if not file_path:
        return False
    
    # Normalize path and check for traversal attempts
    normalized = Path(file_path).resolve()
    
    # Check for path traversal indicators
    if '..' in file_path or file_path.startswith('/') or '~' in file_path:
        return False
    
    # Check file extension
    file_ext = Path(file_path).suffix.lower()
    if file_ext and file_ext not in ALLOWED_FILE_EXTENSIONS:
        return False
    
    return True


def get_safe_file_path(session_id: str, file_path: str) -> Optional[Path]:
    """Get validated and safe absolute file path."""
    try:
        # Validate inputs
        if not validate_session_id(session_id):
            logger.warning(f"Invalid session ID format: {session_id}")
            return None
        
        if not validate_file_path(file_path):
            logger.warning(f"Invalid file path: {file_path}")
            return None
        
        # Decode URL-encoded path
        decoded_path = unquote(file_path)
        
        # Build safe path
        attachments_dir = ATTACHMENTS_BASE_DIR / session_id / "attachments"
        full_path = (attachments_dir / decoded_path).resolve()
        
        # Ensure the resolved path is within the allowed directory
        if not str(full_path).startswith(str(attachments_dir.resolve())):
            logger.warning(f"Path traversal attempt detected: {file_path}")
            return None
        
        return full_path
    
    except Exception as e:
        logger.error(f"Error validating file path {session_id}/{file_path}: {e}")
        return None


@router.get("/serve/{session_id}/{file_path:path}")
async def serve_file(
    session_id: str = PathParam(..., description="Session ID for the conversation"),
    file_path: str = PathParam(..., description="Relative path to the file within attachments"),
    download: bool = Query(False, description="Force download instead of inline display")
):
    """
    Serve a file from the attachments directory for a specific session.
    
    This endpoint provides secure access to files created during Claude conversations.
    
    Parameters:
    - session_id: The conversation session ID
    - file_path: Relative path to the file within the session's attachments directory
    - download: If true, forces download; if false, attempts inline display
    
    Security Features:
    - Path traversal protection
    - Session-based access control
    - File extension validation
    - File size limits
    
    Example:
        /api/v1/files/serve/abc123/report.pdf
        /api/v1/files/serve/abc123/subfolder/data.csv?download=true
    """
    
    # Get validated file path
    safe_path = get_safe_file_path(session_id, file_path)
    if not safe_path:
        raise HTTPException(
            status_code=400, 
            detail="Invalid session ID or file path"
        )
    
    # Check if file exists
    if not safe_path.exists():
        logger.info(f"File not found: {safe_path}")
        raise HTTPException(
            status_code=404, 
            detail="File not found"
        )
    
    # Check if it's actually a file (not a directory)
    if not safe_path.is_file():
        logger.warning(f"Path is not a file: {safe_path}")
        raise HTTPException(
            status_code=400, 
            detail="Path is not a file"
        )
    
    try:
        # Check file size
        file_size = safe_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large ({file_size} bytes): {safe_path}")
            raise HTTPException(
                status_code=413, 
                detail=f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)"
            )
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(safe_path))
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Log successful file access
        logger.info(f"Serving file: {session_id}/{file_path} ({file_size} bytes, {mime_type})")
        
        # Determine disposition
        disposition_type = "attachment" if download else "inline"
        
        # Return file response
        return FileResponse(
            path=str(safe_path),
            media_type=mime_type,
            filename=safe_path.name,
            headers={
                "Content-Disposition": f'{disposition_type}; filename="{safe_path.name}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    
    except PermissionError:
        logger.error(f"Permission denied accessing file: {safe_path}")
        raise HTTPException(
            status_code=403, 
            detail="Permission denied"
        )
    except Exception as e:
        logger.error(f"Error serving file {safe_path}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@router.get("/info/{session_id}/{file_path:path}")
async def get_file_info(
    session_id: str = PathParam(..., description="Session ID for the conversation"),
    file_path: str = PathParam(..., description="Relative path to the file within attachments")
) -> FileInfo:
    """
    Get metadata information about a file without downloading it.
    
    Returns file size, modification time, and other metadata.
    
    Example:
        /api/v1/files/info/abc123/report.pdf
    """
    
    # Get validated file path
    safe_path = get_safe_file_path(session_id, file_path)
    if not safe_path:
        raise HTTPException(
            status_code=400, 
            detail="Invalid session ID or file path"
        )
    
    # Check if file exists
    if not safe_path.exists():
        raise HTTPException(
            status_code=404, 
            detail="File not found"
        )
    
    if not safe_path.is_file():
        raise HTTPException(
            status_code=400, 
            detail="Path is not a file"
        )
    
    try:
        # Get file stats
        stat = safe_path.stat()
        
        # Calculate relative path from attachments directory
        attachments_dir = ATTACHMENTS_BASE_DIR / session_id / "attachments"
        try:
            relative_path = safe_path.relative_to(attachments_dir.resolve())
        except ValueError:
            # Fallback to just the filename if relative_to fails
            relative_path = safe_path.name
        
        return FileInfo(
            path=str(relative_path),
            absolute_path=str(safe_path),
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime),
            is_new=False,  # Can't determine without comparison
            is_updated=False  # Can't determine without comparison
        )
    
    except Exception as e:
        logger.error(f"Error getting file info for {safe_path}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@router.get("/list/{session_id}")
async def list_session_files(
    session_id: str = PathParam(..., description="Session ID for the conversation"),
    recursive: bool = Query(True, description="Include files in subdirectories")
) -> list[FileInfo]:
    """
    List all files in a session's attachments directory.
    
    Parameters:
    - session_id: The conversation session ID
    - recursive: Whether to include files in subdirectories
    
    Returns a list of FileInfo objects for all accessible files.
    
    Example:
        /api/v1/files/list/abc123
        /api/v1/files/list/abc123?recursive=false
    """
    
    # Validate session ID
    if not validate_session_id(session_id):
        raise HTTPException(
            status_code=400, 
            detail="Invalid session ID format"
        )
    
    attachments_dir = ATTACHMENTS_BASE_DIR / session_id / "attachments"
    
    # Check if directory exists
    if not attachments_dir.exists():
        logger.info(f"Attachments directory not found for session: {session_id}")
        return []
    
    if not attachments_dir.is_dir():
        raise HTTPException(
            status_code=400, 
            detail="Attachments path is not a directory"
        )
    
    try:
        files = []
        
        # Get file pattern
        pattern = "**/*" if recursive else "*"
        
        for file_path in attachments_dir.glob(pattern):
            if file_path.is_file():
                try:
                    # Validate file extension
                    file_ext = file_path.suffix.lower()
                    if file_ext and file_ext not in ALLOWED_FILE_EXTENSIONS:
                        logger.debug(f"Skipping file with disallowed extension: {file_path}")
                        continue
                    
                    # Get file stats
                    stat = file_path.stat()
                    
                    # Skip files that are too large
                    if stat.st_size > MAX_FILE_SIZE:
                        logger.debug(f"Skipping large file: {file_path}")
                        continue
                    
                    # Calculate relative path
                    relative_path = file_path.relative_to(attachments_dir)
                    
                    files.append(FileInfo(
                        path=str(relative_path),
                        absolute_path=str(file_path),
                        size=stat.st_size,
                        modified=datetime.fromtimestamp(stat.st_mtime),
                        is_new=False,
                        is_updated=False
                    ))
                
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
                    continue
        
        logger.info(f"Listed {len(files)} files for session {session_id}")
        return files
    
    except Exception as e:
        logger.error(f"Error listing files for session {session_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@router.delete("/clean/{session_id}")
async def clean_session_files(
    session_id: str = PathParam(..., description="Session ID for the conversation"),
    older_than_hours: int = Query(24, ge=1, le=168, description="Delete files older than X hours")
):
    """
    Clean up old files for a session.
    
    Parameters:
    - session_id: The conversation session ID  
    - older_than_hours: Only delete files older than this many hours (1-168)
    
    This is an administrative endpoint for cleanup.
    
    Example:
        /api/v1/files/clean/abc123?older_than_hours=48
    """
    
    # Validate session ID
    if not validate_session_id(session_id):
        raise HTTPException(
            status_code=400, 
            detail="Invalid session ID format"
        )
    
    attachments_dir = ATTACHMENTS_BASE_DIR / session_id / "attachments"
    
    if not attachments_dir.exists():
        return {"deleted_count": 0, "message": "No files to clean"}
    
    try:
        import time
        cutoff_time = time.time() - (older_than_hours * 3600)
        deleted_count = 0
        
        for file_path in attachments_dir.rglob("*"):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    if stat.st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete file {file_path}: {e}")
        
        # Remove empty directories
        for dir_path in sorted(attachments_dir.rglob("*"), reverse=True):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                    logger.info(f"Removed empty directory: {dir_path}")
                except Exception as e:
                    logger.debug(f"Could not remove directory {dir_path}: {e}")
        
        logger.info(f"Cleaned {deleted_count} files for session {session_id}")
        return {
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} files older than {older_than_hours} hours"
        }
    
    except Exception as e:
        logger.error(f"Error cleaning files for session {session_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )