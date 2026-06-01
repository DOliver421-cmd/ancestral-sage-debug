"""app/routes/credentials.py — Credential, XP, portfolio, certificate, and transcript endpoints.

Extracted from backend/server.py lines 5244–5682, 7028–7190, 6916–6944.
No logic changed.
"""
import io
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from app.config import JWT_SECRET, JWT_ALGO
from app.database import db
from app.models.user import User
from app.security.auth import current_user, require_role
from app.utils.audit import audit, notify

logger = logging.getLogger("lcewai")

router = APIRouter()

try:
    from seed import MODULES, CREDENTIALS, COMPETENCIES
except ImportError:
    MODULES: list = []
    CREDENTIALS: list = []
    COMPETENCIES: list = []


class PortfolioPublishReq(BaseModel):
    bio: Optional[str] = None
    publish: bool = True


# ── Helper functions ──────────────────────────────────────────────────────────

async def get_user_state(user_id: str) -> dict:
    """Load modules, labs, competencies relevant for credential eligibility."""
    mod_progress = await db.progress.find(
        {"user_id": user_id, "status": "completed"}, {"_id": 0}
    ).to_list(500)
    completed_modules = {p["module_slug"] for p in mod_progress}
    lab_subs = await db.lab_submissions.find(
        {"user_id": user_id, "status": {"$in": ["passed", "approved"]}}, {"_id": 0}
    ).to_list(500)
    passed_labs = {s["lab_slug"] for s in lab_subs}
    comp = {c["key"]: 0 for c in COMPETENCIES}
    slugs = list({s["lab_slug"] for s in lab_subs})
    labs = await db.labs.find({"slug": {"$in": slugs}}, {"_id": 0}).to_list(500) if slugs else []
    labs_by_slug = {lab["slug"]: lab for lab in labs}
    for s in lab_subs:
        lab = labs_by_slug.get(s["lab_slug"])
        if lab:
            for k in lab.get("competencies", []):
                if k in comp:
                    comp[k] += lab.get("skill_points", 0)
    return {
        "completed_modules": completed_modules,
        "passed_labs": passed_labs,
        "competencies": comp,
        "module_count": len(completed_modules),
        "lab_count": len(passed_labs),
    }


def credential_eligible(cred: dict, state: dict) -> bool:
    trig = cred["trigger"]
    t = trig["type"]
    if t == "all_modules":
        return state["module_count"] >= len(MODULES)
    if t == "modules_all_of":
        return all(s in state["completed_modules"] for s in trig["slugs"])
    if t == "module_completed":
        return trig["slug"] in state["completed_modules"]
    if t == "labs_all_of":
        return all(s in state["passed_labs"] for s in trig["slugs"])
    if t == "lab_passed":
        return trig["slug"] in state["passed_labs"]
    if t == "competency_at_least":
        return state["competencies"].get(trig["key"], 0) >= trig["points"]
    return False


async def award_credentials(user_id: str) -> list:
    """Run all credential triggers and insert newly-earned credentials. Returns newly-awarded keys."""
    state = await get_user_state(user_id)
    awarded = []
    now = datetime.now(timezone.utc)
    for cred in CREDENTIALS:
        if not credential_eligible(cred, state):
            continue
        existing = await db.user_credentials.find_one(
            {"user_id": user_id, "credential_key": cred["key"]}, {"_id": 0}
        )
        if existing:
            continue
        exp_months = cred.get("expires_months")
        expires_at = (now + timedelta(days=30 * exp_months)).isoformat() if exp_months else None
        await db.user_credentials.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "credential_key": cred["key"],
            "earned_at": now.isoformat(),
            "expires_at": expires_at,
            "status": "active",
            "verification_code": secrets.token_urlsafe(12),
        })
        awarded.append(cred["key"])
        await notify(user_id, "Credential earned",
                     f"You earned: {cred['name']}",
                     link="/credentials", kind="success")
        await audit(user_id, "credential.earned", target=cred["key"])
    return awarded


