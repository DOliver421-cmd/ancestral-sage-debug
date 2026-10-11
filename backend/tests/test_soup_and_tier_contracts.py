"""tests/test_soup_and_tier_contracts.py — the access policy, pinned end to end.

Owner requirement (2026-10-11): if a feature/tier/role rule cannot be clearly
defined, the AI has no policy to enforce. These tests are that definition in
executable form:

  1. POLICY COMPLETENESS — every enforced gate is defined in exactly one place
     per surface, and every gate is editable from the exec console's
     authorization matrix (a gate the console cannot edit is a lock nobody
     holds the key to).
  2. AI CHAT — member+ or active BYOK; the keyword-KB helper stays free.
  3. PUZZLES / SOVEREIGN — the daily puzzle is free (it lives on the free
     student dashboard); the Sovereign chat stays executive.
  4. THE SOUP — the bytes are gated server-side per file, anonymous is 401,
     a signed-in account gets `soup`, member gets `soup_manual`, plus gets
     `soup_full`, owner/executive_admin bypass everything, and an exec edit to
     db.authz_matrix changes what the gate enforces.
  5. THE PARTNER API — the five routes the partner page has always called now
     exist, authenticate (Bearer or the scoped cookie), enforce the member AI
     contract, and never store a raw provider key.

Run: cd backend && python -m pytest tests/test_soup_and_tier_contracts.py -v
"""

import asyncio
import base64
import os
import sys
import types

import jwt as pyjwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security import feature_control as fc  # noqa: E402
from security.soup_gate import soup_gate_verdict  # noqa: E402

TEST_SECRET = "test-secret-32-chars-minimum-ok!!"


def _u(role="student", feature_tier="free", uid="u1"):
    return types.SimpleNamespace(
        id=uid, email="u@example.com", full_name="U", role=role,
        feature_tier=feature_tier, is_active=True,
    )


class _FakeColl:
    """Minimal async Motor-shaped collection for the maps these tests touch."""

    def __init__(self, docs=None):
        self.docs = list(docs or [])

    async def find_one(self, q, projection=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items() if not k.startswith("$")):
                return dict(d)
        return None

    async def insert_one(self, d):
        self.docs.append(dict(d))
        return types.SimpleNamespace(inserted_id="x")

    async def update_one(self, q, update, upsert=False):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                for op, payload in update.items():
                    if op == "$set":
                        d.update(payload)
                    elif op == "$push":
                        for key, val in payload.items():
                            entries = d.setdefault(key, [])
                            if isinstance(val, dict):
                                entries.extend(val.get("$each", []))
                                if "$slice" in val:
                                    del entries[: max(0, len(entries) + val["$slice"])]
                            else:
                                entries.append(val)
                    elif op == "$setOnInsert":
                        for k, v in payload.items():
                            d.setdefault(k, v)
                return types.SimpleNamespace(matched_count=1, modified_count=1)
        if upsert:
            doc = dict(q)
            for op, payload in update.items():
                if op == "$set":
                    doc.update(payload)
                elif op == "$setOnInsert":
                    doc.update(payload)
                elif op == "$push":
                    for key, val in payload.items():
                        entries = doc.setdefault(key, [])
                        if isinstance(val, dict):
                            entries.extend(val.get("$each", []))
                        else:
                            entries.append(val)
            self.docs.append(doc)
            return types.SimpleNamespace(matched_count=0, modified_count=0, upserted_id="new")
        return types.SimpleNamespace(matched_count=0, modified_count=0)

    async def count_documents(self, q):
        return sum(1 for d in self.docs if all(d.get(k) == v for k, v in q.items()))

    def find(self, q, projection=None):
        self._q = q
        return self

    def sort(self, *a, **k):
        return self

    async def to_list(self, n):
        return [dict(d) for d in self.docs
                if all(d.get(k) == v for k, v in getattr(self, "_q", {}).items())][:n]


class _FakeDB:
    def __init__(self, authz=None, users=None):
        # __getitem__ mirrors Motor's db[collection] access used by the routers.
        self._cols = {}
        self.authz_matrix = _FakeColl(
            [{"_id": "matrix", "requirements": dict(authz or {})}])
        self.users = _FakeColl(users or [])
        self.user_feature_overrides = _FakeColl()
        self.platform_flags = _FakeColl()
        self.page_access = _FakeColl()
        self.tier_definitions = _FakeColl()
        self.partner_memory = _FakeColl()
        self.partner_uploads = _FakeColl()
        self.partner_config = _FakeColl()
        self._cols.update({
            "partner_memory": self.partner_memory,
            "partner_uploads": self.partner_uploads,
            "partner_config": self.partner_config,
        })

    def __getitem__(self, name):
        return self._cols.setdefault(name, _FakeColl())


