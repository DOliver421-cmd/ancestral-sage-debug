"""Comprehensive RBAC matrix test — EXECUTIVE_ADMIN / ADMIN / INSTRUCTOR / STUDENT.

Covers:
  * Login for all four roles.
  * Permitted endpoints (positive tests).
  * Forbidden endpoints (negative tests — must 403).
  * Hierarchy guards (admin cannot modify exec, etc.).
  * User-management happy path end-to-end.

Runs against the live REACT_APP_BACKEND_URL (loaded by conftest.py from
/app/frontend/.env).
"""
import os
import uuid

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"

SEED = {
    "executive_admin": ("delon.oliver@lightningcityelectric.com", "Executive@LCE2026"),
    "admin": ("admin@lcewai.org", "Admin@LCE2026"),
    "instructor": ("instructor@lcewai.org", "Teach@LCE2026"),
    "student": ("student@lcewai.org", "Learn@LCE2026"),
}


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    return r.json()


@pytest.fixture(scope="module")
def tokens():
    out = {}
    for role, (email, pw) in SEED.items():
        data = _login(email, pw)
        assert data["user"]["role"] == role, f"{email} expected role={role} got {data['user']['role']}"
        out[role] = {"token": data["access_token"], "id": data["user"]["id"], "email": email}
    return out


def _h(t):
    return {"Authorization": f"Bearer {t}"}


# ---------------------------------------------------------------------------
# Phase 1 — positive access matrix.  Each role's permitted GETs return 200.
# ---------------------------------------------------------------------------
class TestPositiveAccess:

    def test_all_roles_can_get_me(self, tokens):
        for role, ctx in tokens.items():
            r = requests.get(f"{API}/auth/me", headers=_h(ctx["token"]))
            assert r.status_code == 200, f"{role} /auth/me failed"
            assert r.json()["role"] == role

    @pytest.mark.parametrize("path", [
        "/modules", "/labs", "/competencies", "/credentials", "/credentials/me",
        "/portfolio/me", "/compliance", "/adaptive/me", "/notifications/me",
    ])
    def test_student_protected_content(self, tokens, path):
        r = requests.get(f"{API}{path}", headers=_h(tokens["student"]["token"]))
        assert r.status_code == 200, f"student {path}: {r.status_code}"

    @pytest.mark.parametrize("path", ["/roster", "/instructor/submissions", "/instructor/lab-report"])
    def test_instructor_routes(self, tokens, path):
        r = requests.get(f"{API}{path}", headers=_h(tokens["instructor"]["token"]))
        assert r.status_code == 200

    @pytest.mark.parametrize("path", [
        "/admin/stats", "/admin/users", "/admin/audit",
        "/admin/sites", "/admin/inventory", "/admin/checkouts",
        "/analytics/program",
    ])
    def test_admin_routes(self, tokens, path):
        r = requests.get(f"{API}{path}", headers=_h(tokens["admin"]["token"]))
        assert r.status_code == 200

    @pytest.mark.parametrize("path", [
        "/admin/stats", "/admin/users", "/admin/audit",
        "/admin/sites", "/admin/inventory", "/admin/checkouts",
        "/analytics/program", "/exec/system",
    ])
    def test_exec_routes(self, tokens, path):
        """Exec_admin inherits EVERYTHING."""
        r = requests.get(f"{API}{path}", headers=_h(tokens["executive_admin"]["token"]))
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Phase 1b — negative access matrix.  Lower-privileged roles → 403.
# ---------------------------------------------------------------------------
class TestNegativeAccess:

    @pytest.mark.parametrize("role", ["student", "instructor"])
    @pytest.mark.parametrize("path", [
        "/admin/users", "/admin/audit", "/admin/stats", "/analytics/program",
    ])
    def test_non_admin_cannot_read_admin(self, tokens, role, path):
        r = requests.get(f"{API}{path}", headers=_h(tokens[role]["token"]))
        assert r.status_code == 403, f"{role} {path} expected 403 got {r.status_code}"

    def test_student_cannot_read_sites_or_inventory(self, tokens):
        # Students have zero business with the tool inventory.
        for path in ("/admin/sites", "/admin/inventory"):
            r = requests.get(f"{API}{path}", headers=_h(tokens["student"]["token"]))
            assert r.status_code == 403, f"student {path} expected 403 got {r.status_code}"

    @pytest.mark.parametrize("role", ["student", "instructor", "admin"])
    def test_non_exec_cannot_read_exec_system(self, tokens, role):
        r = requests.get(f"{API}/exec/system", headers=_h(tokens[role]["token"]))
        assert r.status_code == 403

    def test_student_cannot_see_roster(self, tokens):
        r = requests.get(f"{API}/roster", headers=_h(tokens["student"]["token"]))
        assert r.status_code == 403

    def test_no_token_admin_users(self):
        r = requests.get(f"{API}/admin/users")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Phase 1c — hierarchy guards on user-management writes.
