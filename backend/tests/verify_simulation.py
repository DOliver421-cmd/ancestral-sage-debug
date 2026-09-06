#!/usr/bin/env python3
"""Standalone verification for simulation system (no pytest required)."""
import os
import sys
import asyncio
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "testsecret")

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import routers.simulation as sim_router
from simulation import (
    SimulationEngine, SimulationProfile, SimulationRun, SimulationEvent,
    STUDENT_PROFILES, INSTRUCTOR_PROFILES, SCENARIOS,
    _now, _flatten_lessons, _score_attempt, _simulate_answers,
    reset_engine, get_engine,
)


class FakeDB:
    def __init__(self):
        self.collections = {}

    def __getattr__(self, name):
        if name not in self.collections:
            self.collections[name] = _FakeCollection()
        return self.collections[name]


class _FakeCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def _match(self, doc, q):
        for k, v in q.items():
            val = doc.get(k)
            if isinstance(v, dict) and "$in" in v:
                if isinstance(val, list):
                    if not any(item in v["$in"] for item in val):
                        return False
                elif val not in v["$in"]:
                    return False
            elif isinstance(val, list) and not isinstance(v, (dict, list)):
                if v not in val:
                    return False
            elif val != v:
                return False
        return True

    def find(self, q=None, proj=None, **kw):
        q = q or {}
        matched = [d for d in self.docs if self._match(d, q)]
        class _Cursor:
            def __init__(self, docs, projection):
                self.docs = docs
                self.proj = projection
            def sort(self, *a, **k):
                return self
            async def to_list(self, n=None):
                out = [self._project(d, self.proj) for d in self.docs]
                return out[:n] if n else out
            @staticmethod
            def _project(d, proj):
                if not proj:
                    return {k: v for k, v in d.items() if k != "_id"}
                includes = [k for k, v in proj.items() if v]
                excludes = [k for k, v in proj.items() if not v]
                if includes:
                    return {k: d.get(k) for k in includes}
                if excludes:
                    return {k: v for k, v in d.items() if k not in excludes}
                return {k: v for k, v in d.items() if k != "_id"}
        return _Cursor(matched, proj)

    async def find_one(self, q, proj=None, **kw):
        for d in self.docs:
            if self._match(d, q):
                if proj is None:
                    return {k: v for k, v in d.items() if k != "_id"}
                includes = [k for k, v in proj.items() if v]
                excludes = [k for k, v in proj.items() if not v]
                if includes:
                    return {k: d.get(k) for k in includes}
                if excludes:
                    return {k: v for k, v in d.items() if k not in excludes}
                return {k: v for k, v in d.items() if k != "_id"}
        return None

    async def insert_one(self, doc):
        self.docs.append(dict(doc))
        return SimpleNamespace(inserted_id="x")

    async def update_one(self, q, update, upsert=False):
        target = next((d for d in self.docs if self._match(d, q)), None)
        if target is None:
            if not upsert:
                return SimpleNamespace(matched_count=0, modified_count=0)
            target = {}
            for key in ("id", "student_id", "course_slug", "lesson_slug", "parent_user_id", "slug", "run_id", "simulated_user_id"):
                if key in q:
                    target[key] = q[key]
            self.docs.append(target)
        for op, fields in (update or {}).items():
            if op == "$set":
                target.update(fields)
            elif op == "$push":
                for k, v in fields.items():
                    target.setdefault(k, [])
                    if isinstance(v, dict) and "$each" in v:
                        target[k].extend(v["$each"])
                    else:
                        target[k].append(v)
            elif op == "$setOnInsert":
                for k, v in fields.items():
                    target.setdefault(k, v)
        return SimpleNamespace(matched_count=1, modified_count=1)

    async def count_documents(self, q):
        return sum(1 for d in self.docs if self._match(d, q))


async def _fake_current_user(authorization=None):
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    return SimpleNamespace(id="admin-1", email="admin@test.com", full_name="Admin", role="admin", feature_tier="free")


