"""app/security/auth.py — JWT token creation and user dependency functions.

Extracted from backend/server.py lines 806–866.
No logic changed.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException

from app.config import JWT_SECRET, JWT_ALGO, JWT_EXPIRE_HOURS, ROLE_RANK
from app.database import db
from app.models.user import User

logger = logging.getLogger("lcewai")


def make_token(user_id: str, role: str, extra: Optional[dict] = None, token_version: int = 0) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": user_id, "role": role, "exp": exp, "tv": token_version}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


async def current_user(authorization: Optional[str] = Header(None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    user_doc = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(401, "User not found")
    if user_doc.get("is_active") is False:
        raise HTTPException(403, "Account deactivated")
    # Token version check — revoked when user calls DELETE /auth/sessions (all)
    # or when an admin forcibly invalidates tokens.
    db_tv = user_doc.get("token_version", 0)
    token_tv = payload.get("tv", 0)
    if token_tv < db_tv:
        raise HTTPException(401, "Token has been revoked. Please log in again.")
    return User(**user_doc)


def require_role(*roles):
    """Authorize the current user against a hierarchy."""
    needed_rank = min(ROLE_RANK[r] for r in roles)

    async def dep(user: User = Depends(current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            logger.warning(
                "Unauthorized access attempt — insufficient privileges (user=%s, role=%s)",
                user.id, user.role,
            )
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


def assert_role(user: User, *roles) -> None:
    """Inline authorization check (raises 403 if the user lacks the rank)."""
    needed_rank = min(ROLE_RANK[r] for r in roles)
    if ROLE_RANK.get(user.role, 0) < needed_rank:
        raise HTTPException(403, "Insufficient permissions to access this resource.")


def can_modify(actor: User, target_role: str) -> bool:
    """Returns True iff `actor` is allowed to modify a user with `target_role`."""
    actor_rank  = ROLE_RANK.get(actor.role, 0)
    target_rank = ROLE_RANK.get(target_role, 0)
    return actor_rank >= target_rank