# ══════════════════════════════════════════════════════════════════════════════
# 1. POLICY COMPLETENESS — one definition per surface, all exec-editable
# ══════════════════════════════════════════════════════════════════════════════
def test_every_enforced_feature_has_an_api_surface():
    for feature, required in fc.FEATURE_MIN_TIER.items():
        assert feature in fc.FEATURE_API_PATHS, f"{feature}: enforced but no API surface"
        assert required in fc.TIER_RANK, f"{required}: not a real tier"
        assert fc.FEATURE_API_PATHS[feature], f"{feature}: empty prefix list"


def test_every_enforced_feature_is_exec_editable():
    # A gate the exec console cannot edit is a lock nobody holds the key to.
    try:
        from routers.exec_control import AUTHZ_FEATURE_KEYS
    except ImportError:
        pytest.skip("fastapi/exec_control not importable in this runner")
    for feature in list(fc.FEATURE_MIN_TIER) + list(fc.SOUP_MIN_TIER):
        assert feature in AUTHZ_FEATURE_KEYS, (
            f"{feature} is enforced server-side but absent from the exec "
            "authorization matrix (routers/exec_control.AUTHZ_FEATURES)"
        )


def test_soup_maps_are_complete_and_consistent():
    assert set(fc.SOUP_MIN_TIER) == {"soup", "soup_manual", "soup_full"}
    for filename, feature in fc.SOUP_FILE_FEATURES.items():
        assert feature in fc.SOUP_MIN_TIER, f"{filename}: unknown feature {feature}"
        assert (fc.SOUP_PATH_PREFIX + filename) not in ("",), filename


def test_soup_map_matches_the_ui_catalog():
    """Every Soup file the launcher lists is gated server-side by the same
    feature it shows in the UI (frontend/src/lib/originalTools.js)."""
    tools_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "frontend", "src", "lib", "originalTools.js",
    )
    if not os.path.exists(tools_path):
        pytest.skip("frontend/src/lib/originalTools.js not present")
    src = open(tools_path, encoding="utf-8").read()
    soup_block = src.split("The Soup", 1)[1]
    ui_paths = {}
    for chunk in soup_block.split("slug:")[1:]:
        path = chunk.split('path: "', 1)[1].split('"', 1)[0]
        feature = chunk.split('feature: "', 1)[1].split('"', 1)[0]
        ui_paths[path.rsplit("/", 1)[1]] = feature
    assert ui_paths, "could not parse the Soup entries from originalTools.js"
    for filename, feature in ui_paths.items():
        assert fc.SOUP_FILE_FEATURES.get(filename) == feature, (
            f"{filename}: server gate says {fc.SOUP_FILE_FEATURES.get(filename)}, "
            f"UI catalog says {feature}"
        )


def test_soup_files_actually_exist_in_the_build_input():
    public = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "frontend", "public", "mini-more-help-center",
    )
    if not os.path.isdir(public):
        pytest.skip("frontend/public/mini-more-help-center not present")
    # rule_90211.mp3 is the documented pre-existing gap (docs/TIER_BASELINE.md
    # §4.6): soup-suno.html references it and it exists nowhere in the repo. It
    # stays in the gate map so the day the owner supplies the asset it is
    # protected automatically — nothing else may be missing.
    for filename in fc.SOUP_FILE_FEATURES:
        if filename == "rule_90211.mp3":
            continue
        assert os.path.isfile(os.path.join(public, filename)), (
            f"{filename} is gated but absent from the public bundle"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 2. AI CHAT — member+ or BYOK; keyword-KB helper stays free
# ══════════════════════════════════════════════════════════════════════════════
def test_ai_chat_is_member_everywhere():
    assert fc.FEATURE_MIN_TIER["ai_chat"] == "member"
    frontend = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "frontend", "src", "lib", "tiers.js",
    )
    if os.path.exists(frontend):
        src = open(frontend, encoding="utf-8").read()
        assert 'ai_chat: "member"' in src, "frontend tiers.js drifted from the backend map"


def _check(db, user, path):
    return asyncio.run(fc.check_user_feature_access(db, user, path))


def test_ai_chat_free_user_is_blocked():
    db = _FakeDB(users=[{"id": "u1", "byok_enabled": False}])
    action, detail = _check(db, _u(feature_tier="free"), "/api/ai/chat")
    assert action == "block" and "Member plan" in detail


def test_ai_chat_byok_user_passes():
    db = _FakeDB(users=[{"id": "u1", "byok_enabled": True}])
    assert _check(db, _u(feature_tier="free"), "/api/ai/chat") == ("pass", None)


