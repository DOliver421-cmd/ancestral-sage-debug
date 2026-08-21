"""
Billing + Provider Gateway + Team Operations router.

Extracted verbatim from backend/server.py (monolith refactor, slice 10).
Each registration block keeps its original try/except wrapper — if a
dependency is missing (e.g. cryptography), the routes skip with a warning
instead of crashing startup. Shared state (db, current_user, audit) is bound
by server.py via bind() at include time — no circular imports.
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["billing", "providers", "team"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = audit = None


def bind(_db, _current_user, _audit):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit
    db = _db
    current_user = _current_user
    audit = _audit


# Mirrors server.py's role hierarchy for runtime require_role checks.
from routers.roles import ROLE_RANK, Role


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: Role = "student"
    associate: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    avatar_url: Optional[str] = None
    feature_tier: str = "free"


async def _dep_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Resolve the real current_user at REQUEST time (bind() sets it after import)."""
    return await current_user(authorization)


def _require_rank(*roles):
    """Runtime equivalent of server.py's require_role() — used in Depends()
    because require_role is bound after this module loads (no import-time call)."""
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: User = Depends(_dep_current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            logger.warning("Unauthorized access attempt — insufficient privileges (user=%s, role=%s)", user.id, user.role)
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


# ═════════════════════════════════════════════════════════════════════════════
# Extracted registration blocks (verbatim from backend/server.py)
# ═════════════════════════════════════════════════════════════════════════════
# ── Billing Admin routes (/billing/credits, /billing/refunds, /billing/sage-sessions) ─
# WAI-specific admin tools: credit grants, site-credit refunds, cash refunds, Sage sessions.
# Stored in MongoDB collections: wai_credits, wai_refunds, sage_conduct_sessions.
try:
    from cryptography.fernet import Fernet as _Fernet, InvalidToken as _InvalidToken
    _BILLING_FERNET = None
    _bfe_key = os.environ.get("PROVIDER_KEY_ENCRYPTION_SECRET", "")
    if _bfe_key:
        try:
            _BILLING_FERNET = _Fernet(_bfe_key.encode() if isinstance(_bfe_key, str) else _bfe_key)
        except Exception:
            pass

    class _GrantBody(BaseModel):
        user_id: str
        amount_cents: int
        reason: str

    class _SiteCreditBody(BaseModel):
        user_id: str
        platform_cost_cents: int
        reason: str
        user_received_value: bool = False

    class _CashRefundBody(BaseModel):
        user_id: str
        amount_cents: int
        reason: str
        conditions: dict

    class _ResolveSessionBody(BaseModel):
        user_self_corrected: bool
        actor_id: Optional[str] = None

    @router.get("/billing/credits/balance")
    async def billing_credits_balance(user_id: Optional[str] = None, user: User = Depends(_require_rank("admin"))):
        uid = user_id or user.id
        doc = await db.wai_credits.find_one({"user_id": uid}, {"_id": 0})
        if not doc:
            return {"user_id": uid, "balance_cents": 0}
        return {"user_id": uid, "balance_cents": doc.get("balance_cents", 0)}

    @router.post("/billing/credits/grant")
    async def billing_credits_grant(body: _GrantBody, user: User = Depends(_require_rank("admin"))):
        await db.wai_credits.update_one(
            {"user_id": body.user_id},
            {"$inc": {"balance_cents": body.amount_cents},
             "$push": {"ledger": {"ts": datetime.utcnow(), "amount_cents": body.amount_cents,
                                  "reason": body.reason, "actor_id": user.id}}},
            upsert=True,
        )
        await audit(db, user.id, "billing_grant", {"user_id": body.user_id, "amount_cents": body.amount_cents, "reason": body.reason})
        return {"ok": True, "user_id": body.user_id, "granted_cents": body.amount_cents}

    @router.post("/billing/refunds/site-credits")
    async def billing_site_credit_refund(body: _SiteCreditBody, user: User = Depends(_require_rank("admin"))):
        # If no value delivered: refund = cost + 10%. If value received: refund = cost only.
        amount = body.platform_cost_cents if body.user_received_value else round(body.platform_cost_cents * 1.10)
        await db.wai_credits.update_one(
            {"user_id": body.user_id},
            {"$inc": {"balance_cents": amount},
             "$push": {"ledger": {"ts": datetime.utcnow(), "amount_cents": amount,
                                  "reason": f"Site credit refund: {body.reason}", "actor_id": user.id}}},
            upsert=True,
        )
        await db.wai_refunds.insert_one({
            "type": "site_credit", "user_id": body.user_id, "amount_cents": amount,
            "platform_cost_cents": body.platform_cost_cents, "reason": body.reason,
            "user_received_value": body.user_received_value, "actor_id": user.id,
            "created_at": datetime.utcnow(),
        })
        await audit(db, user.id, "billing_site_credit_refund", {"user_id": body.user_id, "amount_cents": amount})
        return {"ok": True, "user_id": body.user_id, "amount_cents": amount}

    @router.post("/billing/refunds/cash")
    async def billing_cash_refund(body: _CashRefundBody, user: User = Depends(_require_rank("executive_admin"))):
        conditions = body.conditions or {}
        required = ["is_extreme_violation", "user_not_at_fault", "is_legal", "no_harm_to_wai", "supervisor_approved"]
        if not all(conditions.get(k) for k in required):
            raise HTTPException(400, "All 5 conditions must be confirmed for a cash refund.")
        await db.wai_refunds.insert_one({
            "type": "cash", "user_id": body.user_id, "amount_cents": body.amount_cents,
            "reason": body.reason, "conditions": conditions, "actor_id": user.id,
            "status": "pending_processing", "created_at": datetime.utcnow(),
        })
        await audit(db, user.id, "billing_cash_refund_submitted", {"user_id": body.user_id, "amount_cents": body.amount_cents})
        return {"ok": True, "status": "pending_processing", "message": "Cash refund submitted for processing."}

    @router.get("/billing/sage-sessions")
    async def billing_sage_sessions(user: User = Depends(_require_rank("admin"))):
        docs = await db.sage_conduct_sessions.find({}, {"_id": 1, "user_id": 1, "trigger_reason": 1,
            "status": 1, "fee_amount": 1, "created_at": 1}).sort("created_at", -1).to_list(200)
        for d in docs:
            d["_id"] = str(d["_id"])
            if hasattr(d.get("created_at"), "isoformat"):
                d["created_at"] = d["created_at"].isoformat()
        return docs

    @router.post("/billing/sage-sessions/{session_id}/resolve")
    async def billing_resolve_sage_session(session_id: str, body: _ResolveSessionBody, user: User = Depends(_require_rank("admin"))):
        from bson import ObjectId as _ObjId
        try:
            oid = _ObjId(session_id)
        except Exception:
            raise HTTPException(400, "Invalid session ID")
        update = {
            "status": "resolved" if body.user_self_corrected else "escalated",
            "fee_waived": body.user_self_corrected,
            "resolved_by": body.actor_id or user.id,
            "resolved_at": datetime.utcnow(),
        }
        result = await db.sage_conduct_sessions.update_one({"_id": oid}, {"$set": update})
        if result.matched_count == 0:
            raise HTTPException(404, "Session not found")
        await audit(db, user.id, "sage_session_resolved", {"session_id": session_id, "self_corrected": body.user_self_corrected})
        return {"ok": True, "status": update["status"], "fee_waived": body.user_self_corrected}

    logger.info("Billing admin routes registered")
except Exception as _billing_routes_err:
    logger.warning(f"Billing admin routes unavailable: {_billing_routes_err}")


# ── Provider Gateway routes (/providers, /providers/keys) ─────────────────────
# Executive-only AI provider management. Keys encrypted at rest via Fernet.
# PROVIDER_KEY_ENCRYPTION_SECRET env var must be set; keys are never returned in plaintext.
try:
    import secrets as _secrets_mod
    from cryptography.fernet import Fernet as _PFernet
    from bson import ObjectId as _PObjId

    _PFERNET = None
    _pfk = os.environ.get("PROVIDER_KEY_ENCRYPTION_SECRET", "")
    if _pfk:
        try:
            _PFERNET = _PFernet(_pfk.encode() if isinstance(_pfk, str) else _pfk)
        except Exception:
            try:
                import base64 as _pfb64
                _pfkb = (_pfk.encode() * 3)[:32]
                _PFERNET = _PFernet(_pfb64.urlsafe_b64encode(_pfkb))
            except Exception:
                pass

    def _encrypt_key(plaintext: str) -> str:
        if not _PFERNET:
            raise HTTPException(503, "PROVIDER_KEY_ENCRYPTION_SECRET not configured")
        return _PFERNET.encrypt(plaintext.encode()).decode()

    class _ProviderBody(BaseModel):
        name: str
        provider_type: str = "custom"
        base_url: Optional[str] = ""
        notes: Optional[str] = ""

    class _KeyBody(BaseModel):
        provider_id: str
        label: str
        plaintext_key: str
        scope: Optional[str] = "chat"

    class _ProviderStatusBody(BaseModel):
        status: str

    def _ser_provider(doc):
        if doc:
            doc["_id"] = str(doc["_id"])
            if hasattr(doc.get("created_at"), "isoformat"):
                doc["created_at"] = doc["created_at"].isoformat()
            doc.pop("encrypted_key", None)  # never expose encrypted key
        return doc

    @router.get("/providers")
    async def providers_list(user: User = Depends(_require_rank("executive_admin"))):
        docs = await db.ai_providers.find({}, {"encrypted_key": 0}).sort("created_at", -1).to_list(200)
        return [_ser_provider(d) for d in docs]

    @router.post("/providers")
    async def providers_create(body: _ProviderBody, user: User = Depends(_require_rank("executive_admin"))):
        doc = {"name": body.name, "provider_type": body.provider_type,
               "base_url": body.base_url or "", "notes": body.notes or "",
               "status": "inactive", "created_by": user.id, "created_at": datetime.utcnow()}
        result = await db.ai_providers.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        doc.pop("encrypted_key", None)
        await audit(db, user.id, "provider_created", {"name": body.name, "type": body.provider_type})
        return _ser_provider(doc)

    @router.patch("/providers/{provider_id}/status")
    async def providers_set_status(provider_id: str, body: _ProviderStatusBody, user: User = Depends(_require_rank("executive_admin"))):
        if body.status not in ("active", "inactive"):
            raise HTTPException(400, "status must be active or inactive")
        try:
            oid = _PObjId(provider_id)
        except Exception:
            raise HTTPException(400, "Invalid provider ID")
        result = await db.ai_providers.update_one({"_id": oid}, {"$set": {"status": body.status}})
        if result.matched_count == 0:
            raise HTTPException(404, "Provider not found")
        await audit(db, user.id, "provider_status_changed", {"provider_id": provider_id, "status": body.status})
        return {"ok": True, "status": body.status}

    @router.get("/providers/keys")
    async def provider_keys_list(user: User = Depends(_require_rank("executive_admin"))):
        docs = await db.ai_provider_keys.find({}, {"encrypted_key": 0}).sort("created_at", -1).to_list(500)
        for d in docs:
            d["_id"] = str(d["_id"])
            if hasattr(d.get("created_at"), "isoformat"):
                d["created_at"] = d["created_at"].isoformat()
        return docs

    @router.post("/providers/keys")
    async def provider_keys_create(body: _KeyBody, user: User = Depends(_require_rank("executive_admin"))):
        encrypted = _encrypt_key(body.plaintext_key)
        doc = {"provider_id": body.provider_id, "label": body.label,
               "encrypted_key": encrypted, "scope": body.scope or "chat",
               "created_by": user.id, "created_at": datetime.utcnow()}
        result = await db.ai_provider_keys.insert_one(doc)
        await audit(db, user.id, "provider_key_added", {"provider_id": body.provider_id, "label": body.label})
        # Reload gateway keys immediately so the new key takes effect without a redeploy
        try:
            from ai.llm_gateway import reload_provider_keys as _rlk
            await _rlk(db)
        except Exception:
            pass
        return {"ok": True, "_id": str(result.inserted_id), "label": body.label, "scope": body.scope}

    @router.delete("/providers/keys/{key_id}")
    async def provider_keys_delete(key_id: str, user: User = Depends(_require_rank("executive_admin"))):
        try:
            oid = _PObjId(key_id)
        except Exception:
            raise HTTPException(400, "Invalid key ID")
        result = await db.ai_provider_keys.delete_one({"_id": oid})
        if result.deleted_count == 0:
            raise HTTPException(404, "Key not found")
        await audit(db, user.id, "provider_key_deleted", {"key_id": key_id})
        return {"ok": True}

    @router.post("/providers/keys/{key_id}/test")
    async def provider_keys_test(key_id: str, user: User = Depends(_require_rank("executive_admin"))):
        try:
            oid = _PObjId(key_id)
        except Exception:
            raise HTTPException(400, "Invalid key ID")
        doc = await db.ai_provider_keys.find_one({"_id": oid})
        if not doc:
            raise HTTPException(404, "Key not found")
        if not _PFERNET:
            raise HTTPException(503, "Encryption not configured — cannot decrypt key for test")
        try:
            plaintext = _PFERNET.decrypt(doc["encrypted_key"].encode()).decode()
        except Exception:
            raise HTTPException(500, "Failed to decrypt key")
        # Determine provider type to pick the right test endpoint
        provider = await db.ai_providers.find_one({"_id": _PObjId(doc["provider_id"])}) if doc.get("provider_id") else None
        ptype = (provider or {}).get("provider_type", "openai")
        import httpx as _httpx, time as _time
        start = _time.monotonic()
        try:
            async with _httpx.AsyncClient(timeout=10) as client:
                if ptype == "anthropic":
                    r = await client.post("https://api.anthropic.com/v1/messages",
                        headers={"x-api-key": plaintext, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}]})
                else:
                    base = (provider or {}).get("base_url") or "https://api.openai.com/v1"
                    r = await client.post(f"{base}/chat/completions",
                        headers={"Authorization": f"Bearer {plaintext}", "content-type": "application/json"},
                        json={"model": "gpt-4o-mini", "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}]})
            latency_ms = round((_time.monotonic() - start) * 1000)
            ok = r.status_code < 500
            return {"ok": ok, "latency_ms": latency_ms, "status_code": r.status_code}
        except Exception as e:
            latency_ms = round((_time.monotonic() - start) * 1000)
            return {"ok": False, "latency_ms": latency_ms, "error": str(e)}

    @router.get("/providers/usage-log")
    async def provider_usage_log(user: User = Depends(_require_rank("executive_admin"))):
        docs = await db.ai_usage_log.find({}, {"_id": 0}).sort("created_at", -1).limit(500).to_list(500)
        for d in docs:
            if hasattr(d.get("created_at"), "isoformat"):
                d["created_at"] = d["created_at"].isoformat()
        return docs

    logger.info("Provider gateway routes registered")

    # ── Quick-setup endpoints (preset cards UI) ────────────────────────────────
    # These use db.api_providers / db.api_keys (new modular collections) and the
    # correct Fernet key derivation that matches app/services/provider_gateway.py.

    import base64 as _b64, uuid as _uuid2
    _PFERNET2 = None
    _pfk2 = os.environ.get("PROVIDER_KEY_ENCRYPTION_SECRET", "")
    if _pfk2:
        try:
            _kb2 = (_pfk2.encode() * 3)[:32]
            _PFERNET2 = _PFernet(_b64.urlsafe_b64encode(_kb2))
        except Exception:
            pass

    def _qs_encrypt(plaintext: str) -> str:
        if _PFERNET2:
            return _PFERNET2.encrypt(plaintext.encode()).decode()
        return plaintext  # no secret — store unencrypted

    _QS_META = {
        "groq":        {"name": "groq",        "display_name": "Groq / Llama 3.3 70B"},
        "cerebras":    {"name": "cerebras",     "display_name": "Cerebras / Llama 3.3 70B"},
        "sambanova":   {"name": "sambanova",    "display_name": "SambaNova / Llama 3.3 70B"},
        "gemini":      {"name": "gemini",       "display_name": "Google Gemini 2.0 Flash"},
        "xai":         {"name": "xai",          "display_name": "xAI / Grok 3 Mini"},
        "grok":        {"name": "xai",          "display_name": "xAI / Grok 3 Mini"},
        "cohere":      {"name": "cohere",       "display_name": "Cohere Command R+"},
        "mistral":     {"name": "mistral",      "display_name": "Mistral Small"},
        "together":    {"name": "together",     "display_name": "Together AI / Llama 3.3 70B"},
        "openrouter":  {"name": "openrouter",   "display_name": "OpenRouter (free models)"},
        "huggingface": {"name": "huggingface",  "display_name": "HuggingFace Inference"},
    }

    class _QuickSetupReq(BaseModel):
        provider_type: str
        api_key: str

    @router.post("/providers/quick-setup")
    async def quick_setup_provider(body: _QuickSetupReq, user: User = Depends(_require_rank("executive_admin"))):
        meta = _QS_META.get(body.provider_type.lower())
        if not meta:
            raise HTTPException(400, f"Unknown provider_type: {body.provider_type}")
        if not body.api_key.strip():
            raise HTTPException(400, "api_key is required")
        _now = lambda: datetime.utcnow().isoformat()
        existing = await db.api_providers.find_one({"name": meta["name"]})
        if existing:
            if not existing.get("id"):
                new_id = str(_uuid2.uuid4())
                await db.api_providers.update_one({"_id": existing["_id"]}, {"$set": {"id": new_id}})
                existing["id"] = new_id
            provider_id = existing["id"]
        else:
            provider_doc = {"id": str(_uuid2.uuid4()), "name": meta["name"],
                            "display_name": meta["display_name"], "type": body.provider_type.lower(),
                            "status": "active", "created_by": user.id, "created_at": _now()}
            await db.api_providers.insert_one(provider_doc)
            provider_id = provider_doc["id"]
        # Revoke old primary keys
        await db.api_keys.update_many(
            {"provider_id": provider_id, "scope": "primary", "status": "active"},
            {"$set": {"status": "revoked"}})
        masked = f"***{body.api_key.strip()[-4:]}" if len(body.api_key.strip()) >= 4 else "***"
        key_doc = {"id": str(_uuid2.uuid4()), "provider_id": provider_id,
                   "label": f"{meta['name']} key", "encrypted_key": _qs_encrypt(body.api_key.strip()),
                   "key_masked": masked, "status": "active", "scope": "primary",
                   "created_by_user_id": user.id, "created_at": _now(), "last_used_at": None}
        await db.api_keys.insert_one(key_doc)
        try:
            from ai.llm_gateway import reload_provider_keys as _rlk2
            await _rlk2(db)
        except Exception:
            pass
        return {"ok": True, "provider": meta["name"], "provider_id": provider_id, "key_id": key_doc["id"]}

    _QS_ENV = {
        "groq": ["GROQ_API_KEY"], "cerebras": ["CEREBRAS_API_KEY"],
        "gemini": ["GEMINI_API_KEY"], "mistral": ["MISTRAL_API_KEY"],
        "cohere": ["COHERE_API_KEY"], "together": ["TOGETHER_API_KEY"],
        "xai": ["XAI_API_KEY", "GROK_API_KEY"],
    }

    @router.get("/providers/quick-setup/status")
    async def quick_setup_status(user: User = Depends(_require_rank("executive_admin"))):
        preset_types = ["groq", "cerebras", "gemini", "mistral", "cohere", "together", "xai"]
        result = {}
        for pt in preset_types:
            env_key = next((os.environ.get(k, "") for k in _QS_ENV.get(pt, []) if os.environ.get(k)), "")
            if env_key:
                result[pt] = {"configured": True, "source": "env", "key_masked": f"***{env_key[-4:]}"}
                continue
            provider = await db.api_providers.find_one({"name": pt})
            if provider:
                pid = provider.get("id", str(provider.get("_id", "")))
                key = await db.api_keys.find_one({"provider_id": pid, "status": "active", "scope": "primary"})
                result[pt] = {"configured": bool(key), "source": "db" if key else None,
                              "key_masked": key.get("key_masked") if key else None}
            else:
                result[pt] = {"configured": False, "source": None, "key_masked": None}
        return result

    @router.get("/providers/usage-log")
    async def provider_usage_log_v2(
        provider_id: Optional[str] = None,
        limit: int = 100,
        user: User = Depends(_require_rank("executive_admin")),
    ):
        filt = {}
        if provider_id:
            filt["provider_id"] = provider_id
        logs = await db.api_key_usage_log.find(filt, {"_id": 0}).sort("created_at", -1).limit(min(limit, 500)).to_list(500)
        return {"logs": logs, "total": len(logs)}

except Exception as _pgw_err:
    logger.warning("Provider gateway routes skipped: %s", _pgw_err)


# ── Team Operations routes ─────────────────────────────────────────────────────
try:
    @router.get("/team/actions")
    async def team_actions_list(
        limit: int = 100,
        user: User = Depends(_require_rank("executive_admin")),
    ):
        docs = await db.team_actions.find({"actor": "team.supervisor"}, {"_id": 0}).sort("at", -1).limit(min(limit, 500)).to_list(500)
        human_count = await db.team_actions.count_documents({"human_initiated": True})
        auto_count  = await db.team_actions.count_documents({"human_initiated": False})
        return {"actions": docs, "total": len(docs), "human_count": human_count, "auto_count": auto_count}

    @router.get("/team/monitor/status")
    async def team_monitor_status(user: User = Depends(_require_rank("executive_admin"))):
        try:
            from ai.team_monitor import _failure_counts, _degraded, MONITOR_INTERVAL_SEC, FAILURE_THRESHOLD
            return {"interval_sec": MONITOR_INTERVAL_SEC, "failure_threshold": FAILURE_THRESHOLD,
                    "failure_counts": dict(_failure_counts), "degraded": list(_degraded)}
        except Exception:
            return {"interval_sec": 300, "failure_threshold": 3, "failure_counts": {}, "degraded": []}

    logger.info("Team operations routes registered")
except Exception as _tops_err:
    logger.warning("Team operations routes skipped: %s", _tops_err)
except Exception as _provider_routes_err:
    logger.warning(f"Provider gateway routes unavailable: {_provider_routes_err}")
