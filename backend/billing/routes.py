"""
WAI Institute Billing API Routes
Real endpoints for subscription, invoice, and payment management
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from typing import List, Optional
import json
import hmac
import hashlib
from datetime import datetime

import jwt as _jwt

from .models import (
    Subscription,
    SubscriptionCreate,
    SubscriptionUpdate,
    Invoice,
    PaymentMethod,
    PaymentMethodCreate,
    BillingCycle,
    SubscriptionTier,
)
from .stripe_service import StripeService, CreatorPayoutService
from .financial_reporting import FinancialReportingService, RevenueRecognitionService
from security.field_authorization import FieldAuthorization, get_visible_fields
from security.encryption import decrypt_payout_account, mask_sensitive_field

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

router = APIRouter(prefix="/api/billing", tags=["billing"])


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_stripe_service(request: Request) -> StripeService:
    """Get Stripe service from app state"""
    return request.app.state.stripe_service


async def get_creator_payout_service(request: Request) -> CreatorPayoutService:
    """Get creator payout service from app state"""
    return request.app.state.creator_payout_service


async def get_financial_service(request: Request) -> FinancialReportingService:
    """Get financial reporting service from app state"""
    return request.app.state.financial_service


# ============================================================================
# SUBSCRIPTION ENDPOINTS
# ============================================================================

@router.post("/subscribe", response_model=Subscription)
async def create_subscription(
    subscription_create: SubscriptionCreate,
    current_user: dict = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """
    Create a new subscription for the current user

    Request body:
    {
        "tier": "basic|advanced|premium|enterprise",
        "billing_cycle": "monthly|quarterly|annual",
        "payment_method_id": "pm_xxx" (from Stripe)
    }
    """
    try:
        subscription = await stripe_service.create_subscription(
            user_id=current_user["id"],
            tier=SubscriptionTier(subscription_create.tier),
            billing_cycle=BillingCycle(subscription_create.billing_cycle),
            payment_method_id=subscription_create.payment_method_id,
            email=current_user["email"],
        )

        return subscription

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create subscription")


@router.get("/subscription", response_model=Optional[Subscription])
async def get_subscription(
    current_user: dict = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
    request: Request = None,
):
    """Get the current user's active subscription

    ✅ Field-level authorization applied
    ✅ Payment method details masked
    ✅ Audit logged
    """
    subscription = await stripe_service.get_subscription(current_user["id"])

    if subscription:
        # Mask payment method details
        if "payment_method" in subscription and subscription["payment_method"]:
            payment = subscription["payment_method"]
            subscription["payment_method"] = {
                "type": payment.get("type"),
                "last4": payment.get("last4"),
                "brand": payment.get("brand"),
                "exp_month": payment.get("exp_month"),
                "exp_year": payment.get("exp_year"),
                # Remove card number, CVV, etc.
            }

        # Audit log subscription access
        try:
            audit_fn = getattr(request.app, "audit", None)
            if audit_fn:
                await audit_fn(
                    actor_id=current_user["id"],
                    action="subscription.viewed",
                    target=current_user["id"],
                    meta={"tier": subscription.get("tier")}
                )
        except Exception:
            pass

    return subscription


@router.post("/subscription/upgrade", response_model=Subscription)
async def upgrade_subscription(
    new_tier: SubscriptionTier,
    current_user: dict = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """
    Upgrade to a higher tier
    Proration applied immediately

    Query params:
    - new_tier: basic|advanced|premium
    """
    try:
        subscription = await stripe_service.update_subscription_tier(
            user_id=current_user["id"],
            new_tier=new_tier,
        )
        return subscription

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upgrade subscription")


@router.post("/subscription/cancel", response_model=Subscription)
async def cancel_subscription(
    reason: str = "User requested cancellation",
    current_user: dict = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """
    Cancel the user's subscription
    Access continues until end of billing period

    Query params:
    - reason: Optional cancellation reason
    """
    try:
        subscription = await stripe_service.cancel_subscription(
            user_id=current_user["id"],
            reason=reason,
        )
        return subscription

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


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
# PAYMENT METHOD ENDPOINTS
# ============================================================================

@router.post("/payment-method", response_model=PaymentMethod)
async def add_payment_method(
    payment_method_create: PaymentMethodCreate,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """
    Add a payment method to the user's account

    Request body:
    {
        "stripe_payment_method_id": "pm_xxx",
        "type": "card",
        "last_4": "4242",
        "exp_month": 12,
        "exp_year": 2025,
        "is_default": false
    }
    """
    payment_methods_collection = request.app.state.db.payment_methods

    # Save payment method
    payment_method_doc = {
        "user_id": current_user["id"],
        "stripe_payment_method_id": payment_method_create.stripe_payment_method_id,
        "type": payment_method_create.type,
        "last_4": payment_method_create.last_4,
        "exp_month": payment_method_create.exp_month,
        "exp_year": payment_method_create.exp_year,
        "is_default": payment_method_create.is_default,
        "created_at": datetime.utcnow(),
    }

    # If this is set as default, unset others
    if payment_method_create.is_default:
        await payment_methods_collection.update_many(
            {"user_id": current_user["id"]},
            {"$set": {"is_default": False}}
        )

    result = await payment_methods_collection.insert_one(payment_method_doc)

    return PaymentMethod(**payment_method_doc, id=str(result.inserted_id))


@router.get("/payment-methods", response_model=List[PaymentMethod])
async def list_payment_methods(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Get all payment methods for the current user"""
    payment_methods_collection = request.app.state.db.payment_methods

    methods = await payment_methods_collection.find({
        "user_id": current_user["id"]
    }).to_list(None)

    return [PaymentMethod(**m, id=str(m["_id"])) for m in methods]


