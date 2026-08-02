"""Phase 1 storage upload endpoint for Supabase-backed file handling."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.supabase import store_upload_bytes

router = APIRouter()

_MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


@router.post("/storage/upload", tags=["storage"])
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    """Accept an upload and store it safely, enforcing the 10MB limit."""
    if file.filename is None or file.filename.strip() == "":
        raise HTTPException(status_code=400, detail="Filename is required")

    contents = await file.read()
    if len(contents) > _MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10MB upload limit")

    try:
        record: dict[str, Any] = store_upload_bytes(
            filename=file.filename,
            content=contents,
            content_type=file.content_type or "application/octet-stream",
            metadata={"original_name": file.filename},
        )
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    return JSONResponse(status_code=201, content={"ok": True, "upload": record})
