"""
Shared FastAPI dependencies for routers that live outside server.py.
Provides JWT auth and db access without creating circular imports.
"""
import os
from fastapi import Header, HTTPException
from typing import Optional

import jwt as _jwt
from motor.motor_asyncio import AsyncIOMotorDatabase

# Resolved at import time — same env vars server.py uses
_JWT_SECRET = os.environ.get("JWT_SECRET", "")
_JWT_ALGO   = os.environ.get("JWT_ALGORITHM", "HS256")

# db reference injected by server.py on startup via deps.set_db(db)
_db: Optional[AsyncIOMotorDatabase] = None


def set_db(database: AsyncIOMotorDatabase) -> None:
    """Called once from server._on_startup_impl() to wire up the db."""
    global _db
    _db = database


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialised yet")
    return _db


async def require_user(authorization: Optional[str] = Header(None)) -> dict:
    """JWT dependency usable in any router — mirrors server.py current_user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = _jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGO])
    except _jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    db = get_db()
    user_doc = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(401, "User not found")
    if user_doc.get("is_active") is False:
        raise HTTPException(403, "Account deactivated")
    return user_doc
