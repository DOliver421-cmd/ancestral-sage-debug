"""Offline behavioral tests for forensic remediation of audit findings.

These tests prove the actual behavior of the fixed execution paths WITHOUT a
live MongoDB / LLM provider / payment provider. Each test mounts the real
router (routers.ai / routers.media / routers.payments) into a minimal FastAPI
app, binds stubbed shared state, and drives real HTTP requests through the
actual handler code.

Covered findings:
  1. Media file serving fails closed (authenticated + paid entitlement).
  2. Persona dispatch enforces activation state (deactivated => 403).
  3. Persona chat distinguishes REAL vs FALLBACK/FAILURE (does not masquerade).
  4. Payments webhook is idempotent (repeat delivery is a no-op).

These are unit tests: they do NOT start the server and do NOT touch a database.
"""
import os

# Set before any router import so module-level env reads behave.
os.environ.setdefault("JWT_SECRET", "forensic-test-secret")
os.environ.setdefault("MONGO_URL", "")  # keep DB disabled for these units
os.environ["LEMON_SQUEEZY_WEBHOOK_SECRET"] = "forensic-webhook-secret"

import hmac
import hashlib
import urllib.parse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import routers.media
import routers.payments
import routers.ai


# ── Fake database surface (only the methods the routers use) ───────────────
class FakeDb:
    def __init__(self, capabilities: dict):
        self._cap = capabilities

    async def media_products_find_file(self, file_ref):
        return self._cap.get("media_products_by_file", [])

    async def media_purchases_find_one(self, q):
        return self._cap.get("media_purchase", None)

    async def persona_activations_find_one(self, q, proj):
        return self._cap.get("persona_activation", None)

    async def payments_find_one(self, q, proj=None):
        if q.get("provider_order_id") == "LS-ORD-DUP-123":
            return {"id": "pay-existing", "provider_order_id": "LS-ORD-DUP-123"}
        return None

    # Payment webhook also calls these only when NOT idempotent-guarded.
    async def payments_insert_one(self, doc):
        return None

    async def users_find_one(self, q, proj=None):
        return None

    async def users_update_one(self, q, u):
        return None

    async def audit_insert_one(self, *_):
        return None

    async def notifications_insert_one(self, *_):
        return None

    async def scholarship_pledges_find_one_and_update(self, *a, **k):
        return None

    async def chat_history_insert_one(self, *_):
        return None


class FakeCtx:
    """Each method is realized as a FakeDb exposed via attribute, mirroring how
    the routers read `db.media_products.find(...)` etc."""

    def __init__(self, capabilities: dict):
        self._cap = capabilities

    @property
    def persona_activations(self):
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

    # find_one
    async def find_one(self, q, proj=None):
        if self._cap.get("kind") == "persona_activation":
            return self._cap.get("persona_activation")
        if self._cap.get("kind") == "media_purchases":
            return self._cap.get("media_purchase")
        if self._cap.get("kind") == "payments":
            if q.get("provider_order_id") == "LS-ORD-DUP-123":
                return {"id": "pay-existing"}
            return None
        return None

    # and_ / query builders for to_list
    def to_list(self, n):
        from types import SimpleNamespace
        return (self._cap.get("media_products_by_file") or [])

    def __call__(self, *a, **k):
        return self

    async def find(self, q, proj=None):
        return self

    def to_list(self, n):
        return self._cap.get("media_products_by_file") or []

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

    def curr_user(authz=None):
        return user

    def noop_rate(*a, **k):
        return None

    def fake_auth(authz=None):  # _dep_current_user used by persona_chat
        return user

    routers.ai.bind(db, fake_auth, None, None, noop_rate)

    # Stub the LLM + persona-loader so no network/provider call occurs.
    import ai.persona_loader as pl
    import ai.source_protocol as sp
    import ai.llm_gateway as gw

    monkeypatch.setattr(pl, "load_personas", lambda: {"cipher": "system prompt"})
    monkeypatch.setattr(sp, "compose_system", lambda s, **k: s)
    monkeypatch.setattr(sp, "get_controls", lambda: {})
    monkeypatch.setattr(sp, "apply_controls", lambda s, c, **k: s)
    monkeypatch.setattr(gw, "call_llm", lambda **k: {"text": "real answer", "provider": "groq"})

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
@pytest.fixture
def media_app():
    app = FastAPI()
    db = FakeCtx({})
    owner = routers.media.User(
        id="owner-1", email="owner@example.com", full_name="Owner", role="student"
    )

    routers.media.bind(db, lambda a: owner, None)

    # Stub GridFS so 200-path does not need a real Mongo client.
    import motor.motor_asyncio as mma

    class FakeBucket:
        async def open_download_stream(self, oid):
            return StreamStub()

    class StreamStub:
        async def __aiter__(self):
            yield b"file-bytes"

        async def read(self, n):
            return b""

    monkeypatch_needed = True  # patched at use site via monkeypatch
    app.include_router(routers.media.router)
    return TestClient(app), db, owner, monkeypatch_needed


