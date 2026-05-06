"""Regression test for the seed_users() role-drift auto-heal.

Bug: in production, admin@lcewai.org had been manually demoted to
"instructor" at some point.  The original seed_users() only inserted
new accounts; it did not correct role drift.  Fix: mirror the exec
admin bootstrap pattern — on every startup, if a seeded demo account
exists with the wrong role or is_active=False, heal it.

This test:
  1. demote admin@lcewai.org to "instructor" + deactivate it
  2. run seed_users()
  3. assert role == "admin" and is_active is True
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server  # noqa: E402


def _run(coro_factory):
    async def wrapper():
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = client[os.environ.get("DB_NAME", "lcewai")]
        original_db, original_client = server.db, server.client
        server.db, server.client = db, client
        try:
            return await coro_factory()
        finally:
            server.db, server.client = original_db, original_client
            client.close()
    return asyncio.run(wrapper())


def test_seed_heals_role_drift_on_admin():
    """Promote/demote then re-seed; admin must be back to role=admin."""
    async def go():
        # Snapshot the original state so we don't break other tests.
        before = await server.db.users.find_one(
            {"email": "admin@lcewai.org"}, {"_id": 0}
        )
        if before is None:
            pytest.skip("admin@lcewai.org not seeded yet")
        # Inject the production-style drift.
        await server.db.users.update_one(
            {"email": "admin@lcewai.org"},
            {"$set": {"role": "instructor", "is_active": False}},
        )
        # Run the seed → it must heal both fields.
        await server.seed_users()
        after = await server.db.users.find_one(
            {"email": "admin@lcewai.org"}, {"_id": 0}
        )
        assert after["role"] == "admin", (
            f"seed_users() did not heal role drift: still {after['role']}"
        )
        assert after["is_active"] is True, (
            "seed_users() did not reactivate deactivated demo account"
        )
        # Restore the prior state (whatever it was) for hygiene.
        await server.db.users.update_one(
            {"email": "admin@lcewai.org"},
            {"$set": {
                "role": before.get("role", "admin"),
                "is_active": before.get("is_active", True),
            }},
        )

    _run(go)


def test_seed_does_not_reset_password_on_existing_account():
    """Drift-heal must NOT touch the password — only role/is_active.
    A user who has rotated their password must keep it."""
    async def go():
        before = await server.db.users.find_one(
            {"email": "instructor@lcewai.org"}, {"_id": 0}
        )
        if before is None:
            pytest.skip("instructor@lcewai.org not seeded yet")
        # Set a known custom password hash.
        custom_hash = server.hash_pw("UserChose@NewPw1")
        await server.db.users.update_one(
            {"email": "instructor@lcewai.org"},
            {"$set": {"password_hash": custom_hash, "role": "student"}},
        )
        await server.seed_users()
        after = await server.db.users.find_one(
            {"email": "instructor@lcewai.org"}, {"_id": 0}
        )
        # Role is healed.
        assert after["role"] == "instructor"
        # Password is preserved.
        assert after["password_hash"] == custom_hash, (
            "seed_users() unexpectedly mutated password_hash"
        )
        # Restore.
        await server.db.users.update_one(
            {"email": "instructor@lcewai.org"},
            {"$set": {
                "password_hash": before["password_hash"],
                "role": before.get("role", "instructor"),
            }},
        )

    _run(go)
