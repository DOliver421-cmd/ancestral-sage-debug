"""app/routes/misc.py — Small miscellaneous routes.

Extracted from backend/server.py:
  /consent/cookie        (line 9570)
  /revenue/api-keys/*    (lines 9596–9646)
  /revenue/verify-credential (line 9647)
  /revenue/employer/*    (lines 9672–9812)
  /revenue/courses/*     (lines 9699–9744)
  /revenue/sovereign/*   (lines 9782–9845)
  /revenue/resume/preview (line 9846)
  /help/guide            (line 9871)
  /bug-report            (line 9937)
  /prices/public         (line 11115)
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from app.config import JWT_SECRET, JWT_ALGO
from app.database import db
from app.models.user import User
from app.security.auth import current_user, require_role

logger = logging.getLogger("lcewai")
router = APIRouter()


# ── Cookie Consent ─────────────────────────────────────────────────────────────

@router.post("/consent/cookie")
async def log_cookie_consent(body: dict, request: Request):
    choice = body.get("choice", "accepted")
    if choice not in ("accepted", "declined"):
        raise HTTPException(400, "choice must be 'accepted' or 'declined'")
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    user_id = None
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            user_id = payload.get("sub")
        except Exception:
            pass
    await db.cookie_consent_log.insert_one({
        "user_id": user_id, "choice": choice,
        "ip": request.client.host if request.client else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True}


# ── API-as-a-Service: Revenue Division ─────────────────────────────────────────

@router.get("/revenue/api-keys")
async def revenue_list_keys(user: User = Depends(current_user)):
    from api_keys import list_api_keys
    keys = await list_api_keys(db, user.id)
    return {"keys": keys}


@router.post("/revenue/api-keys")
async def revenue_create_key(body: dict, user: User = Depends(current_user)):
    from api_keys import create_api_key
    from app.utils.audit import audit
    label = body.get("label", "").strip()
    tier  = body.get("tier", "free")
    if not label:
        raise HTTPException(400, "label is required")
    if tier not in ("free", "starter", "pro", "enterprise"):
        raise HTTPException(400, "tier must be free, starter, pro, or enterprise")
    result = await create_api_key(db, label, tier, user.id)
    await audit(user.id, "revenue.api_key.created", meta={"tier": tier, "label": label})
    return result


@router.delete("/revenue/api-keys/{key_hash}")
async def revenue_revoke_key(key_hash: str, user: User = Depends(current_user)):
    from api_keys import revoke_api_key
    from app.utils.audit import audit
    ok = await revoke_api_key(db, key_hash, user.id)
    if not ok:
        raise HTTPException(404, "Key not found or already revoked")
    await audit(user.id, "revenue.api_key.revoked")
    return {"ok": True}


@router.get("/revenue/api-keys/stats")
async def revenue_key_stats(user: User = Depends(current_user)):
    from api_keys import get_usage_stats
    stats = await get_usage_stats(db, user.id)
    return stats


@router.get("/revenue/api-keys/tiers")
async def revenue_list_tiers():
    from api_keys import TIERS
    return {"tiers": TIERS}


# ── Credential Verification ────────────────────────────────────────────────────

@router.post("/revenue/verify-credential")
async def revenue_verify_credential(body: dict):
    code = body.get("verification_code", "")
    if not code:
        raise HTTPException(400, "verification_code is required")
    cred = await db.credentials.find_one({"verification_code": code}, {"_id": 0, "password_hash": 0})
    if not cred:
        raise HTTPException(404, "Credential not found")
    return {
        "valid": True,
        "credential": cred.get("title", ""),
        "holder": cred.get("holder_name", ""),
        "issued": cred.get("issued_at", ""),
        "expires": cred.get("expires_at", ""),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/revenue/employer/verify-batch")
async def revenue_employer_batch_verify(codes: str = "", user: User = Depends(require_role("instructor"))):
    if not codes:
        raise HTTPException(400, "Provide comma-separated verification codes")
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    results = []
    for code in code_list:
        cred = await db.credentials.find_one({"verification_code": code}, {"_id": 0, "title": 1, "holder_name": 1, "issued_at": 1, "expires_at": 1})
        results.append({
            "code": code, "valid": cred is not None,
            "credential": cred.get("title", "") if cred else None,
            "holder": cred.get("holder_name", "") if cred else None,
        })
    return {"results": results, "total": len(results), "valid": sum(1 for r in results if r["valid"])}


# ── Course Licensing ───────────────────────────────────────────────────────────

@router.get("/revenue/courses/public")
async def revenue_public_courses():
    modules = await db.modules.find({}, {"_id": 0, "slug": 1, "title": 1, "description": 1, "hours": 1, "competencies": 1, "price": 1}).to_list(length=50)
    return {"courses": modules}


@router.post("/revenue/courses/license")
async def revenue_license_course(body: dict, user: User = Depends(current_user)):
    from app.utils.audit import audit
    org   = body.get("organization", "").strip()
    slugs = body.get("course_slugs", [])
    seats = int(body.get("seats", 1))
    if not org or not slugs:
        raise HTTPException(400, "organization and course_slugs are required")
    if seats < 1 or seats > 1000:
        raise HTTPException(400, "seats must be between 1 and 1000")
    license_id = str(uuid.uuid4())
    await db.course_licenses.insert_one({
        "license_id": license_id, "organization": org, "course_slugs": slugs,
        "seats": seats, "user_id": user.id, "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await audit(user.id, "revenue.course.licensed", meta={"org": org, "slugs": slugs, "seats": seats})
    return {"license_id": license_id, "organization": org, "seats": seats}


@router.get("/revenue/courses/my-licenses")
async def revenue_my_licenses(user: User = Depends(current_user)):
    licenses = await db.course_licenses.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(length=50)
    return {"licenses": licenses}


# ── Employer Compliance ────────────────────────────────────────────────────────

@router.get("/revenue/employer/compliance")
async def revenue_employer_compliance(associate: str = "", user: User = Depends(require_role("instructor"))):
    match = {}
    if associate:
        match["associate"] = associate
    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$user_id", "total_hours": {"$sum": "$hours"}, "lab_count": {"$sum": 1}, "last_activity": {"$max": "$created_at"}}},
        {"$sort": {"total_hours": -1}},
        {"$limit": 100},
    ]
    try:
        attendance = await db.attendance.aggregate(pipeline).to_list(length=100)
    except Exception:
        attendance = []
    total_hours = sum(a.get("total_hours", 0) for a in attendance)
    return {
        "total_apprentices": len(attendance),
        "total_hours": total_hours,
        "average_hours": round(total_hours / len(attendance), 1) if attendance else 0,
        "records": attendance, "associate_filter": associate or "all",
    }


# ── Sovereign AI Workspaces ────────────────────────────────────────────────────

@router.post("/revenue/sovereign/workspace")
async def revenue_create_workspace(body: dict, user: User = Depends(require_role("admin"))):
    from app.utils.audit import audit
    name       = body.get("name", "").strip()
    member_ids = body.get("member_ids", [])
    if not name:
        raise HTTPException(400, "workspace name is required")
    ws_id = str(uuid.uuid4())
    await db.sovereign_workspaces.insert_one({
        "workspace_id": ws_id, "name": name, "owner_id": user.id, "member_ids": member_ids,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await audit(user.id, "revenue.sovereign.workspace_created", meta={"name": name, "members": len(member_ids)})
    return {"workspace_id": ws_id, "name": name}


@router.get("/revenue/sovereign/workspaces")
async def revenue_list_workspaces(user: User = Depends(require_role("admin"))):
    workspaces = await db.sovereign_workspaces.find(
        {"$or": [{"owner_id": user.id}, {"member_ids": user.id}]}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=50)
    return {"workspaces": workspaces}


@router.post("/revenue/sovereign/workspace/{ws_id}/chat")
async def revenue_workspace_chat(ws_id: str, body: dict, user: User = Depends(current_user)):
    ws = await db.sovereign_workspaces.find_one({"workspace_id": ws_id})
    if not ws:
        raise HTTPException(404, "Workspace not found")
    if user.id != ws["owner_id"] and user.id not in ws.get("member_ids", []):
        raise HTTPException(403, "Not a member of this workspace")
    message = body.get("message", "").strip()
    if not message:
        raise HTTPException(400, "message is required")
    memory = await db.sovereign_memory.find({"workspace_id": ws_id}, {"_id": 0}).sort("ts", -1).limit(10).to_list(length=10)
    memory_context = "\n".join(f"[{m.get('actor','')}]: {m.get('content','')}" for m in reversed(memory))
    system_prompt = f"You are the Sovereign AI for workspace '{ws['name']}'. Respond helpfully."
    if memory_context:
        system_prompt += f"\n\nRecent workspace memory:\n{memory_context}"
    from ai.llm_gateway import call_llm as _call_llm
    _gw = await _call_llm(system=system_prompt, messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="revenue_workspace")
    reply = _gw["text"].strip()
    await db.sovereign_memory.insert_one({
        "workspace_id": ws_id, "actor": user.id, "content": message[:500],
        "reply": reply[:500], "ts": datetime.now(timezone.utc).isoformat(),
    })
    return {"reply": reply, "workspace": ws["name"]}


# ── AI Resume Preview ─────────────────────────────────────────────────────────

@router.get("/revenue/resume/preview")
async def revenue_resume_preview(user: User = Depends(current_user)):
    portfolio   = await db.portfolio.find_one({"user_id": user.id}, {"_id": 0})
    credentials = await db.credentials.find({"user_id": user.id}, {"_id": 0, "title": 1, "issued_at": 1, "issuer": 1}).to_list(length=50)
    user_doc    = await db.users.find_one({"id": user.id}, {"_id": 0, "full_name": 1, "email": 1})
    return {
        "name":              user_doc.get("full_name", "") if user_doc else "",
        "email":             user_doc.get("email", "") if user_doc else "",
        "credentials":       credentials,
        "portfolio_bio":     (portfolio or {}).get("bio", ""),
        "portfolio_projects": (portfolio or {}).get("projects", []),
    }


# ── Help Guide ────────────────────────────────────────────────────────────────

class HelpGuideRequest(BaseModel):
    path:  str           = Field(..., min_length=1, max_length=500)
    query: Optional[str] = Field(default=None, max_length=500)


@router.post("/help/guide")
async def help_guide(body: HelpGuideRequest, user: User = Depends(current_user)):
    from help_guide import get_help_for
    return get_help_for(role=user.role, path=body.path, query=body.query)


# ── Bug Report ────────────────────────────────────────────────────────────────

class BugReportRequest(BaseModel):
    name:         str            = Field(..., min_length=1, max_length=200)
    email:        EmailStr
    venmoOrPaypal: str           = Field(..., min_length=1, max_length=200)
    whatYouTried: str            = Field(..., min_length=1, max_length=100)
    whatBroke:    str            = Field(..., min_length=1, max_length=2000)
    screenshot:   Optional[str] = None


@router.post("/bug-report")
async def submit_bug_report(body: BugReportRequest):
    try:
        report = {
            "id":           str(uuid.uuid4()),
            "name":         body.name.strip(),
            "email":        body.email,
            "venmoOrPaypal": body.venmoOrPaypal.strip(),
            "whatYouTried": body.whatYouTried.strip(),
            "whatBroke":    body.whatBroke.strip(),
            "screenshot":   body.screenshot,
            "submittedAt":  datetime.now(timezone.utc),
            "status":       "new",
        }
        await db["bug_reports"].insert_one(report)
        logger.info("Bug report submitted: %s — %s", body.email, body.whatYouTried)
        return {"ok": True, "message": "Bug report received. Thank you!"}
    except Exception as e:
        logger.exception("Bug report submission failed")
        raise HTTPException(500, f"Failed to submit bug report: {e}")


# ── Public Pricing ─────────────────────────────────────────────────────────────

@router.get("/prices/public")
async def prices_public():
    import app.database as _app_db
    if not _app_db._discount_manager:
        raise HTTPException(500, "Pricing system not initialized")
    from billing.models import TIER_PRICING
    discount = await _app_db._discount_manager.get_active_discount()
    pricing  = _app_db._discount_manager.get_pricing_with_discount(TIER_PRICING, discount)
    return pricing