# ---------------------------------------------------------------------------
class TestHierarchyGuards:

    def test_public_register_forces_student(self):
        email = f"rbac-reg-{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{API}/auth/register", json={
            "email": email,
            "full_name": "Reg Test",
            "password": "TestPass12",
            "role": "admin",  # ← should be ignored
        })
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "student"

    def test_admin_cannot_grant_exec_role(self, tokens):
        stu_id = tokens["student"]["id"]
        r = requests.patch(f"{API}/admin/users/{stu_id}/role",
                           headers=_h(tokens["admin"]["token"]),
                           json={"role": "executive_admin"})
        assert r.status_code == 403

    def test_admin_cannot_create_exec_user(self, tokens):
        r = requests.post(f"{API}/admin/users", headers=_h(tokens["admin"]["token"]),
                          json={
                              "email": f"admin-try-exec-{uuid.uuid4().hex[:6]}@example.com",
                              "full_name": "X", "password": "Test12345",
                              "role": "executive_admin",
                          })
        assert r.status_code == 403

    def test_admin_cannot_modify_exec(self, tokens):
        exec_id = tokens["executive_admin"]["id"]
        r = requests.patch(f"{API}/admin/users/{exec_id}", headers=_h(tokens["admin"]["token"]),
                           json={"full_name": "hacker"})
        assert r.status_code == 403

    def test_admin_cannot_deactivate_exec(self, tokens):
        exec_id = tokens["executive_admin"]["id"]
        r = requests.patch(f"{API}/admin/users/{exec_id}/active", headers=_h(tokens["admin"]["token"]),
                           json={"is_active": False})
        assert r.status_code == 403

    def test_admin_cannot_reset_exec_password(self, tokens):
        exec_id = tokens["executive_admin"]["id"]
        r = requests.post(f"{API}/admin/users/{exec_id}/password", headers=_h(tokens["admin"]["token"]),
                          json={"new_password": "hacker123"})
        assert r.status_code == 403

    def test_admin_cannot_delete_exec(self, tokens):
        exec_id = tokens["executive_admin"]["id"]
        r = requests.delete(f"{API}/admin/users/{exec_id}", headers=_h(tokens["admin"]["token"]))
        assert r.status_code == 403

    def test_admin_self_demote_refused(self, tokens):
        r = requests.patch(f"{API}/admin/users/{tokens['admin']['id']}/role",
                           headers=_h(tokens["admin"]["token"]),
                           json={"role": "student"})
        assert r.status_code == 400

    def test_admin_self_deactivate_refused(self, tokens):
        r = requests.patch(f"{API}/admin/users/{tokens['admin']['id']}/active",
                           headers=_h(tokens["admin"]["token"]),
                           json={"is_active": False})
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Phase 1d — user-management happy path (by exec).
# ---------------------------------------------------------------------------
class TestUserManagementHappyPath:

    def test_full_user_lifecycle(self, tokens):
        ex = tokens["executive_admin"]["token"]
        email = f"rbac-life-{uuid.uuid4().hex[:8]}@example.com"

        # create
        r = requests.post(f"{API}/admin/users", headers=_h(ex), json={
            "email": email, "full_name": "Life Cycle", "password": "TestPass12",
            "role": "instructor", "associate": "Associate-QA",
        })
        assert r.status_code == 200, r.text
        uid = r.json()["user"]["id"]

        # edit
        r = requests.patch(f"{API}/admin/users/{uid}", headers=_h(ex),
                           json={"full_name": "Life Cycle 2", "associate": "Associate-QA2"})
        assert r.status_code == 200

        # promote instructor → admin
        r = requests.patch(f"{API}/admin/users/{uid}/role", headers=_h(ex),
                           json={"role": "admin"})
        assert r.status_code == 200

        # deactivate + login refused
        r = requests.patch(f"{API}/admin/users/{uid}/active", headers=_h(ex),
                           json={"is_active": False})
        assert r.status_code == 200
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "TestPass12"})
        assert r.status_code == 403

        # reactivate + login OK
        r = requests.patch(f"{API}/admin/users/{uid}/active", headers=_h(ex),
                           json={"is_active": True})
        assert r.status_code == 200
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "TestPass12"})
        assert r.status_code == 200

        # admin-reset password
        r = requests.post(f"{API}/admin/users/{uid}/password", headers=_h(ex),
                          json={"new_password": "NewPw12345"})
        assert r.status_code == 200

        # new password works, old doesn't
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "NewPw12345"})
        assert r.status_code == 200
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "TestPass12"})
        assert r.status_code == 401

        # self change-password
        new_token = r = requests.post(f"{API}/auth/login", json={"email": email, "password": "NewPw12345"}).json()["access_token"]
        r = requests.post(f"{API}/auth/change-password", headers=_h(new_token),
                          json={"current_password": "NewPw12345", "new_password": "Third12345"})
        assert r.status_code == 200

        # delete
        r = requests.delete(f"{API}/admin/users/{uid}", headers=_h(ex))
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Phase 1e — list/filter query-params (added in this pass).
# ---------------------------------------------------------------------------
class TestUserListFilters:

    def test_filter_by_role(self, tokens):
        r = requests.get(f"{API}/admin/users?role=student", headers=_h(tokens["admin"]["token"]))
        assert r.status_code == 200
        assert all(u["role"] == "student" for u in r.json())

    def test_filter_active_only(self, tokens):
        r = requests.get(f"{API}/admin/users?active=true", headers=_h(tokens["admin"]["token"]))
        assert r.status_code == 200
        for u in r.json():
            assert u.get("is_active", True) is True

    def test_search_substring(self, tokens):
        r = requests.get(f"{API}/admin/users?q=instructor", headers=_h(tokens["admin"]["token"]))
        assert r.status_code == 200
        for u in r.json():
            q = "instructor"
            assert q in (u["full_name"] + u["email"]).lower() or u["role"] == "instructor"


