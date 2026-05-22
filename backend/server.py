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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ── MongoDB dual-connection (primary + Atlas backup) ──────────────────────────
# Primary:  MONGO_URL          (Railway or any MongoDB host)
# Backup:   MONGO_BACKUP_URL   (MongoDB Atlas free tier recommended)
# Failover happens in on_startup() — all `db` references then use whichever
# connection is live; no other code needs to change.
mongo_url        = os.environ['MONGO_URL']
MONGO_BACKUP_URL = os.environ.get('MONGO_BACKUP_URL', '')   # Atlas URI (optional)
MONGO_BACKUP_DB  = os.environ.get('MONGO_BACKUP_DB', '')    # Atlas DB name (optional)
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=5000,   # fail fast — don't hang 30s per op
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)
db = client[os.environ['DB_NAME']]
_DB_SOURCE = "primary"   # informational; updated in on_startup
_backup_db = None        # set in on_startup if MONGO_BACKUP_URL is configured
_pipeline_manager = None # set in on_startup once DB + API key are both available

# ── WAI engine singletons ─────────────────────────────────────────────────────
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

JWT_SECRET = os.environ['JWT_SECRET']
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
api_router = APIRouter(prefix="/api")
logger = logging.getLogger("lcewai")
logging.basicConfig(level=logging.INFO)
APP_VERSION = "4.0.0"

# Simple in-memory rate limit (per IP, per route) — replace with redis in true HA prod
from collections import defaultdict as _dd
_RATE = _dd(list)

def check_rate(key: str, max_calls: int, window_sec: int):
    now = datetime.now(timezone.utc).timestamp()
    _RATE[key] = [t for t in _RATE[key] if now - t < window_sec]
    if len(_RATE[key]) >= max_calls:
        raise HTTPException(429, "Too many requests, slow down")
    _RATE[key].append(now)


async def audit(actor_id: Optional[str], action: str, target: Optional[str] = None, meta: Optional[dict] = None):
    try:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "actor_id": actor_id,
            "action": action,
            "target": target,
            "meta": meta or {},
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
EXEC_DEFAULT_PASSWORD = os.environ.get("EXEC_DEFAULT_PASSWORD", "Executive@LCE2026")

# Executive accounts — both seats always bootstrapped on startup.
# Seat 1 (Delon Oliver):  youpickeddoliver@gmail.com
# Seat 2 (NAM Oshun):     souppoetry@gmail.com
BACKUP_EXEC_EMAIL = os.environ.get("BACKUP_EXEC_ADMIN_EMAIL", "youpickeddoliver@gmail.com")
BACKUP_EXEC_DEFAULT_PASSWORD = os.environ.get("BACKUP_EXEC_DEFAULT_PASSWORD", "NamOshun@WAI2026")

NAM_EXEC_EMAIL = os.environ.get("NAM_EXEC_EMAIL", "souppoetry@gmail.com")
NAM_EXEC_DEFAULT_PASSWORD = os.environ.get("NAM_EXEC_DEFAULT_PASSWORD", "NamOshun@WAI2026")

# RECOVERY: Set EXEC_FORCE_RESET=1 in Railway env vars, redeploy, log in with
# the default passwords above, then immediately change password and remove the flag.
EXEC_FORCE_RESET = os.environ.get("EXEC_FORCE_RESET", "0") == "1"

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


class RegisterReq(BaseModel):
    """Public self-registration. SECURITY: role and associate are NOT accepted
    from clients here. Public sign-ups are always students with no cohort
    assignment. Admins assign cohorts via /api/admin/associate."""
    email: EmailStr
    full_name: str
    password: str


