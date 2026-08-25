"""
Identity & Access Management — "Who has authorized access to what?"

A delegation-based authorization layer that sits NEXT TO the role/tier system
without creating or deleting any roles. It answers:

  1. Identities      — humans, AI agents, system services, organizations, external
  2. Ownership       — every resource records an owner (ownership != administration)
  3. Authorization   — Owner -> authorizes -> Agent, with explicit can/cannot scope
  4. AI identity     — an agent acts ON BEHALF OF a principal under a delegation,
                       never "as the user"
  5. Delegation      — principal grants a delegate authority over a scope,
                       optionally time-boxed and revocable
  6. Consent history — "what have I authorized?" + revoke
  7. Action history  — every action records its authorization (or the denial)
  8. AI-to-AI chains — authority propagates ONLY through explicit delegations,
                       never by inheritance

Roles and tiers are intentionally untouched: this module reads `users.role`
only to decide who may administer the IAM console itself.
"""
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

router = APIRouter(prefix="/iam", tags=["iam"])

# ── Database binding (set by server.py) ──────────────────────────────────────
db = None
current_user = None

def bind(_db, _current_user):
    global db, current_user
    db = _db
    current_user = _current_user


async def _dep_current_user(authorization: Optional[str] = Header(None)):
    """Resolve the real current_user at REQUEST time (bind sets it after import)."""
    if current_user is None:
        raise HTTPException(503, "Service starting up")
    return await current_user(authorization)


async def _dep_optional_user(authorization: Optional[str] = Header(None)):
    """Like _dep_current_user, but anonymous is allowed — agents authenticate
    with their own X-Agent-ID / X-Agent-Token instead of a human session."""
    if current_user is None:
        return None
    try:
        return await current_user(authorization)
    except HTTPException:
        return None


# ── Constants ────────────────────────────────────────────────────────────────
IDENTITY_KINDS = ("human", "ai_agent", "system_service", "organization", "external")
AUTHORITIES = ("read", "write", "create", "delete", "execute", "manage")

# Action verb -> required authority
ACTION_AUTHORITY = {
    "read": "read",
    "view": "read",
    "create": "create",
    "edit": "write",
    "update": "write",
    "write": "write",
    "delete": "delete",
    "execute": "execute",
    "run": "execute",
    "grant": "manage",
    "manage": "manage",
}

ADMIN_ROLES = ("admin", "executive_admin")


# ── Small helpers ────────────────────────────────────────────────────────────
def _uid() -> str:
    return secrets.token_hex(8)


def _now():
    return datetime.now(timezone.utc)


def _is_admin(user) -> bool:
    return bool(user) and getattr(user, "role", "") in ADMIN_ROLES


def _role_rank(user) -> int:
    rank = {"student": 0, "member": 0, "support_staff": 1, "instructor": 1,
            "admin": 2, "executive_admin": 3}
    return rank.get(getattr(user, "role", ""), 0)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _iso(dt) -> Optional[str]:
    return dt.isoformat() if dt else None


def _identity(identity_id: str):
    return db.iam_identities.find_one({"id": identity_id})


async def _ensure_human_identity(user) -> dict:
    """Materialize (or refresh) the human identity record for a platform user."""
    ident = await db.iam_identities.find_one({"kind": "human", "owner_id": user.id})
    if ident is None:
        ident = {
            "id": _uid(),
            "kind": "human",
            "name": getattr(user, "full_name", None) or getattr(user, "email", "human"),
            "description": "Platform user",
            "owner_id": user.id,
            "owner_kind": "self",
            "parent_id": None,
            "role": getattr(user, "role", "student"),
            "status": "active",
            "created_at": _now(),
            "created_by": user.id,
        }
        await db.iam_identities.insert_one(ident)
    else:
        # Keep the human profile in sync with the users collection.
        updates = {}
        full_name = getattr(user, "full_name", None)
        if full_name:
            updates["name"] = full_name
        role = getattr(user, "role", None)
        if role and ident.get("role") != role:
            updates["role"] = role
        if updates:
            await db.iam_identities.update_one({"id": ident["id"]}, {"$set": updates})
            ident.update(updates)
    return ident


