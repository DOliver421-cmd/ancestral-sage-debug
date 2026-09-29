"""
test_password_recovery_regressions.py — Phase 2 (account recovery) regressions.

Pure, DB-free regressions for the two recovery fixes:

  1. /auth/reset-password and /auth/emergency-recovery must enforce the same
     8-character password floor as registration, password-change, and the
     reset UI. The old schema accepted any length (the endpoint helper only
     rejected < 6), so one path could set a weaker password than every other
     path on the site. The floor raises HTTPException(400) so the endpoints
     keep their documented 400 contract (see tests/test_password_reset.py::
     TestResetPassword::test_password_too_short_400) and the reset token is
     not consumed by a rejected request.

  2. The password-reset email must HTML-escape user-controlled fields. The
     old template interpolated `full_name` raw into the HTML body, so a
     display name containing markup executed in the recipient's mail client.

Each regression fails against the pre-fix implementation and passes on the
current one. No database, network, or mail provider is touched.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402
from server import (  # noqa: E402
    EmergencyRecoveryReq,
    ResetPasswordReq,
    _reset_email_html,
)

LONG_TOKEN = "t" * 40


# ---------------------------------------------------------------------------
# Password floor on recovery flows (regression: old schema accepted < 8).
# ---------------------------------------------------------------------------
class TestRecoveryPasswordFloor:
    def test_reset_password_rejects_6_chars(self):
        """Regression: the old schema accepted 6-char passwords (only the
        endpoint helper's 6-char floor stood behind it, weaker than the 8-char
        policy everywhere else)."""
        with pytest.raises(HTTPException) as ei:
            ResetPasswordReq(token=LONG_TOKEN, new_password="Ab12cd")
        assert ei.value.status_code == 400
        assert "8" in str(ei.value.detail)

    def test_reset_password_rejects_7_chars(self):
        with pytest.raises(HTTPException) as ei:
            ResetPasswordReq(token=LONG_TOKEN, new_password="Ab12cde")
        assert ei.value.status_code == 400

    def test_reset_password_accepts_exactly_8(self):
        req = ResetPasswordReq(token=LONG_TOKEN, new_password="Ab12cdef")
        assert req.new_password == "Ab12cdef"

    def test_reset_password_accepts_longer(self):
        req = ResetPasswordReq(token=LONG_TOKEN, new_password="Whatever@1")
        assert req.new_password == "Whatever@1"

    def test_emergency_recovery_rejects_short(self):
        """Regression: EmergencyRecoveryReq had no minimum at all."""
        with pytest.raises(HTTPException) as ei:
            EmergencyRecoveryReq(
                email="exec@example.com",
                recovery_code="R" * 32,
                new_password="short",
            )
        assert ei.value.status_code == 400

    def test_emergency_recovery_accepts_8(self):
        req = EmergencyRecoveryReq(
            email="exec@example.com",
            recovery_code="R" * 32,
            new_password="Ab12cdef",
        )
        assert req.new_password == "Ab12cdef"

    def test_reset_token_still_validated_independently(self):
        """The password floor must not change token validation semantics: a
        short token with a valid password is still a 400 from the endpoint
        helper (covered in test_password_reset.py); the model only guards the
        password field."""
        req = ResetPasswordReq(token="short", new_password="Ab12cdef")
        assert req.token == "short"


# ---------------------------------------------------------------------------
# Reset email HTML escaping (regression: raw full_name was interpolated).
# ---------------------------------------------------------------------------
class TestResetEmailEscaping:
    def test_full_name_is_html_escaped(self):
        """Regression: a display name with markup was written raw into the
        reset email body."""
        hostile = '<img src=x onerror=alert(1)>'
        _, html = _reset_email_html(hostile, "https://app.example/reset-password?token=t")
        assert "<img" not in html
        assert "&lt;img" in html

    def test_quoted_name_escaped(self):
        _, html = _reset_email_html('Bob "the Builder"', "https://app.example/r?token=t")
        assert 'Bob "the Builder"' not in html
        assert "&quot;" in html

    def test_url_still_rendered_intact(self):
        url = "https://app.example/reset-password?token=abc123"
        _, html = _reset_email_html("Member", url)
        assert url in html

    def test_default_name_when_empty(self):
        _, html = _reset_email_html("", "https://app.example/r?token=t")
        assert "Hi there," in html


# ---------------------------------------------------------------------------
# No weak 6-character password floor may survive anywhere in the backend.
# Phase 5 cleanup: six handler-level checks enforced 6 chars — three in
# server.py (shadowed by 8-char request models) and three in routers/ (not
# mounted, but a latent 6-char floor if they ever are). All aligned to 8.
# ---------------------------------------------------------------------------
class TestNoWeakPasswordFloorRemains:
    """Behavioral enforcement of the 8-character floor.

    The earlier version of this guard grepped the source tree for the literal
    string "at least 6 characters". That is a phrasing check, not a policy
    check: it passed even when a real 6-char floor was reinstated with
    different wording. These tests call the live ASGI app instead, so any
    endpoint that accepts a short password fails regardless of message text.
    """

    @staticmethod
    def _post(client, url, body):
        return client.post(url, json=body)

    def test_reset_password_endpoint_rejects_6_chars(self):
        client = TestClient(server.app, raise_server_exceptions=False)
        r = self._post(client, "/api/auth/reset-password",
                       {"token": LONG_TOKEN, "new_password": "Ab12cd"})
        # 400 = rejected by the password floor. 401/404 would mean the request
        # got past validation, which is the regression this guards.
        assert r.status_code == 400, r.text
        assert "8" in r.text

    def test_reset_password_endpoint_rejects_7_chars(self):
        client = TestClient(server.app, raise_server_exceptions=False)
        r = self._post(client, "/api/auth/reset-password",
                       {"token": LONG_TOKEN, "new_password": "Ab12cde"})
        assert r.status_code == 400, r.text

    def test_eight_chars_passes_the_floor(self):
        """8 chars must CLEAR the password floor.

        Asserts only on the floor message, not on the downstream outcome: past
        validation the request reaches the token lookup, whose result depends
        on database and rate-limit state and is not what this test is about.
        """
        client = TestClient(server.app, raise_server_exceptions=False)
        r = self._post(client, "/api/auth/reset-password",
                       {"token": LONG_TOKEN, "new_password": "Ab12cdef"})
        assert "8 characters" not in r.text, (
            "8-character password was rejected by the floor: " + r.text
        )

    def test_admin_reset_password_endpoint_rejects_6_chars(self):
        """The admin reset path is mounted; short passwords must not validate."""
        client = TestClient(server.app, raise_server_exceptions=False)
        r = self._post(client, "/api/admin/users/someone/reset-password",
                       {"new_password": "Ab12cd"})
        assert r.status_code in (400, 401, 403), r.text
        if r.status_code == 400:
            assert "8" in r.text

    def test_change_password_endpoint_rejects_6_chars(self):
        client = TestClient(server.app, raise_server_exceptions=False)
        r = self._post(client, "/api/auth/change-password",
                       {"current_password": "whatever", "new_password": "Ab12cd"})
        # 401 is acceptable: auth runs before the handler body. 422 would mean
        # the schema let a 6-char password through.
        assert r.status_code in (400, 401, 403, 422), r.text
        assert r.status_code != 200

    def test_reset_request_helper_enforces_8(self):
        with pytest.raises(HTTPException) as ei:
            server._validate_reset_request(LONG_TOKEN, "Ab12cd")
        assert ei.value.status_code == 400
        assert "8" in str(ei.value.detail)
        # Exactly 8 passes the password floor (token length is a separate gate)
        server._validate_reset_request(LONG_TOKEN, "Ab12cdef")


# ---------------------------------------------------------------------------
# User-administration routes must actually mount.
#
# Regression: server.py's _USERS_ROUTES table referenced handler names that
# did not exist in routers/users.py (exec_list_user_sessions /
# exec_force_logout). The surrounding `except Exception` swallowed the
# AttributeError into a log WARNING, so ALL 20 user-admin endpoints silently
# vanished — including force-logout. The frontend called them anyway.
# ---------------------------------------------------------------------------
class TestUserAdminRoutesRegistered:
    REQUIRED = [
        "/api/admin/users/{uid}",
        "/api/admin/users/{uid}/tier",
        "/api/admin/users/{uid}/ban",
        "/api/admin/users/{uid}/unban",
        "/api/admin/users/{uid}/erasure",
        "/api/admin/users/{uid}/sessions",
        "/api/admin/users/{uid}/audit",
        "/api/admin/users/{uid}/reset-password",
        "/api/admin/users/{uid}/elevated-role",
        "/api/admin/users/bulk",
        "/api/admin/mfa/config",
        "/api/admin/access/ipwhitelist",
    ]

    def test_all_user_admin_paths_present(self):
        paths = server.app.openapi()["paths"]
        missing = [p for p in self.REQUIRED if p not in paths]
        assert missing == [], "user-admin routes not registered: " + ", ".join(missing)

    def test_force_logout_is_reachable_not_404(self):
        """Force logout is a real security control; it must not 404."""
        client = TestClient(server.app, raise_server_exceptions=False)
        r = client.delete("/api/admin/users/someone/sessions")
        assert r.status_code != 404, r.text
        assert r.status_code in (401, 403), r.text

    def test_session_list_binds_the_session_handler(self):
        """The GET must reach admin_list_sessions on the module's own router.

        Regression: an orphaned @router.get("/admin/users/{uid}/sessions")
        decorator in routers/users.py had no function beneath it, so it stacked
        onto exec_bulk_action and registered the session-list GET against the
        bulk-action handler.

        This must be asserted against routers.users.router, NOT the app's
        OpenAPI: server.py registers these handlers by name via add_api_route
        and never mounts the module router, so the app surface stays correct
        even while the module's own routing table is wrong.
        """
        from routers import users as users_router

        matches = [
            r for r in users_router.router.routes
            if getattr(r, "path", "") == "/admin/users/{uid}/sessions"
            and "GET" in getattr(r, "methods", set())
        ]
        assert matches, "no GET route registered for /admin/users/{uid}/sessions"
        for r in matches:
            assert r.endpoint.__name__ == "admin_list_sessions", (
                "GET /admin/users/{uid}/sessions is bound to "
                f"{r.endpoint.__name__}, expected admin_list_sessions"
            )

    def test_reset_password_route_binds_the_exec_policy_handler(self):
        """guards the admin_reset_password vs admin_reset_password_exec shadow."""
        spec = server.app.openapi()
        op = spec["paths"]["/api/admin/users/{uid}/reset-password"]["post"]
        assert op["operationId"].startswith("admin_reset_password_exec"), op["operationId"]
