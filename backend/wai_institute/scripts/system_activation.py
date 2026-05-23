"""
WAI-Institute System Activation
==================================
Called once on backend startup to bootstrap the full autonomous system.

What it does:
  1. Bootstraps all 7 core personas in db.persona_activations
  2. Ensures MongoDB indexes for pipeline collections
  3. Registers the background cultural scout scheduler
  4. Logs system activation to db.system_events

Safe to call on every startup — all operations are idempotent.
"""

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.system_activation")

# ── Startup entry point ───────────────────────────────────────────────────────

async def activate_system(db) -> dict:
    """
    Full system activation. Call from FastAPI on_startup.
    Returns activation summary dict.
    """
    started = datetime.now(timezone.utc)
    results = {}

    # ── 1. Bootstrap personas ─────────────────────────────────────────────────
    try:
        from wai_institute.core.persona_manager import PersonaManager
        pm = PersonaManager(db)
        results["personas"] = await pm.bootstrap_core_personas(activated_by="system_startup")
    except Exception as e:
        logger.warning("system_activation: persona bootstrap failed — %s", e)
        results["personas"] = {"error": str(e)}

    # ── 1b. Bootstrap PRT + The 9 ─────────────────────────────────────────────
    try:
        from wai_institute.core.persona_manager import PersonaManager, PERSONA_TIERS, REPORTING_LINES
        pm = PersonaManager(db)
        for pname, scope, mode in [
            ("poor_righteous_teacher", ["internal_ops", "cultural_enforcement", "the9_activation"], "active"),
            ("the_9",                  ["internal_ops", "unified_execution", "campaign_synthesis"],  "active"),
        ]:
            existing = await db.persona_activations.find_one({"persona": pname}) if db is not None else None
            if not existing:
                await pm.activate(
                    name=pname,
                    config={
                        "source":        "system_activation",
                        "bootstrapped":  True,
                        "authority_model": "ESDAL_v4",
                    },
                    mode=mode,
                    scope=scope,
                    activated_by="system_startup",
                )
                logger.info("system_activation: bootstrapped %s", pname)
        results["prt_the9"] = {"bootstrapped": True}
    except Exception as e:
        logger.warning("system_activation: PRT/The 9 bootstrap failed (non-fatal): %s", e)
        results["prt_the9"] = {"error": str(e)}

    # ── 2. Ensure pipeline indexes ────────────────────────────────────────────
    try:
        results["indexes"] = await _ensure_pipeline_indexes(db)
    except Exception as e:
        logger.warning("system_activation: index creation failed — %s", e)
        results["indexes"] = {"error": str(e)}

    # ── 3. Log activation event ───────────────────────────────────────────────
    try:
        await db.system_events.insert_one({
            "event":      "system_activation",
            "results":    results,
            "timestamp":  started.isoformat(),
        })
    except Exception as e:
        logger.warning("system_activation: event log failed — %s", e)

    duration = (datetime.now(timezone.utc) - started).total_seconds()
    logger.info(
        "WAI-Institute system activated in %.2fs — personas: %s",
        duration,
        results.get("personas", {}).get("bootstrapped", 0),
    )

    return {
        "status":       "activated",
        "duration_secs": round(duration, 3),
        "timestamp":    started.isoformat(),
        **results,
    }


