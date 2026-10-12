"""Tests for Sage v3 perf additions: TTS audio caching, circuit breaker,
cost caps, and metrics endpoint."""
import os
import time
import uuid

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"


_AI_NOT_CONFIGURED = "AI not configured"


def _require_ai_provider(r):
    """Skip rather than fail when the live backend has no AI key.

    These tests call the real TTS provider (test_sage_v2's header documents
    the cost and the key requirement). With no EMERGENT_LLM_KEY/OPENAI_API_KEY
    the endpoint answers 500 "AI not configured" — an environment condition,
    not a defect in the code under test. A red run must say "skipped: no AI
    provider" instead of failing, otherwise real breakage hides among
    environment noise.
    """
    if r.status_code == 500 and _AI_NOT_CONFIGURED in r.text:
        pytest.skip("live backend has no AI provider configured "
                    "(EMERGENT_LLM_KEY / OPENAI_API_KEY)")

STUDENT_EMAIL = "student@lcewai.org"
STUDENT_PW = "Learn@LCE2026"
EXEC_EMAIL = os.environ.get("TEST_EXEC_EMAIL", "youpickeddoliver@gmail.com")
EXEC_PW = os.environ.get("TEST_EXEC_PW", "")


def _set_student_tier(tier):
    """Set the shared demo student's tier in the LOCAL test database.

    /api/ai/sage/tts is `publisher_ai` = member (security/feature_control.py:
    the Sage voice is part of the Creator Suite, Member tier). A free student
    is correctly refused with 403 ACCESS_ENFORCED, so these tests run an
    entitled account. Always paired with a restore.
    """
    from pymongo import MongoClient
    url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "phase0_dev")
    c = MongoClient(url, serverSelectionTimeoutMS=5000)
    try:
        if tier:
            c[db_name].users.update_one({"email": STUDENT_EMAIL}, {"$set": {"feature_tier": tier}})
        else:
            c[db_name].users.update_one({"email": STUDENT_EMAIL}, {"$unset": {"feature_tier": ""}})
    finally:
        c.close()


def _login(email, password, attempts=3):
    """Session-cached login via the shared helper (see tests/conftest.py).

    Keeping the original signature so call sites are unchanged; the token
    is cached per account for the whole run, which is what keeps the suite
    inside the login rate limit."""
    try:
        from conftest import login_token
    except ImportError:      # standalone run: python3 tests/<file>.py
        r = requests.post(f"{os.environ['REACT_APP_BACKEND_URL'].rstrip('/')}/api/auth/login",
                          json={"email": email, "password": password}, timeout=20)
        assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
        return r.json()["access_token"]
    return login_token(email, password)

