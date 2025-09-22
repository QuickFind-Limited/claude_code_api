"""API router for serving attachment files created during Claude sessions."""

import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi import Path as FastAPIPath
from fastapi.responses import FileResponse

from src.claude_sdk_server.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/files", tags=["files"])

ALLOWED_BASE_DIR = Path("./tmp")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

ALLOWED_EXTENSIONS = {
    ".txt",
    ".md",
    ".json",
    ".csv",
    ".log",
    ".xml",
    ".html",
    ".css",
    ".js",
    ".py",
    ".ts",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".sh",
    ".sql",
    ".yaml",
    ".yml",
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".svg",
    ".webp",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".parquet",
    ".arrow",
    ".feather",
}


def _resolve_attachment_path(conversation_id: str, file_path: str) -> Path:
    if not conversation_id or ".." in conversation_id or "/" in conversation_id:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    normalized = Path(file_path)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise HTTPException(status_code=400, detail="Invalid file path")

    resolved = (
        ALLOWED_BASE_DIR / conversation_id / "attachments" / normalized
    ).resolve()
    allowed_root = (ALLOWED_BASE_DIR / conversation_id / "attachments").resolve()

    try:
        resolved.relative_to(allowed_root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Path traversal detected") from exc

    return resolved


def _guess_content_type(path: Path) -> str:
    content_type, _ = mimetypes.guess_type(str(path))
    if content_type:
        return content_type
    if path.suffix.lower() in {
        ".py",
        ".js",
        ".ts",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".cs",
        ".go",
        ".rs",
    }:
        return "text/plain"
    if path.suffix.lower() == ".json":
        return "application/json"
    if path.suffix.lower() == ".csv":
        return "text/csv"
    if path.suffix.lower() == ".xml":
        return "application/xml"
    if path.suffix.lower() == ".html":
        return "text/html"
    if path.suffix.lower() == ".css":
        return "text/css"
    if path.suffix.lower() in {".yaml", ".yml"}:
        return "application/x-yaml"
    if path.suffix.lower() == ".sql":
        return "application/sql"
    return "application/octet-stream"


def _validate_file(path: Path) -> None:
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if not path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    try:
        file_size = path.stat().st_size
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not access file") from exc

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=403, detail="File type not allowed")


@router.get("/conversations/{conversation_id}/attachments/{file_path:path}")
async def serve_attachment(
    conversation_id: str = FastAPIPath(..., description="Conversation identifier"),
    file_path: str = FastAPIPath(..., description="Relative path within attachments"),
    download: bool = Query(
        False, description="Force download instead of inline display"
    ),
):
    resolved = _resolve_attachment_path(conversation_id, file_path)

    logger.info(
        "Serving attachment",
        extra={"conversation_id": conversation_id, "path": str(resolved)},
    )

    _validate_file(resolved)

    content_type = _guess_content_type(resolved)
    disposition = "attachment" if download else "inline"

    headers = {
        "Content-Disposition": f'{disposition}; filename="{resolved.name}"',
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    return FileResponse(path=str(resolved), media_type=content_type, headers=headers)
