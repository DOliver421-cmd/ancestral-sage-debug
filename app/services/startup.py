"""app/services/startup.py — Startup event handlers and index management.

Extracted from backend/server.py lines 1176–1527.
No logic changed.
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.database import db, client, _get_prt_engine, _get_the9_engine
from app.config import (
    APP_VERSION, MONGO_BACKUP_URL, MONGO_BACKUP_DB, SERVE_FRONTEND,
    ANTHROPIC_API_KEY,
)
from app.security.rate_limit import _RATE

logger = logging.getLogger("lcewai")

ROOT_DIR = Path(__file__).parent.parent.parent / "backend"


async def ensure_indexes():
    """Declare critical indexes. Idempotent; safe to call on every startup."""
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        await db.lab_submissions.create_index([("user_id", 1), ("lab_slug", 1)], unique=True)
        await db.progress.create_index([("user_id", 1), ("module_slug", 1)], unique=True)
        await db.progress.create_index([("status", 1), ("user_id", 1)])
        await db.users.create_index([("associate", 1), ("role", 1)])
        await db.compliance_progress.create_index([("user_id", 1), ("module_slug", 1)], unique=True)
        await db.audit_log.create_index([("at", -1)])
        await db.audit_log.create_index("at", expireAfterSeconds=365 * 24 * 3600)
        await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
        await db.notifications.create_index("created_at", expireAfterSeconds=30 * 24 * 3600)
        await db.user_credentials.create_index([("user_id", 1), ("credential_key", 1)], unique=True)
        await db.attendance.create_index([("user_id", 1), ("date", -1)])
        await db.incidents.create_index([("status", 1), ("created_at", -1)])
        await db.tool_checkouts.create_index([("user_id", 1), ("status", 1)])
        await db.inventory.create_index("sku", unique=True)
        await db.sites.create_index("slug", unique=True)
        await db.password_reset_tokens.create_index("token_hash", unique=True)
        await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
        await db.password_reset_tokens.create_index("user_id")
        await db.recovery_codes.create_index("email", unique=True)
        await db.recovery_codes.create_index("generated_at", expireAfterSeconds=365 * 24 * 3600)
        await db.recovery_log.create_index([("email", 1), ("at", -1)])
        await db.recovery_log.create_index("at", expireAfterSeconds=7 * 365 * 24 * 3600)
        await db.tts_cache.create_index("key", unique=True)
        await db.tts_cache.create_index("created_at", expireAfterSeconds=7 * 24 * 3600)
        await db.tts_usage.create_index([("user_id", 1), ("day", 1)], unique=True)
        await db.tts_usage.create_index("created_at", expireAfterSeconds=25 * 3600)
        await db.mode_decisions.create_index("audit_id", unique=True)
        await db.mode_decisions.create_index("user_id")
        await db.mode_decisions.create_index("created_at", expireAfterSeconds=90 * 24 * 3600)
        await db.chat_history.create_index("expires_at", expireAfterSeconds=0,
                                           partialFilterExpression={"expires_at": {"$exists": True}})
        await db.ai_consents.create_index([("user_id", 1), ("persona", 1), ("created_at", -1)])
        await db.chat_history.create_index([("mode", 1), ("user_id", 1), ("created_at", -1)])
        await db.more_posts.create_index("expires_at", expireAfterSeconds=0,
                                        partialFilterExpression={"expires_at": {"$exists": True}})
        await db.more_posts.create_index("category")
        await db.more_posts.create_index([("created_at", -1)])
        await db.more_needs.create_index("expires_at", expireAfterSeconds=0,
                                        partialFilterExpression={"expires_at": {"$exists": True}})
        await db.more_needs.create_index("status")
        await db.more_needs.create_index([("created_at", -1)])
        await db.more_chats.create_index("expires_at", expireAfterSeconds=0,
                                        partialFilterExpression={"expires_at": {"$exists": True}})
        await db.more_chats.create_index("session_id")
        await db.more_flags.create_index("expires_at", expireAfterSeconds=0,
                                        partialFilterExpression={"expires_at": {"$exists": True}})
        await db.more_flags.create_index("status")
        await db.more_moderation_log.create_index([("created_at", -1)])
        await db.more_moderation_log.create_index("user_id")
        await db.more_moderation_log.create_index("decision")
        await db.more_appeals.create_index("expires_at", expireAfterSeconds=0,
                                          partialFilterExpression={"expires_at": {"$exists": True}})
        await db.more_appeals.create_index("status")
        await db.more_appeals.create_index("user_id")
        await db.user_credentials.create_index("verification_code", unique=True,
                                               sparse=True)
        await db.user_xp.create_index("user_id", unique=True)
        await db.user_xp.create_index([("total_xp", -1)])
        await db.incidents.create_index([("status", 1), ("created_at", 1)])
        logger.info("Indexes ensured")
    except Exception:
        logger.exception("ensure_indexes failed (non-fatal)")


async def run_escalation_check():
    """Scan open incidents and flag any that have been open > 48 hours without update."""
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        stale = await db.incidents.find(
            {"status": "open", "created_at": {"$lt": cutoff}},
            {"_id": 0, "id": 1, "title": 1, "created_by": 1},
        ).to_list(length=100)
        if not stale:
            return
        admin_ids = [
            u["id"] for u in await db.users.find(
                {"role": {"$in": ["admin", "executive_admin"]}, "is_active": {"$ne": False}},
                {"id": 1, "_id": 0},
            ).to_list(20)
        ]
        from app.utils.audit import notify
        for inc in stale:
            for aid in admin_ids:
                await notify(
                    aid,
                    f"Escalation: incident open 48h+ — {inc.get('title', inc['id'])}",
                    f"Incident {inc['id']} has been open for more than 48 hours without resolution.",
                    link="/admin",
                    kind="warning",
                )
        logger.info("Escalation check: flagged %d stale incidents", len(stale))
    except Exception as _e:
        logger.warning("run_escalation_check error: %s", _e)


async def _on_startup_impl(app=None):
    from app.database import _DB_SOURCE
    import app.database as _db_module
    from motor.motor_asyncio import AsyncIOMotorClient

    _db_module._DB_SOURCE = "primary"
    _db_module._backup_db = None

    # Wire shared db reference for sub-routers (social, playlist, etc.)
    import deps as _deps
    _deps.set_db(db)

    if MONGO_BACKUP_URL:
        try:
            _backup_client = AsyncIOMotorClient(
                MONGO_BACKUP_URL, serverSelectionTimeoutMS=8000
            )
            _backup_db_name = MONGO_BACKUP_DB or os.environ.get('DB_NAME', 'wai')
            _db_module._backup_db = _backup_client[_backup_db_name]
            logger.info("STARTUP: Atlas backup DB client initialized (%s).", _backup_db_name)
        except Exception as _bce:
            logger.warning("STARTUP: Could not initialize Atlas backup client: %s", _bce)
    else:
        logger.info("STARTUP: No MONGO_BACKUP_URL set — single-DB mode.")

    try:
        await ensure_indexes()
    except Exception as _e:
        logger.warning("STARTUP: ensure_indexes failed (non-fatal): %s", _e)

    try:
        from partnership import points as _pp_idx
        await _pp_idx.ensure_indexes(db)
        await db["puzzle_progress"].create_index("user_id")
        await db["sovereign_memory"].create_index([("exec_id", 1), ("ts", -1)])
        logger.info("STARTUP: sovereign/partnership/puzzle indexes ensured")
    except Exception as _e:
        logger.warning("STARTUP: sovereign/partnership indexes failed (non-fatal): %s", _e)

    try:
        from app.services.seed import seed_modules
        await seed_modules()
    except Exception as _e:
        logger.warning("STARTUP: seed_modules failed (non-fatal): %s", _e)

    try:
        from app.services.seed import seed_users
        await seed_users()
    except Exception as _e:
        logger.warning("STARTUP: seed_users failed (non-fatal): %s", _e)

    try:
        from app.services.seed import seed_labs
        await seed_labs()
    except Exception as _e:
        logger.warning("STARTUP: seed_labs failed (non-fatal): %s", _e)

    try:
        from app.services.seed import seed_compliance
        await seed_compliance()
    except Exception as _e:
        logger.warning("STARTUP: seed_compliance failed (non-fatal): %s", _e)

    try:
        from app.services.seed import seed_sites_inventory
        await seed_sites_inventory()
    except Exception as _e:
        logger.warning("STARTUP: seed_sites_inventory failed (non-fatal): %s", _e)

    try:
        from app.services.engagement import backfill_verification_codes
        await backfill_verification_codes()
    except Exception as _e:
        logger.warning("STARTUP: backfill_verification_codes failed (non-fatal): %s", _e)

    try:
        await run_escalation_check()
    except Exception as _e:
        logger.warning("STARTUP: run_escalation_check failed (non-fatal): %s", _e)

    try:
        from app.services.engagement import run_engagement_check
        await run_engagement_check()
    except Exception as _e:
        logger.warning("STARTUP: run_engagement_check failed (non-fatal): %s", _e)

    # Revenue Operations System initialization
    try:
        from revenue_operations_integration import (
            init_revenue_operations, init_revenue_services,
            start_revenue_operations,
        )
        await init_revenue_operations(db)
        if app is not None:
            init_revenue_services(app, db)
        logger.info("STARTUP: Revenue operations system initialized")
    except Exception as _rev_err:
        logger.warning("STARTUP: Revenue operations initialization failed (non-fatal): %s", _rev_err)

    try:
        from revenue_operations_integration import start_revenue_operations
        await start_revenue_operations(db)
    except Exception as _sched_err:
        logger.warning("STARTUP: Revenue job scheduler startup failed (non-fatal): %s", _sched_err)

    # WAI-Institute Autonomous Pipeline activation
    try:
        from wai_institute.scripts.system_activation import activate_system, start_scout_scheduler
        _wai_result = await activate_system(db)
        logger.info(
            "WAI autonomous pipeline activated — %d personas bootstrapped",
            _wai_result.get("personas", {}).get("bootstrapped", 0),
        )
        _scout_interval = int(os.environ.get("SCOUT_INTERVAL_HOURS", "6"))
        await start_scout_scheduler(db, interval_hours=_scout_interval)
    except Exception as _wai_err:
        logger.warning("WAI autonomous pipeline startup failed (non-fatal): %s", _wai_err)

    # PipelineManager (LLM intent routing)
    try:
        from src.agents.pipeline_manager import PipelineManager as _PipelineManager
        import app.database as _db_mod2
        _db_mod2._pipeline_manager = _PipelineManager(db=db, anthropic_api_key=ANTHROPIC_API_KEY)
        _mode = "llm" if ANTHROPIC_API_KEY else "keyword_fallback"
        logger.info("STARTUP: PipelineManager ready — analyzer=%s", _mode)
    except Exception as _pm_err:
        logger.warning("STARTUP: PipelineManager init failed (non-fatal): %s", _pm_err)

    # Discount Management System initialization
    try:
        from billing.discount_service import init_discount_service
        import app.database as _db_mod3
        _db_mod3._discount_manager = await init_discount_service(db)
        logger.info("STARTUP: Discount management system initialized")
    except Exception as _disc_err:
        logger.warning("STARTUP: Discount system initialization failed (non-fatal): %s", _disc_err)

    # Rate-limiter memory guard
    async def _rate_limiter_cleanup():
        while True:
            await asyncio.sleep(600)
            now = datetime.now(timezone.utc).timestamp()
            stale = [k for k, v in _RATE.items() if not v or now - v[-1] > 300]
            for k in stale:
                del _RATE[k]
            if stale:
                logger.debug("Rate limiter: pruned %d stale keys.", len(stale))
    asyncio.create_task(_rate_limiter_cleanup())

    # Serve built React frontend (home/backup server only)
    if SERVE_FRONTEND and app is not None:
        _build_paths = [
            ROOT_DIR.parent / "frontend" / "build",
            ROOT_DIR.parent / "frontend" / "dist",
            Path("/app/frontend/build"),
            Path("/app/frontend/dist"),
        ]
        _served = False
        for _bp in _build_paths:
            if _bp.exists() and (_bp / "index.html").exists():
                from fastapi.staticfiles import StaticFiles
                from fastapi.responses import FileResponse

                app.mount("/static", StaticFiles(directory=str(_bp / "static")), name="static")

                @app.get("/{full_path:path}", include_in_schema=False)
                async def _spa_catchall(full_path: str):
                    return FileResponse(str(_bp / "index.html"))

                logger.info("STARTUP: Serving React frontend from %s", _bp)
                _served = True
                break
        if not _served:
            logger.warning(
                "STARTUP: SERVE_FRONTEND=1 but no built frontend found. "
                "Run 'npm run build' in the frontend directory first."
            )

    # Director 4.0 — prompt integrity baseline
    try:
        from ai.prompt_guard import prompt_guard
        results = prompt_guard.startup_integrity_check()
        failed = [k for k, v in results.items() if not v]
        if failed:
            logger.error(
                "STARTUP INTEGRITY WARNING: Prompt baseline enrollment incomplete for: %s. "
                "AI endpoints will use fallback restrictions where applicable.", failed
            )
        else:
            logger.info("STARTUP: All prompt integrity baselines enrolled successfully.")
    except Exception as _pg_exc:
        logger.error("STARTUP: prompt_guard baseline enrollment failed: %s", _pg_exc)

    if os.environ.get("DEV_RETURN_RESET_TOKEN") == "1":
        logger.warning(
            "DEV_RETURN_RESET_TOKEN=1 is set — /api/auth/forgot-password "
            "will return raw reset tokens in the response. THIS IS UNSAFE "
            "FOR PRODUCTION. Remove DEV_RETURN_RESET_TOKEN from .env "
            "before deploying to a public environment."
        )

    # Auto-failover watchdog
    if not os.environ.get("WATCHDOG_DISABLE"):
        try:
            from failover_watchdog import run_watchdog
            asyncio.create_task(run_watchdog(panel_db=db))
            logger.info("STARTUP: Failover watchdog launched (interval=%s, threshold=%s)",
                        os.environ.get("WATCHDOG_CHECK_INTERVAL", "60"),
                        os.environ.get("WATCHDOG_FAILURE_THRESHOLD", "3"))
        except Exception as _wd_err:
            logger.warning("STARTUP: Failover watchdog not available: %s", _wd_err)
    else:
        logger.info("STARTUP: Failover watchdog disabled via WATCHDOG_DISABLE=1")

    # GDPR hard-delete purge (daily)
    async def _gdpr_purge_loop():
        while True:
            await asyncio.sleep(86400)
            try:
                _cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
                _expired = await db.users.find(
                    {"gdpr_deleted_at": {"$ne": None}, "gdpr_grace_until": {"$lte": _cutoff}}
                ).to_list(length=100)
                for _u in _expired:
                    await db.users.delete_one({"id": _u.get("id")})
                if _expired:
                    logger.info("GDPR purge: hard-deleted %d expired accounts.", len(_expired))
            except Exception as _g_err:
                logger.warning("GDPR purge cycle failed: %s", _g_err)
    asyncio.create_task(_gdpr_purge_loop())
    logger.info("STARTUP: GDPR purge cron launched (24h interval)")

    # Memory consolidation cron (daily)
    async def _memory_consolidation_loop():
        while True:
            await asyncio.sleep(86400)
            try:
                from ai.memory import consolidate_all
                await consolidate_all(db)
                logger.info("Memory consolidation cycle complete.")
            except Exception as _m_err:
                logger.warning("Memory consolidation failed: %s", _m_err)
    asyncio.create_task(_memory_consolidation_loop())
    logger.info("STARTUP: Memory consolidation cron launched (24h interval)")

    logger.info(
        "STARTUP COMPLETE — Version: %s | DB: %s | Frontend: %s",
        APP_VERSION, _db_module._DB_SOURCE, "served" if SERVE_FRONTEND else "railway-nginx"
    )
