"""Tests for the promo-code tier-grant system.

Covers:
- POST /api/promo/validate          (public preview)
- Promo redemption inside register  (auth router, via reserve_promo/grant_fields)
- Admin CRUD on /api/admin/promo-codes
"""
import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import routers.promo_codes as promo


class _FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs if docs is not None else []
        self.next_id = 1

    def find(self, q, proj=None, **kw):
        return self

    def sort(self, *a, **k):
        return self

    async def to_list(self, n):
        return [dict(d) for d in self.docs]

    async def find_one(self, q, proj=None, **kw):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                return dict(d)
        return None

    async def find_one_and_update(self, q, update, **kw):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items() if k not in ("$expr",)):
                # fake $expr: max_uses null or uses < max
                max_uses = d.get("max_uses")
                if max_uses is not None and d.get("uses_count", 0) >= max_uses:
                    continue
                for op, fields in update.items():
                    for k, v in fields.items():
                        if op == "$inc":
                            d[k] = d.get(k, 0) + v
                        elif op == "$set":
                            d[k] = v
                return dict(d)
        return None

    async def insert_one(self, d):
        d = dict(d)
        d["id"] = f"id{self.next_id}"
        self.next_id += 1
        self.docs.append(d)
        return SimpleNamespace(inserted_id=d["id"])

    async def update_one(self, q, update):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                for op, fields in update.items():
                    for k, v in fields.items():
                        if op == "$set":
                            d[k] = v
                        elif op == "$inc":
                            d[k] = d.get(k, 0) + v
                return SimpleNamespace(matched_count=1, modified_count=1)
        return SimpleNamespace(matched_count=0, modified_count=0)

    async def delete_one(self, q):
        before = len(self.docs)
        self.docs = [d for d in self.docs if not all(d.get(k) == v for k, v in q.items())]
        return SimpleNamespace(deleted_count=before - len(self.docs))

    async def count_documents(self, q=None):
        return len(self.docs)


def make_code(**over):
    base = {
        "code": "LEGACY704", "granted_tier": "member", "label": "Legacy Student",
        "description": "", "max_uses": None, "uses_count": 0, "expires_at": None,
        "active": True, "duration_days": None, "created_by": "system",
        "note": "", "created_at": datetime.now(timezone.utc).isoformat(),
    }
    base.update(over)
    return base


@pytest.fixture
def db():
    return SimpleNamespace(promo_codes=_FakeCollection())


@pytest.fixture
def client(db):
    audits = []

    async def _current_user(authorization=None):
        if not authorization:
            raise HTTPException(401, "Not authenticated")
        return SimpleNamespace(id="u1", email="a@b.c", full_name="A", role="admin", feature_tier="free")

    async def _audit(*a, **k):
        audits.append((a, k))

    promo.bind(db, _current_user, _audit)
    app = FastAPI()
    app.include_router(promo.router, prefix="/api")
    c = TestClient(app)
    c._audits = audits
    return c


def test_validate_unknown_code(client):
    r = client.post("/api/promo/validate", json={"code": "NOPE"})
    assert r.status_code == 200
    assert r.json()["valid"] is False


def test_validate_valid_code(client, db):
    db.promo_codes.docs.append(make_code())
    r = client.post("/api/promo/validate", json={"code": "legacy704"})  # case-insensitive
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["tier"] == "member"


def test_validate_inactive_and_expired(client, db):
    db.promo_codes.docs.append(make_code(active=False))
    assert client.post("/api/promo/validate", json={"code": "LEGACY704"}).json()["valid"] is False

    db.promo_codes.docs.clear()
    expired = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    db.promo_codes.docs.append(make_code(expires_at=expired))
    assert client.post("/api/promo/validate", json={"code": "LEGACY704"}).json()["valid"] is False


def test_validate_exhausted(client, db):
    db.promo_codes.docs.append(make_code(max_uses=1, uses_count=1))
    assert client.post("/api/promo/validate", json={"code": "LEGACY704"}).json()["valid"] is False


def test_reserve_is_atomic_and_release_restores(client, db):
    db.promo_codes.docs.append(make_code(max_uses=2))
    doc = asyncio.run(promo.reserve_promo("legacy704"))
    assert doc is not None
    assert doc["uses_count"] == 1
    # second reserve still allowed (max 2)
    doc2 = asyncio.run(promo.reserve_promo("LEGACY704"))
    assert doc2 is not None and doc2["uses_count"] == 2
    # third must fail
    doc3 = asyncio.run(promo.reserve_promo("LEGACY704"))
    assert doc3 is None
    asyncio.run(promo.release_promo("LEGACY704"))
    assert db.promo_codes.docs[0]["uses_count"] == 1


def test_grant_fields_with_duration():
    doc = make_code(duration_days=365)
    fields = promo.grant_fields_for(doc)
    assert fields["feature_tier"] == "member"
    assert fields["feature_tier_source"] == "promo"
    assert fields["feature_tier_product"] == "promo:LEGACY704"
    assert fields["feature_tier_expires_at"] is not None
    assert fields["feature_tier_revert_to"] == "free"
    assert fields["promo_code_redeemed"] == "LEGACY704"


def test_grant_fields_permanent_has_no_expiry():
    fields = promo.grant_fields_for(make_code(duration_days=None))
    assert "feature_tier_expires_at" not in fields
    assert "feature_tier_revert_to" not in fields


