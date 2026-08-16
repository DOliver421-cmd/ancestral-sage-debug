"""
supervisor — Supervisor Control Panel — dashboard, escalations, greeter/visitor flow config, content moderation, backup gateway, sage sessions, continuity checks.

Extracted verbatim from backend/server.py (monolith refactor, slice 12).
Shared state (db, current_user, ...) is bound by server.py via bind()
at include time — no circular imports.
"""
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("lcewai")
router = APIRouter(tags=['supervisor'])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None


def bind(_db, _current_user, _audit):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit
    
    db = _db
    current_user = _current_user
    audit = _audit


# Mirrors server.py's role hierarchy for runtime require_role checks.
ROLE_RANK = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4, "creative_partner": 2}
Role = Literal["student", "instructor", "admin", "executive_admin", "creative_partner"]


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: Role = "student"
    associate: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    avatar_url: Optional[str] = None
    feature_tier: str = "free"


async def _dep_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Resolve the real current_user at REQUEST time (bind() sets it after import)."""
    return await current_user(authorization)


def _require_rank(*roles):
    """Runtime equivalent of server.py's require_role() — used in Depends()
    because require_role is bound after this module loads (no import-time call)."""
    def dep(user: User = Depends(_dep_current_user)) -> User:
        if not user or user.role not in ROLE_RANK or not any(
            ROLE_RANK.get(user.role, 0) >= ROLE_RANK.get(r, 0) for r in roles
        ):
            raise HTTPException(403, "Insufficient permissions")
        return user
    return dep


# ── Supervisor Control Panel Routes ────────────────────────────────────────────
# Distinct from exec routes. Supervisor has independent controls:
# content moderation, escalation management, visitor flow, greeter config,
# backup system health, and system continuity controls.
# All require executive_admin (supervisor rank).

@router.get("/supervisor/dashboard")
async def supervisor_dashboard(user: User = Depends(_require_rank("executive_admin"))):
    """Supervisor overview: moderation queue counts, system health summary, backup status, incident summary."""
    mod_pending  = await db.more_posts.count_documents({"status": "pending_review"})
    need_pending = await db.more_needs.count_documents({"status": "pending_review"})
    flag_pending = await db.more_flags.count_documents({"status": "pending"})
    appeal_pending = await db.more_appeals.count_documents({"status": "pending"})
    open_incidents = await db.incidents.count_documents({"status": "open"})
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": {"$ne": False}})
    return {
        "moderation": {
            "posts_pending": mod_pending,
            "needs_pending": need_pending,
            "flags_pending": flag_pending,
            "appeals_pending": appeal_pending,
        },
        "incidents": {"open": open_incidents},
        "users": {"total": total_users, "active": active_users},
    }

@router.get("/supervisor/escalations")
async def supervisor_escalations(user: User = Depends(_require_rank("executive_admin"))):
    """List open escalation records — supervisor manages these."""
    escalations = await db.escalations.find(
        {"status": {"$in": ["open", "pending_supervisor"]}},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=100)
    return {"escalations": escalations}

@router.post("/supervisor/escalations/{esc_id}/resolve")
async def supervisor_resolve_escalation(esc_id: str, body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Supervisor resolves an escalation with a decision and note."""
    decision = body.get("decision", "resolved")
    note     = body.get("note", "")
    result   = await db.escalations.update_one(
        {"id": esc_id},
        {"$set": {
            "status": decision,
            "resolved_by": user.id,
            "resolution_note": note,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Escalation not found")
    await audit(user.id, "supervisor.escalation.resolved", meta={"esc_id": esc_id, "decision": decision})
    return {"ok": True, "decision": decision}

@router.post("/supervisor/escalations")
async def supervisor_create_escalation(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Supervisor creates a new escalation record (e.g. flagging a pattern for exec review)."""
    import uuid as _uuid
    esc = {
        "id": str(_uuid.uuid4()),
        "title": body.get("title", "Untitled"),
        "description": body.get("description", ""),
        "severity": body.get("severity", "medium"),
        "target_id": body.get("target_id"),
        "target_type": body.get("target_type", "user"),
        "status": "open",
        "created_by": user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.escalations.insert_one(esc)
    await audit(user.id, "supervisor.escalation.created", meta={"id": esc["id"], "title": esc["title"]})
    esc.pop("_id", None)
    return esc

@router.get("/supervisor/greeter/config")
async def supervisor_greeter_config(user: User = Depends(_require_rank("executive_admin"))):
    """Return greeter/Supervisor persona config: welcome message, mode, routing rules."""
    doc = await db.platform_config.find_one({"key": "greeter_config"}, {"_id": 0})
    default = {
        "welcome_message": "Welcome to the WAI Institute. I'm here to guide you.",
        "mode": "greeter",
        "route_unauthenticated_to": "/more-help-center",
        "route_authenticated_to": "/dashboard",
        "show_help_link": True,
        "show_community_link": True,
        "greeter_name": "The Supervisor",
    }
    return {"config": (doc or {}).get("value", default)}

@router.patch("/supervisor/greeter/config")
async def supervisor_update_greeter(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Update greeter persona config — supervisor controls the visitor welcome experience."""
    config = body.get("config")
    if not isinstance(config, dict):
        raise HTTPException(400, "config must be an object")
    await db.platform_config.update_one(
        {"key": "greeter_config"},
        {"$set": {"key": "greeter_config", "value": config,
                  "updated_by": user.id, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await audit(user.id, "supervisor.greeter.config_updated", meta=config)
    return {"ok": True, "config": config}

@router.get("/supervisor/visitor-flow")
async def supervisor_visitor_flow(user: User = Depends(_require_rank("executive_admin"))):
    """Return visitor routing/flow config: where unauthenticated visitors land, fallback paths."""
    doc = await db.platform_config.find_one({"key": "visitor_flow"}, {"_id": 0})
    default = {
        "public_landing": "/more-help-center",
        "auth_landing": "/dashboard",
        "fallback_path": "/help-center",
        "login_optional": True,
        "auto_redirect_to_login": False,
        "show_supervisor_widget": True,
    }
    return {"flow": (doc or {}).get("value", default)}

@router.patch("/supervisor/visitor-flow")
async def supervisor_update_visitor_flow(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Update visitor flow config — supervisor controls public routing."""
    flow = body.get("flow")
    if not isinstance(flow, dict):
        raise HTTPException(400, "flow must be an object")
    # Enforce governance rule: login must never auto-redirect
    if flow.get("auto_redirect_to_login") is True:
        raise HTTPException(400, "auto_redirect_to_login must remain false — governance rule.")
    await db.platform_config.update_one(
        {"key": "visitor_flow"},
        {"$set": {"key": "visitor_flow", "value": flow,
                  "updated_by": user.id, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await audit(user.id, "supervisor.visitor_flow.updated", meta=flow)
    return {"ok": True, "flow": flow}

@router.post("/supervisor/content/{content_type}/{content_id}/approve")
async def supervisor_approve_content(content_type: str, content_id: str, user: User = Depends(_require_rank("executive_admin"))):
    """Supervisor approves content — same as admin queue but with supervisor audit trail."""
    if content_type == "post":
        result = await db.more_posts.update_one(
            {"id": content_id},
            {"$set": {"status": "active", "reviewed_by": user.id,
                      "reviewed_at": datetime.now(timezone.utc).isoformat(), "reviewed_by_role": "supervisor"}},
        )
    elif content_type == "need":
        result = await db.more_needs.update_one(
            {"id": content_id},
            {"$set": {"status": "open", "reviewed_by": user.id,
                      "reviewed_at": datetime.now(timezone.utc).isoformat(), "reviewed_by_role": "supervisor"}},
        )
    elif content_type == "appeal":
        result = await db.more_appeals.update_one(
            {"id": content_id},
            {"$set": {"status": "approved", "reviewed_by": user.id,
                      "reviewed_at": datetime.now(timezone.utc).isoformat()}},
        )
    else:
        raise HTTPException(400, "content_type must be post|need|appeal")
    await audit(user.id, f"supervisor.content.approved.{content_type}", meta={"content_id": content_id})
    return {"ok": True, "content_id": content_id}

@router.post("/supervisor/content/{content_type}/{content_id}/reject")
async def supervisor_reject_content(content_type: str, content_id: str, body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Supervisor rejects/removes content with reason."""
    reason = body.get("reason", "")
    if content_type == "post":
        result = await db.more_posts.delete_one({"id": content_id})
    elif content_type == "need":
        result = await db.more_needs.delete_one({"id": content_id})
    elif content_type == "appeal":
        result = await db.more_appeals.update_one(
            {"id": content_id},
            {"$set": {"status": "rejected", "rejection_reason": reason,
                      "reviewed_by": user.id, "reviewed_at": datetime.now(timezone.utc).isoformat()}},
        )
    elif content_type == "flag":
        result = await db.more_flags.update_one(
            {"id": content_id},
            {"$set": {"status": "dismissed", "dismissed_by": user.id,
                      "dismissed_at": datetime.now(timezone.utc).isoformat()}},
        )
    else:
        raise HTTPException(400, "content_type must be post|need|appeal|flag")
    await audit(user.id, f"supervisor.content.rejected.{content_type}", meta={"content_id": content_id, "reason": reason})
    return {"ok": True}

@router.get("/supervisor/backup/status")
async def supervisor_backup_status(user: User = Depends(_require_rank("executive_admin"))):
    """Comprehensive backup system status: gateway, providers, panel health, DB reachability."""
    status = {"checked_at": datetime.now(timezone.utc).isoformat()}
    # DB ping
    try:
        await db.command("ping")
        status["database"] = "connected"
    except Exception as e:
        status["database"] = f"error: {str(e)[:80]}"

    # Gateway
    try:
        import ai.llm_gateway as _gw
        status["gateway"] = {
            "tokens_used": _gw._hour_tokens_used,
            "cap": _gw.HOURLY_TOKEN_CAP,
            "percent": round(_gw._hour_tokens_used / max(_gw.HOURLY_TOKEN_CAP, 1) * 100, 1),
        }
    except Exception:
        status["gateway"] = "unavailable"
    # Backup panel state
    try:
        from emergency_panel import get_panel
        panel = await get_panel(db)
        status["breaker_panel"] = panel
    except Exception:
        status["breaker_panel"] = "unavailable"
    # Provider ranking
    try:
        doc = await db.platform_config.find_one({"key": "gateway_provider_ranking"}, {"_id": 0})
        status["provider_ranking"] = (doc or {}).get("value", [])
    except Exception:
        status["provider_ranking"] = []
    return status

@router.post("/supervisor/backup/switch-provider")
async def supervisor_switch_provider(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Supervisor manually promotes a provider to top of ranking (backup system override)."""
    provider = body.get("provider", "").strip()
    _DEFAULT = ["groq","cerebras","gemini","xai","cohere","openrouter","huggingface","anthropic"]
    if provider not in _DEFAULT:
        raise HTTPException(400, f"Unknown provider: {provider}. Valid: {_DEFAULT}")
    doc = await db.platform_config.find_one({"key": "gateway_provider_ranking"}, {"_id": 0})
    ranking = list((doc or {}).get("value", _DEFAULT))
    if provider in ranking:
        ranking.remove(provider)
    ranking.insert(0, provider)
    await db.platform_config.update_one(
        {"key": "gateway_provider_ranking"},
        {"$set": {"key": "gateway_provider_ranking", "value": ranking,
                  "updated_by": user.id, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await audit(user.id, "supervisor.backup.provider_switched", meta={"provider": provider, "new_ranking": ranking})
    return {"ok": True, "provider": provider, "ranking": ranking}

@router.post("/supervisor/backup/reset-gateway")
async def supervisor_reset_gateway(user: User = Depends(_require_rank("executive_admin"))):
    """Supervisor resets gateway budget counter (backup system continuity action)."""
    try:
        import ai.llm_gateway as _gw
        prev = _gw._hour_tokens_used
        _gw._hour_tokens_used = 0
        _gw._hour_window_start = 0.0
        await audit(user.id, "supervisor.backup.gateway_reset", meta={"previous_tokens_used": prev})
        return {"ok": True, "previous_tokens_used": prev}
    except Exception as e:
        raise HTTPException(500, f"Gateway reset failed: {e}")

@router.get("/supervisor/backup/free-matrix")
async def supervisor_backup_matrix(user: User = Depends(_require_rank("executive_admin"))):
    """Return the free backup provider matrix with live status for each provider."""
    try:
        from emergency_panel import get_system_health
        health = await get_system_health(db)
        return health
    except Exception as e:
        return {"error": str(e), "note": "emergency_panel module unavailable"}

@router.post("/supervisor/backup/emergency-broadcast")
async def supervisor_emergency_broadcast(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Supervisor sends an emergency broadcast — system continuity announcement."""
    title   = body.get("title", "System Notice").strip()
    message = body.get("message", "").strip()
    target  = body.get("target", "all")
    if not message:
        raise HTTPException(400, "message is required")
    import uuid as _uuid
    broadcast = {
        "id": str(_uuid.uuid4()),
        "title": title,
        "message": message,
        "target": target,
        "sent_by": user.id,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "type": "emergency",
    }
    await db.broadcasts.insert_one(broadcast)
    await audit(user.id, "supervisor.backup.emergency_broadcast", meta={"title": title, "target": target})
    broadcast.pop("_id", None)
    return broadcast

@router.get("/supervisor/sage/sessions")
async def supervisor_sage_sessions(
    limit: int = 50,
    user_id: str = None,
    user: User = Depends(_require_rank("executive_admin")),
):
    """Supervisor reviews Sage session activity — for content safety oversight."""
    filt = {}
    if user_id:
        filt["user_id"] = user_id
    sessions = await db.sage_sessions.find(filt, {"_id": 0}).sort("created_at", -1).limit(min(limit, 200)).to_list(length=200)
    return {"sessions": sessions, "total": len(sessions)}

@router.post("/supervisor/sage/sessions/{session_id}/flag")
async def supervisor_flag_sage_session(session_id: str, body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Supervisor flags a Sage session for exec review."""
    reason = body.get("reason", "")
    await db.sage_sessions.update_one(
        {"id": session_id},
        {"$set": {"flagged": True, "flagged_by": user.id,
                  "flag_reason": reason, "flagged_at": datetime.now(timezone.utc).isoformat()}},
    )
    await audit(user.id, "supervisor.sage.session_flagged", meta={"session_id": session_id, "reason": reason})
    return {"ok": True}

@router.get("/supervisor/system/continuity-check")
async def supervisor_continuity_check(user: User = Depends(_require_rank("executive_admin"))):
    """Run a full system continuity check: DB, gateway, backup panel, key routes."""
    results = {}
    # DB
    try:
        await db.command("ping")
        results["database"] = {"status": "ok"}
    except Exception as e:
        results["database"] = {"status": "error", "detail": str(e)[:120]}
    # Gateway module
    try:
        import ai.llm_gateway as _gw
        results["gateway_module"] = {"status": "ok", "tokens_used": _gw._hour_tokens_used, "cap": _gw.HOURLY_TOKEN_CAP}
    except Exception as e:
        results["gateway_module"] = {"status": "error", "detail": str(e)[:120]}
    # Exec panel module
    try:
        from emergency_panel import get_panel
        await get_panel(db)
        results["exec_panel"] = {"status": "ok"}
    except Exception as e:
        results["exec_panel"] = {"status": "error", "detail": str(e)[:120]}
    # Platform config
    try:
        count = await db.platform_config.count_documents({})
        results["platform_config"] = {"status": "ok", "keys": count}
    except Exception as e:
        results["platform_config"] = {"status": "error", "detail": str(e)[:120]}
    # User count sanity check
    try:
        uc = await db.users.count_documents({})
        results["users_collection"] = {"status": "ok", "count": uc}
    except Exception as e:
        results["users_collection"] = {"status": "error", "detail": str(e)[:120]}
    all_ok = all(v.get("status") == "ok" for v in results.values())
    return {"all_ok": all_ok, "checks": results, "checked_at": datetime.now(timezone.utc).isoformat()}


@router.post("/supervisor-integrity-alert")
async def supervisor_integrity_alert(body: dict):
    """
    Unauthenticated endpoint — called by backup/index.html when the Supervisor
    prompt hash fails at page load. Logs a CRITICAL governance incident and
    emails D. Oliver. No auth required because the Supervisor panel may fire this
    before the user has logged in.
    """
    failed = body.get("failed_personas", [])
    source = body.get("source", "unknown")
    ts     = body.get("ts", datetime.now(timezone.utc).isoformat())

    logger.critical(
        "SUPERVISOR INTEGRITY ALERT from %s: failed personas=%s ts=%s",
        source, failed, ts,
    )

    # Log to audit trail
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "supervisor_integrity_failure",
        "actor": "supervisor_panel",
        "detail": f"Prompt hash mismatch: {failed} | source={source}",
        "at": ts,
        "severity": "CRITICAL",
    })

    # Email D. Oliver via the Director's email tool
    try:
        from ai.email_utils import send_platform_email  # type: ignore
        names = ", ".join(failed)
        send_platform_email(
            to=os.getenv("EXEC_EMAIL", "morehelpcenter@gmail.com"),
            subject=f"[GOVERNANCE INTEGRITY] Supervisor prompt hash failure — {names}",
            body=(
                f"D. Oliver —\n\n"
                f"The Supervisor backup panel detected a prompt integrity failure at {ts}.\n\n"
                f"Failed prompts: {names}\n"
                f"Source: {source}\n\n"
                f"This means the Supervisor system prompt in backup/index.html may have been "
                f"modified without authorization. Review the file immediately.\n\n"
                f"The Director | WAI-Institute | {ts}"
            ),
        )
    except Exception as email_exc:
        logger.error("SUPERVISOR INTEGRITY: email dispatch failed: %s", email_exc)

    return {"received": True, "logged": True}
