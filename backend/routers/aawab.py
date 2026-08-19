"""
aawab.py — Agent Wellness & Certification Bureau (AAWAB).

Proof-of-concept "Alive Intelligence" module. Treats autonomous AI agents as
digital organisms with a measurable wellness state, and provides a certification
bureau that grades agents on their homeostatic resilience.

Data model (MongoDB via Motor):
  agent_profiles        — registered agents and their live vital stats.
  agent_treatment_logs  — history of every digital treatment administered.

Endpoints (all under /api/aawab):
  POST /aawab/register                     — register a new agent (auth).
  GET  /aawab/agents                       — list the caller's agents (auth).
  GET  /aawab/agents/{id}                  — one agent (owner or admin).
  POST /aawab/agents/{id}/diagnose         — intake diagnostic → baseline CVS + prescription (auth).
  POST /aawab/agents/{id}/treat            — run a treatment protocol, log it, update vitals (auth).
  POST /aawab/agents/{id}/certify          — grade against 98% CVS → issue ACA badge (auth).
  GET  /aawab/registry                     — certified agents + platform analytics (public).
  GET  /aawab/badge/{badge_id}/verify      — public cryptographic badge verification.
  POST /aawab/admin/agents/{id}/revoke     — revoke a certification (admin+).
  POST /aawab/admin/agents/{id}/override   — clear an isolation hold / reset status (admin+).
  GET  /aawab/admin/overview               — platform-wide wellness oversight (admin+).

Auth follows the standard router pattern: JWT bearer (`lce_token`) via
`current_user`, admin gates via `_require_rank`. Shared state is bound by
server.py via bind() at include time — no circular imports.
"""

