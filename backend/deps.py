"""deps.py — Shared FastAPI dependencies for auth and authorization.

Every router currently re-implements _require_rank() and _dep_current_user()
because of the bind() pattern.  This module provides the canonical versions
so routers can import them instead of duplicating.

Usage in a router:

    from deps import dep_current_user, require_rank

    @router.get("/my-endpoint")
    async def my_endpoint(user: User = Depends(require_rank("admin"))):
        ...

    @router.get("/auth-only")
    async def auth_only(user: User = Depends(dep_current_user)):
        ...
"""

import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException

from roles import role_rank, normalize_role, Role

logger = logging.getLogger("lcewai.deps")

# These are set by server.py at startup via bind().
# Routers that haven't migrated yet still use their local copies —
# this module is the canonical target.
_current_user_fn = None
_audit_fn = None
_check_rate_fn = None
_db = None


def bind(current_user_fn, audit_fn=None, check_rate_fn=None):
    """Called by server.py at startup to inject shared dependencies."""
    global _current_user_fn, _audit_fn, _check_rate_fn
    _current_user_fn = current_user_fn
    _audit_fn = audit_fn
    _check_rate_fn = check_rate_fn


def set_db(db_ref):
    """Called by server.py startup to inject the shared db reference."""
    global _db
    _db = db_ref


def get_db():
    """Return the shared db reference (set by set_db at startup)."""
    return _db


async def dep_current_user(authorization: Optional[str] = Header(None)):
    """Resolve the current user from the Authorization header.

    This is the canonical current_user dependency.  Routers should
    import this instead of re-implementing _dep_current_user.
    """
    if _current_user_fn is None:
        raise HTTPException(503, "Service starting up")
    return await _current_user_fn(authorization)


def require_rank(*min_roles: str):
    """Authorize the current user against a hierarchy.

    Pass if the user's role rank is >= the LOWEST rank among the
    requested roles.  Uses role_rank() which normalizes legacy strings
    via LEGACY_ROLE_MAP.

    Usage:
        @router.get("/admin-only")
        async def admin_only(user: User = Depends(require_rank("admin"))):
            ...

        @router.get("/oversight-or-above")
        async def oversight(user: User = Depends(require_rank("oversight"))):
            ...
    """
    needed = min(role_rank(r) for r in min_roles)

    async def dep(user=Depends(dep_current_user)):
        if role_rank(user.role) < needed:
            logger.warning(
                "Unauthorized — insufficient privileges (user=%s, role=%s, needed_rank=%d)",
                user.id, user.role, needed,
            )
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


def require_tier(min_tier: str):
    """Authorize the current user's feature tier.

    Checks the user's role rank against the minimum required for
    the given feature tier (see roles.TIER_MIN_RANK).

    Usage:
        @router.get("/premium-feature")
        async def premium(user: User = Depends(require_tier("premium"))):
            ...
    """
    needed = role_rank(min_tier) if min_tier in ("student", "trial_pass", "instructor", "support_staff", "oversight", "admin", "executive_admin") else 0

    async def dep(user=Depends(dep_current_user)):
        if role_rank(user.role) < needed:
            raise HTTPException(403, f"This feature requires {min_tier} access or above.")
        return user

    return dep


async def audit_log(actor_id, action, target=None, meta=None):
    """Write an audit log entry.  Wraps server.py's audit() for router use."""
    if _audit_fn:
        await _audit_fn(actor_id, action, target=target, meta=meta)


# Re-export for routers that import require_user expecting the canonical dep.
require_user = dep_current_user


def check_rate(key: str, max_calls: int = 60, window_sec: int = 60):
    """Rate-limit check.  Wraps server.py's check_rate() for router use."""
    if _check_rate_fn:
        _check_rate_fn(key, max_calls=max_calls, window_sec=window_sec)
