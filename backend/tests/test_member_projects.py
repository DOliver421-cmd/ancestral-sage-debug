"""
Tests for the member-facing projects router (routers/member_projects.py).
Covers the auth/tier gate, the per-member daily AI-run cap, and project caps.
All tests use mocks — no live APIs or DB needed.
"""
import sys
import os
import jwt as pyjwt
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from bson import ObjectId

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from routers import member_projects as mp  # noqa: E402

SECRET = "test-secret"

# The router resolves the JWT secret from the canonical server module
# (server.JWT_SECRET, read from the environment at import).  Force the
# environment to match the signing literal BEFORE server.py is first
# imported by the dependency under test, so the suite exercises the real
# production contract instead of a private app.state secret.
os.environ["JWT_SECRET"] = SECRET


@pytest.fixture(autouse=True)
def _restore_shared_db():
    """Isolate the deps-injected shared db across tests."""
    import deps

    before = deps.get_db()
    yield
    deps.set_db(before)


def _bind_shared_db(db):
    """Point the router's canonical shared-db source at a test fake."""
    import deps

    deps.set_db(db)


def _fake_request(db=None, user_doc=None):
    """Minimal Request stand-in exposing app.state.db + jwt_secret."""
    req = MagicMock()
    req.app.state.jwt_secret = SECRET
    req.app.state.db = db or MagicMock()
    if user_doc is not None:
        req.app.state.db.users.find_one = AsyncMock(return_value=user_doc)
    return req


def _token(user_id="u-123", role="student", tier="member"):
    exp = datetime.now(timezone.utc) + timedelta(hours=1)
    return pyjwt.encode({"sub": user_id, "role": role, "exp": exp}, SECRET, algorithm="HS256")


def _user_doc(user_id="u-123", role="student", tier="member", is_active=True):
    return {
        "id": user_id,
        "role": role,
        "feature_tier": tier,
        "full_name": "Test Member",
        "is_active": is_active,
    }


@pytest.mark.asyncio
async def test_require_member_rejects_missing_token():
    dep = mp._require_member()
    req = _fake_request()
    with pytest.raises(Exception) as exc:
        await dep(req, authorization=None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_require_member_rejects_free_tier():
    dep = mp._require_member()
    req = _fake_request(user_doc=_user_doc(tier="free"))
    _bind_shared_db(req.app.state.db)
    with pytest.raises(Exception) as exc:
        await dep(req, authorization=f"Bearer {_token(tier='free')}")
    assert exc.value.status_code == 403
    assert "Member access required" in exc.value.detail


@pytest.mark.asyncio
async def test_require_member_allows_member_tier():
    dep = mp._require_member()
    req = _fake_request(user_doc=_user_doc(tier="member"))
    _bind_shared_db(req.app.state.db)
    user = await dep(req, authorization=f"Bearer {_token(tier='member')}")
    assert user.id == "u-123"
    assert user.tier == "member"


@pytest.mark.asyncio
async def test_require_member_allows_staff_regardless_of_tier():
    dep = mp._require_member()
    req = _fake_request(user_doc=_user_doc(role="admin", tier="free"))
    _bind_shared_db(req.app.state.db)
    user = await dep(req, authorization=f"Bearer {_token(role='admin', tier='free')}")
    assert user.id == "u-123"
    assert user.is_staff is True


@pytest.mark.asyncio
async def test_require_member_rejects_deactivated_account():
    dep = mp._require_member()
    req = _fake_request(user_doc=_user_doc(is_active=False))
    _bind_shared_db(req.app.state.db)
    with pytest.raises(Exception) as exc:
        await dep(req, authorization=f"Bearer {_token()}")
    assert exc.value.status_code == 403


def test_daily_run_limit_default():
    assert mp._daily_run_limit() == mp.MEMBER_PROJECT_DAILY_RUNS


@pytest.mark.asyncio
async def test_daily_runs_left_counts_only_todays_auto_runs():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    projects = [
        {
            "deliverables": [
                {"metadata": {"auto": True}, "submitted_at": f"{today}T10:00:00+00:00"},
                {"metadata": {"auto": True}, "submitted_at": f"{today}T11:00:00+00:00"},
                # manual member entry should not count against the AI cap
                {"metadata": {"auto": False}, "submitted_at": f"{today}T12:00:00+00:00"},
                # yesterday's auto run should not count
                {"metadata": {"auto": True}, "submitted_at": f"{yesterday}T10:00:00+00:00"},
            ]
        }
    ]
    db = MagicMock()
    db.member_projects.find = MagicMock(return_value=MagicMock(to_list=AsyncMock(return_value=projects)))
    user = mp.MemberUser(id="u-123", role="student", tier="member", full_name="Test")
    left = await mp._daily_runs_left(db, user)
    assert left == mp._daily_run_limit() - 2


@pytest.mark.asyncio
async def test_run_stage_blocked_without_byok():
    """Member without BYOK cannot run AI — gets 403, not platform tokens."""
    db = MagicMock()
    project_doc = {
        "_id": ObjectId(),
        "owner_id": "u-123",
        "current_stage": "execute",
        "status": "active",
        "context": {"brief": "test"},
        "deliverables": [],
        "packet": {"ai_team": ["Production"]},
    }
    db.member_projects.find_one = AsyncMock(return_value=project_doc)
    db.member_projects.find = MagicMock(return_value=MagicMock(to_list=AsyncMock(return_value=[]) ))
    user = mp.MemberUser(id="u-123", role="student", tier="member", full_name="Test")
    body = mp.StageRun(persona="Production", instructions="")
    req = _fake_request(db=db)
    _bind_shared_db(db)
    # Mock byok.resolve_byok to return None (user has no BYOK key)
    with patch("byok.resolve_byok", new_callable=AsyncMock, return_value=None):
        with pytest.raises(Exception) as exc:
            await mp.run_stage(
                project_id=str(project_doc["_id"]),
                body=body,
                user=user,
                request=req,
            )
        assert exc.value.status_code == 403
        assert "BYOK" in exc.value.detail


@pytest.mark.asyncio
async def test_create_project_enforces_active_cap():
    db = MagicMock()
    db.member_projects.count_documents = AsyncMock(return_value=mp.MAX_ACTIVE_PROJECTS)
    user = mp.MemberUser(id="u-123", role="student", tier="member", full_name="Test")
    body = mp.MemberProjectCreate(
        title="Launch my podcast",
        brief="A 10-episode launch plan for a community podcast.",
        category="launch",
    )
    req = _fake_request(db=db)
    _bind_shared_db(db)
    with pytest.raises(Exception) as exc:
        await mp.create_project(body, user=user, request=req)
    assert exc.value.status_code == 403
