"""app/routes/payments.py — Payments, subscriptions, and pricing endpoints.

Ecommerce runs through the free-tier publishing pipeline (backend/ai/publishing.py):
  Tier 1 — Lemon Squeezy  (LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID)
  Tier 2 — Gumroad        (GUMROAD_API_KEY)
  Tier 3 — MongoDB archive (always works)
Stripe has been fully removed from this platform.
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

import app.database as _app_db
from app.database import db
from app.models.user import User
from app.security.auth import current_user, require_role
from app.utils.audit import audit, notify

logger = logging.getLogger("lcewai")
router = APIRouter()

LEMON_SQUEEZY_API_KEY = os.environ.get("LEMON_SQUEEZY_API_KEY", "")
LEMON_SQUEEZY_STORE_ID = os.environ.get("LEMON_SQUEEZY_STORE_ID", "")
GUMROAD_API_KEY = os.environ.get("GUMROAD_API_KEY", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://wai-institute.org")

PAYMENTS_ENABLED = bool(
    (LEMON_SQUEEZY_API_KEY and LEMON_SQUEEZY_STORE_ID) or GUMROAD_API_KEY
)

# Product catalog — amounts in cents USD.
# physical=True items are not sold online yet (no fulfillment provider wired up).
PAYMENT_PRODUCTS = {
    "tshirt":       {"name": "WAI Institute T-Shirt",         "amount": 2500, "mode": "payment",      "description": "Official WAI Apprentice tee", "physical": True},
    "workbook":     {"name": "WAI Apprentice Workbook",        "amount": 1500, "mode": "payment",      "description": "Printed apprentice study guide", "physical": True},
    "kit":          {"name": "WAI Apprentice Kit",             "amount": 4500, "mode": "payment",      "description": "T-Shirt + Workbook bundle", "physical": True},
    "more_monthly":   {"name": "M.O.R.E. Membership – Monthly",   "amount":  999, "mode": "subscription", "interval": "month", "description": "Monthly M.O.R.E. community access"},
    "more_annual":    {"name": "M.O.R.E. Membership – Annual",    "amount": 7999, "mode": "subscription", "interval": "year",  "description": "Annual M.O.R.E. membership (save 33%)"},
    "member_monthly": {"name": "WAI Member – Monthly",            "amount":  900, "mode": "subscription", "interval": "month", "description": "WAI Member tier — full M.O.R.E. + AI Tutor"},
    "plus_monthly":   {"name": "WAI Plus – Monthly",              "amount": 1500, "mode": "subscription", "interval": "month", "description": "WAI Plus tier — priority matching + expanded courses"},
    "pro_monthly":    {"name": "WAI Pro – Monthly",               "amount": 2900, "mode": "subscription", "interval": "month", "description": "WAI Pro tier — advanced courses, labs, full AI suite"},
    "patron_monthly": {"name": "WAI Patron – Monthly",            "amount": 5900, "mode": "subscription", "interval": "month", "description": "WAI Patron — founders circle + funds free access for others"},
    "credential":     {"name": "WAI Credential Certificate",      "amount": 2500, "mode": "payment",      "description": "Official printed credential certificate", "physical": True},
    "donation":     {"name": "Donation – WAI Institute",      "amount": None, "mode": "payment",      "description": "Support the WAI mission"},
    # Creators Sanctuary tiers
    "sanctuary_trial":   {"name": "Creators Sanctuary – 3-Day Trial",     "amount":  300, "mode": "payment",      "description": "All-access 3 days & 33 minutes trial"},
    "sanctuary_paid":    {"name": "Creators Sanctuary – Paid Creator",    "amount":  700, "mode": "subscription", "interval": "month", "description": "Paid Beginning Creator tier — $7/mo"},
    "sanctuary_creator": {"name": "Creators Sanctuary – Advanced Creator","amount": 1100, "mode": "subscription", "interval": "month", "description": "Advanced Creator tier — $11/mo"},
    "sanctuary_mod":     {"name": "Creators Sanctuary – Certified Mod",   "amount": 1500, "mode": "subscription", "interval": "month", "description": "Certified Moderator tier — $15/mo"},
}

# Maps every purchasable product key → the feature_tier it grants.
_PRODUCT_TIER_MAP: dict[str, str] = {
    "more_monthly":       "member",
    "more_annual":        "member",
    "member_monthly":     "member",
    "plus_monthly":       "plus",
    "pro_monthly":        "pro",
    "patron_monthly":     "patron",
    "sanctuary_trial":    "pro",
    "sanctuary_paid":     "member",
    "sanctuary_creator":  "plus",
    "sanctuary_mod":      "pro",
}


class CheckoutReq(BaseModel):
    product_key: str
    amount_cents: Optional[int] = None  # required only for "donation"
    quantity: int = 1
    extra_meta: Optional[dict] = None


@router.get("/payments/products")
async def list_payment_products():
    provider = (
        "lemon_squeezy" if (LEMON_SQUEEZY_API_KEY and LEMON_SQUEEZY_STORE_ID)
        else "gumroad" if GUMROAD_API_KEY
        else "disabled"
    )
    return {
        "publishable_key": "",
        "products": PAYMENT_PRODUCTS,
        "payments_enabled": PAYMENTS_ENABLED,
        "provider": provider,
    }


@router.post("/payments/checkout")
async def create_checkout_session(req: CheckoutReq, user=Depends(current_user)):
    """Create a checkout session via the free-tier pipeline (Lemon Squeezy → Gumroad)."""
    product = PAYMENT_PRODUCTS.get(req.product_key)
    if not product:
        raise HTTPException(400, f"Unknown product: {req.product_key}")

    amount = req.amount_cents if req.product_key == "donation" else product["amount"]
    if not amount or amount < 50:
        raise HTTPException(400, "Amount must be at least $0.50")

    if product.get("physical"):
        raise HTTPException(501, "Physical merchandise is not available for online purchase yet.")

    from ai.publishing import _publish_lemon_squeezy, _publish_gumroad

    mode = product["mode"]
    is_subscription = mode == "subscription"

    # Tier 1 — Lemon Squeezy (digital products + subscriptions)
    ls_result = await _publish_lemon_squeezy(
        name=product["name"],
        description=product.get("description", ""),
        price_cents=amount,
        persona="commerce",
        is_subscription=is_subscription,
        interval=product.get("interval", "month"),
    )
    if ls_result and ls_result.get("url"):
        await audit(user.id, "payment_checkout_created",
                    meta={"product": req.product_key, "provider": "lemon_squeezy"})
        return {"url": ls_result["url"], "provider": "lemon_squeezy"}

    # Tier 2 — Gumroad (one-time digital purchases only)
    if not is_subscription:
        gr_result = await _publish_gumroad(product["name"], product.get("description", ""), amount)
        if gr_result and gr_result.get("url"):
            await audit(user.id, "payment_checkout_created",
                        meta={"product": req.product_key, "provider": "gumroad"})
            return {"url": gr_result["url"], "provider": "gumroad"}

    raise HTTPException(
        501,
        "Payments are not configured yet. Add LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID "
        "(free tier — payouts via PayPal or bank) or GUMROAD_API_KEY to enable checkout.",
    )


@router.post("/payments/webhook")
async def payments_webhook(request: Request):
    """Lemon Squeezy order webhook — records paid orders and grants feature tiers.

    Configure in Lemon Squeezy → Settings → Webhooks with endpoint:
        {FRONTEND_URL}/api/payments/webhook
    Signature: X-Signature header = HMAC-SHA256 of the raw body using
    LEMON_SQUEEZY_WEBHOOK_SECRET.
    """
    import json
    import hmac as _hmac
    import hashlib as _hashlib

    secret = os.environ.get("LEMON_SQUEEZY_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(404, "Payment webhook not configured")

    payload = await request.body()
    sig = request.headers.get("x-signature", "")
    if not sig or not _hmac.compare_digest(
        sig, _hmac.new(secret.encode(), payload, _hashlib.sha256).hexdigest()
    ):
        raise HTTPException(400, "Invalid webhook signature")

    try:
        event = json.loads(payload)
    except Exception:
        raise HTTPException(400, "Invalid JSON payload")

    event_name = (event.get("meta") or {}).get("event_name", "")
    if event_name == "order_created":
        data = (event.get("data") or {}).get("attributes") or {}
        order_id = str((event.get("data") or {}).get("id", ""))
        user_email = data.get("user_email", "")
        total = data.get("total", 0)
        currency = data.get("currency", "usd")
        status = data.get("status", "")

        try:
            await db.payments.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": None,
                "provider": "lemon_squeezy",
                "provider_order_id": order_id,
                "product_key": "lemon_squeezy_order",
                "amount_cents": int(float(total) * 100) if total else 0,
                "currency": currency,
                "mode": "order",
                "status": "paid" if status == "paid" else status,
                "buyer_email": user_email,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            logger.exception("LS webhook: payment record failed")

        # Best-effort tier grant: match buyer email → user, product name → tier.
        first_item = data.get("first_order_item") or {}
        product_name = first_item.get("product_name", "")
        product_key = next(
            (k for k, pr in PAYMENT_PRODUCTS.items()
             if str(pr["name"]).lower() == str(product_name).lower()),
            None,
        )
        if user_email and product_key and product_key in _PRODUCT_TIER_MAP:
            user_doc = await db.users.find_one({"email": user_email}, {"id": 1, "feature_tier": 1})
            if user_doc:
                granted = _PRODUCT_TIER_MAP[product_key]
                tier_rank = {"free": 0, "member": 1, "plus": 2, "pro": 3, "patron": 4, "executive": 5}
                if tier_rank.get(granted, 0) > tier_rank.get(user_doc.get("feature_tier", "free"), 0):
                    await db.users.update_one(
                        {"id": user_doc["id"]},
                        {"$set": {"feature_tier": granted, "feature_tier_source": "payment"}},
                    )
                    await notify(user_doc["id"], "Feature tier upgraded",
                                 f"Your WAI feature tier is now {granted} — thank you for supporting the mission!",
                                 link="/app/dashboard", kind="success")

    return {"received": True}


@router.get("/payments/portal")
async def customer_portal(user=Depends(current_user)):
    raise HTTPException(501, "Subscription management portal is not available yet. "
                             "Contact support to change or cancel your subscription.")


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