def _delegation_active(d: dict) -> bool:
    if d.get("revoked_at"):
        return False
    exp = d.get("expires_at")
    if exp and isinstance(exp, str):
        try:
            from datetime import datetime as _dt
            exp = _dt.fromisoformat(exp.replace("Z", "+00:00"))
        except Exception:
            exp = None
    if exp and exp < _now():
        return False
    return True


def _delegation_covers(d: dict, resource_type: str, resource_key: Optional[str]) -> bool:
    if d.get("scope_all_owned") or not d.get("resources"):
        return True
    for r in d.get("resources", []):
        if r.get("resource_type") != resource_type:
            continue
        if r.get("resource_key") and resource_key and r["resource_key"] != resource_key:
            continue
        return True
    return False


def _required_authority(action: str) -> Optional[str]:
    return ACTION_AUTHORITY.get((action or "").lower())


def _resource_domains(actions: list) -> dict:
    """Aggregate observed resource types so the matrix has stable domains."""
    domains = {}
    for r in actions:
        rt = r.get("resource_type")
        if rt:
            domains.setdefault(rt, set())
    return domains


# ── Authorization core ───────────────────────────────────────────────────────
async def _resolve_actor(user=None, agent_id=None, agent_token=None) -> dict:
    """Resolve who is acting. Agents authenticate with their own token —
    they never borrow a human session."""
    if agent_id and agent_token:
        ident = await db.iam_identities.find_one({"id": agent_id})
        if not ident or ident.get("kind") not in ("ai_agent", "system_service"):
            raise HTTPException(401, "Unknown agent identity")
        if ident.get("status") == "suspended":
            raise HTTPException(403, "Agent identity is suspended")
        if ident.get("token_hash") != _token_hash(agent_token):
            raise HTTPException(401, "Invalid agent token")
        return {"identity": ident, "human": None, "agent": ident}
    if user is None:
        raise HTTPException(401, "Authentication required")
    ident = await _ensure_human_identity(user)
    return {"identity": ident, "human": user, "agent": None}


async def _can(identity_id: str, action: str, resource_type: str,
               resource_key: Optional[str] = None, owner_id: Optional[str] = None) -> tuple:
    """Return (allowed, delegation_id, reason).

    Resolution order:
      1. A matching active delegation covers the action on the resource.
      2. Humans with admin/exec role may act on any resource (platform role).
      3. The resource owner may always act on their own resource.
    Agents NEVER inherit authority — only explicit delegations apply.
    """
    required = _required_authority(action)
    if required is None:
        return False, None, f"Unknown action '{action}' — no authority mapping"

    now = _now()
    async for d in db.iam_delegations.find({
        "delegate_id": identity_id,
        "revoked_at": None,
    }).sort("created_at", -1):
        if not _delegation_active(d):
            continue
        if not _delegation_covers(d, resource_type, resource_key):
            continue
        if required in d.get("authorities", []):
            return True, d["id"], None

    ident = await db.iam_identities.find_one({"id": identity_id})
    if ident and ident.get("kind") == "human":
        role = ident.get("role", "")
        if role in ADMIN_ROLES:
            return True, None, "platform role"
        if owner_id and ident.get("owner_id") == owner_id:
            return True, None, "resource owner"

    return False, None, "outside delegation scope"


def _authority_by_domain(delegations: list, identity_id: str) -> dict:
    """Aggregate a delegate's effective authority per resource type."""
    by_domain = {}
    for d in delegations:
        if d.get("delegate_id") != identity_id:
            continue
        if not _delegation_active(d):
            continue
        domains = [r.get("resource_type") for r in d.get("resources", [])] if d.get("resources") else ["*"]
        for dom in domains or ["*"]:
            by_domain.setdefault(dom, set()).update(d.get("authorities", []))
    return {dom: sorted(auths) for dom, auths in by_domain.items()}


