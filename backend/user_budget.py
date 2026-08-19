"""
user_budget.py — Per-user daily token budgets for platform-paid AI calls
=========================================================================
Protects the platform API from any single non-exec account consuming
excessive tokens and breaking AI features for everyone else.

Design (per owner directive):
  - Users are NEVER cut off. When the daily budget is exhausted they are
    routed to the extensive keyword/KB fallback and told their live AI
    answers resume the next day.
  - BYOK users pay with their own keys and never count against the
    platform budget (their usage is not tracked here).
  - Instructor tier and above (instructor, admin, executive_admin,
    creative_partner) are exempt — unlimited daily budget. This matches
    the BYOK-free tier: trusted insiders who run the platform.
  - Anonymous visitors are budgeted by IP (budget_key="ip:...") so no
    single anonymous visitor can drain the platform either.
  - The cap is configurable via USER_DAILY_TOKEN_CAP (default 50,000
    tokens/day — roughly 15–50 free LLM answers per user per day).

Usage from the LLM gateway:
    from user_budget import check_user_budget, record_user_tokens
    info = await check_user_budget(user_id)          # before platform-paid call
    await record_user_tokens(user_id, tokens, role)  # after a platform-paid call
"""

import logging
import os
from datetime import datetime, timezone
from roles import role_rank

logger = logging.getLogger("lcewai.user_budget")

# Roles at or above instructor rank (3) are exempt from the daily budget.
UNLIMITED_ROLE_RANK = 3  # instructor (3) and above

# Daily token cap for budgeted roles (students / members / anonymous IPs).
DEFAULT_DAILY_CAP = int(os.environ.get("USER_DAILY_TOKEN_CAP", "50000"))

_COLLECTION = "user_token_budgets"


def daily_cap_for(role: str):
    """Daily token cap for a role; None means unlimited (trusted/exec tiers)."""
    if not role:
        return DEFAULT_DAILY_CAP
    if role_rank(role) >= UNLIMITED_ROLE_RANK:
        return None
    return DEFAULT_DAILY_CAP


def _day_key(now=None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d")


def budget_notice() -> str:
    """Shared, honest notice shown when a user's daily AI budget is exhausted."""
    return (
        "You've reached today's free AI answer budget for your account. "
        "I'm not cutting you off — I'll still help you right now from my free "
        "knowledge base below. Live AI answers will be available again after "
        "midnight, so please try again then. Your saved notes, courses, and "
        "every other platform feature keep working normally."
    )


async def resolve_role(user_id: str) -> str:
    """Look up a user's role for budget purposes. Empty string on any failure
    (which then falls back to the default capped budget — safe by default)."""
    if not user_id or user_id.startswith("ip:"):
        return ""
    try:
        from deps import get_db

        db = get_db()
        doc = await db.users.find_one({"id": user_id}, {"_id": 0, "role": 1})
        if not doc:
            doc = await db.users.find_one({"_id": user_id}, {"_id": 0, "role": 1})
        return (doc or {}).get("role", "")
    except Exception as e:
        logger.warning("user_budget: role lookup failed for %s — %s", user_id, e)
        return ""


async def check_user_budget(user_id: str, role: str = "") -> dict:
    """Return the user's current daily budget state.

    Called BEFORE a platform-paid LLM call. Returns:
        {"allowed": bool, "exceeded": bool, "used": int, "cap": int|None, "role": str}
    exceeded=True → the caller must serve the free KB fallback + budget_notice()
    and must NOT call the LLM gateway.
    """
    if not user_id:
        return {"allowed": True, "exceeded": False, "used": 0, "cap": None, "role": role}

    if not role:
        role = await resolve_role(user_id)

    cap = daily_cap_for(role)
    if cap is None:
        return {"allowed": True, "exceeded": False, "used": 0, "cap": None, "role": role}

    used = 0
    try:
        from deps import get_db

        db = get_db()
        doc = await db[_COLLECTION].find_one(
            {"user_id": user_id, "date": _day_key()}, {"_id": 0, "tokens": 1}
        )
        used = (doc or {}).get("tokens", 0)
    except Exception as e:
        logger.warning("user_budget: read failed — %s", e)

    return {
        "allowed": used < cap,
        "exceeded": used >= cap,
        "used": used,
        "cap": cap,
        "role": role,
    }


async def record_user_tokens(user_id: str, tokens: int, role: str = "") -> None:
    """Add tokens to a user's daily platform-paid counter.

    Exempt roles and BYOK calls are never recorded (BYOK is handled by the
    gateway, which does not call this for byok: providers). Best-effort —
    recording failures never block a reply.
    """
    if not user_id or tokens <= 0:
        return
    if daily_cap_for(role or await resolve_role(user_id)) is None:
        return  # exempt role — nothing to track
    try:
        from deps import get_db

        db = get_db()
        await db[_COLLECTION].update_one(
            {"user_id": user_id, "date": _day_key()},
            {
                "$inc": {"tokens": tokens},
                "$setOnInsert": {
                    "role": role or "student",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            },
            upsert=True,
        )
    except Exception as e:
        logger.warning("user_budget: record failed — %s", e)
