"""app/routes/compliance.py — Compliance module routes.

Extracted from backend/server.py lines 5683–5739.
No logic changed.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.database import db
from app.models.user import User
from app.security.auth import current_user

logger = logging.getLogger("lcewai")

router = APIRouter()


async def _award_credentials(user_id: str):
    from app.routes.credentials import award_credentials
    await award_credentials(user_id)


@router.get("/compliance")
async def list_compliance(user: User = Depends(current_user)):
    docs = await db.compliance_modules.find({}, {"_id": 0}).sort("order", 1).to_list(50)
    progress = await db.compliance_progress.find({"user_id": user.id}, {"_id": 0}).to_list(50)
    pmap = {p["module_slug"]: p for p in progress}
    for d in docs:
        d["my_progress"] = pmap.get(d["slug"])
    return docs


@router.get("/compliance/{slug}")
async def get_compliance(slug: str, user: User = Depends(current_user)):
    doc = await db.compliance_modules.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Compliance module not found")
    doc["my_progress"] = await db.compliance_progress.find_one(
        {"user_id": user.id, "module_slug": slug}, {"_id": 0}
    )
    return doc


@router.post("/compliance/{slug}/quiz")
async def submit_compliance_quiz(slug: str, body: dict, user: User = Depends(current_user)):
    mod = await db.compliance_modules.find_one({"slug": slug}, {"_id": 0})
    if not mod:
        raise HTTPException(404, "Module not found")
    answers = body.get("answers", [])
    quiz = mod.get("quiz", [])
    if len(answers) != len(quiz):
        raise HTTPException(400, "Answer count mismatch")
    correct = sum(1 for i, q in enumerate(quiz) if q["answer"] == answers[i])
    score = correct / len(quiz) * 100 if quiz else 0
    pass_pct = 80 if slug == "loto-certification" else 70
    status_val = "completed" if score >= pass_pct else "in_progress"
    now = datetime.now(timezone.utc)
    expires_at = None
    if status_val == "completed" and mod.get("expires_months"):
        expires_at = (now + timedelta(days=30 * mod["expires_months"])).isoformat()
    update = {
        "user_id": user.id,
        "module_slug": slug,
        "status": status_val,
        "quiz_score": score,
        "completed_at": now.isoformat() if status_val == "completed" else None,
        "expires_at": expires_at,
        "hours_logged": mod.get("hours", 0) if status_val == "completed" else 0,
        "updated_at": now.isoformat(),
    }
    await db.compliance_progress.update_one(
        {"user_id": user.id, "module_slug": slug},
        {"$set": update, "$setOnInsert": {"id": str(uuid.uuid4())}},
        upsert=True,
    )
    if status_val == "completed":
        await _award_credentials(user.id)
    return {"score": score, "correct": correct, "total": len(quiz), "status": status_val, "pass_pct": pass_pct, "expires_at": expires_at}
