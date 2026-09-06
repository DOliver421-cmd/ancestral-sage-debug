"""routers/academy.py — WAI Institute Homeschool Academy API.

Family-model homeschool academy built on the existing account system:
  * A parent = any authenticated MHC account (no new site role).
  * A student = a profile owned by one account (db.academy_students), with a
    grade (K–12) and a track. Students do not log in; parents manage them.
  * Curriculum lives in db.academy_courses (seeded from academy_content).
  * Mastery: each lesson has a knowledge check; a lesson is PASSED at
    >= passing_score (default 80). Lessons unlock in order — lesson N+1
    unlocks only after lesson N is passed. The server enforces this; the UI
    cannot bypass the sequence.
  * Progress lives in db.academy_progress (one doc per student/course/lesson
    with attempts and best score).

Mounted by server.py as an _ADDITIONAL_API_ROUTER_MODULES router under /api
and auto-bound by _bind_router_dependencies().
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["academy"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = current_user = audit = notify = None

GRADES = ["K", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "adult"]
TRACK_KEYS = ["foundations", "builder", "artist", "scholar", "adult_ed", "life_skills", "leadership", "career", "entrepreneurship"]

GRADE_RANK = {g: i for i, g in enumerate(GRADES)}


def bind(_db, _current_user, _audit=None, _notify=None, _assert_role=None):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, notify
    db = _db
    current_user = _current_user
    audit = _audit
    notify = _notify


class _StubUser:
    """Dependency-resolved user shape used by handlers."""
    pass


async def _dep_current_user(authorization: Optional[str] = Header(None)):
    """Resolve the real current_user at REQUEST time (bind() sets it later)."""
    return await current_user(authorization)


async def _dep_optional_user(authorization: Optional[str] = Header(None)):
    """Optional auth: anonymous callers browse public course pages; a provided
    (valid) token is resolved so enrolled owners can see full content."""
    if not authorization:
        return None
    return await current_user(authorization)


# ── Pydantic request models ──────────────────────────────────────────────────
class StudentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    grade: str = Field(min_length=1, max_length=2)
    track: Literal["foundations", "builder", "artist", "scholar"]
    notes: Optional[str] = Field(default=None, max_length=500)


class StudentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    grade: Optional[str] = Field(default=None, min_length=1, max_length=2)
    track: Optional[Literal["foundations", "builder", "artist", "scholar"]] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    status: Optional[Literal["active", "archived"]] = None


class EnrollmentChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    course_slug: str = Field(min_length=1)
    enroll: bool = True


class AttemptSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    student_id: str
    answers: List[int]


# ── Pure domain helpers (unit-tested) ────────────────────────────────────────
def course_applies(course: dict, grade: str, track: str) -> bool:
    """True when a published course is offered to a student of this grade/track."""
    if course.get("status") != "published":
        return False
    if grade not in course.get("grades", []):
        return False
    if track not in course.get("tracks", []):
        return False
    return True


def recommended_courses(courses: List[dict], grade: str, track: str) -> List[dict]:
    """Published courses matching a grade/track, in a stable catalog order."""
    return [
        c for c in courses
        if course_applies(c, grade, track)
    ]


def flatten_lessons(course: dict) -> List[dict]:
    """All lessons with unit context, sorted by their global order."""
    out = []
    for unit in course.get("units", []):
        for lesson in unit.get("lessons", []):
            out.append({**lesson, "_unit_slug": unit.get("slug"), "_unit_title": unit.get("title")})
    out.sort(key=lambda l: (l.get("order", 0), l.get("slug", "")))
    return out


def score_attempt(lesson: dict, answers: List[int], passing_score: int = 80) -> dict:
    """Grade a knowledge-check attempt. Answers are 0-based option indexes.

    Correct option is resolved from the stored EXACT answer string, so content
    edits can never silently move the answer key.
    """
    questions = lesson.get("check", {}).get("questions", [])
    if len(answers) != len(questions):
        raise HTTPException(400, "Answer count mismatch")
    correct = 0
    for i, question in enumerate(questions):
        try:
            expected = question["options"].index(question["answer"])
        except (KeyError, ValueError):
            raise HTTPException(500, f"Content error: lesson {lesson.get('slug')} question {i + 1} answer key broken")
        answer = answers[i]
        if not isinstance(answer, int) or answer < 0 or answer >= len(question["options"]):
            raise HTTPException(400, f"Answer for question {i + 1} out of range")
        if answer == expected:
            correct += 1
    total = len(questions) or 1
    score = round(correct / total * 100, 1) if questions else 0.0
    return {"score": score, "correct": correct, "total": len(questions), "passed": score >= passing_score}


def _passing_score(course: dict) -> int:
    try:
        return int(course.get("passing_score") or 80)
    except (TypeError, ValueError):
        return 80


def _now():
    return datetime.now(timezone.utc).isoformat()


async def _owned_student(student_id: str, user) -> dict:
    doc = await db.academy_students.find_one({"id": student_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Student profile not found")
    if doc.get("parent_user_id") != user.id:
        raise HTTPException(403, "This student profile belongs to another account")
    return doc


async def _course_or_404(slug: str, published_only: bool = True) -> dict:
    doc = await db.academy_courses.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Course not found")
    if published_only and doc.get("status") != "published":
        raise HTTPException(404, "Course not found")
    return doc


async def _enrolled_snapshot(student: dict) -> List[dict]:
    """Return the student's enrolled published course docs (catalog order)."""
    if not student.get("course_slugs"):
        return []
    docs = await db.academy_courses.find(
        {"slug": {"$in": student["course_slugs"]}, "status": "published"},
        {"_id": 0},
    ).to_list(200)
    docs.sort(key=lambda c: student["course_slugs"].index(c["slug"]) if c["slug"] in student["course_slugs"] else 999)
    return docs


