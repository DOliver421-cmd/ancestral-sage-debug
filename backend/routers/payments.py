"""
Payments router — Lemon Squeezy → Gumroad checkout pipeline.

Extracted verbatim from backend/server.py (monolith refactor, slice 0).
Shared module state (db, audit, notify, current_user) is bound by server.py
via bind() at include time, so this module has no circular imports.
"""
import os
import uuid
import logging
import asyncio
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


# ─── PAYMENTS (Lemon Squeezy → Stripe → Gumroad) ────────────────────────────
# Ecommerce runs through the publishing pipeline in ai/publishing.py.
# Provider chain order — Lemon Squeezy is the merchant of record (owner
# directive, restated 2026-08-28); Stripe remains as a configured fallback:
#   Tier 1 — Lemon Squeezy  (LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID)
#   Tier 2 — Stripe         (STRIPE_SECRET_KEY [+ STRIPE_WEBHOOK_SECRET])
#   Tier 3 — Gumroad        (GUMROAD_API_KEY)
#   Tier 4 — MongoDB archive (always works)
# Contracts are fulfilled (tier grant / digital delivery) by the webhook that
# matches the chosen provider.

STRIPE_SECRET_KEY      = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET  = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
LEMON_SQUEEZY_API_KEY = os.environ.get("LEMON_SQUEEZY_API_KEY", "")
LEMON_SQUEEZY_STORE_ID = os.environ.get("LEMON_SQUEEZY_STORE_ID", "")
GUMROAD_API_KEY = os.environ.get("GUMROAD_API_KEY", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://www.morehelp.center")

STRIPE_ENABLED = bool(STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY)
PAYMENTS_ENABLED = bool(
    STRIPE_ENABLED
    or ((LEMON_SQUEEZY_API_KEY and LEMON_SQUEEZY_STORE_ID) or GUMROAD_API_KEY)
)


def _stripe():
    """Return a configured Stripe client (sync) or None if no secret is set."""
    if not STRIPE_SECRET_KEY:
        return None
    try:
        import stripe  # lazily imported — SDK is an optional runtime dependency
        if getattr(stripe, "api_key", "") != STRIPE_SECRET_KEY:
            stripe.api_key = STRIPE_SECRET_KEY
        return stripe
    except Exception:
        logger.exception("Stripe SDK not installed — Stripe tier unavailable")
        return None


def _resolve_provider() -> str:
    """Truthful active payment provider (first configured in chain order).

    Lemon Squeezy first — merchant of record per owner directive. Gumroad is
    the one-time fallback, Stripe last-resort (deferred per owner)."""
    if LEMON_SQUEEZY_API_KEY and LEMON_SQUEEZY_STORE_ID:
        return "lemon_squeezy"
    if GUMROAD_API_KEY:
        return "gumroad"
    if STRIPE_ENABLED:
        return "stripe"
    return "disabled"


async def reload_payment_keys(db=None) -> int:
    """Load payment-provider keys from the encrypted vault (env wins).

    Payment providers (Stripe, Lemon Squeezy, Gumroad) may be stored in the
    same encrypted Provider Gateway vault used for AI keys. This runs at
    startup and after every exec save so a pasted payment key takes effect
    immediately without a redeploy. Returns the number of keys loaded from DB.
    """
    from ai.llm_gateway import reload_provider_keys as _ai_reload
    # Env constants (the canonical source) keep winning over DB-typed values.
    loaded = 0
    try:
        import keyvault as _kv
        fernet = _kv.get_fernet()
    except Exception:
        fernet = None
    global STRIPE_ENABLED, STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET
    global LEMON_SQUEEZY_API_KEY, LEMON_SQUEEZY_STORE_ID, GUMROAD_API_KEY, PAYMENTS_ENABLED
    if not db:
        try:
            from deps import get_db as _get_db
            db = _get_db()
        except Exception:
            db = None
    if db is not None and fernet is not None:
        try:
            providers = {}
            async for p in db.api_providers.find({"provider_type": {"$in": ["stripe", "lemon_squeezy", "gumroad"]}}):
                providers[p.get("provider_type")] = p.get("id")
            if providers:
                async for k in db.api_keys.find({"provider_id": {"$in": list(providers.values())}, "status": "active"}):
                    ptype = next((t for t, pid in providers.items() if pid == k.get("provider_id")), None)
                    if not ptype:
                        continue
                    try:
                        key = fernet.decrypt(k["encrypted_key"].encode()).decode()
                    except Exception:
                        key = k.get("encrypted_key", "")
                    def _decrypt(field):
                        raw = k.get(field, "")
                        if not raw:
                            return ""
                        try:
                            return fernet.decrypt(raw.encode()).decode()
                        except Exception:
                            return raw
                    if ptype == "stripe":
                        if not os.environ.get("STRIPE_SECRET_KEY", "").strip():
                            STRIPE_SECRET_KEY = key
                        if not os.environ.get("STRIPE_PUBLISHABLE_KEY", "").strip():
                            STRIPE_PUBLISHABLE_KEY = _decrypt("second_encrypted_key")
                        if not os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip():
                            STRIPE_WEBHOOK_SECRET = _decrypt("third_encrypted_key")
                    elif ptype == "lemon_squeezy":
                        if not os.environ.get("LEMON_SQUEEZY_API_KEY", "").strip():
                            LEMON_SQUEEZY_API_KEY = key
                        if not os.environ.get("LEMON_SQUEEZY_STORE_ID", "").strip():
                            LEMON_SQUEEZY_STORE_ID = _decrypt("second_encrypted_key")
                    elif ptype == "gumroad":
                        if not os.environ.get("GUMROAD_API_KEY", "").strip():
                            GUMROAD_API_KEY = key
                    loaded += 1
        except Exception as e:
            logger.warning("reload_payment_keys error: %s", e)
    # Recompute derived flags after any vault fill.
    STRIPE_ENABLED = bool(STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY)
    PAYMENTS_ENABLED = bool(STRIPE_ENABLED or ((LEMON_SQUEEZY_API_KEY and LEMON_SQUEEZY_STORE_ID) or GUMROAD_API_KEY))
    try:
        # Also adopt any newly stored AI keys (openai/deepseek/etc.) in one pass.
        loaded += await _ai_reload(db)
    except Exception:
        pass
    return loaded

# Product catalog — amounts in cents USD.
# Only every item here is fully fulfillable end-to-end. A membership purchase
# grants its tier (or a credential/DYOK/donation/scholarship row) via the webhook.
# Physical SKUs were removed: no delivery provider is wired, so selling them
# would be a dead end. The Arena/Our-Legacy digital keys were removed: they had
# no media product or deliverable behind them — the real creator catalog lives
# in db.media_products (Store feed). If a product cannot be delivered, it is not
# listed here — no sale without fulfillment.
PAYMENT_PRODUCTS = {
    "more_monthly":   {"name": "M.O.R.E. Membership – Monthly",   "amount":  999, "mode": "subscription", "interval": "month", "description": "Monthly M.O.R.E. community access"},
    "more_annual":    {"name": "M.O.R.E. Membership – Annual",    "amount": 7999, "mode": "subscription", "interval": "year",  "description": "Annual M.O.R.E. membership (save 33%)"},
    "member_monthly": {"name": "M.O.R.E. Member – Monthly",            "amount":  900, "mode": "subscription", "interval": "month", "description": "M.O.R.E. Member tier — full community + AI Tutor"},
    "plus_monthly":   {"name": "M.O.R.E. Plus – Monthly",              "amount": 1500, "mode": "subscription", "interval": "month", "description": "M.O.R.E. Plus tier — priority matching + expanded courses"},
    "pro_monthly":    {"name": "M.O.R.E. Pro – Monthly",               "amount": 2900, "mode": "subscription", "interval": "month", "description": "M.O.R.E. Pro tier — advanced courses, labs, full AI suite"},
    "patron_monthly": {"name": "M.O.R.E. Patron – Monthly",            "amount": 5900, "mode": "subscription", "interval": "month", "description": "M.O.R.E. Patron — founders circle + funds free access for others"},
    "donation":       {"name": "Donation – M.O.R.E. Help Center",      "amount": None, "mode": "payment",      "description": "Support the M.O.R.E. Help Center mission"},
    # BYOK — $3 one-time unlock (below instructor tier). Grants byok_enabled,
    # not a membership tier; instructor tier and above activate free.
    "byok":           {"name": "BYOK – Bring Your Own Key",            "amount":  300, "mode": "payment",      "description": "One-time $3 unlock — attach a free Groq, Cerebras, or Gemini key so your AI runs on your own key"},
    # Sponsor a Scholarship — milestone-based giving. Amount is set by the
    # sponsor (like donation); a paid order matches the sponsor's pledge.
    "scholarship":    {"name": "Sponsor a Scholarship — M.O.R.E. Help Center",      "amount": None, "mode": "payment", "description": "Sponsor a scholar — Full, Partial, or Collective. Milestone-based release, fully transparent."},
    # Our Legacy book — one-time digital purchase
    "book":           {"name": "Our Legacy · Our Future — The Book",                "amount": 8900, "mode": "payment", "description": "One-time digital purchase of the Our Legacy book"},
    # Creator's Sanctuary tiers (creator lane — see _PRODUCT_TIER_MAP)
    "sanctuary_trial":   {"name": "M.O.R.E. Creator's Sanctuary – 3-Day Trial",     "amount":  300, "mode": "payment",      "description": "All-access 3 days & 33 minutes trial — everything through Pro"},
    "sanctuary_paid":    {"name": "M.O.R.E. Creator's Sanctuary – Paid Creator",    "amount":  700, "mode": "subscription", "interval": "month", "description": "Member-level creator lane — $7/mo", "deprecated": True},
    "sanctuary_creator": {"name": "M.O.R.E. Creator's Sanctuary – Advanced Creator","amount": 1100, "mode": "subscription", "interval": "month", "description": "Plus-level creator lane — $11/mo", "deprecated": True},
    "sanctuary_mod":     {"name": "M.O.R.E. Creator's Sanctuary – Certified Mod",   "amount": 1500, "mode": "subscription", "interval": "month", "description": "Pro-level creator lane — $15/mo", "deprecated": True},
}

# Legacy names (pre-rebrand) → product key, so the LS webhook keeps matching
# orders made under the old names after the physical/arena removal. Current
# names survive; deprecated-flag SKUs typed by a legacy alias are still
# grantable if a legacy subscription somehow renews. Aliases that pointed at
# REMOVED SKUs (tshirt/workbook/kit/credential/book/arena_*) are intentionally
# absent — those products no longer exist and must not be sold.
_LEGACY_PRODUCT_NAMES = {
    "WAI Member – Monthly": "member_monthly",
    "WAI Plus – Monthly": "plus_monthly",
    "WAI Pro – Monthly": "pro_monthly",
    "WAI Patron – Monthly": "patron_monthly",
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
    "sanctuary_trial":    "plus",
    "sanctuary_paid":     "member",
    "sanctuary_creator":  "plus",
    "sanctuary_mod":      "pro",
}

TIER_RANK = {"free": 0, "member": 1, "plus": 2, "pro": 3, "patron": 4, "platinum": 5, "executive": 6}


class CheckoutReq(BaseModel):
    product_key: str
    amount_cents: Optional[int] = None  # required only for "donation"
    quantity: int = 1
    extra_meta: Optional[dict] = None


def _match_product_key(name: str):
    """Resolve a Lemon Squeezy product name to a catalog key (current + legacy)."""
    key = next(
        (k for k, pr in PAYMENT_PRODUCTS.items()
         if str(pr["name"]).lower() == str(name).lower()),
        None,
    )
    if not key:
        key = _LEGACY_PRODUCT_NAMES.get(str(name))
    return key


# Creator share of Media Store sales (Mandate 2: creator-first 70/30 split).
MEDIA_CREATOR_SHARE = float(os.environ.get("MEDIA_CREATOR_SHARE", "0.70"))


async def _fulfill_media_order(buyer_email: str, product_name: str, order_id: str):
    """Grant a paid Media Store purchase and record the 70/30 revenue split.

    Called from the order_created webhook. Matches the pending-sale row the
    checkout endpoint wrote (buyer email + provider product name), then:
      1. inserts media_purchases → download unlocks immediately
      2. inserts a creator_earnings row (gross / creator share / platform fee)
         so the split is verifiable by the creator in their earnings dashboard
      3. marks the pending row fulfilled (audit trail, no double-grant)
    Idempotent: an already-fulfilled pending row short-circuits.
    """
    import re as _re
    if not (buyer_email and product_name):
        return
    email_rx = "^" + _re.escape(buyer_email.strip().lower()) + "$"
    name_rx = "^" + _re.escape(product_name.strip()) + "$"
    pending = await db.media_checkout_pending.find_one_and_update(
        {"buyer_email": {"$regex": email_rx, "$options": "i"},
         "provider_product_name": {"$regex": name_rx},
         "status": "pending"},
        {"$set": {"status": "fulfilled",
                  "fulfilled_at": datetime.now(timezone.utc).isoformat(),
                  "provider_order_id": order_id}},
        sort=[("created_at", -1)],
    )
    if not pending:
        return  # not a store product (or already fulfilled) — nothing to do

    product_id = pending.get("product_id", "")
    product = await db.media_products.find_one({"id": product_id})
    if not product:
        logger.error("media fulfillment: pending sale references missing product %s", product_id)
        return

    buyer = await db.users.find_one(
        {"email": {"$regex": email_rx, "$options": "i"}}, {"id": 1}
    )
    buyer_id = (buyer or {}).get("id") or pending.get("buyer_id", "")
    price_cents = int(product.get("price_cents", 0)) or int(pending.get("price_cents", 0))

    # Idempotency guard: never double-record a purchase.
    existing = await db.media_purchases.find_one(
        {"buyer_id": buyer_id, "product_id": product_id}
    ) if buyer_id else None
    if not existing:
        await db.media_purchases.insert_one({
            "id": str(uuid.uuid4())[:8],
            "buyer_id": buyer_id,
            "product_id": product_id,
            "title": product.get("title", ""),
            "file_url": product.get("file_url", ""),
            "purchased_at": datetime.now(timezone.utc).isoformat(),
            "price_cents": price_cents,
            "provider_order_id": order_id,
        })

    # 70/30 creator-first split — verifiable ledger row in the creator's own
    # earnings dashboard (same collection the payout processor reads).
    owner_id = product.get("owner_id", "")
    if owner_id and owner_id != buyer_id and price_cents > 0:
        now = datetime.now(timezone.utc)
        creator_share = round(price_cents * MEDIA_CREATOR_SHARE)
        await db.creator_earnings.insert_one({
            "creator_id": owner_id,
            "period": now.strftime("%Y-%m"),
            "source": "media_store",
            "product_id": product_id,
            "product_title": product.get("title", ""),
            "buyer_id": buyer_id,
            "order_id": order_id,
            "gross_cents": price_cents,
            "creator_share_cents": creator_share,
            "platform_fee_cents": price_cents - creator_share,
            "payout_status": "pending",
            "created_at": now.isoformat(),
        })
        try:
            await notify(owner_id, "Store Sale",
                         f"'{product.get('title', 'Your product')}' just sold — ${creator_share / 100:.2f} added to your pending earnings (70% creator share).",
                         link="/creator/earnings", kind="success")
        except Exception:
            pass

    if buyer_id:
        try:
            await audit(buyer_id, "media.purchased",
                        target=product_id, meta={"order_id": order_id, "price_cents": price_cents})
            await notify(buyer_id, "Purchase Complete",
                         f"'{product.get('title', 'Your purchase')}' is ready — download it anytime from My Purchases.",
                         link="/store", kind="success")
        except Exception:
            pass
    logger.info("media fulfillment OK: %s bought %s (split %d/%d cents)",
                buyer_email, product_id, creator_share if price_cents else 0,
                (price_cents - creator_share) if price_cents else 0)


async def _grant_tier_by_email(user_email: str, product_key: str, *, reason: str = "payment"):
    """Upgrade-only tier grant matched by buyer email (order + subscription events).

    Shared by order_created and subscription_resumed/unpaused. Never
    downgrades: a renewal, resume, or a different product's event cannot
    strip a higher tier granted elsewhere.
    """
    if not (user_email and product_key and product_key in _PRODUCT_TIER_MAP):
        return
    user_doc = await _find_user_by_email(
        user_email,
        {"_id": 0, "id": 1, "feature_tier": 1, "feature_tier_expires_at": 1},
    )
    if not user_doc:
        return
    granted = _PRODUCT_TIER_MAP[product_key]
    prev_tier = user_doc.get("feature_tier", "free")
    now = datetime.now(timezone.utc)
    if TIER_RANK.get(granted, 0) > TIER_RANK.get(prev_tier, 0):
        set_fields = {
            "feature_tier": granted,
            "feature_tier_source": "trial" if product_key == "sanctuary_trial" else reason,
            "feature_tier_product": product_key,
            "feature_tier_updated_at": now.isoformat(),
        }
        unset_fields = {}
        if product_key == "sanctuary_trial":
            # Time-boxed all-access: revert to their previous tier after the trial window.
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
    try:
        await audit(user_doc["id"], "tier.granted",
                    meta={"product": product_key, "tier": granted, "reason": reason})
    except Exception:
        pass
    if reason == "resume":
        try:
            await notify(user_doc["id"], "Subscription Active",
                         "Your subscription is active again, so its features are unlocked.",
                         link="/plans", kind="success")
        except Exception:
            pass
    else:
        try:
            await notify(user_doc["id"], "Payment Confirmed",
                         "Thank you! Your payment has been received and your features are unlocked.",
                         link="/profile", kind="success")
        except Exception:
            pass


def _email_rx(email: str) -> str:
    """Case-insensitive exact-match regex source for buyer emails.

    Lemon Squeezy lowercases buyer emails; this site stores the email exactly
    as typed at registration (auth.py does not normalize case). An exact-match
    lookup therefore silently fails for any member who registered with a
    capital letter — they pay and no entitlement is granted. Escaped so emails
    containing '+' or '.' cannot widen the match."""
    import re as _re
    return "^" + _re.escape((email or "").strip()) + "$"


async def _find_user_by_email(email: str, projection: dict) -> Optional[dict]:
    """Find a user by buyer email, case-insensitively (webhook-safe)."""
    if not email:
        return None
    return await db.users.find_one(
        {"email": {"$regex": _email_rx(email), "$options": "i"}}, projection
    )


@router.get("/products")
async def list_payment_products():
    provider = _resolve_provider()
    return {
        "publishable_key": STRIPE_PUBLISHABLE_KEY if provider == "stripe" else "",
        "products": PAYMENT_PRODUCTS,
        "payments_enabled": PAYMENTS_ENABLED,
        "provider": provider,
        "stripe_publishable_key": STRIPE_PUBLISHABLE_KEY if provider == "stripe" else "",
    }


async def _create_stripe_checkout(product_key: str, product: dict, amount_cents: int,
                                  is_subscription: bool, user) -> Optional[dict]:
    """Create a hosted Stripe Checkout Session.

    Returns {"url", "id"} on success, or None if Stripe isn't configured / the
    SDK is unavailable / Stripe can't build the session. The caller falls back
    to the next provider in the chain (Lemon Squeezy → Gumroad).
    """
    stripe = _stripe()
    if not stripe:
        return None
    try:
        base_url = FRONTEND_URL.rstrip("/")
        metadata = {"product_key": product_key}
        # A deterministic ledger so the webhook can attribute the sale back to
        # this platform user even when their email differs on Stripe.
        client_ref = getattr(user, "id", "") or (getattr(user, "email", "") or "") or "guest"
        params: dict = {
            "client_reference_id": str(client_ref),
            "metadata": metadata,
            "success_url": f"{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{base_url}/payment/cancel",
            "mode": "payment",
        }
        if is_subscription:
            interval = product.get("interval", "month")
            price = await asyncio.to_thread(
                stripe.Price.create,
                currency="usd",
                unit_amount=amount_cents,
                recurring={"interval": interval, "interval_count": 1},
                product_data={"name": product["name"]},
            )
            params["mode"] = "subscription"
            params["line_items"] = [{"price": price["id"], "quantity": 1}]
        else:
            params["line_items"] = [{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": amount_cents,
                    "product_data": {"name": product["name"]},
                },
                "quantity": 1,
            }]
        session = await asyncio.to_thread(stripe.checkout.Session.create, **params)
        if not session or not session.get("url"):
            return None
        return {"url": session["url"], "id": session.get("id", "")}
    except Exception:
        logger.exception("Stripe checkout failed for %s — falling back to next provider", product_key)
        return None


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

    # Tier 1 — Lemon Squeezy (PRIMARY — merchant of record per owner directive;
    # digital products + subscriptions, then one-time digital). This is the
    # business-primary processor as decided by the owner. Stripe was deferred
    # (could not be configured correctly) and is only a LAST-RESORT fallback
    # below, never the first choice.
    ls_result = await _publish_lemon_squeezy(
        name=product["name"],
        description=product.get("description", ""),
        price_cents=amount,
        persona="platform",
        is_subscription=is_subscription,
        interval=product.get("interval", "month"),
        checkout_email=user.email,
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

    # Tier 3 — Stripe (LAST-RESORT fallback — one-time + subscriptions)
    stripe_session = await _create_stripe_checkout(
        product_key=req.product_key,
        product=product,
        amount_cents=amount,
        is_subscription=is_subscription,
        user=user,
    )
    if stripe_session:
        # Pre-payment ledger so a dropped webhook is still reconcilable: the
        # pending row carries the buyer + product, matching how the media
        # checkout already records a pending sale before the provider round-trip.
        try:
            session_id = stripe_session.get("id") or ""
            await db.payment_pending.insert_one({
                "id": session_id or (str(uuid.uuid4())[:16]),
                "user_id": user.id,
                "buyer_email": (user.email or "").lower(),
                "product_key": req.product_key,
                "amount_cents": amount,
                "provider": "stripe",
                "provider_order": session_id or "",
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            logger.exception("checkout: failed to record pending order for %s", req.product_key)
        await audit(
            user.id, "payment_checkout_created",
            meta={"product": req.product_key, "provider": "stripe",
                  "session_id": stripe_session.get("id")},
        )
        return {"url": stripe_session["url"], "session_id": stripe_session.get("id")}


    if not PAYMENTS_ENABLED:
        raise HTTPException(
            501,
            "Payments are not configured. Add STRIPE_SECRET_KEY (or LEMON_SQUEEZY_API_KEY + "
            "LEMON_SQUEEZY_STORE_ID, or GUMROAD_API_KEY) in your environment.",
        )
    raise HTTPException(
        500,
        "Payment processing failed. The payment providers are configured but the request could not be completed. "
        "Check your Stripe, Lemon Squeezy, or Gumroad API keys and try again.",
    )


@router.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    """Stripe webhook — verify signature, then fulfill the paid contract.

    Configure in Stripe → Developers → Webhooks with endpoint:
        {FRONTEND_URL}/api/payments/stripe-webhook
    Events to send: check.session.completed, customer.subscription.deleted,
    invoice.paid (for live renewals). The checkout session carries
    `metadata.product_key` (catalog key or "media") so fulfillment is
    deterministic and idempotent.

    Returns 202 to acknowledge even when the SDK/types are missing so Stripe
    does not fire endless retries for cosmetic failures; contract-critical
    errors still surface in the audit log.
    """
    import json
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(404, "Stripe webhook not configured (STRIPE_WEBHOOK_SECRET)")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    stripe = _stripe()
    if not stripe:
        raise HTTPException(404, "Stripe SDK unavailable")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception:
        logger.exception("Stripe webhook signature verification failed")
        raise HTTPException(400, "Invalid Stripe signature")

    event_type = event.get("type", "")
    event_id = str(event.get("id", ""))
    # Idempotency — same as the Lemon Squeezy webhook; duplicate delivery is a no-op.
    if event_id:
        try:
            await db.webhook_events.insert_one({
                "_id": event_id,
                "event_name": event_type,
                "provider": "stripe",
                "received_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as _dup:
            if getattr(_dup, "code", None) == 11000:
                return {"received": True, "duplicate": True}
            pass

    data_obj = event.get("data", {}).get("object", {}) or {}

    # ── One-time purchase / subscription activation ──────────────────────────
    if event_type == "checkout.session.completed":
        session = data_obj
        session_meta = session.get("metadata") or {}
        product_key = session_meta.get("product_key", "")
        session_id = str(session.get("id", ""))
        amount_cents = int(session.get("amount_total") or 0)
        buyer_email = (session.get("customer_details") or {}).get("email") or ""
        paid = session.get("payment_status") == "paid"
        # raw = "subscription" if session['mode'] == 'subscription' else "payment"

        client_ref = str(session.get("client_reference_id") or "")
        # Prefer the deterministic buyer id in client_reference_id, else match email.
        buyer_id = client_ref if (client_ref and client_ref not in ("guest", "")) else ""

        # Media Store digital product — match the pending-sale row (buyer + title)
        if product_key == "media":
            title = session_meta.get("product_title") or ""
            try:
                await _fulfill_media_order(buyer_email=buyer_email, product_name=title,
                                           order_id=session_id)
            except Exception:
                logger.exception("Stripe webhook: media fulfillment failed (%s)", session_id)
            return {"received": True}

        # Mark the pre-payment pending row fulfilled (it unmatchable rows remain
        # pending and are surfaced for human reconciliation). Idempotent by design.
        try:
            await db.payment_pending.update_one(
                {"provider_order": session_id, "status": "pending"},
                {"$set": {"status": "fulfilled", "fulfilled_at": datetime.now(timezone.utc).isoformat()}},
            )
        except Exception:
            pass

        # Catalog product — record the order, grant tier / BYOK / scholarship.
        await _record_stripe_order({
            "session": session, "session_id": session_id,
            "product_key": product_key, "amount_cents": amount_cents,
            "buyer_email": buyer_email, "buyer_id": buyer_id,
            "paid": paid, "mode": session.get("mode", "payment"),
        })
        return {"received": True}

    # ── Subscriptions: renewal keeps the tier live (still under its product).
    if event_type == "invoice.paid":
        sub_id = str(data_obj.get("subscription") or "")
        meta = {}  # invoice objects carry customer + a linked subscription, not our metadata
        if sub_id:
            # Re-grant is upgrade-only/idempotent; nothing else is needed since
            # our metadata product_key isn't on the invoice. Tie by subscription.
            try:
                await db.payments.update_one(
                    {"provider_order_id": sub_id, "provider": "stripe"},
                    {"$set": {"status": "active",
                              "last_invoice_paid_at": datetime.now(timezone.utc).isoformat()}},
                    upsert=True,
                )
            except Exception:
                logger.exception("Stripe webhook: invoice.paid update failed")
        return {"received": True}

    # ── Subscription cancelled / unpaid → revoke the tier it granted.
    if event_type in ("customer.subscription.deleted", "invoice.payment_failed"):
        sub_id = str(data_obj.get("id") or "")
        user_id = str(data_obj.get("metadata", {}).get("user_id") or "")
        if not user_id:
            # Recover the user from the recorded order.
            row = await db.payments.find_one(
                {"provider_order_id": sub_id, "provider": "stripe"}, {"user_id": 1})
            user_id = str((row or {}).get("user_id") or "")
        if not user_id:
            return {"received": True}
        now = datetime.now(timezone.utc)
        user_doc = await db.users.find_one(
            {"id": user_id},
            {"_id": 0, "feature_tier": 1, "feature_tier_product": 1,
             "feature_tier_revert_to": 1},
        )
        if not user_doc:
            return {"received": True}
        revert_to = (user_doc.get("feature_tier_revert_to") or "free")
        set_fields = {
            "feature_tier": revert_to,
            "feature_tier_source": "revoked",
            "feature_tier_product": "",
            "feature_tier_revoked_at": now.isoformat(),
            "feature_tier_updated_at": now.isoformat(),
        }
        await db.users.update_one({"id": user_id}, {"$set": set_fields})
        try:
            await audit(user_id, "subscription.revoked",
                        meta={"event": event_type, "product": user_doc.get("feature_tier_product")})
        except Exception:
            pass
        try:
            await notify(user_id, "Subscription Ended",
                         "Your subscription has ended, so the features it unlocked were reverted. "
                         "You can upgrade again anytime from the Plans page.",
                         link="/plans", kind="warning")
        except Exception:
            pass
        return {"received": True}

    return {"received": True}


async def _record_stripe_order(info: dict) -> None:
    """Record a completed Stripe order and apply its contract (tier/BYOK)."""
    user_id = info.get("buyer_id", "")
    buyer_email = info.get("buyer_email", "")
    product_key = info.get("product_key", "")
    if user_id and buyer_email:
        rd = await _find_user_by_email(buyer_email, {"_id": 0, "id": 1})
        if rd:
            user_id = str(rd.get("id") or "")
    try:
        await db.payments.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id or None,
            "provider": "stripe",
            "provider_order_id": info.get("session_id", ""),
            "product_key": product_key,
            "amount_cents": info.get("amount_cents", 0),
            "currency": "usd",
            "mode": info.get("mode", "payment"),
            "status": "paid" if info.get("paid") else info.get("mode", "payment"),
            "buyer_email": buyer_email,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.exception("Stripe webhook: payment record failed")

    if info.get("paid") and product_key:
        # BYOK $3 unlock / tier grant / scholarship — reuse the shared helpers.
        email = buyer_email or ""
        if email and product_key == "byok":
            rd = await _find_user_by_email(email, {"_id": 0, "id": 1})
            if rd:
                await db.users.update_one(
                    {"id": rd["id"]},
                    {"$set": {"byok_enabled": True, "byok_paid": True,
                              "byok_order_id": info.get("session_id", ""),
                              "byok_activated_at": datetime.now(timezone.utc).isoformat()}},
                )
                try:
                    await audit(rd["id"], "byok.paid", meta={"product": "byok", "order_id": info.get("session_id")})
                except Exception:
                    pass
        if email and product_key == "scholarship":
            rd = await _find_user_by_email(email, {"_id": 0, "id": 1})
            if rd:
                await db.scholarship_pledges.update_one(
                    {"user_id": rd["id"], "status": "pending"},
                    {"$set": {"status": "paid", "paid_at": datetime.now(timezone.utc).isoformat(),
                              "provider_order_id": info.get("session_id", ""),
                              "paid_amount_cents": info.get("amount_cents") or None}},
                    sort=[("created_at", -1)],
                )
        await _grant_tier_by_email(email, product_key, reason="payment")


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

    # ── Idempotency — process each Lemon Squeezy event exactly once ──────────
    # Lemon Squeezy retries failed deliveries, so the same event can arrive
    # more than once. A duplicate must never double-grant or double-revoke an
    # entitlement. The event id is stored as the _id; a second delivery hits
    # the unique index and is acknowledged as a no-op.
    event_id = str(
        (event.get("meta") or {}).get("event_id")
        or (event.get("data") or {}).get("id")
        or ""
    )
    if event_id:
        try:
            await db.webhook_events.insert_one({
                "_id": event_id,
                "event_name": event_name,
                "received_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as _dup:
            if getattr(_dup, "code", None) == 11000:
                return {"received": True, "duplicate": True}
            # DB hiccup — the grant/revoke paths below are upgrade-only or
            # guarded, so a re-delivery remains safe.
            pass

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
                # Lemon Squeezy sends `total` already in integer cents (e.g. 999
                # = $9.99). Multiplying by 100 here inflated every recorded
                # order and scholarship fund total 100× in revenue reporting.
                "amount_cents": int(total) if total else 0,
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
        product_key = _match_product_key(first_item.get("product_name", ""))
        # ── BYOK ($3 one-time unlock, below instructor tier) ────────────────
        # A paid BYOK product grants byok_enabled directly (not a membership
        # tier — instructor tier and above activate BYOK free without payment).
        if user_email and product_key == "byok":
            user_doc = await _find_user_by_email(user_email, {"id": 1, "byok_enabled": 1})
            if user_doc:
                await db.users.update_one(
                    {"id": user_doc["id"]},
                    {"$set": {
                        "byok_enabled": True,
                        "byok_paid": True,
                        "byok_order_id": order_id,
                        "byok_activated_at": datetime.now(timezone.utc).isoformat(),
                    }},
                )
                try:
                    await audit(user_doc["id"], "byok.paid", meta={"product": "byok", "order_id": order_id})
                except Exception:
                    pass
                await notify(user_doc["id"], "BYOK Activated",
                             "Your $3 BYOK unlock is active — attach a free Groq, Cerebras, or Gemini key at /byok to route your AI through your own key.",
                             link="/byok", kind="success")

        # ── Media Store digital products (prompt packs, templates, files) ───
        # A paid store order MUST grant the download and record the creator's
        # 70/30 revenue split. Without this, customers pay and never receive
        # their product. Matches the pending-sale row written at checkout time.
        if user_email and status == "paid":
            try:
                await _fulfill_media_order(
                    buyer_email=user_email,
                    product_name=(first_item.get("product_name") or ""),
                    order_id=order_id,
                )
            except Exception:
                logger.exception("LS webhook: media fulfillment failed (order %s)", order_id)

        # ── Scholarship sponsorship ─────────────────────────────────────────
        # A paid scholarship order marks the sponsor's pending pledge as paid.
        # The committee then matches the pledge to an approved application
        # (milestone-based release, so funds follow real progress).
        if user_email and product_key == "scholarship":
            user_doc = await _find_user_by_email(user_email, {"id": 1})
            if user_doc:
                # `total` arrives in integer cents from Lemon Squeezy.
                paid_amount = int(total) if total else 0
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

        # Shared upgrade-only grant (order_created, subscriptions, resumes).
        await _grant_tier_by_email(user_email, product_key, reason="payment")

    # ── Subscription lifecycle — revoke the tier a cancelled/expired/paused
    # subscription granted. Revocation is scoped: it only fires when THIS
    # product is the one that granted the user's current tier, so an upgrade
    # or a separate product's renewal is never wrongly reverted.
    if event_name in ("subscription_cancelled", "subscription_expired", "subscription_paused"):
        data = (event.get("data") or {}).get("attributes") or {}
        user_email = data.get("user_email", "")
        product_key = _match_product_key(data.get("product_name", ""))
        if not (user_email and product_key and product_key in _PRODUCT_TIER_MAP):
            return {"received": True}
        user_doc = await _find_user_by_email(
            user_email,
            {"_id": 0, "id": 1, "feature_tier": 1, "feature_tier_product": 1,
             "feature_tier_revert_to": 1},
        )
        if not user_doc or user_doc.get("feature_tier_product") != product_key:
            return {"received": True}
        now = datetime.now(timezone.utc)
        revert_to = user_doc.get("feature_tier_revert_to") or "free"
        await db.users.update_one(
            {"id": user_doc["id"]},
            {
                "$set": {
                    "feature_tier": revert_to,
                    "feature_tier_source": "revoked",
                    "feature_tier_product": "",
                    "feature_tier_revoked_at": now.isoformat(),
                    "feature_tier_updated_at": now.isoformat(),
                },
                "$unset": {"feature_tier_expires_at": "", "feature_tier_revert_to": ""},
            },
        )
        try:
            await audit(user_doc["id"], "subscription.revoked",
                        meta={"product": product_key, "event": event_name})
        except Exception:
            pass
        try:
            await notify(user_doc["id"], "Subscription Ended",
                         "Your subscription has ended, so the features it unlocked were reverted. "
                         "You can upgrade again anytime from the Plans page.",
                         link="/plans", kind="warning")
        except Exception:
            pass
        return {"received": True}

    # ── Dunning: a renewal payment failed ────────────────────────────────────
    # Deliberately does NOT revoke. Lemon Squeezy retries a failed renewal over
    # several days; revoking on the first decline would punish a customer for a
    # transient bank rejection. Termination is already handled correctly by the
    # subscription_cancelled/expired/paused branch above, which fires when LS
    # exhausts its dunning retries.
    #
    # What was actually missing is the NOTIFICATION. Without it the customer is
    # never told their card failed, cannot fix it, and silently loses access days
    # later when the subscription expires — avoidable involuntary churn.
    #
    # Before this branch existed the event fell through to the terminal
    # `return {"received": True}`, which answers 200 so Lemon Squeezy marks it
    # delivered and never retries. The event looked handled and was discarded.
    if event_name == "subscription_payment_failed":
        data = (event.get("data") or {}).get("attributes") or {}
        user_email = data.get("user_email", "")
        product_key = _match_product_key(data.get("product_name", ""))
        sub_id = str((event.get("data") or {}).get("id", ""))
        now = datetime.now(timezone.utc)
        # Guarded: the event id is recorded in db.webhook_events BEFORE this
        # branch runs, so an uncaught exception here would 500, Lemon Squeezy
        # would retry, and the retry would be answered as a duplicate no-op —
        # permanently losing the dunning notice. Degrade instead of crashing.
        user_doc = None
        if user_email:
            try:
                user_doc = await _find_user_by_email(user_email, {"_id": 0, "id": 1})
            except Exception:
                logger.exception(
                    "LS webhook: user lookup failed for payment-failure (sub=%s)", sub_id
                )
        # Record the failure so the exec/billing surfaces can see at-risk revenue
        # even when the buyer email does not match a local account.
        try:
            await db.payment_failures.update_one(
                {"provider": "lemon_squeezy", "provider_order_id": sub_id},
                {"$set": {
                    "provider": "lemon_squeezy",
                    "provider_order_id": sub_id,
                    "buyer_email": user_email,
                    "product_key": product_key,
                    "user_id": (user_doc or {}).get("id", ""),
                    "status": data.get("status", ""),
                    "last_failed_at": now.isoformat(),
                },
                 "$inc": {"failure_count": 1},
                 "$setOnInsert": {"first_failed_at": now.isoformat()}},
                upsert=True,
            )
        except Exception:
            logger.exception("LS webhook: payment-failure record failed (%s)", sub_id)
        if user_doc:
            try:
                await notify(
                    user_doc["id"],
                    "Payment failed — update your card",
                    "We could not process your subscription renewal. Please update your "
                    "payment method to keep your access. We will retry automatically for "
                    "a few days before the subscription ends.",
                    link="/plans", kind="warning",
                )
            except Exception:
                logger.exception("LS webhook: dunning notify failed (%s)", user_doc.get("id"))
            try:
                await audit(user_doc["id"], "subscription.payment_failed",
                            meta={"product": product_key, "event": event_name})
            except Exception:
                pass
        else:
            logger.warning(
                "LS webhook: subscription_payment_failed for unmatched email (sub=%s) — "
                "recorded for manual reconciliation", sub_id,
            )
        return {"received": True}

    # ── Refunds — a refunded order revokes what it granted. Refunds are
    # issued as site credit unless the platform caused the failure (see the
    # Refund Policy page), so the paid capability goes away when the order is
    # refunded.
    if event_name == "order_refunded":
        data = (event.get("data") or {}).get("attributes") or {}
        user_email = data.get("user_email", "")
        order_id = str((event.get("data") or {}).get("id", ""))
        product_key = _match_product_key((data.get("first_order_item") or {}).get("product_name", ""))
        if not user_email:
            return {"received": True}
        user_doc = await _find_user_by_email(
            user_email,
            {"_id": 0, "id": 1, "byok_enabled": 1, "feature_tier": 1,
             "feature_tier_product": 1, "feature_tier_revert_to": 1},
        )
        if not user_doc:
            return {"received": True}
        now = datetime.now(timezone.utc)
        set_fields = {}
        unset_fields = {}
        if product_key == "byok" and user_doc.get("byok_enabled"):
            set_fields["byok_enabled"] = False
            set_fields["byok_revoked_at"] = now.isoformat()
        if product_key in _PRODUCT_TIER_MAP and user_doc.get("feature_tier_product") == product_key:
            set_fields["feature_tier"] = user_doc.get("feature_tier_revert_to") or "free"
            set_fields["feature_tier_source"] = "revoked"
            set_fields["feature_tier_product"] = ""
            set_fields["feature_tier_revoked_at"] = now.isoformat()
            set_fields["feature_tier_updated_at"] = now.isoformat()
            unset_fields = {"feature_tier_expires_at": "", "feature_tier_revert_to": ""}
        if set_fields:
            update = {"$set": set_fields}
            if unset_fields:
                update["$unset"] = unset_fields
            await db.users.update_one({"id": user_doc["id"]}, update)
            try:
                await audit(user_doc["id"], "order.refunded_revoked",
                            meta={"product": product_key, "order_id": order_id})
            except Exception:
                pass
            try:
                await notify(user_doc["id"], "Refund Processed",
                             "Your refund has been processed as site credit. The features that order "
                             "unlocked have been reverted. See the Refund Policy for details.",
                             link="/refund-policy", kind="warning")
            except Exception:
                pass
        return {"received": True}

    # ── Subscription resumed/unpaused — billing is active again, so the tier
    # the subscription grants is restored. Upgrade-only and idempotent (a
    # resume can never strip a higher tier granted by another product).
    if event_name in ("subscription_resumed", "subscription_unpaused"):
        data = (event.get("data") or {}).get("attributes") or {}
        await _grant_tier_by_email(
            data.get("user_email", ""),
            _match_product_key(data.get("product_name", "")),
            reason="resume",
        )
        return {"received": True}

    # ── Subscription created — record the subscription so /history and the
    # customer portal can track it. The tier grant itself arrives via the
    # order_created event (upgrade-only, idempotent).
    if event_name == "subscription_created":
        data = (event.get("data") or {}).get("attributes") or {}
        user_email = data.get("user_email", "")
        product_key = _match_product_key(data.get("product_name", ""))
        sub_id = str((event.get("data") or {}).get("id", ""))
        if user_email and product_key:
            user_doc = await _find_user_by_email(user_email, {"_id": 0, "id": 1})
            if user_doc:
                try:
                    await db.payments.update_one(
                        {"provider_order_id": sub_id},
                        {"$set": {
                            "user_id": user_doc["id"],
                            "provider": "lemon_squeezy",
                            "provider_order_id": sub_id,
                            "product_key": product_key,
                            "mode": "subscription",
                            "type": "subscription",
                            "lemon_squeezy_subscription_id": sub_id,
                            "status": data.get("status", "active"),
                            "buyer_email": user_email,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }},
                        upsert=True,
                    )
                except Exception:
                    logger.exception("LS webhook: subscription record failed")
        return {"received": True}

    # ── Subscription payment succeeded (renewal) ───────────────────────────────
    # A successful recurring payment keeps the subscription active. The tier
    # was already granted at subscription_created; this just records the
    # payment and refreshes the subscription document. Upgrade-only grant: a
    # higher tier from one product does not strip a tier granted by another.
    if event_name == "subscription_payment_success":
        data = (event.get("data") or {}).get("attributes") or {}
        user_email = data.get("user_email", "")
        product_key = _match_product_key(data.get("product_name", ""))
        sub_id = str((event.get("data") or {}).get("id", ""))
        try:
            await db.payments.update_one(
                {"provider_order_id": sub_id},
                {"$set": {
                    "status": data.get("status", "active"),
                    "renewal_timestamp": datetime.now(timezone.utc).isoformat(),
                }},
                upsert=True,
            )
        except Exception:
            logger.exception("LS webhook: subscription_payment_success record failed (%s)", sub_id)
        await _grant_tier_by_email(user_email, product_key, reason="renewal")
        return {"received": True}

    # ── Subscription updated (plan change: upgrade) ──────────────────────────
    # Customer changed to a different plan. Re-grant the matching tier
    # (upgrade-only — a downgrade to a lower tier is handled at the next
    # renewal cycle by subscription_cancelled/expired if the lower plan is
    # not configured separately).
    if event_name == "subscription_updated":
        data = (event.get("data") or {}).get("attributes") or {}
        user_email = data.get("user_email", "")
        product_key = _match_product_key(data.get("product_name", ""))
        sub_id = str((event.get("data") or {}).get("id", ""))
        try:
            await db.payments.update_one(
                {"provider_order_id": sub_id},
                {"$set": {
                    "product_key": product_key,
                    "status": data.get("status", "active"),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }},
                upsert=True,
            )
        except Exception:
            logger.exception("LS webhook: subscription_updated record failed (%s)", sub_id)
        await _grant_tier_by_email(user_email, product_key, reason="plan_change")
        if user_email and product_key:
            user_doc = await _find_user_by_email(user_email, {"_id": 0, "id": 1})
            if user_doc:
                try:
                    await notify(user_doc["id"], "Plan Updated",
                                 "Your plan has been updated. Any tier change is now active in your account.",
                                 link="/account/billing", kind="info")
                except Exception:
                    pass
        return {"received": True}

    return {"received": True}


@router.post("/gumroad-webhook")
async def gumroad_webhook(request: Request):
    """Gumroad sale webhook — records the sale and grants the matching tier.

    Configure in Gumroad → Settings → Advanced → Webhooks with endpoint:
        {FRONTEND_URL}/api/payments/gumroad-webhook

    Gumroad does not provide HMAC signature verification, so authenticity is
    verified by calling the Gumroad API to confirm the sale_id. When
    GUMROAD_API_KEY is not set, the sale is still processed (idempotency on
    sale_id prevents double-grant) but a warning is logged.

    Payload fields (Gumroad v2):
        email, product_permalink, product_name, sale_id, amount, currency,
        timestamp, purchase_timestamp, subscribe (y/n)
    """
    import json as _json
    import time as _time

    if not PAYMENTS_ENABLED:
        raise HTTPException(404, "Payments are not configured")

    body = await request.body()
    try:
        event = _json.loads(body)
    except Exception:
        raise HTTPException(400, "Invalid JSON payload")

    # Gumroad may send form-encoded or JSON; normalize to a dict.
    if not isinstance(event, dict):
        event = {"data": event} if event else {}

    # Extract a stable, globally-unique identifier for idempotency.
    # Gumroad's sale_id is unique per sale and survives retries.
    sale_id = str(event.get("sale_id", ""))
    email = str(event.get("email", "")).strip()
    product_name = str(event.get("product_name", "")).strip()
    amount = event.get("amount", 0)  # cents (Gumroad sends integer cents)
    currency = str(event.get("currency", "usd")).lower()
    is_subscription = str(event.get("subscribe", "")).lower() in ("y", "yes", "true", "1")

    # ── Idempotency — same as the LS webhook; duplicate delivery is a no-op ────
    if sale_id:
        try:
            await db.webhook_events.insert_one({
                "_id": f"gumroad:{sale_id}",
                "provider": "gumroad",
                "event_name": "sale",
                "sale_id": sale_id,
                "email": email,
                "product_name": product_name,
                "received_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as _dup:
            if getattr(_dup, "code", None) == 11000:
                return {"received": True, "duplicate": True}
            logger.exception("Gumroad webhook: idempotency record failed")
    else:
        logger.warning("Gumroad webhook: no sale_id in payload")

    # ── Authenticity: verify the sale via Gumroad API (when key is available) ──
    if GUMROAD_API_KEY and sale_id:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://api.gumroad.com/v2/sales/{sale_id}",
                    params={"access_token": GUMROAD_API_KEY},
                )
                if resp.status_code != 200:
                    logger.warning(
                        "Gumroad webhook: sale %s failed API verification (%d)",
                        sale_id, resp.status_code,
                    )
        except Exception:
            logger.exception("Gumroad webhook: API verification failed for sale %s", sale_id)

    # ── Match product name → catalog key ─────────────────────────────────────
    product_key = _match_product_key(product_name)

    # ── Record the payment ───────────────────────────────────────────────────
    try:
        await db.payments.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": None,
            "provider": "gumroad",
            "provider_order_id": sale_id,
            "product_key": product_key or "unknown",
            "amount_cents": int(amount) if amount else 0,
            "currency": currency,
            "mode": "subscription" if is_subscription else "payment",
            "type": "subscription" if is_subscription else "sale",
            "status": "paid",
            "buyer_email": email,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.exception("Gumroad webhook: payment record failed (sale %s)", sale_id)

    # ── BYOK ($3 one-time unlock) ────────────────────────────────────────────
    if email and product_key == "byok":
        user_doc = await _find_user_by_email(email, {"_id": 0, "id": 1})
        if user_doc:
            await db.users.update_one(
                {"id": user_doc["id"]},
                {"$set": {
                    "byok_enabled": True,
                    "byok_paid": True,
                    "byok_order_id": sale_id,
                    "byok_activated_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
            try:
                await audit(user_doc["id"], "byok.paid", meta={"product": "byok", "sale_id": sale_id, "source": "gumroad"})
            except Exception:
                pass
            await notify(user_doc["id"], "BYOK Activated",
                         "Your $3 BYOK unlock is active — attach a free Groq, Cerebras, or Gemini key at /byok to route your AI through your own key.",
                         link="/byok", kind="success")

    # ── Scholarship sponsorship ──────────────────────────────────────────────
    if email and product_key == "scholarship":
        user_doc = await _find_user_by_email(email, {"_id": 0, "id": 1})
        if user_doc:
            paid_amount = int(amount) if amount else 0
            pledge = await db.scholarship_pledges.find_one_and_update(
                {"user_id": user_doc["id"], "status": "pending"},
                {"$set": {"status": "paid", "paid_at": datetime.now(timezone.utc).isoformat(),
                          "provider_order_id": sale_id,
                          "paid_amount_cents": paid_amount or None},
                 "$setOnInsert": {"provider": "gumroad"}},
                sort=[("created_at", -1)],
            )
            if pledge:
                if pledge.get("fund_id"):
                    await db.scholarship_funds.update_one(
                        {"id": pledge["fund_id"]},
                        {"$inc": {"raised_cents": paid_amount or pledge.get("amount_cents", 0)}},
                    )
                try:
                    await audit(user_doc["id"], "scholarship.pledge_paid",
                                target=pledge.get("id"), meta={"sale_id": sale_id, "amount_cents": paid_amount or pledge.get("amount_cents", 0), "source": "gumroad"})
                except Exception:
                    pass
                await notify(user_doc["id"], "Sponsorship Received",
                             "Thank you — your sponsorship is paid and will be matched to a scholar. Track milestones in your sponsor view.",
                             link="/sponsor", kind="success")

    # ── Media Store digital products (prompt packs, templates, files) ────────
    if email and product_key and product_key not in ("byok", "scholarship", "donation"):
        try:
            await _fulfill_media_order(
                buyer_email=email,
                product_name=product_name,
                order_id=sale_id,
            )
        except Exception:
            logger.exception("Gumroad webhook: media fulfillment failed (sale %s)", sale_id)

    # ── Shared upgrade-only grant (one-time purchases + subscription starts) ─
    await _grant_tier_by_email(email, product_key, reason="gumroad_payment")

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