def xp_level(total: int) -> dict:
    if total >= 3000:
        return {"level": "Master", "level_num": 4, "min": 3000, "next": None}
    if total >= 1500:
        return {"level": "Craftsman", "level_num": 3, "min": 1500, "next": 3000}
    if total >= 500:
        return {"level": "Journeyman", "level_num": 2, "min": 500, "next": 1500}
    return {"level": "Apprentice", "level_num": 1, "min": 0, "next": 500}


async def award_xp(user_id: str, amount: int, reason: str) -> int:
    """Add XP to user total. Returns new total."""
    entry = {"amount": amount, "reason": reason, "at": datetime.now(timezone.utc).isoformat()}
    result = await db.user_xp.find_one_and_update(
        {"user_id": user_id},
        {
            "$inc": {"total_xp": amount},
            "$push": {"history": {"$each": [entry], "$slice": -50}},
            "$setOnInsert": {"id": str(uuid.uuid4())},
        },
        upsert=True,
        return_document=True,
    )
    return (result or {}).get("total_xp", amount)


def public_url_from(request: Request) -> str:
    override = os.environ.get('PUBLIC_BACKEND_URL', '').strip()
    if override:
        return override.rstrip('/')
    fwd_host = request.headers.get('x-forwarded-host')
    fwd_proto = request.headers.get('x-forwarded-proto', request.url.scheme)
    host = fwd_host or request.url.netloc
    return f"{fwd_proto}://{host}"


