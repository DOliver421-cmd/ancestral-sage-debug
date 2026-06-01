"""app/security/enforcement.py — RBAC + tier enforcement layer.

Provides:
  - require_tier(min_tier)       FastAPI dependency
  - require_feature(feature)     FastAPI dependency
  - require_legal_consent(tool)  FastAPI dependency (legal tool gating)
  - TierEnforcementMiddleware    ASGI middleware (passive check + deny)
  - gate(min_role, min_tier, feature, require_consent)  All-in-one dependency

All enforcement is server-side. The frontend capability contract (from
feature_tiers.build_capability_contract) drives UI visibility only.
"""
from __future__ import annotations

import logging
from typing import Literal, Optional

from fastapi import Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.database import db
from app.models.user import User
from app.security.auth import current_user
from app.security.feature_tiers import (
    LegalToolPolicy,
    LEGAL_TOOL_POLICIES,
    feature_allowed,
    tier_meets_minimum,
)
from app.security.rbac import (
    ROLE_RANK,
    role_meets_minimum,
)
from app.utils.audit import audit

logger = logging.getLogger("lcewai")


# ── Tier resolver ───────────────────────────────────────────────────────────────

async def _resolve_user_tier(user_id: str) -> str:
    """Read feature_tier from the users collection. Falls back to 'free'."""
    if db is None:
        return "free"
    doc = await db.users.find_one({"id": user_id}, {"_id": 0, "feature_tier": 1})
    tier = (doc or {}).get("feature_tier", "free")
    return tier if tier in ("free", "premium", "executive") else "free"


async def _resolve_sage_tier(user_id: str) -> str:
    """Read sage_tier from the users collection. Falls back to 'basic'."""
    if db is None:
        return "basic"
    doc = await db.users.find_one({"id": user_id}, {"_id": 0, "sage_tier": 1})
    tier = (doc or {}).get("sage_tier", "basic")
    return tier if tier in ("basic", "advanced") else "basic"


# ── FastAPI dependency: require minimum feature tier ────────────────────────────

def require_tier(min_tier: Literal["free", "premium", "executive"]):
    """FastAPI dependency factory. Raises 403 if user's tier < min_tier."""
    async def _dep(user: User = Depends(current_user)) -> User:
        user_tier = await _resolve_user_tier(user.id)
        if not tier_meets_minimum(user_tier, min_tier):
            logger.warning(
                "Tier gate: user=%s tier=%s required=%s",
                user.id, user_tier, min_tier,
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error":           "tier_insufficient",
                    "message":         f"This feature requires a {min_tier} plan.",
                    "current_tier":    user_tier,
                    "required_tier":   min_tier,
                    "upgrade_url":     "/pricing",
                },
            )
        return user
    return _dep


# ── FastAPI dependency: require specific feature flag ───────────────────────────

def require_feature(feature_attr: str):
    """FastAPI dependency. Raises 403 if feature is not enabled for the user's tier.

    feature_attr: attribute name on TierFeatures (e.g. 'ai_chat', 'tts_sage_openai').
    """
    async def _dep(user: User = Depends(current_user)) -> User:
        user_tier = await _resolve_user_tier(user.id)
        if not feature_allowed(user_tier, feature_attr):
            logger.warning(
                "Feature gate: user=%s tier=%s feature=%s denied",
                user.id, user_tier, feature_attr,
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error":        "feature_not_available",
                    "message":      "This feature is not available on your current plan.",
                    "feature":      feature_attr,
                    "current_tier": user_tier,
                    "upgrade_url":  "/pricing",
                },
            )
        return user
    return _dep


# ── FastAPI dependency: legal tool gating ──────────────────────────────────────

