"""
Regression tests for the Dual-Trigger Visual Rollback System
(routers/system_rollback.py) and its payment webhook integration.

Reality being pinned (owner directive, 2026-09-02):
1. Exactly 3 restore points are retained (FIFO N-3 rotation).
2. Rollback restores CONFIGURATION collections only — creator earnings,
   payments, purchases, BYOK keys, credentials, users and the audit log are
   NEVER touched, even by a poisoned snapshot.
3. External trigger requires a valid HMAC-SHA256 X-MORE-Signature.
4. Admin trigger is gated to admin/executive_admin.
5. While the rollback lock is active, payment webhooks are persisted to the
   deferred queue and the caller must return 503 (provider retries), so a
   paid entitlement is never dropped mid-rollback.
6. The rollback engine calls Railway `deploymentRedeploy` with the restore
   point's deployment id.

Runs endpoint/engine coroutines directly with faked db/user (no server,
no MongoDB, no provider calls) — pytest-asyncio is not configured in this
repo, so asyncio.run() is used.
"""
import asyncio
import base64
import json
import os
import sys
from datetime import datetime, timezone
from types import SimpleNamespace

os.environ.setdefault("MORE_ROLLBACK_WEBHOOK_SECRET", "test-secret-rollback")
os.environ.setdefault("RAILWAY_DEPLOYMENT_ID", "dep-live-001")
os.environ.setdefault("COMMIT_SHA", "sha-live-001")
os.environ.pop("RAILWAY_TOKEN", None)

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import routers.system_rollback as sr


def _run(coro):
    return asyncio.run(coro)


# ── Fakes ───────────────────────────────────────────────────────────────────
class FakeResult:
    def __init__(self, deleted_count=0):
        self.deleted_count = deleted_count


class FakeCursor:
    def __init__(self, docs, sort=None):
        self.docs = list(docs)
        self.sort_spec = sort

    def sort(self, *args):
        self.sort_spec = args
        return self

    async def to_list(self, n):
        docs = self.docs
        if self.sort_spec:
            spec = [(s[0], -1 if (s[1] if len(s) > 1 else 1) == -1 else 1) for s in self.sort_spec]
            for key, direction in reversed(spec):
                docs = sorted(docs, key=lambda d, k=key: d.get(k, ""), reverse=(direction == -1))
        return docs[:n] if n else docs

    def __aiter__(self):
        self._it = iter(self.docs)
        return self

    async def __anext__(self):
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration


class FakeColl:
    def __init__(self):
        self.docs = []

    def _match(self, doc, filt):
        if filt is None:
            return True
        for k, v in filt.items():
            if k == "_id" and isinstance(v, dict) and "$nin" in v:
                if doc.get("_id") in v["$nin"]:
                    return False
                continue
            if doc.get(k) != v:
                return False
        return True

    def find(self, filt=None, projection=None, sort=None):
        out = [d for d in self.docs if self._match(d, filt)]
        if projection:
            exclude = [k for k, v in projection.items() if not v]
            include = [k for k, v in projection.items() if v]
            if include:
                out = [{k: doc[k] for k in doc if k in include} for doc in out]
            elif exclude:
                out = [{k: v for k, v in doc.items() if k not in exclude} for doc in out]
        return FakeCursor(out, sort=sort)

    async def find_one(self, filt=None, projection=None):
        for d in self.docs:
            if self._match(d, filt):
                if projection:
                    exclude = [k for k, v in projection.items() if not v]
                    include = [k for k, v in projection.items() if v]
                    if include:
                        return {k: d[k] for k in d if k in include}
                    if exclude:
                        return {k: v for k, v in d.items() if k not in exclude}
                return dict(d)
        return None

    async def insert_one(self, doc):
        d = dict(doc)
        d.setdefault("_id", len(self.docs) + 1)
        self.docs.append(d)
        return SimpleNamespace(inserted_id=d["_id"])

    async def delete_many(self, filt=None):
        before = len(self.docs)
        self.docs = [d for d in self.docs if not self._match(d, filt)]
        return FakeResult(deleted_count=before - len(self.docs))

    async def update_one(self, filt, update, upsert=False):
        for d in self.docs:
            if self._match(d, filt):
                if "$set" in update:
                    d.update(update["$set"])
                if "$setOnInsert" in update:
                    d.update(update["$setOnInsert"])
                return SimpleNamespace(modified_count=1)
        if upsert:
            merged = dict(filt)
            if "$set" in update:
                merged.update(update["$set"])
            if "$setOnInsert" in update:
                merged.update(update["$setOnInsert"])
            self.docs.append(merged)
            return SimpleNamespace(modified_count=1)
        return SimpleNamespace(modified_count=0)


