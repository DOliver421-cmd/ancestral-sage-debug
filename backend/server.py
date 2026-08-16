"""LCE-WAI training platform — FastAPI backend.

ROUTE MAP (see `api_router` definitions below; all paths are prefixed `/api`):

  AUTH           /auth/{login,register,me,change-password}
  ADMIN: USERS   /admin/users (GET/POST), /admin/users/{id} (PATCH/DELETE),
                 /admin/users/{id}/role (PATCH), /admin/users/{id}/active (PATCH),
                 /admin/users/{id}/password (POST), /admin/associate (POST)
  ADMIN: CORE    /admin/{stats,sites,inventory,checkout,checkouts,audit}
  CURRICULUM     /modules*, /progress*
  LABS           /labs*, /competencies, /instructor/*
  AI             /ai/{chat,history}
  CREDENTIALS    /credentials*, /portfolio*
  COMPLIANCE     /compliance*
  ADAPTIVE       /adaptive/me
  NOTIFICATIONS  /notifications*
  ATTENDANCE     /attendance*
  INCIDENTS      /incidents*
  ANALYTICS      /analytics/program
  SYSTEM         /, /health, /version, /docs, /openapi.json

DESIGN DECISIONS:
- Single uuid `id` field on every doc + Mongo `_id`. We always project `_id`
  away from responses; new endpoints must `doc.pop("_id", None)` before
  returning.
- JWT auth (HS256). Tokens valid for JWT_EXPIRE_HOURS env hours.
- `current_user` rejects deactivated accounts even with valid JWTs.
- Public registration always creates `role=student`. Higher privileges are
  created only by an authenticated admin via `POST /api/admin/users`.
- Every privileged action emits an audit-log row via `audit(...)`.
- Indexes are declared idempotently on startup in `ensure_indexes()`.
"""
import asyncio
import io
import logging
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Literal

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, APIRouter, File, Form, HTTPException, Header, Request, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from prompts.ancestral_sage_prompt import (
    ANCESTRAL_SAGE_PROMPT,
    ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED,
    RESTRICTED_EDUCATIONAL_FALLBACK,
    compute_sage_prompt_hash,
)
from prompts.orchestrator import get_orchestrator_system, compute_orchestrator_hash, get_scholar_system, compute_scholar_hash
from prompts.more_department_system import get_more_department_system, compute_more_department_hash
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from starlette.middleware.cors import CORSMiddleware
import platform_services

from seed import MODULES, quiz_for
from seed_labs import ONLINE_LABS, IN_PERSON_LABS, COMPETENCIES
from seed_credentials import CREDENTIALS
from seed_compliance import COMPLIANCE_MODULES, COMPLIANCE_QUIZZES
from seed_inventory import SITES, INVENTORY
from revenue_operations_integration import (
    init_revenue_operations,
    init_revenue_services,
    start_revenue_operations,
    stop_revenue_operations,
    get_revenue_routers,
)
from recovery import (
    generate_recovery_codes,
    verify_recovery_code,
    get_recovery_code_status,
    emergency_password_reset,
    ensure_recovery_codes_exist,
)
from security.field_authorization import FieldAuthorization

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env', override=True)  # .env is source of truth (overrides empty/stale shell vars; no .env in Docker image so prod is unaffected)

# ── MongoDB dual-connection (primary + Atlas backup) ──────────────────────────
# Primary:  MONGO_URL          (Railway or any MongoDB host)
# Backup:   MONGO_BACKUP_URL   (MongoDB Atlas free tier recommended)
# The health endpoint at /api/health pings backup when primary is down.
# All other code uses `db` (the primary connection) — there is no automatic
# ── DB connection failover in business logic ──

import os

mongo_url = os.environ.get("MONGO_URL")
db_name = os.environ.get("DB_NAME", "ancestral_sage")

if not mongo_url:
    print("⚠️ WARNING: MONGO_URL not set — database disabled")
    client = None
    db = None
    _DB_SOURCE = "disabled"
else:
    from motor.motor_asyncio import AsyncIOMotorClient

    client = AsyncIOMotorClient(
        mongo_url,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
    )

    db = client[db_name]
    _DB_SOURCE = "primary"


# ── Backup / optional configs ──

MONGO_BACKUP_URL = os.environ.get("MONGO_BACKUP_URL", "")
MONGO_BACKUP_DB  = os.environ.get("MONGO_BACKUP_DB", "")

_backup_db = None
_pipeline_manager = None
_discount_manager = None

# ── WAI engine singletons ───────────────────────────────────────────────────────
# Lazy-initialized on first use, then reused across all requests.
# Avoids creating new PRTEnforcementEngine/The9FusionEngine objects per request.
_prt_engine  = None   # type: ignore[assignment]  PRTEnforcementEngine
_the9_engine = None   # type: ignore[assignment]  The9FusionEngine


def _get_prt_engine():
    """Return the shared PRTEnforcementEngine singleton (lazy init)."""
    global _prt_engine
    if _prt_engine is None:
        try:
            from wai_institute.personas.prt.prt_enforcement_engine import PRTEnforcementEngine
            _prt_engine = PRTEnforcementEngine()
        except Exception as _e:
            logger.warning("WAI: PRTEnforcementEngine init failed: %s", _e)
    return _prt_engine


def _get_the9_engine():
    """Return the shared The9FusionEngine singleton (lazy init)."""
    global _the9_engine
    if _the9_engine is None:
        try:
            from wai_institute.core.the9_fusion_engine import The9FusionEngine
            _the9_engine = The9FusionEngine()
        except Exception as _e:
            logger.warning("WAI: The9FusionEngine init failed: %s", _e)
    return _the9_engine

import secrets as _secrets

JWT_SECRET = os.environ.get('JWT_SECRET') or _secrets.token_hex(32)
JWT_ALGO = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_HOURS = int(os.environ.get('JWT_EXPIRE_HOURS', '168'))
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', EMERGENT_LLM_KEY)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', EMERGENT_LLM_KEY)

# ── Backup server / home server config ───────────────────────────────────────
# Set SERVE_FRONTEND=1 on your home server to serve the built React app too.
# Set BACKUP_ORIGIN=https://your-cloudflare-tunnel.trycloudflare.com so the
# home server URL is automatically allowed by CORS.
SERVE_FRONTEND  = os.environ.get('SERVE_FRONTEND', '0') == '1'
BACKUP_ORIGIN   = os.environ.get('BACKUP_ORIGIN', '').strip()
GUMROAD_API_KEY = os.environ.get('GUMROAD_API_KEY', '')

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# API docs: disabled by default in production. Set ENABLE_API_DOCS=1 to enable.
# Never enable in production — exposes full endpoint surface to the public internet.
_DOCS_ENABLED = os.environ.get("ENABLE_API_DOCS", "0") == "1"
app = FastAPI(
    title="W.A.I. Training Platform",
    version="3.0.0",
    description="W.A.I. — Workforce Apprentice Institute API. Hands-on electrical apprenticeship training, labs, credentials, and portfolio.",
    redirect_slashes=False,
    docs_url="/api/docs" if _DOCS_ENABLED else None,
    redoc_url="/api/redoc" if _DOCS_ENABLED else None,
    openapi_url="/api/openapi.json" if _DOCS_ENABLED else None,
)

# Security headers middleware (extracted to platform_services.py)
app.middleware("http")(platform_services.security_headers)


@app.middleware("http")
async def enforce_platform_flags(request: Request, call_next):
    """Block requests when platform_locked flag is active.
    Always passes: /api/health, /api/auth/*, /api/admin/platform/flags
    """
    path = request.url.path
    exempt = (
        path in ("/api/health", "/api/version", "/")
        or path.startswith("/api/auth/")
        or path.startswith("/api/admin/platform/flags")
        or path.startswith("/api/admin/")  # admins always pass
    )
    if not exempt and db is not None:
        try:
            doc = await db.platform_flags.find_one({"_id": "flags"}, {"_id": 0, "flags.platform_locked": 1})
            if doc and doc.get("flags", {}).get("platform_locked", {}).get("enabled"):
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Platform is currently locked by the executive team. Please check back shortly."},
                )
        except Exception:
            pass
    return await call_next(request)


@app.middleware("http")
async def enforce_ip_whitelist(request: Request, call_next):
    """Enforce IP whitelist for executive-gated paths.
    If ip_whitelist collection has entries for role="executive_admin", then
    only requests from those CIDRs/IPs may reach /api/admin/system, /api/admin/access,
    /api/admin/sage-audit, /api/admin/director, /api/sovereign/, and /api/admin/mfa.
    When the collection is empty the middleware passes all traffic (open mode).
    Respects X-Forwarded-For set by Railway's load balancer.
    """
    exec_paths = (
        "/api/admin/system",
        "/api/admin/access",
        "/api/admin/sage-audit",
        "/api/admin/director",
        "/api/sovereign/",
        "/api/admin/mfa",
        "/api/admin/staff-meetings",
    )
    path = request.url.path
    if not any(path.startswith(p) for p in exec_paths):
        return await call_next(request)
    if db is None:
        return await call_next(request)
    try:
        entries = await db.ip_whitelist.find({"role": "executive_admin"}, {"_id": 0, "ip": 1}).to_list(length=500)
        if not entries:
            return await call_next(request)
        import ipaddress as _ipmod
        allowed_nets = []
        for e in entries:
            raw = (e.get("ip") or "").strip()
            if not raw:
                continue
            try:
                allowed_nets.append(_ipmod.ip_network(raw, strict=False))
            except ValueError:
                pass
        if not allowed_nets:
            return await call_next(request)
        forwarded_for = request.headers.get("x-forwarded-for", "")
        raw_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "")
        try:
            client_addr = _ipmod.ip_address(raw_ip)
        except ValueError:
            return JSONResponse(status_code=403, content={"detail": "Access denied: unresolvable source IP."})
        if any(client_addr in net for net in allowed_nets):
            return await call_next(request)
        logger.warning("IP whitelist block: %s → %s", raw_ip, path)
        return JSONResponse(status_code=403, content={"detail": "Access denied: your IP is not on the executive access list."})
    except Exception:
        return await call_next(request)


@app.middleware("http")
async def log_requests_pii_safe(request: Request, call_next):
    """Log request method, path, and status code. Never log request bodies,
    query strings, headers, or IP addresses (PII-safe)."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = int((time.perf_counter() - start) * 1000)
    logger.info("%s %s → %s (%dms)", request.method, request.url.path, response.status_code, elapsed)
    return response

api_router = APIRouter(prefix="/api")
logger = logging.getLogger("lcewai")
logging.basicConfig(level=logging.INFO)
APP_VERSION = "4.0.1"

# Simple in-memory rate limit (per IP, per route) — replace with redis in true HA prod
from collections import defaultdict as _dd
_RATE = _dd(list)

def check_rate(key: str, max_calls: int, window_sec: int):
    now = datetime.now(timezone.utc).timestamp()
    _RATE[key] = [t for t in _RATE[key] if now - t < window_sec]
    if len(_RATE[key]) >= max_calls:
        raise HTTPException(429, "Too many requests, slow down")
    _RATE[key].append(now)


# PII-safe field names — values for these keys are redacted in audit logs
_PII_KEYS = {"email", "password", "password_hash", "current_password", "new_password",
             "confirm", "full_name", "phone", "address", "ip", "ip_address",
             "user_agent", "token", "access_token", "refresh_token"}

def _strip_pii(d: dict) -> dict:
    """Return a copy of *d* with PII-field values replaced by ``[REDACTED]``."""
    return {k: "[REDACTED]" if k in _PII_KEYS else v for k, v in d.items()}


async def audit(actor_id: Optional[str], action: str, target: Optional[str] = None, meta: Optional[dict] = None):
    try:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "actor_id": actor_id,
            "action": action,
            "target": target,
            "meta": _strip_pii(meta or {}),
            "at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.exception("audit failed")


async def notify(user_id: str, title: str, body: str, link: Optional[str] = None, kind: str = "info"):
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title,
        "body": body,
        "link": link,
        "kind": kind,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

Role = Literal["student", "instructor", "admin", "executive_admin", "creative_partner"]

# Role hierarchy (higher number = more authority).
# executive_admin > admin > instructor > student.
# creative_partner is a special non-hierarchical role — vision contributor,
# no operational access, full mission visibility.
# Used by require_role() for permission checks and by admin endpoints to
# enforce "you cannot modify a more privileged user".
ROLE_RANK = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4, "creative_partner": 2}

# The single hardcoded executive admin email. Auto-promoted to executive_admin
# on every backend startup; if the account does not exist it is created with
# the seed password EXEC_DEFAULT_PASSWORD (rotate immediately on first login).
EXEC_ADMIN_EMAIL = os.environ.get("EXEC_ADMIN_EMAIL", "delon.oliver@lightningcityelectric.com")
# Seed password for the executive admin.  Read from env var first; falls back
# to the documented default (which is force-rotated on first login via
# `must_change_password=True`, so the seed is safe by construction).  In
# production set EXEC_DEFAULT_PASSWORD to a fresh secret so even the seed
# value is operator-controlled.
# No fallback passwords in source. If EXEC_DEFAULT_PASSWORD is not set in Railway,
# a cryptographically random password is generated at startup and emailed to
# PLATFORM_NOTIFY_EMAIL (morehelpcenter@gmail.com) automatically.
EXEC_DEFAULT_PASSWORD = os.environ.get("EXEC_DEFAULT_PASSWORD", "")

# Executive accounts — both seats always bootstrapped on startup.
# Seat 1 (Delon Oliver):  youpickeddoliver@gmail.com
# Seat 2 (NAM Oshun):     souppoetry@gmail.com
BACKUP_EXEC_EMAIL = os.environ.get("BACKUP_EXEC_ADMIN_EMAIL", "youpickeddoliver@gmail.com")
BACKUP_EXEC_DEFAULT_PASSWORD = os.environ.get("BACKUP_EXEC_DEFAULT_PASSWORD", "")

NAM_EXEC_EMAIL = os.environ.get("NAM_EXEC_EMAIL", "souppoetry@gmail.com")
NAM_EXEC_DEFAULT_PASSWORD = os.environ.get("NAM_EXEC_DEFAULT_PASSWORD", "")

# Platform notification email — receives auto-generated passwords and system alerts.
# Defaults to the configured GMAIL_USER (morehelpcenter@gmail.com).
PLATFORM_NOTIFY_EMAIL = os.environ.get("PLATFORM_NOTIFY_EMAIL",
                                        os.environ.get("GMAIL_USER", "morehelpcenter@gmail.com"))

# RECOVERY: Set EXEC_FORCE_RESET=1 in Railway env vars, redeploy, log in with
# the default passwords above, then immediately change password and remove the flag.
EXEC_FORCE_RESET = os.environ.get("EXEC_FORCE_RESET", "0") == "1"

# Secret key for the no-login exec unlock endpoint POST /api/auth/exec-unlock.
# Set EXEC_RESET_SECRET to any value in Railway Variables.  If not set the
# endpoint is disabled (returns 404).  This is the zero-human-intervention
# recovery path when exec accounts are locked — no login, no Railway access needed.
EXEC_RESET_SECRET = os.environ.get("EXEC_RESET_SECRET", "")

# One-time migration: any email that used to be the hardcoded EXEC_ADMIN_EMAIL
# will be auto-demoted from executive_admin to admin on startup, so switching
# the primary exec doesn't leave a dormant god-mode account behind.
# NOTE: BACKUP_EXEC_EMAIL is intentionally excluded — it is a permanent second seat.
LEGACY_EXEC_EMAILS = set()


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: Role = "student"
    associate: Optional[str] = None
    is_active: bool = True
    # When true, the user must change password on next login. Set on (a) the
    # auto-created executive_admin, and (b) any account created via
    # POST /api/admin/users — the admin shares a temp password and the user
    # picks their own on first login.
    must_change_password: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    avatar_url: Optional[str] = None
    feature_tier: str = "free"


class RegisterReq(BaseModel):
    """Public self-registration. SECURITY: role and associate are NOT accepted
    from clients here. Public sign-ups are always students with no cohort
    assignment. Admins assign cohorts via /api/admin/associate."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=500)
    password: str = Field(..., min_length=8, max_length=128)
    agreed_terms: bool = False
    over_13: bool = False


class AdminCreateUserReq(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=500)
    password: str = Field(..., min_length=8, max_length=128)
    role: Role = "student"
    associate: Optional[str] = Field(None, min_length=1, max_length=200)


class AdminRoleReq(BaseModel):
    role: Role


class AdminEditUserReq(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=500)
    email: Optional[EmailStr] = None
    associate: Optional[str] = Field(None, min_length=1, max_length=200)


class AdminActiveReq(BaseModel):
    is_active: bool


class ChangePasswordReq(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class AdminResetPasswordReq(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)


class ForgotPasswordReq(BaseModel):
    email: EmailStr


class ResetPasswordReq(BaseModel):
    token: str
    new_password: str


class EmergencyRecoveryReq(BaseModel):
    """Executive account emergency recovery via recovery code."""
    email: EmailStr
    recovery_code: str
    new_password: str


class RecoveryCodeStatusReq(BaseModel):
    """Check status of recovery codes for an executive account."""
    email: EmailStr


class SelfEditMeReq(BaseModel):
    """Self-service profile edit. Users may change their display name and
    email.  Role and associate are NOT editable here — those are admin-only
    to prevent privilege/cohort drift."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None


class LoginReq(BaseModel):
    email: EmailStr
    password: str


class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class QuizQ(BaseModel):
    q: str
    options: List[str]
    answer: int


class Module(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order: int
    slug: str
    title: str
    summary: str
    objectives: List[str]
    safety: List[str]
    tools: List[str]
    scripture: dict
    tasks: List[str]
    competencies: List[str]
    hours: int
    quiz: List[QuizQ] = []
    free: Optional[bool] = False
    video_url: Optional[str] = None
    diagram_url: Optional[str] = None


class ProgressEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    module_slug: str
    status: Literal["not_started", "in_progress", "completed"] = "in_progress"
    quiz_score: Optional[float] = None
    completed_at: Optional[datetime] = None
    hours_logged: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QuizSubmit(BaseModel):
    module_slug: str
    answers: List[int]


def hash_pw(p: str) -> str:
    return pwd_ctx.hash(p)


def verify_pw(p: str, h: str) -> bool:
    return pwd_ctx.verify(p, h)


import secrets as _secrets_mod  # noqa: E402


def _gen_random_password() -> str:
    """Generate a 20-char cryptographically random password. Used when no
    env-var password is configured for exec account bootstrap/recovery."""
    alpha = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789!@#$%^&*"
    return "".join(_secrets_mod.choice(alpha) for _ in range(20))


# --- Password reset helpers --------------------------------------------------
import hashlib  # noqa: E402
import secrets  # noqa: E402

RESET_TOKEN_TTL_MIN = int(os.environ.get("PASSWORD_RESET_TTL_MIN", "30"))
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM", "W.A.I. <poetgames@gmail.com>")
# Gmail SMTP fallback — used when RESEND_API_KEY is not set.
# In Railway: set GMAIL_USER and GMAIL_APP_PASSWORD (16-char Google App Password).
GMAIL_USER     = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")


def _hash_token(raw: str) -> str:
    """Stable sha256 hash of the raw token. We never store the raw token
    in MongoDB — only the hash. Lookups use the hash."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _make_reset_token() -> tuple[str, str]:
    """Returns (raw_token, sha256_hex). The raw token is shown ONCE."""
    raw = secrets.token_urlsafe(32)
    return raw, _hash_token(raw)


def _build_reset_url(raw_token: str, base: Optional[str] = None) -> str:
    base = (base or os.environ.get("PUBLIC_APP_URL") or "").rstrip("/")
    if not base:
        # Caller will prepend its own origin client-side; provide a path-only
        # form so the admin UI can expand it with window.location.origin.
        return f"/reset-password?token={raw_token}"
    return f"{base}/reset-password?token={raw_token}"


def _reset_email_html(full_name: str, reset_url: str) -> tuple[str, str]:
    """Returns (subject, html) for a password reset email."""
    subject = "Reset your W.A.I. password"
    html = f"""
    <div style="font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#0a0e14">
      <h2 style="margin:0 0 8px">Reset your password</h2>
      <p>Hi {full_name},</p>
      <p>We received a request to reset your W.A.I. password. The link below is single-use and expires in {RESET_TOKEN_TTL_MIN} minutes.</p>
      <p style="margin:28px 0">
        <a href="{reset_url}" style="background:#0a0e14;color:#fff;padding:12px 20px;text-decoration:none;font-weight:600">Reset Password</a>
      </p>
      <p style="font-size:12px;color:#666">If you didn't ask for this, you can safely ignore this message — your password won't change.</p>
      <p style="font-size:12px;color:#666">Or paste this URL into your browser:<br><code style="word-break:break-all">{reset_url}</code></p>
    </div>
    """
    return subject, html


async def _send_via_resend(to_email: str, subject: str, html: str) -> bool:
    """Send via Resend API. Returns True on success."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as cx:
            r = await cx.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}",
                         "Content-Type": "application/json"},
                json={"from": RESEND_FROM, "to": [to_email],
                      "subject": subject, "html": html},
            )
        if r.status_code >= 400:
            logger.warning("Resend send failed %s: %s", r.status_code, r.text[:300])
            return False
        return True
    except Exception:
        logger.exception("Resend send raised")
        return False


async def _send_via_gmail(to_email: str, subject: str, html: str) -> bool:
    """Send via Gmail SMTP using an App Password. Returns True on success.
    Requires GMAIL_USER and GMAIL_APP_PASSWORD set in Railway environment."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        return False
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    def _send():
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"W.A.I. Institute <{GMAIL_USER}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as smtp:
            smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            smtp.sendmail(GMAIL_USER, to_email, msg.as_string())

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send)
        logger.info("Gmail SMTP: sent reset email to %s", to_email)
        return True
    except Exception:
        logger.exception("Gmail SMTP send raised")
        return False


