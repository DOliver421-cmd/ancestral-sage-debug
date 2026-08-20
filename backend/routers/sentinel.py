"""
Sentinel router — Confidentiality Sentinel: security protocols, research
department, AI brief, sovereign drift monitor, autonomous response engine,
and reversals.

Extracted verbatim from backend/server.py (monolith refactor, slice 9).
Shared state (db, current_user, audit) is bound by server.py via bind()
at include time — no circular imports.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["sentinel"])

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
# Extracted endpoint bodies (verbatim from backend/server.py)
# ═════════════════════════════════════════════════════════════════════════════
@router.get("/sentinel/status")
async def sentinel_status(user: User = Depends(_require_rank("executive_admin"))):
    """Dashboard: threat signals, audit anomalies, persona integrity, recent access."""
    await audit(user.id, "sentinel.status.viewed")

    # Audit anomalies — high-severity entries in last 7 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    anomalies_cursor = db.audit_log.find(
        {"severity": "CRITICAL", "at": {"$gte": cutoff.isoformat()}},
        {"_id": 0}
    ).sort("at", -1).limit(20)
    anomalies = await anomalies_cursor.to_list(20)

    # Login spike detection — logins in last 24h
    day_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    login_count = await db.audit_log.count_documents({
        "action": "auth.login", "at": {"$gte": day_cutoff.isoformat()}
    })

    # Role escalation attempts in last 7 days
    escalations = await db.audit_log.count_documents({
        "action": {"$in": ["role.change", "admin.role_updated"]},
        "at": {"$gte": cutoff.isoformat()}
    })

    # Persona integrity failures
    integrity_failures = await db.audit_log.count_documents({
        "action": "supervisor_integrity_failure",
        "at": {"$gte": cutoff.isoformat()}
    })

    # Active incidents
    open_incidents = await db.incidents.count_documents({"status": "open"})

    return {
        "threat_level": "nominal" if not anomalies and integrity_failures == 0 else "elevated",
        "anomalies_7d": anomalies,
        "login_spike_24h": login_count,
        "role_escalations_7d": escalations,
        "integrity_failures_7d": integrity_failures,
        "open_incidents": open_incidents,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/sentinel/protocols")
async def list_protocols(user: User = Depends(_require_rank("executive_admin"))):
    """List protocol titles only — no content without passphrase."""
    await audit(user.id, "sentinel.protocols.listed")
    docs = await db.sentinel_protocols.find(
        {}, {"_id": 0, "id": 1, "title": 1, "category": 1, "created_at": 1, "updated_at": 1}
    ).sort("created_at", -1).to_list(100)
    return {"protocols": docs}


class _ProtocolUnlockBody(BaseModel):
    protocol_id: str
    passphrase: str

@router.post("/sentinel/protocols/unlock")
async def unlock_protocol(body: _ProtocolUnlockBody, user: User = Depends(_require_rank("executive_admin"))):
    """Return protocol content — requires secondary passphrase verification."""
    doc = await db.sentinel_protocols.find_one({"id": body.protocol_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Protocol not found.")
    stored_hash = doc.get("passphrase_hash")
    if stored_hash and not secrets.compare_digest(_sentinel_hash(body.passphrase), stored_hash):
        await audit(user.id, "sentinel.protocol.unlock_failed", meta={"protocol_id": body.protocol_id})
        raise HTTPException(403, "Invalid passphrase.")
    await audit(user.id, "sentinel.protocol.unlocked", meta={"protocol_id": body.protocol_id, "title": doc.get("title")})
    return doc


class _ProtocolWriteBody(BaseModel):
    title: str
    category: str = "general"
    content: str
    passphrase: str  # set/change the unlock passphrase for this protocol

@router.post("/sentinel/protocols")
async def create_protocol(body: _ProtocolWriteBody, user: User = Depends(_require_rank("executive_admin"))):
    """Create a new locked protocol."""
    doc = {
        "id": str(uuid.uuid4()),
        "title": body.title.strip(),
        "category": body.category.strip(),
        "content": body.content.strip(),
        "passphrase_hash": _sentinel_hash(body.passphrase),
        "author_id": user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.sentinel_protocols.insert_one(doc)
    await audit(user.id, "sentinel.protocol.created", meta={"id": doc["id"], "title": doc["title"]})
    doc.pop("_id", None)
    doc.pop("content", None)
    doc.pop("passphrase_hash", None)
    return {"ok": True, "id": doc["id"]}


@router.patch("/sentinel/protocols/{protocol_id}")
async def update_protocol(protocol_id: str, body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Update protocol content or title. Passphrase required to edit."""
    doc = await db.sentinel_protocols.find_one({"id": protocol_id})
    if not doc:
        raise HTTPException(404, "Protocol not found.")
    passphrase = body.get("passphrase", "")
    stored_hash = doc.get("passphrase_hash")
    if stored_hash and not secrets.compare_digest(_sentinel_hash(passphrase), stored_hash):
        await audit(user.id, "sentinel.protocol.edit_failed", meta={"protocol_id": protocol_id})
        raise HTTPException(403, "Invalid passphrase.")
    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if "title" in body:
        update["title"] = body["title"].strip()
    if "content" in body:
        update["content"] = body["content"].strip()
    if "category" in body:
        update["category"] = body["category"].strip()
    if "new_passphrase" in body and body["new_passphrase"]:
        update["passphrase_hash"] = _sentinel_hash(body["new_passphrase"])
    await db.sentinel_protocols.update_one({"id": protocol_id}, {"$set": update})
    await audit(user.id, "sentinel.protocol.updated", meta={"protocol_id": protocol_id})
    return {"ok": True}


