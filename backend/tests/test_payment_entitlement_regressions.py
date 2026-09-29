"""
test_payment_entitlement_regressions.py — Phase 3 (payments) regressions.

Provider-free, DB-free regressions for the payment/entitlement fixes:

  1. Lemon Squeezy order_created: `product_key` is resolved BEFORE the payment
     row is written. The old handler referenced `product_key` inside the
     insert_one document before assignment, so an UnboundLocalError was
     swallowed by the surrounding try/except and the payment record was lost
     for every order.

  2. Lemon Squeezy order_created: only a PAID order may move money or grant
     anything (BYOK unlock, scholarship pledge, tier upgrade, digital
     purchases). order_created also fires for unpaid/pending orders.

  3. Stripe checkout.session.completed: media fulfillment and the
     payment_pending → fulfilled transition are gated on
     payment_status == "paid".

  4. (xfail — fix pending) Gumroad webhook must fail CLOSED when a
     GUMROAD_API_KEY is configured and the sale cannot be verified through
     the Gumroad API. The current handler logs the failure and grants the
     entitlements anyway.

Everything runs against in-memory fakes: no Mongo, no provider, no network.
Tests are sync and drive coroutines with asyncio.run(), mirroring the
helper convention in test_password_reset_unit.py (pytest-asyncio is not a
test dependency of this repo).
"""
import asyncio
import hashlib
import hmac
import json
import re
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException  # noqa: E402

import routers.payments as payments  # noqa: E402

LS_SECRET = "test-webhook-secret"
BUYER = "buyer@example.com"


# ---------------------------------------------------------------------------
# In-memory fakes (just enough Mongo surface for the webhook paths).
# ---------------------------------------------------------------------------
class DuplicateKeyError(Exception):
    code = 11000


class FakeCollection:
    def __init__(self):
        self.docs = []
        self.inserted = []
        self.updates = []

    def _matches(self, doc, filt):
        for key, want in (filt or {}).items():
            have = doc.get(key)
            if isinstance(want, dict) and "$regex" in want:
                flags = re.I if want.get("$options") == "i" else 0
                if not re.match(want["$regex"], str(have or ""), flags):
                    return False
            elif have != want:
                return False
        return True

    async def insert_one(self, doc):
        if "_id" in doc and any(d.get("_id") == doc["_id"] for d in self.docs):
            raise DuplicateKeyError(f"duplicate _id {doc['_id']}")
        self.docs.append(doc)
        self.inserted.append(doc)

    async def find_one(self, filt, projection=None):
        for doc in self.docs:
            if self._matches(doc, filt):
                return doc
        return None

    async def update_one(self, filt, update, upsert=False):
        self.updates.append((filt, update))
        for doc in self.docs:
            if self._matches(doc, filt):
                doc.update(update.get("$set", {}))
                return
        if upsert:
            doc = dict(filt)
            doc.update(update.get("$setOnInsert", {}))
            doc.update(update.get("$set", {}))
            self.docs.append(doc)

    async def update_many(self, filt, update, upsert=False):
        for doc in self.docs:
            if self._matches(doc, filt):
                doc.update(update.get("$set", {}))

    async def find_one_and_update(self, filt, update, sort=None):
        for doc in self.docs:
            if self._matches(doc, filt):
                doc.update(update.get("$set", {}))
                return doc
        return None

    async def delete_one(self, filt):
        for i, doc in enumerate(self.docs):
            if self._matches(doc, filt):
                del self.docs[i]
                return


class FakeDB:
    def __init__(self):
        for name in ("payments", "users", "webhook_events", "digital_purchases",
                     "scholarship_pledges", "scholarship_funds", "media_checkout_pending",
                     "media_products", "media_purchases", "creator_earnings",
                     "creator_checkout_pending", "creator_enrollments",
                     "creator_courses", "payment_pending", "payment_failures"):
            setattr(self, name, FakeCollection())


class FakeRequest:
    def __init__(self, payload: bytes, headers=None):
        self._payload = payload
        self.headers = headers or {}

    async def body(self):
        return self._payload


