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
from typing import List, Literal, Optional, Tuple

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from academy_content.enrichment import all_resources

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["academy"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = current_user = audit = notify = None

GRADES = ["K", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "adult"]
TRACK_KEYS = ["foundations", "builder", "artist", "scholar", "adult_ed", "life_skills", "leadership", "career", "entrepreneurship"]

GRADE_RANK = {g: i for i, g in enumerate(GRADES)}

# ── Curriculum catalogue classification (grade-first, per owner spec) ─────────
CORE_SUBJECTS = {"ela", "math", "science", "social_studies"}
NON_GRADE_CATEGORIES = {"adult", "trade", "creative"}
GRADE_ORDER = ["K", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "adult"]

def derive_category(course: dict) -> str:
    """Top-level bucket: k12_core | k12_elective | adult | trade | creative."""
    track = course.get("track", "")
    subject = course.get("subject", "")
    grades = course.get("grades", [])
    # Non-grade buckets win first — they are never K-12 electives
    if track in ("builder",) or subject == "trade":
        # builder/track trade courses belong in Trade even if grade-tagged
        # but keep K-12 numbered grades as electives if they also carry grade
        if any(g in GRADES and g != "adult" for g in grades) and subject == "trade":
            # trade-math-grade-8 style: grade-specific trade elective
            return "trade"
        return "trade"
    if track in ("artist",) or subject == "art":
        return "creative"
    if track in ("adult_ed", "life_skills", "leadership", "career", "entrepreneurship") or "adult" in grades:
        return "adult"
    # Remaining K-12 courses: core vs elective by subject
    if subject in CORE_SUBJECTS:
        return "k12_core"
    return "k12_elective"

def derive_course_type(course: dict) -> str:
    cat = derive_category(course)
    if cat == "k12_core":
        return "core"
    if cat == "k12_elective":
        return "elective"
    # non-grade buckets carry their own type label (used as secondary filter)
    return cat

def enrich_course_card(c: dict) -> dict:
    """Attach derived catalogue fields used by filtering + audit."""
    c["category"] = derive_category(c)
    c["course_type"] = derive_course_type(c)
    # primary grade_level for card grouping: first non-adult grade or adult
    gl = c.get("grades", [])
    c["grade_level"] = gl[0] if gl else "adult" if c["category"] == "adult" else ""
    c["subject_key"] = c.get("subject", "")
    return c


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


async def _dep_optional_current_user(authorization: Optional[str] = Header(None)):
    """Optional auth: anonymous callers browse public course pages; a provided
    (valid) token is resolved so enrolled owners can see full content."""
    if not authorization:
        return None
    return await current_user(authorization)


def _require_rank(*roles):
    async def _dep(authorization: Optional[str] = Header(None)):
        user = await _dep_current_user(authorization)
        if not user:
            raise HTTPException(401, "Sign in or register to access this content.")
        user_role = getattr(user, "role", "student")
        if user_role not in set(roles):
            raise HTTPException(403, f"Required role: {', '.join(roles)}")
        return user
    return _dep


# ── Pydantic request models ──────────────────────────────────────────────────
class StudentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    # "adult" is a valid grade alongside K-12, so this must not be capped at 2.
    grade: str = Field(min_length=1, max_length=10)
    # Every track the catalog actually ships (TRACK_KEYS). Kept as `str` with
    # an explicit check in the handler so an unknown track returns a readable
    # 400 string — not a pydantic 422 detail array, which the client cannot
    # render (it crashes the page with "Objects are not valid as a React child").
    track: str = Field(min_length=1, max_length=40)
    notes: Optional[str] = Field(default=None, max_length=500)


class StudentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    grade: Optional[str] = Field(default=None, min_length=1, max_length=10)
    track: Optional[str] = Field(default=None, min_length=1, max_length=40)
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
@router.get("/academy/curriculum-audit")
async def curriculum_audit():
    """Per-grade completeness: required cores vs present, missing subjects.
    Uses published courses only; planned counts as missing."""
    docs = await db.academy_courses.find({"status": "published"}, {"_id": 0}).to_list(500)
    # index grade -> set(subjects present as core)
    grade_subjects: dict = {g: set() for g in GRADES if g != "adult"}
    grade_course_counts: dict = {g: 0 for g in GRADES if g != "adult"}
    for c in docs:
        if derive_category(c) != "k12_core":
            continue
        for g in c.get("grades", []):
            if g in grade_subjects:
                grade_subjects[g].add(c.get("subject"))
                grade_course_counts[g] += 1
    required = sorted(CORE_SUBJECTS)
    rows = []
    for g in [x for x in GRADES if x != "adult"]:
        present = sorted(grade_subjects[g])
        missing = sorted(set(required) - grade_subjects[g])
        rows.append({
            "grade": g,
            "grade_label": "Kindergarten" if g == "K" else f"Grade {g}",
            "required": required,
            "required_count": len(required),
            "present": present,
            "present_count": len(present),
            "missing": missing,
            "status": "COMPLETE" if not missing else "INCOMPLETE",
        })
    # non-grade buckets summary
    buckets = {k: 0 for k in ["adult", "trade", "creative"]}
    for c in docs:
        cat = derive_category(c)
        if cat in buckets:
            buckets[cat] += 1
        elif cat == "trade":
            buckets["trade"] += 1
        elif cat == "creative":
            buckets["creative"] += 1
    return {"grades": rows, "buckets": buckets, "core_subjects": required}


@router.get("/academy/tracks")
async def academy_tracks():
    from academy_content import TRACKS, SUBJECTS
    return {"tracks": TRACKS, "subjects": SUBJECTS, "grades": GRADES, "core_subjects": sorted(CORE_SUBJECTS), "categories": ["k12_core", "k12_elective", "adult", "trade", "creative"]}


@router.get("/academy/courses")
async def list_courses(grade: Optional[str] = None, track: Optional[str] = None,
                       subject: Optional[str] = None, q: Optional[str] = None,
                       category: Optional[str] = None, course_type: Optional[str] = None):
    """Public catalog cards — metadata only (never lesson content).
    Filters: grade, track, subject, q, category (k12_core|k12_elective|adult|trade|creative),
    course_type (core|elective|adult|trade|creative). Enriches each card with category/course_type/grade_level/subject_key."""
    docs = await db.academy_courses.find({}, {"_id": 0}).to_list(300)
    # enrich for filtering
    for c in docs:
        enrich_course_card(c)
    if grade:
        docs = [c for c in docs if grade in c.get("grades", [])]
    if track:
        docs = [c for c in docs if track in c.get("tracks", [])]
    if subject:
        docs = [c for c in docs if c.get("subject") == subject]
    if category:
        docs = [c for c in docs if c.get("category") == category]
    if course_type:
        docs = [c for c in docs if c.get("course_type") == course_type]
    if q:
        needle = q.strip().lower()
        docs = [
            c for c in docs
            if needle in (c.get("title") or "").lower()
            or needle in (c.get("summary") or "").lower()
            or needle in (c.get("description") or "").lower()
        ]
    docs.sort(key=lambda c: (GRADE_ORDER.index(c.get("grade_level", "99")) if c.get("grade_level") in GRADE_ORDER else 99, c.get("course_type", ""), c.get("title", "")))
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
            "grade_level": c.get("grade_level"),
            "category": c.get("category"),
            "course_type": c.get("course_type"),
            "subject_key": c.get("subject_key"),
            "status": c.get("status", "planned"),
            "audience": c.get("audience", ""),
            "est_hours": c.get("est_hours", 0),
            "lesson_count": lesson_count,
            "objectives": c.get("learning_objectives", []),
        })
    # Real enrichment coverage per course, so the staff tracker reads the
    # content module instead of a hand-maintained copy of it.
    video_coverage = {}
    for c in docs:
        vids = c.get("enrichment_videos", []) or []
        ready = [v for v in vids if v.get("status") == "ready"]
        video_coverage[c["slug"]] = {
            # "ready" videos are embedded on the course page regardless of
            # whether their ID has been confirmed — the unverified ones carry a
            # note. Counting them separately here would under-report coverage.
            "embedded": len(ready),
            "unverified": sum(1 for v in ready if v.get("suspect")),
            "pending_ids": sum(1 for v in vids if v.get("status") == "no_id"),
        }
    return {"courses": cards, "count": len(cards), "video_coverage": video_coverage}


