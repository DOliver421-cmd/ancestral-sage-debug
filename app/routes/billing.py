"""app/routes/billing.py — BillingModule API: credits, refunds, Sage sessions.

Separate from payments.py (which handles Stripe). This module handles:
  - Site credits ledger (add, deduct, balance)
  - Refund requests (site credits default; cash requires Supervisor approval)
  - Sage Counseling sessions (conduct-triggered)
  - Billing event history

All refund decisions run through ComplianceEngine before execution.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.models.user import User
from app.security.auth import current_user, require_role
from app.utils.audit import audit

router = APIRouter()


class CreditGrantReq(BaseModel):
    user_id: str
    amount_cents: int
    source: str
    reason: str


class SiteCreditRefundReq(BaseModel):
    user_id: str
    platform_cost_cents: int
    reason: str
    user_received_value: bool = False


class CashRefundReq(BaseModel):
    user_id: str
    amount_cents: int
    reason: str
    conditions: dict   # {is_extreme_violation, user_not_at_fault, is_legal, no_harm_to_wai, supervisor_approved}


class SageSessionReq(BaseModel):
    trigger_reason: str


class SageResolveReq(BaseModel):
    user_self_corrected: bool


# ── Credits ───────────────────────────────────────────────────────────────────

@router.get("/billing/credits/balance")
async def my_credit_balance(user: User = Depends(current_user)):
    from app.services.billing_service import get_credit_balance
    balance = await get_credit_balance(user.id)
    return {"user_id": user.id, "balance_cents": balance, "balance_dollars": round(balance / 100, 2)}


@router.get("/billing/credits/history")
async def my_credit_history(limit: int = 50, user: User = Depends(current_user)):
    from app.services.billing_service import list_credits
    return {"credits": await list_credits(user.id, limit=min(limit, 200))}


@router.post("/billing/credits/grant")
async def grant_credits(body: CreditGrantReq, user: User = Depends(require_role("admin"))):
    """Admin+: grant site credits to a user."""
    if body.amount_cents <= 0:
        raise HTTPException(400, "amount_cents must be positive")
    from app.services.billing_service import add_credits
    doc = await add_credits(body.user_id, body.amount_cents, body.source, body.reason, actor_id=user.id)
    await audit(user.id, "billing.credits.granted",
                meta={"target": body.user_id, "amount_cents": body.amount_cents, "reason": body.reason})
    return doc


@router.get("/billing/credits/user/{uid}")
async def user_credit_balance(uid: str, user: User = Depends(require_role("admin"))):
    from app.services.billing_service import get_credit_balance, list_credits
    balance = await get_credit_balance(uid)
    history = await list_credits(uid, limit=20)
    return {"user_id": uid, "balance_cents": balance, "recent": history}


# ── Refunds ───────────────────────────────────────────────────────────────────

@router.post("/billing/refunds/site-credits")
async def issue_site_credit_refund(body: SiteCreditRefundReq, user: User = Depends(require_role("admin"))):
    """
    Issue a site-credit refund. Default refund modality per blueprint.
    Amount = platform_cost + 10% fee if user received no value.
    """
    if body.platform_cost_cents < 0:
        raise HTTPException(400, "platform_cost_cents must be non-negative")
    from app.services.billing_service import issue_site_credit_refund
    refund = await issue_site_credit_refund(
        body.user_id, body.platform_cost_cents, body.reason, actor_id=user.id,
        user_received_value=body.user_received_value,
    )
    await audit(user.id, "billing.refund.site_credits",
                meta={"target": body.user_id, "amount": refund["amount"], "reason": body.reason})
    return refund


@router.post("/billing/refunds/cash")
async def request_cash_refund(body: CashRefundReq, user: User = Depends(require_role("executive_admin"))):
    """
    Executive-only: request a cash refund. All five conditions must be met and
    verified by ComplianceEngine before the refund record is created.
    """
    required_keys = {"is_extreme_violation", "user_not_at_fault", "is_legal", "no_harm_to_wai", "supervisor_approved"}
    missing = required_keys - set(body.conditions.keys())
    if missing:
        raise HTTPException(400, f"conditions missing required keys: {', '.join(sorted(missing))}")
    from app.services.billing_service import request_cash_refund
    refund = await request_cash_refund(
        body.user_id, body.amount_cents, body.reason, body.conditions, actor_id=user.id
    )
    await audit(user.id, "billing.refund.cash",
                meta={"target": body.user_id, "amount_cents": body.amount_cents})
    return refund


@router.get("/billing/refunds")
async def list_refunds(
    user_id: Optional[str] = None,
    limit: int = 50,
    user: User = Depends(require_role("admin")),
):
    from app.services.billing_service import list_refunds as _list
    return {"refunds": await _list(user_id=user_id, limit=min(limit, 200))}


# ── Billing events ────────────────────────────────────────────────────────────

@router.get("/billing/events")
async def list_billing_events(
    user_id: Optional[str] = None,
    limit: int = 50,
    user: User = Depends(require_role("admin")),
):
    from app.services.billing_service import list_billing_events
    return {"events": await list_billing_events(user_id=user_id, limit=min(limit, 200))}


@router.get("/billing/events/me")
async def my_billing_events(limit: int = 50, user: User = Depends(current_user)):
    from app.services.billing_service import list_billing_events
    return {"events": await list_billing_events(user_id=user.id, limit=min(limit, 100))}


# ── Sage Counseling ───────────────────────────────────────────────────────────

@router.post("/billing/sage-sessions")
async def start_sage_session(body: SageSessionReq, user: User = Depends(require_role("admin"))):
    """Admin+: initiate a Sage Counseling session for disrespectful conduct."""
    from app.services.billing_service import start_sage_counseling
    session = await start_sage_counseling(user.id, body.trigger_reason)
    await audit(user.id, "billing.sage_session.started",
                meta={"session_id": session["id"], "trigger": body.trigger_reason})
    return session


@router.post("/billing/sage-sessions/{session_id}/resolve")
async def resolve_sage_session(
    session_id: str,
    body: SageResolveReq,
    user: User = Depends(require_role("admin")),
):
    from app.services.billing_service import resolve_sage_session
    result = await resolve_sage_session(session_id, body.user_self_corrected, actor_id=user.id)
    log_key = "sage_fee_waived" if body.user_self_corrected else "user_refused_deescalation"
    await audit(user.id, f"billing.sage_session.{log_key}", meta={"session_id": session_id})
    return result


@router.get("/billing/sage-sessions")
async def list_sage_sessions(
    user_id: Optional[str] = None,
    limit: int = 50,
    user: User = Depends(require_role("admin")),
):
    from app.services.billing_service import list_sage_sessions
    return {"sessions": await list_sage_sessions(user_id=user_id, limit=min(limit, 200))}
