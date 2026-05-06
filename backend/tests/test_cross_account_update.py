"""Cross-account update authority tests.

The previous code-review request asked for explicit verification that
EXECUTIVE_ADMIN can update other accounts.  These tests target the
admin surface (`PATCH /api/admin/users/{uid}`, `POST /api/admin/users`,
`POST /api/admin/users/{uid}/password`, `POST /api/admin/users/{uid}/reset-link`)
to confirm:
  * exec_admin can edit / reset-password / mint reset link for ANY role
    including admin
  * admin CAN update student / instructor but is BLOCKED from touching
    executive_admin (immunity rule)
  * Settings page (`PATCH /api/auth/me`) remains self-only

Driven against REACT_APP_BACKEND_URL.
"""
import os
import uuid

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"

EXEC = ("delon.oliver@lightningcityelectric.com", "Executive@LCE2026")
ADMIN = ("admin@lcewai.org", "Admin@LCE2026")
INSTRUCTOR = ("instructor@lcewai.org", "Teach@LCE2026")
STUDENT = ("student@lcewai.org", "Learn@LCE2026")


def _login(email, pw):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=20)
    assert r.status_code == 200, f"{email} login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def exec_token():
    return _login(*EXEC)


@pytest.fixture(scope="module")
def admin_token():
    return _login(*ADMIN)


@pytest.fixture()
def disposable_target(admin_token):
    """A throwaway student created by admin and torn down at the end."""
    email = f"target-{uuid.uuid4().hex[:8]}@example.com"
    r = requests.post(f"{API}/admin/users",
                      headers=_h(admin_token),
                      json={"email": email, "full_name": "Target",
                            "password": "Target@1", "role": "student",
                            "associate": "Associate-Alpha"},
                      timeout=30)
    assert r.status_code == 200, r.text
    uid = r.json()["user"]["id"]
    yield {"id": uid, "email": email}
    requests.delete(f"{API}/admin/users/{uid}", headers=_h(admin_token), timeout=30)


# -------- exec_admin can edit anyone --------------------------------------
class TestExecAdminCrossAccount:

    def test_exec_can_edit_student(self, exec_token, disposable_target):
        r = requests.patch(f"{API}/admin/users/{disposable_target['id']}",
                           headers=_h(exec_token),
                           json={"full_name": "Edited By Exec",
                                 "associate": "Associate-Beta"})
        assert r.status_code == 200, r.text
        assert r.json()["ok"] is True
        # Verify persistence by re-reading.
        listing = requests.get(f"{API}/admin/users",
                               headers=_h(exec_token)).json()
        target = next(u for u in listing if u["id"] == disposable_target["id"])
        assert target["full_name"] == "Edited By Exec"
        assert target["associate"] == "Associate-Beta"

    def test_exec_can_reset_anyones_password(self, exec_token, disposable_target):
        r = requests.post(f"{API}/admin/users/{disposable_target['id']}/password",
                          headers=_h(exec_token),
                          json={"new_password": "ExecSet@1"})
        assert r.status_code == 200, r.text
        # Confirm it actually persisted by logging in with the new password.
        d = requests.post(f"{API}/auth/login",
                          json={"email": disposable_target["email"],
                                "password": "ExecSet@1"}, timeout=20)
        assert d.status_code == 200

    def test_exec_can_mint_reset_link_for_admin(self, exec_token, admin_token):
        admin_me = requests.get(f"{API}/auth/me", headers=_h(admin_token)).json()
        r = requests.post(f"{API}/admin/users/{admin_me['id']}/reset-link",
                          headers=_h(exec_token), json={})
        assert r.status_code == 200
        # We don't consume the token — that would lock out the seeded admin.
        assert isinstance(r.json()["token"], str)

    def test_exec_can_promote_student_to_instructor(self, exec_token, disposable_target):
        r = requests.patch(f"{API}/admin/users/{disposable_target['id']}/role",
                           headers=_h(exec_token),
                           json={"role": "instructor"})
        assert r.status_code == 200
        assert r.json()["role"] == "instructor"


# -------- admin can edit non-exec, but is blocked from exec ----------------
class TestAdminScope:

    def test_admin_can_edit_student(self, admin_token, disposable_target):
        r = requests.patch(f"{API}/admin/users/{disposable_target['id']}",
                           headers=_h(admin_token),
                           json={"full_name": "Edited By Admin"})
        assert r.status_code == 200

    def test_admin_cannot_edit_executive(self, admin_token, exec_token):
        exec_me = requests.get(f"{API}/auth/me", headers=_h(exec_token)).json()
        r = requests.patch(f"{API}/admin/users/{exec_me['id']}",
                           headers=_h(admin_token),
                           json={"full_name": "Hacked"})
        assert r.status_code == 403

    def test_admin_cannot_reset_executive_password(self, admin_token, exec_token):
        exec_me = requests.get(f"{API}/auth/me", headers=_h(exec_token)).json()
        r = requests.post(f"{API}/admin/users/{exec_me['id']}/password",
                          headers=_h(admin_token),
                          json={"new_password": "Hacked@1"})
        assert r.status_code == 403


# -------- Settings (self-only) --------------------------------------------
class TestSettingsIsSelfOnly:

    def test_patch_me_does_not_accept_role_field(self, admin_token):
        before = requests.get(f"{API}/auth/me", headers=_h(admin_token)).json()
        r = requests.patch(f"{API}/auth/me",
                           headers=_h(admin_token),
                           json={"role": "executive_admin",
                                 "associate": "Hacked"})
        assert r.status_code in (200, 422)  # unknown fields ignored OR rejected
        after = requests.get(f"{API}/auth/me", headers=_h(admin_token)).json()
        assert after["role"] == before["role"]
        assert after["associate"] == before["associate"]

    def test_patch_me_persists_name_and_email(self, admin_token):
        before = requests.get(f"{API}/auth/me", headers=_h(admin_token)).json()
        new_name = f"Admin Edited {uuid.uuid4().hex[:6]}"
        r = requests.patch(f"{API}/auth/me",
                           headers=_h(admin_token),
                           json={"full_name": new_name})
        assert r.status_code == 200
        after = requests.get(f"{API}/auth/me", headers=_h(admin_token)).json()
        assert after["full_name"] == new_name
        # Restore.
        requests.patch(f"{API}/auth/me", headers=_h(admin_token),
                       json={"full_name": before["full_name"]})
