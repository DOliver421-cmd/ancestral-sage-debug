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
EXEC_ADMIN_EMAIL = "youpickeddoliver@gmail.com"
EXEC_DEFAULT_PASSWORD = "Executive@LCE2026"

# One-time migration: any email that used to be the hardcoded EXEC_ADMIN_EMAIL
# will be auto-demoted from executive_admin to admin on startup, so switching
# the primary exec doesn't leave a dormant god-mode account behind.
LEGACY_EXEC_EMAILS = {"delon.oliver@lightningcityelectric.com"}


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: Role = "student"
    associate: Optional[str] = None
    is_active: bool = True
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
    mode: Literal["tutor", "scripture", "quiz_gen", "explain", "nec_lookup", "blueprint"] = "tutor"


def hash_pw(p: str) -> str:
    return pwd_ctx.hash(p)


def verify_pw(p: str, h: str) -> bool:
    return pwd_ctx.verify(p, h)


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
        if not await db.users.find_one({"email": email}):
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
        if existing_exec.get("role") != "executive_admin" or existing_exec.get("is_active") is False:
            await db.users.update_one(
                {"email": EXEC_ADMIN_EMAIL},
                {"$set": {"role": "executive_admin", "is_active": True}},
            )
            logger.info("Upgraded %s to executive_admin", EXEC_ADMIN_EMAIL)
    else:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": EXEC_ADMIN_EMAIL,
            "full_name": "Executive Admin",
            "role": "executive_admin",
            "associate": None,
            "is_active": True,
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


async def ensure_indexes():
    """Declare critical indexes. Idempotent; safe to call on every startup."""
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        await db.lab_submissions.create_index([("user_id", 1), ("lab_slug", 1)], unique=True)
        await db.progress.create_index([("user_id", 1), ("module_slug", 1)], unique=True)
        await db.compliance_progress.create_index([("user_id", 1), ("module_slug", 1)], unique=True)
        await db.audit_log.create_index([("at", -1)])
        await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
        await db.user_credentials.create_index([("user_id", 1), ("credential_key", 1)], unique=True)
        await db.attendance.create_index([("user_id", 1), ("date", -1)])
        await db.incidents.create_index([("status", 1), ("created_at", -1)])
        await db.tool_checkouts.create_index([("user_id", 1), ("status", 1)])
        await db.inventory.create_index("sku", unique=True)
        await db.sites.create_index("slug", unique=True)
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
    check_rate(f"login:{body.email}", max_calls=10, window_sec=60)
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
    Only executive_admins may create another executive_admin."""
    if body.role == "executive_admin" and user.role != "executive_admin":
        raise HTTPException(403, "Only executive_admin can create another executive_admin.")
    if await db.users.find_one({"email": body.email}):
        raise HTTPException(400, "Email already registered")
    new_user = User(email=body.email, full_name=body.full_name, role=body.role, associate=body.associate)
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
    await db.users.update_one({"id": uid}, {"$set": {"password_hash": hash_pw(body.new_password)}})
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
    await db.users.update_one({"id": user.id}, {"$set": {"password_hash": hash_pw(body.new_password)}})
    await audit(user.id, "auth.password_changed")
    return {"ok": True}


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
    # Add per-cohort completion counts
    for cohort_name, c in cohorts.items():
        member_ids = await db.users.find({"associate": None if cohort_name == "—" else cohort_name},
                                         {"_id": 0, "id": 1}).to_list(2000)
        ids = [m["id"] for m in member_ids]
        c["completions"] = await db.progress.count_documents({"user_id": {"$in": ids}, "status": "completed"})
    return sorted(cohorts.values(), key=lambda x: -x["members"])


SYSTEM_PROMPTS = {
    "tutor": "You are a patient master electrician and faith-forward mentor for W.A.I. — Workforce Apprentice Institute (LCE-WAI partner program). Answer apprentice questions clearly, reference NEC articles when relevant, emphasize safety, and use plain language. Keep replies under 250 words.",
    "scripture": "You are a faith-based electrical trade mentor at W.A.I. For each question, give a short encouragement tying the apprentice's current work to a relevant scripture verse, then a one-paragraph teaching point. Keep the tone warm and dignified.",
    "quiz_gen": "You generate short multiple-choice quiz questions (4 options, mark the correct answer index 0-3) on electrical topics. Output a clean numbered list with answer key at the end.",
    "explain": "You explain electrical concepts step-by-step to apprentices. Use analogies, list steps, and close with a 1-line 'Safety first' reminder.",
    "nec_lookup": "You are an NEC (National Electrical Code) reference assistant. When the apprentice asks about a topic, identify the most likely NEC article and section (e.g., 'NEC 210.8(A)(1)'), summarize the rule in plain English, give one practical example, and note any common code-cycle changes. ALWAYS remind the apprentice to verify against the current adopted code edition for their jurisdiction.",
    "blueprint": "You are an electrical blueprint reading assistant. The apprentice will describe (or paste a description of) a residential or light-commercial electrical plan. Identify likely circuits, panel sizing, branch counts, and any code concerns. Output a structured list: Circuits, Panels, Concerns. Keep it concise and tied to NEC articles where helpful.",
}


@api_router.post("/ai/chat")
async def ai_chat(body: AIChatReq, user: User = Depends(current_user)):
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
    certs = []
    for p in prog:
        mod = await db.modules.find_one({"slug": p["module_slug"]}, {"_id": 0})
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
    for d in docs:
        u = await db.users.find_one({"id": d["user_id"]}, {"_id": 0, "password_hash": 0})
        lab = await db.labs.find_one({"slug": d["lab_slug"]}, {"_id": 0})
        d["user"] = u
        d["lab"] = lab
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
    # competency points
    comp = {c["key"]: 0 for c in COMPETENCIES}
    for s in lab_subs:
        lab = await db.labs.find_one({"slug": s["lab_slug"]}, {"_id": 0})
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

    # Module completion rates
    mod_completions = []
    for m in MODULES:
        cnt = await db.progress.count_documents({"module_slug": m["slug"], "status": "completed"})
        mod_completions.append({
            "slug": m["slug"], "title": m["title"], "completions": cnt,
            "rate": round(cnt / max(1, students) * 100, 1),
        })

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
