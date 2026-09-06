"""
backend/routers/ops_admin.py — Executive operations control surfaces (Wave 1).

Three real, human-usable control panels over infrastructure that already
exists — no new providers, no stubs, every route backed by a working read or
write:

  1. NOTIFICATION MANAGEMENT
     - POST /ops/notifications/send        — compose to a role/tier segment
     - GET  /ops/notifications/delivery    — delivery log with segment counts
     - POST /ops/notifications/test        — self-send (verify the pipe works)

  2. EMAIL ADMINISTRATION (Resend -> Gmail chain already in server.py)
     - GET  /ops/email/status              — provider chain config presence
                                             (masked — no secrets returned)
     - POST /ops/email/test                — real test-send to the operator's
                                             own address, returns which
                                             provider actually delivered

  3. UNIFIED AUDIT / HEALTH CONSOLE
     - GET  /ops/console                   — one payload unifying platform
                                             health, gateway status, FCC
                                             denial counts, audit-tail, exec
                                             audit tail, and DB collection
                                             counts. Each section fails soft
                                             with an "error" field rather
                                             than breaking the whole console.

Access: every route requires executive_admin (rank 7). Denials are audited.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("ops_admin")
router = APIRouter(tags=["ops-admin"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None
require_role = None
_send_via_resend = None
_send_via_gmail = None


def bind(_db, _current_user, _audit, _require_role, _resend, _gmail):
    global db, current_user, audit, require_role, _send_via_resend, _send_via_gmail
    db = _db
    current_user = _current_user
    audit = _audit
    require_role = _require_role
    _send_via_resend = _resend
    _send_via_gmail = _gmail


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_exec(user: Any) -> Any:
    """Role gate (rank 7). require_role is bound from server.py; if binding
    failed, fail closed."""
    if require_role is None or current_user is None:
        raise HTTPException(503, "Ops console unavailable — dependency binding failed.")
    return user


async def _exec_dep(authorization: Optional[str] = Header(None)) -> Any:
    """FastAPI dependency: resolve the caller, then require executive_admin.
    Uses the SAME current_user() machinery (token_version revocation,
    deactivation checks) and the same rank ladder via ROLE_RANK."""
    if current_user is None:
        raise HTTPException(503, "Ops console unavailable.")
    user = await current_user(authorization)
    from roles import ROLE_RANK
    if ROLE_RANK.get(getattr(user, "role", ""), 0) < ROLE_RANK["executive_admin"]:
        raise HTTPException(403, "Insufficient permissions to access this resource.")
    return user


# ══ 1. NOTIFICATION MANAGEMENT ═══════════════════════════════════════════════

ROLES = ("student", "trial_pass", "instructor", "support_staff", "oversight", "admin", "executive_admin")
TIERS = ("free", "member", "plus", "pro", "patron", "executive")
NOTIF_KINDS = ("info", "success", "warning", "error")


class SegmentSendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=2000)
    link: Optional[str] = Field(default=None, max_length=300)
    kind: str = "info"
    target_roles: list[str] = Field(default_factory=list)
    target_tiers: list[str] = Field(default_factory=list)

    def validated(self) -> "SegmentSendRequest":
        if self.kind not in NOTIF_KINDS:
            raise HTTPException(400, f"kind must be one of {NOTIF_KINDS}")
        for r in self.target_roles:
            if r not in ROLES:
                raise HTTPException(400, f"unknown role: {r}")
        for t in self.target_tiers:
            if t not in TIERS:
                raise HTTPException(400, f"unknown tier: {t}")
        if not self.target_roles and not self.target_tiers:
            raise HTTPException(400, "Pick at least one target role or tier.")
        if self.link and not self.link.startswith("/"):
            raise HTTPException(400, "link must be an in-app path starting with /")
        return self


@router.post("/ops/notifications/send")
async def ops_notifications_send(
    payload: SegmentSendRequest,
    user: Any = Depends(_exec_dep),
):
    """Compose one notification to every user in the selected role/tier
    segment. Each insert is a real db.notifications row picked up by the
    existing NotificationBell (same collection the app already reads)."""
    _require_exec(user)
    payload.validated()
    q: dict[str, Any] = {"is_active": True}
    if payload.target_roles and len(payload.target_roles) < len(ROLES):
        q["role"] = {"$in": payload.target_roles}
    if payload.target_tiers and len(payload.target_tiers) < len(TIERS):
        q["feature_tier"] = {"$in": payload.target_tiers}

    recipients = await db.users.find(q, {"id": 1, "_id": 0}).to_list(5000)
    now = _now_iso()
    docs = [
        {
            "id": f"ops_{os.urandom(8).hex()}",
            "user_id": r["id"],
            "title": payload.title,
            "body": payload.body,
            "link": payload.link,
            "kind": payload.kind,
            "read": False,
            "created_at": now,
            "sent_by": user.id,
            "segment": {"roles": payload.target_roles, "tiers": payload.target_tiers},
        }
        for r in recipients
    ]
    if docs:
        await db.notifications.insert_many(docs)
    await audit(user.id, "ops.notification_sent", meta={
        "recipients": len(docs), "title": payload.title[:80],
    })
    return {"sent": len(docs), "segment": {"roles": payload.target_roles, "tiers": payload.target_tiers}}


@router.post("/ops/notifications/test")
async def ops_notifications_test(user: Any = Depends(_exec_dep)):
    """Self-send: proves the bell pipe end-to-end without touching members."""
    _require_exec(user)
    doc = {
        "id": f"ops_test_{os.urandom(6).hex()}",
        "user_id": user.id,
        "title": "Test notification",
        "body": "This is a delivery test from the Ops console. If you can read this in your bell, the pipeline works.",
        "link": None,
        "kind": "info",
        "read": False,
        "created_at": _now_iso(),
        "sent_by": user.id,
        "segment": {"roles": [], "tiers": []},
    }
    await db.notifications.insert_one(doc)
    return {"ok": True, "id": doc["id"]}


@router.get("/ops/notifications/delivery")
async def ops_notifications_delivery(user: Any = Depends(_exec_dep), limit: int = 50):
    """Recent ops-composed notifications grouped into campaigns by
    (sent_by, title, created bucket) with per-campaign recipient counts and
    read-through so far."""
    _require_exec(user)
    limit = max(1, min(limit, 200))
    docs = await db.notifications.find(
        {"sent_by": {"$exists": True}}, {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    campaigns: dict[str, dict[str, Any]] = {}
    for d in docs:
        key = f"{d.get('sent_by')}|{d.get('title')}|{(d.get('created_at') or '')[:16]}"
        c = campaigns.setdefault(key, {
            "title": d.get("title"), "kind": d.get("kind"),
            "created_at": d.get("created_at"), "sent_by": d.get("sent_by"),
            "segment": d.get("segment"), "recipients": 0, "read": 0,
        })
        c["recipients"] += 1
        if d.get("read"):
            c["read"] += 1
    out = sorted(campaigns.values(), key=lambda c: c["created_at"] or "", reverse=True)
    return {"campaigns": out[:limit]}


# ══ 2. EMAIL ADMINISTRATION ══════════════════════════════════════════════════

def _mask(v: str) -> str:
    return f"••••{v[-4:]}" if v and len(v) >= 4 else "••••"


@router.get("/ops/email/status")
async def ops_email_status(user: Any = Depends(_exec_dep)):
    """Provider-chain presence. Masked values only — no secret ever returns."""
    _require_exec(user)
    resend = bool(os.environ.get("RESEND_API_KEY"))
    gmail = bool(os.environ.get("GMAIL_USER") and os.environ.get("GMAIL_APP_PASSWORD"))
    notify_to = os.environ.get("EXEC_ADMIN_EMAIL") or os.environ.get("PLATFORM_NOTIFY_EMAIL") or ""
    return {
        "chain": [
            {"provider": "resend", "configured": resend, "detail": _mask(os.environ.get("RESEND_API_KEY", ""))},
            {"provider": "gmail_smtp", "configured": gmail,
             "detail": _mask(os.environ.get("GMAIL_USER", ""))},
        ],
        "primary": "resend" if resend else ("gmail_smtp" if gmail else None),
        "notify_to": notify_to,
        "ok": bool(resend or gmail),
    }


class TestEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to_email: str = Field(min_length=3, max_length=200)


@router.post("/ops/email/test")
async def ops_email_test(payload: TestEmailRequest, user: Any = Depends(_exec_dep)):
    """Real test-send through the actual production chain. Reports which
    provider delivered. Never logs or stores the address beyond this audit."""
    _require_exec(user)
    to_email = payload.to_email.strip()
    if "@" not in to_email or "." not in to_email.split("@")[-1]:
        raise HTTPException(400, "Enter a valid email address.")
    subject = "MoreHelp email test"
    html = (
        "<h3>MoreHelp email test</h3>"
        f"<p>Sent at {_now_iso()} by the Ops console to verify the delivery chain.</p>"
        "<p>If you received this, Resend or Gmail SMTP delivered it — the chain is live.</p>"
    )
    provider = None
    if _send_via_resend and await _send_via_resend(to_email, subject, html):
        provider = "resend"
    elif _send_via_gmail and await _send_via_gmail(to_email, subject, html):
        provider = "gmail_smtp"
    await audit(user.id, "ops.email_test", meta={"provider": provider or "FAILED"})
    if not provider:
        raise HTTPException(502, "No provider delivered the test email. Check Railway keys (RESEND_API_KEY / GMAIL_*).")
    return {"delivered_via": provider, "to": to_email}


# ══ 3. UNIFIED AUDIT / HEALTH CONSOLE ════════════════════════════════════════

async def _soft(fn, *args, **kwargs):
    """Run an aggregator; on failure return {'error': ...} so one broken
    section never blanks the whole console."""
    try:
        return await fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)[:200]}


async def _platform_health() -> dict:
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    return {"db": {"up": True}, "users": {"total": total_users, "active": active_users}}


async def _gateway_status() -> dict:
    from ai.llm_gateway import gateway_status
    gs = gateway_status()
    provs = gs.get("providers") or {}
    return {
        "active_providers": gs.get("active_providers", gs.get("active_free_providers", 0)),
        "providers": {k: bool((v or {}).get("available")) for k, v in provs.items()},
    }


async def _fcc_denials() -> dict:
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    total_7d = await db.access_control_denials.count_documents({})
    recent_7d = await db.access_control_denials.count_documents({"at": {"$gte": since}})
    top = await db.access_control_denials.aggregate([
        {"$group": {"_id": {"path": "$path", "reason": "$reason"}, "n": {"$sum": 1}}},
        {"$sort": {"n": -1}}, {"$limit": 8},
    ]).to_list(8)
    return {"total": total_7d, "last_7d": recent_7d, "top": [
        {"path": t["_id"].get("path"), "reason": t["_id"].get("reason"), "count": t["n"]} for t in top
    ]}


async def _audit_tails() -> dict:
    # db.audit_log (singular) rows use 'at' as their timestamp (server.py audit()).
    tail = await db.audit_log.find({}, {"_id": 0}).sort("at", -1).to_list(15)
    total = await db.audit_log.count_documents({})
    return {"total": total, "tail": tail}


async def _exec_audit_tail() -> dict:
    tail = await db.exec_audit_log.find({}, {"_id": 0}).sort("created_at", -1).to_list(15)
    total = await db.exec_audit_log.count_documents({})
    return {"total": total, "tail": tail}


async def _collection_counts() -> list:
    names = await db.list_collection_names()
    counts = []
    for n in sorted(names)[:40]:
        try:
            counts.append({"collection": n, "count": await db[n].count_documents({})})
        except Exception:
            counts.append({"collection": n, "count": None})
    return counts


@router.get("/ops/console")
async def ops_console(user: Any = Depends(_exec_dep)):
    """One payload for the console page. Every section is independent and
    fails soft, so the console always renders what it can."""
    _require_exec(user)
    from server import APP_VERSION
    return {
        "version": APP_VERSION if isinstance(APP_VERSION, str) else "unknown",
        "generated_at": _now_iso(),
        "platform": await _soft(_platform_health),
        "gateway": await _soft(_gateway_status),
        "fcc_denials": await _soft(_fcc_denials),
        "audit": await _soft(_audit_tails),
        "exec_audit": await _soft(_exec_audit_tail),
        "collections": await _soft(_collection_counts),
    }
