"""Offline behavioral tests for AI Team Bridge delivery (routers/bridge.py).

Proves, WITHOUT a live MongoDB / LLM provider / network:
  1. Outbound dispatch in webhook mode POSTs a signed payload to the configured
     URL and records a structured `delivery` (attempts, HTTP status, delivered_at).
  2. Delivery retries (up to 3 attempts) and reports `failed` with the last
     error when the partner keeps failing.
  3. Manual mode never POSTs — the dispatch is logged for hand-off.
  4. An invalid webhook URL fails closed instead of attempting delivery.
  5. Inbound receipt is idempotent per dispatch_id (retried deliveries do not
     duplicate records) and rejects a wrong shared secret.

These are unit tests: they do NOT start the server and do NOT touch a database.
"""
import os

os.environ.setdefault("JWT_SECRET", "bridge-test-secret")
os.environ.setdefault("MONGO_URL", "")

import hmac
import hashlib
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import routers.bridge as bridge_mod


# ── Fake db surface for the bridge collections ──────────────────────────────
class _Col:
    """A single collection fake: append-only insert_one into a shared store."""

    def __init__(self, store):
        self._store = store

    async def insert_one(self, doc):
        self._store.append(doc)
        return None

    async def find_one(self, q, proj=None):
        return None

    async def create_index(self, *a, **k):
        return None


class _InboundCol(_Col):
    """bridge_inbound: find_one by dispatch_id so retried deliveries dedupe."""

    async def find_one(self, q, proj=None):
        if "dispatch_id" in q and q["dispatch_id"]:
            for m in self._store:
                if m.get("dispatch_id") == q["dispatch_id"]:
                    return m
        return None


class BridgeDb:
    def __init__(self, config: dict):
        self._config = config
        self.dispatches = []   # docs written to bridge_dispatch_log
        self.inbound = []      # docs written to bridge_inbound
        self.bridge_dispatch_log = _Col(self.dispatches)
        self.bridge_inbound = _InboundCol(self.inbound)

    @property
    def bridge_config(self):
        return self

    async def find_one(self, q, proj=None):
        if q.get("_id") == "default":
            return dict(self._config)
        if "dispatch_id" in q and q["dispatch_id"]:
            for m in self.inbound:
                if m.get("dispatch_id") == q["dispatch_id"]:
                    return m
        return None

    async def replace_one(self, q, doc, upsert=False):
        return None

    async def create_index(self, *a, **k):
        return None


def _config(**over):
    cfg = {
        "enabled": True,
        "partner_team_name": "WAI-Institute AI Team",
        "partner_domain": "https://www.wai-institute.org",
        "partner_sites": [],
        "goals": "Coordinate tasks between the two sites.",
        "protocol": "Brief -> dispatch -> respond -> log.",
        "webhook_url": "",
        "dispatch_mode": "manual",
        "shared_secret": "bridge-shared-secret",
        "participants": [
            {"key": "director", "display_name": "The Director", "role": "lead", "goals": "g", "participating": True},
            {"key": "nam_oshun_scholar", "display_name": "NAM Oshun Scholar", "role": "scholar", "goals": "g", "participating": True},
        ],
        "updated_at": None,
        "updated_by": "",
    }
    cfg.update(over)
    return cfg


class _FakeResp:
    def __init__(self, status_code):
        self.status_code = status_code


class _FakeAsyncClient:
    """Replaces httpx.AsyncClient; records every outbound POST."""
    status_code = 200
    calls = []

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, **k):
        _FakeAsyncClient.calls.append({"url": url, **k})
        return _FakeResp(_FakeAsyncClient.status_code)


def _bridge_app(monkeypatch, config, user_role="admin"):
    import ai.llm_gateway as gw

    async def _llm(**k):  # the bridge awaits the gateway result
        return {"text": "coordination note", "provider": "groq"}

    monkeypatch.setattr(gw, "call_llm", _llm)

    import httpx
    _FakeAsyncClient.calls = []
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)

    app = FastAPI()
    db = BridgeDb(config)
    user = bridge_mod.User(
        id="admin-1", email="admin@example.com", full_name="Admin", role=user_role
    )

    async def current_user(authz=None):
        return user

    bridge_mod.bind(db, current_user, None, None, None)
    app.include_router(bridge_mod.router)
    return TestClient(app), db


def _dispatch_payload():
    return {"kind": "task", "title": "Curriculum blueprint review", "task": "Review the 12-module electrical program outline."}