class FakeDB:
    def __init__(self):
        self.collections = {}
        for name in sr.RESTORE_CONFIG_COLLECTIONS + sr.LEDGER_COLLECTIONS + ("system_restore_points", "system_state", "deferred_webhooks"):
            self.collections[name] = FakeColl()

    def __getitem__(self, name):
        return self.collections[name]

    def __getattr__(self, name):
        if name.startswith("_") or name == "collections":
            raise AttributeError(name)
        return self.collections[name]


class FakeUser:
    def __init__(self, role):
        self.id = f"u-{role}"
        self.email = f"{role}@test.local"
        self.role = role


AUDIT_LOG = []
NOTIFY_LOG = []


async def fake_audit(actor, action, target=None, meta=None):
    AUDIT_LOG.append({"actor": actor, "action": action, "target": target, "meta": meta})


async def fake_notify(user_id, title, body, link=None, kind="info"):
    NOTIFY_LOG.append({"user_id": user_id, "title": title})




async def fake_current_user(authorization=None):
    if not authorization or not str(authorization).startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    role = str(authorization).split(" ", 1)[1]
    return FakeUser(role)

def fake_assert_role(user, *roles):
    if getattr(user, "role", None) not in roles:
        raise HTTPException(403, "Insufficient privileges")


def _setup(db, *fakes):
    sr.bind(
        db,
        _current_user=fake_current_user,
        _assert_role=fake_assert_role,
        _audit=fake_audit,
        _notify=fake_notify,
    )
    AUDIT_LOG.clear()
    NOTIFY_LOG.clear()


def _config_coll(name):
    return {"feature_id": f"{name}.a", "enabled": True}


async def _seed(db):
    # configuration collections
    db.feature_configs.docs.append(_config_coll("nam"))
    db.feature_configs.docs.append(_config_coll("jamil"))
    db.platform_flags.docs.append({"flag": "public_read", "value": True})
    # ledger collections (must survive every rollback)
    db.creator_earnings.docs.append({"order_ref": "ord-1", "amount_cents": 7000, "status": "pending"})
    db.payments.docs.append({"order_ref": "ord-1", "amount_cents": 10000, "status": "paid"})
    db.user_byok_keys.docs.append({"user_id": "u1", "provider": "openai", "key_enc": "sensitive-byok"})
    db.users.docs.append({"id": "u1", "email": "member@test.local", "role": "member"})
    db.audit_log.docs.append({"action": "seed", "at": "t0"})


def fake_request(payload_bytes, headers=None):
    async def body():
        return payload_bytes

    return SimpleNamespace(body=body, headers=headers or {})


# ── 1. HMAC signature contract ─────────────────────────────────────────────
def test_hmac_valid_and_invalid():
    import hashlib
    import hmac as h

    payload = b'{"hello":"world"}'
    good = h.new(b"test-secret-rollback", payload, hashlib.sha256).hexdigest()
    assert sr.sign_ok(payload, good) is True
    assert sr.sign_ok(payload, good.upper()) is True  # case-insensitive
    assert sr.sign_ok(payload, "deadbeef") is False
    assert sr.sign_ok(payload, "") is False
    assert sr.sign_ok(payload, None) is False
    assert sr.sign_ok(b"tampered", good) is False


# ── 2. N-3 FIFO rotation ───────────────────────────────────────────────────
def test_rotate_keeps_exactly_three_fifo():
    db = FakeDB()
    _setup(db)
    for i in range(5):
        _run(sr.create_restore_point(actor=f"a{i}", trigger="manual"))
    docs = _run(db.system_restore_points.find({}).to_list(50))
    assert len(docs) == 3, f"expected 3, got {len(docs)}"
    triggers = [d["trigger"] for d in sorted(docs, key=lambda d: d["created_at"])]
    assert triggers == ["manual", "manual", "manual"]  # all manual
    # FIFO: the two oldest (first two created) were pruned
    actors = sorted(d["actor"] for d in docs)
    assert actors == ["a2", "a3", "a4"]


# ── 3. Ledger lockdown ────────────────────────────────────────────────────
def test_restore_config_replaces_config_but_never_ledgers():
    db = FakeDB()
    _setup(db)
    _run(_seed(db))
    snapshot = _run(sr._snapshot_config(db))
    # mutate config AFTER the snapshot so a restore must revert it
    db.feature_configs.docs[0]["enabled"] = False
    marker_earning = dict(db.creator_earnings.docs[0])
    marker_payment = dict(db.payments.docs[0])
    marker_byok = dict(db.user_byok_keys.docs[0])

    restored = _run(sr._restore_config(db, snapshot))
    assert restored.get("feature_configs") == 2
    assert db.feature_configs.docs[0]["enabled"] is True  # snapshot restored

    # Ledgers byte-identical
    assert db.creator_earnings.docs[0] == marker_earning
    assert db.payments.docs[0] == marker_payment
    assert db.user_byok_keys.docs[0] == marker_byok
    assert db.users.docs[0]["email"] == "member@test.local"
    assert db.audit_log.docs[0]["action"] == "seed"


