"""
Payments router — Lemon Squeezy → Gumroad checkout pipeline.

Extracted verbatim from backend/server.py (monolith refactor, slice 0).
Shared module state (db, audit, notify, current_user) is bound by server.py
via bind() at include time, so this module has no circular imports.
"""
import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Header, APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger("lcewai")
router = APIRouter(prefix="/payments", tags=["payments"])

async def _dep_current_user(authorization: Optional[str] = Header(None)):
    """Resolve the real current_user at REQUEST time (bind() sets it after import)."""
    return await current_user(authorization)



# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = audit = notify = current_user = None


def bind(_db, _audit, _notify, _current_user):
    """Called by server.py at include time to inject shared dependencies."""
    global db, audit, notify, current_user
    db, audit, notify, current_user = _db, _audit, _notify, _current_user


# ─── PAYMENTS (Lemon Squeezy → Gumroad — NO Stripe) ──────────────────────────
# Stripe has been fully removed from this platform (owner decision).
# Ecommerce runs through the free-tier publishing pipeline in ai/publishing.py:
#   Tier 1 — Lemon Squeezy  (LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID)
#   Tier 2 — Gumroad        (GUMROAD_API_KEY)
#   Tier 3 — MongoDB archive (always works)
# No Stripe SDK, keys, or webhooks are required anywhere.

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
    "tshirt":       {"name": "M.O.R.E. Help Center T-Shirt",         "amount": 2500, "mode": "payment",      "description": "Official M.O.R.E. apprentice tee", "physical": True},
    "workbook":     {"name": "M.O.R.E. Help Center Workbook",        "amount": 1500, "mode": "payment",      "description": "Printed apprentice study guide", "physical": True},
    "kit":          {"name": "M.O.R.E. Help Center Apprentice Kit",  "amount": 4500, "mode": "payment",      "description": "T-Shirt + Workbook bundle", "physical": True},
    "more_monthly":   {"name": "M.O.R.E. Membership – Monthly",   "amount":  999, "mode": "subscription", "interval": "month", "description": "Monthly M.O.R.E. community access"},
    "more_annual":    {"name": "M.O.R.E. Membership – Annual",    "amount": 7999, "mode": "subscription", "interval": "year",  "description": "Annual M.O.R.E. membership (save 33%)"},
    "member_monthly": {"name": "M.O.R.E. Member – Monthly",            "amount":  900, "mode": "subscription", "interval": "month", "description": "M.O.R.E. Member tier — full community + AI Tutor"},
    "plus_monthly":   {"name": "M.O.R.E. Plus – Monthly",              "amount": 1500, "mode": "subscription", "interval": "month", "description": "M.O.R.E. Plus tier — priority matching + expanded courses"},
    "pro_monthly":    {"name": "M.O.R.E. Pro – Monthly",               "amount": 2900, "mode": "subscription", "interval": "month", "description": "M.O.R.E. Pro tier — advanced courses, labs, full AI suite"},
    "patron_monthly": {"name": "M.O.R.E. Patron – Monthly",            "amount": 5900, "mode": "subscription", "interval": "month", "description": "M.O.R.E. Patron — founders circle + funds free access for others"},
    "credential":     {"name": "M.O.R.E. Credential Certificate",      "amount": 2500, "mode": "payment",      "description": "Physical credential certificate", "physical": True},
    "donation":       {"name": "Donation – M.O.R.E. Help Center",      "amount": None, "mode": "payment",      "description": "Support the M.O.R.E. Help Center mission"},
    # BYOK — $3 one-time unlock (below instructor tier). Grants byok_enabled,
    # not a membership tier; instructor tier and above activate free.
    "byok":           {"name": "BYOK – Bring Your Own Key",            "amount":  300, "mode": "payment",      "description": "One-time $3 unlock — attach a free Groq, Cerebras, or Gemini key so your AI runs on your own key"},
    # Sponsor a Scholarship — milestone-based giving. Amount is set by the
    # sponsor (like donation); a paid order matches the sponsor's pledge.
    "scholarship":    {"name": "Sponsor a Scholarship — M.O.R.E. Help Center", "amount": None, "mode": "payment", "description": "Sponsor a scholar — Full, Partial, or Collective. Milestone-based release, fully transparent."},
    # Creator's Sanctuary tiers (creator lane — see _PRODUCT_TIER_MAP)
    "sanctuary_trial":   {"name": "M.O.R.E. Creator's Sanctuary – 3-Day Trial",     "amount":  300, "mode": "payment",      "description": "All-access 3 days & 33 minutes trial — everything through Pro"},
    "sanctuary_paid":    {"name": "M.O.R.E. Creator's Sanctuary – Paid Creator",    "amount":  700, "mode": "subscription", "interval": "month", "description": "Member-level creator lane — $7/mo", "deprecated": True},
    "sanctuary_creator": {"name": "M.O.R.E. Creator's Sanctuary – Advanced Creator","amount": 1100, "mode": "subscription", "interval": "month", "description": "Plus-level creator lane — $11/mo", "deprecated": True},
    "sanctuary_mod":     {"name": "M.O.R.E. Creator's Sanctuary – Certified Mod",   "amount": 1500, "mode": "subscription", "interval": "month", "description": "Pro-level creator lane — $15/mo", "deprecated": True},
    # The Arena — self-improvement digital products (no comparison, only personal bests)
    "arena_workbook":    {"name": "The Arena Workbook: 21-Day Self-Challenge",       "amount": 2700, "mode": "payment",      "description": "Digital workbook + tracking sheets — outcompete your past self in 21 days"},
    "arena_peer_guide":  {"name": "The Peer Guide: Group Accountability Workbook",    "amount": 4700, "mode": "payment",      "description": "Structured 12-week group challenges + facilitator scripts"},
    "arena_license":     {"name": "The Arena License Kit (Coaches & Employers)",       "amount": 19700,"mode": "payment",      "description": "Editable slides, email templates, and facilitator guides for teams"},
    "arena_album":       {"name": "Everyone Wins: Reflection Album",                   "amount": 999,  "mode": "payment",      "description": "Spoken word album — lyrics, liner notes, reflection guide"},
}

