"""app/services/team_monitor.py — Team-owned infrastructure monitor.

This service runs autonomously in the background. It monitors provider health,
detects failures, and takes corrective action within its operational scope.

All actions are attributed to the team (actor: "team.supervisor") — not to any
human administrator. Delon receives FYI notifications when action is taken.
He does not approve or initiate these actions.

The action log is the proof of autonomous operation.

Check interval: every 5 minutes.
Failure threshold: 3 consecutive failures before action is taken.
"""
import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.team_monitor")

MONITOR_INTERVAL_SEC = 300        # 5 minutes between health cycles
FAILURE_THRESHOLD    = 3          # consecutive failures before action
AUTH_FAIL_THRESHOLD  = 1          # auth failures are immediate (401 = bad key, no retry)

# In-process failure tracking (resets on restart — intentional, transient issues clear)
_failure_counts: dict = {}        # key: provider_type, value: int
_last_action_at: dict = {}        # key: action_type, value: timestamp
_degraded: set  = set()           # provider_types currently marked degraded


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def log_team_action(action: str, reason: str, outcome: str, meta: dict = None) -> None:
    """Write a team action record. actor is always team.supervisor."""
    from app.database import db
    try:
        await db.team_actions.insert_one({
            "id": str(uuid.uuid4()),
            "actor": "team.supervisor",
            "action": action,
            "reason": reason,
            "outcome": outcome,
            "meta": meta or {},
            "human_initiated": False,
            "at": _now(),
        })
    except Exception as e:
        logger.warning("team_monitor: failed to write action log: %s", e)


async def _notify_delon(title: str, body: str) -> None:
    """FYI notification to the executive — not a request for approval."""
    from app.database import db
    from app.utils.audit import notify
    try:
        execs = await db.users.find(
            {"role": "executive_admin", "is_active": {"$ne": False}},
            {"id": 1}
        ).to_list(10)
        for ex in execs:
            await notify(ex["id"], title, body, kind="info")
    except Exception as e:
        logger.warning("team_monitor: notify_delon failed: %s", e)


async def _test_provider_key(provider_type: str, raw_key: str) -> tuple[bool, str | None]:
    """
    Run a lightweight connectivity test for a provider key.
    Returns (ok, error_type) where error_type is "auth" | "connectivity" | None.
    """
    import httpx
    try:
        async with httpx.AsyncClient(timeout=6) as c:
            if provider_type == "groq":
                r = await c.get("https://api.groq.com/openai/v1/models",
                                headers={"Authorization": f"Bearer {raw_key}"})
            elif provider_type == "cerebras":
                r = await c.get("https://api.cerebras.ai/v1/models",
                                headers={"Authorization": f"Bearer {raw_key}"})
            elif provider_type == "gemini":
                r = await c.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={raw_key}")
            elif provider_type == "mistral":
                r = await c.get("https://api.mistral.ai/v1/models",
                                headers={"Authorization": f"Bearer {raw_key}"})
            elif provider_type == "cohere":
                r = await c.get("https://api.cohere.com/v1/models",
                                headers={"Authorization": f"Bearer {raw_key}"})
            elif provider_type == "together":
                r = await c.get("https://api.together.xyz/v1/models",
                                headers={"Authorization": f"Bearer {raw_key}"})
            elif provider_type in ("xai", "grok"):
                r = await c.get("https://api.x.ai/v1/models",
                                headers={"Authorization": f"Bearer {raw_key}"})
            elif provider_type == "openrouter":
                r = await c.get("https://openrouter.ai/api/v1/models",
                                headers={"Authorization": f"Bearer {raw_key}"})
            elif provider_type == "sambanova":
                r = await c.get("https://api.sambanova.ai/v1/models",
                                headers={"Authorization": f"Bearer {raw_key}"})
            else:
                return True, None  # unknown — assume ok, don't block

            if r.status_code in (401, 403):
                return False, "auth"
            if r.status_code == 429:
                return False, "rate_limit"
            if r.status_code >= 500:
                return False, "connectivity"
            return True, None
    except Exception as e:
        return False, "connectivity"