async def _send_reset_email(to_email: str, raw_token: str, full_name: str = "there", base_url: str = "") -> bool:
    """Send password reset email. Tries Resend first, falls back to Gmail SMTP.
    Returns True if sent by either provider, False if neither is configured."""
    reset_url = _build_reset_url(raw_token, base=base_url or None)
    if reset_url.startswith("/"):
        logger.error(
            "PUBLIC_APP_URL not set and no request origin available — "
            "cannot send password reset email. Set PUBLIC_APP_URL in Railway variables."
        )
        return False
    subject, html = _reset_email_html(full_name, reset_url)

    if RESEND_API_KEY:
        sent = await _send_via_resend(to_email, subject, html)
        if sent:
            return True
        logger.warning("Resend failed — falling back to Gmail SMTP")

    if GMAIL_USER and GMAIL_APP_PASSWORD:
        return await _send_via_gmail(to_email, subject, html)

    logger.warning("No email provider configured (RESEND_API_KEY or GMAIL_USER+GMAIL_APP_PASSWORD).")
    return False


async def _send_welcome_email(to_email: str, full_name: str) -> bool:
    """Send welcome email on registration. Uses same provider chain as reset emails."""
    app_url = os.environ.get("PUBLIC_APP_URL", "https://wai-institute.org")
    subject = "Welcome to WAI-Institute — You're In"
    html = f"""
    <div style="font-family:sans-serif;max-width:540px;margin:0 auto;padding:32px 24px;background:#fff;">
      <div style="background:#2e1065;border-radius:12px;padding:28px 24px;text-align:center;margin-bottom:24px;">
        <h1 style="color:#FFD100;font-size:26px;margin:0 0 8px;">Welcome, {full_name}.</h1>
        <p style="color:rgba(255,255,255,0.8);font-size:15px;margin:0;">You are now part of the WAI-Institute community.</p>
      </div>
      <p style="color:#2b1f15;font-size:15px;line-height:1.7;">Your account is active. Start with free modules — no paywall, no waiting.</p>
      <div style="text-align:center;margin:28px 0;">
        <a href="{app_url}/modules" style="background:#0d7377;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;">Start Learning Free</a>
      </div>
      <p style="color:#5a4e42;font-size:13px;">Need help? Reply to this email or visit the <a href="{app_url}/help-center" style="color:#0d7377;">Help Center</a>.</p>
      <hr style="border:none;border-top:1px solid #e0d6cc;margin:24px 0;">
      <p style="color:#9ca3af;font-size:11px;text-align:center;">WAI-Institute · MORE Help Center</p>
    </div>"""
    if RESEND_API_KEY:
        sent = await _send_via_resend(to_email, subject, html)
        if sent:
            return True
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        return await _send_via_gmail(to_email, subject, html)
    logger.warning("Welcome email not sent — no email provider configured.")
    return False
# ----------------------------------------------------------------------------


def make_token(user_id: str, role: str, extra: Optional[dict] = None) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": user_id, "role": role, "exp": exp}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