def test_ai_chat_member_passes():
    db = _FakeDB(users=[{"id": "u1", "byok_enabled": False}])
    assert _check(db, _u(feature_tier="member"), "/api/ai/chat") == ("pass", None)


def test_ai_chat_keyword_kb_helper_stays_free_for_signed_in_users():
    db = _FakeDB(users=[{"id": "u1", "byok_enabled": False}])
    assert _check(db, _u(feature_tier="free"), "/api/ai/helper") == ("pass", None)


def test_ai_chat_staff_bypasses_every_tier():
    db = _FakeDB(users=[])
    assert _check(db, _u(role="executive_admin", feature_tier="free"), "/api/ai/chat") == ("pass", None)
    assert _check(db, _u(role="admin", feature_tier="free"), "/api/ai/chat") == ("pass", None)


# ══════════════════════════════════════════════════════════════════════════════
# 3. PUZZLES vs SOVEREIGN
# ══════════════════════════════════════════════════════════════════════════════
def test_puzzles_are_their_own_free_feature():
    assert fc.FEATURE_MIN_TIER["puzzles"] == "free"
    assert fc.feature_for_path("/api/puzzles/next") == "puzzles"
    assert fc.feature_for_path("/api/puzzles/answer") == "puzzles"
    assert fc.feature_for_path("/api/sovereign/chat") == "sovereign"


def test_free_user_can_play_the_daily_puzzle():
    db = _FakeDB()
    assert _check(db, _u(feature_tier="free"), "/api/puzzles/next") == ("pass", None)


def test_sovereign_chat_stays_executive():
    db = _FakeDB()
    action, detail = _check(db, _u(feature_tier="plus"), "/api/sovereign/chat")
    assert action == "block" and "Executive plan" in detail
    assert _check(db, _u(role="executive_admin"), "/api/sovereign/chat") == ("pass", None)


# ══════════════════════════════════════════════════════════════════════════════
# 4. THE SOUP — byte gate
# ══════════════════════════════════════════════════════════════════════════════
def test_soup_path_mapping():
    assert fc.soup_feature_for_path("/mini-more-help-center/soup-confusion.html") == "soup"
    assert fc.soup_feature_for_path("/mini-more-help-center/soup-founders-manual.html") == "soup_manual"
    assert fc.soup_feature_for_path("/mini-more-help-center/soup-broadcast.html") == "soup_full"
    assert fc.soup_feature_for_path("/mini-more-help-center/soup-partner.html") == "soup_full"
    # Unknown file under the prefix is never confirmed to exist.
    assert fc.soup_feature_for_path("/mini-more-help-center/nope.html") is None
    assert fc.soup_feature_for_path("/api/ai/chat") is None


def test_soup_per_file_tiers():
    db = _FakeDB()
    free = _u(feature_tier="free")
    member = _u(feature_tier="member")
    plus = _u(feature_tier="plus")
    owner = _u(role="executive_admin")

    # free (any signed-in account): the Soup's way in
    assert asyncio.run(fc.check_soup_file_access(db, free, "/mini-more-help-center/soup-confusion.html")) == ("allow", None)
    action, detail = asyncio.run(fc.check_soup_file_access(db, free, "/mini-more-help-center/soup-founders-manual.html"))
    assert action == "block" and "Member plan" in detail
    action, detail = asyncio.run(fc.check_soup_file_access(db, free, "/mini-more-help-center/soup-broadcast.html"))
    assert action == "block" and "Plus plan" in detail

    # member: the manual suite
    assert asyncio.run(fc.check_soup_file_access(db, member, "/mini-more-help-center/soup-tactics.html")) == ("allow", None)
    action, _ = asyncio.run(fc.check_soup_file_access(db, member, "/mini-more-help-center/soup-broadcast.html"))
    assert action == "block"

    # plus: the production suite
    assert asyncio.run(fc.check_soup_file_access(db, plus, "/mini-more-help-center/soup-broadcast.html")) == ("allow", None)
    assert asyncio.run(fc.check_soup_file_access(db, plus, "/mini-more-help-center/soup-partner.html")) == ("allow", None)

    # owner / executive: nothing on this platform is locked away from them
    for f in fc.SOUP_FILE_FEATURES:
        assert asyncio.run(fc.check_soup_file_access(db, owner, fc.SOUP_PATH_PREFIX + f)) == ("allow", None)
        assert asyncio.run(fc.check_soup_file_access(db, _u(role="admin"), fc.SOUP_PATH_PREFIX + f)) == ("allow", None)


