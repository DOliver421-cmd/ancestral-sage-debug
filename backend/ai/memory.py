"""
WAI-Institute Memory System — Phase 1
======================================
Episodic memory and Policy memory for the WAI persona network.

EPISODIC MEMORY: Stores what each persona has said and done per session.
Injected as recent context so personas remember their last conversations.

POLICY MEMORY: Persistent standing orders set by the Executive Director.
Applied globally or per-persona — "always do X", "never discuss Y", etc.
Standing orders persist across all sessions and are injected at runtime.

Both stored in MongoDB. Zero cost. No vector DB required.

Phase 1 scope:
  - Episodic: log + retrieve recent (last 3 episodes, summarized)
  - Policy: standing orders CRUD, per-persona + global

Phase 2 (future):
  - What content has landed (engagement tracking)
  - What each persona has produced (product memory)
  - Semantic search via text index
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("lcewai.memory")

# ── Constants ─────────────────────────────────────────────────────────────────

GLOBAL_POLICY_PERSONA = "__global__"   # Policy orders that apply to all personas
MAX_EPISODE_REPLY_LEN = 300            # Truncate long replies in memory context
MAX_EPISODE_MSG_LEN   = 150            # Truncate long user messages in memory context
DEFAULT_EPISODE_LIMIT = 3             # How many recent episodes to inject


# ── Episodic Memory ───────────────────────────────────────────────────────────

async def log_episode(
    db,
    session_id: str,
    persona: str,
    user_id: str,
    user_message: str,
    ai_reply: str,
    tools_used: list = None,
) -> None:
    """
    Log a completed conversation turn to episodic memory.
    Call this at the end of each persona endpoint, after getting the reply.
    """
    if db is None:
        return
    try:
        await db.persona_episodes.insert_one({
            "session_id":   session_id,
            "persona":      persona,
            "user_id":      user_id,
            "user_message": user_message[:500],   # cap stored length
            "ai_reply":     ai_reply[:1000],
            "tools_used":   tools_used or [],
            "created_at":   datetime.now(timezone.utc).isoformat(),
        })
        logger.debug("memory: logged episode — persona=%s user=%s session=%s", persona, user_id, session_id)
    except Exception as e:
        logger.warning("memory: log_episode failed — %s", e)


async def get_recent_episodes(
    db,
    persona: str,
    user_id: str,
    limit: int = DEFAULT_EPISODE_LIMIT,
) -> list[dict]:
    """
    Retrieve the most recent episodes for a persona + user combination.
    Returns list of {session_id, user_message, ai_reply, tools_used, created_at}.
    """
    if db is None:
        return []
    try:
        cursor = db.persona_episodes.find(
            {"persona": persona, "user_id": user_id},
        ).sort("created_at", -1).limit(limit)
        episodes = []
        async for doc in cursor:
            doc.pop("_id", None)
            episodes.append(doc)
        return list(reversed(episodes))   # chronological order
    except Exception as e:
        logger.warning("memory: get_recent_episodes failed — %s", e)
        return []


# ── Policy Memory ─────────────────────────────────────────────────────────────

async def get_policy_orders(
    db,
    persona: str,
) -> list[dict]:
    """
    Retrieve all standing orders that apply to a given persona:
    - Global orders (apply to every persona)
    - Persona-specific orders
    Returns list of {order_id, content, set_by, created_at}.
    """
    if db is None:
        return []
    try:
        cursor = db.persona_policies.find(
            {"persona": {"$in": [persona, GLOBAL_POLICY_PERSONA]}, "active": True},
            {"_id": 0, "order_id": 1, "content": 1, "set_by": 1, "created_at": 1, "persona": 1},
        ).sort("created_at", 1)
        orders = []
        async for doc in cursor:
            orders.append(doc)
        return orders
    except Exception as e:
        logger.warning("memory: get_policy_orders failed — %s", e)
        return []


async def set_policy_order(
    db,
    persona: str,
    order_id: str,
    content: str,
    set_by: str,
) -> bool:
    """
    Create or update a standing policy order.
    persona = specific persona key or "__global__" for all personas.
    order_id = unique slug (e.g. "always_wai_brand", "no_competitor_mention").
    Returns True on success.
    """
    if db is None:
        return False
    try:
        await db.persona_policies.update_one(
            {"order_id": order_id, "persona": persona},
            {"$set": {
                "order_id":   order_id,
                "persona":    persona,
                "content":    content,
                "set_by":     set_by,
                "active":     True,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }, "$setOnInsert": {
                "created_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )
        logger.info("memory: policy order set — %s / %s by %s", persona, order_id, set_by)
        return True
    except Exception as e:
        logger.warning("memory: set_policy_order failed — %s", e)
        return False


async def remove_policy_order(
    db,
    persona: str,
    order_id: str,
    removed_by: str,
) -> bool:
    """
    Deactivate a standing policy order (soft delete — preserves audit trail).
    Returns True if found and deactivated.
    """
    if db is None:
        return False
    try:
        result = await db.persona_policies.update_one(
            {"order_id": order_id, "persona": persona},
            {"$set": {
                "active":       False,
                "removed_by":   removed_by,
                "removed_at":   datetime.now(timezone.utc).isoformat(),
            }},
        )
        if result.modified_count > 0:
            logger.info("memory: policy order removed — %s / %s by %s", persona, order_id, removed_by)
            return True
        return False
    except Exception as e:
        logger.warning("memory: remove_policy_order failed — %s", e)
        return False


async def list_all_policy_orders(db) -> list[dict]:
    """Return all active policy orders across all personas."""
    if db is None:
        return []
    try:
        cursor = db.persona_policies.find(
            {"active": True},
            {"_id": 0},
        ).sort([("persona", 1), ("created_at", 1)])
        orders = []
        async for doc in cursor:
            orders.append(doc)
        return orders
    except Exception as e:
        logger.warning("memory: list_all_policy_orders failed — %s", e)
        return []


# ── Context Formatter ─────────────────────────────────────────────────────────

def format_memory_context(
    episodes: list[dict],
    policy_orders: list[dict],
    persona: str,
) -> str:
    """
    Format episodes and policy orders as a system prompt injection block.
    Returns empty string if nothing to inject (no extra tokens burned).
    """
    parts = []

    # Policy orders — injected first (highest priority)
    if policy_orders:
        parts.append("STANDING ORDERS (set by Executive Director — follow always):")
        for o in policy_orders:
            scope = "all personas" if o.get("persona") == GLOBAL_POLICY_PERSONA else persona
            parts.append(f"  [{o['order_id']}] {o['content']}")
        parts.append("")

    # Recent episodes — injected as lightweight memory
    if episodes:
        parts.append(f"RECENT MEMORY (last {len(episodes)} conversation{'s' if len(episodes) != 1 else ''} with {persona}):")
        for ep in episodes:
            ts = ep.get("created_at", "")[:10]   # date only
            msg_preview = ep.get("user_message", "")[:MAX_EPISODE_MSG_LEN]
            reply_preview = ep.get("ai_reply", "")[:MAX_EPISODE_REPLY_LEN]
            tools = ep.get("tools_used", [])
            tool_note = f" | Tools: {', '.join(tools)}" if tools else ""
            parts.append(f"  [{ts}{tool_note}]")
            parts.append(f"  User: {msg_preview}{'...' if len(ep.get('user_message','')) > MAX_EPISODE_MSG_LEN else ''}")
            parts.append(f"  Reply: {reply_preview}{'...' if len(ep.get('ai_reply','')) > MAX_EPISODE_REPLY_LEN else ''}")
        parts.append("")
        parts.append("Use this memory for continuity — reference past work when relevant, do not repeat unnecessarily.")

    if not parts:
        return ""

    return "\n\nMEMORY CONTEXT:\n" + "\n".join(parts)


# ── Convenience: load and format memory for a persona endpoint ────────────────

async def get_memory_context(
    db,
    persona: str,
    user_id: str,
    episode_limit: int = DEFAULT_EPISODE_LIMIT,
) -> str:
    """
    Load recent episodes + policy orders and return the formatted context string.
    Safe to call in every persona endpoint — returns "" if DB unavailable.
    Call get_memory_context() and append to system prompt before AI call.
    """
    try:
        episodes, policy_orders = await __import__("asyncio").gather(
            get_recent_episodes(db, persona, user_id, episode_limit),
            get_policy_orders(db, persona),
        )
        return format_memory_context(episodes, policy_orders, persona)
    except Exception as e:
        logger.warning("memory: get_memory_context failed — %s", e)
        return ""