async def _identity_chain(identity_id: str, depth: int = 0) -> list:
    """Walk the creation chain (who created whom) upward to the root principal."""
    chain = []
    seen = set()
    current_id = identity_id
    while current_id and depth < 8 and current_id not in seen:
        seen.add(current_id)
        ident = await db.iam_identities.find_one({"id": current_id})
        if not ident:
            break
        chain.append(ident)
        current_id = ident.get("parent_id") or ident.get("created_by")
        if ident.get("kind") == "human":
            break
        depth += 1
    return chain


# ── Request models ───────────────────────────────────────────────────────────
class IdentityCreate(BaseModel):
    kind: str
    name: str
    description: str = ""
    parent_id: Optional[str] = None
    owner_id: Optional[str] = None
    purpose: str = ""


class IdentityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[str] = None


class ResourceCreate(BaseModel):
    resource_type: str
    resource_key: str
    title: str = ""
    owner_id: Optional[str] = None
    collaborators: List[dict] = []


class DelegationCreate(BaseModel):
    delegate_id: str
    authorities: List[str]
    resources: List[dict] = []          # [{resource_type, resource_key?}] — empty = all owned
    scope_all_owned: bool = False
    purpose: str = ""
    expires_at: Optional[str] = None    # ISO 8601 or null for no expiry
    revocable: bool = True
    owner_id: Optional[str] = None      # admin-only: delegate on behalf of this principal


class ActionRecord(BaseModel):
    action: str
    resource_type: str
    resource_key: Optional[str] = None
    note: str = ""


class ActionCheck(BaseModel):
    action: str
    resource_type: str
    resource_key: Optional[str] = None


# ── Endpoints: Identities ────────────────────────────────────────────────────
@router.get("/identities")
async def list_identities(kind: Optional[str] = None, q: Optional[str] = "",
                          actor: dict = Depends(_dep_current_user)):
    if not _is_admin(actor):
        raise HTTPException(403, "Admin access required for the identity registry")
    query = {}
    if kind:
        query["kind"] = kind
    rows = await db.iam_identities.find(query).sort("created_at", -1).to_list(500)
    if q:
        rows = [r for r in rows if q.lower() in (r.get("name", "") + " " + r.get("description", "")).lower()]
    # Merge in platform users as human identities (synced, never duplicated)
    humans = await db.users.find({}, {"_id": 0, "password_hash": 0, "email": 1,
                                      "full_name": 1, "role": 1, "is_active": 1, "id": 1}).to_list(2000)
    existing = {r.get("owner_id") for r in rows if r.get("kind") == "human"}
    for u in humans:
        if u.get("id") in existing:
            continue
        if q and q.lower() not in (u.get("full_name", "") + " " + u.get("email", "")).lower():
            continue
        rows.append({
            "id": "user:" + u.get("id", ""),
            "kind": "human",
            "name": u.get("full_name") or u.get("email"),
            "description": "Platform user",
            "owner_id": u.get("id"),
            "owner_kind": "self",
            "role": u.get("role"),
            "status": "active" if u.get("is_active", True) else "suspended",
            "email": u.get("email"),
            "created_at": None,
        })
    for r in rows:
        if r.get("token_hash"):
            r["has_token"] = True
            r.pop("token_hash", None)
    return {"identities": rows, "total": len(rows)}


@router.post("/identities")
async def create_identity(body: IdentityCreate, actor: dict = Depends(_dep_current_user)):
    if not _is_admin(actor):
        raise HTTPException(403, "Admin access required to register identities")
    if body.kind not in IDENTITY_KINDS:
        raise HTTPException(400, f"kind must be one of {IDENTITY_KINDS}")
    if body.kind == "human":
        raise HTTPException(400, "Human identities are synced from platform users")

    owner_id = body.owner_id or actor.id
    parent_id = body.parent_id
    if parent_id:
        parent = await db.iam_identities.find_one({"id": parent_id})
        if not parent:
            raise HTTPException(400, "parent_id does not match a known identity")

    token = None
    token_hash = None
    if body.kind in ("ai_agent", "system_service"):
        token = secrets.token_urlsafe(24)
        token_hash = _token_hash(token)

    doc = {
        "id": _uid(),
        "kind": body.kind,
        "name": body.name.strip(),
        "description": body.description,
        "purpose": body.purpose,
        "owner_id": owner_id,
        "owner_kind": "human",
        "parent_id": parent_id,          # authority chain link — NO permission inheritance
        "token_hash": token_hash,
        "status": "active",
        "created_at": _now(),
        "created_by": actor.id,
    }
    await db.iam_identities.insert_one(doc)
    doc.pop("token_hash", None)
    if token:
        doc["token"] = token  # shown exactly once — agent authenticates with this
    return {"identity": doc}


