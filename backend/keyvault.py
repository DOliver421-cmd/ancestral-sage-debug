"""keyvault.py — self-healing Fernet vault for API keys stored at rest.

One shared cipher for every key-encrypting surface on the platform:
BYOK user keys (byok.py), Provider Gateway / billing provider keys
(routers/billing.py), LLM gateway DB-key loading (ai/llm_gateway.py),
and the team monitor health loop (ai/team_monitor.py).

Secret resolution order (first boot needs NO human step):
  1. PROVIDER_KEY_ENCRYPTION_SECRET env var   — explicit config wins
  2. Persisted secret in MongoDB              — platform_config/_id=fernet_secret,
                                                auto-generated once on first boot
  3. Ephemeral in-memory key                  — last resort (no DB); works for
                                                this process lifetime, loud warning

init(db) runs during server startup. get_fernet() is safe anywhere, anytime.
"""
import base64
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.keyvault")

_CONFIG_ID = "fernet_secret"  # document _id inside db.platform_config

_FERNET = None
_SOURCE = "uninitialized"


def _build_fernet(secret: str):
    """Build a Fernet from a secret. Accepts a proper Fernet key directly, or
    deterministically derives one from an arbitrary string (legacy-compatible)."""
    from cryptography.fernet import Fernet
    raw = secret.encode() if isinstance(secret, str) else secret
    try:
        return Fernet(raw)
    except Exception:
        kb = (raw * 3)[:32]
        return Fernet(base64.urlsafe_b64encode(kb))


def source() -> str:
    """Where the active secret came from: env | mongodb | generated | ephemeral | unavailable."""
    return _SOURCE


def get_fernet():
    """The cached vault Fernet, or None if encryption truly cannot be provided."""
    global _FERNET, _SOURCE
    if _FERNET is not None:
        return _FERNET
    # Lazy fallback for paths that run before startup init(): honor the env var.
    env_secret = os.environ.get("PROVIDER_KEY_ENCRYPTION_SECRET", "")
    if env_secret:
        try:
            _FERNET = _build_fernet(env_secret)
            _SOURCE = "env"
        except Exception as e:
            logger.error("keyvault: PROVIDER_KEY_ENCRYPTION_SECRET is unusable: %s", e)
    return _FERNET


async def init(db):
    """Resolve the encryption secret once at startup. Never raises."""
    global _FERNET, _SOURCE
    if get_fernet() is not None:
        return  # env var already resolved

    if db is not None:
        # 2a. Load the previously persisted secret, if any.
        try:
            doc = await db.platform_config.find_one({"_id": _CONFIG_ID})
            if doc and doc.get("value"):
                _FERNET = _build_fernet(doc["value"])
                _SOURCE = "mongodb"
                logger.info("keyvault: loaded persisted encryption secret from MongoDB.")
                return
        except Exception as e:
            logger.warning("keyvault: could not read persisted secret (%s).", e)

        # 2b. First boot with a database: generate once, persist, use forever.
        try:
            from cryptography.fernet import Fernet as _F
            new_key = _F.generate_key().decode()
            await db.platform_config.update_one(
                {"_id": _CONFIG_ID},
                {"$set": {
                    "value": new_key,
                    "auto_generated": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }},
                upsert=True,
            )
            _FERNET = _build_fernet(new_key)
            _SOURCE = "generated"
            logger.info(
                "keyvault: generated and persisted a new encryption secret "
                "(platform_config/%s). No manual configuration needed.", _CONFIG_ID
            )
            return
        except Exception as e:
            logger.warning("keyvault: could not persist generated secret (%s).", e)

    # 3. Last resort: no database. Encrypt for this process lifetime only.
    try:
        from cryptography.fernet import Fernet as _F
        _FERNET = _F(_F.generate_key())
        _SOURCE = "ephemeral"
        logger.warning(
            "keyvault: NO persistent secret available — keys encrypt but will NOT "
            "decrypt after a restart. Set PROVIDER_KEY_ENCRYPTION_SECRET (or give "
            "the app a working MONGO_URL) for durable encryption."
        )
    except Exception as e:
        _FERNET = None
        _SOURCE = "unavailable"
        logger.error("keyvault: cryptography unavailable (%s) — key saves will be refused.", e)
