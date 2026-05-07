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
import io
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Literal

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from prompts.ancestral_sage_prompt import (
    ANCESTRAL_SAGE_PROMPT,
    ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED,
    RESTRICTED_EDUCATIONAL_FALLBACK,
    compute_sage_prompt_hash,
)
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

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGO = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_HOURS = int(os.environ.get('JWT_EXPIRE_HOURS', '168'))
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI(
    title="W.A.I. Training Platform",
    version="3.0.0",
    description="W.A.I. — Workforce Apprentice Institute API. Hands-on electrical apprenticeship training, labs, credentials, and portfolio.",
    redirect_slashes=False,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
api_router = APIRouter(prefix="/api")
logger = logging.getLogger("lcewai")
logging.basicConfig(level=logging.INFO)
APP_VERSION = "3.0.0"

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

# One-time migration: any email that used to be the hardcoded EXEC_ADMIN_EMAIL
# will be auto-demoted from executive_admin to admin on startup, so switching
# the primary exec doesn't leave a dormant god-mode account behind.
LEGACY_EXEC_EMAILS = {"youpickeddoliver@gmail.com"}


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
    """Public self-registration. SECURITY: role is NOT accepted from clients here.
    Public sign-ups are always created as students. Instructors/admins must be
    created by an existing admin via /api/admin/users."""
    email: EmailStr
    full_name: str
    password: str
    associate: Optional[str] = None


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
    seeds = [
        ("admin@lcewai.org", "LCE-WAI Admin", "admin", None, "Admin@LCE2026"),
        ("instructor@lcewai.org", "Jordan Rivera", "instructor", "Associate-Alpha", "Teach@LCE2026"),
        ("student@lcewai.org", "Alex Carter", "student", "Associate-Alpha", "Learn@LCE2026"),
    ]
    for email, name, role, associate, pw in seeds:
        existing = await db.users.find_one({"email": email}, {"_id": 0})
        if not existing:
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": email,
                "full_name": name,
                "role": role,
                "associate": associate,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "password_hash": hash_pw(pw),
            })
        else:
            # Auto-heal role / is_active drift on the seeded demo accounts.
            # Without this, a manual demotion of e.g. admin@lcewai.org → instructor
            # would persist forever (the original code only ran on first insert).
            # Mirrors the executive_admin bootstrap pattern below.
            update = {}
            if existing.get("role") != role:
                update["role"] = role
            if existing.get("is_active") is False:
                update["is_active"] = True
            if update:
                await db.users.update_one({"email": email}, {"$set": update})
                logger.info("Healed seed-account drift for %s: %s", email, update)

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

    existing_exec = await db.users.find_one({"email": EXEC_ADMIN_EMAIL}, {"_id": 0})
    if existing_exec:
        update = {}
        if existing_exec.get("role") != "executive_admin":
            update["role"] = "executive_admin"
        if existing_exec.get("is_active") is False:
            update["is_active"] = True
        # If the password is still the seed default, require rotation on next
        # login. Uses verify_pw because bcrypt hashes are non-deterministic.
        try:
            if verify_pw(EXEC_DEFAULT_PASSWORD, existing_exec.get("password_hash", "")):
                update["must_change_password"] = True
        except Exception:
            pass
        if update:
            await db.users.update_one({"email": EXEC_ADMIN_EMAIL}, {"$set": update})
            logger.info("Bootstrapped %s: %s", EXEC_ADMIN_EMAIL, update)
    else:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": EXEC_ADMIN_EMAIL,
            "full_name": "Executive Admin",
            "role": "executive_admin",
            "associate": None,
            "is_active": True,
            "must_change_password": True,  # force rotation on first login
            "created_at": datetime.now(timezone.utc).isoformat(),
            "password_hash": hash_pw(EXEC_DEFAULT_PASSWORD),
        })
        logger.info("Created executive_admin account: %s", EXEC_ADMIN_EMAIL)


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


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()
    await seed_modules()
    await seed_users()
    await seed_labs()
    await seed_compliance()
    await seed_sites_inventory()
    # Loud warning if the dev-only token leak is enabled.  The production
    # .env should NEVER set this; it exists only for the preview test suite.
    if os.environ.get("DEV_RETURN_RESET_TOKEN") == "1":
        logger.warning(
            "DEV_RETURN_RESET_TOKEN=1 is set — /api/auth/forgot-password "
            "will return raw reset tokens in the response. THIS IS UNSAFE "
            "FOR PRODUCTION. Remove DEV_RETURN_RESET_TOKEN from .env "
            "before deploying to a public environment."
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
    try:
        await client.admin.command("ping")
        return {"status": "ok", "version": APP_VERSION, "db": "up"}
    except Exception:
        raise HTTPException(503, "db_down")


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
    user = User(email=body.email, full_name=body.full_name, role="student", associate=body.associate)
    doc = user.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["password_hash"] = hash_pw(body.password)
    await db.users.insert_one(doc)
    return TokenResp(access_token=make_token(user.id, user.role), user=user)


@api_router.post("/auth/login", response_model=TokenResp)
async def login(body: LoginReq):
    check_rate(f"login:{body.email}", max_calls=30, window_sec=60)
    doc = await db.users.find_one({"email": body.email}, {"_id": 0})
    if not doc or not verify_pw(body.password, doc["password_hash"]):
        await audit(None, "auth.login.failed", body.email)
        raise HTTPException(401, "Invalid credentials")
    if doc.get("is_active") is False:
        await audit(doc.get("id"), "auth.login.blocked_inactive", body.email)
        raise HTTPException(403, "Your account has been deactivated. Contact your administrator.")
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
    """Any authenticated user can change their own password."""
    if len(body.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    doc = await db.users.find_one({"id": user.id}, {"_id": 0})
    if not doc or not verify_pw(body.current_password, doc["password_hash"]):
        raise HTTPException(401, "Current password is incorrect")
    await db.users.update_one({"id": user.id}, {"$set": {
        "password_hash": hash_pw(body.new_password),
        "must_change_password": False,  # cleared on self-change
    }})
    await audit(user.id, "auth.password_changed")
    return {"ok": True}


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
        "consent_log_id": cid,
        "expires_at": expires.isoformat(),
        "ttl_minutes": ANCESTRAL_SAGE_CONSENT_TTL_MIN,
        "human_review_triggered": bool(body.request_human_review),
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
    can view this — exec admins additionally see the full hashes."""
    ok = _sage_prompt_integrity_ok()
    out = {"ok": ok, "restricted": not ok}
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
    if not EMERGENT_LLM_KEY:
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
        from emergentintegrations.llm.openai import OpenAITextToSpeech
    except Exception as exc:
        raise HTTPException(500, f"TTS library unavailable: {exc}") from exc

    t0 = _t.time()
    try:
        tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
        audio_bytes = await tts.generate_speech(
            text=text, model="tts-1", voice=voice, speed=speed,
        )
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

    if not EMERGENT_LLM_KEY:
        raise HTTPException(500, "AI not configured")
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
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
    chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=session_id, system_message=system).with_model(
        "anthropic", "claude-sonnet-4-5-20250929"
    )
    try:
        reply = await chat.send_message(UserMessage(text=body.message))
    except Exception as e:
        logger.exception("AI error")
        raise HTTPException(502, f"AI error: {e}")

    await db.chat_history.insert_one({
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
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"reply": reply}


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
        # notify the apprentice
        lab = await db.labs.find_one({"slug": sub["lab_slug"]}, {"_id": 0})
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
        })
        awarded.append(cred["key"])
        await notify(user_id, "Credential earned",
                     f"You earned: {cred['name']}",
                     link="/credentials", kind="success")
        await audit(user_id, "credential.earned", target=cred["key"])
    return awarded


@api_router.get("/credentials")
async def list_credentials(user: User = Depends(current_user)):
    return CREDENTIALS


@api_router.get("/credentials/me")
async def my_credentials(user: User = Depends(current_user)):
    # re-run awards so fresh on page load
    await award_credentials(user.id)
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


app.include_router(api_router)
# CORS: when origins is wildcard ("*") browsers reject credentials, so we
# turn off allow_credentials in that case (auth uses Bearer token in Authorization
# header anyway). If a specific origin list is supplied, credentials are allowed.
_cors_origins = [o.strip() for o in os.environ.get('CORS_ORIGINS', '*').split(',') if o.strip()]
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
    client.close()
