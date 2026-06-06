"""app/routes/providers.py — ProviderModule API: provider registry + key management.

All endpoints require executive_admin role.
Key values are write-only: they are encrypted at rest and never returned in GET responses.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.models.user import User
from app.security.auth import require_role
from app.utils.audit import audit

router = APIRouter()


class ProviderCreate(BaseModel):
    name: str
    display_name: str
    provider_type: str
    config_schema: dict = {}


class KeyCreate(BaseModel):
    provider_id: str
    label: str
    plaintext_key: str
    scope: str = "primary"   # "primary" | "backup" | "test"


class ProviderStatusUpdate(BaseModel):
    status: str   # "active" | "inactive" | "maintenance"


# ── Providers ─────────────────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers(
    status: Optional[str] = None,
    user: User = Depends(require_role("executive_admin")),
):
    from app.services.provider_gateway import list_providers as _list
    return {"providers": await _list(status=status)}


@router.post("/providers")
async def create_provider(body: ProviderCreate, user: User = Depends(require_role("executive_admin"))):
    from app.services.provider_gateway import register_provider
    provider = await register_provider(
        body.name, body.display_name, body.provider_type, body.config_schema, actor_id=user.id
    )
    await audit(user.id, "provider.registered", meta={"name": body.name})
    return provider


@router.patch("/providers/{provider_id}/status")
async def update_provider_status(
    provider_id: str,
    body: ProviderStatusUpdate,
    user: User = Depends(require_role("executive_admin")),
):
    valid = {"active", "inactive", "maintenance"}
    if body.status not in valid:
        raise HTTPException(400, f"status must be one of: {', '.join(sorted(valid))}")
    from app.services.provider_gateway import set_provider_status
    ok = await set_provider_status(provider_id, body.status, actor_id=user.id)
    if not ok:
        raise HTTPException(404, "Provider not found")
    await audit(user.id, f"provider.status.{body.status}", meta={"provider_id": provider_id})
    return {"ok": True, "provider_id": provider_id, "status": body.status}


# ── API Keys ──────────────────────────────────────────────────────────────────

@router.get("/providers/keys")
async def list_keys(
    provider_id: Optional[str] = None,
    user: User = Depends(require_role("executive_admin")),
):
    """List keys — encrypted_key field is never returned."""
    from app.services.provider_gateway import list_api_keys
    return {"keys": await list_api_keys(provider_id=provider_id)}


@router.post("/providers/keys")
async def add_key(body: KeyCreate, user: User = Depends(require_role("executive_admin"))):
    """Add and encrypt an API key. The plaintext is never stored unencrypted."""
    if body.scope not in ("primary", "backup", "test"):
        raise HTTPException(400, "scope must be primary | backup | test")
    from app.services.provider_gateway import add_api_key
    key_doc = await add_api_key(
        body.provider_id, body.label, body.plaintext_key, body.scope, actor_id=user.id
    )
    await audit(user.id, "provider.key.added",
                meta={"provider_id": body.provider_id, "label": body.label, "scope": body.scope})
    # Reload gateway globals so the new key is available immediately
    try:
        from ai.llm_gateway import reload_provider_keys
        from app.database import db as _db
        await reload_provider_keys(_db)
    except Exception:
        pass
    return key_doc


@router.delete("/providers/keys/{key_id}")
async def revoke_key(key_id: str, user: User = Depends(require_role("executive_admin"))):
    from app.services.provider_gateway import revoke_api_key
    ok = await revoke_api_key(key_id, actor_id=user.id)
    if not ok:
        raise HTTPException(404, "Key not found")
    await audit(user.id, "provider.key.revoked", meta={"key_id": key_id})
    return {"ok": True, "key_id": key_id}


@router.post("/providers/keys/{key_id}/test")
async def test_key(key_id: str, user: User = Depends(require_role("executive_admin"))):
    """Run a live connectivity test for this key. Returns latency and ok/error."""
    from app.services.provider_gateway import test_api_key
    result = await test_api_key(key_id)
    await audit(user.id, "provider.key.tested",
                meta={"key_id": key_id, "ok": result["ok"], "latency_ms": result.get("latency_ms")})
    return result


class QuickSetupReq(BaseModel):
    provider_type: str   # groq | cerebras | gemini | mistral | cohere | together | etc.
    api_key: str


@router.post("/providers/quick-setup")
async def quick_setup_provider(body: QuickSetupReq, user: User = Depends(require_role("executive_admin"))):
    """Create provider + primary key in one step. Idempotent — safe to call again with a new key."""
    from app.services.provider_gateway import register_provider, add_api_key, list_providers

    _META = {
        "groq":        {"name": "groq",        "display_name": "Groq / Llama 3.3 70B"},
        "cerebras":    {"name": "cerebras",     "display_name": "Cerebras / Llama 3.3 70B"},
        "sambanova":   {"name": "sambanova",    "display_name": "SambaNova / Llama 3.3 70B"},
        "gemini":      {"name": "gemini",       "display_name": "Google Gemini 2.0 Flash"},
        "xai":         {"name": "xai",          "display_name": "xAI / Grok 3 Mini"},
        "cohere":      {"name": "cohere",       "display_name": "Cohere Command R+"},
        "mistral":     {"name": "mistral",      "display_name": "Mistral Small"},
        "together":    {"name": "together",     "display_name": "Together AI / Llama 3.3 70B"},
        "openrouter":  {"name": "openrouter",   "display_name": "OpenRouter (free models)"},
        "huggingface": {"name": "huggingface",  "display_name": "HuggingFace Inference"},
    }
    meta = _META.get(body.provider_type.lower())
    if not meta:
        raise HTTPException(400, f"Unknown provider_type: {body.provider_type}")
    if not body.api_key.strip():
        raise HTTPException(400, "api_key is required")

    # Find or create provider
    from app.database import db as _db
    existing = await _db.api_providers.find_one({"name": meta["name"]})
    if existing:
        provider_id = existing.get("id", str(existing.get("_id", "")))
    else:
        p = await register_provider(
            meta["name"], meta["display_name"], body.provider_type.lower(), {}, actor_id=user.id
        )
        provider_id = p["id"]

    # Revoke existing primary keys for this provider (replacing with new one)
    await _db.api_keys.update_many(
        {"provider_id": provider_id, "scope": "primary", "status": "active"},
        {"$set": {"status": "revoked"}},
    )

    key_doc = await add_api_key(provider_id, f"{meta['name']} key", body.api_key.strip(), "primary", actor_id=user.id)
    await audit(user.id, "provider.quick_setup", meta={"provider": meta["name"]})

    # Reload llm_gateway immediately
    try:
        from ai.llm_gateway import reload_provider_keys
        await reload_provider_keys(_db)
    except Exception:
        pass

    return {"ok": True, "provider": meta["name"], "provider_id": provider_id, "key_id": key_doc["id"]}


@router.get("/providers/quick-setup/status")
async def quick_setup_status(user: User = Depends(require_role("executive_admin"))):
    """Return which of the 6 preset providers have an active key — checks env vars AND DB."""
    import os
    from app.database import db as _db

    # Env var names per provider type
    _ENV = {
        "groq":       ["GROQ_API_KEY"],
        "cerebras":   ["CEREBRAS_API_KEY"],
        "gemini":     ["GEMINI_API_KEY"],
        "mistral":    ["MISTRAL_API_KEY"],
        "cohere":     ["COHERE_API_KEY"],
        "together":   ["TOGETHER_API_KEY"],
        "sambanova":  ["SAMBANOVA_API_KEY"],
        "xai":        ["XAI_API_KEY", "GROK_API_KEY"],
        "openrouter": ["OPENROUTER_API_KEY"],
        "huggingface":["HUGGINGFACE_API_KEY", "HF_API_KEY"],
    }

    preset_types = ["groq", "cerebras", "gemini", "mistral", "cohere", "together"]
    result = {}
    for pt in preset_types:
        # Check env var first
        env_key = next((os.environ.get(k, "") for k in _ENV.get(pt, []) if os.environ.get(k)), "")
        if env_key:
            result[pt] = {
                "configured": True,
                "source": "env",
                "key_masked": f"***{env_key[-4:]}",
            }
            continue

        # Check DB
        provider = await _db.api_providers.find_one({"name": pt})
        if provider:
            pid = provider.get("id", str(provider.get("_id", "")))
            key = await _db.api_keys.find_one({"provider_id": pid, "status": "active", "scope": "primary"})
            result[pt] = {
                "configured": bool(key),
                "source": "db" if key else None,
                "key_masked": key.get("key_masked") if key else None,
            }
        else:
            result[pt] = {"configured": False, "source": None, "key_masked": None}
    return result


@router.get("/providers/usage-log")
async def provider_usage_log(
    provider_id: Optional[str] = None,
    limit: int = 100,
    user: User = Depends(require_role("executive_admin")),
):
    from app.database import db
    filt = {}
    if provider_id:
        filt["provider_id"] = provider_id
    logs = await db.api_key_usage_log.find(filt, {"_id": 0}).sort("created_at", -1).limit(min(limit, 500)).to_list(500)
    return {"logs": logs, "total": len(logs)}