@router.get("/academy/courses/{slug}")
async def course_detail(slug: str, user=Depends(_dep_optional_current_user)):
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
        "enrichment_videos": [
            {**v, "unverified": bool(v.get("suspect"))}
            for v in course.get("enrichment_videos", [])
            if v.get("status") == "ready"
        ],
        # Videos with no ID are staff-visible only (the staff tracker shows
        # NEEDS VIDEO ID); there is nothing to embed for a family to see.
        "enrichment_pending_ids": len([
            v for v in course.get("enrichment_videos", []) if v.get("status") == "no_id"
        ]),
        # The curated creator directory documented in enrichment.py as
        # "Educators & Resources" link cards. Defined in the content module but
        # previously never exposed to any endpoint, so no page could show it.
        "educator_resources": all_resources(),
        "enrichment_note": (
            "Curated, publicly accessible educational resources from their creators — not MoreHelp content. "
            "Videos play on-site and never navigate you away."
        ),
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
        raise HTTPException(400, f"track must be one of {', '.join(TRACK_KEYS)}")

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
        if body.track not in TRACK_KEYS:
            raise HTTPException(400, f"track must be one of {', '.join(TRACK_KEYS)}")
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
            "enrichment_videos": [
                v for v in course.get("enrichment_videos", [])
                if v.get("status") == "ready"
            ],
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



