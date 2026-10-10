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
        "stats": {"lessons_passed": 8, "lessons_total": 10, "completed": False},
        "status": "in_progress",
    },
    {
        "course_slug": "reading-grade1",
        "course_title": "Reading Foundations — Grade 1",
        "subject": "reading",
        "subject_label": "Reading",
        "grade_label": "Grade 1",
        "passing_score": 80,
        "stats": {"lessons_passed": 12, "lessons_total": 12, "completed": True},
        "status": "completed",
    },
]
SUMMARY = {"courses_completed": 1, "courses_in_progress": 1, "lessons_passed": 20, "lessons_total": 22}


def test_notice_of_intent_cites_florida_statute():
    p = _compliance_payload("notice_of_intent", {}, ROWS, SUMMARY)
    assert "1002.41" in p["statute"]
    assert "Notice of Intent" in p["title"]


def test_annual_evaluation_includes_rows():
    p = _compliance_payload("annual_evaluation", {}, ROWS, SUMMARY)
    assert len(p["rows"]) == 2
    assert p["summary"]["lessons_passed"] == 20


def test_transcript_computes_progress_and_gpa():
    p = _compliance_payload("transcript", {}, ROWS, SUMMARY)
    graded = {g["course_title"]: g for g in p["graded_courses"]}
    assert graded["Reading Foundations — Grade 1"]["progress_pct"] == 100
    assert graded["Entrepreneurship Foundations"]["progress_pct"] == 80
    assert p["unweighted_gpa_completed_only"] == 4.0
    assert "signature_line" in p


def test_quarterly_report_and_ihip_shapes():
    q = _compliance_payload("quarterly_report", {}, ROWS, SUMMARY)
    assert q["rows"] == ROWS
    ih = _compliance_payload("ihip", {}, ROWS, SUMMARY)
    assert ih["rows"][0]["subject"] == "Entrepreneurship"


def test_all_kinds_have_titles():
    for kind in ("notice_of_intent", "quarterly_report", "annual_evaluation", "transcript", "ihip"):
        assert _compliance_payload(kind, {}, ROWS, SUMMARY)["title"]
