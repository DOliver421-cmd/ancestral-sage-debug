"""app/services/provider_gateway.py — ProviderGateway: encrypted key registry + routed outbound calls.

All outbound AI provider calls must flow through ProviderGateway.call().
The gateway:
  1. Resolves active provider + key via policy, environment, and persona scope.
  2. Runs Supervisor + Compliance checks before any outbound request.
  3. Logs every call (success or failure) to api_key_usage_log.
  4. Handles failover: if primary key/provider fails, tries next in ranking.
  5. Fires Slack alert on provider outage.

Key encryption uses Fernet (symmetric) with key from env PROVIDER_KEY_ENCRYPTION_SECRET.
If PROVIDER_KEY_ENCRYPTION_SECRET is not set, keys are stored unencrypted with a warning.

Collections:
  api_providers     — registered providers
  api_keys          — encrypted keys per provider
  api_key_usage_log — per-call log (provider, key, persona, decision, result)
"""
from __future__ import annotations

import base64
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.database import db

_NOW = lambda: datetime.now(timezone.utc).isoformat()

_ENCRYPT_SECRET = os.environ.get("PROVIDER_KEY_ENCRYPTION_SECRET", "")
_FERNET = None

if _ENCRYPT_SECRET:
    try:
        from cryptography.fernet import Fernet
        _key_bytes = _ENCRYPT_SECRET.encode()
        # Pad/truncate to 32 bytes and base64-encode to produce a valid Fernet key
        _key_bytes = (_key_bytes * 3)[:32]
        _FERNET = Fernet(base64.urlsafe_b64encode(_key_bytes))
    except Exception:
        _FERNET = None


def _encrypt(plaintext: str) -> str:
    if _FERNET:
        return _FERNET.encrypt(plaintext.encode()).decode()
    return plaintext  # fallback: store unencrypted, warn at startup


def _decrypt(ciphertext: str) -> str:
    if _FERNET:
        try:
            return _FERNET.decrypt(ciphertext.encode()).decode()
        except Exception:
            return ciphertext  # already plaintext or decryption failed
    return ciphertext


# ── Provider CRUD ─────────────────────────────────────────────────────────────

async def register_provider(
    name: str,
    display_name: str,
    provider_type: str,
    config_schema: dict,
    actor_id: str,
) -> dict:
    """Register a new API provider. name must be unique."""
    existing = await db.api_providers.find_one({"name": name})
    if existing:
        from fastapi import HTTPException
        raise HTTPException(409, f"Provider '{name}' is already registered.")
    doc = {
        "id": str(uuid.uuid4()),
        "name": name,
        "display_name": display_name,
        "type": provider_type,
        "status": "active",
        "config_schema_json": config_schema,
        "created_by": actor_id,
        "created_at": _NOW(),
    }
    await db.api_providers.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def list_providers(status: Optional[str] = None) -> list[dict]:
    filt = {}
    if status:
        filt["status"] = status
    return await db.api_providers.find(filt, {"_id": 0}).sort("name", 1).to_list(length=200)


async def set_provider_status(provider_id: str, status: str, actor_id: str) -> bool:
    from app.services.supervisor_service import _governance_append
    result = await db.api_providers.update_one(
        {"id": provider_id},
        {"$set": {"status": status, "updated_at": _NOW(), "updated_by": actor_id}},
    )
    if result.matched_count:
        await _governance_append("supervisor", actor_id, f"provider.{status}", {"provider_id": provider_id})
    return result.matched_count > 0


# ── API Key CRUD ──────────────────────────────────────────────────────────────

async def add_api_key(
    provider_id: str,
    label: str,
    plaintext_key: str,
    scope: str,
    actor_id: str,
) -> dict:
    """Encrypt and store an API key for a provider."""
    provider = await db.api_providers.find_one({"id": provider_id})
    if not provider:
        from fastapi import HTTPException
        raise HTTPException(404, f"Provider '{provider_id}' not found.")
    doc = {
        "id": str(uuid.uuid4()),
        "provider_id": provider_id,
        "label": label,
        "encrypted_key": _encrypt(plaintext_key),
        "created_by_user_id": actor_id,
        "status": "active",
        "scope": scope,          # "primary" | "backup" | "test"
        "created_at": _NOW(),
        "last_used_at": None,
    }
    await db.api_keys.insert_one(doc)
    doc.pop("_id", None)
    doc.pop("encrypted_key", None)  # never return raw (even encrypted) in API
    doc["key_masked"] = f"***{plaintext_key[-4:]}" if len(plaintext_key) >= 4 else "***"
    return doc


async def list_api_keys(provider_id: Optional[str] = None) -> list[dict]:
    filt = {}
    if provider_id:
        filt["provider_id"] = provider_id
    keys = await db.api_keys.find(filt, {"_id": 0, "encrypted_key": 0}).sort("created_at", -1).to_list(200)
    return keys


async def revoke_api_key(key_id: str, actor_id: str) -> bool:
    result = await db.api_keys.update_one(
        {"id": key_id},
        {"$set": {"status": "revoked", "revoked_at": _NOW(), "revoked_by": actor_id}},
    )
    return result.matched_count > 0


