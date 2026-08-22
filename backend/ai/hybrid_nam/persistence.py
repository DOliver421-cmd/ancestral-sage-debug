"""
NAM Persistence Adapter

Provides MongoDB-backed storage for all NAM subsystems when MONGO_URL is set.
Falls back to in-memory stores for local development / testing.

Every NAM collection:
- nam_identity
- nam_memory
- nam_knowledge
- nam_dreams
- nam_reflections
- nam_ledger
- nam_escalations
- nam_intentions
- nam_events
"""

import os
from datetime import datetime
from typing import Any, Optional

# ── Lazy MongoDB connection ──────────────────────────────────────────────────
_db = None  # motor database handle, set via init_db()


def init_db(db_handle):
    """Called once from server.py after MongoDB connects."""
    global _db
    _db = db_handle


def _col(name: str):
    """Return a motor collection, or None if MongoDB is disabled."""
    return _db[name] if _db else None


# ── Generic helpers ──────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def insert_one(collection: str, doc: dict) -> dict:
    """Insert a document. Returns the doc with _id added."""
    col = _col(collection)
    if col:
        doc.setdefault("created_at", _now())
        result = await col.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
    else:
        # In-memory fallback handled by caller
        doc.setdefault("created_at", _now())
    return doc


async def find_one(collection: str, query: dict, projection: Optional[dict] = None) -> Optional[dict]:
    col = _col(collection)
    if col:
        doc = await col.find_one(query, projection or {})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    return None


async def find_many(collection: str, query: Optional[dict] = None, projection: Optional[dict] = None,
                    sort: Optional[tuple] = None, limit: int = 100) -> list[dict]:
    col = _col(collection)
    if col:
        cursor = col.find(query or {}, projection or {})
        if sort:
            cursor = cursor.sort(sort[0], sort[1])
        cursor = cursor.limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    return []


async def update_one(collection: str, query: dict, update: dict, upsert: bool = False) -> bool:
    col = _col(collection)
    if col:
        result = await col.update_one(query, {"$set": update}, upsert=upsert)
        return result.modified_count > 0 or result.upserted_id is not None
    return False


async def count_documents(collection: str, query: Optional[dict] = None) -> int:
    col = _col(collection)
    if col:
        return await col.count_documents(query or {})
    return 0


# ── In-memory fallback stores (used when MongoDB is unavailable) ────────────

_FALLBACK: dict[str, list[dict]] = {
    "nam_identity": [],
    "nam_memory": [],
    "nam_knowledge": [],
    "nam_dreams": [],
    "nam_reflections": [],
    "nam_ledger": [],
    "nam_escalations": [],
    "nam_intentions": [],
    "nam_events": [],
    "nam_soul_kernel": [],
}


async def fallback_insert(collection: str, doc: dict) -> dict:
    """Insert into in-memory store when MongoDB is unavailable."""
    doc.setdefault("created_at", _now())
    doc.setdefault("_id", f"local_{len(_FALLBACK.get(collection, [])) + 1}")
    _FALLBACK.setdefault(collection, []).append(doc)
    return doc


async def fallback_find_one(collection: str, query: dict) -> Optional[dict]:
    for doc in _FALLBACK.get(collection, []):
        if all(doc.get(k) == v for k, v in query.items()):
            return doc
    return None


async def fallback_find_many(collection: str, query: Optional[dict] = None, limit: int = 100) -> list[dict]:
    results = []
    for doc in _FALLBACK.get(collection, []):
        if query and not all(doc.get(k) == v for k, v in query.items()):
            continue
        results.append(doc)
        if len(results) >= limit:
            break
    return results


async def fallback_update_one(collection: str, query: dict, update: dict) -> bool:
    for doc in _FALLBACK.get(collection, []):
        if all(doc.get(k) == v for k, v in query.items()):
            doc.update(update)
            return True
    return False


def clear_fallback():
    """Clear all in-memory fallback stores (for testing)."""
    for key in _FALLBACK:
        _FALLBACK[key].clear()
