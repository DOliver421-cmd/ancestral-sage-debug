"""gateway_admin.py — LLM gateway runtime controls for the MoreHelp console.

Implements the /admin/gateway/* surface the exec console has called since the
WAI era but that never had a backend: live provider availability, the running
hourly-token budget, provider priority order, and the rolling-hour counter.

Every handler reads or mutates the SAME runtime state the gateway actually
enforces — ai/llm_gateway module globals (HOURLY_TOKEN_CAP, _hour_tokens_used,
per-provider key globals) and db.provider_rankings / db.platform_budgets — so
the console reflects reality and its controls take effect on the next request.

Bound by server.py's _bind_router_dependencies (db, current_user, audit).
Auth mirrors routers/users.py: request-time resolution through the bound
current_user dependency, then a rank check.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from roles import ROLE_RANK

logger = logging.getLogger("lcewai.gateway_admin")

router = APIRouter(tags=["gateway_admin"])

# ── Shared state, bound by server.py via bind() ─────────────────────────────
db = None
current_user = None
audit = None


def bind(_db, _current_user, _audit):
    global db, current_user, audit
    db, current_user, audit = _db, _current_user, _audit


# ── Auth (same lazy pattern as routers/users.py) ────────────────────────────
import uuid as _uuid  # noqa: E402
from pydantic import EmailStr  # noqa: E402


class User(BaseModel):
    """Minimal annotation model — resolution happens in the bound dependency."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(_uuid.uuid4()))
    email: EmailStr = "u@example.com"
    full_name: str = ""
    role: str = "student"


