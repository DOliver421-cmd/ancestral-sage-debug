"""app/routes/analytics.py — Program analytics and cohort benchmark endpoints.

Extracted from backend/server.py lines 6228–7023.
No logic changed.
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.database import db
from app.models.user import User
from app.security.auth import current_user, require_role
from app.config import GROQ_API_KEY, CEREBRAS_API_KEY, MISTRAL_API_KEY

logger = logging.getLogger("lcewai")

router = APIRouter()

try:
    from seed import MODULES, COMPETENCIES
except ImportError:
    MODULES: list = []
    COMPETENCIES: list = []


@router.get("/analytics/program")
async def program_analytics(user: User = Depends(require_role("admin"))):
    students = await db.users.count_documents({"role": "student"})
    instructors = await db.users.count_documents({"role": "instructor"})
    completions = await db.progress.count_documents({"status": "completed"})
    labs_passed = await db.lab_submissions.count_documents({"status": {"$in": ["passed", "approved"]}})
    labs_pending = await db.lab_submissions.count_documents({"status": "pending"})
    creds_issued = await db.user_credentials.count_documents({})
    incidents_open = await db.incidents.count_documents({"status": "open"})

    pipeline_assoc = [
        {"$match": {"role": "student"}},
        {"$lookup": {"from": "progress", "localField": "id", "foreignField": "user_id", "as": "prog"}},
        {"$project": {"associate": 1, "completed": {"$size": {"$filter": {"input": "$prog", "as": "p", "cond": {"$eq": ["$$p.status", "completed"]}}}}}},
        {"$group": {"_id": "$associate", "students": {"$sum": 1}, "total_completions": {"$sum": "$completed"}}},
    ]
    by_associate = await db.users.aggregate(pipeline_assoc).to_list(50)
    associates = [{"associate": d["_id"] or "Unassigned", "students": d["students"], "completions": d["total_completions"]} for d in by_associate]

    now = datetime.now(timezone.utc)
    soon = (now + timedelta(days=90)).isoformat()
    expiring = await db.user_credentials.count_documents({
        "expires_at": {"$lte": soon, "$gt": now.isoformat()}
    })

    all_subs = await db.lab_submissions.find({"status": {"$in": ["passed", "approved"]}}, {"_id": 0}).to_list(50000)
    all_labs = await db.labs.find({}, {"_id": 0}).to_list(200)
    labs_by_slug = {lab["slug"]: lab for lab in all_labs}
    cohort_comp = {c["key"]: 0 for c in COMPETENCIES}
    for s in all_subs:
        lab = labs_by_slug.get(s["lab_slug"])
        if lab:
            for k in lab.get("competencies", []):
                if k in cohort_comp:
                    cohort_comp[k] += lab.get("skill_points", 0)
    weakest = sorted(cohort_comp.items(), key=lambda x: x[1])[:3]
    weakest_named = [{"key": k, "name": next((c["name"] for c in COMPETENCIES if c["key"] == k), k), "points": v} for k, v in weakest]

    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {"_id": "$module_slug", "count": {"$sum": 1}}},
    ]
    counts = {r["_id"]: r["count"] for r in await db.progress.aggregate(pipeline).to_list(200)}
    mod_completions = [
        {
            "slug": m["slug"], "title": m["title"], "completions": counts.get(m["slug"], 0),
            "rate": round(counts.get(m["slug"], 0) / max(1, students) * 100, 1),
        }
        for m in MODULES
    ]

    thirty_ago = (now - timedelta(days=30)).isoformat()
    active = len(set([
        a["actor_id"] for a in await db.audit_log.find(
            {"at": {"$gte": thirty_ago}, "action": "auth.login.success"}, {"_id": 0, "actor_id": 1}
        ).to_list(50000) if a.get("actor_id")
    ]))

    return {
        "totals": {
            "students": students, "instructors": instructors,
            "module_completions": completions, "labs_passed": labs_passed,
            "labs_pending_review": labs_pending,
            "credentials_issued": creds_issued,
            "credentials_expiring_90d": expiring,
            "open_incidents": incidents_open,
            "active_30d": active,
        },
        "by_associate": associates,
        "weakest_competencies": weakest_named,
        "module_completion_rates": mod_completions,
    }


@router.get("/analytics/benchmark")
async def cohort_benchmark(user: User = Depends(current_user)):
    from app.security.auth import assert_role
    assert_role(user, "instructor")
    total_modules = await db.modules.count_documents({})
    all_students = await db.users.count_documents({"role": "student"})
    platform_completions = await db.progress.count_documents({"status": "completed"})
    platform_avg = platform_completions / max(1, all_students)
    platform_pct = round(platform_avg / max(1, total_modules) * 100)

    associates = await db.users.distinct("associate", {"role": "student"})
    cohorts = []
    for assoc in associates:
        if not assoc:
            continue
        students = await db.users.find({"role": "student", "associate": assoc}, {"id": 1, "_id": 0}).to_list(500)
        sids = [s["id"] for s in students]
        completions = await db.progress.count_documents({"user_id": {"$in": sids}, "status": "completed"}) if sids else 0
        avg_comp = completions / max(1, len(sids))
        pct = round(avg_comp / max(1, total_modules) * 100)
        cohorts.append({"associate": assoc, "students": len(sids), "avg_completions": round(avg_comp, 1), "completion_pct": pct})
    cohorts.sort(key=lambda x: -x["completion_pct"])
    return {
        "platform": {"avg_completions": round(platform_avg, 1), "completion_pct": platform_pct, "total_students": all_students},
        "by_cohort": cohorts,
        "total_modules": total_modules,
    }