def test_profiles():
    db = FakeDB()
    reset_engine()
    sim_router.bind(db, _fake_current_user, None, None)
    app = FastAPI()
    sim_router.get_engine(db, app)
    app.include_router(sim_router.router, prefix="/api")
    client = TestClient(app)

    r = client.get("/api/simulation/profiles", headers={"Authorization": "Bearer t"})
    assert r.status_code == 200
    assert r.json()["profiles"] == []

    r = client.post("/api/simulation/profiles", headers={"Authorization": "Bearer t"}, json={
        "name": "Test", "type": "student", "profile_key": "test", "description": "", "behavior_config": {}
    })
    assert r.status_code == 200
    assert r.json()["profile"]["is_simulation"] is True

    pid = r.json()["profile"]["id"]
    r2 = client.get(f"/api/simulation/profiles/{pid}", headers={"Authorization": "Bearer t"})
    assert r2.status_code == 200
    assert r2.json()["profile"]["name"] == "Test"

    r3 = client.get("/api/simulation/profiles/missing", headers={"Authorization": "Bearer t"})
    assert r3.status_code == 404
    print("PASS: test_profiles")


def test_scenarios():
    db = FakeDB()
    reset_engine()
    sim_router.bind(db, _fake_current_user, None, None)
    app = FastAPI()
    sim_router.get_engine(db, app)
    app.include_router(sim_router.router, prefix="/api")
    client = TestClient(app)

    r = client.get("/api/simulation/scenarios", headers={"Authorization": "Bearer t"})
    assert r.status_code == 200
    data = r.json()["scenarios"]
    ids = [s["id"] for s in data]
    for expected in ["baseline", "struggling_algebra", "disengagement", "improvement", "instructor_overload"]:
        assert expected in ids, f"Missing scenario: {expected}"
    print("PASS: test_scenarios")


def test_runs():
    db = FakeDB()
    reset_engine()
    sim_router.bind(db, _fake_current_user, None, None)
    app = FastAPI()
    sim_router.get_engine(db, app)
    app.include_router(sim_router.router, prefix="/api")
    client = TestClient(app)

    r = client.post("/api/simulation/runs", headers={"Authorization": "Bearer t"}, json={
        "name": "Test Run", "description": "", "scenario_id": "baseline",
        "profile_ids": ["high_performing_student"],
        "course_slugs": ["multiplication-division-fractions-grade-4"],
        "config": {},
    })
    assert r.status_code == 200
    assert r.json()["run"]["status"] == "draft"
    rid = r.json()["run"]["id"]

    r2 = client.get("/api/simulation/runs", headers={"Authorization": "Bearer t"})
    assert r2.status_code == 200
    assert len(r2.json()["runs"]) >= 1

    r3 = client.get(f"/api/simulation/runs/{rid}", headers={"Authorization": "Bearer t"})
    assert r3.status_code == 200
    assert r3.json()["run"]["name"] == "Test Run"

    r4 = client.get("/api/simulation/runs/missing", headers={"Authorization": "Bearer t"})
    assert r4.status_code == 404
    print("PASS: test_runs")


def test_events():
    db = FakeDB()
    reset_engine()
    sim_router.bind(db, _fake_current_user, None, None)
    app = FastAPI()
    sim_router.get_engine(db, app)
    app.include_router(sim_router.router, prefix="/api")
    client = TestClient(app)

    r = client.post("/api/simulation/runs", headers={"Authorization": "Bearer t"}, json={
        "name": "Event Run", "description": "", "scenario_id": "baseline",
        "profile_ids": ["high_performing_student"],
        "course_slugs": ["multiplication-division-fractions-grade-4"],
        "config": {},
    })
    rid = r.json()["run"]["id"]
    db.simulation_events.docs.append({
        "id": "evt-1", "run_id": rid, "simulated_user_id": "u1",
        "event_type": "lesson_start", "target_type": "lesson", "target_id": "l1",
        "metadata": {}, "is_simulation": True, "created_at": _now(),
    })

    r2 = client.get(f"/api/simulation/runs/{rid}/events", headers={"Authorization": "Bearer t"})
    assert r2.status_code == 200
    assert len(r2.json()["events"]) == 1

    r3 = client.get(f"/api/simulation/runs/{rid}/events?event_type=lesson_start", headers={"Authorization": "Bearer t"})
    assert r3.status_code == 200
    assert len(r3.json()["events"]) == 1
    print("PASS: test_events")


