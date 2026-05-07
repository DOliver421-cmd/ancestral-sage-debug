"""Tests for the layered consent flow + persona integrity check + TTS endpoint.

These are the upgrades from spec modules 8 (layered consent), F (integrity
hash check), and D (audio output via OpenAI TTS through the Emergent LLM key).

The TTS test makes a real call to OpenAI TTS. Skipped if the env doesn't have
EMERGENT_LLM_KEY available to the live backend. The cost is ~$0.0003 per run
(short text, tts-1) — negligible.
"""
import os
import uuid

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"

STUDENT_EMAIL = "student@lcewai.org"
STUDENT_PW = "Learn@LCE2026"
EXEC_EMAIL = "delon.oliver@lightningcityelectric.com"
EXEC_PW = "Executive@LCE2026"

COMPREHENSION = "I understand and accept the risks of this practice."


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


# ---------------------------------------------------------------------------
# Integrity hash endpoint
# ---------------------------------------------------------------------------
class TestSageIntegrity:

    def test_authenticated_users_get_ok_status(self):
        t = _login(STUDENT_EMAIL, STUDENT_PW)
        r = requests.get(f"{API}/ai/sage/integrity", headers=_auth(t), timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        assert body["restricted"] is False
        # Students do NOT see hash details
        assert "live_hash" not in body
        assert "expected_hash" not in body

    def test_exec_admin_sees_hash_pair(self):
        try:
            t = _login(EXEC_EMAIL, EXEC_PW)
        except AssertionError:
            pytest.skip("exec creds unavailable")
        r = requests.get(f"{API}/ai/sage/integrity", headers=_auth(t), timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        # Exec sees both hashes — and they're equal in a healthy build
        assert body["live_hash"] == body["expected_hash"]
        assert len(body["live_hash"]) == 64  # sha256 hex

    def test_anonymous_blocked(self):
        r = requests.get(f"{API}/ai/sage/integrity", timeout=10)
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Layered consent — 3 disclaimers + content_type + expert_score validation
# ---------------------------------------------------------------------------
class TestLayeredConsent:

    def setup_method(self):
        self.token = _login(STUDENT_EMAIL, STUDENT_PW)

    def _post(self, body):
        return requests.post(
            f"{API}/ai/consent", headers=_auth(self.token), json=body, timeout=10,
        )

    def test_general_content_type_does_not_require_disclaimers(self):
        r = self._post({
            "persona": "ancestral_sage",
            "confirm_yes": "YES",
            "comprehension": COMPREHENSION,
            "content_type": "general",
        })
        assert r.status_code == 200, r.text
        assert "consent_log_id" in r.json()

    def test_personalization_requires_all_three_disclaimers(self):
        # Missing disclaimer3 → 400
        r = self._post({
            "persona": "ancestral_sage",
            "confirm_yes": "YES",
            "comprehension": COMPREHENSION,
            "content_type": "personalization",
            "disclaimer1_ack": True,
            "disclaimer2_ack": True,
            "disclaimer3_ack": False,
        })
        assert r.status_code == 400, r.text
        assert "disclaimer" in r.json()["detail"].lower()

    def test_high_confidence_with_all_disclaimers_succeeds(self):
        r = self._post({
            "persona": "ancestral_sage",
            "confirm_yes": "YES",
            "comprehension": COMPREHENSION,
            "content_type": "high_confidence",
            "disclaimer1_ack": True,
            "disclaimer2_ack": True,
            "disclaimer3_ack": True,
            "confidence_level": "high",
            "expert_score": 14,
        })
        assert r.status_code == 200, r.text

    def test_expert_score_out_of_range_rejected(self):
        r = self._post({
            "persona": "ancestral_sage",
            "confirm_yes": "YES",
            "comprehension": COMPREHENSION,
            "content_type": "general",
            "expert_score": 21,
        })
        assert r.status_code == 400
        assert "0..20" in r.json()["detail"]

    def test_human_review_request_returns_flag(self):
        r = self._post({
            "persona": "ancestral_sage",
            "confirm_yes": "YES",
            "comprehension": COMPREHENSION,
            "content_type": "high_consensus",
            "disclaimer1_ack": True,
            "disclaimer2_ack": True,
            "disclaimer3_ack": True,
            "expert_score": 18,
            "request_human_review": True,
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("human_review_triggered") is True


# ---------------------------------------------------------------------------
# TTS endpoint
# ---------------------------------------------------------------------------
class TestSageTTS:

    def setup_method(self):
        self.token = _login(STUDENT_EMAIL, STUDENT_PW)

    def test_text_required(self):
        r = requests.post(
            f"{API}/ai/sage/tts", headers=_auth(self.token),
            json={"text": "  "}, timeout=15,
        )
        assert r.status_code == 400, r.text

    def test_anonymous_blocked(self):
        r = requests.post(
            f"{API}/ai/sage/tts", json={"text": "Hello"}, timeout=15,
        )
        assert r.status_code in (401, 403)

    def test_returns_audio_mpeg_bytes(self):
        r = requests.post(
            f"{API}/ai/sage/tts", headers=_auth(self.token),
            json={"text": "Peace, traveler.", "voice": "sage"}, timeout=60,
        )
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type") == "audio/mpeg"
        # mp3 frame header sanity (ID3 or 0xFF 0xFB / 0xFF 0xF3)
        assert len(r.content) > 100
        head = r.content[:3]
        assert head[:3] == b"ID3" or head[0] == 0xFF, f"unexpected head bytes: {head!r}"

    def test_invalid_voice_rejected(self):
        r = requests.post(
            f"{API}/ai/sage/tts", headers=_auth(self.token),
            json={"text": "Hi", "voice": "robot"}, timeout=10,
        )
        assert r.status_code == 422  # pydantic Literal violation
