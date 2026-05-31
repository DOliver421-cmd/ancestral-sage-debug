"""app/routes/system.py — System health, version, and root endpoints.

Extracted from backend/server.py lines 1553–1661.
No logic changed.
"""
import logging

from fastapi import APIRouter

from app.config import APP_VERSION
from app.database import client, db
from app.security.rate_limit import _RATE

logger = logging.getLogger("lcewai")

router = APIRouter()


@router.get("/")
async def root():
    return {"app": "W.A.I. Training Platform", "status": "ok"}


@router.get("/health")
async def health():
    """Deep health check — used by UptimeRobot, home server heartbeat, and Director tool.

    Always returns 200 with a detailed status object.
    Use the top-level `status` field for simple up/down monitoring:
      "operational"  — all systems normal
      "degraded"     — one or more subsystems have issues but service is running
      "critical"     — multiple core systems down

    Non-200 is only returned if the server itself can't respond (handled by infra).
    """
    from datetime import datetime, timezone
    import app.database as _db_module

    now = datetime.now(timezone.utc).isoformat()
    checks: dict = {}
    issues: list[str] = []

    # Database
    try:
        await client.admin.command("ping")
        checks["db"] = {"status": "up", "source": _db_module._DB_SOURCE}
    except Exception as _dbe:
        _db_err_str = str(_dbe)[:120]
        if _db_module._backup_db is not None:
            try:
                await _db_module._backup_db.client.admin.command("ping")
                checks["db"] = {"status": "up(backup)", "source": "atlas-backup",
                                 "primary_error": _db_err_str}
            except Exception as _dbbe:
                checks["db"] = {"status": "down", "source": "both-failed",
                                 "primary_error": _db_err_str, "backup_error": str(_dbbe)[:80]}
                issues.append("db_down")
        else:
            checks["db"] = {"status": "down", "source": _db_module._DB_SOURCE, "error": _db_err_str}
            issues.append("db_down")

    # Anthropic AI API
    from app.config import ANTHROPIC_API_KEY
    if ANTHROPIC_API_KEY:
        checks["ai_api"] = {"status": "configured", "key_present": True}
    else:
        checks["ai_api"] = {"status": "unconfigured", "key_present": False}
        issues.append("ai_api_key_missing")

    # Director 4.0 subsystems
    try:
        from ai.mode_system import mode_system
        checks["mode_system"] = {"status": "up", "current_mode": mode_system.get_mode().value}
    except Exception as _me:
        checks["mode_system"] = {"status": "down", "error": str(_me)[:80]}
        issues.append("mode_system_down")

    try:
        from ai.crisis_engine import crisis_engine
        c = crisis_engine.summary()
        checks["crisis_engine"] = {
            "status": "up",
            "level": c.get("level", "low"),
            "open_incidents": c.get("incident_count", 0),
        }
    except Exception as _ce:
        checks["crisis_engine"] = {"status": "down", "error": str(_ce)[:80]}
        issues.append("crisis_engine_down")

    try:
        from ai.prompt_guard import prompt_guard
        checks["prompt_guard"] = {"status": "up", "patterns": len(getattr(prompt_guard, '_patterns', []))}
    except Exception as _pge:
        checks["prompt_guard"] = {"status": "down", "error": str(_pge)[:80]}
        issues.append("prompt_guard_down")

    try:
        from ai.system_health_monitor import health_monitor
        hm = health_monitor.get_status()
        checks["health_monitor"] = {"status": "up", "health": hm.get("health", "unknown")}
    except Exception as _hme:
        checks["health_monitor"] = {"status": "down", "error": str(_hme)[:80]}

    # Rate limiter
    checks["rate_limiter"] = {"status": "up", "tracked_keys": len(_RATE)}

    # Overall status
    if not issues:
        overall = "operational"
    elif len(issues) >= 2:
        overall = "critical"
    else:
        overall = "degraded"

    return {
        "status":    overall,
        "version":   APP_VERSION,
        "db_source": _db_module._DB_SOURCE,
        "issues":    issues,
        "checks":    checks,
        "timestamp": now,
        "uptime_hint": "Monitor at /api/health — returns 200 always; check `status` field.",
    }


@router.get("/version")
async def version():
    return {"version": APP_VERSION, "name": "W.A.I. Training Platform"}
