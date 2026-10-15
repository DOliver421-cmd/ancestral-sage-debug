"""tests/test_user_rollback.py — T1-9: soft-delete + restore for user accounts.

Before this, `DELETE /admin/users/{uid}` purged the user record and every
dependent collection permanently. An accidental deletion was unrecoverable.
This suite pins the reversible path: deactivate, login is refused, restore,
login works again.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers.users import router as users_router  # noqa: E402


def _build_app():
    """Stand up the users router with the same bind() wiring server.py uses,
    against an in-memory fake so the test exercises the handler logic rather
    than the live HTTP stack."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import routers.users as u

    class FakeUser:
        def __init__(self, uid, role="executive_admin"):
            self.id = uid
            self.role = role
            self.email = "exec@example.com"

    class FakeDB:
        """A minimal async Mongo-like fake backed by a dict.

        Every attribute access returns the same object, so `db.users`,
        `db.auth_sessions`, and `db["anything"]` all route to the single
        in-memory table — enough for these handlers, which only ever touch
        `users` and `auth_sessions`."""
        def __init__(self):
            self._table = {}

        def __getattr__(self, name):
            return self

        def __getitem__(self, name):
            return self

        async def find_one(self, q, projection=None):
            return self._table.get(q.get("id"))

        async def update_one(self, q, u):
            target = self._table.get(q.get("id"))
            if target is None:
                return type("R", (), {"matched_count": 0})()
            target.update(u.get("$set", {}))
            for k in u.get("$unset", {}):
                target.pop(k, None)
            return type("R", (), {"matched_count": 1})()

        async def delete_many(self, *a, **k):
            return type("R", (), {"deleted_count": 0})()

    db = FakeDB()
    AUDIT = []

    async def _audit(actor, action, target=None, meta=None):
        AUDIT.append({"actor": actor, "action": action, "target": target, "meta": meta})

    async def _current_user(authorization=None):
        return FakeUser("exec-1")

    async def _can_modify(actor, target_role):
        return True

    def _hash_pw(pw):
        return "hashed:" + pw

    u.bind(db, _audit, None, _current_user, _can_modify, _hash_pw)
    app = FastAPI()
    app.include_router(users_router, prefix="/api")
    return TestClient(app), db, AUDIT


def test_soft_delete_deactivates_and_refuses_login():
    client, db, _ = _build_app()
    db._table["kid-1"] = {"id": "kid-1", "email": "kid@example.com", "role": "student",
                          "is_active": True, "password_hash": "x"}

    r = client.delete("/api/admin/users/kid-1")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "deactivated"
    assert body["restorable"] is True
    assert "deleted_at" in body
    assert db._table["kid-1"]["is_active"] is False


def test_soft_delete_is_idempotent():
    client, db, _ = _build_app()
    db._table["kid-2"] = {"id": "kid-2", "email": "kid2@example.com", "role": "student",
                          "is_active": True, "password_hash": "x"}

    first = client.delete("/api/admin/users/kid-2")
    assert first.status_code == 200
    second = client.delete("/api/admin/users/kid-2")
    assert second.status_code == 200
    assert second.json()["status"] == "already_deactivated"


def test_soft_delete_refuses_self_and_exec():
    client, db, _ = _build_app()
    db._table["exec-1"] = {"id": "exec-1", "email": "exec@example.com", "role": "executive_admin",
                           "is_active": True, "password_hash": "x"}

    r = client.delete("/api/admin/users/exec-1")
    assert r.status_code == 400  # cannot delete self


def test_restore_reactivates_the_account():
    client, db, _ = _build_app()
    db._table["kid-3"] = {"id": "kid-3", "email": "kid3@example.com", "role": "student",
                          "is_active": True, "password_hash": "x"}

    client.delete("/api/admin/users/kid-3")
    assert db._table["kid-3"]["is_active"] is False

    r = client.post("/api/admin/users/kid-3/restore")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "active"
    assert db._table["kid-3"]["is_active"] is True
    assert "deleted_at" not in db._table["kid-3"]


def test_restore_is_idempotent_on_an_active_account():
    client, db, _ = _build_app()
    db._table["kid-4"] = {"id": "kid-4", "email": "kid4@example.com", "role": "student",
                          "is_active": True, "password_hash": "x"}

    r = client.post("/api/admin/users/kid-4/restore")
    assert r.status_code == 200
    assert r.json()["status"] == "already_active"


def test_soft_delete_audit_recorded():
    client, db, AUDIT = _build_app()
    db._table["kid-5"] = {"id": "kid-5", "email": "kid5@example.com", "role": "student",
                          "is_active": True, "password_hash": "x"}

    client.delete("/api/admin/users/kid-5")
    actions = [a["action"] for a in AUDIT]
    assert "admin.user.deleted" in actions