def test_restore_refuses_poisoned_snapshot():
    db = FakeDB()
    _setup(db)
    poisoned = {"users": [{"id": "u-evil"}]}
    with pytest.raises(HTTPException) as exc:
        _run(sr._restore_config(db, poisoned))
    assert exc.value.status_code == 500
    assert db.users.docs == []  # never written


# ── 4. Admin gating ────────────────────────────────────────────────────────
def test_admin_gating():
    db = FakeDB()
    _setup(db)
    with pytest.raises(HTTPException) as exc:
        _run(sr.admin_health(fake_request(b"", {"authorization": "Bearer student"})))
    assert exc.value.status_code == 403
    healthy = _run(sr.admin_health(fake_request(b"", {"authorization": "Bearer executive_admin"})))
    assert healthy["engine"] == "dual-trigger visual rollback"
    assert healthy["webhook_secret_configured"] is True
    assert healthy["current_deployment_id"] == "dep-live-001"


# ── 5. Full rollback flow: lock lifecycle + redeploy call + ledger safety ──
def test_rollback_flow_calls_redeploy_and_preserves_ledgers():
    db = FakeDB()
    _setup(db)
    _run(_seed(db))
    rp = _run(sr.create_restore_point(actor="admin", trigger="manual"))
    rp_id = rp["restore_point"]["id"]

    # break a config value so the rollback demonstrably repairs it
    db.feature_configs.docs[0]["enabled"] = False
    ledger_before = dict(db.creator_earnings.docs[0])

    calls = []

    async def fake_redeploy(deployment_id):
        calls.append(deployment_id)
        return {"id": deployment_id, "status": "DEPLOYING"}

    sr._railway_redeploy_impl = fake_redeploy
    try:
        outcome = _run(sr.admin_rollback(
            sr.RollbackReq(restore_point_id=rp_id, confirm=True),
            fake_request(b"", {"authorization": "Bearer admin"}),
        ))
    finally:
        sr._railway_redeploy_impl = None

    assert calls == ["dep-live-001"], calls
    assert outcome["rolled_back"] is True
    assert outcome["ledgers"] == "untouched"
    assert db.feature_configs.docs[0]["enabled"] is True  # repaired by rollback
    assert db.creator_earnings.docs[0] == ledger_before  # ledger untouched
    assert _run(sr.is_rollback_locked(db)) is False  # lock released
    assert any(a["action"] == "system.rollback.executed" for a in AUDIT_LOG)


def test_rollback_requires_confirm():
    db = FakeDB()
    _setup(db)
    rp = _run(sr.create_restore_point(actor="admin", trigger="manual"))
    with pytest.raises(HTTPException) as exc:
        _run(sr.admin_rollback(
            sr.RollbackReq(restore_point_id=rp["restore_point"]["id"], confirm=False),
            fake_request(b"", {"authorization": "Bearer admin"}),
        ))
    assert exc.value.status_code == 400


def test_rollback_missing_railway_token_is_honest():
    db = FakeDB()
    _setup(db)
    rp = _run(sr.create_restore_point(actor="admin", trigger="manual"))
    os.environ.pop("RAILWAY_TOKEN", None)  # already absent
    sr._railway_redeploy_impl = None
    with pytest.raises(HTTPException) as exc:
        _run(sr.admin_rollback(
            sr.RollbackReq(restore_point_id=rp["restore_point"]["id"], confirm=True),
            fake_request(b"", {"authorization": "Bearer admin"}),
        ))
    assert exc.value.status_code == 503
    assert "RAILWAY_TOKEN" in exc.value.detail


# ── 6. Payment webhook deferral ────────────────────────────────────────────
def test_webhook_deferral_when_locked():
    db = FakeDB()
    _setup(db)
    payload = b'{"id":"evt-1"}'
    headers = {"x-signature": "abc", "authorization": "Bearer secret"}

    _run(sr.set_rollback_lock(db, "test"))
    deferred = _run(sr.payment_webhook_maybe_defer(db, "lemon_squeezy", payload, headers))
    assert deferred is True
    queued = _run(db.deferred_webhooks.find({}).to_list(50))
    assert len(queued) == 1
    assert queued[0]["provider"] == "lemon_squeezy"
    assert base64.b64decode(queued[0]["payload_b64"]) == payload
    assert "authorization" not in queued[0]["headers"]  # sensitive headers stripped

    _run(sr.clear_rollback_lock(db))
    deferred2 = _run(sr.payment_webhook_maybe_defer(db, "lemon_squeezy", payload, {}))
    assert deferred2 is False


