"""app/utils/audit.py — Audit logging helper and PII stripping.

Extracted from backend/server.py lines 326–360.
No logic changed.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.database import db

logger = logging.getLogger("lcewai")

_PII_KEYS = {
    "email", "password", "password_hash", "current_password", "new_password",
    "confirm", "full_name", "phone", "address", "ip", "ip_address",
    "user_agent", "token", "access_token", "refresh_token",
}


def _strip_pii(d: dict) -> dict:
    """Return a copy of *d* with PII-field values replaced by ``[REDACTED]``."""
    return {k: "[REDACTED]" if k in _PII_KEYS else v for k, v in d.items()}


async def audit(
    actor_id: Optional[str],
    action: str,
    target: Optional[str] = None,
    meta: Optional[dict] = None,
):
    try:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "actor_id": actor_id,
            "action": action,
            "target": target,
            "meta": _strip_pii(meta or {}),
            "at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.exception("audit failed")


async def notify(
    user_id: str,
    title: str,
    body: str,
    link: Optional[str] = None,
    kind: str = "info",
):
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title,
        "body": body,
        "link": link,
        "kind": kind,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
