"""
Emergency Breaker Panel — state tracking for multi-layer redundancy.

Each "breaker" represents a system component and its status (on/off/standby/
tripped/fault). The "gateway" records the desired active origin, but actual
traffic routing depends on infrastructure-level DNS / reverse proxy config.

This module is a control-plane only: it records intent and exposes toggle/
reset/failover/heartbeat endpoints for manual or watchdog-driven operation.

Tiers (documented — actual failover requires the failover_watchdog or manual
invocation of the /api/exec/failover endpoint):
  1. PRIMARY   — Railway (production API + React SPA)
  2. BACKUP    — Home server via Cloudflare Tunnel (requires deploy/ config)
  3. EMERGENCY — Standalone HTML UI (served at /emergency)

Database:
  - Primary MongoDB (MONGO_URL)
  - Backup MongoDB Atlas (MONGO_BACKUP_URL) — used in /api/health
"""

import os
import logging
from datetime import datetime, timezone
from typing import Literal, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger("emergency_panel")

BREAKER_ID = Literal[
    "primary_api", "backup_api", "emergency_ui",
    "database_primary", "database_backup",
    "ai_services", "email_service", "stripe_payments", "scheduler_jobs",
]
BREAKER_STATUS = Literal["on", "off", "standby", "tripped", "fault"]

DEFAULT_BREAKERS = {
    "primary_api":      {"label": "Primary API (Railway)",       "status": "on",      "type": "main",     "order": 0},
    "backup_api":       {"label": "Backup Server (Home)",        "status": "standby",  "type": "backup",   "order": 1},
    "emergency_ui":     {"label": "Emergency UI (Standalone)",   "status": "standby",  "type": "backup",   "order": 2},
    "database_primary": {"label": "MongoDB Primary",             "status": "on",       "type": "database", "order": 3},
    "database_backup":  {"label": "MongoDB Atlas (Backup)",      "status": "standby",  "type": "database", "order": 4},
    "ai_services":      {"label": "AI Services (Anthropic/OAI)", "status": "on",       "type": "service",  "order": 5},
    "email_service":    {"label": "Email (Resend/Gmail)",        "status": "on",       "type": "service",  "order": 6},
    "stripe_payments":  {"label": "Stripe Payments",             "status": "on",       "type": "service",  "order": 7},
    "scheduler_jobs":   {"label": "Scheduled Jobs",              "status": "off",      "type": "service",  "order": 8},
}