# ═════════════════════════════════════════════════════════════════════════════
# Florida homeschool compliance layer (additive; no schema changes).
# Serves three family paths:
#   * FL Home Education Program: Notice of Intent + annual evaluation packet.
#   * Quarterly progress reports (for umbrella schools / families moving from
#     quarterly-reporting states like NY).
#   * Transcript builder (Bright Futures / FDOE submission format).
# NOTE: IHIPs are a New York requirement, not Florida; the IHIP-style plan
# generator is included so families relocating from quarterly/IHIP states
# can still produce one from the same records.
# ═════════════════════════════════════════════════════════════════════════════

class ComplianceDoc(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["notice_of_intent", "quarterly_report", "annual_evaluation", "transcript", "ihip"]
    student_id: str = Field(min_length=1)
    school_year: str = Field(min_length=4, max_length=20, description="e.g. 2026-2027")
    district: Optional[str] = Field(default=None, max_length=120)
    parent_signature: Optional[str] = Field(default=None, max_length=120)
    evaluator_name: Optional[str] = Field(default=None, max_length=120)
    notes: Optional[str] = Field(default=None, max_length=4000)
    period_start: Optional[str] = Field(default=None, max_length=10)
    period_end: Optional[str] = Field(default=None, max_length=10)
    # Notice of Intent requires the child's date of birth and the parent's
    # home address (s. 1002.41, F.S.). Collected here so the generated letter
    # is something a county district can actually file.
    child_dob: Optional[str] = Field(default=None, max_length=40)
    address_line: Optional[str] = Field(default=None, max_length=200)


def _letter_grade(pct) -> Tuple[str, float]:
    """Standard unweighted letter grade from a percentage, for parent-issued
    transcripts. The scale is printed with the document so a reader can check
    the arithmetic rather than take the GPA on trust."""
    try:
        p = float(pct)
    except (TypeError, ValueError):
        return ("—", 0.0)
    for floor, letter, points in ((90, "A", 4.0), (80, "B", 3.0), (70, "C", 2.0), (60, "D", 1.0)):
        if p >= floor:
            return (letter, points)
    return ("F", 0.0)


_COMPLIANCE_DISCLAIMER = (
    "MoreHelp Center is an educational resource provider helping parents manage "
    "their own home education programs. This document was generated from "
    "platform activity records. The parent is the home education program "
    "administrator under Florida law (s. 1002.41, F.S.); submit it to your "
    "county school district or evaluator as appropriate. It is not legal advice."
)


def _compliance_payload(kind: str, student: dict, rows: list, summary: dict, record: Optional[dict] = None) -> dict:
    """Build the content body for each doc kind from real Academy records.

    `record` is the persisted document (school year, period, district, child
    DOB, address). Fields the parent supplied are echoed back so the
    generated document is complete and fileable — a Notice of Intent without
    a date of birth and address is not a filing.
    """
    rec = record or {}
    student_name = (student or {}).get("name") or ""
    child_dob = rec.get("child_dob") or None
    address_line = rec.get("address_line") or None
    district = rec.get("district") or None
    if kind == "notice_of_intent":
        return {
            "title": "Notice of Intent to Establish a Home Education Program",
            "statute": "Section 1002.41, Florida Statutes",
            "body": (
                "This letter provides notice, pursuant to s. 1002.41(1)(b), F.S., "
                "of my intent to establish and maintain a home education program "
                "for the child named below. I understand I am responsible for the "
                "child's educational program and for maintaining a portfolio of "
                "records and materials. Please enroll the student in your district's "
                "home education program."
            ),
            "student_name": student_name,
            "child_dob": child_dob,
            "address_line": address_line,
            "district": district,
            "fields": ["student_name", "child_dob", "address_line", "district"],
            "signature_line": (
                f"Parent / Home Education Program Administrator: "
                f"{rec.get('parent_signature') or '______________________'}  "
                f"Date: ____________"
            ),
        }
    if kind == "quarterly_report":
        return {
            "title": "Quarterly Progress Report",
            "statute": "IHIP-style quarterly reporting (not required by Florida s. 1002.41)",
            "body": "Progress summary for the reporting period below, generated from completed coursework and mastery records.",
            "period": {"start": rec.get("period_start") or None, "end": rec.get("period_end") or None},
            "rows": rows,
            "summary": summary,
        }
    if kind == "annual_evaluation":
        return {
            "title": "Annual Educational Evaluation Packet",
            "statute": "Section 1002.41(1)(f), Florida Statutes",
            "body": (
                "Portfolio summary and activity log prepared for review by a "
                "Florida-certified teacher evaluator, or for submission with a "
                "nationally normed achievement test result. Shows educational "
                "progress commensurate with the child's abilities."
            ),
            "rows": rows,
            "summary": summary,
        }
    if kind == "ihip":
        return {
            "title": "Individualized Home Instruction Plan (IHIP)",
            "statute": "NY CR 100.10 style plan (for families relocating from IHIP states)",
            "body": "Individualized instructional plan derived from the student's enrolled Academy courses.",
            "rows": [
                {
                    "course_title": r["course_title"],
                    "subject": r["subject_label"] or r["subject"],
                    "grade_label": r["grade_label"],
                }
                for r in rows
            ],
        }
    # transcript
    graded = []
    for r in rows:
        total = r["stats"]["lessons_total"]
        if not total:
            continue
        pct = round(100.0 * r["stats"]["lessons_passed"] / total)
        graded.append({
            "course_title": r["course_title"],
            "subject": r["subject_label"] or r["subject"],
            "grade_label": r["grade_label"],
            "progress_pct": pct,
            "avg_mastery": r["stats"].get("avg_score"),
            "status": r["status"],
            "passing_score": r["passing_score"],
        })
    # GPA from the student's ACTUAL mastery scores, on a stated scale. The
    # previous behaviour assigned 4.0 to every completed course, which produced
    # a transcript showing a 4.0 for any student regardless of performance — an
    # accuracy defect on a document a parent signs and submits.
    completed = [g for g in graded if g["status"] == "completed"]
    for g in graded:
        g["grade_letter"], g["grade_points"] = _letter_grade(g["avg_mastery"])
    gpa = round(sum(g["grade_points"] for g in completed) / len(completed), 2) if completed else None
    return {
        "title": "Official High School Transcript (Parent-Issued)",
        "statute": "Prepared for Bright Futures / Florida Department of Education submission",
        "body": (
            "Course list, mastery-based progress percentages, and completion status. "
            "The parent, as school administrator, reviews, signs, and submits this "
            "document to the Florida Department of Education or receiving institution."
        ),
        "graded_courses": graded,
        "unweighted_gpa_completed_only": gpa,
        # The scale is part of the document: a reader can reproduce the number.
        "gpa_scale": "A 90-100 = 4.0 | B 80-89 = 3.0 | C 70-79 = 2.0 | D 60-69 = 1.0 | F below 60 = 0.0 (unweighted)",
        "how_gpa_is_computed": (
            "Unweighted GPA is the sum of each completed course's grade points divided by the number of "
            "completed courses. A course counts as completed when every lesson has been passed at the "
            "course's mastery threshold (80% unless the course states otherwise). Courses still in "
            "progress carry no grade points. This is a parent-issued record, not a state credential."
        ),
        "signature_line": "Parent / School Administrator signature: ______________________  Date: ____________",
    }


@router.post("/academy/compliance/generate")
async def generate_compliance_doc(doc: ComplianceDoc, user: dict = Depends(_dep_current_user)):
    """Generate (and optionally persist) a Florida compliance document."""
    student = await _owned_student(doc.student_id, user)
    enrolled = await _enrolled_snapshot(student)
    rows = []
    for course in enrolled:
        progress = await _progress_map(doc.student_id, course["slug"])
        stats = _course_stats(course, progress)
        rows.append({
            "course_slug": course["slug"],
            "course_title": course["title"],
            "subject": course.get("subject"),
            "subject_label": course.get("subject_label"),
            "grade_label": course.get("grade_label"),
            "passing_score": _passing_score(course),
            "stats": stats,
            "status": "completed" if stats["completed"] else ("in_progress" if stats["lessons_passed"] else "not_started"),
        })
    summary = {
        "courses_completed": sum(1 for r in rows if r["status"] == "completed"),
        "courses_in_progress": sum(1 for r in rows if r["status"] == "in_progress"),
        "lessons_passed": sum(r["stats"]["lessons_passed"] for r in rows),
        "lessons_total": sum(r["stats"]["lessons_total"] for r in rows),
    }
    payload = _compliance_payload(doc.kind, student, rows, summary, {
        "school_year": doc.school_year,
        "district": doc.district,
        "parent_signature": doc.parent_signature,
        "evaluator_name": doc.evaluator_name,
        "notes": doc.notes,
        "period_start": doc.period_start,
        "period_end": doc.period_end,
        "child_dob": doc.child_dob,
        "address_line": doc.address_line,
    })
    record = {
        "id": str(uuid.uuid4()),
        "kind": doc.kind,
        "school_year": doc.school_year,
        "student_id": doc.student_id,
        "parent_user_id": user.id,
        "district": doc.district,
        "parent_signature": doc.parent_signature,
        "evaluator_name": doc.evaluator_name,
        "notes": doc.notes,
        "period_start": doc.period_start,
        "period_end": doc.period_end,
        "child_dob": doc.child_dob,
        "address_line": doc.address_line,
        "payload": payload,
        "generated_at": _now(),
    }
    await db.academy_compliance_docs.insert_one(record)
    if audit:
        try:
            await audit(user.id, "academy.compliance.generate", target=doc.student_id, meta={"kind": doc.kind, "school_year": doc.school_year})
        except Exception:
            logger.exception("audit failed")
    out = {k: v for k, v in record.items() if k != "_id"}
    out["disclaimer"] = _COMPLIANCE_DISCLAIMER
    return {"doc": out}


@router.get("/academy/compliance/docs")
async def list_compliance_docs(user: dict = Depends(_dep_current_user), student_id: Optional[str] = None):
    q = {"parent_user_id": user.id}
    if student_id:
        q["student_id"] = student_id
    docs = await db.academy_compliance_docs.find(q, {"_id": 0}).sort("generated_at", -1).to_list(200)
    return {"docs": docs, "disclaimer": _COMPLIANCE_DISCLAIMER}


# ── Projects: family history, portfolios, and creation-to-earning ─────────────
# A project is a student's own work, owned by the parent account. Projects are
# private to the family by default (the owner's requirement: family
# participation is optional and children's work is never exposed). A submitted
# project becomes a portfolio entry — the evidence half of a transcript.

PROJECT_KINDS = [
    {"id": "family_history", "label": "Family history", "desc": "Oral-history interviews, a family tree, a migration story, recipes, and records."},
    {"id": "research", "label": "Research", "desc": "A primary-source investigation written up for an audience."},
    {"id": "creative", "label": "Creative", "desc": "Poetry, music, visual art, film, or performance."},
    {"id": "performance", "label": "Performance", "desc": "A rehearsed piece performed and recorded."},
    {"id": "build", "label": "Build", "desc": "A physical or digital artifact you made and documented."},
    {"id": "business", "label": "Business concept", "desc": "A plan for a cooperative, a product, or a service."},
]
_PROJECT_STATUSES = ["planning", "in_progress", "review", "submitted"]

# The family-history pathway: a set of concrete steps a student completes to
# build the project. Steps carry their own prompt so a family can run the whole
# project from the page without another document.
FAMILY_HISTORY_STEPS = [
    {
        "id": "interview",
        "title": "Interview an elder",
        "prompt": "Ask three open questions of a parent, grandparent, or elder. Record names, places, and dates exactly as they are said. Ask permission first, and stop whenever they wish.",
        "artifact": "Interview notes or a recording",
    },
    {
        "id": "records",
        "title": "Gather records",
        "prompt": "Collect three documents that exist: birth certificate, deed, photograph, letter, newspaper clipping, military or school record. Note what is missing and why.",
        "artifact": "A copy or a note describing each record",
    },
    {
        "id": "tree",
        "title": "Build the family tree",
        "prompt": "Write down three generations of names, relationships, and places. Mark anything you are unsure of clearly as uncertain rather than guessing.",
        "artifact": "A drawn or typed family tree",
    },
    {
        "id": "migration",
        "title": "Map the migration",
        "prompt": "Draw the route your family took to reach where you live now. Note the push and the pull — why they left, and what they found.",
        "artifact": "A map with labelled moves",
    },
    {
        "id": "story",
        "title": "Write the account",
        "prompt": "Write one page on one person from your research. Use the sources you gathered, and say what is documented and what is uncertain.",
        "artifact": "A one-page written account",
    },
    {
        "id": "submit",
        "title": "Submit for the portfolio",
        "prompt": "Check that every step has an artifact, then submit the project for the parent's review and add it to the portfolio.",
        "artifact": "The completed portfolio entry",
    },
]


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    student_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=160)
    kind: str = Field(min_length=1, max_length=40)
    summary: Optional[str] = Field(default=None, max_length=600)
    course_slug: Optional[str] = Field(default=None, max_length=80)
    status: Optional[Literal["planning", "in_progress", "review", "submitted"]] = None
    # Family-history projects store step artifacts as {step_id: text}
    artifacts: Optional[dict] = None
    notes: Optional[str] = Field(default=None, max_length=4000)


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = Field(default=None, min_length=1, max_length=160)
    summary: Optional[str] = Field(default=None, max_length=600)
    status: Optional[Literal["planning", "in_progress", "review", "submitted"]] = None
    artifacts: Optional[dict] = None
    notes: Optional[str] = Field(default=None, max_length=4000)


