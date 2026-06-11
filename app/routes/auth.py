"""app/routes/auth.py — Authentication, GDPR, recovery, and session endpoints.

Extracted from backend/server.py.
No logic changed.
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import (
    APP_VERSION,
    EXEC_ADMIN_EMAIL, EXEC_DEFAULT_PASSWORD,
    BACKUP_EXEC_EMAIL, BACKUP_EXEC_DEFAULT_PASSWORD,
    NAM_EXEC_EMAIL, NAM_EXEC_DEFAULT_PASSWORD,
    EXEC_RESET_SECRET, JWT_SECRET, JWT_ALGO,
    RESET_TOKEN_TTL_MIN, ROLE_RANK,
)
from app.database import db
from app.models.user import (
    User, RegisterReq, LoginReq, TokenResp, ChangePasswordReq,
    SelfEditMeReq, ForgotPasswordReq, ResetPasswordReq,
    EmergencyRecoveryReq, RecoveryCodeStatusReq,
)
from app.security.auth import current_user, require_role, can_modify, make_token
from app.security.passwords import (
    hash_pw, verify_pw, _hash_token, _make_reset_token, _build_reset_url,
    _send_reset_email, _send_welcome_email,
)
from app.security.rate_limit import async_check_rate as check_rate
from app.utils.audit import audit, notify

logger = logging.getLogger("lcewai")

router = APIRouter()

# FieldAuthorization is used in /auth/me and /admin/users — imported lazily
try:
    from field_authorization import FieldAuthorization
except ImportError:
    FieldAuthorization = None  # type: ignore


@router.post("/auth/register", response_model=TokenResp)
async def register(body: RegisterReq):
    await check_rate(f"register:{body.email}", max_calls=5, window_sec=60)
    if await db.users.find_one({"email": body.email}):
        raise HTTPException(400, "Email already registered")

    if not body.agreed_terms:
        raise HTTPException(400, "You must agree to the Terms of Service and Privacy Policy to create an account.")
    if not body.over_13:
        raise HTTPException(400, "You must be at least 13 years old to create an account. If you are under 13, please ask a parent or guardian to contact us.")
    if len(body.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")

    user = User(email=body.email, full_name=body.full_name, role="student")
    doc = user.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["password_hash"] = hash_pw(body.password)
    doc["terms_accepted_at"] = datetime.now(timezone.utc).isoformat()
    doc["over_13_confirmed"] = True
    await db.users.insert_one(doc)
    await audit(user.id, "auth.register.success", meta={"consent_terms": True, "over_13": True})
    asyncio.create_task(_send_welcome_email(user.email, user.full_name))
    return TokenResp(access_token=make_token(user.id, user.role), user=user)


@router.post("/auth/login", response_model=TokenResp)
async def login(body: LoginReq, request: Request):
    # Per-email AND per-IP rate limits — both must pass
    _login_ip = (
        (request.headers.get("x-forwarded-for", "") or "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )
    await check_rate(f"login:{body.email}", max_calls=5, window_sec=60)
    await check_rate(f"login:ip:{_login_ip}", max_calls=20, window_sec=60)
    doc = await db.users.find_one({"email": body.email}, {"_id": 0})

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
                pass

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
                try:
                    from app.utils.alerting import alert_account_locked
                    asyncio.create_task(alert_account_locked(body.email))
                except Exception:
                    pass
            await db.users.update_one({"email": body.email}, {"$set": update})
        raise HTTPException(401, "Invalid credentials")

    if doc.get("is_active") is False:
        await audit(doc.get("id"), "auth.login.blocked_inactive", body.email)
        raise HTTPException(403, "Your account has been deactivated. Contact your administrator.")

    # ── MFA enforcement ──────────────────────────────────────────────────────────
    # If the executive has configured MFA for this role, require a TOTP token.
    # The client sends it as X-MFA-Token header; the raw header value is checked
    # against the stored TOTP secret via pyotp (if installed).
    if db is not None:
        try:
            mfa_cfg = await db.mfa_config.find_one({"_id": "config"}, {"_id": 0})
            if mfa_cfg and mfa_cfg.get("totp_enabled"):
                required_roles = mfa_cfg.get("require_mfa_for_roles", [])
                user_role_for_mfa = doc.get("role", "student")
                if user_role_for_mfa in required_roles:
                    mfa_token = (request.headers.get("x-mfa-token") or "").strip()
                    totp_secret = doc.get("totp_secret")
                    if not totp_secret:
                        raise HTTPException(
                            403,
                            detail={
                                "error": "mfa_not_configured",
                                "message": "MFA is required for your role but has not been set up on your account. Contact your administrator.",
                            },
                        )
                    if not mfa_token:
                        raise HTTPException(
                            403,
                            detail={
                                "error": "mfa_required",
                                "message": "Multi-factor authentication is required. Provide your TOTP code in the X-MFA-Token header.",
                            },
                        )
                    try:
                        import pyotp as _pyotp
                        totp = _pyotp.TOTP(totp_secret)
                        if not totp.verify(mfa_token, valid_window=1):
                            await audit(doc.get("id"), "auth.login.mfa_failed", body.email)
                            raise HTTPException(401, "Invalid MFA token.")
                    except ImportError:
                        logger.warning("pyotp not installed — MFA check skipped for role=%s", user_role_for_mfa)
        except HTTPException:
            raise
        except Exception as _mfa_err:
            logger.warning("MFA config check failed (non-fatal): %s", _mfa_err)

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
    _tv = doc.get("token_version", 0)
    return TokenResp(access_token=make_token(user.id, user.role, extra=_extra, token_version=_tv), user=user)


@router.post("/auth/refresh")
async def refresh_token(user: User = Depends(current_user)):
    """Issue a rotated JWT for an authenticated user without requiring re-login.

    Reads current token_version from DB (revocation-safe). Each refresh produces a
    unique token via jti claim — the caller should immediately discard the old token.
    """
    import uuid as _uuid
    doc = await db.users.find_one({"id": user.id}, {"_id": 0, "token_version": 1})
    _tv = (doc or {}).get("token_version", 0)
    new_token = make_token(user.id, user.role, extra={"jti": str(_uuid.uuid4())}, token_version=_tv)
    await audit(user.id, "auth.token_rotated")
    return {"access_token": new_token}


@router.get("/auth/me")
async def me(user: User = Depends(current_user)):
    if FieldAuthorization is not None:
        visible_fields = FieldAuthorization.get_visible_fields(
            viewer_role=user.role,
            target_role=user.role,
            is_own_profile=True
        )
        user_dict = user.model_dump()
        filtered = FieldAuthorization.filter_response(user_dict, visible_fields)
        user_out = User(**filtered)
    else:
        user_out = user

    # Attach capability contract so the frontend doesn't need a second round-trip
    try:
        from app.security.feature_tiers import build_capability_contract
        from app.security.enforcement import _resolve_user_tier, _resolve_sage_tier
        feature_tier = await _resolve_user_tier(user.id)
        sage_tier    = await _resolve_sage_tier(user.id)
        capabilities = build_capability_contract(
            role=user.role,
            feature_tier=feature_tier,
            sage_tier=sage_tier,
            more_member=getattr(user, "more_member", False),
        )
    except Exception:
        capabilities = None

    result = user_out.model_dump()
    if capabilities is not None:
        result["capabilities"] = capabilities
    return result


@router.get("/auth/capabilities")
async def get_capabilities(user: User = Depends(current_user)):
    """Return the full capability contract for the authenticated user.

    Used by the frontend to determine feature visibility without re-fetching /auth/me.
    """
    from app.security.feature_tiers import build_capability_contract
    from app.security.enforcement import _resolve_user_tier, _resolve_sage_tier

    feature_tier = await _resolve_user_tier(user.id)
    sage_tier    = await _resolve_sage_tier(user.id)

    return build_capability_contract(
        role=user.role,
        feature_tier=feature_tier,
        sage_tier=sage_tier,
        more_member=getattr(user, "more_member", False),
    )


@router.post("/auth/change-password")
async def change_password(body: ChangePasswordReq, user: User = Depends(current_user)):
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
    fresh_doc = await db.users.find_one({"id": user.id}, {"_id": 0, "password_hash": 0})
    if fresh_doc and isinstance(fresh_doc.get("created_at"), str):
        fresh_doc["created_at"] = datetime.fromisoformat(fresh_doc["created_at"])
    fresh_user = User(**(fresh_doc or {}))
    return {
        "ok": True,
        "access_token": make_token(fresh_user.id, fresh_user.role),
        "user": fresh_user.model_dump(),
    }


@router.patch("/auth/me", response_model=User)
async def edit_self(body: SelfEditMeReq, user: User = Depends(current_user)):
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


# --- GDPR ---

@router.delete("/auth/account")
async def gdpr_delete_account(user: User = Depends(current_user)):
    if user.role == "executive_admin":
        active_execs = await db.users.count_documents({"role": "executive_admin", "is_active": {"$ne": False}})
        if active_execs <= 1:
            raise HTTPException(400, "Cannot delete the last executive_admin account. Contact support.")
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
    # Delete all user-owned data across every collection
    _delete_colls = [
        # Original collections
        "progress", "lab_submissions", "portfolio", "ai_consents",
        # Phase 2 collections (legal, exec controls, chat, sessions)
        "legal_consents", "break_glass_overrides", "user_feature_flags",
        "chat_history", "notifications", "auth_sessions",
    ]
    for coll in _delete_colls:
        try:
            await db[coll].delete_many({"user_id": user.id})
        except Exception:
            pass
    # Anonymise exec_audit_log actor_id rather than delete (preserve audit chain)
    try:
        await db.exec_audit_log.update_many(
            {"actor_id": user.id},
            {"$set": {"actor_id": f"[deleted:{user.id[:8]}]", "actor_email": "[deleted]"}},
        )
    except Exception:
        pass
    await audit(user.id, "gdpr.account_deleted", meta={"grace_period_days": 30})
    return {"ok": True, "message": "Account scheduled for deletion. You have a 30-day grace period to contact support if this was a mistake."}


@router.get("/auth/account/export")
async def gdpr_export_data(user: User = Depends(current_user)):
    export = {"exported_at": datetime.now(timezone.utc).isoformat(), "user_id": user.id}
    doc = await db.users.find_one({"id": user.id}, {"_id": 0, "password_hash": 0})
    if doc:
        export["profile"] = doc
    progress = await db.progress.find({"user_id": user.id}, {"_id": 0}).to_list(length=9999)
    if progress:
        export["progress"] = progress
    certs = await db.certificates.find({"user_id": user.id}, {"_id": 0}).to_list(length=9999)
    if certs:
        export["certificates"] = certs
    labs = await db.lab_submissions.find({"user_id": user.id}, {"_id": 0}).to_list(length=9999)
    if labs:
        export["lab_submissions"] = labs
    consents = await db.ai_consents.find({"user_id": user.id}, {"_id": 0}).to_list(length=9999)
    if consents:
        export["ai_consents"] = consents
    audit_log = await db.audit_log.find({"actor_id": user.id}, {"_id": 0}).sort("at", -1).to_list(length=100)
    if audit_log:
        export["recent_activity"] = audit_log
    await audit(user.id, "gdpr.data_exported")
    return export


@router.post("/auth/reconsent")
async def gdpr_reconsent(body: dict, user: User = Depends(current_user)):
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


# --- Exec system info ---

@router.get("/exec/system")
async def exec_system_info(user: User = Depends(require_role("executive_admin"))):
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


# --- Password reset flow ---

@router.post("/auth/forgot-password")
async def forgot_password(body: ForgotPasswordReq, request: Request):
    ip = (request.client.host if request.client else "anon")
    await check_rate(f"forgot:ip:{ip}", max_calls=30, window_sec=300)
    await check_rate(f"forgot:email:{body.email}", max_calls=5, window_sec=600)

    user_doc = await db.users.find_one({"email": body.email}, {"_id": 0})
    email_sent = False
    if user_doc and user_doc.get("is_active") is not False:
        raw, hashed = _make_reset_token()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=RESET_TOKEN_TTL_MIN)
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
            "expires_at": expires_at,
            "used_at": None,
            "ip": ip,
        })
        await audit(user_doc["id"], "auth.password_reset.requested",
                    target=user_doc["id"], meta={"ip": ip})
        email_sent = await _send_reset_email(
            user_doc["email"], raw, user_doc.get("full_name", "there"),
        )
        if os.environ.get("DEV_RETURN_RESET_TOKEN") == "1":
            return {"ok": True, "email_sent": email_sent,
                    "_dev_token": raw, "_dev_url": _build_reset_url(raw)}
    return {"ok": True, "email_sent": email_sent}


def _validate_reset_request(token: str, new_password: str) -> None:
    if len(new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if len(token) < 16:
        raise HTTPException(400, "Invalid token")


def _normalize_expiry(value) -> datetime:
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
    rec = await db.password_reset_tokens.find_one({"token_hash": token_hash}, {"_id": 0})
    if not rec or rec.get("used_at") is not None:
        raise HTTPException(400, "Invalid or already-used reset link")
    expires_at = _normalize_expiry(rec.get("expires_at"))
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "Reset link has expired — request a new one")
    return rec


async def _load_target_user_for_reset(user_id: str) -> dict:
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(400, "Invalid reset link")
    if target.get("is_active") is False:
        raise HTTPException(403, "Account is deactivated — contact an administrator")
    return target


async def _apply_password_reset(target_id: str, new_password: str,
                                token_hash: str, ip: str) -> None:
    now = datetime.now(timezone.utc)
    await db.users.update_one({"id": target_id}, {"$set": {
        "password_hash": hash_pw(new_password),
        "must_change_password": False,
    }})
    await db.password_reset_tokens.update_one(
        {"token_hash": token_hash},
        {"$set": {"used_at": now, "used_ip": ip}},
    )
    await db.password_reset_tokens.update_many(
        {"user_id": target_id, "used_at": None},
        {"$set": {"used_at": now}},
    )
    await audit(target_id, "auth.password_reset.completed",
                target=target_id, meta={"ip": ip})


@router.post("/auth/reset-password")
async def reset_password_endpoint(body: ResetPasswordReq, request: Request):
    _validate_reset_request(body.token, body.new_password)
    ip = (request.client.host if request.client else "anon")
    await check_rate(f"reset:ip:{ip}", max_calls=60, window_sec=300)
    token_hash = _hash_token(body.token)
    rec = await _load_reset_token(token_hash)
    target = await _load_target_user_for_reset(rec["user_id"])
    await _apply_password_reset(target["id"], body.new_password, token_hash, ip)
    return {"ok": True, "email": target["email"]}


# --- Recovery ---

@router.post("/auth/recovery-status")
async def recovery_code_status(body: RecoveryCodeStatusReq):
    from recovery import get_recovery_code_status
    status = await get_recovery_code_status(db, body.email)
    return {
        "ok": True,
        "remaining_codes": status["remaining_codes"],
        "total_codes": status["total_codes"],
        "generated_at": status["generated_at"],
    }


@router.post("/auth/emergency-recovery")
async def emergency_recovery(body: EmergencyRecoveryReq, request: Request):
    from recovery import verify_recovery_code, emergency_password_reset
    ip = (request.client.host if request.client else "emergency-recovery")
    await check_rate(f"recovery:ip:{ip}", max_calls=10, window_sec=300)
    await check_rate(f"recovery:email:{body.email}", max_calls=3, window_sec=600)

    user_doc = await db.users.find_one({"email": body.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(401, "Recovery code invalid or email not found")
    if user_doc.get("role") != "executive_admin":
        logger.warning("Recovery code attempted on non-executive account: %s", body.email)
        raise HTTPException(403, "Recovery codes are for executive accounts only")

    code_valid = await verify_recovery_code(db, body.email, body.recovery_code)
    if not code_valid:
        logger.warning("Invalid recovery code for: %s (ip=%s)", body.email, ip)
        raise HTTPException(401, "Recovery code invalid or already used")

    try:
        await emergency_password_reset(
            db, body.email, body.new_password,
            reason=f"recovery_code_used (ip={ip})"
        )
    except Exception as exc:
        logger.error("Recovery password reset failed for %s: %s", body.email, exc)
        raise HTTPException(500, "Password reset failed — contact administrator")

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


@router.post("/auth/exec-unlock")
async def exec_unlock(request: Request):
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
        (EXEC_ADMIN_EMAIL,  EXEC_DEFAULT_PASSWORD),
        (BACKUP_EXEC_EMAIL, BACKUP_EXEC_DEFAULT_PASSWORD),
        (NAM_EXEC_EMAIL,    NAM_EXEC_DEFAULT_PASSWORD),
    ]
    reset = []
    for _email, _pw in _seats:
        await db.users.update_one(
            {"email": _email},
            {
                "$set": {
                    "password_hash": hash_pw(_pw),
                    "role": "executive_admin",
                    "is_active": True,
                    "must_change_password": False,
                },
                "$unset": {"login_locked_until": "", "login_failed_attempts": ""},
            },
            upsert=False,
        )
        reset.append(_email)
    await audit(None, "exec.unlock.via_secret", meta={"ip": request.client.host if request.client else "unknown"})
    logger.warning("exec-unlock: all exec seats reset via secret key")
    return {"ok": True, "reset": reset, "message": "All exec seats unlocked. Log in with default passwords."}


@router.post("/auth/recovery-codes-generate")
async def generate_recovery_codes_endpoint(user: User = Depends(require_role("executive_admin"))):
    from recovery import generate_recovery_codes
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


# --- Session management ---

@router.get("/auth/sessions")
async def list_sessions(user: User = Depends(current_user)):
    sessions = await db.auth_sessions.find(
        {"user_id": user.id},
        {"_id": 0, "session_id": 1, "user_agent": 1, "ip": 1, "created_at": 1, "last_seen": 1},
    ).sort("created_at", -1).to_list(length=20)
    return {"sessions": sessions}


@router.delete("/auth/sessions/{session_id}")
async def revoke_session(session_id: str, user: User = Depends(current_user)):
    result = await db.auth_sessions.delete_one({"user_id": user.id, "session_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Session not found")
    return {"ok": True}


@router.delete("/auth/sessions")
async def revoke_all_sessions(user: User = Depends(current_user)):
    await db.users.update_one({"id": user.id}, {"$inc": {"token_version": 1}})
    await db.auth_sessions.delete_many({"user_id": user.id})
    await audit(user.id, "auth.sessions_revoked_all")
    return {"ok": True, "message": "All sessions revoked. Please re-authenticate."}


@router.post("/auth/force-logout/{uid}")
async def force_logout_user(uid: str, user: User = Depends(require_role("admin"))):
    """Force-revoke all tokens for a specific user. Admin+ required.

    Increments token_version in DB — every existing JWT for this user becomes invalid
    on their next request regardless of its exp claim.
    """
    target = await db.users.find_one({"id": uid}, {"_id": 0, "role": 1})
    if not target:
        raise HTTPException(404, "User not found")
    from app.security.auth import can_modify
    if not can_modify(user, target.get("role", "student")):
        raise HTTPException(403, "Cannot force-logout a user with a higher role than yours.")
    await db.users.update_one({"id": uid}, {"$inc": {"token_version": 1}})
    await db.auth_sessions.delete_many({"user_id": uid})
    await audit(user.id, "auth.force_logout", target=uid)
    return {"ok": True, "uid": uid, "message": "All tokens for this user have been revoked."}
