"""
test_readiness_gdpr_regressions.py — Phase 4 (readiness/ops) regressions.

Covers the Phase 4 audit gaps fixed in server.py:

  1. /api/ready must hold at 503 until the background startup task completes
     (a 200 routes traffic to a half-initialized or crashed container) and
     must never surface raw DB driver exception strings to an unauthenticated
     probe.

  2. GDPR self-delete must revoke outstanding JWTs via token_version (same
     mechanism as revoke_all_sessions) and must report only collection NAMES
     to the client — raw DB exception strings stay in server-side logs/audit
     meta.

  3. GDPR account export must include payments (also guest-checkout rows keyed
     by buyer email), digital purchases, sessions, notifications, portfolio,
     and chat history.

Everything runs against in-memory fakes: no Mongo, no network.
Tests are sync and drive coroutines with asyncio.run(), mirroring the
helper convention in test_payment_entitlement_regressions.py (pytest-asyncio
is not a test dependency of this repo).
"""
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server  # noqa: E402


def _run(coro):
    """Run a coroutine in a fresh event loop (repo test convention)."""
    return asyncio.run(coro)


def _json(resp):
    return json.loads(resp.body)


# ---------------------------------------------------------------------------
# In-memory fakes (just enough Mongo surface for the handlers under test).
# ---------------------------------------------------------------------------
class FakeCursor:
    def __init__(self, rows):
        self._rows = list(rows)

    def sort(self, *args, **kwargs):
        return self

    async def to_list(self, length=None):
        return self._rows[:length] if length is not None else list(self._rows)


class FakeCollection:
    def __init__(self, rows=None, fail_delete=False):
        self.rows = list(rows or [])
        self.fail_delete = fail_delete
        self.updates = []
        self.deleted = []

    async def find_one(self, filt=None, projection=None):
        return self.rows[0] if self.rows else None

    def find(self, filt=None, projection=None):
        return FakeCursor(self.rows)

    async def update_one(self, filt, update, upsert=False):
        self.updates.append((filt, update))

    async def update_many(self, filt, update, upsert=False):
        self.updates.append((filt, update))

    async def delete_many(self, filt):
        if self.fail_delete:
            raise Exception("connection refused at mongodb://secret-host:27017")
        self.deleted.append(filt)


class FakeDB:
    def __init__(self, collections=None):
        self._collections = dict(collections or {})

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._collections.setdefault(name, FakeCollection())

    def __getitem__(self, name):
        return self._collections.setdefault(name, FakeCollection())


@pytest.fixture()
def fake_audit(monkeypatch):
    calls = []

    async def _audit(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(server, "audit", _audit)
    return calls


# ---------------------------------------------------------------------------
# /api/ready — startup gating + no raw DB error strings.
# ---------------------------------------------------------------------------
class TestReadyGating:
    def test_ready_503_while_startup_incomplete(self, monkeypatch):
        async def _ping(*args, **kwargs):
            return {"ok": 1}

        monkeypatch.setattr(
            server, "client", SimpleNamespace(admin=SimpleNamespace(command=_ping)))
        monkeypatch.setattr(server, "_startup_impl_done", False)

        resp = _run(server.ready())
        assert resp.status_code == 503
        body = _json(resp)
        assert body["ready"] is False
        assert body["reason"] == "starting"
        assert body["startup_complete"] is False

    def test_ready_200_after_startup_completes(self, monkeypatch):
        async def _ping(*args, **kwargs):
            return {"ok": 1}

        monkeypatch.setattr(
            server, "client", SimpleNamespace(admin=SimpleNamespace(command=_ping)))
        monkeypatch.setattr(server, "_startup_impl_done", True)

        body = _run(server.ready())
        assert body == {"ready": True, "startup_complete": True}

    def test_db_down_hides_raw_driver_errors(self, monkeypatch):
        async def _ping(*args, **kwargs):
            raise Exception("connection refused at mongodb://secret-host:27017")

        monkeypatch.setattr(
            server, "client", SimpleNamespace(admin=SimpleNamespace(command=_ping)))
        monkeypatch.setattr(server, "_startup_impl_done", True)

        resp = _run(server.ready())
        assert resp.status_code == 503
        body = _json(resp)
        assert body["reason"] == "db_down"
        assert body["detail"] == "database unreachable"
        assert "secret-host" not in resp.body.decode()


# ---------------------------------------------------------------------------
# GDPR self-delete — token revocation + sanitized error reporting.
# ---------------------------------------------------------------------------
class TestGdprDelete:
    def test_self_delete_revokes_outstanding_tokens(self, fake_audit, monkeypatch):
        db = FakeDB({"users": FakeCollection()})
        monkeypatch.setattr(server, "db", db)
        user = SimpleNamespace(id="u1", role="student", email="u1@example.com")

        result = _run(server.gdpr_delete_account(user))
        assert result["ok"] is True

        _filt, update = db.users.updates[0]
        assert update.get("$inc") == {"token_version": 1}
        assert update["$set"]["is_active"] is False

    def test_error_response_reports_names_not_db_details(self, fake_audit, monkeypatch):
        db = FakeDB({
            "users": FakeCollection(),
            "chat_history": FakeCollection(fail_delete=True),
        })
        monkeypatch.setattr(server, "db", db)
        user = SimpleNamespace(id="u1", role="student", email="u1@example.com")

        result = _run(server.gdpr_delete_account(user))
        assert result["ok"] is False
        assert result["partial"] is True
        assert "chat_history" in result["errors"]
        # Raw DB exception strings must never reach the client.
        assert "secret-host" not in json.dumps(result)


# ---------------------------------------------------------------------------
# GDPR export — completeness (payments, purchases, sessions, notifications,
# portfolio, chat).
# ---------------------------------------------------------------------------
class TestGdprExport:
    def test_export_includes_payments_and_user_collections(self, fake_audit, monkeypatch):
        db = FakeDB({
            "users": FakeCollection([{"id": "u1", "email": "u1@example.com", "role": "student"}]),
            "payments": FakeCollection([{"id": "p1", "user_id": "u1", "amount_cents": 900}]),
            "notifications": FakeCollection([{"id": "n1", "user_id": "u1"}]),
            "chat_history": FakeCollection([{"id": "c1", "user_id": "u1"}]),
            "digital_purchases": FakeCollection([]),
            "auth_sessions": FakeCollection([]),
            "portfolio": FakeCollection([]),
        })
        monkeypatch.setattr(server, "db", db)
        user = SimpleNamespace(id="u1", role="student", email="u1@example.com")

        export = _run(server.gdpr_export_data(user))
        assert export["user_id"] == "u1"
        assert export["exported_at"]
        assert export["profile"]["email"] == "u1@example.com"
        assert export["payments"][0]["id"] == "p1"
        assert export["notifications"][0]["id"] == "n1"
        assert export["chat_history"][0]["id"] == "c1"
        # Collections with no rows stay omitted (existing contract).
        assert "digital_purchases" not in export
        assert "auth_sessions" not in export
        assert "portfolio" not in export
