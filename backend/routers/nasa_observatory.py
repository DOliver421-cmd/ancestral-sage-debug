"""
nasa_observatory.py — Virtual Observatory (NASA APOD + Image Library proxy)

- /nasa/apod  -> daily Astronomy Picture of the Day (cached 24h in Mongo)
- /nasa/search -> NASA Image Library search (10s cache, no DB write)

Key never leaves the server. Frontend calls /api/nasa/* only.
"""
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Query, HTTPException

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["observatory"])

db = None

def bind(_db, **_kw):
    global db
    db = _db

NASA_API_KEY = os.environ.get("NASA_API_KEY", "").strip()
APOD_URL = "https://api.nasa.gov/planetary/apod"
IMAGES_URL = "https://images-api.nasa.gov/search"

@router.get("/nasa/apod")
async def apod(date: Optional[str] = None):
    """Daily APOD. Cached in Mongo nasa_cache for 24h. Public — no auth needed."""
    key = NASA_API_KEY or "DEMO_KEY"
    cache_key = f"apod:{date or 'today'}"
    # try cache first (if db available)
    try:
        if db is not None:
            cached = await db.nasa_cache.find_one({"key": cache_key}, {"_id": 0})
            if cached and cached.get("expires_at"):
                # ISO string check
                exp = cached["expires_at"]
                try:
                    if datetime.fromisoformat(exp) > datetime.now(timezone.utc):
                        return cached["data"]
                except Exception:
                    pass
    except Exception:
        pass

    params = {"api_key": key}
    if date:
        params["date"] = date
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(APOD_URL, params=params)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"NASA APOD unavailable: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(502, f"NASA APOD fetch failed: {e}")

    payload = {
        "date": data.get("date"),
        "title": data.get("title", ""),
        "explanation": data.get("explanation", ""),
        "url": data.get("url", ""),
        "hdurl": data.get("hdurl") or data.get("url", ""),
        "media_type": data.get("media_type", "image"),
        "copyright": data.get("copyright", ""),
        "service_version": data.get("service_version", "v1"),
    }
    # cache 24h
    try:
        if db is not None:
            exp = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
            await db.nasa_cache.update_one(
                {"key": cache_key},
                {"$set": {"key": cache_key, "data": payload, "expires_at": exp, "cached_at": datetime.now(timezone.utc).isoformat()}},
                upsert=True,
            )
    except Exception:
        pass
    return payload

@router.get("/nasa/search")
async def nasa_search(q: str = Query(..., min_length=1, max_length=120), media_type: str = Query("image", pattern="^(image|video)$"), page: int = Query(1, ge=1, le=100)):
    """Proxy NASA Image Library search — no key required, better with key."""
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(IMAGES_URL, params={"q": q.strip(), "media_type": media_type, "page": str(page)})
            r.raise_for_status()
            j = r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"NASA Images unavailable: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(502, f"NASA Images fetch failed: {e}")
    items = []
    for it in j.get("collection", {}).get("items", [])[:24]:
        data0 = (it.get("data") or [{}])[0]
        link0 = (it.get("links") or [{}])[0].get("href", "")
        items.append({
            "nasa_id": data0.get("nasa_id", ""),
            "title": data0.get("title", ""),
            "description": data0.get("description", "")[:400],
            "date_created": data0.get("date_created", ""),
            "keywords": data0.get("keywords", [])[:8],
            "center": data0.get("center", ""),
            "preview": link0,
        })
    return {"q": q, "media_type": media_type, "count": len(items), "items": items}