async def _dep_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Resolve the real current_user at REQUEST time (bind() sets it after import)."""
    return await current_user(authorization)


def _require_rank(*roles):
    needed = min(ROLE_RANK[r] for r in roles)

    def dep(user: User = Depends(_dep_current_user)) -> User:
        if (ROLE_RANK.get(user.role, 0) or 0) < needed:
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Provider env-globals the gateway loads at import (see ai/llm_gateway.py).
PROVIDER_GLOBALS = [
    ("groq", "GROQ_API_KEY", "free", "fastest, tool-capable"),
    ("cerebras", "CEREBRAS_API_KEY", "free", "fast, tool-capable"),
    ("sambanova", "SAMBANOVA_API_KEY", "free", "tool-capable"),
    ("gemini", "GEMINI_API_KEY", "free", "15 RPM, 1M ctx"),
    ("xai", "XAI_API_KEY", "free", "credits"),
    ("cohere", "COHERE_API_KEY", "free", "tier"),
    ("mistral", "MISTRAL_API_KEY", "free", "1M tokens/mo"),
    ("together", "TOGETHER_API_KEY", "free", "$25 credit"),
    ("openrouter", "OPENROUTER_API_KEY", "free", "models"),
    ("huggingface", "HUGGINGFACE_API_KEY", "free", "slow"),
    ("openai", "OPENAI_API_KEY", "owner", "text tier"),
    ("deepseek", "DEEPSEEK_API_KEY", "owner", "text tier"),
]


def _gateway():
    try:
        import ai.llm_gateway as g
        return g
    except Exception as exc:  # noqa: BLE001
        logger.exception("llm_gateway import failed")
        raise HTTPException(500, f"gateway module unavailable: {exc}")


# ── GET /admin/gateway/status ───────────────────────────────────────────────
@router.get("/admin/gateway/status")
async def gateway_status(user: User = Depends(_require_rank("admin", "executive_admin"))):
    g = _gateway()
    providers = {}
    for name, gvar, tier, cost in PROVIDER_GLOBALS:
        providers[name] = {"available": bool(getattr(g, gvar, "")), "tier": tier, "cost": cost}
    cap = int(getattr(g, "HOURLY_TOKEN_CAP", 200000) or 200000)
    used = int(getattr(g, "_hour_tokens_used", 0) or 0)
    pct = round(used * 100.0 / cap, 1) if cap else 0
    return {
        "providers": providers,
        "budget": {
            "tokens_used": used,
            "hourly_cap": cap,
            "budget_pct": pct,
            "over_budget": used >= cap,
            "window": "rolling-hour",
        },
    }


# ── GET /admin/gateway/ranking ──────────────────────────────────────────────
@router.get("/admin/gateway/ranking")
async def gateway_ranking(user: User = Depends(_require_rank("admin", "executive_admin"))):
    doc = await db.provider_rankings.find_one({"service": "ai"}, {"_id": 0})
    if doc and doc.get("ranking"):
        return {"ranking": doc["ranking"], "source": "db", "updated_at": doc.get("updated_at")}
    return {"ranking": [name for name, _, _, _ in PROVIDER_GLOBALS], "source": "default"}


# ── PATCH /admin/gateway/ranking — persist the free-first priority order ────
class RankingReq(BaseModel):
    ranking: list[str]


@router.patch("/admin/gateway/ranking")
async def gateway_set_ranking(body: RankingReq, user: User = Depends(_require_rank("executive_admin"))):
    valid = {name for name, _, _, _ in PROVIDER_GLOBALS}
    unknown = [p for p in body.ranking if p not in valid]
    if unknown:
        raise HTTPException(400, f"Unknown provider(s): {sorted(unknown)}")
    if len(body.ranking) != len(set(body.ranking)):
        raise HTTPException(400, "ranking must not contain duplicates")
    now = _now()
    old = await db.provider_rankings.find_one({"service": "ai"}, {"_id": 0, "ranking": 1})
    await db.provider_rankings.update_one(
        {"service": "ai"},
        {"$set": {"ranking": body.ranking, "updated_by": user.id, "updated_at": now}},
        upsert=True,
    )
    try:
        await audit(user.id, "gateway.ranking.updated",
                    before={"ranking": (old or {}).get("ranking")}, after={"ranking": body.ranking})
    except Exception as _ae:  # noqa: BLE001
        logger.exception("audit write failed: %s", _ae)
    return {"ok": True, "ranking": body.ranking, "updated_at": now}


# ── PATCH /admin/gateway/budget — runtime hourly-token cap ──────────────────
class BudgetReq(BaseModel):
    hourly_cap: int = Field(..., ge=1000)


@router.patch("/admin/gateway/budget")
async def gateway_set_budget(body: BudgetReq, user: User = Depends(_require_rank("executive_admin"))):
    g = _gateway()
    old_cap = int(getattr(g, "HOURLY_TOKEN_CAP", 200000) or 200000)
    # Applied to the running process now — call_llm reads the module global on
    # every request. Persisted for audit + restart visibility; the HOURLY_TOKEN_CAP
    # env var remains the boot-time default on the next deploy.
    g.HOURLY_TOKEN_CAP = body.hourly_cap
    now = _now()
    await db.platform_budgets.update_one(
        {"key": "hourly_token_cap"},
        {"$set": {"limit": body.hourly_cap, "updated_by": user.id, "updated_at": now}},
        upsert=True,
    )
    try:
        await audit(user.id, "gateway.budget.updated",
                    before={"limit": old_cap}, after={"limit": body.hourly_cap})
    except Exception as _ae:  # noqa: BLE001
        logger.exception("audit write failed: %s", _ae)
    return {"ok": True, "hourly_cap": body.hourly_cap, "applied": "runtime", "persisted": True}


# ── POST /admin/gateway/reset-budget — zero the rolling-hour counter ────────
@router.post("/admin/gateway/reset-budget")
async def gateway_reset_budget(user: User = Depends(_require_rank("executive_admin"))):
    g = _gateway()
    before = int(getattr(g, "_hour_tokens_used", 0) or 0)
    g._hour_tokens_used = 0
    g._hour_window_start = time.time()
    try:
        await audit(user.id, "gateway.budget.reset", before={"tokens_used": before}, after={"tokens_used": 0})
    except Exception as _ae:  # noqa: BLE001
        logger.exception("audit write failed: %s", _ae)
    return {"ok": True, "reset_from": before}