async def _run_health_cycle() -> None:
    """One full health check pass across all active provider keys."""
    from app.database import db

    import os, base64
    enc_secret = os.environ.get("PROVIDER_KEY_ENCRYPTION_SECRET", "")
    fernet = None
    if enc_secret:
        try:
            from cryptography.fernet import Fernet
            kb = (enc_secret.encode() * 3)[:32]
            fernet = Fernet(base64.urlsafe_b64encode(kb))
        except Exception:
            pass

    try:
        keys = await db.api_keys.find({"status": "active"}).to_list(50)
    except Exception as e:
        logger.warning("team_monitor: DB read failed: %s", e)
        return

    if not keys:
        return

    # Build provider_type map
    provider_ids = list({k.get("provider_id") for k in keys if k.get("provider_id")})
    providers = {}
    try:
        async for p in db.api_providers.find({"id": {"$in": provider_ids}}):
            providers[p["id"]] = p.get("provider_type", p.get("type", "")).lower()
    except Exception:
        pass

    any_action_taken = False

    for key_doc in keys:
        pid     = key_doc.get("provider_id", "")
        pt      = providers.get(pid, "unknown")
        key_id  = key_doc.get("id", "")
        label   = key_doc.get("label", pt)

        # Decrypt key
        encrypted = key_doc.get("encrypted_key", "")
        if not encrypted:
            continue
        try:
            raw_key = fernet.decrypt(encrypted.encode()).decode() if fernet else encrypted
        except Exception:
            raw_key = encrypted  # may be plaintext if no encryption secret

        if not raw_key:
            continue

        ok, error_type = await _test_provider_key(pt, raw_key)

        if ok:
            if pt in _degraded:
                _degraded.discard(pt)
                _failure_counts[pt] = 0
                logger.info("team_monitor: %s recovered", pt)
                await log_team_action(
                    action=f"provider.recovery.{pt}",
                    reason=f"{pt} passed health check after previous failures",
                    outcome="provider restored to active rotation",
                    meta={"provider_type": pt, "key_id": key_id},
                )
            else:
                _failure_counts[pt] = 0
            continue

        # Failure path
        _failure_counts[pt] = _failure_counts.get(pt, 0) + 1
        count = _failure_counts[pt]

        if error_type == "auth" and count >= AUTH_FAIL_THRESHOLD:
            # Bad key — revoke immediately
            logger.warning("team_monitor: %s key auth failed — revoking", pt)
            try:
                await db.api_keys.update_one(
                    {"id": key_id},
                    {"$set": {"status": "revoked", "revoked_at": _now(),
                              "revoked_by": "team.supervisor"}},
                )
            except Exception:
                pass

            await log_team_action(
                action=f"key.revoked.{pt}",
                reason=f"{label} returned auth failure (401/403) — key is invalid",
                outcome="key revoked; gateway will use next available provider",
                meta={"provider_type": pt, "key_id": key_id, "error": error_type},
            )
            any_action_taken = True
            _failure_counts[pt] = 0

            # Reload gateway so this key is no longer used
            try:
                from ai.llm_gateway import reload_provider_keys
                await reload_provider_keys(db)
            except Exception:
                pass

        elif error_type in ("connectivity", "rate_limit") and count >= FAILURE_THRESHOLD:
            # Transient failure — mark degraded, don't revoke
            if pt not in _degraded:
                _degraded.add(pt)
                logger.warning("team_monitor: %s marked degraded after %d failures", pt, count)
                await log_team_action(
                    action=f"provider.degraded.{pt}",
                    reason=f"{pt} failed {count} consecutive health checks ({error_type})",
                    outcome="provider marked degraded; requests routing to next tier",
                    meta={"provider_type": pt, "key_id": key_id,
                          "error": error_type, "failures": count},
                )
                any_action_taken = True

    if any_action_taken:
        active_count = sum(1 for k, v in _failure_counts.items() if v == 0)
        await _notify_delon(
            "Team monitor took action — FYI",
            f"The team monitor resolved a provider issue. "
            f"Check /team/ops for the full action log. "
            f"No action needed from you unless you want to add a replacement key."
        )


async def run_monitor_loop() -> None:
    """Main loop — runs forever, one health cycle every MONITOR_INTERVAL_SEC."""
    logger.info("team_monitor: starting — interval=%ds, threshold=%d failures",
                MONITOR_INTERVAL_SEC, FAILURE_THRESHOLD)
    # Initial delay so startup completes before first check
    await asyncio.sleep(60)
    while True:
        try:
            await _run_health_cycle()
        except Exception as e:
            logger.error("team_monitor: unhandled error in health cycle: %s", e)
        await asyncio.sleep(MONITOR_INTERVAL_SEC)
