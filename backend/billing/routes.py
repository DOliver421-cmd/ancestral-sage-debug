"""
WAI Institute Billing API Routes
Subscription/invoice tracking, creator finance, and financial reporting.

Payments run through Lemon Squeezy → Gumroad (see server.py /payments/* and
ai/publishing.py). Stripe was fully removed from this platform — no Stripe
SDK, webhooks, or connect payouts exist here.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import List, Optional
from datetime import datetime

import jwt as _jwt

from .models import Invoice
from .financial_reporting import FinancialReportingService

_JWT_SECRET = os.environ.get("JWT_SECRET", "")
_JWT_ALGO = os.environ.get("JWT_ALGORITHM", "HS256")


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> dict:
    """Validate JWT and return user dict, mirroring server.py's current_user dependency."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = _jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGO])
    except _jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except _jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    if not user_doc.get("active", True):
        raise HTTPException(status_code=403, detail="Account deactivated")
    return user_doc

router = APIRouter(prefix="/billing", tags=["billing"])


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_financial_service(request: Request) -> FinancialReportingService:
    """Get financial reporting service from app state"""
    return request.app.state.financial_service


# ============================================================================
# INVOICE ENDPOINTS
# ============================================================================

@router.get("/invoices", response_model=List[Invoice])
async def get_invoices(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    limit: int = 10,
):
    """
    Get user's invoice history
    Paginated, most recent first

    Query params:
    - limit: Number of invoices to return (default 10)
    """
    invoices_collection = request.app.state.db.invoices
    subscriptions_collection = request.app.state.db.subscriptions

    # Get user's subscriptions
    user_subs = await subscriptions_collection.find({
        "user_id": current_user["id"]
    }).to_list(None)

    sub_ids = [str(sub["_id"]) for sub in user_subs]

    # Get invoices for those subscriptions
    invoices = await invoices_collection.find({
        "subscription_id": {"$in": sub_ids}
    }).sort("issued_date", -1).limit(limit).to_list(None)

    return [Invoice(**inv, id=str(inv["_id"])) for inv in invoices]


# ============================================================================
# CREATOR FINANCE ENDPOINTS
# ============================================================================