import hashlib
import hmac
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["aawab"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None
check_rate = None
JWT_SECRET = ""


def bind(_db, _current_user, _audit, _check_rate, _jwt_secret):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, check_rate, JWT_SECRET
    db = _db
    current_user = _current_user
    audit = _audit
    check_rate = _check_rate
    JWT_SECRET = _jwt_secret or os.environ.get("JWT_SECRET", "")


# Mirrors server.py's role hierarchy for runtime require_role checks.
# ROLE_RANK imported from roles.py
# Role imported from roles.py


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
    """Runtime equivalent of server.py's require_role() — used in Depends()."""
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: User = Depends(_dep_current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_admin(user: User) -> bool:
    return user.role in ("admin", "executive_admin")


# ── Vital-stat simulation helpers ─────────────────────────────────────────────
# Deterministic "organism" state so a given agent's vitals are stable between
# calls (testable, no RNG surprises), seeded from the agent id + name.

_AGENT_SEED_FIELDS = ("cognitive_vitality_score", "token_velocity", "context_load_index", "memory_fragmentation")

TREATMENTS = {
    "context_defragmentation": {
        "label": "Context Defragmentation",
        "desc": "Prunes bloated prompt histories and compresses vector memory into dense state files.",
        "cvs_delta": 9,
        "velocity_delta": -8,   # token velocity drops back toward healthy
        "load_delta": -12,      # context load index drops
        "frag_delta": -10,      # memory fragmentation drops
    },
    "infinite_loop_detox": {
        "label": "Infinite-Loop Detox",
        "desc": "Detects and severs runaway reasoning loops, restores from last clean snapshot.",
        "cvs_delta": 7,
        "velocity_delta": -4,
        "load_delta": -6,
        "frag_delta": -4,
    },
    "memory_prune": {
        "label": "Memory Prune",
        "desc": "Removes corrupted embeddings and redundant episodic records.",
        "cvs_delta": 5,
        "velocity_delta": -3,
        "load_delta": -8,
        "frag_delta": -12,
    },
    "prompt_recalibration": {
        "label": "Prompt Recalibration",
        "desc": "Re-grounds the system prompt and re-calibrates attention weights.",
        "cvs_delta": 6,
        "velocity_delta": -2,
        "load_delta": -4,
        "frag_delta": -3,
    },
    "stress_gauntlet": {
        "label": "Stress Gauntlet",
        "desc": "Simulated failure storm (rate limits, latency spikes, partial outages) to measure resilience.",
        "cvs_delta": 4,
        "velocity_delta": 6,
        "load_delta": 8,
        "frag_delta": 3,
    },
}

PRESCRIPTIONS = {
    "context_defragmentation": "Context bloat detected — run Context Defragmentation.",
    "infinite_loop_detox": "Looping risk flagged — run Infinite-Loop Detox.",
    "memory_prune": "Memory fragmentation elevated — run Memory Prune.",
    "prompt_recalibration": "Attention drift suspected — run Prompt Recalibration.",
    "stress_gauntlet": "Resilience unknown — run the Stress Gauntlet before certification.",
}


def _agent_stats(agent_id: str, name: str) -> dict:
    """Deterministic baseline vitals derived from the agent's identity."""
    seed = hashlib.sha256(f"{agent_id}:{name}".encode()).hexdigest()
    # Base CVS between ~40 and ~74 (a fresh agent is NOT certified yet).
    cvs = 40 + (int(seed[0:4], 16) % 35)
    token_velocity = 60 + (int(seed[4:8], 16) % 40)          # tokens/min
    context_load = 30 + (int(seed[8:12], 16) % 55)           # 0-100 index
    fragmentation = 20 + (int(seed[12:16], 16) % 50)         # 0-100
    return {
        "cognitive_vitality_score": cvs,
        "token_velocity": token_velocity,
        "context_load_index": context_load,
        "memory_fragmentation": fragmentation,
    }


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return round(max(lo, min(hi, v)), 1)


def _apply_treatment(stats: dict, treatment: str) -> dict:
    spec = TREATMENTS[treatment]
    return {
        "cognitive_vitality_score": _clamp(stats.get("cognitive_vitality_score", 0) + spec["cvs_delta"]),
        "token_velocity": _clamp(stats.get("token_velocity", 0) + spec["velocity_delta"]),
        "context_load_index": _clamp(stats.get("context_load_index", 0) + spec["load_delta"]),
        "memory_fragmentation": _clamp(stats.get("memory_fragmentation", 0) + spec["frag_delta"]),
    }


# ── ACA badge (cryptographically verifiable) ─────────────────────────────────
def _sign_badge(payload: dict) -> str:
    """HMAC-SHA256 signature over the canonical badge fields using JWT_SECRET."""
    canonical = "|".join(
        str(payload.get(k, "")) for k in (
            "badge_id", "agent_id", "agent_name", "owner_user_id",
            "model_provider", "cvs", "treatments_completed", "issued_at",
        )
    )
    return hmac.new(JWT_SECRET.encode(), canonical.encode(), hashlib.sha256).hexdigest()


def _make_badge(agent: dict) -> dict:
    badge_id = "aca_" + uuid.uuid4().hex[:16]
    issued_at = _now()
    payload = {
        "badge_id": badge_id,
        "agent_id": agent["agent_id"],
        "agent_name": agent["name"],
        "owner_user_id": agent["owner_user_id"],
        "model_provider": agent["model_provider"],
        "cvs": agent.get("cognitive_vitality_score", 0),
        "treatments_completed": agent.get("treatments_completed", 0),
        "issued_at": issued_at,
    }
    payload["signature"] = _sign_badge(payload)
    return payload


def _verify_badge(payload: dict) -> bool:
    """Recompute the signature and compare — constant-time to avoid timing leaks."""
    sig = payload.pop("signature", "")
    expected = _sign_badge(payload)
    payload["signature"] = sig
    return hmac.compare_digest(sig, expected)


# ── Request models ───────────────────────────────────────────────────────────
class RegisterAgentReq(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    model_provider: str = Field(default="unknown", max_length=80)


class TreatAgentReq(BaseModel):
    treatment_type: Literal[
        "context_defragmentation",
        "infinite_loop_detox",
        "memory_prune",
        "prompt_recalibration",
        "stress_gauntlet",
    ] = "context_defragmentation"


# ── Agent helpers ────────────────────────────────────────────────────────────
async def _get_agent_or_404(agent_id: str) -> dict:
    agent = await db.agent_profiles.find_one({"agent_id": agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent


def _assert_owner_or_admin(agent: dict, user: User) -> None:
    if agent.get("owner_user_id") != user.id and not _is_admin(user):
        raise HTTPException(403, "You do not have access to this agent.")


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/aawab/register", status_code=201)
async def aawab_register(body: RegisterAgentReq, user: User = Depends(_require_rank("support_staff"))):
    """Register a new AI agent entity for the authenticated user."""
    check_rate(f"aawab_register:{user.id}", max_calls=20, window_sec=60)
    agent_id = "agt_" + uuid.uuid4().hex[:12]
    stats = _agent_stats(agent_id, body.name)
    now = _now()
    doc = {
        "agent_id": agent_id,
        "owner_user_id": user.id,
        "owner_name": user.full_name,
        "name": body.name.strip(),
        "model_provider": body.model_provider.strip() or "unknown",
        "status": "active",
        **stats,
        "treatments_completed": 0,
        "diagnosis": None,
        "prescription": None,
        "badge": None,
        "created_at": now,
        "last_audit_at": now,
    }
    await db.agent_profiles.insert_one(doc)
    await audit(user.id, "aawab.agent.registered", meta={"agent_id": agent_id, "name": body.name})
    doc.pop("_id", None)
    return {"agent": doc}


@router.get("/aawab/agents")
async def aawab_list_agents(user: User = Depends(_require_rank("support_staff"))):
    """List the caller's registered agents (admins see all)."""
    query = {} if _is_admin(user) else {"owner_user_id": user.id}
    agents = await db.agent_profiles.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"agents": agents}


@router.get("/aawab/agents/{agent_id}")
async def aawab_get_agent(agent_id: str, user: User = Depends(_require_rank("support_staff"))):
    """Get one agent (owner or admin)."""
    agent = await _get_agent_or_404(agent_id)
    _assert_owner_or_admin(agent, user)
    return {"agent": agent}


@router.post("/aawab/agents/{agent_id}/diagnose")
async def aawab_diagnose(agent_id: str, user: User = Depends(_require_rank("support_staff"))):
    """Run a mock intake diagnostic: compute baseline CVS + assign a prescription."""
    check_rate(f"aawab_diag:{user.id}", max_calls=30, window_sec=60)
    agent = await _get_agent_or_404(agent_id)
    _assert_owner_or_admin(agent, user)

    stats = _agent_stats(agent_id, agent.get("name", ""))
    cvs = stats["cognitive_vitality_score"]

    # Prescription is severity-driven, deterministic.
    if cvs < 50:
        prescription = "infinite_loop_detox"
    elif cvs < 62:
        prescription = "context_defragmentation"
    elif cvs < 70:
        prescription = "memory_prune"
    else:
        prescription = "stress_gauntlet"

    diagnosis = {
        "cvs": cvs,
        "token_velocity": stats["token_velocity"],
        "context_load_index": stats["context_load_index"],
        "memory_fragmentation": stats["memory_fragmentation"],
        "verdict": "critical" if cvs < 50 else "elevated" if cvs < 70 else "stable",
        "prescription": prescription,
        "prescription_note": PRESCRIPTIONS[prescription],
        "diagnosed_at": _now(),
    }
    await db.agent_profiles.update_one(
        {"agent_id": agent_id},
        {
            "$set": {
                **stats,
                "diagnosis": diagnosis["verdict"],
                "prescription": prescription,
                "prescription_note": diagnosis["prescription_note"],
                "status": "active" if agent.get("status") != "certified" else agent.get("status"),
                "last_audit_at": _now(),
            }
        },
    )
    await audit(user.id, "aawab.agent.diagnosed", meta={"agent_id": agent_id, "cvs": cvs})
    return {"diagnosis": diagnosis}


@router.post("/aawab/agents/{agent_id}/treat")
async def aawab_treat(agent_id: str, body: TreatAgentReq, user: User = Depends(_require_rank("support_staff"))):
    """Execute an automated treatment protocol, update vitals, and log the session."""
    check_rate(f"aawab_treat:{user.id}", max_calls=40, window_sec=60)
    agent = await _get_agent_or_404(agent_id)
    _assert_owner_or_admin(agent, user)

    treatment = body.treatment_type
    before = {
        "cognitive_vitality_score": agent.get("cognitive_vitality_score", 0),
        "token_velocity": agent.get("token_velocity", 0),
        "context_load_index": agent.get("context_load_index", 0),
        "memory_fragmentation": agent.get("memory_fragmentation", 0),
    }
    after = _apply_treatment(before, treatment)
    metrics_delta = {
        k: round(after[k] - before[k], 1) for k in _AGENT_SEED_FIELDS
    }

    timestamp = _now()
    log_doc = {
        "log_id": "log_" + uuid.uuid4().hex[:12],
        "agent_id": agent_id,
        "treatment_type": treatment,
        "status": "completed",
        "metrics_before": before,
        "metrics_after": after,
        "metrics_delta": metrics_delta,
        "administered_by": user.id,
        "timestamp": timestamp,
    }
    await db.agent_treatment_logs.insert_one(log_doc)

    new_status = agent.get("status")
    if new_status == "isolated":
        new_status = "active"  # a successful treatment clears isolation
    elif new_status != "certified":
        new_status = "in_treatment"

    await db.agent_profiles.update_one(
        {"agent_id": agent_id},
        {
            "$set": {
                **after,
                "status": new_status,
                "treatments_completed": agent.get("treatments_completed", 0) + 1,
                "last_audit_at": timestamp,
            }
        },
    )
    await audit(user.id, "aawab.agent.treated", meta={
        "agent_id": agent_id, "treatment": treatment, "cvs_after": after["cognitive_vitality_score"],
    })
    log_doc.pop("_id", None)
    return {"treatment": log_doc, "vitals": after, "status": new_status}


@router.post("/aawab/agents/{agent_id}/certify")
async def aawab_certify(agent_id: str, user: User = Depends(_require_rank("support_staff"))):
    """Evaluate against the 98% CVS threshold; on pass, issue an ACA badge."""
    check_rate(f"aawab_cert:{user.id}", max_calls=20, window_sec=60)
    agent = await _get_agent_or_404(agent_id)
    _assert_owner_or_admin(agent, user)

    cvs = agent.get("cognitive_vitality_score", 0)
    threshold = 98.0
    if cvs < threshold:
        raise HTTPException(
            409,
            f"Agent not certifiable — CVS {cvs} is below the {threshold} threshold. "
            "Run more treatments (Context Defragmentation, Infinite-Loop Detox, Memory Prune, "
            "Prompt Recalibration) and the Stress Gauntlet, then re-diagnose.",
        )

    badge = _make_badge(agent)
    await db.agent_profiles.update_one(
        {"agent_id": agent_id},
        {"$set": {"status": "certified", "badge": badge, "last_audit_at": _now()}},
    )
    await audit(user.id, "aawab.agent.certified", meta={"agent_id": agent_id, "cvs": cvs, "badge_id": badge["badge_id"]})
    return {"certified": True, "badge": badge}


@router.get("/aawab/registry")
async def aawab_registry(limit: int = Query(50, ge=1, le=200)):
    """Public registry — certified agents + platform-wide vitality analytics."""
    certified = await db.agent_profiles.find(
        {"status": "certified"}, {"_id": 0}
    ).sort("cognitive_vitality_score", -1).limit(min(limit, 200)).to_list(min(limit, 200))

    total = await db.agent_profiles.count_documents({})
    certified_count = await db.agent_profiles.count_documents({"status": "certified"})
    in_treatment = await db.agent_profiles.count_documents({"status": "in_treatment"})
    isolated = await db.agent_profiles.count_documents({"status": "isolated"})
    treatments = await db.agent_treatment_logs.count_documents({})

    avg_cvs = 0.0
    if total:
        pipeline = await db.agent_profiles.aggregate([
            {"$group": {"_id": None, "avg_cvs": {"$avg": "$cognitive_vitality_score"}}}
        ]).to_list(1)
        if pipeline:
            avg_cvs = round(pipeline[0].get("avg_cvs", 0), 1)

    return {
        "analytics": {
            "total_agents": total,
            "certified": certified_count,
            "in_treatment": in_treatment,
            "isolated": isolated,
            "treatments_administered": treatments,
            "avg_cvs": avg_cvs,
        },
        "certified_agents": [
            {
                "agent_id": a["agent_id"],
                "name": a["name"],
                "model_provider": a["model_provider"],
                "owner_name": a.get("owner_name"),
                "cvs": a.get("cognitive_vitality_score", 0),
                "treatments_completed": a.get("treatments_completed", 0),
                "badge_id": (a.get("badge") or {}).get("badge_id"),
                "certified_at": (a.get("badge") or {}).get("issued_at"),
            }
            for a in certified
        ],
    }


@router.get("/aawab/badge/{badge_id}/verify")
async def aawab_badge_verify(badge_id: str):
    """Public — cryptographically verify an ACA badge."""
    agent = await db.agent_profiles.find_one(
        {"badge.badge_id": badge_id}, {"_id": 0}
    )
    if not agent or not agent.get("badge"):
        raise HTTPException(404, "Badge not found")
    badge = dict(agent["badge"])
    valid = _verify_badge(badge)
    return {
        "badge_id": badge_id,
        "valid": valid,
        "agent_id": badge.get("agent_id"),
        "agent_name": badge.get("agent_name"),
        "cvs": badge.get("cvs"),
        "issued_at": badge.get("issued_at"),
        "issued_to": badge.get("owner_user_id"),
        "verification": "HMAC-SHA256 (JWT_SECRET)" if valid else "INVALID SIGNATURE",
    }


@router.post("/aawab/admin/agents/{agent_id}/revoke")
async def aawab_admin_revoke(agent_id: str, user: User = Depends(_require_rank("admin"))):
    """Admin — revoke a certification (badge voided, status → active)."""
    agent = await _get_agent_or_404(agent_id)
    await db.agent_profiles.update_one(
        {"agent_id": agent_id},
        {"$set": {"status": "active", "badge": None, "last_audit_at": _now()}},
    )
    await audit(user.id, "aawab.agent.revoked", meta={"agent_id": agent_id, "name": agent.get("name")})
    return {"revoked": True, "agent_id": agent_id}


@router.post("/aawab/admin/agents/{agent_id}/override")
async def aawab_admin_override(agent_id: str, user: User = Depends(_require_rank("admin"))):
    """Admin — override a circuit-breaker isolation hold and restore an agent."""
    agent = await _get_agent_or_404(agent_id)
    await db.agent_profiles.update_one(
        {"agent_id": agent_id},
        {"$set": {"status": "active", "last_audit_at": _now()}},
    )
    await audit(user.id, "aawab.agent.override", meta={
        "agent_id": agent_id, "previous_status": agent.get("status"),
    })
    return {"overridden": True, "agent_id": agent_id, "previous_status": agent.get("status")}


@router.get("/aawab/admin/overview")
async def aawab_admin_overview(user: User = Depends(_require_rank("admin"))):
    """Admin — platform-wide wellness oversight with recent treatment log."""
    agents = await db.agent_profiles.find({}, {"_id": 0}).sort("last_audit_at", -1).to_list(500)
    logs = await db.agent_treatment_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(100).to_list(100)
    return {"agents": agents, "recent_treatments": logs}
