"""app/routes/payments.py — Stripe payments, subscriptions, and pricing endpoints.

Extracted from backend/server.py lines 7391–7778. No logic changed.
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import stripe as _stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

import app.database as _app_db
from app.database import db
from app.models.user import User
from app.security.auth import current_user, require_role
from app.utils.audit import audit, notify

logger = logging.getLogger("lcewai")
router = APIRouter()

STRIPE_SECRET_KEY     = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://wai-institute.org")

if STRIPE_SECRET_KEY:
    _stripe.api_key = STRIPE_SECRET_KEY

PAYMENT_PRODUCTS = {
    "tshirt":       {"name": "WAI Institute T-Shirt",         "amount": 2500, "mode": "payment",      "description": "Official WAI Apprentice tee"},
    "workbook":     {"name": "WAI Apprentice Workbook",        "amount": 1500, "mode": "payment",      "description": "Printed apprentice study guide"},
    "kit":          {"name": "WAI Apprentice Kit",             "amount": 4500, "mode": "payment",      "description": "T-Shirt + Workbook bundle"},
    "more_monthly": {"name": "M.O.R.E. Membership – Monthly", "amount":  999, "mode": "subscription", "interval": "month", "description": "Monthly M.O.R.E. community access"},
    "more_annual":  {"name": "M.O.R.E. Membership – Annual",  "amount": 7999, "mode": "subscription", "interval": "year",  "description": "Annual M.O.R.E. membership (save 33%)"},
    "credential":   {"name": "WAI Credential Certificate",    "amount": 2500, "mode": "payment",      "description": "Official printed credential certificate"},
    "donation":     {"name": "Donation – WAI Institute",      "amount": None, "mode": "payment",      "description": "Support the WAI mission"},
}


class CheckoutReq(BaseModel):
    product_key: str
    amount_cents: Optional[int] = None
    quantity: int = 1
    extra_meta: Optional[dict] = None


@router.get("/payments/products")
async def list_payment_products():
    return {
        "publishable_key": STRIPE_PUBLISHABLE_KEY,
        "products": PAYMENT_PRODUCTS,
        "stripe_enabled": bool(STRIPE_SECRET_KEY),
    }


@router.post("/payments/checkout")
async def create_checkout_session(req: CheckoutReq, user=Depends(current_user)):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "Payment system not configured")
    product = PAYMENT_PRODUCTS.get(req.product_key)
    if not product:
        raise HTTPException(400, f"Unknown product: {req.product_key}")
    amount = req.amount_cents if req.product_key == "donation" else product["amount"]
    if not amount or amount < 50:
        raise HTTPException(400, "Amount must be at least $0.50")
    mode = product["mode"]
    price_data: dict = {
        "currency": "usd",
        "product_data": {"name": product["name"], "description": product.get("description", "")},
        "unit_amount": amount,
    }
    if mode == "subscription":
        price_data["recurring"] = {"interval": product["interval"]}
    user_doc = await db.users.find_one({"id": user.id}, {"stripe_customer_id": 1, "email": 1, "full_name": 1})
    customer_id = (user_doc or {}).get("stripe_customer_id")
    if not customer_id:
        customer = _stripe.Customer.create(
            email=user.email,
            name=user.full_name,
            metadata={"wai_user_id": user.id},
        )
        customer_id = customer.id
        await db.users.update_one({"id": user.id}, {"$set": {"stripe_customer_id": customer_id}})
    # Idempotency key prevents duplicate sessions if the client retries the request.
    # Scoped to user + product + UTC date so each legitimate daily purchase gets
    # a unique key while accidental double-submits are de-duplicated by Stripe.
    from datetime import date as _date
    _idem_key = f"checkout-{user.id}-{req.product_key}-{_date.today().isoformat()}"
    session = _stripe.checkout.Session.create(
        mode=mode,
        customer=customer_id,
        line_items=[{"price_data": price_data, "quantity": req.quantity}],
        success_url=f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/payment/cancel",
        metadata={"wai_user_id": user.id, "product_key": req.product_key, **(req.extra_meta or {})},
        idempotency_key=_idem_key,
    )
    await audit(user.id, "payment_checkout_created", meta={"product": req.product_key, "session_id": session.id})
    return {"url": session.url, "session_id": session.id}


@router.post("/payments/webhook")
async def stripe_webhook(request: Request):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(503, "Webhook not configured")
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = _stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except _stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid webhook signature")
    etype = event["type"]
    obj   = event["data"]["object"]
    if etype == "checkout.session.completed":
        await _stripe_checkout_done(obj)
    elif etype in ("customer.subscription.created", "customer.subscription.updated"):
        await _stripe_sub_upsert(obj)
    elif etype == "customer.subscription.deleted":
        await _stripe_sub_deleted(obj)
    elif etype == "invoice.payment_succeeded":
        await _stripe_invoice_paid(obj)
    elif etype == "invoice.payment_failed":
        await _stripe_invoice_failed(obj)
    return {"received": True}


async def _stripe_checkout_done(session):
    uid = (session.get("metadata") or {}).get("wai_user_id")
    product_key = (session.get("metadata") or {}).get("product_key", "unknown")
    amount = session.get("amount_total", 0)
    await db.payments.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": uid,
        "stripe_session_id": session.get("id"),
        "stripe_customer_id": session.get("customer"),
        "product_key": product_key,
        "amount_cents": amount,
        "currency": session.get("currency", "usd"),
        "mode": session.get("mode"),
        "status": "paid",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    if uid:
        await notify(uid, "Payment Confirmed",
                     f"Thank you! Your payment of ${amount/100:.2f} has been received.",
                     link="/payment/history", kind="success")


async def _stripe_sub_upsert(sub):
    customer_id = sub.get("customer")
    user_doc = await db.users.find_one({"stripe_customer_id": customer_id}, {"id": 1})
    uid = user_doc["id"] if user_doc else None
    await db.subscriptions.update_one(
        {"stripe_subscription_id": sub["id"]},
        {"$set": {
            "stripe_subscription_id": sub["id"],
            "stripe_customer_id": customer_id,
            "user_id": uid,
            "status": sub.get("status"),
            "current_period_end": sub.get("current_period_end"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    if uid and sub.get("status") == "active":
        await db.users.update_one(
            {"id": uid},
            {"$set": {"more_member": True, "more_subscription_id": sub["id"],
                      "more_member_since": datetime.now(timezone.utc).isoformat()}},
        )
        await notify(uid, "M.O.R.E. Membership Active",
                     "Your M.O.R.E. membership is now active. Welcome to the community!",
                     link="/app/more", kind="success")


async def _stripe_sub_deleted(sub):
    customer_id = sub.get("customer")
    user_doc = await db.users.find_one({"stripe_customer_id": customer_id}, {"id": 1})
    uid = user_doc["id"] if user_doc else None
    await db.subscriptions.update_one(
        {"stripe_subscription_id": sub["id"]},
        {"$set": {"status": "canceled", "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if uid:
        await db.users.update_one({"id": uid}, {"$unset": {"more_member": "", "more_subscription_id": ""}})
        await notify(uid, "Subscription Canceled",
                     "Your M.O.R.E. membership has been canceled.", kind="warning")


async def _stripe_invoice_paid(invoice):
    customer_id = invoice.get("customer")
    user_doc = await db.users.find_one({"stripe_customer_id": customer_id}, {"id": 1})
    uid = user_doc["id"] if user_doc else None
    await db.payments.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": uid,
        "stripe_invoice_id": invoice.get("id"),
        "stripe_customer_id": customer_id,
        "amount_cents": invoice.get("amount_paid", 0),
        "currency": invoice.get("currency", "usd"),
        "mode": "subscription_renewal",
        "status": "paid",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


async def _stripe_invoice_failed(invoice):
    customer_id = invoice.get("customer")
    user_doc = await db.users.find_one({"stripe_customer_id": customer_id}, {"id": 1})
    uid = user_doc["id"] if user_doc else None
    if uid:
        await notify(uid, "Payment Failed",
                     "Your subscription payment failed. Update your payment method to keep your M.O.R.E. membership.",
                     link="/payment/manage", kind="error")


@router.get("/payments/portal")
async def customer_portal(user=Depends(current_user)):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "Payment system not configured")
    user_doc = await db.users.find_one({"id": user.id}, {"stripe_customer_id": 1})
    customer_id = (user_doc or {}).get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(404, "No billing account found. Complete a purchase first.")
    portal = _stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{FRONTEND_URL}/dashboard",
    )
    return {"url": portal.url}


@router.get("/payments/history")
async def payment_history(user=Depends(current_user)):
    cursor = db.payments.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).limit(50)
    return {"payments": await cursor.to_list(50)}


@router.get("/pricing")
async def get_pricing():
    """Public endpoint — subscription pricing with active discount applied."""
    if not _app_db._discount_manager:
        raise HTTPException(500, "Pricing system not initialized")
    from billing.models import TIER_PRICING
    discount = await _app_db._discount_manager.get_active_discount()
    pricing_response = _app_db._discount_manager.get_pricing_with_discount(TIER_PRICING, discount)
    return pricing_response
