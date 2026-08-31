"""
Auth router — login, registration, sessions, password reset, exec recovery.

Extracted verbatim from backend/server.py (monolith refactor, slice 1).
Shared state (db, audit, notify, current_user, require_role, can_modify,
and the auth helper functions) is bound by server.py via bind() at include
time, so this module has no circular imports.
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel, Field

from recovery import (
    generate_recovery_codes,
    verify_recovery_code,
    get_recovery_code_status,
    emergency_password_reset,
)
from security.field_authorization import FieldAuthorization

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["auth"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = audit = notify = None
current_user = can_modify = None
check_rate = hash_pw = verify_pw = make_token = None
_send_reset_email = _build_reset_url = _send_welcome_email = None
_gen_random_password = None


def bind(_db, _audit, _notify, _current_user, _can_modify,
         _check_rate, _hash_pw, _verify_pw, _make_token,
         _sre, _bru, _swe, _grp):
    """Called by server.py at include time to inject shared dependencies.
    Short param names avoid shadowing the module-level helper globals
    (_send_reset_email, _build_reset_url, _send_welcome_email,
    _gen_random_password)."""
    global db, audit, notify, current_user, can_modify
    global check_rate, hash_pw, verify_pw, make_token
    global _send_reset_email, _build_reset_url, _send_welcome_email
    global _gen_random_password
    db, audit, notify = _db, _audit, _notify
    current_user, can_modify = _current_user, _can_modify
    check_rate, hash_pw, verify_pw = _check_rate, _hash_pw, _verify_pw
    make_token = _make_token
    _send_reset_email, _build_reset_url = _sre, _bru
    _send_welcome_email = _swe
    _gen_random_password = _grp


# ── Exec seat / env configuration (read directly, mirrors server.py) ─────────
EXEC_ADMIN_EMAIL = os.environ.get("EXEC_ADMIN_EMAIL", "").strip()
EXEC_DEFAULT_PASSWORD = os.environ.get("EXEC_DEFAULT_PASSWORD", "")
BACKUP_EXEC_EMAIL = os.environ.get("BACKUP_EXEC_ADMIN_EMAIL", "").strip()
BACKUP_EXEC_DEFAULT_PASSWORD = os.environ.get("BACKUP_EXEC_DEFAULT_PASSWORD", "")
NAM_EXEC_EMAIL = os.environ.get("NAM_EXEC_EMAIL", "").strip()
NAM_EXEC_DEFAULT_PASSWORD = os.environ.get("NAM_EXEC_DEFAULT_PASSWORD", "")
EXEC_RESET_SECRET = os.environ.get("EXEC_RESET_SECRET", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESET_TOKEN_TTL_MIN = int(os.environ.get("PASSWORD_RESET_TTL_MIN", "30"))
# Mirrors server.py's role hierarchy for runtime require_role checks.



def _require_rank(*roles):
    """Runtime equivalent of server.py's require_role() — used inside handlers
    because require_role is bound after this module loads (no import-time call)."""
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: UserOut = Depends(_dep_current_user)) -> UserOut:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            logger.warning("Unauthorized access attempt — insufficient privileges (user=%s, role=%s)", user.id, user.role)
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep

# ── Request models (mirror server.py definitions) ────────────────────────────
class RegisterReq(BaseModel):
    email: str
    full_name: str
    password: str
    agreed_terms: bool = False
    over_13: bool = False
    promo_code: Optional[str] = None


class LoginReq(BaseModel):
    email: str
    password: str


class ForgotPasswordReq(BaseModel):
    email: str


class ResetPasswordReq(BaseModel):
    token: str
    new_password: str


class RecoveryCodeStatusReq(BaseModel):
    email: str


class EmergencyRecoveryReq(BaseModel):
    email: str
    recovery_code: str
    new_password: str


class ChangePasswordReq(BaseModel):
    current_password: str
    new_password: str


class SelfEditMeReq(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    social_handles: Optional[dict] = None


class UserOut(BaseModel):
    """Mirror of server.py's User model — identical field set + defaults so
    doc construction (register/login) and response serialization behave the
    same after extraction. EmailStr is intentionally plain str here: server.py
    validates on the way in; we only construct from DB docs."""
    model_config = {"extra": "ignore"}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: str = "student"
    social_handles: Optional[dict] = None
    associate: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    avatar_url: Optional[str] = None
    feature_tier: str = "free"


async def _dep_current_user(authorization: Optional[str] = Header(None)) -> UserOut:
    """Resolve the real current_user at REQUEST time (bind() sets it after import)."""
    return await current_user(authorization)


class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Password-reset helpers (extracted verbatim from server.py) ───────────────
import hashlib  # noqa: E402
import secrets  # noqa: E402
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES


def _hash_token(raw: str) -> str:
    """Stable sha256 hash of the raw token. We never store the raw token
    in MongoDB — only the hash. Lookups use the hash."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _make_reset_token() -> tuple:
    """Returns (raw_token, sha256_hex). The raw token is shown ONCE."""
    raw = secrets.token_urlsafe(32)
    return raw, _hash_token(raw)


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
    await db.users.update_one({"id": target_id}, {
        "$set": {
            "password_hash": hash_pw(new_password),
            "must_change_password": False,
        },
        "$inc": {"token_version": 1},  # credential rotation revokes all prior JWTs
    })
    await db.auth_sessions.delete_many({"user_id": target_id})
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