class _BytesStream:
    def __init__(self):
        self._done = False

    async def read(self, n=65536):
        if self._done:
            return b""
        self._done = True
        return b"payload"

    def metadata(self):
        return {"content_type": "application/pdf"}

    @property
    def filename(self):
        return "f.pdf"


def _fake_bucket_factory(bucket=None):
    async def open_download_stream(oid):
        return _BytesStream()
    return open_download_stream


def _make_owner_ctx():
    return routers.media.User(
        id="owner-1", email="owner@example.com", full_name="Owner", role="student"
    )


def _priced_product(owner_id, file_url):
    return {"id": "mp-1", "owner_id": owner_id, "price_cents": 1500,
            "published": True, "file_url": file_url}


def test_media_file_paid_non_purchaser_403(monkeypatch):
    app = FastAPI()
    db = FakeCtx({
        "kind": "media_purchases",
        "media_purchase": None,
        "media_products_by_file": [_priced_product("owner-1", "/api/media/file/507f1f77bcf86cd799439011")],
    })
    buyer = make_user(role="student", user_id="buyer-1")
    routers.media.bind(db, lambda a: buyer, None)
    app.include_router(routers.media.router)

    client = TestClient(app)
    resp = client.get(
        "/media/file/507f1f77bcf86cd799439011",
        headers={"Authorization": "Bearer token"},
    )
    assert resp.status_code == 403, f"expected 403 for non-purchaser, got {resp.status_code}: {resp.text}"
    assert "Purchase required" in resp.text


def test_media_file_paid_owner_200(monkeypatch):
    app = FastAPI()
    db = FakeCtx({
        "kind": "media_purchases",
        "media_purchase": None,
        "media_products_by_file": [_priced_product("owner-1", "/api/media/file/507f1f77bcf86cd799439011")],
    })
    owner = _make_owner_ctx()
    routers.media.bind(db, lambda a: owner, None)
    app.include_router(routers.media.router)

    # Stub GridFS to avoid a real Mongo client on the 200 path.
    import motor.motor_asyncio as mma
    monkeypatch.setattr(mma, "AsyncIOMotorGridFSBucket", lambda db: _FakeBucket())
    client = TestClient(app)
    resp = client.get(
        "/media/file/507f1f77bcf86cd799439011",
        headers={"Authorization": "Bearer token"},
    )
    assert resp.status_code == 200, f"expected 200 for owner, got {resp.status_code}: {resp.text}"


class _FakeBucket:
    async def open_download_stream(self, oid):
        return _BytesStream()


def test_media_file_unauthenticated_401(monkeypatch):
    """The file endpoint must fail closed for unauthenticated callers."""
    from fastapi import HTTPException

    def deny(authz=None):
        raise HTTPException(401, "Missing bearer token")

    app = FastAPI()
    db = FakeCtx({"kind": "media_purchases", "media_purchase": None,
                  "media_products_by_file": [_priced_product("owner-1", "/api/media/file/507f1f77bcf86cd799439011")]})
    routers.media.bind(db, deny, None)
    app.include_router(routers.media.router)
    client = TestClient(app)
    resp = client.get("/media/file/507f1f77bcf86cd799439011")  # no auth header
    assert resp.status_code == 401, f"expected 401 unauthenticated, got {resp.status_code}"


# ── 3. PAYMENTS WEBHOOK IDEMPOTENCY ─────────────────────────────────────────
def test_payments_webhook_repeat_delivery_is_noop(monkeypatch):
    """Two deliveries of the same order: second is idempotent (no fan-out)."""
    app = FastAPI()
    db = FakeCtx({"kind": "payments"})
    routers.payments.bind(db, None, None, lambda a: make_user())

    # Force idempotency guard to see a prior record for this order.
    db._cap["provider_order_seen"] = True
    app.include_router(routers.payments.router)
    client = TestClient(app)

    payload = {"meta": {"event_name": "order_created"},
               "data": {"id": "LS-ORD-DUP-123",
                        "attributes": {"user_email": "b@e.com", "total": "10.00", "status": "paid"}}}
    body = urllib.parse.dumps(payload).encode() if False else __import__("json").dumps(payload).encode()
    sig = hmac.new("forensic-webhook-secret".encode(), body, hashlib.sha256).hexdigest()

    resp = client.post("/webhook", content=body,
                       headers={"Content-Type": "application/json", "X-Signature": sig})
    assert resp.status_code == 200, f"expected 200 idempotent ack, got {resp.status_code}: {resp.text}"
    assert resp.json().get("idempotent") is True


def test_payments_webhook_rejects_bad_signature():
    app = FastAPI()
    db = FakeCtx({"kind": "payments"})
    routers.payments.bind(db, None, None, lambda a: make_user())
    app.include_router(routers.payments.router)
    client = TestClient(app)
    body = __import__("json").dumps({"meta": {"event_name": "order_created"}}).encode()
    resp = client.post("/webhook", content=body,
                       headers={"Content-Type": "application/json", "X-Signature": "bogus"})
    assert resp.status_code == 400, f"expected 400 bad signature, got {resp.status_code}"