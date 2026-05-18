"""
Emergency password reset for executive admin accounts.
Run from the Render shell or locally with the production MONGO_URL:

    cd /app/backend
    python3 reset_exec_passwords.py

Sets both exec accounts to the passwords below and clears must_change_password
so they land directly on the admin dashboard after login.
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

load_dotenv("/app/backend/.env")

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCOUNTS = [
    {
        "email":     "delon.oliver@lightningcityelectric.com",
        "full_name": "Executive Admin",
        "password":  "LCE_Executive2026!",
    },
    {
        "email":     "youpickeddoliver@gmail.com",
        "full_name": "NAM Oshun",
        "password":  "NamOshun2026!",
    },
]


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    for acct in ACCOUNTS:
        email    = acct["email"]
        new_hash = pwd_ctx.hash(acct["password"])
        existing = await db.users.find_one({"email": email}, {"_id": 0})

        if existing:
            await db.users.update_one(
                {"email": email},
                {"$set": {
                    "role":                "executive_admin",
                    "is_active":           True,
                    "password_hash":       new_hash,
                    "must_change_password": False,
                }},
            )
            print(f"[RESET] {email}  →  password updated, role=executive_admin")
        else:
            await db.users.insert_one({
                "id":                  str(uuid.uuid4()),
                "email":               email,
                "full_name":           acct["full_name"],
                "role":                "executive_admin",
                "associate":           None,
                "is_active":           True,
                "must_change_password": False,
                "created_at":          datetime.now(timezone.utc).isoformat(),
                "password_hash":       new_hash,
            })
            print(f"[CREATED] {email}  →  account created with new password")

        final = await db.users.find_one({"email": email}, {"_id": 0, "password_hash": 0})
        print(f"         State: role={final['role']}  active={final['is_active']}  must_change={final.get('must_change_password')}")
        print()

    client.close()
    print("Done. Log in with the passwords above, then change them in Settings.")


if __name__ == "__main__":
    asyncio.run(main())
