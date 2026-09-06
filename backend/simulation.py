"""simulation — Student/Instructor Simulation Lab core engine, profiles, scenarios.

This module provides:
  * Built-in student and instructor behavior profiles
  * Built-in simulation scenarios
  * SimulationEngine: creates simulated users, executes real API workflows,
    records simulation events, and supports run control (start/pause/stop)

Design rules:
  * Simulated users are real accounts flagged with is_simulation=True.
  * The simulator exercises the real application via internal ASGI calls
    (httpx.AsyncClient + ASGITransport) so the same auth, validation,
    business logic, and persistence run as for real users.
  * All generated events are tagged with is_simulation=True for analytics
    filtering. Normal learner-facing UI does NOT display simulation labels.
  * Simulation never modifies real-user records.
"""

import asyncio
import logging
import os
import random
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException

from roles import Role

logger = logging.getLogger("lcewai.simulation")

# Optional httpx — only needed for in-process ASGI simulation calls.
try:
    import httpx as _httpx
except Exception:
    _httpx = None

# ── Built-in student profiles ────────────────────────────────────────────────
STUDENT_PROFILES: Dict[str, Dict[str, Any]] = {
    "high_performing_student": {
        "name": "High-Performing Student",
        "type": "student",
        "description": "Regular attendance, steady progression, high assessment performance, occasional review, efficient lesson completion, occasional AI Tutor use, course completion.",
        "behavior": {
            "session_interval_hours": [8, 36],
            "lessons_per_session": [2, 5],
            "assessment_pass_probability": 0.88,
            "ai_tutor_use_probability": 0.15,
            "review_probability": 0.05,
            "inactivity_probability": 0.02,
            "min_score_if_passing": 85,
        },
    },
    "typical_student": {
        "name": "Typical Student",
        "type": "student",
        "description": "Moderate progression, occasional missed work, some assessment failures, lesson revisits, occasional assistance, eventual improvement.",
        "behavior": {
            "session_interval_hours": [12, 72],
            "lessons_per_session": [1, 3],
            "assessment_pass_probability": 0.65,
            "ai_tutor_use_probability": 0.30,
            "review_probability": 0.20,
            "inactivity_probability": 0.08,
            "min_score_if_passing": 75,
        },
    },
    "struggling_student": {
        "name": "Struggling Student",
        "type": "student",
        "description": "Slower progression, repeated lessons, repeated assessment attempts, lower scores, increased assistance requests, difficulty with selected concepts, inconsistent activity.",
        "behavior": {
            "session_interval_hours": [24, 120],
            "lessons_per_session": [1, 2],
            "assessment_pass_probability": 0.35,
            "ai_tutor_use_probability": 0.60,
            "review_probability": 0.45,
            "inactivity_probability": 0.15,
            "min_score_if_passing": 70,
        },
    },
    "inconsistent_student": {
        "name": "Inconsistent Student",
        "type": "student",
        "description": "Irregular attendance, incomplete lessons, gaps in progression, returning after inactivity, uneven assessment performance.",
        "behavior": {
            "session_interval_hours": [48, 168],
            "lessons_per_session": [1, 4],
            "assessment_pass_probability": 0.50,
            "ai_tutor_use_probability": 0.25,
            "review_probability": 0.30,
            "inactivity_probability": 0.25,
            "min_score_if_passing": 72,
        },
    },
}

