"""tests/test_erasure.py — cascading deletion router (GDPR-style erasure).

Exercises routers/users.admin_user_erasure with a fake db: every collection
that references a user id must be purged, missing collections must be reported
(never silently skipped), and the self-erasure + last-executive guards must
hold.  No live server or MongoDB required.

Run:  cd backend && python3 tests/test_erasure.py   (or pytest)
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers import users as _users  # noqa: E402


class _Result:
    def __init__(self, n=0):
        self.deleted_count = n


class _Col:
    """Fake collection: counts delete_many/delete_one calls by user_id."""

    def __init__(self, present=True, doc_count=2):
        self.present = present
        self.deleted = {}
        self.doc_count = doc_count

    async def find_one(self, query, projection=None):
        uid = query.get("id")
        role = "executive_admin" if uid == "exec1" else "student"
        return {"id": uid, "email": "e@x.com", "role": role}

    async def count_documents(self, query):
        return self.doc_count

    async def delete_many(self, query):
        uid = query.get("user_id")
        self.deleted[uid] = self.deleted.get(uid, 0) + 1
        return _Result(1)

    async def delete_one(self, query):
        uid = query.get("id")
        self.deleted[uid] = self.deleted.get(uid, 0) + 1
        return _Result(1)


class _FakeDB:
    def __init__(self, present_cols):
        self.users = _Col()
        self._cols = {c: _Col() for c in present_cols}
        for c in present_cols:
            setattr(self, c, self._cols[c])

    async def find_one(self, query, projection=None):
        uid = query.get("id")
        if uid == "exec1":
            return {"id": uid, "email": "e@x.com", "role": "executive_admin"}
        return {"id": uid, "email": "e@x.com", "role": "student"}

    async def count_documents(self, query):
        return 2  # not the last exec

    async def update_many(self, query, update):
        return _Result(1)


def _run(uid, present_cols, actor_role="admin", actor_id="admin1"):
    db = _FakeDB(present_cols)
    _users.db = db
    async def _noop_audit(*a, **k):
        return None
    _users.audit = _noop_audit
    _users.can_modify = lambda actor, target_role: True  # rank check stubbed
    actor = type("U", (), {"id": actor_id, "role": actor_role})()
    return asyncio.run(_users.admin_user_erasure(uid, actor)), db


def test_erasure_purges_every_referencing_collection():
    cols = ["auth_sessions", "sessions", "user_feature_overrides", "ai_consents",
            "password_reset_tokens", "progress", "notifications", "exec_notifications",
            "audit_log"]
    (res, db) = _run("u1", cols)
    assert res["ok"] is True
    for c in cols:
        assert db._cols[c].deleted.get("u1") == 1, f"{c} not purged"
    assert db.users.deleted.get("u1") == 1
    assert res["purged"]["users"] == 1


def test_erasure_reports_missing_collections_honestly():
    (res, db) = _run("u1", ["auth_sessions"])
    assert res["purged"]["auth_sessions"] == 1
    for c in ["sessions", "progress", "notifications"]:
        assert "skipped" in res["purged"][c], f"{c} should report skipped"


def test_erasure_refuses_self():
    try:
        _run("admin1", ["auth_sessions"], actor_id="admin1")
        raise AssertionError("should have raised 400 for self-erasure")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400


def test_erasure_refuses_last_executive():
    class _OneExecDB(_FakeDB):
        def __init__(self, present_cols):
            super().__init__(present_cols)
            self.users.doc_count = 1  # last exec

    _users.db = _OneExecDB(["auth_sessions"])

    async def _noop_audit(*a, **k):
        return None
    _users.audit = _noop_audit
    _users.can_modify = lambda actor, target_role: True
    actor = type("U", (), {"id": "admin1", "role": "executive_admin"})()
    try:
        asyncio.run(_users.admin_user_erasure("exec1", actor))
        raise AssertionError("should have raised 400 for last exec erasure")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL  {name}: {exc}")
    total = sum(1 for n in globals() if n.startswith("test_") and callable(globals()[n]))
    print(f"\n{total - failures}/{total} passed")
    sys.exit(1 if failures else 0)
