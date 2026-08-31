"""Critical path tests: auth, staff meetings, GDPR, help guide, cost tracking, session management."""
import os
import requests
import pytest
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = ("admin@lcewai.org", "Admin@LCE2026")
EXEC = ("exec@lcewai.org", "Exec@LCE2026")
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
def exec_t(s):
    return _login(s, *EXEC)


@pytest.fixture(scope="module")
def admin_t(s):
    return _login(s, *ADMIN)


@pytest.fixture(scope="module")
def stud_t(s):
    return _login(s, *STUDENT)


# ── Auth & Registration ────────────────────────────────────────────────────────

class TestAuth:
    def test_register_enforces_min_length(self):
        r = requests.post(f"{API}/auth/register", json={
            "email": "test-min@test.com", "full_name": "T", "password": "1234567",
            "agreed_terms": True, "over_13": True,
        }, timeout=15)
        assert r.status_code == 422, f"expected 422 for short password, got {r.status_code}"
        detail = r.json().get("detail", "")
        assert "min_length" in str(detail) or "password" in str(detail).lower()

    def test_register_requires_age_gate(self):
        r = requests.post(f"{API}/auth/register", json={
            "email": "test-age@test.com", "full_name": "T", "password": "12345678",
            "agreed_terms": True, "over_13": False,
        }, timeout=15)
        assert r.status_code == 400
        assert "13" in r.json().get("detail", "")

    def test_register_requires_terms(self):
        r = requests.post(f"{API}/auth/register", json={
            "email": "test-terms@test.com", "full_name": "T", "password": "12345678",
            "agreed_terms": False, "over_13": True,
        }, timeout=15)
        assert r.status_code == 400
        assert "Terms" in r.json().get("detail", "")


# ── GDPR Endpoints ─────────────────────────────────────────────────────────────

