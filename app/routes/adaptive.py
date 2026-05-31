"""app/routes/adaptive.py — Adaptive learning engine endpoint.

Extracted from backend/server.py lines 5742–5833.
No logic changed.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends

from app.database import db
from app.models.user import User
from app.security.auth import current_user

logger = logging.getLogger("lcewai")

router = APIRouter()

try:
    from seed import COMPETENCIES
except ImportError:
    COMPETENCIES: list = []


@router.get("/adaptive/me")
async def adaptive_recommendations(user: User = Depends(current_user)):
    """Analyze student state, identify weak areas, return personalized recommendations."""
    progress = await db.progress.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    lab_subs = await db.lab_submissions.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    all_labs = await db.labs.find({}, {"_id": 0}).to_list(200)
    labs_by_slug = {lab["slug"]: lab for lab in all_labs}

    heatmap = {c["key"]: {"name": c["name"], "points": 0, "labs_passed": 0, "level": "cold"} for c in COMPETENCIES}
    for s in lab_subs:
        if s.get("status") in ("passed", "approved"):
            lab = labs_by_slug.get(s["lab_slug"])
            if lab:
                for k in lab.get("competencies", []):
                    if k in heatmap:
                        heatmap[k]["points"] += lab.get("skill_points", 0)
                        heatmap[k]["labs_passed"] += 1
    for h in heatmap.values():
        h["level"] = "hot" if h["points"] >= 100 else ("warm" if h["points"] >= 40 else "cold")

    weak = sorted(heatmap.values(), key=lambda x: x["points"])[:3]
    weak_keys = [next(k for k, v in heatmap.items() if v["name"] == w["name"]) for w in weak]

    low_quizzes = [p for p in progress if p.get("quiz_score") is not None and p["quiz_score"] < 80]

    passed_labs = {s["lab_slug"] for s in lab_subs if s.get("status") in ("passed", "approved")}
    recs = []
    for lab in all_labs:
        if lab["slug"] in passed_labs:
            continue
        overlap = set(lab.get("competencies", [])) & set(weak_keys)
        if overlap:
            recs.append({
                "type": "lab",
                "slug": lab["slug"],
                "title": lab["title"],
                "track": lab["track"],
                "reason": f"Strengthens: {', '.join(sorted(overlap))}",
                "skill_points": lab.get("skill_points", 0),
            })
    recs = sorted(recs, key=lambda r: -r["skill_points"])[:4]

    for q in low_quizzes[:2]:
        mod = await db.modules.find_one({"slug": q["module_slug"]}, {"_id": 0})
        if mod:
            recs.append({
                "type": "module_review",
                "slug": mod["slug"],
                "title": f"Review: {mod['title']}",
                "track": "core",
                "reason": f"You scored {int(q['quiz_score'])}% — retake to lock it in",
                "skill_points": 0,
            })

    ai_topic = None
    if weak:
        ai_topic = {
            "type": "ai_topic",
            "title": f"Ask the tutor about: {weak[0]['name']}",
            "reason": f"Your coldest area — {weak[0]['points']} skill points",
        }

    PREREQS = {
        "battery-inverter-build": ["solar-charge-controller"],
        "loto-real-equipment": ["loto-scenario"],
    }
    locked = []
    for lab_slug, prereq_slugs in PREREQS.items():
        if lab_slug in passed_labs:
            continue
        missing = [p for p in prereq_slugs if p not in passed_labs]
        if missing:
            lab = labs_by_slug.get(lab_slug)
            if lab:
                locked.append({"slug": lab_slug, "title": lab["title"], "missing_prereqs": missing})

    return {
        "heatmap": heatmap,
        "weak_areas": weak,
        "recommendations": recs,
        "ai_topic": ai_topic,
        "locked_labs": locked,
    }
