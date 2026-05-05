"""One-shot idempotent exec-admin bootstrap.

Run on the host where the production MongoDB lives:

    cd /app/backend
    python3 seed_exec_admin.py

Safe to run multiple times. It will:
  * create the exec admin if absent (with seed password + must_change_password=true)
  * upgrade an existing account to executive_admin if it has any other role
  * reactivate the account if it was deactivated
  * leave the password alone if the account already exists
  * print the final state for verification

This script is purely a redundancy / break-glass tool — the same logic runs
automatically on every backend startup inside server.py::seed_users().
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

load_dotenv("/app/backend/.env")

EXEC_EMAIL = "delon.oliver@lightningcityelectric.com"
SEED_PW = "Executive@LCE2026"

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    existing = await db.users.find_one({"email": EXEC_EMAIL}, {"_id": 0})
    if existing:
        update = {}
        if existing.get("role") != "executive_admin":
            update["role"] = "executive_admin"
        if existing.get("is_active") is False:
            update["is_active"] = True
        if update:
            await db.users.update_one({"email": EXEC_EMAIL}, {"$set": update})
            print(f"[ok] Upgraded {EXEC_EMAIL}: {update}")
        else:
            print(f"[ok] {EXEC_EMAIL} already exists with role=executive_admin, active=True")
    else:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": EXEC_EMAIL,
            "full_name": "Executive Admin",
            "role": "executive_admin",
            "associate": None,
            "is_active": True,
            "must_change_password": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "password_hash": pwd_ctx.hash(SEED_PW),
        })
        print(f"[ok] Created {EXEC_EMAIL} with seed password (rotation required on first login)")

    final = await db.users.find_one({"email": EXEC_EMAIL}, {"_id": 0, "password_hash": 0})
    print("Final state:", final)
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
