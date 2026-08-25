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
from roles import Role, ROLE_RANK, LEGACY_ROLE_MAP, normalize_role, role_rank, ALL_ROLES

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
from security.feature_control import (
    check_request_config,
    check_user_feature_access,
    feature_for_path,
    fcc_feature_for_path,
)

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

_jwt_raw = os.environ.get('JWT_SECRET', '').strip()
if not _jwt_raw:
    import logging as _log
    _log.getLogger('lcewai').critical(
        'FATAL: JWT_SECRET is not set. Sessions will not work and auth will fail. '
        'Set a persistent JWT_SECRET in your deploy environment (e.g. Railway Variables).'
    )
    JWT_SECRET = _secrets.token_hex(32)
    JWT_SECRET_IS_EPHEMERAL = True
else:
    JWT_SECRET = _jwt_raw
    JWT_SECRET_IS_EPHEMERAL = False
JWT_ALGO = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_HOURS = int(os.environ.get('JWT_EXPIRE_HOURS', '168'))
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', EMERGENT_LLM_KEY)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', EMERGENT_LLM_KEY)

# ── Backup server / home server config ───────────────────────────────────────
# SERVE_FRONTEND defaults ON (unless explicitly set to 0): the deployment
# Dockerfile bakes the React build into /app/frontend/build, so the backend
# serves the SPA and the frontend calls the API same-origin at /api — the
# single-service topology. Set SERVE_FRONTEND=0 only for API-only hosts.
# Set BACKUP_ORIGIN=https://your-cloudflare-tunnel.trycloudflare.com so the
# home server URL is automatically allowed by CORS.
SERVE_FRONTEND  = os.environ.get('SERVE_FRONTEND', '1') != '0'
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
            doc = await db.platform_flags.find_one({"_id": "flags"}, {"_id": 0})
            if doc and doc.get("flags", {}).get("platform_locked", {}).get("enabled"):
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Platform is currently locked by the executive team. Please check back shortly."},
                )
            # ── Per-user enforcement (feature overrides + feature_tier) ─────────
            # Only runs on mapped feature surfaces and only when a valid session
            # resolves; the route's own auth still produces the 401 for missing
            # tokens.  An explicit per-user grant skips the platform checks.
            if feature_for_path(path) or fcc_feature_for_path(path):
                user = None
                authz = request.headers.get("authorization")
                if authz:
                    try:
                        user = await current_user(authz)
                    except Exception:
                        user = None  # let the route handler raise the 401/403
                action, detail = await check_user_feature_access(db, user, path)
                if action == "block":
                    return JSONResponse(status_code=403, content={"detail": detail})
                if action == "unavailable":
                    return JSONResponse(
                        status_code=503,
                        content={"detail": detail},
                        headers={"cache-control": "no-store"},
                    )
                if action == "allow":
                    return await call_next(request)
            # Enforce the exec panel's platform controls (feature flags + page
            # access).  Safe default: only blocks when an executive explicitly
            # disabled a mapped flag/page — absent config == allow.
            decision = await check_request_config(db, path, doc)
            if decision:
                return JSONResponse(status_code=decision[0], content={"detail": decision[1]})
        except Exception:
            # A mapped feature cannot be authorized when its policy store is
            # unavailable.  Fail closed for the sensitive surface; leave
            # unrelated/public endpoints alone so a database outage does not
            # turn the whole site into a maintenance page.
            controlled = (
                feature_for_path(path) is not None
                or fcc_feature_for_path(path) is not None
                or path.startswith("/api/ai/")
            )
            if controlled:
                logger.exception("Feature authorization unavailable for %s", path)
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Feature authorization unavailable — request rejected."},
                    headers={"cache-control": "no-store"},
                )
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

# Role hierarchy imported from roles.py (canonical source of truth).
# 8-tier: public(0) < student(1) < trial_pass(2) < instructor(3) <
#         support_staff(4) < oversight(5) < admin(6) < executive_admin(7)

