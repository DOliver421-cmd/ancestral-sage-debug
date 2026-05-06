"""In-process unit tests for the password-reset helper functions.

These complement the integration tests in test_password_reset.py by
exercising the small pure-ish helpers extracted from
reset_password_endpoint() directly:

  * _hash_token(raw)              — hashing
  * _make_reset_token()           — secure random token
  * _normalize_expiry(value)      — datetime parsing edge cases
  * _load_reset_token(hash)       — expiry / used / missing handling
  * _load_target_user_for_reset   — deactivated user handling
  * _apply_password_reset         — persistence + invalidation
  * _send_reset_email             — graceful no-op when key absent

They run against the live DB and clean up after themselves.
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient

import server  # noqa: E402
from server import (  # noqa: E402
    _apply_password_reset,
    _hash_token,
    _load_reset_token,
    _load_target_user_for_reset,
    _make_reset_token,
    _normalize_expiry,
    _send_reset_email,
    hash_pw,
    verify_pw,
)
from fastapi import HTTPException  # noqa: E402

PERF_TAG = "pytest_pwreset_unit"


def _run(coro_factory):
    """Run a coroutine in a fresh event loop with a fresh motor client.

    Mirrors the helper in test_cohorts_perf.py — Motor binds to whatever
    loop the client was created on, so each test gets its own.
    """
    async def wrapper():
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = client[os.environ.get("DB_NAME", "lcewai")]
        original_db = server.db
        original_client = server.client
        server.db = db
        server.client = client
        try:
            return await coro_factory()
        finally:
            server.db = original_db
            server.client = original_client
            client.close()

    return asyncio.run(wrapper())


# ---------- Pure helpers (no DB) -------------------------------------------

def test_hash_token_is_stable_and_deterministic():
    assert _hash_token("abc") == _hash_token("abc")
    assert _hash_token("abc") != _hash_token("abcd")
    assert len(_hash_token("anything")) == 64  # sha256 hex


def test_make_reset_token_is_random_and_long():
    a, ah = _make_reset_token()
    b, bh = _make_reset_token()
    assert a != b
    assert ah == _hash_token(a)
    assert bh == _hash_token(b)
    assert len(a) >= 32
    # Hash must NOT equal the raw token — caller must never store the raw.
    assert ah != a


def test_normalize_expiry_handles_all_input_shapes():
    # tz-aware datetime → unchanged
    dt = datetime(2030, 1, 1, tzinfo=timezone.utc)
    assert _normalize_expiry(dt) == dt
    # naive datetime → made tz-aware
    naive = datetime(2030, 1, 1)
    out = _normalize_expiry(naive)
    assert out.tzinfo == timezone.utc
    # ISO string → parsed
    iso = "2030-01-01T00:00:00+00:00"
    parsed = _normalize_expiry(iso)
    assert parsed.year == 2030
    # malformed string → minimum (already-expired sentinel)
    bad = _normalize_expiry("not-a-date")
    assert bad < datetime.now(timezone.utc)
    # None → minimum
    none_out = _normalize_expiry(None)
    assert none_out < datetime.now(timezone.utc)


def test_password_hash_round_trip():
    h = hash_pw("Initial@1")
    assert verify_pw("Initial@1", h)
    assert not verify_pw("wrong", h)


# ---------- _load_reset_token ------------------------------------------------

def test_load_reset_token_rejects_missing():
    async def go():
        with pytest.raises(HTTPException) as exc:
            await _load_reset_token("does-not-exist-" + uuid.uuid4().hex)
        assert exc.value.status_code == 400
    _run(go)


def test_load_reset_token_rejects_expired():
    raw, hashed = _make_reset_token()
    rec_id = str(uuid.uuid4())

    async def seed_and_test():
        await server.db.password_reset_tokens.insert_one({
            "id": rec_id,
            "user_id": "user-x",
            "email": "x@example.com",
            "token_hash": hashed,
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
            "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1),
            "used_at": None,
            "_perf_tag": PERF_TAG,
        })
        try:
            with pytest.raises(HTTPException) as exc:
                await _load_reset_token(hashed)
            assert exc.value.status_code == 400
            assert "expired" in exc.value.detail.lower()
        finally:
            await server.db.password_reset_tokens.delete_one({"id": rec_id})

    _run(seed_and_test)


def test_load_reset_token_rejects_used():
    raw, hashed = _make_reset_token()
    rec_id = str(uuid.uuid4())

    async def seed_and_test():
        await server.db.password_reset_tokens.insert_one({
            "id": rec_id,
            "user_id": "user-x",
            "email": "x@example.com",
            "token_hash": hashed,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "used_at": datetime.now(timezone.utc),  # already consumed
            "_perf_tag": PERF_TAG,
        })
        try:
            with pytest.raises(HTTPException) as exc:
                await _load_reset_token(hashed)
            assert exc.value.status_code == 400
        finally:
            await server.db.password_reset_tokens.delete_one({"id": rec_id})

    _run(seed_and_test)


def test_load_reset_token_succeeds_when_valid():
    raw, hashed = _make_reset_token()
    rec_id = str(uuid.uuid4())

    async def go():
        await server.db.password_reset_tokens.insert_one({
            "id": rec_id,
            "user_id": "user-y",
            "email": "y@example.com",
            "token_hash": hashed,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
            "used_at": None,
            "_perf_tag": PERF_TAG,
        })
        try:
            rec = await _load_reset_token(hashed)
            assert rec["user_id"] == "user-y"
        finally:
            await server.db.password_reset_tokens.delete_one({"id": rec_id})

    _run(go)


# ---------- _load_target_user_for_reset --------------------------------------

def test_load_target_user_rejects_missing():
    async def go():
        with pytest.raises(HTTPException) as exc:
            await _load_target_user_for_reset("nonexistent-id")
        assert exc.value.status_code == 400
    _run(go)


def test_load_target_user_rejects_deactivated():
    uid = str(uuid.uuid4())

    async def go():
        await server.db.users.insert_one({
            "id": uid,
            "email": f"deact-{uid[:6]}@example.com",
            "full_name": "Deactivated",
            "role": "student",
            "is_active": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "password_hash": "x",
            "_perf_tag": PERF_TAG,
        })
        try:
            with pytest.raises(HTTPException) as exc:
                await _load_target_user_for_reset(uid)
            assert exc.value.status_code == 403
        finally:
            await server.db.users.delete_one({"id": uid})

    _run(go)


# ---------- _apply_password_reset (full persistence path) -------------------

def test_apply_password_reset_persists_and_invalidates_other_tokens():
    uid = str(uuid.uuid4())
    raw1, h1 = _make_reset_token()
    raw2, h2 = _make_reset_token()  # second unused token for same user

    async def go():
        await server.db.users.insert_one({
            "id": uid,
            "email": f"apply-{uid[:6]}@example.com",
            "full_name": "Apply Test",
            "role": "student",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "password_hash": hash_pw("OldPassword@1"),
            "must_change_password": True,
            "_perf_tag": PERF_TAG,
        })
        for h in (h1, h2):
            await server.db.password_reset_tokens.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": uid,
                "email": "apply@example.com",
                "token_hash": h,
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
                "used_at": None,
                "_perf_tag": PERF_TAG,
            })
        try:
            await _apply_password_reset(uid, "NewPassword@1", h1, ip="testclient")
            # Password was rotated.
            doc = await server.db.users.find_one({"id": uid}, {"_id": 0})
            assert verify_pw("NewPassword@1", doc["password_hash"])
            assert doc["must_change_password"] is False
            # The consumed token is now used.
            t1 = await server.db.password_reset_tokens.find_one({"token_hash": h1}, {"_id": 0})
            assert t1["used_at"] is not None
            assert t1.get("used_ip") == "testclient"
            # Defensive invalidation: the OTHER unused token is also marked used.
            t2 = await server.db.password_reset_tokens.find_one({"token_hash": h2}, {"_id": 0})
            assert t2["used_at"] is not None
        finally:
            await server.db.users.delete_one({"id": uid})
            await server.db.password_reset_tokens.delete_many({"user_id": uid})

    _run(go)


# ---------- _send_reset_email (no Resend key configured) --------------------

def test_send_reset_email_returns_false_without_key(monkeypatch):
    """When RESEND_API_KEY is unset, the helper must return False rather
    than raise — the admin-mediated reset link UI keeps the flow
    functional without an email provider."""
    monkeypatch.setattr(server, "RESEND_API_KEY", "")

    async def go():
        sent = await _send_reset_email("anyone@example.com", "rawtoken", "Anyone")
        assert sent is False

    asyncio.run(go())


def test_send_reset_email_returns_false_when_key_set_but_no_public_url(monkeypatch):
    """When key is set but PUBLIC_APP_URL is absent, the helper refuses
    to email a relative URL (would render as a broken link) and returns
    False."""
    monkeypatch.setattr(server, "RESEND_API_KEY", "fake-key")
    monkeypatch.delenv("PUBLIC_APP_URL", raising=False)

    async def go():
        sent = await _send_reset_email("anyone@example.com", "rawtoken", "Anyone")
        assert sent is False

    asyncio.run(go())
