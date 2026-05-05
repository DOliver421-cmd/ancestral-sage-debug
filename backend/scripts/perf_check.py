"""Performance proof for the /api/admin/cohorts N+1 fix.

Uses PyMongo's CommandListener to count *every* MongoDB wire command
issued during a call to `cohort_summary()` — bulletproof against any
Motor/proxy weirdness because it intercepts at the driver level.

Acceptance: total wire commands at K=5 cohorts must equal those at
K=50 cohorts (i.e. O(1), independent of cohort count).

Run:  cd /app/backend && python3 scripts/perf_check.py
"""
import asyncio
import os
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
import pymongo.monitoring
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

PERF_TAG = "perf_check"
DB_NAME = os.environ["DB_NAME"]


class CommandCounter(pymongo.monitoring.CommandListener):
    """Counts only commands hitting the app DB, ignoring system noise."""

    def __init__(self):
        self.calls = Counter()
        self.enabled = False

    def started(self, event):
        if not self.enabled:
            return
        if event.database_name != DB_NAME:
            return
        # Skip the meta-commands the driver issues every connection.
        if event.command_name in ("hello", "ismaster", "ping", "buildInfo",
                                  "saslStart", "saslContinue"):
            return
        coll = event.command.get(event.command_name)
        if isinstance(coll, str):
            self.calls[f"{coll}.{event.command_name}"] += 1
        else:
            self.calls[event.command_name] += 1

    def succeeded(self, event):
        pass

    def failed(self, event):
        pass


_counter = CommandCounter()
pymongo.monitoring.register(_counter)

# Import server *after* registering the listener so its client picks it up.
import server  # noqa: E402
from server import cohort_summary, User  # noqa: E402


async def _seed(k: int):
    now = datetime.now(timezone.utc).isoformat()
    users, prog = [], []
    for i in range(k):
        assoc = f"PerfAssoc-{i:03d}"
        for j in range(3):
            uid = str(uuid.uuid4())
            users.append({
                "id": uid,
                "email": f"perf-{i}-{j}-{uid[:6]}@example.com",
                "full_name": f"Perf {i}.{j}",
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
                    "module_slug": f"perf-mod-{m}",
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


async def _measure(k: int, label: str):
    await _cleanup()
    await _seed(k)
    admin = User(
        id="perf-admin", email="perf-admin@example.com",
        full_name="Perf Admin", role="admin",
    )
    _counter.calls.clear()
    _counter.enabled = True
    t0 = time.perf_counter()
    result = await cohort_summary(user=admin)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    _counter.enabled = False
    breakdown = dict(_counter.calls)
    total = sum(breakdown.values())
    print(f"[{label:<8}] K={k:<3} cohorts | mongo_cmds={total:<3} | "
          f"elapsed={elapsed_ms:6.1f} ms | cohorts_returned={len(result)}")
    print(f"           breakdown: {breakdown}")
    return total


async def main():
    # Warm up the connection so meta-commands aren't measured.
    await server.db.users.count_documents({})

    print("=== /api/admin/cohorts — N+1 proof (PyMongo command monitoring) ===")
    n1 = await _measure(5, "k=5")
    n2 = await _measure(20, "k=20")
    n3 = await _measure(50, "k=50")
    await _cleanup()

    print()
    print(f"calls@k=5  : {n1}")
    print(f"calls@k=20 : {n2}")
    print(f"calls@k=50 : {n3}")
    print()
    if n1 == n2 == n3 and n1 > 0:
        print(f"PASS - query count is constant ({n1}) regardless of K. No N+1.")
        return 0
    if n1 < n2 < n3:
        print("FAIL - query count grows with K (N+1 still present).")
        return 1
    print(f"INDETERMINATE - n1={n1} n2={n2} n3={n3}")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