# Legacy names (pre-rebrand) → product key, so webhook matching keeps working
# for orders made under the old names. Current names match by exact string;
# aliases are checked only when the exact match fails.
_LEGACY_PRODUCT_NAMES = {
    "WAI Institute T-Shirt": "tshirt",
    "WAI Apprentice Workbook": "workbook",
    "WAI Apprentice Kit": "kit",
    "WAI Member – Monthly": "member_monthly",
    "WAI Plus – Monthly": "plus_monthly",
    "WAI Pro – Monthly": "pro_monthly",
    "WAI Patron – Monthly": "patron_monthly",
    "WAI Credential Certificate": "credential",
    "Donation – WAI Institute": "donation",
    "Creators Sanctuary – 3-Day Trial": "sanctuary_trial",
    "Creators Sanctuary – Paid Creator": "sanctuary_paid",
    "Creators Sanctuary – Advanced Creator": "sanctuary_creator",
    "Creators Sanctuary – Certified Mod": "sanctuary_mod",
}

# Trial window: 3 days · 33 minutes · 33 seconds (matches marketing copy).
TRIAL_DELTA = {"days": 3, "minutes": 33, "seconds": 33}

# Maps every purchasable product key → the feature_tier it grants.
# Admins can still manually override via the exec panel. Payments drive the
# tier automatically through the payment webhook.
_PRODUCT_TIER_MAP: dict[str, str] = {
    # Main membership ladder
    "more_monthly":       "member",
    "more_annual":        "member",
    "member_monthly":     "member",
    "plus_monthly":       "plus",
    "pro_monthly":        "pro",
    "patron_monthly":     "patron",
    # Creator's Sanctuary lane — a purchase grants the matching membership
    # level (so creator perks sit on top of a real membership) plus the
    # creator-specific privileges managed by the Sanctuary surface.
    "sanctuary_trial":    "pro",
    "sanctuary_paid":     "member",
    "sanctuary_creator":  "plus",
    "sanctuary_mod":      "pro",
}

TIER_RANK = {"free": 0, "member": 1, "plus": 2, "pro": 3, "patron": 4, "executive": 5}


class CheckoutReq(BaseModel):
    product_key: str
    amount_cents: Optional[int] = None  # required only for "donation"
    quantity: int = 1
    extra_meta: Optional[dict] = None


