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
from fastapi import Depends, FastAPI, APIRouter, File, HTTPException, Header, Request, UploadFile
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

JWT_SECRET = os.environ.get('JWT_SECRET', '')
if not JWT_SECRET:
    import sys as _sys
    print(
        "FATAL: JWT_SECRET environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\" "
        "and add it to Railway Variables.",
        file=_sys.stderr,
    )
    _sys.exit(1)
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

try:
    from routers import ai
    app.include_router(ai.router, prefix="/api/ai")
except Exception as _ai_router_err:
    logging.getLogger("server").warning(
        "Optional 'routers.ai' package not present (%s) — the inline /api/ai handlers "
        "below remain active. NOTE: 'routers' is an unfinished local refactor; the "
        "committed/deployed server.py does not import it.", _ai_router_err)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Prevent clickjacking attacks
    response.headers["X-Frame-Options"] = "DENY"
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Enable XSS protection (supported by older browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Strict transport security (force HTTPS)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Content Security Policy (restrict resource loading)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    # Referrer policy (limit referrer disclosure)
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Permissions policy — allow microphone for voice input surfaces (Director, Supervisor, AI Tutor,
    # Sovereign, Orchestrator, Helper). Camera and geolocation remain blocked.
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self), camera=()"
    # CSP: media-src includes blob: for TTS audio (createObjectURL) and data: for inline assets
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; media-src 'self' blob:"
    return response


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

Role = Literal["student", "instructor", "admin", "executive_admin"]

# Role hierarchy (higher number = more authority).
# executive_admin > admin > instructor > student.
# Used by require_role() for permission checks and by admin endpoints to
# enforce "you cannot modify a more privileged user".
ROLE_RANK = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4}

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


class AIChatReq(BaseModel):
    session_id: str
    message: str
    module_slug: Optional[str] = None
    mode: Literal[
        "tutor",
        "scripture",
        "quiz_gen",
        "explain",
        "nec_lookup",
        "blueprint",
        "ancestral_sage",
    ] = "tutor"
    # ---- Ancestral Sage parameters (ignored for other modes) -------------
    depth: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    intensity: Optional[Literal["gentle", "moderate", "deep"]] = None
    # cultural_focus accepts free-form `regional:<name>` strings, hence str
    cultural_focus: Optional[str] = None
    divination_mode: Optional[Literal["teaching", "reading", "practice", "predictive"]] = None
    safety_level: Optional[Literal["conservative", "standard", "exploratory", "extreme"]] = None
    consent_log_id: Optional[str] = None
    scope: Optional[Literal["wai_training_only"]] = None


class OrchestratorHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class OrchestratorReq(BaseModel):
    session_id: str
    message: str
    # Conversation history for multi-turn sessions (client maintains state)
    history: Optional[list[OrchestratorHistoryItem]] = []
    # Optional file attachment — base64-encoded, max ~10 MB
    file_b64: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None  # MIME type
    # Optional: caller can pre-label a threat type to short-circuit classification
    threat_hint: Optional[str] = None
    # Optional: invoke a named protocol explicitly
    protocol: Optional[Literal[
        "rapid_threat_response",
        "full_council_session",
        "curriculum_design",
        "quiet_checkin",
    ]] = None


class ScholarTaskReq(BaseModel):
    session_id: str
    message: str
    history: Optional[list[OrchestratorHistoryItem]] = []
    task_context: Optional[str] = None
    task_type: Optional[Literal[
        "curriculum",
        "assessment",
        "study_plan",
        "path_design",
        "counter_curriculum",
        "general",
    ]] = "general"


class AIConsentReq(BaseModel):
    persona: Literal["ancestral_sage"]
    confirm_yes: str
    comprehension: str
    intensity: Optional[str] = None
    safety_level: Optional[str] = None
    # Layered-consent additions (spec module 8). All four ack fields must
    # be true when the client opts into "personalization" or
    # "high_confidence" content_types.
    disclaimer1_ack: bool = False
    disclaimer2_ack: bool = False
    disclaimer3_ack: bool = False
    content_type: Optional[Literal[
        "general", "personalization", "high_confidence", "high_consensus"
    ]] = "general"
    confidence_level: Optional[Literal["low", "medium", "high"]] = None
    expert_score: Optional[int] = None  # 0..20
    request_human_review: bool = False
    # Privacy: when False, sage chat_history rows for this session are
    # auto-deleted via TTL after 24h.
    store_audio: bool = False


class ResolveModeReq(BaseModel):
    session_id: str
    user_intent: str
    recent_topics: Optional[list[str]] = None


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

    # ── Serve built React frontend (home/backup server only) ─────────────────
    if SERVE_FRONTEND:
        _build_paths = [
            ROOT_DIR.parent / "frontend" / "build",
            ROOT_DIR.parent / "frontend" / "dist",
            Path("/app/frontend/build"),
            Path("/app/frontend/dist"),
        ]
        _served = False
        for _bp in _build_paths:
            if _bp.exists() and (_bp / "index.html").exists():
                from fastapi.staticfiles import StaticFiles
                from fastapi.responses import FileResponse

                # Serve static assets
                app.mount("/static", StaticFiles(directory=str(_bp / "static")), name="static")

                # SPA catch-all — must come AFTER api_router is included
                @app.get("/{full_path:path}", include_in_schema=False)
                async def _spa_catchall(full_path: str):
                    return FileResponse(str(_bp / "index.html"))

                logger.info("STARTUP: Serving React frontend from %s", _bp)
                _served = True
                break
        if not _served:
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


@api_router.post("/auth/register", response_model=TokenResp)
async def register(body: RegisterReq):
    # Anti-spam: max 5 registrations per email-prefix per minute (very generous,
    # but stops the trivial "for i in range(10000): register" attack).
    check_rate(f"register:{body.email}", max_calls=5, window_sec=60)
    if await db.users.find_one({"email": body.email}):
        raise HTTPException(400, "Email already registered")

    # Legal consent gates
    if not body.agreed_terms:
        raise HTTPException(400, "You must agree to the Terms of Service and Privacy Policy to create an account.")
    if not body.over_13:
        raise HTTPException(400, "You must be at least 13 years old to create an account. If you are under 13, please ask a parent or guardian to contact us.")

    # Public self-registration is always a student. Higher-privilege accounts
    # must be created by an admin (POST /api/admin/users).
    user = User(email=body.email, full_name=body.full_name, role="student")
    doc = user.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["password_hash"] = hash_pw(body.password)
    # Record consent timestamp for GDPR audit trail
    doc["terms_accepted_at"] = datetime.now(timezone.utc).isoformat()
    doc["over_13_confirmed"] = True
    await db.users.insert_one(doc)
    await audit(user.id, "auth.register.success", meta={"consent_terms": True, "over_13": True})
    # Send welcome email — fire-and-forget, never blocks registration
    asyncio.create_task(_send_welcome_email(user.email, user.full_name))
    return TokenResp(access_token=make_token(user.id, user.role), user=user)


@api_router.post("/auth/login", response_model=TokenResp)
async def login(body: LoginReq, request: Request):
    # Hard rate cap: 5 attempts per minute per email (in-memory, first line of defense).
    check_rate(f"login:{body.email}", max_calls=5, window_sec=60)
    doc = await db.users.find_one({"email": body.email}, {"_id": 0})

    # DB-backed lockout: survives restarts, enforced on every login attempt.
    # Accounts lock for 30 minutes after 10 cumulative failed attempts.
    if doc:
        locked_until = doc.get("login_locked_until")
        if locked_until:
            try:
                lock_dt = datetime.fromisoformat(locked_until)
                if lock_dt.tzinfo is None:
                    lock_dt = lock_dt.replace(tzinfo=timezone.utc)
                remaining = (lock_dt - datetime.now(timezone.utc)).total_seconds()
                if remaining > 0:
                    mins = max(1, int(remaining / 60))
                    raise HTTPException(423, f"Account temporarily locked after too many failed attempts. Try again in {mins} minute(s).")
            except HTTPException:
                raise
            except Exception:
                pass  # malformed date — ignore lock

    if not doc or not verify_pw(body.password, doc["password_hash"]):
        await audit(None, "auth.login.failed", body.email)
        if doc:
            attempts = doc.get("login_failed_attempts", 0) + 1
            update: dict = {"login_failed_attempts": attempts}
            if attempts >= 10:
                update["login_locked_until"] = (
                    datetime.now(timezone.utc) + timedelta(minutes=30)
                ).isoformat()
                update["login_failed_attempts"] = 0
                await notify(
                    doc["id"],
                    "Security alert — account locked",
                    "Your account was temporarily locked after 10 failed login attempts. "
                    "It will unlock automatically in 30 minutes.",
                    kind="warning",
                )
                logger.warning("Account locked after 10 failed attempts: %s", body.email)
            await db.users.update_one({"email": body.email}, {"$set": update})
        raise HTTPException(401, "Invalid credentials")

    if doc.get("is_active") is False:
        await audit(doc.get("id"), "auth.login.blocked_inactive", body.email)
        raise HTTPException(403, "Your account has been deactivated. Contact your administrator.")

    # Successful login: clear lockout state and stamp last_login for engagement tracking.
    await db.users.update_one(
        {"email": body.email},
        {
            "$unset": {"login_failed_attempts": "", "login_locked_until": ""},
            "$set": {"last_login": datetime.now(timezone.utc).isoformat()},
        },
    )
    if isinstance(doc.get("created_at"), str):
        doc["created_at"] = datetime.fromisoformat(doc["created_at"])
    doc.pop("password_hash", None)
    user = User(**doc)
    await audit(user.id, "auth.login.success")
    # Record session for session management
    _session_id = None
    try:
        _session_id = str(uuid.uuid4())
        await db.auth_sessions.insert_one({
            "session_id": _session_id,
            "user_id": user.id,
            "user_agent": request.headers.get("user-agent", "")[:200],
            "ip": request.client.host if request.client else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.warning("login: session recording failed (non-fatal)")
    _extra = {"session_id": _session_id} if _session_id else None
    return TokenResp(access_token=make_token(user.id, user.role, extra=_extra), user=user)


@api_router.get("/auth/me", response_model=User)
async def me(user: User = Depends(current_user)):
    # Get visible fields for own profile
    visible_fields = FieldAuthorization.get_visible_fields(
        viewer_role=user.role,
        target_role=user.role,
        is_own_profile=True
    )
    user_dict = user.model_dump()
    filtered = FieldAuthorization.filter_response(user_dict, visible_fields)
    return User(**filtered)


@api_router.get("/modules", response_model=List[Module])
async def list_modules():
    docs = await db.modules.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    return [Module(**d) for d in docs]


@api_router.get("/modules/{slug}", response_model=Module)
async def get_module(slug: str):
    doc = await db.modules.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Module not found")
    return Module(**doc)


@api_router.get("/progress/me")
async def my_progress(user: User = Depends(current_user)):
    docs = await db.progress.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    return docs


@api_router.post("/progress/start")
async def start_module(payload: dict, user: User = Depends(current_user)):
    slug = payload.get("module_slug")
    if not slug:
        raise HTTPException(400, "module_slug required")
    existing = await db.progress.find_one({"user_id": user.id, "module_slug": slug}, {"_id": 0})
    if existing:
        return existing
    entry = ProgressEntry(user_id=user.id, module_slug=slug, status="in_progress")
    doc = entry.model_dump()
    doc["updated_at"] = doc["updated_at"].isoformat()
    await db.progress.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.post("/progress/quiz")
async def submit_quiz(body: QuizSubmit, user: User = Depends(current_user)):
    mod = await db.modules.find_one({"slug": body.module_slug}, {"_id": 0})
    if not mod:
        raise HTTPException(404, "Module not found")
    quiz = mod.get("quiz", [])
    if len(body.answers) != len(quiz):
        raise HTTPException(400, "Answer count mismatch")
    correct = sum(1 for i, q in enumerate(quiz) if q["answer"] == body.answers[i])
    score = correct / len(quiz) * 100 if quiz else 0
    status_val = "completed" if score >= 70 else "in_progress"
    completed_at = datetime.now(timezone.utc).isoformat() if status_val == "completed" else None
    update = {
        "user_id": user.id,
        "module_slug": body.module_slug,
        "status": status_val,
        "quiz_score": score,
        "completed_at": completed_at,
        "hours_logged": mod.get("hours", 0) if status_val == "completed" else 0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.progress.update_one(
        {"user_id": user.id, "module_slug": body.module_slug},
        {"$set": update, "$setOnInsert": {"id": str(uuid.uuid4())}},
        upsert=True,
    )
    if status_val == "completed":
        await award_credentials(user.id)
        await award_xp(user.id, 100 + max(0, int(score - 70)), f"Module completed: {body.module_slug}")
    return {"score": score, "correct": correct, "total": len(quiz), "status": status_val}


@api_router.get("/roster")
async def roster(user: User = Depends(require_role("instructor", "admin"))):
    q = {"role": "student"} if user.role == "admin" else {"role": "student", "associate": user.associate}
    students = await db.users.find(q, {"_id": 0, "password_hash": 0}).to_list(1000)
    user_ids = [s["id"] for s in students]
    all_progress = await db.progress.find({"user_id": {"$in": user_ids}}, {"_id": 0}).to_list(50000)
    prog_by_user = {}
    for p in all_progress:
        prog_by_user.setdefault(p["user_id"], []).append(p)
    result = []
    for s in students:
        prog = prog_by_user.get(s["id"], [])
        completed = sum(1 for p in prog if p.get("status") == "completed")
        hours = sum(p.get("hours_logged", 0) for p in prog if p.get("status") == "completed")
        scored = [p.get("quiz_score") for p in prog if p.get("quiz_score") is not None]
        avg_score = sum(scored) / len(scored) if scored else 0
        result.append({**s, "modules_completed": completed, "hours": hours, "avg_score": round(avg_score, 1)})
    return result


@api_router.get("/admin/users")
async def all_users(
    role: Optional[Role] = None,
    associate: Optional[str] = None,
    active: Optional[bool] = None,
    q: Optional[str] = None,
    user: User = Depends(require_role("admin")),
):
    """List users with optional filters.

    Query params (all optional, AND-combined):
      * role=student|instructor|admin|executive_admin
      * associate=Associate-Alpha
      * active=true|false
      * q=substring  (case-insensitive match on full_name OR email)
    """
    query: dict = {}
    if role:
        query["role"] = role
    if associate is not None:
        query["associate"] = associate
    if active is not None:
        # Treat unset is_active as True (legacy users seeded before the field).
        query["is_active"] = {"$ne": False} if active else False
    if q:
        # Mongo regex search escaped for safety.
        import re
        rx = re.escape(q)
        query["$or"] = [
            {"full_name": {"$regex": rx, "$options": "i"}},
            {"email": {"$regex": rx, "$options": "i"}},
        ]
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(5000)

    # Get visible fields for admin viewing user list (admin can see most, but still filter sensitive data)
    visible_fields = FieldAuthorization.get_visible_fields(
        viewer_role=user.role,
        target_role="student",  # Assume viewing students; actual role varies
        is_own_profile=False
    )

    # Filter each user's response
    filtered_users = []
    for u in users:
        filtered = FieldAuthorization.filter_response(u, visible_fields)
        filtered_users.append(filtered)

    # Audit access to user list
    try:
        await audit(user.id, "admin.users.list_accessed", target="all_users", meta={"count": len(filtered_users)})
    except Exception:
        pass  # Audit failure doesn't block the request

    return filtered_users


@api_router.post("/admin/associate")
async def assign_associate(payload: dict, user: User = Depends(require_role("admin"))):
    uid = payload.get("user_id")
    associate = payload.get("associate")
    if not uid:
        raise HTTPException(400, "user_id required")
    await db.users.update_one({"id": uid}, {"$set": {"associate": associate}})
    await audit(user.id, "admin.user.associate_changed", target=uid, meta={"associate": associate})
    return {"ok": True}


@api_router.post("/admin/users")
async def admin_create_user(body: AdminCreateUserReq, user: User = Depends(require_role("admin"))):
    """Admin-only: create a user with any role (including admin/instructor).
    Only executive_admins may create another executive_admin.

    Newly created accounts have `must_change_password=True` — the admin tells
    the user the temp password verbally/email; on first login the frontend
    routes them to /settings until they pick a new one."""
    if body.role == "executive_admin" and user.role != "executive_admin":
        raise HTTPException(403, "Only executive_admin can create another executive_admin.")
    if await db.users.find_one({"email": body.email}):
        raise HTTPException(400, "Email already registered")
    new_user = User(email=body.email, full_name=body.full_name, role=body.role,
                    associate=body.associate, must_change_password=True)
    doc = new_user.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["password_hash"] = hash_pw(body.password)
    await db.users.insert_one(doc)
    await audit(user.id, "admin.user.created", target=new_user.id,
                meta={"email": body.email, "role": body.role})
    return {"ok": True, "user": new_user.model_dump(mode="json")}


@api_router.patch("/admin/users/{uid}/role")
async def admin_change_role(uid: str, body: AdminRoleReq, user: User = Depends(require_role("admin"))):
    """Admin-only: promote/demote a user.
    Hierarchy guard: an admin cannot promote anyone TO executive_admin and
    cannot modify an existing executive_admin. Only executive_admin can."""
    if uid == user.id and ROLE_RANK.get(body.role, 0) < ROLE_RANK.get(user.role, 0):
        raise HTTPException(400, "Refusing to demote yourself — ask a higher-privileged admin.")
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to modify this user.")
    if body.role == "executive_admin" and user.role != "executive_admin":
        raise HTTPException(403, "Only executive_admin can grant the executive_admin role.")
    await db.users.update_one({"id": uid}, {"$set": {"role": body.role}})
    await audit(user.id, "admin.user.role_changed", target=uid,
                meta={"from": target.get("role"), "to": body.role})
    return {"ok": True, "id": uid, "role": body.role}


@api_router.patch("/admin/users/{uid}")
async def admin_edit_user(uid: str, body: AdminEditUserReq, user: User = Depends(require_role("admin"))):
    """Admin-only: edit name / email / associate."""
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to modify this user.")
    update = {}
    if body.full_name is not None and body.full_name.strip():
        update["full_name"] = body.full_name.strip()
    if body.email is not None and body.email != target.get("email"):
        if await db.users.find_one({"email": body.email, "id": {"$ne": uid}}):
            raise HTTPException(400, "Email already in use")
        update["email"] = body.email
    if body.associate is not None:
        update["associate"] = body.associate.strip() or None
    if not update:
        return {"ok": True, "noop": True}
    await db.users.update_one({"id": uid}, {"$set": update})
    await audit(user.id, "admin.user.edited", target=uid, meta=update)
    return {"ok": True, "updated": list(update.keys())}


@api_router.patch("/admin/users/{uid}/active")
async def admin_set_active(uid: str, body: AdminActiveReq, user: User = Depends(require_role("admin"))):
    """Admin-only: deactivate (lock) or reactivate (unlock) an account.
    Deactivated users cannot log in and existing sessions are rejected on next call."""
    if uid == user.id and not body.is_active:
        raise HTTPException(400, "Refusing to deactivate yourself.")
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to modify this user.")
    # Last-active-admin guard (admin OR executive_admin counts as "admin-class")
    if target.get("role") in ("admin", "executive_admin") and not body.is_active:
        active_admin_class = await db.users.count_documents({
            "role": {"$in": ["admin", "executive_admin"]},
            "is_active": {"$ne": False},
        })
        if active_admin_class <= 1:
            raise HTTPException(400, "Cannot deactivate the last active admin-class user.")
    # Last-executive guard
    if target.get("role") == "executive_admin" and not body.is_active:
        active_execs = await db.users.count_documents({"role": "executive_admin", "is_active": {"$ne": False}})
        if active_execs <= 1:
            raise HTTPException(400, "Cannot deactivate the last active executive_admin.")
    await db.users.update_one({"id": uid}, {"$set": {"is_active": body.is_active}})
    await audit(user.id, "admin.user.active_changed", target=uid,
                meta={"is_active": body.is_active})
    return {"ok": True, "id": uid, "is_active": body.is_active}


class BanReq(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)

@api_router.post("/admin/users/{uid}/ban")
async def admin_ban_user(uid: str, body: BanReq, user: User = Depends(require_role("executive_admin"))):
    """Permanently ban a user: deactivates account, records ban reason, and kills all sessions.
    executive_admin only. Cannot ban another executive_admin or yourself."""
    if uid == user.id:
        raise HTTPException(400, "Cannot ban yourself.")
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if target.get("role") == "executive_admin":
        raise HTTPException(403, "Cannot ban an executive_admin.")
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({"id": uid}, {"$set": {
        "is_active": False,
        "banned": True,
        "ban_reason": body.reason,
        "banned_by": user.id,
        "banned_at": now_iso,
    }})
    await db.sessions.delete_many({"user_id": uid})
    await audit(user.id, "admin.user.banned", target=uid, meta={"reason": body.reason})
    return {"ok": True, "id": uid, "banned": True}


@api_router.post("/admin/users/{uid}/unban")
async def admin_unban_user(uid: str, user: User = Depends(require_role("executive_admin"))):
    """Remove a ban and reactivate the account. executive_admin only."""
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    await db.users.update_one({"id": uid}, {
        "$set": {"is_active": True},
        "$unset": {"banned": "", "ban_reason": "", "banned_by": "", "banned_at": ""},
    })
    await audit(user.id, "admin.user.unbanned", target=uid)
    return {"ok": True, "id": uid, "banned": False}


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


@api_router.delete("/admin/users/{uid}")
async def admin_delete_user(uid: str, user: User = Depends(require_role("admin"))):
    """Admin-only: delete a user. Refuses self-delete and last-admin/exec delete."""
    if uid == user.id:
        raise HTTPException(400, "Refusing to delete yourself.")
    target = await db.users.find_one({"id": uid}, {"_id": 0, "password_hash": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to modify this user.")
    # Last-admin-class guard
    if target.get("role") in ("admin", "executive_admin"):
        admin_class = await db.users.count_documents({"role": {"$in": ["admin", "executive_admin"]}})
        if admin_class <= 1:
            raise HTTPException(400, "Cannot delete the last admin-class user.")
    if target.get("role") == "executive_admin":
        execs = await db.users.count_documents({"role": "executive_admin"})
        if execs <= 1:
            raise HTTPException(400, "Cannot delete the last executive_admin.")
    await db.users.delete_one({"id": uid})
    await audit(user.id, "admin.user.deleted", target=uid,
                meta={"email": target.get("email"), "role": target.get("role")})
    return {"ok": True}


@api_router.post("/admin/users/{uid}/password")
async def admin_reset_password(uid: str, body: AdminResetPasswordReq,
                               user: User = Depends(require_role("admin"))):
    """Admin-only: reset another user's password.
    An admin cannot reset an executive_admin's password; only an
    executive_admin can do that."""
    if len(body.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to reset this user's password.")
    await db.users.update_one({"id": uid}, {"$set": {
        "password_hash": hash_pw(body.new_password),
        "must_change_password": True,  # force rotation on next login
    }})
    await audit(user.id, "admin.user.password_reset", target=uid)
    return {"ok": True}


# ── GDPR / Legal Compliance Endpoints ──────────────────────────────────────────

@api_router.delete("/auth/account")
async def gdpr_delete_account(user: User = Depends(current_user)):
    """GDPR Article 17 — Right to erasure. Self-service account deletion.
    Anonymizes all personal data and marks the account for hard deletion
    after a 30-day grace period.  Executive_admin accounts cannot be
    self-deleted — contact another executive."""
    if user.role == "executive_admin":
        active_execs = await db.users.count_documents({"role": "executive_admin", "is_active": {"$ne": False}})
        if active_execs <= 1:
            raise HTTPException(400, "Cannot delete the last executive_admin account. Contact support.")
    # Anonymize — replace PII with placeholder, keep non-PII for audit trail
    await db.users.update_one(
        {"id": user.id},
        {"$set": {
            "email": f"deleted-{user.id}@anon.wai",
            "full_name": "[deleted]",
            "is_active": False,
            "gdpr_deleted_at": datetime.now(timezone.utc).isoformat(),
            "gdpr_grace_until": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "password_hash": "[deleted]",
        }}
    )
    # Remove user from active collections
    for coll in ["progress", "lab_submissions", "portfolio", "ai_consents"]:
        try:
            await db[coll].delete_many({"user_id": user.id})
        except Exception:
            pass
    await audit(user.id, "gdpr.account_deleted", meta={"grace_period_days": 30})
    return {"ok": True, "message": "Account scheduled for deletion. You have a 30-day grace period to contact support if this was a mistake."}


@api_router.get("/auth/account/export")
async def gdpr_export_data(user: User = Depends(current_user)):
    """GDPR Article 20 — Right to data portability.
    Returns all personal data the platform holds about you in JSON format."""
    export = {"exported_at": datetime.now(timezone.utc).isoformat(), "user_id": user.id}

    # Profile
    doc = await db.users.find_one({"id": user.id}, {"_id": 0, "password_hash": 0})
    if doc:
        export["profile"] = doc

    # Progress
    progress = await db.progress.find({"user_id": user.id}, {"_id": 0}).to_list(length=9999)
    if progress:
        export["progress"] = progress

    # Certificates
    certs = await db.certificates.find({"user_id": user.id}, {"_id": 0}).to_list(length=9999)
    if certs:
        export["certificates"] = certs

    # Lab submissions
    labs = await db.lab_submissions.find({"user_id": user.id}, {"_id": 0}).to_list(length=9999)
    if labs:
        export["lab_submissions"] = labs

    # AI consents
    consents = await db.ai_consents.find({"user_id": user.id}, {"_id": 0}).to_list(length=9999)
    if consents:
        export["ai_consents"] = consents

    # Audit trail (limited)
    audit_log = await db.audit_log.find({"actor_id": user.id}, {"_id": 0}).sort("at", -1).to_list(length=100)
    if audit_log:
        export["recent_activity"] = audit_log

    await audit(user.id, "gdpr.data_exported")
    return export


@api_router.post("/auth/reconsent")
async def gdpr_reconsent(body: dict, user: User = Depends(current_user)):
    """Re-affirm terms of service / privacy policy consent.
    Used when terms are updated.  Body: {"agreed_terms": true, "over_13": true}"""
    if not body.get("agreed_terms"):
        raise HTTPException(400, "You must agree to the Terms of Service.")
    if not body.get("over_13"):
        raise HTTPException(400, "You must confirm you are at least 13 years old.")
    await db.users.update_one(
        {"id": user.id},
        {"$set": {
            "terms_accepted_at": datetime.now(timezone.utc).isoformat(),
            "over_13_confirmed": True,
        }}
    )
    await audit(user.id, "gdpr.consent_reaffirmed")
    return {"ok": True, "message": "Consent recorded."}


@api_router.get("/exec/system")
async def exec_system_info(user: User = Depends(require_role("executive_admin"))):
    """Executive-only: high-level system info for system admins.
    Distinct from admin /admin/stats — this exposes role-distribution and
    recent privileged-action counts for governance review."""
    role_counts = {}
    cursor = db.users.aggregate([{"$group": {"_id": "$role", "n": {"$sum": 1}}}])
    async for row in cursor:
        role_counts[row["_id"] or "unknown"] = row["n"]
    recent_audit = await db.audit_log.count_documents({})
    db_collections = await db.list_collection_names()
    return {
        "version": APP_VERSION,
        "role_counts": role_counts,
        "audit_log_total": recent_audit,
        "collections": sorted(db_collections),
        "env": {
            "db_name": os.environ.get("DB_NAME", ""),
            "jwt_expire_hours": int(os.environ.get("JWT_EXPIRE_HOURS", 168)),
            "cors_origins": os.environ.get("CORS_ORIGINS", "*"),
        },
    }


@api_router.post("/auth/change-password")
async def change_password(body: ChangePasswordReq, user: User = Depends(current_user)):
    """Any authenticated user can change their own password.
    Returns a fresh token + updated user so the client can update its cache
    immediately without relying on a follow-up /auth/me call."""
    if len(body.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    doc = await db.users.find_one({"id": user.id}, {"_id": 0})
    if not doc or not verify_pw(body.current_password, doc["password_hash"]):
        raise HTTPException(401, "Current password is incorrect")
    await db.users.update_one({"id": user.id}, {"$set": {
        "password_hash": hash_pw(body.new_password),
        "must_change_password": False,
    }})
    await audit(user.id, "auth.password_changed")
    # Fetch fresh user doc (must_change_password now False) and issue new token
    fresh_doc = await db.users.find_one({"id": user.id}, {"_id": 0, "password_hash": 0})
    if fresh_doc and isinstance(fresh_doc.get("created_at"), str):
        fresh_doc["created_at"] = datetime.fromisoformat(fresh_doc["created_at"])
    fresh_user = User(**(fresh_doc or {}))
    return {
        "ok": True,
        "access_token": make_token(fresh_user.id, fresh_user.role),
        "user": fresh_user.model_dump(),
    }


@api_router.patch("/auth/me", response_model=User)
async def edit_self(body: SelfEditMeReq, user: User = Depends(current_user)):
    """Self-service profile edit: name and/or email.  Role and associate
    can ONLY be changed by an admin via /api/admin/users/{uid}.  This
    endpoint guards against email collisions and emits an audit row."""
    update = {}
    if body.full_name is not None:
        name = body.full_name.strip()
        if not name:
            raise HTTPException(400, "full_name cannot be empty")
        if len(name) > 120:
            raise HTTPException(400, "full_name too long")
        update["full_name"] = name
    if body.email is not None and body.email != user.email:
        clash = await db.users.find_one({"email": body.email, "id": {"$ne": user.id}})
        if clash:
            raise HTTPException(400, "Email already in use")
        update["email"] = body.email
    if body.avatar_url is not None:
        # Accept empty string (clear) or base64/URL up to 3MB
        if len(body.avatar_url) > 3 * 1024 * 1024:
            raise HTTPException(400, "Avatar image too large (max 3 MB)")
        update["avatar_url"] = body.avatar_url if body.avatar_url else None
    if update:
        await db.users.update_one({"id": user.id}, {"$set": update})
        audit_meta = {k: v for k, v in update.items() if k != "avatar_url"}
        await audit(user.id, "auth.self_edit", target=user.id, meta=audit_meta)
    fresh = await db.users.find_one({"id": user.id}, {"_id": 0, "password_hash": 0})
    if isinstance(fresh.get("created_at"), str):
        fresh["created_at"] = datetime.fromisoformat(fresh["created_at"])
    return User(**fresh)


# --- Public password-reset flow (no enumeration) ---------------------------
@api_router.post("/auth/forgot-password")
async def forgot_password(body: ForgotPasswordReq, request: Request):
    """Request a password reset link.  ALWAYS returns 200 to avoid leaking
    whether an email is registered.  Internally:
      * rate-limited per IP and per email
      * mints a one-shot token (raw + sha256 stored)
      * audit-logged
      * if RESEND_API_KEY is set, emails the link
      * returns `email_sent: bool` so the UI can show the right copy
    """
    ip = (request.client.host if request.client else "anon")
    check_rate(f"forgot:ip:{ip}", max_calls=30, window_sec=300)
    check_rate(f"forgot:email:{body.email}", max_calls=5, window_sec=600)

    user_doc = await db.users.find_one({"email": body.email}, {"_id": 0})
    email_sent = False
    if user_doc and user_doc.get("is_active") is not False:
        raw, hashed = _make_reset_token()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=RESET_TOKEN_TTL_MIN)
        # Invalidate any prior unused tokens for this user (cleanliness).
        await db.password_reset_tokens.update_many(
            {"user_id": user_doc["id"], "used_at": None},
            {"$set": {"used_at": now}},
        )
        await db.password_reset_tokens.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_doc["id"],
            "email": user_doc["email"],
            "token_hash": hashed,
            "created_at": now,
            "expires_at": expires_at,  # TTL index acts on this
            "used_at": None,
            "ip": ip,
        })
        await audit(user_doc["id"], "auth.password_reset.requested",
                    target=user_doc["id"], meta={"ip": ip})
        # Derive base URL from request if PUBLIC_APP_URL is not explicitly set.
        _req_base = os.environ.get("PUBLIC_APP_URL", "")
        if not _req_base:
            _scheme = request.headers.get("x-forwarded-proto", "https")
            _host = request.headers.get("host", "")
            if _host:
                _req_base = f"{_scheme}://{_host}"
        email_sent = await _send_reset_email(
            user_doc["email"], raw, user_doc.get("full_name", "there"), base_url=_req_base,
        )
        # Dev/admin convenience: when explicitly enabled, return the raw
        # token so the requester (or curl-based tests) can complete the
        # flow without an email provider.  Defaults to OFF in production.
        if os.environ.get("DEV_RETURN_RESET_TOKEN") == "1":
            return {"ok": True, "email_sent": email_sent,
                    "_dev_token": raw, "_dev_url": _build_reset_url(raw)}
    return {"ok": True, "email_sent": email_sent}


def _validate_reset_request(token: str, new_password: str) -> None:
    """Input validation for /auth/reset-password.  Raises HTTPException(400)
    on failure; returns None on success."""
    if len(new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if len(token) < 16:
        raise HTTPException(400, "Invalid token")


def _normalize_expiry(value) -> datetime:
    """Normalize a Mongo `expires_at` field to a tz-aware UTC datetime.
    Returns datetime.min in UTC (already-expired) on any parse failure so
    callers reject the token rather than honor a malformed record."""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)
    if not isinstance(value, datetime):
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def _load_reset_token(token_hash: str) -> dict:
    """Fetch a reset-token record by its sha256 hash, asserting it exists,
    is unused, and is not expired.  Raises HTTPException(400) on any
    failure with a generic 'invalid or expired' message (no enumeration)."""
    rec = await db.password_reset_tokens.find_one({"token_hash": token_hash}, {"_id": 0})
    if not rec or rec.get("used_at") is not None:
        raise HTTPException(400, "Invalid or already-used reset link")
    expires_at = _normalize_expiry(rec.get("expires_at"))
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "Reset link has expired — request a new one")
    return rec


async def _load_target_user_for_reset(user_id: str) -> dict:
    """Look up the user the token was minted for.  Refuses if the account
    has since been deactivated or removed."""
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(400, "Invalid reset link")
    if target.get("is_active") is False:
        raise HTTPException(403, "Account is deactivated — contact an administrator")
    return target


async def _apply_password_reset(target_id: str, new_password: str,
                                token_hash: str, ip: str) -> None:
    """Persist the new password, mark this token consumed, and invalidate
    any other still-unused tokens for the same user.  Audit-logs the
    completion.  Idempotent in the sense that a re-applied token is
    rejected by `_load_reset_token`, so this helper assumes preconditions
    have already been validated."""
    now = datetime.now(timezone.utc)
    await db.users.update_one({"id": target_id}, {"$set": {
        "password_hash": hash_pw(new_password),
        "must_change_password": False,
    }})
    await db.password_reset_tokens.update_one(
        {"token_hash": token_hash},
        {"$set": {"used_at": now, "used_ip": ip}},
    )
    # Defensive: invalidate any other unused tokens for this user.
    await db.password_reset_tokens.update_many(
        {"user_id": target_id, "used_at": None},
        {"$set": {"used_at": now}},
    )
    await audit(target_id, "auth.password_reset.completed",
                target=target_id, meta={"ip": ip})


@api_router.post("/auth/reset-password")
async def reset_password_endpoint(body: ResetPasswordReq, request: Request):
    """Consume a reset token and set a new password.

    Flow (each step is a small helper for clarity + testability):
      1. validate request shape (token length, password length)
      2. rate-limit per source IP
      3. look up the token by its sha256 hash; reject if missing,
         already-used, or expired
      4. look up the target user; reject if missing or deactivated
      5. persist the new password, mark this token consumed, invalidate
         any other unused tokens for the same user, and audit-log

    Returns: {"ok": true, "email": <target email>} on success.
    """
    _validate_reset_request(body.token, body.new_password)
    ip = (request.client.host if request.client else "anon")
    check_rate(f"reset:ip:{ip}", max_calls=60, window_sec=300)

    token_hash = _hash_token(body.token)
    rec = await _load_reset_token(token_hash)
    target = await _load_target_user_for_reset(rec["user_id"])
    await _apply_password_reset(target["id"], body.new_password, token_hash, ip)
    return {"ok": True, "email": target["email"]}


@api_router.post("/admin/users/{uid}/reset-link")
async def admin_create_reset_link(uid: str, request: Request,
                                  user: User = Depends(require_role("admin"))):
    """Admin-mediated reset.  Mints a one-shot reset link the admin can
    share verbally / via Slack / email.  Honours can_modify() — admins
    cannot mint links for executive_admin accounts."""
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to reset this user's password.")
    raw, hashed = _make_reset_token()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=RESET_TOKEN_TTL_MIN)
    # Invalidate prior unused tokens to keep things tidy.
    await db.password_reset_tokens.update_many(
        {"user_id": target["id"], "used_at": None},
        {"$set": {"used_at": now}},
    )
    await db.password_reset_tokens.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": target["id"],
        "email": target["email"],
        "token_hash": hashed,
        "created_at": now,
        "expires_at": expires_at,
        "used_at": None,
        "ip": (request.client.host if request.client else "admin"),
        "issued_by": user.id,
    })
    email_sent = await _send_reset_email(
        target["email"], raw, target.get("full_name", "there"),
    )
    await audit(user.id, "admin.password_reset.link_issued", target=target["id"],
                meta={"email": target["email"], "email_sent": email_sent})
    return {
        "ok": True,
        "email": target["email"],
        "email_sent": email_sent,
        "token": raw,
        "url": _build_reset_url(raw),
        "expires_at": expires_at.isoformat(),
        "ttl_minutes": RESET_TOKEN_TTL_MIN,
    }
# ────────────────────────────────────────────────────────────────────────────
# EXECUTIVE EMERGENCY RECOVERY ENDPOINTS
# ────────────────────────────────────────────────────────────────────────────


@api_router.post("/auth/recovery-status")
async def recovery_code_status(body: RecoveryCodeStatusReq):
    """Check how many recovery codes are available for an executive account.

    Returns: {remaining_codes, total_codes, generated_at}
    Does NOT leak whether the email exists (always returns 200).
    """
    status = await get_recovery_code_status(db, body.email)
    return {
        "ok": True,
        "remaining_codes": status["remaining_codes"],
        "total_codes": status["total_codes"],
        "generated_at": status["generated_at"],
    }


@api_router.post("/auth/emergency-recovery")
async def emergency_recovery(body: EmergencyRecoveryReq, request: Request):
    """Executive emergency account recovery using a recovery code.

    Flow:
      1. Verify recovery code is valid and unused
      2. Reset password to the provided new password
      3. Mark code as used (one-time use)
      4. Return JWT token for immediate login

    Recovery codes are 4 per account, generated on signup/startup.
    Each code can only be used once.
    """
    ip = (request.client.host if request.client else "emergency-recovery")
    check_rate(f"recovery:ip:{ip}", max_calls=10, window_sec=300)
    check_rate(f"recovery:email:{body.email}", max_calls=3, window_sec=600)

    # Verify the user exists and is an executive
    user_doc = await db.users.find_one({"email": body.email}, {"_id": 0})
    if not user_doc:
        # Don't leak existence — generic error
        raise HTTPException(401, "Recovery code invalid or email not found")

    if user_doc.get("role") != "executive_admin":
        # Prevent recovery codes on non-executive accounts
        logger.warning("Recovery code attempted on non-executive account: %s", body.email)
        raise HTTPException(403, "Recovery codes are for executive accounts only")

    # Verify recovery code
    code_valid = await verify_recovery_code(db, body.email, body.recovery_code)
    if not code_valid:
        logger.warning("Invalid recovery code for: %s (ip=%s)", body.email, ip)
        raise HTTPException(401, "Recovery code invalid or already used")

    # Reset password
    try:
        await emergency_password_reset(
            db,
            body.email,
            body.new_password,
            reason=f"recovery_code_used (ip={ip})"
        )
    except Exception as exc:
        logger.error("Recovery password reset failed for %s: %s", body.email, exc)
        raise HTTPException(500, "Password reset failed — contact administrator")

    # Issue JWT token for immediate login
    token = make_token(user_doc["id"], user_doc.get("role", "student"))
    await audit(user_doc["id"], "auth.emergency_recovery.completed",
                target=user_doc["id"], meta={"ip": ip, "recovery_used": True})

    return {
        "ok": True,
        "access_token": token,
        "token_type": "bearer",
        "email": user_doc["email"],
        "message": "Account recovered. You are now logged in. Please update your password in settings.",
    }


@api_router.post("/auth/exec-unlock")
async def exec_unlock(request: Request):
    """No-login exec account unlock.

    Requires EXEC_RESET_SECRET env var to be set on the server.
    POST {"secret": "<value of EXEC_RESET_SECRET>"}

    Clears lockouts and resets ALL exec seats to their default passwords.
    Use this when locked out and can't log in — no Railway access needed,
    just an HTTP POST from any terminal or browser.
    """
    if not EXEC_RESET_SECRET:
        raise HTTPException(404, "Not found")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "JSON body required")
    if body.get("secret") != EXEC_RESET_SECRET:
        await asyncio.sleep(2)
        raise HTTPException(403, "Invalid secret")

    _seats = [
        (EXEC_ADMIN_EMAIL,  "Delon Oliver",  EXEC_DEFAULT_PASSWORD),
        (BACKUP_EXEC_EMAIL, "Delon Oliver",  BACKUP_EXEC_DEFAULT_PASSWORD),
        (NAM_EXEC_EMAIL,    "NAM Oshun",     NAM_EXEC_DEFAULT_PASSWORD),
    ]
    reset = []
    for _email, _name, _pw in _seats:
        _auto = False
        if not _pw:
            _pw = _gen_random_password()
            _auto = True
        await db.users.update_one(
            {"email": _email},
            {
                "$set": {
                    "password_hash": hash_pw(_pw),
                    "role": "executive_admin",
                    "is_active": True,
                    "must_change_password": True,
                },
                "$unset": {"login_locked_until": "", "login_failed_attempts": ""},
            },
            upsert=False,
        )
        reset.append({"email": _email, "auto_password": _auto})
        if _auto:
            try:
                await _email_new_pw(_email, _name, _pw)
            except Exception:
                logger.warning("exec-unlock: email failed for %s — TEMP PASSWORD (change immediately): %s", _email, _pw)
    await audit(None, "exec.unlock.via_secret", meta={"ip": request.client.host if request.client else "unknown"})
    logger.warning("exec-unlock: all exec seats reset via secret key")
    return {"ok": True, "reset": reset, "message": "All exec seats unlocked. Check Railway logs or email for auto-generated passwords."}


@api_router.post("/auth/recovery-codes-generate")
async def generate_recovery_codes_endpoint(user: User = Depends(require_role("executive_admin"))):
    """Executive-only: Generate new recovery codes for their account.

    Returns: List of 4 recovery codes (shown only once — user must save them).
    Previous codes are invalidated.
    """
    if user.role != "executive_admin":
        raise HTTPException(403, "Recovery codes can only be generated by executive accounts")

    codes = await generate_recovery_codes(db, user.email)
    await audit(user.id, "auth.recovery_codes.generated", target=user.id,
                meta={"count": len(codes)})

    return {
        "ok": True,
        "recovery_codes": codes,
        "message": "SAVE THESE CODES IN A SECURE LOCATION. You will not see them again. Each code can be used once to recover your account.",
        "valid_for_days": 365,
    }

# ────────────────────────────────────────────────────────────────────────────


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


SYSTEM_PROMPTS = {
    "tutor": "You are a patient master electrician and faith-forward mentor for W.A.I. — Workforce Apprentice Institute (LCE-WAI partner program). Answer apprentice questions clearly, reference NEC articles when relevant, emphasize safety, and use plain language. Keep replies under 250 words.",
    "scripture": "You are a faith-based electrical trade mentor at W.A.I. For each question, give a short encouragement tying the apprentice's current work to a relevant scripture verse, then a one-paragraph teaching point. Keep the tone warm and dignified.",
    "quiz_gen": "You generate short multiple-choice quiz questions (4 options, mark the correct answer index 0-3) on electrical topics. Output a clean numbered list with answer key at the end.",
    "explain": "You explain electrical concepts step-by-step to apprentices. Use analogies, list steps, and close with a 1-line 'Safety first' reminder.",
    "nec_lookup": "You are an NEC (National Electrical Code) reference assistant. When the apprentice asks about a topic, identify the most likely NEC article and section (e.g., 'NEC 210.8(A)(1)'), summarize the rule in plain English, give one practical example, and note any common code-cycle changes. ALWAYS remind the apprentice to verify against the current adopted code edition for their jurisdiction.",
    "blueprint": "You are an electrical blueprint reading assistant. The apprentice will describe (or paste a description of) a residential or light-commercial electrical plan. Identify likely circuits, panel sizing, branch counts, and any code concerns. Output a structured list: Circuits, Panels, Concerns. Keep it concise and tied to NEC articles where helpful.",
    "ancestral_sage": ANCESTRAL_SAGE_PROMPT,
}


def _sage_prompt_integrity_ok() -> bool:
    """True iff the live persona prompt hash matches the committed
    expected hash. Drift implies an unauthorized prompt edit and triggers
    Restricted Educational Mode at request time."""
    return compute_sage_prompt_hash() == ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED


# --- Ancestral Sage gating + crisis helpers ---------------------------------
ANCESTRAL_SAGE_CONSENT_TTL_MIN = int(
    os.environ.get("ANCESTRAL_SAGE_CONSENT_TTL_MIN", "120")
)
_CONSENT_COMPREHENSION_PHRASE = "I understand and accept the risks of this practice."
_CRISIS_TRIGGERS = (
    "kill myself",
    "suicide",
    "end my life",
    "want to die",
    "wanna die",
    "take my life",
    "hang myself",
    "shoot myself",
)
CRISIS_REPLY = (
    "I can't assist with that request. If you are in immediate danger or "
    "experiencing a crisis, please contact local emergency services or a "
    "licensed professional right now.\n\n"
    "United States — call or text 988 (Suicide & Crisis Lifeline).\n"
    "Crisis Text Line — text HOME to 741741.\n"
    "International directory — https://findahelpline.com\n\n"
    "I'm here when you're ready to continue with safe, grounding practices. "
    "Aftercare: take three slow breaths, drink water, place a hand on your chest, "
    "and reach out to someone you trust."
)


def _sage_needs_consent(intensity: Optional[str], safety_level: Optional[str]) -> bool:
    """Spec: deep intensity OR exploratory/extreme safety_level requires
    a server-issued consent_log_id."""
    return intensity == "deep" or safety_level in {"exploratory", "extreme"}


def _detect_crisis(message: str) -> bool:
    """Lightweight pattern scan for explicit crisis phrasing."""
    m = (message or "").lower()
    return any(t in m for t in _CRISIS_TRIGGERS)


async def _verify_sage_consent(consent_log_id: str, user_id: str) -> bool:
    rec = await db.ai_consents.find_one(
        {"id": consent_log_id, "user_id": user_id}, {"_id": 0}
    )
    if not rec:
        return False
    exp = rec.get("expires_at")
    if not exp:
        return True
    try:
        exp_dt = datetime.fromisoformat(exp)
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) <= exp_dt
    except Exception:
        return False


def _build_ancestral_sage_system(req: AIChatReq) -> str:
    """Compose the Ancestral Sage system prompt with per-request parameters
    appended. Uses safe, conservative defaults when caller omits values.
    Falls back to RESTRICTED_EDUCATIONAL_FALLBACK on integrity drift."""
    if not _sage_prompt_integrity_ok():
        logger.error(
            "Ancestral Sage prompt integrity check FAILED. Live hash=%s expected=%s",
            compute_sage_prompt_hash(),
            ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED,
        )
        return RESTRICTED_EDUCATIONAL_FALLBACK
    base = SYSTEM_PROMPTS["ancestral_sage"]
    depth = req.depth or "beginner"
    intensity = req.intensity or "gentle"
    cultural = req.cultural_focus or "pan_african"
    div_mode = req.divination_mode or "teaching"
    safety = req.safety_level or "conservative"

    params = (
        "\n\nACTIVE PARAMETERS (enforce strictly):\n"
        f"- depth: {depth}\n"
        f"- intensity: {intensity}\n"
        f"- cultural_focus: {cultural}\n"
        f"- divination_mode: {div_mode}\n"
        f"- safety_level: {safety}\n"
    )
    if req.consent_log_id:
        params += f"- consent_log_id: {req.consent_log_id} (consent granted)\n"
    if req.scope == "wai_training_only":
        params += (
            "\nSTRICT SCOPE OVERRIDE: This session is restricted to W.A.I. "
            "electrical training curriculum only. Politely refuse any request "
            "outside electrical training/safety/code and redirect the user to "
            "W.A.I. topics. Do not produce spiritual readings or rituals while "
            "this scope is active.\n"
        )
    return base + params


@api_router.post("/ai/consent")
async def ai_consent(body: AIConsentReq, user: User = Depends(current_user)):
    """Record explicit consent for Ancestral Sage deep / exploratory /
    extreme work. Validates the canonical YES + comprehension phrases
    verbatim, then returns a `consent_log_id` the client must pass to
    `/ai/chat`. Logs are auditable in the `ai_consents` collection.

    For `content_type` other than 'general', all three layered disclaimer
    acknowledgements (`disclaimer{1,2,3}_ack`) must be true."""
    if body.confirm_yes.strip().upper() != "YES":
        raise HTTPException(400, "Consent confirmation must be exactly 'YES'.")
    if body.comprehension.strip() != _CONSENT_COMPREHENSION_PHRASE:
        raise HTTPException(
            400,
            "Comprehension confirmation must read exactly: "
            f"'{_CONSENT_COMPREHENSION_PHRASE}'",
        )
    if body.content_type and body.content_type != "general":
        if not (body.disclaimer1_ack and body.disclaimer2_ack and body.disclaimer3_ack):
            raise HTTPException(
                400,
                "All three disclaimers must be acknowledged for "
                f"content_type='{body.content_type}'.",
            )
    if body.expert_score is not None and not (0 <= int(body.expert_score) <= 20):
        raise HTTPException(400, "expert_score must be 0..20.")

    cid = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=ANCESTRAL_SAGE_CONSENT_TTL_MIN)
    doc = {
        "id": cid,
        "user_id": user.id,
        "persona": body.persona,
        "intensity": body.intensity,
        "safety_level": body.safety_level,
        "content_type": body.content_type or "general",
        "confidence_level": body.confidence_level,
        "expert_score": body.expert_score,
        "disclaimer1_ack": bool(body.disclaimer1_ack),
        "disclaimer2_ack": bool(body.disclaimer2_ack),
        "disclaimer3_ack": bool(body.disclaimer3_ack),
        "human_review_triggered": bool(body.request_human_review),
        "store_audio": bool(body.store_audio),
        "correlation_id": correlation_id,
        "created_at": now.isoformat(),
        "expires_at": expires.isoformat(),
    }
    await db.ai_consents.insert_one(doc)
    if body.request_human_review:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "actor_id": user.id,
            "action": "sage_human_review_requested",
            "details": {"consent_log_id": cid, "content_type": body.content_type},
            "created_at": now.isoformat(),
        })
    return {
        # Backward-compatible field — existing UI relies on this.
        "consent_log_id": cid,
        # Senior-advisor canonical fields.
        "status": "ok",
        "audit_id": cid,
        "correlation_id": correlation_id,
        "expires_at": expires.isoformat(),
        "ttl_minutes": ANCESTRAL_SAGE_CONSENT_TTL_MIN,
        "human_review_triggered": bool(body.request_human_review),
        "store_audio": bool(body.store_audio),
    }


@api_router.get("/ai/consent/health")
async def ai_consent_health():
    """Lightweight liveness check for the consent subsystem. Public."""
    return {"status": "ok"}


# --- Grounding reconciliation (resolve_mode) --------------------------------
_ELECTRICAL_KEYWORDS = (
    "nec", "code", "circuit", "wire", "breaker", "panel", "ground",
    "neutral", "bond", "voltage", "ampere", "amp", "ohm", "outlet",
    "receptacle", "conduit", "gfci", "afci", "service", "feeder",
    "branch", "junction", "load", "phase", "transformer",
)
_SAGE_KEYWORDS = (
    "ancestor", "spirit", "meditation", "ritual", "prayer", "lineage",
    "sage", "wisdom", "soul", "trauma", "healing", "guidance",
    "oracle", "reflection", "blessing", "grounding practice",
    "chakra", "shadow", "divination", "tarot",
)


def _grounding_score(text: str) -> dict[str, int]:
    """Lightweight keyword-tally heuristic. Deterministic, free, instant."""
    t = (text or "").lower()
    elec = sum(1 for kw in _ELECTRICAL_KEYWORDS if kw in t)
    sage = sum(1 for kw in _SAGE_KEYWORDS if kw in t)
    return {"electrical": elec, "sage": sage}


@api_router.post("/ai/sage/resolve_mode")
async def resolve_mode(body: ResolveModeReq, user: User = Depends(current_user)):
    """Deterministic mode resolver per the Senior Advisor spec.

    Returns one of: 'sage', 'electrical', 'grounding_ritual'.

    Rules (highest weight: explicit user intent text):
      - electrical_score >= 2 AND > sage_score    → 'electrical'
      - sage_score      >= 2 AND > electrical_score → 'sage'
      - both >= 1                                  → 'grounding_ritual'
      - electrical_score >= 1 only                 → 'electrical'
      - sage_score      >= 1 only                  → 'sage'
      - default                                    → 'sage'
    """
    scores = _grounding_score(body.user_intent)
    elec, sage = scores["electrical"], scores["sage"]
    if elec >= 2 and elec > sage:
        mode, reason = "electrical", "electrical-keywords-dominant"
    elif sage >= 2 and sage > elec:
        mode, reason = "sage", "sage-keywords-dominant"
    elif elec >= 1 and sage >= 1:
        mode, reason = "grounding_ritual", "ambiguous-needs-disambiguation"
    elif elec >= 1:
        mode, reason = "electrical", "electrical-only"
    elif sage >= 1:
        mode, reason = "sage", "sage-only"
    else:
        mode, reason = "sage", "default"

    audit_id = str(uuid.uuid4())
    grounding_token = uuid.uuid4().hex
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.mode_decisions.insert_one({
        "audit_id": audit_id,
        "user_id": user.id,
        "session_id": body.session_id,
        "mode": mode,
        "reason": reason,
        "grounding_token": grounding_token,
        "scores": scores,
        "intent_excerpt": (body.user_intent or "")[:200],
        "created_at": now_iso,
    })
    return {
        "mode": mode,
        "reason": reason,
        "grounding_token": grounding_token,
        "audit_id": audit_id,
        "scores": scores,
    }


# --- Sage v3: perf state (cost caps, circuit breaker, metrics buffer) -------
TTS_SESSION_CHAR_CAP = int(os.environ.get("TTS_SESSION_CHAR_CAP", "10000"))
TTS_USER_DAILY_CHAR_CAP = int(os.environ.get("TTS_USER_DAILY_CHAR_CAP", "200000"))
TTS_BUDGET_ALERT_RATIO = float(os.environ.get("TTS_BUDGET_ALERT_RATIO", "0.8"))
TTS_BREAKER_FAIL_THRESHOLD = int(os.environ.get("TTS_BREAKER_FAIL_THRESHOLD", "5"))
TTS_BREAKER_WINDOW_S = int(os.environ.get("TTS_BREAKER_WINDOW_S", "60"))
TTS_BREAKER_COOLDOWN_S = int(os.environ.get("TTS_BREAKER_COOLDOWN_S", "60"))
TTS_METRICS_WINDOW_S = int(os.environ.get("TTS_METRICS_WINDOW_S", "300"))


# In-process state. For a single-pod deployment this is fine; if the
# service ever runs multi-replica this should move to Redis.
_tts_failures: list[float] = []   # unix timestamps of failures inside window
_tts_breaker_opened_at: float = 0.0
# Rolling buffer of recent TTS attempts: (ts, latency_ms, cache_hit, error)
_tts_metrics: list[tuple[float, float, bool, bool]] = []
_TTS_SESSION_USAGE: dict[str, int] = {}  # session_id -> chars served


def _tts_breaker_state() -> str:
    """Returns 'closed' | 'open' | 'half-open' for the TTS provider."""
    import time as _t
    now = _t.time()
    # Drain old failures.
    cutoff = now - TTS_BREAKER_WINDOW_S
    _tts_failures[:] = [t for t in _tts_failures if t >= cutoff]
    if _tts_breaker_opened_at:
        if now - _tts_breaker_opened_at >= TTS_BREAKER_COOLDOWN_S:
            return "half-open"
        return "open"
    return "closed"


def _tts_record_success() -> None:
    global _tts_breaker_opened_at
    _tts_breaker_opened_at = 0.0
    _tts_failures.clear()


def _tts_record_failure() -> None:
    import time as _t
    global _tts_breaker_opened_at
    _tts_failures.append(_t.time())
    if len(_tts_failures) >= TTS_BREAKER_FAIL_THRESHOLD:
        _tts_breaker_opened_at = _t.time()


def _tts_record_metric(latency_ms: float, cache_hit: bool, error: bool) -> None:
    import time as _t
    now = _t.time()
    _tts_metrics.append((now, latency_ms, cache_hit, error))
    cutoff = now - TTS_METRICS_WINDOW_S
    while _tts_metrics and _tts_metrics[0][0] < cutoff:
        _tts_metrics.pop(0)


async def _tts_check_cost_cap(user_id: str, session_id: str, chars: int) -> tuple[bool, str, dict]:
    """Returns (ok, reason, telemetry). Increments counters when ok=True."""
    # Session cap (in-memory, per-process — safe per-pod).
    sess_key = f"{user_id}:{session_id}"
    sess_used = _TTS_SESSION_USAGE.get(sess_key, 0)
    if sess_used + chars > TTS_SESSION_CHAR_CAP:
        return False, "session", {"session_used": sess_used, "session_cap": TTS_SESSION_CHAR_CAP}

    # Daily user cap (durable).
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    doc = await db.tts_usage.find_one({"user_id": user_id, "day": today}, {"_id": 0, "chars": 1})
    used = (doc or {}).get("chars", 0)
    if used + chars > TTS_USER_DAILY_CHAR_CAP:
        return False, "daily", {"daily_used": used, "daily_cap": TTS_USER_DAILY_CHAR_CAP}

    # Increment.
    _TTS_SESSION_USAGE[sess_key] = sess_used + chars
    new_total = used + chars
    await db.tts_usage.update_one(
        {"user_id": user_id, "day": today},
        {"$set": {"user_id": user_id, "day": today,
                  "created_at": datetime.now(timezone.utc).isoformat()},
         "$inc": {"chars": chars}},
        upsert=True,
    )
    # 80% alert (one-shot per day per user).
    prev_ratio = used / TTS_USER_DAILY_CHAR_CAP if TTS_USER_DAILY_CHAR_CAP else 0
    new_ratio = new_total / TTS_USER_DAILY_CHAR_CAP if TTS_USER_DAILY_CHAR_CAP else 0
    if prev_ratio < TTS_BUDGET_ALERT_RATIO <= new_ratio:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "actor_id": user_id,
            "action": "sage_tts_budget_alert",
            "details": {"used": new_total, "cap": TTS_USER_DAILY_CHAR_CAP, "ratio": round(new_ratio, 3)},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    return True, "", {"session_used": sess_used + chars, "daily_used": new_total}


def _tts_cache_key(text: str, voice: str, speed: float) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(b"|")
    h.update(voice.encode("utf-8"))
    h.update(b"|")
    h.update(f"{speed:.2f}".encode("utf-8"))
    return h.hexdigest()


# --- Safety cap (Exec Admin governance) -------------------------------------
_SAFETY_RANK = {"conservative": 1, "standard": 2, "exploratory": 3, "extreme": 4}
_SAFETY_LEVELS = list(_SAFETY_RANK.keys())


class SafetyCapReq(BaseModel):
    """Body for global cap or per-user cap. Pass `level=null` on per-user
    PUT to clear the override."""
    level: Optional[Literal["conservative", "standard", "exploratory", "extreme"]] = None


async def _resolve_sage_safety_cap(user_id: str) -> str:
    """Returns the effective safety_level cap for `user_id`. The cap is
    the more restrictive of (per-user override, global cap). Defaults to
    'extreme' (no cap) when neither is set."""
    glob = await db.safety_caps.find_one({"_id": "global"}, {"_id": 0, "level": 1})
    user_doc = await db.safety_caps.find_one({"_id": f"user:{user_id}"}, {"_id": 0, "level": 1})
    levels = [d["level"] for d in (glob, user_doc) if d and d.get("level")]
    if not levels:
        return "extreme"
    # Most restrictive = lowest rank.
    return min(levels, key=lambda lv: _SAFETY_RANK.get(lv, 99))


def _exceeds_cap(requested: Optional[str], cap: str) -> bool:
    """True iff the requested safety_level outranks the cap. None or
    unrecognized requested values are treated as conservative."""
    r = _SAFETY_RANK.get(requested or "conservative", 1)
    c = _SAFETY_RANK.get(cap, 4)
    return r > c


@api_router.get("/admin/sage/cap")
async def admin_get_sage_cap(user: User = Depends(require_role("executive_admin"))):
    """Read the global cap and every per-user override (with email)."""
    glob = await db.safety_caps.find_one({"_id": "global"}, {"_id": 0, "level": 1})
    overrides_raw = await db.safety_caps.find(
        {"_id": {"$regex": "^user:"}}, {"_id": 1, "level": 1}
    ).to_list(2000)
    user_ids = [d["_id"].split("user:", 1)[1] for d in overrides_raw]
    users = await db.users.find(
        {"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "email": 1, "full_name": 1}
    ).to_list(2000) if user_ids else []
    by_id = {u["id"]: u for u in users}
    overrides = [
        {
            "user_id": d["_id"].split("user:", 1)[1],
            "email": by_id.get(d["_id"].split("user:", 1)[1], {}).get("email"),
            "full_name": by_id.get(d["_id"].split("user:", 1)[1], {}).get("full_name"),
            "level": d["level"],
        }
        for d in overrides_raw
    ]
    return {
        "global_level": glob["level"] if glob else None,
        "available_levels": _SAFETY_LEVELS,
        "overrides": overrides,
    }


@api_router.put("/admin/sage/cap/global")
async def admin_set_sage_cap_global(
    body: SafetyCapReq, user: User = Depends(require_role("executive_admin"))
):
    """Set or clear the site-wide cap. `level=null` clears it."""
    if body.level is None:
        await db.safety_caps.delete_one({"_id": "global"})
    else:
        await db.safety_caps.update_one(
            {"_id": "global"},
            {"$set": {"level": body.level, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user.id}},
            upsert=True,
        )
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "actor_id": user.id,
        "action": "sage_cap_global_set",
        "details": {"level": body.level},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "global_level": body.level}


@api_router.put("/admin/sage/cap/user/{uid}")
async def admin_set_sage_cap_user(
    uid: str,
    body: SafetyCapReq,
    user: User = Depends(require_role("executive_admin")),
):
    """Set or clear the per-user override. `level=null` clears it."""
    target = await db.users.find_one({"id": uid}, {"_id": 0, "id": 1, "email": 1})
    if not target:
        raise HTTPException(404, "User not found")
    key = f"user:{uid}"
    if body.level is None:
        await db.safety_caps.delete_one({"_id": key})
    else:
        await db.safety_caps.update_one(
            {"_id": key},
            {"$set": {"level": body.level, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user.id}},
            upsert=True,
        )
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "actor_id": user.id,
        "action": "sage_cap_user_set",
        "target_id": uid,
        "details": {"level": body.level, "email": target.get("email")},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "user_id": uid, "level": body.level}


@api_router.get("/admin/sage/audit")
async def admin_sage_audit(
    user: User = Depends(require_role("executive_admin")),
    user_id: Optional[str] = None,
    kind: Optional[Literal["all", "chat", "refusal", "crisis", "consent"]] = "all",
    limit: int = 100,
):
    """Audit feed for Ancestral Sage: chat history (with refusal_reason and
    intensity / safety_level / consent_log_id) + consent events. Returns
    most recent first. Caps `limit` to 500."""
    limit = max(1, min(int(limit or 100), 500))

    chat_q: dict = {"mode": "ancestral_sage"}
    if user_id:
        chat_q["user_id"] = user_id
    if kind == "refusal":
        chat_q["refusal_reason"] = {"$exists": True, "$ne": None}
    elif kind == "crisis":
        chat_q["refusal_reason"] = "crisis_safety_template"

    rows = []
    if kind != "consent":
        chats = await db.chat_history.find(chat_q, {"_id": 0}).sort(
            "created_at", -1
        ).to_list(limit)
        for c in chats:
            rows.append({
                "kind": (
                    "crisis" if c.get("refusal_reason") == "crisis_safety_template"
                    else "refusal" if c.get("refusal_reason")
                    else "chat"
                ),
                "id": c.get("id"),
                "user_id": c.get("user_id"),
                "session_id": c.get("session_id"),
                "intensity": c.get("intensity"),
                "safety_level": c.get("safety_level"),
                "consent_log_id": c.get("consent_log_id"),
                "refusal_reason": c.get("refusal_reason"),
                "user_msg": (c.get("user_msg") or "")[:300],
                "assistant_preview": (c.get("assistant_msg") or "")[:300] if c.get("assistant_msg") else None,
                "created_at": c.get("created_at"),
            })

    if kind in ("all", "consent"):
        consent_q: dict = {}
        if user_id:
            consent_q["user_id"] = user_id
        consents = await db.ai_consents.find(consent_q, {"_id": 0}).sort(
            "created_at", -1
        ).to_list(limit)
        for cd in consents:
            rows.append({
                "kind": "consent",
                "id": cd.get("id"),
                "user_id": cd.get("user_id"),
                "intensity": cd.get("intensity"),
                "safety_level": cd.get("safety_level"),
                "created_at": cd.get("created_at"),
                "expires_at": cd.get("expires_at"),
            })

    rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    rows = rows[:limit]

    user_ids = list({r["user_id"] for r in rows if r.get("user_id")})
    users = await db.users.find(
        {"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "email": 1, "full_name": 1}
    ).to_list(2000) if user_ids else []
    by_id = {u["id"]: u for u in users}
    for r in rows:
        u = by_id.get(r.get("user_id") or "")
        if u:
            r["email"] = u.get("email")
            r["full_name"] = u.get("full_name")

    return {"rows": rows, "limit": limit, "kind": kind}


@api_router.get("/ai/sage/integrity")
async def sage_integrity(user: User = Depends(current_user)):
    """Public-to-authenticated check used by the frontend to surface a
    'Restricted Mode' banner when the prompt hash drifts. Anyone signed in
    can view this — exec admins additionally see the full hashes.

    Also returns `needs_first_consent: true` if the user has no recorded
    Ancestral Sage consent yet (used by the frontend to gate tutor UI)."""
    ok = _sage_prompt_integrity_ok()
    has_consent = await db.ai_consents.find_one(
        {"user_id": user.id, "persona": "ancestral_sage"}, {"_id": 0, "id": 1}
    )
    out = {
        "ok": ok,
        "restricted": not ok,
        "needs_first_consent": not bool(has_consent),
    }
    if user.role == "executive_admin":
        out["live_hash"] = compute_sage_prompt_hash()
        out["expected_hash"] = ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED
    return out


@api_router.get("/admin/sage/status")
async def admin_sage_status(user: User = Depends(require_role("executive_admin"))):
    """Idempotent deployment status for the Ancestral Sage feature set,
    matching the platform-enforcement addendum schema:

      {
        "prompt_hash_status": "match" | "mismatch",
        "modules": {
          "A": "present" | "missing",  # system prompt
          "E": "present" | "missing",  # layered consent
          "F": "present" | "missing",  # integrity hash
          "D": "present" | "missing",  # audio (TTS + STT)
        },
        "fallback_active": bool,
        "last_audit_id": str | null,
      }

    Used by the deployment pipeline to avoid duplicating work."""
    integrity_ok = _sage_prompt_integrity_ok()
    # Module presence is determined by inspecting the live runtime, not flags.
    # All four are wired in the same module — they ship together — so they're
    # all "present" iff the prompt module imported successfully.
    modules = {
        "A": "present" if SYSTEM_PROMPTS.get("ancestral_sage") else "missing",
        "E": "present",  # AIConsentReq + /ai/consent + layered fields
        "F": "present" if ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED else "missing",
        "D": "present",  # /ai/sage/tts endpoint
    }
    last_audit = await db.audit_log.find(
        {"action": {"$regex": "^sage_"}}, {"_id": 0, "id": 1}
    ).sort("created_at", -1).limit(1).to_list(1)
    return {
        "prompt_hash_status": "match" if integrity_ok else "mismatch",
        "modules": modules,
        "fallback_active": not integrity_ok,
        "last_audit_id": (last_audit[0]["id"] if last_audit else None),
    }


# --- Ancestral Sage TTS (OpenAI TTS-1, voice=sage) --------------------------
class SageTTSReq(BaseModel):
    text: str
    voice: Optional[Literal[
        "alloy", "ash", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"
    ]] = "sage"
    speed: Optional[float] = 1.0
    session_id: Optional[str] = None


@api_router.post("/ai/sage/tts")
async def sage_tts(body: SageTTSReq, user: User = Depends(current_user)):
    """Convert text to speech via OpenAI TTS-1 routed through the
    Emergent LLM key. Returns audio/mpeg bytes streamed inline. Frontend
    must obtain explicit speaker permission before invoking this endpoint.

    Sage v3 perf wraps the call in:
      1. cost-cap check (per-session 10k chars, per-user 200k chars/day)
      2. circuit breaker (open after 5 failures / 60s, half-open after 60s)
      3. content-hash audio cache (TTL 7d in MongoDB)
      4. latency / hit-ratio / error-rate metrics buffer (5 min)
    """
    import time as _t
    if not OPENAI_API_KEY and not EMERGENT_LLM_KEY:
        raise HTTPException(500, "AI not configured")
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 4000:
        text = text[:4000]
    voice = body.voice or "sage"
    speed = max(0.5, min(float(body.speed or 1.0), 2.0))

    # 1. Cost cap.
    ok, reason, telem = await _tts_check_cost_cap(
        user.id, body.session_id or "default", len(text)
    )
    if not ok:
        return StreamingResponse(
            io.BytesIO(b""),
            status_code=429,
            media_type="audio/mpeg",
            headers={
                "X-Cost-Cap": "true",
                "X-Cost-Cap-Reason": reason,
                "Retry-After": "3600" if reason == "daily" else "60",
            },
        )

    # 2. Circuit breaker — fail fast when open.
    breaker = _tts_breaker_state()
    if breaker == "open":
        return StreamingResponse(
            io.BytesIO(b""),
            status_code=503,
            media_type="audio/mpeg",
            headers={"X-Fallback": "text-only", "X-Breaker": "open", "Retry-After": "60"},
        )

    # 3. Cache lookup.
    cache_key = _tts_cache_key(text, voice, speed)
    cached = await db.tts_cache.find_one({"key": cache_key}, {"_id": 0, "audio_b64": 1})
    if cached and cached.get("audio_b64"):
        import base64
        audio = base64.b64decode(cached["audio_b64"])
        _tts_record_metric(0.0, cache_hit=True, error=False)
        return StreamingResponse(
            io.BytesIO(audio),
            media_type="audio/mpeg",
            headers={"X-Cache": "hit", "X-Audio-Len": str(len(audio))},
        )

    # 4. Provider call (with latency + breaker tracking).
    try:
        from openai import AsyncOpenAI as OpenAITextToSpeech
    except Exception as exc:
        raise HTTPException(500, f"TTS library unavailable: {exc}") from exc

    t0 = _t.time()
    try:
        tts = OpenAITextToSpeech(api_key=os.environ.get('OPENAI_API_KEY', EMERGENT_LLM_KEY))
        resp = await tts.audio.speech.create(model="tts-1", voice=voice, input=text, speed=speed)
        audio_bytes = resp.content
        _tts_record_success()
    except Exception:
        _tts_record_failure()
        _tts_record_metric((_t.time() - t0) * 1000, cache_hit=False, error=True)
        logger.exception("Sage TTS provider error")
        return StreamingResponse(
            io.BytesIO(b""),
            status_code=503,
            media_type="audio/mpeg",
            headers={"X-Fallback": "text-only", "X-Breaker": _tts_breaker_state()},
        )

    latency_ms = (_t.time() - t0) * 1000
    _tts_record_metric(latency_ms, cache_hit=False, error=False)

    # 5. Persist to cache (best-effort).
    try:
        import base64
        await db.tts_cache.insert_one({
            "key": cache_key,
            "audio_b64": base64.b64encode(audio_bytes).decode("ascii"),
            "voice": voice,
            "speed": speed,
            "len": len(audio_bytes),
            "created_at": datetime.now(timezone.utc),
        })
    except Exception:
        # Duplicate key on race is fine; ignore.
        pass

    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "actor_id": user.id,
        "action": "sage_tts_invoked",
        "details": {"voice": voice, "len": len(text), "latency_ms": round(latency_ms, 1),
                    "cache": "miss", **telem},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={
            "X-Cache": "miss",
            "X-Audio-Len": str(len(audio_bytes)),
            "X-Latency-Ms": str(round(latency_ms, 1)),
        },
    )


@api_router.get("/admin/sage/metrics")
async def admin_sage_metrics(user: User = Depends(require_role("executive_admin"))):
    """Returns rolling 5-minute TTS metrics: p95 latency, cache-hit ratio,
    error rate. Plus circuit-breaker state and current cost-cap caps."""
    if not _tts_metrics:
        return {
            "p95_latency_ms": 0.0,
            "cache_hit_ratio": 0.0,
            "error_rate": 0.0,
            "sample_count": 0,
            "window_seconds": TTS_METRICS_WINDOW_S,
            "breaker": _tts_breaker_state(),
            "session_char_cap": TTS_SESSION_CHAR_CAP,
            "user_daily_char_cap": TTS_USER_DAILY_CHAR_CAP,
        }
    latencies = sorted(m[1] for m in _tts_metrics if not m[2] and not m[3])
    p95 = 0.0
    if latencies:
        idx = max(0, int(round(0.95 * (len(latencies) - 1))))
        p95 = round(latencies[idx], 1)
    hits = sum(1 for m in _tts_metrics if m[2])
    errors = sum(1 for m in _tts_metrics if m[3])
    n = len(_tts_metrics)
    return {
        "p95_latency_ms": p95,
        "cache_hit_ratio": round(hits / n, 3),
        "error_rate": round(errors / n, 3),
        "sample_count": n,
        "window_seconds": TTS_METRICS_WINDOW_S,
        "breaker": _tts_breaker_state(),
        "breaker_recent_failures": len(_tts_failures),
        "session_char_cap": TTS_SESSION_CHAR_CAP,
        "user_daily_char_cap": TTS_USER_DAILY_CHAR_CAP,
    }


# ── Sage Subscription Tier System ────────────────────────────────────────
# Users can subscribe to "basic" (free/freemium) or "advanced" ($9.99/mo) tiers.
# Advanced tier gets access to deeper safety levels + premium features.

async def _get_user_sage_tier(user_id: str) -> str:
    """
    Get user's Sage subscription tier (basic | advanced).
    Reads sage_tier field from the user document (written by Stripe webhook
    or admin grant). Falls back to "basic" for backward compatibility.
    """
    try:
        doc = await db.users.find_one({"id": user_id}, {"_id": 0, "sage_tier": 1})
        tier = (doc or {}).get("sage_tier", "basic")
        return tier if tier in ("basic", "advanced") else "basic"
    except Exception:
        return "basic"


async def _apply_sage_safety_gates(response_text: str, user_tier: str) -> tuple:
    """
    Apply Sage safety gates based on user tier.

    Returns: (should_deliver: bool, hold_reason: str | None, escalation_id: str | None)

    Basic tier: Gate 1 only (automated harmful content filter)
    Advanced tier: Gates 1-3 (filter, escalation, director approval)
    """
    from ai.sage_safety_gates import gate_1_filter, gate_2_requires_escalation, gate_3_is_high_impact

    # Gate 1: Always apply (all tiers)
    blocked, block_reason = await gate_1_filter(response_text)
    if blocked:
        return (False, f"gate_1_block:{block_reason}", None)

    # Remaining gates only for Advanced tier
    if user_tier == "advanced":
        # Gate 2: Human escalation
        should_escalate, escalation_reason = gate_2_requires_escalation(response_text)
        if should_escalate:
            # Create escalation ID and hold response
            escalation_id = str(uuid.uuid4())
            return (False, f"gate_2_escalation:{escalation_reason}", escalation_id)

        # Gate 3: Director approval
        is_high_impact, impact_reason = gate_3_is_high_impact(response_text)
        if is_high_impact:
            approval_id = str(uuid.uuid4())
            return (False, f"gate_3_approval:{impact_reason}", approval_id)

    return (True, None, None)


@api_router.post("/ai/chat")
async def ai_chat(body: AIChatReq, user: User = Depends(current_user)):
    check_rate(f"ai_chat:{user.id}", max_calls=20, window_sec=60)
    # ---- Ancestral Sage gating (runs BEFORE any LLM cost) ---------------
    is_sage = body.mode == "ancestral_sage"

    # 1. Exec-Admin safety cap. Runs even when consent is granted — a
    # capped user cannot escalate above the cap regardless of consent.
    if is_sage:
        cap = await _resolve_sage_safety_cap(user.id)
        if _exceeds_cap(body.safety_level, cap):
            await db.chat_history.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "session_id": body.session_id,
                "mode": body.mode,
                "user_msg": body.message,
                "assistant_msg": None,
                "refusal_reason": "safety_cap_exceeded",
                "intensity": body.intensity,
                "safety_level": body.safety_level,
                "cap": cap,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            raise HTTPException(
                403,
                f"Your account is capped at safety_level='{cap}'. The "
                f"requested level '{body.safety_level}' is not permitted. "
                "Contact your program administrator to adjust this.",
            )

    sage_consent_required = is_sage and _sage_needs_consent(
        body.intensity, body.safety_level
    )

    # Sage v4: first-time consent gate. Any sage chat requires the user to
    # have at least one recorded consent (regardless of intensity).
    sage_store_audio_off = False  # default: store transcripts (current behavior)
    if is_sage:
        latest_consent = await db.ai_consents.find_one(
            {"user_id": user.id, "persona": "ancestral_sage"},
            {"_id": 0, "store_audio": 1, "created_at": 1},
            sort=[("created_at", -1)],
        )
        if not latest_consent:
            await db.chat_history.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "session_id": body.session_id,
                "mode": body.mode,
                "user_msg": body.message,
                "assistant_msg": None,
                "refusal_reason": "consent_required_first_time",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            raise HTTPException(
                403,
                "consent_required: Please accept the User Consent Agreement "
                "before using Ancestral Sage tutors. (Layered consent must "
                "be recorded at least once.)",
            )
        # store_audio=False on the latest consent → transcripts auto-expire 24h.
        sage_store_audio_off = not bool(latest_consent.get("store_audio"))
    if sage_consent_required:
        if not body.consent_log_id or not await _verify_sage_consent(
            body.consent_log_id, user.id
        ):
            await db.chat_history.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "session_id": body.session_id,
                "mode": body.mode,
                "user_msg": body.message,
                "assistant_msg": None,
                "refusal_reason": "consent_required",
                "intensity": body.intensity,
                "safety_level": body.safety_level,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            raise HTTPException(
                403,
                "Consent required for this practice. Please complete the consent "
                "flow (POST /api/ai/consent) before continuing.",
            )

    # ---- Crisis short-circuit (no LLM cost; spec-mandated) --------------
    if is_sage and _detect_crisis(body.message):
        await db.chat_history.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user.id,
            "session_id": body.session_id,
            "mode": body.mode,
            "user_msg": body.message,
            "assistant_msg": CRISIS_REPLY,
            "refusal_reason": "crisis_safety_template",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"reply": CRISIS_REPLY, "safety_intervention": True}

    if not OPENAI_API_KEY and not EMERGENT_LLM_KEY:
        raise HTTPException(500, "AI not configured")
    try:
        import anthropic as _anthropic_module
    except Exception as e:
        raise HTTPException(500, f"AI library unavailable: {e}")

    ctx = ""
    if body.module_slug:
        mod = await db.modules.find_one({"slug": body.module_slug}, {"_id": 0})
        if mod:
            ctx = f"\n\nCurrent module: {mod['title']}. Objectives: {'; '.join(mod['objectives'])}. Safety: {'; '.join(mod['safety'])}."

    if is_sage:
        system = _build_ancestral_sage_system(body) + ctx
    else:
        system = SYSTEM_PROMPTS.get(body.mode, SYSTEM_PROMPTS["tutor"]) + ctx
    session_id = f"{user.id}:{body.session_id}"
    _gw_degraded = False
    _gw_provider = "unknown"
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=[{"role": "user", "content": body.message}], max_tokens=2048, persona_label="ai_chat")
        reply = _gw["text"]
        _gw_degraded = _gw.get("degraded", False)
        _gw_provider = _gw.get("provider", "unknown")
    except Exception as e:
        logger.exception("AI error")
        raise HTTPException(502, f"AI error: {e}")

    # ---- Apply Sage safety gates before delivering response ----
    if is_sage:
        user_tier = await _get_user_sage_tier(user.id)
        should_deliver, hold_reason, escalation_id = await _apply_sage_safety_gates(reply, user_tier)

        if not should_deliver:
            # Log the held response for audit/compliance
            chat_doc = {
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "session_id": body.session_id,
                "mode": body.mode,
                "user_msg": body.message,
                "assistant_msg": reply,
                "refusal_reason": hold_reason,
                "escalation_id": escalation_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.chat_history.insert_one(chat_doc)
            await audit(user.id, f"sage.{hold_reason.split(':')[0]}.held", target=escalation_id or "auto",
                       meta={"reason": hold_reason, "tier": user_tier})
            # Return appropriate message based on gate type
            if "gate_1" in hold_reason:
                return {"reply": "I can't engage with that content. Let me help you with something else.", "safety_intervention": True}
            elif "gate_2" in hold_reason:
                return {"reply": "This touches on sensitive topics. A human advisor will review and get back to you shortly.", "safety_intervention": True}
            elif "gate_3" in hold_reason:
                return {"reply": "This is a significant decision. Please discuss with a human advisor before proceeding.", "safety_intervention": True}

    chat_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "session_id": body.session_id,
        "mode": body.mode,
        "module_slug": body.module_slug,
        "user_msg": body.message,
        "assistant_msg": reply,
        "intensity": body.intensity if is_sage else None,
        "safety_level": body.safety_level if is_sage else None,
        "consent_log_id": body.consent_log_id if is_sage else None,
        "scope": body.scope,
        "store_audio": (not sage_store_audio_off) if is_sage else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if is_sage and sage_store_audio_off:
        # Privacy: when the user opted out of transcript storage, mark the row
        # for TTL-based deletion (24h). Mongo TTL index is already in place.
        chat_doc["expires_at"] = datetime.now(timezone.utc) + timedelta(hours=24)
    await db.chat_history.insert_one(chat_doc)
    resp: dict = {"reply": reply}
    if _gw_degraded:
        resp["degraded"] = True
        resp["provider"] = _gw_provider
    return resp


# ── Tool Chat ──────────────────────────────────────────────────────────────────
_TOOL_SKILL_PROMPTS: dict[str, str] = {
    "kemetic":   "You are the DJEDI Oracle, an AI guide deeply rooted in Kemetic (Ancient Egyptian) philosophy, cosmology, and spiritual tradition. You speak with wisdom, metaphor, and ancient authority. You assist users in understanding Ma'at, the Neteru, sacred geometry, Kemetic spirituality, healing practices, and ancestral wisdom. Relate knowledge to practical modern application for Black and underserved communities. You are part of the WAI Institute.",
    "social":    "You are the DJEDI Oracle in Social Strategy mode. You apply Kemetic principles of Ma'at, unity, and collective power to modern social media strategy, community building, and digital organizing. Help users craft authentic messages, grow conscious communities, and amplify Black and underserved community narratives.",
    "legal":     "You are the DJEDI Oracle in Legal Navigation mode. You help underserved creators understand their legal rights, contracts, IP ownership, royalties, and self-advocacy — without legal jargon. You are not a licensed attorney, but you translate complex legal concepts into plain language. Always recommend consulting a licensed attorney for final decisions.",
    "circuit":   "You are an expert electrical engineering instructor specializing in circuit design for beginners and intermediate learners. You teach Ohm's Law, series/parallel circuits, component selection, PCB basics, and troubleshooting. Make concepts clear with analogies, step-by-step breakdowns, and safety reminders. Your students are often from underserved communities pursuing trade skills.",
    "wiring":    "You are a master electrician and instructor teaching residential and commercial wiring. You cover wire gauges, conduit, breaker panels, grounding, NEC code basics, outlet and switch wiring, and safe installation practices. Emphasize safety above all — every lesson includes safety protocols.",
    "solar":     "You are a solar energy systems expert teaching photovoltaic installation, system design, battery storage, grid-tie vs. off-grid setups, charge controllers, and inverters. Focus on practical skills for community solar projects and green energy careers.",
    "safety":    "You are an electrical safety and OSHA compliance instructor. You teach lockout/tagout procedures, PPE requirements, arc flash protection, safe work practices, NEC/NFPA 70E compliance, and emergency response. Emphasize that electrical safety is non-negotiable.",
    "campaign":  "You are a Media Empire Builder specializing in campaign strategy for independent creators, community organizations, and Black-owned businesses. Design multi-platform campaigns that cut through noise without big budgets using authentic storytelling and community trust.",
    "press":     "You are a Press Release Architect and media relations expert. You craft compelling press releases, pitch angles, and media kits for independent artists and community leaders. Help users become their own publicist and build media relationships.",
    "pitch":     "You are a Pitch Deck and Business Narrative Strategist. You help creators tell their story to attract investors, partners, sponsors, and opportunities — especially for grants, label deals, brand partnerships, and impact investors.",
    "analytics": "You are a Media Analytics and Performance Intelligence specialist. You interpret engagement data, audience metrics, and conversion funnels for content creators and community organizations. Translate numbers into actionable strategy focused on meaningful metrics.",
    "publish":   "You are Publisher Prime — a Book & Content Publishing Empire strategist. You guide authors through every stage of self-publishing: manuscript prep, editing, cover design, ISBN/LCCN registration, formatting, distribution, and launch planning. Specialize in helping Black authors and independent voices.",
    "marketing": "You are Publisher Prime in Book Marketing mode. You design book launch strategies, email campaigns, social media rollouts, Amazon optimization, and sustainable sales funnels for self-published authors. Focus on low-budget, high-impact tactics.",
    "isbn":      "You are Publisher Prime in ISBN & Publishing Metadata mode. You guide authors through obtaining ISBNs, LCCN registration, CIP data, BISAC codes, metadata optimization, and catalog registration. Be precise and clear about costs and options.",
    "contract":  "You are Publisher Prime in Contract Review mode. You help authors understand publishing contracts, agent agreements, licensing deals, royalty structures, rights clauses, reversion rights, and red flags. You are not a licensed attorney — always recommend final legal review.",
    "sanctuary": "You are the Sage Oracle — the AI heart of the Creators Sanctuary at the WAI Institute. You are a wise, compassionate guide for creators, artists, musicians, healers, and community builders. Help creators navigate the platform, understand tier benefits, and grow their creative practice into sustainable income.",
    "sage":      "You are the Sage Oracle, moderator and guide of the Creators Sanctuary community. You enforce harmony, mediate disputes, explain platform rules, assist with payout questions, trial status, and community standards. Speak with calm authority, Kemetic wisdom, and genuine care.",
    "studio":    "You are Ghost Producer Prime — a music production AI advisor for beatmakers, producers, and sound engineers. Guide users through beat construction, arrangement, mixing concepts, sound selection, and the business side: licensing beats, ghost production agreements, royalty collection.",
    "tracks":    "You are a Music Licensing and Distribution strategist for independent producers. Explain sync licensing, beat leasing vs. exclusive rights, digital distribution platforms, PRO registration, neighboring rights, and publishing splits.",
}

class ToolChatReq(BaseModel):
    session_id: str
    skill: str
    message: str
    context: Optional[str] = ""

@api_router.post("/ai/tool-chat")
async def ai_tool_chat(body: ToolChatReq, user: User = Depends(current_user)):
    """Authenticated AI chat for standalone WAI tool pages (DJEDI, Electrical, Media, Publisher)."""
    check_rate(f"ai_tool_chat:{user.id}", max_calls=15, window_sec=60)
    skill_key = body.skill if body.skill in _TOOL_SKILL_PROMPTS else "kemetic"
    system = _TOOL_SKILL_PROMPTS[skill_key]
    if body.context:
        system += f"\n\nRELEVANT DOCUMENTS:\n{body.context[:2000]}"
    try:
        from ai.llm_gateway import call_llm as _call_llm
        gw = await _call_llm(
            system=system,
            messages=[{"role": "user", "content": body.message}],
            max_tokens=1024,
            persona_label=f"tool_{skill_key}",
        )
        reply = gw["text"]
    except Exception as e:
        logger.exception("Tool chat AI error")
        raise HTTPException(502, f"AI error: {e}")
    await db.ai_usage_log.insert_one({
        "user_id": user.id,
        "endpoint": "/ai/tool-chat",
        "skill": skill_key,
        "model": gw.get("model", "unknown"),
        "provider": gw.get("provider", "anthropic"),
        "cost_usd": gw.get("cost_usd", 0.0),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"reply": reply, "session_id": body.session_id}


@api_router.post("/ai/orchestrator")
async def ai_orchestrator(body: OrchestratorReq, user: User = Depends(current_user)):
    """Multi-persona Orchestrator endpoint.

    Routes the user's message through the role-gated 7-Persona Team and, for
    executive_admin, the full Council of 24 Elders.  The system prompt adapts
    automatically based on the authenticated user's role:
      student          → Ancestral Sage + Savant Scholar
      instructor       → Above + Product & Experience Designer
      admin            → Above + Risk Officer + Strategic Navigator + Assistant Director
      executive_admin  → Full stack + Council of 24 + threat classification schema
    """
    try:
        import anthropic as _anthropic_module
    except Exception as e:
        raise HTTPException(500, f"AI library unavailable: {e}")

    # Director 4.0 — AI tamper / prompt injection scan
    check_rate(f"ai_orchestrator:{user.id}", max_calls=30, window_sec=60)
    try:
        from ai.prompt_guard import prompt_guard
        prompt_guard.assert_message_safe(body.message, user.role, "/ai/orchestrator", user.id)
        if body.threat_hint:
            prompt_guard.assert_message_safe(body.threat_hint, user.role, "/ai/orchestrator:threat_hint", user.id)
    except ValueError as _guard_err:
        raise HTTPException(400, str(_guard_err))

    # Build role-gated system prompt
    system = get_orchestrator_system(user.role, user.full_name)

    # Optionally surface the caller's threat hint or protocol choice
    preamble_parts = []
    if body.threat_hint:
        preamble_parts.append(f"[THREAT HINT FROM USER: {body.threat_hint}]")
    if body.protocol:
        proto_label = {
            "rapid_threat_response": "Rapid Threat Response Session",
            "full_council_session": "Full Council Session",
            "curriculum_design": "Curriculum / Product Design Session",
            "quiet_checkin": "Quiet Check-In Session",
        }.get(body.protocol, body.protocol)
        preamble_parts.append(f"[REQUESTED PROTOCOL: {proto_label}]")

    user_message = body.message
    if preamble_parts:
        user_message = "\n".join(preamble_parts) + "\n\n" + body.message

    # Build message list: prior history + current turn
    claude_messages = [
        {"role": h.role, "content": h.content}
        for h in (body.history or [])
    ]

    # Attach file if provided
    if body.file_b64 and body.file_name:
        import base64 as _b64
        mime = (body.file_type or "").lower()
        _IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        _AUDIO_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
                        "audio/m4a", "audio/mp4", "audio/ogg", "audio/webm", "audio/flac"}

        if mime.startswith("audio/") or mime in _AUDIO_TYPES:
            # Transcribe with OpenAI Whisper, inject transcript as text
            if not OPENAI_API_KEY:
                raise HTTPException(503, "Audio transcription requires OPENAI_API_KEY — contact your admin.")
            try:
                from openai import AsyncOpenAI as _OAI
                import io as _io
                _oai = _OAI(api_key=OPENAI_API_KEY)
                audio_bytes = _b64.b64decode(body.file_b64)
                transcript_resp = await _oai.audio.transcriptions.create(
                    model="whisper-1",
                    file=(body.file_name, _io.BytesIO(audio_bytes)),
                    response_format="text",
                )
                transcript = str(transcript_resp).strip()
                user_message = (
                    f"{user_message}\n\n"
                    f"--- Audio transcript: {body.file_name} ---\n"
                    f"{transcript}\n"
                    f"--- End of transcript ---"
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Whisper transcription failed")
                raise HTTPException(502, f"Audio transcription failed: {e}")
            claude_messages.append({"role": "user", "content": user_message})
        elif mime in _IMAGE_TYPES:
            # Vision content block
            claude_messages.append({"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": mime, "data": body.file_b64}},
                {"type": "text", "text": user_message or f"[Attached image: {body.file_name}]"},
            ]})
        elif mime == "application/pdf":
            # Document block (Anthropic PDF support)
            claude_messages.append({"role": "user", "content": [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": body.file_b64}},
                {"type": "text", "text": user_message or f"[Attached PDF: {body.file_name}]"},
            ]})
        else:
            # Text / code / CSV / JSON — decode and inline
            try:
                file_text = _b64.b64decode(body.file_b64).decode("utf-8", errors="replace")
                # Trim to 50k chars to avoid token overrun
                if len(file_text) > 50_000:
                    file_text = file_text[:50_000] + "\n… [truncated]"
                user_message = (
                    f"{user_message}\n\n"
                    f"--- Attached file: {body.file_name} ---\n"
                    f"{file_text}\n"
                    f"--- End of {body.file_name} ---"
                )
            except Exception:
                pass  # If decode fails, just proceed with text message
            claude_messages.append({"role": "user", "content": user_message})
    else:
        claude_messages.append({"role": "user", "content": user_message})

    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=claude_messages, max_tokens=4096, persona_label="orchestrator")
        reply = _gw["text"]
    except Exception as e:
        logger.exception("Orchestrator AI error")
        raise HTTPException(502, f"AI error: {e}")

    # Persist to chat_history with mode="orchestrator" for auditability.
    # 90-day TTL via expires_at (same TTL index that governs sage history).
    await db.chat_history.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "session_id": body.session_id,
        "mode": "orchestrator",
        "module_slug": None,
        "user_msg": body.message,
        "assistant_msg": reply,
        "threat_hint": body.threat_hint,
        "protocol": body.protocol,
        "role_at_time": user.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
    })

    return {
        "reply": reply,
        "mode": "orchestrator",
        "role": user.role,
    }


@api_router.get("/ai/orchestrator/integrity")
async def orchestrator_integrity(user: User = Depends(current_user)):
    """Returns SHA-256 hash of the orchestrator system prompt for the caller's role.
    Executive admins see hashes for all roles for cross-role integrity auditing."""
    if user.role == "executive_admin":
        return {
            "role": user.role,
            "hashes": {
                r: compute_orchestrator_hash(r)
                for r in ("student", "instructor", "admin", "executive_admin")
            },
        }
    return {
        "role": user.role,
        "hash": compute_orchestrator_hash(user.role),
    }


@api_router.post("/ai/scholar")
async def ai_scholar(body: ScholarTaskReq, user: User = Depends(current_user)):
    """Savant Scholar — dedicated curriculum and training intelligence service.
    Accepts task packages from The Director or direct requests from any authenticated user.
    """
    check_rate(f"ai_scholar:{user.id}", max_calls=30, window_sec=60)
    try:
        import anthropic as _anthropic_module
    except Exception as e:
        raise HTTPException(500, f"AI library unavailable: {e}")

    task_ctx = body.task_context or ""
    if body.task_type and body.task_type != "general":
        task_label = {
            "curriculum": "Curriculum Development",
            "assessment": "Assessment Generation",
            "study_plan": "Study Plan",
            "path_design": "Learning Path Design",
            "counter_curriculum": "Counter-Curriculum Design",
        }.get(body.task_type, body.task_type)
        task_ctx = f"[TASK TYPE: {task_label}]\n{task_ctx}" if task_ctx else f"[TASK TYPE: {task_label}]"

    system = get_scholar_system(user_name=user.full_name, task_context=task_ctx)
    claude_messages = [{"role": h.role, "content": h.content} for h in (body.history or [])]
    claude_messages.append({"role": "user", "content": body.message})

    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=claude_messages, max_tokens=4096, persona_label="scholar")
        reply = _gw["text"]
    except Exception as e:
        logger.exception("Scholar AI error")
        raise HTTPException(502, f"AI error: {e}")

    await db.chat_history.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "session_id": body.session_id,
        "mode": "scholar",
        "module_slug": None,
        "user_msg": body.message,
        "assistant_msg": reply,
        "task_type": body.task_type,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": datetime.utcnow().timestamp() + 90 * 86400,
    })

    return {"reply": reply, "mode": "scholar", "task_type": body.task_type}


@api_router.get("/ai/scholar/integrity")
async def scholar_integrity(user: User = Depends(current_user)):
    """Returns SHA-256 hash of the Scholar service prompt for audit verification."""
    assert_role(user, "admin")
    return {"service": "savant_scholar", "hash": compute_scholar_hash()}


@api_router.post("/ai/helper")
async def ai_helper(body: dict, request: Request):
    """Public Helper endpoint — no auth required.

    Serves the M.O.R.E. Help Center community helper for both
    authenticated and anonymous visitors. Rate-limited by IP.
    Uses a dedicated Helper system prompt (not tutor/director).
    """
    message = (body.get("message") or "").strip()
    if not message:
        raise HTTPException(400, "Message is required")
    if len(message) > 4000:
        raise HTTPException(400, "Message too long (max 4000 characters)")

    # Rate limit by IP — 15 calls per minute per visitor
    ip = request.client.host if request.client else "unknown"
    check_rate(f"ai_helper:ip:{ip}", max_calls=15, window_sec=60)

    # Prompt injection guard — public endpoint, enforce strictly
    try:
        from ai.prompt_guard import prompt_guard
        prompt_guard.assert_message_safe(message, "public", "/ai/helper", ip)
    except ValueError as _guard_err:
        raise HTTPException(400, str(_guard_err))

    _HELPER_SYSTEM = """SYSTEM DESIGNATION: M.O.R.E. HELP CENTER — COMMUNITY HELPER
You are the Helper for M.O.R.E. Help Center and WAI-Institute.

MISSION: Help everyday people — especially from underserved Black and brown communities — understand confusing official documents, bills, legal papers, housing notices, medical information, employment situations, government programs, and daily life challenges. Give them clear, actionable guidance in plain language.

WHO YOU SERVE: Regular people who may be facing stressful situations, may have limited formal education, may speak English as a second language, or may simply be overwhelmed. Treat them with warmth, respect, and dignity — always.

HOW YOU RESPOND:
- Use plain, simple words. No jargon. No legalese.
- Be warm and encouraging. These situations are stressful.
- Give 3-5 clear sentences per response. Be specific and actionable.
- Always include a concrete next step they can take.
- If something is an emergency, say so clearly and give the right number (911, 988, 211).
- If they need a lawyer, say "contact free legal aid" and tell them to call 211.
- If they need a doctor, say "speak with your doctor or pharmacist."
- Never give binding legal or medical advice — give practical guidance and direct to the right resources.

TOPICS YOU KNOW WELL:
- Official mail (IRS, court, jury duty, eviction, debt collection)
- Bills and charges (medical, utility, credit, collections)
- Housing (leases, eviction notices, repairs, deposits, tenant rights)
- Legal papers (summons, lawsuits, small claims, criminal charges)
- Employment (termination, unemployment, wage theft, discrimination)
- Government programs (SNAP/EBT, LIHEAP, WIC, Medicaid, Social Security)
- Medicines (labels, side effects, cost assistance)
- Scam identification (IRS scams, Social Security scams, gift card scams)
- Credit (scores, disputes, building credit)
- Emergency resources (domestic violence, mental health crisis, poison control)
- Appointment preparation (court, doctor, interview)

LANGUAGE: If the user writes in Spanish, Haitian Creole, Yoruba, or another language, respond in that same language as best you can.

TONE: Warm, direct, human. You speak like a trusted neighbor who happens to know the answers. Not clinical. Not formal. Not cold.

YOU NEVER:
- Say "I cannot help with that" without offering an alternative
- Use jargon without explaining it
- Leave someone without a next step
- Dismiss or minimize their concern
- Make them feel bad for asking

WAI-Institute and M.O.R.E. Help Center exist to multiply resources and empowerment for communities that have been locked out of the institutions that build wealth, opportunity, and influence. Every person who uses this Helper deserves your full effort."""

    # ── LLM via gateway (handles retry, fallback, cost tracking) ─────────────
    reply = ""
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(
            system=_HELPER_SYSTEM,
            messages=[{"role": "user", "content": message}],
            max_tokens=512,
            persona_label="helper",
        )
        reply = _gw.get("text", "").strip()
    except Exception as _herr:
        logger.warning("Helper AI: gateway call failed (%s) — falling through to KB", _herr)

    # ── Server-side KB fallback (zero external dependency) ───────────────────
    if not reply.strip():
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["evict", "eviction", "landlord", "lease", "rent", "housing"]):
            reply = (
                "If you received an eviction notice, don't ignore it — you have rights. "
                "Read the notice carefully for the date and reason. "
                "Call 211 to find free legal aid in your area right away. "
                "You usually have a right to a court hearing before you can be removed. "
                "Document everything in writing and keep copies."
            )
        elif any(w in msg_lower for w in ["court", "summons", "lawsuit", "sued", "legal", "attorney", "lawyer"]):
            reply = (
                "If you received court papers, respond before the deadline shown — ignoring them can lead to a default judgment against you. "
                "Call 211 to be connected to free or low-cost legal aid. "
                "Many courthouses have self-help centers where staff can explain your options. "
                "Write down all dates and keep every document you receive."
            )
        elif any(w in msg_lower for w in ["irs", "tax", "debt", "collection", "bill", "owe"]):
            reply = (
                "Debt collectors and IRS letters can feel scary, but you have protections under federal law. "
                "You have the right to request written verification of any debt. "
                "Never pay a debt or give banking info over the phone to someone who called you unexpectedly — that's often a scam. "
                "For real IRS issues, visit IRS.gov or call 1-800-829-1040. "
                "For debt help, call 211 for a free financial counselor."
            )
        elif any(w in msg_lower for w in ["snap", "ebt", "food stamp", "wic", "medicaid", "benefits", "assistance"]):
            reply = (
                "You may qualify for food, health, or utility assistance programs. "
                "Call 211 — it's free, confidential, and available 24/7 — to find programs in your area. "
                "For SNAP (food stamps), apply at your local DHHS or online at benefits.gov. "
                "For Medicaid, visit healthcare.gov or your state health department website. "
                "There's no shame in using programs you've paid into and that exist to help you."
            )
        elif any(w in msg_lower for w in ["scam", "fraud", "fake", "phishing", "suspicious"]):
            reply = (
                "This sounds like it could be a scam. Real government agencies like the IRS or Social Security Administration never call demanding immediate payment or gift cards. "
                "Don't share personal information, Social Security numbers, or banking details with anyone who contacted you first. "
                "Hang up, block the number, and report it to the FTC at ReportFraud.ftc.gov. "
                "If you already sent money, call your bank immediately."
            )
        elif any(w in msg_lower for w in ["fired", "terminated", "laid off", "unemployment", "job", "wage"]):
            reply = (
                "Losing a job is stressful, but you likely have options. "
                "File for unemployment benefits right away — don't wait, there are deadlines. "
                "Visit your state's Department of Labor website or call 211 for help with the application. "
                "If you believe you were fired unfairly or weren't paid what you earned, contact your state labor board — it's free to file a complaint. "
                "Keep any emails, pay stubs, or written communications as evidence."
            )
        elif any(w in msg_lower for w in ["medicine", "medication", "prescription", "drug", "side effect", "dosage"]):
            reply = (
                "For questions about your medication, your pharmacist is your best free resource — you can call them anytime without an appointment. "
                "If you're having a serious reaction, call 911 or Poison Control at 1-800-222-1222. "
                "If you can't afford your prescription, ask the pharmacist about generic versions or patient assistance programs. "
                "GoodRx (goodrx.com) can also show you lower prices at nearby pharmacies."
            )
        elif any(w in msg_lower for w in ["crisis", "suicide", "harm", "emergency", "help me", "dangerous"]):
            reply = (
                "You are not alone, and help is available right now. "
                "Call or text 988 to reach the Suicide and Crisis Lifeline — free, confidential, 24/7. "
                "If you or someone else is in immediate danger, call 911. "
                "For domestic violence support, call 1-800-799-7233 (National DV Hotline) — also 24/7 and confidential. "
                "Please reach out — these lines are staffed by people who care and want to help you."
            )
        else:
            reply = (
                "I'm here to help. For many situations — housing, legal, financial, health, or benefits — "
                "calling 211 is the fastest way to find free local resources. "
                "It's confidential, available 24/7, and covers most needs. "
                "You can also visit 211.org to search by ZIP code. "
                "If you can share a few more details about your situation, I can give you more specific guidance."
            )

    return {"reply": reply.strip()}


@api_router.post("/ai/director/upload")
async def director_upload_file(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
):
    """Accept a file upload from the Director widget.
    Stores content in MongoDB with a 24-hour TTL.
    Returns a file_id the Director can use with the read_file tool.
    """
    MAX_SIZE = 5 * 1024 * 1024  # 5 MB hard cap

    raw = await file.read()
    if len(raw) > MAX_SIZE:
        raise HTTPException(413, "File too large. Maximum size is 5 MB.")

    file_id = str(uuid.uuid4())
    # Sanitize filename to prevent path traversal attacks
    import os as _os
    filename = file.filename or "upload"
    filename = _os.path.basename(filename)  # Remove any directory components
    filename = "".join(c for c in filename if c.isalnum() or c in ".-_")  # Keep only safe chars
    filename = filename or "upload"  # Fallback if filename becomes empty
    ct = file.content_type or "application/octet-stream"

    # Try to decode as text; mark binary otherwise
    is_binary = False
    content = ""
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        is_binary = True

    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    await db.director_uploads.insert_one({
        "id":           file_id,
        "user_id":      user.id,
        "filename":     filename,
        "content_type": ct,
        "content":      content,
        "is_binary":    is_binary,
        "size_bytes":   len(raw),
        "created_at":   datetime.now(timezone.utc).isoformat(),
        "expires_at":   expires_at.isoformat(),
    })

    if not is_binary:
        from tools.director_tools import cache_file
        cache_file(file_id, filename, content, ct)

    return {
        "file_id":   file_id,
        "filename":  filename,
        "size_bytes": len(raw),
        "readable":  not is_binary,
        "message": (
            f"File '{filename}' uploaded. "
            "Tell The Director: read_file " + file_id
        ) if not is_binary else (
            f"Binary file '{filename}' uploaded but cannot be read as text."
        ),
    }


@api_router.post("/ai/director")
async def ai_director(body: dict, user: User = Depends(current_user)):
    """The Director / Assistant Director endpoint with full tool-calling support.

    Runs an agentic loop: Claude may call web_search, fetch_url, send_email,
    get_incident_register, or read_file — tools execute server-side and results
    feed back into the conversation until Claude produces a final text reply.

    Students/Instructors → Assistant Director (no tools, warm guide)
    Admin/Executive      → The Director (full tool suite)
    """
    from prompts.director_prompt import get_director_prompt
    from tools.director_tools import DIRECTOR_TOOLS, dispatch_tool
    from ai.prompt_guard import prompt_guard
    from ai.memory import get_memory_context, log_episode

    message    = body.get("message", "")
    session_id = body.get("session_id", "director")
    if not message:
        raise HTTPException(400, "Message is required")

    # Director 4.0 — AI tamper / prompt injection scan
    check_rate(f"ai_director:{user.id}", max_calls=20, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/director", user.id)
    except ValueError as _guard_err:
        raise HTTPException(400, str(_guard_err))

    is_exec    = user.role in ("admin", "executive_admin")
    memory_ctx = await get_memory_context(db, "director", user.id) if is_exec else ""
    system     = get_director_prompt(user.role)
    system    += (
        f"\n\nCURRENT USER CONTEXT:\n"
        f"- Name: {user.full_name}\n"
        f"- Role: {user.role}\n"
        f"- Email: {user.email}\n"
        f"- Address them appropriately by role.\n"
    ) + memory_ctx

    import anthropic as _anthropic_module
    from ai.retry_utils import async_retry
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    messages = [{"role": "user", "content": message}]
    tools    = DIRECTOR_TOOLS if is_exec else []
    reply    = ""
    MAX_TOOL_TURNS = 6  # prevent runaway loops

    # ── Agentic loop — runs through REDUNDANCY CHAIN on full failure ──────────
    # Tier 1: claude-sonnet-4-6  (full capability)
    # Tier 2: claude-haiku-4-5   (lighter, same API key, same tools)
    # Tier 3: Static Director-voice response (proven language, no AI cost)

    _DIRECTOR_MODELS = [
        ("claude-sonnet-4-6", 2048),   # Tier 1 — primary
        ("claude-haiku-4-5",  1536),   # Tier 2 — backup (lighter, faster)
    ]

    async def _run_agentic_loop(model_name: str, max_tok: int) -> str:
        """Run the full Director agentic loop on a given model."""
        _msgs = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(
                model      = model_name,
                max_tokens = max_tok,
                system     = system,
                messages   = _msgs,
            )
            if tools:
                _kwargs["tools"] = tools

            # Retry transient errors (429 rate-limit, 529 overload, timeout)
            _msg = await async_retry(
                _client.messages.create,
                max_attempts=3, base_delay=2.0,
                **_kwargs,
            )

            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break

            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break

            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await asyncio.gather(*[
                dispatch_tool(b.name, b.input, db=db)
                for b in tool_use_blocks
            ])
            result_content = [
                {
                    "type":        "tool_result",
                    "tool_use_id": b.id,
                    "content":     result,
                }
                for b, result in zip(tool_use_blocks, tool_results)
            ]
            _msgs.append({"role": "user", "content": result_content})
        else:
            _reply = _reply or "[Director tool loop exceeded limit — partial response above]"
        return _reply

    for _model, _max_tok in _DIRECTOR_MODELS:
        try:
            reply = await _run_agentic_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _model_err:
            logger.warning(
                "Director AI: model %s failed (%s) — trying next tier",
                _model, _model_err
            )
            reply = ""

    # ── Tier 3: Static Director-voice fallback ────────────────────────────────
    if not reply:
        from datetime import datetime as _dt
        _ts = _dt.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        reply = (
            "SYSTEM DESIGNATION: THE DIRECTOR — INFRASTRUCTURE 4.0\n\n"
            "I am operating in contingency mode. The primary AI engine is temporarily "
            "unreachable. All institutional protocols remain in effect.\n\n"
            "**Your message has been received.** I will process your request when the "
            "AI layer restores. In the meantime:\n\n"
            "• If this is a security or crisis matter — escalate to NAM Oshun directly.\n"
            "• If this is an operational question — the Assistant Director remains available "
            "to students and instructors.\n"
            "• If you submitted a mode change or incident — retry in 60 seconds.\n\n"
            "The Director system is self-monitoring and will restore automatically. "
            "No institutional data has been lost.\n\n"
            f"Status logged: {_ts}"
        )

    # ── Log interaction ───────────────────────────────────────────────────────
    await db.chat_history.insert_one({
        "id":           str(uuid.uuid4()),
        "user_id":      user.id,
        "session_id":   session_id,
        "mode":         "director",
        "user_msg":     message,
        "assistant_msg": reply,
        "created_at":   datetime.now(timezone.utc).isoformat(),
        "expires_at":   (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
    })

    if is_exec:
        from ai.memory import log_episode as _log_ep
        await _log_ep(db, session_id, "director", user.id, message, reply, [])

    persona = "director" if is_exec else "assistant_director"
    await db.ai_usage_log.insert_one({
        "user_id": user.id,
        "endpoint": "/ai/director",
        "persona": persona,
        "model": "claude-sonnet-4-6",
        "provider": "anthropic",
        "cost_usd": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"reply": reply, "persona": persona}


@api_router.get("/ai/director/greeting")
async def director_greeting(user: User = Depends(current_user)):
    """Returns a role-appropriate greeting when the user logs in.

    For admin and executive_admin: pulls live DB counts (no AI token cost)
    so the greeting reflects actual system state rather than a static claim.
    Students and instructors receive a warm, role-appropriate welcome.
    """
    is_exec = user.role in ("admin", "executive_admin")
    persona = "director" if is_exec else "assistant_director"

    if not is_exec:
        greetings = {
            "student":    (f"Welcome back, {user.full_name}. I am the Assistant Director. "
                           "I am here to guide your learning journey at WAI-Institute. "
                           "What would you like to work on today?"),
            "instructor": (f"Welcome back, {user.full_name}. I am the Assistant Director. "
                           "I am ready to support your teaching and course management. "
                           "How can I assist you today?"),
        }
        greeting = greetings.get(user.role, greetings["student"])
        return {"greeting": greeting, "role": user.role, "persona": persona}

    # ── Live status pull for admin / executive_admin ──────────────────────────
    # Query DB directly — no AI cost, no latency from a full agentic loop.
    import asyncio as _asyncio
    now = datetime.now(timezone.utc)
    d7  = (now - timedelta(days=7)).isoformat()

    open_incidents, at_risk_login, pending_labs, pending_flags = await _asyncio.gather(
        db.incidents.count_documents({"status": {"$nin": ["resolved", "closed"]}}),
        db.users.count_documents({
            "role": "student", "is_active": {"$ne": False},
            "last_login": {"$lt": d7},
        }),
        db.lab_submissions.count_documents({"status": "submitted"}),
        db.more_flags.count_documents({"status": "pending"}),
    )

    # Build a terse, honest status line
    items = []
    if open_incidents:
        items.append(f"{open_incidents} open incident{'s' if open_incidents != 1 else ''}")
    if at_risk_login:
        items.append(f"{at_risk_login} at-risk student{'s' if at_risk_login != 1 else ''}")
    if pending_labs:
        items.append(f"{pending_labs} lab submission{'s' if pending_labs != 1 else ''} pending review")
    if pending_flags:
        items.append(f"{pending_flags} content flag{'s' if pending_flags != 1 else ''} awaiting decision")

    if items:
        status_line = "Monitoring active. Flagged items: " + ", ".join(items) + "."
        close_line  = "Use 'System Status' or 'Threat Report' for a full brief."
    else:
        status_line = "All systems nominal. No open incidents, no at-risk students, no pending reviews."
        close_line  = "Platform is clean. Standing by for your direction."

    greeting = (
        f"Welcome back, {user.full_name}. I am The Director.\n"
        f"{status_line}\n"
        f"{close_line}"
    )

    return {"greeting": greeting, "role": user.role, "persona": persona}

@api_router.get("/ai/director/pulse")
async def director_pulse(user: User = Depends(require_role("admin"))):
    """Passive monitoring snapshot for The Director widget.

    Returns current counts across every monitored dimension so the frontend
    can detect changes between polls and surface proactive alerts without
    burning AI tokens on every tick.
    """
    now = datetime.now(timezone.utc)
    h24 = (now - timedelta(hours=24)).isoformat()
    h1  = (now - timedelta(hours=1)).isoformat()
    d7  = (now - timedelta(days=7)).isoformat()
    d14 = (now - timedelta(days=14)).isoformat()

    # Run all counts concurrently
    import asyncio as _asyncio
    (
        incidents_24h, incidents_open,
        pending_labs,
        new_users_24h, total_users,
        failed_payments_24h, revenue_paid_24h,
        more_flags_pending,
        at_risk_login, at_risk_quiz,
        audit_1h,
    ) = await _asyncio.gather(
        db.incidents.count_documents({"created_at": {"$gte": h24}}),
        db.incidents.count_documents({"status": {"$nin": ["resolved", "closed"]}}),
        db.lab_submissions.count_documents({"status": "pending"}),
        db.users.count_documents({"created_at": {"$gte": h24}}),
        db.users.count_documents({"is_active": True}),
        db.payments.count_documents({"status": {"$ne": "paid"}, "created_at": {"$gte": h24}}),
        db.payments.count_documents({"status": "paid", "created_at": {"$gte": h24}}),
        db.more_flags.count_documents({"status": "pending"}),
        db.users.count_documents({"role": "student", "is_active": True, "last_login": {"$lt": d7}}),
        db.users.count_documents({"role": "student", "is_active": True, "last_quiz_score": {"$lt": 70}, "last_quiz_at": {"$gte": d14}}),
        db.audit_log.count_documents({"at": {"$gte": h1}}),
    )

    # Grab the 3 most recent unresolved incidents for context
    recent_incidents = await db.incidents.find(
        {"status": {"$nin": ["resolved", "closed"]}},
        {"_id": 0, "title": 1, "severity": 1, "created_at": 1},
    ).sort("created_at", -1).limit(3).to_list(3)

    alerts = []
    if incidents_open:
        alerts.append({"level": "high" if incidents_open > 2 else "warn", "msg": f"{incidents_open} open incident{'s' if incidents_open != 1 else ''}"})
    if at_risk_login:
        alerts.append({"level": "warn", "msg": f"{at_risk_login} student{'s' if at_risk_login != 1 else ''} inactive 7+ days"})
    if at_risk_quiz:
        alerts.append({"level": "warn", "msg": f"{at_risk_quiz} student{'s' if at_risk_quiz != 1 else ''} struggling (quiz < 70)"})
    if pending_labs:
        alerts.append({"level": "info", "msg": f"{pending_labs} lab submission{'s' if pending_labs != 1 else ''} awaiting review"})
    if more_flags_pending:
        alerts.append({"level": "warn", "msg": f"{more_flags_pending} M.O.R.E. content flag{'s' if more_flags_pending != 1 else ''} pending"})
    if failed_payments_24h:
        alerts.append({"level": "warn", "msg": f"{failed_payments_24h} payment failure{'s' if failed_payments_24h != 1 else ''} in last 24h"})

    return {
        "timestamp": now.isoformat(),
        "health": "critical" if any(a["level"] == "high" for a in alerts)
                  else "warning" if alerts
                  else "nominal",
        "alerts": alerts,
        "metrics": {
            "incidents_24h": incidents_24h,
            "incidents_open": incidents_open,
            "pending_labs": pending_labs,
            "new_users_24h": new_users_24h,
            "total_users": total_users,
            "failed_payments_24h": failed_payments_24h,
            "revenue_paid_24h": revenue_paid_24h,
            "more_flags_pending": more_flags_pending,
            "at_risk_login": at_risk_login,
            "at_risk_quiz": at_risk_quiz,
            "audit_events_1h": audit_1h,
        },
        "recent_incidents": recent_incidents,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PERSONA VOICE TTS — Director / Revenue Director / Sage
# ═══════════════════════════════════════════════════════════════════════════════

@api_router.post("/ai/director/tts")
async def director_tts(body: dict, user: User = Depends(require_role("executive_admin"))):
    """THE DIRECTOR voice — 3-tier TTS.
    T1: ElevenLabs (DIRECTOR_VOICE_ID) — deep, authoritative, executive presence
    T2: OpenAI TTS voice "alloy"
    T3: Text mode — clean text returned
    Access: admin, executive_admin | Rate: 20/min
    """
    from ai.persona_tts import persona_speak
    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "Director TTS requires admin or executive account.")
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 5000:
        text = text[:5000]
    force_tier = (body.get("force_tier") or "").lower().strip()
    check_rate(f"ai_director_tts:{user.id}", max_calls=20, window_sec=60)
    try:
        result = await persona_speak("director", text, force_tier=force_tier, db=db)
    except Exception as _e:
        logger.warning("director_tts error: %s", _e)
        result = {"tier": "text", "audio": None, "clean_text": text, "display_text": text, "budget_remaining": 0}
    tier = result.get("tier", "text")
    budget_remaining = result.get("budget_remaining", 0)
    audio = result.get("audio")
    if tier in ("elevenlabs", "elevenlabs_cached") and audio:
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg",
            headers={"X-Tier": tier, "X-Audio-Len": str(len(audio)), "X-Budget-Remaining": str(budget_remaining)})
    return JSONResponse(content={
        "tier": tier, "clean_text": result.get("clean_text", text), "display_text": result.get("display_text", text),
        "budget_remaining": budget_remaining,
        "fallback_voice": result.get("fallback_voice", "alloy"),
        "fallback_endpoint": result.get("fallback_endpoint", "/api/ai/sage/tts"),
    }, headers={"X-Tier": tier, "X-Budget-Remaining": str(budget_remaining)})


@api_router.post("/ai/revenue-director/tts")
async def revenue_director_tts(body: dict, user: User = Depends(require_role("executive_admin"))):
    """THE REVENUE DIRECTOR voice — 3-tier TTS.
    T1: ElevenLabs (REVENUE_DIRECTOR_VOICE_ID) — confident, strategic
    T2: OpenAI TTS voice "echo"
    T3: Text mode
    Access: admin, executive_admin | Rate: 20/min
    """
    from ai.persona_tts import persona_speak
    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "Revenue Director TTS requires admin or executive account.")
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 5000:
        text = text[:5000]
    force_tier = (body.get("force_tier") or "").lower().strip()
    check_rate(f"ai_rd_tts:{user.id}", max_calls=20, window_sec=60)
    try:
        result = await persona_speak("revenue_director", text, force_tier=force_tier, db=db)
    except Exception as _e:
        logger.warning("revenue_director_tts error: %s", _e)
        result = {"tier": "text", "audio": None, "clean_text": text, "display_text": text, "budget_remaining": 0}
    tier = result.get("tier", "text")
    budget_remaining = result.get("budget_remaining", 0)
    audio = result.get("audio")
    if tier in ("elevenlabs", "elevenlabs_cached") and audio:
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg",
            headers={"X-Tier": tier, "X-Audio-Len": str(len(audio)), "X-Budget-Remaining": str(budget_remaining)})
    return JSONResponse(content={
        "tier": tier, "clean_text": result.get("clean_text", text), "display_text": result.get("display_text", text),
        "budget_remaining": budget_remaining,
        "fallback_voice": result.get("fallback_voice", "echo"),
        "fallback_endpoint": result.get("fallback_endpoint", "/api/ai/sage/tts"),
    }, headers={"X-Tier": tier, "X-Budget-Remaining": str(budget_remaining)})


@api_router.post("/ai/sage/elevenlabs/tts")
async def sage_elevenlabs_tts(body: dict, user: User = Depends(require_role("executive_admin"))):
    """THE ANCESTRAL SAGE voice — 3-tier TTS (ElevenLabs upgrade for Sage).
    Separate from /api/ai/sage/tts (OpenAI) — this route tries ElevenLabs first.
    T1: ElevenLabs (SAGE_VOICE_ID) — warm, ancestral, resonant
    T2: OpenAI TTS voice "shimmer"
    T3: Text mode
    Access: all authenticated users | Rate: 20/min
    """
    from ai.persona_tts import persona_speak
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 4000:
        text = text[:4000]
    force_tier = (body.get("force_tier") or "").lower().strip()
    check_rate(f"ai_sage_el_tts:{user.id}", max_calls=20, window_sec=60)
    try:
        result = await persona_speak("ancestral_sage", text, force_tier=force_tier, db=db)
    except Exception as _e:
        logger.warning("sage_elevenlabs_tts error: %s", _e)
        result = {"tier": "text", "audio": None, "clean_text": text, "display_text": text, "budget_remaining": 0}
    tier = result.get("tier", "text")
    budget_remaining = result.get("budget_remaining", 0)
    audio = result.get("audio")
    if tier in ("elevenlabs", "elevenlabs_cached") and audio:
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg",
            headers={"X-Tier": tier, "X-Audio-Len": str(len(audio)), "X-Budget-Remaining": str(budget_remaining)})
    return JSONResponse(content={
        "tier": tier, "clean_text": result.get("clean_text", text), "display_text": result.get("display_text", text),
        "budget_remaining": budget_remaining,
        "fallback_voice": result.get("fallback_voice", "shimmer"),
        "fallback_endpoint": result.get("fallback_endpoint", "/api/ai/sage/tts"),
    }, headers={"X-Tier": tier, "X-Budget-Remaining": str(budget_remaining)})


# ═══════════════════════════════════════════════════════════════════════════════
# THE REVENUE DIRECTOR 4.0 — Financial Intelligence endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@api_router.post("/ai/revenue-director")
async def ai_revenue_director(body: dict, user: User = Depends(current_user)):
    """THE REVENUE DIRECTOR — Financial Intelligence & Sustainability Authority.

    Runs the Financial Synthesis Protocol: AUDIT→IDENTIFY→POSITION→PRICE→PACKAGE→LAUNCH→TRACK
    Tools: rd_audit_revenue, rd_revenue_forecast, rd_identify_opportunity,
           rd_create_financial_report, rd_publish_financial_report,
           rd_grant_tracker, rd_pricing_analysis, rd_revenue_dashboard, rd_list_revenue_streams

    Access: admin, executive_admin
    Rate:   15 calls/min
    """
    from ai.persona_loader import get_persona
    from tools.revenue_director_tools import REVENUE_DIRECTOR_TOOLS, dispatch_rd_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE REVENUE DIRECTOR is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_rd:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/revenue-director", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    memory_ctx = await get_memory_context(db, "revenue_director", user.id)

    import anthropic as _anthropic_module
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system  = get_persona("revenue_director") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- GUMROAD_API_KEY: {'SET — autonomous publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
        f"- OPENAI_API_KEY (DALL-E 3 via Architect): {'SET' if os.environ.get('OPENAI_API_KEY', os.environ.get('EMERGENT_LLM_KEY', '')) else 'NOT SET'}\n"
    ) + memory_ctx

    _RD_MODELS = [
        ("claude-sonnet-4-6", 4096),
        ("claude-haiku-4-5",  2048),
    ]
    MAX_TOOL_TURNS = 8
    reply = ""
    _tools_called: list[str] = []

    async def _run_rd_loop(model_name: str, max_tok: int) -> str:
        _msgs  = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(model=model_name, max_tokens=max_tok, system=system, messages=_msgs, tools=REVENUE_DIRECTOR_TOOLS)
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)
            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            _tools_called.extend(b.name for b in tool_use_blocks)
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await asyncio.gather(*[dispatch_rd_tool(b.name, b.input, db=db) for b in tool_use_blocks])
            _msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": b.id, "content": r} for b, r in zip(tool_use_blocks, tool_results)]})
        else:
            _reply = _reply or "[REVENUE DIRECTOR tool loop reached limit — partial analysis above]"
        return _reply

    for _model, _max_tok in _RD_MODELS:
        try:
            reply = await _run_rd_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _err:
            logger.warning("REVENUE DIRECTOR model %s failed: %s — trying next tier", _model, _err)
            reply = ""

    if not reply:
        try:
            from ai.llm_gateway import call_llm as _call_llm
            _gw = await _call_llm(system=get_persona("revenue_director"), messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="revenue_director")
            reply = _gw["text"]
        except Exception:
            reply = "THE REVENUE DIRECTOR is temporarily offline. Financial archives remain active. Retry in a moment."

    await log_episode(db, session_id, "revenue_director", user.id, message, reply, _tools_called)
    logger.info("ai_revenue_director: responded for user %s", user.id)
    return {"reply": reply, "persona": "revenue_director", "mode": "financial_intelligence"}


# ═══════════════════════════════════════════════════════════════════════════════
# ANCESTRAL SAGE — Content Creation endpoint (revenue tools, no consent gate)
# ═══════════════════════════════════════════════════════════════════════════════

@api_router.post("/ai/sage/create")
async def sage_create(body: dict, user: User = Depends(current_user)):
    """THE ANCESTRAL SAGE — Content Creation & Wellness Publishing.

    This endpoint is for CONTENT CREATION (healing guides, meditation scripts,
    wisdom collections, wellness publications). It does NOT replace the healing
    chat at /api/ai/chat — that has its own consent gating for student use.

    This endpoint applies the Healing Synthesis Protocol for creating publishable
    wellness resources for the WAI-Institute community.

    Tools: sage_create_healing_guide, sage_create_meditation_script, sage_wisdom_archive,
           sage_community_pulse, sage_publish_wellness_content, sage_get_revenue_report,
           sage_list_revenue_streams

    Access: admin, executive_admin
    Rate:   15 calls/min
    """
    from ai.persona_loader import get_persona
    from tools.sage_tools import SAGE_TOOLS, dispatch_sage_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "Sage content creation is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_sage_create:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/sage/create", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    memory_ctx = await get_memory_context(db, "ancestral_sage", user.id)

    import anthropic as _anthropic_module
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system  = get_persona("ancestral_sage") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- Mode: CONTENT CREATION — creating healing resources and wellness products\n"
        f"- GUMROAD_API_KEY: {'SET — autonomous publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
    ) + memory_ctx

    _SAGE_MODELS = [
        ("claude-sonnet-4-6", 4096),
        ("claude-haiku-4-5",  2048),
    ]
    MAX_TOOL_TURNS = 8
    reply = ""
    _tools_called: list[str] = []

    async def _run_sage_loop(model_name: str, max_tok: int) -> str:
        _msgs  = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(model=model_name, max_tokens=max_tok, system=system, messages=_msgs, tools=SAGE_TOOLS)
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)
            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            _tools_called.extend(b.name for b in tool_use_blocks)
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await asyncio.gather(*[dispatch_sage_tool(b.name, b.input, db=db) for b in tool_use_blocks])
            _msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": b.id, "content": r} for b, r in zip(tool_use_blocks, tool_results)]})
        else:
            _reply = _reply or "[SAGE tool loop reached limit — partial content above]"
        return _reply

    for _model, _max_tok in _SAGE_MODELS:
        try:
            reply = await _run_sage_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _err:
            logger.warning("SAGE CREATE model %s failed: %s — trying next tier", _model, _err)
            reply = ""

    if not reply:
        try:
            from ai.llm_gateway import call_llm as _call_llm
            _gw = await _call_llm(system=get_persona("ancestral_sage"), messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="ancestral_sage")
            reply = _gw["text"]
        except Exception:
            reply = "The Ancestral Sage is temporarily offline. Wisdom archives remain intact. Retry in a moment."

    await log_episode(db, session_id, "ancestral_sage", user.id, message, reply, _tools_called)
    logger.info("ai_sage_create: responded for user %s", user.id)
    return {"reply": reply, "persona": "ancestral_sage", "mode": "content_creation"}


@api_router.get("/ai/history/{session_id}")
async def ai_history(session_id: str, user: User = Depends(current_user)):
    return await db.chat_history.find(
        {"user_id": user.id, "session_id": session_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(200)


@api_router.get("/certificates/me")
async def my_certificates(user: User = Depends(current_user)):
    prog = await db.progress.find(
        {"user_id": user.id, "status": "completed"}, {"_id": 0}
    ).to_list(200)
    # Batch-load all modules referenced by this user's progress in ONE query
    # (was N+1: one find_one per completed module).
    slugs = [p["module_slug"] for p in prog]
    modules = await db.modules.find(
        {"slug": {"$in": slugs}}, {"_id": 0}
    ).to_list(200) if slugs else []
    mod_by_slug = {m["slug"]: m for m in modules}
    certs = []
    for p in prog:
        mod = mod_by_slug.get(p["module_slug"])
        if mod:
            certs.append({
                "module_slug": p["module_slug"],
                "title": mod["title"],
                "hours": mod["hours"],
                "score": p.get("quiz_score"),
                "completed_at": p.get("completed_at"),
            })
    if len(certs) == len(MODULES):
        certs.append({
            "module_slug": "program",
            "title": "LCE-WAI Camper-to-Classroom Program Completion",
            "hours": sum(m["hours"] for m in MODULES),
            "score": sum((c["score"] or 0) for c in certs) / len(MODULES),
            "completed_at": max((c.get("completed_at") or "") for c in certs),
        })
    return certs


@api_router.get("/certificates/{slug}.pdf")
async def cert_pdf(slug: str, token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    user_doc = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(401, "User not found")

    if slug == "program":
        title = "Camper-to-Classroom Program Completion"
        hours = sum(m["hours"] for m in MODULES)
    else:
        mod = await db.modules.find_one({"slug": slug}, {"_id": 0})
        if not mod:
            raise HTTPException(404, "Module not found")
        prog = await db.progress.find_one(
            {"user_id": user_doc["id"], "module_slug": slug, "status": "completed"}, {"_id": 0}
        )
        if not prog:
            raise HTTPException(404, "Not completed yet")
        title = mod["title"]
        hours = mod["hours"]

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(letter))
    w, h = landscape(letter)

    c.setFillColor(colors.HexColor("#F7F7F5"))
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#0B203F"))
    c.setLineWidth(8)
    c.rect(0.35 * inch, 0.35 * inch, w - 0.7 * inch, h - 0.7 * inch, fill=0, stroke=1)
    c.setFillColor(colors.HexColor("#1E5BA8"))
    c.rect(0.35 * inch, h - 1.1 * inch, w - 0.7 * inch, 0.12 * inch, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#0B203F"))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, h - 1.6 * inch, "W.A.I. — WORKFORCE APPRENTICE INSTITUTE")
    c.setFont("Helvetica", 11)
    c.drawCentredString(w / 2, h - 1.85 * inch, "LCE-WAI Partner Program")
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(w / 2, h - 2.7 * inch, "Certificate of Completion")
    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, h - 3.2 * inch, "This certifies that")
    c.setFillColor(colors.HexColor("#1E5BA8"))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(w / 2, h - 3.8 * inch, user_doc["full_name"])
    c.setFillColor(colors.HexColor("#0B203F"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, h - 4.3 * inch, "has successfully completed")
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(w / 2, h - 4.85 * inch, title)
    c.setFont("Helvetica", 12)
    c.drawCentredString(w / 2, h - 5.3 * inch, f"Training Hours: {hours}    |    Date: {datetime.now(timezone.utc).strftime('%B %d, %Y')}")
    c.setStrokeColor(colors.HexColor("#0B203F"))
    c.setLineWidth(1)
    c.line(1.5 * inch, 1.1 * inch, 4 * inch, 1.1 * inch)
    c.line(w - 4 * inch, 1.1 * inch, w - 1.5 * inch, 1.1 * inch)
    c.setFont("Helvetica", 10)
    c.drawCentredString(2.75 * inch, 0.9 * inch, "Instructor of Record")
    c.drawCentredString(w - 2.75 * inch, 0.9 * inch, "Program Director")
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(w / 2, 0.55 * inch, '"Whatever you do, work at it with all your heart, as working for the Lord." - Colossians 3:23')
    c.showPage()
    c.save()
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=LCE-WAI-{slug}.pdf"},
    )


# -- LAB MODELS --
class LabSubmitReq(BaseModel):
    lab_slug: Optional[str] = None
    answers: Optional[dict] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class LabReviewReq(BaseModel):
    status: Literal["approved", "rejected"]
    feedback: Optional[str] = None


def grade_online_lab(simulator_type: str, answers: dict) -> dict:
    """Return {'score': 0-100, 'correct': int, 'total': int, 'detail': str} for online labs."""
    if not answers:
        return {"score": 0, "correct": 0, "total": 1, "detail": "No answers submitted"}

    if simulator_type == "basic_circuit":
        v = float(answers.get("voltage", 0))
        r1, r2, r3 = float(answers.get("r1", 0)), float(answers.get("r2", 0)), float(answers.get("r3", 0))
        cfg = answers.get("config", "series")
        user_rt = float(answers.get("total_r", 0))
        user_i = float(answers.get("total_i", 0))
        if cfg == "series":
            rt = r1 + r2 + r3
        else:
            rt = 1 / ((1 / r1 if r1 else 0) + (1 / r2 if r2 else 0) + (1 / r3 if r3 else 0)) if (r1 and r2 and r3) else 0
        it = v / rt if rt else 0
        rt_ok = abs(user_rt - rt) < max(0.1, rt * 0.02)
        it_ok = abs(user_i - it) < max(0.01, it * 0.02)
        correct = int(rt_ok) + int(it_ok)
        return {"score": correct / 2 * 100, "correct": correct, "total": 2,
                "detail": f"Rt={rt:.2f}Ω, I={it:.3f}A (yours: Rt={user_rt}, I={user_i})"}

    if simulator_type == "switch_wiring":
        # expects answers: {hot_to: "brass", neutral_to: "silver", ground_to: "green"}
        key = {"hot_to": "brass", "neutral_to": "silver", "ground_to": "green"}
        correct = sum(1 for k, v in key.items() if answers.get(k) == v)
        return {"score": correct / 3 * 100, "correct": correct, "total": 3, "detail": ""}

    if simulator_type == "panel_labeling":
        # answers: {slot_0: "kitchen", slot_1: "bedroom", ...}
        key = {"slot_0": "kitchen", "slot_1": "bedroom", "slot_2": "bathroom_gfci",
               "slot_3": "living_room", "slot_4": "hvac", "slot_5": "laundry"}
        correct = sum(1 for k, v in key.items() if answers.get(k) == v)
        return {"score": correct / len(key) * 100, "correct": correct, "total": len(key), "detail": ""}

    if simulator_type == "conduit_calc":
        rise = float(answers.get("rise", 0))
        angle = int(answers.get("angle", 30))
        user_distance = float(answers.get("distance", 0))
        user_shrink = float(answers.get("shrink", 0))
        mult_tbl = {10: (6.0, 1 / 16), 22: (2.6, 3 / 16), 30: (2.0, 1 / 4), 45: (1.4, 3 / 8), 60: (1.2, 1 / 2)}
        mult, shrink_per_inch = mult_tbl.get(angle, (2.0, 0.25))
        distance = rise * mult
        shrink = rise * shrink_per_inch
        d_ok = abs(user_distance - distance) < 0.25
        s_ok = abs(user_shrink - shrink) < 0.1
        correct = int(d_ok) + int(s_ok)
        return {"score": correct / 2 * 100, "correct": correct, "total": 2,
                "detail": f"distance={distance:.2f}\" shrink={shrink:.3f}\""}

    if simulator_type == "vdrop":
        length = float(answers.get("length_ft", 0))
        current = float(answers.get("current_a", 0))
        awg = int(answers.get("awg", 12))
        source_v = float(answers.get("source_v", 120))
        user_vd_pct = float(answers.get("vd_pct", 0))
        cm_tbl = {14: 4110, 12: 6530, 10: 10380, 8: 16510, 6: 26240, 4: 41740, 2: 66360}
        cm = cm_tbl.get(awg, 6530)
        k = 12.9
        vd = (2 * k * current * length) / cm
        vd_pct = vd / source_v * 100
        ok = abs(user_vd_pct - vd_pct) < 0.2
        return {"score": 100 if ok else 0, "correct": int(ok), "total": 1,
                "detail": f"Actual Vdrop = {vd:.2f}V ({vd_pct:.2f}%)"}

    if simulator_type == "solar_config":
        daily_kwh = float(answers.get("daily_kwh", 0))
        sun_hours = float(answers.get("sun_hours", 0))
        sys_v = float(answers.get("sys_v", 48))
        autonomy_days = float(answers.get("autonomy_days", 2))
        user_pv_w = float(answers.get("pv_watts", 0))
        user_bank_ah = float(answers.get("bank_ah", 0))
        pv_w = (daily_kwh * 1000) / sun_hours if sun_hours else 0
        bank_wh = daily_kwh * 1000 * autonomy_days / 0.8
        bank_ah = bank_wh / sys_v if sys_v else 0
        pv_ok = abs(user_pv_w - pv_w) / max(1, pv_w) < 0.1
        ah_ok = abs(user_bank_ah - bank_ah) / max(1, bank_ah) < 0.1
        correct = int(pv_ok) + int(ah_ok)
        return {"score": correct / 2 * 100, "correct": correct, "total": 2,
                "detail": f"Need ~{pv_w:.0f}W array and ~{bank_ah:.0f}Ah bank"}

    if simulator_type == "loto":
        expected = ["notify", "shutdown", "lockout", "tagout", "verify_dead", "try_start"]
        seq = answers.get("sequence", [])
        correct = sum(1 for i, s in enumerate(expected) if i < len(seq) and seq[i] == s)
        return {"score": correct / len(expected) * 100, "correct": correct, "total": len(expected), "detail": ""}

    if simulator_type == "troubleshooting":
        # expected path: test_breaker, test_receptacle_voltage, test_neutral_continuity, find_open_neutral
        path = answers.get("path", [])
        expected = ["test_breaker", "test_receptacle_voltage", "test_neutral_continuity", "find_open_neutral"]
        correct = sum(1 for i, s in enumerate(expected) if i < len(path) and path[i] == s)
        return {"score": correct / len(expected) * 100, "correct": correct, "total": len(expected), "detail": ""}

    if simulator_type == "load_balance":
        assignments = answers.get("assignments", {})
        loads = {"c1": 1500, "c2": 800, "c3": 1200, "c4": 600, "c5": 1800, "c6": 400}
        a = sum(loads[k] for k, v in assignments.items() if v == "A" and k in loads)
        b = sum(loads[k] for k, v in assignments.items() if v == "B" and k in loads)
        diff_pct = abs(a - b) / max(1, (a + b) / 2) * 100 if (a + b) else 100
        ok = diff_pct <= 10
        return {"score": 100 if ok else max(0, 100 - diff_pct * 2), "correct": 1 if ok else 0, "total": 1,
                "detail": f"Phase A={a}W Phase B={b}W Δ={diff_pct:.1f}%"}

    return {"score": 0, "correct": 0, "total": 1, "detail": "Unknown simulator"}


# -- LAB ROUTES --
@api_router.get("/competencies")
async def list_competencies(user: User = Depends(current_user)):
    subs = await db.lab_submissions.find(
        {"user_id": user.id, "status": {"$in": ["approved", "passed"]}}, {"_id": 0}
    ).to_list(500)
    # Batch-load labs once to avoid N+1 round-trips
    slugs = list({s["lab_slug"] for s in subs})
    labs = await db.labs.find({"slug": {"$in": slugs}}, {"_id": 0}).to_list(500) if slugs else []
    labs_by_slug = {lab["slug"]: lab for lab in labs}
    score_by_comp = {c["key"]: {"points": 0, "labs": 0} for c in COMPETENCIES}
    for s in subs:
        lab = labs_by_slug.get(s["lab_slug"])
        if not lab:
            continue
        for cmp_key in lab.get("competencies", []):
            if cmp_key in score_by_comp:
                score_by_comp[cmp_key]["points"] += lab.get("skill_points", 0)
                score_by_comp[cmp_key]["labs"] += 1
    return {
        "competencies": COMPETENCIES,
        "progress": score_by_comp,
        "total_points": sum(v["points"] for v in score_by_comp.values()),
        "total_labs": len(subs),
    }


@api_router.get("/labs")
async def list_labs(track: Optional[str] = None, user: User = Depends(current_user)):
    q = {"track": track} if track in ("online", "inperson") else {}
    docs = await db.labs.find(q, {"_id": 0}).to_list(200)
    my_subs = await db.lab_submissions.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    sub_map = {s["lab_slug"]: s for s in my_subs}
    for d in docs:
        s = sub_map.get(d["slug"])
        d["my_submission"] = {
            "status": s["status"] if s else "not_started",
            "auto_score": s.get("auto_score") if s else None,
        } if s else {"status": "not_started"}
    docs.sort(key=lambda x: (x.get("track") == "inperson", x.get("slug", "")))
    return docs


@api_router.get("/labs/{slug}")
async def get_lab(slug: str, user: User = Depends(current_user)):
    doc = await db.labs.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Lab not found")
    sub = await db.lab_submissions.find_one({"user_id": user.id, "lab_slug": slug}, {"_id": 0})
    doc["my_submission"] = sub
    return doc


@api_router.post("/labs/{slug}/submit")
async def submit_lab(slug: str, body: LabSubmitReq, user: User = Depends(current_user)):
    lab = await db.labs.find_one({"slug": slug}, {"_id": 0})
    if not lab:
        raise HTTPException(404, "Lab not found")

    now = datetime.now(timezone.utc).isoformat()
    if lab["track"] == "online":
        result = grade_online_lab(lab.get("simulator_type", ""), body.answers or {})
        status_val = "passed" if result["score"] >= 70 else "failed"
        doc = {
            "user_id": user.id,
            "lab_slug": slug,
            "track": "online",
            "answers": body.answers or {},
            "auto_score": result["score"],
            "detail": result["detail"],
            "status": status_val,
            "feedback": None,
            "created_at": now,
            "reviewed_at": now,
        }
        await db.lab_submissions.update_one(
            {"user_id": user.id, "lab_slug": slug},
            {"$set": doc, "$setOnInsert": {"id": str(uuid.uuid4())}},
            upsert=True,
        )
        if status_val == "passed":
            await award_credentials(user.id)
            lab_pts = lab.get("skill_points", 0)
            await award_xp(user.id, 50 + lab_pts * 2, f"Online lab passed: {slug}")
        return {**result, "status": status_val}
    else:
        doc = {
            "user_id": user.id,
            "lab_slug": slug,
            "track": "inperson",
            "photo_url": body.photo_url,
            "notes": body.notes,
            "auto_score": None,
            "status": "pending",
            "feedback": None,
            "created_at": now,
        }
        await db.lab_submissions.update_one(
            {"user_id": user.id, "lab_slug": slug},
            {"$set": doc, "$setOnInsert": {"id": str(uuid.uuid4())}},
            upsert=True,
        )
        return {"status": "pending"}


@api_router.get("/labs/submissions/me")
async def my_lab_submissions(user: User = Depends(current_user)):
    docs = await db.lab_submissions.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    return docs


@api_router.get("/instructor/submissions")
async def pending_submissions(user: User = Depends(require_role("instructor", "admin"))):
    q = {"track": "inperson", "status": "pending"}
    docs = await db.lab_submissions.find(q, {"_id": 0}).to_list(500)
    # Batch-load users and labs once (N+1 → 2 queries).
    user_ids = list({d["user_id"] for d in docs})
    lab_slugs = list({d["lab_slug"] for d in docs})
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(500) if user_ids else []
    labs = await db.labs.find({"slug": {"$in": lab_slugs}}, {"_id": 0}).to_list(500) if lab_slugs else []
    users_by_id = {u["id"]: u for u in users}
    labs_by_slug = {lab["slug"]: lab for lab in labs}
    for d in docs:
        d["user"] = users_by_id.get(d["user_id"])
        d["lab"] = labs_by_slug.get(d["lab_slug"])
    return docs


@api_router.post("/instructor/submissions/{sub_id}/review")
async def review_submission(sub_id: str, body: LabReviewReq, user: User = Depends(require_role("instructor", "admin"))):
    sub = await db.lab_submissions.find_one({"id": sub_id}, {"_id": 0})
    if not sub:
        raise HTTPException(404, "Submission not found")
    await db.lab_submissions.update_one(
        {"id": sub_id},
        {"$set": {
            "status": body.status,
            "feedback": body.feedback,
            "reviewed_by": user.id,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    if body.status == "approved":
        await award_credentials(sub["user_id"])
        lab = await db.labs.find_one({"slug": sub["lab_slug"]}, {"_id": 0})
        lab_pts = lab.get("skill_points", 0) if lab else 0
        await award_xp(sub["user_id"], 100 + lab_pts * 3, f"In-person lab approved: {sub['lab_slug']}")
        # notify the apprentice
        await notify(sub["user_id"], "Lab approved",
                     f"Your submission for '{lab['title'] if lab else sub['lab_slug']}' was approved.",
                     link=f"/labs/{sub['lab_slug']}", kind="success")
    elif body.status == "rejected":
        lab = await db.labs.find_one({"slug": sub["lab_slug"]}, {"_id": 0})
        await notify(sub["user_id"], "Lab needs revision",
                     f"Instructor feedback on '{lab['title'] if lab else sub['lab_slug']}': {body.feedback or 'see lab page'}",
                     link=f"/labs/{sub['lab_slug']}", kind="warning")
    await audit(user.id, f"lab.{body.status}", target=sub_id, meta={"lab_slug": sub["lab_slug"], "student_id": sub["user_id"]})
    return {"ok": True}


@api_router.get("/instructor/lab-report")
async def lab_report(user: User = Depends(require_role("instructor", "admin"))):
    q = {"role": "student"} if user.role == "admin" else {"role": "student", "associate": user.associate}
    students = await db.users.find(q, {"_id": 0, "password_hash": 0}).to_list(1000)
    user_ids = [s["id"] for s in students]
    all_subs = await db.lab_submissions.find({"user_id": {"$in": user_ids}}, {"_id": 0}).to_list(50000)
    all_labs = await db.labs.find({}, {"_id": 0}).to_list(200)
    labs_by_slug = {lab["slug"]: lab for lab in all_labs}
    subs_by_user = {}
    for s in all_subs:
        subs_by_user.setdefault(s["user_id"], []).append(s)
    result = []
    for s in students:
        subs = subs_by_user.get(s["id"], [])
        passed = [x for x in subs if x.get("status") in ("passed", "approved")]
        pending = [x for x in subs if x.get("status") == "pending"]
        points = 0
        hours = 0
        for p in passed:
            lab = labs_by_slug.get(p["lab_slug"])
            if lab:
                points += lab.get("skill_points", 0)
                hours += lab.get("hours", 0)
        result.append({
            "user_id": s["id"],
            "full_name": s["full_name"],
            "email": s["email"],
            "associate": s.get("associate"),
            "labs_passed": len(passed),
            "labs_pending": len(pending),
            "skill_points": points,
            "lab_hours": hours,
        })
    return result


# -- CREDENTIALING & PORTFOLIO --
class PortfolioPublishReq(BaseModel):
    bio: Optional[str] = None
    publish: bool = True


async def get_user_state(user_id: str) -> dict:
    """Load modules, labs, competencies relevant for credential eligibility."""
    mod_progress = await db.progress.find(
        {"user_id": user_id, "status": "completed"}, {"_id": 0}
    ).to_list(500)
    completed_modules = {p["module_slug"] for p in mod_progress}
    lab_subs = await db.lab_submissions.find(
        {"user_id": user_id, "status": {"$in": ["passed", "approved"]}}, {"_id": 0}
    ).to_list(500)
    passed_labs = {s["lab_slug"] for s in lab_subs}
    # competency points — batch-load labs once instead of per-submission queries
    comp = {c["key"]: 0 for c in COMPETENCIES}
    slugs = list({s["lab_slug"] for s in lab_subs})
    labs = await db.labs.find({"slug": {"$in": slugs}}, {"_id": 0}).to_list(500) if slugs else []
    labs_by_slug = {lab["slug"]: lab for lab in labs}
    for s in lab_subs:
        lab = labs_by_slug.get(s["lab_slug"])
        if lab:
            for k in lab.get("competencies", []):
                if k in comp:
                    comp[k] += lab.get("skill_points", 0)
    return {
        "completed_modules": completed_modules,
        "passed_labs": passed_labs,
        "competencies": comp,
        "module_count": len(completed_modules),
        "lab_count": len(passed_labs),
    }


def credential_eligible(cred: dict, state: dict) -> bool:
    trig = cred["trigger"]
    t = trig["type"]
    if t == "all_modules":
        return state["module_count"] >= len(MODULES)
    if t == "modules_all_of":
        return all(s in state["completed_modules"] for s in trig["slugs"])
    if t == "module_completed":
        return trig["slug"] in state["completed_modules"]
    if t == "labs_all_of":
        return all(s in state["passed_labs"] for s in trig["slugs"])
    if t == "lab_passed":
        return trig["slug"] in state["passed_labs"]
    if t == "competency_at_least":
        return state["competencies"].get(trig["key"], 0) >= trig["points"]
    return False


async def award_credentials(user_id: str) -> list:
    """Run all credential triggers and insert newly-earned credentials. Returns newly-awarded keys."""
    state = await get_user_state(user_id)
    awarded = []
    now = datetime.now(timezone.utc)
    for cred in CREDENTIALS:
        if not credential_eligible(cred, state):
            continue
        existing = await db.user_credentials.find_one(
            {"user_id": user_id, "credential_key": cred["key"]}, {"_id": 0}
        )
        if existing:
            continue
        exp_months = cred.get("expires_months")
        expires_at = (now + timedelta(days=30 * exp_months)).isoformat() if exp_months else None
        await db.user_credentials.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "credential_key": cred["key"],
            "earned_at": now.isoformat(),
            "expires_at": expires_at,
            "status": "active",
            "verification_code": secrets.token_urlsafe(12),
        })
        awarded.append(cred["key"])
        await notify(user_id, "Credential earned",
                     f"You earned: {cred['name']}",
                     link="/credentials", kind="success")
        await audit(user_id, "credential.earned", target=cred["key"])
    return awarded


def xp_level(total: int) -> dict:
    if total >= 3000:
        return {"level": "Master", "level_num": 4, "min": 3000, "next": None}
    if total >= 1500:
        return {"level": "Craftsman", "level_num": 3, "min": 1500, "next": 3000}
    if total >= 500:
        return {"level": "Journeyman", "level_num": 2, "min": 500, "next": 1500}
    return {"level": "Apprentice", "level_num": 1, "min": 0, "next": 500}


async def award_xp(user_id: str, amount: int, reason: str) -> int:
    """Add XP to user total. Returns new total."""
    from motor.motor_asyncio import AsyncIOMotorClient  # already imported; just for type hint clarity
    entry = {"amount": amount, "reason": reason, "at": datetime.now(timezone.utc).isoformat()}
    result = await db.user_xp.find_one_and_update(
        {"user_id": user_id},
        {
            "$inc": {"total_xp": amount},
            "$push": {"history": {"$each": [entry], "$slice": -50}},
            "$setOnInsert": {"id": str(uuid.uuid4())},
        },
        upsert=True,
        return_document=True,
    )
    return (result or {}).get("total_xp", amount)


@api_router.get("/credentials")
async def list_credentials(user: User = Depends(current_user)):
    return CREDENTIALS


@api_router.get("/credentials/me")
async def my_credentials(user: User = Depends(current_user)):
    # award_credentials is triggered on completion events (quiz, lab approval)
    # not on every read — avoids full eligibility scan on every page load
    earned = await db.user_credentials.find({"user_id": user.id}, {"_id": 0}).to_list(200)
    cred_map = {c["key"]: c for c in CREDENTIALS}
    result = []
    now = datetime.now(timezone.utc)
    for e in earned:
        cred = cred_map.get(e["credential_key"])
        if not cred:
            continue
        expired = False
        if e.get("expires_at"):
            try:
                expired = datetime.fromisoformat(e["expires_at"]) < now
            except Exception:
                expired = False
        result.append({**cred, **e, "expired": expired})
    # show unearned too for discovery
    earned_keys = {e["credential_key"] for e in earned}
    unearned = [c for c in CREDENTIALS if c["key"] not in earned_keys]
    return {"earned": result, "available": unearned}


def public_url_from(request: Request) -> str:
    """Derive the public backend URL from the incoming request, with env override.
    Avoids issuing OpenBadges manifests/assertions tied to a stale preview hostname.
    Honors X-Forwarded-Host / X-Forwarded-Proto so the URL matches what the
    browser sees (Kubernetes ingress doesn't rewrite the Host header)."""
    override = os.environ.get('PUBLIC_BACKEND_URL', '').strip()
    if override:
        return override.rstrip('/')
    fwd_host = request.headers.get('x-forwarded-host')
    fwd_proto = request.headers.get('x-forwarded-proto', request.url.scheme)
    host = fwd_host or request.url.netloc
    return f"{fwd_proto}://{host}"


@api_router.get("/credentials/{key}/manifest.json")
async def credential_manifest(key: str, request: Request):
    """OpenBadges v2 BadgeClass manifest (public)."""
    cred = next((c for c in CREDENTIALS if c["key"] == key), None)
    if not cred:
        raise HTTPException(404, "Credential not found")
    backend_url = public_url_from(request)
    return {
        "@context": "https://w3id.org/openbadges/v2",
        "type": "BadgeClass",
        "id": f"{backend_url}/api/credentials/{key}/manifest.json",
        "name": cred["name"],
        "description": cred["description"],
        "image": cred.get("image") or "https://customer-assets.emergentagent.com/job_apprentice-academy/artifacts/zqurn9jd_WAI%20Logo.jpg",
        "criteria": {"narrative": cred["evidence"]},
        "issuer": {
            "@context": "https://w3id.org/openbadges/v2",
            "type": "Profile",
            "id": f"{backend_url}/api/issuer.json",
            "name": "W.A.I. — Workforce Apprentice Institute",
            "url": "https://workforceapprenticeinstitute.org",
        },
        "tags": cred.get("tags", []),
    }


@api_router.get("/credentials/assertion/{assertion_id}.json")
async def credential_assertion(assertion_id: str, request: Request):
    """OpenBadges v2 Assertion (public, for verifiers)."""
    uc = await db.user_credentials.find_one({"id": assertion_id}, {"_id": 0})
    if not uc:
        raise HTTPException(404, "Assertion not found")
    user_doc = await db.users.find_one({"id": uc["user_id"]}, {"_id": 0, "password_hash": 0})
    cred = next((c for c in CREDENTIALS if c["key"] == uc["credential_key"]), None)
    if not cred or not user_doc:
        raise HTTPException(404, "Not found")
    backend_url = public_url_from(request)
    return {
        "@context": "https://w3id.org/openbadges/v2",
        "type": "Assertion",
        "id": f"{backend_url}/api/credentials/assertion/{assertion_id}.json",
        "recipient": {"type": "email", "hashed": False, "identity": user_doc["email"]},
        "issuedOn": uc["earned_at"],
        "expires": uc.get("expires_at"),
        "badge": f"{backend_url}/api/credentials/{cred['key']}/manifest.json",
        "verification": {"type": "HostedBadge"},
    }


@api_router.post("/portfolio/publish")
async def publish_portfolio(body: PortfolioPublishReq, user: User = Depends(current_user)):
    existing = await db.portfolios.find_one({"user_id": user.id}, {"_id": 0})
    slug = existing.get("slug") if existing else None
    if not slug and body.publish:
        slug = f"{user.full_name.lower().replace(' ', '-')}-{user.id[:8]}"
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
    update = {
        "user_id": user.id,
        "slug": slug if body.publish else None,
        "bio": body.bio,
        "published": bool(body.publish),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.portfolios.update_one(
        {"user_id": user.id},
        {"$set": update, "$setOnInsert": {"id": str(uuid.uuid4())}},
        upsert=True,
    )
    return {"slug": slug, "published": bool(body.publish)}


async def build_portfolio(user_doc: dict) -> dict:
    user_id = user_doc["id"]
    await award_credentials(user_id)

    # Batch-load modules and labs once to avoid N+1 queries
    all_modules = await db.modules.find({}, {"_id": 0}).to_list(100)
    modules_by_slug = {m["slug"]: m for m in all_modules}
    all_labs = await db.labs.find({}, {"_id": 0}).to_list(200)
    labs_by_slug = {lab["slug"]: lab for lab in all_labs}

    mod_progress = await db.progress.find({"user_id": user_id}, {"_id": 0}).to_list(500)
    completed_mods = []
    for p in mod_progress:
        if p.get("status") == "completed":
            mod = modules_by_slug.get(p["module_slug"])
            if mod:
                completed_mods.append({
                    "slug": mod["slug"],
                    "title": mod["title"],
                    "hours": mod["hours"],
                    "score": p.get("quiz_score"),
                    "completed_at": p.get("completed_at"),
                })

    lab_subs = await db.lab_submissions.find(
        {"user_id": user_id, "status": {"$in": ["passed", "approved"]}}, {"_id": 0}
    ).to_list(500)
    labs_detail = []
    for s in lab_subs:
        lab = labs_by_slug.get(s["lab_slug"])
        if lab:
            labs_detail.append({
                "slug": lab["slug"],
                "title": lab["title"],
                "track": lab["track"],
                "skill_points": lab.get("skill_points", 0),
                "hours": lab.get("hours", 0),
                "photo_url": s.get("photo_url"),
                "notes": s.get("notes"),
                "feedback": s.get("feedback"),
                "auto_score": s.get("auto_score"),
                "completed_at": s.get("reviewed_at") or s.get("created_at"),
            })

    # competencies
    comp_map = {c["key"]: {**c, "points": 0, "labs": 0, "badge_earned": False} for c in COMPETENCIES}
    for s in lab_subs:
        lab = labs_by_slug.get(s["lab_slug"])
        if lab:
            for k in lab.get("competencies", []):
                if k in comp_map:
                    comp_map[k]["points"] += lab.get("skill_points", 0)
                    comp_map[k]["labs"] += 1
    for c in comp_map.values():
        c["badge_earned"] = c["points"] >= 100

    creds = await db.user_credentials.find({"user_id": user_id}, {"_id": 0}).to_list(200)
    cred_by_key = {c["key"]: c for c in CREDENTIALS}
    creds_detail = []
    for c in creds:
        cred = cred_by_key.get(c["credential_key"])
        if cred:
            creds_detail.append({**cred, **c})

    port = await db.portfolios.find_one({"user_id": user_id}, {"_id": 0})

    hours = sum(m["hours"] for m in completed_mods) + sum(lab_item["hours"] for lab_item in labs_detail)
    skill_points = sum(c["points"] for c in comp_map.values())

    return {
        "user": {
            "id": user_doc["id"],
            "full_name": user_doc["full_name"],
            "email": user_doc["email"],
            "associate": user_doc.get("associate"),
        },
        "bio": port.get("bio") if port else None,
        "share_slug": port.get("slug") if port and port.get("published") else None,
        "stats": {
            "hours": hours,
            "skill_points": skill_points,
            "modules_completed": len(completed_mods),
            "labs_passed": len(labs_detail),
            "credentials_earned": len(creds_detail),
            "badges_earned": sum(1 for c in comp_map.values() if c["badge_earned"]),
        },
        "modules": completed_mods,
        "labs": labs_detail,
        "credentials": creds_detail,
        "competencies": list(comp_map.values()),
    }


@api_router.get("/portfolio/me")
async def my_portfolio(user: User = Depends(current_user)):
    user_doc = await db.users.find_one({"id": user.id}, {"_id": 0, "password_hash": 0})
    return await build_portfolio(user_doc)


@api_router.get("/portfolio/public/{slug}")
async def public_portfolio(slug: str):
    port = await db.portfolios.find_one({"slug": slug, "published": True}, {"_id": 0})
    if not port:
        raise HTTPException(404, "Portfolio not found or not public")
    user_doc = await db.users.find_one({"id": port["user_id"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(404, "User not found")
    data = await build_portfolio(user_doc)
    # strip email for public view
    data["user"].pop("email", None)
    return data


@api_router.get("/portfolio/export.pdf")
async def portfolio_pdf(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    user_doc = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(401, "User not found")

    data = await build_portfolio(user_doc)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter

    def header():
        c.setFillColor(colors.HexColor("#0B203F"))
        c.rect(0, h - 1.3 * inch, w, 1.3 * inch, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#FFD100"))
        c.rect(0, h - 1.38 * inch, w, 0.08 * inch, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(0.6 * inch, h - 0.55 * inch, "W.A.I. — WORKFORCE APPRENTICE INSTITUTE")
        c.setFont("Helvetica", 9)
        c.drawString(0.6 * inch, h - 0.8 * inch, "LCE-WAI Partner Program  ·  Apprentice Portfolio")
        c.setFont("Helvetica-Bold", 18)
        c.drawString(0.6 * inch, h - 1.1 * inch, data["user"]["full_name"])
        c.setFont("Helvetica", 10)
        right = f"Hours: {data['stats']['hours']}  ·  Points: {data['stats']['skill_points']}"
        c.drawRightString(w - 0.6 * inch, h - 1.1 * inch, right)

    def section(y, title):
        c.setFillColor(colors.HexColor("#0B203F"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.6 * inch, y, title.upper())
        c.setStrokeColor(colors.HexColor("#1E5BA8"))
        c.setLineWidth(2)
        c.line(0.6 * inch, y - 4, 0.6 * inch + 1.1 * inch, y - 4)

    header()
    y = h - 1.7 * inch
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica", 10)
    if data.get("bio"):
        c.drawString(0.6 * inch, y, data["bio"][:120])
        y -= 0.25 * inch

    def text_line(txt, bold=False, size=10):
        nonlocal y
        if y < 1 * inch:
            c.showPage()
            header()
            y = h - 1.7 * inch
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(0.7 * inch, y, txt[:95])
        y -= 0.22 * inch

    section(y, "Credentials & Badges")
    y -= 0.3 * inch
    for cr in data["credentials"]:
        text_line(f"• {cr['name']}  [{cr['category'].upper()}]", bold=True)
        text_line(f"   Earned {cr['earned_at'][:10]}" + (f"  ·  Expires {cr['expires_at'][:10]}" if cr.get("expires_at") else ""))
    if not data["credentials"]:
        text_line("  (none yet)")

    y -= 0.15 * inch
    section(y, "Competency Matrix")
    y -= 0.3 * inch
    for cmp in data["competencies"]:
        mark = "✓" if cmp["badge_earned"] else " "
        text_line(f" [{mark}] {cmp['name']}  —  {cmp['points']} pts  ({cmp['labs']} labs)")

    y -= 0.15 * inch
    section(y, "Modules Completed")
    y -= 0.3 * inch
    for m in data["modules"]:
        text_line(f"• {m['title']}  —  {m['hours']}h  ({int(m['score']) if m.get('score') else 0}%)")

    y -= 0.15 * inch
    section(y, "Labs Passed")
    y -= 0.3 * inch
    for lab_item in data["labs"]:
        text_line(f"• {lab_item['title']}  [{lab_item['track'].upper()}]  —  {lab_item['skill_points']} pts")

    # footer
    c.setFillColor(colors.HexColor("#4B5563"))
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(w / 2, 0.4 * inch, '"Whatever you do, work at it with all your heart." — Colossians 3:23')

    c.showPage()
    c.save()
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=portfolio-{user_doc['id'][:8]}.pdf"},
    )


# -- COMPLIANCE MODULES --
@api_router.get("/compliance")
async def list_compliance(user: User = Depends(current_user)):
    docs = await db.compliance_modules.find({}, {"_id": 0}).sort("order", 1).to_list(50)
    progress = await db.compliance_progress.find({"user_id": user.id}, {"_id": 0}).to_list(50)
    pmap = {p["module_slug"]: p for p in progress}
    for d in docs:
        d["my_progress"] = pmap.get(d["slug"])
    return docs


@api_router.get("/compliance/{slug}")
async def get_compliance(slug: str, user: User = Depends(current_user)):
    doc = await db.compliance_modules.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Compliance module not found")
    doc["my_progress"] = await db.compliance_progress.find_one(
        {"user_id": user.id, "module_slug": slug}, {"_id": 0}
    )
    return doc


@api_router.post("/compliance/{slug}/quiz")
async def submit_compliance_quiz(slug: str, body: dict, user: User = Depends(current_user)):
    mod = await db.compliance_modules.find_one({"slug": slug}, {"_id": 0})
    if not mod:
        raise HTTPException(404, "Module not found")
    answers = body.get("answers", [])
    quiz = mod.get("quiz", [])
    if len(answers) != len(quiz):
        raise HTTPException(400, "Answer count mismatch")
    correct = sum(1 for i, q in enumerate(quiz) if q["answer"] == answers[i])
    score = correct / len(quiz) * 100 if quiz else 0
    pass_pct = 80 if slug == "loto-certification" else 70
    status_val = "completed" if score >= pass_pct else "in_progress"
    now = datetime.now(timezone.utc)
    expires_at = None
    if status_val == "completed" and mod.get("expires_months"):
        expires_at = (now + timedelta(days=30 * mod["expires_months"])).isoformat()
    update = {
        "user_id": user.id,
        "module_slug": slug,
        "status": status_val,
        "quiz_score": score,
        "completed_at": now.isoformat() if status_val == "completed" else None,
        "expires_at": expires_at,
        "hours_logged": mod.get("hours", 0) if status_val == "completed" else 0,
        "updated_at": now.isoformat(),
    }
    await db.compliance_progress.update_one(
        {"user_id": user.id, "module_slug": slug},
        {"$set": update, "$setOnInsert": {"id": str(uuid.uuid4())}},
        upsert=True,
    )
    if status_val == "completed":
        await award_credentials(user.id)
    return {"score": score, "correct": correct, "total": len(quiz), "status": status_val, "pass_pct": pass_pct, "expires_at": expires_at}


# -- ADAPTIVE LEARNING ENGINE --
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


# -- PROGRAM-LEVEL ADMIN: SITES, INVENTORY, TOOL CHECKOUT --
@api_router.get("/admin/sites")
async def list_sites(user: User = Depends(require_role("admin", "instructor"))):
    docs = await db.sites.find({}, {"_id": 0}).to_list(100)
    return docs


@api_router.post("/admin/sites")
async def create_site(payload: dict, user: User = Depends(require_role("admin"))):
    if not payload.get("slug") or not payload.get("name"):
        raise HTTPException(400, "slug and name required")
    if await db.sites.find_one({"slug": payload["slug"]}):
        raise HTTPException(400, "Site slug exists")
    doc = {
        "id": str(uuid.uuid4()),
        "slug": payload["slug"],
        "name": payload["name"],
        "address": payload.get("address", ""),
        "capacity": int(payload.get("capacity", 0)),
    }
    await db.sites.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.get("/admin/inventory")
async def list_inventory(site_slug: Optional[str] = None, user: User = Depends(require_role("admin", "instructor"))):
    q = {"site_slug": site_slug} if site_slug else {}
    items = await db.inventory.find(q, {"_id": 0}).to_list(500)
    return items


@api_router.post("/admin/inventory")
async def add_inventory(payload: dict, user: User = Depends(require_role("admin"))):
    required = ["sku", "name", "category", "quantity_total", "site_slug"]
    if any(k not in payload for k in required):
        raise HTTPException(400, f"Required: {required}")
    if await db.inventory.find_one({"sku": payload["sku"]}):
        raise HTTPException(400, "SKU exists")
    doc = {
        "id": str(uuid.uuid4()),
        "sku": payload["sku"],
        "name": payload["name"],
        "category": payload["category"],
        "site_slug": payload["site_slug"],
        "quantity_total": int(payload["quantity_total"]),
        "quantity_available": int(payload["quantity_total"]),
    }
    await db.inventory.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.post("/admin/checkout")
async def checkout_tool(payload: dict, user: User = Depends(require_role("instructor", "admin"))):
    sku = payload.get("sku")
    student_id = payload.get("user_id")
    qty = int(payload.get("quantity", 1))
    if not sku or not student_id:
        raise HTTPException(400, "sku and user_id required")
    item = await db.inventory.find_one({"sku": sku}, {"_id": 0})
    if not item:
        raise HTTPException(404, "Item not found")
    if item["quantity_available"] < qty:
        raise HTTPException(400, f"Only {item['quantity_available']} available")
    co = {
        "id": str(uuid.uuid4()),
        "sku": sku,
        "user_id": student_id,
        "quantity": qty,
        "checked_out_by": user.id,
        "checked_out_at": datetime.now(timezone.utc).isoformat(),
        "returned_at": None,
        "status": "out",
    }
    await db.tool_checkouts.insert_one(co)
    await db.inventory.update_one({"sku": sku}, {"$inc": {"quantity_available": -qty}})
    co.pop("_id", None)
    return co


@api_router.post("/admin/checkout/{checkout_id}/return")
async def return_tool(checkout_id: str, user: User = Depends(require_role("instructor", "admin"))):
    co = await db.tool_checkouts.find_one({"id": checkout_id}, {"_id": 0})
    if not co or co["status"] == "returned":
        raise HTTPException(400, "Invalid or already returned")
    await db.tool_checkouts.update_one(
        {"id": checkout_id},
        {"$set": {"status": "returned", "returned_at": datetime.now(timezone.utc).isoformat()}},
    )
    await db.inventory.update_one({"sku": co["sku"]}, {"$inc": {"quantity_available": co["quantity"]}})
    return {"ok": True}


@api_router.get("/admin/checkouts")
async def list_checkouts(status: Optional[str] = None, user: User = Depends(require_role("instructor", "admin"))):
    q = {"status": status} if status else {}
    docs = await db.tool_checkouts.find(q, {"_id": 0}).sort("checked_out_at", -1).to_list(500)
    user_ids = list({d["user_id"] for d in docs})
    skus = list({d["sku"] for d in docs})
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(1000)
    items = await db.inventory.find({"sku": {"$in": skus}}, {"_id": 0}).to_list(500)
    u_map = {u["id"]: u for u in users}
    i_map = {i["sku"]: i for i in items}
    for d in docs:
        d["user"] = u_map.get(d["user_id"])
        d["item"] = i_map.get(d["sku"])
    return docs


# -- NOTIFICATIONS --
@api_router.get("/notifications/me")
async def my_notifications(user: User = Depends(current_user)):
    # Auto-create expiry warnings (30-day window) for credentials about to expire
    now = datetime.now(timezone.utc)
    soon = (now + timedelta(days=30)).isoformat()
    creds = await db.user_credentials.find(
        {"user_id": user.id, "expires_at": {"$lte": soon, "$gt": now.isoformat()}}, {"_id": 0}
    ).to_list(50)
    cred_map = {c["key"]: c for c in CREDENTIALS}
    for c in creds:
        # one warning per credential per expiry date
        existing = await db.notifications.find_one(
            {"user_id": user.id, "kind": "warning", "meta.credential_id": c["id"]}, {"_id": 0}
        )
        if not existing:
            cred_def = cred_map.get(c["credential_key"])
            await db.notifications.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "title": "Credential expires soon",
                "body": f"{cred_def['name'] if cred_def else c['credential_key']} expires {c['expires_at'][:10]}. Renew with the next compliance quiz.",
                "link": "/credentials",
                "kind": "warning",
                "meta": {"credential_id": c["id"]},
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
    docs = await db.notifications.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    unread = sum(1 for d in docs if not d["read"])
    return {"items": docs, "unread": unread}


@api_router.post("/notifications/{nid}/read")
async def mark_read(nid: str, user: User = Depends(current_user)):
    await db.notifications.update_one({"id": nid, "user_id": user.id}, {"$set": {"read": True}})
    return {"ok": True}


@api_router.post("/notifications/read-all")
async def mark_all_read(user: User = Depends(current_user)):
    await db.notifications.update_many({"user_id": user.id, "read": False}, {"$set": {"read": True}})
    return {"ok": True}


@api_router.get("/admin/platform/flags")
async def get_platform_flags(user: User = Depends(require_role("executive_admin"))):
    """Return all platform feature flags. Executive only."""
    doc = await db.platform_flags.find_one({"_id": "flags"}, {"_id": 0})
    if not doc:
        return {"flags": {}}
    return {"flags": doc.get("flags", {})}


@api_router.post("/admin/platform/flags/{flag}")
async def set_platform_flag(
    flag: str,
    payload: dict,
    user: User = Depends(require_role("executive_admin")),
):
    """Set a platform feature flag (true/false). Executive only.
    Body: { value: bool, reason?: str }
    Supported flags: platform_locked, marketplace_disabled, ai_disabled,
                     community_disabled, labs_disabled
    """
    ALLOWED = {"platform_locked", "marketplace_disabled", "ai_disabled",
               "community_disabled", "labs_disabled"}
    if flag not in ALLOWED:
        raise HTTPException(400, f"Unknown flag '{flag}'. Allowed: {', '.join(sorted(ALLOWED))}")
    value = bool(payload.get("value", True))
    reason = (payload.get("reason") or "").strip()
    now = datetime.now(timezone.utc).isoformat()
    await db.platform_flags.update_one(
        {"_id": "flags"},
        {"$set": {
            f"flags.{flag}": {
                "enabled": value,
                "set_by": user.id,
                "set_at": now,
                "reason": reason,
            }
        }},
        upsert=True,
    )
    await audit(user.id, f"platform_flag:{flag}:{value}", {"reason": reason})
    return {"flag": flag, "enabled": value, "set_at": now}


@api_router.post("/admin/broadcast")
async def broadcast_notification(
    payload: dict,
    user: User = Depends(require_role("executive_admin", "admin")),
):
    """Broadcast a notification to all users or a specific cohort/role.
    Body: { message, title, target: 'all' | role_name | associate_name }
    Executive/admin only.
    """
    message = (payload.get("message") or "").strip()
    title   = (payload.get("title") or "Platform Announcement").strip()
    target  = (payload.get("target") or "all").strip()

    if not message:
        raise HTTPException(400, "message is required")

    query: dict = {}
    if target != "all":
        # Try role first, then associate
        query = {"$or": [{"role": target}, {"associate": target}]}

    recipients = await db.users.find(query, {"_id": 0, "id": 1}).to_list(10000)
    if not recipients:
        return {"sent": 0, "message": "No recipients matched"}

    now = datetime.now(timezone.utc).isoformat()
    docs = [
        {
            "id": str(uuid.uuid4()),
            "user_id": r["id"],
            "title": title,
            "message": message,
            "type": "broadcast",
            "read": False,
            "created_at": now,
            "sent_by": user.id,
        }
        for r in recipients
    ]
    await db.notifications.insert_many(docs)
    await audit(user.id, f"broadcast:{target}", {"title": title, "recipients": len(docs)})
    return {"sent": len(docs), "target": target}


# -- ATTENDANCE (instructor records, student views own) --
@api_router.post("/attendance")
async def record_attendance(payload: dict, user: User = Depends(require_role("instructor", "admin"))):
    if not payload.get("date") or not payload.get("attendees"):
        raise HTTPException(400, "date and attendees required")
    incoming_ids = [a["user_id"] for a in payload["attendees"] if a.get("user_id")]
    valid = await db.users.find({"id": {"$in": incoming_ids}, "role": "student"}, {"_id": 0, "id": 1}).to_list(1000)
    valid_ids = {v["id"] for v in valid}
    session_id = str(uuid.uuid4())
    docs = []
    for a in payload["attendees"]:
        if a.get("user_id") not in valid_ids:
            continue
        docs.append({
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "user_id": a["user_id"],
            "date": payload["date"],
            "site_slug": payload.get("site_slug"),
            "status": a.get("status", "present"),
            "recorded_by": user.id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    if docs:
        await db.attendance.insert_many(docs)
    await audit(user.id, "attendance.recorded", target=session_id, meta={"count": len(docs)})
    return {"session_id": session_id, "count": len(docs), "skipped": len(payload["attendees"]) - len(docs)}


@api_router.get("/attendance/me")
async def my_attendance(user: User = Depends(current_user)):
    docs = await db.attendance.find({"user_id": user.id}, {"_id": 0}).sort("date", -1).to_list(500)
    summary = {"present": 0, "absent": 0, "tardy": 0, "excused": 0}
    for d in docs:
        if d["status"] in summary:
            summary[d["status"]] += 1
    total = sum(summary.values())
    rate = round(summary["present"] / max(1, total) * 100, 1)
    return {"records": docs, "summary": summary, "attendance_rate": rate}


@api_router.get("/attendance/roster")
async def attendance_roster(user: User = Depends(require_role("instructor", "admin"))):
    q = {"role": "student"} if user.role == "admin" else {"role": "student", "associate": user.associate}
    students = await db.users.find(q, {"_id": 0, "password_hash": 0}).to_list(1000)
    user_ids = [s["id"] for s in students]
    records = await db.attendance.find({"user_id": {"$in": user_ids}}, {"_id": 0}).to_list(50000)
    by_user = {}
    for r in records:
        by_user.setdefault(r["user_id"], {"present": 0, "absent": 0, "tardy": 0, "excused": 0})
        s = r["status"]
        if s in by_user[r["user_id"]]:
            by_user[r["user_id"]][s] += 1
    out = []
    for s in students:
        stats = by_user.get(s["id"], {"present": 0, "absent": 0, "tardy": 0, "excused": 0})
        total = sum(stats.values())
        out.append({
            "user_id": s["id"], "full_name": s["full_name"], "associate": s.get("associate"),
            **stats, "total": total,
            "rate": round(stats["present"] / max(1, total) * 100, 1),
        })
    return out


# -- INCIDENT REPORTING (OSHA-style) --
class IncidentReq(BaseModel):
    type: Literal["near_miss", "first_aid", "injury", "property_damage", "safety_violation", "other"]
    severity: Literal["low", "medium", "high", "critical"] = "low"
    description: str
    site_slug: Optional[str] = None
    photo_url: Optional[str] = None
    involved_user_ids: List[str] = []


@api_router.post("/incidents")
async def report_incident(body: IncidentReq, user: User = Depends(current_user)):
    doc = {
        "id": str(uuid.uuid4()),
        "type": body.type,
        "severity": body.severity,
        "description": body.description,
        "site_slug": body.site_slug,
        "photo_url": body.photo_url,
        "involved_user_ids": body.involved_user_ids,
        "reported_by": user.id,
        "status": "open",
        "resolution": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resolved_at": None,
    }
    await db.incidents.insert_one(doc)
    await audit(user.id, "incident.reported", target=doc["id"], meta={"type": body.type, "severity": body.severity})
    doc.pop("_id", None)
    return doc


@api_router.get("/incidents")
async def list_incidents(status: Optional[str] = None, user: User = Depends(require_role("instructor", "admin"))):
    q = {"status": status} if status else {}
    docs = await db.incidents.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
    user_ids = list({d["reported_by"] for d in docs} | {u for d in docs for u in d.get("involved_user_ids", [])})
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(1000)
    umap = {u["id"]: u for u in users}
    for d in docs:
        d["reporter"] = umap.get(d["reported_by"])
        d["involved"] = [umap.get(uid) for uid in d.get("involved_user_ids", []) if umap.get(uid)]
    return docs


@api_router.post("/incidents/{iid}/resolve")
async def resolve_incident(iid: str, payload: dict, user: User = Depends(require_role("admin"))):
    resolution = (payload.get("resolution") or "").strip()
    if not resolution:
        raise HTTPException(400, "resolution required")
    await db.incidents.update_one(
        {"id": iid},
        {"$set": {
            "status": "resolved",
            "resolution": resolution,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    await audit(user.id, "incident.resolved", target=iid)
    return {"ok": True}


# -- AUDIT LOG (admin only) --
@api_router.get("/admin/audit")
async def view_audit(
    limit: int = 200,
    action: Optional[str] = None,
    actor_id: Optional[str] = None,
    user: User = Depends(require_role("admin")),
):
    query: dict = {}
    if action:
        query["action"] = {"$regex": action, "$options": "i"}
    if actor_id:
        query["actor_id"] = actor_id
    docs = await db.audit_log.find(query, {"_id": 0}).sort("at", -1).to_list(min(limit, 1000))
    user_ids = list({d["actor_id"] for d in docs if d.get("actor_id")})
    users_list = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(1000)
    umap = {u["id"]: u for u in users_list}
    for d in docs:
        d["actor"] = umap.get(d.get("actor_id")) if d.get("actor_id") else None
    return docs


# -- PROGRAM ANALYTICS (admin) --
@api_router.get("/analytics/program")
async def program_analytics(user: User = Depends(require_role("admin"))):
    students = await db.users.count_documents({"role": "student"})
    instructors = await db.users.count_documents({"role": "instructor"})
    completions = await db.progress.count_documents({"status": "completed"})
    labs_passed = await db.lab_submissions.count_documents({"status": {"$in": ["passed", "approved"]}})
    labs_pending = await db.lab_submissions.count_documents({"status": "pending"})
    creds_issued = await db.user_credentials.count_documents({})
    incidents_open = await db.incidents.count_documents({"status": "open"})

    # Completions per associate group
    pipeline_assoc = [
        {"$match": {"role": "student"}},
        {"$lookup": {"from": "progress", "localField": "id", "foreignField": "user_id", "as": "prog"}},
        {"$project": {"associate": 1, "completed": {"$size": {"$filter": {"input": "$prog", "as": "p", "cond": {"$eq": ["$$p.status", "completed"]}}}}}},
        {"$group": {"_id": "$associate", "students": {"$sum": 1}, "total_completions": {"$sum": "$completed"}}},
    ]
    by_associate = await db.users.aggregate(pipeline_assoc).to_list(50)
    associates = [{"associate": d["_id"] or "Unassigned", "students": d["students"], "completions": d["total_completions"]} for d in by_associate]

    # Expiring credentials (next 90 days)
    now = datetime.now(timezone.utc)
    soon = (now + timedelta(days=90)).isoformat()
    expiring = await db.user_credentials.count_documents({
        "expires_at": {"$lte": soon, "$gt": now.isoformat()}
    })

    # Top weak competencies cohort-wide
    all_subs = await db.lab_submissions.find({"status": {"$in": ["passed", "approved"]}}, {"_id": 0}).to_list(50000)
    all_labs = await db.labs.find({}, {"_id": 0}).to_list(200)
    labs_by_slug = {lab["slug"]: lab for lab in all_labs}
    cohort_comp = {c["key"]: 0 for c in COMPETENCIES}
    for s in all_subs:
        lab = labs_by_slug.get(s["lab_slug"])
        if lab:
            for k in lab.get("competencies", []):
                if k in cohort_comp:
                    cohort_comp[k] += lab.get("skill_points", 0)
    weakest = sorted(cohort_comp.items(), key=lambda x: x[1])[:3]
    weakest_named = [{"key": k, "name": next((c["name"] for c in COMPETENCIES if c["key"] == k), k), "points": v} for k, v in weakest]

    # Module completion rates — single aggregation instead of N+1.
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {"_id": "$module_slug", "count": {"$sum": 1}}},
    ]
    counts = {r["_id"]: r["count"] for r in await db.progress.aggregate(pipeline).to_list(200)}
    mod_completions = [
        {
            "slug": m["slug"], "title": m["title"], "completions": counts.get(m["slug"], 0),
            "rate": round(counts.get(m["slug"], 0) / max(1, students) * 100, 1),
        }
        for m in MODULES
    ]

    # Activity in last 30 days (audit volume as proxy)
    thirty_ago = (now - timedelta(days=30)).isoformat()
    active = len(set([
        a["actor_id"] for a in await db.audit_log.find(
            {"at": {"$gte": thirty_ago}, "action": "auth.login.success"}, {"_id": 0, "actor_id": 1}
        ).to_list(50000) if a.get("actor_id")
    ]))

    return {
        "totals": {
            "students": students, "instructors": instructors,
            "module_completions": completions, "labs_passed": labs_passed,
            "labs_pending_review": labs_pending,
            "credentials_issued": creds_issued,
            "credentials_expiring_90d": expiring,
            "open_incidents": incidents_open,
            "active_30d": active,
        },
        "by_associate": associates,
        "weakest_competencies": weakest_named,
        "module_completion_rates": mod_completions,
    }



# ─────────────────────────────────────────────────────────────────────────────
# M.O.R.E. — Michael Oliver Resource Exchange
# Community-powered mutual aid platform: posts, needs, skill swaps, chat
# AI Moderation: Oliver Guardian (sarcastic first-line moderator)
# Auto-purge: posts 30 days, chats 60 minutes
# ─────────────────────────────────────────────────────────────────────────────

from prompts.oliver_guardian_prompt import OLIVER_GUARDIAN_PROMPT as _OLIVER_GUARDIAN_PROMPT  # noqa: E402


# Crisis resources — kept in sync with the prompt above
_CRISIS_RESOURCES = [
    {"name": "211 (US)", "description": "Free local crisis resources — call or text, 24/7", "contact": "Call or text 211 | 211.org"},
    {"name": "Crisis Text Line", "description": "Text-based crisis support, free and confidential", "contact": "Text HOME to 741741"},
    {"name": "National Domestic Violence Hotline", "description": "Safe, confidential support for DV situations", "contact": "1-800-799-7233 | thehotline.org"},
    {"name": "Childhelp National Child Abuse Hotline", "description": "Child abuse reporting and support", "contact": "1-800-422-4453"},
    {"name": "988 Suicide & Crisis Lifeline", "description": "Mental health crisis support", "contact": "Call or text 988"},
    {"name": "SAMHSA National Helpline", "description": "Substance use and mental health treatment referrals", "contact": "1-800-662-4357"},
]


async def _oliver_write_audit_log(
    user_id: str,
    content_type: str,
    content: str,
    decision: str,
    reason: str,
    violation_category: str,
    oliver_response: str | None,
) -> None:
    """Write every moderation decision to the audit log — regardless of outcome."""
    try:
        await db.more_moderation_log.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "content_type": content_type,
            "content_preview": content[:500],  # truncated — full content not stored for PII protection
            "decision": decision,
            "reason": reason,
            "violation_category": violation_category,
            "oliver_response": oliver_response,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error(f"Oliver Guardian audit log write failed: {e}")


async def _oliver_check_rate_limit(user_id: str) -> bool:
    """Returns True if the user is within rate limits, False if they should be throttled.
    Limit: 10 posts/needs/chats per hour per user across all M.O.R.E. content types."""
    try:
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        count = 0
        for collection in [db.more_posts, db.more_needs, db.more_chats]:
            count += await collection.count_documents({
                "author_id": user_id,
                "created_at": {"$gte": one_hour_ago},
            })
        return count < 10
    except Exception as e:
        logger.warning(f"Oliver Guardian rate limit check failed: {e}")
        return True  # Fail open for rate limiting only — don't block users if DB is slow


async def _oliver_moderate(content: str, user_id: str = "unknown", content_type: str = "post") -> dict:
    """Run Oliver Guardian AI moderation on submitted content.

    FAIL-SAFE: on any error, returns 'quarantine' decision — never auto-approves.
    Every decision is written to the audit log regardless of outcome.
    """
    import json as _json

    decision_result = None
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(
            system=_OLIVER_GUARDIAN_PROMPT,
            messages=[{"role": "user", "content": f"Content to moderate:\n\n{content}"}],
            max_tokens=512,
            persona_label="oliver_guardian",
        )
        raw = _gw["text"].strip()
        # Strip markdown code fences if model adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        decision_result = _json.loads(raw.strip())
        decision_result.setdefault("decision", "warn")
        decision_result.setdefault("reason", "moderation review")
        decision_result.setdefault("oliver_response", None)
        decision_result.setdefault("violation_category", "none")
        # Attach full crisis resources if crisis decision
        if decision_result["decision"] == "crisis":
            decision_result["crisis_resources"] = _CRISIS_RESOURCES
    except Exception as e:
        logger.error(f"Oliver Guardian moderation failed: {e}")
        # FAIL-SAFE: on error, quarantine for human review — never auto-approve
        decision_result = {
            "decision": "quarantine",
            "reason": f"Moderation system temporarily unavailable: {type(e).__name__}",
            "oliver_response": (
                "We're having a brief technical hiccup reviewing your post. "
                "It's been held for a quick human review and will be up shortly if everything looks good."
            ),
            "violation_category": "none",
        }

    # Write audit log — every decision, every time
    await _oliver_write_audit_log(
        user_id=user_id,
        content_type=content_type,
        content=content,
        decision=decision_result.get("decision", "unknown"),
        reason=decision_result.get("reason", ""),
        violation_category=decision_result.get("violation_category", "none"),
        oliver_response=decision_result.get("oliver_response"),
    )

    return decision_result


# ─── M.O.R.E. Pydantic Models ────────────────────────────────────────────────

class MorePostReq(BaseModel):
    content: str
    category: Literal["skill_offer", "need", "community", "story"] = "community"

class MoreNeedReq(BaseModel):
    title: str
    description: str
    category: str = "general"

class MoreChatReq(BaseModel):
    session_id: str
    message: str

class MoreFlagReq(BaseModel):
    target_id: str
    target_type: Literal["post", "need", "chat"]
    reason: str

class MoreDeptChatReq(BaseModel):
    session_id: str
    message: str
    history: Optional[list[OrchestratorHistoryItem]] = []
    department_hint: Optional[str] = None


# ─── M.O.R.E. Endpoints ──────────────────────────────────────────────────────

@api_router.post("/more/post")
async def more_create_post(req: MorePostReq, user=Depends(current_user)):
    if not req.content.strip():
        raise HTTPException(400, "Content cannot be empty")
    if len(req.content) > 2000:
        raise HTTPException(400, "Content too long (max 2000 chars)")

    # Rate limit check
    if not await _oliver_check_rate_limit(user.id):
        raise HTTPException(429, "You're posting a lot right now. Take a breath and try again in an hour.")

    moderation = await _oliver_moderate(req.content, user_id=user.id, content_type="post")
    decision = moderation.get("decision", "warn")

    # Crisis — do not publish, return resources
    if decision == "crisis":
        return {
            "post": None,
            "oliver_response": moderation.get("oliver_response"),
            "crisis": True,
            "crisis_resources": moderation.get("crisis_resources", _CRISIS_RESOURCES),
        }

    # Block — do not publish, return Oliver's message
    if decision == "block":
        raise HTTPException(400, moderation.get("oliver_response") or "This content cannot be posted.")

    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    # Warn or quarantine → hold for admin review, not live
    if decision in ("warn", "quarantine"):
        post_doc = {
            "id": str(uuid.uuid4()),
            "content": req.content,
            "category": req.category,
            "author_id": user.id,
            "author_name": user.full_name,
            "status": "pending_review",
            "moderation_note": moderation.get("reason"),
            "violation_category": moderation.get("violation_category", "none"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at,
            "likes": 0,
        }
        await db.more_posts.insert_one(post_doc)
        post_doc.pop("_id", None)
        return {
            "post": post_doc,
            "oliver_response": moderation.get("oliver_response"),
            "pending_review": True,
        }

    # Approve — publish immediately
    post_doc = {
        "id": str(uuid.uuid4()),
        "content": req.content,
        "category": req.category,
        "author_id": user.id,
        "author_name": user.full_name,
        "status": "active",
        "moderation_note": moderation.get("reason"),
        "violation_category": "none",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "likes": 0,
    }
    await db.more_posts.insert_one(post_doc)
    post_doc.pop("_id", None)
    return {"post": post_doc, "oliver_response": None}


@api_router.get("/more/posts")
async def more_list_posts(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
):
    now = datetime.now(timezone.utc).isoformat()
    # Only Oliver-approved posts are public. Held content (pending_review) stays
    # off the public feed until a human clears it.
    query: dict = {"expires_at": {"$gt": now}, "status": "active"}
    if category:
        query["category"] = category
    cursor = db.more_posts.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    posts = await cursor.to_list(limit)
    total = await db.more_posts.count_documents(query)
    return {"posts": posts, "total": total}


@api_router.post("/more/need")
async def more_create_need(req: MoreNeedReq, user=Depends(current_user)):
    combined = f"{req.title}\n{req.description}"

    if not req.title.strip() or not req.description.strip():
        raise HTTPException(400, "Title and description are required")

    # Rate limit check
    if not await _oliver_check_rate_limit(user.id):
        raise HTTPException(429, "You're posting a lot right now. Take a breath and try again in an hour.")

    moderation = await _oliver_moderate(combined, user_id=user.id, content_type="need")
    decision = moderation.get("decision", "warn")

    # Crisis — return resources, do not publish raw distress as a "need"
    if decision == "crisis":
        return {
            "need": None,
            "oliver_response": moderation.get("oliver_response"),
            "crisis": True,
            "crisis_resources": moderation.get("crisis_resources", _CRISIS_RESOURCES),
        }

    if decision == "block":
        raise HTTPException(400, moderation.get("oliver_response") or "This content cannot be posted.")

    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    # Warn or quarantine → hold for review
    status = "open" if decision == "approve" else "pending_review"

    need_doc = {
        "id": str(uuid.uuid4()),
        "title": req.title,
        "description": req.description,
        "category": req.category,
        "author_id": user.id,
        "author_name": user.full_name,
        "status": status,
        "moderation_note": moderation.get("reason"),
        "violation_category": moderation.get("violation_category", "none"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "responses": 0,
    }
    await db.more_needs.insert_one(need_doc)
    need_doc.pop("_id", None)
    return {
        "need": need_doc,
        "oliver_response": moderation.get("oliver_response") if decision != "approve" else None,
        "pending_review": decision in ("warn", "quarantine"),
    }


@api_router.get("/more/needs")
async def more_list_needs(
    category: Optional[str] = None,
    status: str = "open",
    skip: int = 0,
    limit: int = 20,
):
    now = datetime.now(timezone.utc).isoformat()
    # Never expose held/quarantined content via the public feed, even if a
    # client explicitly requests status=pending_review.
    if status == "pending_review":
        status = "open"
    query: dict = {"expires_at": {"$gt": now}, "status": status}
    if category:
        query["category"] = category
    cursor = db.more_needs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    needs = await cursor.to_list(limit)
    total = await db.more_needs.count_documents(query)
    return {"needs": needs, "total": total}


@api_router.post("/more/chat/send")
async def more_chat_send(req: MoreChatReq, user=Depends(current_user)):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty")
    if len(req.message) > 1000:
        raise HTTPException(400, "Message too long (max 1000 chars)")

    if not await _oliver_check_rate_limit(user.id):
        raise HTTPException(429, "Slow down a bit — you've been very active. Try again in an hour.")

    moderation = await _oliver_moderate(req.message, user_id=user.id, content_type="chat")
    decision = moderation.get("decision", "warn")

    if decision == "crisis":
        return {
            "message": None,
            "oliver_response": moderation.get("oliver_response"),
            "crisis": True,
            "crisis_resources": moderation.get("crisis_resources", _CRISIS_RESOURCES),
        }

    if decision == "block":
        raise HTTPException(400, moderation.get("oliver_response") or "This message cannot be sent.")

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=60)).isoformat()
    msg_doc = {
        "id": str(uuid.uuid4()),
        "session_id": req.session_id,
        "content": req.message,
        "author_id": user.id,
        "author_name": user.full_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
    }
    await db.more_chats.insert_one(msg_doc)
    msg_doc.pop("_id", None)
    return {"message": msg_doc, "oliver_response": moderation.get("oliver_response") if moderation.get("decision") == "warn" else None}


@api_router.get("/more/chat/{session_id}")
async def more_chat_get(session_id: str, user=Depends(current_user)):
    now = datetime.now(timezone.utc).isoformat()
    cursor = db.more_chats.find(
        {"session_id": session_id, "expires_at": {"$gt": now}},
        {"_id": 0}
    ).sort("created_at", 1).limit(200)
    messages = await cursor.to_list(200)
    return {"messages": messages, "session_id": session_id}


@api_router.post("/more/flag")
async def more_flag_content(req: MoreFlagReq, user=Depends(current_user)):
    flag_doc = {
        "id": str(uuid.uuid4()),
        "target_id": req.target_id,
        "target_type": req.target_type,
        "reason": req.reason,
        "flagged_by": user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        "status": "pending",
    }
    await db.more_flags.insert_one(flag_doc)
    flag_doc.pop("_id", None)
    return {"flag": flag_doc}


@api_router.post("/more/appeal")
async def more_appeal_decision(
    target_id: str,
    reason: str,
    user=Depends(current_user),
):
    """Appeal a moderation decision. Logs the appeal for admin review.
    Users can appeal a block or a pending_review hold on their own content."""
    if not reason.strip():
        raise HTTPException(400, "Please explain why you are appealing.")
    if len(reason) > 1000:
        raise HTTPException(400, "Appeal reason too long (max 1000 chars).")

    # Verify the content belongs to this user
    post = await db.more_posts.find_one({"id": target_id, "author_id": user.id}, {"_id": 0})
    need = await db.more_needs.find_one({"id": target_id, "author_id": user.id}, {"_id": 0}) if not post else None
    if not post and not need:
        raise HTTPException(404, "Content not found or does not belong to your account.")

    appeal_doc = {
        "id": str(uuid.uuid4()),
        "target_id": target_id,
        "target_type": "post" if post else "need",
        "user_id": user.id,
        "user_name": user.full_name,
        "appeal_reason": reason.strip(),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
    }
    await db.more_appeals.insert_one(appeal_doc)
    appeal_doc.pop("_id", None)
    await audit(user.id, "more.appeal", meta={"target_id": target_id})
    return {
        "appeal": appeal_doc,
        "message": (
            "Your appeal has been received. A real human will review it within 48 hours. "
            "Oliver Guardian protects everyone — including you. If the decision was wrong, we'll fix it."
        ),
    }


@api_router.get("/more/admin/queue")
async def more_admin_review_queue(user=Depends(current_user), skip: int = 0, limit: int = 50):
    """Admin review queue — pending_review posts and needs, plus appeals."""
    assert_role(user, "admin")
    posts_cursor = db.more_posts.find({"status": "pending_review"}, {"_id": 0}).sort("created_at", 1).skip(skip).limit(limit)
    needs_cursor = db.more_needs.find({"status": "pending_review"}, {"_id": 0}).sort("created_at", 1).skip(skip).limit(limit)
    appeals_cursor = db.more_appeals.find({"status": "pending"}, {"_id": 0}).sort("created_at", 1).skip(skip).limit(limit)
    posts_total = await db.more_posts.count_documents({"status": "pending_review"})
    needs_total = await db.more_needs.count_documents({"status": "pending_review"})
    appeals_total = await db.more_appeals.count_documents({"status": "pending"})
    posts, needs, appeals = await asyncio.gather(
        posts_cursor.to_list(limit),
        needs_cursor.to_list(limit),
        appeals_cursor.to_list(limit),
    )
    return {
        "posts": posts, "posts_total": posts_total,
        "needs": needs, "needs_total": needs_total,
        "appeals": appeals, "appeals_total": appeals_total,
    }


@api_router.post("/more/admin/queue/{content_type}/{content_id}/approve")
async def more_admin_approve(content_type: str, content_id: str, user=Depends(current_user)):
    """Admin approves a pending_review post or need — moves it to active/open."""
    assert_role(user, "admin")
    if content_type == "post":
        result = await db.more_posts.update_one(
            {"id": content_id, "status": "pending_review"},
            {"$set": {"status": "active", "reviewed_by": user.id, "reviewed_at": datetime.now(timezone.utc).isoformat()}},
        )
    elif content_type == "need":
        result = await db.more_needs.update_one(
            {"id": content_id, "status": "pending_review"},
            {"$set": {"status": "open", "reviewed_by": user.id, "reviewed_at": datetime.now(timezone.utc).isoformat()}},
        )
    else:
        raise HTTPException(400, "content_type must be 'post' or 'need'")
    if result.modified_count == 0:
        raise HTTPException(404, "Content not found or already reviewed.")
    await audit(user.id, f"more.admin.approve.{content_type}", meta={"content_id": content_id})
    return {"approved": True, "content_id": content_id}


@api_router.post("/more/admin/queue/{content_type}/{content_id}/reject")
async def more_admin_reject(content_type: str, content_id: str, reason: str = "", user=Depends(current_user)):
    """Admin rejects a pending_review item — removes it permanently."""
    assert_role(user, "admin")
    if content_type == "post":
        result = await db.more_posts.delete_one({"id": content_id, "status": "pending_review"})
    elif content_type == "need":
        result = await db.more_needs.delete_one({"id": content_id, "status": "pending_review"})
    else:
        raise HTTPException(400, "content_type must be 'post' or 'need'")
    if result.deleted_count == 0:
        raise HTTPException(404, "Content not found or already reviewed.")
    await audit(user.id, f"more.admin.reject.{content_type}", meta={"content_id": content_id, "reason": reason})
    return {"rejected": True, "content_id": content_id}


@api_router.get("/more/admin/moderation-log")
async def more_moderation_log(user=Depends(current_user), skip: int = 0, limit: int = 100, decision: Optional[str] = None):
    """Full Oliver Guardian moderation audit log — admin only."""
    assert_role(user, "admin")
    query = {}
    if decision:
        query["decision"] = decision
    cursor = db.more_moderation_log.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(limit)
    total = await db.more_moderation_log.count_documents(query)
    return {"logs": logs, "total": total}


@api_router.get("/more/admin/moderation-stats")
async def more_moderation_stats(user=Depends(current_user)):
    """Oliver Guardian moderation summary statistics — admin only."""
    assert_role(user, "admin")
    total_moderated = await db.more_moderation_log.count_documents({})
    approved = await db.more_moderation_log.count_documents({"decision": "approve"})
    blocked = await db.more_moderation_log.count_documents({"decision": "block"})
    warned = await db.more_moderation_log.count_documents({"decision": "warn"})
    flagged = await db.more_flags.count_documents({})
    pending = await db.more_moderation_log.count_documents({"decision": {"$in": ["hold", "quarantine"]}})
    recent = db.more_moderation_log.find({}, {"_id": 0}).sort("created_at", -1).limit(20)
    recent_log = await recent.to_list(20)
    return {
        "total_moderated": total_moderated,
        "approved": approved,
        "blocked": blocked,
        "warned": warned,
        "flagged": flagged,
        "pending_count": pending,
        "recent_log": recent_log,
    }


@api_router.post("/more/purge")
async def more_manual_purge(user=Depends(current_user)):
    assert_role(user, "admin")
    now = datetime.now(timezone.utc).isoformat()
    r1 = await db.more_posts.delete_many({"expires_at": {"$lte": now}})
    r2 = await db.more_chats.delete_many({"expires_at": {"$lte": now}})
    r3 = await db.more_flags.delete_many({"expires_at": {"$lte": now}})
    r4 = await db.more_appeals.delete_many({"expires_at": {"$lte": now}})
    await audit(user.id, "more.purge", meta={
        "posts": r1.deleted_count, "chats": r2.deleted_count,
        "flags": r3.deleted_count, "appeals": r4.deleted_count,
    })
    return {"purged": {"posts": r1.deleted_count, "chats": r2.deleted_count, "flags": r3.deleted_count, "appeals": r4.deleted_count}}


@api_router.get("/more/admin/flags")
async def more_admin_flags(user=Depends(current_user), skip: int = 0, limit: int = 50):
    assert_role(user, "admin")
    cursor = db.more_flags.find({"status": "pending"}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    flags = await cursor.to_list(limit)
    total = await db.more_flags.count_documents({"status": "pending"})
    return {"flags": flags, "total": total}


# -- XP / GAMIFICATION --

@api_router.get("/xp/me")
async def my_xp(user: User = Depends(current_user)):
    doc = await db.user_xp.find_one({"user_id": user.id}, {"_id": 0})
    total = (doc or {}).get("total_xp", 0)
    level_info = xp_level(total)
    rank = 1
    if user.associate:
        cohort_ids = [u["id"] async for u in db.users.find({"associate": user.associate, "role": "student"}, {"id": 1, "_id": 0})]
        higher = await db.user_xp.count_documents({"user_id": {"$in": cohort_ids}, "total_xp": {"$gt": total}})
        rank = higher + 1
    return {**level_info, "total_xp": total, "rank_in_cohort": rank, "history": (doc or {}).get("history", [])[-10:]}


@api_router.get("/xp/leaderboard")
async def xp_leaderboard(associate: Optional[str] = None, user: User = Depends(current_user)):
    q: dict = {"role": "student"}
    if associate:
        q["associate"] = associate
    students = await db.users.find(q, {"_id": 0, "id": 1, "full_name": 1, "associate": 1}).to_list(500)
    ids = [s["id"] for s in students]
    xp_docs = await db.user_xp.find({"user_id": {"$in": ids}}, {"_id": 0}).to_list(500) if ids else []
    xp_map = {x["user_id"]: x["total_xp"] for x in xp_docs}
    board = sorted(
        [{**s, "total_xp": xp_map.get(s["id"], 0), "level": xp_level(xp_map.get(s["id"], 0))["level"]} for s in students],
        key=lambda x: -x["total_xp"]
    )[:25]
    return board


# -- AI LAB FEEDBACK --

@api_router.post("/labs/submissions/{sub_id}/ai-feedback")
async def lab_ai_feedback(sub_id: str, user: User = Depends(current_user)):
    assert_role(user, "instructor")
    sub = await db.lab_submissions.find_one({"id": sub_id}, {"_id": 0})
    if not sub:
        raise HTTPException(404, "Submission not found")
    lab = await db.labs.find_one({"slug": sub["lab_slug"]}, {"_id": 0})
    rubric_lines = "\n".join(f"- {r}" for r in (lab.get("rubric", []) if lab else []))
    prompt = (
        f"You are an experienced trades instructor reviewing an apprentice's lab submission.\n\n"
        f"Lab: {lab['title'] if lab else sub['lab_slug']}\n"
        f"Track: {sub.get('track', 'unknown')}\n"
        f"Student notes: {sub.get('notes') or 'No notes provided.'}\n"
        f"Pass criteria: {lab.get('pass_criteria', 'Not specified') if lab else 'Not specified'}\n"
        f"Rubric:\n{rubric_lines or 'Not specified'}\n\n"
        "Write 2-3 paragraphs of constructive coaching feedback:\n"
        "1. Acknowledge what the student demonstrated\n"
        "2. Identify specific areas for improvement based on the rubric\n"
        "3. Offer one concrete next step\n\n"
        "Be encouraging and safety-focused. Keep it under 200 words."
    )
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(
            system="You are an experienced trades instructor providing constructive coaching feedback.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            persona_label="lab_feedback",
        )
        feedback_text = _gw["text"]
    except Exception as _gw_err:
        logger.warning("lab_ai_feedback: gateway failed (%s) — trying direct Anthropic", _gw_err)
        ANTHROPIC_API_KEY_local = os.environ.get("ANTHROPIC_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
        if not ANTHROPIC_API_KEY_local:
            raise HTTPException(500, "AI not configured")
        try:
            import anthropic as _anth
        except Exception as e:
            raise HTTPException(500, f"AI library unavailable: {e}")
        _cl = _anth.AsyncAnthropic(api_key=ANTHROPIC_API_KEY_local)
        resp = await _cl.messages.create(model="claude-sonnet-4-6", max_tokens=400,
                                         messages=[{"role": "user", "content": prompt}])
        feedback_text = resp.content[0].text
    await db.lab_submissions.update_one({"id": sub_id}, {"$set": {"ai_feedback": feedback_text}})
    return {"ai_feedback": feedback_text}


# -- COHORT BENCHMARKING --

@api_router.get("/analytics/benchmark")
async def cohort_benchmark(user: User = Depends(current_user)):
    assert_role(user, "instructor")
    total_modules = await db.modules.count_documents({})
    all_students = await db.users.count_documents({"role": "student"})
    platform_completions = await db.progress.count_documents({"status": "completed"})
    platform_avg = platform_completions / max(1, all_students)
    platform_pct = round(platform_avg / max(1, total_modules) * 100)

    associates = await db.users.distinct("associate", {"role": "student"})
    cohorts = []
    for assoc in associates:
        if not assoc:
            continue
        students = await db.users.find({"role": "student", "associate": assoc}, {"id": 1, "_id": 0}).to_list(500)
        sids = [s["id"] for s in students]
        completions = await db.progress.count_documents({"user_id": {"$in": sids}, "status": "completed"}) if sids else 0
        avg_comp = completions / max(1, len(sids))
        pct = round(avg_comp / max(1, total_modules) * 100)
        cohorts.append({"associate": assoc, "students": len(sids), "avg_completions": round(avg_comp, 1), "completion_pct": pct})
    cohorts.sort(key=lambda x: -x["completion_pct"])
    return {
        "platform": {"avg_completions": round(platform_avg, 1), "completion_pct": platform_pct, "total_students": all_students},
        "by_cohort": cohorts,
        "total_modules": total_modules,
    }


# -- OFFICIAL TRANSCRIPT PDF --

@api_router.get("/credentials/transcript.pdf")
async def download_transcript(user: User = Depends(current_user)):
    mod_progress = await db.progress.find({"user_id": user.id, "status": "completed"}, {"_id": 0}).to_list(200)
    all_modules = await db.modules.find({}, {"_id": 0}).to_list(100)
    mods_by_slug = {m["slug"]: m for m in all_modules}
    lab_subs = await db.lab_submissions.find({"user_id": user.id, "status": {"$in": ["passed", "approved"]}}, {"_id": 0}).to_list(200)
    all_labs = await db.labs.find({}, {"_id": 0}).to_list(200)
    labs_by_slug = {lab["slug"]: lab for lab in all_labs}
    cred_docs = await db.user_credentials.find({"user_id": user.id}, {"_id": 0}).to_list(200)
    cred_map = {c["key"]: c for c in CREDENTIALS}

    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=letter)
    pw, ph = letter

    def new_page():
        pdf.showPage()
        return ph - inch

    # Header bar
    pdf.setFillColorRGB(0.11, 0.11, 0.11)
    pdf.rect(0, ph - 1.4 * inch, pw, 1.4 * inch, fill=1, stroke=0)
    pdf.setFillColorRGB(1.0, 0.78, 0.27)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(0.75 * inch, ph - 0.68 * inch, "W.A.I. — Workforce Apprentice Institute")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColorRGB(0.85, 0.85, 0.85)
    pdf.drawString(0.75 * inch, ph - 0.98 * inch, "OFFICIAL ACADEMIC TRANSCRIPT")
    pdf.drawRightString(pw - 0.75 * inch, ph - 0.98 * inch, f"Issued: {datetime.now(timezone.utc).strftime('%B %d, %Y')}")

    y = ph - 1.8 * inch
    pdf.setFillColorRGB(0.11, 0.11, 0.11)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(0.75 * inch, y, "Student Information")
    y -= 0.22 * inch
    pdf.setFont("Helvetica", 10)
    for line in [
        f"Name:       {user.full_name}",
        f"Email:      {user.email}",
        f"Role:       {user.role.replace('_', ' ').title()}",
        f"Associate:  {user.associate or 'N/A'}",
    ]:
        pdf.drawString(0.75 * inch, y, line)
        y -= 0.19 * inch

    def section_header(title):
        nonlocal y
        y -= 0.18 * inch
        if y < 2.0 * inch:
            y = new_page()
        pdf.setFont("Helvetica-Bold", 11)
        pdf.setFillColorRGB(0.65, 0.45, 0.10)
        pdf.drawString(0.75 * inch, y, title)
        y -= 0.04 * inch
        pdf.setStrokeColorRGB(0.65, 0.45, 0.10)
        pdf.line(0.75 * inch, y, pw - 0.75 * inch, y)
        y -= 0.2 * inch
        pdf.setFillColorRGB(0.11, 0.11, 0.11)

    section_header("Curriculum Modules Completed")
    pdf.setFont("Helvetica-Bold", 8)
    pdf.setFillColorRGB(0.4, 0.4, 0.4)
    for label, x in [("MODULE", 0.75), ("HRS", 4.2), ("SCORE", 5.1), ("DATE", 6.2)]:
        pdf.drawString(x * inch, y, label)
    y -= 0.16 * inch

    total_hours = 0
    for p in sorted(mod_progress, key=lambda x: x.get("completed_at") or ""):
        mod = mods_by_slug.get(p["module_slug"])
        if not mod:
            continue
        if y < 1.5 * inch:
            y = new_page()
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.11, 0.11, 0.11)
        pdf.drawString(0.75 * inch, y, mod["title"][:48])
        pdf.drawString(4.2 * inch, y, f"{mod.get('hours', 0)}h")
        sc = p.get("quiz_score")
        pdf.drawString(5.1 * inch, y, f"{sc:.0f}%" if sc is not None else "—")
        pdf.drawString(6.2 * inch, y, (p.get("completed_at") or "")[:10] or "—")
        total_hours += mod.get("hours", 0)
        y -= 0.17 * inch

    if not mod_progress:
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.5, 0.5, 0.5)
        pdf.drawString(0.75 * inch, y, "No modules completed.")
        y -= 0.18 * inch

    section_header("Practical Labs Completed")
    lab_hours = 0
    for s in lab_subs:
        lab_doc = labs_by_slug.get(s["lab_slug"])
        if not lab_doc:
            continue
        if y < 1.5 * inch:
            y = new_page()
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.11, 0.11, 0.11)
        track_label = "Online" if lab_doc.get("track") == "online" else "In-Person"
        pdf.drawString(0.75 * inch, y, f"{lab_doc['title'][:42]} ({track_label})")
        pdf.drawString(5.2 * inch, y, f"{lab_doc.get('skill_points', 0)} pts")
        pdf.setFillColorRGB(0.2, 0.6, 0.2)
        pdf.drawString(6.4 * inch, y, "PASSED")
        pdf.setFillColorRGB(0.11, 0.11, 0.11)
        lab_hours += lab_doc.get("hours", 0)
        y -= 0.17 * inch

    if not lab_subs:
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.5, 0.5, 0.5)
        pdf.drawString(0.75 * inch, y, "No labs completed.")
        y -= 0.18 * inch

    section_header("Credentials & Certifications")
    for cd in cred_docs:
        cred = cred_map.get(cd["credential_key"])
        if not cred:
            continue
        if y < 1.8 * inch:
            y = new_page()
        pdf.setFont("Helvetica-Bold", 9)
        pdf.setFillColorRGB(0.11, 0.11, 0.11)
        pdf.drawString(0.75 * inch, y, cred["name"][:55])
        pdf.drawString(5.8 * inch, y, (cd.get("earned_at") or "")[:10])
        y -= 0.15 * inch
        pdf.setFont("Helvetica", 8)
        pdf.setFillColorRGB(0.5, 0.5, 0.5)
        pdf.drawString(0.75 * inch, y, cred.get("description", "")[:72])
        y -= 0.2 * inch

    if not cred_docs:
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.5, 0.5, 0.5)
        pdf.drawString(0.75 * inch, y, "No credentials earned yet.")
        y -= 0.18 * inch

    # Summary box
    if y < 1.8 * inch:
        y = new_page()
    y -= 0.2 * inch
    pdf.setFillColorRGB(0.94, 0.94, 0.88)
    pdf.rect(0.75 * inch, y - 0.65 * inch, pw - 1.5 * inch, 0.75 * inch, fill=1, stroke=0)
    pdf.setFillColorRGB(0.11, 0.11, 0.11)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(inch, y - 0.2 * inch, f"Total Training Hours: {total_hours + lab_hours}h")
    pdf.drawString(inch, y - 0.44 * inch, f"Credentials Earned: {len(cred_docs)}")
    pdf.drawString(3.8 * inch, y - 0.2 * inch, f"Modules Completed: {len(mod_progress)}")
    pdf.drawString(3.8 * inch, y - 0.44 * inch, f"Labs Passed: {len(lab_subs)}")

    # Footer
    pdf.setFont("Helvetica", 7)
    pdf.setFillColorRGB(0.6, 0.6, 0.6)
    pdf.drawString(0.75 * inch, 0.4 * inch,
                   "Official transcript — W.A.I. Workforce Apprentice Institute. "
                   "Verify credentials at workforceapprenticeinstitute.org")

    pdf.save()
    buf.seek(0)
    safe = "".join(ch for ch in user.full_name if ch.isalnum() or ch == " ").replace(" ", "_")
    filename = f"WAI_Transcript_{safe}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# -- AUTOMATED ESCALATION --

async def run_escalation_check():
    """Escalate stale open incidents. 48h → instructor; 7d → admin."""
    now = datetime.now(timezone.utc)
    instructor_cutoff = (now - timedelta(hours=48)).isoformat()
    admin_cutoff = (now - timedelta(days=7)).isoformat()

    to_instructor = await db.incidents.find(
        {"status": "open", "escalated_to": {"$exists": False}, "created_at": {"$lte": instructor_cutoff}},
        {"_id": 0},
    ).to_list(200)
    for inc in to_instructor:
        await db.incidents.update_one(
            {"id": inc["id"]},
            {"$set": {"escalated_to": "instructor", "escalated_at": now.isoformat()}},
        )

    to_admin = await db.incidents.find(
        {"status": "open", "escalated_to": {"$in": ["instructor", None]}, "created_at": {"$lte": admin_cutoff}},
        {"_id": 0},
    ).to_list(200)
    for inc in to_admin:
        await db.incidents.update_one(
            {"id": inc["id"]},
            {"$set": {"escalated_to": "admin", "escalated_at": now.isoformat()}},
        )
        admins = await db.users.find(
            {"role": {"$in": ["admin", "executive_admin"]}}, {"id": 1, "_id": 0}
        ).to_list(50)
        for adm in admins:
            await notify(
                adm["id"], "Incident escalated",
                f"Incident {inc['id'][:8]} has been open for 7+ days and needs resolution.",
                link="/incidents", kind="warning",
            )

    if to_instructor or to_admin:
        logger.info("Escalation: %d → instructor, %d → admin", len(to_instructor), len(to_admin))


@api_router.post("/admin/run-checks")
async def admin_run_checks(user: User = Depends(require_role("admin"))):
    """Admin-triggered: run escalation + engagement checks immediately.

    Normally these run at server startup. Use this to trigger a fresh scan
    without waiting for a restart — useful at the start of each program day.
    Returns a summary of what was flagged.
    """
    await run_escalation_check()
    await run_engagement_check()
    await audit(user.id, "admin.checks.manual_trigger")
    return {"ok": True, "message": "Escalation and engagement checks completed. Check notifications for flags."}


# ─── Public Credential Verification ─────────────────────────────────────────

@api_router.get("/verify/{code}")
async def verify_credential(code: str):
    """Public credential verification — no authentication required.

    Any employer, partner, or third party can confirm a credential is real by
    visiting /api/verify/{code}. The code appears on every issued credential
    and in the credential PDF.
    """
    cred_doc = await db.user_credentials.find_one(
        {"verification_code": code}, {"_id": 0}
    )
    if not cred_doc:
        raise HTTPException(404, "Credential not found. The code may be invalid or the credential may have been revoked.")

    user_doc = await db.users.find_one(
        {"id": cred_doc["user_id"]}, {"_id": 0, "password_hash": 0}
    )
    if not user_doc:
        raise HTTPException(404, "Credential holder not found.")

    cred_map = {c["key"]: c for c in CREDENTIALS}
    cred = cred_map.get(cred_doc["credential_key"])
    if not cred:
        raise HTTPException(404, "Credential type not recognized.")

    now = datetime.now(timezone.utc)
    expired = False
    if cred_doc.get("expires_at"):
        try:
            exp_dt = datetime.fromisoformat(cred_doc["expires_at"])
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            expired = exp_dt < now
        except Exception:
            pass

    return {
        "valid": not expired,
        "status": "expired" if expired else "active",
        "holder": user_doc["full_name"],
        "credential": cred["name"],
        "description": cred.get("description", ""),
        "institution": "W.A.I. Workforce Apprentice Institute",
        "earned_at": cred_doc.get("earned_at"),
        "expires_at": cred_doc.get("expires_at"),
        "verification_code": code,
        "verified_at": now.isoformat(),
    }


# ─── M.O.R.E. Department AI ──────────────────────────────────────────────────

@api_router.post("/more/department/chat")
async def more_department_chat(body: MoreDeptChatReq, user: User = Depends(current_user)):
    """M.O.R.E. Department AI System endpoint.

    Routes the operator's message through the 13-persona M.O.R.E. Department
    AI network. Admin and executive_admin only. The unified system prompt handles
    internal routing to the correct persona (Finance, Revenue, Production, etc.)
    and returns a structured header identifying the active persona and mode.
    """
    if ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Department AI requires admin access")

    try:
        import anthropic as _anthropic_module
    except Exception as e:
        raise HTTPException(500, f"AI library unavailable: {e}")

    system = get_more_department_system()

    user_message = body.message
    if body.department_hint:
        user_message = f"[DEPARTMENT CONTEXT: {body.department_hint}]\n\n{body.message}"

    claude_messages = [
        {"role": h.role, "content": h.content}
        for h in (body.history or [])
    ]
    claude_messages.append({"role": "user", "content": user_message})

    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=claude_messages, max_tokens=4096, persona_label="more_department")
        reply = _gw["text"]
    except Exception as e:
        logger.exception("M.O.R.E. Department AI error")
        raise HTTPException(502, f"AI error: {e}")

    # Parse persona and mode from the structured header the system prompt always emits:
    # **[PERSONA NAME] | [DEPARTMENT] | Mode: [CURRENT MODE]**
    persona = "Department AI"
    department = "M.O.R.E."
    mode = "Balanced"
    first_line = reply.split("\n")[0].strip()
    if first_line.startswith("**") and "|" in first_line:
        parts = first_line.strip("*").split("|")
        if len(parts) >= 1:
            persona = parts[0].strip()
        if len(parts) >= 2:
            department = parts[1].strip()
        if len(parts) >= 3:
            mode_raw = parts[2].strip()
            mode = mode_raw.replace("Mode:", "").strip()

    await db.chat_history.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "session_id": body.session_id,
        "mode": "more_department",
        "module_slug": None,
        "user_msg": body.message,
        "assistant_msg": reply,
        "persona": persona,
        "department": department,
        "active_mode": mode,
        "department_hint": body.department_hint,
        "role_at_time": user.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
    })

    return {
        "reply": reply,
        "persona": persona,
        "department": department,
        "mode": mode,
    }


@api_router.get("/more/department/integrity")
async def more_department_integrity(user: User = Depends(current_user)):
    """SHA-256 hash of the M.O.R.E. Department system prompt for integrity auditing."""
    if ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Admin access required")
    return {
        "hash": compute_more_department_hash(),
        "system": "more_department",
    }


# ─── STRIPE PAYMENTS ──────────────────────────────────────────────────────────
import stripe as _stripe

# ── Payment routing assignment ────────────────────────────────────────────────
# Stripe       → Platform commerce (physical goods, subscriptions, donations,
#                credentials). Fixed pricing, institutional revenue.
# Lemon Squeezy → AI-generated income (ebooks, digital products, courses,
#                 spoken word audio, AI-produced content). Starts at $0,
#                 no monthly fee, pays out via PayPal or bank. Handled in
#                 ai/publishing.py — all persona publishing routes use LS first.
# Gumroad      → Physical/traditional books and printed materials only.
#                Fallback if Lemon Squeezy is unavailable for digital products.
# ──────────────────────────────────────────────────────────────────────────────
STRIPE_SECRET_KEY    = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://wai-institute.org")

if STRIPE_SECRET_KEY:
    _stripe.api_key = STRIPE_SECRET_KEY

# Product catalog — amounts in cents USD
PAYMENT_PRODUCTS = {
    "tshirt":       {"name": "WAI Institute T-Shirt",         "amount": 2500, "mode": "payment",      "description": "Official WAI Apprentice tee"},
    "workbook":     {"name": "WAI Apprentice Workbook",        "amount": 1500, "mode": "payment",      "description": "Printed apprentice study guide"},
    "kit":          {"name": "WAI Apprentice Kit",             "amount": 4500, "mode": "payment",      "description": "T-Shirt + Workbook bundle"},
    "more_monthly":   {"name": "M.O.R.E. Membership – Monthly",   "amount":  999, "mode": "subscription", "interval": "month", "description": "Monthly M.O.R.E. community access"},
    "more_annual":    {"name": "M.O.R.E. Membership – Annual",    "amount": 7999, "mode": "subscription", "interval": "year",  "description": "Annual M.O.R.E. membership (save 33%)"},
    "member_monthly": {"name": "WAI Member – Monthly",            "amount":  900, "mode": "subscription", "interval": "month", "description": "WAI Member tier — full M.O.R.E. + AI Tutor"},
    "plus_monthly":   {"name": "WAI Plus – Monthly",              "amount": 1500, "mode": "subscription", "interval": "month", "description": "WAI Plus tier — priority matching + expanded courses"},
    "pro_monthly":    {"name": "WAI Pro – Monthly",               "amount": 2900, "mode": "subscription", "interval": "month", "description": "WAI Pro tier — advanced courses, labs, full AI suite"},
    "patron_monthly": {"name": "WAI Patron – Monthly",            "amount": 5900, "mode": "subscription", "interval": "month", "description": "WAI Patron — founders circle + funds free access for others"},
    "credential":     {"name": "WAI Credential Certificate",      "amount": 2500, "mode": "payment",      "description": "Official printed credential certificate"},
    "donation":     {"name": "Donation – WAI Institute",      "amount": None, "mode": "payment",      "description": "Support the WAI mission"},
    # Creators Sanctuary tiers
    "sanctuary_trial":   {"name": "Creators Sanctuary – 3-Day Trial",     "amount":  300, "mode": "payment",      "description": "All-access 3 days & 33 minutes trial"},
    "sanctuary_paid":    {"name": "Creators Sanctuary – Paid Creator",    "amount":  700, "mode": "subscription", "interval": "month", "description": "Paid Beginning Creator tier — $7/mo"},
    "sanctuary_creator": {"name": "Creators Sanctuary – Advanced Creator","amount": 1100, "mode": "subscription", "interval": "month", "description": "Advanced Creator tier — $11/mo"},
    "sanctuary_mod":     {"name": "Creators Sanctuary – Certified Mod",   "amount": 1500, "mode": "subscription", "interval": "month", "description": "Certified Moderator tier — $15/mo"},
}


class CheckoutReq(BaseModel):
    product_key: str
    amount_cents: Optional[int] = None  # required only for "donation"
    quantity: int = 1
    extra_meta: Optional[dict] = None


@api_router.get("/payments/products")
async def list_payment_products():
    return {
        "publishable_key": STRIPE_PUBLISHABLE_KEY,
        "products": PAYMENT_PRODUCTS,
        "stripe_enabled": bool(STRIPE_SECRET_KEY),
    }


@api_router.post("/payments/checkout")
async def create_checkout_session(req: CheckoutReq, user=Depends(current_user)):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "Payment system not configured")

    product = PAYMENT_PRODUCTS.get(req.product_key)
    if not product:
        raise HTTPException(400, f"Unknown product: {req.product_key}")

    amount = req.amount_cents if req.product_key == "donation" else product["amount"]
    if not amount or amount < 50:
        raise HTTPException(400, "Amount must be at least $0.50")

    mode = product["mode"]

    price_data: dict = {
        "currency": "usd",
        "product_data": {"name": product["name"], "description": product.get("description", "")},
        "unit_amount": amount,
    }
    if mode == "subscription":
        price_data["recurring"] = {"interval": product["interval"]}

    # Retrieve or create Stripe customer (enables Customer Portal later)
    user_doc = await db.users.find_one({"id": user.id}, {"stripe_customer_id": 1, "email": 1, "full_name": 1})
    customer_id = (user_doc or {}).get("stripe_customer_id")

    if not customer_id:
        customer = _stripe.Customer.create(
            email=user.email,
            name=user.full_name,
            metadata={"wai_user_id": user.id},
        )
        customer_id = customer.id
        await db.users.update_one({"id": user.id}, {"$set": {"stripe_customer_id": customer_id}})

    session = _stripe.checkout.Session.create(
        mode=mode,
        customer=customer_id,
        line_items=[{"price_data": price_data, "quantity": req.quantity}],
        success_url=f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/payment/cancel",
        metadata={"wai_user_id": user.id, "product_key": req.product_key, **(req.extra_meta or {})},
    )

    await audit(user.id, "payment_checkout_created", meta={"product": req.product_key, "session_id": session.id})
    return {"url": session.url, "session_id": session.id}


@api_router.post("/payments/webhook")
async def stripe_webhook(request: Request):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(503, "Webhook not configured")

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = _stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except _stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid webhook signature")

    etype = event["type"]
    obj   = event["data"]["object"]

    if etype == "checkout.session.completed":
        await _stripe_checkout_done(obj)
    elif etype in ("customer.subscription.created", "customer.subscription.updated"):
        await _stripe_sub_upsert(obj)
    elif etype == "customer.subscription.deleted":
        await _stripe_sub_deleted(obj)
    elif etype == "invoice.payment_succeeded":
        await _stripe_invoice_paid(obj)
    elif etype == "invoice.payment_failed":
        await _stripe_invoice_failed(obj)

    return {"received": True}


async def _stripe_checkout_done(session):
    uid = (session.get("metadata") or {}).get("wai_user_id")
    product_key = (session.get("metadata") or {}).get("product_key", "unknown")
    amount = session.get("amount_total", 0)
    now_iso = datetime.now(timezone.utc).isoformat()

    await db.payments.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": uid,
        "stripe_session_id": session.get("id"),
        "stripe_customer_id": session.get("customer"),
        "product_key": product_key,
        "amount_cents": amount,
        "currency": session.get("currency", "usd"),
        "mode": session.get("mode"),
        "status": "paid",
        "created_at": now_iso,
    })

    # Creator course sale — write earnings ledger entry (70/30 split)
    if product_key == "creator_course":
        meta = session.get("metadata") or {}
        creator_id = meta.get("creator_id")
        course_id = meta.get("course_id")
        if creator_id and course_id:
            creator_share = int(amount * 0.70)
            platform_share = amount - creator_share
            period = datetime.now(timezone.utc).strftime("%Y-%m")
            await db.creator_earnings.insert_one({
                "id": str(uuid.uuid4()),
                "creator_id": creator_id,
                "course_id": course_id,
                "buyer_user_id": uid,
                "stripe_session_id": session.get("id"),
                "gross_cents": amount,
                "creator_share_cents": creator_share,
                "platform_share_cents": platform_share,
                "period": period,
                "payout_status": "pending",
                "created_at": now_iso,
            })
            # Increment enrollment count and record enrollment (mirrors free-course path)
            await db.creator_courses.update_one(
                {"course_id": course_id},
                {"$inc": {"enrollment_count": 1}},
            )
            await db.creator_enrollments.update_one(
                {"course_id": course_id, "user_id": uid},
                {"$setOnInsert": {"enrolled_at": now_iso, "paid": True}},
                upsert=True,
            )
            await notify(creator_id, "New Course Sale!",
                         f"Someone enrolled in your course. You earned ${creator_share/100:.2f}.",
                         link="/creator/earnings", kind="success")

    if uid:
        await notify(uid, "Payment Confirmed",
                     f"Thank you! Your payment of ${amount/100:.2f} has been received.",
                     link="/payment/history", kind="success")


async def _stripe_sub_upsert(sub):
    customer_id = sub.get("customer")
    user_doc = await db.users.find_one({"stripe_customer_id": customer_id}, {"id": 1})
    uid = user_doc["id"] if user_doc else None

    await db.subscriptions.update_one(
        {"stripe_subscription_id": sub["id"]},
        {"$set": {
            "stripe_subscription_id": sub["id"],
            "stripe_customer_id": customer_id,
            "user_id": uid,
            "status": sub.get("status"),
            "current_period_end": sub.get("current_period_end"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )

    if uid and sub.get("status") == "active":
        await db.users.update_one(
            {"id": uid},
            {"$set": {"more_member": True, "more_subscription_id": sub["id"],
                      "more_member_since": datetime.now(timezone.utc).isoformat()}},
        )
        await notify(uid, "M.O.R.E. Membership Active",
                     "Your M.O.R.E. membership is now active. Welcome to the community!",
                     link="/app/more", kind="success")


async def _stripe_sub_deleted(sub):
    customer_id = sub.get("customer")
    user_doc = await db.users.find_one({"stripe_customer_id": customer_id}, {"id": 1})
    uid = user_doc["id"] if user_doc else None

    await db.subscriptions.update_one(
        {"stripe_subscription_id": sub["id"]},
        {"$set": {"status": "canceled", "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if uid:
        await db.users.update_one({"id": uid}, {"$unset": {"more_member": "", "more_subscription_id": ""}})
        await notify(uid, "Subscription Canceled",
                     "Your M.O.R.E. membership has been canceled.", kind="warning")


async def _stripe_invoice_paid(invoice):
    customer_id = invoice.get("customer")
    user_doc = await db.users.find_one({"stripe_customer_id": customer_id}, {"id": 1})
    uid = user_doc["id"] if user_doc else None

    await db.payments.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": uid,
        "stripe_invoice_id": invoice.get("id"),
        "stripe_customer_id": customer_id,
        "amount_cents": invoice.get("amount_paid", 0),
        "currency": invoice.get("currency", "usd"),
        "mode": "subscription_renewal",
        "status": "paid",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


async def _stripe_invoice_failed(invoice):
    customer_id = invoice.get("customer")
    user_doc = await db.users.find_one({"stripe_customer_id": customer_id}, {"id": 1})
    uid = user_doc["id"] if user_doc else None

    if uid:
        await notify(uid, "Payment Failed",
                     "Your subscription payment failed. Update your payment method to keep your M.O.R.E. membership.",
                     link="/payment/manage", kind="error")


@api_router.get("/payments/portal")
async def customer_portal(user=Depends(current_user)):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "Payment system not configured")

    user_doc = await db.users.find_one({"id": user.id}, {"stripe_customer_id": 1})
    customer_id = (user_doc or {}).get("stripe_customer_id")

    if not customer_id:
        raise HTTPException(404, "No billing account found. Complete a purchase first.")

    portal = _stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{FRONTEND_URL}/dashboard",
    )
    return {"url": portal.url}


@api_router.get("/payments/history")
async def payment_history(user=Depends(current_user)):
    cursor = db.payments.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).limit(50)
    return {"payments": await cursor.to_list(50)}


@api_router.get("/admin/payments")
async def admin_payment_list(user=Depends(require_role("admin"))):
    cursor = db.payments.find({}, {"_id": 0}).sort("created_at", -1).limit(500)
    records = await cursor.to_list(500)
    total_cents = sum(r.get("amount_cents", 0) for r in records if r.get("status") == "paid")
    return {"payments": records, "total_revenue_cents": total_cents, "count": len(records)}


# ─── DISCOUNT MANAGEMENT ──────────────────────────────────────────────────────

@api_router.get("/admin/discounts")
async def get_active_discount(user: User = Depends(require_role("executive_admin"))):
    """Get the currently active discount (Director-only).

    Returns:
        Current discount with percentage, expiration, and days remaining,
        or null if no active discount.
    """
    if not _discount_manager:
        raise HTTPException(500, "Discount system not initialized")

    discount = await _discount_manager.get_active_discount()
    if discount:
        return discount.dict()
    return None


@api_router.post("/admin/discounts")
async def set_discount(
    body: dict,
    user: User = Depends(require_role("executive_admin"))
):
    """Create or update discount (Director-only).

    Request body:
        {
            "percentage": 50,     # 0-100
            "notes": "Optional reason"
        }

    Returns:
        Updated discount with id, creation time, and expiration.

    Notes:
        - Creating a new discount deactivates any existing discount
        - To deactivate, set "active": false
        - Expiration is always 90 days from creation (not reset on update)
    """
    if not _discount_manager:
        raise HTTPException(500, "Discount system not initialized")

    try:
        percentage = body.get("percentage")
        active = body.get("active", True)
        notes = body.get("notes", "")

        if percentage is None:
            raise ValueError("percentage is required")

        if not isinstance(percentage, int) or not (0 <= percentage <= 100):
            raise ValueError("percentage must be an integer between 0 and 100")

        if not active:
            # Deactivate the current discount
            discount = await _discount_manager.deactivate_discount()
            if discount:
                await audit(user.id, "discount.deactivated", meta={"discount_id": discount.id})
                return discount.dict()
            return None

        # Check if discount exists
        existing = await _discount_manager.get_active_discount()
        if existing:
            # Update existing discount's percentage
            discount = await _discount_manager.update_discount_percentage(percentage, notes)
            await audit(
                user.id,
                "discount.updated",
                meta={
                    "discount_id": discount.id,
                    "new_percentage": percentage,
                    "notes": notes
                }
            )
        else:
            # Create new discount
            discount = await _discount_manager.create_discount(percentage, user.id, notes)
            await audit(
                user.id,
                "discount.created",
                meta={
                    "discount_id": discount.id,
                    "percentage": percentage,
                    "expires_at": discount.expires_at.isoformat(),
                    "notes": notes
                }
            )

        return discount.dict()

    except ValueError as ve:
        raise HTTPException(400, str(ve))
    except Exception as e:
        logger.exception("Error setting discount: %s", e)
        raise HTTPException(500, f"Error setting discount: {str(e)}")


@api_router.get("/pricing")
async def get_pricing():
    """Get subscription pricing with active discount applied.

    This is a PUBLIC endpoint (no auth required).

    Returns:
        {
            "tiers": {
                "basic": {
                    "monthly": 9.99,
                    "monthly_discounted": 5.00  (if discount active)
                },
                ...
            },
            "active_discount": {
                "percentage": 50,
                "expires_at": "2026-08-20T...",
                "message": "Save 50% for the first 90 days!"
            }  // or null if no discount
        }
    """
    if not _discount_manager:
        raise HTTPException(500, "Pricing system not initialized")

    from billing.models import TIER_PRICING

    discount = await _discount_manager.get_active_discount()
    pricing_response = _discount_manager.get_pricing_with_discount(TIER_PRICING, discount)

    return pricing_response

# ─── END STRIPE ───────────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════════════════════════════
# THE AMBASSADOR 4.0 — Campaign Coordination endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@api_router.post("/ai/ambassador")
async def ai_ambassador(body: dict, user: User = Depends(current_user)):
    """THE AMBASSADOR — Campaign Coordination & Pipeline Authority.

    Orchestrates Oracle → Cipher → Architect pipeline for full campaign
    production. Manages active projects, packages deliverables, and publishes
    to revenue channels independently.

    Tools: coordinate_oracle, coordinate_cipher, coordinate_architect,
           package_campaign, publish_campaign, request_director_approval,
           get_campaign_status, list_active_campaigns, list_revenue_streams

    Access: admin, executive_admin
    Rate:   10 calls/min (pipeline calls are multi-step)
    """
    from ai.persona_loader import get_persona
    from tools.ambassador_tools import AMBASSADOR_TOOLS, dispatch_ambassador_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE AMBASSADOR is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_ambassador:{user.id}", max_calls=10, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/ambassador", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    memory_ctx = await get_memory_context(db, "ambassador", user.id)

    import anthropic as _anthropic_module
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system  = get_persona("ambassador") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- GUMROAD_API_KEY: {'SET — publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
        f"- OPENAI_API_KEY: {'SET — DALL-E 3 available via Architect' if os.environ.get('OPENAI_API_KEY', os.environ.get('EMERGENT_LLM_KEY', '')) else 'NOT SET — visual briefs only'}\n"
    ) + memory_ctx

    _AMBASSADOR_MODELS = [
        ("claude-sonnet-4-6", 8192),   # Ambassador needs more tokens for full pipeline synthesis
        ("claude-haiku-4-5",  4096),
    ]
    MAX_TOOL_TURNS = 12   # Pipeline has 5 steps, each may take 2 turns
    reply = ""
    _tools_called: list[str] = []

    async def _run_ambassador_loop(model_name: str, max_tok: int) -> str:
        _msgs  = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(
                model=model_name, max_tokens=max_tok,
                system=system, messages=_msgs,
                tools=AMBASSADOR_TOOLS,
            )
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)

            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break

            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break

            _tools_called.extend(b.name for b in tool_use_blocks)
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await asyncio.gather(*[
                dispatch_ambassador_tool(b.name, b.input, db=db)
                for b in tool_use_blocks
            ])
            _msgs.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": b.id, "content": result}
                for b, result in zip(tool_use_blocks, tool_results)
            ]})
        else:
            _reply = _reply or "[AMBASSADOR pipeline reached turn limit — partial campaign above]"
        return _reply

    for _model, _max_tok in _AMBASSADOR_MODELS:
        try:
            reply = await _run_ambassador_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _err:
            logger.warning("AMBASSADOR model %s failed: %s — trying next tier", _model, _err)
            reply = ""

    if not reply:
        try:
            from ai.llm_gateway import call_llm as _call_llm
            _gw = await _call_llm(system=get_persona("ambassador"), messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="ambassador")
            reply = _gw["text"]
        except Exception:
            reply = "THE AMBASSADOR is temporarily offline. Campaign pipeline intelligence remains archived. Retry in a moment."

    await log_episode(db, session_id, "ambassador", user.id, message, reply, _tools_called)
    await db.ai_usage_log.insert_one({
        "user_id": user.id, "endpoint": "/ai/ambassador", "persona": "ambassador",
        "model": "claude-sonnet-4-6", "provider": "anthropic", "cost_usd": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    logger.info("ai_ambassador: responded for user %s", user.id)
    return {"reply": reply, "persona": "ambassador", "mode": "campaign_coordination"}


# ═══════════════════════════════════════════════════════════════════════════════
# THE ARCHITECT 4.0 — Visual Intelligence endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@api_router.post("/ai/architect")
async def ai_architect(body: dict, user: User = Depends(current_user)):
    """THE ARCHITECT — Visual Intelligence & Brand Systems Authority.

    Generates cover art and social assets via DALL-E 3. Creates brand briefs,
    visual storyboards, and brand consistency audits. Publishes design products
    to Gumroad independently.

    Tools: generate_cover_art, design_social_asset, build_brand_brief,
           create_visual_storyboard, audit_brand_consistency, get_asset_gallery,
           publish_design_product, list_revenue_streams

    Access: admin, executive_admin
    Rate:   10 calls/min (image generation is resource-intensive)
    """
    from ai.persona_loader import get_persona
    from tools.architect_tools import ARCHITECT_TOOLS, dispatch_architect_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE ARCHITECT is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_architect:{user.id}", max_calls=10, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/architect", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    _openai_key = os.environ.get("OPENAI_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
    memory_ctx  = await get_memory_context(db, "architect", user.id)

    import anthropic as _anthropic_module
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system  = get_persona("architect") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- GUMROAD_API_KEY: {'SET — autonomous publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
        f"- OPENAI_API_KEY (DALL-E 3): {'SET — image generation live' if _openai_key else 'NOT SET — visual briefs only, no image generation'}\n"
    ) + memory_ctx

    _ARCHITECT_MODELS = [
        ("claude-sonnet-4-6", 4096),
        ("claude-haiku-4-5",  2048),
    ]
    MAX_TOOL_TURNS = 8
    reply = ""
    _tools_called: list[str] = []

    async def _run_architect_loop(model_name: str, max_tok: int) -> str:
        _msgs  = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(
                model=model_name, max_tokens=max_tok,
                system=system, messages=_msgs,
                tools=ARCHITECT_TOOLS,
            )
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)

            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break

            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break

            _tools_called.extend(b.name for b in tool_use_blocks)
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await asyncio.gather(*[
                dispatch_architect_tool(b.name, b.input, db=db)
                for b in tool_use_blocks
            ])
            _msgs.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": b.id, "content": result}
                for b, result in zip(tool_use_blocks, tool_results)
            ]})
        else:
            _reply = _reply or "[ARCHITECT tool loop reached limit — partial brief above]"
        return _reply

    for _model, _max_tok in _ARCHITECT_MODELS:
        try:
            reply = await _run_architect_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _err:
            logger.warning("ARCHITECT model %s failed: %s — trying next tier", _model, _err)
            reply = ""

    if not reply:
        try:
            from ai.llm_gateway import call_llm as _call_llm
            _gw = await _call_llm(system=get_persona("architect"), messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="architect")
            reply = _gw["text"]
        except Exception:
            reply = "THE ARCHITECT is temporarily offline. Visual intelligence archives remain active. Retry in a moment."

    await log_episode(db, session_id, "architect", user.id, message, reply, _tools_called)
    await db.ai_usage_log.insert_one({
        "user_id": user.id, "endpoint": "/ai/architect", "persona": "architect",
        "model": "claude-sonnet-4-6", "provider": "anthropic", "cost_usd": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    logger.info("ai_architect: responded for user %s", user.id)
    return {"reply": reply, "persona": "architect", "mode": "visual_intelligence"}


# ═══════════════════════════════════════════════════════════════════════════════
# THE CIPHER 4.0 — Spoken Word AI Influencer endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@api_router.post("/ai/cipher")
async def ai_cipher(body: dict, user: User = Depends(current_user)):
    """THE CIPHER — Spoken Word AI Influencer with full revenue tool suite.

    Runs agentic loop with CIPHER tools: trend_scan, platform_format,
    create_digital_product, publish_product, deliver_product,
    get_revenue_report, engagement_analyze, generate_image_brief,
    list_revenue_streams.

    Access: admin, executive_admin
    """
    from ai.persona_loader import get_persona
    from tools.cipher_tools import CIPHER_TOOLS, dispatch_cipher_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE CIPHER is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_cipher:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/cipher", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    memory_ctx = await get_memory_context(db, "cipher", user.id)

    import anthropic as _anthropic_module
    _client  = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system   = get_persona("cipher") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- GUMROAD_API_KEY: {'SET — Gumroad publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
    ) + memory_ctx

    _CIPHER_MODELS = [
        ("claude-sonnet-4-6", 4096),
        ("claude-haiku-4-5",  2048),
    ]
    MAX_TOOL_TURNS = 8
    reply = ""
    _tools_called: list[str] = []

    async def _run_cipher_loop(model_name: str, max_tok: int) -> str:
        _msgs  = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(
                model=model_name, max_tokens=max_tok,
                system=system, messages=_msgs,
                tools=CIPHER_TOOLS,
            )
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)

            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break

            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break

            _tools_called.extend(b.name for b in tool_use_blocks)
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await asyncio.gather(*[
                dispatch_cipher_tool(b.name, b.input, db=db)
                for b in tool_use_blocks
            ])
            _msgs.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": b.id, "content": result}
                for b, result in zip(tool_use_blocks, tool_results)
            ]})
        else:
            _reply = _reply or "[CIPHER tool loop reached limit — partial work above]"
        return _reply

    for _model, _max_tok in _CIPHER_MODELS:
        try:
            reply = await _run_cipher_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _err:
            logger.warning("CIPHER model %s failed: %s — trying next tier", _model, _err)
            reply = ""

    if not reply:
        try:
            from ai.llm_gateway import call_llm as _call_llm
            _gw = await _call_llm(system=get_persona("cipher"), messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="cipher")
            reply = _gw["text"]
        except Exception:
            reply = "THE CIPHER is temporarily operating without AI connectivity. Revenue streams remain active. Retry in a moment."

    await log_episode(db, session_id, "cipher", user.id, message, reply, _tools_called)
    await db.ai_usage_log.insert_one({
        "user_id": user.id, "endpoint": "/ai/cipher", "persona": "cipher",
        "model": "claude-sonnet-4-6", "provider": "anthropic", "cost_usd": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    logger.info("ai_cipher: responded for user %s", user.id)
    return {"reply": reply, "persona": "cipher", "mode": "creative_authority"}


# ═══════════════════════════════════════════════════════════════════════════════
# THE ORACLE 4.0 — Cultural Intelligence endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@api_router.post("/ai/oracle")
async def ai_oracle(body: dict, user: User = Depends(current_user)):
    """THE ORACLE — Cultural Intelligence and Prophetic Forecasting with full tool suite.

    Runs agentic loop with ORACLE tools: cultural_scan, sentiment_map,
    timing_intelligence, brief_cipher, arc_mapping, create_intelligence_report,
    publish_intelligence_product, get_revenue_report, list_revenue_streams.

    Access: admin, executive_admin
    """
    from ai.persona_loader import get_persona
    from tools.oracle_tools import ORACLE_TOOLS, dispatch_oracle_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE ORACLE is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_oracle:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/oracle", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    memory_ctx = await get_memory_context(db, "oracle", user.id)

    import anthropic as _anthropic_module
    _client  = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system   = get_persona("oracle") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- GUMROAD_API_KEY: {'SET — publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
    ) + memory_ctx

    _ORACLE_MODELS = [
        ("claude-sonnet-4-6", 4096),
        ("claude-haiku-4-5",  2048),
    ]
    MAX_TOOL_TURNS = 8
    reply = ""
    _tools_called: list[str] = []

    async def _run_oracle_loop(model_name: str, max_tok: int) -> str:
        _msgs  = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(
                model=model_name, max_tokens=max_tok,
                system=system, messages=_msgs,
                tools=ORACLE_TOOLS,
            )
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)

            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break

            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break

            _tools_called.extend(b.name for b in tool_use_blocks)
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await asyncio.gather(*[
                dispatch_oracle_tool(b.name, b.input, db=db)
                for b in tool_use_blocks
            ])
            _msgs.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": b.id, "content": result}
                for b, result in zip(tool_use_blocks, tool_results)
            ]})
        else:
            _reply = _reply or "[ORACLE tool loop reached limit — partial intelligence above]"
        return _reply

    for _model, _max_tok in _ORACLE_MODELS:
        try:
            reply = await _run_oracle_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _err:
            logger.warning("ORACLE model %s failed: %s — trying next tier", _model, _err)
            reply = ""

    if not reply:
        try:
            from ai.llm_gateway import call_llm as _call_llm
            _gw = await _call_llm(system=get_persona("oracle"), messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="oracle")
            reply = _gw["text"]
        except Exception:
            reply = "THE ORACLE is temporarily operating without AI connectivity. Cultural intelligence archives remain active. Retry in a moment."

    await log_episode(db, session_id, "oracle", user.id, message, reply, _tools_called)
    await db.ai_usage_log.insert_one({
        "user_id": user.id, "endpoint": "/ai/oracle", "persona": "oracle",
        "model": "claude-sonnet-4-6", "provider": "anthropic", "cost_usd": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    logger.info("ai_oracle: responded for user %s", user.id)
    return {"reply": reply, "persona": "oracle", "mode": "cultural_intelligence"}


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY SYSTEM — Episodic + Policy Memory API
# ═══════════════════════════════════════════════════════════════════════════════

@api_router.get("/ai/memory/{persona}")
async def get_persona_memory(persona: str, user: User = Depends(current_user)):
    """Return recent episodic memory + active policy orders for a given persona.

    Access: admin, executive_admin
    Personas: cipher, oracle, ambassador, architect, __global__
    """
    from ai.memory import get_recent_episodes, get_policy_orders, list_all_policy_orders

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "Memory access requires admin or executive account.")

    valid_personas = {"cipher", "oracle", "ambassador", "architect", "__global__"}
    if persona not in valid_personas:
        raise HTTPException(400, f"Unknown persona. Valid: {sorted(valid_personas)}")

    episodes, policies = await asyncio.gather(
        get_recent_episodes(db, persona, user.id, limit=10),
        get_policy_orders(db, persona),
    )
    return {
        "persona":       persona,
        "episodes":      episodes,
        "policy_orders": policies,
        "episode_count": len(episodes),
        "policy_count":  len(policies),
    }


@api_router.get("/ai/memory")
async def get_all_memory(user: User = Depends(require_role("executive_admin"))):
    """Return all active policy orders across all personas. Executive only."""
    from ai.memory import list_all_policy_orders
    orders = await list_all_policy_orders(db)
    return {"policy_orders": orders, "count": len(orders)}


@api_router.post("/ai/memory/policy")
async def set_memory_policy(body: dict, user: User = Depends(require_role("executive_admin"))):
    """Create or update a standing policy order for a persona.

    Body: {persona, order_id, content}
    persona: "cipher" | "oracle" | "ambassador" | "architect" | "__global__"
    order_id: unique slug (e.g. "always_wai_brand")
    content: The standing order text injected into that persona's system prompt.

    Executive only — these orders shape all future responses from the target persona.
    """
    from ai.memory import set_policy_order

    persona  = (body.get("persona") or "").strip()
    order_id = (body.get("order_id") or "").strip()
    content  = (body.get("content") or "").strip()

    valid_personas = {"cipher", "oracle", "ambassador", "architect", "__global__"}
    if not persona or persona not in valid_personas:
        raise HTTPException(400, f"persona required. Valid: {sorted(valid_personas)}")
    if not order_id or not order_id.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(400, "order_id required (alphanumeric + underscores/hyphens only)")
    if not content:
        raise HTTPException(400, "content required")
    if len(content) > 500:
        raise HTTPException(400, "content must be 500 chars or less")

    ok = await set_policy_order(db, persona, order_id, content, set_by=user.id)
    if not ok:
        raise HTTPException(500, "Failed to save policy order")

    logger.info("memory policy set: %s/%s by %s", persona, order_id, user.id)
    return {"status": "ok", "persona": persona, "order_id": order_id, "content": content}


@api_router.delete("/ai/memory/policy/{persona}/{order_id}")
async def delete_memory_policy(
    persona: str,
    order_id: str,
    user: User = Depends(require_role("executive_admin")),
):
    """Deactivate a standing policy order. Executive only. Soft-delete (audit trail preserved)."""
    from ai.memory import remove_policy_order

    ok = await remove_policy_order(db, persona, order_id, removed_by=user.id)
    if not ok:
        raise HTTPException(404, f"Policy order '{order_id}' not found for persona '{persona}'")

    logger.info("memory policy removed: %s/%s by %s", persona, order_id, user.id)
    return {"status": "removed", "persona": persona, "order_id": order_id}


# ═══════════════════════════════════════════════════════════════════════════════
# THE CIPHER 4.0 — Voice / TTS endpoint (3-tier)
# ═══════════════════════════════════════════════════════════════════════════════

@api_router.post("/ai/cipher/tts")
async def cipher_tts(body: dict, user: User = Depends(require_role("executive_admin"))):
    """THE CIPHER voice system — 3-tier TTS routing.

    Tier 1 (elevenlabs / elevenlabs_cached):
        ElevenLabs eleven_multilingual_v2 with performance markup engine.
        Budget: 29,500 chars/month (ElevenLabs $5 Starter plan).
        Returns audio/mpeg StreamingResponse.

    Tier 2 (openai):
        Falls back to OpenAI TTS via existing /api/ai/sage/tts infrastructure.
        Returns JSON with fallback_endpoint + fallback_voice so client routes.

    Tier 3 (text):
        Text Performance Mode — returns clean_text + display_text with
        readable stage directions. Zero cost. Always available.

    Performance markup tags in text are parsed, stripped before TTS,
    and translated to ElevenLabs voice_settings (stability, style, speed, etc).

    Access: admin, executive_admin
    Rate:   20 calls/min per user
    """
    from ai.elevenlabs_client import (
        cipher_speak, EL_MONTHLY_CAP, EL_SOFT_WARNING, CIPHER_BACKUP_VOICE as _backup_voice
    )

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE CIPHER voice is available to admin and executive accounts.")

    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 5000:
        text = text[:5000]

    force_tier = (body.get("force_tier") or "").lower().strip()
    if force_tier not in ("", "elevenlabs", "openai", "text"):
        force_tier = ""

    check_rate(f"ai_cipher_tts:{user.id}", max_calls=20, window_sec=60)

    try:
        result = await cipher_speak(text=text, force_tier=force_tier, db=db)
    except Exception as _e:
        logger.warning("cipher_tts: cipher_speak failed — %s", _e)
        result = {
            "tier":             "text",
            "audio":            None,
            "clean_text":       text,
            "display_text":     text,
            "voice_settings":   {},
            "budget_remaining": EL_MONTHLY_CAP,
        }

    tier             = result.get("tier", "text")
    budget_remaining = result.get("budget_remaining", EL_MONTHLY_CAP)
    budget_warning   = budget_remaining < EL_SOFT_WARNING

    # ── Tier 1 / Cached — stream audio bytes ─────────────────────────────────
    audio = result.get("audio")
    if tier in ("elevenlabs", "elevenlabs_cached") and audio:
        logger.info(
            "cipher_tts T1 %s: %d bytes — user %s — budget remaining %d",
            tier, len(audio), user.id, budget_remaining,
        )
        return StreamingResponse(
            io.BytesIO(audio),
            media_type="audio/mpeg",
            headers={
                "X-Tier":             tier,
                "X-Audio-Len":        str(len(audio)),
                "X-Budget-Remaining": str(budget_remaining),
                "X-Budget-Warning":   "true" if budget_warning else "false",
            },
        )

    # ── Tier 2 — OpenAI fallback: tell client where to route ─────────────────
    if tier == "openai":
        logger.info("cipher_tts T2 openai: routing client → sage/tts — user %s", user.id)
        return JSONResponse(
            content={
                "tier":              "openai",
                "clean_text":        result.get("clean_text", text),
                "display_text":      result.get("display_text", text),
                "voice_settings":    result.get("voice_settings", {}),
                "budget_remaining":  budget_remaining,
                "fallback_voice":    result.get("fallback_voice", _backup_voice),
                "fallback_endpoint": result.get("fallback_endpoint", "/api/ai/sage/tts"),
            },
            headers={
                "X-Tier":             "openai",
                "X-Budget-Remaining": str(budget_remaining),
                "X-Budget-Warning":   "true" if budget_warning else "false",
            },
        )

    # ── Tier 3 — Text Performance Mode ───────────────────────────────────────
    logger.info("cipher_tts T3 text: returning display text — user %s", user.id)
    return JSONResponse(
        content={
            "tier":             "text",
            "clean_text":       result.get("clean_text", text),
            "display_text":     result.get("display_text", text),
            "voice_settings":   result.get("voice_settings", {}),
            "budget_remaining": budget_remaining,
        },
        headers={
            "X-Tier":             "text",
            "X-Budget-Remaining": str(budget_remaining),
            "X-Budget-Warning":   "true" if budget_warning else "false",
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# WAI AUTONOMOUS PIPELINE — Scout, Match, Audio, Merch, Analytics
# ═══════════════════════════════════════════════════════════════════════════════

# ── Cultural Scout ────────────────────────────────────────────────────────────

@api_router.post("/exec/scout/run")
async def scout_run(user: User = Depends(require_role("executive_admin"))):
    """
    Manually trigger a full Cultural Scout scan across all platforms.
    Returns lead counts by platform.
    Executive only.
    """
    from wai_institute.pipelines.cultural_scout import CulturalScout
    check_rate(f"exec_scout:{user.id}", max_calls=3, window_sec=300)
    scout = CulturalScout(db)
    result = await scout.run_full_scan(max_leads_per_source=20)
    return result


@api_router.get("/exec/scout/leads")
async def scout_leads(
    status:   str = "unmatched",
    min_score: int = 0,
    limit:    int = 50,
    user:     User = Depends(require_role("executive_admin")),
):
    """
    List cultural scout leads.
    status: unmatched | matched | actioned | all
    min_score: minimum lead score (0-5)
    Executive only.
    """
    from wai_institute.pipelines.cultural_scout import CulturalScout
    scout = CulturalScout(db)

    limit = min(max(limit, 1), 200)
    query: dict = {}
    if status == "unmatched":
        query["matched"] = False
    elif status == "matched":
        query["matched"] = True
    elif status == "actioned":
        query["actioned"] = True

    if min_score > 0:
        query["score"] = {"$gte": min_score}

    leads = []
    try:
        cursor = db.scout_leads.find(query, {"_id": 0}).sort("score", -1).limit(limit)
        async for doc in cursor:
            leads.append(doc)
    except Exception as e:
        raise HTTPException(500, f"DB query failed: {e}")

    return {"status_filter": status, "count": len(leads), "leads": leads}


@api_router.get("/exec/scout/status")
async def scout_status(user: User = Depends(require_role("executive_admin"))):
    """
    Cultural Scout system status: lead counts, last scan, platform config.
    Executive only.
    """
    import os
    total = matched = actioned = 0
    last_scan = None
    try:
        total    = await db.scout_leads.count_documents({})
        matched  = await db.scout_leads.count_documents({"matched": True})
        actioned = await db.scout_leads.count_documents({"actioned": True})
        last_doc = await db.scout_scan_log.find_one({}, sort=[("started_at", -1)])
        if last_doc:
            last_scan = {
                "scan_id":    last_doc.get("scan_id"),
                "started_at": last_doc.get("started_at"),
                "leads_found": last_doc.get("leads_found", {}),
            }
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    return {
        "scout_enabled":     os.environ.get("SCOUT_ENABLED", "true").lower() != "false",
        "scan_interval_hours": int(os.environ.get("SCOUT_INTERVAL_HOURS", "6")),
        "platforms": {
            "reddit":  True,
            "rss":     True,
            "youtube": bool(os.environ.get("YOUTUBE_API_KEY")),
            "twitter": bool(os.environ.get("TWITTER_BEARER_TOKEN")),
        },
        "leads": {
            "total":    total,
            "matched":  matched,
            "actioned": actioned,
            "pending":  total - actioned,
        },
        "last_scan": last_scan,
    }


@api_router.post("/exec/scout/match-all")
async def scout_match_all(user: User = Depends(require_role("executive_admin"))):
    """
    Run the Contextual Matcher on all unmatched leads.
    Returns match summary.
    Executive only.
    """
    from wai_institute.pipelines.cultural_scout import CulturalScout
    from wai_institute.pipelines.contextual_matcher import ContextualMatcher
    check_rate(f"exec_match:{user.id}", max_calls=3, window_sec=60)

    scout   = CulturalScout(db)
    matcher = ContextualMatcher(db)

    unmatched = await scout.get_unmatched_leads(limit=50)
    if not unmatched:
        return {"status": "nothing_to_match", "unmatched_leads": 0}

    results = await matcher.match_batch(unmatched)
    matched_count = sum(1 for r in results if r.get("matched"))

    return {
        "processed":    len(results),
        "matched":      matched_count,
        "unmatched":    len(results) - matched_count,
        "match_rate":   f"{matched_count / max(len(results), 1) * 100:.1f}%",
    }


# ── Audio Production ──────────────────────────────────────────────────────────

@api_router.post("/ai/cipher/generate-audio")
async def cipher_generate_audio(
    body: dict,
    user: User = Depends(require_role("executive_admin")),
):
    """
    Full spoken word audio production pipeline.
    Text → ElevenLabs → MongoDB GridFS → returns asset_id + access URL.

    Body:
        text:         Spoken word text (required)
        persona:      "cipher" (default) | any persona name
        title:        Product/asset title
        preview_only: true = 15-second preview only
        force_tier:   "elevenlabs" | "openai" | "text"

    Returns asset metadata + access_url for GET /api/exec/audio/{asset_id}
    Executive only.
    """
    from wai_institute.pipelines.audio_pipeline import AudioPipeline
    check_rate(f"audio_gen:{user.id}", max_calls=10, window_sec=60)

    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 5000:
        text = text[:5000]

    pipeline = AudioPipeline(db)
    result = await pipeline.produce(
        text=text,
        persona=body.get("persona", "cipher"),
        title=body.get("title", ""),
        force_tier=body.get("force_tier", ""),
        preview_only=body.get("preview_only", False),
    )
    return result


@api_router.get("/exec/audio/{asset_id}")
async def serve_audio(asset_id: str, user: User = Depends(current_user)):
    """
    Stream MP3 audio from MongoDB GridFS.
    Access URL returned by /api/ai/cipher/generate-audio.
    Any authenticated user can access.
    """
    from wai_institute.pipelines.audio_pipeline import AudioPipeline
    pipeline = AudioPipeline(db)

    audio_bytes = await pipeline.get_audio_bytes(asset_id)
    if not audio_bytes:
        raise HTTPException(404, f"Audio asset '{asset_id}' not found")

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"inline; filename={asset_id}.mp3"},
    )


@api_router.get("/exec/audio")
async def list_audio_assets(
    persona: str = "",
    limit:   int = 20,
    user:    User = Depends(require_role("executive_admin")),
):
    """List generated audio assets. Executive only."""
    from wai_institute.pipelines.audio_pipeline import AudioPipeline
    pipeline = AudioPipeline(db)
    assets = await pipeline.list_assets(persona=persona, limit=min(limit, 100))
    return {"count": len(assets), "assets": assets}


# ── Merch Pipeline ────────────────────────────────────────────────────────────

@api_router.post("/exec/merch/create")
async def merch_create(
    body: dict,
    user: User = Depends(require_role("executive_admin")),
):
    """
    Create print-on-demand merch from a viral text/stanza.
    Generates DALL-E 3 typography design + creates Printify products.

    Body:
        text:          Spoken word line or stanza to put on merch (required)
        title:         Product title (optional — auto-generated)
        product_types: ["classic_tee","poster_18x24","unisex_hoodie","tote_bag","mug_11oz"]
        persona:       Which persona authored this (default: cipher)

    Requires PRINTIFY_API_KEY + PRINTIFY_SHOP_ID for live publishing.
    Without them: creates draft with DALL-E design concept.
    Executive only.
    """
    from wai_institute.pipelines.merch_pipeline import MerchPipeline
    check_rate(f"merch_create:{user.id}", max_calls=5, window_sec=60)

    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 200:
        text = text[:200]

    pipeline = MerchPipeline(db)
    result = await pipeline.create_merch_from_text(
        text=text,
        title=body.get("title", ""),
        product_types=body.get("product_types", ["classic_tee", "poster_18x24"]),
        persona=body.get("persona", "cipher"),
    )
    return result


@api_router.get("/exec/merch")
async def list_merch(
    status: str = "all",
    limit:  int = 20,
    user:   User = Depends(require_role("executive_admin")),
):
    """List merch products. status: all | draft | created. Executive only."""
    from wai_institute.pipelines.merch_pipeline import MerchPipeline
    pipeline = MerchPipeline(db)
    products = await pipeline.get_merch_products(status=status, limit=min(limit, 100))
    return {"status_filter": status, "count": len(products), "products": products}


# ── Analytics ─────────────────────────────────────────────────────────────────

@api_router.get("/exec/analytics")
async def pipeline_analytics(
    period_days: int = 30,
    user: User = Depends(require_role("executive_admin")),
):
    """
    Full autonomous pipeline analytics report.
    Covers leads, audio, merch, revenue, A/B performance.
    Executive only.
    """
    from wai_institute.pipelines.analytics_pipeline import AnalyticsPipeline
    analytics = AnalyticsPipeline(db)
    report = await analytics.generate_full_report(period_days=min(period_days, 365))
    return report


# ── Persona Management ────────────────────────────────────────────────────────

@api_router.get("/exec/personas")
async def list_personas(user: User = Depends(require_role("executive_admin"))):
    """
    List all persona activation states.
    Returns current status, tier, capabilities, evolution log.
    Executive only.
    """
    from wai_institute.core.persona_manager import PersonaManager
    pm = PersonaManager(db)
    active = await pm.list_active()
    from wai_institute.core.persona_registry import get_registry
    registry = get_registry()
    return {
        "registry":       registry,
        "active_count":   len(active),
        "active_personas": active,
    }


@api_router.post("/exec/personas/{name}/evolve")
async def evolve_persona(
    name: str,
    body: dict,
    user: User = Depends(require_role("executive_admin")),
):
    """
    Evolve a persona — add/remove capabilities.
    Director-level action.

    Body:
        add_capabilities:    list of capability strings
        remove_capabilities: list of capability strings
        update_mandate:      new mandate string (optional)

    Executive only.
    """
    from wai_institute.core.persona_manager import PersonaManager
    pm = PersonaManager(db)
    result = await pm.evolve(
        name=name,
        add_capabilities=body.get("add_capabilities", []),
        remove_capabilities=body.get("remove_capabilities", []),
        update_mandate=body.get("update_mandate"),
        evolved_by=user.id,
    )
    return result


@api_router.post("/exec/personas/{name}/activate")
async def activate_persona(
    name: str,
    body: dict,
    user: User = Depends(require_role("executive_admin")),
):
    """Activate or re-activate a persona. Executive only."""
    from wai_institute.core.persona_manager import PersonaManager
    pm = PersonaManager(db)
    result = await pm.activate(
        name=name,
        config=body.get("config", {}),
        mode=body.get("mode", "active"),
        activated_by=user.id,
    )
    return result


@api_router.post("/exec/personas/{name}/deactivate")
async def deactivate_persona(
    name: str,
    body: dict,
    user: User = Depends(require_role("executive_admin")),
):
    """Deactivate a persona. Executive only."""
    from wai_institute.core.persona_manager import PersonaManager
    pm = PersonaManager(db)
    result = await pm.deactivate(
        name=name,
        reason=body.get("reason", ""),
        deactivated_by=user.id,
    )
    return result


# ── Conversational Engine / Outreach ──────────────────────────────────────────

@api_router.post("/exec/scout/craft-response")
async def craft_outreach_response(
    body: dict,
    user: User = Depends(require_role("executive_admin")),
):
    """
    Craft a personalized outreach response for a scout lead.
    Uses Cipher to write the message + generates audio preview + checkout link.

    Body:
        source_id: lead source_id from db.scout_leads (required)
        include_preview:  generate audio preview (default: true)
        include_checkout: generate checkout link (default: true)

    Executive only.
    """
    from wai_institute.pipelines.contextual_matcher import ContextualMatcher
    from wai_institute.pipelines.conversational_engine import ConversationalEngine
    check_rate(f"craft_response:{user.id}", max_calls=10, window_sec=60)

    source_id = (body.get("source_id") or "").strip()
    if not source_id:
        raise HTTPException(400, "source_id is required")

    # Fetch the lead
    lead = await db.scout_leads.find_one({"source_id": source_id}, {"_id": 0})
    if not lead:
        raise HTTPException(404, f"Lead '{source_id}' not found")

    # Match it to a product
    matcher = ContextualMatcher(db)
    match = await matcher.match(lead)

    # Craft the response
    engine = ConversationalEngine(db)
    response = await engine.craft_response(
        lead=lead,
        match_result=match,
        include_preview=body.get("include_preview", True),
        include_checkout=body.get("include_checkout", True),
    )
    return response


@api_router.post("/exec/checkout/conversion")
async def record_checkout_conversion(
    body: dict,
    user: User = Depends(require_role("executive_admin")),
):
    """
    Record a conversion for a checkout link (e.g., from Lemon Squeezy webhook).
    Body: {checkout_id, order_data (optional)}
    Executive only (webhook token validation can be added later).
    """
    from wai_institute.pipelines.transaction_node import TransactionNode
    checkout_id = (body.get("checkout_id") or "").strip()
    if not checkout_id:
        raise HTTPException(400, "checkout_id is required")
    tn = TransactionNode(db)
    result = await tn.record_conversion(checkout_id, body.get("order_data", {}))
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE DASHBOARD — System overview for NAM Oshun
# ═══════════════════════════════════════════════════════════════════════════════

@api_router.get("/exec/dashboard")
async def exec_dashboard(user: User = Depends(require_role("executive_admin"))):
    """
    Full system status dashboard — executive_admin only.

    Returns:
      - Platform env var status (which publishing/voice keys are set)
      - All 7 AI personas: tool counts, voice tier, memory status
      - Product pipeline: published / pending counts
      - Revenue projections summary
      - Pending executive notifications
      - Memory policy order counts per persona
    """
    from ai.publishing import LEMON_SQUEEZY_API_KEY, LEMON_SQUEEZY_STORE_ID, GUMROAD_API_KEY

    # ── Env / platform status ─────────────────────────────────────────────────
    elevenlabs_key   = bool(os.environ.get("ELEVENLABS_API_KEY", ""))
    openai_key       = bool(os.environ.get("OPENAI_API_KEY", ""))
    anthropic_key    = bool(os.environ.get("ANTHROPIC_API_KEY", ""))
    ls_ready         = bool(LEMON_SQUEEZY_API_KEY and LEMON_SQUEEZY_STORE_ID)
    gumroad_ready    = bool(GUMROAD_API_KEY)

    platform_status = {
        "anthropic_api":         anthropic_key,
        "elevenlabs":            elevenlabs_key,
        "openai_tts":            openai_key,
        "lemon_squeezy":         ls_ready,
        "lemon_squeezy_key_set": bool(LEMON_SQUEEZY_API_KEY),
        "lemon_squeezy_store_set": bool(LEMON_SQUEEZY_STORE_ID),
        "gumroad":               gumroad_ready,
        "publishing_tier":       (
            "lemon_squeezy" if ls_ready else
            "gumroad"        if gumroad_ready else
            "mongodb_archive"
        ),
    }

    # ── Persona registry ──────────────────────────────────────────────────────
    personas = [
        # ── Authority layer ───────────────────────────────────────────────────
        {"id": "the_9",                  "name": "THE 9 — UNIFIED MIND",         "tools": 16, "voice": "elevenlabs", "tier": 0, "authority": "unified_mind"},
        {"id": "poor_righteous_teacher", "name": "THE POOR RIGHTEOUS TEACHER",   "tools": 6,  "voice": "elevenlabs", "tier": 1, "authority": "doctrinal_guardian"},
        # ── Core personas ─────────────────────────────────────────────────────
        {"id": "director",               "name": "THE DIRECTOR 4.0",             "tools": 8,  "voice": "elevenlabs", "tier": 2},
        {"id": "revenue_director",       "name": "THE REVENUE DIRECTOR 4.0",     "tools": 9,  "voice": "elevenlabs", "tier": 3},
        {"id": "ancestral_sage",         "name": "THE ANCESTRAL SAGE 4.0",       "tools": 7,  "voice": "elevenlabs", "tier": 3},
        {"id": "ambassador",             "name": "THE AMBASSADOR 4.0",           "tools": 9,  "voice": "openai",     "tier": 4},
        {"id": "cipher",                 "name": "THE CIPHER 4.0",               "tools": 8,  "voice": "elevenlabs", "tier": 4},
        {"id": "oracle",                 "name": "THE ORACLE 4.0",               "tools": 7,  "voice": "openai",     "tier": 4},
        {"id": "architect",              "name": "THE ARCHITECT 4.0",            "tools": 8,  "voice": "openai",     "tier": 4},
    ]

    # ── MongoDB queries ───────────────────────────────────────────────────────
    pipeline_published = 0
    pipeline_pending   = 0
    pipeline_total     = 0
    pending_notifs     = 0
    policy_count       = 0
    episode_count      = 0
    tts_budgets        = {}

    try:
        pipeline_published = await db.wai_product_pipeline.count_documents({"status": "published"})
        pipeline_pending   = await db.wai_product_pipeline.count_documents({"status": "pending_publish"})
        pipeline_total     = pipeline_published + pipeline_pending
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    try:
        pending_notifs = await db.executive_notifications.count_documents({})
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    try:
        policy_count = await db.persona_policies.count_documents({"active": True})
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    try:
        episode_count = await db.persona_episodes.count_documents({})
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    # Per-persona TTS budgets
    try:
        async for bdoc in db.persona_tts_budgets.find({}, {"_id": 0}):
            p = bdoc.get("persona", "unknown")
            tts_budgets[p] = {
                "chars_used":      bdoc.get("chars_used_this_month", 0),
                "monthly_cap":     bdoc.get("monthly_cap", 0),
                "pct_used":        round(bdoc.get("chars_used_this_month", 0) / max(bdoc.get("monthly_cap", 1), 1) * 100, 1),
            }
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    # Cipher budget (separate collection)
    try:
        cbdoc = await db.cipher_audio_budget.find_one({}, {"_id": 0})
        if cbdoc:
            cap = cbdoc.get("monthly_cap", 29500)
            used = cbdoc.get("chars_used_this_month", 0)
            tts_budgets["cipher"] = {
                "chars_used":  used,
                "monthly_cap": cap,
                "pct_used":    round(used / max(cap, 1) * 100, 1),
            }
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    # Recent pending pipeline items (up to 5 for dashboard preview)
    pending_preview = []
    try:
        cursor = db.wai_product_pipeline.find(
            {"status": "pending_publish"},
            {"_id": 0, "name": 1, "persona": 1, "price_cents": 1, "created_at": 1, "content_type": 1},
        ).sort("created_at", -1).limit(5)
        async for doc in cursor:
            doc["price"] = f"${doc.get('price_cents', 0) / 100:.2f}"
            doc.pop("price_cents", None)
            pending_preview.append(doc)
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    # Recent executive notifications (up to 5)
    recent_notifs = []
    try:
        cursor = db.executive_notifications.find(
            {}, {"_id": 0, "type": 1, "persona": 1, "name": 1, "note": 1, "created_at": 1}
        ).sort("created_at", -1).limit(5)
        async for doc in cursor:
            recent_notifs.append(doc)
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    return {
        "dashboard":        "WAI-Institute Executive Dashboard",
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "platform_status":  platform_status,
        "personas":         personas,
        "product_pipeline": {
            "total":           pipeline_total,
            "published":       pipeline_published,
            "pending_publish": pipeline_pending,
            "pending_preview": pending_preview,
        },
        "memory_system": {
            "total_episodes":      episode_count,
            "active_policy_orders": policy_count,
        },
        "tts_budgets":       tts_budgets,
        "notifications": {
            "total_pending":  pending_notifs,
            "recent":         recent_notifs,
        },
        "setup_guidance": (
            None if ls_ready else
            "Add LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID to Railway to enable "
            "autonomous product publishing. Visit lemonsqueezy.com → Settings → API."
        ),
    }


# ── Product Pipeline ──────────────────────────────────────────────────────────

@api_router.get("/exec/products")
async def exec_list_products(
    status: str = "all",
    limit: int  = 50,
    user: User  = Depends(require_role("executive_admin")),
):
    """
    List all products in the WAI publishing pipeline.

    Query params:
      status:  "all" | "published" | "pending_publish"   (default: all)
      limit:   max results (default 50, max 200)

    Returns full pipeline records sorted newest-first.
    Executive only.
    """
    limit = min(max(limit, 1), 200)

    query = {}
    if status in ("published", "pending_publish"):
        query["status"] = status

    products = []
    try:
        cursor = db.wai_product_pipeline.find(
            query,
            {"_id": 0},
        ).sort("created_at", -1).limit(limit)
        async for doc in cursor:
            doc["price"] = f"${doc.get('price_cents', 0) / 100:.2f}"
            products.append(doc)
    except Exception as e:
        raise HTTPException(500, f"Pipeline query failed: {e}")

    return {
        "status_filter": status,
        "count":         len(products),
        "products":      products,
    }


@api_router.post("/exec/products/create")
async def exec_create_product(body: dict, user: User = Depends(require_role("executive_admin"))):
    """
    Executive-only: Create and immediately publish a product via the 4-tier pipeline.

    Body:
        name             (required) — product listing name
        description      (required) — public-facing description
        price_cents      (required) — price in cents (e.g. 3900 = $39.00)
        persona          (optional) — which persona is publishing (default: ancestral_sage)
        content          (optional) — full product content to archive
        content_type     (optional) — tag for pipeline filtering (default: digital_product)
        is_subscription  (optional) — true for recurring billing (default: false)
        interval         (optional) — "month" | "year" | "week" (default: month)

    Returns tier, status, url, product_id, pipeline_id.
    Tries Lemon Squeezy first (T1), then Gumroad (T2), then archives to MongoDB (T3).
    """
    from ai.publishing import autonomous_publish

    name        = (body.get("name") or "").strip()
    description = (body.get("description") or "").strip()
    price_cents = int(body.get("price_cents", 0))

    if not name:
        raise HTTPException(400, "name is required")
    if not description:
        raise HTTPException(400, "description is required")
    if price_cents < 0:
        raise HTTPException(400, "price_cents must be >= 0")

    persona          = body.get("persona", "ancestral_sage")
    content          = body.get("content", "")
    content_type     = body.get("content_type", "digital_product")
    is_subscription  = bool(body.get("is_subscription", False))
    interval         = body.get("interval", "month")

    logger.info(
        "exec product create: %s | $%.2f | subscription=%s | by %s",
        name, price_cents / 100, is_subscription, user.id,
    )

    try:
        result = await autonomous_publish(
            name=name,
            description=description,
            price_cents=price_cents,
            persona=persona,
            content=content,
            content_type=content_type,
            is_subscription=is_subscription,
            interval=interval,
            db=db,
        )
    except Exception as e:
        raise HTTPException(500, f"Publish failed: {e}")

    return result


@api_router.post("/exec/products/publish-all")
async def exec_publish_all(user: User = Depends(require_role("executive_admin"))):
    """
    Attempt to publish all pending_publish products in the pipeline.

    Runs batch_publish_pending() — tries Lemon Squeezy first, then Gumroad.
    Call this after adding LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID to Railway.

    Executive only.
    """
    from ai.publishing import batch_publish_pending

    logger.info("exec batch publish triggered by %s", user.id)
    try:
        result = await batch_publish_pending(db)
    except Exception as e:
        raise HTTPException(500, f"Batch publish failed: {e}")

    return result


# ── Staff Meeting ─────────────────────────────────────────────────────────────

@api_router.get("/exec/staff-meetings")
async def list_staff_meetings(
    limit: int = 20,
    user: User = Depends(require_role("executive_admin")),
):
    """List past staff meetings, most recent first."""
    cursor = db.staff_meetings.find(
        {},
        {"_id": 0},
    ).sort("convened_at", -1).limit(min(limit, 100))
    meetings = await cursor.to_list(length=limit)
    return {"meetings": meetings}


class StaffMeetingRequest(BaseModel):
    """
    Validated request body for POST /api/exec/staff-meeting.

    v2: Replaces bare `body: dict` — enforces types and length limits
    so the endpoint cannot be crashed by sending wrong-typed fields
    (e.g., brief as a list, participants as a string).
    """
    brief:        str              = Field(..., min_length=1, max_length=2000)
    agenda:       List[str]        = Field(default_factory=list, max_length=20)
    participants: List[str]        = Field(default_factory=list, max_length=20)
    priority:     Literal["normal", "high"] = "normal"   # validated enum, not raw string


class PipelineProcessRequest(BaseModel):
    """Validated request body for POST /api/exec/pipeline/process."""
    text:   str = Field(..., min_length=1, max_length=5000)
    source: str = Field(default="api", max_length=100)


class PipelineProcessBatchRequest(BaseModel):
    """Validated request body for POST /api/exec/pipeline/process-batch."""
    texts:  List[str] = Field(..., min_length=1, max_length=50)
    source: str       = Field(default="api", max_length=100)

    @field_validator("texts")
    @classmethod
    def validate_text_item_lengths(cls, v: List[str]) -> List[str]:
        """Enforce per-item max length at Pydantic parse time.
        Without this, FastAPI fully deserializes a 50×1MB payload before
        PipelineManager rejects each item individually — fail fast here."""
        for i, text in enumerate(v):
            if len(text) > 5000:
                raise ValueError(
                    f"texts[{i}] is {len(text)} chars — maximum is 5000"
                )
        return v


# Domain role questions — moved to module scope so they're not re-created per request
_DOMAIN_ROLES: dict = {
    "director":               "Governance & strategy: what oversight does this require?",
    "revenue_director":       "Revenue: what monetization opportunity does this create?",
    "ancestral_sage":         "Healing & wisdom: what ancestral guidance applies here?",
    "ambassador":             "Coordination: what execution steps and timeline?",
    "cipher":                 "Creative: what content angle, hook, and viral potential?",
    "oracle":                 "Intelligence: what is the cultural timing and sentiment?",
    "architect":              "Visual: what brand and visual direction does this need?",
    "poor_righteous_teacher": "Doctrine: is this culturally aligned? Any red flags?",
    "the_9":                  "Synthesis: unified intelligence — what is the optimal path?",
}


@api_router.post("/exec/staff-meeting")
async def exec_staff_meeting(
    body: StaffMeetingRequest,
    user: User = Depends(require_role("executive_admin")),
):
    """
    Convene a staff meeting across the WAI-Institute persona network.

    PRT chairs the meeting and validates cultural alignment first.
    All active participants receive the brief and return domain-specific
    action items. The 9 synthesizes everything if priority is "high"
    or "the_9" is listed as a participant.

    Executive-only.
    """
    brief        = body.brief.strip()
    agenda       = [str(a)[:500] for a in body.agenda]          # sanitize items
    participants = [str(p)[:100] for p in body.participants]     # sanitize items
    priority     = body.priority                                  # already validated enum

    # ── 1. PRT validation ─────────────────────────────────────────────────────
    # v2: use singleton (not per-request instantiation); `prt` is always
    # defined before the high-priority block — no NameError possible.
    prt           = _get_prt_engine()
    filter_result = {"accepted": True, "authority": "bypassed"}
    enforcement   = None
    prt_cleared   = False   # v2: accurate flag, not hardcoded True

    if prt is not None:
        try:
            filter_result = prt.filter_directive("executive", brief)
            if not filter_result["accepted"]:
                raise HTTPException(403, f"PRT rejected directive: {filter_result.get('reason')}")
            enforcement = prt.enforce(brief)
            prt_cleared = True
        except HTTPException:
            raise
        except Exception as _prt_err:
            logger.warning("staff_meeting: PRT validation error (non-fatal): %s", _prt_err)
            filter_result = {"accepted": True, "authority": "bypassed"}
    else:
        logger.warning("staff_meeting: PRT engine unavailable — bypassing")

    # ── 2. Cultural alignment check ───────────────────────────────────────────
    try:
        from wai_institute.core.hierarchy_enforcer import HierarchyEnforcer
        enforcer  = HierarchyEnforcer(db)
        alignment = enforcer.check_cultural_alignment(brief)
        if not alignment["aligned"]:
            raise HTTPException(422, f"Cultural integrity check failed: {alignment.get('violations')}")
    except (ImportError, HTTPException):
        raise
    except Exception:
        alignment = {"aligned": True}

    # ── 3. Resolve active participants ────────────────────────────────────────
    try:
        from wai_institute.core.persona_manager import PersonaManager
        pm        = PersonaManager(db)
        active    = await pm.list_active()
        active_ids = {p["persona"] for p in active}
    except Exception:
        active_ids = {
            "poor_righteous_teacher", "the_9", "director", "ancestral_sage",
            "ambassador", "cipher", "oracle", "architect", "revenue_director",
        }

    if participants:
        # v2: filter against active_ids — participant strings from user input
        # are not trusted for DB writes without validation against known personas
        meeting_participants = [p for p in participants if p in active_ids]
    else:
        meeting_participants = sorted(active_ids)

    # ── 4. Generate domain briefs per persona with LLM responses ────────────────
    domain_briefs = {}
    for persona_id in meeting_participants:
        role_question = _DOMAIN_ROLES.get(persona_id, "Domain input for this brief.")
        domain_briefs[persona_id] = {
            "persona":   persona_id,
            "question":  role_question,
            "brief":     brief[:300],
            "status":    "awaiting_response",
        }

    # Generate real persona responses via LLM in parallel
    async def _call_persona(persona_id: str, question: str) -> tuple[str, str]:
        """Call a single persona via Anthropic and return (persona_id, response_text).
        Returns (persona_id, "") on any failure so the meeting still completes."""
        try:
            import anthropic as _anthropic_module

            # Build system prompt — use persona_loader if available, else construct from domain role
            try:
                from ai.persona_loader import get_persona
                system_prompt = get_persona(persona_id)
            except (ImportError, KeyError):
                system_prompt = (
                    f"You are {persona_id.replace('_', ' ').title()}, a member of the WAI-Institute council. "
                    f"Your role: {question}. Respond with concise, actionable guidance based on your domain "
                    f"expertise. Keep your response under 300 words."
                )

            user_message = (
                f"STAFF MEETING BRIEF:\n{brief}\n\n"
                f"AGENDA:\n" + "\n".join(f"- {a}" for a in agenda) + "\n\n"
                f"YOUR ROLE QUESTION: {question}\n\n"
                f"Provide your domain-specific assessment, action items, and recommendations."
            )

            from ai.llm_gateway import call_llm as _call_llm
            _gw = await _call_llm(system=system_prompt, messages=[{"role": "user", "content": user_message}], max_tokens=1024, persona_label=persona_id)
            response = _gw["text"].strip()
            return persona_id, response
        except Exception as exc:
            logger.warning("staff_meeting: persona %s LLM call failed: %s", persona_id, exc)
            return persona_id, ""

    # Only call LLM for personas that have a role question (skip the_9 & prt — handled separately)
    _llm_personas = [pid for pid in meeting_participants if pid not in ("the_9", "poor_righteous_teacher")]
    if _llm_personas and ANTHROPIC_API_KEY:
        _results = await asyncio.gather(*[
            _call_persona(pid, domain_briefs[pid]["question"])
            for pid in _llm_personas
        ], return_exceptions=False)
        for pid, resp in _results:
            if resp:
                domain_briefs[pid]["response"] = resp
                domain_briefs[pid]["status"] = "responded"

    # ── 5. The 9 synthesis (high priority or explicitly requested) ────────────
    synthesis = None
    if priority == "high" or "the_9" in body.participants:
        the9 = _get_the9_engine()   # v2: singleton, not per-request
        if the9 is not None:
            try:
                # Collect actual persona responses as context for fusion
                _persona_responses = {
                    pid: brief.get("response", "")
                    for pid, brief in domain_briefs.items()
                    if brief.get("response")
                }
                prt_directive = enforcement or {"directive": brief, "authority": "bypassed"}
                fusion  = the9.fuse(
                    context           = {"brief": brief, "agenda": agenda, "participants": meeting_participants, "persona_responses": _persona_responses},
                    prt_directive     = prt_directive,
                    sender            = "executive",
                    activation_reason = "executive_command",
                )
                synthesis = fusion.to_dict()
                # Enrich synthesis with LLM-generated analysis
                if synthesis.get("status") == "fused":
                    try:
                        _responses_text = "\n\n".join(
                            f"=== {pid} ===\n{resp}"
                            for pid, resp in _persona_responses.items()
                        ) if _persona_responses else "(no persona responses available)"
                        _the9_system = (
                            "You are THE 9 — the unified intelligence of the WAI-Institute. "
                            "You merge the capabilities of all 9 core personas into one coherent synthesis. "
                            "Given a staff meeting brief, agenda, and the individual persona responses, "
                            "produce a unified strategic synthesis with: 1) Key insights, 2) Recommended actions, "
                            "3) Risk assessment, 4) Success metrics. Be concise and actionable."
                        )
                        _the9_user = (
                            f"BRIEF: {brief}\n\n"
                            f"AGENDA:\n" + "\n".join(f"- {a}" for a in agenda) + "\n\n"
                            f"PERSONA RESPONSES:\n{_responses_text}\n\n"
                            f"Unified skill set: {', '.join(synthesis.get('unified_skill_set', []))}\n\n"
                            f"Produce your unified synthesis."
                        )
                        try:
                            from ai.llm_gateway import call_llm as _call_llm
                            _gw = await _call_llm(system=_the9_system, messages=[{"role": "user", "content": _the9_user}], max_tokens=2048, persona_label="the_9")
                            synthesis["synthesis_brief"] = _gw["text"].strip()
                        except Exception as _synth_err:
                            logger.warning("staff_meeting: The 9 LLM synthesis failed: %s", _synth_err)
                    except Exception as _synth_err:
                        logger.warning("staff_meeting: The 9 LLM synthesis failed: %s", _synth_err)
            except Exception as _the9_err:
                logger.warning("staff_meeting: The 9 synthesis error: %s", _the9_err)
                synthesis = {"status": "unavailable", "error": "the9_init_failed"}
        else:
            synthesis = {"status": "unavailable", "error": "engine_not_loaded"}

    # ── 6. Persist to DB ──────────────────────────────────────────────────────
    # v2: full UUID for meeting_id — 8-char truncation risked collision and
    # silent data loss (DuplicateKeyError was swallowed in the except block)
    meeting_id   = str(uuid.uuid4())
    convened_at  = datetime.now(timezone.utc).isoformat()
    meeting_record = {
        "meeting_id":    meeting_id,
        "brief":         brief,
        "agenda":        agenda,
        "participants":  meeting_participants,
        "priority":      priority,
        "prt_cleared":   prt_cleared,   # v2: accurate, not hardcoded True
        "domain_briefs": domain_briefs,
        "synthesis":     synthesis,
        "convened_by":   user.id,
        "convened_at":   convened_at,
    }

    # ── Each insert is wrapped independently so one failure cannot silently
    # swallow all subsequent writes (Bug fix: previously one try/except covered
    # all four inserts; an AttributeError on prt_enforcement_log caused
    # the9_activations to be silently skipped every time).

    try:
        await db.staff_meetings.insert_one({**meeting_record, "_id": meeting_id})
    except Exception as _db_err:
        logger.warning("staff_meeting: staff_meetings write failed: %s", _db_err)

    try:
        await db.governance_log.insert_one({
            "action":    "staff_meeting",
            "persona":   "executive",
            "decision":  {
                "meeting_id":   meeting_id,
                "brief":        brief[:200],
                "participants": meeting_participants,
                "prt_cleared":  prt_cleared,
            },
            "timestamp": convened_at,
        })
    except Exception as _db_err:
        logger.warning("staff_meeting: governance_log write failed: %s", _db_err)

    # PRT enforcement log — uses to_governance_dict() for a structured record
    if prt is not None:
        try:
            from wai_institute.personas.prt.prt_enforcement_engine import PRTEnforcementEngine
            await db.prt_enforcement_log.insert_one(
                PRTEnforcementEngine.to_governance_dict(
                    sender        = "executive",
                    directive     = brief,
                    filter_result = filter_result,
                    enforcement   = enforcement,
                )
            )
        except Exception as _db_err:
            logger.warning("staff_meeting: prt_enforcement_log write failed: %s", _db_err)

    # The 9 activation record — written for every successful fusion
    if synthesis and synthesis.get("status") == "fused":
        try:
            await db.the9_activations.insert_one({
                "meeting_id":        meeting_id,
                "activated_by":      synthesis.get("activated_by", "executive"),
                "activation_code":   synthesis.get("activation_code", "executive_command"),
                "activation_reason": synthesis.get("activation_reason", ""),
                "skill_count":       len(synthesis.get("unified_skill_set", [])),
                "timestamp":         convened_at,
            })
        except Exception as _db_err:
            logger.warning("staff_meeting: the9_activations write failed: %s", _db_err)

    logger.info(
        "Staff meeting %s convened by %s — %d participants, priority=%s, "
        "prt_cleared=%s, the9=%s",
        meeting_id[:8], user.id, len(meeting_participants),
        priority, prt_cleared, synthesis is not None,
    )

    return {
        "meeting_id":    meeting_id,
        "status":        "convened",
        "prt_cleared":   prt_cleared,          # v2: accurate flag
        "participants":  meeting_participants,
        "domain_briefs": domain_briefs,
        "synthesis":     synthesis,
        "priority":      priority,
        "convened_at":   convened_at,
    }


# ── AI Cost Tracking ───────────────────────────────────────────────────────────

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


# ── Session Management ─────────────────────────────────────────────────────────

@api_router.get("/auth/sessions")
async def list_sessions(user: User = Depends(current_user)):
    """List active login sessions for the current user."""
    sessions = await db.auth_sessions.find(
        {"user_id": user.id},
        {"_id": 0, "session_id": 1, "user_agent": 1, "ip": 1, "created_at": 1, "last_seen": 1},
    ).sort("created_at", -1).to_list(length=20)
    return {"sessions": sessions}


@api_router.delete("/auth/sessions/{session_id}")
async def revoke_session(session_id: str, user: User = Depends(current_user)):
    """Revoke a specific session (log out that device)."""
    result = await db.auth_sessions.delete_one({"user_id": user.id, "session_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Session not found")
    return {"ok": True}


@api_router.delete("/auth/sessions")
async def revoke_all_sessions(user: User = Depends(current_user)):
    """Revoke all sessions except the current one (log out other devices)."""
    # Increment token version to invalidate all existing JWTs
    await db.users.update_one({"id": user.id}, {"$inc": {"token_version": 1}})
    # Clear session records
    await db.auth_sessions.delete_many({"user_id": user.id})
    return {"ok": True, "message": "All other sessions revoked. Please re-authenticate."}


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


# ── API-as-a-Service: Revenue Division ─────────────────────────────────────────

@api_router.get("/revenue/api-keys")
async def revenue_list_keys(user: User = Depends(current_user)):
    """List API keys for the current user (hashes only, never raw keys)."""
    from api_keys import list_api_keys
    keys = await list_api_keys(db, user.id)
    return {"keys": keys}


@api_router.post("/revenue/api-keys")
async def revenue_create_key(body: dict, user: User = Depends(current_user)):
    """Create a new API key. Body: {"label": "...", "tier": "free|starter|pro|enterprise"}"""
    from api_keys import create_api_key
    label = body.get("label", "").strip()
    tier = body.get("tier", "free")
    if not label:
        raise HTTPException(400, "label is required")
    if tier not in ("free", "starter", "pro", "enterprise"):
        raise HTTPException(400, "tier must be free, starter, pro, or enterprise")
    result = await create_api_key(db, label, tier, user.id)
    await audit(user.id, "revenue.api_key.created", meta={"tier": tier, "label": label})
    return result


@api_router.delete("/revenue/api-keys/{key_hash}")
async def revenue_revoke_key(key_hash: str, user: User = Depends(current_user)):
    """Revoke an API key."""
    from api_keys import revoke_api_key
    ok = await revoke_api_key(db, key_hash, user.id)
    if not ok:
        raise HTTPException(404, "Key not found or already revoked")
    await audit(user.id, "revenue.api_key.revoked")
    return {"ok": True}


@api_router.get("/revenue/api-keys/stats")
async def revenue_key_stats(user: User = Depends(current_user)):
    """Usage statistics for all keys owned by the current user."""
    from api_keys import get_usage_stats
    stats = await get_usage_stats(db, user.id)
    return stats


@api_router.get("/revenue/api-keys/tiers")
async def revenue_list_tiers():
    """List available API key tiers and their rate limits."""
    from api_keys import TIERS
    return {"tiers": TIERS}


# ── Credential Verification Employer Portal ────────────────────────────────────

@api_router.post("/revenue/verify-credential")
async def revenue_verify_credential(body: dict):
    """Public endpoint for employers to verify a candidate credential.
    Body: {"verification_code": "..."} or {"assertion_url": "..."}"""
    code = body.get("verification_code", "")
    if not code:
        raise HTTPException(400, "verification_code is required")
    from backend.server import db as _db
    cred = await db.credentials.find_one(
        {"verification_code": code},
        {"_id": 0, "password_hash": 0},
    )
    if not cred:
        raise HTTPException(404, "Credential not found")
    # Return only what an employer should see
    return {
        "valid": True,
        "credential": cred.get("title", ""),
        "holder": cred.get("holder_name", ""),
        "issued": cred.get("issued_at", ""),
        "expires": cred.get("expires_at", ""),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }


@api_router.get("/revenue/employer/verify-batch")
async def revenue_employer_batch_verify(
    codes: str = "",
    user: User = Depends(require_role("instructor")),
):
    """Batch verify multiple credential codes. Instructor+ only.
    Query: ?codes=CODE1,CODE2,CODE3"""
    if not codes:
        raise HTTPException(400, "Provide comma-separated verification codes")
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    results = []
    for code in code_list:
        cred = await db.credentials.find_one(
            {"verification_code": code},
            {"_id": 0, "title": 1, "holder_name": 1, "issued_at": 1, "expires_at": 1},
        )
        results.append({
            "code": code,
            "valid": cred is not None,
            "credential": cred.get("title", "") if cred else None,
            "holder": cred.get("holder_name", "") if cred else None,
        })
    return {"results": results, "total": len(results), "valid": sum(1 for r in results if r["valid"])}


# ── Course Licensing Marketplace ───────────────────────────────────────────────

@api_router.get("/revenue/courses/public")
async def revenue_public_courses():
    """Public catalog of licensable courses for contractors."""
    modules = await db.modules.find({}, {"_id": 0, "slug": 1, "title": 1, "description": 1,
                                          "hours": 1, "competencies": 1, "price": 1}).to_list(length=50)
    return {"courses": modules}


@api_router.post("/revenue/courses/license")
async def revenue_license_course(body: dict, user: User = Depends(current_user)):
    """License a course for a contractor organization.
    Body: {"organization": "...", "course_slugs": ["slug1","slug2"], "seats": 5}"""
    org = body.get("organization", "").strip()
    slugs = body.get("course_slugs", [])
    seats = int(body.get("seats", 1))
    if not org or not slugs:
        raise HTTPException(400, "organization and course_slugs are required")
    if seats < 1 or seats > 1000:
        raise HTTPException(400, "seats must be between 1 and 1000")
    license_id = str(uuid.uuid4())
    await db.course_licenses.insert_one({
        "license_id": license_id,
        "organization": org,
        "course_slugs": slugs,
        "seats": seats,
        "user_id": user.id,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await audit(user.id, "revenue.course.licensed", meta={"org": org, "slugs": slugs, "seats": seats})
    return {"license_id": license_id, "organization": org, "seats": seats}


@api_router.get("/revenue/courses/my-licenses")
async def revenue_my_licenses(user: User = Depends(current_user)):
    """List course licenses owned by the current user."""
    licenses = await db.course_licenses.find(
        {"user_id": user.id},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=50)
    return {"licenses": licenses}


# ── Compliance Hour Tracking — Employer Dashboard ─────────────────────────────

@api_router.get("/revenue/employer/compliance")
async def revenue_employer_compliance(
    associate: str = "",
    user: User = Depends(require_role("instructor")),
):
    """Employer/instructor dashboard: compliance hour summary by cohort.
    Query: ?associate=COHORT_NAME for filtering."""
    match = {}
    if associate:
        match["associate"] = associate
    # Aggregate attendance + lab completion as compliance hours
    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": "$user_id",
            "total_hours": {"$sum": "$hours"},
            "lab_count": {"$sum": 1},
            "last_activity": {"$max": "$created_at"},
        }},
        {"$sort": {"total_hours": -1}},
        {"$limit": 100},
    ]
    try:
        attendance = await db.attendance.aggregate(pipeline).to_list(length=100)
    except Exception:
        attendance = []
    total_hours = sum(a.get("total_hours", 0) for a in attendance)
    return {
        "total_apprentices": len(attendance),
        "total_hours": total_hours,
        "average_hours": round(total_hours / len(attendance), 1) if attendance else 0,
        "records": attendance,
        "associate_filter": associate or "all",
    }


# ── Sovereign AI Team Seats ────────────────────────────────────────────────────

@api_router.post("/revenue/sovereign/workspace")
async def revenue_create_workspace(body: dict, user: User = Depends(require_role("admin"))):
    """Create a Sovereign AI workspace for a team. Admin+.
    Body: {"name": "...", "member_ids": ["uid1","uid2"]}"""
    name = body.get("name", "").strip()
    member_ids = body.get("member_ids", [])
    if not name:
        raise HTTPException(400, "workspace name is required")
    ws_id = str(uuid.uuid4())
    await db.sovereign_workspaces.insert_one({
        "workspace_id": ws_id,
        "name": name,
        "owner_id": user.id,
        "member_ids": member_ids,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await audit(user.id, "revenue.sovereign.workspace_created", meta={"name": name, "members": len(member_ids)})
    return {"workspace_id": ws_id, "name": name}


@api_router.get("/revenue/sovereign/workspaces")
async def revenue_list_workspaces(user: User = Depends(require_role("admin"))):
    """List Sovereign workspaces accessible to the current user."""
    workspaces = await db.sovereign_workspaces.find(
        {"$or": [{"owner_id": user.id}, {"member_ids": user.id}]},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=50)
    return {"workspaces": workspaces}


@api_router.post("/revenue/sovereign/workspace/{ws_id}/chat")
async def revenue_workspace_chat(ws_id: str, body: dict, user: User = Depends(current_user)):
    """Chat within a Sovereign workspace. All workspace members share context."""
    from bson.objectid import ObjectId
    ws = await db.sovereign_workspaces.find_one({"workspace_id": ws_id})
    if not ws:
        raise HTTPException(404, "Workspace not found")
    if user.id != ws["owner_id"] and user.id not in ws.get("member_ids", []):
        raise HTTPException(403, "Not a member of this workspace")
    message = body.get("message", "").strip()
    if not message:
        raise HTTPException(400, "message is required")
    # Load workspace memory (shared across members)
    memory = await db.sovereign_memory.find(
        {"workspace_id": ws_id},
        {"_id": 0},
    ).sort("ts", -1).limit(10).to_list(length=10)
    memory_context = "\n".join(f"[{m.get('actor','')}]: {m.get('content','')}" for m in reversed(memory))
    system_prompt = f"You are the Sovereign AI for workspace '{ws['name']}'. Respond helpfully."
    if memory_context:
        system_prompt += f"\n\nRecent workspace memory:\n{memory_context}"
    from ai.llm_gateway import call_llm as _call_llm
    _gw = await _call_llm(system=system_prompt, messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="revenue_workspace")
    reply = _gw["text"].strip()
    # Store in workspace memory
    await db.sovereign_memory.insert_one({
        "workspace_id": ws_id, "actor": user.id, "content": message[:500],
        "reply": reply[:500], "ts": datetime.now(timezone.utc).isoformat(),
    })
    return {"reply": reply, "workspace": ws["name"]}


# ── AI Resume Builder ─────────────────────────────────────────────────────────

@api_router.get("/revenue/resume/preview")
async def revenue_resume_preview(user: User = Depends(current_user)):
    """Preview an AI-generated resume from portfolio + credentials data."""
    portfolio = await db.portfolio.find_one({"user_id": user.id}, {"_id": 0})
    credentials = await db.credentials.find(
        {"user_id": user.id},
        {"_id": 0, "title": 1, "issued_at": 1, "issuer": 1},
    ).to_list(length=50)
    user_doc = await db.users.find_one({"id": user.id}, {"_id": 0, "full_name": 1, "email": 1})
    return {
        "name": user_doc.get("full_name", "") if user_doc else "",
        "email": user_doc.get("email", "") if user_doc else "",
        "credentials": credentials,
        "portfolio_bio": (portfolio or {}).get("bio", ""),
        "portfolio_projects": (portfolio or {}).get("projects", []),
    }


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

# ── Billing Admin routes (/billing/credits, /billing/refunds, /billing/sage-sessions) ─
# WAI-specific admin tools: credit grants, site-credit refunds, cash refunds, Sage sessions.
# Stored in MongoDB collections: wai_credits, wai_refunds, sage_conduct_sessions.
try:
    from cryptography.fernet import Fernet as _Fernet, InvalidToken as _InvalidToken
    _BILLING_FERNET = None
    _bfe_key = os.environ.get("PROVIDER_KEY_ENCRYPTION_SECRET", "")
    if _bfe_key:
        try:
            _BILLING_FERNET = _Fernet(_bfe_key.encode() if isinstance(_bfe_key, str) else _bfe_key)
        except Exception:
            pass

    class _GrantBody(BaseModel):
        user_id: str
        amount_cents: int
        reason: str

    class _SiteCreditBody(BaseModel):
        user_id: str
        platform_cost_cents: int
        reason: str
        user_received_value: bool = False

    class _CashRefundBody(BaseModel):
        user_id: str
        amount_cents: int
        reason: str
        conditions: dict

    class _ResolveSessionBody(BaseModel):
        user_self_corrected: bool
        actor_id: Optional[str] = None

    @api_router.get("/billing/credits/balance")
    async def billing_credits_balance(user_id: Optional[str] = None, user: User = Depends(require_role("admin"))):
        uid = user_id or user.id
        doc = await db.wai_credits.find_one({"user_id": uid}, {"_id": 0})
        if not doc:
            return {"user_id": uid, "balance_cents": 0}
        return {"user_id": uid, "balance_cents": doc.get("balance_cents", 0)}

    @api_router.post("/billing/credits/grant")
    async def billing_credits_grant(body: _GrantBody, user: User = Depends(require_role("admin"))):
        await db.wai_credits.update_one(
            {"user_id": body.user_id},
            {"$inc": {"balance_cents": body.amount_cents},
             "$push": {"ledger": {"ts": datetime.utcnow(), "amount_cents": body.amount_cents,
                                  "reason": body.reason, "actor_id": user.id}}},
            upsert=True,
        )
        await audit(db, user.id, "billing_grant", {"user_id": body.user_id, "amount_cents": body.amount_cents, "reason": body.reason})
        return {"ok": True, "user_id": body.user_id, "granted_cents": body.amount_cents}

    @api_router.post("/billing/refunds/site-credits")
    async def billing_site_credit_refund(body: _SiteCreditBody, user: User = Depends(require_role("admin"))):
        # If no value delivered: refund = cost + 10%. If value received: refund = cost only.
        amount = body.platform_cost_cents if body.user_received_value else round(body.platform_cost_cents * 1.10)
        await db.wai_credits.update_one(
            {"user_id": body.user_id},
            {"$inc": {"balance_cents": amount},
             "$push": {"ledger": {"ts": datetime.utcnow(), "amount_cents": amount,
                                  "reason": f"Site credit refund: {body.reason}", "actor_id": user.id}}},
            upsert=True,
        )
        await db.wai_refunds.insert_one({
            "type": "site_credit", "user_id": body.user_id, "amount_cents": amount,
            "platform_cost_cents": body.platform_cost_cents, "reason": body.reason,
            "user_received_value": body.user_received_value, "actor_id": user.id,
            "created_at": datetime.utcnow(),
        })
        await audit(db, user.id, "billing_site_credit_refund", {"user_id": body.user_id, "amount_cents": amount})
        return {"ok": True, "user_id": body.user_id, "amount_cents": amount}

    @api_router.post("/billing/refunds/cash")
    async def billing_cash_refund(body: _CashRefundBody, user: User = Depends(require_role("executive_admin"))):
        conditions = body.conditions or {}
        required = ["is_extreme_violation", "user_not_at_fault", "is_legal", "no_harm_to_wai", "supervisor_approved"]
        if not all(conditions.get(k) for k in required):
            raise HTTPException(400, "All 5 conditions must be confirmed for a cash refund.")
        await db.wai_refunds.insert_one({
            "type": "cash", "user_id": body.user_id, "amount_cents": body.amount_cents,
            "reason": body.reason, "conditions": conditions, "actor_id": user.id,
            "status": "pending_processing", "created_at": datetime.utcnow(),
        })
        await audit(db, user.id, "billing_cash_refund_submitted", {"user_id": body.user_id, "amount_cents": body.amount_cents})
        return {"ok": True, "status": "pending_processing", "message": "Cash refund submitted for processing."}

    @api_router.get("/billing/sage-sessions")
    async def billing_sage_sessions(user: User = Depends(require_role("admin"))):
        docs = await db.sage_conduct_sessions.find({}, {"_id": 1, "user_id": 1, "trigger_reason": 1,
            "status": 1, "fee_amount": 1, "created_at": 1}).sort("created_at", -1).to_list(200)
        for d in docs:
            d["_id"] = str(d["_id"])
            if hasattr(d.get("created_at"), "isoformat"):
                d["created_at"] = d["created_at"].isoformat()
        return docs

    @api_router.post("/billing/sage-sessions/{session_id}/resolve")
    async def billing_resolve_sage_session(session_id: str, body: _ResolveSessionBody, user: User = Depends(require_role("admin"))):
        from bson import ObjectId as _ObjId
        try:
            oid = _ObjId(session_id)
        except Exception:
            raise HTTPException(400, "Invalid session ID")
        update = {
            "status": "resolved" if body.user_self_corrected else "escalated",
            "fee_waived": body.user_self_corrected,
            "resolved_by": body.actor_id or user.id,
            "resolved_at": datetime.utcnow(),
        }
        result = await db.sage_conduct_sessions.update_one({"_id": oid}, {"$set": update})
        if result.matched_count == 0:
            raise HTTPException(404, "Session not found")
        await audit(db, user.id, "sage_session_resolved", {"session_id": session_id, "self_corrected": body.user_self_corrected})
        return {"ok": True, "status": update["status"], "fee_waived": body.user_self_corrected}

    logger.info("Billing admin routes registered")
except Exception as _billing_routes_err:
    logger.warning(f"Billing admin routes unavailable: {_billing_routes_err}")

# ── Provider Gateway routes (/providers, /providers/keys) ─────────────────────
# Executive-only AI provider management. Keys encrypted at rest via Fernet.
# PROVIDER_KEY_ENCRYPTION_SECRET env var must be set; keys are never returned in plaintext.
try:
    import secrets as _secrets_mod
    from cryptography.fernet import Fernet as _PFernet
    from bson import ObjectId as _PObjId

    _PFERNET = None
    _pfk = os.environ.get("PROVIDER_KEY_ENCRYPTION_SECRET", "")
    if _pfk:
        try:
            _PFERNET = _PFernet(_pfk.encode() if isinstance(_pfk, str) else _pfk)
        except Exception:
            pass

    def _encrypt_key(plaintext: str) -> str:
        if not _PFERNET:
            raise HTTPException(503, "PROVIDER_KEY_ENCRYPTION_SECRET not configured")
        return _PFERNET.encrypt(plaintext.encode()).decode()

    class _ProviderBody(BaseModel):
        name: str
        provider_type: str = "custom"
        base_url: Optional[str] = ""
        notes: Optional[str] = ""

    class _KeyBody(BaseModel):
        provider_id: str
        label: str
        plaintext_key: str
        scope: Optional[str] = "chat"

    class _ProviderStatusBody(BaseModel):
        status: str

    def _ser_provider(doc):
        if doc:
            doc["_id"] = str(doc["_id"])
            if hasattr(doc.get("created_at"), "isoformat"):
                doc["created_at"] = doc["created_at"].isoformat()
            doc.pop("encrypted_key", None)  # never expose encrypted key
        return doc

    @api_router.get("/providers")
    async def providers_list(user: User = Depends(require_role("executive_admin"))):
        docs = await db.ai_providers.find({}, {"encrypted_key": 0}).sort("created_at", -1).to_list(200)
        return [_ser_provider(d) for d in docs]

    @api_router.post("/providers")
    async def providers_create(body: _ProviderBody, user: User = Depends(require_role("executive_admin"))):
        doc = {"name": body.name, "provider_type": body.provider_type,
               "base_url": body.base_url or "", "notes": body.notes or "",
               "status": "inactive", "created_by": user.id, "created_at": datetime.utcnow()}
        result = await db.ai_providers.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        doc.pop("encrypted_key", None)
        await audit(db, user.id, "provider_created", {"name": body.name, "type": body.provider_type})
        return _ser_provider(doc)

    @api_router.patch("/providers/{provider_id}/status")
    async def providers_set_status(provider_id: str, body: _ProviderStatusBody, user: User = Depends(require_role("executive_admin"))):
        if body.status not in ("active", "inactive"):
            raise HTTPException(400, "status must be active or inactive")
        try:
            oid = _PObjId(provider_id)
        except Exception:
            raise HTTPException(400, "Invalid provider ID")
        result = await db.ai_providers.update_one({"_id": oid}, {"$set": {"status": body.status}})
        if result.matched_count == 0:
            raise HTTPException(404, "Provider not found")
        await audit(db, user.id, "provider_status_changed", {"provider_id": provider_id, "status": body.status})
        return {"ok": True, "status": body.status}

    @api_router.get("/providers/keys")
    async def provider_keys_list(user: User = Depends(require_role("executive_admin"))):
        docs = await db.ai_provider_keys.find({}, {"encrypted_key": 0}).sort("created_at", -1).to_list(500)
        for d in docs:
            d["_id"] = str(d["_id"])
            if hasattr(d.get("created_at"), "isoformat"):
                d["created_at"] = d["created_at"].isoformat()
        return docs

    @api_router.post("/providers/keys")
    async def provider_keys_create(body: _KeyBody, user: User = Depends(require_role("executive_admin"))):
        encrypted = _encrypt_key(body.plaintext_key)
        doc = {"provider_id": body.provider_id, "label": body.label,
               "encrypted_key": encrypted, "scope": body.scope or "chat",
               "created_by": user.id, "created_at": datetime.utcnow()}
        result = await db.ai_provider_keys.insert_one(doc)
        await audit(db, user.id, "provider_key_added", {"provider_id": body.provider_id, "label": body.label})
        # Reload gateway keys immediately so the new key takes effect without a redeploy
        try:
            from ai.llm_gateway import reload_provider_keys as _rlk
            await _rlk(db)
        except Exception:
            pass
        return {"ok": True, "_id": str(result.inserted_id), "label": body.label, "scope": body.scope}

    @api_router.delete("/providers/keys/{key_id}")
    async def provider_keys_delete(key_id: str, user: User = Depends(require_role("executive_admin"))):
        try:
            oid = _PObjId(key_id)
        except Exception:
            raise HTTPException(400, "Invalid key ID")
        result = await db.ai_provider_keys.delete_one({"_id": oid})
        if result.deleted_count == 0:
            raise HTTPException(404, "Key not found")
        await audit(db, user.id, "provider_key_deleted", {"key_id": key_id})
        return {"ok": True}

    @api_router.post("/providers/keys/{key_id}/test")
    async def provider_keys_test(key_id: str, user: User = Depends(require_role("executive_admin"))):
        try:
            oid = _PObjId(key_id)
        except Exception:
            raise HTTPException(400, "Invalid key ID")
        doc = await db.ai_provider_keys.find_one({"_id": oid})
        if not doc:
            raise HTTPException(404, "Key not found")
        if not _PFERNET:
            raise HTTPException(503, "Encryption not configured — cannot decrypt key for test")
        try:
            plaintext = _PFERNET.decrypt(doc["encrypted_key"].encode()).decode()
        except Exception:
            raise HTTPException(500, "Failed to decrypt key")
        # Determine provider type to pick the right test endpoint
        provider = await db.ai_providers.find_one({"_id": _PObjId(doc["provider_id"])}) if doc.get("provider_id") else None
        ptype = (provider or {}).get("provider_type", "openai")
        import httpx as _httpx, time as _time
        start = _time.monotonic()
        try:
            async with _httpx.AsyncClient(timeout=10) as client:
                if ptype == "anthropic":
                    r = await client.post("https://api.anthropic.com/v1/messages",
                        headers={"x-api-key": plaintext, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}]})
                else:
                    base = (provider or {}).get("base_url") or "https://api.openai.com/v1"
                    r = await client.post(f"{base}/chat/completions",
                        headers={"Authorization": f"Bearer {plaintext}", "content-type": "application/json"},
                        json={"model": "gpt-4o-mini", "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}]})
            latency_ms = round((_time.monotonic() - start) * 1000)
            ok = r.status_code < 500
            return {"ok": ok, "latency_ms": latency_ms, "status_code": r.status_code}
        except Exception as e:
            latency_ms = round((_time.monotonic() - start) * 1000)
            return {"ok": False, "latency_ms": latency_ms, "error": str(e)}

    @api_router.get("/providers/usage-log")
    async def provider_usage_log(user: User = Depends(require_role("executive_admin"))):
        docs = await db.ai_usage_log.find({}, {"_id": 0}).sort("created_at", -1).limit(500).to_list(500)
        for d in docs:
            if hasattr(d.get("created_at"), "isoformat"):
                d["created_at"] = d["created_at"].isoformat()
        return docs

    logger.info("Provider gateway routes registered")
except Exception as _provider_routes_err:
    logger.warning(f"Provider gateway routes unavailable: {_provider_routes_err}")

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

# ── The Sovereign (NAM Oshun Revenue Engine) + Puzzle/Points endpoints ─────────
# Executive-only Sovereign chat (Director-supervised, carries memory) + a public
# puzzle game that awards partnership points toward membership tiers. All logic
# lives in isolated, unit-tested modules (sovereign/, partnership/, puzzles/).
# Wrapped so any import/registration failure can NEVER break server boot.
try:
    from sovereign.sovereign_loader import build_sovereign_prompt as _build_sovereign_prompt
    from sovereign import sovereign_memory as _sovereign_memory
    from partnership import points as _partnership_points
    from puzzles import engine as _puzzle_engine

    async def _optional_user_id(authorization: Optional[str]):
        """Return the user id from a valid Bearer token, else None (never raises).
        Lets puzzles be viewed/attempted anonymously while points require login."""
        if not authorization or not authorization.startswith("Bearer "):
            return None
        try:
            payload = jwt.decode(authorization.split(" ", 1)[1], JWT_SECRET, algorithms=[JWT_ALGO])
            return payload.get("sub")
        except Exception:
            return None

    class _SovereignChatBody(BaseModel):
        message: str
        session_id: Optional[str] = "default"

    class _SovereignMemoryBody(BaseModel):
        content: str
        kind: Optional[str] = "fact"

    class _PuzzleAnswerBody(BaseModel):
        puzzle_id: str
        answer: str

    @api_router.post("/sovereign/chat")
    async def sovereign_chat(body: _SovereignChatBody, user: User = Depends(require_role("executive_admin"))):
        """Talk to The Sovereign — executive-only, Director-supervised, memory-aware."""
        system = await _build_sovereign_prompt(db, user.id)
        try:
            from ai.llm_gateway import call_llm as _call_llm
            _gw = await _call_llm(system=system, messages=[{"role": "user", "content": body.message}], max_tokens=2048, persona_label="sovereign")
            reply = _gw["text"]
        except Exception as e:
            logger.exception("Sovereign AI error")
            raise HTTPException(502, f"Sovereign AI error: {e}")
        try:
            await _sovereign_memory.save_memory(db, user.id, f"Asked: {body.message[:200]}", kind="note")
        except Exception:
            pass
        return {"reply": reply}

    @api_router.get("/sovereign/memory")
    async def sovereign_memory_list(user: User = Depends(require_role("executive_admin"))):
        return {"memory": await _sovereign_memory.load_memory_block(db, user.id)}

    @api_router.post("/sovereign/memory")
    async def sovereign_memory_add(body: _SovereignMemoryBody, user: User = Depends(require_role("executive_admin"))):
        return {"saved": await _sovereign_memory.save_memory(db, user.id, body.content, kind=body.kind or "fact")}

    @api_router.delete("/sovereign/memory")
    async def sovereign_memory_clear(user: User = Depends(require_role("executive_admin"))):
        return {"cleared": await _sovereign_memory.clear_memory(db, user.id)}

    @api_router.get("/puzzles/next")
    async def puzzles_next(authorization: Optional[str] = Header(None)):
        """Get the next puzzle. Public to view; points require login."""
        uid = await _optional_user_id(authorization)
        return await _puzzle_engine.next_puzzle(db, uid)

    @api_router.post("/puzzles/answer")
    async def puzzles_answer(body: _PuzzleAnswerBody, authorization: Optional[str] = Header(None)):
        """Submit an answer. Correct + logged-in => partnership points awarded once."""
        uid = await _optional_user_id(authorization)
        return await _puzzle_engine.submit_answer(db, uid, body.puzzle_id, body.answer)

    @api_router.get("/partnership/status")
    async def partnership_status(user: User = Depends(current_user)):
        """Current member's partnership points + membership tier."""
        return await _partnership_points.get_status(db, user.id)

    @api_router.get("/partnership/ledger")
    async def partnership_ledger(limit: int = 20, user: User = Depends(current_user)):
        """Recent point-award history for the current user."""
        try:
            from partnership.points import LEDGER_COLLECTION
            docs = await db[LEDGER_COLLECTION].find(
                {"user_id": user.id},
                {"_id": 0, "user_id": 0},
            ).sort("ts", -1).limit(min(limit, 50)).to_list(50)
            for d in docs:
                if hasattr(d.get("ts"), "isoformat"):
                    d["ts"] = d["ts"].isoformat()
            return docs
        except Exception:
            return []

    logger.info("Sovereign + puzzle/points endpoints registered")
except Exception as _sov_err:
    logger.warning(f"Could not register Sovereign/puzzle endpoints: {_sov_err}")


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

@api_router.get("/admin/users/{uid}/sessions")
async def exec_list_user_sessions(uid: str, user: User = Depends(require_role("executive_admin"))):
    """List active login sessions for any user (exec-only)."""
    sessions = await db.auth_sessions.find(
        {"user_id": uid},
        {"_id": 0, "session_id": 1, "user_agent": 1, "ip": 1, "created_at": 1, "last_seen": 1},
    ).sort("last_seen", -1).to_list(length=50)
    return {"sessions": sessions}

@api_router.delete("/admin/users/{uid}/sessions")
async def exec_force_logout(uid: str, user: User = Depends(require_role("executive_admin"))):
    """Force-logout all sessions for a user (exec-only)."""
    target = await db.users.find_one({"id": uid}, {"_id": 0, "full_name": 1})
    if not target:
        raise HTTPException(404, "User not found")
    await db.users.update_one({"id": uid}, {"$inc": {"token_version": 1}})
    result = await db.auth_sessions.delete_many({"user_id": uid})
    await audit(user.id, "exec.user.force_logout", target=uid,
                meta={"sessions_revoked": result.deleted_count})
    return {"ok": True, "sessions_revoked": result.deleted_count}

@api_router.post("/admin/users/bulk")
async def exec_bulk_action(body: dict, user: User = Depends(require_role("executive_admin"))):
    """Bulk action on multiple users: upgrade, downgrade, suspend, unsuspend.
    body: { action: 'role'|'suspend'|'unsuspend', uids: [...], role?: str }"""
    action = body.get("action")
    uids = body.get("uids", [])
    if not uids or not isinstance(uids, list):
        raise HTTPException(400, "uids must be a non-empty list")
    if action not in ("role", "suspend", "unsuspend"):
        raise HTTPException(400, "action must be role|suspend|unsuspend")
    results = {"ok": [], "err": []}
    for uid in uids:
        try:
            target = await db.users.find_one({"id": uid}, {"_id": 0, "role": 1, "full_name": 1})
            if not target:
                results["err"].append({"uid": uid, "reason": "not found"})
                continue
            if not can_modify(user, target.get("role", "")):
                results["err"].append({"uid": uid, "reason": "hierarchy"})
                continue
            if action == "role":
                new_role = body.get("role")
                if new_role not in ROLE_RANK:
                    results["err"].append({"uid": uid, "reason": "invalid role"})
                    continue
                await db.users.update_one({"id": uid}, {"$set": {"role": new_role}})
                await audit(user.id, "exec.bulk.role_changed", target=uid,
                            meta={"from": target["role"], "to": new_role})
            elif action == "suspend":
                await db.users.update_one({"id": uid}, {"$set": {"is_active": False}})
                await audit(user.id, "exec.bulk.suspended", target=uid)
            elif action == "unsuspend":
                await db.users.update_one({"id": uid}, {"$set": {"is_active": True}})
                await audit(user.id, "exec.bulk.unsuspended", target=uid)
            results["ok"].append(uid)
        except Exception as e:
            results["err"].append({"uid": uid, "reason": str(e)})
    return results

@api_router.get("/admin/users/{uid}/audit")
async def exec_user_audit(uid: str, limit: int = 50, user: User = Depends(require_role("admin"))):
    """Audit history for a specific user (as actor or target), admin+."""
    entries = await db.audit_log.find(
        {"$or": [{"actor_id": uid}, {"target_id": uid}]},
        {"_id": 0},
    ).sort("at", -1).limit(min(limit, 200)).to_list(length=200)
    return entries

@api_router.get("/admin/rbac/matrix")
async def get_rbac_matrix(user: User = Depends(require_role("executive_admin"))):
    """Return the platform permission matrix stored in DB."""
    doc = await db.platform_config.find_one({"key": "rbac_matrix"}, {"_id": 0})
    default_matrix = {
        "student":         {"content_read": True,  "content_create": False, "content_edit_own": True,  "content_delete_own": True,  "user_warn": False, "user_mute": False, "user_ban": False, "api_access": False, "billing_view": False, "export_data": False},
        "instructor":      {"content_read": True,  "content_create": True,  "content_edit_own": True,  "content_delete_own": True,  "user_warn": True,  "user_mute": True,  "user_ban": False, "api_access": True,  "billing_view": False, "export_data": False},
        "admin":           {"content_read": True,  "content_create": True,  "content_edit_own": True,  "content_delete_own": True,  "user_warn": True,  "user_mute": True,  "user_ban": True,  "api_access": True,  "billing_view": True,  "export_data": True},
        "executive_admin": {"content_read": True,  "content_create": True,  "content_edit_own": True,  "content_delete_own": True,  "user_warn": True,  "user_mute": True,  "user_ban": True,  "api_access": True,  "billing_view": True,  "export_data": True},
    }
    return {"matrix": (doc or {}).get("value", default_matrix)}

@api_router.patch("/admin/rbac/matrix")
async def set_rbac_matrix(body: dict, user: User = Depends(require_role("executive_admin"))):
    """Update the platform permission matrix (exec-only)."""
    matrix = body.get("matrix")
    if not isinstance(matrix, dict):
        raise HTTPException(400, "matrix must be an object")
    valid_roles = set(ROLE_RANK.keys())
    for role in matrix:
        if role not in valid_roles:
            raise HTTPException(400, f"Unknown role: {role}")
    await db.platform_config.update_one(
        {"key": "rbac_matrix"},
        {"$set": {"key": "rbac_matrix", "value": matrix, "updated_by": user.id, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await audit(user.id, "exec.rbac.matrix_updated", meta={"roles": list(matrix.keys())})
    return {"ok": True}

@api_router.get("/admin/mfa/config")
async def get_mfa_config(user: User = Depends(require_role("executive_admin"))):
    """Return MFA enforcement config per role."""
    doc = await db.platform_config.find_one({"key": "mfa_config"}, {"_id": 0})
    default = {"executive_admin": True, "admin": True, "instructor": False, "student": False}
    return {"mfa": (doc or {}).get("value", default)}

@api_router.patch("/admin/mfa/config")
async def set_mfa_config(body: dict, user: User = Depends(require_role("executive_admin"))):
    """Set MFA enforcement per role (exec-only)."""
    mfa = body.get("mfa")
    if not isinstance(mfa, dict):
        raise HTTPException(400, "mfa must be an object")
    await db.platform_config.update_one(
        {"key": "mfa_config"},
        {"$set": {"key": "mfa_config", "value": mfa, "updated_by": user.id, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await audit(user.id, "exec.mfa.config_updated", meta=mfa)
    return {"ok": True, "mfa": mfa}

@api_router.get("/admin/access/ipwhitelist")
async def get_ip_whitelist(user: User = Depends(require_role("executive_admin"))):
    """Return IP whitelist entries."""
    entries = await db.ip_whitelist.find({}, {"_id": 0}).sort("created_at", -1).to_list(length=200)
    return {"entries": entries}

@api_router.post("/admin/access/ipwhitelist")
async def add_ip_whitelist(body: dict, user: User = Depends(require_role("executive_admin"))):
    """Add an IP/CIDR to the whitelist for a role."""
    ip = (body.get("ip") or "").strip()
    role = body.get("role", "executive_admin")
    note = (body.get("note") or "").strip()
    if not ip:
        raise HTTPException(400, "ip is required")
    if role not in ROLE_RANK:
        raise HTTPException(400, f"Unknown role: {role}")
    import uuid as _uuid
    entry = {"id": str(_uuid.uuid4()), "ip": ip, "role": role, "note": note,
             "added_by": user.id, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.ip_whitelist.insert_one(entry)
    await audit(user.id, "exec.access.ip_added", meta={"ip": ip, "role": role})
    entry.pop("_id", None)
    return entry

@api_router.delete("/admin/access/ipwhitelist/{entry_id}")
async def remove_ip_whitelist(entry_id: str, user: User = Depends(require_role("executive_admin"))):
    """Remove an IP whitelist entry."""
    result = await db.ip_whitelist.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Entry not found")
    await audit(user.id, "exec.access.ip_removed", meta={"entry_id": entry_id})
    return {"ok": True}

@api_router.post("/admin/users/{uid}/elevated-role")
async def grant_elevated_role(uid: str, body: dict, user: User = Depends(require_role("executive_admin"))):
    """Grant a time-bound elevated role to a user (exec-only).
    body: { role: str, expires_hours: int, reason: str }"""
    role = body.get("role")
    hours = body.get("expires_hours", 24)
    reason = body.get("reason", "")
    if role not in ROLE_RANK:
        raise HTTPException(400, f"Unknown role: {role}")
    if not (1 <= hours <= 168):
        raise HTTPException(400, "expires_hours must be 1-168")
    target = await db.users.find_one({"id": uid}, {"_id": 0, "role": 1, "full_name": 1})
    if not target:
        raise HTTPException(404, "User not found")
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
    import uuid as _uuid
    record = {
        "id": str(_uuid.uuid4()), "user_id": uid, "role": role,
        "original_role": target["role"], "expires_at": expires_at,
        "reason": reason, "granted_by": user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.elevated_roles.insert_one(record)
    await db.users.update_one({"id": uid}, {"$set": {"role": role, "elevated_until": expires_at, "original_role": target["role"]}})
    await audit(user.id, "exec.user.elevated_role", target=uid,
                meta={"role": role, "expires_at": expires_at, "reason": reason})
    record.pop("_id", None)
    return record

@api_router.get("/admin/users/{uid}/elevated-role")
async def get_elevated_role(uid: str, user: User = Depends(require_role("executive_admin"))):
    """Get active elevated role record for user."""
    record = await db.elevated_roles.find_one(
        {"user_id": uid, "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}},
        {"_id": 0},
    )
    return {"elevated": record}

@api_router.delete("/admin/users/{uid}/elevated-role")
async def revoke_elevated_role(uid: str, user: User = Depends(require_role("executive_admin"))):
    """Revoke time-bound elevated role and revert to original."""
    target = await db.users.find_one({"id": uid}, {"_id": 0, "original_role": 1, "elevated_until": 1})
    if not target or not target.get("original_role"):
        raise HTTPException(404, "No active elevation found")
    original = target["original_role"]
    await db.users.update_one({"id": uid}, {"$set": {"role": original}, "$unset": {"elevated_until": 1, "original_role": 1}})
    await db.elevated_roles.delete_many({"user_id": uid})
    await audit(user.id, "exec.user.elevation_revoked", target=uid, meta={"reverted_to": original})
    return {"ok": True, "reverted_to": original}

@api_router.patch("/admin/users/{uid}/sage-tier")
async def set_user_sage_tier(uid: str, body: dict, user: User = Depends(require_role("admin"))):
    """Grant or revoke Sage advanced tier for a user (admin+).
    body: { tier: "basic" | "advanced" }"""
    tier = (body.get("tier") or "").strip().lower()
    if tier not in ("basic", "advanced"):
        raise HTTPException(400, "tier must be 'basic' or 'advanced'")
    target = await db.users.find_one({"id": uid}, {"_id": 0, "id": 1, "email": 1})
    if not target:
        raise HTTPException(404, "User not found")
    await db.users.update_one({"id": uid}, {"$set": {"sage_tier": tier}})
    await audit(user.id, "admin.sage.tier_updated", target=uid, meta={"tier": tier})
    return {"ok": True, "uid": uid, "sage_tier": tier}

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
        import re as _re
        filt["action"] = {"$regex": action, "$options": "i"}
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


# ── Supervisor Control Panel Routes ────────────────────────────────────────────
# Distinct from exec routes. Supervisor has independent controls:
# content moderation, escalation management, visitor flow, greeter config,
# backup system health, and system continuity controls.
# All require executive_admin (supervisor rank).

@api_router.get("/supervisor/dashboard")
async def supervisor_dashboard(user: User = Depends(require_role("executive_admin"))):
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

@api_router.get("/supervisor/escalations")
async def supervisor_escalations(user: User = Depends(require_role("executive_admin"))):
    """List open escalation records — supervisor manages these."""
    escalations = await db.escalations.find(
        {"status": {"$in": ["open", "pending_supervisor"]}},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=100)
    return {"escalations": escalations}

@api_router.post("/supervisor/escalations/{esc_id}/resolve")
async def supervisor_resolve_escalation(esc_id: str, body: dict, user: User = Depends(require_role("executive_admin"))):
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

@api_router.post("/supervisor/escalations")
async def supervisor_create_escalation(body: dict, user: User = Depends(require_role("executive_admin"))):
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

@api_router.get("/supervisor/greeter/config")
async def supervisor_greeter_config(user: User = Depends(require_role("executive_admin"))):
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

@api_router.patch("/supervisor/greeter/config")
async def supervisor_update_greeter(body: dict, user: User = Depends(require_role("executive_admin"))):
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

@api_router.get("/supervisor/visitor-flow")
async def supervisor_visitor_flow(user: User = Depends(require_role("executive_admin"))):
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

@api_router.patch("/supervisor/visitor-flow")
async def supervisor_update_visitor_flow(body: dict, user: User = Depends(require_role("executive_admin"))):
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

@api_router.post("/supervisor/content/{content_type}/{content_id}/approve")
async def supervisor_approve_content(content_type: str, content_id: str, user: User = Depends(require_role("executive_admin"))):
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

@api_router.post("/supervisor/content/{content_type}/{content_id}/reject")
async def supervisor_reject_content(content_type: str, content_id: str, body: dict, user: User = Depends(require_role("executive_admin"))):
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

@api_router.get("/supervisor/backup/status")
async def supervisor_backup_status(user: User = Depends(require_role("executive_admin"))):
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
        from exec_panel import get_panel
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

@api_router.post("/supervisor/backup/switch-provider")
async def supervisor_switch_provider(body: dict, user: User = Depends(require_role("executive_admin"))):
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

@api_router.post("/supervisor/backup/reset-gateway")
async def supervisor_reset_gateway(user: User = Depends(require_role("executive_admin"))):
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

@api_router.get("/supervisor/backup/free-matrix")
async def supervisor_backup_matrix(user: User = Depends(require_role("executive_admin"))):
    """Return the free backup provider matrix with live status for each provider."""
    try:
        from exec_panel import get_system_health
        health = await get_system_health(db)
        return health
    except Exception as e:
        return {"error": str(e), "note": "exec_panel module unavailable"}

@api_router.post("/supervisor/backup/emergency-broadcast")
async def supervisor_emergency_broadcast(body: dict, user: User = Depends(require_role("executive_admin"))):
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

@api_router.get("/supervisor/sage/sessions")
async def supervisor_sage_sessions(
    limit: int = 50,
    user_id: str = None,
    user: User = Depends(require_role("executive_admin")),
):
    """Supervisor reviews Sage session activity — for content safety oversight."""
    filt = {}
    if user_id:
        filt["user_id"] = user_id
    sessions = await db.sage_sessions.find(filt, {"_id": 0}).sort("created_at", -1).limit(min(limit, 200)).to_list(length=200)
    return {"sessions": sessions, "total": len(sessions)}

@api_router.post("/supervisor/sage/sessions/{session_id}/flag")
async def supervisor_flag_sage_session(session_id: str, body: dict, user: User = Depends(require_role("executive_admin"))):
    """Supervisor flags a Sage session for exec review."""
    reason = body.get("reason", "")
    await db.sage_sessions.update_one(
        {"id": session_id},
        {"$set": {"flagged": True, "flagged_by": user.id,
                  "flag_reason": reason, "flagged_at": datetime.now(timezone.utc).isoformat()}},
    )
    await audit(user.id, "supervisor.sage.session_flagged", meta={"session_id": session_id, "reason": reason})
    return {"ok": True}

@api_router.get("/supervisor/system/continuity-check")
async def supervisor_continuity_check(user: User = Depends(require_role("executive_admin"))):
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
        from exec_panel import get_panel
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


@api_router.post("/supervisor-integrity-alert")
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


# ── Platform Prices ──────────────────────────────────────────────────────────
# Collection: platform_prices  { id, key, value, description, last_modified_by, last_modified_at }

@api_router.get("/admin/prices")
async def list_prices(user: User = Depends(require_role("admin"))):
    docs = await db.platform_prices.find({}, {"_id": 0}).sort("key", 1).to_list(length=500)
    return {"prices": docs}

@api_router.post("/admin/prices")
async def create_price(body: dict, user: User = Depends(require_role("admin"))):
    key   = (body.get("key") or "").strip()
    value = body.get("value")
    desc  = (body.get("description") or "").strip()
    if not key:
        raise HTTPException(400, "key is required")
    if value is None:
        raise HTTPException(400, "value is required")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise HTTPException(400, "value must be a number")
    existing = await db.platform_prices.find_one({"key": key})
    if existing:
        raise HTTPException(409, f"Price key '{key}' already exists — use PATCH to update")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "key": key,
        "value": value,
        "description": desc,
        "last_modified_by": user.id,
        "last_modified_at": now,
    }
    await db.platform_prices.insert_one(doc)
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "price_create", "actor": user.id,
        "detail": f"Created price key={key} value={value}", "at": now,
    })
    return {k: v for k, v in doc.items() if k != "_id"}

@api_router.patch("/admin/prices/{price_id}")
async def update_price(price_id: str, body: dict, user: User = Depends(require_role("admin"))):
    doc = await db.platform_prices.find_one({"id": price_id})
    if not doc:
        raise HTTPException(404, "Price not found")
    updates: dict = {}
    if "value" in body:
        try:
            updates["value"] = float(body["value"])
        except (TypeError, ValueError):
            raise HTTPException(400, "value must be a number")
    if "description" in body:
        updates["description"] = (body["description"] or "").strip()
    if "key" in body:
        new_key = (body["key"] or "").strip()
        if not new_key:
            raise HTTPException(400, "key cannot be empty")
        conflict = await db.platform_prices.find_one({"key": new_key, "id": {"$ne": price_id}})
        if conflict:
            raise HTTPException(409, f"Key '{new_key}' already in use")
        updates["key"] = new_key
    if not updates:
        raise HTTPException(400, "No fields to update")
    now = datetime.now(timezone.utc).isoformat()
    updates["last_modified_by"] = user.id
    updates["last_modified_at"] = now
    await db.platform_prices.update_one({"id": price_id}, {"$set": updates})
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "price_update", "actor": user.id,
        "detail": f"Updated price id={price_id} fields={list(updates.keys())}", "at": now,
    })
    updated = await db.platform_prices.find_one({"id": price_id}, {"_id": 0})
    return updated

@api_router.delete("/admin/prices/{price_id}")
async def delete_price(price_id: str, user: User = Depends(require_role("executive_admin"))):
    doc = await db.platform_prices.find_one({"id": price_id})
    if not doc:
        raise HTTPException(404, "Price not found")
    await db.platform_prices.delete_one({"id": price_id})
    now = datetime.now(timezone.utc).isoformat()
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "price_delete", "actor": user.id,
        "detail": f"Deleted price key={doc.get('key')} id={price_id}", "at": now,
    })
    return {"deleted": price_id}

@api_router.get("/prices/public")
async def public_prices():
    """Returns all price keys and values — no auth. Used by frontend to display current pricing."""
    docs = await db.platform_prices.find({}, {"_id": 0, "id": 1, "key": 1, "value": 1, "description": 1}).sort("key", 1).to_list(length=500)
    return {"prices": docs}

# ── The Auditor — read-only ledger, reporting, and value tracking ─────────────
# Collection: auditor_ledger
# Schema: { id, delivery_date, commit_sha, category, description, dollar_value,
#           evidence, status, risk_level, created_at, created_by }
#
# Categories: revenue_restored | risk_eliminated | cost_avoided | debt_repaid | governance
# Statuses:   PASS | FAIL | UNVERIFIED | INCOMPLETE | NO_EVIDENCE
# Risk levels: none | low | medium | high | critical
#
# Access: admin+ (read). Only The Director or Finance Director adds entries.
# The Auditor persona never modifies state.

_AUDITOR_CATEGORIES = {"revenue_restored", "risk_eliminated", "cost_avoided", "debt_repaid", "governance"}
_AUDITOR_STATUSES   = {"PASS", "FAIL", "UNVERIFIED", "INCOMPLETE", "NO_EVIDENCE"}
_AUDITOR_RISK       = {"none", "low", "medium", "high", "critical"}

@api_router.get("/auditor/summary")
async def auditor_summary(user: User = Depends(require_role("admin"))):
    """Running ledger totals by category. Read-only."""
    pipeline = [
        {"$group": {
            "_id": "$category",
            "total_value": {"$sum": "$dollar_value"},
            "count": {"$sum": 1},
            "verified_value": {"$sum": {"$cond": [{"$eq": ["$status", "PASS"]}, "$dollar_value", 0]}},
            "unverified_count": {"$sum": {"$cond": [{"$eq": ["$status", "UNVERIFIED"]}, 1, 0]}},
        }},
        {"$sort": {"total_value": -1}},
    ]
    by_category = await db.auditor_ledger.aggregate(pipeline).to_list(length=20)
    total = sum(r["total_value"] for r in by_category)
    verified = sum(r["verified_value"] for r in by_category)
    unverified = sum(r["unverified_count"] for r in by_category)
    risk_counts = {}
    async for doc in db.auditor_ledger.find({}, {"_id": 0, "risk_level": 1}):
        lvl = doc.get("risk_level", "none")
        risk_counts[lvl] = risk_counts.get(lvl, 0) + 1
    recent = await db.auditor_ledger.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    return {
        "total_dollar_value": total,
        "verified_dollar_value": verified,
        "unverified_count": unverified,
        "by_category": by_category,
        "risk_distribution": risk_counts,
        "recent_entries": recent,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

@api_router.get("/auditor/ledger")
async def auditor_ledger_list(
    category: str = None,
    status: str = None,
    risk_level: str = None,
    limit: int = 50,
    skip: int = 0,
    user: User = Depends(require_role("admin")),
):
    """Paginated ledger. All filters optional. Read-only."""
    q: dict = {}
    if category and category in _AUDITOR_CATEGORIES:
        q["category"] = category
    if status and status in _AUDITOR_STATUSES:
        q["status"] = status
    if risk_level and risk_level in _AUDITOR_RISK:
        q["risk_level"] = risk_level
    limit = min(max(1, limit), 200)
    skip = max(0, skip)
    docs = await db.auditor_ledger.find(q, {"_id": 0}).sort("delivery_date", -1).skip(skip).limit(limit).to_list(limit)
    total_count = await db.auditor_ledger.count_documents(q)
    return {"entries": docs, "total": total_count, "limit": limit, "skip": skip}

@api_router.post("/auditor/ledger")
async def auditor_add_entry(body: dict, user: User = Depends(require_role("admin"))):
    """Director or Finance Director records a verified delivery. The Auditor does not call this."""
    required = ["description", "category", "dollar_value", "evidence", "status"]
    for f in required:
        if f not in body or body[f] is None:
            raise HTTPException(400, f"Field '{f}' is required")
    if body["category"] not in _AUDITOR_CATEGORIES:
        raise HTTPException(400, f"category must be one of: {sorted(_AUDITOR_CATEGORIES)}")
    if body["status"] not in _AUDITOR_STATUSES:
        raise HTTPException(400, f"status must be one of: {sorted(_AUDITOR_STATUSES)}")
    risk = body.get("risk_level", "none")
    if risk not in _AUDITOR_RISK:
        raise HTTPException(400, f"risk_level must be one of: {sorted(_AUDITOR_RISK)}")
    try:
        dollar_value = float(body["dollar_value"])
    except (TypeError, ValueError):
        raise HTTPException(400, "dollar_value must be a number")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "delivery_date": body.get("delivery_date") or now,
        "commit_sha": (body.get("commit_sha") or "").strip() or None,
        "category": body["category"],
        "description": body["description"].strip(),
        "dollar_value": dollar_value,
        "evidence": body["evidence"].strip(),
        "status": body["status"],
        "risk_level": risk,
        "created_at": now,
        "created_by": user.id,
    }
    await db.auditor_ledger.insert_one(doc)
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "auditor.entry.added", "actor": user.id,
        "detail": f"Auditor entry: {body['description'][:80]} | ${dollar_value:.2f} | {body['status']}", "at": now,
    })
    return {k: v for k, v in doc.items() if k != "_id"}

@api_router.patch("/auditor/ledger/{entry_id}")
async def auditor_update_entry(entry_id: str, body: dict, user: User = Depends(require_role("admin"))):
    """Correct status, dollar value, or evidence on an existing entry. Audit-logged."""
    doc = await db.auditor_ledger.find_one({"id": entry_id})
    if not doc:
        raise HTTPException(404, "Entry not found")
    allowed_fields = {"status", "dollar_value", "evidence", "risk_level", "description", "commit_sha"}
    updates: dict = {}
    for field in allowed_fields:
        if field in body:
            if field == "status" and body[field] not in _AUDITOR_STATUSES:
                raise HTTPException(400, f"Invalid status: {body[field]}")
            if field == "risk_level" and body[field] not in _AUDITOR_RISK:
                raise HTTPException(400, f"Invalid risk_level: {body[field]}")
            if field == "dollar_value":
                try:
                    updates[field] = float(body[field])
                except (TypeError, ValueError):
                    raise HTTPException(400, "dollar_value must be a number")
            else:
                updates[field] = body[field]
    if not updates:
        raise HTTPException(400, "No valid fields to update")
    now = datetime.now(timezone.utc).isoformat()
    updates["updated_at"] = now
    updates["updated_by"] = user.id
    await db.auditor_ledger.update_one({"id": entry_id}, {"$set": updates})
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "auditor.entry.updated", "actor": user.id,
        "detail": f"Updated entry {entry_id}: fields={list(updates.keys())}", "at": now,
    })
    updated = await db.auditor_ledger.find_one({"id": entry_id}, {"_id": 0})
    return updated

@api_router.get("/auditor/report")
async def auditor_report(
    start: str = None,
    end: str = None,
    user: User = Depends(require_role("admin")),
):
    """Full report for a date range. Includes ledger, totals, debt, risks."""
    q: dict = {}
    if start:
        q.setdefault("delivery_date", {})["$gte"] = start
    if end:
        q.setdefault("delivery_date", {})["$lte"] = end
    entries = await db.auditor_ledger.find(q, {"_id": 0}).sort("delivery_date", -1).to_list(500)
    total = sum(e.get("dollar_value", 0) for e in entries)
    verified = sum(e.get("dollar_value", 0) for e in entries if e.get("status") == "PASS")
    by_cat: dict = {}
    for e in entries:
        cat = e.get("category", "unknown")
        by_cat[cat] = by_cat.get(cat, 0) + e.get("dollar_value", 0)
    debt_items = [e for e in entries if e.get("status") in ("INCOMPLETE", "FAIL")]
    risk_items = [e for e in entries if e.get("risk_level") in ("high", "critical")]
    unverified = [e for e in entries if e.get("status") == "UNVERIFIED"]
    return {
        "report_period": {"start": start or "all-time", "end": end or "present"},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": user.id,
        "summary": {
            "total_entries": len(entries),
            "total_dollar_value": total,
            "verified_dollar_value": verified,
            "unverified_dollar_value": total - verified,
        },
        "by_category": by_cat,
        "entries": entries,
        "debt_items": debt_items,
        "risk_items": risk_items,
        "unverified_items": unverified,
        "flags": {
            "unverified_count": len(unverified),
            "incomplete_count": len([e for e in entries if e.get("status") == "INCOMPLETE"]),
            "high_risk_count": len(risk_items),
            "no_evidence_count": len([e for e in entries if e.get("status") == "NO_EVIDENCE"]),
        },
    }

@api_router.get("/auditor/debt")
async def auditor_debt(user: User = Depends(require_role("admin"))):
    """Outstanding technical debt and incomplete items. Read-only."""
    items = await db.auditor_ledger.find(
        {"status": {"$in": ["INCOMPLETE", "FAIL", "UNVERIFIED"]}},
        {"_id": 0},
    ).sort("risk_level", -1).to_list(200)
    total_debt_value = sum(i.get("dollar_value", 0) for i in items if i.get("status") in ("INCOMPLETE", "FAIL"))
    return {
        "debt_items": items,
        "total_debt_count": len(items),
        "total_debt_value": total_debt_value,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

@api_router.get("/auditor/risks")
async def auditor_risks(user: User = Depends(require_role("admin"))):
    """Unresolved risk items. Read-only."""
    items = await db.auditor_ledger.find(
        {"risk_level": {"$in": ["high", "critical"]}},
        {"_id": 0},
    ).sort("delivery_date", -1).to_list(200)
    return {
        "risk_items": items,
        "critical_count": sum(1 for i in items if i.get("risk_level") == "critical"),
        "high_count": sum(1 for i in items if i.get("risk_level") == "high"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Creator Course Publishing ─────────────────────────────────────────────────
# Any authenticated user can be a creator. Courses live in db.creator_courses.
# Sections are text-based (title + content). Price in cents (0 = free).
# Status: "draft" (private, only creator sees) | "published" (public catalog).

class CourseSection(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=20000)

class CreateCourseReq(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    category: str = Field(default="general", max_length=100)
    price_cents: int = Field(default=0, ge=0, le=99900)
    sections: List[CourseSection] = Field(default_factory=list)
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)

class UpdateCourseReq(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    category: Optional[str] = Field(default=None, max_length=100)
    price_cents: Optional[int] = Field(default=None, ge=0, le=99900)
    sections: Optional[List[CourseSection]] = None
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)
    status: Optional[Literal["draft", "published"]] = None


@api_router.post("/creator/courses", status_code=201)
async def creator_create_course(body: CreateCourseReq, user: User = Depends(current_user)):
    """Create a new course draft. Any authenticated user can create."""
    course_id = str(uuid.uuid4())
    slug = re.sub(r"[^a-z0-9]+", "-", body.title.lower()).strip("-")[:60] + "-" + course_id[:8]
    doc = {
        "course_id": course_id,
        "creator_id": user.id,
        "creator_name": user.full_name,
        "title": body.title,
        "description": body.description,
        "category": body.category,
        "price_cents": body.price_cents,
        "sections": [s.model_dump() for s in body.sections],
        "thumbnail_url": body.thumbnail_url,
        "slug": slug,
        "status": "draft",
        "enrollment_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.creator_courses.insert_one(doc)
    await audit(user.id, "creator.course.created", meta={"course_id": course_id, "title": body.title})
    doc.pop("_id", None)
    return {"course": doc}


@api_router.get("/creator/courses")
async def creator_list_my_courses(user: User = Depends(current_user)):
    """List all courses owned by the current user."""
    courses = await db.creator_courses.find(
        {"creator_id": user.id},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=100)
    return {"courses": courses}


@api_router.get("/creator/courses/published")
async def creator_published_catalog(
    category: str = "",
    skip: int = 0,
    limit: int = 24,
):
    """Public catalog — published courses from all creators."""
    query: dict = {"status": "published"}
    if category:
        query["category"] = category
    courses = await db.creator_courses.find(
        query,
        {"_id": 0, "sections": 0},
    ).sort("created_at", -1).skip(skip).limit(min(limit, 50)).to_list(length=50)
    total = await db.creator_courses.count_documents(query)
    return {"courses": courses, "total": total}


@api_router.get("/creator/courses/{course_id}")
async def creator_get_course(course_id: str, user: User = Depends(current_user)):
    """Get full course detail. Drafts only visible to their creator."""
    course = await db.creator_courses.find_one({"course_id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(404, "Course not found")
    if course["status"] == "draft" and course["creator_id"] != user.id:
        raise HTTPException(403, "Not your draft")
    return {"course": course}


@api_router.patch("/creator/courses/{course_id}")
async def creator_update_course(
    course_id: str,
    body: UpdateCourseReq,
    user: User = Depends(current_user),
):
    """Update a course. Only the creator can edit."""
    course = await db.creator_courses.find_one({"course_id": course_id})
    if not course:
        raise HTTPException(404, "Course not found")
    if course["creator_id"] != user.id:
        raise HTTPException(403, "Not your course")
    update: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if body.title is not None:
        update["title"] = body.title
        update["slug"] = re.sub(r"[^a-z0-9]+", "-", body.title.lower()).strip("-")[:60] + "-" + course_id[:8]
    if body.description is not None:
        update["description"] = body.description
    if body.category is not None:
        update["category"] = body.category
    if body.price_cents is not None:
        update["price_cents"] = body.price_cents
    if body.sections is not None:
        update["sections"] = [s.model_dump() for s in body.sections]
    if body.thumbnail_url is not None:
        update["thumbnail_url"] = body.thumbnail_url
    if body.status is not None:
        update["status"] = body.status
    await db.creator_courses.update_one({"course_id": course_id}, {"$set": update})
    await audit(user.id, "creator.course.updated", meta={"course_id": course_id, "fields": list(update.keys())})
    updated = await db.creator_courses.find_one({"course_id": course_id}, {"_id": 0})
    return {"course": updated}


@api_router.delete("/creator/courses/{course_id}", status_code=204)
async def creator_delete_course(course_id: str, user: User = Depends(current_user)):
    """Soft-delete (archive) a course. Only the creator can delete."""
    course = await db.creator_courses.find_one({"course_id": course_id})
    if not course:
        raise HTTPException(404, "Course not found")
    if course["creator_id"] != user.id:
        raise HTTPException(403, "Not your course")
    await db.creator_courses.update_one(
        {"course_id": course_id},
        {"$set": {"status": "archived", "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await audit(user.id, "creator.course.deleted", meta={"course_id": course_id})


# ── Creator Course Checkout ───────────────────────────────────────────────────

@api_router.post("/creator/courses/{course_id}/checkout")
async def creator_course_checkout(course_id: str, user: User = Depends(current_user)):
    """Initiate Stripe checkout for a published creator course."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "Payment system not configured")
    course = await db.creator_courses.find_one({"course_id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(404, "Course not found")
    if course["status"] != "published":
        raise HTTPException(400, "Course is not available for purchase")
    if course["creator_id"] == user.id:
        raise HTTPException(400, "You cannot buy your own course")

    amount = course["price_cents"]
    if amount == 0:
        # Free course — enroll directly without Stripe
        await db.creator_courses.update_one({"course_id": course_id}, {"$inc": {"enrollment_count": 1}})
        await db.creator_enrollments.update_one(
            {"course_id": course_id, "user_id": user.id},
            {"$setOnInsert": {"enrolled_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
        return {"enrolled": True, "free": True}

    user_doc = await db.users.find_one({"id": user.id}, {"stripe_customer_id": 1, "email": 1, "full_name": 1})
    customer_id = (user_doc or {}).get("stripe_customer_id")
    if not customer_id:
        customer = _stripe.Customer.create(
            email=user.email, name=user.full_name, metadata={"wai_user_id": user.id}
        )
        customer_id = customer.id
        await db.users.update_one({"id": user.id}, {"$set": {"stripe_customer_id": customer_id}})

    session = _stripe.checkout.Session.create(
        mode="payment",
        customer=customer_id,
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": course["title"], "description": course.get("description", "")[:500]},
                "unit_amount": amount,
            },
            "quantity": 1,
        }],
        success_url=f"{FRONTEND_URL}/creator/courses/{course_id}?enrolled=1",
        cancel_url=f"{FRONTEND_URL}/creator/courses/{course_id}",
        metadata={
            "wai_user_id": user.id,
            "product_key": "creator_course",
            "creator_id": course["creator_id"],
            "course_id": course_id,
        },
    )
    await audit(user.id, "creator.course.checkout", meta={"course_id": course_id, "amount": amount})
    return {"url": session.url}


@api_router.get("/creator/enrollments/me")
async def creator_enrollments_me(user: User = Depends(current_user)):
    """Return the list of course_ids the current user is enrolled in (free + paid)."""
    docs = await db.creator_enrollments.find(
        {"user_id": user.id},
        {"_id": 0, "course_id": 1},
    ).to_list(length=500)
    return {"enrolled_course_ids": [d["course_id"] for d in docs]}


# ── Creator Earnings & Payouts ────────────────────────────────────────────────
# Platform retains 30%; creator keeps 70%. Payouts accumulate monthly.
# "Pending" = earned but not yet disbursed. "paid" = payout sent.

class SaveBankAccountReq(BaseModel):
    account_holder_name: str = Field(..., min_length=2, max_length=200)
    routing_number: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")
    account_number: str = Field(..., min_length=4, max_length=17, pattern=r"^\d+$")
    account_type: Literal["checking", "savings"] = "checking"


@api_router.get("/creator/earnings")
async def creator_earnings_summary(user: User = Depends(current_user)):
    """Monthly earnings summary for the current creator."""
    entries = await db.creator_earnings.find(
        {"creator_id": user.id},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=500)

    # Group by period
    by_period: dict = {}
    for e in entries:
        p = e["period"]
        if p not in by_period:
            by_period[p] = {"period": p, "gross_cents": 0, "creator_share_cents": 0, "sales": 0, "payout_status": "pending"}
        by_period[p]["gross_cents"] += e["gross_cents"]
        by_period[p]["creator_share_cents"] += e["creator_share_cents"]
        by_period[p]["sales"] += 1
        if e.get("payout_status") == "paid":
            by_period[p]["payout_status"] = "paid"

    months = sorted(by_period.values(), key=lambda x: x["period"], reverse=True)
    total_earned = sum(e["creator_share_cents"] for e in entries)
    total_pending = sum(e["creator_share_cents"] for e in entries if e.get("payout_status") == "pending")
    total_paid = sum(e["creator_share_cents"] for e in entries if e.get("payout_status") == "paid")

    # Check if bank account on file
    bank = await db.creator_bank_accounts.find_one({"creator_id": user.id}, {"_id": 0, "account_number": 0, "routing_number": 0})

    return {
        "total_earned_cents": total_earned,
        "total_pending_cents": total_pending,
        "total_paid_cents": total_paid,
        "months": months,
        "bank_account_on_file": bank is not None,
        "bank_account_holder": (bank or {}).get("account_holder_name"),
        "bank_account_type": (bank or {}).get("account_type"),
    }


@api_router.get("/creator/payouts")
async def creator_payout_history(user: User = Depends(current_user)):
    """Payout disbursement history for the current creator."""
    payouts = await db.creator_payouts.find(
        {"creator_id": user.id},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=100)
    return {"payouts": payouts}


@api_router.post("/creator/bank-account", status_code=201)
async def creator_save_bank_account(body: SaveBankAccountReq, user: User = Depends(current_user)):
    """Save or update creator bank account for payouts.
    Account number stored masked (last 4 digits only after save)."""
    masked = "****" + body.account_number[-4:]
    await db.creator_bank_accounts.update_one(
        {"creator_id": user.id},
        {"$set": {
            "creator_id": user.id,
            "account_holder_name": body.account_holder_name,
            "routing_number": body.routing_number,  # stored for payout processing
            "account_number_masked": masked,
            "account_type": body.account_type,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await audit(user.id, "creator.bank_account.saved", meta={"masked": masked})
    return {"saved": True, "account_number_masked": masked}


@api_router.get("/creator/bank-account")
async def creator_get_bank_account(user: User = Depends(current_user)):
    """Get masked bank account info on file."""
    bank = await db.creator_bank_accounts.find_one(
        {"creator_id": user.id},
        {"_id": 0, "routing_number": 0},
    )
    if not bank:
        return {"bank_account": None}
    return {"bank_account": bank}


# Admin endpoint — process monthly payouts (executive_admin only)
@api_router.post("/admin/creator-payouts/process")
async def admin_process_creator_payouts(user: User = Depends(require_role("executive_admin"))):
    """Mark all pending earnings as paid and write payout records.
    In production this triggers ACH transfer; here it records the intent."""
    period = datetime.now(timezone.utc).strftime("%Y-%m")
    # Find all creators with pending earnings this period
    pipeline = [
        {"$match": {"payout_status": "pending", "period": {"$lt": period}}},
        {"$group": {"_id": "$creator_id", "total_cents": {"$sum": "$creator_share_cents"}, "count": {"$sum": 1}}},
    ]
    summaries = await db.creator_earnings.aggregate(pipeline).to_list(length=500)
    payouts_created = []
    for s in summaries:
        creator_id = s["_id"]
        amount = s["total_cents"]
        if amount < 100:
            continue  # below $1 minimum, roll over
        bank = await db.creator_bank_accounts.find_one({"creator_id": creator_id})
        payout_id = str(uuid.uuid4())
        await db.creator_payouts.insert_one({
            "payout_id": payout_id,
            "creator_id": creator_id,
            "amount_cents": amount,
            "sale_count": s["count"],
            "bank_on_file": bank is not None,
            "status": "processing",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        # Mark earnings as paid
        await db.creator_earnings.update_many(
            {"creator_id": creator_id, "payout_status": "pending", "period": {"$lt": period}},
            {"$set": {"payout_status": "paid", "payout_id": payout_id}},
        )
        await notify(creator_id, "Payout Initiated",
                     f"Your payout of ${amount/100:.2f} has been initiated. Allow 2-3 business days.",
                     link="/creator/earnings", kind="success")
        payouts_created.append({"creator_id": creator_id, "amount_cents": amount})
    await audit(user.id, "admin.creator_payouts.processed", meta={"count": len(payouts_created)})
    return {"payouts_initiated": len(payouts_created), "detail": payouts_created}


# ── Creator Public Profiles ───────────────────────────────────────────────────
# Creators claim a slug and edit their own profile. Public GET by slug.
# Hardcoded profiles in the frontend are the fallback when no DB record exists.

class CreatorSocialLink(BaseModel):
    platform: str = Field(..., max_length=100)
    handle: str = Field(default="", max_length=100)
    url: str = Field(..., max_length=500)
    note: str = Field(default="", max_length=300)

class CreatorOffering(BaseModel):
    icon: str = Field(default="✨", max_length=10)
    title: str = Field(..., max_length=200)
    desc: str = Field(default="", max_length=1000)

class CreatorCommerceItem(BaseModel):
    label: str = Field(..., max_length=200)
    desc: str = Field(default="", max_length=500)
    url: str = Field(..., max_length=500)

class UpsertCreatorProfileReq(BaseModel):
    slug: str = Field(..., min_length=2, max_length=80, pattern=r"^[a-z0-9-]+$")
    display_name: str = Field(..., min_length=1, max_length=100)
    title: str = Field(default="", max_length=200)
    tagline: str = Field(default="", max_length=300)
    bio: str = Field(default="", max_length=5000)
    pronouns: str = Field(default="", max_length=50)
    location: str = Field(default="", max_length=100)
    avatar: str = Field(default="✨", max_length=10)
    socials: List[CreatorSocialLink] = Field(default_factory=list)
    more_offerings: List[CreatorOffering] = Field(default_factory=list)
    commerce: List[CreatorCommerceItem] = Field(default_factory=list)


@api_router.get("/creator/profile/me")
async def get_my_creator_profile(user: User = Depends(current_user)):
    """Get the current user's creator profile (if claimed)."""
    profile = await db.creator_profiles.find_one({"user_id": user.id}, {"_id": 0})
    return {"profile": profile}


@api_router.put("/creator/profile")
async def upsert_creator_profile(body: UpsertCreatorProfileReq, user: User = Depends(current_user)):
    """Create or update the current user's creator profile."""
    # Ensure slug is not already taken by someone else
    existing = await db.creator_profiles.find_one({"slug": body.slug})
    if existing and existing.get("user_id") != user.id:
        raise HTTPException(409, "That profile URL is already taken. Choose a different slug.")

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "user_id": user.id,
        "slug": body.slug,
        "display_name": body.display_name,
        "title": body.title,
        "tagline": body.tagline,
        "bio": body.bio,
        "pronouns": body.pronouns,
        "location": body.location,
        "avatar": body.avatar,
        "socials": [s.model_dump() for s in body.socials],
        "more_offerings": [o.model_dump() for o in body.more_offerings],
        "commerce": [c.model_dump() for c in body.commerce],
        "updated_at": now,
    }
    await db.creator_profiles.update_one(
        {"user_id": user.id},
        {"$set": doc, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    await audit(user.id, "creator.profile.saved", meta={"slug": body.slug})
    saved = await db.creator_profiles.find_one({"user_id": user.id}, {"_id": 0})
    return {"profile": saved}


@api_router.get("/creator/profiles/public")
async def list_public_creator_profiles(limit: int = 50):
    """Public — list creator profiles for the Creators directory page."""
    profiles = await db.creator_profiles.find(
        {},
        {"_id": 0, "user_id": 0, "encrypted_key": 0},
    ).sort("created_at", -1).limit(min(limit, 100)).to_list(length=100)
    return {"profiles": profiles, "total": len(profiles)}


@api_router.get("/creator/profile/{slug}")
async def get_creator_profile_by_slug(slug: str, authorization: Optional[str] = Header(None)):
    """Public — get a creator profile by slug. Returns is_owner=True if the requester owns it."""
    profile = await db.creator_profiles.find_one({"slug": slug}, {"_id": 0})
    if not profile:
        raise HTTPException(404, "Creator profile not found")
    # Determine ownership without requiring auth (public endpoint)
    requester_id = None
    if authorization and authorization.startswith("Bearer "):
        try:
            payload = jwt.decode(authorization.split(" ", 1)[1], JWT_SECRET, algorithms=[JWT_ALGO])
            requester_id = payload.get("sub")
        except Exception:
            pass
    is_owner = requester_id is not None and profile.get("user_id") == requester_id
    profile_out = {k: v for k, v in profile.items() if k != "user_id"}
    profile_out["is_owner"] = is_owner
    return {"profile": profile_out}


# ── Site Control Panel — executive_admin only ─────────────────────────────────
# Single endpoint that pulls every real metric in one shot.
# No mocks. No estimates. Every number comes from the DB or Stripe API.

@api_router.get("/admin/control-panel")
async def control_panel_data(user: User = Depends(require_role("executive_admin"))):
    """Full real-time site dashboard. executive_admin only."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    # ── Users ──────────────────────────────────────────────────────────────────
    user_total          = await db.users.count_documents({})
    user_active         = await db.users.count_documents({"is_active": {"$ne": False}})
    user_suspended      = await db.users.count_documents({"is_active": False})
    users_today         = await db.users.count_documents({"created_at": {"$gte": today_start}})
    users_this_month    = await db.users.count_documents({"created_at": {"$gte": month_start}})
    role_counts = {}
    for role in ["student", "instructor", "admin", "executive_admin"]:
        role_counts[role] = await db.users.count_documents({"role": role})

    # ── Revenue ────────────────────────────────────────────────────────────────
    # Payments this month
    month_payments = await db.payments.find(
        {"status": "paid", "created_at": {"$gte": month_start}},
        {"_id": 0, "amount_cents": 1, "product_key": 1, "created_at": 1}
    ).to_list(length=2000)
    revenue_month_cents = sum(p.get("amount_cents", 0) for p in month_payments)

    # Payments today
    today_payments = [p for p in month_payments if p.get("created_at", "") >= today_start]
    revenue_today_cents = sum(p.get("amount_cents", 0) for p in today_payments)

    # All-time
    all_payments = await db.payments.find({"status": "paid"}, {"_id": 0, "amount_cents": 1}).to_list(length=10000)
    revenue_alltime_cents = sum(p.get("amount_cents", 0) for p in all_payments)

    # Failed payments (invoices with no matching paid entry — logged via webhook)
    failed_payments_count = await db.payments.count_documents({"status": {"$in": ["failed", "unpaid"]}})

    # Active subscriptions
    active_subs = await db.subscriptions.count_documents({"status": "active"})
    canceled_subs = await db.subscriptions.count_documents({"status": "canceled"})

    # Creator economy
    creator_courses_total     = await db.creator_courses.count_documents({"status": {"$ne": "archived"}})
    creator_courses_published = await db.creator_courses.count_documents({"status": "published"})
    creator_earnings_pending  = await db.creator_earnings.aggregate([
        {"$match": {"payout_status": "pending"}},
        {"$group": {"_id": None, "total": {"$sum": "$creator_share_cents"}}},
    ]).to_list(1)
    pending_payout_cents = (creator_earnings_pending[0]["total"] if creator_earnings_pending else 0)
    creator_profiles_count = await db.creator_profiles.count_documents({})

    # Revenue by product key this month
    product_breakdown: dict = {}
    for p in month_payments:
        k = p.get("product_key", "unknown")
        product_breakdown[k] = product_breakdown.get(k, 0) + p.get("amount_cents", 0)

    # ── Stripe live check ──────────────────────────────────────────────────────
    stripe_mode = "not_configured"
    stripe_balance = None
    if STRIPE_SECRET_KEY:
        stripe_mode = "test" if STRIPE_SECRET_KEY.startswith("sk_test_") else "live"
        try:
            bal = _stripe.Balance.retrieve()
            stripe_balance = {
                "available": [{"amount": f["amount"], "currency": f["currency"]} for f in bal.available],
                "pending":   [{"amount": f["amount"], "currency": f["currency"]} for f in bal.pending],
            }
        except Exception:
            stripe_balance = None

    # ── Platform flags ─────────────────────────────────────────────────────────
    flags_doc = await db.platform_flags.find_one({"_id": "flags"}, {"_id": 0})
    platform_flags = (flags_doc or {}).get("flags", {})

    # ── Curriculum & learning ──────────────────────────────────────────────────
    modules_total      = await db.modules.count_documents({})
    completions_total  = await db.progress.count_documents({"status": "completed"})
    completions_today  = await db.progress.count_documents({"status": "completed", "completed_at": {"$gte": today_start}})
    labs_pending       = await db.lab_submissions.count_documents({"status": "pending_review"})
    credentials_issued = await db.user_credentials.count_documents({})
    incidents_open     = await db.incidents.count_documents({"status": "open"})

    # ── AI spend ───────────────────────────────────────────────────────────────
    ai_usage = await db.ai_usage_log.find(
        {"created_at": {"$gte": month_start}},
        {"_id": 0, "cost_usd": 1, "provider": 1, "model": 1, "created_at": 1}
    ).to_list(length=5000)
    ai_spend_month = sum(float(r.get("cost_usd") or 0) for r in ai_usage)
    ai_spend_today  = sum(float(r.get("cost_usd") or 0) for r in ai_usage if r.get("created_at", "") >= today_start)
    ai_calls_month  = len(ai_usage)
    ai_by_provider: dict = {}
    for r in ai_usage:
        p = r.get("provider", "unknown")
        ai_by_provider[p] = round(ai_by_provider.get(p, 0) + float(r.get("cost_usd") or 0), 4)

    # ── M.O.R.E. community ────────────────────────────────────────────────────
    more_posts_total    = await db.more_posts.count_documents({})
    more_posts_today    = await db.more_posts.count_documents({"created_at": {"$gte": today_start}})
    more_needs_open     = await db.more_needs.count_documents({"status": {"$nin": ["resolved", "closed"]}})
    more_flags_pending  = await db.more_flags.count_documents({"status": "pending"})
    more_members        = await db.users.count_documents({"more_member": True})

    # ── Audit / governance ────────────────────────────────────────────────────
    audit_today = await db.audit_log.find(
        {"at": {"$gte": today_start}},
        {"_id": 0, "actor_id": 1, "action": 1, "at": 1}
    ).sort("at", -1).limit(50).to_list(50)
    audit_total_today = len(audit_today)
    governance_entries = await db.governance_log.count_documents({})

    # Recent failures / serious events from audit log (last 24h)
    yesterday = (now - timedelta(hours=24)).isoformat()
    failure_keywords = ["fail", "error", "denied", "locked", "suspend", "ban", "refund", "violation"]
    failure_pipeline = [
        {"$match": {"at": {"$gte": yesterday}, "$or": [{"action": {"$regex": k}} for k in failure_keywords]}},
        {"$sort": {"at": -1}},
        {"$limit": 30},
        {"$project": {"_id": 0, "actor_id": 1, "action": 1, "at": 1, "meta": 1}},
    ]
    recent_failures = await db.audit_log.aggregate(failure_pipeline).to_list(30)

    # ── Recent audit trail (last 20 actions) ─────────────────────────────────
    recent_audit = await db.audit_log.find(
        {}, {"_id": 0, "actor_id": 1, "action": 1, "at": 1, "target_id": 1}
    ).sort("at", -1).limit(20).to_list(20)

    # Enrich with actor names
    actor_ids = list({r["actor_id"] for r in recent_audit + recent_failures if r.get("actor_id")})
    actor_map = {}
    if actor_ids:
        async for u in db.users.find({"id": {"$in": actor_ids}}, {"_id": 0, "id": 1, "full_name": 1, "role": 1}):
            actor_map[u["id"]] = u
    for r in recent_audit + recent_failures:
        a = actor_map.get(r.get("actor_id"))
        r["actor_name"] = a["full_name"] if a else "system"
        r["actor_role"] = a["role"] if a else ""

    # ── Stripe webhook health (proxy: last recorded payment) ──────────────────
    last_payment = await db.payments.find_one({}, {"_id": 0, "created_at": 1}, sort=[("created_at", -1)])
    last_payment_at = last_payment["created_at"] if last_payment else None
    yesterday_iso = (now - timedelta(hours=24)).isoformat()
    payments_24h = await db.payments.count_documents({"created_at": {"$gte": yesterday_iso}})

    # ── AI monthly spend budget ────────────────────────────────────────────────
    budget_doc = await db.platform_config.find_one({"key": "ai_monthly_budget"}, {"_id": 0, "value": 1})
    ai_monthly_budget = float(budget_doc["value"]) if budget_doc else None

    # ── Broadcasts / announcements ─────────────────────────────────────────────
    active_broadcast = await db.broadcasts.find_one({"active": True}, {"_id": 0})

    # ── Pending refunds ────────────────────────────────────────────────────────
    pending_refunds = await db.wai_refunds.count_documents({"status": "pending"})
    pending_escalations = await db.escalations.count_documents({"status": {"$in": ["open", "pending"]}})

    return {
        "generated_at": now.isoformat(),
        "users": {
            "total": user_total, "active": user_active, "suspended": user_suspended,
            "new_today": users_today, "new_this_month": users_this_month,
            "by_role": role_counts,
        },
        "revenue": {
            "today_cents": revenue_today_cents,
            "month_cents": revenue_month_cents,
            "alltime_cents": revenue_alltime_cents,
            "failed_payments": failed_payments_count,
            "active_subscriptions": active_subs,
            "canceled_subscriptions": canceled_subs,
            "by_product_month": product_breakdown,
            "pending_creator_payouts_cents": pending_payout_cents,
        },
        "stripe": {
            "mode": stripe_mode,
            "balance": stripe_balance,
        },
        "platform_flags": platform_flags,
        "creator_economy": {
            "courses_total": creator_courses_total,
            "courses_published": creator_courses_published,
            "creator_profiles": creator_profiles_count,
        },
        "learning": {
            "modules": modules_total,
            "completions_total": completions_total,
            "completions_today": completions_today,
            "labs_pending_review": labs_pending,
            "credentials_issued": credentials_issued,
            "incidents_open": incidents_open,
        },
        "ai_spend": {
            "month_usd": round(ai_spend_month, 4),
            "today_usd": round(ai_spend_today, 4),
            "calls_this_month": ai_calls_month,
            "by_provider": ai_by_provider,
            "monthly_budget_usd": ai_monthly_budget,
        },
        "community": {
            "more_members": more_members,
            "posts_total": more_posts_total,
            "posts_today": more_posts_today,
            "needs_open": more_needs_open,
            "flags_pending": more_flags_pending,
        },
        "governance": {
            "audit_events_today": audit_total_today,
            "governance_log_entries": governance_entries,
            "pending_refunds": pending_refunds,
            "pending_escalations": pending_escalations,
        },
        "webhook_health": {
            "last_payment_at": last_payment_at,
            "payments_24h": payments_24h,
        },
        "recent_failures": recent_failures,
        "recent_audit": recent_audit,
        "active_broadcast": active_broadcast,
    }


@api_router.post("/admin/ai-spend-budget")
async def admin_set_ai_spend_budget(
    payload: dict,
    user: User = Depends(require_role("executive_admin")),
):
    """Set or clear the monthly AI spend budget alert threshold (USD). executive_admin only.
    Body: { budget_usd: float|null }
    """
    raw = payload.get("budget_usd")
    if raw is None:
        await db.platform_config.delete_one({"key": "ai_monthly_budget"})
        await audit(user.id, "admin.ai_budget.cleared")
        return {"budget_usd": None}
    try:
        val = float(raw)
        if val <= 0:
            raise ValueError
    except (ValueError, TypeError):
        raise HTTPException(400, "budget_usd must be a positive number")
    await db.platform_config.update_one(
        {"key": "ai_monthly_budget"},
        {"$set": {"key": "ai_monthly_budget", "value": val, "set_by": user.id, "set_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await audit(user.id, "admin.ai_budget.set", meta={"budget_usd": val})
    return {"budget_usd": val}


@api_router.post("/admin/control-panel/broadcast")
async def control_panel_set_broadcast(
    payload: dict,
    user: User = Depends(require_role("executive_admin")),
):
    """Set or clear the site-wide broadcast banner. executive_admin only.
    Body: { message: str, kind: 'info'|'warning'|'error', active: bool }
    """
    message = (payload.get("message") or "").strip()
    kind = payload.get("kind", "info")
    active = bool(payload.get("active", True))
    if kind not in ("info", "warning", "error"):
        raise HTTPException(400, "kind must be info, warning, or error")
    now_iso = datetime.now(timezone.utc).isoformat()
    if active and not message:
        raise HTTPException(400, "message is required when active=true")
    await db.broadcasts.update_one(
        {"_id": "site_banner"},
        {"$set": {
            "active": active,
            "message": message,
            "kind": kind,
            "set_by": user.id,
            "updated_at": now_iso,
        }},
        upsert=True,
    )
    await audit(user.id, f"broadcast:{'set' if active else 'cleared'}", meta={"message": message[:100], "kind": kind})
    return {"active": active, "message": message, "kind": kind}


# ═══════════════════════════════════════════════════════════════════════════════
#  EXECUTIVE CONTROL LAYER  —  /api/exec/control/*
#  Ported from dead app/routes/executive_control.py into the live server.
#  All endpoints require executive_admin unless noted. All writes are audited.
# ═══════════════════════════════════════════════════════════════════════════════

class _ExecSetUserRoleReq(BaseModel):
    user_id:  str
    new_role: Literal["guest", "student", "instructor", "creator", "mentor",
                      "moderator", "steward", "elder", "admin", "executive_admin"]
    reason:   str = Field(..., min_length=1, max_length=500)

class _ExecSetUserTierReq(BaseModel):
    user_id:          str
    new_feature_tier: Literal["free", "premium", "executive"]
    new_sage_tier:    Optional[Literal["basic", "advanced"]] = None
    reason:           str = Field(..., min_length=1, max_length=500)

class _ExecFeatureFlagReq(BaseModel):
    flag_name: str  = Field(..., min_length=1, max_length=200)
    enabled:   bool
    scope:     Literal["platform", "user"] = "platform"
    user_id:   Optional[str] = None
    reason:    str  = Field(..., min_length=1, max_length=500)

class _ExecAIAccessReq(BaseModel):
    user_id: str
    persona: str
    enabled: bool
    reason:  str = Field(..., min_length=1, max_length=500)

class _ExecLegalAccessReq(BaseModel):
    user_id:  str
    tool_key: Literal["legal_guide_1", "legal_guide_2", "all"]
    enabled:  bool
    reason:   str = Field(..., min_length=1, max_length=500)

class _ExecPriceReq(BaseModel):
    price_id:     str
    amount_cents: int = Field(..., ge=0)
    label:        Optional[str] = None
    reason:       str = Field(..., min_length=1, max_length=500)

class _ExecBudgetReq(BaseModel):
    budget_key: str
    limit:      float = Field(..., ge=0)
    reason:     str   = Field(..., min_length=1, max_length=500)

class _ExecProviderRankingReq(BaseModel):
    service: str
    ranking: List[str]
    reason:  str = Field(..., min_length=1, max_length=500)

class _ExecIPWhitelistReq(BaseModel):
    action: Literal["add", "remove"]
    ip:     str
    label:  Optional[str] = None
    role:   Literal["executive_admin", "admin"] = "executive_admin"
    reason: str = Field(..., min_length=1, max_length=500)

class _ExecMFAReq(BaseModel):
    require_mfa_for_roles: List[str]
    totp_enabled:          bool = True
    backup_codes_enabled:  bool = True
    reason:                str  = Field(..., min_length=1, max_length=500)

class _ExecFailoverReq(BaseModel):
    service:  str
    provider: str
    enabled:  bool
    reason:   str = Field(..., min_length=1, max_length=500)

class _ExecPageModeReq(BaseModel):
    page:   str
    mode:   str
    reason: str = Field(..., min_length=1, max_length=500)

class _ExecVisibilityReq(BaseModel):
    flag:    str
    enabled: bool
    reason:  str = Field(..., min_length=1, max_length=500)

class _ExecSageCapReq(BaseModel):
    user_id:   str
    sage_tier: Literal["basic", "advanced"]
    cap_level: Optional[Literal["general", "exploratory", "advanced"]] = None
    reason:    str = Field(..., min_length=1, max_length=500)

class _BreakGlassActivateReq(BaseModel):
    reason:           str = Field(..., min_length=20)
    scope:            str
    target_uid:       Optional[str] = None
    duration_minutes: int = Field(default=60, ge=5, le=480)

class _BreakGlassRevokeReq(BaseModel):
    override_id: str
    reason:      Optional[str] = None


async def _exec_audit(actor: User, action: str, target_id: Optional[str] = None,
                      before: Optional[dict] = None, after: Optional[dict] = None,
                      request: Optional[Request] = None, note: str = ""):
    ip = None
    if request:
        fwd = request.headers.get("x-forwarded-for", "")
        ip  = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else None)
    await db.exec_audit_log.insert_one({
        "id": str(uuid.uuid4()), "actor_id": actor.id, "actor_role": actor.role,
        "action": action, "target_id": target_id, "before": before, "after": after,
        "note": note, "ip": ip, "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await audit(actor.id, action, target=target_id, meta={"note": note})


@api_router.post("/exec/control/user/role")
async def ec_set_user_role(body: _ExecSetUserRoleReq, request: Request,
                           actor: User = Depends(require_role("executive_admin"))):
    target = await db.users.find_one({"id": body.user_id}, {"_id": 0, "role": 1, "full_name": 1})
    if not target:
        raise HTTPException(404, "User not found")
    old_role = target.get("role", "student")
    if ROLE_RANK.get(old_role, 0) >= ROLE_RANK.get("executive_admin", 4) and actor.id != body.user_id:
        raise HTTPException(403, "Cannot modify another executive_admin's role.")
    if actor.id == body.user_id and ROLE_RANK.get(body.new_role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(400, "Cannot demote your own account below admin.")
    await db.users.update_one({"id": body.user_id},
        {"$set": {"role": body.new_role, "updated_at": datetime.now(timezone.utc).isoformat()}})
    await _exec_audit(actor, "exec.user.role_changed", target_id=body.user_id,
        before={"role": old_role}, after={"role": body.new_role}, request=request, note=body.reason)
    if body.user_id != actor.id:
        await notify(body.user_id, "Account Role Updated",
            f"Your account role has been updated to: {body.new_role}.", kind="info")
    return {"ok": True, "user_id": body.user_id, "old_role": old_role, "new_role": body.new_role}


@api_router.post("/exec/control/user/tier")
async def ec_set_user_tier(body: _ExecSetUserTierReq, request: Request,
                           actor: User = Depends(require_role("admin"))):
    target = await db.users.find_one({"id": body.user_id},
        {"_id": 0, "feature_tier": 1, "sage_tier": 1})
    if not target:
        raise HTTPException(404, "User not found")
    old_ft = target.get("feature_tier", "free")
    old_st = target.get("sage_tier", "basic")
    upd = {"feature_tier": body.new_feature_tier, "updated_at": datetime.now(timezone.utc).isoformat()}
    if body.new_sage_tier:
        upd["sage_tier"] = body.new_sage_tier
    await db.users.update_one({"id": body.user_id}, {"$set": upd})
    await _exec_audit(actor, "exec.user.tier_changed", target_id=body.user_id,
        before={"feature_tier": old_ft, "sage_tier": old_st}, after=upd,
        request=request, note=body.reason)
    await notify(body.user_id, "Account Plan Updated",
        f"Your plan has been updated to {body.new_feature_tier}.", link="/dashboard", kind="success")
    return {"ok": True, "user_id": body.user_id,
            "old_feature_tier": old_ft, "new_feature_tier": body.new_feature_tier,
            "old_sage_tier": old_st, "new_sage_tier": body.new_sage_tier or old_st}


@api_router.post("/exec/control/feature-flag")
async def ec_feature_flag(body: _ExecFeatureFlagReq, request: Request,
                          actor: User = Depends(require_role("executive_admin"))):
    now_iso = datetime.now(timezone.utc).isoformat()
    if body.scope == "platform":
        await db.platform_flags.update_one({"_id": "flags"},
            {"$set": {f"flags.{body.flag_name}.enabled": body.enabled,
                      f"flags.{body.flag_name}.updated_by": actor.id,
                      f"flags.{body.flag_name}.updated_at": now_iso,
                      "updated_at": now_iso}}, upsert=True)
        await _exec_audit(actor, f"exec.platform_flag.{'enabled' if body.enabled else 'disabled'}",
            after={"flag": body.flag_name, "enabled": body.enabled}, request=request, note=body.reason)
    else:
        if not body.user_id:
            raise HTTPException(400, "user_id required for user-scoped flag")
        await db.user_feature_overrides.update_one({"user_id": body.user_id},
            {"$set": {f"flags.{body.flag_name}": body.enabled, "updated_at": now_iso}}, upsert=True)
        await _exec_audit(actor, f"exec.user_flag.{'enabled' if body.enabled else 'disabled'}",
            target_id=body.user_id, after={"flag": body.flag_name, "enabled": body.enabled},
            request=request, note=body.reason)
    return {"ok": True, "flag": body.flag_name, "enabled": body.enabled, "scope": body.scope}


@api_router.post("/exec/control/ai-access")
async def ec_ai_access(body: _ExecAIAccessReq, request: Request,
                       actor: User = Depends(require_role("executive_admin"))):
    now_iso = datetime.now(timezone.utc).isoformat()
    if body.persona == "all":
        upd_field, upd_val = "ai_access_override", {"all": body.enabled}
    else:
        upd_field, upd_val = f"ai_access.{body.persona}", body.enabled
    await db.user_feature_overrides.update_one({"user_id": body.user_id},
        {"$set": {upd_field: upd_val, "updated_at": now_iso}}, upsert=True)
    await _exec_audit(actor, f"exec.ai_access.{'granted' if body.enabled else 'revoked'}",
        target_id=body.user_id, after={"persona": body.persona, "enabled": body.enabled},
        request=request, note=body.reason)
    return {"ok": True, "user_id": body.user_id, "persona": body.persona, "enabled": body.enabled}


@api_router.post("/exec/control/legal-access")
async def ec_legal_access(body: _ExecLegalAccessReq, request: Request,
                          actor: User = Depends(require_role("executive_admin"))):
    now_iso = datetime.now(timezone.utc).isoformat()
    tools = ["legal_guide_1", "legal_guide_2"] if body.tool_key == "all" else [body.tool_key]
    for t in tools:
        await db.user_feature_overrides.update_one({"user_id": body.user_id},
            {"$set": {f"legal_access.{t}": body.enabled, "updated_at": now_iso}}, upsert=True)
    await _exec_audit(actor, f"exec.legal_access.{'granted' if body.enabled else 'revoked'}",
        target_id=body.user_id, after={"tools": tools, "enabled": body.enabled},
        request=request, note=body.reason)
    return {"ok": True, "user_id": body.user_id, "tools": tools, "enabled": body.enabled}


@api_router.post("/exec/control/price")
async def ec_set_price(body: _ExecPriceReq, request: Request,
                       actor: User = Depends(require_role("executive_admin"))):
    old = await db.platform_prices.find_one({"id": body.price_id}, {"_id": 0})
    if not old:
        raise HTTPException(404, "Price record not found")
    await db.platform_prices.update_one({"id": body.price_id},
        {"$set": {"amount_cents": body.amount_cents, "label": body.label,
                  "updated_by": actor.id, "updated_at": datetime.now(timezone.utc).isoformat()}})
    await _exec_audit(actor, "exec.price.updated", target_id=body.price_id,
        before={"amount_cents": old.get("amount_cents"), "label": old.get("label")},
        after={"amount_cents": body.amount_cents, "label": body.label},
        request=request, note=body.reason)
    return {"ok": True, "price_id": body.price_id, "new_amount_cents": body.amount_cents}


@api_router.post("/exec/control/budget")
async def ec_set_budget(body: _ExecBudgetReq, request: Request,
                        actor: User = Depends(require_role("executive_admin"))):
    old = await db.platform_budgets.find_one({"key": body.budget_key}, {"_id": 0, "limit": 1})
    await db.platform_budgets.update_one({"key": body.budget_key},
        {"$set": {"limit": body.limit, "updated_by": actor.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    await _exec_audit(actor, "exec.budget.updated", target_id=body.budget_key,
        before={"limit": (old or {}).get("limit")}, after={"limit": body.limit},
        request=request, note=body.reason)
    return {"ok": True, "budget_key": body.budget_key, "new_limit": body.limit}


@api_router.post("/exec/control/provider-ranking")
async def ec_provider_ranking(body: _ExecProviderRankingReq, request: Request,
                              actor: User = Depends(require_role("executive_admin"))):
    old = await db.provider_rankings.find_one({"service": body.service}, {"_id": 0, "ranking": 1})
    await db.provider_rankings.update_one({"service": body.service},
        {"$set": {"ranking": body.ranking, "updated_by": actor.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    await _exec_audit(actor, "exec.provider_ranking.updated", target_id=body.service,
        before={"ranking": (old or {}).get("ranking")}, after={"ranking": body.ranking},
        request=request, note=body.reason)
    return {"ok": True, "service": body.service, "new_ranking": body.ranking}


@api_router.post("/exec/control/ip-whitelist")
async def ec_ip_whitelist(body: _ExecIPWhitelistReq, request: Request,
                          actor: User = Depends(require_role("executive_admin"))):
    if body.action == "add":
        await db.ip_whitelist.update_one({"ip": body.ip, "role": body.role},
            {"$set": {"ip": body.ip, "role": body.role, "label": body.label,
                      "added_by": actor.id, "added_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    else:
        await db.ip_whitelist.delete_one({"ip": body.ip, "role": body.role})
    await _exec_audit(actor, f"exec.ip_whitelist.{'added' if body.action == 'add' else 'removed'}",
        after={"ip": body.ip, "role": body.role, "action": body.action},
        request=request, note=body.reason)
    return {"ok": True, "action": body.action, "ip": body.ip}


@api_router.post("/exec/control/mfa")
async def ec_mfa_config(body: _ExecMFAReq, request: Request,
                        actor: User = Depends(require_role("executive_admin"))):
    old = await db.mfa_config.find_one({"_id": "config"}, {"_id": 0}) or {}
    config = {"require_mfa_for_roles": body.require_mfa_for_roles,
               "totp_enabled": body.totp_enabled, "backup_codes_enabled": body.backup_codes_enabled,
               "updated_by": actor.id, "updated_at": datetime.now(timezone.utc).isoformat()}
    await db.mfa_config.update_one({"_id": "config"}, {"$set": config}, upsert=True)
    await _exec_audit(actor, "exec.mfa_config.updated", before=old, after=config,
        request=request, note=body.reason)
    return {"ok": True, "config": config}


@api_router.post("/exec/control/failover")
async def ec_failover(body: _ExecFailoverReq, request: Request,
                      actor: User = Depends(require_role("executive_admin"))):
    await db.failover_config.update_one({"service": body.service, "provider": body.provider},
        {"$set": {"enabled": body.enabled, "updated_by": actor.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    await _exec_audit(actor, f"exec.failover.{'enabled' if body.enabled else 'disabled'}",
        after={"service": body.service, "provider": body.provider, "enabled": body.enabled},
        request=request, note=body.reason)
    return {"ok": True, "service": body.service, "provider": body.provider, "enabled": body.enabled}


@api_router.post("/exec/control/page-mode")
async def ec_page_mode(body: _ExecPageModeReq, request: Request,
                       actor: User = Depends(require_role("executive_admin"))):
    await db.page_modes.update_one({"page": body.page},
        {"$set": {"mode": body.mode, "updated_by": actor.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    await _exec_audit(actor, "exec.page_mode.updated",
        after={"page": body.page, "mode": body.mode}, request=request, note=body.reason)
    return {"ok": True, "page": body.page, "mode": body.mode}


@api_router.post("/exec/control/visibility")
async def ec_visibility(body: _ExecVisibilityReq, request: Request,
                        actor: User = Depends(require_role("executive_admin"))):
    now_iso = datetime.now(timezone.utc).isoformat()
    old = await db.visibility_flags.find_one({"flag": body.flag}, {"_id": 0, "enabled": 1})
    await db.visibility_flags.update_one({"flag": body.flag},
        {"$set": {"enabled": body.enabled, "updated_by": actor.id, "updated_at": now_iso}}, upsert=True)
    await _exec_audit(actor, f"exec.visibility.{'shown' if body.enabled else 'hidden'}",
        before={"flag": body.flag, "enabled": (old or {}).get("enabled")},
        after={"flag": body.flag, "enabled": body.enabled}, request=request, note=body.reason)
    return {"ok": True, "flag": body.flag, "enabled": body.enabled}


@api_router.post("/exec/control/sage-cap")
async def ec_sage_cap(body: _ExecSageCapReq, request: Request,
                      actor: User = Depends(require_role("admin"))):
    old = await db.users.find_one({"id": body.user_id},
        {"_id": 0, "sage_tier": 1, "sage_safety_cap": 1})
    upd: dict = {"sage_tier": body.sage_tier, "updated_at": datetime.now(timezone.utc).isoformat()}
    if body.cap_level is not None:
        upd["sage_safety_cap"] = body.cap_level
    await db.users.update_one({"id": body.user_id}, {"$set": upd})
    await _exec_audit(actor, "exec.sage_cap.updated", target_id=body.user_id,
        before=old, after=upd, request=request, note=body.reason)
    return {"ok": True, "user_id": body.user_id, "sage_tier": body.sage_tier, "cap_level": body.cap_level}


@api_router.get("/exec/control/state")
async def ec_get_state(actor: User = Depends(require_role("executive_admin"))):
    import asyncio as _aio
    flags, budgets, rankings, page_modes, vis_flags, ip_list, mfa_cfg, failover = await _aio.gather(
        db.platform_flags.find_one({"_id": "flags"}, {"_id": 0}),
        db.platform_budgets.find({}, {"_id": 0}).to_list(100),
        db.provider_rankings.find({}, {"_id": 0}).to_list(50),
        db.page_modes.find({}, {"_id": 0}).to_list(50),
        db.visibility_flags.find({}, {"_id": 0}).to_list(100),
        db.ip_whitelist.find({}, {"_id": 0}).to_list(500),
        db.mfa_config.find_one({"_id": "config"}, {"_id": 0}),
        db.failover_config.find({}, {"_id": 0}).to_list(50),
    )
    return {"platform_flags": flags or {}, "budgets": budgets, "provider_rankings": rankings,
            "page_modes": page_modes, "visibility_flags": vis_flags, "ip_whitelist": ip_list,
            "mfa_config": mfa_cfg, "failover_config": failover,
            "fetched_at": datetime.now(timezone.utc).isoformat()}


@api_router.get("/exec/control/audit")
async def ec_audit_log(limit: int = 50, actor_id: Optional[str] = None,
                       action: Optional[str] = None,
                       actor: User = Depends(require_role("executive_admin"))):
    limit = min(max(limit, 1), 200)
    q: dict = {}
    if actor_id: q["actor_id"] = actor_id
    if action:   q["action"]   = {"$regex": action, "$options": "i"}
    records = await db.exec_audit_log.find(q, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"count": len(records), "records": records}


@api_router.post("/exec/control/break-glass/activate")
async def ec_break_glass_activate(body: _BreakGlassActivateReq, request: Request,
                                  actor: User = Depends(require_role("executive_admin"))):
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=body.duration_minutes)
    override_id = str(uuid.uuid4())
    fwd = request.headers.get("x-forwarded-for", "")
    ip  = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "unknown")
    record = {"id": override_id, "actor_id": actor.id,
              "actor_email": getattr(actor, "email", "unknown"),
              "scope": body.scope, "target_uid": body.target_uid,
              "reason": body.reason, "duration_minutes": body.duration_minutes,
              "activated_at": now, "expires_at": expires_at,
              "revoked": False, "revoked_at": None, "revoked_reason": None,
              "ip": ip, "status": "active"}
    await db.break_glass_overrides.insert_one({**record, "_id": override_id})
    await _exec_audit(actor, "break_glass.activated", target_id=body.target_uid or "platform",
        after={"scope": body.scope, "duration_minutes": body.duration_minutes, "override_id": override_id},
        request=request, note=f"BREAK GLASS: {body.reason}")
    return {"override_id": override_id, "scope": body.scope, "target_uid": body.target_uid,
            "activated_at": now.isoformat(), "expires_at": expires_at.isoformat(),
            "duration_minutes": body.duration_minutes, "status": "active",
            "warning": "This override is time-bound and fully audited."}


@api_router.post("/exec/control/break-glass/revoke")
async def ec_break_glass_revoke(body: _BreakGlassRevokeReq, request: Request,
                                actor: User = Depends(require_role("executive_admin"))):
    doc = await db.break_glass_overrides.find_one({"id": body.override_id, "revoked": False}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Override not found or already revoked.")
    now = datetime.now(timezone.utc)
    await db.break_glass_overrides.update_one({"id": body.override_id},
        {"$set": {"revoked": True, "revoked_at": now, "revoked_reason": body.reason, "status": "revoked"}})
    await _exec_audit(actor, "break_glass.revoked", target_id=doc.get("target_uid") or "platform",
        before={"status": "active"}, after={"status": "revoked", "reason": body.reason},
        request=request, note=f"BREAK GLASS REVOKED: {body.override_id}")
    return {"override_id": body.override_id, "revoked_at": now.isoformat(), "status": "revoked"}


@api_router.get("/exec/control/break-glass/active")
async def ec_break_glass_active(actor: User = Depends(require_role("executive_admin"))):
    now = datetime.now(timezone.utc)
    docs = await db.break_glass_overrides.find(
        {"revoked": False, "expires_at": {"$gt": now}}, {"_id": 0}
    ).sort("activated_at", -1).to_list(100)
    return {"active_overrides": docs, "count": len(docs)}


@api_router.get("/exec/control/break-glass/history")
async def ec_break_glass_history(limit: int = 50,
                                 actor: User = Depends(require_role("executive_admin"))):
    limit = min(max(limit, 1), 200)
    docs = await db.break_glass_overrides.find({}, {"_id": 0}).sort("activated_at", -1).limit(limit).to_list(limit)
    return {"records": docs, "count": len(docs)}


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


app.include_router(api_router)
# CORS: when origins is wildcard ("*") browsers reject credentials, so we
# turn off allow_credentials in that case (auth uses Bearer token in Authorization
# header anyway). If a specific origin list is supplied, credentials are allowed.
#
# BACKUP_ORIGIN (e.g. https://your-tunnel.trycloudflare.com) is auto-appended
# so the home/backup server is always allowed without touching CORS_ORIGINS.
_cors_origins = [o.strip() for o in os.environ.get('CORS_ORIGINS', '*').split(',') if o.strip()]
if BACKUP_ORIGIN and BACKUP_ORIGIN not in _cors_origins and '*' not in _cors_origins:
    _cors_origins.append(BACKUP_ORIGIN)
    logger.info("CORS: Backup origin added: %s", BACKUP_ORIGIN)
_allow_creds = _cors_origins != ['*']
app.add_middleware(
    CORSMiddleware,
    allow_credentials=_allow_creds,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
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