def test_analytics():
    db = FakeDB()
    reset_engine()
    sim_router.bind(db, _fake_current_user, None, None)
    app = FastAPI()
    sim_router.get_engine(db, app)
    app.include_router(sim_router.router, prefix="/api")
    client = TestClient(app)

    r = client.post("/api/simulation/runs", headers={"Authorization": "Bearer t"}, json={
        "name": "Analytics Run", "description": "", "scenario_id": "baseline",
        "profile_ids": ["high_performing_student"],
        "course_slugs": ["multiplication-division-fractions-grade-4"],
        "config": {},
    })
    rid = r.json()["run"]["id"]
    for etype in ["lesson_start", "assessment_pass", "assessment_fail", "lesson_complete", "dashboard_view"]:
        db.simulation_events.docs.append({
            "id": f"evt-{etype}", "run_id": rid, "simulated_user_id": "u1",
            "event_type": etype, "target_type": "lesson", "target_id": "l1",
            "metadata": {}, "is_simulation": True, "created_at": _now(),
        })

    r2 = client.get(f"/api/simulation/runs/{rid}/analytics", headers={"Authorization": "Bearer t"})
    assert r2.status_code == 200
    a = r2.json()["analytics"]
    assert a["total_events"] == 5
    assert a["by_event_type"]["assessment_pass"] == 1
    assert a["by_event_type"]["lesson_complete"] == 1

    r3 = client.get("/api/simulation/analytics/comparison", headers={"Authorization": "Bearer t"})
    assert r3.status_code == 200
    assert "real_events" in r3.json()["analytics"]
    print("PASS: test_analytics")


def test_engine_unit():
    course = {
        "units": [
            {"slug": "u1", "title": "Unit 1", "order": 1, "lessons": [
                {"slug": "l2", "title": "L2", "order": 2},
                {"slug": "l1", "title": "L1", "order": 1},
            ]},
            {"slug": "u2", "title": "Unit 2", "order": 2, "lessons": [
                {"slug": "l3", "title": "L3", "order": 1},
            ]},
        ]
    }
    lessons = _flatten_lessons(course)
    assert [l["slug"] for l in lessons] == ["l2", "l1", "l3"]

    lesson = {
        "slug": "l1",
        "check": {
            "questions": [
                {"q": "Q1", "options": ["a", "b", "c"], "answer": "a", "explain": "e1"},
                {"q": "Q2", "options": ["x", "y", "z"], "answer": "y", "explain": "e2"},
            ]
        },
    }
    result = _score_attempt(lesson, [0, 1], 80)
    assert result["score"] == 100.0
    assert result["passed"] is True

    result = _score_attempt(lesson, [1, 0], 80)
    assert result["score"] == 0.0
    assert result["passed"] is False

    questions = [
        {"q": "Q1", "options": ["a", "b", "c"], "answer": "a", "explain": "e1"},
        {"q": "Q2", "options": ["x", "y"], "answer": "y", "explain": "e2"},
    ]
    assert _simulate_answers(questions, 1.0) == [0, 1]

    assert "high_performing_student" in STUDENT_PROFILES
    assert "typical_student" in STUDENT_PROFILES
    assert "struggling_student" in STUDENT_PROFILES
    assert "inconsistent_student" in STUDENT_PROFILES
    assert "active_instructor" in INSTRUCTOR_PROFILES
    assert "normal_instructor" in INSTRUCTOR_PROFILES
    assert "overloaded_instructor" in INSTRUCTOR_PROFILES
    print("PASS: test_engine_unit")


def test_isolation():
    profile = SimulationProfile(id="p1", name="Test", type="student", profile_key="test", description="", behavior_config={}, created_at=_now())
    assert profile.to_doc()["is_simulation"] is True

    event = SimulationEvent(id="e1", run_id="r1", simulated_user_id="u1", event_type="start", target_type="lesson", target_id="l1", metadata={}, created_at=_now())
    assert event.to_doc()["is_simulation"] is True

    run = SimulationRun(id="r1", name="T", description="", scenario_id="baseline", profile_ids=[], course_slugs=[], config={}, created_by="a", created_at=_now())
    assert run.status == "draft"
    print("PASS: test_isolation")


if __name__ == "__main__":
    test_profiles()
    test_scenarios()
    test_runs()
    test_events()
    test_analytics()
    test_engine_unit()
    test_isolation()
    print("\nAll simulation verification tests passed.")