def test_soup_tier_is_editable_from_the_exec_matrix():
    # An executive retires soup_manual to free in db.authz_matrix → the gate
    # enforces it on the very next request (no redeploy, no code edit).
    db = _FakeDB(authz={"soup_manual": "free"})
    assert asyncio.run(fc.load_soup_tier_requirements(db))["soup_manual"] == "free"
    assert asyncio.run(fc.check_soup_file_access(
        db, _u(feature_tier="free"), "/mini-more-help-center/soup-founders-manual.html")) == ("allow", None)
    # Unknown keys/tiers in the matrix are dropped, never invented into gates.
    db2 = _FakeDB(authz={"soup_manual": "not_a_tier", "nope": "plus"})
    assert asyncio.run(fc.load_soup_tier_requirements(db2))["soup_manual"] == "member"
    assert "nope" not in asyncio.run(fc.load_soup_tier_requirements(db2))


class _GateUser:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _soup_verdict(db, user_doc, path, token=None, secret=TEST_SECRET):
    tok = token if token is not None else pyjwt.encode(
        {"sub": user_doc["id"], "tv": 0}, secret, algorithm="HS256")
    return asyncio.run(soup_gate_verdict(
        db=db, path=path, auth_header=f"Bearer {tok}" if tok else "",
        cookie_token=None, jwt_secret=secret, jwt_algo="HS256",
        user_cls=_GateUser,
    ))


def test_soup_gate_anonymous_is_401_and_unknown_file_is_404():
    db = _FakeDB(users=[{"id": "u1", "role": "student", "feature_tier": "member"}])
    # No credential at all.
    v = asyncio.run(soup_gate_verdict(
        db=db, path="/mini-more-help-center/soup-confusion.html", auth_header="",
        cookie_token=None, jwt_secret=TEST_SECRET, jwt_algo="HS256", user_cls=_GateUser))
    assert v[0] == 401
    # Unknown file under the prefix never confirms existence.
    v = _soup_verdict(db, {"id": "u1"}, "/mini-more-help-center/does-not-exist.html")
    assert v[0] == 404


def test_soup_gate_accepts_the_scoped_session_cookie():
    db = _FakeDB(users=[{"id": "u1", "role": "student", "feature_tier": "free"}])
    tok = pyjwt.encode({"sub": "u1", "tv": 0}, TEST_SECRET, algorithm="HS256")
    v = asyncio.run(soup_gate_verdict(
        db=db, path="/mini-more-help-center/soup-confusion.html", auth_header="",
        cookie_token=tok, jwt_secret=TEST_SECRET, jwt_algo="HS256", user_cls=_GateUser))
    assert v is None  # allowed — the cookie is what the Soup's pages rely on
    # A member-only file still respects the tier with a cookie present.
    v = asyncio.run(soup_gate_verdict(
        db=db, path="/mini-more-help-center/soup-broadcast.html", auth_header="",
        cookie_token=tok, jwt_secret=TEST_SECRET, jwt_algo="HS256", user_cls=_GateUser))
    assert v[0] == 403 and "Plus plan" in v[1]


def test_soup_gate_revoked_token_version_is_rejected():
    db = _FakeDB(users=[{"id": "u1", "role": "student", "feature_tier": "plus",
                         "token_version": 3}])
    tok = pyjwt.encode({"sub": "u1", "tv": 0}, TEST_SECRET, algorithm="HS256")
    v = asyncio.run(soup_gate_verdict(
        db=db, path="/mini-more-help-center/soup-broadcast.html", auth_header=f"Bearer {tok}",
        cookie_token=None, jwt_secret=TEST_SECRET, jwt_algo="HS256", user_cls=_GateUser))
    assert v[0] == 401


# ══════════════════════════════════════════════════════════════════════════════
# 5. THE PARTNER API
# ══════════════════════════════════════════════════════════════════════════════
def _stub_gateway(reply="✅ Executed.\n\n| Metric | Value |\n|--------|-------|\n| Artists Onboarded | 2 |\n\nNEXT: ship the eBook"):
    mod = types.ModuleType("ai.llm_gateway")

    async def call_llm(**kwargs):
        return {"provider": "free-tier", "text": reply}

    mod.call_llm = call_llm
    return mod


def _partner_client(monkeypatch, users):
    import routers.soup_partner as sp
    db = _FakeDB(users=users)
    sp.bind(db, None, TEST_SECRET, "HS256")
    monkeypatch.setitem(sys.modules, "ai.llm_gateway", _stub_gateway())
    app = FastAPI()
    app.include_router(sp.router, prefix="/api")
    return TestClient(app), db


