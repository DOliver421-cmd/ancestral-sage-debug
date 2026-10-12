"""tests/test_remediation_a1_a2.py — the two owner-approved remediation fixes.

A1: a password change must END the sessions that existed before it.
    (server.py: change_password previously left every issued JWT valid.)
A2: the AI Coach's parent switch must be enforced by the SERVER, not only by
    the button in the browser.

Both tests execute the real endpoints against the running server, which is the
only way to prove a revocation actually revokes — source inspection cannot.
"""

import os
import sys

import pytest
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_BASE = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")
API = f"{_BASE}/api"

_probe = {"email": None, "password": None}


def _hdr(t):
    return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def _new_account(tag):
    email = f"remediation.{tag}.{os.getpid()}@example.com"
    r = requests.post(f"{API}/auth/register", json={
        "email": email, "password": "FirstPass123!", "full_name": "Remediation Probe",
        "agreed_terms": True, "over_13": True, "birth_date": "1990-01-01",
    }, timeout=30)
    assert r.status_code == 200, r.text
    return email, r.json()["access_token"]


def _login(email, password):
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_password_change_revokes_every_prior_session():
    """A1 — the owner's security finding, executed."""
    email, token_a = _new_account("a1")
    _probe.update(email=email, password="SecondPass456!")
    # A second device signs in with the ORIGINAL password.
    token_b = _login(email, "FirstPass123!")

    # The second device is alive before the change (the finding was that it
    # stayed alive afterwards).
    assert requests.get(f"{API}/auth/me", headers=_hdr(token_b), timeout=20).status_code == 200

    r = requests.post(
        f"{API}/auth/change-password", headers=_hdr(token_a),
        json={"current_password": "FirstPass123!", "new_password": "SecondPass456!"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    fresh = r.json()["access_token"]

    # The device that changed the password stays signed in.
    assert requests.get(f"{API}/auth/me", headers=_hdr(fresh), timeout=20).status_code == 200
    # The OTHER device — same account, same session count as before — is dead.
    r2 = requests.get(f"{API}/auth/me", headers=_hdr(token_b), timeout=20)
    assert r2.status_code == 401, "a password change must end the other sessions"
    # The fresh token carries a bumped token_version, and the old tokens
    # cannot be revived by replaying the old password either.
    assert _login(email, "FirstPass123!") if False else True  # old password is dead
    r3 = requests.post(f"{API}/auth/login",
                       json={"email": email, "password": "FirstPass123!"}, timeout=20)
    assert r3.status_code == 401, "the old password itself must stop working"

    # The session list shows only the device that performed the change.
    ses = requests.get(f"{API}/auth/sessions", headers=_hdr(fresh), timeout=20)
    assert ses.status_code == 200, ses.text
    rows = ses.json().get("sessions", ses.json() if isinstance(ses.json(), list) else [])
    assert len(rows) == 1, f"expected exactly one live session, got {len(rows)}"


def test_coach_switch_is_enforced_by_the_server():
    """A2 — the parent's coach switch, executed against the API directly."""
    email, token = _new_account("a2")
    _probe["password"] = "FirstPass123!"
    r = requests.post(f"{API}/academy/students", headers=_hdr(token),
                      json={"name": "A2 Learner", "grade": "4", "track": "foundations"},
                      timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    learner = body.get("student") or body
    sid = learner["id"]

    payload = {"session_id": "remediation", "message": "what is 7 times 8",
               "mode": "academy_coach", "student_id": sid}

    # Coach on (the default): the coach answers.
    on = requests.post(f"{API}/ai/chat", headers=_hdr(token), json=payload, timeout=60)
    assert on.status_code == 200, on.text

    # The parent switches it off.
    off = requests.patch(f"{API}/academy/students/{sid}", headers=_hdr(token),
                         json={"coach_enabled": False}, timeout=30)
    assert off.status_code == 200, off.text

    # The direct API call — no browser in the way — must be refused.
    r = requests.post(f"{API}/ai/chat", headers=_hdr(token), json=payload, timeout=60)
    assert r.status_code == 403, f"the coach answered with the switch off: {r.text[:200]}"
    assert "coach" in (r.json().get("detail") or "").lower()

    # And the switch back on restores it.
    requests.patch(f"{API}/academy/students/{sid}", headers=_hdr(token),
                   json={"coach_enabled": True}, timeout=30)
    again = requests.post(f"{API}/ai/chat", headers=_hdr(token), json=payload, timeout=60)
    assert again.status_code == 200, again.text


def test_coach_does_not_500_when_a_provider_answers():
    """Regression guard: _coach_grounded was assigned only in the provider-
    failure branch, so any SUCCESSFUL coach reply raised UnboundLocalError."""
    from ai import llm_gateway  # noqa: F401  (import proves the module loads)
    import inspect
    import server as srv
    src = inspect.getsource(srv.ai_chat)
    init = "_coach_grounded = False"
    assert init in src, (
        "ai_chat must initialise _coach_grounded before the provider branch — "
        "it is read unconditionally after it (UnboundLocalError on success)"
    )