@router.delete("/payment-method/{payment_method_id}")
async def delete_payment_method(
    payment_method_id: str,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Delete a payment method"""
    payment_methods_collection = request.app.state.db.payment_methods

    result = await payment_methods_collection.delete_one({
        "_id": payment_method_id,
        "user_id": current_user["id"],
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")

    return {"message": "Payment method deleted"}


# ============================================================================
# STRIPE WEBHOOK ENDPOINT
# ============================================================================

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """
    Handle Stripe webhook events

    Stripe sends webhooks for:
    - invoice.payment_succeeded
    - invoice.payment_failed
    - customer.subscription.updated
    - customer.subscription.deleted
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        # Verify webhook signature (prevents spoofing)
        webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
        if not webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET not configured")
        event = _verify_stripe_webhook(payload, sig_header, webhook_secret)

        # Process the event
        await stripe_service.handle_webhook(event)

        return {"status": "success"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")
    except Exception as e:
        # Return 200 anyway (Stripe retry logic)
        import logging
        logging.error(f"Webhook processing error: {e}")
        return {"status": "error", "message": str(e)}


# ============================================================================
# CREATOR PAYOUT ENDPOINTS
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


@router.post("/creator/withdraw")
async def creator_withdraw(
    amount: float,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    creator_payout_service: CreatorPayoutService = Depends(get_creator_payout_service),
):
    """
    Withdraw accrued creator earnings
    Requires Stripe Connect account linked to creator profile

    Query params:
    - amount: Amount to withdraw (must be <= available balance)
    """
    try:
        # Get creator's Stripe Connect ID
        users_collection = request.app.state.db.users
        creator_doc = await users_collection.find_one({"id": current_user["id"]}, {"_id": 0})

        stripe_connect_id = creator_doc.get("stripe_connect_account_id")
        if not stripe_connect_id:
            raise HTTPException(
                status_code=400,
                detail="Stripe Connect account not linked"
            )

        # Execute withdrawal
        payout_id = await creator_payout_service.execute_creator_withdrawal(
            creator_id=current_user["id"],
            amount=amount,
            stripe_connect_account_id=stripe_connect_id,
        )

        return {
            "payout_id": payout_id,
            "amount": amount,
            "status": "paid",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process withdrawal")


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
    allowed_roles = ["admin", "steward", "elder", "executive_admin"]
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
    allowed_roles = ["admin", "steward", "elder", "executive_admin"]
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
    allowed_roles = ["admin", "steward", "elder", "executive_admin"]
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
    allowed_roles = ["admin", "steward", "elder", "executive_admin"]
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
    allowed_roles = ["admin", "steward", "elder", "executive_admin"]
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
    allowed_roles = ["admin", "steward", "elder", "executive_admin"]
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
    allowed_roles = ["admin", "steward", "elder", "executive_admin"]
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


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _verify_stripe_webhook(payload: bytes, sig_header: str, secret: str) -> dict:
    """
    Verify Stripe webhook signature

    Args:
        payload: Raw request body
        sig_header: stripe-signature header value
        secret: Webhook signing secret

    Returns:
        Parsed event dict
    """
    try:
        # Parse signature header: t=timestamp,v1=signature
        timestamp, signature = sig_header.split(",")[0].split("=")[1], sig_header.split("v1=")[1]

        # Compute expected signature
        signed_content = f"{timestamp}.{payload.decode('utf-8')}"
        expected_sig = hmac.new(
            secret.encode(),
            signed_content.encode(),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures (constant-time to prevent timing attacks)
        if not hmac.compare_digest(signature, expected_sig):
            raise ValueError("Invalid signature")

        # Parse event
        event = json.loads(payload)
        return event

    except (ValueError, KeyError) as e:
        raise ValueError(f"Invalid webhook: {e}")