async def _ensure_pipeline_indexes(db) -> dict:
    """
    Create indexes for all autonomous pipeline collections.
    Idempotent — safe to run on every startup.
    """
    indexes_created = []

    index_plan = [
        # Scout leads
        ("scout_leads",       [("source_id", 1)],    {"unique": True, "sparse": True}),
        ("scout_leads",       [("matched", 1)],       {}),
        ("scout_leads",       [("score", -1)],        {}),
        ("scout_leads",       [("created_at", -1)],   {}),
        # Scout campaigns
        ("scout_campaigns",   [("converted", 1)],     {}),
        ("scout_campaigns",   [("created_at", -1)],   {}),
        # Audio assets
        ("audio_asset_meta",  [("asset_id", 1)],      {"unique": True}),
        ("audio_asset_meta",  [("persona", 1)],       {}),
        # Merch products
        ("merch_products",    [("status", 1)],        {}),
        ("merch_products",    [("product_type", 1)],  {}),
        # Checkout links
        ("checkout_links",    [("converted", 1)],     {}),
        ("checkout_links",    [("campaign_id", 1)],   {}),
        # Persona activations
        ("persona_activations", [("persona", 1)],     {"unique": True}),
        ("persona_activations", [("status", 1)],      {}),
        # Governance log
        ("governance_log",    [("action", 1)],        {}),
        ("governance_log",    [("timestamp", -1)],    {}),
        # Staff meetings
        ("staff_meetings",    [("meeting_id", 1)],    {"unique": True}),
        ("staff_meetings",    [("convened_at", -1)],  {}),
        ("staff_meetings",    [("priority", 1)],      {}),
        # PRT enforcement log
        ("prt_enforcement_log", [("sender", 1)],      {}),
        ("prt_enforcement_log", [("timestamp", -1)],  {}),
        # The 9 activation log
        ("the9_activations",  [("activated_by", 1)],  {}),
        ("the9_activations",  [("timestamp", -1)],    {}),
    ]

    for collection, keys, kwargs in index_plan:
        try:
            col = getattr(db, collection)
            await col.create_index(keys, **kwargs)
            indexes_created.append(f"{collection}.{'+'.join(k for k, _ in keys)}")
        except Exception as e:
            # Index may already exist — not a critical error
            logger.debug("Index create for %s: %s", collection, e)

    return {"indexes_created": len(indexes_created), "collections": indexes_created[:10]}


# ── Background Scout Scheduler ────────────────────────────────────────────────

_scout_task = None

async def start_scout_scheduler(db, interval_hours: int = 6) -> None:
    """
    Start the background cultural scout scan loop.
    Runs every `interval_hours` hours autonomously.

    Called from FastAPI startup after DB is ready.
    """
    global _scout_task

    if _scout_task and not _scout_task.done():
        logger.info("Scout scheduler already running")
        return

    _scout_task = asyncio.create_task(
        _scout_loop(db, interval_hours=interval_hours)
    )
    logger.info("Cultural Scout scheduler started — interval: %dh", interval_hours)


async def _scout_loop(db, interval_hours: int = 6) -> None:
    """
    Perpetual background loop: scan → match → log.
    Runs inside the FastAPI event loop.
    """
    import os
    # Scout is OFF by default. Set SCOUT_ENABLED=true in Railway Variables to enable.
    if os.environ.get("SCOUT_ENABLED", "false").lower() != "true":
        logger.info("Cultural Scout disabled (set SCOUT_ENABLED=true to enable)")
        return

    interval_secs = interval_hours * 3600

    # Wait 5 minutes before the first scan so startup seeding and health checks
    # complete cleanly before the scout adds HTTP load to the event loop.
    _initial_delay = int(os.environ.get("SCOUT_INITIAL_DELAY_SECS", "300"))
    if _initial_delay > 0:
        logger.info("CulturalScout: waiting %ds before first scan (SCOUT_INITIAL_DELAY_SECS)", _initial_delay)
        await asyncio.sleep(_initial_delay)

    while True:
        try:
            logger.info("CulturalScout: starting scheduled scan...")
            from wai_institute.pipelines.cultural_scout import CulturalScout
            from wai_institute.pipelines.contextual_matcher import ContextualMatcher

            scout   = CulturalScout(db)
            matcher = ContextualMatcher(db)

            # 1. Scan all platforms
            scan_result = await scout.run_full_scan(max_leads_per_source=15)
            logger.info("Scout scan: %d leads found", scan_result["leads_found"]["total"])

            # 2. Match unmatched leads
            unmatched = await scout.get_unmatched_leads(limit=30)
            if unmatched:
                match_results = await matcher.match_batch(unmatched)
                matched_count = sum(1 for r in match_results if r.get("matched"))
                logger.info("Scout match: %d/%d leads matched", matched_count, len(unmatched))

        except asyncio.CancelledError:
            logger.info("Scout scheduler cancelled")
            break
        except Exception as e:
            logger.warning("Scout loop error: %s", e)

        # Wait for next interval
        await asyncio.sleep(interval_secs)


def stop_scout_scheduler() -> None:
    """Cancel the background scout task (called on shutdown)."""
    global _scout_task
    if _scout_task and not _scout_task.done():
        _scout_task.cancel()
        logger.info("Scout scheduler stopped")