def _project_out(p: dict) -> dict:
    """Client shape for a project: plain fields plus derived steps/complete."""
    out = {k: v for k, v in p.items() if not k.startswith("_")}
    out.pop("parent_user_id", None)
    steps = out.get("steps") or []
    out["steps_completed"] = sum(1 for s in steps if s.get("done"))
    out["kind_label"] = next(
        (k["label"] for k in PROJECT_KINDS if k["id"] == out.get("kind")), out.get("kind")
    )
    out["progress_pct"] = round(100 * out["steps_completed"] / len(steps)) if steps else 0
    return out


@router.get("/academy/projects/kinds")
async def list_project_kinds():
    """Public-to-members catalogue of project types. Free by design."""
    return {
        "kinds": PROJECT_KINDS,
        "family_history_steps": FAMILY_HISTORY_STEPS,
        "note": (
            "Projects are private to the family account by default. Nothing is published "
            "or shared unless a parent chooses to share it. Participation by family members "
            "is always optional."
        ),
    }


@router.post("/academy/projects")
async def create_project(body: ProjectCreate, user: dict = Depends(_dep_current_user)):
    if body.kind not in {k["id"] for k in PROJECT_KINDS}:
        raise HTTPException(400, f"kind must be one of {', '.join(k['id'] for k in PROJECT_KINDS)}")
    await _owned_student(body.student_id, user)
    kind = body.kind
    steps = []
    if kind == "family_history":
        # Seed the family-history pathway with the standard steps.
        steps = [{"id": s["id"], "title": s["title"], "artifact": s["artifact"],
                  "prompt": s["prompt"], "done": False} for s in FAMILY_HISTORY_STEPS]
    artifacts = {
        k: v for k, v in dict(body.artifacts or {}).items()
        if k in {s["id"] for s in steps} and isinstance(v, str) and len(v) <= 20000
    }
    record = {
        "id": str(uuid.uuid4()),
        "student_id": body.student_id,
        "parent_user_id": user.id,
        "title": body.title,
        "kind": kind,
        "summary": body.summary,
        "course_slug": body.course_slug,
        "status": body.status or "planning",
        "steps": [{**s, "done": bool(artifacts.get(s["id"]))} for s in steps],
        "artifacts": body.artifacts or {},
        "notes": body.notes,
        "created_at": _now(),
        "updated_at": _now(),
        "submitted_at": None,
        "visibility": "family",   # never public without an explicit parent action
    }
    await db.academy_projects.insert_one(record)
    if audit:
        try:
            await audit(user.id, "academy.project.create", target=body.student_id, meta={"kind": kind})
        except Exception:
            logger.exception("audit failed")
    return {"project": _project_out(record)}