async def get_panel(db: AsyncIOMotorDatabase) -> dict:
    """Read breaker panel state from DB, initializing defaults if missing."""
    doc = await db.system_config.find_one({"_id": "emergency_panel"})
    if doc is None:
        doc = {
            "_id": "emergency_panel",
            "breakers": dict(DEFAULT_BREAKERS),
            "gateway": {
                "active_origin": "primary",
                "auto_failover": True,
                "last_failover": None,
                "last_failover_reason": None,
                "backup_last_seen": None,
                "backup_version": None,
                "emergency_last_seen": None,
            },
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.system_config.insert_one(doc)
    else:
        # Ensure all default breakers exist (add any new ones)
        changed = False
        for bid, bcfg in DEFAULT_BREAKERS.items():
            if bid not in doc.get("breakers", {}):
                doc["breakers"][bid] = bcfg
                changed = True
        if changed:
            await db.system_config.update_one(
                {"_id": "emergency_panel"},
                {"$set": {"breakers": doc["breakers"]}}
            )
    return doc


async def save_panel(db: AsyncIOMotorDatabase, panel: dict):
    """Persist panel state to DB."""
    panel["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.system_config.replace_one({"_id": "emergency_panel"}, panel, upsert=True)


async def toggle_breaker(db: AsyncIOMotorDatabase, breaker_id: str) -> dict:
    """Toggle a breaker: on→off, off→on, standby→on, tripped→reset→standby, fault→standby."""
    panel = await get_panel(db)
    breaker = panel["breakers"].get(breaker_id)
    if breaker is None:
        return {"ok": False, "error": f"Unknown breaker: {breaker_id}"}

    cycle = {"on": "off", "off": "on", "standby": "on", "tripped": "standby", "fault": "standby"}
    breaker["status"] = cycle.get(breaker["status"], "standby")
    await save_panel(db, panel)
    logger.info("Breaker toggled: %s → %s", breaker_id, breaker["status"])
    return {"ok": True, "breaker_id": breaker_id, "status": breaker["status"]}


async def reset_breaker(db: AsyncIOMotorDatabase, breaker_id: str) -> dict:
    """Reset a tripped/faulted breaker back to its default state."""
    panel = await get_panel(db)
    breaker = panel["breakers"].get(breaker_id)
    if breaker is None:
        return {"ok": False, "error": f"Unknown breaker: {breaker_id}"}
    default = DEFAULT_BREAKERS.get(breaker_id, {})
    breaker["status"] = default.get("status", "standby")
    await save_panel(db, panel)
    logger.info("Breaker reset: %s → %s", breaker_id, breaker["status"])
    return {"ok": True, "breaker_id": breaker_id, "status": breaker["status"]}


async def failover(db: AsyncIOMotorDatabase, target: str, reason: Optional[str] = None) -> dict:
    """Perform gateway failover to a specific origin tier."""
    valid = {"primary", "backup", "emergency"}
    if target not in valid:
        return {"ok": False, "error": f"Invalid target: {target}. Choose from {valid}"}

    panel = await get_panel(db)
    old = panel["gateway"]["active_origin"]
    panel["gateway"]["active_origin"] = target
    panel["gateway"]["last_failover"] = datetime.now(timezone.utc).isoformat()
    panel["gateway"]["last_failover_reason"] = reason or f"Manual failover: {old} → {target}"

    # Auto-toggle breakers to match
    if target == "primary":
        panel["breakers"]["primary_api"]["status"] = "on"
        panel["breakers"]["backup_api"]["status"] = "standby"
        panel["breakers"]["emergency_ui"]["status"] = "standby"
    elif target == "backup":
        panel["breakers"]["primary_api"]["status"] = "standby"
        panel["breakers"]["backup_api"]["status"] = "on"
        panel["breakers"]["emergency_ui"]["status"] = "standby"
    elif target == "emergency":
        panel["breakers"]["primary_api"]["status"] = "standby"
        panel["breakers"]["backup_api"]["status"] = "standby"
        panel["breakers"]["emergency_ui"]["status"] = "on"

    await save_panel(db, panel)
    logger.info("Failover: %s → %s (%s)", old, target, reason or "manual")
    return {"ok": True, "previous": old, "active": target, "reason": panel["gateway"]["last_failover_reason"]}


async def heartbeat(db: AsyncIOMotorDatabase, source: str, version: Optional[str] = None) -> dict:
    """Receive heartbeat from backup/emergency systems."""
    panel = await get_panel(db)
    now = datetime.now(timezone.utc).isoformat()
    if source == "backup":
        panel["gateway"]["backup_last_seen"] = now
        panel["gateway"]["backup_version"] = version
        panel["breakers"]["backup_api"]["status"] = "on"
    elif source == "emergency":
        panel["gateway"]["emergency_last_seen"] = now
        panel["breakers"]["emergency_ui"]["status"] = "on"
    else:
        return {"ok": False, "error": f"Unknown source: {source}"}
    await save_panel(db, panel)
    return {"ok": True, "source": source, "recorded_at": now}


async def get_system_health(db: AsyncIOMotorDatabase) -> dict:
    """Get a live health summary of all systems for the panel."""
    panel = await get_panel(db)
    breakers = panel["breakers"]
    gateway = panel["gateway"]

    online_breakers = sum(1 for b in breakers.values() if b["status"] == "on")
    total_breakers = len(breakers)
    tripped = [k for k, v in breakers.items() if v["status"] in ("tripped", "fault")]

    return {
        "online": online_breakers,
        "total": total_breakers,
        "health_pct": round((online_breakers / total_breakers) * 100) if total_breakers else 0,
        "active_origin": gateway["active_origin"],
        "tripped_breakers": tripped,
        "auto_failover": gateway["auto_failover"],
        "backup_alive": gateway.get("backup_last_seen") is not None,
        "last_failover": gateway.get("last_failover"),
    }