def _tok(sub="u1", secret=TEST_SECRET):
    return pyjwt.encode({"sub": sub, "tv": 0}, secret, algorithm="HS256")


def _udoc(uid, role="student", tier="free", byok=False):
    return {"id": uid, "email": f"{uid}@example.com", "full_name": uid.upper(),
            "role": role, "feature_tier": tier, "byok_enabled": byok,
            "is_active": True, "token_version": 0}


def test_partner_requires_authentication(monkeypatch):
    client, _ = _partner_client(monkeypatch, users=[])
    assert client.post("/api/partner", json={"prompt": "go"}).status_code == 401
    assert client.get("/api/memory").status_code == 401


def test_partner_enforces_the_member_ai_contract(monkeypatch):
    users = [_udoc("u1", "student", "free", False),
             _udoc("u2", "student", "member", False),
             _udoc("u3", "student", "free", True),
             _udoc("u4", "instructor", "free", False)]
    client, _ = _partner_client(monkeypatch, users=users)

    r = client.post("/api/partner", json={"prompt": "build the eBook"},
                    headers={"Authorization": f"Bearer {_tok('u1')}"})
    assert r.status_code == 403 and "Member" in r.json()["detail"]

    for uid in ("u2", "u3", "u4"):
        r = client.post("/api/partner", json={"prompt": "build the eBook"},
                        headers={"Authorization": f"Bearer {_tok(uid)}"})
        assert r.status_code == 200, (uid, r.text)
        body = r.json()
        assert body["success"] is True and body["response"]
        assert "dashboard" in body and "actions" in body


def test_partner_accepts_the_scoped_cookie(monkeypatch):
    users = [_udoc("u2", "student", "member", False)]
    client, _ = _partner_client(monkeypatch, users=users)
    client.cookies.set("lce_session", _tok("u2"))
    r = client.post("/api/partner", json={"prompt": "ship it"})
    assert r.status_code == 200, r.text


def test_partner_never_stores_a_provider_key(monkeypatch):
    users = [_udoc("u2", "student", "member", False)]
    client, db = _partner_client(monkeypatch, users=users)
    r = client.post("/api/config", json={"apiKey": "sk-live-should-never-be-stored",
                                         "model": "meta-llama/llama-3-8b-instruct"},
                    headers={"Authorization": f"Bearer {_tok('u2')}"})
    assert r.status_code == 200
    assert r.json()["key_stored"] is False
    stored = db.partner_config.docs[0]
    assert "sk-live-should-never-be-stored" not in str(stored)
    assert stored["model"] == "meta-llama/llama-3-8b-instruct"
    # GET never echoes a key either.
    assert "apiKey" not in str(client.get("/api/config",
        headers={"Authorization": f"Bearer {_tok('u2')}"}).json())


def test_partner_upload_memory_and_report(monkeypatch):
    users = [_udoc("u2", "student", "member", False)]
    client, db = _partner_client(monkeypatch, users=users)
    h = {"Authorization": f"Bearer {_tok('u2')}"}

    raw = b"partner workspace bytes"
    r = client.post("/api/upload", json={
        "projectName": "Sovereign eBook",
        "files": [{"name": "chapter.txt", "type": "text/plain",
                   "size": len(raw), "data": base64.b64encode(raw).decode()}],
    }, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["project"] == "Sovereign eBook"
    assert db.partner_uploads.docs and db.partner_uploads.docs[0]["data_b64"]

    # Oversized upload is rejected, not silently truncated.
    big = base64.b64encode(b"x" * (10 * 1024 * 1024 + 10)).decode()
    r = client.post("/api/upload", json={"files": [{"name": "big.bin", "data": big}]}, headers=h)
    assert r.status_code == 413

    r = client.get("/api/memory", headers=h)
    assert r.status_code == 200 and r.json()["memory"] == []

    r = client.post("/api/report", json={"type": "financial"}, headers=h)
    assert r.status_code == 200
    assert "FINANCIAL REPORT" in r.json()["content"]


def test_partner_memory_is_persisted_per_user(monkeypatch):
    users = [_udoc("u2", "student", "member", False),
             _udoc("u9", "student", "member", False)]
    client, _ = _partner_client(monkeypatch, users=users)
    client.post("/api/partner", json={"prompt": "first command"},
                headers={"Authorization": f"Bearer {_tok('u2')}"})
    mem = client.get("/api/memory", headers={"Authorization": f"Bearer {_tok('u2')}"}).json()["memory"]
    assert [m["role"] for m in mem] == ["user", "partner"]
    # Another member's memory is not visible.
    other = client.get("/api/memory", headers={"Authorization": f"Bearer {_tok('u9')}"}).json()["memory"]
    assert other == []
