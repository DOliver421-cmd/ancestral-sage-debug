#!/usr/bin/env python3
"""
ONE-TIME Executive Admin Bootstrap Script

This script creates an initial executive_admin account.
It should ONLY be run once on first production deployment.

USAGE:
    export MONGO_URL="your_production_mongo_url"
    export DB_NAME="wai_institute"
    python -m backend.scripts.bootstrap_exec_admin

DO NOT run this script more than once. It creates a .bootstrap.lock file to prevent re-running.
"""
import asyncio
import os
import sys
import uuid
import secrets
from pathlib import Path
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
LOCK_FILE = Path("./.bootstrap.lock")


async def main():
    # Verify lock file doesn't exist
    if LOCK_FILE.exists():
        print("❌ ERROR: Bootstrap has already been run (lock file exists).")
        print("   If you need to reset, contact your database administrator.")
        sys.exit(1)

    # Get MongoDB connection
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")

    if not mongo_url or not db_name:
        print("❌ ERROR: MONGO_URL and DB_NAME environment variables required")
        sys.exit(1)

    print("🔐 WAI-Institute Executive Admin Bootstrap")
    print("=" * 60)
    print()

    # Get exec email
    exec_email = input("Enter executive admin email: ").strip()
    if not exec_email or "@" not in exec_email:
        print("❌ Invalid email address")
        sys.exit(1)

    # Generate temporary password
    temp_password = secrets.token_urlsafe(16)

    # Connect to MongoDB
    try:
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        db = client[db_name]

        # Verify connection
        await db.command("ping")
        print(f"✅ Connected to MongoDB: {db_name}")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        sys.exit(1)

    # Check if account already exists
    try:
        existing = await db.users.find_one({"email": exec_email})
        if existing:
            print(f"❌ Account already exists for {exec_email}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        sys.exit(1)

    # Create executive account
    try:
        account = {
            "id": str(uuid.uuid4()),
            "email": exec_email,
            "full_name": "Executive Admin",
            "password_hash": pwd_ctx.hash(temp_password),
            "role": "executive_admin",
            "is_active": True,
            "must_change_password": True,  # Force password change on first login
            "associate": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        result = await db.users.insert_one(account)
        print(f"✅ Executive admin account created: {exec_email}")
        print()

        # Display credentials
        print("🔐 TEMPORARY CREDENTIALS (SAVE THESE)")
        print("=" * 60)
        print(f"Email:    {exec_email}")
        print(f"Password: {temp_password}")
        print()
        print("⚠️  IMPORTANT:")
        print("   1. Save these credentials in a secure location")
        print("   2. Log in immediately after deployment")
        print("   3. Change your password on first login")
        print("   4. Generate recovery codes for account recovery")
        print("   5. See EMERGENCY_ACCESS_RECOVERY.md for full recovery procedures")
        print()

        # Create lock file
        LOCK_FILE.touch()
        print("✅ Bootstrap complete. Lock file created to prevent re-running.")
        print()
        print("📚 See EMERGENCY_ACCESS_RECOVERY.md for access recovery procedures")
        print("📚 See LOCKED_OUT_QUICK_FIX.txt for instant access if needed")

    except Exception as e:
        print(f"❌ Account creation failed: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
