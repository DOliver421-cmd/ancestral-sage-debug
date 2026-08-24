"""Provider Gateway endpoints for the executive shared AI key pool."""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from roles import ROLE_RANK

router = APIRouter(tags=["provider-gateway"])
db = None
current_user = audit = None

PROVIDERS = {
    "groq": ("Groq", "llama-3.3-70b-versatile", "https://console.groq.com"),
    "cerebras": ("Cerebras", "llama3.3-70b", "https://cloud.cerebras.ai"),
    "gemini": ("Google Gemini", "gemini-2.0-flash", "https://aistudio.google.com"),
    "mistral": ("Mistral", "mistral-small-latest", "https://console.mistral.ai"),
    "cohere": ("Cohere", "command-r-plus", "https://dashboard.cohere.com/api-keys"),
    "together": ("Together AI", "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", "https://api.together.xyz/settings/api-keys"),
    "xai": ("xAI / Grok", "grok-3-mini", "https://console.x.ai"),
}

class QuickSetupRequest(BaseModel):
    provider_type: str
    api_key: str

async def _user(authorization: Optional[str] = Header(None)):
    return await current_user(authorization)

def _exec(user):
    if ROLE_RANK.get(user.role, 0) < ROLE_RANK["executive_admin"]:
        raise HTTPException(403, "Executive access required.")
    return user

def bind(_db, _current_user, _audit):
    global db, current_user, audit
    db, current_user, audit = _db, _current_user, _audit

def _fernet():
    try:
        import keyvault
        return keyvault.get_fernet()
    except Exception:
        return None

def _mask(value):
    return "••••" + value[-4:] if len(value) >= 4 else "••••"

async def _provider_id(provider_type):
    doc = await db.api_providers.find_one({"provider_type": provider_type})
    if doc:
        return doc.get("id")
    provider_id = str(uuid.uuid4())
    await db.api_providers.insert_one({
        "id": provider_id, "provider_type": provider_type,
        "name": PROVIDERS[provider_type][0], "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return provider_id

@router.get("/providers/quick-setup/status")
async def quick_setup_status(user=Depends(_user)):
    _exec(user)
    providers = {}
    async for p in db.api_providers.find({"provider_type": {"$in": list(PROVIDERS)}}):
        providers[p.get("provider_type")] = p.get("id")
    keys = {}
    if providers:
        async for k in db.api_keys.find({"provider_id": {"$in": list(providers.values())}, "status": "active"}):
            for provider_type, provider_id in providers.items():
                if k.get("provider_id") == provider_id:
                    keys[provider_type] = k
    return {
        provider_type: {
            "configured": provider_type in keys,
            "key_masked": (keys[provider_type].get("key_masked") if provider_type in keys else None),
            "source": "gateway",
        }
        for provider_type in PROVIDERS
    }

@router.post("/providers/quick-setup")
async def quick_setup(body: QuickSetupRequest, user=Depends(_user)):
    _exec(user)
    provider_type = body.provider_type.strip().lower()
    api_key = body.api_key.strip()
    if provider_type not in PROVIDERS:
        raise HTTPException(400, "Unsupported provider.")
    if not api_key:
        raise HTTPException(400, "API key cannot be empty.")
    fernet = _fernet()
    if fernet is None:
        raise HTTPException(503, "Provider key encryption is not configured on the server.")
    provider_id = await _provider_id(provider_type)
    now = datetime.now(timezone.utc).isoformat()
    encrypted = fernet.encrypt(api_key.encode()).decode()
    await db.api_keys.update_one(
        {"provider_id": provider_id},
        {"$set": {"provider_id": provider_id, "encrypted_key": encrypted, "key_masked": _mask(api_key), "status": "active", "updated_at": now}, "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
        upsert=True,
    )
    from ai.llm_gateway import reload_provider_keys
    await reload_provider_keys(db)
    await audit(user.id, "provider_gateway.key_saved", meta={"provider": provider_type})
    return {"provider_type": provider_type, "configured": True, "key_masked": _mask(api_key)}

@router.get("/providers/usage-log")
async def usage_log(limit: int = 50, user=Depends(_user)):
    _exec(user)
    return await db.provider_usage.find({}).sort("created_at", -1).to_list(length=min(max(limit, 1), 200))
