"""Regression tests for the BYOK → Creator Studio wiring.

The owner's report: "BYOK API is not linked to the Studio, nor is the site
API. No functions can work." Both halves were true, and both are pinned here.

  1. BYOK satisfies the Studio's paid-tier gates.
     `security/feature_control.py` had a BYOK carve-out for `ai_chat` only,
     and `studio.py::_video_access` had none — so a user who paid the $3 BYOK
     unlock (whose whole purpose is running AI on their OWN key at zero
     platform cost) was still answered "requires the Member plan".
  2. `byok_enabled` was never declared on server.User, so `extra="ignore"`
     dropped it on every request and no gate could ever see it. It was also
     absent from the own-profile visible field set, so the frontend
     (AppShell.jsx, MyProjects.jsx read `user.byok_enabled`) saw it as false
     and kept its Studio entry disabled.
  3. The Studio's voice function read `ELEVENLABS_API_KEY` from os.environ at
     IMPORT time only, and the gateway's DB-reload map had no `elevenlabs`
     entry — so a key pasted into the exec Provider Gateway was invisible to
     TTS forever. Voice now resolves at call time from the gateway global.
  4. `/studio/cheer` and `/arcade/chat` called call_llm WITHOUT `user_id`, so
     the gateway could not see the caller's key even when one existed.

Async tests use httpx.AsyncClient over ASGITransport so the app, the client,
and Motor all share one event loop.

Run:  cd backend && python -m pytest tests/test_studio_byok_wiring.py -v
"""
import inspect
import sys
import time
import uuid
from pathlib import Path

import httpx
import pytest
import pytest_asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server  # noqa: E402
from routers import studio as studio_router  # noqa: E402

# Motor binds its client to the loop that first uses it. Pin every async test
# in this module to ONE module-scoped loop, otherwise each function-scoped
# loop leaves the DB client attached to a closed loop.
pytestmark = pytest.mark.asyncio(loop_scope="module")


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def client():
    # One loop for the whole module: Motor binds its client to the loop that
    # first uses it, so a per-test loop leaves every later DB write raising
    # "Event loop is closed".
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _register(client):
    email = f"studio_byok_{int(time.time())}_{uuid.uuid4().hex[:6]}@example.com"
    r = await client.post("/api/auth/register", json={
        "email": email,
        "password": "StudioCheck#2026",
        "full_name": "Studio BYOK",
        "agreed_terms": True,
        "over_13": True,
    })
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def _user_id(client, token):
    me = await client.get("/api/auth/me", headers=_auth(token))
    return me.json()["id"]


async def _enable_byok(client, user_id):
    await server.db.users.update_one(
        {"id": user_id},
        {"$set": {"byok_enabled": True, "byok_activated_at": "2026-10-15"}})


# ── 1. BYOK satisfies the Studio gates ───────────────────────────────────────
async def test_byok_user_reaches_the_video_studio(client):
    token = await _register(client)
    await _enable_byok(client, await _user_id(client, token))
    # The gate used to answer 403 "Pro membership or staff access is required".
    r = await client.get("/api/video/projects", headers=_auth(token))
    assert r.status_code == 200, r.text


class _FakeUser:
    """Minimal user object for the feature gate (it only reads id/role/tier)."""
    def __init__(self, user_id, role="student", feature_tier="free", byok_enabled=False):
        self.id = user_id
        self.role = role
        self.feature_tier = feature_tier
        self.byok_enabled = byok_enabled


async def test_byok_satisfies_the_studio_feature_gate(client):
    """The feature-control tier gate used to answer "requires the Member plan"
    to a caller holding the $3 BYOK unlock."""
    from security.feature_control import check_user_feature_access
    token = await _register(client)
    uid = await _user_id(client, token)

    without = await check_user_feature_access(server.db, _FakeUser(uid), "/api/studio/lyric")
    assert without[0] == "block", without

    await _enable_byok(client, uid)
    with_byok = await check_user_feature_access(server.db, _FakeUser(uid, byok_enabled=True), "/api/studio/lyric")
    assert with_byok[0] == "pass", with_byok