# Executive seat emails come from the environment ONLY — there are no
# hardcoded fallbacks. A seat is created at startup only when its email is
# explicitly configured; docker-entrypoint.sh refuses to boot when none are
# set, so a fresh database can never silently fall to the first registrant.
EXEC_ADMIN_EMAIL = os.environ.get("EXEC_ADMIN_EMAIL", "").strip()
# Seed password for the executive admin.  Read from env var first; falls back
# to the documented default (which is force-rotated on first login via
# `must_change_password=True`, so the seed is safe by construction).  In
# production set EXEC_DEFAULT_PASSWORD to a fresh secret so even the seed
# value is operator-controlled.
# No fallback passwords in source. If EXEC_DEFAULT_PASSWORD is not set in Railway,
# a cryptographically random password is generated at startup and emailed to
# PLATFORM_NOTIFY_EMAIL (must be explicitly configured) automatically.
EXEC_DEFAULT_PASSWORD = os.environ.get("EXEC_DEFAULT_PASSWORD", "")

# Executive seats — bootstrapped at startup ONLY when the email is explicitly
# configured (empty env var = seat skipped). No hardcoded addresses.
BACKUP_EXEC_EMAIL = os.environ.get("BACKUP_EXEC_ADMIN_EMAIL", "").strip()
BACKUP_EXEC_DEFAULT_PASSWORD = os.environ.get("BACKUP_EXEC_DEFAULT_PASSWORD", "")

NAM_EXEC_EMAIL = os.environ.get("NAM_EXEC_EMAIL", "").strip()
NAM_EXEC_DEFAULT_PASSWORD = os.environ.get("NAM_EXEC_DEFAULT_PASSWORD", "")

# Platform notification email — receives auto-generated passwords and system alerts.
# Env-only. Falls back to the configured GMAIL_USER if set, otherwise empty
# (alerts are logged instead of emailed; no mail goes to an unconfigured inbox).
PLATFORM_NOTIFY_EMAIL = os.environ.get("PLATFORM_NOTIFY_EMAIL",
                                        os.environ.get("GMAIL_USER", "")).strip()

# Fail-closed guard: with no exec seat configured, a fresh database has no
# owner and the first registrant becomes executive_admin (auth.py register).
# docker-entrypoint.sh refuses to boot in this state; this log makes the
# condition unmissable on any other boot path too.
if not (EXEC_ADMIN_EMAIL or BACKUP_EXEC_EMAIL or NAM_EXEC_EMAIL):
    import logging as _log
    _log.getLogger("lcewai").critical(
        "No executive admin email is configured (EXEC_ADMIN_EMAIL / "
        "BACKUP_EXEC_ADMIN_EMAIL / NAM_EXEC_EMAIL all empty). On a fresh "
        "database the first registered user would become executive_admin. "
        "Set at least one seat email before going live."
    )

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
LEGACY_EXEC_EMAILS = {"delon.oliver@lightningcityelectric.com"}


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
    # $3 BYOK entitlement (flipped by POST /api/byok/activate).  Exposed on
    # /auth/me so the frontend can show the BYOK-unlock state in navigation.
    byok_enabled: bool = False


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

# ---- Member Projects Routes ("Have your M.O.R.E. team work on it") ----
# Registered at import time here (the main include block sits far below this
# line; FastAPI collects routes regardless of order). Customer-facing:
# any authenticated user whose tier covers `member` can ask the M.O.R.E.
# team to work on a goal, review what it produces, and approve it.
try:
    from routers import member_projects as _mp_mod
    app.include_router(_mp_mod.router)
    logger.info("Member Projects routes registered at /api/my-projects")
except Exception as _mp_err:
    logger.warning("Member Projects routes failed to load: %s", _mp_err)


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
RESEND_FROM = os.environ.get("RESEND_FROM", "")  # env-only — no hardcoded from-address
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