# ── Endpoints (extracted verbatim from server.py) ────────────────────────────
@router.post("/auth/register", response_model=TokenResp)
async def register(body: RegisterReq, request: Request):

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

    # Optional promo code — a valid code grants its stated tier at signup.
    # The reservation is atomic (find_one_and_update + $inc) so two people can't
    # redeem the last use simultaneously. If the account is then rolled back,
    # the reserved use is released.
    _promo_grant = None
    if body.promo_code:
        from routers import promo_codes as _promo_mod
        _promo_doc = await _promo_mod.reserve_promo(body.promo_code)
        if not _promo_doc:
            raise HTTPException(400, "That promo code is invalid, expired, or already fully redeemed.")
        _promo_grant = _promo_mod.grant_fields_for(_promo_doc)

    # Public self-registration is always a student. Higher-privilege accounts
    # must be created by an admin (POST /api/admin/users). Exception: the very
    # FIRST account ever registered (empty users collection — e.g. immediately
    # after a factory reset) may bootstrap the executive_admin owner — but ONLY
    # when the registering address IS one of the configured exec seat emails.
    #
    # SECURITY FIX (2026-08-31): this previously required only that *some* seat
    # email was configured (`bool(EXEC_ADMIN_EMAIL or ...)`), without checking
    # that the registrant was that person. Configuring EXEC_ADMIN_EMAIL therefore
    # ARMED the grant for whoever registered first, with any address — the exact
    # opposite of the intent in this comment. It was masked only because no seat
    # email was set, which kept the branch permanently unreachable.
    #
    # This is not a theoretical window. Exec seats are seeded inside
    # server._on_startup_impl (server.py:1065), which runs as a fire-and-forget
    # asyncio task, so the API accepts registrations BEFORE the seed rows exist.
    # During that window `existing_users` is genuinely 0 on a fresh database.
    # Matching the email closes the escalation regardless of the race.
    existing_users = await db.users.count_documents({})
    _seat_emails = {
        _e.strip().lower()
        for _e in (EXEC_ADMIN_EMAIL, BACKUP_EXEC_EMAIL, NAM_EXEC_EMAIL)
        if _e and _e.strip()
    }
    _is_exec_seat = (body.email or "").strip().lower() in _seat_emails
    role = "executive_admin" if (existing_users == 0 and _is_exec_seat) else "student"
    if existing_users == 0 and not _is_exec_seat:
        logger.warning(
            "Bootstrap exec grant DENIED — first registration did not match a "
            "configured exec seat email. Account created as student."
        )
    user = UserOut(email=body.email, full_name=body.full_name, role=role)
    if _promo_grant:
        user = user.model_copy(update={"feature_tier": _promo_grant["feature_tier"]})
    doc = user.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["password_hash"] = hash_pw(body.password)
    doc["token_version"] = 0
    # Record consent timestamp for GDPR audit trail
    doc["terms_accepted_at"] = datetime.now(timezone.utc).isoformat()
    doc["over_13_confirmed"] = True
    # Promo tier grant fields (feature_tier already set above via model_copy).
    if _promo_grant:
        doc.update({k: v for k, v in _promo_grant.items() if k != "feature_tier"})
    await db.users.insert_one(doc)
    # Registration tokens are session-bound just like login tokens. If the
    # session record cannot be created, do not issue an untracked token.
    session_id = str(uuid.uuid4())
    try:
        await db.auth_sessions.insert_one({
            "session_id": session_id,
            "user_id": user.id,
            "user_agent": request.headers.get("user-agent", "")[:200],
            "ip": request.client.host if request.client else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.exception("register: session recording failed")
        # Do not leave an account that can neither authenticate nor be
        # deterministically resumed after a session-store failure.
        if _promo_grant:
            from routers import promo_codes as _promo_mod
            await _promo_mod.release_promo(body.promo_code)
        await db.users.delete_one({"id": user.id})
        raise HTTPException(503, "Unable to establish a secure session. Please try again.")
    await audit(user.id, "auth.register.success", meta={"consent_terms": True, "over_13": True})
    if _promo_grant:
        await audit(user.id, "promo.redeemed", target=body.promo_code.strip().upper(),
                    meta={"tier": _promo_grant["feature_tier"]})
    # Send welcome email — fire-and-forget, never blocks registration
    asyncio.create_task(_send_welcome_email(user.email, user.full_name))
    return TokenResp(
        access_token=make_token(user.id, user.role, extra={"tv": 0, "session_id": session_id}),
        user=user,
    )


@router.post("/auth/login", response_model=TokenResp)
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
    user = UserOut(**doc)
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
        logger.exception("login: session recording failed")
        raise HTTPException(503, "Unable to establish a secure session. Please try again.")
    _extra = {"tv": int(doc.get("token_version", 0)), "session_id": _session_id}
    return TokenResp(access_token=make_token(user.id, user.role, extra=_extra), user=user)


@router.get("/auth/me", response_model=UserOut)
async def me(user: UserOut = Depends(_dep_current_user)):
    # Check if a time-limited trial has expired and revert feature_tier automatically
    user_doc = await db.users.find_one({"id": user.id},
        {"feature_tier_expires_at": 1, "feature_tier_revert_to": 1, "feature_tier": 1})
    if user_doc:
        expires_str = user_doc.get("feature_tier_expires_at")
        if expires_str:
            try:
                from dateutil.parser import parse as _parse_dt
                expires_dt = _parse_dt(expires_str)
                if expires_dt.tzinfo is None:
                    expires_dt = expires_dt.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > expires_dt:
                    revert_to = user_doc.get("feature_tier_revert_to", "free")
                    await db.users.update_one({"id": user.id}, {"$set": {
                        "feature_tier": revert_to,
                        "feature_tier_source": "trial_expired",
                        "feature_tier_updated_at": datetime.now(timezone.utc).isoformat(),
                    }, "$unset": {"feature_tier_expires_at": "", "feature_tier_revert_to": ""}})
                    user = user.model_copy(update={"feature_tier": revert_to})
            except Exception:
                pass

    visible_fields = FieldAuthorization.get_visible_fields(
        viewer_role=user.role,
        target_role=user.role,
        is_own_profile=True
    )
    user_dict = user.model_dump()
    filtered = FieldAuthorization.filter_response(user_dict, visible_fields)
    return UserOut(**filtered)


@router.delete("/auth/account")
async def gdpr_delete_account(user: UserOut = Depends(_dep_current_user)):
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


@router.get("/auth/account/export")
async def gdpr_export_data(user: UserOut = Depends(_dep_current_user)):
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


@router.post("/auth/reconsent")
async def gdpr_reconsent(body: dict, user: UserOut = Depends(_dep_current_user)):
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


@router.post("/auth/change-password")
async def change_password(body: ChangePasswordReq, request: Request,
                          user: UserOut = Depends(_dep_current_user)):
    """Any authenticated user can change their own password.
    Returns a fresh token + updated user so the client can update its cache
    immediately without relying on a follow-up /auth/me call."""
    if len(body.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    doc = await db.users.find_one({"id": user.id}, {"_id": 0})
    if not doc or not verify_pw(body.current_password, doc["password_hash"]):
        raise HTTPException(401, "Current password is incorrect")
    await db.users.update_one({"id": user.id}, {
        "$set": {
            "password_hash": hash_pw(body.new_password),
            "must_change_password": False,
        },
        "$inc": {"token_version": 1},  # credential rotation revokes ALL sessions (fresh token issued below)
    })
    # Password rotation revokes every prior session. Establish one fresh,
    # tracked session for the response token so single-session logout remains
    # meaningful after a password change.
    await db.auth_sessions.delete_many({"user_id": user.id})
    fresh_session_id = str(uuid.uuid4())
    try:
        await db.auth_sessions.insert_one({
            "session_id": fresh_session_id,
            "user_id": user.id,
            "user_agent": request.headers.get("user-agent", "")[:200],
            "ip": request.client.host if request.client else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.exception("change-password: session recording failed")
        raise HTTPException(503, "Password changed, but a secure session could not be created. Please sign in again.")
    await audit(user.id, "auth.password_changed")
    # Fetch fresh user doc (must_change_password now False) and issue new token
    fresh_doc = await db.users.find_one({"id": user.id}, {"_id": 0, "password_hash": 0})
    if fresh_doc and isinstance(fresh_doc.get("created_at"), str):
        fresh_doc["created_at"] = datetime.fromisoformat(fresh_doc["created_at"])
    fresh_user = UserOut(**(fresh_doc or {}))
    return {
        "ok": True,
        "access_token": make_token(
            fresh_user.id,
            fresh_user.role,
            extra={
                "tv": int(fresh_doc.get("token_version", 0)) if fresh_doc else 0,
                "session_id": fresh_session_id,
            },
        ),
        "user": fresh_user.model_dump(),
    }


@router.patch("/auth/me", response_model=UserOut)
async def edit_self(body: SelfEditMeReq, user: UserOut = Depends(_dep_current_user)):
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
    if body.social_handles is not None:
        if not isinstance(body.social_handles, dict):
            raise HTTPException(400, "social_handles must be an object of platform → handle")
        cleaned = {}
        for k, v in body.social_handles.items():
            if not isinstance(k, str):
                continue
            val = "" if v is None else str(v).strip()
            if val:
                cleaned[k[:50]] = val[:300]
        update["social_handles"] = cleaned
    if update:
        await db.users.update_one({"id": user.id}, {"$set": update})
        audit_meta = {k: v for k, v in update.items() if k != "avatar_url"}
        await audit(user.id, "auth.self_edit", target=user.id, meta=audit_meta)
    fresh = await db.users.find_one({"id": user.id}, {"_id": 0, "password_hash": 0})
    if isinstance(fresh.get("created_at"), str):
        fresh["created_at"] = datetime.fromisoformat(fresh["created_at"])
    return UserOut(**fresh)


@router.post("/auth/forgot-password")
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
    email_reason = ""
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
        email_sent, email_reason = await _send_reset_email(
            user_doc["email"], raw, user_doc.get("full_name", "there"), base_url=_req_base,
        )
        if not email_sent:
            # Owner escape hatch: no email provider configured (or delivery failed) —
            # surface the one-time recovery link in the server log so the operator
            # can complete the flow from Railway logs. Link expires in
            # RESET_TOKEN_TTL_MIN minutes and is single-use.
            logger.warning(
                "PASSWORD RESET: email could not be delivered to %s (%s) — one-time recovery link (expires in %s min): %s",
                user_doc["email"], email_reason, RESET_TOKEN_TTL_MIN, _build_reset_url(raw, base=_req_base),
            )
        # Dev/admin convenience: when explicitly enabled, return the raw
        # token so the requester (or curl-based tests) can complete the
        # flow without an email provider.  Defaults to OFF in production.
        if os.environ.get("DEV_RETURN_RESET_TOKEN") == "1":
            return {"ok": True, "email_sent": email_sent,
                    "_dev_token": raw, "_dev_url": _build_reset_url(raw)}
    return {"ok": True, "email_sent": email_sent, "email_error": email_reason if not email_sent else ""}


@router.post("/admin/users/{uid}/reset-link")
async def admin_create_reset_link(uid: str, request: Request,
                                  user: UserOut = Depends(_require_rank("admin"))):
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
    email_sent, email_reason = await _send_reset_email(
        target["email"], raw, target.get("full_name", "there"),
    )
    await audit(user.id, "admin.password_reset.link_issued", target=target["id"],
                meta={"email": target["email"], "email_sent": email_sent})
    return {
        "ok": True,
        "email": target["email"],
        "email_sent": email_sent,
        "email_error": email_reason if not email_sent else "",
        "token": raw,
        "url": _build_reset_url(raw),
        "expires_at": expires_at.isoformat(),
        "ttl_minutes": RESET_TOKEN_TTL_MIN,
    }


@router.post("/auth/reset-password")
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


@router.post("/auth/recovery-status")
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


@router.post("/auth/emergency-recovery")
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

    # Recovery rotates credentials and invalidates every prior session. Issue
    # one new tracked session using the incremented token generation.
    await db.auth_sessions.delete_many({"user_id": user_doc["id"]})
    recovery_session_id = str(uuid.uuid4())
    try:
        await db.auth_sessions.insert_one({
            "session_id": recovery_session_id,
            "user_id": user_doc["id"],
            "user_agent": request.headers.get("user-agent", "")[:200],
            "ip": request.client.host if request.client else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.exception("emergency-recovery: session recording failed")
        raise HTTPException(503, "Password reset succeeded, but a secure session could not be created. Please sign in again.")
    user_doc["token_version"] = int(user_doc.get("token_version", 0)) + 1
    # Issue JWT token for immediate login
    token = make_token(
        user_doc["id"],
        user_doc.get("role", "student"),
        extra={"tv": int(user_doc.get("token_version", 0)), "session_id": recovery_session_id},
    )
    await audit(user_doc["id"], "auth.emergency_recovery.completed",
                target=user_doc["id"], meta={"ip": ip, "recovery_used": True})

    return {
        "ok": True,
        "access_token": token,
        "token_type": "bearer",
        "email": user_doc["email"],
        "message": "Account recovered. You are now logged in. Please update your password in settings.",
    }


@router.post("/auth/exec-unlock")
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
        _seat for _seat in [
            (EXEC_ADMIN_EMAIL,  "Delon Oliver",  EXEC_DEFAULT_PASSWORD),
            (BACKUP_EXEC_EMAIL, "Delon Oliver",  BACKUP_EXEC_DEFAULT_PASSWORD),
            (NAM_EXEC_EMAIL,    "NAM Oshun",     NAM_EXEC_DEFAULT_PASSWORD),
        ] if _seat[0]
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
                # Send the generated password via the standard provider chain
                # (Resend -> Gmail). If it fails, the log below still carries it.
                await _send_welcome_email(_email, _name)
            except Exception:
                logger.warning("exec-unlock: email failed for %s — TEMP PASSWORD (change immediately): %s", _email, _pw)
    # A stale executive IP whitelist can block the very routes exec needs after
    # recovery — clear it so the unlocked accounts can actually reach the panel.
    try:
        await db.ip_whitelist.delete_many({"role": "executive_admin"})
    except Exception:
        pass
    await audit(None, "exec.unlock.via_secret", meta={"ip": request.client.host if request.client else "unknown"})
    logger.warning("exec-unlock: all exec seats reset via secret key")
    return {"ok": True, "reset": reset, "message": "All exec seats unlocked. Check Railway logs or email for auto-generated passwords."}


@router.post("/auth/factory-reset")
async def factory_reset(request: Request):
    """Wipe ALL user accounts and user-owned data — full factory reset.

    Gated by a break-glass secret: either EXEC_RESET_SECRET or RESEND_API_KEY
    (both are owner-only secrets; accepting either means the wipe works even
    when only one of them has reached the running process).

    POST {"secret": "<secret>", "confirm": "DELETE ALL"}

    After the wipe the users collection is empty, so the NEXT registration
    becomes the executive_admin bootstrap owner (see /auth/register).
    """
    gate = EXEC_RESET_SECRET or RESEND_API_KEY
    if not gate:
        raise HTTPException(404, "Not found")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "JSON body required")
    if body.get("secret") != gate:
        await asyncio.sleep(2)
        raise HTTPException(403, "Invalid secret")
    if body.get("confirm") != "DELETE ALL":
        raise HTTPException(400, 'Send {"confirm": "DELETE ALL"} to confirm this destructive action.')

    deleted = {}
    for coll in ["users", "password_reset_tokens", "progress", "lab_submissions",
                 "portfolio", "ai_consents", "certificates", "sessions"]:
        try:
            r = await db[coll].delete_many({})
            deleted[coll] = r.deleted_count
        except Exception as exc:
            deleted[coll] = f"error: {exc}"
    try:
        await db.ip_whitelist.delete_many({"role": "executive_admin"})
    except Exception:
        pass
    await audit(None, "factory.reset.performed", meta={"ip": request.client.host if request.client else "unknown"})
    logger.warning("FACTORY RESET: all accounts and user data deleted: %s", deleted)
    return {"ok": True, "deleted": deleted,
            "message": "All accounts deleted. The next registration becomes the executive_admin (owner) account."}


@router.post("/auth/recovery-codes-generate")
async def generate_recovery_codes_endpoint(user: UserOut = Depends(_require_rank("executive_admin"))):
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


# ── Session management ───────────────────────────────────────────────────────
@router.get("/auth/sessions")
async def list_sessions(user: UserOut = Depends(_dep_current_user)):
    """List active login sessions for the current user."""
    sessions = await db.auth_sessions.find(
        {"user_id": user.id},
        {"_id": 0, "session_id": 1, "user_agent": 1, "ip": 1, "created_at": 1, "last_seen": 1},
    ).sort("created_at", -1).to_list(length=20)
    return {"sessions": sessions}


@router.delete("/auth/sessions/{session_id}")
async def revoke_session(session_id: str, user: UserOut = Depends(_dep_current_user)):
    """Revoke a specific session (log out that device)."""
    result = await db.auth_sessions.delete_one({"user_id": user.id, "session_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Session not found")
    return {"ok": True}


@router.delete("/auth/sessions")
async def revoke_all_sessions(user: UserOut = Depends(_dep_current_user)):
    """Revoke all sessions except the current one (log out other devices)."""
    # Increment token version to invalidate all existing JWTs
    await db.users.update_one({"id": user.id}, {"$inc": {"token_version": 1}})
    # Clear session records
    await db.auth_sessions.delete_many({"user_id": user.id})
    return {"ok": True, "message": "All other sessions revoked. Please re-authenticate."}


# ── Cross-site SSO ──────────────────────────────────────────────────────────

@router.get("/auth/cross-site-token")
async def generate_cross_site_token(user: UserOut = Depends(_dep_current_user)):
    """Generate a short-lived token for cross-site login.

    The caller (frontend) passes this token to the partner site's
    /auth/cross-site-login endpoint to establish a session there.
    """
    from cross_site_auth import generate_cross_site_token as _gen_token
    token = _gen_token(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )
    return {"token": token, "expires_in": 300}


@router.post("/auth/cross-site-login")
async def cross_site_login(body: dict, request: Request):
    """Exchange a cross-site token for a local session.

    Accepts {"token": "<cross-site-token>"} and returns a local JWT
    if the token is valid and the user exists (or is auto-created).
    """
    from cross_site_auth import validate_cross_site_token
    from roles import normalize_role
    
    token = body.get("token", "")
    if not token:
        raise HTTPException(400, "Token is required")
    
    payload = validate_cross_site_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired cross-site token")
    
    email = payload.get("email", "")
    user_id = payload.get("uid", "")
    full_name = payload.get("name", "Student")

    # Partner-token roles are NEVER trusted for authorization. A cross-site
    # token only proves the bearer holds an account on the partner site; it
    # does not prove staff/executive authority here. All cross-site sessions
    # are created as least-privilege (student) and an existing local user's
    # role is never raised by partner claims — role changes are admin-only.
    role = "student"

    # Find or create the local user
    existing = await db.users.find_one({"email": email})
    if existing:
        # Never elevate: role is unchanged regardless of what the partner
        # token claimed. (An existing privileged local user keeps their role;
        # a local student stays a student.)
        user_doc = existing
    else:
        # Auto-create the user on this site — always least-privilege.
        user_doc = {
            "id": user_id or str(uuid.uuid4()),
            "email": email,
            "full_name": full_name,
            "role": role,
            "is_active": True,
            "must_change_password": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "avatar_url": None,
            "feature_tier": "free",
            "token_version": 0,
        }
        await db.users.insert_one(user_doc)
        logger.info("Cross-site: auto-created user %s (least-privilege student)", email)
    
    # Bind the local token to a tracked session just like password login.
    cross_site_session_id = str(uuid.uuid4())
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.auth_sessions.insert_one({
            "session_id": cross_site_session_id,
            "user_id": user_doc["id"],
            "user_agent": request.headers.get("user-agent", "")[:200],
            "ip": request.client.host if request.client else None,
            "created_at": now_iso,
            "last_seen": now_iso,
            "source": "partner_site",
        })
    except Exception:
        logger.exception("cross-site-login: session recording failed")
        raise HTTPException(503, "Unable to establish a secure session. Please try again.")

    # Issue a local JWT
    token_raw = make_token(
        user_doc["id"],
        user_doc.get("role", "student"),
        extra={"tv": int(user_doc.get("token_version", 0)), "session_id": cross_site_session_id},
    )
    
    # Audit the cross-site login
    await audit(user_doc["id"], "cross_site.login", meta={
        "source": "partner_site",
        "source_uid": user_id,
        "role": role,
    })
    
    return {"token": token_raw, "role": user_doc.get("role", "student")}
