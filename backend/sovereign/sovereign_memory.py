"""
sovereign_memory.py — lightweight persistent memory for The Sovereign.

Extended memory is a core point of this persona (Delon: "I want this particular
persona to have extended memory ... that is the point of this feature"), so it is
NOT deferred. It is implemented the CHEAP way: a single MongoDB collection on the
existing Atlas cluster (reuses the app's Motor `db` handle — no new client, no new
infra, no vector RAG). Each session loads the executive's stored memory into the
Sovereign prompt; new facts are appended.

SAFETY (per project rules): every DB call is wrapped in try/except — a memory
outage degrades gracefully (returns "" / False) and NEVER raises into a request
path. No asyncio.wait_for is used around Motor coroutines.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger("sovereign.memory")

COLLECTION = "sovereign_memory"
MAX_CONTEXT_ENTRIES = 40  # cap injected memory to keep the prompt (and credits) bounded

VALID_KINDS = ("fact", "preference", "decision", "pipeline", "note", "summary")


async def save_memory(db, exec_id: str, content: str, kind: str = "note") -> bool:
    """Persist one memory entry for the executive. Returns True on success.
    Never raises — logs and returns False on any failure."""
    if db is None or not exec_id or not content:
        return False
    if kind not in VALID_KINDS:
        kind = "note"
    try:
        await db[COLLECTION].insert_one({
            "exec_id": exec_id,
            "kind": kind,
            "content": content.strip(),
            "ts": datetime.now(timezone.utc),
        })
        return True
    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"sovereign save_memory failed: {e}")
        return False


async def load_memory_block(db, exec_id: str, limit: int = MAX_CONTEXT_ENTRIES) -> str:
    """Return a formatted memory block to inject into the Sovereign prompt.
    Returns '' if there is nothing to load or on any failure (memory must never
    break the persona)."""
    if db is None or not exec_id:
        return ""
    try:
        cursor = db[COLLECTION].find({"exec_id": exec_id}).sort("ts", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"sovereign load_memory_block failed: {e}")
        return ""
    if not docs:
        return ""
    docs.reverse()  # oldest -> newest reads naturally
    lines = []
    for d in docs:
        ts = d.get("ts")
        stamp = ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else ""
        kind = (d.get("kind") or "note").upper()
        content = (d.get("content") or "").strip()
        if content:
            lines.append(f"- [{stamp} {kind}] {content}")
    if not lines:
        return ""
    return "WHAT YOU REMEMBER ABOUT NAM OSHUN (persistent memory):\n" + "\n".join(lines)


async def clear_memory(db, exec_id: str) -> int:
    """Delete all stored memory for an executive. Returns count deleted (0 on failure)."""
    if db is None or not exec_id:
        return 0
    try:
        res = await db[COLLECTION].delete_many({"exec_id": exec_id})
        return int(getattr(res, "deleted_count", 0) or 0)
    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"sovereign clear_memory failed: {e}")
        return 0
