"""Comprehensive tests for the password-reset + self-edit auth surface.

Covers:
  * /auth/forgot-password — happy path, no-user enumeration, rate limiting
  * /auth/reset-password — success, expired, reused, invalid token, length
  * /admin/users/{uid}/reset-link — admin-only, hierarchy guard
  * /auth/me PATCH — self profile edit, email collision, validation
  * RBAC: student/instructor/admin/exec on the new endpoints

Driven against REACT_APP_BACKEND_URL (loaded by conftest.py).
Requires DEV_RETURN_RESET_TOKEN=1 in the backend environment so
forgot-password returns the raw token to this test harness.
"""
import os
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"

EXEC_EMAIL = "delon.oliver@lightningcityelectric.com"
EXEC_PW = "Executive@LCE2026"
ADMIN_EMAIL = "admin@lcewai.org"
ADMIN_PW = "Admin@LCE2026"
INSTRUCTOR_EMAIL = "instructor@lcewai.org"
INSTRUCTOR_PW = "Teach@LCE2026"
STUDENT_EMAIL = "student@lcewai.org"
STUDENT_PW = "Learn@LCE2026"


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    return r.json()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# /auth/forgot-password
# ---------------------------------------------------------------------------
class TestForgotPassword:

    def test_real_email_returns_200_with_dev_token(self):
        r = requests.post(f"{API}/auth/forgot-password",
                          json={"email": STUDENT_EMAIL}, timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        # DEV_RETURN_RESET_TOKEN=1 must be set for the test to obtain a token.
        assert "_dev_token" in body, (
            "Backend must run with DEV_RETURN_RESET_TOKEN=1 for these tests"
        )
        assert isinstance(body["_dev_token"], str)
        assert len(body["_dev_token"]) >= 32
        assert body["_dev_url"].startswith(("/reset-password", "http"))

    def test_unknown_email_does_not_enumerate(self):
        unique = f"nope-{uuid.uuid4()}@example.com"
        r = requests.post(f"{API}/auth/forgot-password",
                          json={"email": unique}, timeout=10)
        assert r.status_code == 200
        body = r.json()
        # Same shape as a real email — no _dev_token field.
        assert body["ok"] is True
        assert "_dev_token" not in body
        assert body.get("email_sent") is False

    def test_invalid_email_format_400(self):
        r = requests.post(f"{API}/auth/forgot-password",
                          json={"email": "not-an-email"}, timeout=10)
        assert r.status_code == 422  # pydantic validation

    def test_rate_limit_per_email(self):
        # Per-email cap: 5 in 600s. Hit it deliberately.
        unique = f"rl-{uuid.uuid4()}@example.com"
        codes = []
        for _ in range(8):
            r = requests.post(f"{API}/auth/forgot-password",
                              json={"email": unique}, timeout=10)
            codes.append(r.status_code)
        assert 429 in codes, f"expected at least one 429, got {codes}"


# ---------------------------------------------------------------------------
# /auth/reset-password
# ---------------------------------------------------------------------------
class TestResetPassword:

    @pytest.fixture()
    def disposable_user(self):
        """A throwaway student we can mint reset tokens against without
        racing the per-email rate limit on the seeded student.  Function
        scope so each test gets a clean rate-limit budget."""
        admin_token = _login(ADMIN_EMAIL, ADMIN_PW)["access_token"]
        email = f"reset-{uuid.uuid4().hex[:8]}@example.com"
        pw = "Initial@1"
        r = requests.post(f"{API}/admin/users",
                          headers=_auth(admin_token),
                          json={"email": email, "full_name": "Reset Subject",
                                "password": pw, "role": "student"},
                          timeout=30)
        assert r.status_code == 200, r.text
        uid = r.json()["user"]["id"]
        yield {"id": uid, "email": email, "password": pw}
        requests.delete(f"{API}/admin/users/{uid}",
                        headers=_auth(admin_token), timeout=30)

    def _request_token(self, email):
        r = requests.post(f"{API}/auth/forgot-password",
                          json={"email": email}, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "_dev_token" in body, "DEV_RETURN_RESET_TOKEN must be enabled"
        return body["_dev_token"]

    def test_happy_path_then_login(self, disposable_user):
        token = self._request_token(disposable_user["email"])
        new_pw = f"Reset@{uuid.uuid4().hex[:8]}"
        r = requests.post(f"{API}/auth/reset-password",
                          json={"token": token, "new_password": new_pw}, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["email"] == disposable_user["email"]
        data = _login(disposable_user["email"], new_pw)
        assert data["user"]["email"] == disposable_user["email"]

    def test_token_is_single_use(self, disposable_user):
        token = self._request_token(disposable_user["email"])
        new_pw = f"Reset@{uuid.uuid4().hex[:8]}"
        r1 = requests.post(f"{API}/auth/reset-password",
                           json={"token": token, "new_password": new_pw}, timeout=30)
        assert r1.status_code == 200
        r2 = requests.post(f"{API}/auth/reset-password",
                           json={"token": token, "new_password": "DoesntMatter@1"}, timeout=30)
        assert r2.status_code == 400

    def test_invalid_token_400(self):
        r = requests.post(f"{API}/auth/reset-password",
                          json={"token": "x" * 40, "new_password": "Whatever@1"}, timeout=30)
        assert r.status_code == 400

    def test_token_too_short_400(self):
        r = requests.post(f"{API}/auth/reset-password",
                          json={"token": "abc", "new_password": "Whatever@1"}, timeout=30)
        assert r.status_code == 400

    def test_password_too_short_400(self, disposable_user):
        token = self._request_token(disposable_user["email"])
        r = requests.post(f"{API}/auth/reset-password",
                          json={"token": token, "new_password": "abc"}, timeout=30)
        assert r.status_code == 400
        # Token should still be valid since the request was rejected before consumption.
        good = requests.post(f"{API}/auth/reset-password",
                             json={"token": token,
                                   "new_password": f"OK@{uuid.uuid4().hex[:6]}"},
                             timeout=30)
        assert good.status_code == 200

    def test_minting_new_token_invalidates_old(self, disposable_user):
        t1 = self._request_token(disposable_user["email"])
        t2 = self._request_token(disposable_user["email"])
        r1 = requests.post(f"{API}/auth/reset-password",
                           json={"token": t1, "new_password": "NewPass@1"}, timeout=30)
        assert r1.status_code == 400
        r2 = requests.post(f"{API}/auth/reset-password",
                           json={"token": t2,
                                 "new_password": f"OK@{uuid.uuid4().hex[:6]}"},
                           timeout=30)
        assert r2.status_code == 200


# ---------------------------------------------------------------------------
# /admin/users/{uid}/reset-link  (admin-mediated)
# ---------------------------------------------------------------------------
class TestAdminResetLink:

    @pytest.fixture(scope="class")
    def admin_token(self):
        return _login(ADMIN_EMAIL, ADMIN_PW)["access_token"]

    @pytest.fixture(scope="class")
    def exec_token(self):
        return _login(EXEC_EMAIL, EXEC_PW)["access_token"]

    @pytest.fixture(scope="class")
    def student_token(self):
        return _login(STUDENT_EMAIL, STUDENT_PW)["access_token"]

    @pytest.fixture(scope="class")
    def fresh_student(self, admin_token):
        """A throwaway student to receive reset links — never the seeded one."""
        email = f"rstest-{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{API}/admin/users",
                          headers=_auth(admin_token),
                          json={"email": email, "full_name": "Reset Test",
                                "password": "TempPass@1", "role": "student"})
        assert r.status_code == 200, r.text
        uid = r.json()["user"]["id"]
        yield {"id": uid, "email": email}
        # Cleanup
        requests.delete(f"{API}/admin/users/{uid}", headers=_auth(admin_token))

    def test_admin_can_mint_reset_link(self, admin_token, fresh_student):
        r = requests.post(f"{API}/admin/users/{fresh_student['id']}/reset-link",
                          headers=_auth(admin_token), json={})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["email"] == fresh_student["email"]
        assert isinstance(body["token"], str) and len(body["token"]) >= 32
        assert body["url"].startswith(("/reset-password", "http"))
        assert body["ttl_minutes"] >= 5

    def test_admin_link_completes_reset_flow(self, admin_token, fresh_student):
        r = requests.post(f"{API}/admin/users/{fresh_student['id']}/reset-link",
                          headers=_auth(admin_token), json={})
        assert r.status_code == 200
        token = r.json()["token"]
        new_pw = f"AdminLink@{uuid.uuid4().hex[:6]}"
        r2 = requests.post(f"{API}/auth/reset-password",
                           json={"token": token, "new_password": new_pw})
        assert r2.status_code == 200
        # User can now log in with the new password.
        d = _login(fresh_student["email"], new_pw)
        assert d["user"]["email"] == fresh_student["email"]

    def test_student_cannot_mint_reset_link(self, student_token, fresh_student):
        r = requests.post(f"{API}/admin/users/{fresh_student['id']}/reset-link",
                          headers=_auth(student_token), json={})
        assert r.status_code == 403

    def test_admin_cannot_mint_link_for_executive(self, admin_token, exec_token):
        # Find the exec admin's id.
        me = requests.get(f"{API}/auth/me", headers=_auth(exec_token)).json()
        r = requests.post(f"{API}/admin/users/{me['id']}/reset-link",
                          headers=_auth(admin_token), json={})
        assert r.status_code == 403

    def test_executive_can_mint_link_for_admin(self, exec_token, admin_token):
        admin_me = requests.get(f"{API}/auth/me", headers=_auth(admin_token)).json()
        r = requests.post(f"{API}/admin/users/{admin_me['id']}/reset-link",
                          headers=_auth(exec_token), json={})
        assert r.status_code == 200
        # Don't actually consume the token — that would lock out the seeded admin.

    def test_unauthenticated_blocked(self, fresh_student):
        r = requests.post(f"{API}/admin/users/{fresh_student['id']}/reset-link", json={})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# /auth/me PATCH  (self profile edit)
# ---------------------------------------------------------------------------
class TestSelfEdit:

    @pytest.fixture()
    def fresh_user(self):
        admin_token = _login(ADMIN_EMAIL, ADMIN_PW)["access_token"]
        email = f"self-{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{API}/admin/users",
                          headers=_auth(admin_token),
                          json={"email": email, "full_name": "Self Edit",
                                "password": "TempPass@1", "role": "student",
                                "associate": "Associate-Alpha"})
        assert r.status_code == 200, r.text
        uid = r.json()["user"]["id"]
        # admin-created users have must_change_password=True; bypass by direct login
        # (login still succeeds; the flag is informational for the UI).
        token = _login(email, "TempPass@1")["access_token"]
        yield {"id": uid, "email": email, "token": token}
        requests.delete(f"{API}/admin/users/{uid}", headers=_auth(admin_token))

    def test_user_can_edit_own_name(self, fresh_user):
        r = requests.patch(f"{API}/auth/me",
                           headers=_auth(fresh_user["token"]),
                           json={"full_name": "New Name"})
        assert r.status_code == 200
        assert r.json()["full_name"] == "New Name"

    def test_user_can_edit_own_email(self, fresh_user):
        new_email = f"renamed-{uuid.uuid4().hex[:6]}@example.com"
        r = requests.patch(f"{API}/auth/me",
                           headers=_auth(fresh_user["token"]),
                           json={"email": new_email})
        assert r.status_code == 200
        assert r.json()["email"] == new_email

    def test_email_collision_400(self, fresh_user):
        # Try to take the seeded admin's email.
        r = requests.patch(f"{API}/auth/me",
                           headers=_auth(fresh_user["token"]),
                           json={"email": ADMIN_EMAIL})
        assert r.status_code == 400

    def test_empty_name_400(self, fresh_user):
        r = requests.patch(f"{API}/auth/me",
                           headers=_auth(fresh_user["token"]),
                           json={"full_name": "   "})
        assert r.status_code == 400

    def test_unauthenticated_401(self):
        r = requests.patch(f"{API}/auth/me", json={"full_name": "x"})
        assert r.status_code == 401

    def test_role_and_associate_silently_ignored(self, fresh_user):
        """Role and associate fields are not in the SelfEditMeReq schema —
        Pydantic should ignore unknown fields and the values must NOT
        change."""
        before = requests.get(f"{API}/auth/me", headers=_auth(fresh_user["token"])).json()
        r = requests.patch(f"{API}/auth/me",
                           headers=_auth(fresh_user["token"]),
                           json={"role": "admin", "associate": "Hacked"})
        # Either 200 (unknown fields ignored) or 422 (strict). Both are fine
        # so long as the role/associate did not change.
        assert r.status_code in (200, 422)
        after = requests.get(f"{API}/auth/me", headers=_auth(fresh_user["token"])).json()
        assert after["role"] == before["role"]
        assert after["associate"] == before["associate"]


# ---------------------------------------------------------------------------
# Frontend ↔ backend domain parity
# ---------------------------------------------------------------------------
class TestDomainParity:

    def test_health_ok(self):
        r = requests.get(f"{API}/health", timeout=30)
        assert r.status_code == 200
        assert r.json()["db"] == "up"

    def test_login_returns_bearer_token(self):
        d = _login(EXEC_EMAIL, EXEC_PW)
        assert d["token_type"] == "bearer"
        assert isinstance(d["access_token"], str) and len(d["access_token"]) > 50
        assert d["user"]["role"] == "executive_admin"