def test_lock_ttl_expires():
    db = FakeDB()
    _setup(db)
    _run(db.system_state.update_one(
        {"key": sr.ROLLBACK_LOCK_KEY},
        {"$set": {"active": True, "expires_at": datetime.now(timezone.utc).timestamp() - 10}},
        upsert=True,
    ))
    assert _run(sr.is_rollback_locked(db)) is False


# ── 7. External trigger (emergency revert) ─────────────────────────────────
def test_emergency_revert_requires_signature():
    db = FakeDB()
    _setup(db)
    _run(sr.create_restore_point(actor="a", trigger="manual"))
    req = fake_request(b'{"panic":true}', {})
    with pytest.raises(HTTPException) as exc:
        _run(sr.emergency_revert(req))
    assert exc.value.status_code == 401


def test_emergency_revert_valid_signature_executes():
    import hashlib
    import hmac as h

    db = FakeDB()
    _setup(db)
    _run(_seed(db))
    rp = _run(sr.create_restore_point(actor="a", trigger="manual"))
    db.feature_configs.docs[0]["enabled"] = False

    calls = []

    async def fake_redeploy(deployment_id):
        calls.append(deployment_id)
        return {"id": deployment_id, "status": "DEPLOYING"}

    sr._railway_redeploy_impl = fake_redeploy
    try:
        payload = b'{"panic":true}'
        sig = h.new(b"test-secret-rollback", payload, hashlib.sha256).hexdigest()
        outcome = _run(sr.emergency_revert(fake_request(payload, {"x-more-signature": sig})))
    finally:
        sr._railway_redeploy_impl = None

    assert calls == ["dep-live-001"]
    assert outcome["trigger"] == "webhook"
    assert outcome["actor"] == "webhook:emergency-revert"
    assert db.feature_configs.docs[0]["enabled"] is True
    assert any(a["action"] == "system.rollback.executed" and a["actor"] == "webhook:emergency-revert" for a in AUDIT_LOG)


def test_emergency_revert_no_restore_point():
    import hashlib
    import hmac as h

    db = FakeDB()
    _setup(db)
    payload = b'{}'
    sig = h.new(b"test-secret-rollback", payload, hashlib.sha256).hexdigest()
    with pytest.raises(HTTPException) as exc:
        _run(sr.emergency_revert(fake_request(payload, {"x-more-signature": sig})))
    assert exc.value.status_code == 404


# ── 8. Visual-state ingest ─────────────────────────────────────────────────
def test_visual_state_ingest_attaches_to_latest():
    import hashlib
    import hmac as h

    db = FakeDB()
    _setup(db)
    rp = _run(sr.create_restore_point(actor="a", trigger="manual"))

    urls = {"landing": base64.b64encode(b"FAKEPNG").decode(), "login": base64.b64encode(b"FAKEPNG2").decode()}
    payload = json.dumps({"urls": urls, "captured_at": "2026-09-02T12:00:00Z"}).encode()
    sig = h.new(b"test-secret-rollback", payload, hashlib.sha256).hexdigest()
    resp = _run(sr.ingest_visual_state(fake_request(payload, {"x-more-signature": sig})))

    assert resp["ingested"] is True
    assert resp["restore_point_id"] == rp["restore_point"]["id"]
    doc = _run(db.system_restore_points.find_one({"id": rp["restore_point"]["id"]}))
    assert doc["screenshot_item"]["urls"]["landing"] == urls["landing"]
    assert len(doc["screenshot_item"]["urls"]) == 2


def test_visual_state_ingest_rejects_bad_signature():
    db = FakeDB()
    _setup(db)
    payload = json.dumps({"urls": {"landing": "AA=="}}).encode()
    with pytest.raises(HTTPException) as exc:
        _run(sr.ingest_visual_state(fake_request(payload, {"x-more-signature": "bad"})))
    assert exc.value.status_code == 401


# ── 9. Admin endpoints read server truth ───────────────────────────────────
def test_list_restore_points_and_queue():
    db = FakeDB()
    _setup(db)
    _run(sr.create_restore_point(actor="admin", trigger="manual"))
    listing = _run(sr.list_restore_points(fake_request(b"", {"authorization": "Bearer admin"})))
    assert len(listing["restore_points"]) == 1
    assert listing["restore_points"][0]["has_screenshot"] is False
    assert listing["restore_points"][0]["railway_deployment_id"] == "dep-live-001"

    q = _run(sr.webhook_queue(fake_request(b"", {"authorization": "Bearer executive_admin"})))
    assert q["deferred"] == []
    with pytest.raises(HTTPException):
        _run(sr.webhook_queue(fake_request(b"", {"authorization": "Bearer member"})))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "-p", "no:cacheprovider"]))