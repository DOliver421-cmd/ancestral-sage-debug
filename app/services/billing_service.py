"""app/services/billing_service.py — BillingService: credits, refunds, Sage sessions.

Implements the SYSTEM_RECONSTRUCTION_BLUEPRINT billing principles:
  - Never charge for value not delivered
  - Default refund = Site Credits (platform_cost + 10% processing fee if applicable)
  - Cash refunds require all five conditions + Supervisor approval
  - Respect required for resolution; disrespect triggers Sage Counseling

Collections:
  billing_events  — immutable log of all billing activity
  credits         — per-user credit ledger (additive; use balance aggregation to read)
  refunds         — refund records linked to supervisor decisions
  sage_sessions   — counseling sessions triggered by disrespectful conduct
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from app.database import db

_NOW = lambda: datetime.now(timezone.utc).isoformat()

PROCESSING_FEE_RATE = 0.10   # 10% on top of platform cost when no value delivered
SAGE_FEE_CENTS      = 300    # $3.00 for Sage Counseling session


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _billing_event(
    user_id: str,
    event_type: str,
    amount_cents: int,
    currency: str = "usd",
    metadata: Optional[dict] = None,
) -> dict:
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": event_type,
        "amount": amount_cents,
        "currency": currency,
        "metadata_json": metadata or {},
        "created_at": _NOW(),
    }
    await db.billing_events.insert_one(doc)
    doc.pop("_id", None)
    return doc


# ── Credits ───────────────────────────────────────────────────────────────────

async def add_credits(
    user_id: str,
    amount_cents: int,
    source: str,
    reason: str,
    actor_id: str = "system",
) -> dict:
    """Add credits to a user's account. Returns the credit record."""
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "amount": amount_cents,
        "source": source,
        "reason": reason,
        "granted_by": actor_id,
        "created_at": _NOW(),
    }
    await db.credits.insert_one(doc)
    doc.pop("_id", None)
    await _billing_event(user_id, "credit_added", amount_cents, metadata={"source": source, "reason": reason})
    return doc


async def get_credit_balance(user_id: str) -> int:
    """Return total credit balance in cents via aggregation."""
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    result = await db.credits.aggregate(pipeline).to_list(1)
    return (result[0]["total"] if result else 0)


async def deduct_credits(user_id: str, amount_cents: int, reason: str) -> dict:
    """Record a credit deduction (negative amount entry)."""
    balance = await get_credit_balance(user_id)
    if balance < amount_cents:
        from fastapi import HTTPException
        raise HTTPException(402, f"Insufficient credits: balance={balance}¢, required={amount_cents}¢")
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "amount": -amount_cents,
        "source": "deduction",
        "reason": reason,
        "created_at": _NOW(),
    }
    await db.credits.insert_one(doc)
    doc.pop("_id", None)
    await _billing_event(user_id, "credit_deducted", amount_cents, metadata={"reason": reason})
    return doc


async def list_credits(user_id: str, limit: int = 50) -> list[dict]:
    cursor = db.credits.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ── Refunds ───────────────────────────────────────────────────────────────────

async def issue_site_credit_refund(
    user_id: str,
    platform_cost_cents: int,
    reason: str,
    actor_id: str,
    user_received_value: bool = False,
) -> dict:
    """
    Issue a site-credit refund per blueprint rules.

    If user_received_value=False: credit = platform_cost + 10% processing fee.
    If user_received_value=True:  credit = platform_cost (no processing fee — value was delivered).
    """
    if user_received_value:
        refund_amount = platform_cost_cents
    else:
        refund_amount = int(platform_cost_cents * (1 + PROCESSING_FEE_RATE))

    credit_doc = await add_credits(
        user_id, refund_amount, "refund", reason, actor_id=actor_id
    )
    refund_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "amount": refund_amount,
        "mode": "site_credits",
        "reason": reason,
        "supervisor_decision_id": None,
        "credit_id": credit_doc["id"],
        "created_at": _NOW(),
        "processed_by": actor_id,
    }
    await db.refunds.insert_one(refund_doc)
    refund_doc.pop("_id", None)
    await _billing_event(user_id, "refund_issued", refund_amount,
                         metadata={"mode": "site_credits", "reason": reason})
    return refund_doc


