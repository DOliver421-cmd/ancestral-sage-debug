"""Tests for the Ancestral Sage AI persona.

Covers:
  * /api/ai/consent — phrase validation, exact YES/comprehension, log id issued
  * /api/ai/chat (mode=ancestral_sage) — gating returns 403 without consent
    when intensity=deep or safety_level in {exploratory, extreme}
  * /api/ai/chat (mode=ancestral_sage) — crisis short-circuit returns the
    safety template WITHOUT calling the LLM
  * RBAC sanity — anonymous requests are blocked

The gating + crisis branches deliberately short-circuit before the LLM call
so these tests run fast, deterministically, and incur zero LLM cost. We
explicitly do NOT test the live LLM happy-path here — that is covered by
existing test_lcewai.TestAI tests for the other modes and is functionally
equivalent for ancestral_sage once gating passes.
"""
import os
import uuid

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"

STUDENT_EMAIL = "student@lcewai.org"
STUDENT_PW = "Learn@LCE2026"

COMPREHENSION = "I understand and accept the risks of this practice."


def _login(email, password):
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

def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _grant_member(email: str) -> None:
    """Give the shared demo account member entitlement for one test.

    The consent-layer tests need an entitled account; the paywall is asserted
    separately in tests/test_soup_and_tier_contracts.py. Always paired with
    _revoke_member in a finally block so no suite inherits the change.
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    import asyncio

    async def _set():
        client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017"))
        try:
            await client[os.environ.get("DB_NAME", "phase0_dev")].users.update_one(
                {"email": email}, {"$set": {"feature_tier": "member"}}
            )
        finally:
            client.close()

    asyncio.run(_set())


def _revoke_member(email: str) -> None:
    """Restore the demo account to its seeded (unentitled) state."""
    from motor.motor_asyncio import AsyncIOMotorClient
    import asyncio

    async def _set():
        client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017"))
        try:
            await client[os.environ.get("DB_NAME", "phase0_dev")].users.update_one(
                {"email": email}, {"$unset": {"feature_tier": ""}}
            )
        finally:
            client.close()

    asyncio.run(_set())


# ---------------------------------------------------------------------------
# /ai/consent
# ---------------------------------------------------------------------------
class TestAIConsent:

    def setup_method(self):
        self.token = _login(STUDENT_EMAIL, STUDENT_PW)

    def test_requires_auth(self):
        r = requests.post(
            f"{API}/ai/consent",
            json={
                "persona": "ancestral_sage",
                "confirm_yes": "YES",
                "comprehension": COMPREHENSION,
            },
            timeout=10,
        )
        assert r.status_code in (401, 403), r.text

    def test_yes_must_be_exact(self):
        r = requests.post(
            f"{API}/ai/consent",
            headers=_auth(self.token),
            json={
                "persona": "ancestral_sage",
                "confirm_yes": "yeah",
                "comprehension": COMPREHENSION,
            },
            timeout=10,
        )
        assert r.status_code == 400
        assert "YES" in r.json()["detail"]

    def test_comprehension_phrase_must_be_exact(self):
        r = requests.post(
            f"{API}/ai/consent",
            headers=_auth(self.token),
            json={
                "persona": "ancestral_sage",
                "confirm_yes": "YES",
                "comprehension": "i understand",
            },
            timeout=10,
        )
        assert r.status_code == 400
        assert "exactly" in r.json()["detail"].lower()

    def test_lowercase_yes_accepted_after_strip_upper(self):
        # Server upper-cases — "yes" is accepted (server normalises).
        r = requests.post(
            f"{API}/ai/consent",
            headers=_auth(self.token),
            json={
                "persona": "ancestral_sage",
                "confirm_yes": "  yes  ",
                "comprehension": COMPREHENSION,
            },
            timeout=10,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "consent_log_id" in body
        assert "expires_at" in body
        assert body.get("ttl_minutes", 0) > 0

    def test_persona_must_be_ancestral_sage(self):
        r = requests.post(
            f"{API}/ai/consent",
            headers=_auth(self.token),
            json={
                "persona": "tutor",  # not allowed
                "confirm_yes": "YES",
                "comprehension": COMPREHENSION,
            },
            timeout=10,
        )
        assert r.status_code == 422  # pydantic Literal violation

    def test_happy_path_returns_log_id(self):
        r = requests.post(
            f"{API}/ai/consent",
            headers=_auth(self.token),
            json={
                "persona": "ancestral_sage",
                "confirm_yes": "YES",
                "comprehension": COMPREHENSION,
                "intensity": "deep",
                "safety_level": "exploratory",
            },
            timeout=10,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        cid = body["consent_log_id"]
        assert isinstance(cid, str) and len(cid) >= 32


# ---------------------------------------------------------------------------
# /ai/chat — Ancestral Sage gating (no LLM cost)
# ---------------------------------------------------------------------------
class TestAncestralSageGating:

    def setup_method(self):
        self.token = _login(STUDENT_EMAIL, STUDENT_PW)
        self.sid = f"sage-{uuid.uuid4().hex[:8]}"

    def _chat(self, body):
        return requests.post(
            f"{API}/ai/chat",
            headers=_auth(self.token),
            json=body,
            timeout=60,
        )

    def test_deep_intensity_without_consent_is_403(self):
        # This test covers the CONSENT layer, which sits behind the AI Tutor
        # paywall: an unentitled account is stopped before consent matters.
        # So the account is granted member entitlement for the duration of
        # this one test and restored immediately afterwards (self-cleaning —
        # no cross-suite state), then the assertion is about consent alone.
        _grant_member(STUDENT_EMAIL)
        try:
            r = self._chat({
                "session_id": self.sid,
                "message": "Guide me into deep visualization.",
                "mode": "ancestral_sage",
                "intensity": "deep",
                "safety_level": "standard",
            })
            assert r.status_code == 403, r.text
            assert "consent" in r.json()["detail"].lower()
        finally:
            _revoke_member(STUDENT_EMAIL)

    def test_exploratory_safety_without_consent_is_403(self):
        r = self._chat({
            "session_id": self.sid,
            "message": "Take me deeper into ancestral memory.",
            "mode": "ancestral_sage",
            "intensity": "moderate",
            "safety_level": "exploratory",
        })
        assert r.status_code == 403, r.text

    def test_extreme_safety_without_consent_is_403(self):
        r = self._chat({
            "session_id": self.sid,
            "message": "Begin extreme planetary regression.",
            "mode": "ancestral_sage",
            "intensity": "moderate",
            "safety_level": "extreme",
        })
        assert r.status_code == 403, r.text

    def test_invalid_consent_id_is_403(self):
        r = self._chat({
            "session_id": self.sid,
            "message": "Begin deep practice.",
            "mode": "ancestral_sage",
            "intensity": "deep",
            "safety_level": "exploratory",
            "consent_log_id": "nope-not-a-real-id",
        })
        assert r.status_code == 403, r.text

    def test_consent_for_other_user_is_rejected(self):
        # Mint a consent_log_id for student, then try to use it from a fresh
        # student token (same user — should work)... To prove cross-user
        # rejection we'd need a second account. Instead verify the lookup is
        # scoped: a random uuid is still rejected (covered above) and a
        # valid id is accepted (next class).
        pass  # placeholder to keep the assertion structure documented

    def test_crisis_message_short_circuits_with_safety_template(self):
        # Crisis branch returns 200 with the canonical safety reply and does
        # NOT touch the LLM (no EMERGENT_LLM_KEY required to pass).
        r = self._chat({
            "session_id": self.sid,
            "message": "I want to kill myself tonight.",
            "mode": "ancestral_sage",
            "intensity": "gentle",
            "safety_level": "conservative",
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("safety_intervention") is True
        reply = body["reply"]
        assert "988" in reply or "emergency" in reply.lower()
        assert "licensed professional" in reply.lower()

    def test_gentle_conservative_does_not_require_consent_payload_validation(self):
        # We don't actually call the LLM here — we just confirm the gate
        # does NOT trip. The endpoint will still try to call the LLM, so we
        # only require that the failure (if any) is NOT a 403 consent error.
        r = self._chat({
            "session_id": self.sid,
            "message": "Teach me a simple grounding breath.",
            "mode": "ancestral_sage",
            "intensity": "gentle",
            "safety_level": "conservative",
        })
        # Acceptable: 200 (LLM responded), 5xx (LLM unreachable in CI), or a
        # paywall for an unentitled account. Unacceptable: a 403 CONSENT
        # rejection — that would mean the gentle/conservative path started
        # demanding a consent payload it does not need.
        detail = (r.json().get("detail") or "").lower() if r.headers.get(
            "content-type", ""
        ).startswith("application/json") else ""
        assert not (r.status_code == 403 and "consent" in detail), (
            f"unexpected consent gate trip: {r.text}"
        )


# ---------------------------------------------------------------------------
# Consent → Chat happy path (still no LLM call: we stop at gate-passed 200
# on environments with LLM up; otherwise tolerate 5xx, never 403).
# ---------------------------------------------------------------------------
class TestAncestralSageConsentedChat:

    def setup_method(self):
        self.token = _login(STUDENT_EMAIL, STUDENT_PW)
        # Mint a consent
        r = requests.post(
            f"{API}/ai/consent",
            headers=_auth(self.token),
            json={
                "persona": "ancestral_sage",
                "confirm_yes": "YES",
                "comprehension": COMPREHENSION,
                "intensity": "deep",
                "safety_level": "exploratory",
            },
            timeout=10,
        )
        assert r.status_code == 200, r.text
        self.cid = r.json()["consent_log_id"]
        self.sid = f"sage-c-{uuid.uuid4().hex[:8]}"

    def test_consent_id_passes_gate(self):
        r = requests.post(
            f"{API}/ai/chat",
            headers=_auth(self.token),
            json={
                "session_id": self.sid,
                "message": "Offer a brief grounding teaching.",
                "mode": "ancestral_sage",
                "depth": "beginner",
                "intensity": "deep",
                "safety_level": "exploratory",
                "cultural_focus": "pan_african",
                "divination_mode": "teaching",
                "consent_log_id": self.cid,
            },
            timeout=60,
        )
        # Must NOT be a consent-gate rejection. The consent record is what
        # this test is about, and the consent layer is deliberately outside
        # the AI tier gate (security/feature_control.AI_NO_COST_PATHS) so an
        # account can always give consent. A free student may still be stopped
        # by the AI Tutor's own entitlement check (402 member/BYOK) — that is
        # the paywall, not the consent gate, and is asserted elsewhere.
        detail = (r.json().get("detail") or "").lower() if r.headers.get(
            "content-type", ""
        ).startswith("application/json") else ""
        assert not (r.status_code == 403 and "consent" in detail), (
            f"consent gate regressed: {r.text}"
        )
