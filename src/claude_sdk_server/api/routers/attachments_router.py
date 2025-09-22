"""Attachment download endpoints used by the chatbot frontend."""

import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi import Path as FastAPIPath
from fastapi.responses import FileResponse

from src.claude_sdk_server.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/files", tags=["files"])

# Only serve artifacts produced during conversations.
ALLOWED_BASE_DIR = Path("./tmp")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

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


def _resolve_attachment(conversation_id: str, file_path: str) -> Path:
    if not conversation_id or ".." in conversation_id or "/" in conversation_id:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    candidate = Path(file_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise HTTPException(status_code=400, detail="Invalid file path")

    base = (ALLOWED_BASE_DIR / conversation_id / "attachments").resolve()
    resolved = (base / candidate).resolve()

    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Path traversal detected") from exc

    return resolved


def _content_type(path: Path) -> str:
    content_type, _ = mimetypes.guess_type(str(path))
    if content_type:
        return content_type

    suffix = path.suffix.lower()
    if suffix in {
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
    if suffix == ".json":
        return "application/json"
    if suffix == ".csv":
        return "text/csv"
    if suffix == ".xml":
        return "application/xml"
    if suffix == ".html":
        return "text/html"
    if suffix == ".css":
        return "text/css"
    if suffix in {".yaml", ".yml"}:
        return "application/x-yaml"
    if suffix == ".sql":
        return "application/sql"
    return "application/octet-stream"


def _ensure_servable(path: Path) -> None:
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
    resolved = _resolve_attachment(conversation_id, file_path)
    logger.info(
        "Serving conversation attachment",
        extra={"conversation_id": conversation_id, "path": str(resolved)},
    )

    _ensure_servable(resolved)

    content_type = _content_type(resolved)
    disposition = "attachment" if download else "inline"

    headers = {
        "Content-Disposition": f'{disposition}; filename="{resolved.name}"',
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    return FileResponse(path=str(resolved), media_type=content_type, headers=headers)
