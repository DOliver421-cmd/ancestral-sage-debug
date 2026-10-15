"""Regression tests for the server.py half of the launch repairs.

Each test below pins a behaviour that was broken and is now working, so the
defect cannot silently return:

  1. PATCH /auth/me persists avatar_url (it used to be dropped by the
     request model while the UI reported success), rejects a javascript:
     avatar URL, and still refuses self-service role changes.
  2. DELETE /auth/sessions hands back a fresh token so the caller stays
     signed in (it used to bump token_version and sign the caller out).
  3. The commerce routes that used to 404 are registered at the exact paths
     the frontend calls: GET /api/digital/purchases,
     GET /api/digital/{key}/download, POST /api/payments/gumroad-webhook.

The router-level repairs (transcript mastery, seed hash, ascension
protocols, scholarship reconciliation, and the own-profile visible-field set
that lets social_handles read back through /auth/me) are pinned in
tests/test_launch_repairs.py, which ships with that change.

Runs with only a reachable Mongo — no live server process.
Run:  cd backend && python -m pytest tests/test_launch_repairs_server.py -v
"""
import sys
import time
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(server.app) as c:
        yield c


def _register(client):
    email = f"launch_regress_{int(time.time())}_{uuid.uuid4().hex[:6]}@example.com"
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": "LaunchCheck#2026",
        "full_name": "Launch Regression",
        "agreed_terms": True,
        "over_13": True,
    })
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _registered_paths():
    """Every path the running app can serve.

    app.routes holds _IncludedRouter wrappers, so walk each wrapper's
    original_router (an APIRouter) as well as api_router itself; a path is
    only "registered" if a real APIRoute serves it.
    """
    paths = set()

    def _walk(routes):
        for r in routes:
            p = getattr(r, "path", "")
            if p and type(r).__name__ == "APIRoute":
                paths.add(p)
            original = getattr(r, "original_router", None)
            if original is not None and hasattr(original, "routes"):
                _walk(original.routes)

    _walk(server.app.routes)
    _walk(server.api_router.routes)
    return paths


# ── 1. Profile edits persist ─────────────────────────────────────────────────
def test_patch_me_persists_avatar(client):
    token = _register(client)
    avatar = ("data:image/png;base64,"
              "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
    r = client.patch("/api/auth/me", headers=_auth(token), json={"avatar_url": avatar})
    assert r.status_code == 200, r.text
    me = client.get("/api/auth/me", headers=_auth(token)).json()
    assert me.get("avatar_url") == avatar, me


def test_patch_me_accepts_social_handles(client):
    """The write must be accepted.

    Reading social_handles BACK through /auth/me additionally needs the
    own-profile visible-field set, which ships with the companion routers
    PR and is asserted by its own suite.
    """
    token = _register(client)
    r = client.patch("/api/auth/me", headers=_auth(token),
                     json={"social_handles": {"twitter": "mhc_regress"}})
    assert r.status_code == 200, r.text


def test_patch_me_refuses_self_role_change(client):
    token = _register(client)
    r = client.patch("/api/auth/me", headers=_auth(token), json={"role": "executive_admin"})
    assert r.status_code == 200  # the field is ignored, never honoured
    me = client.get("/api/auth/me", headers=_auth(token)).json()
    assert me.get("role") == "student"


def test_patch_me_rejects_javascript_avatar(client):
    token = _register(client)
    r = client.patch("/api/auth/me", headers=_auth(token),
                     json={"avatar_url": "javascript:alert(1)"})
    assert r.status_code == 400, r.text


# ── 2. Session revocation keeps the caller signed in ─────────────────────────
def test_revoke_all_sessions_returns_fresh_token(client):
    token = _register(client)
    r = client.delete("/api/auth/sessions", headers=_auth(token))
    assert r.status_code == 200, r.text
    fresh = r.json().get("access_token")
    assert fresh, "revoke-all must re-issue the caller's token"
    me = client.get("/api/auth/me", headers=_auth(fresh))
    assert me.status_code == 200, me.text
    old = client.get("/api/auth/me", headers=_auth(token))
    assert old.status_code == 401  # the pre-revocation token is dead


def test_revoke_all_fresh_token_session_id_is_new(client):
    """The re-issued token must carry a session row that actually exists.

    The first cut fell back to the caller's OLD session_id when the session
    re-record failed — but that row had just been deleted, so the new token
    pointed at a session that no longer existed. On the happy path the new
    session id must differ from the old one."""
    import jwt as _jwt
    import server as _srv
    token = _register(client)
    old_sid = _jwt.decode(token, _srv.JWT_SECRET, algorithms=[_srv.JWT_ALGO]).get("session_id")
    r = client.delete("/api/auth/sessions", headers=_auth(token))
    assert r.status_code == 200, r.text
    new_sid = _jwt.decode(r.json()["access_token"], _srv.JWT_SECRET,
                          algorithms=[_srv.JWT_ALGO]).get("session_id")
    assert new_sid and new_sid != old_sid, (old_sid, new_sid)
    # ...and that session row is really in the database.
    rows = [s for s in client.get("/api/auth/sessions",
                                  headers=_auth(r.json()["access_token"])).json()["sessions"]
            if s["session_id"] == new_sid]
    assert rows, "the re-issued token's session must exist"


def test_revoke_all_sessions_is_rate_limited(client):
    """A high-impact operation: 6th call inside the window is 429, not 200."""
    token = _register(client)
    statuses = []
    for _ in range(6):
        r = client.delete("/api/auth/sessions", headers=_auth(token))
        statuses.append(r.status_code)
        if r.status_code == 200 and r.json().get("access_token"):
            token = r.json()["access_token"]  # stay authenticated across calls
    assert 429 in statuses, statuses


def test_empty_avatar_url_clears_rather_than_silently_storing(client):
    token = _register(client)
    avatar = ("data:image/png;base64,"
              "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
    r = client.patch("/api/auth/me", headers=_auth(token), json={"avatar_url": avatar})
    assert r.status_code == 200, r.text
    r = client.patch("/api/auth/me", headers=_auth(token), json={"avatar_url": ""})
    assert r.status_code == 200, r.text
    me = client.get("/api/auth/me", headers=_auth(token)).json()
    assert me.get("avatar_url") in (None, ""), me


def test_digital_routes_are_rate_limited(client):
    """The new commerce routes must 429 rather than hammer the DB."""
    token = _register(client)
    statuses = [client.get("/api/digital/purchases", headers=_auth(token)).status_code
                for _ in range(65)]
    assert 429 in statuses, statuses[-3:]


def test_password_change_returns_fresh_token(client):
    """The contract revoke-all now follows: change-password re-issues."""
    token = _register(client)
    r = client.post("/api/auth/change-password", headers=_auth(token),
                    json={"current_password": "LaunchCheck#2026",
                          "new_password": "LaunchCheck#2027"})
    assert r.status_code == 200, r.text
    fresh = r.json().get("access_token")
    assert fresh, "change-password must re-issue the caller's token"
    me = client.get("/api/auth/me", headers=_auth(fresh))
    assert me.status_code == 200, me.text


# ── 3. Commerce routes the frontend calls are registered ────────────────────
def test_digital_purchase_routes_registered():
    paths = _registered_paths()
    digital = sorted(p for p in paths if "digital" in p)
    assert any(p.endswith("/digital/purchases") for p in paths), digital
    assert any("/digital/" in p and "download" in p for p in paths), digital


def test_gumroad_webhook_registered():
    paths = _registered_paths()
    assert any(p.endswith("/payments/gumroad-webhook") for p in paths), \
        sorted(p for p in paths if "gumroad" in p)
