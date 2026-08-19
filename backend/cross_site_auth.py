"""cross_site_auth.py — Cross-site SSO between WAI Institute and M.O.R.E. Help Center.

Allows a user logged into one site to access the partner site without
re-entering credentials.  Both sites share a JWT secret (JWT_SECRET env var)
and a cross-site signing key (CROSS_SITE_SECRET env var).

Flow:
  1. User is logged into wai-institute.org
  2. User clicks "Open in M.O.R.E. Help Center"
  3. Frontend calls GET /api/auth/cross-site-token on wai-institute.org
  4. Backend generates a short-lived (5 min) cross-site token containing
     the user's identity (id, email, full_name, role)
  5. Frontend redirects to morehelp.center/auth/cross-site?token=<token>
  6. morehelp.center's /api/auth/cross-site-login validates the token,
     finds or creates the local user, and returns a session token
  7. Frontend stores the new token and navigates to the intended page

Security:
  - Cross-site tokens are signed with CROSS_SITE_SECRET (separate from JWT)
  - Tokens are single-use (consumed on validation)
  - Tokens expire after 5 minutes
  - The partner site must be in ALLOWED_PARTNER_DOMAINS
  - Tokens contain only identity data (no password, no session state)
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("lcewai.cross_site_auth")

# ── Config ───────────────────────────────────────────────────────────────────

CROSS_SITE_SECRET = os.environ.get("CROSS_SITE_SECRET", "")

# Token validity window (seconds)
TOKEN_TTL = 300  # 5 minutes

# Allowed partner domains (for redirect validation)
ALLOWED_PARTNER_DOMAINS = {
    "www.wai-institute.org",
    "wai-institute.org",
    "www.morehelp.center",
    "morehelp.center",
}

# Partner site API base URLs
PARTNER_API_BASE = {
    "www.wai-institute.org": os.environ.get("WAI_API_BASE", "https://www.wai-institute.org/api"),
    "morehelp.center": os.environ.get("MORE_API_BASE", "https://www.morehelp.center/api"),
    "www.morehelp.center": os.environ.get("MORE_API_BASE", "https://www.morehelp.center/api"),
}


def _sign(payload: str) -> str:
    """HMAC-SHA256 signature."""
    if not CROSS_SITE_SECRET:
        raise ValueError("CROSS_SITE_SECRET not configured")
    return hmac.new(CROSS_SITE_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def generate_cross_site_token(user_id: str, email: str, full_name: str, role: str) -> str:
    """Generate a short-lived cross-site token.

    The token is a signed JSON payload: base64(payload).signature
    """
    payload = {
        "uid": user_id,
        "email": email,
        "name": full_name,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_TTL,
        "nonce": secrets.token_hex(16),
    }
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")))
    sig = _sign(payload_b64)
    return f"{payload_b64}.{sig}"


def validate_cross_site_token(token: str) -> Optional[dict]:
    """Validate a cross-site token.  Returns the payload dict or None."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts

        # Verify signature
        expected_sig = _sign(payload_b64)
        if not hmac.compare_digest(sig, expected_sig):
            logger.warning("Cross-site token signature mismatch")
            return None

        # Decode and check expiry
        payload = json.loads(_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            logger.warning("Cross-site token expired")
            return None

        return payload
    except Exception as e:
        logger.warning("Cross-site token validation failed: %s", e)
        return None


def is_valid_partner_domain(domain: str) -> bool:
    """Check if a domain is an allowed partner."""
    return domain.lower().strip("/") in ALLOWED_PARTNER_DOMAINS


def get_partner_api_base(domain: str) -> Optional[str]:
    """Get the API base URL for a partner domain."""
    return PARTNER_API_BASE.get(domain.lower().strip("/"))


# ── Base64 helpers (url-safe, no padding) ────────────────────────────────────

import base64

def _b64encode(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode()).rstrip(b"=").decode()

def _b64decode(data: str) -> str:
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode()).decode()
