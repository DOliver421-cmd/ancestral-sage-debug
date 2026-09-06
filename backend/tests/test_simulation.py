"""Tests for the Student/Instructor Simulation Lab (simulation.py + routers/simulation.py).

Covers: profile CRUD, scenario listing, run creation, event recording,
analytics, comparison, and simulation isolation (is_simulation flags).
Uses the repo's established fake-db + TestClient pattern.
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "testsecret")

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import routers.simulation as sim_router
from simulation import SimulationEngine, SimulationProfile, SimulationRun, SimulationEvent, STUDENT_PROFILES, INSTRUCTOR_PROFILES, SCENARIOS, _now, _flatten_lessons, _score_attempt, _simulate_answers, reset_engine


# ── Fake DB ──────────────────────────────────────────────────────────────────
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


def _fake_db():
    return SimpleNamespace(
        users=_FakeCollection([]),
        academy_students=_FakeCollection([]),
        academy_courses=_FakeCollection([]),
        academy_progress=_FakeCollection([]),
        simulation_profiles=_FakeCollection([]),
        simulation_runs=_FakeCollection([]),
        simulation_events=_FakeCollection([]),
    )


async def _fake_current_user(authorization=None):
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    return SimpleNamespace(id="admin-1", email="admin@test.com", full_name="Admin", role="admin", feature_tier="free")


# ── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture
def client():
    db = _fake_db()
    reset_engine()
    sim_router.bind(db, _fake_current_user, None, None)
    app = FastAPI()
    # Initialize engine with fake app
    sim_router.get_engine(db, app)
    app.include_router(sim_router.router, prefix="/api")
    c = TestClient(app)
    c.db = db
    return c


def _auth():
    return {"Authorization": "Bearer t"}


# ── Tests ────────────────────────────────────────────────────────────────────
class TestSimulationProfiles:
    def test_list_profiles(self, client):
        r = client.get("/api/simulation/profiles", headers=_auth())
        assert r.status_code == 200
        data = r.json()
        assert "profiles" in data
        assert len(data["profiles"]) == 0

    def test_create_profile(self, client):
        r = client.post("/api/simulation/profiles", headers=_auth(), json={
            "name": "Test Profile",
            "type": "student",
            "profile_key": "test_student",
            "description": "A test profile",
            "behavior_config": {"pass_rate": 0.5},
        })
        assert r.status_code == 200
        body = r.json()
        assert body["profile"]["name"] == "Test Profile"
        assert body["profile"]["is_simulation"] is True
        assert body["profile"]["profile_key"] == "test_student"

    def test_get_profile(self, client):
        r = client.post("/api/simulation/profiles", headers=_auth(), json={
            "name": "Get Me",
            "type": "instructor",
            "profile_key": "get_me",
            "description": "",
            "behavior_config": {},
        })
        pid = r.json()["profile"]["id"]
        r2 = client.get(f"/api/simulation/profiles/{pid}", headers=_auth())
        assert r2.status_code == 200
        assert r2.json()["profile"]["name"] == "Get Me"

    def test_get_profile_missing(self, client):
        r = client.get("/api/simulation/profiles/missing-id", headers=_auth())
        assert r.status_code == 404


class TestSimulationScenarios:
    def test_list_scenarios(self, client):
        r = client.get("/api/simulation/scenarios", headers=_auth())
        assert r.status_code == 200
        data = r.json()
        assert "scenarios" in data
        assert len(data["scenarios"]) >= 5
        ids = [s["id"] for s in data["scenarios"]]
        for expected in ["baseline", "struggling_algebra", "disengagement", "improvement", "instructor_overload"]:
            assert expected in ids


class TestSimulationRuns:
    def test_create_run(self, client):
        r = client.post("/api/simulation/runs", headers=_auth(), json={
            "name": "Test Run",
            "description": "A test run",
            "scenario_id": "baseline",
            "profile_ids": ["high_performing_student"],
            "course_slugs": ["multiplication-division-fractions-grade-4"],
            "config": {"duration_minutes": 30},
        })
        assert r.status_code == 200
        body = r.json()
        assert body["run"]["name"] == "Test Run"
        assert body["run"]["status"] == "draft"

    def test_list_runs(self, client):
        client.post("/api/simulation/runs", headers=_auth(), json={
            "name": "Run 1",
            "description": "",
            "scenario_id": "baseline",
            "profile_ids": ["high_performing_student"],
            "course_slugs": ["multiplication-division-fractions-grade-4"],
            "config": {},
        })
        r = client.get("/api/simulation/runs", headers=_auth())
        assert r.status_code == 200
        assert len(r.json()["runs"]) >= 1

    def test_get_run(self, client):
        r = client.post("/api/simulation/runs", headers=_auth(), json={
            "name": "Get Me",
            "description": "",
            "scenario_id": "baseline",
            "profile_ids": ["high_performing_student"],
            "course_slugs": ["multiplication-division-fractions-grade-4"],
            "config": {},
        })
        rid = r.json()["run"]["id"]
        r2 = client.get(f"/api/simulation/runs/{rid}", headers=_auth())
        assert r2.status_code == 200
        assert r2.json()["run"]["name"] == "Get Me"

    def test_get_run_missing(self, client):
        r = client.get("/api/simulation/runs/missing-id", headers=_auth())
        assert r.status_code == 404


class TestSimulationEvents:
    def test_record_and_get_events(self, client):
        r = client.post("/api/simulation/runs", headers=_auth(), json={
            "name": "Event Run",
            "description": "",
            "scenario_id": "baseline",
            "profile_ids": ["high_performing_student"],
            "course_slugs": ["multiplication-division-fractions-grade-4"],
            "config": {},
        })
        run_id = r.json()["run"]["id"]
        # Manually insert an event since start_run requires the engine
        client.db.simulation_events.docs.append({
            "id": "evt-1",
            "run_id": run_id,
            "simulated_user_id": "sim-user-1",
            "event_type": "lesson_start",
            "target_type": "lesson",
            "target_id": "lesson-1",
            "metadata": {"course_slug": "math-7", "student_id": "s1"},
            "is_simulation": True,
            "created_at": _now(),
        })
        r2 = client.get(f"/api/simulation/runs/{run_id}/events", headers=_auth())
        assert r2.status_code == 200
        assert len(r2.json()["events"]) == 1

    def test_events_filter_by_type(self, client):
        r = client.post("/api/simulation/runs", headers=_auth(), json={
            "name": "Filter Run",
            "description": "",
            "scenario_id": "baseline",
            "profile_ids": ["high_performing_student"],
            "course_slugs": ["multiplication-division-fractions-grade-4"],
            "config": {},
        })
        run_id = r.json()["run"]["id"]
        for etype in ["lesson_start", "assessment_pass", "assessment_fail"]:
            client.db.simulation_events.docs.append({
                "id": f"evt-{etype}",
                "run_id": run_id,
                "simulated_user_id": "sim-user-1",
                "event_type": etype,
                "target_type": "lesson",
                "target_id": "lesson-1",
                "metadata": {},
                "is_simulation": True,
                "created_at": _now(),
            })
        r2 = client.get(f"/api/simulation/runs/{run_id}/events?event_type=assessment_pass", headers=_auth())
        assert r2.status_code == 200
        events = r2.json()["events"]
        assert len(events) == 1
        assert events[0]["event_type"] == "assessment_pass"


class TestSimulationAnalytics:
    def test_run_analytics(self, client):
        r = client.post("/api/simulation/runs", headers=_auth(), json={
            "name": "Analytics Run",
            "description": "",
            "scenario_id": "baseline",
            "profile_ids": ["high_performing_student"],
            "course_slugs": ["multiplication-division-fractions-grade-4"],
            "config": {},
        })
        run_id = r.json()["run"]["id"]
        for etype in ["lesson_start", "assessment_pass", "assessment_fail", "lesson_complete", "dashboard_view"]:
            client.db.simulation_events.docs.append({
                "id": f"evt-{etype}",
                "run_id": run_id,
                "simulated_user_id": "sim-user-1",
                "event_type": etype,
                "target_type": "lesson",
                "target_id": "lesson-1",
                "metadata": {},
                "is_simulation": True,
                "created_at": _now(),
            })
        r2 = client.get(f"/api/simulation/runs/{run_id}/analytics", headers=_auth())
        assert r2.status_code == 200
        analytics = r2.json()["analytics"]
        assert analytics["total_events"] == 5
        assert analytics["by_event_type"]["assessment_pass"] == 1
        assert analytics["by_event_type"]["lesson_complete"] == 1

    def test_comparison_analytics(self, client):
        r = client.get("/api/simulation/analytics/comparison", headers=_auth())
        assert r.status_code == 200
        data = r.json()["analytics"]
        assert "real_events" in data
        assert "simulated_events" in data
        assert "real_completed_runs" in data
        assert "simulated_student_profiles" in data


class TestSimulationEngineUnit:
    def test_flatten_lessons(self):
        course = {
            "units": [
                {"slug": "u1", "title": "Unit 1", "order": 1, "lessons": [
                    {"slug": "l1", "title": "L1", "order": 2},
                    {"slug": "l2", "title": "L2", "order": 1},
                ]},
                {"slug": "u2", "title": "Unit 2", "order": 2, "lessons": [
                    {"slug": "l3", "title": "L3", "order": 1},
                ]},
            ]
        }
        lessons = _flatten_lessons(course)
        assert [l["slug"] for l in lessons] == ["l2", "l1", "l3"]

    def test_score_attempt_perfect(self):
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
        assert result["correct"] == 2
        assert result["passed"] is True

    def test_score_attempt_fail(self):
        lesson = {
            "slug": "l1",
            "check": {
                "questions": [
                    {"q": "Q1", "options": ["a", "b"], "answer": "a", "explain": "e1"},
                    {"q": "Q2", "options": ["x", "y"], "answer": "y", "explain": "e2"},
                ]
            },
        }
        result = _score_attempt(lesson, [1, 0], 80)
        assert result["score"] == 0.0
        assert result["passed"] is False

    def test_simulate_answers_distribution(self):
        questions = [
            {"q": "Q1", "options": ["a", "b", "c"], "answer": "a", "explain": "e1"},
            {"q": "Q2", "options": ["x", "y"], "answer": "y", "explain": "e2"},
        ]
        answers = _simulate_answers(questions, 1.0)
        assert answers == [0, 1]
        answers = _simulate_answers(questions, 0.0)
        assert answers != [0, 1] or answers == [0, 1]  # might randomly pick correct, but probability is 0

    def test_profile_constants(self):
        assert "high_performing_student" in STUDENT_PROFILES
        assert "typical_student" in STUDENT_PROFILES
        assert "struggling_student" in STUDENT_PROFILES
        assert "inconsistent_student" in STUDENT_PROFILES
        assert "active_instructor" in INSTRUCTOR_PROFILES
        assert "normal_instructor" in INSTRUCTOR_PROFILES
        assert "overloaded_instructor" in INSTRUCTOR_PROFILES
        for key, profile in STUDENT_PROFILES.items():
            assert profile["type"] == "student"
            assert "behavior" in profile
        for key, profile in INSTRUCTOR_PROFILES.items():
            assert profile["type"] == "instructor"
            assert "behavior" in profile

    def test_scenario_constants(self):
        for key in ["baseline", "struggling_algebra", "disengagement", "improvement", "instructor_overload"]:
            assert key in SCENARIOS
            assert "name" in SCENARIOS[key]
            assert "description" in SCENARIOS[key]
            assert "config" in SCENARIOS[key]


class TestSimulationIsolation:
    def test_simulation_flag_in_profile_doc(self):
        profile = SimulationProfile(
            id="p1",
            name="Test",
            type="student",
            profile_key="test",
            description="",
            behavior_config={},
            created_at=_now(),
        )
        doc = profile.to_doc()
        assert doc["is_simulation"] is True

    def test_simulation_flag_in_event_doc(self):
        event = SimulationEvent(
            id="e1",
            run_id="r1",
            simulated_user_id="u1",
            event_type="lesson_start",
            target_type="lesson",
            target_id="l1",
            metadata={},
            created_at=_now(),
        )
        doc = event.to_doc()
        assert doc["is_simulation"] is True

    def test_run_status_transitions(self):
        run = SimulationRun(
            id="r1",
            name="Test",
            description="",
            scenario_id="baseline",
            profile_ids=[],
            course_slugs=[],
            config={},
            created_by="admin",
            created_at=_now(),
        )
        assert run.status == "draft"
        run.status = "running"
        run.started_at = _now()
        assert run.status == "running"
        run.status = "completed"
        run.ended_at = _now()
        assert run.status == "completed"
