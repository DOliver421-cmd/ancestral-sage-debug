"""soup_gate.py — server-side byte gate for "The Soup" (Mini More Help Center).

WHY THIS EXISTS
    The Soup's files are static assets under /mini-more-help-center/, so their
    raw URLs were reachable by anyone — logged in or not — while the tier gate
    lived only in the React launcher (frontend/src/pages/LegacyTool.jsx). A
    UI-only gate is decoration: the bytes were one URL away. This middleware
    gates the bytes themselves.

WHAT IT ENFORCES (the policy — security/feature_control.py is the source)
    SOUP_FILE_FEATURES maps each file to its feature; SOUP_MIN_TIER maps each
    feature to its minimum tier; load_soup_tier_requirements overlays the
    exec console's db.authz_matrix edits, so an executive can retier any Soup
    surface from the console without a code change. Unknown files under the
    prefix are a 404 (never a leak).

AUTHENTICATION
    Authorization: Bearer <token> (the app's normal mechanism), or the scoped
    session cookie (security/session_cookie.py) — the Soup's own pages make
    same-origin fetch() calls without the header and cannot be edited to add
    one, and an iframe's document navigation cannot carry the header either.

OWNER / EXECUTIVE BYPASS
    admin and executive_admin roles bypass every Soup tier. No part of this
    platform is ever locked away from its owner.

SAFE-DEFAULT CONTRACT
    Same shape as the Feature Control gate: absent policy == allow for a known
    file at its documented tier; a policy store that cannot be read is a 503,
    never an allow; a malformed/unverifiable credential is a 401 left to the
    same JWT verification the /api surface uses.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional, Tuple, Type

from fastapi import Request
from fastapi.responses import JSONResponse

# The Soup is document navigation (iframe src / direct URL), not XHR: the
# browser sends no Authorization header there, which is exactly why the scoped
# cookie exists. GET and HEAD are the only methods that fetch an asset.
_SOUP_METHODS = {"GET", "HEAD"}


def _cookie_from(request: Request) -> Optional[str]:
    # Imported lazily so this module never hard-depends on FastAPI's Response
    # machinery at import time (tests import this module directly).
    from security.session_cookie import read_session_cookie
    return read_session_cookie(request)


async def soup_gate_verdict(
    db,
    path: str,
    auth_header: str,
    cookie_token: Optional[str],
    jwt_secret: str,
    jwt_algo: str,
    user_cls: Type,
) -> Optional[Tuple[int, str]]:
    """Return ``(status_code, detail)`` to reject *path*, or ``None`` to allow.

    *db*        — Motor database handle (None before binding).
    *user_cls*  — Pydantic user model used to rebuild the user from its document.
    """
    from security import feature_control as fc

    feature = fc.soup_feature_for_path(path)
    if feature is None:
        # Unknown file under the Soup prefix: do not confirm what exists.
        return (404, "Not Found")

    token = None
    if (auth_header or "").startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip() or None
    token = token or cookie_token
    if not token:
        return (401, "Sign in to open the Soup.")

    try:
        import jwt as _jwt
        payload = _jwt.decode(token, jwt_secret, algorithms=[jwt_algo])
    except Exception:
        return (401, "Your session has expired — sign in again to open the Soup.")

    sub = payload.get("sub")
    if not sub or db is None:
        return (503, "Soup authorization unavailable — request rejected.")

    try:
        udoc = await db.users.find_one({"id": sub}, {"_id": 0, "password_hash": 0})
    except Exception:
        return (503, "Soup authorization unavailable — request rejected.")
    if not udoc:
        return (401, "Your session is no longer valid — sign in again to open the Soup.")
    if udoc.get("is_active") is False:
        return (403, "This account has been deactivated.")

    # token_version revocation — the same check current_user() applies to the
    # header path, so a revoked session cannot keep fetching Soup bytes.
    try:
        _tv = int(payload.get("tv", 0) or 0)
    except Exception:
        _tv = 0
    if _tv < int(udoc.get("token_version", 0) or 0):
        return (401, "Your session was revoked — sign in again to open the Soup.")

    try:
        user = user_cls(**udoc)
    except Exception:
        return (503, "Soup authorization unavailable — user identity could not be resolved.")

    action, detail = await fc.check_soup_file_access(db, user, path)
    if action == "allow":
        return None
    if action == "missing":
        return (404, "Not Found")
    if action == "unavailable":
        return (503, detail)
    return (403, detail)


def make_soup_gate_middleware(
    get_db: Callable[[], Any],
    get_jwt_secret: Callable[[], str],
    get_jwt_algo: Callable[[], str],
    get_user_cls: Callable[[], Type],
) -> Callable[[Request, Awaitable], Awaitable[Any]]:
    """Build the ``@app.middleware("http")``-compatible Soup byte gate.

    Lazy providers mirror security/fcc_middleware.py: db / JWT_* / User all
    resolve at request time, after the whole server module has loaded.
    """

    async def soup_gate_http_middleware(request: Request, call_next):
        from security import feature_control as _fc
        path = request.url.path
        if not path.startswith(_fc.SOUP_PATH_PREFIX):
            return await call_next(request)
        method = (request.method or "GET").upper()
        if method not in _SOUP_METHODS:
            return JSONResponse(
                status_code=405,
                content={"detail": "Method Not Allowed"},
                headers={"cache-control": "no-store"},
            )

        verdict = await soup_gate_verdict(
            db=get_db(),
            path=path,
            auth_header=request.headers.get("authorization") or "",
            cookie_token=_cookie_from(request),
            jwt_secret=get_jwt_secret(),
            jwt_algo=get_jwt_algo(),
            user_cls=get_user_cls(),
        )
        if verdict is None:
            return await call_next(request)
        status, detail = verdict
        return JSONResponse(
            status_code=status,
            content={"detail": detail, "error": "SOUP_GATE_ENFORCED"},
            headers={"cache-control": "no-store"},
        )

    return soup_gate_http_middleware
