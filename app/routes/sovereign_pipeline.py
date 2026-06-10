"""app/routes/sovereign_pipeline.py — Sovereign pipeline tracker.

CRUD for booking/revenue pipeline records. Executive-admin only.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import db
from app.models.user import User
from app.security.auth import require_role

logger = logging.getLogger("lcewai")
router = APIRouter()

# ── Stage config ──────────────────────────────────────────────────────────────

STAGE_ORDER = [
    "Prospecting", "Outreach", "Conversation", "Proposal",
    "Negotiation", "Confirmed", "Delivered", "Lost",
]
STAGE_RANK = {s: i for i, s in enumerate(STAGE_ORDER)}
STAGE_PROBABILITY = {
    "Prospecting": 0.05,
    "Outreach": 0.10,
    "Conversation": 0.25,
    "Proposal": 0.40,
    "Negotiation": 0.65,
    "Confirmed": 1.0,
    "Delivered": 1.0,
    "Lost": 0.0,
}
CLOSED_STAGES = {"Confirmed", "Delivered"}
COLLECTION = "sovereign_pipeline"


# ── Pydantic models ───────────────────────────────────────────────────────────

class PipelineRecordCreate(BaseModel):
    institution: str
    vertical: Optional[str] = "Corporate"
    stage: Optional[str] = "Prospecting"
    contact_name: Optional[str] = ""
    contact_email: Optional[str] = ""
    contact_title: Optional[str] = ""
    fee_offered: Optional[int] = 0
    fee_floor: Optional[int] = 0
    hos_score: Optional[float] = 0.0
    event_date: Optional[str] = None
    notes: Optional[str] = ""
    grant_pipeline: Optional[bool] = False


class PipelineRecordPatch(BaseModel):
    institution: Optional[str] = None
    vertical: Optional[str] = None
    stage: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_title: Optional[str] = None
    fee_offered: Optional[int] = None
    fee_floor: Optional[int] = None
    hos_score: Optional[float] = None
    close_probability: Optional[float] = None
    event_date: Optional[str] = None
    notes: Optional[str] = None
    grant_pipeline: Optional[bool] = None


class ParseCommandBody(BaseModel):
    message: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize(doc: dict) -> dict:
    doc.pop("_id", None)
    for f in ("created_at", "updated_at"):
        if hasattr(doc.get(f), "isoformat"):
            doc[f] = doc[f].isoformat()
    return doc


def _summary(records: list) -> dict:
    confirmed_revenue = 0
    weighted_pipeline = 0
    by_stage: dict = {}
    for r in records:
        stage = r.get("stage", "Prospecting")
        by_stage[stage] = by_stage.get(stage, 0) + 1
        fee = r.get("fee_offered", 0) or 0
        prob = r.get("close_probability", STAGE_PROBABILITY.get(stage, 0.0))
        if stage in CLOSED_STAGES:
            confirmed_revenue += fee
        else:
            weighted_pipeline += fee * prob
    return {
        "total_count": len(records),
        "confirmed_revenue": confirmed_revenue,
        "weighted_pipeline": weighted_pipeline,
        "by_stage": by_stage,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/sovereign/pipeline")
async def list_pipeline(user: User = Depends(require_role("executive_admin"))):
    try:
        docs = await db[COLLECTION].find({"user_id": user.id}, {"_id": 0}).to_list(1000)
    except Exception as e:
        logger.exception("Pipeline list error")
        raise HTTPException(502, f"Database error: {e}")
    docs.sort(key=lambda d: (STAGE_RANK.get(d.get("stage", "Prospecting"), 99), -(d.get("hos_score") or 0)))
    serialized = [_serialize(d) for d in docs]
    return {"records": serialized, "summary": _summary(docs)}


@router.post("/sovereign/pipeline", status_code=201)
async def create_pipeline_record(
    body: PipelineRecordCreate,
    user: User = Depends(require_role("executive_admin")),
):
    stage = body.stage if body.stage in STAGE_PROBABILITY else "Prospecting"
    now = datetime.now(timezone.utc)
    doc = {
        "id": str(uuid4()),
        "user_id": user.id,
        "institution": body.institution,
        "vertical": body.vertical or "Corporate",
        "stage": stage,
        "contact_name": body.contact_name or "",
        "contact_email": body.contact_email or "",
        "contact_title": body.contact_title or "",
        "fee_offered": body.fee_offered or 0,
        "fee_floor": body.fee_floor or 0,
        "hos_score": body.hos_score or 0.0,
        "close_probability": STAGE_PROBABILITY[stage],
        "event_date": body.event_date,
        "notes": body.notes or "",
        "grant_pipeline": body.grant_pipeline or False,
        "created_at": now,
        "updated_at": now,
    }
    try:
        await db[COLLECTION].insert_one(doc)
    except Exception as e:
        logger.exception("Pipeline create error")
        raise HTTPException(502, f"Database error: {e}")
    return _serialize(doc)


@router.patch("/sovereign/pipeline/{record_id}")
async def update_pipeline_record(
    record_id: str,
    body: PipelineRecordPatch,
    user: User = Depends(require_role("executive_admin")),
):
    existing = await db[COLLECTION].find_one({"id": record_id, "user_id": user.id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Record not found")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "stage" in updates and updates["stage"] in STAGE_PROBABILITY:
        if "close_probability" not in updates:
            updates["close_probability"] = STAGE_PROBABILITY[updates["stage"]]
    updates["updated_at"] = datetime.now(timezone.utc)
    try:
        await db[COLLECTION].update_one({"id": record_id, "user_id": user.id}, {"$set": updates})
    except Exception as e:
        raise HTTPException(502, f"Database error: {e}")
    existing.update(updates)
    return _serialize(existing)


@router.delete("/sovereign/pipeline/{record_id}")
async def delete_pipeline_record(
    record_id: str,
    user: User = Depends(require_role("executive_admin")),
):
    result = await db[COLLECTION].delete_one({"id": record_id, "user_id": user.id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Record not found")
    return {"deleted": True}


@router.post("/sovereign/pipeline/parse")
async def parse_pipeline_command(
    body: ParseCommandBody,
    user: User = Depends(require_role("executive_admin")),
):
    """Parse a natural-language pipeline command via AI and execute it."""
    import httpx
    key = os.environ.get("ANTHROPIC_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
    if not key:
        raise HTTPException(503, "No AI key configured")

    parse_system = (
        "You are a pipeline command parser. Given a user message, extract the pipeline action.\n"
        "Return JSON only — no other text.\n"
        "Schema: {\"action\": \"create\"|\"update_stage\"|\"update_fee\"|\"delete\"|null, "
        "\"institution\": str, \"stage\": str|null, \"fee_cents\": int|null}\n"
        "Valid stages: Prospecting, Outreach, Conversation, Proposal, Negotiation, Confirmed, Delivered, Lost\n"
        "Examples:\n"
        "  'add Stanford to pipeline' → {\"action\":\"create\",\"institution\":\"Stanford\",\"stage\":\"Prospecting\",\"fee_cents\":null}\n"
        "  'move Yale to Proposal' → {\"action\":\"update_stage\",\"institution\":\"Yale\",\"stage\":\"Proposal\",\"fee_cents\":null}\n"
        "  'mark Google as confirmed' → {\"action\":\"update_stage\",\"institution\":\"Google\",\"stage\":\"Confirmed\",\"fee_cents\":null}\n"
        "  'set fee for MIT 500000' → {\"action\":\"update_fee\",\"institution\":\"MIT\",\"stage\":null,\"fee_cents\":50000000}\n"
        "  'remove Harvard from pipeline' → {\"action\":\"delete\",\"institution\":\"Harvard\",\"stage\":null,\"fee_cents\":null}\n"
        "If not a pipeline command, return {\"action\": null}"
    )

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={
                    "model": "claude-haiku-4-5",
                    "max_tokens": 256,
                    "system": parse_system,
                    "messages": [{"role": "user", "content": body.message}],
                },
            )
            r.raise_for_status()
            raw = r.json()["content"][0]["text"].strip()
    except Exception as e:
        raise HTTPException(502, f"AI parse error: {e}")

    import json as _json
    try:
        cmd = _json.loads(raw)
    except Exception:
        return {"executed": False, "message": "Could not parse command"}

    if not cmd.get("action"):
        return {"executed": False, "message": "Not a pipeline command"}

    action = cmd["action"]
    institution = cmd.get("institution", "")
    stage = cmd.get("stage")
    fee_cents = cmd.get("fee_cents")

    if action == "create":
        stage = stage if stage in STAGE_PROBABILITY else "Prospecting"
        now = datetime.now(timezone.utc)
        doc = {
            "id": str(uuid4()),
            "user_id": user.id,
            "institution": institution,
            "vertical": "Corporate",
            "stage": stage,
            "contact_name": "", "contact_email": "", "contact_title": "",
            "fee_offered": fee_cents or 0,
            "fee_floor": 0,
            "hos_score": 0.0,
            "close_probability": STAGE_PROBABILITY[stage],
            "event_date": None, "notes": "",
            "grant_pipeline": False,
            "created_at": now, "updated_at": now,
        }
        await db[COLLECTION].insert_one(doc)
        return {"executed": True, "action": "created", "institution": institution, "stage": stage}

    if action in ("update_stage", "update_fee"):
        existing = await db[COLLECTION].find_one(
            {"user_id": user.id, "institution": {"$regex": institution, "$options": "i"}},
            {"_id": 0}
        )
        if not existing:
            return {"executed": False, "message": f"No pipeline record found for '{institution}'"}
        updates: dict = {"updated_at": datetime.now(timezone.utc)}
        if action == "update_stage" and stage in STAGE_PROBABILITY:
            updates["stage"] = stage
            updates["close_probability"] = STAGE_PROBABILITY[stage]
        if action == "update_fee" and fee_cents is not None:
            updates["fee_offered"] = fee_cents
        await db[COLLECTION].update_one({"id": existing["id"]}, {"$set": updates})
        return {"executed": True, "action": action, "institution": institution, **updates}

    if action == "delete":
        result = await db[COLLECTION].delete_one(
            {"user_id": user.id, "institution": {"$regex": institution, "$options": "i"}}
        )
        if result.deleted_count:
            return {"executed": True, "action": "deleted", "institution": institution}
        return {"executed": False, "message": f"No pipeline record found for '{institution}'"}

    return {"executed": False, "message": "Unknown action"}