@router.get("/creator/balance")
async def get_creator_balance(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Get creator's current accrued balance"""
    creator_balances = request.app.state.db.creator_balances

    balance_doc = await creator_balances.find_one({
        "creator_id": current_user["id"]
    })

    if not balance_doc:
        return {
            "amount_available": 0.0,
            "amount_held_chargebacks": 0.0,
            "amount_pending": 0.0,
        }

    return {
        "amount_available": balance_doc.get("amount_available", 0),
        "amount_held_chargebacks": balance_doc.get("amount_held_chargebacks", 0),
        "amount_pending": balance_doc.get("amount_pending", 0),
    }


@router.get("/creator/payouts")
async def get_creator_payouts(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    limit: int = 20,
):
    """Get creator's payout history"""
    creator_payouts = request.app.state.db.creator_payouts

    payouts = await creator_payouts.find({
        "creator_id": current_user["id"]
    }).sort("requested_date", -1).limit(limit).to_list(None)

    return [{
        "id": str(p["_id"]),
        "amount": p["amount_paid"],
        "status": p["status"],
        "requested_date": p["requested_date"],
        "paid_date": p["paid_date"],
    } for p in payouts]


# ============================================================================
# FINANCIAL REPORTING ENDPOINTS
# ============================================================================

@router.get("/reporting/summary")
async def get_financial_dashboard(
    financial_service: FinancialReportingService = Depends(get_financial_service),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Get complete financial dashboard summary - all key metrics

    ✅ Authorization: Admin/steward only
    ✅ Audit logged for sensitive data access
    """
    # Only admins, stewards, and executives can access financial reporting
    allowed_roles = ["admin", "oversight", "oversight", "executive_admin"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="Financial reporting access denied")

    # Audit log financial data access
    try:
        audit_fn = getattr(request.app, "audit", None)
        if audit_fn:
            await audit_fn(
                actor_id=current_user["id"],
                action="financial_reporting.summary_accessed",
                target="financial_reporting",
                meta={"severity": "high"}
            )
    except Exception:
        pass

    return await financial_service.get_dashboard_summary()


@router.get("/reporting/mrr")
async def get_monthly_recurring_revenue(
    financial_service: FinancialReportingService = Depends(get_financial_service),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Get current MRR (Monthly Recurring Revenue)

    ✅ Authorization: Admin/steward only
    """
    allowed_roles = ["admin", "oversight", "oversight", "executive_admin"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="Financial reporting access denied")

    try:
        audit_fn = getattr(request.app, "audit", None)
        if audit_fn:
            await audit_fn(actor_id=current_user["id"], action="financial_reporting.mrr_accessed", target="mrr")
    except Exception:
        pass

    return {"mrr": await financial_service.get_mrr()}


@router.get("/reporting/revenue/{year}/{month}")
async def get_revenue_summary(
    year: int,
    month: int,
    financial_service: FinancialReportingService = Depends(get_financial_service),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Get revenue summary for specific month

    ✅ Authorization: Admin/steward only
    """
    allowed_roles = ["admin", "oversight", "oversight", "executive_admin"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="Financial reporting access denied")

    try:
        audit_fn = getattr(request.app, "audit", None)
        if audit_fn:
            await audit_fn(
                actor_id=current_user["id"],
                action="financial_reporting.revenue_accessed",
                target=f"revenue:{year}:{month}"
            )
    except Exception:
        pass

    return await financial_service.get_monthly_revenue_summary(year, month)


@router.get("/reporting/ltv-cac")
async def get_ltv_metrics(
    financial_service: FinancialReportingService = Depends(get_financial_service),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Get LTV (Lifetime Value) and CAC (Customer Acquisition Cost) metrics

    ✅ Authorization: Admin/steward only
    """
    allowed_roles = ["admin", "oversight", "oversight", "executive_admin"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="Financial reporting access denied")

    try:
        audit_fn = getattr(request.app, "audit", None)
        if audit_fn:
            await audit_fn(actor_id=current_user["id"], action="financial_reporting.ltv_cac_accessed", target="ltv_cac")
    except Exception:
        pass

    return await financial_service.get_ltv_cac()


@router.get("/reporting/nrr")
async def get_net_revenue_retention(
    financial_service: FinancialReportingService = Depends(get_financial_service),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Get NRR (Net Revenue Retention) - measure of expansion/contraction

    ✅ Authorization: Admin/steward only
    """
    allowed_roles = ["admin", "oversight", "oversight", "executive_admin"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="Financial reporting access denied")

    try:
        audit_fn = getattr(request.app, "audit", None)
        if audit_fn:
            await audit_fn(actor_id=current_user["id"], action="financial_reporting.nrr_accessed", target="nrr")
    except Exception:
        pass

    return {"nrr": await financial_service.get_nrr()}


@router.get("/reporting/cohort-analysis")
async def get_retention_cohorts(
    financial_service: FinancialReportingService = Depends(get_financial_service),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Get cohort analysis - retention by signup cohort

    ✅ Authorization: Admin/steward only
    """
    allowed_roles = ["admin", "oversight", "oversight", "executive_admin"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="Financial reporting access denied")

    try:
        audit_fn = getattr(request.app, "audit", None)
        if audit_fn:
            await audit_fn(actor_id=current_user["id"], action="financial_reporting.cohort_accessed", target="cohort")
    except Exception:
        pass

    return await financial_service.get_cohort_analysis()


@router.get("/reporting/forecast")
async def get_cash_flow_forecast(
    months: int = 12,
    financial_service: FinancialReportingService = Depends(get_financial_service),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Get cash flow forecast for next N months (default 12)

    ✅ Authorization: Admin/steward only
    """
    allowed_roles = ["admin", "oversight", "oversight", "executive_admin"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="Financial reporting access denied")

    try:
        audit_fn = getattr(request.app, "audit", None)
        if audit_fn:
            await audit_fn(
                actor_id=current_user["id"],
                action="financial_reporting.forecast_accessed",
                target=f"forecast:{months}m"
            )
    except Exception:
        pass

    return await financial_service.get_cash_flow_forecast(months)
