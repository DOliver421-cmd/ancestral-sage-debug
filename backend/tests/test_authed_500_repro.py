"""Live-defect repro: authenticated requests 500 on production while
anonymous paths 401 correctly (evidence: 2026-09-02 QA account probes).

Runs the REAL FastAPI app (server.app, all routers, FCC middleware) with a
minimal async in-memory Mongo stand-in, and issues real HTTP requests via
TestClient — no startup event, so nothing outside the request path runs.
Whatever raises here is the production root cause, printed verbatim.
"""
import pytest
from types import SimpleNamespace
from fastapi.testclient import TestClient


class _FakeAsyncCollection:
    """Just enough of motor's async API for the authed request path."""

    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def find(self, q=None, proj=None, **kw):
        return _FakeCursor(self._match(q))

    def _match(self, q):
        # Very small subset of Mongo matching — enough for user_id/id lookups
        out = []
        for d in self.docs:
            ok = True
            for k, v in (q or {}).items():
                if k == "_id":
                    continue
                if k.endswith("$ne"):
                    if d.get(k[:-3]) == v:
                        ok = False
                elif k == "id" and isinstance(v, dict):
                    continue
                elif d.get(k) != v:
                    ok = False
            if ok:
                out.append(d)
        return out

    async def find_one(self, q=None, proj=None, **kw):
        m = self._match(q)
        return dict(m[0]) if m else None

    async def insert_one(self, d):
        self.docs.append(dict(d))
        return SimpleNamespace(inserted_id="x")

    async def update_one(self, q, upd, *a, **kw):
        m = self._match(q)
        for d in m:
            self._apply(d, upd)
        return SimpleNamespace(matched_count=len(m), modified_count=len(m))

    def _apply(self, d, upd):
        for k, v in (upd.get("$set") or {}).items():
            d[k] = v
        for k, v in (upd.get("$unset") or {}).items():
            d.pop(k, None)
        for k, v in (upd.get("$inc") or {}).items():
            d[k] = d.get(k, 0) + v

    async def count_documents(self, q=None, **kw):
        return len(self._match(q))

    async def delete_many(self, q=None):
        n = len(self._match(q))
        self.docs = [d for d in self.docs if d not in self._match(q)]
        return SimpleNamespace(deleted_count=n)

    def __getitem__(self, name):
        return self  # allow db["coll"] style


class _FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    def sort(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    async def to_list(self, n=None):
        return [dict(d) for d in self._docs]


class _FakeDB:
    def __init__(self):
        self.users = _FakeAsyncCollection()
        self.progress = _FakeAsyncCollection()
        self.audit_log = _FakeAsyncCollection()
        self.modules = _FakeAsyncCollection()
        self.auth_sessions = _FakeAsyncCollection()

    def __getitem__(self, name):
        if not hasattr(self, name):
            setattr(self, name, _FakeAsyncCollection())
        return getattr(self, name)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self.__dict__:
            setattr(self, name, _FakeAsyncCollection())
        return self.__dict__[name]


REGISTER_DOC = {
    "id": "11111111-2222-3333-4444-555555555555",
    "email": "qa.repro@morehelp.center",
    "full_name": "QA Repro",
    "role": "student",
    "is_active": True,
    "must_change_password": False,
    "created_at": "2026-09-02T21:01:22.123456+00:00",
    "password_hash": "$2b$12$notarealhashnotarealhashnotarealhash",
    "token_version": 0,
    "terms_accepted_at": "2026-09-02T21:01:22.123456+00:00",
    "over_13_confirmed": True,
    "feature_tier": "free",
}


@pytest.fixture()
def client(monkeypatch):
    import server

    fake = _FakeDB()
    fake.users.docs.append(dict(REGISTER_DOC))
    monkeypatch.setattr(server, "db", fake)
    token = server.make_token(
        REGISTER_DOC["id"], "student", extra={"tv": 0, "session_id": "sess-1"}
    )
    return TestClient(server.app, raise_server_exceptions=True), token


def test_authed_paths_live_repro(client):
    tc, token = client
    auth = {"Authorization": f"Bearer {token}"}

    r = tc.get("/api/auth/me", headers=auth)
    print("\nGET /api/auth/me →", r.status_code, r.text[:200])
    assert r.status_code == 200, f"/auth/me regressed: {r.status_code} {r.text[:200]}"

    r = tc.patch("/api/auth/me", headers={**auth, "Content-Type": "application/json"},
                 json={"full_name": "QA Repro"})
    print("PATCH /api/auth/me →", r.status_code, r.text[:200])
    assert r.status_code == 200, f"PATCH /auth/me regressed: {r.status_code} {r.text[:200]}"

    r = tc.get("/api/progress/me", headers=auth)
    print("GET /api/progress/me →", r.status_code, r.text[:200])
    # The regression this suite exists for is the AttributeError → 500. The
    # FCC tier matrix may legitimately deny a free-tier student (structured
    # 403 ACCESS_ENFORCED) — that is the access policy working, not a defect.
    assert r.status_code != 500, f"/progress/me regressed to 500: {r.text[:200]}"
    if r.status_code == 403:
        assert "ACCESS_ENFORCED" in r.text, f"403 must be structured FCC denial: {r.text[:200]}"
    else:
        assert r.status_code == 200, f"/progress/me unexpected: {r.status_code} {r.text[:200]}"
