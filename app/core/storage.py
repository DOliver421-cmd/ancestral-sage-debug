"""app/core/storage.py — Phase 1 upload and storage helpers.

This module provides a thin, type-hinted upload abstraction that delegates to
Supabase storage when configured and gracefully falls back to in-memory records
when the environment is not configured.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.core.supabase import store_upload_bytes

logger = logging.getLogger("lcewai")

MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024


def validate_upload_size(size_bytes: int) -> None:
    """Raise an error when the upload exceeds the 10MB guardrail."""
    if size_bytes > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError("File exceeds the 10MB upload limit")


def store_upload_from_bytes(
    filename: str,
    content: bytes,
    content_type: str = "application/octet-stream",
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Store uploaded bytes using the Supabase-backed helper or memory fallback."""
    validate_upload_size(len(content))
    return store_upload_bytes(
        filename=filename,
        content=content,
        content_type=content_type,
        metadata=metadata,
    )
