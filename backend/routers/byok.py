"""routers/byok.py — $3 Bring Your Own Key (BYOK) endpoints.

Let any authenticated user activate the $3 BYOK entitlement, attach a key from
one of three free providers, test it, and remove it. Admin staff get an
aggregate view via /api/byok/admin.

Shared state (db, current_user, audit, assert_role) is bound by server.py via
bind() at include time — no circular imports.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["byok"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = audit = assert_role = None


def bind(_db, _current_user, _audit, _assert_role):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, assert_role
    db = _db
    current_user = _current_user
    audit = _audit
    assert_role = _assert_role


# Mirrors server.py's role hierarchy for runtime require_role checks.
from routers.roles import ROLE_RANK, Role


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
    because require_role is bound after this module loads."""
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: User = Depends(_dep_current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            logger.warning("Unauthorized BYOK admin access (user=%s, role=%s)", user.id, user.role)
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


class ByokKeyReq(BaseModel):
    provider: str
    key: str


@router.get("/byok/status")
async def byok_status(user: User = Depends(_dep_current_user)):
    """Entitlement + configured-provider status. Never returns raw keys."""
    from byok import get_byok_status

    return await get_byok_status(db, user.id, user.role)


@router.post("/byok/activate")
async def byok_activate(user: User = Depends(_dep_current_user)):
    """Activate the $3 BYOK entitlement.

    The $3 unlock is a PAID entitlement. It can only be activated when one of
    these is true:
      1. The user's role is in FREE_BYOK_ROLES (staff/support/instructor
         roles that legitimately receive BYOK free), or
      2. The user holds an admin/executive role (authorized staff grant), or
      3. A paid BYOK order for this user has been recorded by the payment
         webhook (byok_paid=True on the user record).
    Anything else is a 402 — activation is not a free endpoint.
    """
    from byok import activate_byok, byok_price_for, BYOK_PRICE_USD
    from roles import FREE_BYOK_ROLES

    price = byok_price_for(user.role)
    staff_grant = user.role in ("admin", "executive_admin")
    if not staff_grant and price > 0:
        # Non-staff, non-free-role user: require proof of payment.
        user_doc = await db.users.find_one(
            {"id": user.id}, {"_id": 0, "byok_paid": 1}
        )
        if not user_doc or not user_doc.get("byok_paid"):
            raise HTTPException(
                402,
                "BYOK access is a $3 unlock. Complete the checkout on the BYOK page to activate it.",
            )

    result = await activate_byok(db, user.id, user.role)
    await audit(user.id, "byok.activated", meta={"price_usd": result.get("price_usd", BYOK_PRICE_USD)})
    return result


@router.post("/byok/checkout")
async def byok_checkout(user: User = Depends(_dep_current_user)):
    """Start the BYOK unlock for the current user.

    Instructor tier and above activate FREE immediately (price 0) — no
    checkout needed. Users below instructor tier get a $3 checkout session
    through the existing payments pipeline; the payment webhook flips
    byok_enabled once paid. When payments are not configured, falls back to
    direct activation (documented dev/grace path) so the feature never breaks
    — the audit row records the price either way.
    """
    from byok import activate_byok, byok_price_for, BYOK_PRICE_USD

    price = byok_price_for(user.role)
    if price == 0:
        result = await activate_byok(db, user.id, user.role)
        await audit(user.id, "byok.activated", meta={"price_usd": 0, "path": "checkout", "free": True})
        return {**result, "activated": True, "url": None}

    # Below instructor tier → $3 one-time fee via the payments pipeline.
    try:
        from routers.payments import CheckoutReq, create_checkout_session, PAYMENTS_ENABLED

        if PAYMENTS_ENABLED:
            checkout = await create_checkout_session(
                CheckoutReq(product_key="byok", quantity=1), user=user
            )
            url = checkout.get("url") if isinstance(checkout, dict) else None
            if url:
                await audit(user.id, "byok.checkout_created", meta={"price_usd": price})
                return {
                    "activated": False,
                    "price_usd": price,
                    "url": url,
                    "session_id": checkout.get("session_id"),
                }
    except Exception as _ce:
        # Payment provider unavailable — the $3 unlock stays locked. It is a
        # paid entitlement; checkout failure must not silently become a free
        # grant.
        logger.warning("byok: checkout unavailable (%s) — entitlement stays locked", _ce)

    # No grace path: the $3 unlock is a paid entitlement and must not be
    # granted for free when payments are unconfigured. The authorized routes
    # are a configured checkout, a staff/admin grant via /byok/activate, or a
    # FREE_BYOK_ROLES role. Anything else stays locked.
    raise HTTPException(
        501,
        "Payments are not configured, so the $3 BYOK unlock cannot be purchased yet. "
        "Please try again later, or contact support if you believe this is an error.",
    )


@router.post("/byok/key")
async def byok_save_key(body: ByokKeyReq, user: User = Depends(_dep_current_user)):
    """Attach or replace a key for one of the three BYOK providers."""
    from byok import BYOK_PROVIDERS, save_byok_key

    if body.provider not in BYOK_PROVIDERS:
        raise HTTPException(400, f"Unknown BYOK provider: {body.provider}")

    user_doc = await db.users.find_one({"id": user.id}, {"_id": 0, "byok_enabled": 1})
    if not user_doc or not user_doc.get("byok_enabled"):
        raise HTTPException(402, "BYOK access is $3 — activate it before saving a key.")

    try:
        result = await save_byok_key(db, user.id, body.provider, body.key)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    await audit(user.id, "byok.key.saved", meta={"provider": body.provider})
    # Site support keys join the platform's shared free pool immediately.
    if getattr(user, "role", None) == "support_staff":
        try:
            from ai.llm_gateway import reload_shared_byok as _rl_shared
            await _rl_shared(db)
        except Exception:
            pass
    return result


@router.post("/byok/key/{provider}/test")
async def byok_test_key(provider: str, body: ByokKeyReq, user: User = Depends(_dep_current_user)):
    """Make a real 1-token call to verify a key. The key is never stored."""
    from byok import BYOK_PROVIDERS, test_byok_key

    if provider not in BYOK_PROVIDERS:
        raise HTTPException(400, f"Unknown BYOK provider: {provider}")

    result = await test_byok_key(provider, body.key)
    await audit(user.id, "byok.key.tested", meta={"provider": provider, "ok": bool(result.get("ok"))})
    return result


@router.delete("/byok/key/{provider}")
async def byok_remove_key(provider: str, user: User = Depends(_dep_current_user)):
    """Remove a configured key for the given provider."""
    from byok import BYOK_PROVIDERS, remove_byok_key

    if provider not in BYOK_PROVIDERS:
        raise HTTPException(400, f"Unknown BYOK provider: {provider}")

    try:
        removed = await remove_byok_key(db, user.id, provider)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    await audit(user.id, "byok.key.removed", meta={"provider": provider})
    # A removed site support key leaves the platform's shared free pool now.
    if getattr(user, "role", None) == "support_staff":
        try:
            from ai.llm_gateway import reload_shared_byok as _rl_shared
            await _rl_shared(db)
        except Exception:
            pass
    return {"removed": removed}


@router.get("/byok/admin")
async def byok_admin(user: User = Depends(_require_rank("admin"))):
    """Aggregate BYOK adoption stats (admin+)."""
    from byok import BYOK_PRICE_USD

    activated = await db.users.count_documents({"byok_enabled": True})
    configured = await db.user_byok_keys.count_documents({"active": True})
    return {
        "price_usd": BYOK_PRICE_USD,
        "activated_users": activated,
        "configured_keys": configured,
    }
