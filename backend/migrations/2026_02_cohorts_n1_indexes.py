"""Migration: add the indexes that support the /admin/cohorts aggregation.

Idempotent.  Safe to run multiple times.

Forward:   python3 migrations/2026_02_cohorts_n1_indexes.py up
Rollback:  python3 migrations/2026_02_cohorts_n1_indexes.py down

Indexes added:
  * progress(status, user_id)  — supports aggregation $match + $lookup
  * users(associate, role)     — supports cohort grouping query
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

PROGRESS_IDX = [("status", 1), ("user_id", 1)]
USERS_IDX = [("associate", 1), ("role", 1)]


async def up():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    name1 = await db.progress.create_index(PROGRESS_IDX)
    name2 = await db.users.create_index(USERS_IDX)
    print(f"[ok] created index on progress: {name1}")
    print(f"[ok] created index on users:    {name2}")
    client.close()


async def down():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    for coll, key in (("progress", PROGRESS_IDX), ("users", USERS_IDX)):
        # build the canonical Mongo index name: "field_1_field_1"
        idx_name = "_".join(f"{f}_{d}" for f, d in key)
        try:
            await db[coll].drop_index(idx_name)
            print(f"[ok] dropped index {coll}.{idx_name}")
        except Exception as e:
            print(f"[skip] {coll}.{idx_name}: {e}")
    client.close()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "up"
    if cmd == "up":
        asyncio.run(up())
    elif cmd == "down":
        asyncio.run(down())
    else:
        print("usage: migration.py [up|down]")
        sys.exit(2)
