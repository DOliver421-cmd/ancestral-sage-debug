"""app/core/supabase.py — lightweight Supabase client integration.

This module provides a safe initialization path for Supabase-backed features and
falls back to an in-memory simulation when the environment is not configured.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any, Optional

logger = logging.getLogger("lcewai")

_SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "").strip()
_SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "").strip()
_SUPABASE_AVAILABLE: bool = bool(_SUPABASE_URL and _SUPABASE_KEY)
_MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024

_memory_store: dict[str, list[dict[str, Any]]] = {
    "ai_persona_profiles": [],
    "ai_memory_ledger": [],
    "uploads": [],
}

_supabase_client: Optional[Any] = None


if not _SUPABASE_AVAILABLE:
    logger.warning(
        "SUPABASE: environment variables not detected; using in-memory simulation mode"
    )


def get_runtime_mode() -> str:
    """Return the current runtime mode: 'supabase' or 'memory'."""
    return "supabase" if _SUPABASE_AVAILABLE else "memory"


def is_supabase_available() -> bool:
    """Return True when both Supabase environment variables are configured."""
    return _SUPABASE_AVAILABLE


def get_supabase_client() -> Optional[Any]:
    """Lazily initialize and return the Supabase client if available."""
    global _supabase_client

    if not _SUPABASE_AVAILABLE:
        return None

    if _supabase_client is not None:
        return _supabase_client

    try:
        from supabase import create_client
    except ImportError:
        logger.warning("SUPABASE: 'supabase' package is not installed.")
        return None

    try:
        _supabase_client = create_client(_SUPABASE_URL, _SUPABASE_KEY)
        logger.info("SUPABASE: client initialized successfully")
        return _supabase_client
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("SUPABASE: client initialization failed: %s", exc)
        return None


async def create_persona_profile(persona_name: str, profile: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Create a persona profile record in Supabase or in-memory storage."""
    payload: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "persona_name": persona_name,
        "profile": profile or {},
        "created_at": int(time.time()),
        "mode": get_runtime_mode(),
    }

    if _SUPABASE_AVAILABLE:
        client = get_supabase_client()
        if client is not None:
            try:
                result = client.table("ai_persona_profiles").insert(payload).execute()
                data = getattr(result, "data", None) or []
                if data:
                    return {"mode": "supabase", "record": data[0]}
            except Exception as exc:
                logger.warning("SUPABASE: persona profile insert failed: %s", exc)

    _memory_store["ai_persona_profiles"].append(payload)
    return {"mode": "memory", "record": payload}


async def append_memory_event(
    persona_name: str,
    event_type: str,
    content: str,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Append a persona interaction event to the persistent memory ledger."""
    payload: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "persona_name": persona_name,
        "event_type": event_type,
        "content": content,
        "metadata": metadata or {},
        "created_at": int(time.time()),
        "mode": get_runtime_mode(),
    }

    if _SUPABASE_AVAILABLE:
        client = get_supabase_client()
        if client is not None:
            try:
                result = client.table("ai_memory_ledger").insert(payload).execute()
                data = getattr(result, "data", None) or []
                if data:
                    return {"mode": "supabase", "record": data[0]}
            except Exception as exc:
                logger.warning("SUPABASE: memory ledger insert failed: %s", exc)

    _memory_store["ai_memory_ledger"].append(payload)
    return {"mode": "memory", "record": payload}


async def resolve_keyword_fallback(keyword: str) -> Optional[dict[str, Any]]:
    """Look up a keyword in Supabase and return a matching record if found."""
    if not keyword:
        return None

    client = get_supabase_client()
    if client is None:
        return None

    normalized = keyword.strip().lower()

    try:
        result = client.table("keywords").select("*").eq("keyword", normalized).execute()
        data = getattr(result, "data", None) or []
        if data:
            return data[0]

        result = client.table("keywords").select("*").ilike("keyword", f"%{normalized}%").execute()
        data = getattr(result, "data", None) or []
        if data:
            return data[0]
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("SUPABASE: keyword lookup failed: %s", exc)

    return None


def store_upload_bytes(
    filename: str,
    content: bytes,
    content_type: str = "application/octet-stream",
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Store uploaded bytes, honoring a 10MB file size limit."""
    if len(content) > _MAX_UPLOAD_SIZE_BYTES:
        raise ValueError("File exceeds the 10MB upload limit")

    storage_key = f"{int(time.time())}/{filename or 'upload.bin'}"
    public_url = f"/simulated/uploads/{storage_key}"
    record: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "filename": filename or "upload.bin",
        "content_type": content_type,
        "size_bytes": len(content),
        "storage_key": storage_key,
        "public_url": public_url,
        "metadata": metadata or {},
        "mode": get_runtime_mode(),
    }

    if _SUPABASE_AVAILABLE:
        client = get_supabase_client()
        if client is not None:
            try:
                storage = getattr(client, "storage", None)
                if storage is not None:
                    bucket = storage.from_("uploads")
                    bucket.upload(storage_key, content, file_options={"content-type": content_type})
                    public_url = bucket.get_public_url(storage_key)
                    record["public_url"] = public_url
                    record["mode"] = "supabase"
                    _memory_store["uploads"].append(record)
                    return record
            except Exception as exc:
                logger.warning("SUPABASE: upload storage failed; using memory fallback: %s", exc)

    _memory_store["uploads"].append(record)
    return record


def get_required_schema_definitions() -> list[dict[str, Any]]:
    """Return the Phase 1 schema definitions that should exist in Supabase."""
    return [
        {
            "table": "ai_persona_profiles",
            "columns": [
                {"name": "id", "type": "uuid", "primary_key": True},
                {"name": "persona_name", "type": "text", "nullable": False},
                {"name": "profile", "type": "jsonb", "nullable": True},
                {"name": "created_at", "type": "bigint", "nullable": False},
            ],
        },
        {
            "table": "ai_memory_ledger",
            "columns": [
                {"name": "id", "type": "uuid", "primary_key": True},
                {"name": "persona_name", "type": "text", "nullable": False},
                {"name": "event_type", "type": "text", "nullable": False},
                {"name": "content", "type": "text", "nullable": False},
                {"name": "metadata", "type": "jsonb", "nullable": True},
                {"name": "created_at", "type": "bigint", "nullable": False},
            ],
        },
    ]
