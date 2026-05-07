"""Tests for Sage v3 perf additions: TTS audio caching, circuit breaker,
cost caps, and metrics endpoint."""
import os
import time
import uuid

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"

STUDENT_EMAIL = "student@lcewai.org"
STUDENT_PW = "Learn@LCE2026"
EXEC_EMAIL = "delon.oliver@lightningcityelectric.com"
EXEC_PW = "Executive@LCE2026"


def _login(email, password, attempts=3):
    last = None
    for i in range(attempts):
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
        if r.status_code == 200:
            return r.json()["access_token"]
        last = r
        if r.status_code == 429:
            time.sleep(2 + i * 2)
            continue
        break
    raise AssertionError(f"login failed: {last.status_code if last else '?'} {last.text if last else ''}")


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
        assert r1.status_code == 200, r1.text
        assert r1.headers.get("x-cache") == "miss"
        # Second identical call should hit cache.
        r2 = requests.post(
            f"{API}/ai/sage/tts", headers=_auth(student_token),
            json=body, timeout=20,
        )
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
        r2 = requests.post(
            f"{API}/ai/sage/tts", headers=_auth(student_token),
            json={"text": text, "voice": "echo"}, timeout=60,
        )
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
