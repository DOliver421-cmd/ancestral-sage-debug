"""app/routes/incidents.py — Incident reporting and resolution endpoints.

Extracted from backend/server.py lines 6143–6202.
No logic changed.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import db
from app.models.user import User
from app.security.auth import current_user, require_role
from app.utils.audit import audit

logger = logging.getLogger("lcewai")

router = APIRouter()


class IncidentReq(BaseModel):
    type: Literal["near_miss", "first_aid", "injury", "property_damage", "safety_violation", "other"]
    severity: Literal["low", "medium", "high", "critical"] = "low"
    description: str
    site_slug: Optional[str] = None
    photo_url: Optional[str] = None
    involved_user_ids: List[str] = []


@router.post("/incidents")
async def report_incident(body: IncidentReq, user: User = Depends(current_user)):
    doc = {
        "id": str(uuid.uuid4()),
        "type": body.type,
        "severity": body.severity,
        "description": body.description,
        "site_slug": body.site_slug,
        "photo_url": body.photo_url,
        "involved_user_ids": body.involved_user_ids,
        "reported_by": user.id,
        "status": "open",
        "resolution": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resolved_at": None,
    }
    await db.incidents.insert_one(doc)
    await audit(user.id, "incident.reported", target=doc["id"], meta={"type": body.type, "severity": body.severity})
    doc.pop("_id", None)
    return doc


@router.get("/incidents")
async def list_incidents(status: Optional[str] = None, user: User = Depends(require_role("instructor", "admin"))):
    q = {"status": status} if status else {}
    docs = await db.incidents.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
    user_ids = list({d["reported_by"] for d in docs} | {u for d in docs for u in d.get("involved_user_ids", [])})
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(1000)
    umap = {u["id"]: u for u in users}
    for d in docs:
        d["reporter"] = umap.get(d["reported_by"])
        d["involved"] = [umap.get(uid) for uid in d.get("involved_user_ids", []) if umap.get(uid)]
    return docs


@router.post("/incidents/{iid}/resolve")
async def resolve_incident(iid: str, payload: dict, user: User = Depends(require_role("admin"))):
    resolution = (payload.get("resolution") or "").strip()
    if not resolution:
        raise HTTPException(400, "resolution required")
    await db.incidents.update_one(
        {"id": iid},
        {"$set": {
            "status": "resolved",
            "resolution": resolution,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    await audit(user.id, "incident.resolved", target=iid)
    return {"ok": True}