async def _progress_map(student_id: str, course_slug: str) -> dict:
    docs = await db.academy_progress.find(
        {"student_id": student_id, "course_slug": course_slug}, {"_id": 0}
    ).to_list(500)
    return {d["lesson_slug"]: d for d in docs}


def _course_stats(course: dict, progress: dict) -> dict:
    lessons = flatten_lessons(course)
    total = len(lessons)
    passed = [l for l in lessons if progress.get(l["slug"], {}).get("status") == "passed"]
    best_scores = [p.get("best_score") for p in progress.values() if p.get("best_score") is not None]
    mastery_avg = round(sum(best_scores) / len(best_scores), 1) if best_scores else None
    return {
        "lessons_total": total,
        "lessons_passed": len(passed),
        "percent": round(len(passed) / total * 100, 1) if total else 0.0,
        "mastery_avg": mastery_avg,
        "completed": total > 0 and len(passed) == total,
    }


def _next_lesson(lessons: List[dict], progress: dict, passing_score: int) -> Optional[dict]:
    """First lesson that is not passed, scanning in order (returns None if all passed)."""
    for lesson in lessons:
        if progress.get(lesson["slug"], {}).get("status") != "passed":
            return lesson
    return None


def _unlock_state(lessons: List[dict], progress: dict) -> dict:
    """Return per-lesson {unlocked, passed, best_score} + current lesson."""
    states = {}
    blocked = False
    current = None
    for lesson in lessons:
        prog = progress.get(lesson["slug"], {})
        passed = prog.get("status") == "passed"
        states[lesson["slug"]] = {
            "unlocked": not blocked,
            "passed": passed,
            "best_score": prog.get("best_score"),
            "attempts": len(prog.get("attempts", [])),
        }
        if not passed and current is None and not blocked:
            current = lesson
        if not passed:
            blocked = True
    return {"states": states, "current": current}


