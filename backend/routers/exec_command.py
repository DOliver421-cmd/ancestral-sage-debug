"""
exec_command.py — Executive Command Center backend
===================================================
Two endpoints that power the integrated exec surface:

  GET /api/exec/system   — RESTORED aggregate platform overview.
    The exec dashboard (ExecSystem.jsx) and the M.O.R.E. admin surface both
    call this endpoint, but it was lost during the router extraction refactor,
    leaving the exec dashboard showing "System endpoint unavailable". Restored
    here with the exact payload the frontends expect: role_counts, version,
    env key-presence flags, audit_log_total, collections, plus the full LLM
    gateway status (providers + hourly budget) for the Command Center's
    AI & Providers tab.

  GET /api/exec/manuals  — every operations manual & report in one call.
    Serves the repo's docs/*.md and backend/handbooks/*.md so reports and
    manuals are reachable from the exec interface without hunting through
    GitHub or copy/pasting between screens.
"""

import logging
import os
import pathlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")

router = APIRouter(tags=["exec_command"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = current_user = None




def bind(_db, _current_user):
    global db, current_user
    db = _db
    current_user = _current_user


async def _dep_current_user(authorization: Optional[str] = Header(None)):
    return await current_user(authorization)


def _require_rank(*roles):
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: BaseModel = Depends(_dep_current_user)):
        if ROLE_RANK.get(getattr(user, "role", ""), 0) < needed_rank:
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


# ─────────────────────────────────────────────────────────────────────────────
# /exec/system — aggregate platform overview
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/exec/system")
async def exec_system_overview(user: BaseModel = Depends(_require_rank("executive_admin"))):
    role_counts = {}
    try:
        cursor = db.users.aggregate([{"$group": {"_id": "$role", "n": {"$sum": 1}}}])
        async for d in cursor:
            role_counts[d.get("_id") or "unknown"] = d.get("n", 0)
    except Exception as e:
        logger.warning("exec/system: role count failed — %s", e)

    audit_log_total = 0
    try:
        audit_log_total = await db.audit_logs.count_documents({})
    except Exception:
        pass

    collections = []
    try:
        collections = await db.list_collection_names()
    except Exception:
        pass

    try:
        from server import APP_VERSION as _version, _DB_SOURCE as _db_source
    except Exception:
        _version = os.environ.get("APP_VERSION", "4.0.1")
        _db_source = os.environ.get("DB_SOURCE", "unknown")

    gateway = {}
    try:
        from ai.llm_gateway import gateway_status as _gateway_status
        gateway = _gateway_status()
    except Exception as e:
        logger.warning("exec/system: gateway status failed — %s", e)

    _prov = gateway.get("providers") or {}
    ls_ready = bool(os.environ.get("LEMON_SQUEEZY_API_KEY", "") and os.environ.get("LEMON_SQUEEZY_STORE_ID", ""))
    gr_ready = bool(os.environ.get("GUMROAD_API_KEY", ""))

    env_flags = {
        "db_name": os.environ.get("DB_NAME", "ancestral_sage"),
        "db_source": _db_source,
        "jwt_expire_hours": int(os.environ.get("JWT_EXPIRE_HOURS", "168")),
        "version": _version,
        "groq_key": bool(_prov.get("groq", {}).get("available")),
        "cerebras_key": bool(_prov.get("cerebras", {}).get("available")),
        "gemini_key": bool(_prov.get("gemini", {}).get("available")),
        "payments_enabled": bool(ls_ready or gr_ready),
        "lemon_squeezy": ls_ready,
        "gumroad": gr_ready,
        "active_free_providers": gateway.get("active_free_providers", 0),
    }

    return {
        "version": _version,
        "role_counts": role_counts,
        "audit_log_total": audit_log_total,
        "collections": collections,
        "env": env_flags,
        "gateway": gateway,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# /exec/manuals — operations manuals & reports
# ─────────────────────────────────────────────────────────────────────────────
_MANUAL_DIRS = None


def _manual_dirs():
    global _MANUAL_DIRS
    if _MANUAL_DIRS is not None:
        return _MANUAL_DIRS
    here = pathlib.Path(__file__).resolve()
    repo = here.parents[2]  # backend/routers/exec_command.py → repo root
    dirs = {
        "docs": [repo / "docs", repo.parent / "docs"],
        "handbook": [repo / "backend" / "handbooks", here.parents[1] / "handbooks"],
    }
    found = {}
    for group, candidates in dirs.items():
        for c in candidates:
            if c.is_dir():
                found[group] = c
                break
    _MANUAL_DIRS = found
    return found


@router.get("/exec/manuals")
async def exec_manuals(user: BaseModel = Depends(_require_rank("executive_admin"))):
    dirs = _manual_dirs()
    out = []
    for group, d in dirs.items():
        try:
            for f in sorted(d.glob("*.md")):
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                out.append({
                    "slug": f.stem,
                    "title": f.stem.replace("_", " ").title(),
                    "group": group,
                    "content": content[:120000],
                })
        except Exception as e:
            logger.warning("exec/manuals: reading %s failed — %s", group, e)
    out.sort(key=lambda m: (m["group"] != "docs", m["title"]))
    return {"manuals": out}
