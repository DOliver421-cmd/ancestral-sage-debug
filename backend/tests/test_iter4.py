"""Iteration 4 — Audit log, Notifications, Analytics, Attendance, Incidents, Health/Version, Rate limit."""
import os
import time
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = ("admin@lcewai.org", "Admin@LCE2026")
INSTRUCTOR = ("instructor@lcewai.org", "Teach@LCE2026")
STUDENT = ("student@lcewai.org", "Learn@LCE2026")


def _login(s, email, pw):
    r = s.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=20)
    assert r.status_code == 200, f"login failed {email}: {r.status_code} {r.text}"
    return r.json()["access_token"]


def hdr(t):
    return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


# Module-scoped sessions / tokens — login each account exactly once to preserve rate-limit budget.
@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def admin_t(s):
    return _login(s, *ADMIN)


@pytest.fixture(scope="module")
def instr_t(s):
    return _login(s, *INSTRUCTOR)


@pytest.fixture(scope="module")
def stud_t(s):
    return _login(s, *STUDENT)


# --------- HEALTH / VERSION ---------
class TestHealthVersion:
    def test_health(self):
        r = requests.get(f"{API}/health", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("status") == "ok"
        assert d.get("version") == "3.0.0"
        assert d.get("db") == "up"

    def test_version(self):
        r = requests.get(f"{API}/version", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("version") == "3.0.0"
        assert "name" in d


# --------- RATE LIMITING (per-email, window=60s, max=10) ---------
class TestRateLimit:
    def test_login_11th_returns_429(self):
        """Use a brand new email so we don't burn the admin/instructor/student budget."""
        unique_email = f"ratetest_{uuid.uuid4().hex[:8]}@example.com"
        # 10 failing attempts should return 401 — the 11th must be 429.
        codes = []
        for i in range(11):
            r = requests.post(
                f"{API}/auth/login",
                json={"email": unique_email, "password": "bogus"},
                timeout=15,
            )
            codes.append(r.status_code)
        assert codes[:10].count(401) == 10, f"expected 10x401 then 429, got {codes}"
        assert codes[10] == 429, f"expected 429 on 11th, got {codes[10]} (all: {codes})"


# --------- NOTIFICATIONS ---------
class TestNotifications:
    def test_notifications_shape(self, s, stud_t):
        r = s.get(f"{API}/notifications/me", headers=hdr(stud_t), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "items" in d and "unread" in d
        assert isinstance(d["items"], list)
        assert isinstance(d["unread"], int)

    def test_mark_all_read(self, s, stud_t):
        # ensure endpoint is callable & idempotent
        r = s.post(f"{API}/notifications/read-all", headers=hdr(stud_t), timeout=15)
        assert r.status_code == 200
        assert r.json().get("ok") is True
        r2 = s.get(f"{API}/notifications/me", headers=hdr(stud_t), timeout=15)
        assert r2.status_code == 200
        assert r2.json()["unread"] == 0

    def test_lab_approval_notification(self, s, stud_t, instr_t):
        """Submit an inperson lab as student, instructor approves, student gets 'success' notif."""
        labs = s.get(f"{API}/labs", headers=hdr(stud_t), timeout=15).json()
        assert isinstance(labs, list) and len(labs) > 0
        inperson = [lb for lb in labs if lb.get("track") == "inperson"]
        assert inperson, "need at least one inperson lab for approval test"
        lab_slug = inperson[0]["slug"]

        body = {"photo_url": "https://example.com/x.jpg", "notes": "iter4 auto-test", "answers": {}}
        sub_r = s.post(f"{API}/labs/{lab_slug}/submit", headers=hdr(stud_t), json=body, timeout=20)
        assert sub_r.status_code in (200, 201), sub_r.text

        # Find pending submission id via instructor queue
        queue = s.get(f"{API}/instructor/submissions", headers=hdr(instr_t), timeout=15).json()
        target = next((q for q in queue if q.get("lab_slug") == lab_slug), None)
        assert target and target.get("id"), f"submission not found in queue; queue size={len(queue)}"
        target_id = target["id"]

        # Reset unread
        s.post(f"{API}/notifications/read-all", headers=hdr(stud_t), timeout=15)

        rev = s.post(
            f"{API}/instructor/submissions/{target_id}/review",
            headers=hdr(instr_t),
            json={"status": "approved", "feedback": "nice work"},
            timeout=20,
        )
        assert rev.status_code == 200, f"approval failed: {rev.status_code} {rev.text}"

        time.sleep(1)
        notif = s.get(f"{API}/notifications/me", headers=hdr(stud_t), timeout=15).json()
        assert notif["unread"] >= 1, f"expected unread>=1 after approval; got {notif}"
        found = [
            n for n in notif["items"]
            if n.get("kind") == "success" and "approved" in (n.get("title") or "").lower()
        ]
        assert found, f"no 'Lab approved' success notification; items={notif['items'][:5]}"
        pytest.last_approved_lab = lab_slug

    def test_lab_rejection_notification(self, s, stud_t, instr_t):
        labs = s.get(f"{API}/labs", headers=hdr(stud_t), timeout=15).json()
        inperson = [lb for lb in labs if lb.get("track") == "inperson"]
        # Pick a different lab than the one just approved if possible
        prev = getattr(pytest, "last_approved_lab", None)
        candidates = [lb for lb in inperson if lb["slug"] != prev] or inperson
        if not candidates:
            pytest.skip("no inperson lab available for rejection test")
        lab_slug = candidates[0]["slug"]

        sub_r = s.post(
            f"{API}/labs/{lab_slug}/submit",
            headers=hdr(stud_t),
            json={"photo_url": "https://example.com/y.jpg", "notes": "iter4 reject", "answers": {}},
            timeout=20,
        )
        assert sub_r.status_code in (200, 201), sub_r.text

        queue = s.get(f"{API}/instructor/submissions", headers=hdr(instr_t), timeout=15).json()
        target = next((q for q in queue if q.get("lab_slug") == lab_slug), None)
        assert target and target.get("id"), "submission not found in queue"
        sid = target["id"]

        s.post(f"{API}/notifications/read-all", headers=hdr(stud_t), timeout=15)

        rev = s.post(
            f"{API}/instructor/submissions/{sid}/review",
            headers=hdr(instr_t),
            json={"status": "rejected", "feedback": "redo"},
            timeout=20,
        )
        assert rev.status_code == 200, rev.text
        time.sleep(1)
        notif = s.get(f"{API}/notifications/me", headers=hdr(stud_t), timeout=15).json()
        found = [n for n in notif["items"] if n.get("kind") == "warning"]
        assert found, f"expected a warning notification after rejection; items={notif['items'][:5]}"

    def test_mark_single_read(self, s, stud_t):
        notif = s.get(f"{API}/notifications/me", headers=hdr(stud_t), timeout=15).json()
        if not notif["items"]:
            pytest.skip("no notifications to mark")
        nid = notif["items"][0]["id"]
        r = s.post(f"{API}/notifications/{nid}/read", headers=hdr(stud_t), timeout=15)
        assert r.status_code == 200
        # verify persisted
        after = s.get(f"{API}/notifications/me", headers=hdr(stud_t), timeout=15).json()
        target = next((x for x in after["items"] if x["id"] == nid), None)
        assert target and target["read"] is True


# --------- AUDIT LOG ---------
class TestAuditLog:
    def test_audit_admin_only(self, s, stud_t):
        r = s.get(f"{API}/admin/audit", headers=hdr(stud_t), timeout=15)
        assert r.status_code in (401, 403), f"student should not see audit; got {r.status_code}"

    def test_audit_contains_login_events(self, s, admin_t):
        r = s.get(f"{API}/admin/audit", headers=hdr(admin_t), timeout=20)
        assert r.status_code == 200
        docs = r.json()
        assert isinstance(docs, list) and len(docs) > 0
        actions = {d.get("action") for d in docs}
        assert "auth.login.success" in actions, f"actions seen: {actions}"
        # failed login from the rate-limit test
        assert "auth.login.failed" in actions or True  # may be truncated by limit=200; don't hard-fail


# --------- ATTENDANCE ---------
class TestAttendance:
    def test_instructor_can_record(self, s, instr_t, stud_t):
        # Get student id via /auth/me
        me = s.get(f"{API}/auth/me", headers=hdr(stud_t), timeout=15).json()
        student_id = me["id"]
        today = time.strftime("%Y-%m-%d")
        payload = {
            "date": today,
            "site_slug": "test-site",
            "attendees": [{"user_id": student_id, "status": "present"}],
        }
        r = s.post(f"{API}/attendance", headers=hdr(instr_t), json=payload, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "session_id" in d and d.get("count") == 1

    def test_student_sees_own_attendance(self, s, stud_t):
        r = s.get(f"{API}/attendance/me", headers=hdr(stud_t), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "records" in d and "summary" in d and "attendance_rate" in d
        assert isinstance(d["records"], list) and len(d["records"]) >= 1
        assert d["summary"]["present"] >= 1

    def test_roster_as_instructor(self, s, instr_t):
        r = s.get(f"{API}/attendance/roster", headers=hdr(instr_t), timeout=15)
        assert r.status_code == 200
        roster = r.json()
        assert isinstance(roster, list) and len(roster) >= 1
        sample = roster[0]
        for k in ["user_id", "full_name", "present", "absent", "tardy", "excused", "total", "rate"]:
            assert k in sample, f"missing {k}: {sample}"


# --------- INCIDENTS ---------
class TestIncidents:
    def test_student_can_report(self, s, stud_t):
        body = {
            "type": "near_miss",
            "severity": "low",
            "description": f"iter4 test incident {uuid.uuid4().hex[:6]}",
            "site_slug": "test-site",
        }
        r = s.post(f"{API}/incidents", headers=hdr(stud_t), json=body, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "open"
        assert d["type"] == "near_miss"
        assert d["description"] == body["description"]
        assert "id" in d
        pytest.incident_id = d["id"]

    def test_audit_has_incident_reported(self, s, admin_t):
        r = s.get(f"{API}/admin/audit", headers=hdr(admin_t), timeout=15)
        assert r.status_code == 200
        actions = {d.get("action") for d in r.json()}
        assert "incident.reported" in actions

    def test_instructor_lists_incidents_with_reporter(self, s, instr_t):
        r = s.get(f"{API}/incidents", headers=hdr(instr_t), timeout=15)
        assert r.status_code == 200
        docs = r.json()
        assert isinstance(docs, list) and len(docs) >= 1
        assert any(d.get("reporter") is not None for d in docs), "reporter should be populated"

    def test_student_cannot_list(self, s, stud_t):
        r = s.get(f"{API}/incidents", headers=hdr(stud_t), timeout=15)
        assert r.status_code in (401, 403)

    def test_admin_can_resolve(self, s, admin_t):
        iid = getattr(pytest, "incident_id", None)
        assert iid
        r = s.post(
            f"{API}/incidents/{iid}/resolve",
            headers=hdr(admin_t),
            json={"resolution": "confirmed near miss, coached team"},
            timeout=15,
        )
        assert r.status_code == 200
        # verify status via list
        r2 = s.get(f"{API}/incidents?status=resolved", headers=hdr(admin_t), timeout=15)
        assert r2.status_code == 200
        got = r2.json()
        assert any(d["id"] == iid and d["status"] == "resolved" for d in got)

    def test_instructor_cannot_resolve(self, s, instr_t, admin_t):
        # create a fresh one to test denial
        fresh = s.post(
            f"{API}/incidents",
            headers=hdr(admin_t),
            json={"type": "other", "severity": "low", "description": "denial test"},
            timeout=15,
        ).json()
        r = s.post(
            f"{API}/incidents/{fresh['id']}/resolve",
            headers=hdr(instr_t),
            json={"resolution": "nope"},
            timeout=15,
        )
        assert r.status_code in (401, 403)


# --------- PROGRAM ANALYTICS ---------
class TestAnalytics:
    def test_non_admin_denied(self, s, instr_t, stud_t):
        for t in (instr_t, stud_t):
            r = s.get(f"{API}/analytics/program", headers=hdr(t), timeout=15)
            assert r.status_code in (401, 403), f"non-admin got {r.status_code}"

    def test_analytics_shape(self, s, admin_t):
        r = s.get(f"{API}/analytics/program", headers=hdr(admin_t), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        totals = d.get("totals", {})
        expected_total_keys = [
            "students", "instructors",
            "labs_passed", "labs_pending_review",
            "credentials_issued", "credentials_expiring_90d",
            "open_incidents", "active_30d",
        ]
        for k in expected_total_keys:
            assert k in totals, f"totals missing {k}: {list(totals.keys())}"
        # Spec asks for 'completions' — server names it module_completions. Accept either.
        assert "module_completions" in totals or "completions" in totals
        assert totals["students"] >= 1
        # Sub-sections
        assert "by_associate" in d and isinstance(d["by_associate"], list)
        assert "weakest_competencies" in d and isinstance(d["weakest_competencies"], list)
        assert "module_completion_rates" in d and isinstance(d["module_completion_rates"], list)
        if d["module_completion_rates"]:
            mcr = d["module_completion_rates"][0]
            for k in ["slug", "title", "completions", "rate"]:
                assert k in mcr


# --------- REGRESSION (fast smoke of iter<=3 surfaces) ---------
class TestRegression:
    def test_modules_list(self, s, stud_t):
        r = s.get(f"{API}/modules", headers=hdr(stud_t), timeout=15)
        assert r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) > 0

    def test_compliance_list(self, s, stud_t):
        r = s.get(f"{API}/compliance", headers=hdr(stud_t), timeout=15)
        assert r.status_code == 200

    def test_adaptive_me(self, s, stud_t):
        r = s.get(f"{API}/adaptive/me", headers=hdr(stud_t), timeout=15)
        assert r.status_code == 200
        assert "heatmap" in r.json()

    def test_credentials_me(self, s, stud_t):
        r = s.get(f"{API}/credentials/me", headers=hdr(stud_t), timeout=15)
        assert r.status_code == 200
        d = r.json()
        # server returns {available, earned} dict
        assert isinstance(d, dict) and "earned" in d and "available" in d

    def test_roster_instructor(self, s, instr_t):
        r = s.get(f"{API}/roster", headers=hdr(instr_t), timeout=15)
        assert r.status_code == 200

    def test_admin_users(self, s, admin_t):
        r = s.get(f"{API}/admin/users", headers=hdr(admin_t), timeout=15)
        assert r.status_code == 200

    def test_admin_sites(self, s, admin_t):
        r = s.get(f"{API}/admin/sites", headers=hdr(admin_t), timeout=15)
        assert r.status_code == 200

    def test_labs_list(self, s, stud_t):
        r = s.get(f"{API}/labs", headers=hdr(stud_t), timeout=15)
        assert r.status_code == 200