# ── Public catalog ───────────────────────────────────────────────────────────
@router.get("/academy/tracks")
async def academy_tracks():
    from academy_content import TRACKS, SUBJECTS
    return {"tracks": TRACKS, "subjects": SUBJECTS, "grades": GRADES}


@router.get("/academy/courses")
async def list_courses(grade: Optional[str] = None, track: Optional[str] = None,
                       subject: Optional[str] = None, q: Optional[str] = None):
    """Public catalog cards — metadata only (never lesson content)."""
    docs = await db.academy_courses.find({}, {"_id": 0}).to_list(300)
    if grade:
        docs = [c for c in docs if grade in c.get("grades", [])]
    if track:
        docs = [c for c in docs if track in c.get("tracks", [])]
    if subject:
        docs = [c for c in docs if c.get("subject") == subject]
    if q:
        needle = q.strip().lower()
        docs = [
            c for c in docs
            if needle in (c.get("title") or "").lower()
            or needle in (c.get("summary") or "").lower()
            or needle in (c.get("description") or "").lower()
        ]
    docs.sort(key=lambda c: (c.get("track", ""), c.get("grades", [""])[0] if c.get("grades") else "", c.get("title", "")))
    cards = []
    for c in docs:
        lesson_count = sum(len(u.get("lessons", [])) for u in c.get("units", []))
        cards.append({
            "slug": c["slug"],
            "title": c["title"],
            "summary": c["summary"],
            "description": c["description"],
            "subject": c.get("subject"),
            "subject_label": c.get("subject_label"),
            "track": c.get("track"),
            "tracks": c.get("tracks", []),
            "grades": c.get("grades", []),
            "grade_label": c.get("grade_label"),
            "status": c.get("status", "planned"),
            "audience": c.get("audience", ""),
            "est_hours": c.get("est_hours", 0),
            "lesson_count": lesson_count,
            "objectives": c.get("learning_objectives", []),
        })
    return {"courses": cards, "count": len(cards)}


@router.get("/academy/courses/{slug}")
async def course_detail(slug: str, user=Depends(_dep_optional_user)):
    """Course page data.

    Public for browsing, but full lesson MATERIAL + knowledge-check keys are
    served only to the owner of an enrolled student. Everyone else receives the
    course description, objectives, and the unit/lesson map (titles only).
    """
    course = await db.academy_courses.find_one({"slug": slug}, {"_id": 0})
    if not course:
        raise HTTPException(404, "Course not found")

    include_content = False
    if getattr(user, "id", None):
        mine = await db.academy_students.find_one(
            {"parent_user_id": user.id, "status": "active", "course_slugs": slug},
            {"_id": 0},
        )
        include_content = bool(mine)

    units_out = []
    for unit in course.get("units", []):
        lessons_out = []
        for lesson in unit.get("lessons", []):
            base = {
                "slug": lesson["slug"],
                "title": lesson["title"],
                "order": lesson.get("order"),
                "minutes": lesson.get("minutes"),
                "summary": lesson.get("summary", ""),
            }
            if include_content:
                base["learn"] = lesson.get("learn", [])
                base["check"] = lesson.get("check", {})
            lessons_out.append(base)
        units_out.append({
            "slug": unit.get("slug"),
            "title": unit.get("title"),
            "summary": unit.get("summary", ""),
            "order": unit.get("order"),
            "lessons": lessons_out,
        })
    payload = {
        "slug": course["slug"],
        "title": course["title"],
        "summary": course.get("summary", ""),
        "description": course.get("description", ""),
        "subject": course.get("subject"),
        "subject_label": course.get("subject_label"),
        "track": course.get("track"),
        "tracks": course.get("tracks", []),
        "grades": course.get("grades", []),
        "grade_label": course.get("grade_label"),
        "status": course.get("status", "planned"),
        "audience": course.get("audience", ""),
        "est_hours": course.get("est_hours", 0),
        "passing_score": _passing_score(course),
        "objectives": course.get("learning_objectives", []),
        "units": units_out,
        "content_visible": include_content,
    }
    return payload