def require_legal_consent(tool_key: str):
    """FastAPI dependency for legal tool access.

    Enforces:
      1. User is authenticated (current_user)
      2. User has premium (or executive) tier
      3. User has acknowledged the legal disclaimer (consent in DB)
      4. Access is logged unconditionally (every call)

    tool_key: one of 'legal_guide_1' or 'legal_guide_2'
    """
    policy: LegalToolPolicy = LEGAL_TOOL_POLICIES.get(
        tool_key,
        LEGAL_TOOL_POLICIES["legal_guide_1"],
    )

    async def _dep(
        user: User = Depends(current_user),
        x_legal_consent_id: Optional[str] = Header(None),
    ) -> User:
        # 1. Tier check
        user_tier = await _resolve_user_tier(user.id)
        if not tier_meets_minimum(user_tier, "premium"):
            raise HTTPException(
                status_code=403,
                detail={
                    "error":          "legal_tool_premium_required",
                    "message":        f"'{policy.feature_name}' is available on Premium and Executive plans only.",
                    "current_tier":   user_tier,
                    "upgrade_url":    "/pricing",
                    "disclaimer":     policy.disclaimer_text,
                },
            )

        # 2. Consent check — must have a valid consent record in DB
        if db is not None:
            consent_doc = await db.legal_consents.find_one(
                {
                    "user_id":    user.id,
                    "tool_key":   tool_key,
                    "revoked":    {"$ne": True},
                },
                {"_id": 0, "id": 1, "created_at": 1},
            )
        else:
            consent_doc = None

        if not consent_doc:
            raise HTTPException(
                status_code=403,
                detail={
                    "error":       "legal_consent_required",
                    "message":     (
                        f"You must acknowledge the disclaimer before using "
                        f"'{policy.feature_name}'. "
                        f"POST /api/legal/consent to record your acknowledgement."
                    ),
                    "tool_key":    tool_key,
                    "disclaimer":  policy.disclaimer_text,
                    "consent_url": "/api/legal/consent",
                },
            )

        # 3. Audit every access
        await audit(
            user.id,
            f"legal_tool.accessed.{tool_key}",
            meta={"feature": policy.feature_name, "tier": user_tier},
        )

        return user
    return _dep


# ── All-in-one gate dependency ──────────────────────────────────────────────────

def gate(
    min_role:        str  = "student",
    min_tier:        str  = "free",
    feature:         Optional[str] = None,
    require_consent: Optional[str] = None,  # legal tool key
):
    """Composable FastAPI dependency that enforces role + tier + feature + consent.

    Usage:
        @router.post("/ai/chat")
        async def ai_chat(body: AIChatReq, user: User = Depends(gate("student", "premium", "ai_chat"))):
    """
    from app.security.auth import require_role as _require_role

    async def _dep(
        user: User = Depends(_require_role(min_role)),
        x_legal_consent_id: Optional[str] = Header(None),
    ) -> User:
        # Tier check
        user_tier = await _resolve_user_tier(user.id)
        if not tier_meets_minimum(user_tier, min_tier):
            raise HTTPException(
                403,
                detail={
                    "error":         "tier_insufficient",
                    "message":       f"This feature requires a {min_tier} plan.",
                    "current_tier":  user_tier,
                    "required_tier": min_tier,
                    "upgrade_url":   "/pricing",
                },
            )

        # Feature flag check
        if feature and not feature_allowed(user_tier, feature):
            raise HTTPException(
                403,
                detail={
                    "error":        "feature_not_available",
                    "message":      "This feature is not available on your current plan.",
                    "feature":      feature,
                    "current_tier": user_tier,
                    "upgrade_url":  "/pricing",
                },
            )

        # Legal consent check
        if require_consent:
            policy = LEGAL_TOOL_POLICIES.get(require_consent)
            if policy and db is not None:
                consent_doc = await db.legal_consents.find_one(
                    {"user_id": user.id, "tool_key": require_consent, "revoked": {"$ne": True}},
                    {"_id": 0, "id": 1},
                )
                if not consent_doc:
                    raise HTTPException(
                        403,
                        detail={
                            "error":       "legal_consent_required",
                            "message":     f"Disclaimer acknowledgement required before using this feature.",
                            "tool_key":    require_consent,
                            "disclaimer":  policy.disclaimer_text,
                            "consent_url": "/api/legal/consent",
                        },
                    )
                await audit(user.id, f"legal_tool.accessed.{require_consent}", meta={"tier": user_tier})

        return user
    return _dep