async def test_free_user_is_still_gated(client):
    """BYOK grants access; it must not silently open the paywall for everyone."""
    token = await _register(client)
    r = await client.get("/api/video/projects", headers=_auth(token))
    assert r.status_code == 403, r.text
    from security.feature_control import check_user_feature_access
    uid = await _user_id(client, token)
    blocked = await check_user_feature_access(server.db, _FakeUser(uid), "/api/studio/lyric")
    assert blocked[0] == "block", blocked


def test_video_access_honours_byok_unit():
    """The gate function itself, without HTTP."""

    class _Byok:
        role = "student"
        feature_tier = "free"
        byok_enabled = True

    studio_router._video_access(_Byok())  # must not raise

    class _NoByok:
        role = "student"
        feature_tier = "free"
        byok_enabled = False

    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        studio_router._video_access(_NoByok())


# ── 2. The entitlement survives the request round-trip ───────────────────────
def test_user_model_carries_byok_fields():
    src = inspect.getsource(server.User)
    assert "byok_enabled" in src, (
        "byok_enabled must be declared on server.User or extra='ignore' drops "
        "it and every BYOK gate sees an un-entitled user")


def test_byok_is_visible_on_the_own_profile():
    from security.field_authorization import FieldAuthorization
    visible = FieldAuthorization.get_visible_fields("student", "student", True)
    assert "byok_enabled" in visible, (
        "the frontend reads user.byok_enabled off the auth user (AppShell.jsx, "
        "MyProjects.jsx); filtering it out keeps the Studio entry disabled")


async def test_byok_round_trips_through_auth_me(client):
    token = await _register(client)
    uid = await _user_id(client, token)
    await _enable_byok(client, uid)
    me = (await client.get("/api/auth/me", headers=_auth(token))).json()
    assert me.get("byok_enabled") is True, me


# ── 3. The site API reaches the Studio's voice function ──────────────────────
def test_gateway_maps_elevenlabs_provider_type():
    from ai.llm_gateway import _PROVIDER_TYPE_TO_GLOBAL
    assert _PROVIDER_TYPE_TO_GLOBAL.get("elevenlabs") == "ELEVENLABS_API_KEY", (
        "a key pasted into the exec Provider Gateway must land in the gateway "
        "global persona_tts reads, or the site API never reaches voice")


def test_gateway_declares_elevenlabs_key():
    import ai.llm_gateway as gw
    assert hasattr(gw, "ELEVENLABS_API_KEY"), (
        "persona_tts imports this name from the gateway; it must exist")


def test_persona_tts_reads_key_at_call_time():
    from ai import persona_tts
    src = inspect.getsource(persona_tts._elevenlabs_key)
    assert "llm_gateway" in src, (
        "the key must resolve from the gateway's DB-hydrated global at call time")
    assert "_elevenlabs_key()" in inspect.getsource(persona_tts._elevenlabs_call)


async def test_persona_tts_finds_a_gateway_hydrated_key():
    """A key loaded by reload_provider_keys() must reach the ElevenLabs call."""
    from ai import persona_tts
    import ai.llm_gateway as gw
    original = gw.ELEVENLABS_API_KEY
    try:
        gw.ELEVENLABS_API_KEY = "xi_test_key_from_vault"
        assert await persona_tts._elevenlabs_key() == "xi_test_key_from_vault"
    finally:
        gw.ELEVENLABS_API_KEY = original


# ── 4. The Studio passes the caller's identity to the gateway ────────────────
def test_studio_calls_pass_user_id():
    for fn_name in ("studio_cheer", "arcade_chat"):
        fn = getattr(studio_router, fn_name, None)
        assert fn is not None, fn_name
        src = inspect.getsource(fn)
        assert "user_id=" in src, (
            f"{fn_name} must pass user_id so the gateway can route the "
            "caller's BYOK / site key")


def test_arcade_chat_accepts_authorization():
    """Optional auth: playable anonymously, routed for a signed-in caller."""
    assert "authorization" in inspect.signature(studio_router.arcade_chat).parameters
