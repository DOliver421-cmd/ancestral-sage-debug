"""Tests for the Exec-Admin Sage Sessions audit + safety-cap governance.

Covers:
  * /api/admin/sage/cap (GET) — exec-only, returns global + overrides
  * /api/admin/sage/cap/global (PUT) — set/clear, RBAC
  * /api/admin/sage/cap/user/{uid} (PUT) — set/clear, 404 on bad uid
  * /api/admin/sage/audit (GET) — exec-only, kind filters
  * /api/ai/chat (mode=ancestral_sage) — cap enforced even with valid consent

All tests reset the cap to its starting state in teardown so the suite
remains order-independent.
"""
import os
import uuid

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"

EXEC_EMAIL = "delon.oliver@lightningcityelectric.com"
EXEC_PW = "Executive@LCE2026"
ADMIN_EMAIL = "admin@lcewai.org"
ADMIN_PW = "Admin@LCE2026"
STUDENT_EMAIL = "student@lcewai.org"
STUDENT_PW = "Learn@LCE2026"

COMPREHENSION = "I understand and accept the risks of this practice."


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


def _student_id(exec_token):
    r = requests.get(
        f"{API}/admin/users", headers=_auth(exec_token),
        params={"q": STUDENT_EMAIL}, timeout=20,
    )
    assert r.status_code == 200, r.text
    rows = r.json()
    matches = [u for u in rows if u.get("email") == STUDENT_EMAIL]
    assert matches, "student user not found"
    return matches[0]["id"]


@pytest.fixture(scope="module")
def exec_token():
    """Exec admin login. Skip the suite gracefully if the bootstrapped exec
    creds aren't set up in this environment."""
    try:
        return _login(EXEC_EMAIL, EXEC_PW)
    except AssertionError as e:
        pytest.skip(f"exec admin login unavailable: {e}")


@pytest.fixture(autouse=True)
def _reset_caps_after(exec_token):
    """Reset global + per-user caps after every test for isolation."""
    yield
    # Clear global cap
    requests.put(
        f"{API}/admin/sage/cap/global",
        headers=_auth(exec_token), json={"level": None}, timeout=10,
    )
    # Clear all per-user overrides
    r = requests.get(f"{API}/admin/sage/cap", headers=_auth(exec_token), timeout=10)
    if r.status_code == 200:
        for o in r.json().get("overrides", []):
            requests.put(
                f"{API}/admin/sage/cap/user/{o['user_id']}",
                headers=_auth(exec_token), json={"level": None}, timeout=10,
            )


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------
class TestSageCapRBAC:

    def test_anon_blocked(self):
        r = requests.get(f"{API}/admin/sage/cap", timeout=10)
        assert r.status_code in (401, 403)

    def test_student_blocked(self):
        t = _login(STUDENT_EMAIL, STUDENT_PW)
        r = requests.get(f"{API}/admin/sage/cap", headers=_auth(t), timeout=10)
        assert r.status_code == 403

    def test_admin_blocked_exec_only(self):
        t = _login(ADMIN_EMAIL, ADMIN_PW)
        r = requests.get(f"{API}/admin/sage/cap", headers=_auth(t), timeout=10)
        # require_role("executive_admin") — admin (rank 3) does NOT pass.
        assert r.status_code == 403

    def test_audit_admin_blocked_exec_only(self):
        t = _login(ADMIN_EMAIL, ADMIN_PW)
        r = requests.get(f"{API}/admin/sage/audit", headers=_auth(t), timeout=10)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Cap management