async def build_portfolio(user_doc: dict) -> dict:
    user_id = user_doc["id"]
    await award_credentials(user_id)

    all_modules = await db.modules.find({}, {"_id": 0}).to_list(100)
    modules_by_slug = {m["slug"]: m for m in all_modules}
    all_labs = await db.labs.find({}, {"_id": 0}).to_list(200)
    labs_by_slug = {lab["slug"]: lab for lab in all_labs}

    mod_progress = await db.progress.find({"user_id": user_id}, {"_id": 0}).to_list(500)
    completed_mods = []
    for p in mod_progress:
        if p.get("status") == "completed":
            mod = modules_by_slug.get(p["module_slug"])
            if mod:
                completed_mods.append({
                    "slug": mod["slug"],
                    "title": mod["title"],
                    "hours": mod["hours"],
                    "score": p.get("quiz_score"),
                    "completed_at": p.get("completed_at"),
                })

    lab_subs = await db.lab_submissions.find(
        {"user_id": user_id, "status": {"$in": ["passed", "approved"]}}, {"_id": 0}
    ).to_list(500)
    labs_detail = []
    for s in lab_subs:
        lab = labs_by_slug.get(s["lab_slug"])
        if lab:
            labs_detail.append({
                "slug": lab["slug"],
                "title": lab["title"],
                "track": lab["track"],
                "skill_points": lab.get("skill_points", 0),
                "hours": lab.get("hours", 0),
                "photo_url": s.get("photo_url"),
                "notes": s.get("notes"),
                "feedback": s.get("feedback"),
                "auto_score": s.get("auto_score"),
                "completed_at": s.get("reviewed_at") or s.get("created_at"),
            })

    comp_map = {c["key"]: {**c, "points": 0, "labs": 0, "badge_earned": False} for c in COMPETENCIES}
    for s in lab_subs:
        lab = labs_by_slug.get(s["lab_slug"])
        if lab:
            for k in lab.get("competencies", []):
                if k in comp_map:
                    comp_map[k]["points"] += lab.get("skill_points", 0)
                    comp_map[k]["labs"] += 1
    for c in comp_map.values():
        c["badge_earned"] = c["points"] >= 100

    creds = await db.user_credentials.find({"user_id": user_id}, {"_id": 0}).to_list(200)
    cred_by_key = {c["key"]: c for c in CREDENTIALS}
    creds_detail = []
    for c in creds:
        cred = cred_by_key.get(c["credential_key"])
        if cred:
            creds_detail.append({**cred, **c})

    port = await db.portfolios.find_one({"user_id": user_id}, {"_id": 0})

    hours = sum(m["hours"] for m in completed_mods) + sum(lab_item["hours"] for lab_item in labs_detail)
    skill_points = sum(c["points"] for c in comp_map.values())

    return {
        "user": {
            "id": user_doc["id"],
            "full_name": user_doc["full_name"],
            "email": user_doc["email"],
            "associate": user_doc.get("associate"),
        },
        "bio": port.get("bio") if port else None,
        "share_slug": port.get("slug") if port and port.get("published") else None,
        "stats": {
            "hours": hours,
            "skill_points": skill_points,
            "modules_completed": len(completed_mods),
            "labs_passed": len(labs_detail),
            "credentials_earned": len(creds_detail),
            "badges_earned": sum(1 for c in comp_map.values() if c["badge_earned"]),
        },
        "modules": completed_mods,
        "labs": labs_detail,
        "credentials": creds_detail,
        "competencies": list(comp_map.values()),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/credentials")
async def list_credentials(user: User = Depends(current_user)):
    return CREDENTIALS


@router.get("/credentials/me")
async def my_credentials(user: User = Depends(current_user)):
    earned = await db.user_credentials.find({"user_id": user.id}, {"_id": 0}).to_list(200)
    cred_map = {c["key"]: c for c in CREDENTIALS}
    result = []
    now = datetime.now(timezone.utc)
    for e in earned:
        cred = cred_map.get(e["credential_key"])
        if not cred:
            continue
        expired = False
        if e.get("expires_at"):
            try:
                expired = datetime.fromisoformat(e["expires_at"]) < now
            except Exception:
                expired = False
        result.append({**cred, **e, "expired": expired})
    earned_keys = {e["credential_key"] for e in earned}
    unearned = [c for c in CREDENTIALS if c["key"] not in earned_keys]
    return {"earned": result, "available": unearned}


@router.get("/credentials/{key}/manifest.json")
async def credential_manifest(key: str, request: Request):
    """OpenBadges v2 BadgeClass manifest (public)."""
    cred = next((c for c in CREDENTIALS if c["key"] == key), None)
    if not cred:
        raise HTTPException(404, "Credential not found")
    backend_url = public_url_from(request)
    return {
        "@context": "https://w3id.org/openbadges/v2",
        "type": "BadgeClass",
        "id": f"{backend_url}/api/credentials/{key}/manifest.json",
        "name": cred["name"],
        "description": cred["description"],
        "image": cred.get("image") or "https://customer-assets.emergentagent.com/job_apprentice-academy/artifacts/zqurn9jd_WAI%20Logo.jpg",
        "criteria": {"narrative": cred["evidence"]},
        "issuer": {
            "@context": "https://w3id.org/openbadges/v2",
            "type": "Profile",
            "id": f"{backend_url}/api/issuer.json",
            "name": "W.A.I. — Workforce Apprentice Institute",
            "url": "https://workforceapprenticeinstitute.org",
        },
        "tags": cred.get("tags", []),
    }


@router.get("/credentials/assertion/{assertion_id}.json")
async def credential_assertion(assertion_id: str, request: Request):
    """OpenBadges v2 Assertion (public, for verifiers)."""
    uc = await db.user_credentials.find_one({"id": assertion_id}, {"_id": 0})
    if not uc:
        raise HTTPException(404, "Assertion not found")
    user_doc = await db.users.find_one({"id": uc["user_id"]}, {"_id": 0, "password_hash": 0})
    cred = next((c for c in CREDENTIALS if c["key"] == uc["credential_key"]), None)
    if not cred or not user_doc:
        raise HTTPException(404, "Not found")
    backend_url = public_url_from(request)
    return {
        "@context": "https://w3id.org/openbadges/v2",
        "type": "Assertion",
        "id": f"{backend_url}/api/credentials/assertion/{assertion_id}.json",
        "recipient": {"type": "email", "hashed": False, "identity": user_doc["email"]},
        "issuedOn": uc["earned_at"],
        "expires": uc.get("expires_at"),
        "badge": f"{backend_url}/api/credentials/{cred['key']}/manifest.json",
        "verification": {"type": "HostedBadge"},
    }


@router.get("/certificates/me")
async def my_certificates(user: User = Depends(current_user)):
    prog = await db.progress.find(
        {"user_id": user.id, "status": "completed"}, {"_id": 0}
    ).to_list(200)
    slugs = [p["module_slug"] for p in prog]
    modules = await db.modules.find(
        {"slug": {"$in": slugs}}, {"_id": 0}
    ).to_list(200) if slugs else []
    mod_by_slug = {m["slug"]: m for m in modules}
    certs = []
    for p in prog:
        mod = mod_by_slug.get(p["module_slug"])
        if mod:
            certs.append({
                "module_slug": p["module_slug"],
                "title": mod["title"],
                "hours": mod["hours"],
                "score": p.get("quiz_score"),
                "completed_at": p.get("completed_at"),
            })
    if len(certs) == len(MODULES):
        certs.append({
            "module_slug": "program",
            "title": "LCE-WAI Camper-to-Classroom Program Completion",
            "hours": sum(m["hours"] for m in MODULES),
            "score": sum((c["score"] or 0) for c in certs) / len(MODULES),
            "completed_at": max((c.get("completed_at") or "") for c in certs),
        })
    return certs


@router.get("/certificates/{slug}.pdf")
async def cert_pdf(slug: str, token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    user_doc = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(401, "User not found")

    if slug == "program":
        title = "Camper-to-Classroom Program Completion"
        hours = sum(m["hours"] for m in MODULES)
    else:
        mod = await db.modules.find_one({"slug": slug}, {"_id": 0})
        if not mod:
            raise HTTPException(404, "Module not found")
        prog = await db.progress.find_one(
            {"user_id": user_doc["id"], "module_slug": slug, "status": "completed"}, {"_id": 0}
        )
        if not prog:
            raise HTTPException(404, "Not completed yet")
        title = mod["title"]
        hours = mod["hours"]

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(letter))
    w, h = landscape(letter)

    c.setFillColor(colors.HexColor("#F7F7F5"))
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#0B203F"))
    c.setLineWidth(8)
    c.rect(0.35 * inch, 0.35 * inch, w - 0.7 * inch, h - 0.7 * inch, fill=0, stroke=1)
    c.setFillColor(colors.HexColor("#1E5BA8"))
    c.rect(0.35 * inch, h - 1.1 * inch, w - 0.7 * inch, 0.12 * inch, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#0B203F"))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, h - 1.6 * inch, "W.A.I. — WORKFORCE APPRENTICE INSTITUTE")
    c.setFont("Helvetica", 11)
    c.drawCentredString(w / 2, h - 1.85 * inch, "LCE-WAI Partner Program")
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(w / 2, h - 2.7 * inch, "Certificate of Completion")
    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, h - 3.2 * inch, "This certifies that")
    c.setFillColor(colors.HexColor("#1E5BA8"))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(w / 2, h - 3.8 * inch, user_doc["full_name"])
    c.setFillColor(colors.HexColor("#0B203F"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, h - 4.3 * inch, "has successfully completed")
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(w / 2, h - 4.85 * inch, title)
    c.setFont("Helvetica", 12)
    c.drawCentredString(w / 2, h - 5.3 * inch, f"Training Hours: {hours}    |    Date: {datetime.now(timezone.utc).strftime('%B %d, %Y')}")
    c.setStrokeColor(colors.HexColor("#0B203F"))
    c.setLineWidth(1)
    c.line(1.5 * inch, 1.1 * inch, 4 * inch, 1.1 * inch)
    c.line(w - 4 * inch, 1.1 * inch, w - 1.5 * inch, 1.1 * inch)
    c.setFont("Helvetica", 10)
    c.drawCentredString(2.75 * inch, 0.9 * inch, "Instructor of Record")
    c.drawCentredString(w - 2.75 * inch, 0.9 * inch, "Program Director")
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(w / 2, 0.55 * inch, '"Whatever you do, work at it with all your heart, as working for the Lord." - Colossians 3:23')
    c.showPage()
    c.save()
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=LCE-WAI-{slug}.pdf"},
    )


@router.get("/credentials/transcript.pdf")
async def download_transcript(user: User = Depends(current_user)):
    mod_progress = await db.progress.find({"user_id": user.id, "status": "completed"}, {"_id": 0}).to_list(200)
    all_modules = await db.modules.find({}, {"_id": 0}).to_list(100)
    mods_by_slug = {m["slug"]: m for m in all_modules}
    lab_subs = await db.lab_submissions.find({"user_id": user.id, "status": {"$in": ["passed", "approved"]}}, {"_id": 0}).to_list(200)
    all_labs = await db.labs.find({}, {"_id": 0}).to_list(200)
    labs_by_slug = {lab["slug"]: lab for lab in all_labs}
    cred_docs = await db.user_credentials.find({"user_id": user.id}, {"_id": 0}).to_list(200)
    cred_map = {c["key"]: c for c in CREDENTIALS}

    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=letter)
    pw, ph = letter

    def new_page():
        pdf.showPage()
        return ph - inch

    pdf.setFillColorRGB(0.11, 0.11, 0.11)
    pdf.rect(0, ph - 1.4 * inch, pw, 1.4 * inch, fill=1, stroke=0)
    pdf.setFillColorRGB(1.0, 0.78, 0.27)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(0.75 * inch, ph - 0.68 * inch, "W.A.I. — Workforce Apprentice Institute")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColorRGB(0.85, 0.85, 0.85)
    pdf.drawString(0.75 * inch, ph - 0.98 * inch, "OFFICIAL ACADEMIC TRANSCRIPT")
    pdf.drawRightString(pw - 0.75 * inch, ph - 0.98 * inch, f"Issued: {datetime.now(timezone.utc).strftime('%B %d, %Y')}")

    y = ph - 1.8 * inch
    pdf.setFillColorRGB(0.11, 0.11, 0.11)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(0.75 * inch, y, "Student Information")
    y -= 0.22 * inch
    pdf.setFont("Helvetica", 10)
    for line in [
        f"Name:       {user.full_name}",
        f"Email:      {user.email}",
        f"Role:       {user.role.replace('_', ' ').title()}",
        f"Associate:  {user.associate or 'N/A'}",
    ]:
        pdf.drawString(0.75 * inch, y, line)
        y -= 0.19 * inch

    def section_header(title):
        nonlocal y
        y -= 0.18 * inch
        if y < 2.0 * inch:
            y = new_page()
        pdf.setFont("Helvetica-Bold", 11)
        pdf.setFillColorRGB(0.65, 0.45, 0.10)
        pdf.drawString(0.75 * inch, y, title)
        y -= 0.04 * inch
        pdf.setStrokeColorRGB(0.65, 0.45, 0.10)
        pdf.line(0.75 * inch, y, pw - 0.75 * inch, y)
        y -= 0.2 * inch
        pdf.setFillColorRGB(0.11, 0.11, 0.11)

    section_header("Curriculum Modules Completed")
    pdf.setFont("Helvetica-Bold", 8)
    pdf.setFillColorRGB(0.4, 0.4, 0.4)
    for label, x in [("MODULE", 0.75), ("HRS", 4.2), ("SCORE", 5.1), ("DATE", 6.2)]:
        pdf.drawString(x * inch, y, label)
    y -= 0.16 * inch

    total_hours = 0
    for p in sorted(mod_progress, key=lambda x: x.get("completed_at") or ""):
        mod = mods_by_slug.get(p["module_slug"])
        if not mod:
            continue
        if y < 1.5 * inch:
            y = new_page()
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.11, 0.11, 0.11)
        pdf.drawString(0.75 * inch, y, mod["title"][:48])
        pdf.drawString(4.2 * inch, y, f"{mod.get('hours', 0)}h")
        sc = p.get("quiz_score")
        pdf.drawString(5.1 * inch, y, f"{sc:.0f}%" if sc is not None else "—")
        pdf.drawString(6.2 * inch, y, (p.get("completed_at") or "")[:10] or "—")
        total_hours += mod.get("hours", 0)
        y -= 0.17 * inch

    if not mod_progress:
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.5, 0.5, 0.5)
        pdf.drawString(0.75 * inch, y, "No modules completed.")
        y -= 0.18 * inch

    section_header("Practical Labs Completed")
    lab_hours = 0
    for s in lab_subs:
        lab_doc = labs_by_slug.get(s["lab_slug"])
        if not lab_doc:
            continue
        if y < 1.5 * inch:
            y = new_page()
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.11, 0.11, 0.11)
        track_label = "Online" if lab_doc.get("track") == "online" else "In-Person"
        pdf.drawString(0.75 * inch, y, f"{lab_doc['title'][:42]} ({track_label})")
        pdf.drawString(5.2 * inch, y, f"{lab_doc.get('skill_points', 0)} pts")
        pdf.setFillColorRGB(0.2, 0.6, 0.2)
        pdf.drawString(6.4 * inch, y, "PASSED")
        pdf.setFillColorRGB(0.11, 0.11, 0.11)
        lab_hours += lab_doc.get("hours", 0)
        y -= 0.17 * inch

    if not lab_subs:
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.5, 0.5, 0.5)
        pdf.drawString(0.75 * inch, y, "No labs completed.")
        y -= 0.18 * inch

    section_header("Credentials & Certifications")
    for cd in cred_docs:
        cred = cred_map.get(cd["credential_key"])
        if not cred:
            continue
        if y < 1.8 * inch:
            y = new_page()
        pdf.setFont("Helvetica-Bold", 9)
        pdf.setFillColorRGB(0.11, 0.11, 0.11)
        pdf.drawString(0.75 * inch, y, cred["name"][:55])
        pdf.drawString(5.8 * inch, y, (cd.get("earned_at") or "")[:10])
        y -= 0.15 * inch
        pdf.setFont("Helvetica", 8)
        pdf.setFillColorRGB(0.5, 0.5, 0.5)
        pdf.drawString(0.75 * inch, y, cred.get("description", "")[:72])
        y -= 0.2 * inch

    if not cred_docs:
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.5, 0.5, 0.5)
        pdf.drawString(0.75 * inch, y, "No credentials earned yet.")
        y -= 0.18 * inch

    if y < 1.8 * inch:
        y = new_page()
    y -= 0.2 * inch
    pdf.setFillColorRGB(0.94, 0.94, 0.88)
    pdf.rect(0.75 * inch, y - 0.65 * inch, pw - 1.5 * inch, 0.75 * inch, fill=1, stroke=0)
    pdf.setFillColorRGB(0.11, 0.11, 0.11)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(inch, y - 0.2 * inch, f"Total Training Hours: {total_hours + lab_hours}h")
    pdf.drawString(inch, y - 0.44 * inch, f"Credentials Earned: {len(cred_docs)}")
    pdf.drawString(3.8 * inch, y - 0.2 * inch, f"Modules Completed: {len(mod_progress)}")
    pdf.drawString(3.8 * inch, y - 0.44 * inch, f"Labs Passed: {len(lab_subs)}")

    pdf.setFont("Helvetica", 7)
    pdf.setFillColorRGB(0.6, 0.6, 0.6)
    pdf.drawString(0.75 * inch, 0.4 * inch,
                   "Official transcript — W.A.I. Workforce Apprentice Institute. "
                   "Verify credentials at workforceapprenticeinstitute.org")

    pdf.save()
    buf.seek(0)
    safe = "".join(ch for ch in user.full_name if ch.isalnum() or ch == " ").replace(" ", "_")
    filename = f"WAI_Transcript_{safe}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.post("/portfolio/publish")
