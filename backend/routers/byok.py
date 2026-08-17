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
ROLE_RANK = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4, "creative_partner": 2}
Role = Literal["student", "instructor", "admin", "executive_admin", "creative_partner"]


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

    return await get_byok_status(db, user.id)


@router.post("/byok/activate")
async def byok_activate(user: User = Depends(_dep_current_user)):
    """Activate the $3 BYOK entitlement.

    This is the post-payment hook — production wires it to a successful
    Stripe/Lemon Squeezy checkout (see docs/ADMIN-MANUAL.md §7). Until then it
    enables the entitlement directly and records an audit row.
    """
    from byok import activate_byok, BYOK_PRICE_USD

    result = await activate_byok(db, user.id)
    await audit(user.id, "byok.activated", meta={"price_usd": BYOK_PRICE_USD})
    return result


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
