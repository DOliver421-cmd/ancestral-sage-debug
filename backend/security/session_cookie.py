"""session_cookie.py — the scoped session cookie for the Soup bundle.

The platform authenticates API calls with a Bearer token in the Authorization
header (frontend localStorage key ``lce_token``).  That works for the React
app, but NOT for the Soup:

  * an iframe's plain document navigation cannot carry the header, and
  * the Soup's original HTML files make same-origin fetch() calls WITHOUT the
    header (soup-partner.html posts to /api/partner and /api/config).

Those files are read-only content — they must never be edited to add a token —
so login/register ALSO issue the same JWT in an httpOnly cookie.  The browser
then attaches it automatically to iframe navigations and to same-origin
fetch() calls, and both surfaces work unmodified.

SCOPE (owner decision 2026-10-11) — deliberate and narrow:

  the cookie is accepted ONLY by
    * the /mini-more-help-center/* file gate (security/soup_gate.py), and
    * the five Soup partner routes (routers/soup_partner.py).

No other endpoint reads it: the Authorization header remains the one auth
mechanism for the /api surface.  httpOnly (page scripts cannot read it),
SameSite=Lax (not sent on cross-site requests), Secure when the deployment is
HTTPS.  The cookie carries no extra privilege — it is the same signed JWT the
Authorization header carries, with the same token_version revocation checks.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Request, Response

COOKIE_NAME = "lce_session"


def _secure_flag() -> bool:
    """Secure the cookie whenever the deployment is not plainly local.

    Railway serves HTTPS, and a Secure cookie is simply ignored by browsers on
    http://localhost — so this defaults to on unless the operator explicitly
    runs plain-HTTP local development.
    """
    return os.environ.get("SESSION_COOKIE_SECURE", "0" if os.environ.get("DEV_LOCAL_HTTP") else "1") != "0"


def issue_session_cookie(response: Response, token: str) -> None:
    """Attach the session cookie carrying *token* (the issued JWT)."""
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=60 * 60 * 24 * 7,   # 7 days, matching the token lifetime
        httponly=True,
        samesite="lax",
        secure=_secure_flag(),
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def read_session_cookie(request: Request) -> Optional[str]:
    """The raw cookie value, or None when absent/empty."""
    try:
        value = request.cookies.get(COOKIE_NAME)
    except Exception:
        return None
    return value or None
