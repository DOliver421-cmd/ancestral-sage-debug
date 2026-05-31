"""app/routes/labs.py — Lab submission, instructor review, and competency endpoints.

Extracted from backend/server.py lines 4928–5241.
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
from app.utils.audit import audit, notify

logger = logging.getLogger("lcewai")

router = APIRouter()

try:
    from seed import COMPETENCIES
except ImportError:
    COMPETENCIES: list = []


class LabSubmitReq(BaseModel):
    lab_slug: Optional[str] = None
    answers: Optional[dict] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class LabReviewReq(BaseModel):
    status: Literal["approved", "rejected"]
    feedback: Optional[str] = None


def grade_online_lab(simulator_type: str, answers: dict) -> dict:
    """Return {'score': 0-100, 'correct': int, 'total': int, 'detail': str} for online labs."""
    if not answers:
        return {"score": 0, "correct": 0, "total": 1, "detail": "No answers submitted"}

    if simulator_type == "basic_circuit":
        v = float(answers.get("voltage", 0))
        r1, r2, r3 = float(answers.get("r1", 0)), float(answers.get("r2", 0)), float(answers.get("r3", 0))
        cfg = answers.get("config", "series")
        user_rt = float(answers.get("total_r", 0))
        user_i = float(answers.get("total_i", 0))
        if cfg == "series":
            rt = r1 + r2 + r3
        else:
            rt = 1 / ((1 / r1 if r1 else 0) + (1 / r2 if r2 else 0) + (1 / r3 if r3 else 0)) if (r1 and r2 and r3) else 0
        it = v / rt if rt else 0
        rt_ok = abs(user_rt - rt) < max(0.1, rt * 0.02)
        it_ok = abs(user_i - it) < max(0.01, it * 0.02)
        correct = int(rt_ok) + int(it_ok)
        return {"score": correct / 2 * 100, "correct": correct, "total": 2,
                "detail": f"Rt={rt:.2f}Ω, I={it:.3f}A (yours: Rt={user_rt}, I={user_i})"}

    if simulator_type == "switch_wiring":
        key = {"hot_to": "brass", "neutral_to": "silver", "ground_to": "green"}
        correct = sum(1 for k, v in key.items() if answers.get(k) == v)
        return {"score": correct / 3 * 100, "correct": correct, "total": 3, "detail": ""}

    if simulator_type == "panel_labeling":
        key = {"slot_0": "kitchen", "slot_1": "bedroom", "slot_2": "bathroom_gfci",
               "slot_3": "living_room", "slot_4": "hvac", "slot_5": "laundry"}
        correct = sum(1 for k, v in key.items() if answers.get(k) == v)
        return {"score": correct / len(key) * 100, "correct": correct, "total": len(key), "detail": ""}

    if simulator_type == "conduit_calc":
        rise = float(answers.get("rise", 0))
        angle = int(answers.get("angle", 30))
        user_distance = float(answers.get("distance", 0))
        user_shrink = float(answers.get("shrink", 0))
        mult_tbl = {10: (6.0, 1 / 16), 22: (2.6, 3 / 16), 30: (2.0, 1 / 4), 45: (1.4, 3 / 8), 60: (1.2, 1 / 2)}
        mult, shrink_per_inch = mult_tbl.get(angle, (2.0, 0.25))
        distance = rise * mult
        shrink = rise * shrink_per_inch
        d_ok = abs(user_distance - distance) < 0.25
        s_ok = abs(user_shrink - shrink) < 0.1
        correct = int(d_ok) + int(s_ok)
        return {"score": correct / 2 * 100, "correct": correct, "total": 2,
                "detail": f"distance={distance:.2f}\" shrink={shrink:.3f}\""}

    if simulator_type == "vdrop":
        length = float(answers.get("length_ft", 0))
        current = float(answers.get("current_a", 0))
        awg = int(answers.get("awg", 12))
        source_v = float(answers.get("source_v", 120))
        user_vd_pct = float(answers.get("vd_pct", 0))
        cm_tbl = {14: 4110, 12: 6530, 10: 10380, 8: 16510, 6: 26240, 4: 41740, 2: 66360}
        cm = cm_tbl.get(awg, 6530)
        k = 12.9
        vd = (2 * k * current * length) / cm
        vd_pct = vd / source_v * 100
        ok = abs(user_vd_pct - vd_pct) < 0.2
        return {"score": 100 if ok else 0, "correct": int(ok), "total": 1,
                "detail": f"Actual Vdrop = {vd:.2f}V ({vd_pct:.2f}%)"}

    if simulator_type == "solar_config":
        daily_kwh = float(answers.get("daily_kwh", 0))
        sun_hours = float(answers.get("sun_hours", 0))
        sys_v = float(answers.get("sys_v", 48))
        autonomy_days = float(answers.get("autonomy_days", 2))
        user_pv_w = float(answers.get("pv_watts", 0))
        user_bank_ah = float(answers.get("bank_ah", 0))
        pv_w = (daily_kwh * 1000) / sun_hours if sun_hours else 0
        bank_wh = daily_kwh * 1000 * autonomy_days / 0.8
        bank_ah = bank_wh / sys_v if sys_v else 0
        pv_ok = abs(user_pv_w - pv_w) / max(1, pv_w) < 0.1
        ah_ok = abs(user_bank_ah - bank_ah) / max(1, bank_ah) < 0.1
        correct = int(pv_ok) + int(ah_ok)
        return {"score": correct / 2 * 100, "correct": correct, "total": 2,
                "detail": f"Need ~{pv_w:.0f}W array and ~{bank_ah:.0f}Ah bank"}

    if simulator_type == "loto":
        expected = ["notify", "shutdown", "lockout", "tagout", "verify_dead", "try_start"]
        seq = answers.get("sequence", [])
        correct = sum(1 for i, s in enumerate(expected) if i < len(seq) and seq[i] == s)
        return {"score": correct / len(expected) * 100, "correct": correct, "total": len(expected), "detail": ""}

    if simulator_type == "troubleshooting":
        path = answers.get("path", [])
        expected = ["test_breaker", "test_receptacle_voltage", "test_neutral_continuity", "find_open_neutral"]
        correct = sum(1 for i, s in enumerate(expected) if i < len(path) and path[i] == s)
        return {"score": correct / len(expected) * 100, "correct": correct, "total": len(expected), "detail": ""}

    if simulator_type == "load_balance":
        assignments = answers.get("assignments", {})
        loads = {"c1": 1500, "c2": 800, "c3": 1200, "c4": 600, "c5": 1800, "c6": 400}
        a = sum(loads[k] for k, v in assignments.items() if v == "A" and k in loads)
        b = sum(loads[k] for k, v in assignments.items() if v == "B" and k in loads)
        diff_pct = abs(a - b) / max(1, (a + b) / 2) * 100 if (a + b) else 100
        ok = diff_pct <= 10
        return {"score": 100 if ok else max(0, 100 - diff_pct * 2), "correct": 1 if ok else 0, "total": 1,
                "detail": f"Phase A={a}W Phase B={b}W Δ={diff_pct:.1f}%"}

    return {"score": 0, "correct": 0, "total": 1, "detail": "Unknown simulator"}


async def _award_credentials(user_id: str):
    from app.routes.credentials import award_credentials
    await award_credentials(user_id)


async def _award_xp(user_id: str, amount: int, reason: str):
    from app.routes.credentials import award_xp
    await award_xp(user_id, amount, reason)


@router.get("/competencies")
async def list_competencies(user: User = Depends(current_user)):
    subs = await db.lab_submissions.find(
        {"user_id": user.id, "status": {"$in": ["approved", "passed"]}}, {"_id": 0}
    ).to_list(500)
    slugs = list({s["lab_slug"] for s in subs})
    labs = await db.labs.find({"slug": {"$in": slugs}}, {"_id": 0}).to_list(500) if slugs else []
    labs_by_slug = {lab["slug"]: lab for lab in labs}
    score_by_comp = {c["key"]: {"points": 0, "labs": 0} for c in COMPETENCIES}
    for s in subs:
        lab = labs_by_slug.get(s["lab_slug"])
        if not lab:
            continue
        for cmp_key in lab.get("competencies", []):
            if cmp_key in score_by_comp:
                score_by_comp[cmp_key]["points"] += lab.get("skill_points", 0)
                score_by_comp[cmp_key]["labs"] += 1
    return {
        "competencies": COMPETENCIES,
        "progress": score_by_comp,
        "total_points": sum(v["points"] for v in score_by_comp.values()),
        "total_labs": len(subs),
    }


@router.get("/labs")
async def list_labs(track: Optional[str] = None, user: User = Depends(current_user)):
    q = {"track": track} if track in ("online", "inperson") else {}
    docs = await db.labs.find(q, {"_id": 0}).to_list(200)
    my_subs = await db.lab_submissions.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    sub_map = {s["lab_slug"]: s for s in my_subs}
    for d in docs:
        s = sub_map.get(d["slug"])
        d["my_submission"] = {
            "status": s["status"] if s else "not_started",
            "auto_score": s.get("auto_score") if s else None,
        } if s else {"status": "not_started"}
    docs.sort(key=lambda x: (x.get("track") == "inperson", x.get("slug", "")))
    return docs


@router.get("/labs/submissions/me")
async def my_lab_submissions(user: User = Depends(current_user)):
    docs = await db.lab_submissions.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    return docs


@router.get("/labs/{slug}")
async def get_lab(slug: str, user: User = Depends(current_user)):
    doc = await db.labs.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Lab not found")
    sub = await db.lab_submissions.find_one({"user_id": user.id, "lab_slug": slug}, {"_id": 0})
    doc["my_submission"] = sub
    return doc


@router.post("/labs/{slug}/submit")
async def submit_lab(slug: str, body: LabSubmitReq, user: User = Depends(current_user)):
    lab = await db.labs.find_one({"slug": slug}, {"_id": 0})
    if not lab:
        raise HTTPException(404, "Lab not found")

    now = datetime.now(timezone.utc).isoformat()
    if lab["track"] == "online":
        result = grade_online_lab(lab.get("simulator_type", ""), body.answers or {})
        status_val = "passed" if result["score"] >= 70 else "failed"
        doc = {
            "user_id": user.id,
            "lab_slug": slug,
            "track": "online",
            "answers": body.answers or {},
            "auto_score": result["score"],
            "detail": result["detail"],
            "status": status_val,
            "feedback": None,
            "created_at": now,
            "reviewed_at": now,
        }
        await db.lab_submissions.update_one(
            {"user_id": user.id, "lab_slug": slug},
            {"$set": doc, "$setOnInsert": {"id": str(uuid.uuid4())}},
            upsert=True,
        )
        if status_val == "passed":
            await _award_credentials(user.id)
            lab_pts = lab.get("skill_points", 0)
            await _award_xp(user.id, 50 + lab_pts * 2, f"Online lab passed: {slug}")
        return {**result, "status": status_val}
    else:
        doc = {
            "user_id": user.id,
            "lab_slug": slug,
            "track": "inperson",
            "photo_url": body.photo_url,
            "notes": body.notes,
            "auto_score": None,
            "status": "pending",
            "feedback": None,
            "created_at": now,
        }
        await db.lab_submissions.update_one(
            {"user_id": user.id, "lab_slug": slug},
            {"$set": doc, "$setOnInsert": {"id": str(uuid.uuid4())}},
            upsert=True,
        )
        return {"status": "pending"}


@router.get("/instructor/submissions")
async def pending_submissions(user: User = Depends(require_role("instructor", "admin"))):
    q = {"track": "inperson", "status": "pending"}
    docs = await db.lab_submissions.find(q, {"_id": 0}).to_list(500)
    user_ids = list({d["user_id"] for d in docs})
    lab_slugs = list({d["lab_slug"] for d in docs})
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(500) if user_ids else []
    labs = await db.labs.find({"slug": {"$in": lab_slugs}}, {"_id": 0}).to_list(500) if lab_slugs else []
    users_by_id = {u["id"]: u for u in users}
    labs_by_slug = {lab["slug"]: lab for lab in labs}
    for d in docs:
        d["user"] = users_by_id.get(d["user_id"])
        d["lab"] = labs_by_slug.get(d["lab_slug"])
    return docs


@router.post("/instructor/submissions/{sub_id}/review")
async def review_submission(sub_id: str, body: LabReviewReq, user: User = Depends(require_role("instructor", "admin"))):
    sub = await db.lab_submissions.find_one({"id": sub_id}, {"_id": 0})
    if not sub:
        raise HTTPException(404, "Submission not found")
    await db.lab_submissions.update_one(
        {"id": sub_id},
        {"$set": {
            "status": body.status,
            "feedback": body.feedback,
            "reviewed_by": user.id,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    if body.status == "approved":
        await _award_credentials(sub["user_id"])
        lab = await db.labs.find_one({"slug": sub["lab_slug"]}, {"_id": 0})
        lab_pts = lab.get("skill_points", 0) if lab else 0
        await _award_xp(sub["user_id"], 100 + lab_pts * 3, f"In-person lab approved: {sub['lab_slug']}")
        await notify(sub["user_id"], "Lab approved",
                     f"Your submission for '{lab['title'] if lab else sub['lab_slug']}' was approved.",
                     link=f"/labs/{sub['lab_slug']}", kind="success")
    elif body.status == "rejected":
        lab = await db.labs.find_one({"slug": sub["lab_slug"]}, {"_id": 0})
        await notify(sub["user_id"], "Lab needs revision",
                     f"Instructor feedback on '{lab['title'] if lab else sub['lab_slug']}': {body.feedback or 'see lab page'}",
                     link=f"/labs/{sub['lab_slug']}", kind="warning")
    await audit(user.id, f"lab.{body.status}", target=sub_id, meta={"lab_slug": sub["lab_slug"], "student_id": sub["user_id"]})
    return {"ok": True}


@router.post("/labs/submissions/{sub_id}/ai-feedback")
async def lab_ai_feedback(sub_id: str, user: User = Depends(current_user)):
    from app.config import ANTHROPIC_API_KEY
    assert_role = None
    try:
        from app.security.auth import assert_role as _assert_role
        assert_role = _assert_role
    except ImportError:
        pass
    if assert_role:
        assert_role(user, "instructor")
    else:
        if user.role not in ("instructor", "admin", "executive_admin"):
            raise HTTPException(403, "Instructor access required")

    sub = await db.lab_submissions.find_one({"id": sub_id}, {"_id": 0})
    if not sub:
        raise HTTPException(404, "Submission not found")
    lab = await db.labs.find_one({"slug": sub["lab_slug"]}, {"_id": 0})
    rubric_lines = "\n".join(f"- {r}" for r in (lab.get("rubric", []) if lab else []))
    prompt = (
        f"You are an experienced trades instructor reviewing an apprentice's lab submission.\n\n"
        f"Lab: {lab['title'] if lab else sub['lab_slug']}\n"
        f"Track: {sub.get('track', 'unknown')}\n"
        f"Student notes: {sub.get('notes') or 'No notes provided.'}\n"
        f"Pass criteria: {lab.get('pass_criteria', 'Not specified') if lab else 'Not specified'}\n"
        f"Rubric:\n{rubric_lines or 'Not specified'}\n\n"
        "Write 2-3 paragraphs of constructive coaching feedback:\n"
        "1. Acknowledge what the student demonstrated\n"
        "2. Identify specific areas for improvement based on the rubric\n"
        "3. Offer one concrete next step\n\n"
        "Be encouraging and safety-focused. Keep it under 200 words."
    )
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(
            system="You are an experienced trades instructor providing constructive coaching feedback.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            persona_label="lab_feedback",
        )
        feedback_text = _gw["text"]
    except Exception as _gw_err:
        import os
        logger.warning("lab_ai_feedback: gateway failed (%s) — trying direct Anthropic", _gw_err)
        ANTHROPIC_API_KEY_local = os.environ.get("ANTHROPIC_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
        if not ANTHROPIC_API_KEY_local:
            raise HTTPException(500, "AI not configured")
        try:
            import anthropic as _anth
        except Exception as e:
            raise HTTPException(500, f"AI library unavailable: {e}")
        _cl = _anth.AsyncAnthropic(api_key=ANTHROPIC_API_KEY_local)
        resp = await _cl.messages.create(model="claude-sonnet-4-6", max_tokens=400,
                                         messages=[{"role": "user", "content": prompt}])
        feedback_text = resp.content[0].text
    await db.lab_submissions.update_one({"id": sub_id}, {"$set": {"ai_feedback": feedback_text}})
    return {"ai_feedback": feedback_text}


@router.get("/instructor/lab-report")
async def lab_report(user: User = Depends(require_role("instructor", "admin"))):
    q = {"role": "student"} if user.role == "admin" else {"role": "student", "associate": user.associate}
    students = await db.users.find(q, {"_id": 0, "password_hash": 0}).to_list(1000)
    user_ids = [s["id"] for s in students]
    all_subs = await db.lab_submissions.find({"user_id": {"$in": user_ids}}, {"_id": 0}).to_list(50000)
    all_labs = await db.labs.find({}, {"_id": 0}).to_list(200)
    labs_by_slug = {lab["slug"]: lab for lab in all_labs}
    subs_by_user = {}
    for s in all_subs:
        subs_by_user.setdefault(s["user_id"], []).append(s)
    result = []
    for s in students:
        subs = subs_by_user.get(s["id"], [])
        passed = [x for x in subs if x.get("status") in ("passed", "approved")]
        pending = [x for x in subs if x.get("status") == "pending"]
        points = 0
        hours = 0
        for p in passed:
            lab = labs_by_slug.get(p["lab_slug"])
            if lab:
                points += lab.get("skill_points", 0)
                hours += lab.get("hours", 0)
        result.append({
            "user_id": s["id"],
            "full_name": s["full_name"],
            "email": s["email"],
            "associate": s.get("associate"),
            "labs_passed": len(passed),
            "labs_pending": len(pending),
            "skill_points": points,
            "lab_hours": hours,
        })
    return result
