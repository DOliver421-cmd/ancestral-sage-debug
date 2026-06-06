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