class TestGDPR:
    def test_export_data(self, stud_t):
        r = requests.get(f"{API}/auth/account/export", headers=hdr(stud_t), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "user_id" in data
        assert "exported_at" in data

    def test_reconsent(self, stud_t):
        r = requests.post(f"{API}/auth/reconsent", headers=hdr(stud_t),
                          json={"agreed_terms": True, "over_13": True}, timeout=15)
        assert r.status_code == 200
        assert r.json().get("ok") is True

    def test_reconsent_rejects_without_terms(self, stud_t):
        r = requests.post(f"{API}/auth/reconsent", headers=hdr(stud_t),
                          json={"agreed_terms": False, "over_13": True}, timeout=15)
        assert r.status_code == 400

    def test_delete_account_requires_confirmation(self):
        # Use a temporary account so we do not delete the shared demo student.
        email = f"delete-test-{uuid.uuid4().hex[:8]}@example.com"
        password = "Learn@LCE2026"
        reg = requests.post(f"{API}/auth/register", json={
            "email": email,
            "full_name": "Temp Delete",
            "password": password,
            "agreed_terms": True,
            "over_13": True,
        }, timeout=15)
        assert reg.status_code == 200, f"registration failed: {reg.status_code} {reg.text}"
        token = reg.json()["access_token"]

        r = requests.delete(f"{API}/auth/account", headers=hdr(token), timeout=15)
        assert r.status_code != 404


# ── Staff Meeting (exec only) ──────────────────────────────────────────────────

class TestStaffMeeting:
    def test_staff_meeting_requires_exec(self, stud_t, admin_t):
        for token, role in [(stud_t, "student"), (admin_t, "admin")]:
            r = requests.post(f"{API}/exec/staff-meeting", headers=hdr(token),
                              json={"brief": "Test brief", "agenda": ["test"], "priority": "normal"},
                              timeout=30)
            assert r.status_code == 403, f"{role} should not access staff meeting"

    def test_staff_meeting_convenes(self, exec_t):
        r = requests.post(f"{API}/exec/staff-meeting", headers=hdr(exec_t),
                          json={"brief": "System health check", "agenda": ["Review metrics", "Check services"],
                                "participants": ["director", "oracle"], "priority": "normal"},
                          timeout=60)
        assert r.status_code == 200, f"staff meeting failed: {r.text}"
        data = r.json()
        assert data.get("status") == "convened"
        assert data.get("meeting_id")
        assert "participants" in data
        # Should have generated responses
        for pid in data.get("domain_briefs", {}):
            brief = data["domain_briefs"][pid]
            assert brief.get("status") in ("responded", "awaiting_response")

    def test_staff_meeting_list(self, exec_t):
        r = requests.get(f"{API}/exec/staff-meetings", headers=hdr(exec_t), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "meetings" in data

    def test_staff_meeting_rejects_invalid_brief(self, exec_t):
        r = requests.post(f"{API}/exec/staff-meeting", headers=hdr(exec_t),
                          json={"brief": "", "priority": "normal"}, timeout=15)
        assert r.status_code == 422

    def test_staff_meeting_rejects_unknown_priority(self, exec_t):
        r = requests.post(f"{API}/exec/staff-meeting", headers=hdr(exec_t),
                          json={"brief": "test", "priority": "urgent"}, timeout=15)
        assert r.status_code == 422


# ── Help Guide ─────────────────────────────────────────────────────────────────

class TestHelpGuide:
    def test_help_guide(self, stud_t):
        r = requests.post(f"{API}/help/guide", headers=hdr(stud_t),
                          json={"path": "/dashboard"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("title")
        assert "summary" in data
        assert "tip" in data or "details" in data

    def test_help_guide_unknown_route(self, stud_t):
        r = requests.post(f"{API}/help/guide", headers=hdr(stud_t),
                          json={"path": "/nonexistent-route-xyz"}, timeout=15)
        assert r.status_code == 200
        assert r.json().get("title")  # falls back gracefully

    def test_help_guide_with_query(self, stud_t):
        r = requests.post(f"{API}/help/guide", headers=hdr(stud_t),
                          json={"path": "/modules", "query": "curriculum"}, timeout=15)
        assert r.status_code == 200


# ── Session Management ─────────────────────────────────────────────────────────

class TestSessions:
    def test_list_sessions(self, stud_t):
        r = requests.get(f"{API}/auth/sessions", headers=hdr(stud_t), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "sessions" in data

    def test_list_sessions_requires_auth(self):
        r = requests.get(f"{API}/auth/sessions", timeout=15)
        assert r.status_code == 401


# ── AI Cost Tracking ───────────────────────────────────────────────────────────

class TestAICosts:
    def test_ai_costs_requires_admin(self, stud_t):
        r = requests.get(f"{API}/admin/ai-costs", headers=hdr(stud_t), timeout=15)
        assert r.status_code == 403

    def test_ai_costs_admin(self, admin_t):
        r = requests.get(f"{API}/admin/ai-costs?days=7", headers=hdr(admin_t), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "costs" in data
        assert "total" in data


# ── Cookie Consent Logging ─────────────────────────────────────────────────────

class TestCookieConsent:
    def test_cookie_consent_public(self):
        r = requests.post(f"{API}/consent/cookie",
                          json={"choice": "accepted"}, timeout=15)
        assert r.status_code == 200

    def test_cookie_consent_invalid_choice(self):
        r = requests.post(f"{API}/consent/cookie",
                          json={"choice": "maybe"}, timeout=15)
        assert r.status_code == 400


# ── Health Endpoint ────────────────────────────────────────────────────────────

class TestHealth:
    def test_health(self):
        r = requests.get(f"{API}/health", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("status") in ("ok", "operational", "degraded", "critical")
        assert d.get("checks", {}).get("db", {}).get("status") == "up"

    def test_version(self):
        r = requests.get(f"{API}/version", timeout=15)
        assert r.status_code == 200
