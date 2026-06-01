"""Emergency access recovery system for executive accounts.

Three layers of recovery:
1. IMMEDIATE: EXEC_FORCE_RESET=1 in Railway (temporary, one-time use)
2. PERMANENT: Recovery codes (stored securely, can be used multiple times)
3. BACKUP: Secondary executive email accounts (youpickeddoliver@gmail.com, souppoetry@gmail.com)
"""
import os
import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Recovery Code Storage ────────────────────────────────────────────────────
# Recovery codes are hashed before storage (never store plaintext).
# Generate 4 codes per executive account, each usable only once.
# Format: YYYY-XXXX-XXXX-XXXX (easy to type, hard to guess)

async def generate_recovery_codes(db: AsyncIOMotorDatabase, email: str) -> list[str]:
    """Generate 4 new recovery codes for an executive account.

    Returns: List of 4 plaintext codes (show to user once, never again)
    """
    codes = []
    hashed_codes = []

    for _ in range(4):
        # Generate code: YYYY-XXXX-XXXX-XXXX (32 bits entropy per code = 128 bits total)
        code = f"{secrets.randbelow(10000):04d}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
        codes.append(code)

        # Hash before storage (so database breach doesn't expose codes)
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        hashed_codes.append({
            "code_hash": code_hash,
            "used": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    # Store in recovery_codes collection
    await db.recovery_codes.update_one(
        {"email": email},
        {
            "$set": {
                "email": email,
                "codes": hashed_codes,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        upsert=True
    )

    return codes


async def verify_recovery_code(db: AsyncIOMotorDatabase, email: str, code: str) -> bool:
    """Verify and consume a recovery code.

    Returns: True if code is valid and unused, False otherwise.
    Side effect: Marks code as used (cannot be reused).
    """
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    result = await db.recovery_codes.find_one_and_update(
        {
            "email": email,
            "codes": {
                "$elemMatch": {
                    "code_hash": code_hash,
                    "used": False
                }
            }
        },
        {
            "$set": {
                "codes.$[elem].used": True,
                "codes.$[elem].used_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        array_filters=[{"elem.code_hash": code_hash}],
    )

    return result is not None


async def get_recovery_code_status(db: AsyncIOMotorDatabase, email: str) -> dict:
    """Check how many recovery codes are left for an account."""
    doc = await db.recovery_codes.find_one({"email": email})
    if not doc:
        return {
            "email": email,
            "total_codes": 0,
            "used_codes": 0,
            "remaining_codes": 0,
            "generated_at": None,
        }

    codes = doc.get("codes", [])
    used = sum(1 for c in codes if c.get("used"))

    return {
        "email": email,
        "total_codes": len(codes),
        "used_codes": used,
        "remaining_codes": len(codes) - used,
        "generated_at": doc.get("generated_at"),
    }


async def emergency_password_reset(
    db: AsyncIOMotorDatabase,
    email: str,
    new_password: str,
    reason: str = "executive_recovery"
) -> bool:
    """Emergency password reset for executive account.

    Used by recovery endpoints. Logs the action for audit trail.
    """
    password_hash = pwd_ctx.hash(new_password)

    result = await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "password_hash": password_hash,
                "must_change_password": True,
                "last_recovery_reset": datetime.now(timezone.utc).isoformat(),
                "recovery_reason": reason,
            }
        }
    )

    # Log recovery action
    if result.modified_count > 0:
        await db.recovery_log.insert_one({
            "email": email,
            "action": "password_reset",
            "reason": reason,
            "at": datetime.now(timezone.utc).isoformat(),
        })

    return result.modified_count > 0


async def ensure_recovery_codes_exist(db: AsyncIOMotorDatabase, emails: list[str]):
    """Ensure every executive account has recovery codes on startup."""
    for email in emails:
        status = await get_recovery_code_status(db, email)
        if status["remaining_codes"] == 0:
            codes = await generate_recovery_codes(db, email)
            # Log that codes were generated
            await db.recovery_log.insert_one({
                "email": email,
                "action": "codes_generated",
                "reason": "startup",
                "at": datetime.now(timezone.utc).isoformat(),
            })
