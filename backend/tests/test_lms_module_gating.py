"""Regression test for LMS module gating (Phase: course content is never public).

GET  /api/modules         → public catalog cards, metadata only (no lesson content)
GET  /api/modules/{slug}  → 401 anonymous · 200 with auth, full lesson content
"""
import asyncio
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import routers.lms as lms


class _FakeCollection:
    def __init__(self, docs):
        self.docs = docs

    def find(self, q, proj=None, **kw):
        return self

    def sort(self, *a, **k):
        return self

    async def to_list(self, n):
        return list(self.docs)

    async def find_one(self, q, proj=None, **kw):
        slug = q.get("slug")
        return next((d for d in self.docs if d.get("slug") == slug), None)

    async def insert_one(self, d):
        return SimpleNamespace(inserted_id="x")

    async def update_one(self, *a, **k):
        return SimpleNamespace(matched_count=1, modified_count=1)


MODULE_DOC = {
    "id": "m1", "order": 1, "slug": "electrical-safety",
    "title": "Electrical Safety", "summary": "Lockout/tagout basics",
    "objectives": ["Understand LOTO"], "safety": ["Wear PPE"],
    "tools": ["Multimeter"], "scripture": {"text": "x", "ref": "y"},
    "tasks": ["Task 1"], "competencies": ["safety"], "hours": 8,
    "quiz": [{"question": "Q", "options": ["A", "B"], "answer": 0}],
    "free": True, "video_url": None, "diagram_url": None,
}


def _fake_db():
    return SimpleNamespace(modules=_FakeCollection([MODULE_DOC]))


async def _fake_current_user(authorization=None):
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    return SimpleNamespace(id="u1", email="a@b.c", full_name="A", role="student", feature_tier="free")


@pytest.fixture(scope="module")
def client():
    lms.bind(_fake_db(), _fake_current_user, lambda *a, **k: None, lambda *a, **k: None, lambda *a, **k: None)
    app = FastAPI()
    app.include_router(lms.router, prefix="/api")
    return TestClient(app)


def test_public_catalog_is_metadata_only(client):
    r = client.get("/api/modules")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1 and body[0]["slug"] == "electrical-safety"
    # Lesson content must never leak into the public catalog
    for field in ("objectives", "safety", "tools", "scripture", "quiz"):
        assert field not in body[0], f"lesson field '{field}' leaked into public catalog"


def test_module_detail_requires_auth(client):
    r = client.get("/api/modules/electrical-safety")
    assert r.status_code == 401


def test_module_detail_served_to_authenticated_user(client):
    r = client.get("/api/modules/electrical-safety", headers={"Authorization": "Bearer x"})
    assert r.status_code == 200
    m = r.json()
    assert m["objectives"] and m["quiz"] and m["scripture"] and m["safety"]


def test_module_detail_unknown_slug_404(client):
    r = client.get("/api/modules/nope", headers={"Authorization": "Bearer x"})
    assert r.status_code == 404