def _auth(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def exec_token():
    try:
        return _login(EXEC_EMAIL, EXEC_PW)
    except AssertionError:
        pytest.skip("exec creds unavailable")


@pytest.fixture(scope="module")
def student_token():
    return _login(STUDENT_EMAIL, STUDENT_PW)


@pytest.fixture(scope="module", autouse=True)
def _entitled_student():
    """The Sage voice endpoints are Member-gated (publisher_ai); promote the
    shared demo student for this module and restore the seeded tier after."""
    _set_student_tier("member")
    yield
    _set_student_tier(None)


# ---------------------------------------------------------------------------
# Caching — same text+voice+speed served from cache on second hit
# ---------------------------------------------------------------------------
class TestSageTTSCache:

    def test_repeat_call_serves_from_cache(self, student_token):
        # Use a unique-but-reusable text for this run so we don't collide
        # with other test data; first call seeds, second call hits.
        text = f"Cached test phrase {uuid.uuid4().hex[:8]}"
        body = {"text": text, "voice": "sage", "speed": 1.0}
        r1 = requests.post(
            f"{API}/ai/sage/tts", headers=_auth(student_token),
            json=body, timeout=60,
        )
        _require_ai_provider(r1)
        assert r1.status_code == 200, r1.text
        assert r1.headers.get("x-cache") == "miss"
        # Second identical call should hit cache.
        r2 = requests.post(
            f"{API}/ai/sage/tts", headers=_auth(student_token),
            json=body, timeout=20,
        )
        _require_ai_provider(r2)
        assert r2.status_code == 200
        assert r2.headers.get("x-cache") == "hit"
        # Same audio length implies identical bytes served.
        assert r1.headers.get("x-audio-len") == r2.headers.get("x-audio-len")

    def test_cache_key_is_voice_specific(self, student_token):
        text = f"Voice swap probe {uuid.uuid4().hex[:6]}"
        r1 = requests.post(
            f"{API}/ai/sage/tts", headers=_auth(student_token),
            json={"text": text, "voice": "sage"}, timeout=60,
        )
        _require_ai_provider(r1)
        r2 = requests.post(
            f"{API}/ai/sage/tts", headers=_auth(student_token),
            json={"text": text, "voice": "echo"}, timeout=60,
        )
        _require_ai_provider(r2)
        _require_ai_provider(r1)
        assert r1.status_code == 200 and r2.status_code == 200
        # Different voice → fresh cache entry → both miss
        assert r1.headers.get("x-cache") == "miss"
        assert r2.headers.get("x-cache") == "miss"


# ---------------------------------------------------------------------------
# Cost caps — session cap (10000 chars) returns 429 with X-Cost-Cap
# ---------------------------------------------------------------------------
class TestSageTTSCostCaps:

    def test_session_cap_returns_429(self, student_token):
        # Force a session cap hit by using a unique session and oversize text.
        # 4000 chars is the per-call limit; we'll force the session counter
        # high by issuing 3 calls of ~3500 chars (10500 > 10000 cap).
        sid = f"cap-{uuid.uuid4().hex[:6]}"
        chunk = "Ase. " * 700  # 3500 chars
        ok_count = 0
        capped = False
        for _ in range(3):
            r = requests.post(
                f"{API}/ai/sage/tts", headers=_auth(student_token),
                json={"text": chunk, "voice": "sage", "session_id": sid}, timeout=60,
            )
            _require_ai_provider(r)
            if r.status_code == 429:
                assert r.headers.get("x-cost-cap") == "true"
                assert r.headers.get("x-cost-cap-reason") in ("session", "daily")
                capped = True
                break
            assert r.status_code == 200, r.text
            ok_count += 1
        assert capped, f"expected session cap to trigger; ok_count={ok_count}"


# ---------------------------------------------------------------------------
# Metrics endpoint — exec only
# ---------------------------------------------------------------------------
class TestSageMetrics:

    def test_metrics_rbac(self, student_token):
        r = requests.get(f"{API}/admin/sage/metrics", headers=_auth(student_token), timeout=10)
        assert r.status_code == 403

    def test_metrics_anon(self):
        r = requests.get(f"{API}/admin/sage/metrics", timeout=10)
        assert r.status_code in (401, 403)

    def test_metrics_shape(self, exec_token):
        r = requests.get(f"{API}/admin/sage/metrics", headers=_auth(exec_token), timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        for key in (
            "p95_latency_ms", "cache_hit_ratio", "error_rate", "sample_count",
            "window_seconds", "breaker", "session_char_cap", "user_daily_char_cap",
        ):
            assert key in body, f"missing key {key}"
        assert body["breaker"] in ("closed", "open", "half-open")
        assert body["session_char_cap"] >= 1
        assert 0.0 <= body["cache_hit_ratio"] <= 1.0
        assert 0.0 <= body["error_rate"] <= 1.0


# ---------------------------------------------------------------------------
# Status endpoint — modules still report present
# ---------------------------------------------------------------------------
class TestSageStatusUnchanged:

    def test_status_modules_all_present(self, exec_token):
        r = requests.get(f"{API}/admin/sage/status", headers=_auth(exec_token), timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["prompt_hash_status"] == "match"
        assert body["fallback_active"] is False
        for m in ("A", "E", "F", "D"):
            assert body["modules"][m] == "present"
