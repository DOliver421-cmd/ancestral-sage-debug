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