@router.get("/academy/projects")
async def list_projects(user: dict = Depends(_dep_current_user), student_id: Optional[str] = None):
    if student_id:
        # Same ownership rule as every other Academy surface.
        await _owned_student(student_id, user)
        q = {"student_id": student_id, "parent_user_id": user.id}
    else:
        q = {"parent_user_id": user.id}
    projects = await db.academy_projects.find(q, {"_id": 0}).sort("updated_at", -1).to_list(300)
    return {"projects": [_project_out(p) for p in projects]}


@router.get("/academy/projects/{project_id}")
async def get_project(project_id: str, user: dict = Depends(_dep_current_user)):
    p = await _owned_project(project_id, user)
    return {"project": _project_out(p)}


@router.patch("/academy/projects/{project_id}")
async def update_project(project_id: str, body: ProjectUpdate, user: dict = Depends(_dep_current_user)):
    p = await _owned_project(project_id, user)
    update = {"updated_at": _now()}
    if body.title is not None:
        update["title"] = body.title
    if body.summary is not None:
        update["summary"] = body.summary
    if body.status is not None:
        update["status"] = body.status
    if body.notes is not None:
        update["notes"] = body.notes
    if body.artifacts is not None:
        # Store only artifacts for steps that exist on THIS project. Anything
        # else — arbitrary keys, non-text values, oversized values — is dropped,
        # so no unexpected structure can be written into a student's record.
        valid_steps = {s["id"] for s in (p.get("steps") or []) if isinstance(s.get("id"), str)}
        # MERGE with what is already saved: a parent filling the pathway in
        # step order saves one artifact at a time, and replacing the whole map
        # on every save silently discarded the earlier steps (1 of 6
        # completed). Sending a step's artifact as an empty string clears it.
        safe = dict(p.get("artifacts") or {})
        for k, v in dict(body.artifacts).items():
            if (
                isinstance(k, str) and k in valid_steps
                and isinstance(v, str) and len(v) <= 20000
            ):
                if v.strip():
                    safe[k] = v
                else:
                    safe.pop(k, None)
        update["artifacts"] = safe
        steps = p.get("steps") or []
        if steps:
            # A step with an artifact is complete; clearing it reopens the step.
            update["steps"] = [
                {**s, "done": bool(safe.get(s["id"]))} for s in steps
            ]
    if update and len(update) > 1:
        await db.academy_projects.update_one({"id": project_id}, {"$set": update})
        p = await _owned_project(project_id, user)
    return {"project": _project_out(p)}


