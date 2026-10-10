"""Tests for the Florida homeschool compliance document generator (routers/academy.py)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers.academy import _compliance_payload  # noqa: E402


ROWS = [
    {
        "course_slug": "entrepreneurship-foundations",
        "course_title": "Entrepreneurship Foundations",
        "subject": "entrepreneurship",
        "subject_label": "Entrepreneurship",
        "grade_label": "Adult",
        "passing_score": 80,
        "stats": {"lessons_passed": 8, "lessons_total": 10, "completed": False, "avg_score": 82},
        "status": "in_progress",
    },
    {
        "course_slug": "reading-grade1",
        "course_title": "Reading Foundations — Grade 1",
        "subject": "reading",
        "subject_label": "Reading",
        "grade_label": "Grade 1",
        "passing_score": 80,
        "stats": {"lessons_passed": 12, "lessons_total": 12, "completed": True, "avg_score": 95},
        "status": "completed",
    },
]
SUMMARY = {"courses_completed": 1, "courses_in_progress": 1, "lessons_passed": 20, "lessons_total": 22}


def test_notice_of_intent_cites_florida_statute():
    p = _compliance_payload("notice_of_intent", {}, ROWS, SUMMARY)
    assert "1002.41" in p["statute"]
    assert "Notice of Intent" in p["title"]


def test_notice_of_intent_carries_the_filing_fields():
    """Regression: the generated letter used to declare DOB / address fields
    and then never emit them, so a parent could not file it with a county.
    Everything the parent enters must appear in the document, and it must
    always carry a signature line."""
    p = _compliance_payload(
        "notice_of_intent",
        {"name": "Jordan Ellis"},
        ROWS,
        SUMMARY,
        {
            "district": "Miami-Dade",
            "child_dob": "2016-04-02",
            "address_line": "1200 NW 1st Ave, Miami, FL 33127",
            "parent_signature": "Alexis Ellis",
        },
    )
    assert p["student_name"] == "Jordan Ellis"
    assert p["child_dob"] == "2016-04-02"
    assert p["address_line"] == "1200 NW 1st Ave, Miami, FL 33127"
    assert p["district"] == "Miami-Dade"
    assert "Alexis Ellis" in p["signature_line"]
    assert "Date:" in p["signature_line"]
    # The field list must describe what is actually rendered.
    assert set(p["fields"]) == {"student_name", "child_dob", "address_line", "district"}


def test_notice_of_intent_signature_line_present_without_signature():
    p = _compliance_payload("notice_of_intent", {"name": "Jordan"}, ROWS, SUMMARY, {})
    assert "signature_line" in p
    assert "____________" in p["signature_line"]


def test_quarterly_report_includes_the_period_the_parent_entered():
    """Regression: period_start/period_end were collected, persisted, and then
    dropped from the document — the printed report had no reporting period."""
    q = _compliance_payload(
        "quarterly_report", {}, ROWS, SUMMARY,
        {"period_start": "2026-08-01", "period_end": "2026-10-01"},
    )
    assert q["period"] == {"start": "2026-08-01", "end": "2026-10-01"}


def test_annual_evaluation_includes_rows():
    p = _compliance_payload("annual_evaluation", {}, ROWS, SUMMARY)
    assert len(p["rows"]) == 2
    assert p["summary"]["lessons_passed"] == 20


def test_transcript_computes_progress_and_gpa():
    p = _compliance_payload("transcript", {}, ROWS, SUMMARY)
    graded = {g["course_title"]: g for g in p["graded_courses"]}
    assert graded["Reading Foundations — Grade 1"]["progress_pct"] == 100
    assert graded["Entrepreneurship Foundations"]["progress_pct"] == 80
    # GPA is computed from real mastery scores on a stated scale, not a flat
    # 4.0 for anything marked complete.
    reading = graded["Reading Foundations — Grade 1"]      # completed, avg 95 -> A
    entre = graded["Entrepreneurship Foundations"]          # in progress, avg 82 -> B
    assert reading["grade_letter"] == "A" and reading["grade_points"] == 4.0
    assert entre["grade_letter"] == "B" and entre["grade_points"] == 3.0
    # Only completed courses count toward the GPA: (4.0) / 1 = 4.0.
    assert p["unweighted_gpa_completed_only"] == 4.0
    # The scale travels with the document so a reader can check the arithmetic.
    assert "A 90-100 = 4.0" in p["gpa_scale"]
    assert p["how_gpa_is_computed"]


def test_quarterly_report_and_ihip_shapes():
    q = _compliance_payload("quarterly_report", {}, ROWS, SUMMARY)
    assert q["rows"] == ROWS
    ih = _compliance_payload("ihip", {}, ROWS, SUMMARY)
    assert ih["rows"][0]["subject"] == "Entrepreneurship"


def test_all_kinds_have_titles():
    for kind in ("notice_of_intent", "quarterly_report", "annual_evaluation", "transcript", "ihip"):
        assert _compliance_payload(kind, {}, ROWS, SUMMARY)["title"]
