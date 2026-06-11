"""
ai/knowledge_digest.py — Jamil Knowledge Base Digest

Runs every 12 hours. Pulls undigested messages from jamil_history,
summarizes them via the full 9-tier free gateway, stores structured
knowledge entries in jamil_knowledge collection.

Also exposes:
  - run_digest(db)        — single digest pass (called by scheduler + manual trigger)
  - get_knowledge_context(db) — returns last N entries formatted for prompt injection
  - start_digest_scheduler(db) — starts the 12-hour background loop
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("lcewai.knowledge_digest")

DIGEST_INTERVAL_HOURS = 12
KNOWLEDGE_COLLECTION  = "jamil_knowledge"
HISTORY_COLLECTION    = "jamil_history"
CONTEXT_ENTRIES       = 12   # how many knowledge entries to inject into Jamil's prompt
MIN_MESSAGES          = 3    # don't digest unless there are at least this many new messages

_DIGEST_SYSTEM = """You are a knowledge archivist for Jamil, a Director-class AI.

Your job: read a batch of conversation messages and produce a structured knowledge summary.

Output format — respond with ONLY valid JSON, no markdown fences:
{
  "summary": "2-4 sentence summary of what was discussed and decided",
  "decisions": ["list", "of", "explicit", "decisions", "made"],
  "topics": ["topic1", "topic2"],
  "action_items": ["any", "outstanding", "action", "items"],
  "key_facts": ["important", "facts", "or", "context", "established"]
}

Be concise. Focus on decisions, facts, and action items — not conversation style.
Omit empty arrays.
"""


async def run_digest(db) -> dict:
    """
    Pull all undigested jamil_history messages, summarize via gateway,
    store in jamil_knowledge. Returns a status dict.
    """
    if db is None:
        return {"status": "skipped", "reason": "db_unavailable"}

    now = datetime.now(timezone.utc)

    # Find the most recent digest to know where to start
    last = await db[KNOWLEDGE_COLLECTION].find_one(
        {"source": "chat_digest"},
        sort=[("period_end", -1)],
    )
    since = last["period_end"] if last else datetime.min.replace(tzinfo=timezone.utc)

    # Pull undigested messages
    cursor = db[HISTORY_COLLECTION].find(
        {"timestamp": {"$gt": since.isoformat() if isinstance(since, datetime) else since}},
        {"_id": 0, "message": 1, "reply": 1, "timestamp": 1, "user_id": 1},
        sort=[("timestamp", 1)],
    )
    messages = await cursor.to_list(length=500)

    if len(messages) < MIN_MESSAGES:
        logger.info("Knowledge digest: only %d new messages — skipping (min %d)", len(messages), MIN_MESSAGES)
        return {"status": "skipped", "reason": "insufficient_messages", "count": len(messages)}

    # Build conversation text for the LLM
    lines = []
    for m in messages:
        ts = m.get("timestamp", "")[:19]
        lines.append(f"[{ts}] USER: {m.get('message', '').strip()}")
        reply = m.get("reply", "").strip()
        if reply:
            lines.append(f"[{ts}] JAMIL: {reply[:600]}")
    conversation_text = "\n".join(lines)

    period_start = messages[0].get("timestamp", now.isoformat())
    period_end   = messages[-1].get("timestamp", now.isoformat())

    # Call the gateway
    try:
        from ai.llm_gateway import call_llm
        result = await call_llm(
            system=_DIGEST_SYSTEM,
            messages=[{"role": "user", "content": f"Summarize these {len(messages)} conversation exchanges:\n\n{conversation_text[:12000]}"}],
            max_tokens=1024,
            persona_label="knowledge_digest",
        )
        raw_text = result.get("text", "").strip()
        provider = result.get("provider", "unknown")
    except Exception as e:
        logger.error("Knowledge digest LLM call failed: %s", e)
        return {"status": "error", "reason": str(e)}

    # Parse JSON response
    parsed = {}
    try:
        import json as _json
        # Strip any accidental markdown fences
        clean = raw_text.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        parsed = _json.loads(clean.strip())
    except Exception as e:
        logger.warning("Knowledge digest JSON parse failed — storing raw summary: %s", e)
        parsed = {"summary": raw_text[:1000]}

    # Store knowledge entry
    entry = {
        "entry_id":          str(uuid.uuid4()),
        "source":            "chat_digest",
        "created_at":        now.isoformat(),
        "period_start":      period_start,
        "period_end":        period_end,
        "raw_message_count": len(messages),
        "provider":          provider,
        "summary":           parsed.get("summary", ""),
        "decisions":         parsed.get("decisions", []),
        "topics":            parsed.get("topics", []),
        "action_items":      parsed.get("action_items", []),
        "key_facts":         parsed.get("key_facts", []),
        "digest_version":    2,
    }

    await db[KNOWLEDGE_COLLECTION].insert_one(entry)
    entry.pop("_id", None)

    logger.info(
        "Knowledge digest complete: %d messages → entry %s (provider: %s)",
        len(messages), entry["entry_id"], provider,
    )
    return {
        "status":   "ok",
        "entry_id": entry["entry_id"],
        "messages": len(messages),
        "provider": provider,
        "topics":   parsed.get("topics", []),
    }


async def get_knowledge_context(db, limit: int = CONTEXT_ENTRIES) -> str:
    """
    Return the last N knowledge entries formatted as a context block
    for injection into Jamil's system prompt.
    """
    if db is None:
        return ""
    try:
        entries = await db[KNOWLEDGE_COLLECTION].find(
            {"source": "chat_digest", "summary": {"$ne": ""}},
            {"_id": 0, "summary": 1, "decisions": 1, "action_items": 1,
             "key_facts": 1, "topics": 1, "period_start": 1, "period_end": 1},
            sort=[("created_at", -1)],
        ).to_list(length=limit)

        if not entries:
            return ""

        lines = ["\n--- KNOWLEDGE BASE (from past conversations) ---"]
        for e in reversed(entries):  # chronological order
            start = (e.get("period_start") or "")[:10]
            end   = (e.get("period_end")   or "")[:10]
            period = f"{start}" if start == end else f"{start} → {end}"
            lines.append(f"\n[{period}]")
            if e.get("summary"):
                lines.append(f"  Summary: {e['summary']}")
            if e.get("decisions"):
                lines.append(f"  Decisions: {'; '.join(e['decisions'][:5])}")
            if e.get("action_items"):
                lines.append(f"  Action items: {'; '.join(e['action_items'][:5])}")
            if e.get("key_facts"):
                lines.append(f"  Key facts: {'; '.join(e['key_facts'][:5])}")
        lines.append("--- END KNOWLEDGE BASE ---\n")
        return "\n".join(lines)
    except Exception as e:
        logger.warning("get_knowledge_context failed: %s", e)
        return ""


async def _digest_loop(db) -> None:
    """Background loop — runs digest every 12 hours."""
    interval = DIGEST_INTERVAL_HOURS * 3600
    # Initial delay: run first digest 30 seconds after startup
    await asyncio.sleep(30)
    while True:
        try:
            result = await run_digest(db)
            logger.info("Scheduled knowledge digest: %s", result)
        except Exception as e:
            logger.error("Scheduled knowledge digest error: %s", e)
        await asyncio.sleep(interval)


def start_digest_scheduler(db) -> None:
    """Call once at startup to begin the 12-hour digest loop."""
    asyncio.create_task(_digest_loop(db))
    logger.info("Knowledge digest scheduler started — interval: %dh", DIGEST_INTERVAL_HOURS)