# ---------------------------------------------------------------------------
# Phase 1f — last-exec and last-admin-class guards.
# ---------------------------------------------------------------------------
class TestCriticalGuards:

    def test_exec_cannot_delete_self(self, tokens):
        ex_id = tokens["executive_admin"]["id"]
        r = requests.delete(f"{API}/admin/users/{ex_id}", headers=_h(tokens["executive_admin"]["token"]))
        assert r.status_code == 400

    def test_exec_cannot_deactivate_self(self, tokens):
        ex_id = tokens["executive_admin"]["id"]
        r = requests.patch(f"{API}/admin/users/{ex_id}/active",
                           headers=_h(tokens["executive_admin"]["token"]),
                           json={"is_active": False})
        assert r.status_code == 400


class TestForcedPasswordChange:
    """Newly-created accounts and admin-reset accounts must be flagged
    `must_change_password` so the frontend can route them to /settings."""

    def test_admin_created_user_has_force_flag(self, tokens):
        ex = tokens["executive_admin"]["token"]
        email = f"rbac-force-{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{API}/admin/users", headers=_h(ex), json={
            "email": email, "full_name": "Force Test", "password": "TempPw12345",
            "role": "student",
        })
        assert r.status_code == 200
        uid = r.json()["user"]["id"]
        # Login as the new user — must_change_password should be true
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "TempPw12345"})
        assert r.status_code == 200
        assert r.json()["user"].get("must_change_password") is True
        new_token = r.json()["access_token"]
        # After self change-password, flag should clear
        r = requests.post(f"{API}/auth/change-password", headers=_h(new_token),
                          json={"current_password": "TempPw12345", "new_password": "NewPw12345"})
        assert r.status_code == 200
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "NewPw12345"})
        assert r.status_code == 200
        assert r.json()["user"].get("must_change_password", False) is False
        # cleanup
        requests.delete(f"{API}/admin/users/{uid}", headers=_h(ex))

    def test_admin_password_reset_re_arms_force_flag(self, tokens):
        ex = tokens["executive_admin"]["token"]
        email = f"rbac-reset-{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{API}/admin/users", headers=_h(ex), json={
            "email": email, "full_name": "Reset Test", "password": "TempPw12345", "role": "student",
        })
        uid = r.json()["user"]["id"]
        # User clears the flag by self-changing password
        tok = requests.post(f"{API}/auth/login", json={"email": email, "password": "TempPw12345"}).json()["access_token"]
        requests.post(f"{API}/auth/change-password", headers=_h(tok),
                      json={"current_password": "TempPw12345", "new_password": "Mine12345"})
        # Now admin resets the password — flag must come back
        r = requests.post(f"{API}/admin/users/{uid}/password", headers=_h(ex),
                          json={"new_password": "AdminReset123"})
        assert r.status_code == 200
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "AdminReset123"})
        assert r.json()["user"].get("must_change_password") is True
        # cleanup
        requests.delete(f"{API}/admin/users/{uid}", headers=_h(ex))
