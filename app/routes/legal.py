"""app/routes/legal.py — Legal tool gating: consent management + gated guide endpoints.

Routes:
  POST   /api/legal/consent            — Record disclaimer acknowledgement
  GET    /api/legal/consent/status     — Check active consent for a tool
  DELETE /api/legal/consent            — Revoke consent
  POST   /api/legal/guide              — Legal Document Guide (premium + consent)
  POST   /api/legal/advisor            — Legal Situation Advisor (premium + consent)

All legal tool access:
  - Requires authentication (no anonymous access)
  - Requires premium or executive tier
  - Requires explicit consent record in DB
  - Is fully logged (every call to guide/advisor endpoints)
  - Returns disclaimer text in all 403 responses
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, field_validator

from app.database import db
from app.models.user import User
from app.security.auth import current_user
from app.security.enforcement import require_legal_consent, _resolve_user_tier
from app.security.feature_tiers import LEGAL_TOOL_POLICIES, tier_meets_minimum
from app.utils.audit import audit

logger = logging.getLogger("lcewai")

router = APIRouter(tags=["legal"])


# ── Request / response models ────────────────────────────────────────────────

class LegalConsentReq(BaseModel):
    tool_key: str           # "legal_guide_1" or "legal_guide_2"
    acknowledged: bool      # Must be True; client confirms disclaimer was shown

    @field_validator("tool_key")
    @classmethod
    def _valid_tool(cls, v: str) -> str:
        if v not in ("legal_guide_1", "legal_guide_2"):
            raise ValueError("tool_key must be 'legal_guide_1' or 'legal_guide_2'")
        return v

    @field_validator("acknowledged")
    @classmethod
    def _must_ack(cls, v: bool) -> bool:
        if not v:
            raise ValueError("acknowledged must be true to record consent")
        return v


class LegalConsentRevokeReq(BaseModel):
    tool_key: str

    @field_validator("tool_key")
    @classmethod
    def _valid_tool(cls, v: str) -> str:
        if v not in ("legal_guide_1", "legal_guide_2"):
            raise ValueError("tool_key must be 'legal_guide_1' or 'legal_guide_2'")
        return v


class LegalGuideReq(BaseModel):
    question: str
    context: Optional[str] = None
    document_text: Optional[str] = None   # optional document snippet for guide


class LegalAdvisorReq(BaseModel):
    situation: str
    context: Optional[str] = None
    jurisdiction: Optional[str] = None


# ── Helper ───────────────────────────────────────────────────────────────────

async def _get_active_consent(user_id: str, tool_key: str) -> Optional[dict]:
    """Return the active (non-revoked) consent record or None."""
    if db is None:
        return None
    return await db.legal_consents.find_one(
        {"user_id": user_id, "tool_key": tool_key, "revoked": {"$ne": True}},
        {"_id": 0},
    )


# ── POST /legal/consent ───────────────────────────────────────────────────────

@router.post("/legal/consent")
async def record_legal_consent(
    body: LegalConsentReq,
    request: Request,
    user: User = Depends(current_user),
):
    """Record explicit disclaimer acknowledgement for a legal tool.

    Requires:
    - Authentication
    - Premium or executive tier

    Idempotent: re-submitting creates a fresh consent record (previous is not revoked).
    """
    user_tier = await _resolve_user_tier(user.id)
    if not tier_meets_minimum(user_tier, "premium"):
        policy = LEGAL_TOOL_POLICIES.get(body.tool_key, LEGAL_TOOL_POLICIES["legal_guide_1"])
        raise HTTPException(
            status_code=403,
            detail={
                "error":        "legal_tool_premium_required",
                "message":      f"'{policy.feature_name}' is available on Premium and Executive plans only.",
                "current_tier": user_tier,
                "upgrade_url":  "/pricing",
                "disclaimer":   policy.disclaimer_text,
            },
        )

    policy = LEGAL_TOOL_POLICIES[body.tool_key]
    consent_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    record = {
        "id":          consent_id,
        "user_id":     user.id,
        "tool_key":    body.tool_key,
        "feature":     policy.feature_name,
        "acknowledged": True,
        "revoked":     False,
        "created_at":  now,
        "ip":          (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
                       or (request.client.host if request.client else "unknown"),
    }

    if db is not None:
        await db.legal_consents.insert_one({**record, "_id": consent_id})

    await audit(
        user.id,
        "legal_consent.recorded",
        meta={"tool_key": body.tool_key, "consent_id": consent_id, "tier": user_tier},
    )

    logger.info("Legal consent recorded: user=%s tool=%s consent=%s", user.id, body.tool_key, consent_id)

    return {
        "consent_id":  consent_id,
        "tool_key":    body.tool_key,
        "feature":     policy.feature_name,
        "recorded_at": now.isoformat(),
        "disclaimer":  policy.disclaimer_text,
        "message":     "Consent recorded. You may now access this legal tool.",
    }


# ── GET /legal/consent/status ─────────────────────────────────────────────────

@router.get("/legal/consent/status")
async def legal_consent_status(
    tool_key: str,
    user: User = Depends(current_user),
):
    """Return whether the authenticated user has active consent for a legal tool."""
    if tool_key not in ("legal_guide_1", "legal_guide_2"):
        raise HTTPException(400, detail={"error": "invalid_tool_key", "message": "tool_key must be 'legal_guide_1' or 'legal_guide_2'"})

    policy = LEGAL_TOOL_POLICIES[tool_key]
    user_tier = await _resolve_user_tier(user.id)
    consent = await _get_active_consent(user.id, tool_key)

    return {
        "tool_key":      tool_key,
        "feature":       policy.feature_name,
        "tier_eligible": tier_meets_minimum(user_tier, "premium"),
        "has_consent":   consent is not None,
        "consent_id":    consent["id"] if consent else None,
        "consented_at":  consent["created_at"].isoformat() if consent and isinstance(consent.get("created_at"), datetime) else None,
        "disclaimer":    policy.disclaimer_text,
    }


# ── DELETE /legal/consent ─────────────────────────────────────────────────────

@router.delete("/legal/consent")
async def revoke_legal_consent(
    body: LegalConsentRevokeReq,
    user: User = Depends(current_user),
):
    """Revoke all active consent records for a legal tool."""
    if db is not None:
        result = await db.legal_consents.update_many(
            {"user_id": user.id, "tool_key": body.tool_key, "revoked": {"$ne": True}},
            {"$set": {"revoked": True, "revoked_at": datetime.now(timezone.utc)}},
        )
        revoked_count = result.modified_count
    else:
        revoked_count = 0

    await audit(
        user.id,
        "legal_consent.revoked",
        meta={"tool_key": body.tool_key, "revoked_count": revoked_count},
    )

    return {
        "tool_key":      body.tool_key,
        "revoked_count": revoked_count,
        "message":       "Consent revoked. Access to this legal tool has been suspended.",
    }


# ── POST /legal/guide ─────────────────────────────────────────────────────────

@router.post("/legal/guide")
async def legal_document_guide(
    body: LegalGuideReq,
    request: Request,
    user: User = Depends(require_legal_consent("legal_guide_1")),
):
    """Legal Document Guide — general legal information tool.

    Enforcement (via require_legal_consent dependency):
    - Authenticated
    - Premium or executive tier
    - Active consent record in DB
    - Every access audited

    Returns general legal information. NOT legal advice.
    """
    policy = LEGAL_TOOL_POLICIES["legal_guide_1"]

    import app.database as _app_db
    ai_client = getattr(_app_db, "_openai_client", None)

    system_prompt = (
        "You are a legal information assistant. You provide general legal information "
        "to help users understand legal documents, terminology, and general legal concepts. "
        "IMPORTANT: You do NOT provide legal advice. You do NOT form an attorney-client "
        "relationship. Always remind users to consult a licensed attorney for advice specific "
        "to their situation. Be clear, factual, and educational."
    )

    user_message = body.question
    if body.document_text:
        user_message = f"Document excerpt:\n\n{body.document_text[:4000]}\n\nQuestion: {body.question}"
    if body.context:
        user_message += f"\n\nAdditional context: {body.context}"

    if ai_client is None:
        return {
            "answer":     "Legal information service is temporarily unavailable. Please try again later.",
            "disclaimer": policy.disclaimer_text,
            "tool":       policy.feature_name,
        }

    try:
        response = await ai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1500,
            temperature=0.3,
        )
        answer = response.choices[0].message.content
    except Exception as exc:
        logger.error("Legal guide AI error: %s", exc)
        raise HTTPException(502, detail={"error": "ai_unavailable", "message": "Legal information service temporarily unavailable."})

    return {
        "answer":     answer,
        "disclaimer": policy.disclaimer_text,
        "tool":       policy.feature_name,
    }


# ── POST /legal/advisor ───────────────────────────────────────────────────────

@router.post("/legal/advisor")
async def legal_situation_advisor(
    body: LegalAdvisorReq,
    request: Request,
    user: User = Depends(require_legal_consent("legal_guide_2")),
):
    """Legal Situation Advisor — helps users understand legal situations.

    Enforcement (via require_legal_consent dependency):
    - Authenticated
    - Premium or executive tier
    - Active consent record in DB
    - Every access audited

    Returns general legal information. NOT legal advice.
    """
    policy = LEGAL_TOOL_POLICIES["legal_guide_2"]

    import app.database as _app_db
    ai_client = getattr(_app_db, "_openai_client", None)

    system_prompt = (
        "You are a legal situation advisor providing general legal information. "
        "You help users understand the general legal landscape of their situation — "
        "what area of law may apply, what processes generally look like, and what "
        "kinds of professionals they should consult. "
        "CRITICAL: You do NOT provide legal advice. You do NOT tell users what they "
        "should do legally. You do NOT form an attorney-client relationship. "
        "Always recommend consulting a licensed attorney for situation-specific advice."
    )

    user_message = f"Situation: {body.situation}"
    if body.jurisdiction:
        user_message += f"\nJurisdiction: {body.jurisdiction}"
    if body.context:
        user_message += f"\nAdditional context: {body.context}"

    if ai_client is None:
        return {
            "analysis":   "Legal information service is temporarily unavailable. Please try again later.",
            "disclaimer": policy.disclaimer_text,
            "tool":       policy.feature_name,
        }

    try:
        response = await ai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1500,
            temperature=0.3,
        )
        analysis = response.choices[0].message.content
    except Exception as exc:
        logger.error("Legal advisor AI error: %s", exc)
        raise HTTPException(502, detail={"error": "ai_unavailable", "message": "Legal information service temporarily unavailable."})

    return {
        "analysis":   analysis,
        "disclaimer": policy.disclaimer_text,
        "tool":       policy.feature_name,
    }
