"""tests/test_regressions_2026_10_12.py — regressions found and fixed 2026-10-12.

Each test here failed BEFORE its fix. They exist so the failure cannot come
back silently:

1. Payment/provider keys could not be saved at all:
   `if not db:` on a pymongo/motor Database raises NotImplementedError
   ("Database objects do not implement truth value testing"), so
   reload_payment_keys() 500'd after the key was stored — the console showed
   an error and the owner believed nothing had been saved. Same latent bug in
   ai/persona_tts.py (persona_speak) on the TTS path.

2. Completing the OSHA 10 compliance quiz never awarded the credential the
   quiz documents ("Passed Safety & LOTO module with 70%+"). The credential's
   trigger is module_completed -> safety-loto, but nothing linked the
   compliance track to that module, so the trigger was unreachable.
"""

import ast
import asyncio
import os
import sys

import pytest
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_BASE = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")
API = f"{_BASE}/api"
ADMIN = ("admin@lcewai.org", "Admin@LCE2026")
STUDENT = ("student@lcewai.org", "Learn@LCE2026")


_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _hdr(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _login(email, password, attempts=8):
    try:
        from conftest import login_token
    except ImportError:
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": password},
                          timeout=20)
        assert r.status_code == 200, r.text
        return r.json()["access_token"]
    return login_token(email, password, attempts)


def _mongo():
    from pymongo import MongoClient
    url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "phase0_dev")
    return MongoClient(url, serverSelectionTimeoutMS=5000), db_name


def _promote(email, role=None, tier=None):
    client, db_name = _mongo()
    try:
        upd = {}
        if role:
            upd["role"] = role
        if tier:
            upd["feature_tier"] = tier
        client[db_name].users.update_one({"email": email}, {"$set": upd})
    finally:
        client.close()


def _restore_admin_role():
    """Put the demo admin back on its seeded role.

    These tests need an executive account to exercise the save path, but the
    account is shared: leaving it promoted would change what every later suite
    observes (test_sage_caps asserts an `admin` account is refused the
    exec-only audit route and would fail if this file ran first).
    """
    client, db_name = _mongo()
    try:
        client[db_name].users.update_one(
            {"email": ADMIN[0]}, {"$set": {"role": "admin", "feature_tier": "free"}})
    finally:
        client.close()


def _restore_student_tier():
    """Back to the seeded (unentitled) state — later suites assert the
    paywall fires for a free student."""
    client, db_name = _mongo()
    try:
        client[db_name].users.update_one({"email": STUDENT[0]}, {"$unset": {"feature_tier": ""}})
    finally:
        client.close()


def _clear_provider_keys():
    client, db_name = _mongo()
    try:
        client[db_name].api_keys.delete_many({"provider_id": {"$exists": True}})
    finally:
        client.close()


