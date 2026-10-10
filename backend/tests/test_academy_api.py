"""Tests for the WAI Institute Homeschool Academy API (routers/academy.py).

Covers the ownership model, catalog gating, enrollment applicability, lesson
sequencing, 80% mastery + retry, and records. Uses the repo's established
fake-db + TestClient pattern (see test_lms_module_gating.py) — no MongoDB
needed. Also validates that every seeded course satisfies the content contract.

Run: cd backend && python3 -m pytest tests/test_academy_api.py -v
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "testsecret")

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import routers.academy as academy
from seed_academy import validate_all


# ── Fake Mongo collection ────────────────────────────────────────────────────
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
                # Mongo equality on an array field matches array membership.
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

            async def to_list(self, n=None):
                out = [self._project(d, self.proj) for d in self.docs]
                return out[:n] if n else out

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
            if q.get("id"):
                target["id"] = q["id"]
            for key in ("student_id", "course_slug", "lesson_slug", "parent_user_id", "slug"):
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


def _course(slug, status="published", grades=None, tracks=None, subject="math",
            track="foundations", title=None, lessons=2):
    units = []
    if status == "published" and lessons:
        lesson_docs = []
        for i in range(1, lessons + 1):
            lesson_docs.append({
                "slug": f"{slug}-lesson-{i}",
                "title": f"Lesson {i}",
                "order": i,
                "minutes": 10,
                "summary": f"Summary {i}",
                "learn": [{"type": "p", "text": f"Learn {i}"}],
                "check": {
                    "prompt": "Check",
                    "questions": [
                        {"q": f"Q{i}", "options": ["right", "wrong"], "answer": "right",
                         "explain": "Because right is right."},
                        {"q": f"Q{i}b", "options": ["yes", "no"], "answer": "yes",
                         "explain": "Yes is correct."},
                    ],
                },
            })
        units = [{"slug": f"{slug}-u1", "title": "Unit 1", "summary": "U",
                  "order": 1, "lessons": lesson_docs}]
    return {
        "id": f"id-{slug}", "slug": slug, "title": title or slug,
        "summary": "sum", "description": "desc",
        "subject": subject, "subject_label": subject,
        "track": track, "tracks": tracks or [track],
        "grades": grades or ["7"], "grade_label": "Grade 7",
        "status": status, "audience": "", "est_hours": 4,
        "passing_score": 80,
        "learning_objectives": ["Objective 1"] if status == "published" else [],
        "units": units,
    }


def _student(sid, parent="u1", grade="7", track="foundations", course_slugs=None, status="active"):
    return {
        "id": sid, "parent_user_id": parent, "name": "Avery",
        "grade": grade, "track": track, "notes": None,
        "course_slugs": course_slugs or [], "status": status,
        "created_at": "2026-09-01T00:00:00Z", "updated_at": "2026-09-01T00:00:00Z",
    }


def _fake_db():
    courses = [
        _course("math-7", grades=["7"], tracks=["foundations", "builder"], subject="math", track="foundations"),
        _course("ela-1", grades=["1"], tracks=["foundations"], subject="ela", track="foundations"),
        _course("elec-9", grades=["9", "10"], tracks=["builder"], subject="trade", track="builder"),
        _course("bio-9", grades=["9"], tracks=["scholar", "foundations"], subject="science", track="scholar", lessons=2),
        _course("planned-course", status="planned", grades=["7"], tracks=["foundations"], lessons=0),
    ]
    return SimpleNamespace(
        academy_courses=_FakeCollection(courses),
        academy_students=_FakeCollection([]),
        academy_progress=_FakeCollection([]),
    )


async def _fake_current_user(authorization=None):
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    return SimpleNamespace(id="u1", email="p@example.com", full_name="Parent",
                           role="student", feature_tier="free")


@pytest.fixture
def client():
    db = _fake_db()
    academy.bind(db, _fake_current_user, None, None, None)
    app = FastAPI()
    app.include_router(academy.router, prefix="/api")
    c = TestClient(app)
    c.db = db  # expose for arranging state
    return c


def _auth():
    return {"Authorization": "Bearer t"}


def _add_student(client, sid, **kw):
    defaults = dict(sid=sid, parent="u1", grade="7", track="foundations", course_slugs=None)
    defaults.update(kw)
    client.db.academy_students.docs.append(_student(**defaults))
    return sid


# ── Content contract ─────────────────────────────────────────────────────────
def test_seed_content_validates():
    assert validate_all() == []


# ── Catalog ──────────────────────────────────────────────────────────────────
def test_public_catalog_metadata_only(client):
    r = client.get("/api/academy/courses")
    assert r.status_code == 200
    payload = r.json()
    assert payload["count"] == 5
    meta = payload["courses"]
    # Planned courses visible but labelled; lesson counts never leak content.
    planned = next(c for c in meta if c["slug"] == "planned-course")
    assert planned["status"] == "planned"
    assert planned["lesson_count"] == 0
    assert all("units" not in c and "learn" not in c for c in meta)


def test_catalog_filters(client):
    r = client.get("/api/academy/courses", params={"grade": "7", "track": "builder"})
    slugs = [c["slug"] for c in r.json()["courses"]]
    assert "math-7" in slugs
    assert "ela-1" not in slugs
    assert "elec-9" not in slugs
    r = client.get("/api/academy/courses", params={"subject": "trade"})
    assert [c["slug"] for c in r.json()["courses"]] == ["elec-9"]


def test_course_detail_content_gating(client):
    # Anonymous → metadata only, no lesson content even for published course.
    r = client.get("/api/academy/courses/math-7")
    assert r.status_code == 200
    data = r.json()
    assert data["content_visible"] is False
    for unit in data["units"]:
        assert all("learn" not in l and "check" not in l for l in unit["lessons"])


def test_course_detail_content_for_enrolled_owner(client):
    _add_student(client, "s1", course_slugs=["math-7"])
    r = client.get("/api/academy/courses/math-7", headers=_auth())
    data = r.json()
    assert data["content_visible"] is True
    lesson = data["units"][0]["lessons"][0]
    assert lesson["learn"] and lesson["check"]["questions"]


# ── Student profiles + enrollment ────────────────────────────────────────────
def test_create_student_auto_enrolls(client):
    r = client.post("/api/academy/students", headers=_auth(),
                    json={"name": "Avery", "grade": "7", "track": "builder"})
    assert r.status_code == 200
    body = r.json()
    assert body["student"]["parent_user_id"] == "u1"
    # Grade 7 builder → math-7 (track builder allowed). ela-1 is grade 1; elec-9 is grades 9+.
    assert "math-7" in body["auto_enrolled"]
    assert "ela-1" not in body["auto_enrolled"]
    assert "elec-9" not in body["auto_enrolled"]
    # Planned courses are never auto-enrolled.
    assert "planned-course" not in body["auto_enrolled"]


def test_create_student_rejects_bad_grade(client):
    r = client.post("/api/academy/students", headers=_auth(),
                    json={"name": "A", "grade": "13", "track": "foundations"})
    assert r.status_code == 400


def test_student_ownership_enforced(client):
    _add_student(client, "s1", course_slugs=["math-7"])
    r = client.get("/api/academy/students/s1/dashboard", headers=_auth())
    assert r.status_code == 200  # s1 belongs to u1
    r = client.get("/api/academy/students/s-other/dashboard", headers=_auth())
    assert r.status_code == 404  # doesn't exist
    _add_student(client, "s2", parent="u2", course_slugs=["math-7"])
    r = client.get("/api/academy/students/s2/dashboard", headers=_auth())
    assert r.status_code == 403  # belongs to another account


def test_grade_change_recomputes_enrollment(client):
    r = client.post("/api/academy/students", headers=_auth(),
                    json={"name": "Kid", "grade": "1", "track": "foundations"})
    sid = r.json()["student"]["id"]
    assert r.json()["auto_enrolled"] == ["ela-1"]
    r = client.patch(f"/api/academy/students/{sid}", headers=_auth(), json={"grade": "7"})
    assert r.status_code == 200
    slugs = r.json()["student"]["course_slugs"]
    assert "math-7" in slugs
    assert "ela-1" not in slugs  # no longer fits grade 7


def test_manual_enrollment_rules(client):
    sid = _add_student(client, "sm", course_slugs=["math-7"])
    # Not offered for this student's grade/track → 400.
    r = client.post(f"/api/academy/students/{sid}/courses", headers=_auth(),
                    json={"course_slug": "elec-9", "enroll": True})
    assert r.status_code == 400
    # ela-1 is a Grade 1 course — still not offered for a Grade 7 student.
    r = client.post(f"/api/academy/students/{sid}/courses", headers=_auth(),
                    json={"course_slug": "ela-1", "enroll": True})
    assert r.status_code == 400
    # Manual un-enroll works even when the course was auto-recommended.
    r = client.post(f"/api/academy/students/{sid}/courses", headers=_auth(),
                    json={"course_slug": "math-7", "enroll": False})
    assert r.status_code == 200
    assert "math-7" not in r.json()["course_slugs"]


# ── Learning engine: sequencing + 80% mastery ────────────────────────────────
def _enroll_s7(client):
    client.db.academy_students.docs.append(_student("s7", course_slugs=["math-7"]))
    return "s7"


def test_attempt_grading_and_mastery_gate(client):
    sid = _enroll_s7(client)
    # Wrong answers → score 0, not passed, no unlock of lesson 2.
    r = client.post("/api/academy/courses/math-7/lessons/math-7-lesson-1/attempt",
                    headers=_auth(), json={"student_id": sid, "answers": [1, 1]})
    assert r.status_code == 200
    body = r.json()
    assert body["score"] == 0 and body["passed"] is False
    assert body["required"] == 80

    # Lesson 2 is locked until lesson 1 passes.
    r = client.post("/api/academy/courses/math-7/lessons/math-7-lesson-2/attempt",
                    headers=_auth(), json={"student_id": sid, "answers": [0, 0]})
    assert r.status_code == 403
    assert "Locked" in r.json()["detail"]

    # Perfect attempt → passed, next lesson returned as the next step.
    r = client.post("/api/academy/courses/math-7/lessons/math-7-lesson-1/attempt",
                    headers=_auth(), json={"student_id": sid, "answers": [0, 0]})
    assert r.json()["passed"] is True
    assert r.json()["next_lesson"]["slug"] == "math-7-lesson-2"

    # Re-attempting a passed lesson is rejected (no farming/gaming).
    r = client.post("/api/academy/courses/math-7/lessons/math-7-lesson-1/attempt",
                    headers=_auth(), json={"student_id": sid, "answers": [0, 0]})
    assert r.status_code == 409

    # Lesson 2 now unlocked; pass it and the course completes.
    r = client.post("/api/academy/courses/math-7/lessons/math-7-lesson-2/attempt",
                    headers=_auth(), json={"student_id": sid, "answers": [0, 0]})
    assert r.json()["passed"] is True
    assert r.json()["course_completed"] is True

    # Dashboard reflects completion.
    dash = client.get(f"/api/academy/students/{sid}/dashboard", headers=_auth()).json()
    card = dash["courses"][0]
    assert card["stats"]["lessons_passed"] == 2
    assert card["stats"]["completed"] is True
    assert card["next_lesson"] is None


def test_80_percent_passes_when_question_count_allows(client):
    """2-question check cannot hit exactly 80 — verify a 1/2 (50) fails and
    retries accumulate without corrupting best score."""
    sid = _enroll_s7(client)
    r1 = client.post("/api/academy/courses/math-7/lessons/math-7-lesson-1/attempt",
                     headers=_auth(), json={"student_id": sid, "answers": [0, 1]})
    assert r1.json()["passed"] is False
    assert r1.json()["attempt_number"] == 1
    r2 = client.post("/api/academy/courses/math-7/lessons/math-7-lesson-1/attempt",
                     headers=_auth(), json={"student_id": sid, "answers": [0, 0]})
    assert r2.json()["passed"] is True
    assert r2.json()["attempt_number"] == 2
    # Best score persisted correctly.
    prog = client.db.academy_progress.docs[0]
    assert prog["best_score"] == 100.0
    assert len(prog["attempts"]) == 2


def test_course_learn_returns_unlock_states(client):
    sid = _enroll_s7(client)
    r = client.get(f"/api/academy/courses/math-7/learn?student={sid}", headers=_auth())
    assert r.status_code == 200
    data = r.json()
    assert data["current_lesson"]["slug"] == "math-7-lesson-1"
    l1 = data["units"][0]["lessons"][0]
    l2 = data["units"][0]["lessons"][1]
    assert l1["unlocked"] is True
    assert l2["unlocked"] is False  # locked until lesson 1 passes
    assert l1["learn"] and l1["check"]["questions"]  # content present for owner


def test_learn_requires_enrollment(client):
    _add_student(client, "s9", course_slugs=["bio-9"])
    r = client.get("/api/academy/courses/math-7/learn?student=s9", headers=_auth())
    assert r.status_code == 403


def test_learn_defaults_to_owners_enrolled_student(client):
    """A deep link without ?student= (e.g. CourseDetail's "Open course" CTA)
    must resolve to the owner's enrolled student so lesson attempts never fire
    with a null student id."""
    _add_student(client, "sd", course_slugs=["math-7"])
    r = client.get("/api/academy/courses/math-7/learn", headers=_auth())
    assert r.status_code == 200
    data = r.json()
    assert data["student_id"] == "sd"
    assert data["current_lesson"]["slug"] == "math-7-lesson-1"
    l1 = data["units"][0]["lessons"][0]
    assert l1["unlocked"] is True and l1["learn"]
    # An attempt against the resolved default student succeeds.
    r = client.post("/api/academy/courses/math-7/lessons/math-7-lesson-1/attempt",
                    headers=_auth(), json={"student_id": "sd", "answers": [0, 0]})
    assert r.status_code == 200 and r.json()["passed"] is True


# ── Records ──────────────────────────────────────────────────────────────────
def test_records_shape(client):
    sid = _enroll_s7(client)
    r = client.post("/api/academy/courses/math-7/lessons/math-7-lesson-1/attempt",
                    headers=_auth(), json={"student_id": sid, "answers": [0, 0]})
    assert r.json()["passed"] is True
    rec = client.get(f"/api/academy/students/{sid}/records", headers=_auth())
    assert rec.status_code == 200
    body = rec.json()
    assert body["student"]["id"] == sid
    assert body["summary"]["lessons_passed"] == 1
    assert len(body["rows"]) == 1
    row = body["rows"][0]
    assert row["status"] == "in_progress"
    assert row["passed_lessons"][0]["title"] == "Lesson 1"
    assert "disclaimer" in body