# ── Student profiles (owner-scoped) ──────────────────────────────────────────
@router.get("/academy/students")
async def list_students(user=Depends(_dep_current_user)):
    docs = await db.academy_students.find(
        {"parent_user_id": user.id}, {"_id": 0}
    ).to_list(100)
    docs.sort(key=lambda s: (s.get("status") != "active", s.get("created_at", "")))
    return {"students": docs}


@router.post("/academy/students")
async def create_student(body: StudentCreate, user=Depends(_dep_current_user)):
    if body.grade not in GRADES:
        raise HTTPException(400, f"grade must be one of {', '.join(GRADES)}")
    if body.track not in TRACK_KEYS:
        raise HTTPException(400, "track must be foundations, builder, artist, or scholar")

    courses = await db.academy_courses.find({}, {"_id": 0}).to_list(300)
    enrolled = [c["slug"] for c in recommended_courses(courses, body.grade, body.track)]

    now = _now()
    doc = {
        "id": str(uuid.uuid4()),
        "parent_user_id": user.id,
        "name": body.name.strip(),
        "grade": body.grade,
        "track": body.track,
        "notes": body.notes,
        "course_slugs": enrolled,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    await db.academy_students.insert_one(doc)
    if audit is not None:
        try:
            await audit(user.id, "academy.student.create", target=doc["id"],
                        meta={"name": doc["name"], "grade": body.grade, "track": body.track})
        except Exception:
            logger.exception("academy.student.create audit failed")
    doc.pop("_id", None)
    return {"student": doc, "auto_enrolled": enrolled}


@router.patch("/academy/students/{student_id}")
async def update_student(student_id: str, body: StudentUpdate, user=Depends(_dep_current_user)):
    student = await _owned_student(student_id, user)
    update = {"updated_at": _now()}
    if body.name is not None:
        update["name"] = body.name.strip()
    if body.notes is not None:
        update["notes"] = body.notes
    if body.status is not None:
        update["status"] = body.status
    if body.grade is not None and body.grade != student.get("grade"):
        if body.grade not in GRADES:
            raise HTTPException(400, f"grade must be one of {', '.join(GRADES)}")
        update["grade"] = body.grade
    if body.track is not None and body.track != student.get("track"):
        update["track"] = body.track
    if "grade" in update or "track" in update:
        # Recompute the recommended enrollment set for the new grade/track,
        # keeping previous enrollments that still apply to the new placement.
        courses = await db.academy_courses.find({}, {"_id": 0}).to_list(300)
        new_grade = update.get("grade", student.get("grade"))
        new_track = update.get("track", student.get("track"))
        by_slug = {c["slug"]: c for c in courses}
        auto = {c["slug"] for c in recommended_courses(courses, new_grade, new_track)}
        prev = set(student.get("course_slugs", []))
        still_fit = {s for s in prev if course_applies(by_slug.get(s, {}), new_grade, new_track)}
        update["course_slugs"] = sorted(auto | still_fit)
    await db.academy_students.update_one({"id": student_id}, {"$set": update})
    updated = await db.academy_students.find_one({"id": student_id}, {"_id": 0})
    if audit is not None:
        try:
            await audit(user.id, "academy.student.update", target=student_id,
                        meta={k: v for k, v in update.items() if k in ("name", "grade", "track", "status", "course_slugs")})
        except Exception:
            logger.exception("academy.student.update audit failed")
    return {"student": updated}


@router.delete("/academy/students/{student_id}")
async def archive_student(student_id: str, user=Depends(_dep_current_user)):
    student = await _owned_student(student_id, user)
    await db.academy_students.update_one(
        {"id": student_id}, {"$set": {"status": "archived", "updated_at": _now()}}
    )
    return {"ok": True, "archived": student["name"]}


@router.post("/academy/students/{student_id}/courses")
async def change_enrollment(student_id: str, body: EnrollmentChange, user=Depends(_dep_current_user)):
    student = await _owned_student(student_id, user)
    course = await _course_or_404(body.course_slug)
    slugs = set(student.get("course_slugs", []))
    if body.enroll:
        if not course_applies(course, student.get("grade"), student.get("track")):
            raise HTTPException(400, "This course is not offered for the student's grade and track.")
        slugs.add(course["slug"])
    else:
        slugs.discard(course["slug"])
    await db.academy_students.update_one(
        {"id": student_id},
        {"$set": {"course_slugs": sorted(slugs), "updated_at": _now()}},
    )
    return {"student_id": student_id, "course_slugs": sorted(slugs)}


# ── Dashboards ───────────────────────────────────────────────────────────────
@router.get("/academy/students/{student_id}/dashboard")
async def student_dashboard(student_id: str, user=Depends(_dep_current_user)):
    student = await _owned_student(student_id, user)
    enrolled = await _enrolled_snapshot(student)
    course_cards = []
    for course in enrolled:
        progress = await _progress_map(student_id, course["slug"])
        lessons = flatten_lessons(course)
        stats = _course_stats(course, progress)
        next_up = _next_lesson(lessons, progress, _passing_score(course))
        course_cards.append({
            "slug": course["slug"],
            "title": course["title"],
            "summary": course.get("summary", ""),
            "subject": course.get("subject"),
            "subject_label": course.get("subject_label"),
            "grade_label": course.get("grade_label"),
            "passing_score": _passing_score(course),
            "stats": stats,
            "next_lesson": {
                "slug": next_up["slug"],
                "title": next_up["title"],
                "order": next_up.get("order"),
                "unit_title": next_up.get("_unit_title"),
            } if next_up else None,
        })
    records = {
        "courses_enrolled": len(enrolled),
        "courses_completed": sum(1 for c in course_cards if c["stats"]["completed"]),
        "lessons_passed": sum(c["stats"]["lessons_passed"] for c in course_cards),
        "lessons_total": sum(c["stats"]["lessons_total"] for c in course_cards),
        "overall_percent": round(
            sum(c["stats"]["lessons_passed"] for c in course_cards)
            / max(1, sum(c["stats"]["lessons_total"] for c in course_cards)) * 100, 1
        ),
    }
    return {"student": student, "courses": course_cards, "records": records}


@router.get("/academy/courses/{slug}/learn")
async def course_learn(slug: str, student: Optional[str] = None, user=Depends(_dep_current_user)):
    """Full course content for an owned, enrolled student, with unlock states."""
    course = await _course_or_404(slug)
    if not student:
        # Default to the first active student of this account enrolled in the course.
        mine = await db.academy_students.find_one(
            {"parent_user_id": user.id, "status": "active", "course_slugs": slug},
            {"_id": 0},
        )
        student_id = mine["id"] if mine else None
    else:
        student_id = student
    if not student_id:
        raise HTTPException(403, "Enroll a student profile in this course to start learning.")

    student_doc = await _owned_student(student_id, user)
    if slug not in student_doc.get("course_slugs", []):
        raise HTTPException(403, "This course is not on the student's enrollment.")

    progress = await _progress_map(student_id, slug)
    lessons = flatten_lessons(course)
    unlock = _unlock_state(lessons, progress)

    units_out = []
    for unit in course.get("units", []):
        unit_lessons = []
        for lesson in unit.get("lessons", []):
            state = unlock["states"].get(lesson["slug"], {})
            unit_lessons.append({
                "slug": lesson["slug"],
                "title": lesson["title"],
                "order": lesson.get("order"),
                "minutes": lesson.get("minutes"),
                "summary": lesson.get("summary", ""),
                "unlocked": state.get("unlocked", False),
                "passed": state.get("passed", False),
                "best_score": state.get("best_score"),
                "attempts": state.get("attempts", 0),
                "learn": lesson.get("learn", []),
                "check": lesson.get("check", {}),
            })
        units_out.append({
            "slug": unit.get("slug"),
            "title": unit.get("title"),
            "summary": unit.get("summary", ""),
            "order": unit.get("order"),
            "lessons": unit_lessons,
        })

    current = unlock["current"]
    payload = {
        "student_id": student_id,
        "course": {
            "slug": course["slug"],
            "title": course["title"],
            "summary": course.get("summary", ""),
            "subject_label": course.get("subject_label"),
            "grade_label": course.get("grade_label"),
            "passing_score": _passing_score(course),
            "objectives": course.get("learning_objectives", []),
        },
        "units": units_out,
        "current_lesson": {
            "slug": current["slug"],
            "title": current["title"],
            "order": current.get("order"),
        } if current else None,
        "course_completed": current is None and bool(lessons),
    }
    return payload


@router.post("/academy/courses/{slug}/lessons/{lesson_slug}/attempt")
async def submit_attempt(slug: str, lesson_slug: str, body: AttemptSubmit,
                         user=Depends(_dep_current_user)):
    course = await _course_or_404(slug)
    student = await _owned_student(body.student_id, user)
    if slug not in student.get("course_slugs", []):
        raise HTTPException(403, "This course is not on the student's enrollment.")

    lessons = flatten_lessons(course)
    lesson = next((l for l in lessons if l["slug"] == lesson_slug), None)
    if not lesson:
        raise HTTPException(404, "Lesson not found in this course")
    if not lesson.get("check", {}).get("questions"):
        raise HTTPException(500, "Content error: lesson has no knowledge check")

    progress = await _progress_map(body.student_id, slug)
    existing = progress.get(lesson_slug)
    if existing and existing.get("status") == "passed":
        raise HTTPException(409, "This lesson is already passed — move on to the next one.")

    # Enforce the sequence: every earlier lesson must be passed before this one.
    passing_score = _passing_score(course)
    for earlier in lessons:
        if earlier["slug"] == lesson_slug:
            break
        if progress.get(earlier["slug"], {}).get("status") != "passed":
            raise HTTPException(
                403,
                f"Locked — complete and pass '{earlier['title']}' first.",
            )

    result = score_attempt(lesson, body.answers, passing_score)
    now = _now()
    attempt = {
        "score": result["score"],
        "correct": result["correct"],
        "total": result["total"],
        "passed": result["passed"],
        "at": now,
    }
    status_val = "passed" if result["passed"] else "in_progress"
    attempt_number = len(existing.get("attempts", [])) + 1 if existing else 1
    prior = existing or {}
    update = {
        "status": status_val,
        "best_score": result["score"] if result["passed"] else max(
            prior.get("best_score") or 0, result["score"]
        ),
        "passed_at": now if result["passed"] else prior.get("passed_at"),
        "updated_at": now,
    }
    await db.academy_progress.update_one(
        {"student_id": body.student_id, "course_slug": slug, "lesson_slug": lesson_slug},
        {"$set": update, "$push": {"attempts": attempt},
         "$setOnInsert": {"id": str(uuid.uuid4())}},
        upsert=True,
    )

    # Next lesson / course completion for the response.
    merged = {
        **prior,
        **update,
        "attempts": prior.get("attempts", []) + [attempt],
    }
    fresh = {**progress, lesson_slug: merged}
    next_up = None
    course_completed = False
    if result["passed"]:
        remaining = _next_lesson(lessons, fresh, passing_score)
        if remaining:
            next_up = {"slug": remaining["slug"], "title": remaining["title"], "order": remaining.get("order")}
        else:
            course_completed = True

    return {
        **result,
        "required": passing_score,
        "attempt_number": attempt_number,
        "lesson_completed": result["passed"],
        "course_completed": course_completed,
        "next_lesson": next_up,
    }


# ── Records / transcripts ────────────────────────────────────────────────────
@router.get("/academy/students/{student_id}/records")
async def student_records(student_id: str, user=Depends(_dep_current_user)):
    """Printable student educational records / progress documentation.

    Explicitly NOT a legal transcript: it documents actual activity and
    mastery inside the Academy (see HOMESCHOOL_ACADEMY_BUILD_PLAN.md).
    """
    student = await _owned_student(student_id, user)
    enrolled = await _enrolled_snapshot(student)
    rows = []
    for course in enrolled:
        progress = await _progress_map(student_id, course["slug"])
        lessons = flatten_lessons(course)
        stats = _course_stats(course, progress)
        passed_lessons = [
            {
                "title": l["title"],
                "score": progress.get(l["slug"], {}).get("best_score"),
                "passed_at": progress.get(l["slug"], {}).get("passed_at"),
            }
            for l in lessons if progress.get(l["slug"], {}).get("status") == "passed"
        ]
        rows.append({
            "course_slug": course["slug"],
            "course_title": course["title"],
            "subject": course.get("subject"),
            "subject_label": course.get("subject_label"),
            "grade_label": course.get("grade_label"),
            "passing_score": _passing_score(course),
            "stats": stats,
            "status": "completed" if stats["completed"] else ("in_progress" if stats["lessons_passed"] else "not_started"),
            "passed_lessons": passed_lessons,
        })
    return {
        "student": student,
        "generated_at": _now(),
        "rows": rows,
        "summary": {
            "courses_completed": sum(1 for r in rows if r["status"] == "completed"),
            "courses_in_progress": sum(1 for r in rows if r["status"] == "in_progress"),
            "lessons_passed": sum(r["stats"]["lessons_passed"] for r in rows),
            "lessons_total": sum(r["stats"]["lessons_total"] for r in rows),
        },
        "disclaimer": (
            "This document records activity and mastery inside the WAI Institute "
            "Homeschool Academy at MoreHelp Center. It is an educational progress "
            "record, not a state-recognized transcript or credential."
        ),
    }


# ═════════════════════════════════════════════════════════════════════════════
# Academy-scoped communication (learner ↔ instructor)
# ═════════════════════════════════════════════════════════════════════════════
class AcademyMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to_user_id: str = Field(min_length=1)
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5000)
    academy_student_id: Optional[str] = Field(default=None)
    course_slug: Optional[str] = Field(default=None)
    kind: Literal["message", "intervention", "feedback"] = "message"
    parent_message_id: Optional[str] = Field(default=None)


