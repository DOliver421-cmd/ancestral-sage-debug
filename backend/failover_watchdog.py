"""
failover_watchdog.py — auto-failover health poller.

Background asyncio task that:
  1. Pings the primary API health endpoint every CHECK_INTERVAL seconds
  2. After FAILURE_THRESHOLD consecutive failures, triggers failover
     to the next available tier (primary → backup → emergency)
  3. Falls back to the standalone emergency UI if no backup is configured
  4. Logs every state transition for the breaker panel

This is a proof-of-concept watchdog — it assumes the system exists at
the same base URL. In production, a separate monitoring process would
perform health checks from outside the server.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone

import httpx

logger = logging.getLogger("failover_watchdog")

CHECK_INTERVAL = int(os.environ.get("WATCHDOG_CHECK_INTERVAL", "60"))       # seconds
FAILURE_THRESHOLD = int(os.environ.get("WATCHDOG_FAILURE_THRESHOLD", "3"))  # consecutive failures
PRIMARY_URL = os.environ.get("WATCHDOG_PRIMARY_URL", "http://localhost:8000")
BACKUP_URL = os.environ.get("BACKUP_ORIGIN", "")  # optional home server

_HEALTH_PATH = "/api/health"


async def _check_health(base_url: str, timeout: float = 15.0) -> bool:
    """Return True if the health endpoint at base_url responds 200."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(f"{base_url.rstrip('/')}{_HEALTH_PATH}")
        return r.is_success
    except Exception as exc:
        logger.debug("Health check failed for %s: %s", base_url, exc)
        return False


async def run_watchdog(panel_db=None):
    """
    Main watchdog loop.  Runs forever, checking primary health.

    If panel_db (a Motor MongoDB database) is provided, the watchdog will
    also update breaker panel state on failover.  Without it, only logging
    occurs — useful for testing.
    """
    from emergency_panel import failover, get_panel, get_system_health

    consecutive_failures = 0
    current_tier = "primary"
    logger.info(
        "Watchdog started — interval=%ds, threshold=%d, primary=%s",
        CHECK_INTERVAL, FAILURE_THRESHOLD, PRIMARY_URL,
    )

    while True:
        await asyncio.sleep(CHECK_INTERVAL)

        primary_ok = await _check_health(PRIMARY_URL)
        if primary_ok:
            if consecutive_failures > 0:
                logger.info("Watchdog: primary recovered after %d failures", consecutive_failures)
            consecutive_failures = 0
            # If we were on a backup tier and primary recovered, switch back
            if current_tier != "primary" and panel_db is not None:
                try:
                    result = await failover(panel_db, "primary", reason="Watchdog: primary recovered")
                    logger.info("Watchdog: auto-restore to primary — %s", result)
                    current_tier = "primary"
                except Exception as exc:
                    logger.warning("Watchdog: auto-restore failed: %s", exc)
            continue

        consecutive_failures += 1
        logger.warning(
            "Watchdog: primary unhealthy (%d/%d failures)",
            consecutive_failures, FAILURE_THRESHOLD,
        )

        if consecutive_failures < FAILURE_THRESHOLD:
            continue

        # Threshold reached — attempt failover
        consecutive_failures = 0

        if panel_db is None:
            logger.warning("Watchdog: failover triggered (no db — logging only)")
            continue

        try:
            health = await get_system_health(panel_db)
            current_tier = health.get("active_origin", "primary")
        except Exception:
            current_tier = "primary"

        next_tier = "backup" if BACKUP_URL else "emergency"
        if current_tier == "backup":
            next_tier = "emergency"
        elif current_tier == "emergency":
            logger.warning("Watchdog: already on emergency — no further tier. Manual intervention required.")
            continue

        # Quick check: is the next tier reachable?
        test_url = BACKUP_URL if next_tier == "backup" else PRIMARY_URL  # emergency is served by same process
        tier_ok = await _check_health(test_url)
        if not tier_ok and next_tier == "backup":
            logger.warning("Watchdog: backup unreachable, falling through to emergency")
            next_tier = "emergency"

        try:
            result = await failover(panel_db, next_tier, reason=f"Watchdog: {FAILURE_THRESHOLD}x consecutive health failure")
            logger.info("Watchdog: failover complete — %s", result)
            current_tier = next_tier
        except Exception as exc:
            logger.error("Watchdog: failover failed: %s", exc)