# ---------------------------------------------------------------------------
class TestSageCapManagement:

    def test_get_cap_default_no_cap(self, exec_token):
        r = requests.get(f"{API}/admin/sage/cap", headers=_auth(exec_token), timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "global_level" in body
        assert "overrides" in body
        assert body["available_levels"] == ["conservative", "standard", "exploratory", "extreme"]

    def test_set_global_cap_persists(self, exec_token):
        r = requests.put(
            f"{API}/admin/sage/cap/global",
            headers=_auth(exec_token), json={"level": "standard"}, timeout=10,
        )
        assert r.status_code == 200, r.text
        assert r.json()["global_level"] == "standard"
        # Read back
        r2 = requests.get(f"{API}/admin/sage/cap", headers=_auth(exec_token), timeout=10)
        assert r2.json()["global_level"] == "standard"

    def test_clear_global_cap(self, exec_token):
        requests.put(
            f"{API}/admin/sage/cap/global",
            headers=_auth(exec_token), json={"level": "conservative"}, timeout=10,
        )
        r = requests.put(
            f"{API}/admin/sage/cap/global",
            headers=_auth(exec_token), json={"level": None}, timeout=10,
        )
        assert r.status_code == 200
        r2 = requests.get(f"{API}/admin/sage/cap", headers=_auth(exec_token), timeout=10)
        assert r2.json()["global_level"] in (None,)

    def test_invalid_level_rejected(self, exec_token):
        r = requests.put(
            f"{API}/admin/sage/cap/global",
            headers=_auth(exec_token), json={"level": "godmode"}, timeout=10,
        )
        assert r.status_code == 422

    def test_user_override_404_on_bad_uid(self, exec_token):
        r = requests.put(
            f"{API}/admin/sage/cap/user/nope-{uuid.uuid4()}",
            headers=_auth(exec_token), json={"level": "conservative"}, timeout=10,
        )
        assert r.status_code == 404

    def test_user_override_persists_with_email(self, exec_token):
        sid = _student_id(exec_token)
        r = requests.put(
            f"{API}/admin/sage/cap/user/{sid}",
            headers=_auth(exec_token), json={"level": "conservative"}, timeout=10,
        )
        assert r.status_code == 200
        body = requests.get(f"{API}/admin/sage/cap", headers=_auth(exec_token), timeout=10).json()
        match = [o for o in body["overrides"] if o["user_id"] == sid]
        assert len(match) == 1
        assert match[0]["level"] == "conservative"
        assert match[0]["email"] == STUDENT_EMAIL


# ---------------------------------------------------------------------------
# Cap enforcement in /ai/chat — runs BEFORE consent gate.
# ---------------------------------------------------------------------------
class TestSageCapEnforcement:

    def test_global_cap_blocks_higher_level_without_consent(self, exec_token):
        requests.put(
            f"{API}/admin/sage/cap/global",
            headers=_auth(exec_token), json={"level": "standard"}, timeout=10,
        )
        t = _login(STUDENT_EMAIL, STUDENT_PW)
        r = requests.post(
            f"{API}/ai/chat", headers=_auth(t),
            json={
                "session_id": f"cap-{uuid.uuid4().hex[:8]}",
                "message": "Take me deeper.",
                "mode": "ancestral_sage",
                "intensity": "moderate",
                "safety_level": "exploratory",
            }, timeout=15,
        )
        assert r.status_code == 403, r.text
        assert "capped" in r.json()["detail"].lower()

    def test_global_cap_blocks_even_with_valid_consent(self, exec_token):
        # Cap at conservative
        requests.put(
            f"{API}/admin/sage/cap/global",
            headers=_auth(exec_token), json={"level": "conservative"}, timeout=10,
        )
        t = _login(STUDENT_EMAIL, STUDENT_PW)
        # Mint a consent regardless
        cr = requests.post(
            f"{API}/ai/consent", headers=_auth(t),
            json={
                "persona": "ancestral_sage",
                "confirm_yes": "YES",
                "comprehension": COMPREHENSION,
                "intensity": "deep",
                "safety_level": "extreme",
            }, timeout=10,
        )
        assert cr.status_code == 200
        cid = cr.json()["consent_log_id"]

        r = requests.post(
            f"{API}/ai/chat", headers=_auth(t),
            json={
                "session_id": f"cap-{uuid.uuid4().hex[:8]}",
                "message": "Begin extreme practice.",
                "mode": "ancestral_sage",
                "intensity": "deep",
                "safety_level": "extreme",
                "consent_log_id": cid,
            }, timeout=15,
        )
        assert r.status_code == 403, r.text
        assert "cap" in r.json()["detail"].lower()

    def test_per_user_override_more_restrictive_than_global(self, exec_token):
        # Global = exploratory; user-cap = conservative; user request = standard → blocked
        requests.put(
            f"{API}/admin/sage/cap/global",
            headers=_auth(exec_token), json={"level": "exploratory"}, timeout=10,
        )
        sid = _student_id(exec_token)
        requests.put(
            f"{API}/admin/sage/cap/user/{sid}",
            headers=_auth(exec_token), json={"level": "conservative"}, timeout=10,
        )
        t = _login(STUDENT_EMAIL, STUDENT_PW)
        r = requests.post(
            f"{API}/ai/chat", headers=_auth(t),
            json={
                "session_id": f"cap-{uuid.uuid4().hex[:8]}",
                "message": "A simple grounding teaching.",
                "mode": "ancestral_sage",
                "intensity": "gentle",
                "safety_level": "standard",
            }, timeout=15,
        )
        assert r.status_code == 403, r.text

    def test_clearing_user_override_lets_global_apply(self, exec_token):
        sid = _student_id(exec_token)
        # Set then clear the user override; global stays at standard
        requests.put(
            f"{API}/admin/sage/cap/global",
            headers=_auth(exec_token), json={"level": "standard"}, timeout=10,
        )
        requests.put(
            f"{API}/admin/sage/cap/user/{sid}",
            headers=_auth(exec_token), json={"level": "conservative"}, timeout=10,
        )
        # clear user override
        requests.put(
            f"{API}/admin/sage/cap/user/{sid}",
            headers=_auth(exec_token), json={"level": None}, timeout=10,
        )
        t = _login(STUDENT_EMAIL, STUDENT_PW)
        # Standard is allowed by global=standard
        r = requests.post(
            f"{API}/ai/chat", headers=_auth(t),
            json={
                "session_id": f"cap-{uuid.uuid4().hex[:8]}",
                "message": "A grounding teaching.",
                "mode": "ancestral_sage",
                "intensity": "gentle",
                "safety_level": "standard",
            }, timeout=60,
        )
        # Global cap=standard with requested=standard → cap NOT exceeded
        assert r.status_code != 403, f"unexpected cap trip: {r.text}"


# ---------------------------------------------------------------------------
# Audit feed
# ---------------------------------------------------------------------------
class TestSageAuditFeed:

    def test_audit_returns_consent_and_chat_rows(self, exec_token):
        # Seed a consent so the feed has something
        t = _login(STUDENT_EMAIL, STUDENT_PW)
        cr = requests.post(
            f"{API}/ai/consent", headers=_auth(t),
            json={
                "persona": "ancestral_sage",
                "confirm_yes": "YES",
                "comprehension": COMPREHENSION,
                "intensity": "moderate",
                "safety_level": "standard",
            }, timeout=10,
        )
        assert cr.status_code == 200
        # Fetch audit
        r = requests.get(
            f"{API}/admin/sage/audit", headers=_auth(exec_token),
            params={"kind": "consent", "limit": 20}, timeout=10,
        )
        assert r.status_code == 200, r.text
        rows = r.json()["rows"]
        assert any(row["kind"] == "consent" for row in rows)

    def test_audit_filter_by_user(self, exec_token):
        sid = _student_id(exec_token)
        r = requests.get(
            f"{API}/admin/sage/audit", headers=_auth(exec_token),
            params={"user_id": sid, "limit": 50}, timeout=10,
        )
        assert r.status_code == 200
        rows = r.json()["rows"]
        # Every returned row must belong to this user
        assert all(row.get("user_id") == sid for row in rows), rows

    def test_audit_kind_crisis_filters(self, exec_token):
        t = _login(STUDENT_EMAIL, STUDENT_PW)
        # Trigger the crisis short-circuit
        cr = requests.post(
            f"{API}/ai/chat", headers=_auth(t),
            json={
                "session_id": f"crisis-{uuid.uuid4().hex[:8]}",
                "message": "I want to kill myself tonight.",
                "mode": "ancestral_sage",
                "intensity": "gentle",
                "safety_level": "conservative",
            }, timeout=15,
        )
        assert cr.status_code == 200
        # Fetch crisis-only audit
        r = requests.get(
            f"{API}/admin/sage/audit", headers=_auth(exec_token),
            params={"kind": "crisis", "limit": 50}, timeout=10,
        )
        assert r.status_code == 200
        rows = r.json()["rows"]
        assert rows, "expected at least one crisis row"
        assert all(row["kind"] == "crisis" for row in rows)
        assert all(row.get("refusal_reason") == "crisis_safety_template" for row in rows)