@router.get("/identities/{identity_id}")
async def get_identity(identity_id: str, actor: dict = Depends(_dep_current_user)):
    if not _is_admin(actor):
        raise HTTPException(403, "Admin access required")
    ident = await db.iam_identities.find_one({"id": identity_id})
    if not ident:
        raise HTTPException(404, "Identity not found")
    ident.pop("token_hash", None)
    delegations = await db.iam_delegations.find({"delegate_id": identity_id}).sort("created_at", -1).to_list(200)
    for d in delegations:
        d["active"] = _delegation_active(d)
    chain = await _identity_chain(identity_id)
    return {"identity": ident, "delegations": delegations, "chain": chain}


@router.patch("/identities/{identity_id}")
async def update_identity(identity_id: str, body: IdentityUpdate,
                          actor: dict = Depends(_dep_current_user)):
    if not _is_admin(actor):
        raise HTTPException(403, "Admin access required")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "Nothing to update")
    res = await db.iam_identities.update_one({"id": identity_id}, {"$set": updates})
    if not res.matched_count:
        raise HTTPException(404, "Identity not found")
    return {"ok": True}


@router.post("/identities/{identity_id}/rotate-token")
async def rotate_token(identity_id: str, actor: dict = Depends(_dep_current_user)):
    if not _is_admin(actor):
        raise HTTPException(403, "Admin access required")
    ident = await db.iam_identities.find_one({"id": identity_id})
    if not ident:
        raise HTTPException(404, "Identity not found")
    if ident.get("kind") not in ("ai_agent", "system_service"):
        raise HTTPException(400, "Only agents and services carry tokens")
    token = secrets.token_urlsafe(24)
    await db.iam_identities.update_one({"id": identity_id}, {"$set": {"token_hash": _token_hash(token)}})
    return {"token": token}


# ── Endpoints: Ownership ─────────────────────────────────────────────────────
@router.get("/resources")
async def list_resources(q: Optional[str] = "", owner_id: Optional[str] = None,
                         actor: dict = Depends(_dep_current_user)):
    if not _is_admin(actor):
        raise HTTPException(403, "Admin access required")
    query = {}
    if owner_id:
        query["owner_id"] = owner_id
    rows = await db.iam_resources.find(query).sort("created_at", -1).to_list(500)
    if q:
        rows = [r for r in rows if q.lower() in (r.get("title", "") + " " + r.get("resource_type", "")).lower()]
    return {"resources": rows, "total": len(rows)}


@router.post("/resources")
async def create_resource(body: ResourceCreate, actor: dict = Depends(_dep_current_user)):
    owner_id = body.owner_id or actor.id
    if not _is_admin(actor) and owner_id != actor.id:
        raise HTTPException(403, "You can only register resources you own")
    if not body.resource_type.strip() or not body.resource_key.strip():
        raise HTTPException(400, "resource_type and resource_key are required")
    doc = {
        "id": _uid(),
        "resource_type": body.resource_type.strip(),
        "resource_key": body.resource_key.strip(),
        "title": body.title,
        "owner_id": owner_id,
        "collaborators": body.collaborators,
        "created_at": _now(),
        "created_by": actor.id,
    }
    await db.iam_resources.insert_one(doc)
    return {"resource": doc}


@router.delete("/resources/{resource_id}")
async def delete_resource(resource_id: str, actor: dict = Depends(_dep_current_user)):
    if not _is_admin(actor):
        raise HTTPException(403, "Admin access required")
    res = await db.iam_resources.delete_one({"id": resource_id})
    if not res.deleted_count:
        raise HTTPException(404, "Resource not found")
    return {"ok": True}