@router.post("/academy/messages")
async def send_academy_message(payload: AcademyMessage, user: dict = Depends(_dep_current_user)):
    now = _now()
    msg = {
        "id": str(uuid.uuid4()),
        "from_user_id": user.id,
        "to_user_id": payload.to_user_id,
        "academy_student_id": payload.academy_student_id,
        "course_slug": payload.course_slug,
        "subject": payload.subject,
        "body": payload.body,
        "kind": payload.kind,
        "parent_message_id": payload.parent_message_id,
        "read": False,
        "created_at": now,
    }
    await db.academy_messages.insert_one(msg)
    if audit:
        try:
            await audit(user.id, "academy.message.send", target=payload.to_user_id, meta={"kind": payload.kind, "student_id": payload.academy_student_id})
        except Exception:
            logger.exception("audit failed")
    return {"message": msg}


@router.get("/academy/messages")
async def list_academy_messages(
    user: dict = Depends(_dep_current_user),
    academy_student_id: Optional[str] = None,
    kind: Optional[str] = None,
):
    q = {"$or": [{"from_user_id": user.id}, {"to_user_id": user.id}]}
    if academy_student_id:
        q["academy_student_id"] = academy_student_id
    if kind:
        q["kind"] = kind
    docs = await db.academy_messages.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"messages": docs}