@router.get("/products")
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


@router.post("/checkout")
async def create_checkout_session(req: CheckoutReq, user=Depends(_dep_current_user)):
    """Create a checkout session via the free-tier pipeline (Lemon Squeezy → Gumroad).

    Returns {"url": ...} — the same shape the previous checkout flow returned — so the
    existing store / plans / donate UI keeps working unchanged.
    """
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
        persona="platform",
        is_subscription=is_subscription,
        interval=product.get("interval", "month"),
    )
    if ls_result:
        await audit(user.id, "payment_checkout_created",
                    meta={"product": req.product_key, "provider": "lemon_squeezy",
                          "session_id": ls_result.get("product_id")})
        return {"url": ls_result["url"], "session_id": ls_result.get("product_id")}

    # Tier 2 — Gumroad (one-time digital purchases only)
    if not is_subscription:
        gr_result = await _publish_gumroad(product["name"], product.get("description", ""), amount)
        if gr_result:
            await audit(user.id, "payment_checkout_created",
                        meta={"product": req.product_key, "provider": "gumroad",
                              "session_id": gr_result.get("product_id")})
            return {"url": gr_result["url"], "session_id": gr_result.get("product_id")}

    if not PAYMENTS_ENABLED:
        raise HTTPException(
            501,
            "Payments are not configured. Add LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID "
            "or GUMROAD_API_KEY in your environment.",
        )
    raise HTTPException(
        500,
        "Payment processing failed. The payment providers are configured but the request could not be completed. "
        "Check your Lemon Squeezy or Gumroad API keys and try again.",
    )


