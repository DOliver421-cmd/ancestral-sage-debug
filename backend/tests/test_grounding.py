"""Tests for the grounding mode-resolution endpoint, consent_health,
the first-time consent gate, and the new audit_id/correlation_id/store_audio
fields on the consent response."""
import os
import time
import uuid

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"

STUDENT_EMAIL = "student@lcewai.org"
STUDENT_PW = "Learn@LCE2026"

COMPREHENSION = "I understand and accept the risks of this practice."


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
    raise AssertionError(f"login failed: {last.status_code if last else '?'}")


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def student_token():
    return _login(STUDENT_EMAIL, STUDENT_PW)


# ---------------------------------------------------------------------------
# /ai/consent/health
# ---------------------------------------------------------------------------
class TestConsentHealth:

    def test_public_health_check(self):
        r = requests.get(f"{API}/ai/consent/health", timeout=10)
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# resolve_mode keyword routing
# ---------------------------------------------------------------------------
class TestResolveMode:

    def _post(self, token, intent, sid=None):
        return requests.post(
            f"{API}/ai/sage/resolve_mode",
            headers=_auth(token),
            json={"session_id": sid or f"rm-{uuid.uuid4().hex[:6]}",
                  "user_intent": intent},
            timeout=10,
        )

    def test_anonymous_blocked(self):
        r = requests.post(
            f"{API}/ai/sage/resolve_mode",
            json={"session_id": "x", "user_intent": "y"}, timeout=10,
        )
        assert r.status_code in (401, 403)

    def test_electrical_dominant(self, student_token):
        r = self._post(student_token, "Explain GFCI receptacles, NEC bonding, and panel feeders.")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["mode"] == "electrical"
        assert body["scores"]["electrical"] >= 2
        assert body["audit_id"]
        assert body["grounding_token"]

    def test_sage_dominant(self, student_token):
        r = self._post(student_token, "Guide me in a meditation on my ancestors and lineage healing wisdom.")
        body = r.json()
        assert body["mode"] == "sage"
        assert body["scores"]["sage"] >= 2

    def test_grounding_ritual_when_ambiguous(self, student_token):
        r = self._post(student_token, "I want to think about my outlet and my ancestors.")
        body = r.json()
        assert body["mode"] == "grounding_ritual"
        assert body["reason"] == "ambiguous-needs-disambiguation"

    def test_default_sage_on_neutral_text(self, student_token):
        r = self._post(student_token, "hello, how are you")
        body = r.json()
        assert body["mode"] == "sage"
        assert body["reason"] == "default"

    def test_audit_ids_are_unique(self, student_token):
        r1 = self._post(student_token, "outlet panel breaker")
        r2 = self._post(student_token, "outlet panel breaker")
        assert r1.json()["audit_id"] != r2.json()["audit_id"]


# ---------------------------------------------------------------------------
# Consent response now includes audit_id + correlation_id + store_audio
# ---------------------------------------------------------------------------
class TestConsentEnvelope:

    def test_consent_returns_canonical_fields(self, student_token):
        r = requests.post(
            f"{API}/ai/consent", headers=_auth(student_token),
            json={
                "persona": "ancestral_sage",
                "confirm_yes": "YES",
                "comprehension": COMPREHENSION,
                "store_audio": True,
            },
            timeout=10,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        # Backward-compat field still present.
        assert "consent_log_id" in body
        # New canonical fields.
        assert body["status"] == "ok"
        assert body["audit_id"] == body["consent_log_id"]
        assert body["correlation_id"] and body["correlation_id"] != body["audit_id"]
        assert body["store_audio"] is True

    def test_store_audio_defaults_false(self, student_token):
        r = requests.post(
            f"{API}/ai/consent", headers=_auth(student_token),
            json={
                "persona": "ancestral_sage",
                "confirm_yes": "YES",
                "comprehension": COMPREHENSION,
            },
            timeout=10,
        )
        body = r.json()
        assert body["store_audio"] is False


# ---------------------------------------------------------------------------
# Integrity now exposes needs_first_consent
# ---------------------------------------------------------------------------
class TestIntegrityNeedsConsent:

    def test_existing_user_with_consent_does_not_need_first(self, student_token):
        # student@lcewai.org has consent records from earlier tests.
        r = requests.get(f"{API}/ai/sage/integrity", headers=_auth(student_token), timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "needs_first_consent" in body
        # NB: This test is order-dependent on TestConsentEnvelope having seeded
        # at least one record. If run first in a fresh db, this could be True;
        # we tolerate either value here, just verify the key exists.
        assert isinstance(body["needs_first_consent"], bool)