INSTRUCTOR_PROFILES: Dict[str, Dict[str, Any]] = {
    "active_instructor": {
        "name": "Active Instructor",
        "type": "instructor",
        "description": "Regularly reviews students, monitors progress, identifies struggling learners, reviews assessments, performs interventions, uses instructor tools.",
        "behavior": {
            "review_interval_hours": [4, 24],
            "intervention_probability": 0.70,
            "response_delay_hours": [1, 6],
        },
    },
    "normal_instructor": {
        "name": "Normal Instructor",
        "type": "instructor",
        "description": "Moderate review frequency, responds to selected problems, monitors overall progress, performs ordinary instructional tasks.",
        "behavior": {
            "review_interval_hours": [12, 72],
            "intervention_probability": 0.40,
            "response_delay_hours": [6, 24],
        },
    },
    "overloaded_instructor": {
        "name": "Overloaded Instructor",
        "type": "instructor",
        "description": "Delayed reviews, missed opportunities, multiple students requiring attention, higher workload, slower intervention.",
        "behavior": {
            "review_interval_hours": [48, 168],
            "intervention_probability": 0.15,
            "response_delay_hours": [24, 96],
        },
    },
}

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "baseline": {
        "name": "Baseline",
        "description": "Students work through courses at their natural pace with no special conditions.",
        "config": {"duration_minutes": 60, "intensity": "medium", "realistic_timing": True},
    },
    "struggling_algebra": {
        "name": "Struggling with Algebra",
        "description": "Simulated students repeatedly struggle with translating word problems into equations. System records attempts, errors, lesson revisits, help requests, and improvement.",
        "config": {"duration_minutes": 90, "intensity": "heavy", "realistic_timing": True},
        "target_course_filter": {"subject": "math", "grade_label": "Grade 9"},
    },
    "disengagement": {
        "name": "Student Disengagement",
        "description": "Simulated students stop progressing for a defined period. System tests detection, dashboard visibility, intervention signals, and instructor awareness.",
        "config": {"duration_minutes": 120, "intensity": "medium", "realistic_timing": True},
    },
    "improvement": {
        "name": "Student Improvement",
        "description": "Simulated students start struggling but improve after remediation. System tests whether remediation was effective.",
        "config": {"duration_minutes": 90, "intensity": "medium", "realistic_timing": True},
    },
    "instructor_overload": {
        "name": "Instructor Overload",
        "description": "Multiple simulated students require attention simultaneously. Test whether instructor interface helps prioritize intervention.",
        "config": {"duration_minutes": 120, "intensity": "heavy", "realistic_timing": True},
    },
}