@router.post("/academy/projects/{project_id}/submit")
async def submit_project(project_id: str, user: dict = Depends(_dep_current_user)):
    """Move a project to the parent's review, and to the portfolio on their word."""
    p = await _owned_project(project_id, user)
    steps = p.get("steps") or []
    missing = [s["title"] for s in steps if not s.get("done")]
    if missing:
        raise HTTPException(400, f"Add the missing work first: {', '.join(missing)}")
    now = _now()
    await db.academy_projects.update_one(
        {"id": project_id}, {"$set": {"status": "submitted", "submitted_at": now, "updated_at": now}}
    )
    p = await _owned_project(project_id, user)
    if audit:
        try:
            await audit(user.id, "academy.project.submit", target=project_id)
        except Exception:
            logger.exception("audit failed")
    return {"project": _project_out(p), "portfolio_entry": _portfolio_entry(p)}


@router.delete("/academy/projects/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(_dep_current_user)):
    await _owned_project(project_id, user)
    await db.academy_projects.delete_one({"id": project_id})
    if audit:
        try:
            await audit(user.id, "academy.project.delete", target=project_id)
        except Exception:
            logger.exception("audit failed")
    return {"ok": True}


@router.get("/academy/portfolio")
async def get_portfolio(user: dict = Depends(_dep_current_user), student_id: Optional[str] = None):
    """The portfolio half of the record: submitted projects, ready to print."""
    if student_id:
        await _owned_student(student_id, user)
        q = {"student_id": student_id, "parent_user_id": user.id}
    else:
        q = {"parent_user_id": user.id}
    submitted = await db.academy_projects.find(
        {**q, "status": "submitted"}, {"_id": 0}
    ).sort("submitted_at", -1).to_list(300)
    student = await _owned_student(student_id, user) if student_id else None
    return {
        "student": student,
        "entries": [_portfolio_entry(p) for p in submitted],
        "privacy": (
            "Private to this family account. Nothing here is public, shared, or published "
            "unless the parent chooses to share it. Family members take part only if they "
            "want to, and may stop at any time."
        ),
    }


async def _owned_project(project_id: str, user) -> dict:
    doc = await db.academy_projects.find_one({"id": project_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Project not found")
    if doc.get("parent_user_id") != user.id:
        raise HTTPException(403, "This project belongs to another account")
    return doc


def _portfolio_entry(p: dict) -> dict:
    """What a submitted project contributes to a portfolio page."""
    steps = p.get("steps") or []
    return {
        "id": p["id"],
        "title": p.get("title"),
        "kind": p.get("kind"),
        "kind_label": _project_out(p)["kind_label"],
        "summary": p.get("summary"),
        "course_slug": p.get("course_slug"),
        "submitted_at": p.get("submitted_at"),
        "steps": [{"title": s["title"], "artifact": s["artifact"]} for s in steps if s.get("done")],
        "notes": p.get("notes"),
    }
