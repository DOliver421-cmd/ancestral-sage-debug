"""app/database.py — MongoDB client, db, and dependency helpers.

Extracted from backend/server.py lines 95–157.
No logic changed — only moved here so all route modules share one connection.
"""
import os
import logging
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("lcewai")

# These are populated either by this module's own init (when the app module
# is used standalone) or by the backend server.py startup.  Route files
# import `db` and `client` directly from here.

mongo_url = os.environ.get("MONGO_URL", "")
db_name   = os.environ.get("DB_NAME", "ancestral_sage")

if not mongo_url:
    logger.warning("MONGO_URL not set — database disabled")
    client = None
    db     = None
    _DB_SOURCE = "disabled"
else:
    client = AsyncIOMotorClient(
        mongo_url,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
    )
    db         = client[db_name]
    _DB_SOURCE = "primary"

# Backup DB — wired during startup in _on_startup_impl
_backup_db = None

# ── WAI engine singletons ─────────────────────────────────────────────────────
_prt_engine  = None   # PRTEnforcementEngine (lazy)
_the9_engine = None   # The9FusionEngine (lazy)


def _get_prt_engine():
    """Return the shared PRTEnforcementEngine singleton (lazy init)."""
    global _prt_engine
    if _prt_engine is None:
        try:
            from wai_institute.personas.prt.prt_enforcement_engine import PRTEnforcementEngine
            _prt_engine = PRTEnforcementEngine()
        except Exception as _e:
            logger.warning("WAI: PRTEnforcementEngine init failed: %s", _e)
    return _prt_engine


def _get_the9_engine():
    """Return the shared The9FusionEngine singleton (lazy init)."""
    global _the9_engine
    if _the9_engine is None:
        try:
            from wai_institute.core.the9_fusion_engine import The9FusionEngine
            _the9_engine = The9FusionEngine()
        except Exception as _e:
            logger.warning("WAI: The9FusionEngine init failed: %s", _e)
    return _the9_engine


# ── Pipeline / discount managers (set during startup) ─────────────────────────
_pipeline_manager  = None
_discount_manager  = None


# ── FastAPI dependency helpers ────────────────────────────────────────────────
def get_db():
    """FastAPI dependency: yields the primary Motor database."""
    return db


def get_client():
    """FastAPI dependency: yields the primary Motor client."""
    return client
