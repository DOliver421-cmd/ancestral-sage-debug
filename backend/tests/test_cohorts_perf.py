"""Pytest: prove /api/admin/cohorts has no N+1.

Uses PyMongo CommandListener to count wire-level commands.  Because
Motor binds its async client to whatever event loop is current at
import time, this test creates a *fresh* AsyncIOMotorClient bound to
its own loop for each test invocation and rebinds `server.db` for the
duration of the test.  Restored on teardown.
"""
import asyncio
import os
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pymongo.monitoring
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DB_NAME = os.environ.get("DB_NAME") or "lcewai"


class _Counter(pymongo.monitoring.CommandListener):
    def __init__(self):
        self.calls: Counter = Counter()
        self.enabled = False

    def started(self, e):
        if not self.enabled:
            return
        if e.database_name != DB_NAME:
            return
        if e.command_name in ("hello", "ismaster", "ping", "buildInfo",
                              "saslStart", "saslContinue"):
            return
        coll = e.command.get(e.command_name)
        key = f"{coll}.{e.command_name}" if isinstance(coll, str) else e.command_name
        self.calls[key] += 1

    def succeeded(self, e): pass
    def failed(self, e): pass


_COUNTER = _Counter()
pymongo.monitoring.register(_COUNTER)

# Import server module *after* registering listener.
import server  # noqa: E402
from server import cohort_summary, User  # noqa: E402

PERF_TAG = "pytest_cohorts_perf"


def _run(coro):
    """Run a coroutine in a fresh event loop with a fresh motor client.

    Motor binds its client to whatever loop it was created on; rebuilding
    the client *inside* the loop guarantees future/loop affinity.
    """
    from motor.motor_asyncio import AsyncIOMotorClient

    async def _wrapper():
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = client[DB_NAME]
        original_db = server.db
        original_client = server.client
        server.db = db
        server.client = client
        try:
            return await coro()
        finally:
            server.db = original_db
            server.client = original_client
            client.close()

    return asyncio.run(_wrapper())


async def _seed(k: int):
    now = datetime.now(timezone.utc).isoformat()
    users, prog = [], []
    for i in range(k):
        assoc = f"PytestAssoc-{i:03d}"
        for j in range(3):
            uid = str(uuid.uuid4())
            users.append({
                "id": uid,
                "email": f"pt-{i}-{j}-{uid[:6]}@example.com",
                "full_name": f"PT {i}.{j}",
                "role": "student",
                "associate": assoc,
                "is_active": True,
                "created_at": now,
                "password_hash": "x",
                "_perf_tag": PERF_TAG,
            })
            for m in range(2):
                prog.append({
                    "id": str(uuid.uuid4()),
                    "user_id": uid,
                    "module_slug": f"pt-mod-{m}",
                    "status": "completed",
                    "_perf_tag": PERF_TAG,
                })
    if users:
        await server.db.users.insert_many(users)
    if prog:
        await server.db.progress.insert_many(prog)


async def _cleanup():
    await server.db.users.delete_many({"_perf_tag": PERF_TAG})
    await server.db.progress.delete_many({"_perf_tag": PERF_TAG})


async def _measure(k: int) -> int:
    await _cleanup()
    await _seed(k)
    admin = User(
        id="pt-admin", email="pt-admin@example.com",
        full_name="PT Admin", role="admin",
    )
    _COUNTER.calls.clear()
    _COUNTER.enabled = True
    try:
        await cohort_summary(user=admin)
    finally:
        _COUNTER.enabled = False
        await _cleanup()
    return sum(_COUNTER.calls.values())


def test_cohorts_endpoint_is_constant_query_count():
    """Pre-fix: 2K+1 wire commands.  Post-fix: 2, regardless of K."""
    async def warm_then_small():
        await server.db.users.count_documents({})  # warm-up
        return await _measure(5)

    n_small = _run(warm_then_small)
    n_large = _run(lambda: _measure(50))

    assert n_small == n_large, (
        f"N+1 regression: K=5 issued {n_small} mongo commands, "
        f"K=50 issued {n_large}"
    )
    assert 1 <= n_small <= 5, f"unexpectedly chatty endpoint: {n_small} commands"


def test_cohorts_returns_correct_completion_counts():
    """Functional: shape + correctness after the fix."""
    async def go():
        await _cleanup()
        await _seed(3)  # 3 associates × 3 students × 2 completions = 6 per cohort
        admin = User(
            id="pt-admin", email="pt-admin@example.com",
            full_name="PT Admin", role="admin",
        )
        result = await cohort_summary(user=admin)
        await _cleanup()
        return result

    result = _run(go)
    perf_rows = [r for r in result if r["associate"].startswith("PytestAssoc-")]
    assert len(perf_rows) == 3, f"expected 3 perf cohorts, got {len(perf_rows)}"
    for row in perf_rows:
        assert row["members"] == 3
        assert row["students"] == 3
        assert row["completions"] == 6, (
            f"cohort {row['associate']} expected 6 completions, "
            f"got {row['completions']}"
        )