async def _send_via_resend(to_email: str, subject: str, html: str) -> tuple[bool, str]:
    """Send via Resend API. Returns (True, "") on success or (False, reason)."""
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
            reason = f"Resend HTTP {r.status_code}: {r.text[:200]}"
            logger.warning("Resend send failed: %s", reason)
            return False, reason
        return True, ""
    except Exception as exc:
        logger.exception("Resend send raised")
        return False, f"Resend request raised: {exc}"


async def _send_via_gmail(to_email: str, subject: str, html: str) -> tuple[bool, str]:
    """Send via Gmail SMTP using an App Password. Returns (True, "") on
    success or (False, reason). Requires GMAIL_USER and GMAIL_APP_PASSWORD
    set in the Railway environment."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        return False, "GMAIL_USER / GMAIL_APP_PASSWORD not configured"
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
        return True, ""
    except Exception as exc:
        logger.exception("Gmail SMTP send raised")
        return False, f"Gmail SMTP raised: {exc}"


async def _send_reset_email(to_email: str, raw_token: str, full_name: str = "there", base_url: str = "") -> tuple[bool, str]:
    """Send password reset email. Tries Resend first, falls back to Gmail SMTP.
    Returns (True, "") when sent, or (False, reason) so the API response can
    surface the exact failure instead of failing silently."""
    reset_url = _build_reset_url(raw_token, base=base_url or None)
    if reset_url.startswith("/"):
        reason = "PUBLIC_APP_URL is not set on the server (and no request origin was available)"
        logger.error("Password reset email blocked: %s", reason)
        return False, reason
    subject, html = _reset_email_html(full_name, reset_url)

    if RESEND_API_KEY:
        sent, resend_reason = await _send_via_resend(to_email, subject, html)
        if sent:
            return True, ""
        logger.warning("Resend failed (%s) — falling back to Gmail SMTP", resend_reason)
    else:
        resend_reason = "RESEND_API_KEY is not set on the server"

    if GMAIL_USER and GMAIL_APP_PASSWORD:
        sent, gmail_reason = await _send_via_gmail(to_email, subject, html)
        if sent:
            return True, ""
        return False, f"Resend failed ({resend_reason}); Gmail also failed ({gmail_reason})"

    if RESEND_API_KEY:
        return False, f"Resend rejected the send: {resend_reason}"

    return False, "No email provider configured on the server (set RESEND_API_KEY, or GMAIL_USER + GMAIL_APP_PASSWORD)"


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
        sent, _reason = await _send_via_resend(to_email, subject, html)
        if sent:
            return True
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        sent, _reason = await _send_via_gmail(to_email, subject, html)
        return sent
    logger.warning("Welcome email not sent — no email provider configured.")
    return False
# ----------------------------------------------------------------------------


def make_token(user_id: str, role: str, extra: Optional[dict] = None) -> str:
    """Issue a JWT carrying the user's current revocation generation.

    ``token_version`` is stored on the user document and incremented whenever
    credentials, role, tier, activation, or sessions change.  The claim is
    deliberately short (``tv``) to preserve compatibility with existing
    tokens; tokens created before this claim existed are treated as generation
    zero and remain valid until their normal expiry.
    """
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    extra = dict(extra or {})
    raw_version = extra.get("tv", 0)
    try:
        token_version = int(raw_version)
    except (TypeError, ValueError):
        token_version = 0
    payload = {"sub": user_id, "role": role, "exp": exp, "tv": token_version}
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

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Invalid token subject")
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(401, "User not found")
    if user_doc.get("is_active") is False:
        raise HTTPException(403, "Account deactivated")

    # Role/credential/session mutations increment this generation.  Comparing
    # it here makes those existing mutations actually revoke already-issued
    # JWTs instead of merely updating a field no request ever reads.
    try:
        token_version = int(payload.get("tv", 0))
        current_version = int(user_doc.get("token_version", 0))
    except (TypeError, ValueError):
        raise HTTPException(401, "Invalid session generation")
    if token_version != current_version:
        raise HTTPException(401, "Session revoked — please sign in again")

    # Login tokens are bound to an auth_sessions row when one was recorded.
    # Deleting that row (single-device logout or force logout) therefore
    # invalidates the token immediately, while legacy/sessionless tokens remain
    # governed by token_version.
    session_id = payload.get("session_id")
    if session_id:
        try:
            session = await db.auth_sessions.find_one(
                {"user_id": user_id, "session_id": session_id}, {"_id": 1}
            )
        except Exception:
            logger.exception("Session verification failed for user %s", user_id)
            raise HTTPException(503, "Session verification unavailable — request rejected")
        if not session:
            raise HTTPException(401, "Session revoked — please sign in again")

    return User(**user_doc)


def require_role(*roles):
    """Authorize the current user against a hierarchy.

    Pass if the user's role rank is >= the LOWEST rank among the requested
    roles.  Uses role_rank() which normalizes legacy role strings via
    LEGACY_ROLE_MAP so old MongoDB documents still pass correctly.
    """
    needed_rank = min(role_rank(r) for r in roles)
    async def dep(user: User = Depends(current_user)) -> User:
        if role_rank(user.role) < needed_rank:
            logger.warning("Unauthorized access attempt — insufficient privileges (user=%s, role=%s)", user.id, user.role)
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user
    return dep


def assert_role(user: User, *roles) -> None:
    """Inline authorization check (raises 403 if the user lacks the rank)."""
    needed_rank = min(role_rank(r) for r in roles)
    if role_rank(user.role) < needed_rank:
        raise HTTPException(403, "Insufficient permissions to access this resource.")


def can_modify(actor: User, target_role: str) -> bool:
    """Returns True iff `actor` is allowed to modify a user whose role is
    `target_role`. Admins cannot touch executive_admin accounts; only an
    executive_admin can modify another executive_admin."""
    return role_rank(actor.role) >= role_rank(target_role)


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


async def seed_starter_library():
    """Seed the 4 starter-library ebooks as sellable media products.

    Each product gets a description, $4.00 price, and published status.
    The actual markdown files live in content/starter-library/ and are
    available for download once the product record exists.
    """
    STARTER_BOOKS = [
        {
            "title": "The Small Start",
            "description": "A Practical Guide to Turning One Good Idea Into Something Real. Written by the Morehelp.center Support Team, synthesized and authored by NAM Oshun. 16 chapters of practical guidance for creators, writers, artists, entrepreneurs, and anyone with too many ideas.",
            "price_cents": 400,
            "type": "ebook",
            "tags": ["starter-library", "ebook", "creator-tools"],
            "file_path": "content/starter-library/the-small-start.md",
        },
        {
            "title": "From Creator to Product",
            "description": "How to Turn Your Writing, Music, Knowledge, and Ideas Into Things People Can Use. Written by the Morehelp.center Support Team, synthesized and authored by NAM Oshun. Practical product-conversion exercises for writers, musicians, poets, educators, and artists.",
            "price_cents": 400,
            "type": "ebook",
            "tags": ["starter-library", "ebook", "creator-economy"],
            "file_path": "content/starter-library/from-creator-to-product.md",
        },
        {
            "title": "AI Without the Intimidation",
            "description": "A Human-First Guide to Using AI Without Losing Your Judgment. Written by the Morehelp.center Support Team, synthesized and authored by NAM Oshun. Practical introduction to AI for beginners, creators, educators, and community organizations.",
            "price_cents": 400,
            "type": "ebook",
            "tags": ["starter-library", "ebook", "ai-literacy"],
            "file_path": "content/starter-library/ai-without-the-intimidation.md",
        },
        {
            "title": "The Community Funding Starter",
            "description": "A Practical Guide to Turning a Good Community Idea Into a Fundable Plan. Written by the Morehelp.center Support Team, synthesized and authored by NAM Oshun. Worksheets, budget templates, and funding-readiness checklists for grassroots organizers.",
            "price_cents": 400,
            "type": "ebook",
            "tags": ["starter-library", "ebook", "community-funding"],
            "file_path": "content/starter-library/the-community-funding-starter.md",
        },
    ]
    seeded = 0
    for book in STARTER_BOOKS:
        existing = await db.media_products.find_one({"title": book["title"]})
        if existing:
            continue
        product = {
            "id": str(uuid.uuid4())[:12],
            "title": book["title"],
            "description": book["description"],
            "price_cents": book["price_cents"],
            "type": book["type"],
            "tags": book["tags"],
            "file_path": book["file_path"],
            "file_url": f"/api/media/file/{book['file_path'].replace('/', '_')}",
            "published": True,
            "owner_id": "platform",
            "created_at": datetime.utcnow().isoformat(),
        }
        await db.media_products.insert_one(product)
        seeded += 1
    if seeded:
        logger.info("Seeded %d starter-library ebooks into media_products", seeded)


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
    # ── Role migration: rename legacy role strings to canonical 8-tier names ──
    for old_role, (new_role, _) in LEGACY_ROLE_MAP.items():
        result = await db.users.update_many(
            {"role": old_role}, {"$set": {"role": new_role}},
        )
        if result.modified_count:
            logger.info("Role migration: %d user(s) role '%s' → '%s'", result.modified_count, old_role, new_role)

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
        _seat for _seat in [
            (EXEC_ADMIN_EMAIL,  "Delon Oliver",  EXEC_DEFAULT_PASSWORD),
            (BACKUP_EXEC_EMAIL, "Delon Oliver",  BACKUP_EXEC_DEFAULT_PASSWORD),
            (NAM_EXEC_EMAIL,    "NAM Oshun",     NAM_EXEC_DEFAULT_PASSWORD),
        ] if _seat[0]
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

    # Demote any account that previously used a fabricated/legacy exec email so
    # a removed seat does not leave a dormant god-mode account behind.
    for _legacy_email in LEGACY_EXEC_EMAILS:
        try:
            _legacy = await db.users.find_one({"email": _legacy_email})
            if _legacy and _legacy.get("role") == "executive_admin":
                await db.users.update_one(
                    {"email": _legacy_email},
                    {"$set": {"role": "admin", "is_active": False},
                     "$unset": {"login_locked_until": "", "login_failed_attempts": ""}},
                )
                logger.warning(
                    "STARTUP: demoted legacy/fabricated exec email %s to admin (inactive)",
                    _legacy_email,
                )
        except Exception as _le:
            logger.warning("STARTUP: legacy exec demotion failed for %s: %s", _legacy_email, _le)

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
                    _seat for _seat in [
                        (EXEC_ADMIN_EMAIL,  "Delon Oliver",  EXEC_DEFAULT_PASSWORD),
                        (BACKUP_EXEC_EMAIL, "Delon Oliver",  BACKUP_EXEC_DEFAULT_PASSWORD),
                        (NAM_EXEC_EMAIL,    "NAM Oshun",     NAM_EXEC_DEFAULT_PASSWORD),
                    ] if _seat[0]
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

    # ── Key vault — self-healing encryption secret for keys at rest ─────────
    # env var → MongoDB-persisted (auto-generated on first boot) → ephemeral.
    # Must run BEFORE provider-key/BYOK loading so decryption uses the same
    # cipher that encrypted them.
    try:
        import keyvault as _keyvault
        await _keyvault.init(db)
        logger.info("STARTUP: Key vault ready (source=%s).", _keyvault.source())
    except Exception as _kv_err:
        logger.warning("STARTUP: Key vault init failed (non-fatal): %s", _kv_err)
    # Wire NAM persistence (Hybrid NAM Leadership Intelligence)
    try:
        from ai.hybrid_nam import persistence as _nam_persistence
        _nam_persistence.init_db(db)
        logger.info("STARTUP: NAM persistence wired to MongoDB.")
    except Exception as _nam_persist_err:
        logger.warning("STARTUP: NAM persistence not wired (in-memory mode): %s", _nam_persist_err)
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

    # ── Member projects — indexes for the customer project workspace ──────
    try:
        from routers import member_projects as _mp_mod
        await _mp_mod.ensure_indexes(db)
        logger.info("STARTUP: member project indexes ensured")
    except Exception as _mp_e:
        logger.warning("STARTUP: member project indexes failed (non-fatal): %s", _mp_e)

    # ── Promo codes — seed the platform's default codes idempotently ──────
    try:
        from routers import promo_codes as _promo_mod
        await _promo_mod.seed_default_promos()
    except Exception as _e:
        logger.warning("STARTUP: promo code seeding failed (non-fatal): %s", _e)

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
        await seed_starter_library()
    except Exception as _e:
        logger.warning("STARTUP: seed_starter_library failed (non-fatal): %s", _e)

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

    # ── Load shared site-support BYOK keys into the LLM gateway ──────────────
    # Site Support team members share their free BYOK key with the platform:
    # the gateway uses the pool as a free tier when every provider fails.
    try:
        from ai.llm_gateway import reload_shared_byok as _reload_shared
        _ns = await _reload_shared(db)
        if _ns:
            logger.info("STARTUP: Loaded %d shared site-support BYOK provider(s) into LLM gateway.", _ns)
    except Exception as _sb_err:
        logger.warning("STARTUP: shared site-support BYOK reload failed (non-fatal): %s", _sb_err)

    # ── Source human controls — the executive's master sliders ──────────────
    try:
        from ai.source_protocol import load_controls as _load_source_controls
        _cfg = await _load_source_controls(db)
        logger.info("STARTUP: Source controls loaded (warmth=%s directness=%s depth=%s restore=%s plain=%s)",
                    _cfg.get("warmth"), _cfg.get("directness"), _cfg.get("depth"),
                    _cfg.get("restore_focus"), _cfg.get("plain_language"))
    except Exception as _sc_err:
        logger.warning("STARTUP: Source controls load failed (non-fatal): %s", _sc_err)

    # ── Team monitor — autonomous provider health loop ────────────────────────
    try:
        from ai.team_monitor import run_monitor_loop as _run_monitor, bind as _bind_monitor
        _bind_monitor(db, notify)
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

    # If the exec break-glass secret is unset, /api/auth/exec-unlock returns
    # 404 and "exec reset" is impossible from the UI. Make that state visible
    # at boot so the operator knows the recovery lever is off.
    if not os.environ.get("EXEC_RESET_SECRET"):
        logger.warning(
            "EXEC_RESET_SECRET is not set — /api/auth/exec-unlock break-glass "
            "reset is DISABLED (returns 404). Set EXEC_RESET_SECRET in Railway "
            "variables to enable executive account recovery."
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



# --- Exec router (extracted to routers/exec.py) ---
from routers import exec as _exec_mod
_exec_mod.bind(db, current_user, check_rate)
api_router.include_router(_exec_mod.router)
# Re-export pipeline models — /exec/pipeline/* endpoints stayed in server.py



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
from routers.ops import run_escalation_check
_commerce_mod.bind(db, current_user, audit, run_escalation_check, run_engagement_check, _discount_manager)
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

# --- Feature Control Center (canonical feature registry + admin API) ---
from routers import features as _features_mod
_features_mod.bind(db, current_user)
api_router.include_router(_features_mod.router)

# --- Admin dashboard router (extracted to routers/admin.py) ---
from routers import admin as _admin_mod
_admin_mod.bind(db, current_user, audit, notify)
api_router.include_router(_admin_mod.router)
# Re-export helpers other server.py code / tests reference.
cohort_summary = _admin_mod.cohort_summary

# --- Chat/assistant router (extracted to routers/chat.py) ---
from routers import chat as _chat_mod
_chat_mod.bind(db, current_user, check_rate)
api_router.include_router(_chat_mod.router)

# --- Misc services router (extracted to routers/misc.py) ---
from routers import misc as _misc_mod
_misc_mod.bind(db, current_user, JWT_SECRET, JWT_ALGO, _send_via_gmail, _send_via_resend)
api_router.include_router(_misc_mod.router)

# --- Creator Lounge router (extracted to routers/creator_lounge.py) ---
from routers import creator_lounge as _creator_lounge_mod
_creator_lounge_mod.bind(db, current_user, audit, notify)
api_router.include_router(_creator_lounge_mod.router)

# --- Band router (extracted to routers/band.py) ---
from routers import band as _band_mod
_band_mod.bind(db, current_user, audit, notify)
api_router.include_router(_band_mod.router)

# --- Revenue exec overview router (extracted to routers/revenue_exec.py) ---
from routers import revenue_exec as _revenue_exec_mod
_revenue_exec_mod.bind(db, current_user)
api_router.include_router(_revenue_exec_mod.router)

# --- Jamil router (extracted to routers/jamil.py) ---
from routers import jamil as _jamil_mod
_jamil_mod.bind(db, current_user)
api_router.include_router(_jamil_mod.router)

# --- My Position router (extracted to routers/position.py) ---
from routers import position as _position_mod
_position_mod.bind(db, current_user, audit)
api_router.include_router(_position_mod.router)

# --- Projects router (extracted to routers/projects.py) ---
from routers import projects as _projects_mod
_projects_mod.bind(db, current_user, audit)
api_router.include_router(_projects_mod.router)

# --- Media store router (extracted to routers/media.py) ---
from routers import media as _media_mod
_media_mod.bind(db, current_user, audit)
api_router.include_router(_media_mod.router)

# --- Missing Kameron router (extracted to routers/missing.py) ---
from routers import missing as _missing_mod
_missing_mod.bind(db, current_user)
api_router.include_router(_missing_mod.router)
# --- Site Guide + site-wide search router (routers/site_guide.py) ---
from routers import site_guide as _site_guide_mod
_site_guide_mod.bind(db, current_user, check_rate)
api_router.include_router(_site_guide_mod.router)
# --- AAWAB — Agent Wellness & Certification Bureau (routers/aawab.py) ---
from routers import aawab as _aawab_mod
_aawab_mod.bind(db, current_user, audit, check_rate, JWT_SECRET)
api_router.include_router(_aawab_mod.router)
# --- AI Business Office (routers/abo.py) — revenue engine command center ---
from routers import abo as _abo_mod
_abo_mod.bind(db, current_user, audit, check_rate)
api_router.include_router(_abo_mod.router)




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
    from routers.playlist import router as playlist_router, bind as _playlist_bind
    _playlist_bind(db, current_user)
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


# --- Payments router (extracted to routers/payments.py) ---
from routers import payments as _payments_mod
_payments_mod.bind(db, audit, notify, current_user)
api_router.include_router(_payments_mod.router)

# --- Promo codes (tier grants at signup; admin CRUD) ---
from routers import promo_codes as _promo_mod
_promo_mod.bind(db, current_user, audit)
api_router.include_router(_promo_mod.router)

# --- Sponsor a Scholarship (routers/scholarships.py) ---
from routers import scholarships as _scholarships_mod
_scholarships_mod.bind(db, audit, notify, current_user, check_rate)
api_router.include_router(_scholarships_mod.router)

# --- Executive Command Center (routers/exec_command.py) ---
from routers import exec_command as _exec_command_mod
_exec_command_mod.bind(db, current_user)
api_router.include_router(_exec_command_mod.router)

# ---- Unified Access Control Gateway - centralized enforcement + exec dashboard ----
# Single module (backend/security/access_control) bundling the 7-role RBAC
# registry, the hard gatekeeper middleware, and the Tier-3 Executive dashboard.
from security.access_control import AccessGateway, CONTROL_REGISTRY
from security.access_control.audit import DenialAuditBuffer
from security.access_control.dashboard import router as access_control_router, bind as bind_access_control

# Encrypted, write-only denial audit buffer (compliance trail). Set
# AUDIT_ENCRYPTION_KEY to a Fernet key (see security/access_control/audit.py)
# to enable at-rest encryption; without it records are stored plaintext and
# flagged as such at startup.
denial_buffer = DenialAuditBuffer()
denial_buffer.bind(db, encryption_key=os.environ.get("AUDIT_ENCRYPTION_KEY"))

access_gateway = AccessGateway()
access_gateway.bind(db, audit, current_user, denial_buffer=denial_buffer)
bind_access_control(access_gateway)
api_router.include_router(access_control_router)
logger.info("Access Control Gateway + Executive dashboard registered (%d controls)", len(CONTROL_REGISTRY))
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

# --- Competition router (The Arena) ---
from routers import provider_gateway as _provider_gateway_mod
_provider_gateway_mod.bind(db, current_user, audit)
api_router.include_router(_provider_gateway_mod.router)

from routers import competition as _competition_mod
_competition_mod.bind(db, current_user, audit, assert_role, xp_level)
api_router.include_router(_competition_mod.router)

# --- Cross-Domain AI Team Bridge router ---
from routers import bridge as _bridge_mod
_bridge_mod.bind(db, current_user, audit, assert_role, xp_level)
api_router.include_router(_bridge_mod.router)

# --- WAI Handbooks router (public static handbook docs) ---
from routers import handbooks as _handbooks_mod
_handbooks_mod.bind(current_user)
api_router.include_router(_handbooks_mod.router)

# --- $3 BYOK (Bring Your Own Key) router ---
from routers import byok as _byok_mod
_byok_mod.bind(db, current_user, audit, assert_role)
api_router.include_router(_byok_mod.router)





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

# ── Security headers middleware ───────────────────────────────────────────
@app.middleware("http")
async def _security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


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


# ---- Hard Access Control middleware: gate the ENTIRE registered control surface ----
# Wraps after every route is registered so the gate sees the full surface.
# Any request to a monitored control route runs the RBAC tier check BEFORE the
# handler; insufficient clearance -> 403 + audit_log entry (action=access_denied).
app = access_gateway.wrap(app)
logger.info("Access Control middleware wrapping app - %d controls monitored", len(CONTROL_REGISTRY))

# ---- NAM API Routes (Hybrid NAM Leadership Intelligence) ----
try:
    from routers.nam import router as nam_router
    app.include_router(nam_router)
    logger.info("Hybrid NAM API routes registered at /api/nam")
except Exception as _nam_err:
    logger.warning("Hybrid NAM routes failed to load: %s", _nam_err)

# ---- Vonns Saga API Routes (tracks, images, videos) ----
try:
    from routers import saga as _saga_mod
    _saga_mod.bind(db, current_user, audit)
    app.include_router(_saga_mod.router)
    logger.info("Vonns Saga API routes registered at /api/saga")
except Exception as _saga_err:
    logger.warning("Saga routes failed to load: %s", _saga_err)



# ---- Executive Pipeline Routes (unified workflow suite) ----
try:
    from routers import executive_pipeline as _ep_mod
    _ep_mod.bind(db, current_user, audit)
    app.include_router(_ep_mod.router)
    logger.info("Executive Pipeline routes registered at /api/executive")
except Exception as _ep_err:
    logger.warning("Executive Pipeline routes failed to load: %s", _ep_err)

# ---- Executive Tools (web search, email, fetch, knowledge) ----
try:
    from routers import exec_tools as _et_mod
    _et_mod.bind(db, current_user, audit)
    app.include_router(_et_mod.router)
    logger.info("Executive Tools routes registered at /api/exec/tools")
except Exception as _et_err:
    logger.warning("Executive Tools routes failed to load: %s", _et_err)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