@router.post("/academy/messages/{mid}/read")
async def read_academy_message(mid: str, user: dict = Depends(_dep_current_user)):
    await db.academy_messages.update_one({"id": mid, "to_user_id": user.id}, {"$set": {"read": True}})
    return {"ok": True}


# ═════════════════════════════════════════════════════════════════════════════
# Instructor Academy workflow
# ═════════════════════════════════════════════════════════════════════════════
@router.get("/academy/instructor/learners")
async def instructor_learners(user: dict = Depends(_require_rank("instructor", "admin"))):
    """List Academy students visible to the instructor, with aggregate progress."""
    students = await db.academy_students.find({"status": "active"}, {"_id": 0}).to_list(500)
    out = []
    for s in students:
        progress_docs = await db.academy_progress.find({"student_id": s["id"]}, {"_id": 0}).to_list(1000)
        lessons_passed = sum(1 for p in progress_docs if p.get("status") == "passed")
        lessons_total = len(progress_docs)
        avg_score = 0.0
        scores = [p.get("best_score") for p in progress_docs if p.get("best_score") is not None]
        if scores:
            avg_score = round(sum(scores) / len(scores), 1)
        out.append({
            "id": s["id"],
            "name": s.get("name"),
            "grade": s.get("grade"),
            "track": s.get("track"),
            "course_slugs": s.get("course_slugs", []),
            "lessons_passed": lessons_passed,
            "lessons_total": lessons_total,
            "avg_score": avg_score,
            "updated_at": s.get("updated_at"),
        })
    return {"learners": out}


