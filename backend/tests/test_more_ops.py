"""M.O.R.E. Ops and moderation admin critical paths."""
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api"
DB_NAME = os.environ.get("DB_NAME", "ancestral_sage")

ADMIN = ("admin@lcewai.org", "Admin@LCE2026")
STUDENT = ("student@lcewai.org", "Learn@LCE2026")


def _login(s, email, pw):
    r = s.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=20)
    assert r.status_code == 200, f"login failed {email}: {r.status_code} {r.text}"
    return r.json()["access_token"]


def hdr(t):
    return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def admin_t(s):
    return _login(s, *ADMIN)


@pytest.fixture(scope="module")
def stud_t(s):
    return _login(s, *STUDENT)


@pytest.fixture()
def mongo_db():
    url = os.environ.get("MONGO_URL")
    if not url:
        pytest.skip("MONGO_URL required for queue fixture setup")
    client = MongoClient(url)
    try:
        yield client[DB_NAME]
    finally:
        client.close()


class TestMorePublicFeeds:
    def test_public_posts_and_needs_load(self, s):
        posts = s.get(f"{API}/more/posts", params={"limit": 1}, timeout=15)
        needs = s.get(f"{API}/more/needs", params={"limit": 1}, timeout=15)
        assert posts.status_code == 200, posts.text
        assert needs.status_code == 200, needs.text
        assert "posts" in posts.json() and "total" in posts.json()
        assert "needs" in needs.json() and "total" in needs.json()


class TestMoreAdminQueue:
    def test_admin_queue_approve_and_reject(self, s, admin_t, stud_t, mongo_db):
        expires_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        created_at = datetime.now(timezone.utc).isoformat()
        post_id = f"test-post-{uuid.uuid4().hex[:8]}"
        need_id = f"test-need-{uuid.uuid4().hex[:8]}"
        mongo_db.more_posts.insert_one({
            "id": post_id,
            "content": "Temporary test post waiting for review",
            "category": "community",
            "author_id": "pytest",
            "author_name": "Pytest",
            "status": "pending_review",
            "moderation_note": "test",
            "created_at": created_at,
            "expires_at": expires_at,
        })
        mongo_db.more_needs.insert_one({
            "id": need_id,
            "title": "Temporary test need",
            "description": "Needs moderation review",
            "category": "general",
            "author_id": "pytest",
            "author_name": "Pytest",
            "status": "pending_review",
            "moderation_note": "test",
            "created_at": created_at,
            "expires_at": expires_at,
        })
        try:
            forbidden = s.get(f"{API}/more/admin/queue", headers=hdr(stud_t), timeout=15)
            assert forbidden.status_code == 403

            queue = s.get(f"{API}/more/admin/queue", headers=hdr(admin_t), timeout=15)
            assert queue.status_code == 200, queue.text
            data = queue.json()
            queued_post = next((p for p in data["posts"] if p["id"] == post_id), None)
            queued_need = next((n for n in data["needs"] if n["id"] == need_id), None)
            assert queued_post and queued_post["content_type"] == "post" and queued_post["preview"]
            assert queued_need and queued_need["content_type"] == "need" and queued_need["preview"]

            approved = s.post(f"{API}/more/admin/queue/post/{post_id}/approve", headers=hdr(admin_t), timeout=15)
            assert approved.status_code == 200, approved.text
            assert mongo_db.more_posts.find_one({"id": post_id})["status"] == "active"

            rejected = s.post(f"{API}/more/admin/queue/need/{need_id}/reject", headers=hdr(admin_t), timeout=15)
            assert rejected.status_code == 200, rejected.text
            assert mongo_db.more_needs.find_one({"id": need_id}) is None
        finally:
            mongo_db.more_posts.delete_one({"id": post_id})
            mongo_db.more_needs.delete_one({"id": need_id})


class TestMoreDepartmentAI:
    def test_department_chat_student_forbidden(self, s, stud_t):
        r = s.post(
            f"{API}/more/department/chat",
            json={"session_id": str(uuid.uuid4()), "message": "Status?", "history": []},
            headers=hdr(stud_t),
            timeout=20,
        )
        assert r.status_code == 403

    def test_department_chat_admin_returns_200_or_502(self, s, admin_t):
        r = s.post(
            f"{API}/more/department/chat",
            json={"session_id": str(uuid.uuid4()), "message": "Give me one sentence.", "history": []},
            headers=hdr(admin_t),
            timeout=60,
        )
        assert r.status_code in (200, 502), r.text
        if r.status_code == 200:
            data = r.json()
            assert data.get("reply")
            assert data.get("persona")
        else:
            assert "AI" in r.json().get("detail", "")