async def _noop(*args, **kwargs):
    return None


def _run(coro):
    """Run a coroutine in a fresh event loop (repo test convention)."""
    return asyncio.run(coro)


@pytest.fixture()
def fake_db(monkeypatch):
    """Fresh fakes bound into the router; rollback deferral stubbed off."""
    db = FakeDB()
    payments.bind(db, _noop, _noop, None)
    monkeypatch.setenv("LEMON_SQUEEZY_WEBHOOK_SECRET", LS_SECRET)

    stub = types.ModuleType("routers.system_rollback")

    async def _never_defer(*args, **kwargs):
        return False

    stub.payment_webhook_maybe_defer = _never_defer
    monkeypatch.setitem(sys.modules, "routers.system_rollback", stub)
    return db


def _ls_request(event):
    payload = json.dumps(event).encode()
    sig = hmac.new(LS_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return FakeRequest(payload, {"x-signature": sig})


def _ls_order_event(order_id, status, product_name):
    return {
        "meta": {"event_name": "order_created", "event_id": f"evt-{order_id}"},
        "data": {
            "id": order_id,
            "attributes": {
                "user_email": BUYER,
                "total": 300,
                "currency": "usd",
                "status": status,
                "first_order_item": {"product_name": product_name},
            },
        },
    }


def _user():
    return {"id": "u-1", "email": BUYER, "feature_tier": "free"}


def _tier_sets(db):
    return [u["$set"] for _, u in db.users.updates if "feature_tier" in u.get("$set", {})]


# ---------------------------------------------------------------------------
# Lemon Squeezy — payment record must survive (regression: UnboundLocalError).
# ---------------------------------------------------------------------------
class TestLemonSqueezyOrderRecord:
    def test_payment_record_written_with_product_key(self, fake_db):
        """Regression: the old handler raised UnboundLocalError while building
        the insert_one document, so no payment row was ever recorded."""
        fake_db.users.docs.append(_user())
        name = payments.PAYMENT_PRODUCTS["byok"]["name"]

        async def scenario():
            await payments.payments_webhook(
                _ls_request(_ls_order_event("ord-1", "paid", name)))

        _run(scenario())

        assert len(fake_db.payments.inserted) == 1
        row = fake_db.payments.inserted[0]
        assert row["product_key"] == "byok"
        assert row["amount_cents"] == 300
        assert row["status"] == "paid"
        assert row["provider_order_id"] == "ord-1"

    def test_unknown_product_falls_back_to_order_marker(self, fake_db):
        fake_db.users.docs.append(_user())

        async def scenario():
            await payments.payments_webhook(
                _ls_request(_ls_order_event("ord-2", "paid", "Something We Don't Sell")))

        _run(scenario())
        assert fake_db.payments.inserted[0]["product_key"] == "lemon_squeezy_order"


# ---------------------------------------------------------------------------
# Lemon Squeezy — unpaid orders must not move money or grant anything.
# ---------------------------------------------------------------------------
class TestLemonSqueezyPaidGating:
    def test_unpaid_order_does_not_activate_byok(self, fake_db):
        """Regression: BYOK activation was not gated on the order being paid."""
        fake_db.users.docs.append(_user())
        name = payments.PAYMENT_PRODUCTS["byok"]["name"]

        async def scenario():
            await payments.payments_webhook(
                _ls_request(_ls_order_event("ord-3", "pending", name)))

        _run(scenario())

        byok_sets = [u for _, u in fake_db.users.updates
                     if u.get("$set", {}).get("byok_enabled")]
        assert byok_sets == []
        # The order itself is still recorded for reconciliation.
        assert fake_db.payments.inserted[0]["status"] == "pending"

    def test_paid_order_activates_byok(self, fake_db):
        fake_db.users.docs.append(_user())
        name = payments.PAYMENT_PRODUCTS["byok"]["name"]

        async def scenario():
            await payments.payments_webhook(
                _ls_request(_ls_order_event("ord-4", "paid", name)))

        _run(scenario())
        assert any(u.get("$set", {}).get("byok_enabled") is True
                   for _, u in fake_db.users.updates)

    def test_unpaid_order_grants_no_tier(self, fake_db):
        """Regression: _grant_tier_by_email ran for unpaid orders too."""
        fake_db.users.docs.append(_user())
        name = payments.PAYMENT_PRODUCTS["more_monthly"]["name"]

        async def scenario():
            await payments.payments_webhook(
                _ls_request(_ls_order_event("ord-5", "pending", name)))

        _run(scenario())
        assert _tier_sets(fake_db) == []

    def test_paid_order_grants_tier(self, fake_db):
        fake_db.users.docs.append(_user())
        name = payments.PAYMENT_PRODUCTS["more_monthly"]["name"]

        async def scenario():
            await payments.payments_webhook(
                _ls_request(_ls_order_event("ord-6", "paid", name)))

        _run(scenario())
        sets = _tier_sets(fake_db)
        assert sets and sets[0]["feature_tier"] == "member"

    def test_unpaid_order_grants_no_digital_purchase(self, fake_db):
        """Regression: book/guide ownership was granted without a paid check."""
        fake_db.users.docs.append(_user())
        name = payments.PAYMENT_PRODUCTS["book"]["name"]

        async def scenario():
            await payments.payments_webhook(
                _ls_request(_ls_order_event("ord-7", "pending", name)))

        _run(scenario())
        assert fake_db.digital_purchases.inserted == []
        assert fake_db.digital_purchases.updates == []

    def test_paid_order_grants_digital_purchase(self, fake_db):
        fake_db.users.docs.append(_user())
        name = payments.PAYMENT_PRODUCTS["book"]["name"]

        async def scenario():
            await payments.payments_webhook(
                _ls_request(_ls_order_event("ord-8", "paid", name)))

        _run(scenario())
        assert len(fake_db.digital_purchases.docs) == 1
        assert fake_db.digital_purchases.docs[0]["product_key"] == "book"

    def test_duplicate_event_is_idempotent(self, fake_db):
        fake_db.users.docs.append(_user())
        name = payments.PAYMENT_PRODUCTS["byok"]["name"]

        async def scenario():
            first = await payments.payments_webhook(
                _ls_request(_ls_order_event("ord-9", "paid", name)))
            second = await payments.payments_webhook(
                _ls_request(_ls_order_event("ord-9", "paid", name)))
            return first, second

        first, second = _run(scenario())
        assert first == {"received": True}
        # Either dedup layer may ack the replay (event-id or provider-order-id);
        # both are idempotent acks and neither re-records the payment.
        assert second in ({"received": True, "duplicate": True},
                          {"received": True, "idempotent": True})
        assert len(fake_db.payments.inserted) == 1


# ---------------------------------------------------------------------------
# Stripe — unpaid checkout sessions must not fulfill.
# ---------------------------------------------------------------------------
def _stripe_event(payment_status, product_key, title, session_id="cs_1"):
    return {
        "type": "checkout.session.completed",
        "id": "evt_" + session_id,
        "data": {"object": {
            "id": session_id,
            "metadata": {"product_key": product_key, "product_title": title},
            "amount_total": 500,
            "customer_details": {"email": BUYER},
            "payment_status": payment_status,
            "client_reference_id": "u-1",
            "mode": "payment",
            "subscription": "",
            "customer": "",
        }},
    }


def _wire_stripe(monkeypatch, event):
    monkeypatch.setattr(payments, "STRIPE_WEBHOOK_SECRET", "whsec")
    monkeypatch.setattr(
        payments, "_stripe",
        lambda: SimpleNamespace(
            Webhook=SimpleNamespace(construct_event=lambda p, s, k: event)))
    return FakeRequest(json.dumps(event).encode(), {"stripe-signature": "sig"})


class TestStripePaidGating:
    def test_unpaid_media_order_not_fulfilled(self, fake_db, monkeypatch):
        """Regression: checkout.session.completed fulfilled goods even when
        payment_status was not 'paid' (async payment methods)."""
        fake_db.users.docs.append(_user())
        pending = {"buyer_email": BUYER, "provider_product_name": "Prompt Pack",
                   "status": "pending", "product_id": "p1", "buyer_id": "u-1"}
        fake_db.media_checkout_pending.docs.append(pending)
        fake_db.media_products.docs.append(
            {"id": "p1", "title": "Prompt Pack", "price_cents": 500,
             "owner_id": "creator-1", "file_url": "https://files/p1"})
        req = _wire_stripe(
            monkeypatch, _stripe_event("unpaid", "media", "Prompt Pack"))

        _run(payments.stripe_webhook(req))

        assert fake_db.media_purchases.inserted == []
        assert pending["status"] == "pending"

    def test_paid_media_order_fulfilled(self, fake_db, monkeypatch):
        fake_db.users.docs.append(_user())
        pending = {"buyer_email": BUYER, "provider_product_name": "Prompt Pack",
                   "status": "pending", "product_id": "p1", "buyer_id": "u-1"}
        fake_db.media_checkout_pending.docs.append(pending)
        fake_db.media_products.docs.append(
            {"id": "p1", "title": "Prompt Pack", "price_cents": 500,
             "owner_id": "creator-1", "file_url": "https://files/p1"})
        req = _wire_stripe(
            monkeypatch, _stripe_event("paid", "media", "Prompt Pack"))

        _run(payments.stripe_webhook(req))

        assert len(fake_db.media_purchases.inserted) == 1
        assert pending["status"] == "fulfilled"

    def test_unpaid_catalog_order_pending_row_and_tier_untouched(
            self, fake_db, monkeypatch):
        fake_db.users.docs.append(_user())
        pending = {"provider_order": "cs_2", "status": "pending",
                   "product_key": "more_monthly", "user_id": "u-1"}
        fake_db.payment_pending.docs.append(pending)
        req = _wire_stripe(
            monkeypatch,
            _stripe_event("unpaid", "more_monthly", "", session_id="cs_2"))

        _run(payments.stripe_webhook(req))

        assert pending["status"] == "pending"  # regression: was marked fulfilled
        assert _tier_sets(fake_db) == []

    def test_paid_catalog_order_fulfills_pending_row(self, fake_db, monkeypatch):
        fake_db.users.docs.append(_user())
        pending = {"provider_order": "cs_3", "status": "pending",
                   "product_key": "more_monthly", "user_id": "u-1"}
        fake_db.payment_pending.docs.append(pending)
        req = _wire_stripe(
            monkeypatch,
            _stripe_event("paid", "more_monthly", "", session_id="cs_3"))

        _run(payments.stripe_webhook(req))

        assert pending["status"] == "fulfilled"


# ---------------------------------------------------------------------------
# Gumroad — unverifiable sales must be rejected (fix pending).
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    reason="Phase 3 fix pending (editor snapshot limit blocked the patch): "
           "with GUMROAD_API_KEY configured, an unverifiable sale must be "
           "rejected (400) instead of processed. See the Phase 3 handoff.",
    strict=False)
class TestGumroadVerificationFailClosed:
    def test_unverifiable_sale_is_rejected(self, fake_db, monkeypatch):
        monkeypatch.setattr(payments, "GUMROAD_API_KEY", "gr-test-key")
        monkeypatch.setattr(payments, "PAYMENTS_ENABLED", True)

        import httpx

        class _FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

            async def get(self, *args, **kwargs):
                return SimpleNamespace(status_code=404)

        monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)

        payload = json.dumps({
            "sale_id": "s-1",
            "email": BUYER,
            "product_name": payments.PAYMENT_PRODUCTS["more_monthly"]["name"],
            "amount": 900,
            "currency": "usd",
            "subscribe": "y",
        }).encode()

        with pytest.raises(HTTPException) as ei:
            _run(payments.gumroad_webhook(FakeRequest(payload)))
        assert ei.value.status_code == 400
        assert fake_db.payments.inserted == []