# ── 1. The Database truth-value bug ───────────────────────────────────────────
def test_reload_payment_keys_accepts_a_real_database():
    """The exact failure: `if not db:` on a Motor Database raises."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from routers.payments import reload_payment_keys

    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    try:
        db = client[os.environ.get("DB_NAME", "phase0_dev")]
        # A truth-value test on this object is what used to explode.
        with pytest.raises(NotImplementedError):
            bool(db)
        count = asyncio.run(reload_payment_keys(db))
        assert isinstance(count, int)
    finally:
        client.close()


def test_no_bare_db_truthiness_in_the_touched_modules():
    """Static guard: the pattern must not come back in the files that had it."""
    for path in ("routers/payments.py", "ai/persona_tts.py", "routers/provider_gateway.py"):
        src = open(os.path.join(_BACKEND, path), encoding="utf-8").read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue
            test = node.test
            # match `if not db:` / `if db:` / `if db and ...`
            sources = [test]
            if isinstance(test, ast.BoolOp):
                sources = list(test.values)
            for part in sources:
                if isinstance(part, ast.UnaryOp) and isinstance(part.op, ast.Not):
                    part = part.operand
                if isinstance(part, ast.Name) and part.id == "db":
                    pytest.fail(f"{path}:{part.lineno} still truth-tests `db`")


# ── 2. Payment keys actually save and persist ──────────────────────────────────
def test_payment_key_save_persists_and_reports_configured():
    """The owner-visible symptom: 'payment keys won't save'."""
    _promote(ADMIN[0], role="executive_admin")
    _clear_provider_keys()
    token = _login(*ADMIN)
    try:
        r = requests.post(
            f"{API}/providers/quick-setup",
            headers=_hdr(token),
            json={
                "provider_type": "lemon_squeezy",
                "api_key": "regression-ls-key-4242",
                "secondary_key": "123456",
                "third_key": "whsec_regression",
            },
            timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["configured"] is True
        assert body["key_masked"] == "••••4242"

        # And the console's own status endpoint agrees.
        st = requests.get(f"{API}/providers/quick-setup/status", headers=_hdr(token), timeout=20)
        assert st.status_code == 200, st.text
        row = st.json()["lemon_squeezy"]
        assert row["configured"] is True and row["source"] == "gateway"

        # And it is really in the vault, encrypted — never plaintext.
        client, db_name = _mongo()
        try:
            prov = client[db_name].api_providers.find_one({"provider_type": "lemon_squeezy"})
            assert prov, "provider row missing"
            key = client[db_name].api_keys.find_one({"provider_id": prov["id"]})
            assert key and key.get("encrypted_key")
            assert "regression-ls-key-4242" not in key["encrypted_key"]
        finally:
            client.close()
    finally:
        _clear_provider_keys()
        _restore_admin_role()


def test_payment_key_save_requires_executive():
    """The gate itself is correct: below executive_admin the key is refused
    BEFORE anything is stored (a 403 here is the contract, not a bug)."""
    token = _login(*STUDENT)
    r = requests.post(
        f"{API}/providers/quick-setup", headers=_hdr(token),
        json={"provider_type": "gumroad", "api_key": "should-never-store"}, timeout=20,
    )
    assert r.status_code == 403, r.text
    # No key may exist for that provider — the refusal happens before any
    # vault write, so the row (and any key) is either absent or key-less.
    client, db_name = _mongo()
    try:
        prov = client[db_name].api_providers.find_one({"provider_type": "gumroad"})
        if prov:
            assert not client[db_name].api_keys.find_one({"provider_id": prov["id"]}), (
                "a refused save wrote a key anyway"
            )
    finally:
        client.close()


# ── 3. The OSHA credential auto-award linkage ──────────────────────────────────
def test_osha_quiz_completion_awards_the_documented_credential():
    """The credential's evidence says 'Passed Safety & LOTO module with 70%+'
    — completing the compliance quiz is that module, so the award must fire."""
    _promote(STUDENT[0], tier="plus")
    token = _login(*STUDENT)
    try:
        det = requests.get(f"{API}/compliance/osha-10-electrical", headers=_hdr(token), timeout=20)
        assert det.status_code == 200, det.text
        answers = [q["answer"] for q in det.json()["quiz"]]
        r = requests.post(
            f"{API}/compliance/osha-10-electrical/quiz",
            headers=_hdr(token), json={"answers": answers}, timeout=30,
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "completed"

        creds = requests.get(f"{API}/credentials/me", headers=_hdr(token), timeout=20)
        assert creds.status_code == 200, creds.text
        earned = {e["credential_key"] for e in creds.json().get("earned", [])}
        assert "osha-10-awareness" in earned, f"earned={earned}"

        # The declared link must also complete the module it names.
        prog = requests.get(f"{API}/progress/me", headers=_hdr(token), timeout=20)
        assert prog.status_code == 200, prog.text
        done = {p["module_slug"] for p in prog.json() if p.get("status") == "completed"}
        assert "safety-loto" in done, f"completed modules={done}"
    finally:
        _restore_student_tier()
