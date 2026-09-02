"""
fcc_middleware.py — Feature Control Center enforcement middleware.

The Feature Control Center (backend/routers/features.py) WRITES feature control
records to MongoDB (db.feature_configs), and the exec consoles write platform
flags (db.platform_flags), page-access gates (db.page_access), per-user
overrides (db.user_feature_overrides) and the tier matrix (db.authz_matrix).
This middleware is the READ side that turns those records into server-side
rules on every /api request.  Without this layer an admin toggle updates a
record but nothing on the backend routing engine changes — the exact defect
the Feature Control Center spec forbids.

Enforcement order (mirrors security/feature_control.py):

  1. check_request_config()  — exec platform flags + page-access gates
  2. check_user_feature_access() — per-user overrides, FCC config
     (enabled / internal_only / customer_access_allowed / roles / tiers) and
     the DB-backed authorization tier matrix

Safe-default contract:
  absent config == allow; a mapped request whose policy store cannot be read
  is rejected with 503 — an unreadable policy store is never permission.

Why factory functions instead of module globals: server.py binds `db` and the
auth internals at startup, and importing *server* from this module at
middleware-construction time would create a circular import.  The factory
receives lazy providers and is registered with ``@app.middleware("http")``,
so the gate runs before every handler without touching the app object.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional, Tuple, Type

from fastapi import Request
from fastapi.responses import JSONResponse

# Public by design: the frontend shell reads this unsigned-in visitor for nav
# gating.  It must stay reachable even when the Feature Control page is swept
# (exec page-access gate "feature-control" covers /api/features).
_PUBLIC_GATE_MAP_PATH = "/api/features/gate-map"


async def fcc_enforce_request(
    db,
    path: str,
    auth_header: str,
    jwt_secret: str,
    jwt_algo: str,
    user_cls: Type,
) -> Optional[Tuple[int, str]]:
    """Return ``(status_code, detail)`` to reject *path*, or ``None`` to allow.

    *db*         — Motor database handle (may be None before binding).
    *user_cls*   — Pydantic user model used to rebuild the user from the DB
                   document (server.User).
    """
    from security import feature_control as _fc

    # 1) Exec platform flags + page-access gates (stateless policy docs).
    #    The gate map is exempt: it is the public navigation contract.
    if path != _PUBLIC_GATE_MAP_PATH:
        verdict = await _fc.check_request_config(db, path)
        if verdict is not None:
            return verdict

    # 2) Per-user FCC enforcement.  Runs only when a Bearer token is present;
    #    anonymous visitors keep the host's own auth behavior.  A malformed or
    #    unverifiable token is left to the handler's auth dependency (401),
    #    never judged here.
    if not (auth_header or "").startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        import jwt as _jwt

        payload = _jwt.decode(token, jwt_secret, algorithms=[jwt_algo])
    except Exception:
        return None
    sub = payload.get("sub")
    if not sub or db is None:
        return None
    try:
        udoc = await db.users.find_one(
            {"id": sub}, {"_id": 0, "password_hash": 0}
        )
    except Exception:
        # The policy store cannot be verified on a mapped request — but the
        # handler's own dependency will produce the authoritative 401/403/200
        # for identity; only claim 503 when identity is provable, below.
        return None
    if not udoc or udoc.get("is_active") is False:
        return None
    try:
        user = user_cls(**udoc)
    except Exception:
        # The identity exists and the token verifies, but the user document
        # cannot be mapped to the application's user model.  Never skip
        # enforcement silently on a provable identity — that is the exact
        # silent-bypass pattern the Feature Control Center contract forbids.
        return (503, "Access control unavailable — user identity could not be resolved.")
    action, detail = await _fc.check_user_feature_access(db, user, path)
    if action == "block":
        return (403, detail)
    if action == "unavailable":
        return (503, detail)
    return None


def make_fcc_middleware(
    get_db: Callable[[], Any],
    get_jwt_secret: Callable[[], str],
    get_jwt_algo: Callable[[], str],
    get_user_cls: Callable[[], Type],
) -> Callable[[Request, Awaitable], Awaitable[Any]]:
    """Build the ``@app.middleware("http")``-compatible gate.

    Lazy providers avoid a hard import of *server* at construction time.
    """

    async def fcc_http_middleware(request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)
        method = (request.method or "GET").upper()
        if method == "OPTIONS":  # CORS preflight passes through
            return await call_next(request)

        verdict = await fcc_enforce_request(
            db=get_db(),
            path=path,
            auth_header=request.headers.get("authorization") or "",
            jwt_secret=get_jwt_secret(),
            jwt_algo=get_jwt_algo(),
            user_cls=get_user_cls(),
        )
        if verdict is None:
            return await call_next(request)
        status, detail = verdict
        return JSONResponse(
            status_code=status,
            content={"detail": detail, "error": "ACCESS_ENFORCED"},
            headers={"cache-control": "no-store"},
        )

    return fcc_http_middleware