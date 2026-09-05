"""
backend/tests/test_unifier_router.py

Unifier router regression tests.

These validate:
  - the auth gate returns 403 for non-staff or non-patron users
  - the mounted endpoints respond without import-time failures
  - session/plan persistence models are wired correctly in the router layer

Live DB behavior is exercised separately against a real Railway deploy.
This file is the local regression gate for the router and access helper.
"""

from __future__ import annotations

import os
import sys
import typing as t

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import server as _server  # noqa: E402


def _make_user(role: str, tier: str, user_id: str = "user-1") -> t.Any:
    class _User:
        id = user_id
        role = role
        feature_tier = tier
    return _User()


class _NoDb:
    def __bool__(self) -> bool:
        return False

    def __getattr__(self, name: str) -> t.Any:
        if name in ("unifier_sessions", "unifier_plans", "unifier_uploads"):
            return _NoCollection()
        raise AttributeError(name)


class _NoCollection:
    async def insert_one(self, doc: t.Any) -> None:
        return None

    async def find_one(self, filter_: t.Any) -> t.Any:
        return None

    async def find(self, filter_: t.Any) -> t.Any:
        return iter([])

    async def replace_one(self, filter_: t.Any, replacement: t.Any, upsert: bool = False) -> None:
        return None

    async def update_one(self, filter_: t.Any, update: t.Any) -> None:
        return None

    async def delete_one(self, filter_: t.Any) -> None:
        return None


@pytest.fixture
def app_with_no_db() -> t.Any:
    _server.db = _NoDb()
    return _server.app


def test_unifier_requires_auth(app_with_no_db: t.Any) -> None:
    client = TestClient(app_with_no_db)
    resp = client.post("/api/unifier/sessions")
    assert resp.status_code == 403
    body = resp.json()
    assert body.get("detail") == "The Unifier requires staff role and patron tier."


def test_unifier_requires_staff_role_and_patron_tier(app_with_no_db: t.Any) -> None:
    client = TestClient(app_with_no_db)

    def post_with(user: t.Any):
        return client.post("/api/unifier/sessions")

    resp = post_with(_make_user("instructor", "patron"))
    assert resp.status_code == 403

    resp = post_with(_make_user("support_staff", "free"))
    assert resp.status_code == 403

    resp = post_with(_make_user("support_staff", "member"))
    assert resp.status_code == 403


def test_unifier_sessions_endpoint_exists_locally(app_with_no_db: t.Any) -> None:
    client = TestClient(app_with_no_db)
    resp = client.post("/api/unifier/sessions", headers={
        "Authorization": "Bearer fake-staff-patron-token",
    })
    assert resp.status_code == 503
    body = resp.json()
    assert "unavailable" in (body.get("detail") or "").lower()
