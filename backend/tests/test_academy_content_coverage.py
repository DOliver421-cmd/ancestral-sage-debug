"""Regression tests for the culturally grounded curriculum (owner directive 2026-10-10).

The Academy is required to carry deep cultural grounding at every level rather
than generic K-12 titles at the ends of the range. These tests fail if a
culturally centered course is dropped, renamed out of the catalog, or loses
enough content to pass validation.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from academy_content import ACADEMY_COURSES  # noqa: E402
from routers.academy import GRADES, TRACK_KEYS, course_applies  # noqa: E402

REQUIRED_COURSES = {
    # ── Primary & elementary ──────────────────────────────────────────────
    "oral-histories-ancestral-foundations": ["K", "1", "2"],
    "storytelling-diaspora-k2": ["K", "1", "2"],
    "patterns-beadwork-african-math-k2": ["K", "1", "2"],
    "cradles-of-civilization": ["3"],
    "maroon-societies-alliances": ["4"],
    "atlantic-world-resistance-reconstruction": ["5"],
    # ── High school core ──────────────────────────────────────────────────
    "pan-african-diasporic-literature": ["10"],
    "tek-african-botanical-medicine": ["10"],
    "black-political-thought": ["11"],
    "data-analysis-algorithmic-bias": ["11"],
    "prose-of-liberation": ["12"],
    "african-indigenous-governance": ["12"],
    # ── Specialized tracks & adult ─────────────────────────────────────────
    "afrofuturism-sustainable-architecture": ["9", "10", "11", "12"],
    "indigenous-astronomy-maritime-navigation": ["9", "10", "11", "12"],
    "visual-arts-black-diaspora": ["9", "10", "11", "12"],
    "ethnomusicology-roots-black-music": ["9", "10", "11", "12"],
    "health-equity-environmental-justice": ["adult"],
}

BY_SLUG = {c["slug"]: c for c in ACADEMY_COURSES}


def test_all_required_cultural_courses_exist_and_are_published():
    missing = [s for s in REQUIRED_COURSES if s not in BY_SLUG]
    assert not missing, f"culturally centered courses missing from the catalog: {missing}"
    unready = [s for s in REQUIRED_COURSES if BY_SLUG[s]["status"] != "published"]
    assert not unready, f"present but not published: {unready}"


def test_each_course_covers_its_grades():
    for slug, expected in REQUIRED_COURSES.items():
        assert sorted(BY_SLUG[slug]["grades"]) == sorted(expected), (
            f"{slug} should serve {expected}, is {BY_SLUG[slug]['grades']}"
        )


def test_every_cultural_course_is_enrollable():
    """A course that no (grade, track) can match is a dead entry in the catalog."""
    for slug in REQUIRED_COURSES:
        course = BY_SLUG[slug]
        matches = [(g, t) for g in GRADES for t in TRACK_KEYS if course_applies(course, g, t)]
        assert matches, f"{slug} cannot be enrolled with any offered grade/track"


def test_cultural_grounding_covers_every_grade_band():
    """K-2 and 10-12 are no longer generic: each grade band has real content."""
    for grade in ["K", "1", "2", "10", "11", "12"]:
        courses = [BY_SLUG[s] for s in REQUIRED_COURSES if grade in BY_SLUG[s]["grades"]]
        assert courses, f"no culturally centered course for grade {grade}"
        subjects = {c["subject"] for c in courses}
        assert len(subjects) >= 2, f"grade {grade} covers only {subjects}"


def test_cultural_courses_have_real_content_not_placeholders():
    for slug in REQUIRED_COURSES:
        course = BY_SLUG[slug]
        lessons = [l for u in course["units"] for l in u["lessons"]]
        assert len(lessons) >= 4, f"{slug} has only {len(lessons)} lessons"
        assert len(course["units"]) >= 3, f"{slug} has only {len(course['units'])} units"
        for lesson in lessons:
            assert lesson.get("learn"), f"{slug}/{lesson['slug']} has no learn content"
            assert lesson["check"]["questions"], f"{slug}/{lesson['slug']} has no knowledge check"
            for q in lesson["check"]["questions"]:
                assert q["answer"] in q["options"], f"{slug}: answer not among options"
                assert q.get("explain"), f"{slug}: question lacks an explanation"


def test_trade_creative_and_adult_tracks_are_covered():
    by_track = {BY_SLUG[s]["track"] for s in ("afrofuturism-sustainable-architecture",
                                              "indigenous-astronomy-maritime-navigation")}
    assert "builder" in by_track, "trade track lost its culturally centered course"
    assert {"artist"} <= {BY_SLUG[s]["track"] for s in ("visual-arts-black-diaspora",
                                                        "ethnomusicology-roots-black-music")}
    assert BY_SLUG["health-equity-environmental-justice"]["grades"] == ["adult"]
    assert BY_SLUG["health-equity-environmental-justice"]["tracks"]
