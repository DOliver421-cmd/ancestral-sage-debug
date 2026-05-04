"""Backend tests for LCE-WAI training platform."""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://apprentice-academy.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

# Seeded credentials
ADMIN = ("admin@lcewai.org", "Admin@LCE2026")
INSTRUCTOR = ("instructor@lcewai.org", "Teach@LCE2026")
STUDENT = ("student@lcewai.org", "Learn@LCE2026")


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


def _login(s, email, pw):
    r = s.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=20)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token(s):
    return _login(s, *ADMIN)


@pytest.fixture(scope="session")
def instructor_token(s):
    return _login(s, *INSTRUCTOR)


@pytest.fixture(scope="session")
def student_token(s):
    return _login(s, *STUDENT)


def hdr(t):
    return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


# ---------- Auth ----------
class TestAuth:
    def test_login_admin(self, s):
        t = _login(s, *ADMIN)
        assert isinstance(t, str) and len(t) > 10

    def test_login_instructor(self, s):
        _login(s, *INSTRUCTOR)

    def test_login_student(self, s):
        _login(s, *STUDENT)

    def test_login_invalid(self, s):
        r = s.post(f"{API}/auth/login", json={"email": "no@x.com", "password": "x"})
        assert r.status_code in (400, 401)

    def test_register_new_student(self, s):
        email = f"TEST_{uuid.uuid4().hex[:8]}@example.com"
        r = s.post(f"{API}/auth/register", json={
            "email": email, "password": "TestPass123!", "full_name": "Test User",
            "role": "student", "associate": "Associate-Alpha"
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert "access_token" in data
        # me endpoint
        me = s.get(f"{API}/auth/me", headers=hdr(data["access_token"]))
        assert me.status_code == 200
        body = me.json()
        assert body["email"] == email
        assert "associate" in body
        assert "cohort" not in body, "Found legacy 'cohort' key in /auth/me"

    def test_me_associate_field(self, s, student_token):
        r = s.get(f"{API}/auth/me", headers=hdr(student_token))
        assert r.status_code == 200
        body = r.json()
        assert "associate" in body
        assert "cohort" not in body


# ---------- Modules ----------
class TestModules:
    def test_modules_list_12(self, s, student_token):
        r = s.get(f"{API}/modules", headers=hdr(student_token))
        assert r.status_code == 200
        mods = r.json()
        assert len(mods) == 12, f"expected 12 modules, got {len(mods)}"
        for m in mods:
            assert "quiz" in m and isinstance(m["quiz"], list) and len(m["quiz"]) > 0
            assert "scripture" in m or "scripture_tie_in" in m or any("scripture" in str(k).lower() for k in m.keys())

    def test_module_detail(self, s, student_token):
        r = s.get(f"{API}/modules", headers=hdr(student_token))
        slug = r.json()[0]["slug"]
        r2 = s.get(f"{API}/modules/{slug}", headers=hdr(student_token))
        assert r2.status_code == 200
        assert r2.json()["slug"] == slug


# ---------- Progress / Quiz / Certificates ----------
@pytest.fixture(scope="session")
def first_module(s, student_token):
    return s.get(f"{API}/modules", headers=hdr(student_token)).json()[0]


class TestProgressAndCerts:
    def test_complete_quiz(self, s, student_token, first_module):
        m = first_module
        # answers is List[int] of correct indices, ordered like quiz
        answers = [int(q["answer"]) for q in m["quiz"]]
        r = s.post(f"{API}/progress/quiz",
                   json={"module_slug": m["slug"], "answers": answers},
                   headers=hdr(student_token))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("status") == "completed", data
        assert data.get("score", 0) >= 70, data

        # progress reflects
        p = s.get(f"{API}/progress/me", headers=hdr(student_token))
        assert p.status_code == 200
        plist = p.json()
        slugs = [x.get("module_slug") for x in plist]
        assert m["slug"] in slugs

    def test_certs_me(self, s, student_token, first_module):
        r = s.get(f"{API}/certificates/me", headers=hdr(student_token))
        assert r.status_code == 200
        certs = r.json()
        assert any(c.get("module_slug") == first_module["slug"] or c.get("slug") == first_module["slug"] for c in certs), certs

    def test_cert_pdf_download(self, s, student_token, first_module):
        slug = first_module["slug"]
        r = s.get(f"{API}/certificates/{slug}.pdf", params={"token": student_token}, timeout=30)
        assert r.status_code == 200, r.text[:200]
        assert "application/pdf" in r.headers.get("content-type", "")
        assert r.content[:4] == b"%PDF"


# ---------- AI Tutor ----------
class TestAI:
    @pytest.mark.parametrize("mode", ["tutor", "scripture", "explain"])
    def test_ai_chat_modes(self, s, student_token, mode):
        sid = f"sess-{uuid.uuid4().hex[:8]}"
        payload = {"session_id": sid, "message": "Explain Ohm's law in one sentence.", "mode": mode}
        last_err = None
        for attempt in range(2):
            try:
                r = s.post(f"{API}/ai/chat", json=payload, headers=hdr(student_token), timeout=60)
                if r.status_code == 200:
                    body = r.json()
                    reply = body.get("reply") or body.get("message") or body.get("response") or ""
                    assert isinstance(reply, str) and len(reply.strip()) > 0, body
                    return
                last_err = f"{r.status_code} {r.text}"
            except Exception as e:
                last_err = str(e)
            time.sleep(2)
        pytest.fail(f"AI {mode} failed: {last_err}")


# ---------- Labs ----------
class TestLabs:
    def test_labs_total_21(self, s, student_token):
        r = s.get(f"{API}/labs", headers=hdr(student_token))
        assert r.status_code == 200
        labs = r.json()
        assert len(labs) == 21, f"expected 21 labs, got {len(labs)}"
        # my_submission field present
        assert all("my_submission" in l for l in labs)

    def test_labs_online_9(self, s, student_token):
        r = s.get(f"{API}/labs", params={"track": "online"}, headers=hdr(student_token))
        assert r.status_code == 200
        assert len(r.json()) == 9

    def test_labs_inperson_12(self, s, student_token):
        r = s.get(f"{API}/labs", params={"track": "inperson"}, headers=hdr(student_token))
        assert r.status_code == 200
        assert len(r.json()) == 12

    def test_lab_detail(self, s, student_token):
        r = s.get(f"{API}/labs/basic-circuit-sim", headers=hdr(student_token))
        assert r.status_code == 200, r.text
        assert r.json().get("slug") == "basic-circuit-sim"

    def test_basic_circuit_sim_pass(self, s, student_token):
        ans = {"voltage": 12, "r1": 10, "r2": 20, "r3": 30, "config": "series", "total_r": 60, "total_i": 0.2}
        r = s.post(f"{API}/labs/basic-circuit-sim/submit",
                   json={"lab_slug": "basic-circuit-sim", "answers": ans},
                   headers=hdr(student_token))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("score") == 100, data
        assert data.get("status") == "passed", data

    def test_voltage_drop_calc_grading(self, s, student_token):
        r = s.post(f"{API}/labs/voltage-drop-calc/submit",
                   json={"lab_slug": "voltage-drop-calc",
                         "answers": {"voltage_drop": 0, "percent_drop": 0, "acceptable": False}},
                   headers=hdr(student_token))
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body.get("score"), (int, float)), body

    def test_loto_scenario_pass(self, s, student_token):
        seq = ["notify", "shutdown", "lockout", "tagout", "verify_dead", "try_start"]
        r = s.post(f"{API}/labs/loto-scenario/submit",
                   json={"lab_slug": "loto-scenario", "answers": {"sequence": seq}},
                   headers=hdr(student_token))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("score") == 100, data

    def test_inperson_submission_pending(self, s, student_token):
        r = s.post(f"{API}/labs/emt-conduit-install/submit",
                   json={"lab_slug": "emt-conduit-install",
                         "photo_url": "https://example.com/photo.jpg", "notes": "Done"},
                   headers=hdr(student_token))
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "pending"


# ---------- Instructor flow ----------
class TestInstructor:
    def test_pending_submissions(self, s, instructor_token):
        r = s.get(f"{API}/instructor/submissions", headers=hdr(instructor_token))
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        # at least the one we just submitted; must contain user/lab info
        if items:
            it = items[0]
            assert "user" in it or "user_email" in it or "user_id" in it
            assert "lab" in it or "lab_slug" in it

    def test_review_submission(self, s, instructor_token, student_token):
        # ensure we have something to review: submit fresh in-person
        s.post(f"{API}/labs/electrical-safety-audit/submit",
               json={"lab_slug": "electrical-safety-audit",
                     "photo_url": "https://example.com/p.jpg", "notes": "audit"},
               headers=hdr(student_token))
        items = s.get(f"{API}/instructor/submissions", headers=hdr(instructor_token)).json()
        if not items:
            pytest.skip("no pending submissions")
        sid = items[0].get("id") or items[0].get("_id") or items[0].get("submission_id")
        r = s.post(f"{API}/instructor/submissions/{sid}/review",
                   json={"status": "approved", "feedback": "Good work"},
                   headers=hdr(instructor_token))
        assert r.status_code == 200, r.text

    def test_lab_report(self, s, instructor_token):
        r = s.get(f"{API}/instructor/lab-report", headers=hdr(instructor_token))
        assert r.status_code == 200
        roster = r.json()
        assert isinstance(roster, list)
        if roster:
            keys = roster[0].keys()
            assert any(k in keys for k in ["labs_passed", "skill_points", "lab_hours"])


# ---------- Competencies ----------
class TestCompetencies:
    def test_competencies_8(self, s, student_token):
        r = s.get(f"{API}/competencies", headers=hdr(student_token))
        assert r.status_code == 200
        body = r.json()
        comps = body if isinstance(body, list) else body.get("competencies", [])
        assert len(comps) == 8, f"expected 8 competencies, got {len(comps)}"


# ---------- Roster / Admin ----------
class TestRolesAndAdmin:
    def test_roster_student_forbidden(self, s, student_token):
        r = s.get(f"{API}/roster", headers=hdr(student_token))
        assert r.status_code == 403

    def test_roster_instructor_ok(self, s, instructor_token):
        r = s.get(f"{API}/roster", headers=hdr(instructor_token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_stats_forbidden_for_student(self, s, student_token):
        r = s.get(f"{API}/admin/stats", headers=hdr(student_token))
        assert r.status_code == 403

    def test_admin_stats_ok(self, s, admin_token):
        r = s.get(f"{API}/admin/stats", headers=hdr(admin_token))
        assert r.status_code == 200

    def test_admin_users_forbidden_for_student(self, s, student_token):
        r = s.get(f"{API}/admin/users", headers=hdr(student_token))
        assert r.status_code == 403

    def test_admin_users_ok(self, s, admin_token):
        r = s.get(f"{API}/admin/users", headers=hdr(admin_token))
        assert r.status_code == 200

    def test_admin_associate_endpoint(self, s, admin_token):
        # find a student
        users = s.get(f"{API}/admin/users", headers=hdr(admin_token)).json()
        target = next((u for u in users if u.get("role") == "student"), None)
        assert target, "no student found"
        uid = target.get("id") or target.get("_id")
        r = s.post(f"{API}/admin/associate",
                   json={"user_id": uid, "associate": "Associate-Alpha"},
                   headers=hdr(admin_token))
        assert r.status_code == 200, r.text

    def test_legacy_cohort_endpoint_removed(self, s, admin_token):
        r = s.post(f"{API}/admin/cohort",
                   json={"user_id": "x", "cohort": "y"},
                   headers=hdr(admin_token))
        assert r.status_code in (404, 405), f"legacy /admin/cohort should be gone, got {r.status_code}"



# ---------- Credentials (Phase C) ----------
class TestCredentials:
    def test_list_credentials_14(self, s, student_token):
        r = s.get(f"{API}/credentials", headers=hdr(student_token))
        assert r.status_code == 200, r.text
        creds = r.json()
        assert isinstance(creds, list)
        assert len(creds) == 14, f"expected 14 credentials, got {len(creds)}"
        for c in creds:
            assert "key" in c and "name" in c and "description" in c and "trigger" in c

    def test_credentials_me_split(self, s, student_token):
        r = s.get(f"{API}/credentials/me", headers=hdr(student_token))
        assert r.status_code == 200, r.text
        body = r.json()
        assert "earned" in body and "available" in body
        assert isinstance(body["earned"], list)
        assert isinstance(body["available"], list)
        # student already has prior labs passed → expect at least 1 earned
        earned_keys = {e["credential_key"] for e in body["earned"]}
        # confirm split is valid (no duplicates)
        avail_keys = {c["key"] for c in body["available"]}
        assert earned_keys.isdisjoint(avail_keys)

    def test_quiz_completion_awards_osha_10(self, s, student_token):
        # complete safety-loto quiz (module exists)
        mods = s.get(f"{API}/modules", headers=hdr(student_token)).json()
        m = next((x for x in mods if x["slug"] == "safety-loto"), None)
        assert m, "safety-loto module not found"
        answers = [int(q["answer"]) for q in m["quiz"]]
        rq = s.post(f"{API}/progress/quiz",
                    json={"module_slug": "safety-loto", "answers": answers},
                    headers=hdr(student_token))
        assert rq.status_code == 200, rq.text
        # now /credentials/me should award osha-10-awareness
        r = s.get(f"{API}/credentials/me", headers=hdr(student_token))
        assert r.status_code == 200
        body = r.json()
        earned_keys = {e["credential_key"] for e in body["earned"]}
        assert "osha-10-awareness" in earned_keys, f"earned: {earned_keys}"

    def test_credential_manifest_openbadges(self, s):
        # public, no auth needed
        r = requests.get(f"{API}/credentials/osha-10-awareness/manifest.json", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("@context") == "https://w3id.org/openbadges/v2"
        assert data.get("type") == "BadgeClass"
        assert "name" in data and data["name"]
        assert "description" in data
        assert "criteria" in data
        assert "issuer" in data
        assert "W.A.I." in data["issuer"]["name"] or "Workforce" in data["issuer"]["name"]

    def test_credential_manifest_404(self, s):
        r = requests.get(f"{API}/credentials/does-not-exist-xyz/manifest.json", timeout=15)
        assert r.status_code == 404

    def test_credential_assertion(self, s, student_token):
        body = s.get(f"{API}/credentials/me", headers=hdr(student_token)).json()
        if not body["earned"]:
            pytest.skip("no earned credential to assert")
        assertion_id = body["earned"][0]["id"]
        r = requests.get(f"{API}/credentials/assertion/{assertion_id}.json", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["@context"] == "https://w3id.org/openbadges/v2"
        assert data["type"] == "Assertion"
        assert "recipient" in data
        assert "issuedOn" in data
        assert "badge" in data


# ---------- Portfolio ----------
class TestPortfolio:
    def test_portfolio_me(self, s, student_token):
        r = s.get(f"{API}/portfolio/me", headers=hdr(student_token))
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ["user", "stats", "modules", "labs", "credentials", "competencies"]:
            assert k in data, f"missing key {k}"
        for k in ["hours", "skill_points", "credentials_earned", "modules_completed", "labs_passed"]:
            assert k in data["stats"]
            assert isinstance(data["stats"][k], int)
        assert data["user"]["email"]  # private view has email

    def test_portfolio_publish_creates_slug(self, s, student_token):
        r = s.post(f"{API}/portfolio/publish",
                   json={"bio": "Aspiring electrician.", "publish": True},
                   headers=hdr(student_token))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("published") is True
        assert isinstance(data.get("slug"), str) and len(data["slug"]) > 0

        # subsequent /portfolio/me returns share_slug
        me = s.get(f"{API}/portfolio/me", headers=hdr(student_token)).json()
        assert me.get("share_slug") == data["slug"]

    def test_portfolio_public_no_auth_no_email(self, s, student_token):
        # ensure published
        pub = s.post(f"{API}/portfolio/publish",
                     json={"bio": "Public bio.", "publish": True},
                     headers=hdr(student_token)).json()
        slug = pub["slug"]
        # Use a fresh session WITHOUT any auth headers
        clean = requests.Session()
        r = clean.get(f"{API}/portfolio/public/{slug}", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "user" in data
        assert "email" not in data["user"], f"public payload leaked email: {data['user']}"
        assert data["user"].get("full_name")
        assert "stats" in data and "credentials" in data

    def test_portfolio_unpublish_returns_404(self, s, student_token):
        pub = s.post(f"{API}/portfolio/publish",
                     json={"bio": "Public bio.", "publish": True},
                     headers=hdr(student_token)).json()
        slug = pub["slug"]
        # unpublish
        un = s.post(f"{API}/portfolio/publish",
                    json={"bio": "x", "publish": False},
                    headers=hdr(student_token))
        assert un.status_code == 200
        clean = requests.Session()
        r = clean.get(f"{API}/portfolio/public/{slug}", timeout=15)
        assert r.status_code == 404
        # republish for downstream tests
        s.post(f"{API}/portfolio/publish",
               json={"bio": "Aspiring electrician.", "publish": True},
               headers=hdr(student_token))

    def test_portfolio_export_pdf(self, s, student_token):
        r = requests.get(f"{API}/portfolio/export.pdf",
                         params={"token": student_token}, timeout=30)
        assert r.status_code == 200, r.text[:200]
        assert "application/pdf" in r.headers.get("content-type", "")
        assert r.content[:4] == b"%PDF"
        assert len(r.content) > 1000

    def test_portfolio_export_pdf_invalid_token(self, s):
        r = requests.get(f"{API}/portfolio/export.pdf",
                         params={"token": "not-a-jwt"}, timeout=15)
        assert r.status_code == 401


# ---------- Rebrand ----------
class TestRebrand:
    def test_no_cohort_in_modules(self, s, student_token):
        r = s.get(f"{API}/modules", headers=hdr(student_token))
        assert "cohort" not in r.text.lower(), "Found legacy 'cohort' string in /modules"

    def test_no_cohort_in_credentials(self, s, student_token):
        r = s.get(f"{API}/credentials", headers=hdr(student_token))
        assert "cohort" not in r.text.lower()

    def test_no_cohort_in_portfolio(self, s, student_token):
        r = s.get(f"{API}/portfolio/me", headers=hdr(student_token))
        assert "cohort" not in r.text.lower()
