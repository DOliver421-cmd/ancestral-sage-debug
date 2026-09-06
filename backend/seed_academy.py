"""seed_academy — idempotent startup seeding for the Homeschool Academy.

Upserts academy content from backend/academy_content into db.academy_courses
(same pattern as seed_modules for the trade modules). Content is validated
before seeding so a malformed course fails loudly at seed time instead of
breaking a student's lesson later.

Run directly for a one-off check:  python -m seed_academy
"""
import asyncio
import logging
import uuid

import pymongo

from academy_content import ACADEMY_COURSES, PUBLISHED_COURSES

logger = logging.getLogger("lcewai")


class AcademyContentError(ValueError):
    """Raised when a course does not satisfy the content contract."""


def _flat_lessons(course):
    for unit in course.get("units", []):
        for lesson in unit.get("lessons", []):
            yield unit, lesson


def validate_course(course: dict) -> list:
    """Validate one course against the content contract.

    Returns a list of human-readable problems (empty = valid). Answers are
    stored as exact option strings; the grader resolves the index, so we
    verify every answer matches an option exactly.
    """
    problems = []
    if not course.get("slug") or not course.get("title"):
        problems.append("course missing slug/title")
    if course["status"] == "published":
        if not course.get("learning_objectives"):
            problems.append(f"{course['slug']}: published course needs learning_objectives")
        if not course.get("units"):
            problems.append(f"{course['slug']}: published course needs at least one unit")
    seen_orders = {}
    for unit in course.get("units", []):
        if not unit.get("slug") or not unit.get("title"):
            problems.append(f"{course['slug']}: unit missing slug/title")
        for lesson in unit.get("lessons", []):
            slug = lesson.get("slug")
            if not slug:
                problems.append(f"{course['slug']}/{unit['slug']}: lesson missing slug")
                continue
            order = lesson.get("order")
            if order in seen_orders:
                problems.append(f"{course['slug']}: duplicate lesson order {order} ({slug})")
            seen_orders[order] = slug
            if course["status"] == "published":
                if not lesson.get("learn"):
                    problems.append(f"{course['slug']}/{slug}: lesson has no learn content")
                if not lesson.get("check", {}).get("questions"):
                    problems.append(f"{course['slug']}/{slug}: lesson has no knowledge check")
                for qi, question in enumerate(lesson.get("check", {}).get("questions", [])):
                    options = question.get("options", [])
                    if len(options) < 2:
                        problems.append(f"{course['slug']}/{slug}: Q{qi + 1} needs ≥2 options")
                    if question.get("answer") not in options:
                        problems.append(
                            f"{course['slug']}/{slug}: Q{qi + 1} answer {question.get('answer')!r} "
                            f"not found in options {options!r}"
                        )
                    if not question.get("explain"):
                        problems.append(f"{course['slug']}/{slug}: Q{qi + 1} missing explanation")
    # Learning blocks must use known types and carry their text.
    known_kinds = {"p", "list", "example", "tip", "activity"}
    for _unit, lesson in _flat_lessons(course):
        for block in lesson.get("learn", []):
            if block.get("type") not in known_kinds:
                problems.append(
                    f"{course['slug']}/{lesson['slug']}: unknown learn block type {block.get('type')!r}"
                )
            if "text" not in block and "items" not in block:
                problems.append(f"{course['slug']}/{lesson['slug']}: learn block missing text/items")
    return problems


def validate_all() -> list:
    """Validate every course in the catalog. Returns all problems found."""
    problems = []
    slugs = []
    for course in ACADEMY_COURSES:
        problems += validate_course(course)
        if course["slug"] in slugs:
            problems.append(f"duplicate course slug {course['slug']}")
        slugs.append(course["slug"])
    return problems


def _lesson_answer_index(question: dict) -> int:
    return question["options"].index(question["answer"])


async def seed_academy(db) -> dict:
    """Idempotent upsert of academy courses into db.academy_courses.

    Returns {'seeded': n, 'updated': m, 'skipped': k}. Published courses are
    upserted by slug (content edits propagate on deploy, like seed_modules).
    Planned courses are also upserted so the catalog stays complete, but their
    units are forced empty and status forced to "planned" — a planned course
    can never accidentally ship with half-written content.
    """
    problems = validate_all()
    if problems:
        raise AcademyContentError("Academy content validation failed:\n- " + "\n- ".join(problems[:20]))

    seeded = updated = skipped = 0
    # Pull existing catalog in one query to minimize round-trips.
    existing_docs = await db.academy_courses.find({}, {"_id": 0}).to_list(500)
    existing_by_slug = {d["slug"]: d for d in existing_docs}

    bulk_ops = []
    for course in ACADEMY_COURSES:
        existing = existing_by_slug.get(course["slug"])
        if existing and existing.get("_source_version") == course.get("_source_version"):
            skipped += 1
            continue
        doc = {
            **course,
            "units": [] if course["status"] == "planned" else course["units"],
            "_source_version": f"v1-{course['slug']}",
            "_updated_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        }
        if existing:
            doc["id"] = existing.get("id") or str(uuid.uuid4())
            bulk_ops.append(
                pymongo.ReplaceOne({"slug": course["slug"]}, doc, upsert=True)
            )
            updated += 1
        else:
            doc["id"] = str(uuid.uuid4())
            bulk_ops.append(
                pymongo.InsertOne(doc)
            )
            seeded += 1
    if bulk_ops:
        await db.academy_courses.bulk_write(bulk_ops, ordered=False)
    logger.info("Academy seed done: %d inserted, %d updated, %d unchanged", seeded, updated, skipped)
    return {"seeded": seeded, "updated": updated, "skipped": skipped}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    problems = validate_all()
    if problems:
        print("CONTENT PROBLEMS:")
        for p in problems:
            print(" -", p)
        raise SystemExit(1)
    print(f"OK — {len(ACADEMY_COURSES)} courses valid "
          f"({len(PUBLISHED_COURSES)} published, {len(ACADEMY_COURSES) - len(PUBLISHED_COURSES)} planned)")
