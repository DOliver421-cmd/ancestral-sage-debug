"""
misc — Misc services — AI cost tracker, cookie consent logging, help guide, bug reports, audit export.

Extracted verbatim from backend/server.py (monolith refactor, slice 13).
Shared state is bound by server.py via bind() at include time — no circular imports.
"""
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File, Form
from pydantic import BaseModel, ConfigDict, Field, EmailStr

logger = logging.getLogger("lcewai")
router = APIRouter(tags=['misc', 'admin'])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
JWT_SECRET = None
JWT_ALGO = "HS256"
_send_via_gmail = None
_send_via_resend = None


def bind(_db, _current_user, _jwt_secret, _jwt_algo, _gmail, _resend):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, JWT_SECRET, JWT_ALGO, _send_via_gmail, _send_via_resend
    
    db = _db
    current_user = _current_user
    JWT_SECRET = _jwt_secret
    JWT_ALGO = _jwt_algo
    _send_via_gmail = _gmail
    _send_via_resend = _resend


# Mirrors server.py's role hierarchy for runtime require_role checks.
ROLE_RANK = {"student": 1, "priority_member": 2, "instructor": 2, "creative_partner": 2, "site_support": 3, "admin": 3, "executive_admin": 4}
Role = Literal["student", "priority_member", "instructor", "creative_partner", "site_support", "admin", "executive_admin"]


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


# ═══════════════════════════════════════════════════════════════════════════════
# THE AMBASSADOR 4.0 — Campaign Coordination endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/admin/ai-costs")
async def get_ai_costs(
    persona: Optional[str] = None,
    days: int = 7,
    user: User = Depends(_require_rank("admin")),
):
    """Per-persona AI cost summary for the last N days. Admin only."""
    from ai_cost_tracker import get_persona_costs, get_total_cost
    costs = await get_persona_costs(db, persona=persona, days=days)
    total = await get_total_cost(db, days=days)
    return {"costs": costs, "total": total, "period_days": days}


# ── Cookie Consent Logging ─────────────────────────────────────────────────────

@router.post("/consent/cookie")
async def log_cookie_consent(body: dict, request: Request):
    """Log cookie consent preference to DB for GDPR compliance.
    Works for both authenticated and anonymous users."""
    choice = body.get("choice", "accepted")
    if choice not in ("accepted", "declined"):
        raise HTTPException(400, "choice must be 'accepted' or 'declined'")
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    user_id = None
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            user_id = payload.get("sub")
        except Exception:
            pass
    await db.cookie_consent_log.insert_one({
        "user_id": user_id,
        "choice": choice,
        "ip": request.client.host if request.client else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True}


# ── Help Guide: context-sensitive help for every route ─────────────────────────

class HelpGuideRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=500)
    query: Optional[str] = Field(default=None, max_length=500)


@router.post("/help/guide")
async def help_guide(body: HelpGuideRequest, user: User = Depends(_dep_current_user)):
    """
    Context-sensitive help for any route in the platform.
    Returns role-aware guidance, tips, related links, and common tasks.
    """
    from help_guide import get_help_for
    return get_help_for(role=user.role, path=body.path, query=body.query)


# ── BUG REPORT ENDPOINT (48-hour testing campaign) ──────────────────────────────
class BugReportRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    venmoOrPaypal: str = Field(..., min_length=1, max_length=200)
    whatYouTried: str = Field(..., min_length=1, max_length=100)
    whatBroke: str = Field(..., min_length=1, max_length=2000)
    screenshot: Optional[str] = None


@router.post("/bug-report")
async def submit_bug_report(body: BugReportRequest):
    """
    Submit a bug report during the 48-hour break-the-site campaign.
    Submissions are stored in 'bug_reports' collection and emailed to admin.
    """
    try:
        report = {
            "id": str(uuid.uuid4()),
            "name": body.name.strip(),
            "email": body.email,
            "venmoOrPaypal": body.venmoOrPaypal.strip(),
            "whatYouTried": body.whatYouTried.strip(),
            "whatBroke": body.whatBroke.strip(),
            "screenshot": body.screenshot,
            "submittedAt": datetime.now(timezone.utc),
            "status": "new",
        }
        result = await db["bug_reports"].insert_one(report)
        report["_id"] = str(result.inserted_id)

        # Log the submission
        logger.info(f"Bug report submitted: {body.email} — {body.whatYouTried}")

        # Notify admin via platform email provider
        try:
            admin_email = os.environ.get("BUG_REPORT_NOTIFY_EMAIL", PLATFORM_NOTIFY_EMAIL)
            subject = f"[Bug Report] {body.email} — {body.whatBroke[:60]}"
            html = f"""<div style="font-family:sans-serif;max-width:600px;padding:24px;">
<h2 style="color:#b45309;">New Bug Report Submitted</h2>
<p><strong>From:</strong> {body.name} ({body.email})</p>
<p><strong>Payment handle:</strong> {body.venmoOrPaypal}</p>
<p><strong>What they tried:</strong><br>{body.whatYouTried}</p>
<p><strong>What broke:</strong><br>{body.whatBroke}</p>
{'<p><strong>Screenshot:</strong> included (base64)</p>' if body.screenshot else ''}
<p style="color:#666;font-size:12px;">Submitted: {report['submittedAt'].isoformat()}</p>
</div>"""
            if RESEND_API_KEY:
                await _send_via_resend(admin_email, subject, html)
            elif GMAIL_USER and GMAIL_APP_PASSWORD:
                await _send_via_gmail(admin_email, subject, html)
        except Exception as _email_err:
            logger.warning("Bug report email notification failed: %s", _email_err)

        return {"status": "submitted", "message": "Thanks for testing! You'll get $1 for trying."}
    except Exception as e:
        logger.error(f"Bug report submission error: {e}")
        raise HTTPException(500, "Could not submit bug report")


# ── Executive Governance Layer ─────────────────────────────────────────────────
# Routes added for full RBAC governance restoration.
# All routes require executive_admin unless noted.


@router.get("/admin/audit/export")
async def export_audit_log(
    format: str = "json",
    limit: int = 1000,
    action: str = None,
    actor_id: str = None,
    user: User = Depends(_require_rank("executive_admin")),
):
    """Export full audit log as JSON or CSV (exec-only)."""
    filt: dict = {}
    if action:
        filt["action"] = {"$regex": re.escape(action), "$options": "i"}
    if actor_id:
        filt["actor_id"] = actor_id
    entries = await db.audit_log.find(filt, {"_id": 0}).sort("at", -1).limit(min(limit, 5000)).to_list(length=5000)
    if format == "csv":
        import io as _io, csv as _csv
        buf = _io.StringIO()
        writer = _csv.DictWriter(buf, fieldnames=["at", "actor_id", "actor_name", "action", "target_id", "meta"])
        writer.writeheader()
        for e in entries:
            writer.writerow({"at": e.get("at",""), "actor_id": e.get("actor_id",""), "actor_name": e.get("actor_name",""),
                             "action": e.get("action",""), "target_id": e.get("target_id",""), "meta": str(e.get("meta",""))})
        from fastapi.responses import Response as _Response
        return _Response(content=buf.getvalue(), media_type="text/csv",
                         headers={"Content-Disposition": "attachment; filename=audit_export.csv"})
    return entries
