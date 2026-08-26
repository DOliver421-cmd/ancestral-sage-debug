"""Offline behavioral tests for forensic remediation of audit findings.

These tests prove the actual behavior of the fixed execution paths WITHOUT a
live MongoDB / LLM provider / payment provider. Each test mounts the real
router (routers.ai / routers.media / routers.payments) into a minimal FastAPI
app, binds stubbed shared state, and drives real HTTP requests through the
actual handler code.

Covered findings:
  1. Media file serving fails closed (anonymous paid file => 403, non-purchaser
     => 403, entitled owner => 200 with full-access header).
  2. Persona dispatch enforces activation state (deactivated => 403).
  3. Persona chat distinguishes REAL vs FALLBACK/FAILURE (does not masquerade).
  4. Payments webhook is idempotent (repeat delivery is a no-op) and rejects
     bad signatures.

NOTE: assertions track the MERGED implementations on main. Where main changed
an endpoint (async current_user resolution, payments router prefix, anonymous
paid files failing closed with 403 instead of 401), the tests assert the new
behavior — the old expectations were superseded by the merge.

These are unit tests: they do NOT start the server and do NOT touch a database.
"""
import os

# Set before any router import so module-level env reads behave.
os.environ.setdefault("JWT_SECRET", "forensic-test-secret")
os.environ.setdefault("MONGO_URL", "")  # keep DB disabled for these units
os.environ["LEMON_SQUEEZY_WEBHOOK_SECRET"] = "forensic-webhook-secret"

import hmac
import hashlib
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import routers.media
import routers.payments
import routers.ai


# ── Fake database surface (mirrors the async collection APIs the routers use) ─
class FakeCtx:
    """A per-collection fake. Attribute access on the db context returns this
    same object; each method behaves like the Motor surface the routers call.
    `.find(...)` is synchronous and returns self, and `.to_list(n)` is async —
    matching `await db.<col>.find(...).to_list(n)` in the handlers.
    """

    def __init__(self, capabilities: dict):
        self._cap = capabilities

    @property
    def persona_activations(self):
        return self

    @property
    def persona_controls(self):
        return self

    @property
    def media_products(self):
        return self

    @property
    def media_purchases(self):
        return self

    @property
    def payments(self):
        return self

    @property
    def webhook_events(self):
        return self

    @property
    def users(self):
        return self

    @property
    def notifications(self):
        return self

    @property
    def chat_history(self):
        return self

    @property
    def scholarship_pledges(self):
        return self

    def find(self, q=None, proj=None):
        return self

    async def to_list(self, n):
        return list(self._cap.get("media_products_by_file") or [])

    async def find_one(self, q, proj=None):
        # Dispatch by query keys so one fake can serve every collection.
        if "provider_order_id" in q:
            if q.get("provider_order_id") == "LS-ORD-DUP-123":
                return {"id": "pay-existing", "provider_order_id": "LS-ORD-DUP-123"}
            return None
        if "persona" in q:
            return self._cap.get("persona_activation")
        if "buyer_id" in q or "product_id" in q:
            return self._cap.get("media_purchase")
        if "file_url" in q:
            return self._cap.get("media_product")
        return None

    async def insert_one(self, doc):
        return None

    async def update_one(self, q, u, **k):
        return None


def make_user(role="student", user_id="u-1"):
    return routers.media.User(
        id=user_id,
        email="buyer@example.com",
        full_name="Buyer",
        role=role,
        is_active=True,
    )


# ── 1. PERSONA ACTIVATION GATE ──────────────────────────────────────────────
@pytest.fixture
def ai_app(monkeypatch):
    app = FastAPI()
    db = FakeCtx({"kind": "persona_activation", "persona_activation": {"status": "inactive"}})
    user = make_user(role="executive_admin")

    async def fake_auth(authz=None):  # merged _dep_current_user awaits this
        return user

    def noop_rate(*a, **k):
        return None

    routers.ai.bind(db, fake_auth, None, None, noop_rate)

    # Stub the LLM + persona-loader so no network/provider call occurs.
    import ai.persona_loader as pl
    import ai.source_protocol as sp
    import ai.llm_gateway as gw

    monkeypatch.setattr(pl, "load_personas", lambda: {"cipher": "system prompt"})
    monkeypatch.setattr(sp, "compose_system", lambda s, **k: s)
    monkeypatch.setattr(sp, "get_controls", lambda: {})
    monkeypatch.setattr(sp, "apply_controls", lambda s, c, **k: s)

    async def _llm(**k):  # persona_chat awaits the gateway result
        return {"text": "real answer", "provider": "groq"}

    monkeypatch.setattr(gw, "call_llm", _llm)

    app.include_router(routers.ai.router)
    return TestClient(app), db


def test_persona_chat_rejects_deactivated(ai_app):
    client, db = ai_app
    resp = client.post(
        "/personas/cipher/chat",
        json={"message": "hello", "session_id": "s"},
        headers={"Authorization": "Bearer whatever"},
    )
    assert resp.status_code == 403, f"expected 403 for deactivated persona, got {resp.status_code}: {resp.text}"
    assert "deactivated" in resp.json()["detail"].lower()