async def publish_portfolio(body: PortfolioPublishReq, user: User = Depends(current_user)):
    existing = await db.portfolios.find_one({"user_id": user.id}, {"_id": 0})
    slug = existing.get("slug") if existing else None
    if not slug and body.publish:
        slug = f"{user.full_name.lower().replace(' ', '-')}-{user.id[:8]}"
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
    update = {
        "user_id": user.id,
        "slug": slug if body.publish else None,
        "bio": body.bio,
        "published": bool(body.publish),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.portfolios.update_one(
        {"user_id": user.id},
        {"$set": update, "$setOnInsert": {"id": str(uuid.uuid4())}},
        upsert=True,
    )
    return {"slug": slug, "published": bool(body.publish)}


@router.get("/portfolio/me")
async def my_portfolio(user: User = Depends(current_user)):
    user_doc = await db.users.find_one({"id": user.id}, {"_id": 0, "password_hash": 0})
    return await build_portfolio(user_doc)


@router.get("/portfolio/public/{slug}")
async def public_portfolio(slug: str):
    port = await db.portfolios.find_one({"slug": slug, "published": True}, {"_id": 0})
    if not port:
        raise HTTPException(404, "Portfolio not found or not public")
    user_doc = await db.users.find_one({"id": port["user_id"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(404, "User not found")
    data = await build_portfolio(user_doc)
    data["user"].pop("email", None)
    return data


@router.get("/portfolio/export.pdf")
async def portfolio_pdf(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    user_doc = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(401, "User not found")

    data = await build_portfolio(user_doc)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter

    def header():
        c.setFillColor(colors.HexColor("#0B203F"))
        c.rect(0, h - 1.3 * inch, w, 1.3 * inch, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#FFD100"))
        c.rect(0, h - 1.38 * inch, w, 0.08 * inch, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(0.6 * inch, h - 0.55 * inch, "W.A.I. — WORKFORCE APPRENTICE INSTITUTE")
        c.setFont("Helvetica", 9)
        c.drawString(0.6 * inch, h - 0.8 * inch, "LCE-WAI Partner Program  ·  Apprentice Portfolio")
        c.setFont("Helvetica-Bold", 18)
        c.drawString(0.6 * inch, h - 1.1 * inch, data["user"]["full_name"])
        c.setFont("Helvetica", 10)
        right = f"Hours: {data['stats']['hours']}  ·  Points: {data['stats']['skill_points']}"
        c.drawRightString(w - 0.6 * inch, h - 1.1 * inch, right)

    def section(y, title):
        c.setFillColor(colors.HexColor("#0B203F"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.6 * inch, y, title.upper())
        c.setStrokeColor(colors.HexColor("#1E5BA8"))
        c.setLineWidth(2)
        c.line(0.6 * inch, y - 4, 0.6 * inch + 1.1 * inch, y - 4)

    header()
    y = h - 1.7 * inch
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica", 10)
    if data.get("bio"):
        c.drawString(0.6 * inch, y, data["bio"][:120])
        y -= 0.25 * inch

    def text_line(txt, bold=False, size=10):
        nonlocal y
        if y < 1 * inch:
            c.showPage()
            header()
            y = h - 1.7 * inch
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(0.7 * inch, y, txt[:95])
        y -= 0.22 * inch

    section(y, "Credentials & Badges")
    y -= 0.3 * inch
    for cr in data["credentials"]:
        text_line(f"• {cr['name']}  [{cr['category'].upper()}]", bold=True)
        text_line(f"   Earned {cr['earned_at'][:10]}" + (f"  ·  Expires {cr['expires_at'][:10]}" if cr.get("expires_at") else ""))
    if not data["credentials"]:
        text_line("  (none yet)")

    y -= 0.15 * inch
    section(y, "Competency Matrix")
    y -= 0.3 * inch
    for cmp in data["competencies"]:
        mark = "✓" if cmp["badge_earned"] else " "
        text_line(f" [{mark}] {cmp['name']}  —  {cmp['points']} pts  ({cmp['labs']} labs)")

    y -= 0.15 * inch
    section(y, "Modules Completed")
    y -= 0.3 * inch
    for m in data["modules"]:
        text_line(f"• {m['title']}  —  {m['hours']}h  ({int(m['score']) if m.get('score') else 0}%)")

    y -= 0.15 * inch
    section(y, "Labs Passed")
    y -= 0.3 * inch
    for lab_item in data["labs"]:
        text_line(f"• {lab_item['title']}  [{lab_item['track'].upper()}]  —  {lab_item['skill_points']} pts")

    c.setFillColor(colors.HexColor("#4B5563"))
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(w / 2, 0.4 * inch, '"Whatever you do, work at it with all your heart." — Colossians 3:23')

    c.showPage()
    c.save()
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=portfolio-{user_doc['id'][:8]}.pdf"},
    )


# ── XP routes ─────────────────────────────────────────────────────────────────

@router.get("/xp/me")
async def my_xp(user: User = Depends(current_user)):
    doc = await db.user_xp.find_one({"user_id": user.id}, {"_id": 0})
    total = (doc or {}).get("total_xp", 0)
    level_info = xp_level(total)
    rank = 1
    if user.associate:
        cohort_ids = [u["id"] async for u in db.users.find({"associate": user.associate, "role": "student"}, {"id": 1, "_id": 0})]
        higher = await db.user_xp.count_documents({"user_id": {"$in": cohort_ids}, "total_xp": {"$gt": total}})
        rank = higher + 1
    return {**level_info, "total_xp": total, "rank_in_cohort": rank, "history": (doc or {}).get("history", [])[-10:]}


@router.get("/xp/leaderboard")
async def xp_leaderboard(associate: Optional[str] = None, user: User = Depends(current_user)):
    q: dict = {"role": "student"}
    if associate:
        q["associate"] = associate
    students = await db.users.find(q, {"_id": 0, "id": 1, "full_name": 1, "associate": 1}).to_list(500)
    ids = [s["id"] for s in students]
    xp_docs = await db.user_xp.find({"user_id": {"$in": ids}}, {"_id": 0}).to_list(500) if ids else []
    xp_map = {x["user_id"]: x["total_xp"] for x in xp_docs}
    board = sorted(
        [{**s, "total_xp": xp_map.get(s["id"], 0), "level": xp_level(xp_map.get(s["id"], 0))["level"]} for s in students],
        key=lambda x: -x["total_xp"]
    )[:25]
    return board


# ── Public credential verification ────────────────────────────────────────────

@router.get("/verify/{code}")
async def verify_credential(code: str):
    """Public credential verification — no authentication required."""
    cred_doc = await db.user_credentials.find_one(
        {"verification_code": code}, {"_id": 0}
    )
    if not cred_doc:
        raise HTTPException(404, "Credential not found. The code may be invalid or the credential may have been revoked.")

    user_doc = await db.users.find_one(
        {"id": cred_doc["user_id"]}, {"_id": 0, "password_hash": 0}
    )
    if not user_doc:
        raise HTTPException(404, "Credential holder not found.")

    cred_map = {c["key"]: c for c in CREDENTIALS}
    cred = cred_map.get(cred_doc["credential_key"])
    if not cred:
        raise HTTPException(404, "Credential type not recognized.")

    now = datetime.now(timezone.utc)
    expired = False
    if cred_doc.get("expires_at"):
        try:
            exp_dt = datetime.fromisoformat(cred_doc["expires_at"])
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            expired = exp_dt < now
        except Exception:
            pass

    return {
        "valid": not expired,
        "status": "expired" if expired else "active",
        "holder": user_doc["full_name"],
        "credential": cred["name"],
        "description": cred.get("description", ""),
        "institution": "W.A.I. Workforce Apprentice Institute",
        "earned_at": cred_doc.get("earned_at"),
        "expires_at": cred_doc.get("expires_at"),
        "verification_code": code,
        "verified_at": now.isoformat(),
    }