@router.post("/webhook")
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

        # ── Idempotency guard ─────────────────────────────────────────────────
        # The same Lemon Squeezy order may be redelivered (provider retry or
        # duplicate webhook). A repeated delivery of the same provider order
        # MUST NOT create a second payment record, grant, notification, or
        # fulfillment. Dedup on the unique provider_order_id and ack idempotently.
        if order_id:
            try:
                _prior = await db.payments.find_one(
                    {"provider_order_id": order_id}, {"_id": 0, "id": 1})
            except Exception:
                _prior = None
            if _prior:
                return {"received": True, "idempotent": True}


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

        # Best-effort tier grant: match buyer email → user, product name → key.
        # Exact current name first, then legacy (pre-rebrand) aliases so
        # existing subscribers keep counting on renewals.
        first_item = data.get("first_order_item") or {}
        product_name = str(first_item.get("product_name", ""))
        product_key = next(
            (k for k, pr in PAYMENT_PRODUCTS.items()
             if str(pr["name"]).lower() == product_name.lower()),
            None,
        )
        if not product_key:
            product_key = _LEGACY_PRODUCT_NAMES.get(product_name)
        # ── BYOK ($3 one-time unlock, below instructor tier) ────────────────
        # A paid BYOK product grants byok_enabled directly (not a membership
        # tier — instructor tier and above activate BYOK free without payment).
        if user_email and product_key == "byok":
            user_doc = await db.users.find_one(
                {"email": user_email}, {"id": 1, "byok_enabled": 1}
            )
            if user_doc:
                await db.users.update_one(
                    {"id": user_doc["id"]},
                    {"$set": {"byok_enabled": True, "byok_activated_at": datetime.now(timezone.utc).isoformat()}},
                )
                try:
                    await audit(user_doc["id"], "byok.paid", meta={"product": "byok", "order_id": order_id})
                except Exception:
                    pass
                await notify(user_doc["id"], "BYOK Activated",
                             "Your $3 BYOK unlock is active — attach a free Groq, Cerebras, or Gemini key at /byok to route your AI through your own key.",
                             link="/byok", kind="success")

        # ── Scholarship sponsorship ─────────────────────────────────────────
        # A paid scholarship order marks the sponsor's pending pledge as paid.
        # The committee then matches the pledge to an approved application
        # (milestone-based release, so funds follow real progress).
        if user_email and product_key == "scholarship":
            user_doc = await db.users.find_one({"email": user_email}, {"id": 1})
            if user_doc:
                paid_amount = int(float(total) * 100) if total else 0
                pledge = await db.scholarship_pledges.find_one_and_update(
                    {"user_id": user_doc["id"], "status": "pending"},
                    {"$set": {"status": "paid", "paid_at": datetime.now(timezone.utc).isoformat(),
                              "provider_order_id": order_id,
                              "paid_amount_cents": paid_amount or None}},
                    sort=[("created_at", -1)],
                )
                if pledge:
                    # Move the sponsor's money into the chosen fund's raised total.
                    if pledge.get("fund_id"):
                        await db.scholarship_funds.update_one(
                            {"id": pledge["fund_id"]},
                            {"$inc": {"raised_cents": paid_amount or pledge.get("amount_cents", 0)}},
                        )
                    try:
                        await audit(user_doc["id"], "scholarship.pledge_paid",
                                    target=pledge.get("id"), meta={"order_id": order_id, "amount_cents": paid_amount or pledge.get("amount_cents", 0)})
                    except Exception:
                        pass
                    await notify(user_doc["id"], "Sponsorship Received",
                                 "Thank you — your sponsorship is paid and will be matched to a scholar. Track milestones in your sponsor view.",
                                 link="/sponsor", kind="success")

        if user_email and product_key and product_key in _PRODUCT_TIER_MAP:
            user_doc = await db.users.find_one(
                {"email": user_email},
                {"id": 1, "feature_tier": 1, "feature_tier_expires_at": 1},
            )
            if user_doc:
                granted = _PRODUCT_TIER_MAP[product_key]
                prev_tier = user_doc.get("feature_tier", "free")
                now = datetime.now(timezone.utc)
                # Upgrade-only grant (never downgrade an active tier).
                if TIER_RANK.get(granted, 0) > TIER_RANK.get(prev_tier, 0):
                    set_fields = {
                        "feature_tier": granted,
                        "feature_tier_source": "trial" if product_key == "sanctuary_trial" else "payment",
                        "feature_tier_product": product_key,
                        "feature_tier_updated_at": now.isoformat(),
                    }
                    unset_fields = {}
                    if product_key == "sanctuary_trial":
                        # Time-boxed all-access: revert to their previous tier
                        # after 3 days · 33 minutes · 33 seconds.
                        set_fields["feature_tier_expires_at"] = (now + timedelta(**TRIAL_DELTA)).isoformat()
                        set_fields["feature_tier_revert_to"] = (
                            prev_tier if TIER_RANK.get(prev_tier, 0) > 0 else "free"
                        )
                    elif user_doc.get("feature_tier_expires_at"):
                        # A real (recurring) purchase clears any pending trial clock.
                        unset_fields = {"feature_tier_expires_at": "", "feature_tier_revert_to": ""}

                    update = {"$set": set_fields}
                    if unset_fields:
                        update["$unset"] = unset_fields
                    await db.users.update_one({"id": user_doc["id"]}, update)
                await notify(user_doc["id"], "Payment Confirmed",
                             "Thank you! Your payment has been received and your features are unlocked.",
                             link="/profile", kind="success")

    return {"received": True}


@router.get("/portal")
async def customer_portal(user=Depends(_dep_current_user)):
    """Redirect to Lemon Squeezy customer portal for subscription management."""
    if not PAYMENTS_ENABLED:
        raise HTTPException(501, "Payments are not configured.")
    sub = await db.payments.find_one({"user_id": user.id, "type": "subscription", "status": {"$in": ["active", "trialing"]}}, {"_id": 0})
    if not sub:
        raise HTTPException(404, "No active subscription found.")
    ls_id = sub.get("lemon_squeezy_subscription_id") or sub.get("session_id")
    if not ls_id:
        raise HTTPException(404, "Subscription ID not found.")
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.lemonsqueezy.com/v1/subscriptions/{ls_id}",
            headers={"Authorization": f"Bearer {LEMON_SQUEEZY_API_KEY}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {}).get("attributes", {})
            portal_url = data.get("urls", {}).get("customer_portal")
            if portal_url:
                return {"url": portal_url}
    raise HTTPException(500, "Could not retrieve customer portal URL. Try again later.")


@router.get("/history")
async def payment_history(user=Depends(_dep_current_user)):
    cursor = db.payments.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).limit(50)
    return {"payments": await cursor.to_list(50)}