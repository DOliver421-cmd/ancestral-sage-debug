"""app/routes/system.py — System health, version, and root endpoints."""
import logging
import time

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
    """Deep health check — always returns 200; callers inspect `status` field.

    status values:
      "operational" — all core systems normal
      "degraded"    — one non-critical subsystem unavailable
      "critical"    — two or more issues or a core system is down
    """
    from datetime import datetime, timezone
    import app.database as _db_module
    from app.config import GROQ_API_KEY, CEREBRAS_API_KEY, MISTRAL_API_KEY, STRIPE_SECRET_KEY

    now = datetime.now(timezone.utc).isoformat()
    checks: dict = {}
    issues: list[str] = []

    # ── Primary DB with latency ───────────────────────────────────────────────
    _t0 = time.perf_counter()
    try:
        await client.admin.command("ping")
        _db_ms = int((time.perf_counter() - _t0) * 1000)
        checks["db"] = {"status": "up", "source": _db_module._DB_SOURCE, "latency_ms": _db_ms}
    except Exception as _dbe:
        _db_err_str = str(_dbe)[:120]
        # Try backup DB
        if _db_module._backup_db is not None:
            _t1 = time.perf_counter()
            try:
                await _db_module._backup_db.client.admin.command("ping")
                _bk_ms = int((time.perf_counter() - _t1) * 1000)
                checks["db"] = {
                    "status": "up(backup)", "source": "atlas-backup",
                    "latency_ms": _bk_ms, "primary_error": _db_err_str,
                }
                # Emit DB failover alert (fire-and-forget)
                try:
                    import asyncio as _asyncio
                    from app.utils.alerting import alert_db_failover
                    _asyncio.create_task(alert_db_failover(_db_err_str))
                except Exception:
                    pass
            except Exception as _dbbe:
                checks["db"] = {
                    "status": "down", "source": "both-failed",
                    "primary_error": _db_err_str, "backup_error": str(_dbbe)[:80],
                }
                issues.append("db_down")
        else:
            checks["db"] = {"status": "down", "source": _db_module._DB_SOURCE, "error": _db_err_str}
            issues.append("db_down")

    # ── Backup DB latency (independent check when primary is healthy) ─────────
    if _db_module._backup_db is not None and checks.get("db", {}).get("status") == "up":
        _t2 = time.perf_counter()
        try:
            await _db_module._backup_db.client.admin.command("ping")
            checks["db_backup"] = {"status": "up", "latency_ms": int((time.perf_counter() - _t2) * 1000)}
        except Exception as _bke:
            checks["db_backup"] = {"status": "down", "error": str(_bke)[:80]}

    # ── Rate limiter ──────────────────────────────────────────────────────────
    try:
        # Verify MongoDB rate counter collection is reachable when db is up
        if db is not None:
            _t3 = time.perf_counter()
            await db.rate_limit_counters.find_one({})
            checks["rate_limiter"] = {
                "status": "up",
                "tracked_keys": len(_RATE),
                "latency_ms": int((time.perf_counter() - _t3) * 1000),
            }
        else:
            checks["rate_limiter"] = {"status": "local_only", "tracked_keys": len(_RATE)}
    except Exception as _rle:
        checks["rate_limiter"] = {"status": "local_only", "tracked_keys": len(_RATE), "error": str(_rle)[:80]}

    # ── AI provider reachability ──────────────────────────────────────────────
    _ai_configured = bool(GROQ_API_KEY or CEREBRAS_API_KEY or MISTRAL_API_KEY)
    if _ai_configured:
        checks["ai_api"] = {"status": "configured", "key_present": True}
    else:
        checks["ai_api"] = {"status": "unconfigured", "key_present": False}
        issues.append("ai_api_key_missing")

    # ── Stripe connectivity ───────────────────────────────────────────────────
    if STRIPE_SECRET_KEY:
        _t4 = time.perf_counter()
        try:
            import stripe as _stripe
            _stripe.api_key = STRIPE_SECRET_KEY
            _stripe.Balance.retrieve()
            checks["stripe"] = {"status": "up", "latency_ms": int((time.perf_counter() - _t4) * 1000)}
        except Exception as _se:
            _se_str = str(_se)[:120]
            checks["stripe"] = {"status": "error", "error": _se_str}
            issues.append("stripe_error")
    else:
        checks["stripe"] = {"status": "unconfigured"}

    # ── Director 4.0 subsystems ───────────────────────────────────────────────
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
        checks["prompt_guard"] = {"status": "up", "patterns": len(getattr(prompt_guard, "_patterns", []))}
    except Exception as _pge:
        checks["prompt_guard"] = {"status": "down", "error": str(_pge)[:80]}
        issues.append("prompt_guard_down")

    try:
        from ai.system_health_monitor import health_monitor
        hm = health_monitor.get_status()
        checks["health_monitor"] = {"status": "up", "health": hm.get("health", "unknown")}
    except Exception as _hme:
        checks["health_monitor"] = {"status": "down", "error": str(_hme)[:80]}

    # ── Overall status ────────────────────────────────────────────────────────
    if not issues:
        overall = "operational"
    elif "db_down" in issues or len(issues) >= 2:
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


@router.get("/routes/debug")
async def routes_debug():
    """Lists which optional route modules failed to load at startup."""
    try:
        from app.main import _failed_routes, _loaded_routers
        return {
            "loaded": list(_loaded_routers.keys()),
            "failed": list(_failed_routes),
        }
    except Exception as e:
        return {"error": str(e)}
