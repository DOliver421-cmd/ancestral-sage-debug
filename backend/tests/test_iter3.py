"""Iteration 3 — PWA, Compliance, Adaptive, Admin Tools, AI new modes."""
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


# ---------- PWA ----------
class TestPWA:
    def test_manifest(self):
        r = requests.get(f"{BASE_URL}/manifest.json", timeout=15)
        assert r.status_code == 200, r.text[:200]
        d = r.json()
        for k in ["name", "short_name", "icons", "theme_color", "display"]:
            assert k in d, f"manifest missing {k}"
        assert d["display"] == "standalone"
        assert isinstance(d["icons"], list) and len(d["icons"]) > 0

    def test_sw_js(self):
        r = requests.get(f"{BASE_URL}/sw.js", timeout=15)
        assert r.status_code == 200, r.text[:200]
        body = r.text
        assert "serviceWorker" in body or "self.addEventListener" in body or "caches" in body

    def test_index_html_pwa_tags(self):
        r = requests.get(f"{BASE_URL}/", timeout=15)
        assert r.status_code == 200
        html = r.text
        assert 'rel="manifest"' in html or "rel='manifest'" in html
        assert "#0B203F" in html
        assert "apple-touch-icon" in html
        assert "viewport-fit=cover" in html


# ---------- Compliance ----------
class TestCompliance:
    def test_list_4_modules(self, s, stud_t):
        r = s.get(f"{API}/compliance", headers=hdr(stud_t))
        assert r.status_code == 200, r.text
        mods = r.json()
        assert isinstance(mods, list)
        slugs = {m.get("slug") for m in mods}
        for need in ["osha-10-electrical", "nfpa-70e-awareness", "ppe-fitting", "loto-certification"]:
            assert need in slugs, f"missing {need}: got {slugs}"
        for m in mods:
            assert "quiz" in m and isinstance(m["quiz"], list) and len(m["quiz"]) > 0

    def test_loto_detail_with_my_progress(self, s, stud_t):
        r = s.get(f"{API}/compliance/loto-certification", headers=hdr(stud_t))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("slug") == "loto-certification"
        assert "my_progress" in d

    def test_loto_quiz_completes_with_6mo_expiry(self, s, stud_t):
        det = s.get(f"{API}/compliance/loto-certification", headers=hdr(stud_t)).json()
        answers = [int(q["answer"]) for q in det["quiz"]]
        r = s.post(f"{API}/compliance/loto-certification/quiz",
                   json={"answers": answers}, headers=hdr(stud_t))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("status") == "completed", d
        assert d.get("pass_pct") == 80, d
        assert d.get("expires_at"), d

    def test_osha_quiz_completes_36mo_and_awards(self, s, stud_t):
        det = s.get(f"{API}/compliance/osha-10-electrical", headers=hdr(stud_t)).json()
        answers = [int(q["answer"]) for q in det["quiz"]]
        r = s.post(f"{API}/compliance/osha-10-electrical/quiz",
                   json={"answers": answers}, headers=hdr(stud_t))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("status") == "completed", d
        assert d.get("pass_pct") == 70, d
        assert d.get("expires_at"), d

        # Auto-award
        creds = s.get(f"{API}/credentials/me", headers=hdr(stud_t)).json()
        earned = {e["credential_key"] for e in creds.get("earned", [])}
        assert "osha-10-awareness" in earned, f"earned={earned}"


# ---------- Adaptive ----------
class TestAdaptive:
    def test_adaptive_me(self, s, stud_t):
        r = s.get(f"{API}/adaptive/me", headers=hdr(stud_t))
        assert r.status_code == 200, r.text
        d = r.json()
        assert "heatmap" in d
        hm = d["heatmap"]
        # 8 competencies — accept dict-of-comp or list-of-cells
        if isinstance(hm, dict):
            # could be wrapper {cells: [...]} or comp_key -> obj map
            if "cells" in hm or "competencies" in hm:
                cells = hm.get("cells") or hm.get("competencies") or []
            else:
                cells = list(hm.values())
        else:
            cells = hm
        assert len(cells) == 8, f"expected 8 heatmap cells, got {len(cells)}: {hm}"
        for c in cells:
            assert c.get("level") in ("hot", "warm", "cold"), c
        assert "weak_areas" in d
        assert isinstance(d["weak_areas"], list)
        assert "recommendations" in d and isinstance(d["recommendations"], list)
        assert "ai_topic" in d
        assert "locked_labs" in d


