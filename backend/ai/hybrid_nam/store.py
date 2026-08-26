"""
NAM Storage Layer

Transparent storage that uses MongoDB when available, in-memory fallback otherwise.
Every NAM module calls store.create() / store.find() / store.update() instead of
managing its own list/dict.

Collections:
- identity, soul_kernel, memory, knowledge, dreams,
  reflections, ledger, escalations, intentions, events
"""

import logging
from datetime import datetime
from typing import Any, Optional
from . import persistence as p

logger = logging.getLogger("nam.store")

# ── Collection names ─────────────────────────────────────────────────────────
COLLECTIONS = [
    "nam_identity", "nam_soul_kernel", "nam_memory", "nam_knowledge",
    "nam_dreams", "nam_reflections", "nam_ledger", "nam_escalations",
    "nam_intentions", "nam_events",
]


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _is_mongo() -> bool:
    return p._db is not None


async def create(collection: str, doc: dict) -> dict:
    """Insert a document. Returns doc with _id."""
    doc.setdefault("created_at", _now())
    if _is_mongo():
        return await p.insert_one(collection, doc)
    else:
        return await p.fallback_insert(collection, doc)


async def find_one(collection: str, query: dict) -> Optional[dict]:
    if _is_mongo():
        return await p.find_one(collection, query)
    else:
        return await p.fallback_find_one(collection, query)


async def find_many(collection: str, query: Optional[dict] = None, limit: int = 100) -> list[dict]:
    # A database failure must degrade to an empty result, never a 500: NAM's
    # live panels (memory, intentions, dreams, reflections, ledger) would
    # otherwise show hard errors during a Mongo blip or an index rebuild.
    try:
        if _is_mongo():
            return await p.find_many(collection, query, limit=limit)
        return await p.fallback_find_many(collection, query, limit)
    except Exception:
        logger.exception("NAM store.find_many(%s) failed — returning empty", collection)
        return []


async def update_one(collection: str, query: dict, update: dict, upsert: bool = False) -> bool:
    if _is_mongo():
        return await p.update_one(collection, query, update, upsert=upsert)
    else:
        return await p.fallback_update_one(collection, query, update)


async def count(collection: str, query: Optional[dict] = None) -> int:
    try:
        if _is_mongo():
            return await p.count_documents(collection, query)
        return len(await p.fallback_find_many(collection, query, limit=999999))
    except Exception:
        logger.exception("NAM store.count(%s) failed — returning 0", collection)
        return 0


async def delete_one(collection: str, query: dict) -> bool:
    if _is_mongo():
        col = p._col(collection)
        if col:
            result = await col.delete_one(query)
            return result.deleted_count > 0
        return False
    else:
        items = p._FALLBACK.get(collection, [])
        for i, doc in enumerate(items):
            if all(doc.get(k) == v for k, v in query.items()):
                items.pop(i)
                return True
        return False


def clear_all():
    """Clear all in-memory fallback stores (testing only)."""
    p.clear_fallback()
