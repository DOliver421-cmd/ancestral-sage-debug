"""
Route-level tests for the Dual-Trigger Visual Rollback System endpoints,
exercised through a real FastAPI app + TestClient with the SAME wiring
server.py uses: router imported, dependencies bound, router mounted at
/api.  These prove the HTTP contract (401 anonymous, 403 non-admin,
200 admin, 401 bad webhook signature) end to end at the framework layer.
"""
import hashlib
import hmac
import os
import sys
from datetime import datetime, timezone

os.environ.setdefault("MORE_ROLLBACK_WEBHOOK_SECRET", "route-test-secret")
os.environ.setdefault("RAILWAY_DEPLOYMENT_ID", "dep-route-1")
os.environ.setdefault("COMMIT_SHA", "sha-route-1")

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import routers.system_rollback as sr
from tests.test_system_rollback import FakeDB, FakeUser, fake_assert_role, fake_audit, fake_notify


async def fake_current_user(authorization=None):
    if not authorization or not str(authorization).startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    return FakeUser(str(authorization).split(" ", 1)[1])


def build_app(db):
    AUDIT = []

    async def _audit(actor, action, target=None, meta=None):
        AUDIT.append({"actor": actor, "action": action, "target": target})

    sr.bind(db, fake_current_user, fake_assert_role, _audit, fake_notify)
    app = FastAPI()
    app.include_router(sr.router, prefix="/api")
    return app, AUDIT


@pytest.fixture(scope="module")
def client():
    db = FakeDB()
    app, audit = build_app(db)
    c = TestClient(app)
    c.app.state.db = db
    c.app.state.audit = audit
    return c


def _sig(payload: bytes) -> str:
    return hmac.new(b"route-test-secret", payload, hashlib.sha256).hexdigest()


def test_health_anonymous_401(client):
    r = client.get("/api/admin/system/health")
    assert r.status_code == 401, r.text


def test_health_admin_ok(client):
    r = client.get("/api/admin/system/health", headers={"authorization": "Bearer admin"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["engine"] == "dual-trigger visual rollback"
    assert body["webhook_secret_configured"] is True
    assert body["rollback_lock_active"] is False


def test_restore_points_admin_flow(client):
    headers = {"authorization": "Bearer executive_admin"}
    created = client.post("/api/admin/system/restore-points", headers=headers)
    assert created.status_code == 200, created.text
    rp = created.json()["restore_point"]
    listing = client.get("/api/admin/system/restore-points", headers=headers)
    assert listing.status_code == 200
    ids = [p["id"] for p in listing.json()["restore_points"]]
    assert rp["id"] in ids
    assert client.get("/api/admin/system/restore-points", headers={}).status_code == 401
    assert client.get("/api/admin/system/restore-points", headers={"authorization": "Bearer member"}).status_code == 403


def test_rollback_requires_confirm_http(client):
    db = client.app.state.db
    sr.bind(db, fake_current_user, fake_assert_role, fake_audit, fake_notify)
    rp = None
    import asyncio
    rp = asyncio.run(sr.create_restore_point(actor="admin", trigger="manual"))
    r = client.post("/api/admin/system/rollback", json={"restore_point_id": rp["restore_point"]["id"], "confirm": False},
                    headers={"authorization": "Bearer admin"})
    assert r.status_code == 400, r.text


def test_emergency_revert_bad_signature_401(client):
    r = client.post("/api/v1/system/emergency-revert", content=b'{"panic":true}',
                    headers={"x-more-signature": "bogus"})
    assert r.status_code == 401, r.text


def test_visual_state_ingest_http(client):
    payload = b'{"urls":{"landing":"Tk9QRQ=="},"captured_at":"2026-09-02T12:00:00Z"}'
    r = client.post("/api/v1/system/visual-state", content=payload,
                    headers={"x-more-signature": _sig(payload)})
    assert r.status_code == 200, r.text
    assert r.json()["ingested"] is True

    r2 = client.post("/api/v1/system/visual-state", content=payload,
                     headers={"x-more-signature": "wrong"})
    assert r2.status_code == 401


def test_emergency_revert_valid_signature_http(client):
    db = client.app.state.db
    calls = []

    async def fake_redeploy(deployment_id):
        calls.append(deployment_id)
        return {"id": deployment_id, "status": "DEPLOYING"}

    sr._railway_redeploy_impl = fake_redeploy
    try:
        payload = b'{"panic":true}'
        r = client.post("/api/v1/system/emergency-revert", content=payload,
                        headers={"x-more-signature": _sig(payload)})
    finally:
        sr._railway_redeploy_impl = None
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["trigger"] == "webhook"
    assert body["deployment_id"] == "dep-route-1"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "-p", "no:cacheprovider"]))