"""
Find and optionally restore a user account.
Run in Render Shell:

    cd /app/backend
    python3 find_user.py

Lists all non-seeded user accounts and their current state.
Set RESTORE_EMAIL below to reactivate a specific account.
"""
import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

# Set this to reactivate a specific account (leave empty to just list)
RESTORE_EMAIL = ""

# Known seeded/demo accounts — excluded from output
SEEDED = {
    "admin@lcewai.org",
    "instructor@lcewai.org",
    "student@lcewai.org",
    "delon.oliver@lightningcityelectric.com",
    "youpickeddoliver@gmail.com",
}


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    print("=" * 60)
    print("  All registered user accounts")
    print("=" * 60)

    users = await db.users.find(
        {}, {"_id": 0, "password_hash": 0}
    ).sort("created_at", -1).to_list(500)

    real_users = [u for u in users if u.get("email") not in SEEDED]

    if not real_users:
        print("  No registered user accounts found in the database.")
        print("  (The database may have been reset, or no one has registered yet.)")
    else:
        for u in real_users:
            active = u.get("is_active", True)
            print(f"\n  Name:    {u.get('full_name', '—')}")
            print(f"  Email:   {u.get('email', '—')}")
            print(f"  Role:    {u.get('role', '—')}")
            print(f"  Active:  {'YES' if active else 'NO — DEACTIVATED'}")
            print(f"  Created: {str(u.get('created_at', '—'))[:19]}")
            if u.get("must_change_password"):
                print(f"  Note:    must_change_password is set")

    print()
    print(f"  Total real accounts: {len(real_users)}")
    print()

    if RESTORE_EMAIL:
        doc = await db.users.find_one({"email": RESTORE_EMAIL}, {"_id": 0, "password_hash": 0})
        if not doc:
            print(f"[NOT FOUND] {RESTORE_EMAIL} — account does not exist in the database.")
            print("  If the user registered before a database reset, the account is gone.")
            print("  They will need to register again at /register.")
        else:
            update = {"is_active": True, "must_change_password": False}
            await db.users.update_one({"email": RESTORE_EMAIL}, {"$set": update})
            print(f"[RESTORED] {RESTORE_EMAIL} — set active=True, must_change_password=False")
            print(f"  Role: {doc.get('role')} — they can log in with their existing password.")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
