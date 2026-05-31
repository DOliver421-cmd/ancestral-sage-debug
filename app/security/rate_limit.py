"""app/security/rate_limit.py — In-memory rate limiter.

Extracted from backend/server.py lines 314–323.
No logic changed.
"""
from collections import defaultdict as _dd
from datetime import datetime, timezone

from fastapi import HTTPException

_RATE = _dd(list)


def check_rate(key: str, max_calls: int, window_sec: int):
    now = datetime.now(timezone.utc).timestamp()
    _RATE[key] = [t for t in _RATE[key] if now - t < window_sec]
    if len(_RATE[key]) >= max_calls:
        raise HTTPException(429, "Too many requests, slow down")
    _RATE[key].append(now)