# ── Data models ──────────────────────────────────────────────────────────────
class SimulationProfile:
    def __init__(self, id: str, name: str, type: str, profile_key: str, description: str, behavior_config: Dict[str, Any], created_at: str):
        self.id = id
        self.name = name
        self.type = type
        self.profile_key = profile_key
        self.description = description
        self.behavior_config = behavior_config
        self.created_at = created_at

    def to_doc(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "profile_key": self.profile_key,
            "description": self.description,
            "behavior_config": self.behavior_config,
            "is_simulation": True,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_doc(doc: Dict[str, Any]) -> "SimulationProfile":
        return SimulationProfile(
            id=doc["id"],
            name=doc["name"],
            type=doc["type"],
            profile_key=doc["profile_key"],
            description=doc["description"],
            behavior_config=doc.get("behavior_config", {}),
            created_at=doc["created_at"],
        )


class SimulationRun:
    def __init__(self, id: str, name: str, description: str, scenario_id: str, profile_ids: List[str], course_slugs: List[str], config: Dict[str, Any], created_by: str, created_at: str):
        self.id = id
        self.name = name
        self.description = description
        self.scenario_id = scenario_id
        self.profile_ids = profile_ids
        self.course_slugs = course_slugs
        self.config = config
        self.created_by = created_by
        self.status = "draft"
        self.started_at: Optional[str] = None
        self.ended_at: Optional[str] = None
        self.event_count = 0
        self.created_at = created_at
        self.updated_at = created_at

    def to_doc(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "scenario_id": self.scenario_id,
            "profile_ids": self.profile_ids,
            "course_slugs": self.course_slugs,
            "config": self.config,
            "status": self.status,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "event_count": self.event_count,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_doc(doc: Dict[str, Any]) -> "SimulationRun":
        run = SimulationRun(
            id=doc["id"],
            name=doc["name"],
            description=doc["description"],
            scenario_id=doc["scenario_id"],
            profile_ids=doc["profile_ids"],
            course_slugs=doc["course_slugs"],
            config=doc.get("config", {}),
            created_by=doc["created_by"],
            created_at=doc["created_at"],
        )
        run.status = doc.get("status", "draft")
        run.started_at = doc.get("started_at")
        run.ended_at = doc.get("ended_at")
        run.event_count = doc.get("event_count", 0)
        run.updated_at = doc.get("updated_at", run.created_at)
        return run


class SimulationEvent:
    def __init__(self, id: str, run_id: str, simulated_user_id: str, event_type: str, target_type: str, target_id: str, metadata: Dict[str, Any], created_at: str):
        self.id = id
        self.run_id = run_id
        self.simulated_user_id = simulated_user_id
        self.event_type = event_type
        self.target_type = target_type
        self.target_id = target_id
        self.metadata = metadata or {}
        self.created_at = created_at
        self.is_simulation = True

    def to_doc(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "simulated_user_id": self.simulated_user_id,
            "event_type": self.event_type,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "metadata": self.metadata,
            "is_simulation": True,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_doc(doc: Dict[str, Any]) -> "SimulationEvent":
        return SimulationEvent(
            id=doc["id"],
            run_id=doc["run_id"],
            simulated_user_id=doc["simulated_user_id"],
            event_type=doc["event_type"],
            target_type=doc["target_type"],
            target_id=doc["target_id"],
            metadata=doc.get("metadata", {}),
            created_at=doc["created_at"],
        )


# ── Engine ───────────────────────────────────────────────────────────────────
class SimulationEngine:
    def __init__(self, db, app: FastAPI):
        self.db = db
        self.app = app
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._stop_flags: Dict[str, bool] = {}

    async def ensure_indexes(self):
        await self.db.simulation_profiles.create_index("id", unique=True)
        await self.db.simulation_runs.create_index("id", unique=True)
        await self.db.simulation_runs.create_index("status")
        await self.db.simulation_events.create_index("run_id")
        await self.db.simulation_events.create_index("simulated_user_id")
        await self.db.simulation_events.create_index([("run_id", 1), ("created_at", 1)])

    async def create_profile(self, name: str, type: str, profile_key: str, description: str, behavior_config: Dict[str, Any]) -> SimulationProfile:
        now = _now()
        profile = SimulationProfile(
            id=str(uuid.uuid4()),
            name=name,
            type=type,
            profile_key=profile_key,
            description=description,
            behavior_config=behavior_config,
            created_at=now,
        )
        await self.db.simulation_profiles.insert_one(profile.to_doc())
        return profile

    async def list_profiles(self) -> List[SimulationProfile]:
        docs = await self.db.simulation_profiles.find({}, {"_id": 0}).to_list(200)
        return [SimulationProfile.from_doc(d) for d in docs]

    async def get_profile(self, profile_id: str) -> Optional[SimulationProfile]:
        doc = await self.db.simulation_profiles.find_one({"id": profile_id}, {"_id": 0})
        return SimulationProfile.from_doc(doc) if doc else None

    async def create_run(self, name: str, description: str, scenario_id: str, profile_ids: List[str], course_slugs: List[str], config: Dict[str, Any], created_by: str) -> SimulationRun:
        now = _now()
        run = SimulationRun(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            scenario_id=scenario_id,
            profile_ids=profile_ids,
            course_slugs=course_slugs,
            config=config,
            created_by=created_by,
            created_at=now,
        )
        await self.db.simulation_runs.insert_one(run.to_doc())
        return run

    async def get_run(self, run_id: str) -> Optional[SimulationRun]:
        doc = await self.db.simulation_runs.find_one({"id": run_id}, {"_id": 0})
        return SimulationRun.from_doc(doc) if doc else None

    async def update_run(self, run_id: str, **updates):
        updates["updated_at"] = _now()
        await self.db.simulation_runs.update_one({"id": run_id}, {"$set": updates})

    async def list_runs(self, status: Optional[str] = None) -> List[SimulationRun]:
        q: Dict[str, Any] = {}
        if status:
            q["status"] = status
        docs = await self.db.simulation_runs.find(q, {"_id": 0}).sort("created_at", -1).to_list(100)
        return [SimulationRun.from_doc(d) for d in docs]

    async def record_event(self, run_id: str, simulated_user_id: str, event_type: str, target_type: str, target_id: str, metadata: Optional[Dict[str, Any]] = None):
        event = SimulationEvent(
            id=str(uuid.uuid4()),
            run_id=run_id,
            simulated_user_id=simulated_user_id,
            event_type=event_type,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata or {},
            created_at=_now(),
        )
        await self.db.simulation_events.insert_one(event.to_doc())
        count = await self.db.simulation_events.count_documents({"run_id": run_id})
        await self.update_run(run_id, event_count=count)
        return event

    async def get_events(self, run_id: str, event_type: Optional[str] = None, limit: int = 500) -> List[SimulationEvent]:
        q: Dict[str, Any] = {"run_id": run_id, "is_simulation": True}
        if event_type:
            q["event_type"] = event_type
        docs = await self.db.simulation_events.find(q, {"_id": 0}).sort("created_at", 1).limit(limit).to_list(limit)
        return [SimulationEvent.from_doc(d) for d in docs]

    async def get_run_analytics(self, run_id: str) -> Dict[str, Any]:
        events = await self.get_events(run_id, limit=10000)
        by_type: Dict[str, int] = defaultdict(int)
        by_user: Dict[str, int] = defaultdict(int)
        by_target: Dict[str, int] = defaultdict(int)
        for e in events:
            by_type[e.event_type] += 1
            by_user[e.simulated_user_id] += 1
            by_target[e.target_type] += 1
        return {
            "run_id": run_id,
            "total_events": len(events),
            "by_event_type": dict(by_type),
            "by_user": dict(by_user),
            "by_target_type": dict(by_target),
        }

    async def _create_simulated_user(self, profile_key: str, run_id: str) -> Dict[str, Any]:
        password = str(uuid.uuid4())
        from security import hash_password
        hashed = hash_password(password)
        user_doc = {
            "id": str(uuid.uuid4()),
            "email": f"sim_{profile_key}_{run_id[:8]}@simulation.local",
            "full_name": f"Sim {profile_key.replace('_', ' ').title()}",
            "role": "student",
            "associate": None,
            "is_active": True,
            "must_change_password": False,
            "created_at": _now(),
            "avatar_url": None,
            "social_handles": None,
            "feature_tier": "free",
            "sage_tier": None,
            "last_login": None,
            "token_version": 0,
            "terms_accepted_at": _now(),
            "over_13_confirmed": True,
            "is_simulation": True,
            "simulation_profile": profile_key,
            "simulation_run_id": run_id,
            "password": hashed,
        }
        await self.db.users.insert_one(user_doc)
        return user_doc

    async def _create_simulated_instructor(self, profile_key: str, run_id: str) -> Dict[str, Any]:
        password = str(uuid.uuid4())
        from security import hash_password
        hashed = hash_password(password)
        user_doc = {
            "id": str(uuid.uuid4()),
            "email": f"sim_instructor_{profile_key}_{run_id[:8]}@simulation.local",
            "full_name": f"Sim Instructor {profile_key.replace('_', ' ').title()}",
            "role": "instructor",
            "associate": f"sim_{run_id[:8]}",
            "is_active": True,
            "must_change_password": False,
            "created_at": _now(),
            "avatar_url": None,
            "social_handles": None,
            "feature_tier": "free",
            "sage_tier": None,
            "last_login": None,
            "token_version": 0,
            "terms_accepted_at": _now(),
            "over_13_confirmed": True,
            "is_simulation": True,
            "simulation_profile": profile_key,
            "simulation_run_id": run_id,
            "password": hashed,
        }
        await self.db.users.insert_one(user_doc)
        return user_doc

    async def _make_token(self, user: Dict[str, Any]) -> str:
        secret = os.environ.get("JWT_SECRET", "testsecret")
        algo = os.environ.get("JWT_ALGO", "HS256")
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user["id"],
            "role": user.get("role", "student"),
            "tv": user.get("token_version", 0),
            "sid": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": int((now + __import__("datetime").timedelta(hours=24)).timestamp()),
        }
        return jwt.encode(payload, secret, algorithm=algo)

    async def _api_call(self, method: str, path: str, user: Dict[str, Any], json_data: Optional[Dict] = None, params: Optional[Dict] = None):
        if _httpx is None:
            raise RuntimeError("httpx is required for simulation API calls")
        token = await self._make_token(user)
        headers = {"Authorization": f"Bearer {token}"}
        if json_data is not None:
            headers["Content-Type"] = "application/json"
        transport = _httpx.ASGITransport(app=self.app)
        async with _httpx.AsyncClient(transport=transport, base_url="http://academy.internal") as client:
            response = await client.request(method, path, headers=headers, json=json_data, params=params)
        return response

    async def start_run(self, run_id: str):
        await self.update_run(run_id, status="running", started_at=_now())
        run = await self.get_run(run_id)
        if not run:
            raise HTTPException(404, "Simulation run not found")

        scenario = SCENARIOS.get(run.scenario_id, SCENARIOS["baseline"])
        self._stop_flags[run_id] = False

        simulated_users: Dict[str, Dict[str, Any]] = {}
        for profile_id in run.profile_ids:
            if self._stop_flags.get(run_id):
                break
            profile = await self.get_profile(profile_id)
            if not profile:
                continue
            if profile.type == "student":
                user = await self._create_simulated_user(profile.profile_key, run_id)
                # Create student profile
                grade = "adult" if any("adult" in s for s in run.course_slugs) else "9"
                track = "scholar"
                await self.db.academy_students.insert_one({
                    "id": str(uuid.uuid4()),
                    "parent_user_id": user["id"],
                    "name": user["full_name"],
                    "grade": grade,
                    "track": track,
                    "notes": None,
                    "course_slugs": run.course_slugs,
                    "status": "active",
                    "created_at": _now(),
                    "updated_at": _now(),
                })
                simulated_users[profile_id] = user
            elif profile.type == "instructor":
                user = await self._create_simulated_instructor(profile.profile_key, run_id)
                simulated_users[profile_id] = user

        try:
            for profile_id, user in simulated_users.items():
                if self._stop_flags.get(run_id):
                    break
                profile = await self.get_profile(profile_id)
                behavior = profile.behavior_config if profile else {}
                if profile and profile.type == "student":
                    await self._execute_student_scenario(run, user, behavior, scenario)
                elif profile and profile.type == "instructor":
                    await self._execute_instructor_scenario(run, user, behavior, scenario)
        except asyncio.CancelledError:
            pass
        finally:
            self._stop_flags[run_id] = True
            await self.update_run(run_id, status="completed", ended_at=_now())

    async def stop_run(self, run_id: str):
        self._stop_flags[run_id] = True
        task = self._running_tasks.pop(run_id, None)
        if task and not task.done():
            task.cancel()
        await self.update_run(run_id, status="stopped", ended_at=_now())

    async def _execute_student_scenario(self, run: SimulationRun, user: Dict[str, Any], behavior: Dict[str, Any], scenario: Dict[str, Any]):
        student_docs = await self.db.academy_students.find({"parent_user_id": user["id"], "status": "active"}, {"_id": 0}).to_list(100)
        for student in student_docs:
            if self._stop_flags.get(run.id):
                break
            for course_slug in student.get("course_slugs", []):
                if self._stop_flags.get(run.id):
                    break
                if course_slug not in run.course_slugs:
                    continue
                await self._simulate_course_progress(run, user, student, course_slug, behavior, scenario)

    async def _simulate_course_progress(self, run: SimulationRun, user: Dict[str, Any], student: Dict[str, Any], course_slug: str, behavior: Dict[str, Any], scenario: Dict[str, Any]):
        course = await self.db.academy_courses.find_one({"slug": course_slug}, {"_id": 0})
        if not course or course.get("status") != "published":
            return
        lessons = _flatten_lessons(course)
        if not lessons:
            return

        student_id = student["id"]
        await self.record_event(run.id, user["id"], "course_view", "course", course_slug, {"student_id": student_id})

        progress_map = await _load_progress_map(self.db, student_id, course_slug)
        current_lesson = _next_lesson(lessons, progress_map, _passing_score(course))

        for lesson in lessons:
            if self._stop_flags.get(run.id):
                break
            if current_lesson and lesson["slug"] != current_lesson["slug"]:
                continue
            if progress_map.get(lesson["slug"], {}).get("status") == "passed":
                continue

            await self.record_event(run.id, user["id"], "lesson_start", "lesson", lesson["slug"], {"course_slug": course_slug, "student_id": student_id})
            await asyncio.sleep(random.uniform(2, 8))

            passed = False
            attempts = 0
            max_attempts = 3 if behavior.get("assessment_pass_probability", 0.5) < 0.6 else 2
            while not passed and attempts < max_attempts:
                if self._stop_flags.get(run.id):
                    break
                attempts += 1
                questions = lesson.get("check", {}).get("questions", [])
                answers = _simulate_answers(questions, behavior.get("assessment_pass_probability", 0.65))
                result = _score_attempt(lesson, answers, _passing_score(course))

                await self.record_event(run.id, user["id"], "assessment_attempt", "assessment", lesson["slug"], {
                    "course_slug": course_slug,
                    "student_id": student_id,
                    "score": result["score"],
                    "passed": result["passed"],
                    "attempt_number": attempts,
                })

                if result["passed"]:
                    passed = True
                    await self.db.academy_progress.update_one(
                        {"student_id": student_id, "course_slug": course_slug, "lesson_slug": lesson["slug"]},
                        {"$set": {
                            "status": "passed",
                            "best_score": result["score"],
                            "passed_at": _now(),
                            "updated_at": _now(),
                        }, "$push": {"attempts": {
                            "score": result["score"],
                            "correct": result["correct"],
                            "total": result["total"],
                            "passed": True,
                            "at": _now(),
                        }}},
                        upsert=True,
                    )
                    await self.record_event(run.id, user["id"], "assessment_pass", "assessment", lesson["slug"], {
                        "course_slug": course_slug,
                        "student_id": student_id,
                        "score": result["score"],
                    })
                else:
                    existing = await self.db.academy_progress.find_one({"student_id": student_id, "course_slug": course_slug, "lesson_slug": lesson["slug"]}, {"_id": 0})
                    prior = existing or {}
                    await self.db.academy_progress.update_one(
                        {"student_id": student_id, "course_slug": course_slug, "lesson_slug": lesson["slug"]},
                        {"$set": {
                            "status": "in_progress",
                            "best_score": max(prior.get("best_score") or 0, result["score"]),
                            "updated_at": _now(),
                        }, "$push": {"attempts": {
                            "score": result["score"],
                            "correct": result["correct"],
                            "total": result["total"],
                            "passed": False,
                            "at": _now(),
                        }}},
                        upsert=True,
                    )
                    await self.record_event(run.id, user["id"], "assessment_fail", "assessment", lesson["slug"], {
                        "course_slug": course_slug,
                        "student_id": student_id,
                        "score": result["score"],
                        "attempt_number": attempts,
                    })
                    if attempts < max_attempts:
                        await asyncio.sleep(random.uniform(5, 20))
                        if random.random() < behavior.get("review_probability", 0.2):
                            await self.record_event(run.id, user["id"], "lesson_review", "lesson", lesson["slug"], {
                                "course_slug": course_slug,
                                "student_id": student_id,
                            })
                            await asyncio.sleep(random.uniform(3, 10))

            if passed:
                await self.record_event(run.id, user["id"], "lesson_complete", "lesson", lesson["slug"], {
                    "course_slug": course_slug,
                    "student_id": student_id,
                    "attempts": attempts,
                })

        await self.record_event(run.id, user["id"], "dashboard_view", "dashboard", student_id, {
            "course_slug": course_slug,
            "student_id": student_id,
        })

    async def _execute_instructor_scenario(self, run: SimulationRun, user: Dict[str, Any], behavior: Dict[str, Any], scenario: Dict[str, Any]):
        # Instructors review student progress and may intervene
        await self.record_event(run.id, user["id"], "dashboard_view", "dashboard", "instructor", {})
        await asyncio.sleep(random.uniform(2, 5))
        # Look at all simulated students in this run
        students = await self.db.academy_students.find({"status": "active"}, {"_id": 0}).to_list(200)
        for student in students:
            if self._stop_flags.get(run.id):
                break
            parent = await self.db.users.find_one({"id": student.get("parent_user_id")}, {"_id": 0})
            if not parent or not parent.get("is_simulation"):
                continue
            if parent.get("simulation_run_id") != run.id:
                continue
            # View student dashboard
            await self.record_event(run.id, user["id"], "student_review", "student", student["id"], {
                "student_id": student["id"],
            })
            await asyncio.sleep(random.uniform(1, 4))
            if random.random() < behavior.get("intervention_probability", 0.4):
                await self.record_event(run.id, user["id"], "intervention", "student", student["id"], {
                    "student_id": student["id"],
                    "type": "review" if random.random() < 0.7 else "assistance",
                })


# ── Helpers ──────────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _flatten_lessons(course: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for unit in course.get("units", []):
        for lesson in unit.get("lessons", []):
            out.append({**lesson, "_unit_slug": unit.get("slug"), "_unit_title": unit.get("title")})
    out.sort(key=lambda l: (l.get("order", 0), l.get("slug", "")))
    return out


def _passing_score(course: Dict[str, Any]) -> int:
    try:
        return int(course.get("passing_score") or 80)
    except (TypeError, ValueError):
        return 80


async def _load_progress_map(db, student_id: str, course_slug: str) -> Dict[str, Any]:
    docs = await db.academy_progress.find(
        {"student_id": student_id, "course_slug": course_slug}, {"_id": 0}
    ).to_list(500)
    return {d["lesson_slug"]: d for d in docs}


def _next_lesson(lessons: List[Dict[str, Any]], progress: Dict[str, Any], passing_score: int) -> Optional[Dict[str, Any]]:
    for lesson in lessons:
        if progress.get(lesson["slug"], {}).get("status") != "passed":
            return lesson
    return None


def _score_attempt(lesson: Dict[str, Any], answers: List[int], passing_score: int) -> Dict[str, Any]:
    questions = lesson.get("check", {}).get("questions", [])
    if len(answers) != len(questions):
        raise ValueError("Answer count mismatch")
    correct = 0
    for i, question in enumerate(questions):
        try:
            expected = question["options"].index(question["answer"])
        except (KeyError, ValueError):
            raise ValueError(f"Content error: lesson {lesson.get('slug')} question {i + 1} answer key broken")
        answer = answers[i]
        if not isinstance(answer, int) or answer < 0 or answer >= len(question["options"]):
            raise ValueError(f"Answer for question {i + 1} out of range")
        if answer == expected:
            correct += 1
    total = len(questions) or 1
    score = round(correct / total * 100, 1) if questions else 0.0
    return {"score": score, "correct": correct, "total": len(questions), "passed": score >= passing_score}


def _simulate_answers(questions: List[Dict[str, Any]], pass_probability: float) -> List[int]:
    answers = []
    for q in questions:
        options = q.get("options", [])
        if not options:
            answers.append(0)
            continue
        correct_idx = options.index(q["answer"]) if q["answer"] in options else 0
        if random.random() < pass_probability:
            answers.append(correct_idx)
        else:
            wrong = [i for i in range(len(options)) if i != correct_idx]
            answers.append(random.choice(wrong) if wrong else correct_idx)
    return answers


# ── Singleton ────────────────────────────────────────────────────────────────
_engine: Optional[SimulationEngine] = None


def get_engine(db=None, app=None) -> SimulationEngine:
    global _engine
    if _engine is None:
        if db is None or app is None:
            raise RuntimeError("SimulationEngine not initialized")
        _engine = SimulationEngine(db, app)
    return _engine


def reset_engine():
    global _engine
    _engine = None