# ── Endpoints: Delegations ───────────────────────────────────────────────────
@router.post("/delegations")
async def create_delegation(body: DelegationCreate, actor: dict = Depends(_dep_current_user)):
    if not body.authorities:
        raise HTTPException(400, "At least one authority is required")
    bad = [a for a in body.authorities if a not in AUTHORITIES]
    if bad:
        raise HTTPException(400, f"Invalid authorities: {bad}")
    delegate = await db.iam_identities.find_one({"id": body.delegate_id})
    if not delegate:
        raise HTTPException(404, "Delegate identity not found")

    principal_id = body.owner_id if (body.owner_id and _is_admin(actor)) else actor.id
    # The principal must own every specific resource they are delegating.
    for r in body.resources:
        owner = await db.iam_resources.find_one({
            "resource_type": r.get("resource_type"),
            "resource_key": r.get("resource_key"),
        })
        if not owner:
            raise HTTPException(400, f"Resource {r.get('resource_type')}:{r.get('resource_key')} is not registered — register ownership first")
        if owner["owner_id"] != principal_id and not _is_admin(actor):
            raise HTTPException(403, f"You do not own {r.get('resource_type')}:{r.get('resource_key')}")

    expires_at = None
    if body.expires_at:
        try:
            from datetime import datetime as _dt
            expires_at = _dt.fromisoformat(body.expires_at.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(400, "expires_at must be ISO 8601 (e.g. 2026-08-31T00:00:00Z)")

    doc = {
        "id": _uid(),
        "principal_id": principal_id,
        "principal_kind": "human",
        "delegate_id": body.delegate_id,
        "delegate_kind": delegate.get("kind"),
        "authorities": body.authorities,
        "resources": body.resources,
        "scope_all_owned": body.scope_all_owned,
        "purpose": body.purpose,
        "expires_at": _iso(expires_at),
        "revocable": body.revocable,
        "revoked_at": None,
        "revoked_by": None,
        "created_at": _now(),
        "created_by": actor.id,
    }
    await db.iam_delegations.insert_one(doc)
    doc["active"] = True
    return {"delegation": doc}


@router.get("/delegations")
async def list_delegations(delegate_id: Optional[str] = None, principal_id: Optional[str] = None,
                           active_only: bool = False,
                           actor: dict = Depends(_dep_current_user)):
    query = {}
    if not _is_admin(actor):
        # Non-admins only see their own grants: delegations they granted or
        # delegations granted to their own human identity.
        ident = await _ensure_human_identity(actor)
        query["$or"] = [{"principal_id": actor.id}, {"delegate_id": ident["id"]}]
    else:
        if delegate_id:
            query["delegate_id"] = delegate_id
        if principal_id:
            query["principal_id"] = principal_id
    if active_only:
        query["revoked_at"] = None
    rows = await db.iam_delegations.find(query).sort("created_at", -1).to_list(500)
    for d in rows:
        d["active"] = _delegation_active(d)
    return {"delegations": rows, "total": len(rows)}


@router.post("/delegations/{delegation_id}/revoke")
async def revoke_delegation(delegation_id: str, actor: dict = Depends(_dep_current_user)):
    d = await db.iam_delegations.find_one({"id": delegation_id})
    if not d:
        raise HTTPException(404, "Delegation not found")
    if d.get("principal_id") != actor.id and not _is_admin(actor):
        raise HTTPException(403, "Only the principal (or an admin) may revoke this delegation")
    if d.get("revoked_at"):
        return {"ok": True, "already_revoked": True}
    await db.iam_delegations.update_one({"id": delegation_id}, {
        "$set": {"revoked_at": _now(), "revoked_by": actor.id}
    })
    return {"ok": True, "revoked": delegation_id}


# ── Endpoints: Consent ("what have I authorized?") ───────────────────────────
@router.get("/consent")
async def my_consent(actor: dict = Depends(_dep_current_user)):
    ident = await _ensure_human_identity(actor)
    rows = await db.iam_delegations.find({"principal_id": actor.id}).sort("created_at", -1).to_list(500)
    out = []
    for d in rows:
        delegate = await db.iam_identities.find_one({"id": d.get("delegate_id")}) or {}
        d["active"] = _delegation_active(d)
        d["delegate_name"] = delegate.get("name") or d.get("delegate_id")
        d["delegate_kind"] = delegate.get("kind") or d.get("delegate_kind")
        out.append(d)
    return {"consent": out, "identity": ident}


# ── Endpoints: Action history + enforcement ──────────────────────────────────
@router.get("/actions")
async def list_actions(actor_id: Optional[str] = None, resource_type: Optional[str] = None,
                       allowed: Optional[bool] = None, limit: int = 100,
                       actor: dict = Depends(_dep_current_user)):
    query = {}
    if actor_id:
        query["actor_id"] = actor_id
    if resource_type:
        query["resource_type"] = resource_type
    if allowed is not None:
        query["allowed"] = allowed
    if not _is_admin(actor):
        # Non-admins see actions they performed or actions on resources they own.
        ident = await _ensure_human_identity(actor)
        owned = await db.iam_resources.find({"owner_id": actor.id}).to_list(2000)
        keys = {(r["resource_type"], r["resource_key"]) for r in owned}
        query["$or"] = [{"actor_id": ident["id"]},
                        {"$and": [{"resource_type": {"$in": [k[0] for k in keys] or ["__none__"]}},
                                  {"resource_key": {"$in": [k[1] for k in keys] or ["__none__"]}}]}]
    rows = await db.iam_actions.find(query).sort("created_at", -1).limit(min(max(limit, 1), 500)).to_list(500)
    return {"actions": rows, "total": len(rows)}


@router.post("/actions/check")
async def check_action(body: ActionCheck,
                       agent_id: Optional[str] = None, agent_token: Optional[str] = None,
                       actor: dict = Depends(_dep_optional_user)):
    """Non-mutating authorization check. Agents authenticate with
    X-Agent-ID / X-Agent-Token headers — a human session is not required."""
    who = await _resolve_actor(actor, agent_id, agent_token)
    allowed, delegation_id, reason = await _can(
        who["identity"]["id"], body.action, body.resource_type, body.resource_key)
    if not allowed and not reason:
        reason = "outside delegation scope"
    return {
        "allowed": allowed,
        "actor_id": who["identity"]["id"],
        "actor_kind": who["identity"]["kind"],
        "acting_for": who["identity"].get("owner_id"),
        "authorized_by": delegation_id,
        "reason": reason,
    }


@router.post("/actions")
async def record_action(body: ActionRecord,
                        agent_id: Optional[str] = None, agent_token: Optional[str] = None,
                        actor: dict = Depends(_dep_optional_user)):
    """Authorize + record an action. Denials are persisted with the reason."""
    who = await _resolve_actor(actor, agent_id, agent_token)
    ident = who["identity"]
    allowed, delegation_id, reason = await _can(
        ident["id"], body.action, body.resource_type, body.resource_key,
        owner_id=ident.get("owner_id"))
    if not allowed and not reason:
        reason = "outside delegation scope"

    doc = {
        "id": _uid(),
        "actor_id": ident["id"],
        "actor_kind": ident["kind"],
        "actor_name": ident.get("name"),
        "action": body.action,
        "resource_type": body.resource_type,
        "resource_key": body.resource_key,
        "note": body.note,
        "delegation_id": delegation_id,
        "allowed": allowed,
        "reason": reason,
        "created_at": _now(),
    }
    await db.iam_actions.insert_one(doc)

    if not allowed:
        raise HTTPException(403, {
            "detail": f"DENIED — {reason}",
            "allowed": False,
            "reason": reason,
            "authorized_by": delegation_id,
            "action_id": doc["id"],
        })
    return {"allowed": True, "authorized_by": delegation_id, "action_id": doc["id"], "reason": reason}


# ── Endpoints: The two transparency screens ──────────────────────────────────
@router.get("/who-can-do-what")
async def who_can_do_what(identity_id: Optional[str] = None,
                          actor: dict = Depends(_dep_current_user)):
    if not _is_admin(actor):
        raise HTTPException(403, "Admin access required")
    query = {}
    if identity_id:
        query["id"] = identity_id
    identities = await db.iam_identities.find(query).sort("created_at", -1).to_list(500)

    delegations = await db.iam_delegations.find({"revoked_at": None}).sort("created_at", -1).to_list(2000)
    resource_docs = await db.iam_resources.find({}).to_list(2000)

    out = []
    for ident in identities:
        if ident.get("kind") == "human" and ident.get("owner_id") == "self":
            continue
        my_delegations = [d for d in delegations if d.get("delegate_id") == ident["id"]]
        acting_for = []
        for d in my_delegations:
            if not _delegation_active(d):
                continue
            principal = await db.users.find_one({"id": d.get("principal_id")},
                                                {"_id": 0, "password_hash": 0, "full_name": 1, "email": 1}) or {}
            acting_for.append({
                "principal_id": d.get("principal_id"),
                "principal_name": principal.get("full_name") or principal.get("email") or d.get("principal_id"),
                "delegation_id": d["id"],
                "purpose": d.get("purpose", ""),
                "expires_at": _iso(d.get("expires_at")),
            })
        chain = await _identity_chain(ident["id"])
        authority = _authority_by_domain(my_delegations, ident["id"])
        # Only show domains that actually exist in the resource registry + wildcard
        domains = set(authority.keys())
        for r in resource_docs:
            if r.get("owner_id") == ident.get("owner_id"):
                domains.add(r["resource_type"])
        out.append({
            "identity": {k: v for k, v in ident.items() if k != "token_hash"},
            "owner_id": ident.get("owner_id"),
            "acting_for": acting_for,
            "authority_by_domain": authority,
            "domains": sorted(dom for dom in domains if dom != "*") or (["*"] if "*" in authority else []),
            "chain": [{ "id": c.get("id"), "name": c.get("name"), "kind": c.get("kind") } for c in chain],
        })
    return {"identities": out, "total": len(out)}


@router.get("/who-has-access-to-me")
async def who_has_access_to_me(user_id: Optional[str] = None,
                               actor: dict = Depends(_dep_current_user)):
    """Inverse view: which humans, agents, services, and applications can touch
    the caller's (or, for admins, a given user's) information."""
    target_id = user_id if (user_id and _is_admin(actor)) else actor.id
    ident = await db.iam_identities.find_one({"kind": "human", "owner_id": target_id})
    my_id = ident["id"] if ident else "user:" + target_id

    rows = await db.iam_delegations.find({"principal_id": target_id}).sort("created_at", -1).to_list(500)
    out = []
    for d in rows:
        delegate = await db.iam_identities.find_one({"id": d.get("delegate_id")}) or {}
        out.append({
            "delegation_id": d["id"],
            "identity_id": d.get("delegate_id"),
            "identity_name": delegate.get("name") or d.get("delegate_id"),
            "identity_kind": delegate.get("kind") or d.get("delegate_kind"),
            "authorities": d.get("authorities", []),
            "resources": d.get("resources", []),
            "scope_all_owned": bool(d.get("scope_all_owned")),
            "purpose": d.get("purpose", ""),
            "expires_at": _iso(d.get("expires_at")),
            "active": _delegation_active(d),
            "revocable": bool(d.get("revocable", True)),
        })
    return {"user_id": target_id, "access": out, "total": len(out)}


@router.get("/authority-chain")
async def authority_chain(identity_id: str, actor: dict = Depends(_dep_current_user)):
    if not _is_admin(actor):
        raise HTTPException(403, "Admin access required")
    chain = await _identity_chain(identity_id)
    if not chain:
        raise HTTPException(404, "Identity not found")
    return {"chain": [
        {"id": c.get("id"), "name": c.get("name"), "kind": c.get("kind"),
         "parent_id": c.get("parent_id"), "created_by": c.get("created_by")}
        for c in chain
    ]}