def test_bridge_dispatch_manual_mode_never_posts(monkeypatch):
    client, db = _bridge_app(monkeypatch, _config(dispatch_mode="manual"))
    resp = client.post("/bridge/dispatch", json=_dispatch_payload(),
                       headers={"Authorization": "Bearer x"})
    assert resp.status_code == 200, resp.text
    data = resp.json()["dispatch"]
    assert data["status"] == "logged"
    assert data["channel"] == "manual"
    assert data["delivery"]["mode"] == "manual"
    assert data["delivery"]["attempts"] == 0
    assert _FakeAsyncClient.calls == [], "manual mode must never POST"
    assert db.dispatches, "dispatch must still be logged for hand-off"


def test_bridge_dispatch_webhook_delivers_with_signature(monkeypatch):
    secret = "bridge-shared-secret"
    webhook = "https://partner.example.com/hook"
    client, db = _bridge_app(monkeypatch, _config(dispatch_mode="webhook", webhook_url=webhook))
    _FakeAsyncClient.status_code = 200

    resp = client.post("/bridge/dispatch", json=_dispatch_payload(),
                       headers={"Authorization": "Bearer x"})
    assert resp.status_code == 200, resp.text
    data = resp.json()["dispatch"]
    assert data["status"] == "delivered"
    assert data["channel"] == "webhook"
    assert data["delivery"]["mode"] == "webhook"
    assert data["delivery"]["attempts"] == 1
    assert data["delivery"]["last_status"] == 200
    assert data["delivery"]["delivered_at"], "delivered_at must be recorded"

    # The outbound POST carries a signed, idempotent payload.
    assert len(_FakeAsyncClient.calls) == 1
    call = _FakeAsyncClient.calls[0]
    assert call["url"] == webhook
    body = call["content"]
    assert json.loads(body)["dispatch_id"] == data["dispatch_id"]
    expected_sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert call["headers"].get("X-Bridge-Signature") == expected_sig, "outbound payload must be HMAC-signed"


def test_bridge_dispatch_webhook_retries_then_fails(monkeypatch):
    client, db = _bridge_app(monkeypatch, _config(
        dispatch_mode="webhook", webhook_url="https://partner.example.com/hook"))
    _FakeAsyncClient.status_code = 503

    resp = client.post("/bridge/dispatch", json=_dispatch_payload(),
                       headers={"Authorization": "Bearer x"})
    assert resp.status_code == 200, resp.text
    data = resp.json()["dispatch"]
    assert data["status"] == "failed"
    assert data["delivery"]["attempts"] == 3, "must retry up to 3 attempts"
    assert data["delivery"]["last_status"] == 503
    assert "503" in (data["delivery"]["last_error"] or ""), "last error must explain the failure"
    assert not data["delivery"]["delivered_at"]


def test_bridge_dispatch_invalid_webhook_url_fails_closed(monkeypatch):
    client, db = _bridge_app(monkeypatch, _config(
        dispatch_mode="webhook", webhook_url="not-a-url"))
    resp = client.post("/bridge/dispatch", json=_dispatch_payload(),
                       headers={"Authorization": "Bearer x"})
    assert resp.status_code == 200, resp.text
    data = resp.json()["dispatch"]
    assert data["status"] == "failed"
    assert "http" in (data["delivery"]["last_error"] or "").lower()
    assert _FakeAsyncClient.calls == [], "no POST may be attempted for an invalid URL"


def test_bridge_receive_deduplicates_by_dispatch_id(monkeypatch):
    client, db = _bridge_app(monkeypatch, _config())
    body = {"dispatch_id": "d-1", "subject": "Ack", "body": "Received"}
    headers = {"Content-Type": "application/json", "X-Bridge-Secret": "bridge-shared-secret"}

    first = client.post("/bridge/receive", json=body, headers=headers)
    assert first.status_code == 200, first.text
    assert first.json()["duplicate"] is False
    message_id = first.json()["message_id"]

    second = client.post("/bridge/receive", json=body, headers=headers)
    assert second.status_code == 200, second.text
    assert second.json()["duplicate"] is True
    assert second.json()["message_id"] == message_id, "retry must return the same record"
    assert len(db.inbound) == 1, "a retried delivery must not duplicate the inbound record"


def test_bridge_receive_rejects_wrong_secret(monkeypatch):
    client, db = _bridge_app(monkeypatch, _config())
    resp = client.post("/bridge/receive", json={"dispatch_id": "d-2", "body": "x"},
                       headers={"Content-Type": "application/json", "X-Bridge-Secret": "wrong"})
    assert resp.status_code == 401, f"expected 401 for wrong secret, got {resp.status_code}"