def test_admin_create_and_list(client, db):
    h = {"Authorization": "Bearer x"}
    r = client.post("/api/admin/promo-codes", json={
        "code": " summer-2026 ", "granted_tier": "plus", "max_uses": 5,
        "duration_days": 30, "note": "test"},
        headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == "SUMMER-2026"  # normalized uppercase + trimmed
    assert body["granted_tier"] == "plus"

    r = client.get("/api/admin/promo-codes", headers=h)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_admin_create_duplicate_conflicts(client, db):
    db.promo_codes.docs.append(make_code())
    r = client.post("/api/admin/promo-codes", json={"code": "legacy704", "granted_tier": "member"}, headers={"Authorization": "Bearer x"})
    assert r.status_code == 409


def test_admin_create_rejects_bad_tier(client):
    r = client.post("/api/admin/promo-codes", json={"code": "X", "granted_tier": "galaxy"}, headers={"Authorization": "Bearer x"})
    assert r.status_code == 400


def test_admin_update_and_delete(client, db):
    db.promo_codes.docs.append(make_code())
    h = {"Authorization": "Bearer x"}
    r = client.patch("/api/admin/promo-codes/LEGACY704", json={"active": False, "max_uses": 3}, headers=h)
    assert r.status_code == 200
    assert r.json()["active"] is False and r.json()["max_uses"] == 3

    r = client.delete("/api/admin/promo-codes/LEGACY704", headers=h)
    assert r.status_code == 200
    assert db.promo_codes.docs == []


def test_admin_endpoints_require_admin(client):
    # no auth header → 401
    assert client.get("/api/admin/promo-codes").status_code == 401
    assert client.post("/api/admin/promo-codes", json={"code": "A1", "granted_tier": "member"}).status_code == 401


def test_seed_default_promos_is_idempotent(db):
    promo.bind(db, None, None)
    asyncio.run(promo.seed_default_promos())
    assert len(db.promo_codes.docs) == 1
    assert db.promo_codes.docs[0]["code"] == "LEGACY704"
    assert db.promo_codes.docs[0]["granted_tier"] == "member"
    asyncio.run(promo.seed_default_promos())
    assert len(db.promo_codes.docs) == 1  # no duplicate


# ═══ Register flow integration (promo grants tier at signup) ═════════════════
class _FakeAuthDB:
    def __init__(self):
        self.users = _FakeCollection([])
        self.auth_sessions = _FakeCollection([])
        self.promo_codes = _FakeCollection([])


@pytest.fixture
def auth_client():
    import routers.auth as auth_mod
    from routers import promo_codes as _promo_mod

    class _Users(_FakeCollection):
        def __init__(self):
            super().__init__([])

        async def count_documents(self, q=None):
            return len(self.docs)

    class _Sessions(_FakeCollection):
        def __init__(self):
            super().__init__([])

    auth_db = SimpleNamespace(
        users=_Users(),
        auth_sessions=_Sessions(),
        promo_codes=_FakeCollection([]),
    )
    audit_log = []

    async def _noop_send_welcome(email, full_name):
        return None

    async def _audit(*a, **k):
        audit_log.append((a, k))

    def _hash(pw):
        return f"hash:{pw}"

    def _token(uid, role, **kw):
        return f"token-{uid}"

    auth_mod.bind(auth_db, _audit, lambda *a, **k: None, lambda h: None,
                  lambda *a, **k: True, lambda *a, **k: None, _hash,
                  lambda *a, **k: True, _token, _noop_send_welcome,
                  lambda *a, **k: "/reset", _noop_send_welcome, lambda *a, **k: "pw")
    _promo_mod.bind(auth_db, lambda h: None, _audit)

    app = FastAPI()
    app.include_router(auth_mod.router, prefix="/api")
    c = TestClient(app)
    c._auth_db = auth_db
    c._audit_log = audit_log
    return c


def _register_payload(**over):
    payload = {
        "email": "legacy@example.com",
        "full_name": "Legacy Student",
        "password": "supersecret1",
        "agreed_terms": True,
        "over_13": True,
    }
    payload.update(over)
    return payload


def test_register_with_valid_promo_grants_member_tier(auth_client):
    auth_client._auth_db.promo_codes.docs.append(make_code())
    r = auth_client.post("/api/auth/register", json=_register_payload(promo_code="legacy704"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user"]["feature_tier"] == "member"

    saved = auth_client._auth_db.users.docs[0]
    assert saved["feature_tier"] == "member"
    assert saved["feature_tier_source"] == "promo"
    assert saved["feature_tier_product"] == "promo:LEGACY704"
    assert saved["promo_code_redeemed"] == "LEGACY704"
    # one use consumed
    assert auth_client._auth_db.promo_codes.docs[0]["uses_count"] == 1
    # both audits fired
    kinds = [a[0][1] for a in auth_client._audit_log]
    assert "promo.redeemed" in kinds


def test_register_with_invalid_promo_rejected_no_account(auth_client):
    r = auth_client.post("/api/auth/register", json=_register_payload(promo_code="BOGUS"))
    assert r.status_code == 400
    assert "invalid" in r.json()["detail"].lower()
    assert auth_client._auth_db.users.docs == []


def test_register_with_exhausted_promo_rejected(auth_client):
    auth_client._auth_db.promo_codes.docs.append(make_code(max_uses=1, uses_count=1))
    r = auth_client.post("/api/auth/register", json=_register_payload(promo_code="LEGACY704"))
    assert r.status_code == 400
    assert auth_client._auth_db.users.docs == []


def test_register_without_promo_stays_free(auth_client):
    r = auth_client.post("/api/auth/register", json=_register_payload())
    assert r.status_code == 200, r.text
    assert r.json()["user"]["feature_tier"] == "free"
    saved = auth_client._auth_db.users.docs[0]
    assert "promo_code_redeemed" not in saved