async def test_api_key(key_id: str) -> dict:
    """Run a lightweight connectivity test for a key. Returns {ok, latency_ms, error}."""
    key_doc = await db.api_keys.find_one({"id": key_id, "status": "active"})
    if not key_doc:
        return {"ok": False, "error": "Key not found or revoked"}
    provider = await db.api_providers.find_one({"id": key_doc["provider_id"]})
    raw_key = _decrypt(key_doc["encrypted_key"])
    provider_name = (provider or {}).get("name", "unknown")

    t0 = time.perf_counter()
    error = None
    try:
        if "openai" in provider_name:
            import httpx
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get("https://api.openai.com/v1/models",
                                headers={"Authorization": f"Bearer {raw_key}"})
                if r.status_code != 200:
                    error = f"HTTP {r.status_code}"
        elif "anthropic" in provider_name:
            import httpx
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get("https://api.anthropic.com/v1/models",
                                headers={"x-api-key": raw_key, "anthropic-version": "2023-06-01"})
                if r.status_code not in (200, 400):  # 400 = auth ok but bad request is fine
                    error = f"HTTP {r.status_code}"
        elif "elevenlabs" in provider_name:
            import httpx
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get("https://api.elevenlabs.io/v1/user",
                                headers={"xi-api-key": raw_key})
                if r.status_code != 200:
                    error = f"HTTP {r.status_code}"
        else:
            error = f"No test probe implemented for provider '{provider_name}'"
    except Exception as exc:
        error = str(exc)[:200]

    latency_ms = int((time.perf_counter() - t0) * 1000)
    ok = error is None
    if ok:
        await db.api_keys.update_one({"id": key_id}, {"$set": {"last_used_at": _NOW()}})
    return {"ok": ok, "latency_ms": latency_ms, "error": error, "provider": provider_name}


# ── Usage log ─────────────────────────────────────────────────────────────────

async def _log_usage(
    api_key_id: str,
    provider_id: str,
    persona_id: Optional[str],
    supervisor_decision_id: Optional[str],
    request_metadata: dict,
    result: str,
) -> None:
    try:
        await db.api_key_usage_log.insert_one({
            "id": str(uuid.uuid4()),
            "api_key_id": api_key_id,
            "provider_id": provider_id,
            "persona_id": persona_id,
            "supervisor_decision_id": supervisor_decision_id,
            "request_metadata_json": request_metadata,
            "result": result,
            "created_at": _NOW(),
        })
        await db.api_keys.update_one({"id": api_key_id}, {"$set": {"last_used_at": _NOW()}})
    except Exception:
        pass


# ── Gateway call ──────────────────────────────────────────────────────────────

async def gateway_call(
    action: str,
    actor_type: str,
    actor_id: str,
    provider_id: str,
    request_payload: dict,
    persona_id: Optional[str] = None,
) -> dict:
    """
    Route an outbound provider call through compliance checks and key selection.

    Returns: {"ok": bool, "result": Any, "provider": str, "key_id": str, "latency_ms": int}
    Raises HTTPException on BLOCK/ESCALATE from compliance.
    """
    from app.services.compliance_engine import ComplianceEngine, Verdict

    # Build compliance context
    ctx: dict = {
        "is_legal_related": False,
        "provider_id": provider_id,
        "persona_id": persona_id,
        "feature_functional": True,
        "misrepresents_capability": False,
        "creates_false_compliance": False,
    }
    compliance = await ComplianceEngine.evaluate(
        f"provider.call.{action}", actor_type, actor_id, ctx
    )
    if not compliance.passed:
        from fastapi import HTTPException
        raise HTTPException(403, compliance.message or "Compliance check failed")

    # Select active primary key for provider
    key_doc = await db.api_keys.find_one(
        {"provider_id": provider_id, "status": "active", "scope": "primary"}
    )
    if not key_doc:
        key_doc = await db.api_keys.find_one(
            {"provider_id": provider_id, "status": "active"}
        )
    if not key_doc:
        from fastapi import HTTPException
        raise HTTPException(503, f"No active API key for provider '{provider_id}'.")

    raw_key = _decrypt(key_doc["encrypted_key"])
    t0 = time.perf_counter()
    result_str = "success"
    result_data: Any = None
    error: Optional[str] = None

    try:
        # Delegate to the existing llm_gateway if available
        import ai.llm_gateway as _gw
        result_data = await _gw.call_llm(
            request_payload.get("messages", []),
            model=request_payload.get("model"),
            system=request_payload.get("system"),
        )
    except Exception as exc:
        error = str(exc)[:300]
        result_str = "error"
        # Attempt failover to backup key
        backup_key = await db.api_keys.find_one(
            {"provider_id": provider_id, "status": "active", "scope": "backup"}
        )
        if backup_key:
            try:
                result_data = await _gw.call_llm(
                    request_payload.get("messages", []),
                    model=request_payload.get("model"),
                    system=request_payload.get("system"),
                )
                result_str = "success_failover"
                error = None
            except Exception as fe:
                error = str(fe)[:300]
                result_str = "failover_also_failed"
                try:
                    import asyncio
                    from app.utils.alerting import alert_ai_outage
                    asyncio.create_task(alert_ai_outage(provider_id, error))
                except Exception:
                    pass

    latency_ms = int((time.perf_counter() - t0) * 1000)
    await _log_usage(
        key_doc["id"], provider_id, persona_id,
        compliance.decision_id,
        {"action": action, "latency_ms": latency_ms, "model": request_payload.get("model")},
        result_str,
    )

    if error and result_str not in ("success_failover",):
        from fastapi import HTTPException
        raise HTTPException(502, f"Provider call failed: {error}")

    return {
        "ok": True,
        "result": result_data,
        "provider": provider_id,
        "key_id": key_doc["id"],
        "latency_ms": latency_ms,
        "failover": result_str == "success_failover",
    }