@router.get("/academy/instructor/learners/{student_id}/progress")
async def instructor_learner_progress(student_id: str, user: dict = Depends(_require_rank("instructor", "admin"))):
    student = await db.academy_students.find_one({"id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(404, "Student not found")
    course_slugs = student.get("course_slugs", [])
    courses = await db.academy_courses.find({"slug": {"$in": course_slugs}}, {"_id": 0}).to_list(100)
    progress_docs = await db.academy_progress.find({"student_id": student_id}, {"_id": 0}).to_list(1000)
    progress_map = {p["lesson_slug"]: p for p in progress_docs}
    rows = []
    for course in courses:
        lessons = flatten_lessons(course)
        passed = 0
        for lesson in lessons:
            p = progress_map.get(lesson["slug"], {})
            if p.get("status") == "passed":
                passed += 1
        rows.append({
            "course_slug": course["slug"],
            "course_title": course.get("title"),
            "lessons_total": len(lessons),
            "lessons_passed": passed,
            "percent": round(passed / len(lessons) * 100, 1) if lessons else 0.0,
        })
    return {
        "student": student,
        "courses": rows,
        "progress_map": progress_map,
    }


@router.post("/academy/instructor/interventions")
async def create_intervention(payload: dict, user: dict = Depends(_require_rank("instructor", "admin"))):
    """Record an instructor intervention for a learner."""
    student_id = payload.get("student_id")
    kind = payload.get("kind", "review")
    note = payload.get("note", "")
    course_slug = payload.get("course_slug")
    if not student_id:
        raise HTTPException(400, "student_id is required")
    intervention = {
        "id": str(uuid.uuid4()),
        "instructor_id": user.id,
        "student_id": student_id,
        "kind": kind,
        "note": note,
        "course_slug": course_slug,
        "outcome": None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.academy_interventions.insert_one(intervention)
    if audit:
        try:
            await audit(user.id, "academy.intervention.create", target=student_id, meta={"kind": kind, "course_slug": course_slug})
        except Exception:
            logger.exception("audit failed")
    return {"intervention": intervention}


@router.get("/academy/instructor/interventions")
async def list_interventions(user: dict = Depends(_require_rank("instructor", "admin")), student_id: Optional[str] = None):
    q = {"instructor_id": user.id}
    if student_id:
        q["student_id"] = student_id
    docs = await db.academy_interventions.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"interventions": docs}