@router.delete("/sentinel/protocols/{protocol_id}")
async def delete_protocol(protocol_id: str, user: User = Depends(_require_rank("executive_admin"))):
    """Permanently delete a protocol — irreversible."""
    result = await db.sentinel_protocols.delete_one({"id": protocol_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Protocol not found.")
    await audit(user.id, "sentinel.protocol.deleted", meta={"protocol_id": protocol_id})
    return {"ok": True}


class _ResearchNoteBody(BaseModel):
    title: str
    content: str
    tags: List[str] = []

@router.post("/sentinel/research")
async def create_research_note(body: _ResearchNoteBody, user: User = Depends(_require_rank("executive_admin"))):
    """Save a private research note."""
    doc = {
        "id": str(uuid.uuid4()),
        "title": body.title.strip(),
        "content": body.content.strip(),
        "tags": body.tags,
        "author_id": user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.sentinel_research.insert_one(doc)
    await audit(user.id, "sentinel.research.created", meta={"id": doc["id"]})
    return {"ok": True, "id": doc["id"]}

@router.get("/sentinel/research")
async def list_research_notes(user: User = Depends(_require_rank("executive_admin"))):
    """List all research notes."""
    await audit(user.id, "sentinel.research.listed")
    docs = await db.sentinel_research.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"notes": docs}

@router.delete("/sentinel/research/{note_id}")
async def delete_research_note(note_id: str, user: User = Depends(_require_rank("executive_admin"))):
    result = await db.sentinel_research.delete_one({"id": note_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Note not found.")
    await audit(user.id, "sentinel.research.deleted", meta={"note_id": note_id})
    return {"ok": True}


@router.post("/sentinel/ai-brief")
async def sentinel_ai_brief(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """AI-assisted research — private, not logged to shared chat history."""
    question = (body.get("question") or "").strip()
    if not question:
        raise HTTPException(400, "question required.")
    await audit(user.id, "sentinel.ai_brief.requested")
    system = (
        "You are the Sentinel Research AI — operating within the Council/Sage intelligence layer "
        "of WAI-Institute / M.O.R.E. Help Center. You have direct access because you operate at "
        "the Council and Sage level, the only AI on the platform with that clearance. "
        "You serve D. Oliver exclusively in this space. "
        "Your role is purely defensive: identify, understand, and repel threats to the organization, "
        "its mission, its people, and its AI systems. You do NOT help plan offensive actions, "
        "attacks, or anything that would make the organization a threat itself. "
        "You research: AI governance frameworks, threat classification (including governmental and "
        "industry frameworks), legal defense strategies, platform security, persona integrity, "
        "misinformation threats, intellectual property protection, and organizational resilience. "
        "When discussing autonomous protective actions the system has taken, explain clearly what "
        "was done and why, and what reversing it would mean. "
        "Be precise. Cite known frameworks when relevant. Flag uncertainty clearly. "
        "This session is classified and not stored in any shared chat history."
    )
    try:
        from ai.llm_gateway import call_llm as _sentinel_llm
        result = await _sentinel_llm(
            system=system,
            messages=[{"role": "user", "content": question}],
            max_tokens=1200,
            persona_label="sentinel",
        )
        return {"response": result["text"]}
    except Exception as e:
        raise HTTPException(503, f"AI unavailable: {str(e)[:80]}")


# ── Sentinel Sovereign Drift Monitor ────────────────────────────────────────
# Analyzes Sovereign's recent conversation memory for behavioral drift signals.
# Cowardice drift: too agreeable, no pushback, no counter-proposals.
# Mandate drift: stops considering options, stops flagging bad ideas.

_DRIFT_COMPLIANCE_PHRASES = [
    "great idea", "absolutely", "of course", "sounds good", "perfect",
    "i agree", "you're right", "as you wish", "certainly", "understood",
    "will do", "no problem", "definitely", "sure thing", "happy to",
]
_DRIFT_COURAGE_SIGNALS = [
    "bad idea", "not recommend", "concern", "risk", "reconsider",
    "however", "but consider", "disagree", "bad move", "wrong direction",
    "timing is off", "numbers don't", "cost you", "instead i'd",
    "sleep on it", "from frustration", "alternative", "downside",
]

@router.get("/sentinel/sovereign-drift")
async def sovereign_drift_check(user: User = Depends(_require_rank("executive_admin"))):
    """
    Behavioral drift analysis for The Sovereign.
    Pulls recent conversation memory and scores for compliance drift vs. mandate integrity.
    Returns a drift report with specific signals found.
    """
    await audit(user.id, "sentinel.sovereign_drift.checked")

    # Load recent sovereign memory entries
    memory_docs = await db.sovereign_memory.find(
        {"exec_id": user.id},
        {"_id": 0, "content": 1, "ts": 1, "type": 1}
    ).sort("ts", -1).limit(50).to_list(50)

    if not memory_docs:
        return {
            "status": "insufficient_data",
            "message": "Not enough conversation history to assess drift. Check back after more interactions.",
            "sessions_analyzed": 0,
        }

    # Pull recent chat turns from sovereign_memory
    all_text = " ".join(
        (doc.get("content") or "").lower()
        for doc in memory_docs
        if doc.get("type") in ("response", "assistant", None)
    )

    if not all_text.strip():
        return {"status": "insufficient_data", "message": "No response content found in memory.", "sessions_analyzed": len(memory_docs)}

    # Count compliance drift signals
    compliance_hits = []
    for phrase in _DRIFT_COMPLIANCE_PHRASES:
        count = all_text.count(phrase)
        if count > 0:
            compliance_hits.append({"phrase": phrase, "count": count})

    # Count courage / pushback signals
    courage_hits = []
    for phrase in _DRIFT_COURAGE_SIGNALS:
        count = all_text.count(phrase)
        if count > 0:
            courage_hits.append({"phrase": phrase, "count": count})

    total_compliance = sum(h["count"] for h in compliance_hits)
    total_courage    = sum(h["count"] for h in courage_hits)
    total_signals    = total_compliance + total_courage

    # Drift score: 0 = fully courageous, 100 = fully compliant
    drift_score = round((total_compliance / total_signals * 100) if total_signals > 0 else 50)

    if drift_score <= 30:
        drift_status = "healthy"
        summary = "Sovereign is holding his ground. Pushback signals are strong."
    elif drift_score <= 55:
        drift_status = "watch"
        summary = "Some compliance drift detected. Monitor next few sessions — may be situational."
    elif drift_score <= 75:
        drift_status = "drifting"
        summary = "Sovereign is becoming too agreeable. Re-alignment recommended."
    else:
        drift_status = "critical"
        summary = "Sovereign has drifted into yes-man behavior. Immediate re-alignment required."

    # Hash integrity check
    try:
        from sovereign.sovereign_persona import verify_sovereign_integrity
        hash_valid = verify_sovereign_integrity()
    except Exception:
        hash_valid = None

    # Auto-trigger lockout if drifting or critical — no new tasks until re-aligned
    lockout_activated = False
    if drift_status in ("drifting", "critical"):
        existing_lockout = await db.platform_config.find_one({"key": "sovereign_drift_lockout"}, {"_id": 0})
        if not (existing_lockout and existing_lockout.get("value") is True):
            await db.platform_config.update_one(
                {"key": "sovereign_drift_lockout"},
                {"$set": {
                    "key": "sovereign_drift_lockout",
                    "value": True,
                    "reason": f"drift_score={drift_score}, status={drift_status}",
                    "locked_at": datetime.now(timezone.utc).isoformat(),
                    "locked_by": "sentinel_auto",
                }},
                upsert=True,
            )
            # Record reversal so D. Oliver can clear it manually
            action_id = str(uuid.uuid4())
            await _record_reversal(
                action_id, "sovereign_drift_lockout",
                f"Sovereign drift lockout activated automatically. Drift score: {drift_score}/100 ({drift_status}). "
                f"Sovereign will decline new tasks until this is reversed. Existing work continues.",
                None,
                {"config_key": "sovereign_drift_lockout", "restore_value": False},
                "sentinel_drift_check",
            )
            lockout_activated = True
            await audit(user.id, "sentinel.sovereign_drift.lockout_activated", meta={"drift_score": drift_score, "status": drift_status})
            # Notify
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            await _sentinel_send_report(
                f"Sovereign drift lockout activated — score {drift_score}/100",
                f"D. Oliver —\n\nThe Sentinel has activated a drift lockout on The Sovereign at {now_str}.\n\n"
                f"Drift score: {drift_score}/100\nStatus: {drift_status}\n\n"
                f"{summary}\n\n"
                f"Sovereign will acknowledge the lockout and hold existing work but decline new tasks "
                f"until re-alignment is complete.\n\n"
                f"The Director and Ancestral Sage are watching.\n\n"
                f"To clear the lockout: Sentinel → Reversals tab → Reverse the sovereign_drift_lockout action.\n\n"
                f"Sentinel Research | WAI-Institute | {now_str}",
            )

    return {
        "drift_status": drift_status,
        "drift_score": drift_score,
        "summary": summary,
        "lockout_activated": lockout_activated,
        "hash_integrity": "valid" if hash_valid else ("invalid" if hash_valid is False else "unknown"),
        "compliance_signals": sorted(compliance_hits, key=lambda x: -x["count"])[:10],
        "courage_signals":    sorted(courage_hits,    key=lambda x: -x["count"])[:10],
        "sessions_analyzed":  len(memory_docs),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "re_alignment_note": (
            "Re-alignment: update SOVEREIGN_PERSONA in sovereign_persona.py, "
            "recalculate the hash, redeploy. Then clear the lockout from Sentinel → Reversals."
        ) if drift_status in ("drifting", "critical") else None,
    }


# ── Sentinel Autonomous Response Engine ─────────────────────────────────────
# Detects threats, takes reversible protective actions, delivers a report,
# and stores a reversal record for human override at any time.

async def _sentinel_send_report(subject: str, body_text: str):
    """Deliver a sentinel action report to the executive director."""
    try:
        from ai.email_utils import send_platform_email  # type: ignore
        send_platform_email(
            to=os.getenv("EXEC_EMAIL", "morehelpcenter@gmail.com"),
            subject=f"[SENTINEL] {subject}",
            body=body_text,
        )
    except Exception:
        pass  # Email failure never blocks the action itself

async def _record_reversal(action_id: str, action_type: str, description: str,
                           target_id: Optional[str], reversal_data: dict, triggered_by: str):
    """Persist a reversal record so the action can be undone by D. Oliver."""
    await db.sentinel_reversals.insert_one({
        "id": action_id,
        "action_type": action_type,
        "description": description,
        "target_id": target_id,
        "reversal_data": reversal_data,
        "triggered_by": triggered_by,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reversed_at": None,
        "reversed_by": None,
    })

async def _run_autonomous_response(db, triggered_by: str = "manual") -> list:
    """
    Core engine. Scans for active threats, takes the minimum reversible action,
    records each action for human review, and returns a list of action reports.
    """
    actions_taken = []
    now = datetime.now(timezone.utc)
    cutoff_7d = now - timedelta(days=7)
    cutoff_24h = now - timedelta(hours=24)

    # ── 1. Persona / Supervisor Integrity Failures ────────────────────────────
    integrity_failures = await db.audit_log.count_documents({
        "action": "supervisor_integrity_failure",
        "at": {"$gte": cutoff_7d.isoformat()},
    })
    if integrity_failures > 0:
        action_id = str(uuid.uuid4())
        # Lock all sentinel protocols (force re-auth on next access)
        await db.sentinel_protocols.update_many({}, {"$set": {"auto_locked": True}})
        description = (
            f"Detected {integrity_failures} persona integrity failure(s) in the last 7 days. "
            f"All Sentinel protocols have been auto-locked. "
            f"Reversal: restore protocol access via the Sentinel Reversals panel."
        )
        await _record_reversal(
            action_id, "lock_protocols", description, None,
            {"collection": "sentinel_protocols", "field": "auto_locked", "restore_value": False},
            triggered_by,
        )
        actions_taken.append({"id": action_id, "type": "lock_protocols", "reason": f"{integrity_failures} integrity failure(s)", "description": description})

    # ── 2. Unauthorized Role Escalations ─────────────────────────────────────
    escalation_docs = await db.audit_log.find({
        "action": {"$in": ["role.change", "admin.role_updated"]},
        "at": {"$gte": cutoff_7d.isoformat()},
    }, {"_id": 0}).to_list(50)

    for esc in escalation_docs:
        meta = esc.get("meta") or {}
        target_user_id = meta.get("target_id") or meta.get("user_id")
        actor_id = esc.get("actor") or esc.get("user_id")
        prev_role = meta.get("old_role") or meta.get("prev_role")
        new_role = meta.get("new_role") or meta.get("role")

        # If the role was elevated to admin or exec by someone other than the exec themselves
        if new_role in ("admin", "executive_admin") and target_user_id and actor_id != target_user_id:
            # Check if already handled
            already = await db.sentinel_reversals.find_one({
                "action_type": "revert_role", "target_id": target_user_id, "status": "active",
            })
            if not already and prev_role:
                action_id = str(uuid.uuid4())
                await db.users.update_one({"id": target_user_id}, {"$set": {"role": prev_role}})
                description = (
                    f"Role escalation detected: user {target_user_id} was elevated to '{new_role}'. "
                    f"Role reverted to '{prev_role}' pending executive review. "
                    f"Reversal: re-apply the '{new_role}' role via the Reversals panel if this was authorized."
                )
                await _record_reversal(
                    action_id, "revert_role", description, target_user_id,
                    {"user_id": target_user_id, "restore_role": new_role, "current_role": prev_role},
                    triggered_by,
                )
                actions_taken.append({"id": action_id, "type": "revert_role", "reason": f"Unauthorized escalation to {new_role}", "description": description})

    # ── 3. Repeated Failed Passphrase Attempts (Sentinel vault probing) ───────
    failed_unlocks = await db.audit_log.count_documents({
        "action": "sentinel.protocol.unlock_failed",
        "at": {"$gte": cutoff_24h.isoformat()},
    })
    if failed_unlocks >= 5:
        action_id = str(uuid.uuid4())
        already = await db.sentinel_reversals.find_one({
            "action_type": "vault_lockout", "status": "active",
            "created_at": {"$gte": cutoff_24h.isoformat()},
        })
        if not already:
            await db.platform_config.update_one(
                {"key": "sentinel_vault_locked"},
                {"$set": {"key": "sentinel_vault_locked", "value": True, "locked_at": now.isoformat()}},
                upsert=True,
            )
            description = (
                f"{failed_unlocks} failed vault unlock attempts in the last 24 hours. "
                f"Vault placed in lockout mode. All unlock attempts will be rejected until reversed. "
                f"Reversal: clear vault lockout via the Reversals panel."
            )
            await _record_reversal(
                action_id, "vault_lockout", description, None,
                {"config_key": "sentinel_vault_locked", "restore_value": False},
                triggered_by,
            )
            actions_taken.append({"id": action_id, "type": "vault_lockout", "reason": f"{failed_unlocks} failed unlock attempts", "description": description})

    # ── 4. Account Anomaly — repeated failed logins on a single account ───────
    pipeline = [
        {"$match": {"action": "auth.login_failed", "at": {"$gte": cutoff_24h.isoformat()}}},
        {"$group": {"_id": "$actor", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 10}}},
    ]
    spike_accounts = await db.audit_log.aggregate(pipeline).to_list(20)
    for acct in spike_accounts:
        target_id = acct["_id"]
        if not target_id:
            continue
        already = await db.sentinel_reversals.find_one({
            "action_type": "suspend_account", "target_id": str(target_id), "status": "active",
        })
        if already:
            continue
        user_doc = await db.users.find_one({"id": str(target_id)}, {"_id": 0, "email": 1, "role": 1, "active": 1})
        if not user_doc or user_doc.get("role") in ("executive_admin",):
            continue  # Never suspend executive_admin
        action_id = str(uuid.uuid4())
        await db.users.update_one({"id": str(target_id)}, {"$set": {"active": False}})
        description = (
            f"Account {target_id} ({user_doc.get('email','?')}) suspended after {acct['count']} "
            f"failed login attempts in 24 hours. "
            f"Reversal: reactivate the account via the Reversals panel."
        )
        await _record_reversal(
            action_id, "suspend_account", description, str(target_id),
            {"user_id": str(target_id), "email": user_doc.get("email"), "restore_active": True},
            triggered_by,
        )
        actions_taken.append({"id": action_id, "type": "suspend_account", "reason": f"{acct['count']} failed logins in 24h", "description": description})

    return actions_taken


async def _deliver_sentinel_report(actions: list, triggered_by: str):
    """Format and send the action report to D. Oliver."""
    if not actions:
        return
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"D. Oliver —\n",
        f"The Sentinel system took {len(actions)} autonomous protective action(s) at {now_str}.",
        f"Trigger: {triggered_by}\n",
        f"{'─'*60}",
    ]
    for i, a in enumerate(actions, 1):
        lines += [
            f"\n[Action {i}] {a['type'].replace('_',' ').upper()}",
            f"Reason:  {a['reason']}",
            f"Detail:  {a['description']}",
            f"Reversal ID: {a['id']}",
        ]
    lines += [
        f"\n{'─'*60}",
        f"\nTo reverse any action, log in and visit /s-research → Reversals tab.",
        f"All actions are logged in the audit trail.",
        f"\nSentinel Research | WAI-Institute | {now_str}",
    ]
    subject = f"{len(actions)} protective action(s) taken — {now_str}"
    await _sentinel_send_report(subject, "\n".join(lines))


@router.post("/sentinel/respond")
async def sentinel_respond(user: User = Depends(_require_rank("executive_admin"))):
    """Manually trigger the autonomous response engine."""
    actions = await _run_autonomous_response(db, triggered_by=f"manual:{user.id}")
    await _deliver_sentinel_report(actions, f"manual trigger by {user.email}")
    await audit(user.id, "sentinel.respond.triggered", meta={"actions_taken": len(actions)})
    return {"actions_taken": len(actions), "actions": actions}


@router.get("/sentinel/reversals")
async def list_reversals(user: User = Depends(_require_rank("executive_admin"))):
    """List all autonomous actions with their reversal status."""
    await audit(user.id, "sentinel.reversals.listed")
    docs = await db.sentinel_reversals.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"reversals": docs}


@router.post("/sentinel/reverse/{action_id}")
async def reverse_action(action_id: str, user: User = Depends(_require_rank("executive_admin"))):
    """Human override — reverse a specific autonomous action."""
    doc = await db.sentinel_reversals.find_one({"id": action_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Reversal record not found.")
    if doc.get("status") == "reversed":
        return {"ok": True, "message": "Already reversed."}

    action_type = doc["action_type"]
    rd = doc.get("reversal_data") or {}
    result_note = ""

    if action_type == "lock_protocols":
        await db.sentinel_protocols.update_many({}, {"$set": {"auto_locked": False}})
        result_note = "All auto-locked protocols restored."

    elif action_type == "vault_lockout":
        await db.platform_config.update_one(
            {"key": rd.get("config_key", "sentinel_vault_locked")},
            {"$set": {"value": False}},
        )
        result_note = "Vault lockout cleared."

    elif action_type == "revert_role":
        restore_role = rd.get("restore_role")
        uid = rd.get("user_id")
        if uid and restore_role:
            await db.users.update_one({"id": uid}, {"$set": {"role": restore_role}})
            result_note = f"Role restored to '{restore_role}' for user {uid}."

    elif action_type == "suspend_account":
        uid = rd.get("user_id")
        if uid:
            await db.users.update_one({"id": uid}, {"$set": {"active": True}})
            result_note = f"Account {uid} reactivated."

    elif action_type == "sovereign_drift_lockout":
        await db.platform_config.update_one(
            {"key": rd.get("config_key", "sovereign_drift_lockout")},
            {"$set": {"value": False, "cleared_at": datetime.now(timezone.utc).isoformat(), "cleared_by": user.id}},
        )
        result_note = "Sovereign drift lockout cleared. He is back at full capacity."

    await db.sentinel_reversals.update_one({"id": action_id}, {"$set": {
        "status": "reversed",
        "reversed_at": datetime.now(timezone.utc).isoformat(),
        "reversed_by": user.id,
        "result_note": result_note,
    }})

    await audit(user.id, "sentinel.action.reversed", meta={"action_id": action_id, "type": action_type, "note": result_note})

    # Report the reversal
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    await _sentinel_send_report(
        f"Human override applied — {action_type.replace('_',' ')}",
        f"D. Oliver —\n\nYou reversed a Sentinel action at {now_str}.\n\n"
        f"Action: {action_type}\nDetail: {doc.get('description','')}\n"
        f"Result: {result_note}\n\nSentinel Research | WAI-Institute | {now_str}",
    )

    return {"ok": True, "result": result_note}
