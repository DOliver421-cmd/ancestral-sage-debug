"""app/routes/modules.py — Modules, progress, quiz, and roster endpoints.

Extracted from backend/server.py lines 1787–1872.
No logic changed.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.database import db
from app.models.curriculum import Module, ProgressEntry, QuizSubmit
from app.models.user import User
from app.security.auth import current_user, require_role

logger = logging.getLogger("lcewai")

router = APIRouter()


# award_credentials and award_xp are imported lazily to avoid circular deps
async def _award_credentials(user_id: str):
    from app.routes.credentials import award_credentials
    await award_credentials(user_id)


async def _award_xp(user_id: str, amount: int, reason: str):
    from app.routes.credentials import award_xp
    await award_xp(user_id, amount, reason)


@router.get("/modules", response_model=List[Module])
async def list_modules():
    docs = await db.modules.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    return [Module(**d) for d in docs]


@router.get("/modules/{slug}", response_model=Module)
async def get_module(slug: str):
    doc = await db.modules.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Module not found")
    return Module(**doc)


@router.get("/progress/me")
async def my_progress(user: User = Depends(current_user)):
    docs = await db.progress.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    return docs


@router.post("/progress/start")
async def start_module(payload: dict, user: User = Depends(current_user)):
    slug = payload.get("module_slug")
    if not slug:
        raise HTTPException(400, "module_slug required")
    existing = await db.progress.find_one({"user_id": user.id, "module_slug": slug}, {"_id": 0})
    if existing:
        return existing
    entry = ProgressEntry(user_id=user.id, module_slug=slug, status="in_progress")
    doc = entry.model_dump()
    doc["updated_at"] = doc["updated_at"].isoformat()
    await db.progress.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.post("/progress/quiz")
async def submit_quiz(body: QuizSubmit, user: User = Depends(current_user)):
    mod = await db.modules.find_one({"slug": body.module_slug}, {"_id": 0})
    if not mod:
        raise HTTPException(404, "Module not found")
    quiz = mod.get("quiz", [])
    if len(body.answers) != len(quiz):
        raise HTTPException(400, "Answer count mismatch")
    correct = sum(1 for i, q in enumerate(quiz) if q["answer"] == body.answers[i])
    score = correct / len(quiz) * 100 if quiz else 0
    status_val = "completed" if score >= 70 else "in_progress"
    completed_at = datetime.now(timezone.utc).isoformat() if status_val == "completed" else None
    update = {
        "user_id": user.id,
        "module_slug": body.module_slug,
        "status": status_val,
        "quiz_score": score,
        "completed_at": completed_at,
        "hours_logged": mod.get("hours", 0) if status_val == "completed" else 0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.progress.update_one(
        {"user_id": user.id, "module_slug": body.module_slug},
        {"$set": update, "$setOnInsert": {"id": str(uuid.uuid4())}},
        upsert=True,
    )
    if status_val == "completed":
        await _award_credentials(user.id)
        await _award_xp(user.id, 100 + max(0, int(score - 70)), f"Module completed: {body.module_slug}")
    return {"score": score, "correct": correct, "total": len(quiz), "status": status_val}


@router.get("/roster")
async def roster(user: User = Depends(require_role("instructor", "admin"))):
    q = {"role": "student"} if user.role == "admin" else {"role": "student", "associate": user.associate}
    students = await db.users.find(q, {"_id": 0, "password_hash": 0}).to_list(1000)
    user_ids = [s["id"] for s in students]
    all_progress = await db.progress.find({"user_id": {"$in": user_ids}}, {"_id": 0}).to_list(50000)
    prog_by_user = {}
    for p in all_progress:
        prog_by_user.setdefault(p["user_id"], []).append(p)
    result = []
    for s in students:
        prog = prog_by_user.get(s["id"], [])
        completed = sum(1 for p in prog if p.get("status") == "completed")
        hours = sum(p.get("hours_logged", 0) for p in prog if p.get("status") == "completed")
        scored = [p.get("quiz_score") for p in prog if p.get("quiz_score") is not None]
        avg_score = sum(scored) / len(scored) if scored else 0
        result.append({**s, "modules_completed": completed, "hours": hours, "avg_score": round(avg_score, 1)})
    return result