# ---------- Admin Tools (Sites / Inventory / Checkout) ----------
class TestAdminTools:
    def test_sites_list_admin(self, s, admin_t):
        r = s.get(f"{API}/admin/sites", headers=hdr(admin_t))
        assert r.status_code == 200, r.text
        sites = r.json()
        assert isinstance(sites, list) and len(sites) >= 3, f"got {len(sites)} sites"

    def test_sites_list_student_forbidden(self, s, stud_t):
        r = s.get(f"{API}/admin/sites", headers=hdr(stud_t))
        assert r.status_code == 403

    def test_create_site_admin(self, s, admin_t):
        slug = f"test-site-{uuid.uuid4().hex[:6]}"
        r = s.post(f"{API}/admin/sites",
                   json={"slug": slug, "name": f"TEST Site {slug}"},
                   headers=hdr(admin_t))
        assert r.status_code in (200, 201), r.text

    def test_create_site_student_forbidden(self, s, stud_t):
        r = s.post(f"{API}/admin/sites",
                   json={"slug": "x", "name": "x"}, headers=hdr(stud_t))
        assert r.status_code == 403

    def test_inventory_list_15(self, s, admin_t):
        r = s.get(f"{API}/admin/inventory", headers=hdr(admin_t))
        assert r.status_code == 200, r.text
        items = r.json()
        assert isinstance(items, list)
        assert len(items) >= 15, f"expected >=15 items got {len(items)}"

    def test_inventory_filter_by_site(self, s, admin_t):
        r = s.get(f"{API}/admin/inventory", params={"site_slug": "main-campus"},
                  headers=hdr(admin_t))
        assert r.status_code == 200, r.text
        items = r.json()
        assert isinstance(items, list)
        for it in items:
            sslug = it.get("site_slug") or it.get("site")
            assert sslug == "main-campus" or sslug is None or it.get("site_slug") == "main-campus"

    def test_checkout_flow(self, s, admin_t, instr_t, stud_t):
        # Find inventory item with quantity available
        items = s.get(f"{API}/admin/inventory", headers=hdr(admin_t)).json()
        candidate = next((i for i in items if (i.get("quantity_available") or 0) >= 1), None)
        assert candidate, "no inventory item with availability"
        sku = candidate.get("sku")
        before_qty = candidate["quantity_available"]

        # find a student id
        users = s.get(f"{API}/admin/users", headers=hdr(admin_t)).json()
        stud_user = next((u for u in users if u.get("role") == "student"), None)
        assert stud_user
        student_id = stud_user.get("id") or stud_user.get("_id")

        # checkout as instructor
        r = s.post(f"{API}/admin/checkout",
                   json={"sku": sku, "user_id": student_id, "quantity": 1},
                   headers=hdr(instr_t))
        assert r.status_code in (200, 201), r.text
        co = r.json()
        co_id = co.get("id") or co.get("_id") or co.get("checkout_id")
        assert co_id, co

        # quantity decreased
        items2 = s.get(f"{API}/admin/inventory", headers=hdr(admin_t)).json()
        upd = next((i for i in items2 if i.get("sku") == sku), None)
        assert upd, "item missing after checkout"
        assert upd["quantity_available"] == before_qty - 1, (before_qty, upd["quantity_available"])

        # list shows populated user/item
        listing = s.get(f"{API}/admin/checkouts", headers=hdr(admin_t))
        assert listing.status_code == 200, listing.text
        rows = listing.json()
        assert isinstance(rows, list) and len(rows) > 0
        first = rows[0]
        assert "user" in first or "user_email" in first or "user_id" in first
        assert "item" in first or "sku" in first

        # return
        ret = s.post(f"{API}/admin/checkout/{co_id}/return",
                     json={}, headers=hdr(instr_t))
        assert ret.status_code in (200, 204), ret.text

        # quantity restored
        items3 = s.get(f"{API}/admin/inventory", headers=hdr(admin_t)).json()
        upd2 = next((i for i in items3 if i.get("sku") == sku), None)
        assert upd2["quantity_available"] == before_qty, (before_qty, upd2["quantity_available"])


# ---------- AI new modes ----------
class TestAINewModes:
    @pytest.mark.parametrize("mode", ["nec_lookup", "blueprint"])
    def test_ai_modes(self, s, stud_t, mode):
        sid = f"sess-{uuid.uuid4().hex[:8]}"
        msg = "What does NEC 210.8 require?" if mode == "nec_lookup" else \
              "Read this blueprint: panel A, 200A main, 30 circuits."
        last = None
        for _ in range(2):
            try:
                r = s.post(f"{API}/ai/chat",
                           json={"session_id": sid, "message": msg, "mode": mode},
                           headers=hdr(stud_t), timeout=90)
                if r.status_code == 200:
                    body = r.json()
                    reply = body.get("reply") or body.get("message") or body.get("response") or ""
                    assert isinstance(reply, str) and len(reply.strip()) > 0, body
                    return
                last = f"{r.status_code} {r.text[:200]}"
            except Exception as e:
                last = str(e)
            time.sleep(2)
        pytest.fail(f"AI {mode} failed: {last}")


# ---------- Regression: previously-passing ----------
class TestRegression:
    def test_modules_still_12(self, s, stud_t):
        r = s.get(f"{API}/modules", headers=hdr(stud_t))
        assert r.status_code == 200
        assert len(r.json()) == 12

    def test_labs_still_21(self, s, stud_t):
        r = s.get(f"{API}/labs", headers=hdr(stud_t))
        assert r.status_code == 200
        assert len(r.json()) == 21

    def test_credentials_list(self, s, stud_t):
        r = s.get(f"{API}/credentials", headers=hdr(stud_t))
        assert r.status_code == 200
        assert isinstance(r.json(), list) and len(r.json()) >= 14

    def test_portfolio_me(self, s, stud_t):
        r = s.get(f"{API}/portfolio/me", headers=hdr(stud_t))
        assert r.status_code == 200

    def test_instructor_submissions(self, s, instr_t):
        r = s.get(f"{API}/instructor/submissions", headers=hdr(instr_t))
        assert r.status_code == 200