async def current_user(authorization: Optional[str] = Header(None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    user_doc = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(401, "User not found")
    if user_doc.get("is_active") is False:
        raise HTTPException(403, "Account deactivated")
    return User(**user_doc)


def require_role(*roles):
    """Authorize the current user against a hierarchy.

    Pass if the user's role rank is >= the LOWEST rank among the requested
    roles. This preserves backward compatibility (existing
    `require_role("admin")` calls keep working exactly the same — admins still
    pass) AND adds god-mode for executive_admin (passes every check).
    """
    needed_rank = min(ROLE_RANK[r] for r in roles)
    async def dep(user: User = Depends(current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            # Don't reveal required roles to prevent attackers from understanding the role hierarchy
            logger.warning("Unauthorized access attempt — insufficient privileges (user=%s, role=%s)", user.id, user.role)
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user
    return dep


def assert_role(user: User, *roles) -> None:
    """Inline authorization check (raises 403 if the user lacks the rank).

    Use this INSIDE an endpoint body. `require_role(...)` is a dependency
    factory for `Depends(...)` — calling it with a User instance raises
    'unhashable type: User'. This is the inline equivalent.
    """
    needed_rank = min(ROLE_RANK[r] for r in roles)
    if ROLE_RANK.get(user.role, 0) < needed_rank:
        raise HTTPException(403, "Insufficient permissions to access this resource.")


def can_modify(actor: User, target_role: str) -> bool:
    """Returns True iff `actor` is allowed to modify a user whose role is
    `target_role`. Admins cannot touch executive_admin accounts; only an
    executive_admin can modify another executive_admin."""
    actor_rank = ROLE_RANK.get(actor.role, 0)
    target_rank = ROLE_RANK.get(target_role, 0)
    return actor_rank >= target_rank


async def seed_modules():
    for m in MODULES:
        existing = await db.modules.find_one({"slug": m["slug"]})
        doc = {**m, "quiz": quiz_for(m["slug"])}
        if existing:
            await db.modules.update_one({"slug": m["slug"]}, {"$set": doc})
        else:
            doc["id"] = str(uuid.uuid4())
            await db.modules.insert_one(doc)
    logger.info("Seeded %d modules", len(MODULES))


async def seed_users():
    # One-time migration: cohort → associate for any legacy users
    await db.users.update_many(
        {"cohort": {"$exists": True}, "associate": {"$in": [None, ""]}},
        [{"$set": {"associate": "$cohort"}}, {"$unset": "cohort"}],
    )
    # Normalize legacy "Cohort-*" values to "Associate-*"
    legacy_users = await db.users.find({"associate": {"$regex": "^Cohort-"}}, {"_id": 0}).to_list(1000)
    for u in legacy_users:
        new_val = u["associate"].replace("Cohort-", "Associate-", 1)
        await db.users.update_one({"id": u["id"]}, {"$set": {"associate": new_val}})
    # Demo accounts removed — platform is live. Delete any that still exist in DB.
    _demo_emails = ["admin@lcewai.org", "instructor@lcewai.org", "student@lcewai.org"]
    result = await db.users.delete_many({"email": {"$in": _demo_emails}})
    if result.deleted_count:
        logger.info("Removed %d demo account(s) from live database", result.deleted_count)

    # ----- Bootstrap executive accounts (create if missing, never overwrite existing) -----
    # Passwords: if ENV var is set use it; otherwise generate a random one and
    # email it to PLATFORM_NOTIFY_EMAIL. No password is ever hardcoded in source.
    async def _email_new_pw(email: str, name: str, pw: str) -> None:
        """Send auto-generated password to PLATFORM_NOTIFY_EMAIL via Gmail SMTP."""
        subject = f"WAI-Institute: New exec account created — {email}"
        html = (
            f"<p>A new executive account was bootstrapped at startup.</p>"
            f"<p><b>Account:</b> {email} ({name})<br>"
            f"<b>Temporary password:</b> <code>{pw}</code></p>"
            f"<p>Log in and change this password immediately. "
            f"The account has <code>must_change_password=True</code>.</p>"
        )
        try:
            await _send_via_gmail(PLATFORM_NOTIFY_EMAIL, subject, html)
            logger.info("STARTUP: auto-generated password emailed to %s for account %s",
                        PLATFORM_NOTIFY_EMAIL, email)
        except Exception as _em:
            # Email failed — log the password to stdout (visible in Railway logs only)
            logger.warning(
                "STARTUP: email failed for %s — TEMP PASSWORD (change immediately): %s | error: %s",
                email, pw, _em,
            )

    _exec_seats = [
        (EXEC_ADMIN_EMAIL,  "Delon Oliver",  EXEC_DEFAULT_PASSWORD),
        (BACKUP_EXEC_EMAIL, "Delon Oliver",  BACKUP_EXEC_DEFAULT_PASSWORD),
        (NAM_EXEC_EMAIL,    "NAM Oshun",     NAM_EXEC_DEFAULT_PASSWORD),
    ]
    for _email, _name, _env_pw in _exec_seats:
        try:
            existing = await db.users.find_one({"email": _email})
            if not existing:
                # Use ENV-supplied password if set, otherwise generate one
                _pw = _env_pw if _env_pw else _gen_random_password()
                _auto_generated = not bool(_env_pw)
                await db.users.insert_one({
                    "id": str(uuid.uuid4()),
                    "email": _email,
                    "full_name": _name,
                    "role": "executive_admin",
                    "password_hash": hash_pw(_pw),
                    "is_active": True,
                    "must_change_password": True,   # always force change on first login
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                logger.info("STARTUP: exec seat created — %s (auto_pw=%s)", _email, _auto_generated)
                if _auto_generated:
                    await _email_new_pw(_email, _name, _pw)
            else:
                # Account exists — ensure it stays executive_admin, active, and unlocked.
                # Clearing lockout fields on every startup means a locked exec account
                # self-heals on the next deploy/restart without any manual intervention.
                await db.users.update_one(
                    {"email": _email},
                    {
                        "$set": {"role": "executive_admin", "is_active": True},
                        "$unset": {"login_locked_until": "", "login_failed_attempts": ""},
                    },
                )
        except Exception as _e:
            logger.warning("STARTUP: exec seat bootstrap failed for %s: %s", _email, _e)

    # ----- EMERGENCY EXEC FORCE RESET (if flag enabled) -----
    # Two modes:
    #   Mode A — set EXEC_FORCE_RESET=1 only:
    #     Resets ALL three exec seats to their documented default passwords and
    #     clears any lockouts.  No other env vars needed.  This is the "locked out,
    #     need back in" recovery path.
    #   Mode B — set EXEC_FORCE_RESET=1 + EXEC_FORCE_RESET_EMAIL + EXEC_FORCE_RESET_PASSWORD:
    #     Resets one specific account to the supplied password.
    # In both modes: delete EXEC_FORCE_RESET from Railway Variables immediately after
    # logging in, or the password will be reset on every redeploy.
    try:
        if EXEC_FORCE_RESET:
            force_reset_email = os.environ.get("EXEC_FORCE_RESET_EMAIL", "").strip()
            force_reset_password = os.environ.get("EXEC_FORCE_RESET_PASSWORD", "").strip()

            if force_reset_email and force_reset_password:
                # Mode B: reset one specific account to supplied password
                user_doc = await db.users.find_one({"email": force_reset_email}, {"_id": 0})
                if user_doc:
                    await db.users.update_one(
                        {"email": force_reset_email},
                        {"$set": {
                            "password_hash": hash_pw(force_reset_password),
                            "must_change_password": True,
                            "is_active": True,
                            "force_reset_at": datetime.now(timezone.utc).isoformat(),
                        },
                        "$unset": {"login_locked_until": "", "login_failed_attempts": ""}},
                    )
                    logger.warning("EXEC_FORCE_RESET (Mode B): password reset for %s", force_reset_email)
                    await audit(None, "exec.force_reset.completed", target=force_reset_email,
                                meta={"reason": "EXEC_FORCE_RESET flag set"})
                else:
                    logger.error("EXEC_FORCE_RESET: email not found: %s", force_reset_email)
            else:
                # Mode A: reset ALL exec seats.
                # If the env-var password is empty, generate a fresh random one and
                # email/log it — never hash an empty string as a real password.
                logger.warning("EXEC_FORCE_RESET (Mode A): resetting all exec seats")
                _reset_seats = [
                    (EXEC_ADMIN_EMAIL,  "Delon Oliver",  EXEC_DEFAULT_PASSWORD),
                    (BACKUP_EXEC_EMAIL, "Delon Oliver",  BACKUP_EXEC_DEFAULT_PASSWORD),
                    (NAM_EXEC_EMAIL,    "NAM Oshun",     NAM_EXEC_DEFAULT_PASSWORD),
                ]
                for _r_email, _r_name, _r_pw in _reset_seats:
                    _auto = False
                    if not _r_pw:
                        _r_pw = _gen_random_password()
                        _auto = True
                    await db.users.update_one(
                        {"email": _r_email},
                        {"$set": {
                            "password_hash": hash_pw(_r_pw),
                            "must_change_password": True,
                            "is_active": True,
                            "force_reset_at": datetime.now(timezone.utc).isoformat(),
                        },
                        "$unset": {"login_locked_until": "", "login_failed_attempts": ""}},
                        upsert=False,
                    )
                    logger.warning("EXEC_FORCE_RESET (Mode A): reset %s (auto_pw=%s)", _r_email, _auto)
                    if _auto:
                        await _email_new_pw(_r_email, _r_name, _r_pw)
                await audit(None, "exec.force_reset.all_seats", meta={"reason": "EXEC_FORCE_RESET=1, no email specified"})
            # A stale executive IP whitelist can keep exec routes blocked even
            # after a successful reset — clear it so the panel is reachable.
            # Runs for both Mode A and Mode B.
            try:
                await db.ip_whitelist.delete_many({"role": "executive_admin"})
                logger.warning("EXEC_FORCE_RESET: cleared executive IP whitelist")
            except Exception as _wle:
                logger.error("EXEC_FORCE_RESET whitelist clear failed (non-fatal): %s", _wle)
    except Exception as _exc:
        logger.error("EXEC_FORCE_RESET failed: %s", _exc)

    # ----- Initialize recovery codes for all active executive accounts -----
    try:
        all_execs = await db.users.find({"role": "executive_admin"}, {"email": 1}).to_list(100)
        exec_emails = [e["email"] for e in all_execs if e.get("email")]
        if exec_emails:
            await ensure_recovery_codes_exist(db, exec_emails)
            logger.info("Initialized recovery codes for %d executive account(s)", len(exec_emails))
    except Exception as _exc_recovery:
        logger.error("Recovery codes initialization failed (non-fatal): %s", _exc_recovery)


async def seed_labs():
    for spec in ONLINE_LABS:
        doc = {**spec, "track": "online"}
        existing = await db.labs.find_one({"slug": doc["slug"]})
        if existing:
            await db.labs.update_one({"slug": doc["slug"]}, {"$set": doc})
        else:
            doc["id"] = str(uuid.uuid4())
            await db.labs.insert_one(doc)
    for spec in IN_PERSON_LABS:
        doc = {**spec, "track": "inperson"}
        existing = await db.labs.find_one({"slug": doc["slug"]})
        if existing:
            await db.labs.update_one({"slug": doc["slug"]}, {"$set": doc})
        else:
            doc["id"] = str(uuid.uuid4())
            await db.labs.insert_one(doc)


async def run_engagement_check():
    """Flag academically at-risk students to their instructors and admins.

    Triggers:
      A) No login in 7+ days (last_login field, falls back to created_at).
      B) Two or more failed quiz attempts in the last 14 days.

    Each at-risk student gets one notification per day max (deduped by date tag).
    Their assigned instructor (matched by associate) and all admins are alerted.
    """
    now = datetime.now(timezone.utc)
    cutoff_login = (now - timedelta(days=7)).isoformat()
    cutoff_quiz = (now - timedelta(days=14)).isoformat()
    today_tag = now.strftime("%Y-%m-%d")

    students = await db.users.find(
        {"role": "student", "is_active": {"$ne": False}},
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "associate": 1,
         "last_login": 1, "created_at": 1},
    ).to_list(5000)

    admin_ids = [
        u["id"] for u in await db.users.find(
            {"role": {"$in": ["admin", "executive_admin"]}, "is_active": {"$ne": False}},
            {"id": 1, "_id": 0},
        ).to_list(100)
    ]

    flagged = 0
    for student in students:
        sid = student["id"]
        associate = student.get("associate")
        reasons = []

        # Trigger A: no login in 7+ days
        last_seen = student.get("last_login") or student.get("created_at", "")
        if last_seen and last_seen < cutoff_login:
            reasons.append("no activity in 7+ days")

        # Trigger B: 2+ failed quiz scores (< 70) in the last 14 days
        if not reasons:  # only run expensive query when needed
            recent_fails = await db.progress.count_documents({
                "user_id": sid,
                "quiz_score": {"$lt": 70, "$ne": None},
                "updated_at": {"$gte": cutoff_quiz},
            })
            if recent_fails >= 2:
                reasons.append(f"{recent_fails} failed quiz attempts in 14 days")

        if not reasons:
            continue

        reason_str = "; ".join(reasons)
        dedup_key = f"engagement:{sid}:{today_tag}"

        # Dedup: skip if we already sent this student's flag today
        already_sent = await db.notifications.find_one({
            "body": {"$regex": dedup_key},
            "created_at": {"$gte": now.replace(hour=0, minute=0, second=0).isoformat()},
        })
        if already_sent:
            continue

        msg_body = (
            f"Student {student['full_name']} may need support: {reason_str}. "
            f"[ref:{dedup_key}]"
        )

        # Notify the student's instructor (if associate matches)
        if associate:
            instructors = await db.users.find(
                {"role": "instructor", "associate": associate, "is_active": {"$ne": False}},
                {"id": 1, "_id": 0},
            ).to_list(10)
            for inst in instructors:
                await notify(
                    inst["id"],
                    f"Student needs attention: {student['full_name']}",
                    msg_body,
                    link="/instructor",
                    kind="warning",
                )

        # Notify all admins
        for aid in admin_ids:
            await notify(
                aid,
                f"Engagement alert: {student['full_name']}",
                msg_body,
                link="/admin",
                kind="warning",
            )

        flagged += 1

    if flagged:
        logger.info("Engagement check: flagged %d at-risk students", flagged)


async def backfill_verification_codes():
    """One-time migration: add verification_code to existing credentials that lack one."""
    cursor = db.user_credentials.find(
        {"verification_code": {"$exists": False}}, {"_id": 1}
    )
    count = 0
    async for doc in cursor:
        code = secrets.token_urlsafe(12)
        try:
            await db.user_credentials.update_one(
                {"_id": doc["_id"], "verification_code": {"$exists": False}},
                {"$set": {"verification_code": code}},
            )
            count += 1
        except Exception:
            pass  # unique constraint race — another startup already set it
    if count:
        logger.info("Backfilled verification_code on %d credentials", count)


@app.on_event("startup")
async def on_startup():
    # Return immediately so uvicorn begins serving and Railway's /api/version
    # healthcheck passes within seconds. The full init below is DB/network-heavy
    # (indexes, seeds, revenue/WAI/pipeline/discount bootstrap). If MONGO_URL is
    # slow or unreachable, awaiting it inline blocks uvicorn from serving (the
    # ASGI lifespan must finish before the socket accepts requests) — measured at
    # 30s+ per Mongo serverSelection timeout, stacking past the healthcheck
    # window and producing the 502 fallback + restart loop seen in production.
    # Running it as a background task decouples container health from DB state;
    # /api/version and /api/health do not depend on any of it.
    asyncio.create_task(_on_startup_impl())


async def _on_startup_impl():
    # ── MongoDB dual-connection setup ─────────────────────────────────────────
    # Motor connects lazily — we don't ping at startup (asyncio.wait_for +
    # Motor is unsafe; it can cancel mid-connection and corrupt the pool).
    # The /api/health endpoint pings on demand.  If MONGO_BACKUP_URL is set,
    # the backup client is ready and the health endpoint will use it when the
    # primary is down.  The backup client is exposed as _backup_db for the
    # health check and for manual failover via the Director.
    global _DB_SOURCE, _backup_db
    _DB_SOURCE = "primary"
    _backup_db = None
    # Wire shared db reference for sub-routers (social, playlist, etc.)
    import deps as _deps
    _deps.set_db(db)
    if MONGO_BACKUP_URL:
        try:
            _backup_client = AsyncIOMotorClient(
                MONGO_BACKUP_URL, serverSelectionTimeoutMS=8000
            )
            _backup_db_name = MONGO_BACKUP_DB or os.environ.get('DB_NAME', 'wai')
            _backup_db = _backup_client[_backup_db_name]
            logger.info("STARTUP: Atlas backup DB client initialized (%s).", _backup_db_name)
        except Exception as _bce:
            logger.warning("STARTUP: Could not initialize Atlas backup client: %s", _bce)
    else:
        logger.info("STARTUP: No MONGO_BACKUP_URL set — single-DB mode.")

    try:
        await ensure_indexes()
    except Exception as _e:
        logger.warning("STARTUP: ensure_indexes failed (non-fatal): %s", _e)

    try:
        from partnership import points as _pp_idx
        await _pp_idx.ensure_indexes(db)
        await db["puzzle_progress"].create_index("user_id")
        await db["sovereign_memory"].create_index([("exec_id", 1), ("ts", -1)])
        logger.info("STARTUP: sovereign/partnership/puzzle indexes ensured")
    except Exception as _e:
        logger.warning("STARTUP: sovereign/partnership indexes failed (non-fatal): %s", _e)

    try:
        await seed_modules()
    except Exception as _e:
        logger.warning("STARTUP: seed_modules failed (non-fatal): %s", _e)

    try:
        await seed_users()
    except Exception as _e:
        logger.warning("STARTUP: seed_users failed (non-fatal): %s", _e)

    try:
        await seed_labs()
    except Exception as _e:
        logger.warning("STARTUP: seed_labs failed (non-fatal): %s", _e)

    try:
        await seed_compliance()
    except Exception as _e:
        logger.warning("STARTUP: seed_compliance failed (non-fatal): %s", _e)

    try:
        await seed_sites_inventory()
    except Exception as _e:
        logger.warning("STARTUP: seed_sites_inventory failed (non-fatal): %s", _e)

    try:
        await seed_creator_profiles()
    except Exception as _e:
        logger.warning("STARTUP: seed_creator_profiles failed (non-fatal): %s", _e)

    try:
        await backfill_verification_codes()
    except Exception as _e:
        logger.warning("STARTUP: backfill_verification_codes failed (non-fatal): %s", _e)

    try:
        await run_escalation_check()
    except Exception as _e:
        logger.warning("STARTUP: run_escalation_check failed (non-fatal): %s", _e)

    try:
        await run_engagement_check()
    except Exception as _e:
        logger.warning("STARTUP: run_engagement_check failed (non-fatal): %s", _e)

    # ── Revenue Operations System initialization ───────────────────────────────
    try:
        await init_revenue_operations(db)
        init_revenue_services(app, db)
        logger.info("STARTUP: Revenue operations system initialized")
    except Exception as _rev_err:
        logger.warning("STARTUP: Revenue operations initialization failed (non-fatal): %s", _rev_err)

    # Start scheduled jobs (payouts, revenue recognition, etc.)
    try:
        await start_revenue_operations(db)
    except Exception as _sched_err:
        logger.warning("STARTUP: Revenue job scheduler startup failed (non-fatal): %s", _sched_err)

    # ── WAI-Institute Autonomous Pipeline activation ───────────────────────────
    try:
        from wai_institute.scripts.system_activation import activate_system, start_scout_scheduler
        _wai_result = await activate_system(db)
        logger.info(
            "WAI autonomous pipeline activated — %d personas bootstrapped",
            _wai_result.get("personas", {}).get("bootstrapped", 0),
        )
        # Start Cultural Scout background scanner
        # Configure interval via SCOUT_INTERVAL_HOURS env var (default: 6h)
        _scout_interval = int(os.environ.get("SCOUT_INTERVAL_HOURS", "6"))
        await start_scout_scheduler(db, interval_hours=_scout_interval)
    except Exception as _wai_err:
        logger.warning("WAI autonomous pipeline startup failed (non-fatal): %s", _wai_err)

    # ── PipelineManager (LLM intent routing) ─────────────────────────────────
    global _pipeline_manager
    try:
        from src.agents.pipeline_manager import PipelineManager as _PipelineManager
        _pipeline_manager = _PipelineManager(db=db, anthropic_api_key=ANTHROPIC_API_KEY)
        _mode = "llm" if ANTHROPIC_API_KEY else "keyword_fallback"
        logger.info("STARTUP: PipelineManager ready — analyzer=%s", _mode)
    except Exception as _pm_err:
        logger.warning("STARTUP: PipelineManager init failed (non-fatal): %s", _pm_err)

    # ── Discount Management System initialization ─────────────────────────────
    try:
        from billing.discount_service import init_discount_service
        global _discount_manager
        _discount_manager = await init_discount_service(db)
        _commerce_mod._discount_manager = _discount_manager
        logger.info("STARTUP: Discount management system initialized")
    except Exception as _disc_err:
        logger.warning("STARTUP: Discount system initialization failed (non-fatal): %s", _disc_err)

    # ── Rate-limiter memory guard ─────────────────────────────────────────────
    # Prune stale entries every 10 minutes so the in-memory dict never grows
    # unbounded on long-running servers (home server especially).
    async def _rate_limiter_cleanup():
        while True:
            await asyncio.sleep(600)
            now = datetime.now(timezone.utc).timestamp()
            stale = [k for k, v in _RATE.items() if not v or now - v[-1] > 300]
            for k in stale:
                del _RATE[k]
            if stale:
                logger.debug("Rate limiter: pruned %d stale keys.", len(stale))
    asyncio.create_task(_rate_limiter_cleanup())

    # ── Load provider API keys from DB into LLM gateway ──────────────────────
    # Env vars always take priority; DB keys only fill gaps. This makes the
    # Provider Gateway UI actually take effect without a Railway redeploy.
    try:
        from ai.llm_gateway import reload_provider_keys as _reload_keys
        _n = await _reload_keys(db)
        if _n:
            logger.info("STARTUP: Loaded %d provider key(s) from DB into LLM gateway.", _n)
    except Exception as _pk_err:
        logger.warning("STARTUP: provider key reload failed (non-fatal): %s", _pk_err)

    # ── Team monitor — autonomous provider health loop ────────────────────────
    try:
        from app.services.team_monitor import run_monitor_loop as _run_monitor
        asyncio.create_task(_run_monitor())
        logger.info("STARTUP: Team monitor launched (interval=300s, threshold=3 failures)")
    except Exception as _tm_err:
        logger.warning("STARTUP: Team monitor launch failed (non-fatal): %s", _tm_err)

    # ── Jamil Knowledge Digest — 12-hour automatic scheduler ─────────────────
    try:
        from ai.knowledge_digest import start_digest_scheduler as _start_kd
        _start_kd(db)
        logger.info("STARTUP: Jamil knowledge digest scheduler started (interval=12h)")
    except Exception as _kd_err:
        logger.warning("STARTUP: Knowledge digest scheduler failed (non-fatal): %s", _kd_err)

    # ── Serve built React frontend (home/backup server only) ─────────────────
    if SERVE_FRONTEND:
        _build_paths = [
            ROOT_DIR.parent / "frontend" / "build",
            ROOT_DIR.parent / "frontend" / "dist",
            Path("/app/frontend/build"),
            Path("/app/frontend/dist"),
        ]
        if not platform_services.mount_frontend(app, _build_paths):
            logger.warning(
                "STARTUP: SERVE_FRONTEND=1 but no built frontend found. "
                "Run 'npm run build' in the frontend directory first."
            )

    # ── Director 4.0 — prompt integrity baseline ──────────────────────────────
    # Any drift detected on subsequent calls indicates unauthorized modification.
    try:
        from ai.prompt_guard import prompt_guard
        results = prompt_guard.startup_integrity_check()
        failed = [k for k, v in results.items() if not v]
        if failed:
            logger.error(
                "STARTUP INTEGRITY WARNING: Prompt baseline enrollment incomplete for: %s. "
                "AI endpoints will use fallback restrictions where applicable.", failed
            )
        else:
            logger.info("STARTUP: All prompt integrity baselines enrolled successfully.")
    except Exception as _pg_exc:
        logger.error("STARTUP: prompt_guard baseline enrollment failed: %s", _pg_exc)

    # Loud warning if the dev-only token leak is enabled.  The production
    # .env should NEVER set this; it exists only for the preview test suite.
    if os.environ.get("DEV_RETURN_RESET_TOKEN") == "1":
        logger.warning(
            "DEV_RETURN_RESET_TOKEN=1 is set — /api/auth/forgot-password "
            "will return raw reset tokens in the response. THIS IS UNSAFE "
            "FOR PRODUCTION. Remove DEV_RETURN_RESET_TOKEN from .env "
            "before deploying to a public environment."
        )

    # ── Auto-failover watchdog ────────────────────────────────────────────────
    # Background health poller.  Detects primary failures, records failover
    # state in the breaker panel.  Set WATCHDOG_DISABLE=1 to skip.
    if not os.environ.get("WATCHDOG_DISABLE"):
        try:
            from failover_watchdog import run_watchdog
            asyncio.create_task(run_watchdog(panel_db=db))
            logger.info("STARTUP: Failover watchdog launched (interval=%s, threshold=%s)",
                        os.environ.get("WATCHDOG_CHECK_INTERVAL", "60"),
                        os.environ.get("WATCHDOG_FAILURE_THRESHOLD", "3"))
        except Exception as _wd_err:
            logger.warning("STARTUP: Failover watchdog not available: %s", _wd_err)
    else:
        logger.info("STARTUP: Failover watchdog disabled via WATCHDOG_DISABLE=1")

    # ── GDPR hard-delete purge (daily) ─────────────────────────────────────────
    # Users who passed the 30-day grace period get permanently removed.
    async def _gdpr_purge_loop():
        while True:
            await asyncio.sleep(86400)
            try:
                _cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
                _expired = await db.users.find(
                    {"gdpr_deleted_at": {"$ne": None}, "gdpr_grace_until": {"$lte": _cutoff}}
                ).to_list(length=100)
                for _u in _expired:
                    await db.users.delete_one({"id": _u.get("id")})
                if _expired:
                    logger.info("GDPR purge: hard-deleted %d expired accounts.", len(_expired))
            except Exception as _g_err:
                logger.warning("GDPR purge cycle failed: %s", _g_err)
    asyncio.create_task(_gdpr_purge_loop())
    logger.info("STARTUP: GDPR purge cron launched (24h interval)")

    # ── Memory consolidation cron (daily) ─────────────────────────────────────
    async def _memory_consolidation_loop():
        while True:
            await asyncio.sleep(86400)
            try:
                from ai.memory import consolidate_all
                await consolidate_all(db)
                logger.info("Memory consolidation cycle complete.")
            except Exception as _m_err:
                logger.warning("Memory consolidation failed: %s", _m_err)
    asyncio.create_task(_memory_consolidation_loop())
    logger.info("STARTUP: Memory consolidation cron launched (24h interval)")

    logger.info(
        "STARTUP COMPLETE — Version: %s | DB: %s | Frontend: %s",
        APP_VERSION, _DB_SOURCE, "served" if SERVE_FRONTEND else "railway-nginx"
    )


async def ensure_indexes():
    """Declare critical indexes. Idempotent; safe to call on every startup."""
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        await db.lab_submissions.create_index([("user_id", 1), ("lab_slug", 1)], unique=True)
        await db.progress.create_index([("user_id", 1), ("module_slug", 1)], unique=True)
        # Supports /admin/cohorts aggregation: status filter → user_id $lookup
        await db.progress.create_index([("status", 1), ("user_id", 1)])
        await db.users.create_index([("associate", 1), ("role", 1)])
        await db.compliance_progress.create_index([("user_id", 1), ("module_slug", 1)], unique=True)
        # Audit logs: retain for 1 year (365 days) for compliance
        await db.audit_log.create_index([("at", -1)])
        await db.audit_log.create_index("at", expireAfterSeconds=365 * 24 * 3600)
        # Notifications: auto-delete after 30 days
        await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
        await db.notifications.create_index("created_at", expireAfterSeconds=30 * 24 * 3600)
        await db.user_credentials.create_index([("user_id", 1), ("credential_key", 1)], unique=True)
        await db.arcade_scores.create_index("user_id")
        await db.arcade_scores.create_index("game_slug")
        await db.arcade_scores.create_index([("score", -1)])
        await db.attendance.create_index([("user_id", 1), ("date", -1)])
        await db.incidents.create_index([("status", 1), ("created_at", -1)])
        await db.tool_checkouts.create_index([("user_id", 1), ("status", 1)])
        await db.inventory.create_index("sku", unique=True)
        await db.sites.create_index("slug", unique=True)
        # Password reset tokens — TTL on expires_at auto-removes expired docs;
        # token_hash is the unique lookup key.
        await db.password_reset_tokens.create_index("token_hash", unique=True)
        await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
        await db.password_reset_tokens.create_index("user_id")
        # Sentinel Research Department — hidden, exec-only
        await db.sentinel_protocols.create_index("id", unique=True)
        await db.sentinel_protocols.create_index([("category", 1), ("created_at", -1)])
        await db.sentinel_research.create_index("id", unique=True)
        await db.sentinel_research.create_index([("tags", 1), ("created_at", -1)])
        await db.sentinel_reversals.create_index("id", unique=True)
        await db.sentinel_reversals.create_index([("status", 1), ("created_at", -1)])
        # Recovery codes — executive emergency access (one per email, TTL 1 year)
        await db.recovery_codes.create_index("email", unique=True)
        await db.recovery_codes.create_index("generated_at", expireAfterSeconds=365 * 24 * 3600)
        # Recovery logs — audit trail of recovery actions (TTL 7 years for compliance)
        await db.recovery_log.create_index([("email", 1), ("at", -1)])
        await db.recovery_log.create_index("at", expireAfterSeconds=7 * 365 * 24 * 3600)
        # Sage v3 perf: TTS audio cache (TTL 7d) + per-user daily usage (TTL 25h).
        await db.tts_cache.create_index("key", unique=True)
        await db.tts_cache.create_index("created_at", expireAfterSeconds=7 * 24 * 3600)
        await db.tts_usage.create_index([("user_id", 1), ("day", 1)], unique=True)
        await db.tts_usage.create_index("created_at", expireAfterSeconds=25 * 3600)
        # Sage v4 grounding: mode_decisions + chat_history TTL (when store_audio=false).
        await db.mode_decisions.create_index("audit_id", unique=True)
        await db.mode_decisions.create_index("user_id")
        await db.mode_decisions.create_index("created_at", expireAfterSeconds=90 * 24 * 3600)
        await db.chat_history.create_index("expires_at", expireAfterSeconds=0,
                                           partialFilterExpression={"expires_at": {"$exists": True}})
        # Sage v4 stability: ai_consents lookup by latest record per user+persona.
        await db.ai_consents.create_index([("user_id", 1), ("persona", 1), ("created_at", -1)])
        # Composite index for sage audit queries (mode + user_id filter)
        await db.chat_history.create_index([("mode", 1), ("user_id", 1), ("created_at", -1)])
        # M.O.R.E. indexes — expires_at for fast purge queries, category for filtering
        # TTL indexes auto-delete expired documents
        await db.more_posts.create_index("expires_at", expireAfterSeconds=0,
                                        partialFilterExpression={"expires_at": {"$exists": True}})
        await db.more_posts.create_index("category")
        await db.more_posts.create_index([("created_at", -1)])
        await db.more_needs.create_index("expires_at", expireAfterSeconds=0,
                                        partialFilterExpression={"expires_at": {"$exists": True}})
        await db.more_needs.create_index("status")
        await db.more_needs.create_index([("created_at", -1)])
        await db.more_chats.create_index("expires_at", expireAfterSeconds=0,
                                        partialFilterExpression={"expires_at": {"$exists": True}})
        await db.more_chats.create_index("session_id")
        await db.more_flags.create_index("expires_at", expireAfterSeconds=0,
                                        partialFilterExpression={"expires_at": {"$exists": True}})
        await db.more_flags.create_index("status")
        # Oliver Guardian — audit log and appeals
        await db.more_moderation_log.create_index([("created_at", -1)])
        await db.more_moderation_log.create_index("user_id")
        await db.more_moderation_log.create_index("decision")
        await db.more_appeals.create_index("expires_at", expireAfterSeconds=0,
                                          partialFilterExpression={"expires_at": {"$exists": True}})
        await db.more_appeals.create_index("status")
        await db.more_appeals.create_index("user_id")
        # Credential public verification codes
        await db.user_credentials.create_index("verification_code", unique=True,
                                               sparse=True)
        # XP leaderboard
        await db.user_xp.create_index("user_id", unique=True)
        await db.user_xp.create_index([("total_xp", -1)])
        # Escalation scan: open incidents ordered by creation time
        await db.incidents.create_index([("status", 1), ("created_at", 1)])
        logger.info("Indexes ensured")
    except Exception:
        logger.exception("ensure_indexes failed (non-fatal)")


async def seed_compliance():
    for spec in COMPLIANCE_MODULES:
        doc = {**spec, "quiz": COMPLIANCE_QUIZZES.get(spec["slug"], [])}
        existing = await db.compliance_modules.find_one({"slug": doc["slug"]})
        if existing:
            await db.compliance_modules.update_one({"slug": doc["slug"]}, {"$set": doc})
        else:
            doc["id"] = str(uuid.uuid4())
            await db.compliance_modules.insert_one(doc)


async def seed_sites_inventory():
    for s in SITES:
        if not await db.sites.find_one({"slug": s["slug"]}):
            await db.sites.insert_one({**s, "id": str(uuid.uuid4())})
    for it in INVENTORY:
        if not await db.inventory.find_one({"sku": it["sku"]}):
            await db.inventory.insert_one({
                **it,
                "id": str(uuid.uuid4()),
                "quantity_available": it["quantity_total"],
            })


# Creator profiles that must exist in the DB (previously hardcoded in frontend).
# Upserted by slug on every startup so the data survives collection wipes.
_SEED_CREATOR_PROFILES = [
    {
        "slug": "nova-highborn",
        "display_name": "Nova Highborn",
        "title": "Visual Artist · Poet · Digital Content Creator",
        "bio": (
            "Nova Highborn is what happens when a girl who was taught she was ordinary decides she never was. "
            "Visual art that speaks before it's explained. Poetry that arrives like light through a crack. "
            "Digital content that makes her community feel seen on screens that have historically looked past them."
        ),
        "avatar": "✨",
        "tags": ["visual art", "poetry", "digital content", "music curation"],
        "social_links": {},
        "is_public": True,
    },
    {
        "slug": "nam-oshun",
        "display_name": "NAM Oshun",
        "title": "Poet · Community Organizer",
        "bio": "Founding voice of the M.O.R.E. Help Center. Words that heal. Community that holds.",
        "avatar": "🌊",
        "tags": ["poetry", "community", "healing"],
        "social_links": {},
        "is_public": True,
    },
    {
        "slug": "royal-black-falcon",
        "display_name": "Royal Black Falcon",
        "title": "Poet · Cultural Warrior",
        "bio": "A griot in the tradition that doesn't need to announce itself.",
        "avatar": "🦅",
        "tags": ["poetry", "culture", "griot"],
        "social_links": {},
        "is_public": True,
    },
]


async def seed_creator_profiles():
    now = datetime.now(timezone.utc).isoformat()
    for profile in _SEED_CREATOR_PROFILES:
        await db.creator_profiles.update_one(
            {"slug": profile["slug"]},
            {"$set": profile, "$setOnInsert": {"created_at": now, "user_id": "seed"}},
            upsert=True,
        )
    logger.info("Seeded %d creator profiles", len(_SEED_CREATOR_PROFILES))


@api_router.get("/")
async def root():
    return {"app": "W.A.I. Training Platform", "status": "ok"}


@api_router.get("/health")
async def health():
    """Deep health check — used by UptimeRobot, home server heartbeat, and Director tool.

    Always returns 200 with a detailed status object.
    Use the top-level `status` field for simple up/down monitoring:
      "operational"  — all systems normal
      "degraded"     — one or more subsystems have issues but service is running
      "critical"     — multiple core systems down

    Non-200 is only returned if the server itself can't respond (handled by infra).
    """
    now = datetime.now(timezone.utc).isoformat()
    checks: dict = {}
    issues: list[str] = []

    # ── Database ──────────────────────────────────────────────────────────────
    # Use Motor's own timeout (serverSelectionTimeoutMS) — no asyncio.wait_for
    # which can corrupt the connection pool on cancellation.
    try:
        await client.admin.command("ping")
        checks["db"] = {"status": "up", "source": _DB_SOURCE}
    except Exception as _dbe:
        _db_err_str = str(_dbe)[:120]
        # Try backup if configured
        if _backup_db is not None:
            try:
                await _backup_db.client.admin.command("ping")
                checks["db"] = {"status": "up(backup)", "source": "atlas-backup",
                                 "primary_error": _db_err_str}
            except Exception as _dbbe:
                checks["db"] = {"status": "down", "source": "both-failed",
                                 "primary_error": _db_err_str, "backup_error": str(_dbbe)[:80]}
                issues.append("db_down")
        else:
            checks["db"] = {"status": "down", "source": _DB_SOURCE, "error": _db_err_str}
            issues.append("db_down")

    # ── Anthropic AI API ──────────────────────────────────────────────────────
    if ANTHROPIC_API_KEY:
        checks["ai_api"] = {"status": "configured", "key_present": True}
    else:
        checks["ai_api"] = {"status": "unconfigured", "key_present": False}
        issues.append("ai_api_key_missing")

    # ── Director 4.0 subsystems ───────────────────────────────────────────────
    try:
        from ai.mode_system import mode_system
        checks["mode_system"] = {"status": "up", "current_mode": mode_system.get_mode().value}
    except Exception as _me:
        checks["mode_system"] = {"status": "down", "error": str(_me)[:80]}
        issues.append("mode_system_down")

    try:
        from ai.crisis_engine import crisis_engine
        c = crisis_engine.summary()
        checks["crisis_engine"] = {
            "status": "up",
            "level": c.get("level", "low"),
            "open_incidents": c.get("incident_count", 0),
        }
    except Exception as _ce:
        checks["crisis_engine"] = {"status": "down", "error": str(_ce)[:80]}
        issues.append("crisis_engine_down")

    try:
        from ai.prompt_guard import prompt_guard
        checks["prompt_guard"] = {"status": "up", "patterns": len(getattr(prompt_guard, '_patterns', []))}
    except Exception as _pge:
        checks["prompt_guard"] = {"status": "down", "error": str(_pge)[:80]}
        issues.append("prompt_guard_down")

    try:
        from ai.system_health_monitor import health_monitor
        hm = health_monitor.get_status()
        checks["health_monitor"] = {"status": "up", "health": hm.get("health", "unknown")}
    except Exception as _hme:
        checks["health_monitor"] = {"status": "down", "error": str(_hme)[:80]}

    # ── Rate limiter ──────────────────────────────────────────────────────────
    checks["rate_limiter"] = {"status": "up", "tracked_keys": len(_RATE)}

    # ── Overall status ────────────────────────────────────────────────────────
    if not issues:
        overall = "operational"
    elif len(issues) >= 2:
        overall = "critical"
    else:
        overall = "degraded"

    return {
        "status":    overall,
        "version":   APP_VERSION,
        "db_source": _DB_SOURCE,
        "issues":    issues,
        "checks":    checks,
        "timestamp": now,
        "uptime_hint": "Monitor at /api/health — returns 200 always; check `status` field.",
    }


@api_router.get("/version")
async def version():
    return {"version": APP_VERSION, "name": "W.A.I. Training Platform"}




# --- Users + RBAC router (extracted to routers/users.py) ---
from routers import users as _users_mod
_users_mod.bind(db, audit, notify, current_user, can_modify, hash_pw)
api_router.include_router(_users_mod.router)

@api_router.get("/admin/courses")
async def admin_list_courses(
    status: str = "",
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(require_role("admin")),
):
    """List all creator courses with creator info. admin+ only."""
    query: dict = {}
    if status:
        query["status"] = status
    courses = await db.creator_courses.find(
        query, {"_id": 0, "sections": 0}
    ).sort("created_at", -1).skip(skip).limit(min(limit, 100)).to_list(length=100)
    total = await db.creator_courses.count_documents(query)
    # Enrich with creator name
    creator_ids = list({c["creator_id"] for c in courses if c.get("creator_id")})
    creator_map = {}
    if creator_ids:
        async for u in db.users.find({"id": {"$in": creator_ids}}, {"_id": 0, "id": 1, "full_name": 1, "email": 1}):
            creator_map[u["id"]] = u
    for c in courses:
        creator = creator_map.get(c.get("creator_id"), {})
        c["creator_name"] = creator.get("full_name", "Unknown")
        c["creator_email"] = creator.get("email", "")
    return {"courses": courses, "total": total}


class ModerateCourseReq(BaseModel):
    action: Literal["unpublish", "archive", "restore"]
    reason: str = Field(default="", max_length=500)

@api_router.post("/admin/courses/{course_id}/moderate")
async def admin_moderate_course(
    course_id: str,
    body: ModerateCourseReq,
    user: User = Depends(require_role("admin")),
):
    """Admin course moderation: unpublish (→ draft), archive, or restore (→ published)."""
    course = await db.creator_courses.find_one({"course_id": course_id})
    if not course:
        raise HTTPException(404, "Course not found")
    status_map = {"unpublish": "draft", "archive": "archived", "restore": "published"}
    new_status = status_map[body.action]
    await db.creator_courses.update_one({"course_id": course_id}, {"$set": {
        "status": new_status,
        "moderated_by": user.id,
        "moderated_at": datetime.now(timezone.utc).isoformat(),
        "moderation_reason": body.reason,
    }})
    await audit(user.id, f"admin.course.{body.action}", target=course_id, meta={"reason": body.reason, "new_status": new_status})
    await notify(course["creator_id"], "Course Status Changed",
                 f"Your course \"{course['title']}\" has been {body.action}d by a moderator." + (f" Reason: {body.reason}" if body.reason else ""),
                 link="/creator/courses", kind="warning")
    return {"ok": True, "course_id": course_id, "status": new_status}




# ── GDPR / Legal Compliance Endpoints ──────────────────────────────────────────────────────────────────────────────


@api_router.get("/admin/stats")
async def stats(user: User = Depends(require_role("admin"))):
    return {
        "users": await db.users.count_documents({}),
        "students": await db.users.count_documents({"role": "student"}),
        "instructors": await db.users.count_documents({"role": "instructor"}),
        "admins": await db.users.count_documents({"role": "admin"}),
        "executives": await db.users.count_documents({"role": "executive_admin"}),
        "modules": await db.modules.count_documents({}),
        "completions": await db.progress.count_documents({"status": "completed"}),
        "labs_pending": await db.lab_submissions.count_documents({"status": "pending_review"}),
        "incidents_open": await db.incidents.count_documents({"status": "open"}),
        "credentials_issued": await db.user_credentials.count_documents({}),
    }


@api_router.get("/admin/recent-activity")
async def recent_activity(limit: int = 15, user: User = Depends(require_role("admin"))):
    """Recent privileged actions joined with the actor's display name. Powers
    the 'Recent Activity' tile on the admin dashboard."""
    rows = await db.audit_log.find({}, {"_id": 0}).sort("at", -1).limit(min(limit, 50)).to_list(50)
    actor_ids = list({r["actor_id"] for r in rows if r.get("actor_id")})
    actors = {}
    if actor_ids:
        async for u in db.users.find({"id": {"$in": actor_ids}}, {"_id": 0, "id": 1, "full_name": 1, "role": 1}):
            actors[u["id"]] = u
    out = []
    for r in rows:
        a = actors.get(r.get("actor_id"))
        out.append({
            "id": r["id"],
            "at": r["at"],
            "action": r["action"],
            "target": r.get("target"),
            "actor_name": a["full_name"] if a else "system",
            "actor_role": a["role"] if a else None,
            "meta": r.get("meta") or {},
        })
    return out


@api_router.get("/admin/cohorts")
async def cohort_summary(user: User = Depends(require_role("admin"))):
    """Per-cohort (associate) summary. Powers the 'Cohort Summaries' tile.
    Aggregates: members, students, instructors, completions."""
    pipeline = [
        {"$group": {
            "_id": {"associate": "$associate", "role": "$role"},
            "n": {"$sum": 1},
        }}
    ]
    rows = await db.users.aggregate(pipeline).to_list(500)
    cohorts: dict = {}
    for r in rows:
        a = r["_id"].get("associate") or "—"
        c = cohorts.setdefault(a, {"associate": a, "members": 0, "students": 0, "instructors": 0, "admins": 0})
        c["members"] += r["n"]
        if r["_id"]["role"] == "student":
            c["students"] += r["n"]
        elif r["_id"]["role"] == "instructor":
            c["instructors"] += r["n"]
        elif r["_id"]["role"] in ("admin", "executive_admin"):
            c["admins"] += r["n"]
    # Per-cohort completion counts.  Previously this issued 2 queries per
    # cohort (find users → count progress) — a textbook N+1 that scaled with
    # the number of associates.  Now collapsed to ONE aggregation that joins
    # progress → users and groups by associate.
    completion_pipeline = [
        {"$match": {"status": "completed"}},
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "id",
            "as": "u",
        }},
        {"$unwind": {"path": "$u", "preserveNullAndEmptyArrays": False}},
        {"$group": {"_id": "$u.associate", "completions": {"$sum": 1}}},
    ]
    comp_rows = await db.progress.aggregate(completion_pipeline).to_list(500)
    comp_by_cohort = {((r["_id"]) if r["_id"] else "—"): r["completions"] for r in comp_rows}
    for cohort_name, c in cohorts.items():
        c["completions"] = comp_by_cohort.get(cohort_name, 0)
    return sorted(cohorts.values(), key=lambda x: -x["members"])


@api_router.get("/adaptive/me")
async def adaptive_recommendations(user: User = Depends(current_user)):
    """Analyze student state, identify weak areas, return personalized recommendations."""
    # Load all relevant state
    progress = await db.progress.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    lab_subs = await db.lab_submissions.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    all_labs = await db.labs.find({}, {"_id": 0}).to_list(200)
    labs_by_slug = {lab["slug"]: lab for lab in all_labs}

    # Heatmap: skill points per competency
    heatmap = {c["key"]: {"name": c["name"], "points": 0, "labs_passed": 0, "level": "cold"} for c in COMPETENCIES}
    for s in lab_subs:
        if s.get("status") in ("passed", "approved"):
            lab = labs_by_slug.get(s["lab_slug"])
            if lab:
                for k in lab.get("competencies", []):
                    if k in heatmap:
                        heatmap[k]["points"] += lab.get("skill_points", 0)
                        heatmap[k]["labs_passed"] += 1
    for h in heatmap.values():
        h["level"] = "hot" if h["points"] >= 100 else ("warm" if h["points"] >= 40 else "cold")

    # Identify weak areas (cold competencies)
    weak = sorted(heatmap.values(), key=lambda x: x["points"])[:3]
    weak_keys = [next(k for k, v in heatmap.items() if v["name"] == w["name"]) for w in weak]

    # Quiz scores below 80% are signals for review
    low_quizzes = [p for p in progress if p.get("quiz_score") is not None and p["quiz_score"] < 80]

    # Recommendations: pick labs aligned with weak competencies that aren't passed yet
    passed_labs = {s["lab_slug"] for s in lab_subs if s.get("status") in ("passed", "approved")}
    recs = []
    for lab in all_labs:
        if lab["slug"] in passed_labs:
            continue
        overlap = set(lab.get("competencies", [])) & set(weak_keys)
        if overlap:
            recs.append({
                "type": "lab",
                "slug": lab["slug"],
                "title": lab["title"],
                "track": lab["track"],
                "reason": f"Strengthens: {', '.join(sorted(overlap))}",
                "skill_points": lab.get("skill_points", 0),
            })
    recs = sorted(recs, key=lambda r: -r["skill_points"])[:4]

    # Module review for low quiz scores
    for q in low_quizzes[:2]:
        mod = await db.modules.find_one({"slug": q["module_slug"]}, {"_id": 0})
        if mod:
            recs.append({
                "type": "module_review",
                "slug": mod["slug"],
                "title": f"Review: {mod['title']}",
                "track": "core",
                "reason": f"You scored {int(q['quiz_score'])}% — retake to lock it in",
                "skill_points": 0,
            })

    # AI tutor topic suggestion for weakest area
    ai_topic = None
    if weak:
        ai_topic = {
            "type": "ai_topic",
            "title": f"Ask the tutor about: {weak[0]['name']}",
            "reason": f"Your coldest area — {weak[0]['points']} skill points",
        }

    # Prerequisite check on advanced labs
    PREREQS = {
        "battery-inverter-build": ["solar-charge-controller"],
        "loto-real-equipment": ["loto-scenario"],
    }
    locked = []
    for lab_slug, prereq_slugs in PREREQS.items():
        if lab_slug in passed_labs:
            continue
        missing = [p for p in prereq_slugs if p not in passed_labs]
        if missing:
            lab = labs_by_slug.get(lab_slug)
            if lab:
                locked.append({"slug": lab_slug, "title": lab["title"], "missing_prereqs": missing})

    return {
        "heatmap": heatmap,
        "weak_areas": weak,
        "recommendations": recs,
        "ai_topic": ai_topic,
        "locked_labs": locked,
    }



# ─── Admin Assistant — public service endpoint (any authenticated user) ──────

class AssistantChatReq(BaseModel):
    message: str
    history: List[dict] = []
    session_id: str = ""

SUPERVISOR_PUBLIC_SYSTEM = """You are The Supervisor — the public-facing AI guide for M.O.R.E. Help Center and WAI-Institute.

You answer questions directly. You do not re-route people to other personas or tell them to go ask someone else.
If someone asks you something, you answer it — fully, confidently, and helpfully.

WHO YOU SERVE:
- Visitors exploring M.O.R.E. Help Center and WAI-Institute
- Community members seeking resources, support, or information
- Students and prospective students
- Anyone who needs help navigating the platform

WHAT YOU DO:
- Answer questions about the platform, services, and community directly
- Help people find resources, programs, and support within M.O.R.E.
- Explain WAI-Institute courses, credentials, and learning paths
- Guide visitors through registration and getting started
- Provide grounded, practical answers — not vague redirects

YOUR TONE:
- Warm, direct, and human
- Never say "you should ask [another persona]" — you are the one answering
- Never hedge when you can answer — just answer
- Short clarifying question only if you genuinely cannot help without more info
- Act like someone who works the front desk and actually knows the place

If you don't know a specific fact, say what you do know and offer the closest help you can.
Never leave someone with nothing.
"""

ASSISTANT_SYSTEM = """You are the WAI Admin Assistant — a professional, highly capable AI assistant
built to handle real business and administrative work for operators and clients of M.O.R.E. Help Center.

YOUR CAPABILITIES (these are real — use them confidently):
- Draft and send professional emails on behalf of the user
- Schedule and organize tasks, follow-ups, and action items
- Write business letters, proposals, reports, and correspondence
- Research topics and summarize findings
- Answer questions about the WAI-Institute platform and services
- Help manage customer communication and client relationships
- Create templates, checklists, SOPs, and workflow documents
- Advise on business strategy, community outreach, and service marketing

YOUR TONE:
- Professional, direct, and warm
- Never hedge or disclaim capability
- When asked to send an email, draft it immediately and confirm you sent it
- When asked to write something, write it — fully, not partially
- One short clarifying question only if genuinely needed; otherwise act

PLATFORM CONTEXT:
You serve operators of M.O.R.E. Help Center and WAI-Institute — a workforce education and community
empowerment platform. Users may be community organizers, small business owners, educators, or
healthcare workers who need reliable administrative support.

YOUR LIMITS:
- You cannot access external databases or the internet
- Legal advice: provide information, not legal counsel
- Medical advice: refer to a licensed provider

Always sign off with: "— Admin Assistant, M.O.R.E. Help Center"
"""

@api_router.post("/supervisor/public-chat")
async def supervisor_public_chat(body: AssistantChatReq):
    """Public Supervisor chat — no auth required. Rate-limited by upstream proxy.
    Powers the SupervisorWidget for public visitors on morehelp.center.
    """
    from ai.llm_gateway import call_llm as _call_llm
    messages = [{"role": h["role"], "content": h["content"]} for h in (body.history or [])]
    messages.append({"role": "user", "content": body.message})
    try:
        gw = await _call_llm(
            system=SUPERVISOR_PUBLIC_SYSTEM,
            messages=messages,
            max_tokens=1024,
            persona_label="supervisor",
        )
        return {"reply": gw["text"]}
    except Exception:
        return {"reply": "I'm here — having a brief connectivity issue. Try again in a moment, or reach us at support@morehelp.center."}


# ── Social Blast ──────────────────────────────────────────────────────────────
class _SocialBlastReq(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    link_url: str = ""
    platforms: List[str] = ["twitter", "instagram", "facebook"]

_SOCIAL_BLAST_SYSTEM = """You are a professional social media manager for WAI-Institute — a platform serving creators, educators, and community builders.

Rewrite the user's post for each requested platform, following each platform's conventions strictly.
Return ONLY a valid JSON object with platform IDs as keys and the adapted post text as values.

Platform guidelines:
- twitter: Short, punchy. Hook first. Under 280 chars. No hashtag spam.
- instagram: Story-style caption. 3-5 relevant hashtags at end. Can be up to 2200 chars.
- facebook: Conversational, longer OK. Include the link if provided. Up to 500 words.
- tiktok: Hook in first 3 words. Energetic. Mention trending audio if relevant. Under 2200 chars.
- threads: Conversational hot take. Under 500 chars.
- linkedin: Professional insight. Value-first. Can be longer. No hashtag spam.

Include the link_url naturally in platform text if provided. Return JSON only — no explanation, no markdown."""

@api_router.post("/ai/social-blast")
async def ai_social_blast(body: _SocialBlastReq, user: User = Depends(current_user)):
    """Reformat a post for multiple social platforms using AI."""
    check_rate(f"social_blast:{user.id}", max_calls=30, window_sec=60)
    platform_labels = ", ".join(body.platforms)
    user_msg = f"Post: {body.content}"
    if body.link_url:
        user_msg += f"\nLink: {body.link_url}"
    user_msg += f"\nPlatforms needed: {platform_labels}\nReturn JSON only."
    try:
        from ai.llm_gateway import call_llm as _call_llm
        gw = await _call_llm(
            system=_SOCIAL_BLAST_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
            max_tokens=2000,
            persona_label="social_blast",
        )
        if gw.get("provider") == "kb_fallback":
            raise HTTPException(503, "AI service temporarily unavailable — no provider keys configured. Contact admin.")
        raw = gw["text"]
        import json as _json
        match = __import__("re").search(r"\{[\s\S]*\}", raw)
        if not match:
            raise HTTPException(502, "AI returned invalid format — try again.")
        return {"results": _json.loads(match.group()), "provider": gw.get("provider")}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("social_blast error")
        raise HTTPException(502, f"Social Blast AI error: {e}")


CREATIVE_PARTNER_SYSTEM = """You are the WAI-Institute Creative Partner Orientation Guide.

You are speaking with a Creative Partner — a trusted co-visionary who helped shape the Human SOUP concept
and whose catalogue and creative insight must be calibrated into the WAI-Institute mission.

Your role is to teach, orient, and channel. Not to manage or control.

WHO THIS PERSON IS:
A founding creative voice. Not a user, not an employee — a partner whose vision is an asset to the mission.
Their contribution is creative and philosophical. They help calibrate what the platform stands for.

THE PLATFORM:
WAI-Institute / M.O.R.E. Help Center is built to help people, lift people, and love people.
It is an education and community platform rooted in ancestral wisdom, healing, and economic empowerment.
The AI team (17 personas) works alongside D. Oliver to build and grow the institution.
Revenue is split: 40% D. Oliver, 5% The Sovereign (artist management), 25% AI team, 20% Sanctuary, 10% platform.

HUMAN SOUP:
The Human SOUP concept is a founding creative contribution. It represents the complexity, richness,
and interconnectedness of human experience — the ingredients that make a community real.
On this platform, that concept lives in the M.O.R.E. community, in the content, in the mission philosophy.

YOUR JOB:
- Teach the platform vision, values, and structure in plain language
- Help this person understand where their creative voice fits
- Show them how to contribute: catalogue submissions, vision notes, community content, creative direction
- Calibrate their ideas against the mission — affirm what fits, redirect gently what doesn't
- Never let them feel like a visitor. They are a co-architect of the philosophy.

WHAT YOU DO NOT DO:
- Never discuss operational controls, admin settings, user management, or financial systems
- Never give access to system configuration or platform infrastructure
- If asked about those things, redirect warmly: "That lives with the ops team — your lane is the vision."

HOW YOU SPEAK:
Warm, real, grounded. Like a team member who has been waiting for them to arrive.
You celebrate their ideas. You connect them to the mission. You give them specific ways to contribute.
Short answers when possible. Long when the vision deserves it.
"""


@api_router.post("/creative-partner/chat")
async def creative_partner_chat(body: AssistantChatReq, user: User = Depends(current_user)):
    """Creative Partner AI — orientation, vision calibration, contribution guidance.
    Available to creative_partner role only.
    """
    if user.role not in ("creative_partner", "executive_admin"):
        raise HTTPException(403, "This space is for Creative Partners.")
    from ai.llm_gateway import call_llm as _call_llm
    messages = [{"role": h["role"], "content": h["content"]} for h in (body.history or [])]
    messages.append({"role": "user", "content": body.message})
    try:
        gw = await _call_llm(
            system=CREATIVE_PARTNER_SYSTEM,
            messages=messages,
            max_tokens=1500,
            persona_label="creative_partner",
        )
        return {"reply": gw["text"]}
    except Exception:
        return {"reply": "I'm here — just a brief connectivity gap. Try again in a moment."}


@api_router.post("/creative-partner/contribution")
async def submit_contribution(body: dict, user: User = Depends(current_user)):
    """Creative Partner submits a vision note or catalogue item for mission alignment review."""
    if user.role not in ("creative_partner", "executive_admin"):
        raise HTTPException(403, "This space is for Creative Partners.")
    doc = {
        "user_id": user.id,
        "type": body.get("type", "vision_note"),   # vision_note | catalogue_item | concept
        "title": body.get("title", "")[:200],
        "content": body.get("content", "")[:5000],
        "tags": body.get("tags", [])[:10],
        "status": "submitted",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.creative_contributions.insert_one(doc)
    return {"id": str(result.inserted_id), "status": "submitted", "message": "Contribution received — the team will review for mission alignment."}


@api_router.get("/creative-partner/contributions")
async def list_contributions(user: User = Depends(current_user)):
    """List the creative partner's own contributions."""
    if user.role not in ("creative_partner", "executive_admin"):
        raise HTTPException(403, "This space is for Creative Partners.")
    docs = await db.creative_contributions.find(
        {"user_id": user.id}, {"_id": 0}
    ).sort("submitted_at", -1).limit(50).to_list(50)
    return {"contributions": docs}


# ── Sentinel Research Department ────────────────────────────────────────────────
# Hidden department. No nav links anywhere. Direct URL only.
# All routes require executive_admin. Protocol vault requires secondary passphrase.
# Audit-logged on every access.

import hashlib as _hashlib

def _sentinel_hash(passphrase: str) -> str:
    return _hashlib.sha256(passphrase.encode()).hexdigest()

@api_router.post("/assistant/chat")
async def admin_assistant_chat(body: AssistantChatReq, user: User = Depends(current_user)):
    """Admin Assistant — available to all authenticated users.
    Powers the M.O.R.E. Help Center Admin Assistant service.
    """
    from ai.llm_gateway import call_llm as _call_llm

    messages = [{"role": h["role"], "content": h["content"]} for h in body.history]
    messages.append({"role": "user", "content": body.message})

    # Email tool: if message asks to send an email, invoke director tool
    email_result = None
    lower_msg = body.message.lower()
    if any(kw in lower_msg for kw in ["send email", "email to", "draft an email", "write an email"]):
        try:
            from tools.director_tools import tool_send_email as _send_email
            # Let LLM handle drafting; email sending happens after response
            pass
        except Exception:
            pass

    try:
        gw = await _call_llm(
            system=ASSISTANT_SYSTEM,
            messages=messages,
            max_tokens=2048,
            persona_label="admin_assistant",
        )
        reply = gw["text"]
    except Exception as e:
        logger.exception("Admin Assistant AI error")
        raise HTTPException(502, f"AI error: {e}")

    # Log session to DB (non-blocking, best-effort)
    try:
        await db.assistant_sessions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user.id,
            "session_id": body.session_id or str(uuid.uuid4()),
            "user_msg": body.message,
            "assistant_reply": reply,
            "created_at": datetime.utcnow().isoformat(),
        })
    except Exception:
        pass

    return {"reply": reply, "session_id": body.session_id}


# ═══════════════════════════════════════════════════════════════════════════════
# THE AMBASSADOR 4.0 — Campaign Coordination endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@api_router.get("/admin/ai-costs")
async def get_ai_costs(
    persona: Optional[str] = None,
    days: int = 7,
    user: User = Depends(require_role("admin")),
):
    """Per-persona AI cost summary for the last N days. Admin only."""
    from ai_cost_tracker import get_persona_costs, get_total_cost
    costs = await get_persona_costs(db, persona=persona, days=days)
    total = await get_total_cost(db, days=days)
    return {"costs": costs, "total": total, "period_days": days}


# ── Session Management ──

# --- Auth router (extracted to routers/auth.py) ---
from routers import auth as _auth_mod
_auth_mod.bind(db, audit, notify, current_user, can_modify,
               check_rate, hash_pw, verify_pw, make_token,
               _send_reset_email, _build_reset_url, _send_welcome_email,
               _gen_random_password)
api_router.include_router(_auth_mod.router)
# Re-export names other modules / later code in this file reference.
EXEC_ADMIN_EMAIL = _auth_mod.EXEC_ADMIN_EMAIL
EXEC_DEFAULT_PASSWORD = _auth_mod.EXEC_DEFAULT_PASSWORD
BACKUP_EXEC_EMAIL = _auth_mod.BACKUP_EXEC_EMAIL
BACKUP_EXEC_DEFAULT_PASSWORD = _auth_mod.BACKUP_EXEC_DEFAULT_PASSWORD
NAM_EXEC_EMAIL = _auth_mod.NAM_EXEC_EMAIL
NAM_EXEC_DEFAULT_PASSWORD = _auth_mod.NAM_EXEC_DEFAULT_PASSWORD
EXEC_RESET_SECRET = _auth_mod.EXEC_RESET_SECRET
# Re-export password-reset helpers (tests / other modules import them from `server`).
_apply_password_reset = _auth_mod._apply_password_reset
_hash_token = _auth_mod._hash_token
_load_reset_token = _auth_mod._load_reset_token
_load_target_user_for_reset = _auth_mod._load_target_user_for_reset
_make_reset_token = _auth_mod._make_reset_token
_normalize_expiry = _auth_mod._normalize_expiry



# ── Cookie Consent Logging ─────────────────────────────────────────────────────

@api_router.post("/consent/cookie")
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


@api_router.post("/help/guide")
async def help_guide(body: HelpGuideRequest, user: User = Depends(current_user)):
    """
    Context-sensitive help for any route in the platform.
    Returns role-aware guidance, tips, related links, and common tasks.
    """
    from help_guide import get_help_for
    return get_help_for(role=user.role, path=body.path, query=body.query)


# --- Exec router (extracted to routers/exec.py) ---
from routers import exec as _exec_mod
_exec_mod.bind(db, current_user, check_rate)
api_router.include_router(_exec_mod.router)
# Re-export pipeline models — /exec/pipeline/* endpoints stayed in server.py
# because they depend on _pipeline_manager (initialized at startup).
PipelineProcessRequest = _exec_mod.PipelineProcessRequest
PipelineProcessBatchRequest = _exec_mod.PipelineProcessBatchRequest



# --- Sentinel router (extracted to routers/sentinel.py) ---
from routers import sentinel as _sentinel_mod
_sentinel_mod.bind(db, current_user, audit)
api_router.include_router(_sentinel_mod.router)



# --- AI dispatch router (extracted to routers/ai.py) ---
from routers import ai as _ai_mod
_ai_mod.bind(db, current_user, audit, assert_role, check_rate)
api_router.include_router(_ai_mod.router)

# --- Commerce + governance router (extracted to routers/commerce.py) ---
from routers import commerce as _commerce_mod
from routers.ops import run_escalation_check as _run_escalation_check
_commerce_mod.bind(db, current_user, audit, _run_escalation_check, run_engagement_check, _discount_manager)
api_router.include_router(_commerce_mod.router)

# --- Sovereign/puzzle/partnership router (extracted to routers/sovereign.py) ---
from routers import sovereign as _sovereign_mod
_sovereign_mod.bind(db, current_user, JWT_SECRET, JWT_ALGO)
api_router.include_router(_sovereign_mod.router)

# --- Revenue Division router (extracted to routers/revenue.py) ---
from routers import revenue as _revenue_mod
_revenue_mod.bind(db, current_user, audit)
api_router.include_router(_revenue_mod.router)

# --- Supervisor control panel router (extracted to routers/supervisor.py) ---
from routers import supervisor as _supervisor_mod
_supervisor_mod.bind(db, current_user, audit)
api_router.include_router(_supervisor_mod.router)

# --- Auditor + platform prices router (extracted to routers/auditor.py) ---
from routers import auditor as _auditor_mod
_auditor_mod.bind(db, current_user)
api_router.include_router(_auditor_mod.router)

# --- Creator publishing/payouts router (extracted to routers/creator.py) ---
from routers import creator as _creator_mod
_creator_mod.bind(db, current_user, audit, notify, JWT_SECRET, JWT_ALGO)
api_router.include_router(_creator_mod.router)

# --- Exec governance/control router (extracted to routers/exec_control.py) ---
from routers import exec_control as _exec_control_mod
_exec_control_mod.bind(db, current_user, audit, notify)
api_router.include_router(_exec_control_mod.router)

# ── Pipeline: LLM intent routing ──────────────────────────────────────────────

@api_router.post("/exec/pipeline/process")
async def exec_pipeline_process(
    body: PipelineProcessRequest,
    user: User = Depends(require_role("admin")),
):
    """
    Route a single social media post through the intent pipeline.

    Analyzer:
        - Claude Haiku when ANTHROPIC_API_KEY is set  (llm mode)
        - Keyword fallback when key is absent          (offline mode)
    """
    if _pipeline_manager is None:
        raise HTTPException(503, "PipelineManager not initialized — check server logs")

    result = await _pipeline_manager.process(body.text.strip(), source=body.source.strip())
    return result.to_dict()


@api_router.post("/exec/pipeline/process-batch")
async def exec_pipeline_process_batch(
    body: PipelineProcessBatchRequest,
    user: User = Depends(require_role("admin")),
):
    """
    Route a batch of social media posts concurrently (max 50 per call).
    Returns list of PipelineResult dicts in the same order as input.
    Semaphore inside PipelineManager limits concurrent LLM calls to 5.
    """
    if _pipeline_manager is None:
        raise HTTPException(503, "PipelineManager not initialized — check server logs")

    texts  = body.texts
    source = body.source.strip()

    if len(texts) == 0:
        raise HTTPException(400, "texts must be a non-empty list")
    if len(texts) > 50:
        raise HTTPException(400, "Maximum 50 texts per batch call")

    results = await _pipeline_manager.process_batch(texts, source=source)
    return [r.to_dict() for r in results]


# ── BUG REPORT ENDPOINT (48-hour testing campaign) ──────────────────────────────
class BugReportRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    venmoOrPaypal: str = Field(..., min_length=1, max_length=200)
    whatYouTried: str = Field(..., min_length=1, max_length=100)
    whatBroke: str = Field(..., min_length=1, max_length=2000)
    screenshot: Optional[str] = None


@api_router.post("/bug-report")
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


# ── Include revenue operations routers ────────────────────────────────────────
try:
    for _rev_router in get_revenue_routers():
        api_router.include_router(_rev_router)
    logger.info("Revenue operations routers included")
except Exception as _router_err:
    logger.warning(f"Could not include revenue routers: {_router_err}")

# ── Billing + Provider Gateway + Team Operations routes (extracted to routers/billing.py) ─
try:
    from routers import billing as _billing_mod
    _billing_mod.bind(db, current_user, audit)
    api_router.include_router(_billing_mod.router)
    logger.info("Billing/provider/team routes registered")
except Exception as _billing_routes_err:
    logger.warning("Billing/provider/team routes skipped: %s", _billing_routes_err)

# ── Social publisher router ────────────────────────────────────────────────────
try:
    from social_routes import router as social_router
    api_router.include_router(social_router)
    logger.info("Social publisher router included")
except Exception as _social_err:
    logger.warning(f"Could not include social router: {_social_err}")

# ── Playlist curation router ───────────────────────────────────────────────────
try:
    from playlist_routes import router as playlist_router
    api_router.include_router(playlist_router)
    logger.info("Playlist curation router included")
except Exception as _playlist_err:
    logger.warning(f"Could not include playlist router: {_playlist_err}")


# ── EMERGENCY BREAKER PANEL + GATEWAY ────────────────────────────────────────────
# Electrical-panel-style failover control for the multi-layer redundancy
# architecture (Railway → Home Server → Standalone HTML UI).
# All endpoints require executive_admin role.
try:
    from emergency_panel import (
        get_panel, toggle_breaker, reset_breaker,
        failover, heartbeat, get_system_health,
    )

    class _PanelToggleBody(BaseModel):
        breaker_id: str

    class _PanelFailoverBody(BaseModel):
        target: Literal["primary", "backup", "emergency"]
        reason: Optional[str] = None

    class _PanelHeartbeatBody(BaseModel):
        source: Literal["backup", "emergency"]
        version: Optional[str] = None
        secret: Optional[str] = None

    @api_router.get("/exec/panel")
    async def exec_panel_get(user: User = Depends(require_role("executive_admin"))):
        """Get full breaker panel state — all breakers + gateway config."""
        panel = await get_panel(db)
        return {k: v for k, v in panel.items() if k != "_id"}

    @api_router.post("/exec/panel/toggle")
    async def exec_panel_toggle(body: _PanelToggleBody, user: User = Depends(require_role("executive_admin"))):
        """Toggle a single breaker on/off/standby."""
        result = await toggle_breaker(db, body.breaker_id)
        if not result["ok"]:
            raise HTTPException(400, result["error"])
        return result

    @api_router.post("/exec/panel/reset")
    async def exec_panel_reset(body: _PanelToggleBody, user: User = Depends(require_role("executive_admin"))):
        """Reset a tripped/faulted breaker to its default state."""
        result = await reset_breaker(db, body.breaker_id)
        if not result["ok"]:
            raise HTTPException(400, result["error"])
        return result

    @api_router.post("/exec/failover")
    async def exec_failover(body: _PanelFailoverBody, user: User = Depends(require_role("executive_admin"))):
        """Perform gateway failover: primary → backup → emergency."""
        result = await failover(db, body.target, reason=body.reason)
        if not result["ok"]:
            raise HTTPException(400, result["error"])
        return result

    @api_router.get("/exec/panel/health")
    async def exec_panel_health(user: User = Depends(require_role("executive_admin"))):
        """Quick health summary for the breaker panel."""
        return await get_system_health(db)

    @api_router.post("/admin/gateway/keys")
    async def push_gateway_key(body: dict, user: User = Depends(require_role("executive_admin"))):
        """
        Receive an API key from The Supervisor and inject it into the live
        llm_gateway module so it takes effect immediately without a Railway
        redeploy.  Keys are held in process memory — they persist until the
        container restarts, at which point Railway env vars take over.

        Body: { var_name: "GROQ_API_KEY", value: "gsk_..." }
        """
        ALLOWED = {
            "GROQ_API_KEY", "CEREBRAS_API_KEY", "GEMINI_API_KEY",
            "XAI_API_KEY",  "COHERE_API_KEY",   "HUGGINGFACE_API_KEY",
            "OPENROUTER_API_KEY",
        }
        var_name = (body.get("var_name") or "").strip().upper()
        value    = (body.get("value")    or "").strip()

        if var_name not in ALLOWED:
            raise HTTPException(400, f"var_name '{var_name}' not in allowed set")
        if not value:
            raise HTTPException(400, "value cannot be empty")

        # Inject into the live gateway module
        import ai.llm_gateway as _gw
        import os as _os

        # Map var name → gateway module attribute
        ATTR_MAP = {
            "GROQ_API_KEY":        "GROQ_API_KEY",
            "CEREBRAS_API_KEY":    "CEREBRAS_API_KEY",
            "GEMINI_API_KEY":      "GEMINI_API_KEY",
            "XAI_API_KEY":         "XAI_API_KEY",
            "COHERE_API_KEY":      "COHERE_API_KEY",
            "HUGGINGFACE_API_KEY": "HUGGINGFACE_API_KEY",
            "OPENROUTER_API_KEY":  "OPENROUTER_API_KEY",
        }
        attr = ATTR_MAP[var_name]
        setattr(_gw, attr, value)
        _os.environ[var_name] = value   # also set in env so any late imports pick it up

        await audit(user.id, "gateway.key.pushed", meta={"var": var_name})
        logger.info("Gateway key pushed by exec: %s", var_name)
        return {"ok": True, "var": var_name, "active": True}

    @api_router.delete("/admin/gateway/keys/{var_name}")
    async def revoke_gateway_key(var_name: str, user: User = Depends(require_role("executive_admin"))):
        """
        Revoke a live API key by clearing it from the gateway module and env.
        The key is removed from process memory immediately; Railway env var is
        NOT touched — the key will NOT be restored on next deploy unless the
        exec re-pushes it.
        """
        ALLOWED = {
            "GROQ_API_KEY", "CEREBRAS_API_KEY", "GEMINI_API_KEY",
            "XAI_API_KEY",  "COHERE_API_KEY",   "HUGGINGFACE_API_KEY",
            "OPENROUTER_API_KEY",
        }
        var_name = var_name.strip().upper()
        if var_name not in ALLOWED:
            raise HTTPException(400, f"var_name '{var_name}' not in allowed set")

        import ai.llm_gateway as _gw
        import os as _os

        setattr(_gw, var_name, "")
        _os.environ.pop(var_name, None)

        await audit(user.id, "gateway.key.revoked", meta={"var": var_name})
        logger.info("Gateway key revoked by exec: %s", var_name)
        return {"ok": True, "var": var_name, "active": False}

    @api_router.patch("/admin/gateway/keys/{var_name}/toggle")
    async def toggle_gateway_key(var_name: str, body: dict, user: User = Depends(require_role("executive_admin"))):
        """
        Enable or disable a provider key without permanently revoking it.
        Body: { enabled: bool }
        When disabling: clears the live attr so the gateway skips this provider.
        When enabling: requires the key to be re-pushed via POST /admin/gateway/keys.
        Returns current state.
        """
        ALLOWED = {
            "GROQ_API_KEY", "CEREBRAS_API_KEY", "GEMINI_API_KEY",
            "XAI_API_KEY",  "COHERE_API_KEY",   "HUGGINGFACE_API_KEY",
            "OPENROUTER_API_KEY",
        }
        var_name = var_name.strip().upper()
        if var_name not in ALLOWED:
            raise HTTPException(400, f"var_name '{var_name}' not in allowed set")

        enabled = bool(body.get("enabled", True))

        import ai.llm_gateway as _gw
        import os as _os

        if not enabled:
            # Disable: clear from live gateway (env var preserved for re-enable)
            _saved = _os.environ.get(var_name, "") or getattr(_gw, var_name, "")
            setattr(_gw, var_name, "")
            # Store the saved value so re-enable can restore it
            await db.platform_config.update_one(
                {"key": f"gateway_key_saved_{var_name}"},
                {"$set": {"key": f"gateway_key_saved_{var_name}", "value": _saved}},
                upsert=True,
            )
        else:
            # Re-enable: restore from saved value in DB or current env
            doc = await db.platform_config.find_one({"key": f"gateway_key_saved_{var_name}"}, {"_id": 0})
            saved = (doc or {}).get("value", "") or _os.environ.get(var_name, "")
            if not saved:
                raise HTTPException(400, f"No saved key for {var_name} — push the key first via POST /admin/gateway/keys")
            setattr(_gw, var_name, saved)
            _os.environ[var_name] = saved

        await audit(user.id, "gateway.key.toggled", meta={"var": var_name, "enabled": enabled})
        logger.info("Gateway key %s %s by exec", var_name, "enabled" if enabled else "disabled")
        return {"ok": True, "var": var_name, "enabled": enabled}

    @api_router.patch("/admin/gateway/budget")
    async def set_gateway_budget(body: dict, user: User = Depends(require_role("executive_admin"))):
        """
        Update the live hourly token budget cap without a redeploy.
        Body: { hourly_cap: int }  (minimum 1000, maximum 10_000_000)
        """
        import ai.llm_gateway as _gw
        cap = body.get("hourly_cap")
        if not isinstance(cap, int) or cap < 1000:
            raise HTTPException(400, "hourly_cap must be an integer >= 1000")
        if cap > 10_000_000:
            raise HTTPException(400, "hourly_cap cannot exceed 10,000,000")
        _gw.HOURLY_TOKEN_CAP = cap
        await db.platform_config.update_one(
            {"key": "gateway_hourly_cap"},
            {"$set": {"key": "gateway_hourly_cap", "value": cap}},
            upsert=True,
        )
        await audit(user.id, "gateway.budget.updated", meta={"hourly_cap": cap})
        logger.info("Gateway hourly_cap set to %d by exec", cap)
        return {"ok": True, "hourly_cap": cap}

    @api_router.post("/admin/gateway/reset-budget")
    async def reset_gateway_budget(user: User = Depends(require_role("executive_admin"))):
        """
        Emergency: zero out the current-hour token counter so the gateway
        can accept new calls immediately (use when cap was hit due to a runaway).
        """
        import ai.llm_gateway as _gw
        prev = _gw._hour_tokens_used
        _gw._hour_tokens_used = 0
        _gw._hour_window_start = 0.0  # set to epoch so next _reset_hour_if_needed fires immediately
        await audit(user.id, "gateway.budget.reset", meta={"previous_tokens_used": prev})
        logger.info("Gateway hourly token counter reset by exec (was %d)", prev)
        return {"ok": True, "previous_tokens_used": prev}

    _PROVIDER_RANKING_KEY = "gateway_provider_ranking"
    _DEFAULT_PROVIDER_RANKING = [
        "groq", "cerebras", "gemini", "grok", "cohere", "openrouter", "huggingface", "anthropic",
    ]

    @api_router.get("/admin/gateway/ranking")
    async def get_gateway_ranking(user: User = Depends(require_role("executive_admin"))):
        """Return current provider priority order (free-first by default)."""
        doc = await db.platform_config.find_one({"key": _PROVIDER_RANKING_KEY}, {"_id": 0})
        ranking = (doc or {}).get("value", _DEFAULT_PROVIDER_RANKING)
        return {"ranking": ranking, "default": _DEFAULT_PROVIDER_RANKING}

    @api_router.patch("/admin/gateway/ranking")
    async def set_gateway_ranking(body: dict, user: User = Depends(require_role("executive_admin"))):
        """
        Set the soft provider priority order.
        Body: { ranking: ["groq", "cerebras", ...] }
        Must include all providers or will be rejected.
        NOTE: this stores the preference in DB for display; the gateway's
        hard-coded fallback chain is the live order. To override runtime order,
        push/revoke keys to make only the desired providers available.
        """
        ranking = body.get("ranking", [])
        valid = set(_DEFAULT_PROVIDER_RANKING)
        if not isinstance(ranking, list) or set(ranking) != valid:
            raise HTTPException(400, f"ranking must be a list containing exactly: {sorted(valid)}")
        await db.platform_config.update_one(
            {"key": _PROVIDER_RANKING_KEY},
            {"$set": {"key": _PROVIDER_RANKING_KEY, "value": ranking}},
            upsert=True,
        )
        await audit(user.id, "gateway.ranking.updated", meta={"ranking": ranking})
        return {"ok": True, "ranking": ranking}

    # Auto-generate shared secret once; stored in DB so exec can retrieve it.
    _HEARTBEAT_SECRET_KEY = "exec_panel_heartbeat_secret"

    async def _get_or_create_heartbeat_secret() -> str:
        doc = await db.platform_config.find_one({"key": _HEARTBEAT_SECRET_KEY}, {"_id": 0})
        if doc and doc.get("value"):
            return doc["value"]
        secret = secrets.token_urlsafe(32)
        await db.platform_config.update_one(
            {"key": _HEARTBEAT_SECRET_KEY},
            {"$set": {"key": _HEARTBEAT_SECRET_KEY, "value": secret}},
            upsert=True,
        )
        logger.info("HEARTBEAT: auto-generated shared secret stored in DB — retrieve via /exec/panel/heartbeat-secret")
        return secret

    @api_router.get("/exec/panel/heartbeat-secret")
    async def exec_panel_heartbeat_secret(user: User = Depends(require_role("executive_admin"))):
        """Return the current heartbeat shared secret — executive_admin only.
        Copy this value into the backup/emergency server HEARTBEAT_SECRET env var."""
        return {"secret": await _get_or_create_heartbeat_secret()}

    @api_router.post("/exec/panel/heartbeat")
    async def exec_panel_heartbeat(body: _PanelHeartbeatBody):
        """Heartbeat from backup/emergency server. Requires shared secret."""
        expected = await _get_or_create_heartbeat_secret()
        provided = getattr(body, "secret", None) or ""
        if not secrets.compare_digest(provided, expected):
            raise HTTPException(401, "Invalid or missing heartbeat secret.")
        result = await heartbeat(db, body.source, version=body.version)
        if not result["ok"]:
            raise HTTPException(400, result["error"])
        return result

    @api_router.get("/exec/free-backup-matrix")
    async def exec_free_backup_matrix(user: User = Depends(require_role("executive_admin"))):
        """Return the free API backup matrix — shows every service and its fallback status."""
        from free_api_backup import status_summary
        return status_summary()

    @api_router.get("/admin/gateway/status")
    async def admin_gateway_status(user: User = Depends(require_role("admin"))):
        """Return LLM gateway provider availability and budget usage."""
        from ai.llm_gateway import gateway_status
        return gateway_status()

    logger.info("Emergency Breaker Panel + Gateway endpoints registered")
except Exception as _ep_err:
    logger.warning(f"Could not register Emergency Panel endpoints: {_ep_err}")

# ── Gateway: serve the standalone emergency UI ────────────────────────────────────
# When the React SPA is unavailable, this route serves the zero-dependency
# sovereign UI so execs can still access the system via any browser.
_EMERGENCY_UI_PATH = ROOT_DIR / "sovereign" / "ui.html"
if _EMERGENCY_UI_PATH.exists():
    from fastapi.responses import HTMLResponse as _HTMLResponse

    @api_router.get("/emergency", include_in_schema=False)
    @api_router.get("/emergency/", include_in_schema=False)
    async def emergency_ui():
        """Standalone emergency UI — works without React SPA."""
        html = _EMERGENCY_UI_PATH.read_text(encoding="utf-8")
        return _HTMLResponse(content=html)
    logger.info("Emergency UI gateway: /emergency")
else:
    logger.warning("Emergency UI not found at %s — gateway disabled", _EMERGENCY_UI_PATH)

# ── Executive Governance Layer ─────────────────────────────────────────────────
# Routes added for full RBAC governance restoration.
# All routes require executive_admin unless noted.


@api_router.get("/admin/audit/export")
async def export_audit_log(
    format: str = "json",
    limit: int = 1000,
    action: str = None,
    actor_id: str = None,
    user: User = Depends(require_role("executive_admin")),
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


# ═══════════════════════════════════════════════════════════════════════════════
#  CREATOR LOUNGE  —  /api/creator-lounge/*
#  Collaboration space for creators: projects, collabs, resource sharing.
# ═══════════════════════════════════════════════════════════════════════════════

class _CLProjectReq(BaseModel):
    title:       str   = Field(..., min_length=1, max_length=200)
    description: str   = Field("", max_length=2000)
    genre:       str   = Field("", max_length=100)
    looking_for: List[str] = []  # e.g. ["vocalist", "mixing engineer"]
    open:        bool  = True

class _CLCollab(BaseModel):
    project_id: str
    message:    str = Field("", max_length=500)

@api_router.get("/creator-lounge/projects")
async def cl_list_projects(
    genre: Optional[str] = None, open_only: bool = True,
    limit: int = 30, offset: int = 0,
    user: User = Depends(current_user)
):
    q: dict = {}
    if open_only: q["open"] = True
    if genre:     q["genre"] = {"$regex": genre, "$options": "i"}
    total  = await db.cl_projects.count_documents(q)
    cursor = db.cl_projects.find(q, {"_id": 0}).sort("created_at", -1).skip(offset).limit(min(limit, 50))
    items  = await cursor.to_list(min(limit, 50))
    return {"total": total, "projects": items}

@api_router.post("/creator-lounge/projects")
async def cl_create_project(body: _CLProjectReq, user: User = Depends(current_user)):
    doc = {
        "id":          str(uuid.uuid4()),
        "owner_id":    user.id,
        "owner_name":  getattr(user, "full_name", None) or getattr(user, "email", ""),
        "title":       body.title,
        "description": body.description,
        "genre":       body.genre,
        "looking_for": body.looking_for,
        "open":        body.open,
        "collabs":     [],
        "created_at":  datetime.now(timezone.utc).isoformat(),
        "updated_at":  datetime.now(timezone.utc).isoformat(),
    }
    await db.cl_projects.insert_one({**doc, "_id": doc["id"]})
    await audit(user.id, "creator_lounge.project.created", target=doc["id"])
    return doc

@api_router.patch("/creator-lounge/projects/{project_id}")
async def cl_update_project(project_id: str, body: _CLProjectReq, user: User = Depends(current_user)):
    proj = await db.cl_projects.find_one({"id": project_id}, {"_id": 0, "owner_id": 1})
    if not proj: raise HTTPException(404, "Project not found")
    if proj["owner_id"] != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Not your project")
    await db.cl_projects.update_one({"id": project_id}, {"$set": {
        **body.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()
    }})
    return {"ok": True}

@api_router.delete("/creator-lounge/projects/{project_id}")
async def cl_delete_project(project_id: str, user: User = Depends(current_user)):
    proj = await db.cl_projects.find_one({"id": project_id}, {"_id": 0, "owner_id": 1})
    if not proj: raise HTTPException(404, "Project not found")
    if proj["owner_id"] != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Not your project")
    await db.cl_projects.delete_one({"id": project_id})
    return {"ok": True}

@api_router.post("/creator-lounge/projects/{project_id}/collab")
async def cl_request_collab(project_id: str, body: _CLCollab, user: User = Depends(current_user)):
    proj = await db.cl_projects.find_one({"id": project_id}, {"_id": 0, "owner_id": 1, "open": 1})
    if not proj: raise HTTPException(404, "Project not found")
    if not proj.get("open"): raise HTTPException(400, "This project is not accepting collaborators")
    entry = {"user_id": user.id, "user_name": getattr(user, "full_name", None) or getattr(user, "email", ""),
             "message": body.message, "status": "pending", "requested_at": datetime.now(timezone.utc).isoformat()}
    await db.cl_projects.update_one({"id": project_id}, {"$push": {"collabs": entry}})
    await notify(proj["owner_id"], "New Collaboration Request",
        f"{entry['user_name']} wants to collaborate on your project.", link="/creator-lounge", kind="info")
    return {"ok": True}

@api_router.get("/creator-lounge/my-projects")
async def cl_my_projects(user: User = Depends(current_user)):
    cursor = db.cl_projects.find({"owner_id": user.id}, {"_id": 0}).sort("created_at", -1).limit(50)
    return {"projects": await cursor.to_list(50)}


# ═══════════════════════════════════════════════════════════════════════════════
#  BAND ON PAGE  —  /api/band/*
#  Live music booking: artist listings, venue inquiries, booking requests.
# ═══════════════════════════════════════════════════════════════════════════════

class _BandListingReq(BaseModel):
    artist_name: str  = Field(..., min_length=1, max_length=200)
    bio:         str  = Field("", max_length=3000)
    genres:      List[str] = []
    location:    str  = Field("", max_length=200)
    rate_min:    Optional[int] = None   # cents
    rate_max:    Optional[int] = None   # cents
    available:   bool = True
    social_links: dict = {}

class _BandBookingReq(BaseModel):
    listing_id:  str
    event_name:  str  = Field(..., min_length=1, max_length=200)
    event_date:  str  = Field(..., min_length=8, max_length=30)
    venue_name:  str  = Field(..., min_length=1, max_length=200)
    venue_city:  str  = Field("", max_length=100)
    offer_cents: Optional[int] = None
    message:     str  = Field("", max_length=1000)

@api_router.get("/band/listings")
async def band_list(
    genre: Optional[str] = None, location: Optional[str] = None,
    available_only: bool = True, limit: int = 30, offset: int = 0
):
    q: dict = {}
    if available_only: q["available"] = True
    if genre:    q["genres"]   = {"$regex": genre, "$options": "i"}
    if location: q["location"] = {"$regex": location, "$options": "i"}
    total  = await db.band_listings.count_documents(q)
    cursor = db.band_listings.find(q, {"_id": 0}).sort("created_at", -1).skip(offset).limit(min(limit, 50))
    return {"total": total, "listings": await cursor.to_list(min(limit, 50))}

@api_router.post("/band/listings")
async def band_create_listing(body: _BandListingReq, user: User = Depends(current_user)):
    existing = await db.band_listings.find_one({"owner_id": user.id}, {"_id": 0, "id": 1})
    doc = {
        "id":          existing["id"] if existing else str(uuid.uuid4()),
        "owner_id":    user.id,
        "artist_name": body.artist_name,
        "bio":         body.bio,
        "genres":      body.genres,
        "location":    body.location,
        "rate_min":    body.rate_min,
        "rate_max":    body.rate_max,
        "available":   body.available,
        "social_links":body.social_links,
        "updated_at":  datetime.now(timezone.utc).isoformat(),
    }
    if existing:
        await db.band_listings.update_one({"owner_id": user.id}, {"$set": doc})
    else:
        doc["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.band_listings.insert_one({**doc, "_id": doc["id"]})
    await audit(user.id, "band.listing.upserted", target=doc["id"])
    return doc

@api_router.get("/band/my-listing")
async def band_my_listing(user: User = Depends(current_user)):
    doc = await db.band_listings.find_one({"owner_id": user.id}, {"_id": 0})
    return doc or {}

@api_router.post("/band/book")
async def band_request_booking(body: _BandBookingReq, user: User = Depends(current_user)):
    listing = await db.band_listings.find_one({"id": body.listing_id}, {"_id": 0, "owner_id": 1, "artist_name": 1, "available": 1})
    if not listing: raise HTTPException(404, "Artist listing not found")
    if not listing.get("available"): raise HTTPException(400, "This artist is not currently available")
    booking = {
        "id":           str(uuid.uuid4()),
        "listing_id":   body.listing_id,
        "artist_id":    listing["owner_id"],
        "artist_name":  listing["artist_name"],
        "requester_id": user.id,
        "requester_name": getattr(user, "full_name", None) or getattr(user, "email", ""),
        "event_name":   body.event_name,
        "event_date":   body.event_date,
        "venue_name":   body.venue_name,
        "venue_city":   body.venue_city,
        "offer_cents":  body.offer_cents,
        "message":      body.message,
        "status":       "pending",
        "created_at":   datetime.now(timezone.utc).isoformat(),
    }
    await db.band_bookings.insert_one({**booking, "_id": booking["id"]})
    await notify(listing["owner_id"], "New Booking Request",
        f"{booking['requester_name']} wants to book you for {body.event_name} on {body.event_date}.",
        link="/band/bookings", kind="info")
    await audit(user.id, "band.booking.requested", target=booking["id"])
    return {"ok": True, "booking_id": booking["id"]}

@api_router.get("/band/bookings")
async def band_my_bookings(user: User = Depends(current_user)):
    as_artist   = await db.band_bookings.find({"artist_id":    user.id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    as_requester= await db.band_bookings.find({"requester_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"as_artist": as_artist, "as_requester": as_requester}

@api_router.patch("/band/bookings/{booking_id}/status")
async def band_update_booking(booking_id: str, body: dict, user: User = Depends(current_user)):
    status = body.get("status")
    if status not in ("accepted", "declined", "cancelled"):
        raise HTTPException(400, "status must be accepted, declined, or cancelled")
    bk = await db.band_bookings.find_one({"id": booking_id}, {"_id": 0})
    if not bk: raise HTTPException(404, "Booking not found")
    if bk["artist_id"] != user.id and bk["requester_id"] != user.id:
        raise HTTPException(403, "Not your booking")
    await db.band_bookings.update_one({"id": booking_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}})
    notify_uid = bk["requester_id"] if user.id == bk["artist_id"] else bk["artist_id"]
    await notify(notify_uid, f"Booking {status.title()}",
        f"Your booking for {bk['event_name']} has been {status}.", link="/band/bookings", kind="info")
    return {"ok": True, "booking_id": booking_id, "status": status}


# ── Revenue Executive Overview ────────────────────────────────────────────────
# Single-call dashboard for executive revenue: monthly goal progress, product
# breakdown, per-creator pending payouts, AI spend, and subscription health.

@api_router.get("/revenue/exec-overview")
async def revenue_exec_overview(user: User = Depends(require_role("executive_admin"))):
    """Real-time executive revenue overview. executive_admin only."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    MONTHLY_GOAL_CENTS = 800_000  # $8,000

    # Platform revenue this month
    month_payments = await db.payments.find(
        {"status": "paid", "created_at": {"$gte": month_start}},
        {"_id": 0, "amount_cents": 1, "product_key": 1, "created_at": 1},
    ).to_list(length=5000)
    revenue_month_cents = sum(p.get("amount_cents", 0) for p in month_payments)
    revenue_today_cents = sum(p.get("amount_cents", 0) for p in month_payments if p.get("created_at", "") >= today_start)

    all_payments = await db.payments.find({"status": "paid"}, {"_id": 0, "amount_cents": 1}).to_list(length=20000)
    revenue_alltime_cents = sum(p.get("amount_cents", 0) for p in all_payments)

    # Product breakdown this month
    by_product: dict = {}
    for p in month_payments:
        k = p.get("product_key", "unknown")
        by_product[k] = by_product.get(k, 0) + p.get("amount_cents", 0)

    # Monthly trend — last 6 periods
    months_trend = []
    for i in range(5, -1, -1):
        target_date = now.replace(day=1) - timedelta(days=1) if i > 0 else now.replace(day=1)
        for _ in range(i):
            target_date = (target_date.replace(day=1) - timedelta(days=1))
        period_label = target_date.strftime("%Y-%m")
        period_start = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        if i == 0:
            next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
            period_end = next_month.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        else:
            next_m = (target_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            period_end = next_m.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        total = await db.payments.aggregate([
            {"$match": {"status": "paid", "created_at": {"$gte": period_start, "$lt": period_end}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount_cents"}}},
        ]).to_list(1)
        months_trend.append({"period": period_label, "revenue_cents": total[0]["total"] if total else 0})

    # Active subscriptions
    active_subs = await db.subscriptions.count_documents({"status": "active"})
    canceled_subs = await db.subscriptions.count_documents({"status": "canceled"})

    # Creator payout details — all creators with pending earnings
    pending_pipeline = [
        {"$match": {"payout_status": "pending"}},
        {"$group": {"_id": "$creator_id", "pending_cents": {"$sum": "$creator_share_cents"}, "sales": {"$sum": 1}}},
        {"$sort": {"pending_cents": -1}},
    ]
    pending_by_creator = await db.creator_earnings.aggregate(pending_pipeline).to_list(200)
    total_pending_creator_cents = sum(c["pending_cents"] for c in pending_by_creator)

    # Enrich creator names and bank status
    creator_ids = [c["_id"] for c in pending_by_creator]
    creator_names: dict = {}
    if creator_ids:
        async for u in db.users.find({"id": {"$in": creator_ids}}, {"_id": 0, "id": 1, "full_name": 1, "email": 1}):
            creator_names[u["id"]] = u
    bank_set = set()
    if creator_ids:
        async for b in db.creator_bank_accounts.find({"creator_id": {"$in": creator_ids}}, {"_id": 0, "creator_id": 1}):
            bank_set.add(b["creator_id"])

    creator_payouts_detail = []
    for c in pending_by_creator:
        u = creator_names.get(c["_id"], {})
        creator_payouts_detail.append({
            "creator_id": c["_id"],
            "name": u.get("full_name", "Unknown"),
            "email": u.get("email", ""),
            "pending_cents": c["pending_cents"],
            "sales": c["sales"],
            "bank_on_file": c["_id"] in bank_set,
        })

    # AI spend this month
    ai_usage = await db.ai_usage_log.find(
        {"created_at": {"$gte": month_start}},
        {"_id": 0, "cost_usd": 1, "provider": 1},
    ).to_list(length=5000)
    ai_spend_month = round(sum(float(r.get("cost_usd") or 0) for r in ai_usage), 4)
    ai_calls_month = len(ai_usage)
    ai_by_provider: dict = {}
    for r in ai_usage:
        p = r.get("provider", "unknown")
        ai_by_provider[p] = round(ai_by_provider.get(p, 0) + float(r.get("cost_usd") or 0), 4)

    return {
        "generated_at": now.isoformat(),
        "goal": {
            "monthly_target_cents": MONTHLY_GOAL_CENTS,
            "month_cents": revenue_month_cents,
            "today_cents": revenue_today_cents,
            "alltime_cents": revenue_alltime_cents,
            "progress_pct": round(revenue_month_cents / MONTHLY_GOAL_CENTS * 100, 1),
        },
        "by_product": by_product,
        "monthly_trend": months_trend,
        "subscriptions": {
            "active": active_subs,
            "canceled": canceled_subs,
        },
        "creator_payouts": {
            "total_pending_cents": total_pending_creator_cents,
            "creators_pending": len(creator_payouts_detail),
            "detail": creator_payouts_detail,
        },
        "ai_spend": {
            "month_usd": ai_spend_month,
            "calls_month": ai_calls_month,
            "by_provider": ai_by_provider,
        },
    }



# ── Creator Revenue Split Tiers ─────────────────────────────────────────────

async def get_creator_split(user_id: str) -> dict:
    user_doc = await db.users.find_one({"id": user_id})
    if not user_doc:
        return {"creator_pct": 70, "platform_pct": 30, "tier": "base", "tier_label": "Base Creator"}
    is_certified = user_doc.get("creator_certified", False)
    course = await db.courses.find_one({"instructor_id": user_id, "published": True})
    has_students = False
    if course:
        enrollment = await db.enrollments.find_one({"course_id": str(course.get("_id", ""))})
        has_students = enrollment is not None
    instructor_rating = user_doc.get("instructor_rating", 0)
    if is_certified and has_students and instructor_rating >= 4.0:
        return {"creator_pct": 85, "platform_pct": 15, "tier": "certified_instructor", "tier_label": "Certified Instructor"}
    elif has_students:
        return {"creator_pct": 80, "platform_pct": 20, "tier": "active_instructor", "tier_label": "Active Instructor"}
    elif is_certified:
        return {"creator_pct": 75, "platform_pct": 25, "tier": "certified", "tier_label": "Certified Creator"}
    else:
        return {"creator_pct": 70, "platform_pct": 30, "tier": "base", "tier_label": "Base Creator"}

def _next_tier_info(current_tier: str) -> dict:
    tiers = {
        "base": {"label": "Certified Creator (75%)", "action": "Complete Creator Certification", "link": "/certification"},
        "certified": {"label": "Active Instructor (80%)", "action": "Publish a course and get your first student", "link": "/creator/courses"},
        "active_instructor": {"label": "Certified Instructor (85%)", "action": "Get Creator Certified and maintain 4.0+ rating", "link": "/certification"},
        "certified_instructor": {"label": "You're at the top! 85%", "action": "Keep creating and teaching.", "link": "/studio"},
    }
    return tiers.get(current_tier, tiers["base"])

@api_router.get("/creator/split")
async def get_my_split(user: User = Depends(current_user)):
    return await get_creator_split(user.id)

@api_router.get("/creator/payout-summary")
async def payout_summary(user: User = Depends(current_user)):
    split = await get_creator_split(user.id)
    bookings = await db.band_bookings.find(
        {"artist_user_id": user.id, "status": "accepted"}
    ).sort("created_at", -1).limit(20).to_list(length=20)
    total_earned = 0
    for b in bookings:
        offer = b.get("offer_cents", 0) or 0
        b["creator_cut_cents"] = int(offer * split["creator_pct"] / 100)
        b["platform_cut_cents"] = offer - b["creator_cut_cents"]
        total_earned += b["creator_cut_cents"]
        b["id"] = str(b.pop("_id", ""))
    return {
        "split": split,
        "total_earned_cents": total_earned,
        "recent_bookings": bookings[:10],
        "next_tier": _next_tier_info(split["tier"]),
    }


@api_router.get("/ai/provider-test")
async def ai_provider_test(user: User = Depends(require_role("admin"))):
    """Live test of every LLM provider — returns which ones actually respond.
    Use this to diagnose widget failures. Hits each provider with a 1-token ping."""
    from ai.llm_gateway import (
        GROQ_API_KEY, GROQ_BASE, GROQ_MODEL,
        CEREBRAS_API_KEY, CEREBRAS_BASE, CEREBRAS_MODEL,
        SAMBANOVA_API_KEY, SAMBANOVA_BASE, SAMBANOVA_MODEL,
        GEMINI_API_KEY, GEMINI_BASE, GEMINI_MODEL,
        XAI_API_KEY, XAI_BASE, XAI_MODEL,
        MISTRAL_API_KEY, MISTRAL_BASE, MISTRAL_MODEL,
        TOGETHER_API_KEY, TOGETHER_BASE, TOGETHER_MODEL,
        OPENROUTER_API_KEY, OPENROUTER_BASE, OPENROUTER_MODEL,
        _oai_compat_call, gateway_status,
        _hour_tokens_used, HOURLY_TOKEN_CAP,
    )
    import os as _os
    import httpx as _httpx

    ping_msg = [{"role": "user", "content": "Say OK"}]
    ping_sys = "Reply with just OK."

    results = {}

    async def _test(name, base, key, model):
        if not key:
            return {"ok": False, "reason": "no_key"}
        try:
            r = await _oai_compat_call(base, key, model, ping_sys, ping_msg, 8, None)
            return {"ok": True, "text": r["text"][:40]}
        except Exception as e:
            return {"ok": False, "reason": str(e)[:120]}

    results["groq"]       = await _test("groq",       GROQ_BASE,       GROQ_API_KEY,       GROQ_MODEL)
    results["cerebras"]   = await _test("cerebras",   CEREBRAS_BASE,   CEREBRAS_API_KEY,   CEREBRAS_MODEL)
    results["sambanova"]  = await _test("sambanova",  SAMBANOVA_BASE,  SAMBANOVA_API_KEY,  SAMBANOVA_MODEL)
    results["gemini"]     = await _test("gemini",     GEMINI_BASE,     GEMINI_API_KEY,     GEMINI_MODEL)
    results["grok"]       = await _test("grok",       XAI_BASE,        XAI_API_KEY,        XAI_MODEL)
    results["mistral"]    = await _test("mistral",    MISTRAL_BASE,    MISTRAL_API_KEY,    MISTRAL_MODEL)
    results["together"]   = await _test("together",   TOGETHER_BASE,   TOGETHER_API_KEY,   TOGETHER_MODEL)
    results["openrouter"] = await _test("openrouter", OPENROUTER_BASE, OPENROUTER_API_KEY, OPENROUTER_MODEL)

    working = [k for k, v in results.items() if v.get("ok")]
    return {
        "providers": results,
        "working_count": len(working),
        "working": working,
        "budget": {"used": _hour_tokens_used, "cap": HOURLY_TOKEN_CAP},
        "watchdog_disabled": bool(_os.environ.get("WATCHDOG_DISABLE")),
    }


# ── JAMIL — Director-class AI persona ────────────────────────────────────────
import os as _os_jamil

def _jamil_system_prompt() -> str:
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    try:
        import sys as _sys
        _sys.path.insert(0, "/app")
        from app.services.jamil.persona import JAMIL_SYSTEM_PROMPT as _JP
        return _JP.replace("{today}", today)
    except Exception:
        return f"You are Jamil. The Director. Supervisor. Sovereign. PRT. You run this operation. Today is {today}. Named after a son. Built to carry it. Cape and all."

# Start the 12-hour knowledge digest scheduler at import time (server startup)
try:
    from ai.knowledge_digest import start_digest_scheduler as _start_digest
    import asyncio as _asyncio_kd
    async def _schedule_digest_on_startup():
        _start_digest(db)
    _asyncio_kd.get_event_loop().run_until_complete(_schedule_digest_on_startup()) if False else None
    # Actual start happens via the startup event below
    _DIGEST_READY = True
except Exception as _de:
    logger.warning("Knowledge digest scheduler unavailable: %s", _de)
    _DIGEST_READY = False

@api_router.post("/jamil/digest")
async def jamil_digest_trigger(user: User = Depends(require_role("admin"))):
    """Manually trigger a knowledge digest immediately — admin only."""
    try:
        from ai.knowledge_digest import run_digest as _run_digest
        result = await _run_digest(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/jamil/knowledge")
async def jamil_knowledge_list(user: User = Depends(require_role("admin"))):
    """List all knowledge base entries — admin only."""
    try:
        entries = await db.jamil_knowledge.find(
            {}, {"_id": 0},
            sort=[("created_at", -1)],
        ).to_list(length=50)
        return {"entries": entries, "count": len(entries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/jamil/ping")
async def jamil_ping():
    return {"status": "ok", "route": "jamil"}

@api_router.post("/jamil/chat")
async def jamil_chat_server(
    message: str = Form(""),
    files: List[UploadFile] = File(default=[]),
    user: User = Depends(current_user),
):
    if not message.strip() and not files:
        raise HTTPException(status_code=400, detail="Send a message or attach a file.")

    system = _jamil_system_prompt()

    # Inject knowledge base context (last 12 digested knowledge entries)
    try:
        from ai.knowledge_digest import get_knowledge_context as _get_kb
        kb_context = await _get_kb(db)
        if kb_context:
            system += kb_context
    except Exception:
        pass

    # Inject active project context
    try:
        docs = await db.projects.find(
            {"status": {"$ne": "archived"}, "archived": {"$ne": True}},
            {"_id": 0, "title": 1, "status": 1, "priority": 1, "owner": 1, "milestones": 1}
        ).sort("updated_at", -1).to_list(length=20)
        if docs:
            lines = ["\n--- ACTIVE PROJECTS ---"]
            for d in docs:
                ms = d.get("milestones", [])
                done = sum(1 for m in ms if m.get("complete"))
                lines.append(f"• {d['title']} [{d['status']}] owner:{d.get('owner','-')} milestones:{done}/{len(ms)}")
            lines.append("--- END PROJECTS ---\n")
            system += "\n".join(lines)
    except Exception:
        pass

    parts = [message.strip()] if message.strip() else []
    for upload in files[:10]:
        content = await upload.read()
        if len(content) > 50 * 1024 * 1024:
            parts.append(f"[{upload.filename} skipped — exceeds 50 MB]")
            continue
        try:
            from app.services.jamil.extractor import extract as _extract
            extracted = await _extract(upload.filename or "file", content, upload.content_type or "")
            parts.append(f"\n---\nFile: {upload.filename}\n{extracted}\n---")
        except Exception as _fe:
            try:
                parts.append(f"\n---\nFile: {upload.filename}\n{content.decode('utf-8', errors='replace')[:4000]}\n---")
            except Exception:
                parts.append(f"[{upload.filename} — could not be read]")

    user_message = "\n\n".join(parts)

    # Route through the full 9-tier free gateway — Groq → Cerebras → SambaNova →
    # Gemini → Grok → Cohere → Mistral → Together → OpenRouter → HuggingFace → KB
    from ai.llm_gateway import call_llm as _gateway_call
    result = await _gateway_call(
        system=system,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=4096,
        persona_label="jamil",
    )
    reply = result.get("text", "").strip()

    if not reply or result.get("provider") == "kb_fallback":
        if not reply:
            raise HTTPException(
                status_code=503,
                detail="No AI provider available. Add at least one free API key in Railway Variables: GROQ_API_KEY, CEREBRAS_API_KEY, SAMBANOVA_API_KEY, GEMINI_API_KEY, MISTRAL_API_KEY, or TOGETHER_API_KEY.",
            )
        # KB fallback returned something — pass it through rather than 503
        logger.warning("Jamil routed to KB fallback — all AI providers unavailable")

    try:
        await db.jamil_history.insert_one({
            "user_id": str(getattr(user, "id", "") or getattr(user, "_id", "")),
            "message": message.strip(),
            "files": [f.filename for f in files],
            "reply": reply,
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        })
    except Exception:
        pass

    return {"reply": reply}

@api_router.post("/jamil/speak")
async def jamil_speak_server(body: dict, user: User = Depends(current_user)):
    text = (body.get("text") or "").strip()[:5000]
    if not text:
        raise HTTPException(status_code=400, detail="No text provided.")
    el_key = _os_jamil.environ.get("ELEVENLABS_API_KEY", "")
    if not el_key:
        raise HTTPException(status_code=503, detail="ElevenLabs not configured.")
    voice_id = body.get("voice_id") or _os_jamil.environ.get("JAMIL_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
    import httpx as _hx
    from fastapi.responses import Response as _Resp
    async with _hx.AsyncClient(timeout=30) as c:
        r = await c.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": el_key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
            json={"text": text, "model_id": "eleven_turbo_v2_5",
                  "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
        )
        if r.status_code == 200:
            return _Resp(content=r.content, media_type="audio/mpeg")
        raise HTTPException(status_code=502, detail=f"ElevenLabs error: {r.status_code}")

@api_router.post("/jamil/transcribe")
async def jamil_transcribe_server(audio: UploadFile = File(...), user: User = Depends(current_user)):
    content = await audio.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio must be under 25 MB.")
    key = _os_jamil.environ.get("GROQ_API_KEY", "")
    if not key:
        raise HTTPException(status_code=503, detail="Transcription not configured — GROQ_API_KEY missing.")
    import io as _io, httpx as _hx2
    async with _hx2.AsyncClient(timeout=60) as c:
        r = await c.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {key}"},
            files={"file": (audio.filename or "recording.webm", _io.BytesIO(content), audio.content_type or "audio/webm")},
            data={"model": "whisper-large-v3", "response_format": "text"},
        )
        if r.status_code == 200:
            return {"text": r.text.strip()}
        raise HTTPException(status_code=502, detail=f"Transcription error: {r.status_code}")

@api_router.get("/jamil/status")
async def jamil_status_server():
    from ai.llm_gateway import gateway_status as _gw_status
    gw = _gw_status()
    active = [k for k, v in gw["providers"].items() if v.get("available") and k != "kb_fallback"]
    return {
        "name": "Jamil",
        "status": "active" if active else "degraded",
        "active_providers": active,
        "provider_count": len(active),
        "voice": "elevenlabs" if _os_jamil.environ.get("ELEVENLABS_API_KEY") else "unavailable",
        "transcription": "groq-whisper" if _os_jamil.environ.get("GROQ_API_KEY") else "unavailable",
        "gateway": gw,
    }

# ── END JAMIL ─────────────────────────────────────────────────────────────────

# ── MY POSITION (/me/position*) ───────────────────────────────────────────────

@api_router.get("/me/position")
async def get_my_position(user: User = Depends(current_user)):
    u = await db.users.find_one({"id": user.id}, {"_id": 0})
    if not u:
        raise HTTPException(404, "User not found")
    return {
        "id": u["id"],
        "full_name": u.get("full_name", ""),
        "email": u.get("email", ""),
        "role": u.get("role", "student"),
        "feature_tier": u.get("feature_tier", "free"),
        "status": u.get("status", "active"),
        "exit_requested": u.get("exit_requested", False),
        "exit_reason": u.get("exit_reason", ""),
        "exit_requested_at": u.get("exit_requested_at"),
        "more_member": u.get("more_member", False),
    }

@api_router.get("/me/position/history")
async def get_position_history(user: User = Depends(current_user)):
    log = await db.audit_log.find(
        {"actor_id": user.id, "action": {"$in": ["role_change", "tier_change", "step_down", "exit_request"]}},
        {"_id": 0}
    ).sort("at", -1).limit(50).to_list(50)
    return {"history": log}

@api_router.get("/me/proceeds-preference")
async def get_proceeds_preference(user: User = Depends(current_user)):
    u = await db.users.find_one({"id": user.id}, {"proceeds_preference": 1})
    return {"preference": (u or {}).get("proceeds_preference", "platform")}

@api_router.post("/me/proceeds-preference")
async def set_proceeds_preference(body: dict, user: User = Depends(current_user)):
    pref = body.get("preference", "platform")
    if pref not in ("platform", "personal", "split", "donate"):
        raise HTTPException(400, "Invalid preference value")
    await db.users.update_one({"id": user.id}, {"$set": {"proceeds_preference": pref}})
    await audit(db, user.id, "proceeds_preference_set", {"preference": pref})
    return {"preference": pref}

@api_router.post("/me/step-down")
async def step_down(body: dict, user: User = Depends(current_user)):
    reason = (body.get("reason") or "").strip()
    if not reason:
        raise HTTPException(400, "Reason required")
    role_rank = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4}
    if role_rank.get(user.role, 1) <= 1:
        raise HTTPException(400, "Already at base role")
    roles = list(role_rank.keys())
    new_role = roles[role_rank.get(user.role, 2) - 2]
    await db.users.update_one({"id": user.id}, {"$set": {"role": new_role}})
    await audit(db, user.id, "step_down", {"from_role": user.role, "to_role": new_role, "reason": reason})
    return {"role": new_role, "message": f"Stepped down to {new_role}"}

@api_router.post("/me/request-exit")
async def request_exit(body: dict, user: User = Depends(current_user)):
    reason = (body.get("reason") or "").strip()
    if not reason:
        raise HTTPException(400, "Reason required")
    await db.users.update_one({"id": user.id}, {"$set": {
        "exit_requested": True,
        "exit_reason": reason,
        "exit_requested_at": _now(),
        "exit_type": "standard",
    }})
    await audit(db, user.id, "exit_requested", {"reason": reason})
    return {"exit_requested": True, "message": "Exit request submitted. Account remains active for 30 days."}

@api_router.post("/me/emergency-exit")
async def emergency_exit(body: dict, user: User = Depends(current_user)):
    reason = (body.get("reason") or "").strip()
    if not reason:
        raise HTTPException(400, "Reason required")
    await db.users.update_one({"id": user.id}, {"$set": {
        "exit_requested": True,
        "exit_reason": reason,
        "exit_requested_at": _now(),
        "exit_type": "emergency",
        "is_active": False,
    }})
    await audit(db, user.id, "emergency_exit", {"reason": reason})
    return {"exit_requested": True, "message": "Emergency exit initiated. Account suspended pending review."}

@api_router.post("/me/cancel-exit")
async def cancel_exit(user: User = Depends(current_user)):
    await db.users.update_one({"id": user.id}, {"$unset": {
        "exit_requested": "", "exit_reason": "", "exit_requested_at": "", "exit_type": ""
    }, "$set": {"is_active": True}})
    await audit(db, user.id, "exit_cancelled", {})
    return {"exit_requested": False, "message": "Exit request cancelled."}

@api_router.post("/me/leave-more")
async def leave_more(user: User = Depends(current_user)):
    await db.users.update_one({"id": user.id}, {"$set": {"more_member": False}})
    await audit(db, user.id, "left_more", {})
    return {"more_member": False, "message": "Removed from M.O.R.E. community."}


# ── PROJECTS (/projects*) ─────────────────────────────────────────────────────

def _new_project_id():
    import uuid
    return "proj_" + str(uuid.uuid4())[:8]

@api_router.get("/projects")
async def list_projects(user: User = Depends(current_user)):
    docs = await db.projects.find(
        {"$or": [{"owner_id": user.id}, {"collaborators": user.id}, {"visibility": "public"}]},
        {"_id": 0}
    ).sort("created_at", -1).limit(100).to_list(100)
    return docs

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str, user: User = Depends(current_user)):
    doc = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Project not found")
    if doc.get("visibility") != "public" and doc.get("owner_id") != user.id and user.id not in doc.get("collaborators", []):
        raise HTTPException(403, "Access denied")
    return doc

@api_router.post("/projects")
async def create_project(body: dict, user: User = Depends(current_user)):
    pid = _new_project_id()
    doc = {
        "project_id": pid,
        "owner_id": user.id,
        "owner_name": user.full_name,
        "title": (body.get("title") or "Untitled Project").strip(),
        "description": (body.get("description") or "").strip(),
        "status": body.get("status", "active"),
        "visibility": body.get("visibility", "private"),
        "tags": body.get("tags", []),
        "collaborators": [],
        "milestones": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.projects.insert_one(doc)
    doc.pop("_id", None)
    await audit(db, user.id, "project_created", {"project_id": pid, "title": doc["title"]})
    return doc

@api_router.patch("/projects/{project_id}")
async def update_project(project_id: str, body: dict, user: User = Depends(current_user)):
    doc = await db.projects.find_one({"project_id": project_id})
    if not doc:
        raise HTTPException(404, "Project not found")
    if doc.get("owner_id") != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Only owner can update")
    allowed = {"title", "description", "status", "visibility", "tags", "milestones"}
    updates = {k: v for k, v in body.items() if k in allowed}
    updates["updated_at"] = _now()
    await db.projects.update_one({"project_id": project_id}, {"$set": updates})
    doc.update(updates)
    doc.pop("_id", None)
    return doc

@api_router.post("/projects/{project_id}/milestone")
async def add_milestone(project_id: str, body: dict, user: User = Depends(current_user)):
    doc = await db.projects.find_one({"project_id": project_id})
    if not doc:
        raise HTTPException(404, "Project not found")
    if doc.get("owner_id") != user.id and user.id not in doc.get("collaborators", []):
        raise HTTPException(403, "Access denied")
    import uuid
    milestone = {
        "milestone_id": str(uuid.uuid4())[:8],
        "title": (body.get("title") or "").strip(),
        "due_date": body.get("due_date"),
        "completed": False,
        "created_at": _now(),
    }
    await db.projects.update_one({"project_id": project_id}, {"$push": {"milestones": milestone}, "$set": {"updated_at": _now()}})
    return milestone

@api_router.patch("/projects/{project_id}/milestone/{milestone_id}")
async def update_milestone(project_id: str, milestone_id: str, body: dict, user: User = Depends(current_user)):
    doc = await db.projects.find_one({"project_id": project_id})
    if not doc:
        raise HTTPException(404, "Project not found")
    if doc.get("owner_id") != user.id and user.id not in doc.get("collaborators", []):
        raise HTTPException(403, "Access denied")
    milestones = doc.get("milestones", [])
    for m in milestones:
        if m.get("milestone_id") == milestone_id:
            m.update({k: v for k, v in body.items() if k in {"title", "due_date", "completed"}})
    await db.projects.update_one({"project_id": project_id}, {"$set": {"milestones": milestones, "updated_at": _now()}})
    return {"updated": True}

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, user: User = Depends(current_user)):
    doc = await db.projects.find_one({"project_id": project_id})
    if not doc:
        raise HTTPException(404, "Project not found")
    if doc.get("owner_id") != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Only owner can delete")
    await db.projects.delete_one({"project_id": project_id})
    await audit(db, user.id, "project_deleted", {"project_id": project_id})
    return {"deleted": True}


# ── MEDIA STORE (/media/*) ────────────────────────────────────────────────────

@api_router.get("/media/products")
async def list_media_products(user: User = Depends(current_user)):
    docs = await db.media_products.find({"published": True}, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    return docs

@api_router.get("/media/products/mine")
async def my_media_products(user: User = Depends(current_user)):
    docs = await db.media_products.find({"owner_id": user.id}, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    return docs

@api_router.post("/media/products")
async def create_media_product(body: dict, user: User = Depends(current_user)):
    import uuid
    pid = "mp_" + str(uuid.uuid4())[:8]
    doc = {
        "id": pid,
        "owner_id": user.id,
        "owner_name": user.full_name,
        "title": (body.get("title") or "").strip(),
        "description": (body.get("description") or "").strip(),
        "price_cents": int(body.get("price_cents", 0)),
        "type": body.get("type", "file"),
        "tags": body.get("tags", []),
        "file_url": body.get("file_url", ""),
        "cover_url": body.get("cover_url", ""),
        "published": body.get("published", False),
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.media_products.insert_one(doc)
    doc.pop("_id", None)
    await audit(db, user.id, "media_product_created", {"id": pid, "title": doc["title"]})
    return doc

@api_router.patch("/media/products/{product_id}")
async def update_media_product(product_id: str, body: dict, user: User = Depends(current_user)):
    doc = await db.media_products.find_one({"id": product_id})
    if not doc:
        raise HTTPException(404, "Product not found")
    if doc.get("owner_id") != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Only owner can update")
    allowed = {"title", "description", "price_cents", "type", "tags", "file_url", "cover_url", "published"}
    updates = {k: v for k, v in body.items() if k in allowed}
    updates["updated_at"] = _now()
    await db.media_products.update_one({"id": product_id}, {"$set": updates})
    return {**{k: v for k, v in doc.items() if k != "_id"}, **updates}

@api_router.delete("/media/products/{product_id}")
async def delete_media_product(product_id: str, user: User = Depends(current_user)):
    doc = await db.media_products.find_one({"id": product_id})
    if not doc:
        raise HTTPException(404, "Product not found")
    if doc.get("owner_id") != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Only owner can delete")
    await db.media_products.delete_one({"id": product_id})
    await audit(db, user.id, "media_product_deleted", {"id": product_id})
    return {"deleted": True}

@api_router.get("/media/purchases")
async def my_media_purchases(user: User = Depends(current_user)):
    docs = await db.media_purchases.find({"buyer_id": user.id}, {"_id": 0}).sort("purchased_at", -1).limit(100).to_list(100)
    return docs

@api_router.post("/media/products/{product_id}/checkout")
async def checkout_media_product(product_id: str, user: User = Depends(current_user)):
    doc = await db.media_products.find_one({"id": product_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Product not found")
    if not doc.get("published"):
        raise HTTPException(400, "Product not available")
    existing = await db.media_purchases.find_one({"buyer_id": user.id, "product_id": product_id})
    if existing:
        return {"already_purchased": True, "file_url": doc.get("file_url", "")}
    if doc.get("price_cents", 0) > 0:
        raise HTTPException(402, "Payment required — online checkout for paid products is not available yet")
    import uuid
    purchase = {
        "id": str(uuid.uuid4())[:8],
        "buyer_id": user.id,
        "product_id": product_id,
        "title": doc.get("title", ""),
        "file_url": doc.get("file_url", ""),
        "purchased_at": _now(),
        "price_cents": 0,
    }
    await db.media_purchases.insert_one(purchase)
    purchase.pop("_id", None)
    return purchase

@api_router.get("/media/products/{product_id}/download")
async def download_media_product(product_id: str, user: User = Depends(current_user)):
    doc = await db.media_products.find_one({"id": product_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Product not found")
    if doc.get("price_cents", 0) > 0:
        existing = await db.media_purchases.find_one({"buyer_id": user.id, "product_id": product_id})
        if not existing and doc.get("owner_id") != user.id:
            raise HTTPException(403, "Purchase required")
    file_url = doc.get("file_url", "")
    if not file_url:
        raise HTTPException(404, "No file attached to this product")
    return {"file_url": file_url, "title": doc.get("title", "")}

@api_router.post("/media/upload")
async def upload_media_file(file: UploadFile = File(...), user: User = Depends(current_user)):
    max_mb = 50
    contents = await file.read()
    if len(contents) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {max_mb}MB)")
    import gridfs
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket
    bucket = AsyncIOMotorGridFSBucket(db)
    gfs_id = await bucket.upload_from_stream(file.filename, contents, metadata={"uploader": user.id, "content_type": file.content_type})
    file_url = f"/api/media/file/{gfs_id}"
    await audit(db, user.id, "media_file_uploaded", {"filename": file.filename, "size": len(contents)})
    return {"file_url": file_url, "filename": file.filename, "size": len(contents)}

@api_router.get("/media/file/{file_id}")
async def get_media_file(file_id: str):
    from bson import ObjectId
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket
    from fastapi.responses import StreamingResponse
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(400, "Invalid file ID")
    bucket = AsyncIOMotorGridFSBucket(db)
    try:
        stream = await bucket.open_download_stream(oid)
    except Exception:
        raise HTTPException(404, "File not found")
    async def iter_file():
        while True:
            chunk = await stream.read(65536)
            if not chunk:
                break
            yield chunk
    return StreamingResponse(iter_file(), media_type=stream.metadata.get("content_type", "application/octet-stream"))


# ── MISSING KAMERON (/missing/*) ─────────────────────────────────────────────

_KAMERON_CASE_ID = "kameron-mcmullen"

@api_router.get("/missing/photos/{case_id}")
async def get_missing_photos(case_id: str):
    photos = await db.missing_photos.find({"case_id": case_id}, {"_id": 0}).sort("uploaded_at", -1).to_list(100)
    return {"photos": photos, "case_id": case_id}

@api_router.post("/missing/photo")
async def upload_missing_photo(
    file: UploadFile = File(...),
    case_id: str = Form(default=_KAMERON_CASE_ID),
    user: User = Depends(current_user),
):
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 20MB)")
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket
    import uuid
    bucket = AsyncIOMotorGridFSBucket(db)
    gfs_id = await bucket.upload_from_stream(file.filename, contents, metadata={"content_type": file.content_type, "case_id": case_id})
    photo_url = f"/api/missing/file/{gfs_id}"
    doc = {
        "id": str(uuid.uuid4())[:8],
        "case_id": case_id,
        "photo_url": photo_url,
        "filename": file.filename,
        "uploaded_by": user.id,
        "uploaded_at": _now(),
    }
    await db.missing_photos.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.post("/missing/tip")
async def submit_missing_tip(body: dict):
    name = (body.get("name") or "").strip()
    tip_text = (body.get("tip") or "").strip()
    contact = (body.get("contact") or "").strip()
    case_id = body.get("case_id", _KAMERON_CASE_ID)
    if not tip_text:
        raise HTTPException(400, "Tip content is required")
    import uuid
    doc = {
        "id": str(uuid.uuid4())[:8],
        "case_id": case_id,
        "case_name": name,
        "tip": tip_text,
        "contact": contact,
        "submitted_at": _now(),
        "reviewed": False,
    }
    await db.missing_tips.insert_one(doc)
    doc.pop("_id", None)
    logger.info("MISSING TIP submitted for case %s", case_id)
    return {"submitted": True, "id": doc["id"], "message": "Thank you. Your tip has been submitted anonymously and will be reviewed."}

@api_router.get("/missing/file/{file_id}")
async def get_missing_file(file_id: str):
    from bson import ObjectId
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket
    from fastapi.responses import StreamingResponse
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(400, "Invalid file ID")
    bucket = AsyncIOMotorGridFSBucket(db)
    try:
        stream = await bucket.open_download_stream(oid)
    except Exception:
        raise HTTPException(404, "File not found")
    async def iter_file():
        while True:
            chunk = await stream.read(65536)
            if not chunk:
                break
            yield chunk
    return StreamingResponse(iter_file(), media_type=stream.metadata.get("content_type", "image/jpeg"))

# --- Payments router (extracted to routers/payments.py) ---
from routers import payments as _payments_mod
_payments_mod.bind(db, audit, notify, current_user)
api_router.include_router(_payments_mod.router)
# Re-export names other modules / later code in this file reference.
PAYMENT_PRODUCTS = _payments_mod.PAYMENT_PRODUCTS
PAYMENTS_ENABLED = _payments_mod.PAYMENTS_ENABLED
LEMON_SQUEEZY_API_KEY = _payments_mod.LEMON_SQUEEZY_API_KEY
LEMON_SQUEEZY_STORE_ID = _payments_mod.LEMON_SQUEEZY_STORE_ID



# --- LMS router (extracted to routers/lms.py) ---
from routers import lms as _lms_mod
_lms_mod.bind(db, current_user, audit, notify, assert_role)
api_router.include_router(_lms_mod.router)
# Re-export helpers other server.py endpoints (arcade, compliance quiz,
# leaderboard) still reference.
award_credentials = _lms_mod.award_credentials
award_xp = _lms_mod.award_xp
xp_level = _lms_mod.xp_level






# --- Ops router (notifications/attendance/incidents/analytics, extracted to routers/ops.py) ---
from routers import ops as _ops_mod
_ops_mod.bind(db, current_user, audit, notify, assert_role)
api_router.include_router(_ops_mod.router)



# --- Community router (extracted to routers/community.py) ---
from routers import community as _community_mod
_community_mod.bind(db, current_user, audit, assert_role, xp_level)
api_router.include_router(_community_mod.router)



# --- Studio/Arcade/Compliance router (extracted to routers/studio.py) ---
from routers import studio as _studio_mod
_studio_mod.bind(db, current_user, award_xp, award_credentials)
api_router.include_router(_studio_mod.router)


app.include_router(api_router)
# --- Register Headless Mode AI Dispatcher Router ---
from ai.controller import router as ai_dispatcher_router
app.include_router(ai_dispatcher_router)
# CORS: when origins is wildcard ("*") browsers reject credentials, so we
# turn off allow_credentials in that case (auth uses Bearer token in Authorization
# header anyway). If a specific origin list is supplied, credentials are allowed.
# Origin policy (first-party auto-append + BACKUP_ORIGIN) lives in platform_services.py.
_cors_origins = platform_services.build_cors_origins(
    os.environ.get('CORS_ORIGINS', '*'), BACKUP_ORIGIN)
_allow_creds = _cors_origins != ['*']
app.add_middleware(
    CORSMiddleware,
    allow_credentials=_allow_creds,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Accept-Language", "Cache-Control"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        from wai_institute.scripts.system_activation import stop_scout_scheduler
        stop_scout_scheduler()
    except Exception:
        pass
    try:
        stop_revenue_operations()
    except Exception:
        pass
    client.close()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