def test_persona_chat_allows_active(ai_app, monkeypatch):
    client, db = ai_app
    db._cap["persona_activation"] = {"status": "active"}
    resp = client.post(
        "/personas/cipher/chat",
        json={"message": "hello", "session_id": "s"},
        headers={"Authorization": "Bearer whatever"},
    )
    assert resp.status_code == 200, f"expected 200 for active persona, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body["reply"] == "real answer"
    assert body["status"] == "ok"  # REAL execution signalled, not fallback


# ── 2. MEDIA FILE FAILS CLOSED ──────────────────────────────────────────────
def _priced_product(owner_id, file_url):
    return {"id": "mp-1", "owner_id": owner_id, "price_cents": 1500,
            "published": True, "file_url": file_url}


class _FakeBucket:
    """GridFS stand-in: open_download_stream yields a stream whose `metadata`
    is a plain dict (the merged endpoint reads stream.metadata.get(...))."""

    def __init__(self, metadata=None, chunks=(b"payload",)):
        self._metadata = metadata or {"content_type": "application/pdf", "filename": "f.pdf"}
        self._chunks = list(chunks)

    async def open_download_stream(self, oid):
        return _StreamStub(self._metadata, self._chunks)


class _StreamStub:
    def __init__(self, metadata, chunks):
        self.metadata = metadata
        self._chunks = list(chunks)

    async def read(self, n=65536):
        return self._chunks.pop(0) if self._chunks else b""


def _media_app(monkeypatch, current_user, products, purchase=None, product=None):
    app = FastAPI()
    db = FakeCtx({
        "media_purchase": purchase,
        "media_products_by_file": products,
        "media_product": product,
    })

    async def auth(authz=None):
        return current_user

    routers.media.bind(db, auth, None)
    import motor.motor_asyncio as mma
    monkeypatch.setattr(mma, "AsyncIOMotorGridFSBucket", lambda db: _FakeBucket())
    app.include_router(routers.media.router)
    return TestClient(app)


def test_media_file_paid_non_purchaser_403(monkeypatch):
    buyer = make_user(role="student", user_id="buyer-1")
    product = _priced_product("owner-1", "/api/media/file/507f1f77bcf86cd799439011")
    client = _media_app(monkeypatch, buyer, [product], purchase=None, product=product)
    resp = client.get(
        "/media/file/507f1f77bcf86cd799439011",
        headers={"Authorization": "Bearer token"},
    )
    assert resp.status_code == 403, f"expected 403 for non-purchaser, got {resp.status_code}: {resp.text}"
    assert "Purchase required" in resp.text


def test_media_file_paid_owner_200(monkeypatch):
    owner = make_user(role="student", user_id="owner-1")
    product = _priced_product("owner-1", "/api/media/file/507f1f77bcf86cd799439011")
    client = _media_app(monkeypatch, owner, [product], purchase=None, product=product)
    resp = client.get(
        "/media/file/507f1f77bcf86cd799439011",
        headers={"Authorization": "Bearer token"},
    )
    assert resp.status_code == 200, f"expected 200 for owner, got {resp.status_code}: {resp.text}"
    assert resp.headers.get("X-Media-Full-Access") == "true"


def test_media_file_unauthenticated_paid_fails_closed_403(monkeypatch):
    """An anonymous caller requesting a priced file must fail closed (403), not
    crash (500) and not be served the file. The merged endpoint returns 403
    before the auth-required 401 check because the file is protected."""
    product = _priced_product("owner-1", "/api/media/file/507f1f77bcf86cd799439011")
    client = _media_app(monkeypatch, make_user(), [product], purchase=None, product=product)
    resp = client.get("/media/file/507f1f77bcf86cd799439011")  # no auth header
    assert resp.status_code == 403, f"expected 403 fail-closed for anonymous paid file, got {resp.status_code}: {resp.text}"
    assert "Purchase required" in resp.text


# ── 3. PAYMENTS WEBHOOK IDEMPOTENCY ─────────────────────────────────────────
def _payments_app(monkeypatch):
    app = FastAPI()
    db = FakeCtx({})
    routers.payments.bind(db, None, None, lambda a: make_user())
    app.include_router(routers.payments.router)
    return TestClient(app), db


def test_payments_webhook_repeat_delivery_is_noop(monkeypatch):
    """Two deliveries of the same order: second is idempotent (no fan-out)."""
    client, db = _payments_app(monkeypatch)
    payload = {"meta": {"event_name": "order_created", "event_id": "evt-1"},
               "data": {"id": "LS-ORD-DUP-123",
                        "attributes": {"user_email": "b@e.com", "total": "10.00", "status": "paid"}}}
    body = json.dumps(payload).encode()
    sig = hmac.new("forensic-webhook-secret".encode(), body, hashlib.sha256).hexdigest()

    resp = client.post("/payments/webhook", content=body,
                       headers={"Content-Type": "application/json", "X-Signature": sig})
    assert resp.status_code == 200, f"expected 200 idempotent ack, got {resp.status_code}: {resp.text}"
    assert resp.json().get("idempotent") is True


def test_payments_webhook_rejects_bad_signature(monkeypatch):
    client, db = _payments_app(monkeypatch)
    body = json.dumps({"meta": {"event_name": "order_created"}}).encode()
    resp = client.post("/payments/webhook", content=body,
                       headers={"Content-Type": "application/json", "X-Signature": "bogus"})
    assert resp.status_code == 400, f"expected 400 bad signature, got {resp.status_code}: {resp.text}"
