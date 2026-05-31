"""app/services/engagement.py — Engagement check and credential backfill.

Extracted from backend/server.py lines 1057–1173.
No logic changed.
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone

from app.database import db
from app.utils.audit import notify

logger = logging.getLogger("lcewai")


async def run_engagement_check():
    """Flag academically at-risk students to their instructors and admins.

    Triggers:
      A) No login in 7+ days (last_login field, falls back to created_at).
      B) Two or more failed quiz attempts in the last 14 days.

    Each at-risk student gets one notification per day max (deduped by date tag).
    Their assigned instructor (matched by associate) and all admins are alerted.
    """
    now = datetime.now(timezone.utc)
    cutoff_login = (now - timedelta(days=7)).isoformat()
    cutoff_quiz = (now - timedelta(days=14)).isoformat()
    today_tag = now.strftime("%Y-%m-%d")

    students = await db.users.find(
        {"role": "student", "is_active": {"$ne": False}},
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "associate": 1,
         "last_login": 1, "created_at": 1},
    ).to_list(5000)

    admin_ids = [
        u["id"] for u in await db.users.find(
            {"role": {"$in": ["admin", "executive_admin"]}, "is_active": {"$ne": False}},
            {"id": 1, "_id": 0},
        ).to_list(100)
    ]

    flagged = 0
    for student in students:
        sid = student["id"]
        associate = student.get("associate")
        reasons = []

        # Trigger A: no login in 7+ days
        last_seen = student.get("last_login") or student.get("created_at", "")
        if last_seen and last_seen < cutoff_login:
            reasons.append("no activity in 7+ days")

        # Trigger B: 2+ failed quiz scores (< 70) in the last 14 days
        if not reasons:  # only run expensive query when needed
            recent_fails = await db.progress.count_documents({
                "user_id": sid,
                "quiz_score": {"$lt": 70, "$ne": None},
                "updated_at": {"$gte": cutoff_quiz},
            })
            if recent_fails >= 2:
                reasons.append(f"{recent_fails} failed quiz attempts in 14 days")

        if not reasons:
            continue

        reason_str = "; ".join(reasons)
        dedup_key = f"engagement:{sid}:{today_tag}"

        # Dedup: skip if we already sent this student's flag today
        already_sent = await db.notifications.find_one({
            "body": {"$regex": dedup_key},
            "created_at": {"$gte": now.replace(hour=0, minute=0, second=0).isoformat()},
        })
        if already_sent:
            continue

        msg_body = (
            f"Student {student['full_name']} may need support: {reason_str}. "
            f"[ref:{dedup_key}]"
        )

        # Notify the student's instructor (if associate matches)
        if associate:
            instructors = await db.users.find(
                {"role": "instructor", "associate": associate, "is_active": {"$ne": False}},
                {"id": 1, "_id": 0},
            ).to_list(10)
            for inst in instructors:
                await notify(
                    inst["id"],
                    f"Student needs attention: {student['full_name']}",
                    msg_body,
                    link="/instructor",
                    kind="warning",
                )

        # Notify all admins
        for aid in admin_ids:
            await notify(
                aid,
                f"Engagement alert: {student['full_name']}",
                msg_body,
                link="/admin",
                kind="warning",
            )

        flagged += 1

    if flagged:
        logger.info("Engagement check: flagged %d at-risk students", flagged)


async def backfill_verification_codes():
    """One-time migration: add verification_code to existing credentials that lack one."""
    cursor = db.user_credentials.find(
        {"verification_code": {"$exists": False}}, {"_id": 1}
    )
    count = 0
    async for doc in cursor:
        code = secrets.token_urlsafe(12)
        try:
            await db.user_credentials.update_one(
                {"_id": doc["_id"], "verification_code": {"$exists": False}},
                {"$set": {"verification_code": code}},
            )
            count += 1
        except Exception:
            pass  # unique constraint race — another startup already set it
    if count:
        logger.info("Backfilled verification_code on %d credentials", count)