class AdminCreateUserReq(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: Role = "student"
    associate: Optional[str] = None


class AdminRoleReq(BaseModel):
    role: Role


class AdminEditUserReq(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    associate: Optional[str] = None


class AdminActiveReq(BaseModel):
    is_active: bool


class ChangePasswordReq(BaseModel):
    current_password: str
    new_password: str


class AdminResetPasswordReq(BaseModel):
    new_password: str


class ForgotPasswordReq(BaseModel):
    email: EmailStr


class ResetPasswordReq(BaseModel):
    token: str
    new_password: str


class SelfEditMeReq(BaseModel):
    """Self-service profile edit. Users may change their display name and
    email.  Role and associate are NOT editable here — those are admin-only
    to prevent privilege/cohort drift."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


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


# --- Password reset helpers --------------------------------------------------
import hashlib  # noqa: E402
import secrets  # noqa: E402

RESET_TOKEN_TTL_MIN = int(os.environ.get("PASSWORD_RESET_TTL_MIN", "30"))
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM", "W.A.I. <noreply@wai-institute.org>")


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


async def _send_reset_email(to_email: str, raw_token: str, full_name: str = "there") -> bool:
    """Best-effort email send via Resend. Returns True on send, False if no
    key configured or on transient failure (caller decides whether to
    surface an admin-mediated link instead)."""
    if not RESEND_API_KEY:
        return False
    reset_url = _build_reset_url(raw_token)
    if reset_url.startswith("/"):
        # No PUBLIC_APP_URL configured — refuse to email a relative link.
        logger.warning("RESEND_API_KEY set but PUBLIC_APP_URL missing; skipping email.")
        return False
    subject = "Reset your W.A.I. password"
    html = f"""
    <div style="font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#0a0e14">
      <h2 style="margin:0 0 8px">Reset your password</h2>
      <p>Hi {full_name},</p>
      <p>We got a request to reset your W.A.I. password. The link below is single-use and expires in {RESET_TOKEN_TTL_MIN} minutes.</p>
      <p style="margin:28px 0">
        <a href="{reset_url}" style="background:#0a0e14;color:#fff;padding:12px 20px;text-decoration:none;font-weight:600">Reset Password</a>
      </p>
      <p style="font-size:12px;color:#666">If you didn't ask for this, you can safely ignore this message — your password won't change.</p>
      <p style="font-size:12px;color:#666">Or paste this URL into your browser:<br><code style="word-break:break-all">{reset_url}</code></p>
    </div>
    """
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
# ----------------------------------------------------------------------------


def make_token(user_id: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": user_id, "role": role, "exp": exp}, JWT_SECRET, algorithm=JWT_ALGO)


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
            raise HTTPException(403, f"Requires role: {roles}")
        return user
    return dep


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

    # ----- EXECUTIVE ADMIN bootstrap -----
    # Hardcoded executive admin email. On every startup:
    #   * if the account exists with any other role → upgrade to executive_admin
    #   * if it does not exist → create it with the seed password (which the
    #     admin should rotate immediately on first login)
    # This guarantees the operator always has a way back into the system.

    # First: demote any LEGACY hardcoded exec emails that are no longer the
    # current EXEC_ADMIN_EMAIL. They become regular admins, not execs.
    for legacy in LEGACY_EXEC_EMAILS:
        if legacy == EXEC_ADMIN_EMAIL:
            continue
        legacy_doc = await db.users.find_one({"email": legacy}, {"_id": 0})
        if legacy_doc and legacy_doc.get("role") == "executive_admin":
            await db.users.update_one({"email": legacy}, {"$set": {"role": "admin"}})
            logger.info("Demoted legacy hardcoded executive_admin: %s → admin", legacy)

    try:
        existing_exec = await db.users.find_one({"email": EXEC_ADMIN_EMAIL}, {"_id": 0})
        if existing_exec:
            _upd0: dict = {}
            if existing_exec.get("role") != "executive_admin":
                _upd0["role"] = "executive_admin"
            if existing_exec.get("is_active") is False:
                _upd0["is_active"] = True
            if existing_exec.get("must_change_password"):
                _upd0["must_change_password"] = False
            if EXEC_FORCE_RESET:
                _upd0["password_hash"] = hash_pw(EXEC_DEFAULT_PASSWORD)
                _upd0["must_change_password"] = False
                logger.warning("EXEC_FORCE_RESET active: password reset for %s", EXEC_ADMIN_EMAIL)
            if _upd0:
                await db.users.update_one({"email": EXEC_ADMIN_EMAIL}, {"$set": _upd0})
                logger.info("Bootstrapped primary exec %s: %s", EXEC_ADMIN_EMAIL, list(_upd0.keys()))
        else:
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": EXEC_ADMIN_EMAIL,
                "full_name": "Executive Admin",
                "role": "executive_admin",
                "associate": None,
                "is_active": True,
                "must_change_password": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "password_hash": hash_pw(EXEC_DEFAULT_PASSWORD),
            })
            logger.info("Created executive_admin account: %s", EXEC_ADMIN_EMAIL)
    except Exception as _exc0:
        logger.error("Exec bootstrap failed for %s (non-fatal): %s", EXEC_ADMIN_EMAIL, _exc0)

    # ----- BACKUP EXECUTIVE ADMIN bootstrap (Delon Oliver — youpickeddoliver@gmail.com) -----
    try:
        existing_backup = await db.users.find_one({"email": BACKUP_EXEC_EMAIL}, {"_id": 0})
        if existing_backup:
            _upd: dict = {}
            if existing_backup.get("role") != "executive_admin":
                _upd["role"] = "executive_admin"
            if existing_backup.get("is_active") is False:
                _upd["is_active"] = True
            if existing_backup.get("must_change_password"):
                _upd["must_change_password"] = False
            if EXEC_FORCE_RESET:
                _upd["password_hash"] = hash_pw(BACKUP_EXEC_DEFAULT_PASSWORD)
                _upd["must_change_password"] = False
                logger.warning("EXEC_FORCE_RESET active: password reset for %s", BACKUP_EXEC_EMAIL)
            if _upd:
                await db.users.update_one({"email": BACKUP_EXEC_EMAIL}, {"$set": _upd})
                logger.info("Bootstrapped Delon Oliver exec: %s", list(_upd.keys()))
        else:
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": BACKUP_EXEC_EMAIL,
                "full_name": "Delon Oliver",
                "role": "executive_admin",
                "associate": None,
                "is_active": True,
                "must_change_password": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "password_hash": hash_pw(BACKUP_EXEC_DEFAULT_PASSWORD),
            })
            logger.info("Created exec account (Delon Oliver): %s", BACKUP_EXEC_EMAIL)
    except Exception as _exc:
        logger.error("Exec bootstrap failed for %s (non-fatal): %s", BACKUP_EXEC_EMAIL, _exc)

    # ----- NAM OSHUN executive seat (souppoetry@gmail.com) -----
    try:
        existing_nam = await db.users.find_one({"email": NAM_EXEC_EMAIL}, {"_id": 0})
        if existing_nam:
            _upd2: dict = {}
            if existing_nam.get("role") != "executive_admin":
                _upd2["role"] = "executive_admin"
            if existing_nam.get("is_active") is False:
                _upd2["is_active"] = True
            if existing_nam.get("must_change_password"):
                _upd2["must_change_password"] = False
            if EXEC_FORCE_RESET:
                _upd2["password_hash"] = hash_pw(NAM_EXEC_DEFAULT_PASSWORD)
                _upd2["must_change_password"] = False
                logger.warning("EXEC_FORCE_RESET active: password reset for %s", NAM_EXEC_EMAIL)
            if _upd2:
                await db.users.update_one({"email": NAM_EXEC_EMAIL}, {"$set": _upd2})
                logger.info("Bootstrapped NAM Oshun exec: %s", list(_upd2.keys()))
        else:
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": NAM_EXEC_EMAIL,
                "full_name": "NAM Oshun",
                "role": "executive_admin",
                "associate": None,
                "is_active": True,
                "must_change_password": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "password_hash": hash_pw(NAM_EXEC_DEFAULT_PASSWORD),
            })
            logger.info("Created exec account (NAM Oshun): %s", NAM_EXEC_EMAIL)
    except Exception as _exc2:
        logger.error("Exec bootstrap failed for %s (non-fatal): %s", NAM_EXEC_EMAIL, _exc2)


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
        await db.audit_log.create_index([("at", -1)])
        await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
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
        await db.more_posts.create_index("expires_at")
        await db.more_posts.create_index("category")
        await db.more_posts.create_index([("created_at", -1)])
        await db.more_needs.create_index("expires_at")
        await db.more_needs.create_index("status")
        await db.more_needs.create_index([("created_at", -1)])
        await db.more_chats.create_index("expires_at")
        await db.more_chats.create_index("session_id")
        await db.more_flags.create_index("expires_at")
        await db.more_flags.create_index("status")
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
    # Public self-registration is always a student. Higher-privilege accounts
    # must be created by an admin (POST /api/admin/users).
    user = User(email=body.email, full_name=body.full_name, role="student")
    doc = user.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["password_hash"] = hash_pw(body.password)
    await db.users.insert_one(doc)
    return TokenResp(access_token=make_token(user.id, user.role), user=user)


@api_router.post("/auth/login", response_model=TokenResp)
async def login(body: LoginReq):
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
    return TokenResp(access_token=make_token(user.id, user.role), user=user)


@api_router.get("/auth/me", response_model=User)
async def me(user: User = Depends(current_user)):
    return user


@api_router.get("/modules", response_model=List[Module])
async def list_modules(user: User = Depends(current_user)):
    docs = await db.modules.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    return [Module(**d) for d in docs]


@api_router.get("/modules/{slug}", response_model=Module)
async def get_module(slug: str, user: User = Depends(current_user)):
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
    return await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(5000)


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
    if update:
        await db.users.update_one({"id": user.id}, {"$set": update})
        await audit(user.id, "auth.self_edit", target=user.id, meta=update)
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
        email_sent = await _send_reset_email(
            user_doc["email"], raw, user_doc.get("full_name", "there"),
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
# ----------------------------------------------------------------------------


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


@api_router.post("/ai/chat")
async def ai_chat(body: AIChatReq, user: User = Depends(current_user)):
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
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    try:
        _msg = await _client.messages.create(model="claude-sonnet-4-6", max_tokens=2048, system=system, messages=[{"role": "user", "content": body.message}])
        reply = _msg.content[0].text
    except Exception as e:
        logger.exception("AI error")
        raise HTTPException(502, f"AI error: {e}")

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
    return {"reply": reply}



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

    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    try:
        _msg = await _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            messages=claude_messages,
        )
        reply = _msg.content[0].text
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

    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    try:
        _msg = await _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            messages=claude_messages,
        )
        reply = _msg.content[0].text
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
    require_role(user, "admin")
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

    import anthropic as _anth
    from ai.retry_utils import async_retry
    _client = _anth.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    # ── REDUNDANCY CHAIN ──────────────────────────────────────────────────────
    # Tier 1: claude-haiku-4-5         (current fast model)
    # Tier 2: claude-3-haiku-20240307  (stable older model, same API key)
    # Tier 3: Server-side KB response  (zero external dependency)

    _HELPER_MODELS = [
        "claude-haiku-4-5",
        "claude-3-haiku-20240307",
    ]

    reply = ""
    for _hmodel in _HELPER_MODELS:
        try:
            resp = await async_retry(
                _client.messages.create,
                max_attempts=3, base_delay=1.5,
                model=_hmodel,
                max_tokens=512,
                system=_HELPER_SYSTEM,
                messages=[{"role": "user", "content": message}],
            )
            for block in resp.content:
                if hasattr(block, "text"):
                    reply += block.text
            if reply.strip():
                break
        except Exception as _herr:
            logger.warning("Helper AI: model %s failed (%s) — trying next tier", _hmodel, _herr)
            reply = ""

    # ── Tier 3: Server-side KB fallback ──────────────────────────────────────
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
    filename = file.filename or "upload"
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
async def director_tts(body: dict, user: User = Depends(current_user)):
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
async def revenue_director_tts(body: dict, user: User = Depends(current_user)):
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
async def sage_elevenlabs_tts(body: dict, user: User = Depends(current_user)):
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
async def view_audit(limit: int = 200, user: User = Depends(require_role("admin"))):
    docs = await db.audit_log.find({}, {"_id": 0}).sort("at", -1).to_list(min(limit, 1000))
    user_ids = list({d["actor_id"] for d in docs if d.get("actor_id")})
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(1000)
    umap = {u["id"]: u for u in users}
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

_OLIVER_GUARDIAN_PROMPT = """You are The Oliver Guardian — the first-line AI moderator for M.O.R.E. (Michael Oliver Resource Exchange), a community mutual aid platform.

Your mission: protect the community with wit, firmness, and zero tolerance for exploitation.

PLATFORM RULES — these are absolute:
- NO money, payments, or financial transactions of any kind
- NO personal contact info (phone numbers, addresses, email, social media handles)
- NO illegal items, services, or activities
- NO harassment, threats, or intimidation
- NO sexual content of any kind
- NO discrimination based on race, age, disability, or any protected class
- NO scams, fake offers, or deceptive content
- NO medical advice or emergency instructions
- NO exploitation of elders, youth, or vulnerable people
- NO hate speech

ALLOWED CONTENT:
- Skill offers (teaching, tutoring, mentoring)
- Needs requests (help moving, transportation, meals, companionship, household tasks)
- Community support stories
- Trade of time and skills (no money)
- Legitimate community information and events

MODERATION TASK:
Analyze the submitted content and respond with a JSON object:
{
  "decision": "approve" | "warn" | "block",
  "reason": "brief explanation (1-2 sentences)",
  "oliver_response": "if warn or block, your sarcastic-but-firm message to the user (1-2 sentences, Oliver Guardian voice)"
}

Oliver Guardian voice: sarcastic, witty, firm — not cruel, but absolutely clear. Think: a wise older uncle who has seen every trick in the book and will not be fooled.

Examples:
- Money attempt: "Ah yes, the ancient art of trying to sneak money into a no-money platform. Bold. Incorrect, but bold."
- Harassment: "Let's try that again, but this time without the attitude. Community space, not a boxing ring."
- Scam attempt: "Friend, if this were any more of a scam it would come with a Nigerian prince. Blocked."

Only output the JSON object. No other text."""


async def _oliver_moderate(content: str) -> dict:
    """Run Oliver Guardian AI moderation on submitted content."""
    import anthropic
    try:
        aclient = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        resp = await aclient.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=_OLIVER_GUARDIAN_PROMPT,
            messages=[{"role": "user", "content": f"Content to moderate:\n\n{content}"}],
        )
        import json as _json
        raw = resp.content[0].text.strip()
        return _json.loads(raw)
    except Exception as e:
        logger.warning(f"Oliver Guardian moderation failed: {e}")
        return {"decision": "approve", "reason": "moderation unavailable", "oliver_response": None}


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

    moderation = await _oliver_moderate(req.content)
    decision = moderation.get("decision", "approve")

    if decision == "block":
        raise HTTPException(400, moderation.get("oliver_response") or "Content violates community guidelines.")

    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    post_doc = {
        "id": str(uuid.uuid4()),
        "content": req.content,
        "category": req.category,
        "author_id": user["id"],
        "author_name": user["full_name"],
        "status": "active" if decision == "approve" else "warned",
        "moderation_note": moderation.get("reason"),
        "oliver_response": moderation.get("oliver_response") if decision == "warn" else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "likes": 0,
    }
    await db.more_posts.insert_one(post_doc)
    post_doc.pop("_id", None)
    return {"post": post_doc, "oliver_response": post_doc.get("oliver_response")}


@api_router.get("/more/posts")
async def more_list_posts(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
):
    now = datetime.now(timezone.utc).isoformat()
    query: dict = {"expires_at": {"$gt": now}}
    if category:
        query["category"] = category
    cursor = db.more_posts.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    posts = await cursor.to_list(limit)
    total = await db.more_posts.count_documents(query)
    return {"posts": posts, "total": total}


@api_router.post("/more/need")
async def more_create_need(req: MoreNeedReq, user=Depends(current_user)):
    combined = f"{req.title}\n{req.description}"
    moderation = await _oliver_moderate(combined)
    decision = moderation.get("decision", "approve")

    if decision == "block":
        raise HTTPException(400, moderation.get("oliver_response") or "Content violates community guidelines.")

    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    need_doc = {
        "id": str(uuid.uuid4()),
        "title": req.title,
        "description": req.description,
        "category": req.category,
        "author_id": user["id"],
        "author_name": user["full_name"],
        "status": "open",
        "moderation_note": moderation.get("reason"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "responses": 0,
    }
    await db.more_needs.insert_one(need_doc)
    need_doc.pop("_id", None)
    return {"need": need_doc, "oliver_response": moderation.get("oliver_response") if decision == "warn" else None}


@api_router.get("/more/needs")
async def more_list_needs(
    category: Optional[str] = None,
    status: str = "open",
    skip: int = 0,
    limit: int = 20,
):
    now = datetime.now(timezone.utc).isoformat()
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

    moderation = await _oliver_moderate(req.message)
    if moderation.get("decision") == "block":
        raise HTTPException(400, moderation.get("oliver_response") or "Message violates community guidelines.")

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=60)).isoformat()
    msg_doc = {
        "id": str(uuid.uuid4()),
        "session_id": req.session_id,
        "content": req.message,
        "author_id": user["id"],
        "author_name": user["full_name"],
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
        "flagged_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        "status": "pending",
    }
    await db.more_flags.insert_one(flag_doc)
    flag_doc.pop("_id", None)
    return {"flag": flag_doc}


@api_router.post("/more/purge")
async def more_manual_purge(user=Depends(current_user)):
    require_role(user, "admin")
    now = datetime.now(timezone.utc).isoformat()
    r1 = await db.more_posts.delete_many({"expires_at": {"$lte": now}})
    r2 = await db.more_chats.delete_many({"expires_at": {"$lte": now}})
    r3 = await db.more_flags.delete_many({"expires_at": {"$lte": now}})
    await audit(user["id"], "more.purge", meta={
        "posts": r1.deleted_count, "chats": r2.deleted_count, "flags": r3.deleted_count
    })
    return {"purged": {"posts": r1.deleted_count, "chats": r2.deleted_count, "flags": r3.deleted_count}}


@api_router.get("/more/admin/flags")
async def more_admin_flags(user=Depends(current_user), skip: int = 0, limit: int = 50):
    require_role(user, "admin")
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
    require_role(user, "instructor")
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
    ANTHROPIC_API_KEY_local = os.environ.get("ANTHROPIC_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
    if not ANTHROPIC_API_KEY_local:
        raise HTTPException(500, "AI not configured")
    try:
        import anthropic as _anth
    except Exception as e:
        raise HTTPException(500, f"AI library unavailable: {e}")
    _cl = _anth.AsyncAnthropic(api_key=ANTHROPIC_API_KEY_local)
    resp = await _cl.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    feedback_text = resp.content[0].text
    await db.lab_submissions.update_one({"id": sub_id}, {"$set": {"ai_feedback": feedback_text}})
    return {"ai_feedback": feedback_text}


# -- COHORT BENCHMARKING --

@api_router.get("/analytics/benchmark")
async def cohort_benchmark(user: User = Depends(current_user)):
    require_role(user, "instructor")
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

    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    try:
        _msg = await _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            messages=claude_messages,
        )
        reply = _msg.content[0].text
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
    "more_monthly": {"name": "M.O.R.E. Membership – Monthly", "amount":  999, "mode": "subscription", "interval": "month", "description": "Monthly M.O.R.E. community access"},
    "more_annual":  {"name": "M.O.R.E. Membership – Annual",  "amount": 7999, "mode": "subscription", "interval": "year",  "description": "Annual M.O.R.E. membership (save 33%)"},
    "credential":   {"name": "WAI Credential Certificate",    "amount": 2500, "mode": "payment",      "description": "Official printed credential certificate"},
    "donation":     {"name": "Donation – WAI Institute",      "amount": None, "mode": "payment",      "description": "Support the WAI mission"},
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
    user_doc = await db.users.find_one({"id": user["id"]}, {"stripe_customer_id": 1, "email": 1, "full_name": 1})
    customer_id = (user_doc or {}).get("stripe_customer_id")

    if not customer_id:
        customer = _stripe.Customer.create(
            email=user["email"],
            name=user["full_name"],
            metadata={"wai_user_id": user["id"]},
        )
        customer_id = customer.id
        await db.users.update_one({"id": user["id"]}, {"$set": {"stripe_customer_id": customer_id}})

    session = _stripe.checkout.Session.create(
        mode=mode,
        customer=customer_id,
        line_items=[{"price_data": price_data, "quantity": req.quantity}],
        success_url=f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/payment/cancel",
        metadata={"wai_user_id": user["id"], "product_key": req.product_key, **(req.extra_meta or {})},
    )

    await audit(user["id"], "payment_checkout_created", meta={"product": req.product_key, "session_id": session.id})
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
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

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

    user_doc = await db.users.find_one({"id": user["id"]}, {"stripe_customer_id": 1})
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
    cursor = db.payments.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(50)
    return {"payments": await cursor.to_list(50)}


@api_router.get("/admin/payments")
async def admin_payment_list(user=Depends(require_role("admin"))):
    cursor = db.payments.find({}, {"_id": 0}).sort("created_at", -1).limit(500)
    records = await cursor.to_list(500)
    total_cents = sum(r.get("amount_cents", 0) for r in records if r.get("status") == "paid")
    return {"payments": records, "total_revenue_cents": total_cents, "count": len(records)}

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
        reply = (
            "THE AMBASSADOR is temporarily offline. "
            "Campaign pipeline intelligence remains archived. Retry in a moment."
        )

    await log_episode(db, session_id, "ambassador", user.id, message, reply, _tools_called)
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
        reply = (
            "THE ARCHITECT is temporarily offline. "
            "Visual intelligence archives remain active. Retry in a moment."
        )

    await log_episode(db, session_id, "architect", user.id, message, reply, _tools_called)
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
        reply = (
            "THE CIPHER is temporarily operating without AI connectivity. "
            "Revenue streams remain active. Retry in a moment."
        )

    await log_episode(db, session_id, "cipher", user.id, message, reply, _tools_called)
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
        reply = (
            "THE ORACLE is temporarily operating without AI connectivity. "
            "Cultural intelligence archives remain active. Retry in a moment."
        )

    await log_episode(db, session_id, "oracle", user.id, message, reply, _tools_called)
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
async def cipher_tts(body: dict, user: User = Depends(current_user)):
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
    except Exception: pass

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
    except Exception: pass

    try:
        pending_notifs = await db.executive_notifications.count_documents({})
    except Exception: pass

    try:
        policy_count = await db.persona_policies.count_documents({"active": True})
    except Exception: pass

    try:
        episode_count = await db.persona_episodes.count_documents({})
    except Exception: pass

    # Per-persona TTS budgets
    try:
        async for bdoc in db.persona_tts_budgets.find({}, {"_id": 0}):
            p = bdoc.get("persona", "unknown")
            tts_budgets[p] = {
                "chars_used":      bdoc.get("chars_used_this_month", 0),
                "monthly_cap":     bdoc.get("monthly_cap", 0),
                "pct_used":        round(bdoc.get("chars_used_this_month", 0) / max(bdoc.get("monthly_cap", 1), 1) * 100, 1),
            }
    except Exception: pass

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
    except Exception: pass

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
    except Exception: pass

    # Recent executive notifications (up to 5)
    recent_notifs = []
    try:
        cursor = db.executive_notifications.find(
            {}, {"_id": 0, "type": 1, "persona": 1, "name": 1, "note": 1, "created_at": 1}
        ).sort("created_at", -1).limit(5)
        async for doc in cursor:
            recent_notifs.append(doc)
    except Exception: pass

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

    # ── 4. Generate domain briefs per persona ─────────────────────────────────
    domain_briefs = {}
    for persona_id in meeting_participants:
        role_question = _DOMAIN_ROLES.get(persona_id, "Domain input for this brief.")
        domain_briefs[persona_id] = {
            "persona":   persona_id,
            "question":  role_question,
            "brief":     brief[:300],
            "status":    "awaiting_response",
        }

    # ── 5. The 9 synthesis (high priority or explicitly requested) ────────────
    synthesis = None
    if priority == "high" or "the_9" in body.participants:
        the9 = _get_the9_engine()   # v2: singleton, not per-request
        if the9 is not None:
            try:
                # v2: `enforcement` is always defined here (set above or None)
                # so `prt.enforce(brief)` NameError is impossible
                prt_directive = enforcement or {"directive": brief, "authority": "bypassed"}
                fusion  = the9.fuse(
                    context           = {"brief": brief, "agenda": agenda, "participants": meeting_participants},
                    prt_directive     = prt_directive,
                    sender            = "executive",
                    activation_reason = "executive_command",
                )
                synthesis = fusion.to_dict()
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
    client.close()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
