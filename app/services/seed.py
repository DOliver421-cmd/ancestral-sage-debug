"""app/services/seed.py — Database seeding functions.

Extracted from backend/server.py lines 869–1551.
No logic changed.
"""
import logging
import uuid
from datetime import datetime, timezone

from app.database import db
from app.config import (
    EXEC_ADMIN_EMAIL, EXEC_DEFAULT_PASSWORD,
    BACKUP_EXEC_EMAIL, BACKUP_EXEC_DEFAULT_PASSWORD,
    NAM_EXEC_EMAIL, NAM_EXEC_DEFAULT_PASSWORD,
    PLATFORM_NOTIFY_EMAIL, EXEC_FORCE_RESET,
)

logger = logging.getLogger("lcewai")


async def seed_modules():
    from seed import MODULES, quiz_for
    for m in MODULES:
        existing = await db.modules.find_one({"slug": m["slug"]})
        doc = {**m, "quiz": quiz_for(m["slug"])}
        if existing:
            await db.modules.update_one({"slug": m["slug"]}, {"$set": doc})
        else:
            doc["id"] = str(uuid.uuid4())
            await db.modules.insert_one(doc)
    logger.info("Seeded %d modules", len(MODULES))


async def seed_users():
    from app.security.passwords import hash_pw, _send_via_gmail
    from recovery import ensure_recovery_codes_exist
    import os
    import secrets as _secrets

    # One-time migration: cohort → associate for any legacy users
    await db.users.update_many(
        {"cohort": {"$exists": True}, "associate": {"$in": [None, ""]}},
        [{"$set": {"associate": "$cohort"}}, {"$unset": "cohort"}],
    )
    # Normalize legacy "Cohort-*" values to "Associate-*"
    legacy_users = await db.users.find({"associate": {"$regex": "^Cohort-"}}, {"_id": 0}).to_list(1000)
    for u in legacy_users:
        new_val = u["associate"].replace("Cohort-", "Associate-", 1)
        await db.users.update_one({"id": u["id"]}, {"$set": {"associate": new_val}})
    # Demo accounts removed — platform is live. Delete any that still exist in DB.
    _demo_emails = ["admin@lcewai.org", "instructor@lcewai.org", "student@lcewai.org"]
    result = await db.users.delete_many({"email": {"$in": _demo_emails}})
    if result.deleted_count:
        logger.info("Removed %d demo account(s) from live database", result.deleted_count)

    def _gen_pw() -> str:
        """Generate a 20-char cryptographically random password."""
        alpha = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789!@#$%^&*"
        return "".join(_secrets.choice(alpha) for _ in range(20))

    async def _email_new_pw(email: str, name: str, pw: str) -> None:
        """Send auto-generated password to PLATFORM_NOTIFY_EMAIL via Gmail SMTP."""
        subject = f"WAI-Institute: New exec account created — {email}"
        html = (
            f"<p>A new executive account was bootstrapped at startup.</p>"
            f"<p><b>Account:</b> {email} ({name})<br>"
            f"<b>Temporary password:</b> <code>{pw}</code></p>"
            f"<p>Log in and change this password immediately. "
            f"The account has <code>must_change_password=True</code>.</p>"
        )
        try:
            await _send_via_gmail(PLATFORM_NOTIFY_EMAIL, subject, html)
            logger.info("STARTUP: auto-generated password emailed to %s for account %s",
                        PLATFORM_NOTIFY_EMAIL, email)
        except Exception as _em:
            logger.warning(
                "STARTUP: email failed for %s — TEMP PASSWORD (change immediately): %s | error: %s",
                email, pw, _em,
            )

    _exec_seats = [
        (EXEC_ADMIN_EMAIL,  "Delon Oliver",  EXEC_DEFAULT_PASSWORD),
        (BACKUP_EXEC_EMAIL, "Delon Oliver",  BACKUP_EXEC_DEFAULT_PASSWORD),
        (NAM_EXEC_EMAIL,    "NAM Oshun",     NAM_EXEC_DEFAULT_PASSWORD),
    ]
    for _email, _name, _env_pw in _exec_seats:
        try:
            existing = await db.users.find_one({"email": _email})
            if not existing:
                _pw = _env_pw if _env_pw else _gen_pw()
                _auto_generated = not bool(_env_pw)
                await db.users.insert_one({
                    "id": str(uuid.uuid4()),
                    "email": _email,
                    "full_name": _name,
                    "role": "executive_admin",
                    "password_hash": hash_pw(_pw),
                    "is_active": True,
                    "must_change_password": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                logger.info("STARTUP: exec seat created — %s (auto_pw=%s)", _email, _auto_generated)
                if _auto_generated:
                    await _email_new_pw(_email, _name, _pw)
            else:
                await db.users.update_one(
                    {"email": _email},
                    {
                        "$set": {"role": "executive_admin", "is_active": True},
                        "$unset": {"login_locked_until": "", "login_failed_attempts": ""},
                    },
                )
        except Exception as _e:
            logger.warning("STARTUP: exec seat bootstrap failed for %s: %s", _email, _e)

    try:
        if EXEC_FORCE_RESET:
            force_reset_email = os.environ.get("EXEC_FORCE_RESET_EMAIL", "").strip()
            force_reset_password = os.environ.get("EXEC_FORCE_RESET_PASSWORD", "").strip()

            if force_reset_email and force_reset_password:
                user_doc = await db.users.find_one({"email": force_reset_email}, {"_id": 0})
                if user_doc:
                    await db.users.update_one(
                        {"email": force_reset_email},
                        {"$set": {
                            "password_hash": hash_pw(force_reset_password),
                            "must_change_password": True,
                            "is_active": True,
                            "force_reset_at": datetime.now(timezone.utc).isoformat(),
                        },
                        "$unset": {"login_locked_until": "", "login_failed_attempts": ""}},
                    )
                    logger.warning("EXEC_FORCE_RESET (Mode B): password reset for %s", force_reset_email)
                    from app.utils.audit import audit
                    await audit(None, "exec.force_reset.completed", target=force_reset_email,
                                meta={"reason": "EXEC_FORCE_RESET flag set"})
                else:
                    logger.error("EXEC_FORCE_RESET: email not found: %s", force_reset_email)
            else:
                logger.warning("EXEC_FORCE_RESET (Mode A): resetting all exec seats to default passwords")
                _reset_seats = [
                    (EXEC_ADMIN_EMAIL,  EXEC_DEFAULT_PASSWORD),
                    (BACKUP_EXEC_EMAIL, BACKUP_EXEC_DEFAULT_PASSWORD),
                    (NAM_EXEC_EMAIL,    NAM_EXEC_DEFAULT_PASSWORD),
                ]
                for _r_email, _r_pw in _reset_seats:
                    await db.users.update_one(
                        {"email": _r_email},
                        {"$set": {
                            "password_hash": hash_pw(_r_pw),
                            "must_change_password": False,
                            "is_active": True,
                            "force_reset_at": datetime.now(timezone.utc).isoformat(),
                        },
                        "$unset": {"login_locked_until": "", "login_failed_attempts": ""}},
                        upsert=False,
                    )
                    logger.warning("EXEC_FORCE_RESET (Mode A): reset %s to default", _r_email)
                from app.utils.audit import audit
                await audit(None, "exec.force_reset.all_seats", meta={"reason": "EXEC_FORCE_RESET=1, no email specified"})
    except Exception as _exc:
        logger.error("EXEC_FORCE_RESET failed: %s", _exc)

    try:
        all_execs = await db.users.find({"role": "executive_admin"}, {"email": 1}).to_list(100)
        exec_emails = [e["email"] for e in all_execs if e.get("email")]
        if exec_emails:
            await ensure_recovery_codes_exist(db, exec_emails)
            logger.info("Initialized recovery codes for %d executive account(s)", len(exec_emails))
    except Exception as _exc_recovery:
        logger.error("Recovery codes initialization failed (non-fatal): %s", _exc_recovery)


async def seed_labs():
    from seed_labs import ONLINE_LABS, IN_PERSON_LABS
    for spec in ONLINE_LABS:
        doc = {**spec, "track": "online"}
        existing = await db.labs.find_one({"slug": doc["slug"]})
        if existing:
            await db.labs.update_one({"slug": doc["slug"]}, {"$set": doc})
        else:
            doc["id"] = str(uuid.uuid4())
            await db.labs.insert_one(doc)
    for spec in IN_PERSON_LABS:
        doc = {**spec, "track": "inperson"}
        existing = await db.labs.find_one({"slug": doc["slug"]})
        if existing:
            await db.labs.update_one({"slug": doc["slug"]}, {"$set": doc})
        else:
            doc["id"] = str(uuid.uuid4())
            await db.labs.insert_one(doc)


async def seed_compliance():
    from seed_compliance import COMPLIANCE_MODULES, COMPLIANCE_QUIZZES
    for spec in COMPLIANCE_MODULES:
        doc = {**spec, "quiz": COMPLIANCE_QUIZZES.get(spec["slug"], [])}
        existing = await db.compliance_modules.find_one({"slug": doc["slug"]})
        if existing:
            await db.compliance_modules.update_one({"slug": doc["slug"]}, {"$set": doc})
        else:
            doc["id"] = str(uuid.uuid4())
            await db.compliance_modules.insert_one(doc)


async def seed_sites_inventory():
    from seed_inventory import SITES, INVENTORY
    for s in SITES:
        if not await db.sites.find_one({"slug": s["slug"]}):
            await db.sites.insert_one({**s, "id": str(uuid.uuid4())})
    for it in INVENTORY:
        if not await db.inventory.find_one({"sku": it["sku"]}):
            await db.inventory.insert_one({
                **it,
                "id": str(uuid.uuid4()),
                "quantity_available": it["quantity_total"],
            })
