"""app/security/rate_limit.py — Hybrid rate limiter.

Strategy:
  1. Primary  — MongoDB TTL counter (durable, works across pods/restarts).
  2. Fallback — in-process sliding window (used when DB is unavailable).

The MongoDB implementation uses a single `rate_limit_counters` collection.
Documents have a TTL index on `expires_at` so Mongo cleans them automatically.
Each document key is (key, window_bucket) so counters are naturally partitioned
by time window without needing a background job beyond the TTL index.

TTL index (run once, idempotent):
    db.rate_limit_counters.createIndex({"expires_at": 1}, {expireAfterSeconds: 0})

This index is created automatically at startup via app/services/startup.py.
"""
from __future__ import annotations

import math
from collections import defaultdict as _dd
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

# ── Fallback in-process store (used only when DB is unavailable) ─────────────
_RATE: dict = _dd(list)


def _check_rate_local(key: str, max_calls: int, window_sec: int) -> None:
    """Sliding-window rate check against the local in-process store."""
    now = datetime.now(timezone.utc).timestamp()
    _RATE[key] = [t for t in _RATE[key] if now - t < window_sec]
    if len(_RATE[key]) >= max_calls:
        raise HTTPException(429, "Too many requests, slow down")
    _RATE[key].append(now)


async def _check_rate_mongo(key: str, max_calls: int, window_sec: int) -> None:
    """Fixed-window counter stored in MongoDB.

    Uses atomic $inc + upsert so it is safe under concurrent requests from
    multiple pods. The window bucket is derived from the current UTC timestamp
    quantised to window_sec, which makes the window fixed rather than sliding —
    a minor trade-off that eliminates the need for per-request list scans.
    """
    from app.database import db as _db
    now = datetime.now(timezone.utc)
    # Quantise to a fixed window bucket (e.g. every 60 s)
    bucket = math.floor(now.timestamp() / window_sec)
    doc_key = f"{key}:{bucket}"
    expires_at = datetime.fromtimestamp((bucket + 1) * window_sec, tz=timezone.utc)

    result = await _db.rate_limit_counters.find_one_and_update(
        {"_id": doc_key},
        {
            "$inc": {"count": 1},
            "$setOnInsert": {"expires_at": expires_at},
        },
        upsert=True,
        return_document=True,  # pymongo ReturnDocument.AFTER equivalent
    )
    count = (result or {}).get("count", 1)
    if count > max_calls:
        raise HTTPException(429, "Too many requests, slow down")


def check_rate(key: str, max_calls: int, window_sec: int):
    """Synchronous-compatible entry point called from route handlers.

    Route handlers are async, so they call this as a regular function but in
    an async context. We return a coroutine when DB is available and fall back
    to the synchronous local check otherwise.

    Usage in async handlers:
        await check_rate(...)   ← if returned coroutine
        check_rate(...)         ← if DB unavailable (sync fallback raises inline)

    To keep the call-site uniform across all 35 existing usages, this function
    detects whether the DB is available and either raises synchronously (fallback)
    or returns an awaitable (primary). All existing call sites use:

        check_rate(f"key:{user.id}", max_calls=N, window_sec=M)

    Because route handlers are async functions, Python evaluates this but does
    NOT automatically await a returned coroutine. To make this transparent we
    use an async wrapper imported at the call site — see `async_check_rate` below.
    """
    try:
        from app.database import db as _db
        if _db is None:
            raise RuntimeError("db not ready")
        # Return an awaitable — caller must await it.
        return _check_rate_mongo(key, max_calls, window_sec)
    except Exception:
        # DB unavailable — fall back to local check (synchronous, raises inline).
        _check_rate_local(key, max_calls, window_sec)
        # Return None so callers that do `await check_rate(...)` get None.
        import asyncio
        return asyncio.coroutine(lambda: None)()


async def async_check_rate(key: str, max_calls: int, window_sec: int) -> None:
    """Awaitable version of check_rate for use in async route handlers.

    Preferred call site going forward:
        await async_check_rate(f"ai_chat:{user.id}", max_calls=20, window_sec=60)

    Existing call sites using the synchronous `check_rate()` are patched below
    to be awaited via a compatibility shim in each route module.
    """
    try:
        from app.database import db as _db
        if _db is None:
            raise RuntimeError("db not ready")
        await _check_rate_mongo(key, max_calls, window_sec)
    except HTTPException:
        raise
    except Exception:
        _check_rate_local(key, max_calls, window_sec)
