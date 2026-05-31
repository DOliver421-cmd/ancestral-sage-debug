"""app/routes/notifications.py — Notification endpoints.

Extracted from backend/server.py lines 5946–5989.
No logic changed.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from app.database import db
from app.models.user import User
from app.security.auth import current_user

logger = logging.getLogger("lcewai")

router = APIRouter()

try:
    from seed import CREDENTIALS
except ImportError:
    CREDENTIALS: list = []


@router.get("/notifications/me")
async def my_notifications(user: User = Depends(current_user)):
    now = datetime.now(timezone.utc)
    soon = (now + timedelta(days=30)).isoformat()
    creds = await db.user_credentials.find(
        {"user_id": user.id, "expires_at": {"$lte": soon, "$gt": now.isoformat()}}, {"_id": 0}
    ).to_list(50)
    cred_map = {c["key"]: c for c in CREDENTIALS}
    for c in creds:
        existing = await db.notifications.find_one(
            {"user_id": user.id, "kind": "warning", "meta.credential_id": c["id"]}, {"_id": 0}
        )
        if not existing:
            cred_def = cred_map.get(c["credential_key"])
            await db.notifications.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "title": "Credential expires soon",
                "body": f"{cred_def['name'] if cred_def else c['credential_key']} expires {c['expires_at'][:10]}. Renew with the next compliance quiz.",
                "link": "/credentials",
                "kind": "warning",
                "meta": {"credential_id": c["id"]},
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
    docs = await db.notifications.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    unread = sum(1 for d in docs if not d["read"])
    return {"items": docs, "unread": unread}


@router.post("/notifications/{nid}/read")
async def mark_read(nid: str, user: User = Depends(current_user)):
    await db.notifications.update_one({"id": nid, "user_id": user.id}, {"$set": {"read": True}})
    return {"ok": True}


@router.post("/notifications/read-all")
async def mark_all_read(user: User = Depends(current_user)):
    await db.notifications.update_many({"user_id": user.id, "read": False}, {"$set": {"read": True}})
    return {"ok": True}