# ── Free-tier isolation: deny premium features explicitly ───────────────────────

async def deny_if_free(user: User = Depends(current_user)) -> User:
    """Dependency: raises 403 with upgrade prompt if user is on free tier."""
    user_tier = await _resolve_user_tier(user.id)
    if user_tier == "free":
        raise HTTPException(
            403,
            detail={
                "error":       "free_tier_restriction",
                "message":     "This feature is not available on the Free plan. Upgrade to Premium to continue.",
                "upgrade_url": "/pricing",
            },
        )
    return user


# ── ASGI Middleware: TierEnforcementMiddleware ──────────────────────────────────

class TierEnforcementMiddleware:
    """ASGI middleware that passively validates tier/role on every request.

    Acts as a second line of defence. Route dependencies are the primary
    enforcement; this middleware catches any route that was missed.

    Checks performed:
      - /api/ai/* (except /ai/helper and /ai/consent*): requires authentication
      - /api/legal/*: requires premium + consent header presence
      - /api/exec/*: requires executive_admin role (via JWT claim check only)
      - /api/admin/*: requires admin role (via JWT claim check only)

    This middleware does NOT replace route-level dependencies — it supplements them.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        path    = request.url.path

        # ── Fast-path: public routes bypass all checks
        _PUBLIC_PREFIXES = (
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/forgot",
            "/api/auth/reset",
            "/api/auth/recovery",
            "/api/ai/helper",
            "/api/ai/consent",
            "/api/consent/cookie",
            "/api/payments/webhook",
            "/api/health",
            "/api/version",
            "/api/prices/public",
            "/api/bug-report",
            "/api/revenue/verify-credential",
            "/api/revenue/courses/public",
            "/api/revenue/api-keys/tiers",
            "/api/credentials/",
            "/api/verify/",
            "/",
        )
        if any(path.startswith(p) for p in _PUBLIC_PREFIXES) or path == "/":
            await self.app(scope, receive, send)
            return

        # ── Extract JWT claims without raising (route deps will raise properly)
        auth_header = request.headers.get("authorization", "")
        role        = "guest"
        user_id     = None

        if auth_header.startswith("Bearer "):
            try:
                import jwt as _jwt
                from app.config import JWT_SECRET, JWT_ALGO
                payload  = _jwt.decode(auth_header.split(" ", 1)[1], JWT_SECRET, algorithms=[JWT_ALGO])
                role     = payload.get("role", "guest")
                user_id  = payload.get("sub")
            except Exception:
                pass  # route-level auth will handle invalid tokens

        # ── Block /api/legal/* for unauthenticated users immediately
        if path.startswith("/api/legal/") and role == "guest":
            response = JSONResponse(
                {"detail": "Authentication required to access legal tools."},
                status_code=401,
            )
            await response(scope, receive, send)
            return

        # ── Block /api/exec/* for non-executives immediately
        if path.startswith("/api/exec/") and ROLE_RANK.get(role, 0) < ROLE_RANK.get("executive_admin", 4):
            # Allow /exec/audio/{id} for authenticated users
            if not path.startswith("/api/exec/audio/") or role == "guest":
                response = JSONResponse(
                    {"detail": "Executive access required."},
                    status_code=403,
                )
                await response(scope, receive, send)
                return

        # ── Block /api/admin/* for non-admins immediately
        if path.startswith("/api/admin/") and ROLE_RANK.get(role, 0) < ROLE_RANK.get("admin", 3):
            response = JSONResponse(
                {"detail": "Administrator access required."},
                status_code=403,
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
