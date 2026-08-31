"""Unit tests for creator course checkout gate ordering (2026-08-27 audit).

Reality being pinned:
1. A FREE course (price_cents == 0) enrolls directly — the PAYMENTS_ENABLED
   gate must NOT block free enrollment (it used to sit above the course lookup
   and 501 every free enroll while no provider was configured).
2. A PAID course still 501s when no payment provider is configured.
3. Course lookup errors keep their correct status codes regardless of the
   payments gate (404 unknown course, 400 unpublished, 400 own course).

Runs the endpoint coroutine directly with faked db/user (no server, no
MongoDB, no provider calls) — pytest-asyncio is not configured in this repo,
so asyncio.run() is used.
"""
import asyncio

import pytest
from fastapi import HTTPException

import routers.creator as creator


class FakeCollection:
    def __init__(self, doc=None):
        self.doc = doc
        self.updated = False

    async def find_one(self, *_a, **_k):
        return self.doc

    async def update_one(self, *_a, **_k):
        self.updated = True


class FakeDB:
    def __init__(self, course):
        self.creator_courses = FakeCollection(course)
        self.creator_enrollments = FakeCollection()


class FakeUser:
    id = "user-1"
    email = "student@example.com"


def _run(db, course_id="course-1"):
    return asyncio.run(creator.creator_course_checkout(course_id, FakeUser()))


def test_free_course_enrolls_without_payment_provider():
    db = FakeDB({"course_id": "course-1", "status": "published",
                 "creator_id": "creator-9", "price_cents": 0})
    creator.db = db
    creator.PAYMENTS_ENABLED = False  # no provider keys configured
    result = _run(db)
    assert result == {"enrolled": True, "free": True}
    assert db.creator_courses.updated and db.creator_enrollments.updated


def test_paid_course_still_gates_on_payments_enabled():
    db = FakeDB({"course_id": "course-1", "status": "published",
                 "creator_id": "creator-9", "price_cents": 2900})
    creator.db = db
    creator.PAYMENTS_ENABLED = False
    with pytest.raises(HTTPException) as err:
        _run(db)
    assert err.value.status_code == 501


def test_unknown_course_is_404_even_without_provider():
    db = FakeDB(None)
    creator.db = db
    creator.PAYMENTS_ENABLED = False
    with pytest.raises(HTTPException) as err:
        _run(db)
    assert err.value.status_code == 404


def test_unpublished_course_is_400_even_without_provider():
    db = FakeDB({"course_id": "course-1", "status": "draft",
                 "creator_id": "creator-9", "price_cents": 0})
    creator.db = db
    creator.PAYMENTS_ENABLED = False
    with pytest.raises(HTTPException) as err:
        _run(db)
    assert err.value.status_code == 400


def test_own_course_is_400_even_without_provider():
    db = FakeDB({"course_id": "course-1", "status": "published",
                 "creator_id": "user-1", "price_cents": 0})
    creator.db = db
    creator.PAYMENTS_ENABLED = False
    with pytest.raises(HTTPException) as err:
        _run(db)
    assert err.value.status_code == 400
