"""
Direct MongoDB exec account reset — runs without the server.

Usage:
    python reset_exec_accounts.py

Requires MONGO_URL and DB_NAME in your .env or environment.
Clears lockouts and resets all 3 exec seats to their default passwords.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

load_dotenv(Path(__file__).parent / "backend" / ".env")
load_dotenv(Path(__file__).parent / ".env")

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME   = os.environ.get("DB_NAME")

if not MONGO_URL or not DB_NAME:
    print("ERROR: MONGO_URL and DB_NAME must be set in environment or .env")
    raise SystemExit(1)

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

EXEC_SEATS = [
    ("delon.oliver@lightningcityelectric.com", "Executive@LCE2026",  "Delon Oliver"),
    ("youpickeddoliver@gmail.com",             "NamOshun@WAI2026",   "Delon Oliver"),
    ("souppoetry@gmail.com",                   "NamOshun@WAI2026",   "NAM Oshun"),
]


async def main():
    client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=8000)
    db = client[DB_NAME]

    try:
        await db.command("ping")
        print(f"Connected to MongoDB: {DB_NAME}")
    except Exception as e:
        print(f"ERROR: Cannot connect to MongoDB: {e}")
        raise SystemExit(1)

    for email, password, name in EXEC_SEATS:
        existing = await db.users.find_one({"email": email})
        if existing:
            result = await db.users.update_one(
                {"email": email},
                {
                    "$set": {
                        "password_hash": pwd_ctx.hash(password),
                        "role": "executive_admin",
                        "is_active": True,
                        "must_change_password": False,
                    },
                    "$unset": {
                        "login_locked_until": "",
                        "login_failed_attempts": "",
                    },
                }
            )
            status = "RESET" if result.modified_count else "no change"
        else:
            await db.users.insert_one({
                "id": str(__import__("uuid").uuid4()),
                "email": email,
                "full_name": name,
                "role": "executive_admin",
                "password_hash": pwd_ctx.hash(password),
                "is_active": True,
                "must_change_password": False,
                "created_at": __import__("datetime").datetime.utcnow().isoformat(),
            })
            status = "CREATED"

        print(f"  {status}: {email}  →  password: {password}")

    client.close()
    print("\nDone. You can now log in with the passwords shown above.")


if __name__ == "__main__":
    asyncio.run(main())
