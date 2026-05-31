"""app/routes/attendance.py — Attendance recording and reporting endpoints.

Extracted from backend/server.py lines 6078–6140.
No logic changed.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.database import db
from app.models.user import User
from app.security.auth import current_user, require_role
from app.utils.audit import audit

logger = logging.getLogger("lcewai")

router = APIRouter()


@router.post("/attendance")
async def record_attendance(payload: dict, user: User = Depends(require_role("instructor", "admin"))):
    if not payload.get("date") or not payload.get("attendees"):
        raise HTTPException(400, "date and attendees required")
    incoming_ids = [a["user_id"] for a in payload["attendees"] if a.get("user_id")]
    valid = await db.users.find({"id": {"$in": incoming_ids}, "role": "student"}, {"_id": 0, "id": 1}).to_list(1000)
    valid_ids = {v["id"] for v in valid}
    session_id = str(uuid.uuid4())
    docs = []
    for a in payload["attendees"]:
        if a.get("user_id") not in valid_ids:
            continue
        docs.append({
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "user_id": a["user_id"],
            "date": payload["date"],
            "site_slug": payload.get("site_slug"),
            "status": a.get("status", "present"),
            "recorded_by": user.id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    if docs:
        await db.attendance.insert_many(docs)
    await audit(user.id, "attendance.recorded", target=session_id, meta={"count": len(docs)})
    return {"session_id": session_id, "count": len(docs), "skipped": len(payload["attendees"]) - len(docs)}


@router.get("/attendance/me")
async def my_attendance(user: User = Depends(current_user)):
    docs = await db.attendance.find({"user_id": user.id}, {"_id": 0}).sort("date", -1).to_list(500)
    summary = {"present": 0, "absent": 0, "tardy": 0, "excused": 0}
    for d in docs:
        if d["status"] in summary:
            summary[d["status"]] += 1
    total = sum(summary.values())
    rate = round(summary["present"] / max(1, total) * 100, 1)
    return {"records": docs, "summary": summary, "attendance_rate": rate}


@router.get("/attendance/roster")
async def attendance_roster(user: User = Depends(require_role("instructor", "admin"))):
    q = {"role": "student"} if user.role == "admin" else {"role": "student", "associate": user.associate}
    students = await db.users.find(q, {"_id": 0, "password_hash": 0}).to_list(1000)
    user_ids = [s["id"] for s in students]
    records = await db.attendance.find({"user_id": {"$in": user_ids}}, {"_id": 0}).to_list(50000)
    by_user = {}
    for r in records:
        by_user.setdefault(r["user_id"], {"present": 0, "absent": 0, "tardy": 0, "excused": 0})
        s = r["status"]
        if s in by_user[r["user_id"]]:
            by_user[r["user_id"]][s] += 1
    out = []
    for s in students:
        stats = by_user.get(s["id"], {"present": 0, "absent": 0, "tardy": 0, "excused": 0})
        total = sum(stats.values())
        out.append({
            "user_id": s["id"], "full_name": s["full_name"], "associate": s.get("associate"),
            **stats, "total": total,
            "rate": round(stats["present"] / max(1, total) * 100, 1),
        })
    return out