async def request_cash_refund(
    user_id: str,
    amount_cents: int,
    reason: str,
    conditions: dict,
    actor_id: str,
) -> dict:
    """
    Request a cash refund. Runs ComplianceEngine before proceeding.

    conditions must contain all five keys:
      is_extreme_violation, user_not_at_fault, is_legal, no_harm_to_wai, supervisor_approved
    """
    from app.services.compliance_engine import ComplianceEngine, Verdict

    ctx = {
        "is_legal_related": True,
        "is_clear": True,
        "is_action_legal": conditions.get("is_legal", False) or None,
        "benefits_platform_only": False,
        "harms_wai": not conditions.get("no_harm_to_wai", False) or None,
        "harms_user": False,
        "refund_mode": "cash",
        "cash_refund_conditions": conditions,
        "user_received_value": True,  # cash refund path assumes this was a violation scenario
        "charge_amount": amount_cents,
        "platform_cost": amount_cents,
    }
    compliance = await ComplianceEngine.evaluate(
        "billing.refund.cash", "system", actor_id, ctx
    )
    if not compliance.passed:
        from fastapi import HTTPException
        raise HTTPException(403, compliance.message)

    refund_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "amount": amount_cents,
        "mode": "cash",
        "reason": reason,
        "supervisor_decision_id": compliance.decision_id,
        "conditions_json": conditions,
        "created_at": _NOW(),
        "processed_by": actor_id,
    }
    await db.refunds.insert_one(refund_doc)
    refund_doc.pop("_id", None)
    await _billing_event(user_id, "cash_refund_approved", amount_cents,
                         metadata={"mode": "cash", "reason": reason})
    return refund_doc


async def list_refunds(user_id: Optional[str] = None, limit: int = 50) -> list[dict]:
    filt = {}
    if user_id:
        filt["user_id"] = user_id
    cursor = db.refunds.find(filt, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ── Sage Counseling sessions ──────────────────────────────────────────────────

async def start_sage_counseling(
    user_id: str,
    trigger_reason: str,
) -> dict:
    """
    Initiate a Sage Counseling session for disrespectful conduct.
    Applies $3 tentative fee and a 5-minute delay flag.
    """
    session = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "status": "pending_correction",
        "fee_amount": SAGE_FEE_CENTS,
        "fee_waived": False,
        "delay_minutes": 5,
        "delay_removed": False,
        "trigger_reason": trigger_reason,
        "notes_json": {},
        "started_at": _NOW(),
        "completed_at": None,
        "waived": False,
    }
    await db.sage_sessions.insert_one(session)
    session.pop("_id", None)

    # Compliance event for the session initiation
    from app.services.compliance_engine import _log_compliance_event, Verdict
    await _log_compliance_event(
        "sage_counseling.initiated", "user", user_id, Verdict.ESCALATE,
        {"session_id": session["id"], "trigger": trigger_reason},
    )
    return session


async def resolve_sage_session(
    session_id: str,
    user_self_corrected: bool,
    actor_id: str,
) -> dict:
    """
    Resolve a Sage session.
    - If user self-corrected: waive fee, remove delay, return to normal flow.
    - If refused: escalate.
    """
    now = _NOW()
    if user_self_corrected:
        update = {
            "status": "resolved_corrected",
            "fee_amount": 0,
            "fee_waived": True,
            "delay_removed": True,
            "waived": True,
            "completed_at": now,
            "resolved_by": actor_id,
        }
        log_key = "sage_fee_waived"
    else:
        update = {
            "status": "escalated",
            "completed_at": now,
            "resolved_by": actor_id,
        }
        log_key = "user_refused_deescalation"

    result = await db.sage_sessions.update_one({"id": session_id}, {"$set": update})
    if not result.matched_count:
        from fastapi import HTTPException
        raise HTTPException(404, "Sage session not found")

    from app.services.compliance_engine import _log_compliance_event, Verdict
    v = Verdict.PASS if user_self_corrected else Verdict.ESCALATE
    doc = await db.sage_sessions.find_one({"id": session_id}, {"_id": 0})
    await _log_compliance_event(
        f"sage_counseling.{update['status']}", "user", doc.get("user_id", ""),
        v, {"session_id": session_id, "log_key": log_key},
    )
    return doc


async def list_sage_sessions(user_id: Optional[str] = None, limit: int = 50) -> list[dict]:
    filt = {}
    if user_id:
        filt["user_id"] = user_id
    cursor = db.sage_sessions.find(filt, {"_id": 0}).sort("started_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ── Billing events read ───────────────────────────────────────────────────────

async def list_billing_events(user_id: Optional[str] = None, limit: int = 50) -> list[dict]:
    filt = {}
    if user_id:
        filt["user_id"] = user_id
    cursor = db.billing_events.find(filt, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)
