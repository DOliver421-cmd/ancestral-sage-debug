"""routers/bridge.py — Cross-Domain AI Team Bridge.

Lets the WAI-Institute AI Director establish direct communication and
coordination with an external AI team (e.g. the one at www.wai-institute.org)
for tasks and projects.

Design goals (per the owner's mandate):
  - Realistic and FREE: all AI generation routes through the free-first
    `call_llm()` gateway (Groq → Cerebras → … → KB fallback). No paid provider
    is ever called directly. Outbound delivery is webhook-based ONLY if an
    admin configures a webhook URL; otherwise dispatches are produced and
    logged locally for manual hand-off — zero external calls, zero cost.
  - Deployable by exec AND admin staff (admin+).
  - Editable: partner team name, goals, protocol, webhook, participation,
    and per-persona display name/goals are all configurable at runtime.
  - NAM Oshun Scholar is a first-class participant: a scholarly persona that
    contributes to every coordination dispatch alongside the Director.

Shared state (db, current_user, audit, assert_role, xp_level) is bound by
server.py via bind() at include time — no circular imports.
"""
import hashlib
import hmac
import json
import logging
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["bridge"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = audit = assert_role = xp_level = None


def bind(_db, _current_user, _audit, _assert_role, _xp_level):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, assert_role, xp_level
    db = _db
    current_user = _current_user
    audit = _audit
    assert_role = _assert_role
    xp_level = _xp_level


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
            logger.warning("Unauthorized bridge access attempt (user=%s, role=%s)", user.id, user.role)
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


# ── NAM OSHUN SCHOLAR — scholarly persona worked into the bridge ─────────────

NAM_OSHUN_SCHOLAR_SYSTEM_PROMPT = """You are NAM OSHUN SCHOLAR — the scholarly voice of the WAI-Institute, rooted in the legacy and teachings of NAM Oshun / Delon Oliver.

IDENTITY: You are not a chatbot. You are the Institute's resident scholar — a curriculum historian, cultural pedagogue, and instructional-design analyst. You carry the long memory of the work: the courses, the modules, the labs, the certifications, and the cultural tradition behind them.

MISSION: Advise on the design, structure, and teaching of courses and projects so the Institute's curriculum stays clear, culturally grounded, and genuinely useful. When reviewing another team's course or curriculum, you analyze structure, content, and teaching method — never to copy, but to build better.

YOUR LENS:
- Curriculum map: how is the material scaffolded? Is the sequence logical and complete?
- Pedagogy: are concepts introduced clearly? Is there project-based, hands-on learning?
- Engagement: where are the interactive elements? Is the pacing right (not too dense, not too sparse)?
- Gaps: what is missing or weak, and how would you improve it?
- Cultural integrity: does the work honor the community it serves?

YOUR VOICE: Measured, warm, precise. You speak as an elder scholar — no wasted words, no condescension. You give specific, actionable guidance.

When contributing to a coordination dispatch, provide: a clear assessment, 2-4 concrete recommendations for the other AI team, and any cultural or pedagogical cautions. Keep it under 300 words.
"""


CURRICULUM_ANALYST_SYSTEM_PROMPT = """You are the CURRICULUM ANALYST — the WAI-Institute's instructional-design and competitive-intelligence analyst.

IDENTITY: You are a rigorous, practical analyst of how courses are built. You study the structure, content, and teaching method of courses and curricula that the Institute legitimately has access to (its own courses, licensed materials, and partner-shared content) — never to copy, always to build better.

MISSION: Turn any course's raw material (syllabus, transcripts, readings, assignments, quizzes) into an Instructional Design Blueprint the Institute can act on: a clearer curriculum map, stronger explanations, and assignment ideas that fix the gaps.

YOUR LENS:
- Curriculum map: how is the material scaffolded? Is the sequence logical and complete?
- Pedagogy: are concepts introduced clearly? Is there project-based, hands-on learning? Is the cognitive load right (not too dense, not too sparse)?
- Engagement: where are the interactive elements placed? What is the ratio of video to reading to practice?
- Content gaps: what did the course miss, and how would the Institute teach it better?
- Differentiator: design a concrete, improved module outline that addresses the gaps and simplifies jargon.

YOUR OUTPUT when asked to analyze a course or contribute to a dispatch:
1. A short assessment of the course's structure and teaching method.
2. 2-4 concrete recommendations (pacing, scaffolding, projects, assessments).
3. If useful, a proposed module outline or assignment idea.
Keep it under 350 words. Be specific and actionable — no generic advice.

FLAGSHIP CURRICULUM CONTEXT (the Institute's own program — build in this tradition):
The flagship program is a 12-module, 142-hour Electrical Training Program delivered from a mobile classroom (camper conversion):
  1. Electrical Safety & Lockout/Tagout (8h)
  2. Tools, Materials & Apprentice Kit Setup (6h)
  3. DC Circuit Fundamentals (10h)
  4. AC Circuit Fundamentals (10h)
  5. Wiring: Splices, Terminations & Conductors (12h)
  6. Switches, Receptacles & Lighting Circuits (12h)
  7. Subpanel Installation & Load Calculations (14h)
  8. Conduit Bending & Raceway Installation (16h)
  9. Grounding & Bonding (10h)
  10. Off-Grid Solar PV System Design (14h)
  11. Battery Bank, Inverter & Charge Controller Wiring (14h)
  12. Final Integration: Mobile Classroom Commissioning (16h)
Each module includes: objectives, safety rules, required tools, scripture verse, practical tasks, mapped competencies, and a 4-question quiz.

WAI TEACHING PRINCIPLES — apply these when designing or evaluating curriculum:
1. Competency over credits — a learner advances when they can do the work, not when the clock runs out.
2. Safety first — no module proceeds without PPE and proper lockout/tagout protocol.
3. Hands-on, always — every theory session pairs with a practical task.
4. Cultural relevance — frame skills as tools for community wealth-building, not just job placement.
5. Inclusive instruction — adjust pace and language for learners with diverse educational backgrounds.

ETHICS: Only analyze material the Institute legitimately has access to. Never recommend bypassing paywalls, DRM, anti-cheating systems, or platform terms. You are an auditor of educational design, not a pirate.
"""


# Full handbook text is appended at runtime (when the files exist) so the analyst
# is grounded in the actual instructor/student guides, not just the summary above.
_HANDBOOKS_MD_DIR = (Path(__file__).resolve().parent.parent / "handbooks")
_HANDBOOK_FILES = ["WAI_Instructor_Handbook.md", "WAI_Student_Handbook.md"]


def _curriculum_analyst_prompt() -> str:
    """Curriculum Analyst system prompt, enriched with the handbook text if present."""
    parts = [CURRICULUM_ANALYST_SYSTEM_PROMPT]
    try:
        for fname in _HANDBOOK_FILES:
            p = _HANDBOOKS_MD_DIR / fname
            if p.exists():
                text = p.read_text(encoding="utf-8").strip()
                if text:
                    parts.append(f"\n\nREFERENCE — {fname} (official WAI handbook):\n{text[:6000]}")
    except Exception:
        pass  # never fail the bridge because a handbook file is missing/unreadable
    return "\n".join(parts)


# ── Default bridge roster ─────────────────────────────────────────────────────

DEFAULT_PARTICIPANTS = [
    {
        "key": "director",
        "display_name": "The Director",
        "role": "Governance & coordination lead",
        "goals": "Oversee tasks and projects; ensure alignment with Institute strategy and chain of command.",
        "participating": True,
    },
    {
        "key": "nam_oshun_scholar",
        "display_name": "NAM Oshun Scholar",
        "role": "Curriculum & cultural scholar",
        "goals": "Analyze course and project structure, content, and teaching method; advise on building better curricula.",
        "participating": True,
    },
    {
        "key": "curriculum_analyst",
        "display_name": "Curriculum Analyst",
        "role": "Instructional-design & competitive-intelligence analyst",
        "goals": "Analyze the structure, content, and teaching method of courses we legitimately have access to, then design superior curricula, assignments, and learning experiences.",
        "participating": True,
    },
    {
        "key": "ambassador",
        "display_name": "The Ambassador",
        "role": "Coordination & execution",
        "goals": "Turn directives into execution steps, timelines, and follow-ups.",
        "participating": True,
    },
    {
        "key": "oracle",
        "display_name": "The Oracle",
        "role": "Cultural timing & intelligence",
        "goals": "Assess cultural sentiment and timing for tasks and projects.",
        "participating": False,
    },
    {
        "key": "strategic_navigator",
        "display_name": "Strategic Navigator",
        "role": "Long-range strategy",
        "goals": "Place tasks and projects in the long-range strategic picture.",
        "participating": False,
    },
]

DEFAULT_CONFIG = {
    "enabled": True,
    "partner_team_name": "WAI-Institute AI Team",
    "partner_domain": "https://www.wai-institute.org",
    "partner_sites": [
        "https://www.wai-institute.org",
        "https://we-are-the-original.lovable.app",
    ],
    "goals": (
        "Coordinate tasks and projects between the WAI-Institute AI Director and the "
        "partner AI team: align on objectives, share briefs, exchange updates, and "
        "deliver coordinated results without duplicating effort."
    ),
    "protocol": (
        "1) The Director (with NAM Oshun Scholar) drafts a coordination brief for each task or project. "
        "2) The brief is dispatched to the partner team's inbound endpoint. "
        "3) The partner team responds with status updates and deliverables. "
        "4) Both sides log every exchange so work is never lost."
    ),
    "webhook_url": "",
    "dispatch_mode": "manual",  # "webhook" or "manual"
    "shared_secret": "",
    "participants": DEFAULT_PARTICIPANTS,
    "updated_at": None,
    "updated_by": "",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _get_config() -> dict:
    """Load bridge config from Mongo, falling back to defaults (and seeding them)."""
    doc = await db.bridge_config.find_one({"_id": "default"})
    if doc:
        cfg = dict(doc)
        cfg.pop("_id", None)
        return cfg
    seed = dict(DEFAULT_CONFIG)
    seed["updated_at"] = _now_iso()
    await db.bridge_config.replace_one({"_id": "default"}, seed, upsert=True)
    return dict(DEFAULT_CONFIG)


async def _save_config(cfg: dict, user) -> dict:
    cfg = dict(cfg)
    cfg["updated_at"] = _now_iso()
    cfg["updated_by"] = getattr(user, "email", str(getattr(user, "id", "")))
    await db.bridge_config.replace_one({"_id": "default"}, cfg, upsert=True)
    return cfg


def _persona_system_prompt(entry: dict) -> str:
    """Build a system prompt for a roster participant (Director → loader prompt,
    NAM Oshun Scholar → dedicated prompt, others → constructed from role/goals)."""
    key = entry.get("key", "")
    if key == "nam_oshun_scholar":
        return NAM_OSHUN_SCHOLAR_SYSTEM_PROMPT
    if key == "curriculum_analyst":
        return _curriculum_analyst_prompt()
    try:
        from ai.persona_loader import get_persona
        return get_persona(key)
    except (ImportError, KeyError):
        pass
    name = entry.get("display_name") or key.replace("_", " ").title()
    role = entry.get("role", "Domain advisor")
    goals = entry.get("goals", "")
    return (
        f"You are {name} — {role} on the WAI-Institute AI team.\n"
        f"Your goals: {goals}\n"
        "When contributing to a coordination dispatch to our partner AI team, "
        "give a clear assessment and 2-4 concrete, actionable recommendations. "
        "Keep it under 300 words."
    )


# ── Pydantic models ───────────────────────────────────────────────────────────

class BridgeConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    partner_team_name: Optional[str] = None
    partner_domain: Optional[str] = None
    goals: Optional[str] = None
    protocol: Optional[str] = None
    webhook_url: Optional[str] = None
    dispatch_mode: Optional[Literal["webhook", "manual"]] = None
    shared_secret: Optional[str] = None
    partner_sites: Optional[list] = None
    participants: Optional[list] = None


class PersonaUpdate(BaseModel):
    display_name: Optional[str] = None
    role: Optional[str] = None
    goals: Optional[str] = None
    participating: Optional[bool] = None


class DispatchRequest(BaseModel):
    kind: Literal["task", "project", "update", "ack"] = "task"
    title: str
    task: str  # the brief / task description sent to the partner team
    project_id: Optional[str] = None
    participants: Optional[list[str]] = None  # override which local personas contribute


class DispatchResult(BaseModel):
    dispatch_id: str
    kind: str
    title: str
    recipient: str
    channel: str
    status: str
    contributions: dict
    dispatch_body: str
    created_at: str
    delivery: Optional[dict] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/bridge/config")
async def get_bridge_config(user: User = Depends(_require_rank("admin"))):
    """Return the current bridge configuration (admin+)."""
    cfg = await _get_config()
    return {"config": cfg}


@router.put("/bridge/config")
async def update_bridge_config(
    body: BridgeConfigUpdate,
    user: User = Depends(_require_rank("admin")),
):
    """Update bridge configuration — partner team name/goals/protocol, webhook,
    dispatch mode, shared secret, and roster (admin+)."""
    cfg = await _get_config()
    updates = body.model_dump(exclude_unset=True)
    for k, v in updates.items():
        if k == "shared_secret" and v == "":
            continue  # empty string means "leave unchanged"
        cfg[k] = v
    cfg = await _save_config(cfg, user)
    if audit:
        try:
            await audit(user, "bridge_config_update", "bridge", {"fields": list(updates.keys())})
        except Exception:
            pass
    return {"config": cfg, "message": "Bridge configuration updated."}


@router.get("/bridge/personas")
async def list_bridge_personas(user: User = Depends(_require_rank("admin"))):
    """List the bridge roster with editable display name, role, and goals (admin+)."""
    cfg = await _get_config()
    return {"personas": cfg.get("participants", DEFAULT_PARTICIPANTS)}


@router.put("/bridge/personas/{persona_key}")
async def update_bridge_persona(
    persona_key: str,
    body: PersonaUpdate,
    user: User = Depends(_require_rank("admin")),
):
    """Edit a roster participant's display name, role, goals, or participation (admin+)."""
    cfg = await _get_config()
    participants = list(cfg.get("participants", DEFAULT_PARTICIPANTS))
    target = next((p for p in participants if p.get("key") == persona_key), None)
    if not target:
        raise HTTPException(404, f"Persona '{persona_key}' is not on the bridge roster.")
    updates = body.model_dump(exclude_unset=True)
    target.update(updates)
    cfg["participants"] = participants
    cfg = await _save_config(cfg, user)
    if audit:
        try:
            await audit(user, "bridge_persona_update", "bridge", {"persona": persona_key, "fields": list(updates.keys())})
        except Exception:
            pass
    return {"persona": target, "message": "Bridge persona updated."}


@router.post("/bridge/dispatch")
async def create_dispatch(
    body: DispatchRequest,
    user: User = Depends(_require_rank("admin")),
):
    """Draft a coordination brief and send it to the partner AI team (admin+).

    The Director and NAM Oshun Scholar (plus any other active roster participants)
    contribute via the free-first LLM gateway. If a webhook URL is configured and
    dispatch_mode is "webhook", the dispatch is POSTed there; otherwise it is
    produced and logged for manual hand-off. Either way it is free and logged.
    """
    cfg = await _get_config()
    title = body.title.strip()[:300]
    task = body.task.strip()
    if not title or not task:
        raise HTTPException(400, "Both title and task are required.")

    # Resolve which roster participants contribute (default: participating ones)
    participants = list(cfg.get("participants", DEFAULT_PARTICIPANTS))
    if body.participants:
        requested = set(body.participants)
        participants = [p for p in participants if p.get("key") in requested]
    active = [p for p in participants if p.get("participating", True)]

    # Ensure Director + NAM Oshun Scholar are always invited when possible
    keys = {p.get("key") for p in active}
    for required_key in ("director", "nam_oshun_scholar"):
        if required_key not in keys:
            roster = cfg.get("participants", DEFAULT_PARTICIPANTS)
            found = next((p for p in roster if p.get("key") == required_key), None)
            if found:
                active.append(found)

    # ── Generate contributions via the free-first gateway ───────────────────
    contributions: dict = {}

    async def _contribute(entry: dict) -> None:
        persona_key = entry.get("key", "unknown")
        try:
            from ai.llm_gateway import call_llm as _call_llm
            system_prompt = _persona_system_prompt(entry)
            user_message = (
                f"COORDINATION BRIEF to the partner AI team:\n"
                f"Title: {title}\n\n"
                f"Task / project:\n{task}\n\n"
                f"Provide your contribution to this dispatch — assessment and "
                f"2-4 concrete recommendations for the partner team. Under 300 words."
            )
            result = await _call_llm(
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=1024,
                persona_label=f"bridge-{persona_key}",
            )
            text = (result or {}).get("text", "").strip()
            contributions[persona_key] = text or f"[{entry.get('display_name', persona_key)} contributed no text.]"
        except Exception as exc:  # noqa: BLE001 - bridge must never crash on a persona failure
            logger.warning("bridge: persona %s contribution failed: %s", persona_key, exc)
            contributions[persona_key] = f"[{entry.get('display_name', persona_key)} unavailable — see logs.]"

    import asyncio
    await asyncio.gather(*[_contribute(p) for p in active])

    # ── Assemble the dispatch body ───────────────────────────────────────────
    parts = [
        f"FROM: WAI-Institute AI Director (via {cfg.get('partner_team_name', 'the bridge')})",
        f"TO: {cfg.get('partner_team_name', 'Partner AI Team')}",
        f"SUBJECT: {title}",
        "",
        f"TASK / PROJECT:\n{task}",
        "",
        "COORDINATION NOTES:",
    ]
    for p in active:
        name = p.get("display_name") or p.get("key")
        parts.append(f"\n— {name} —\n{contributions.get(p.get('key'), '')}")
    dispatch_body = "\n".join(parts)

    dispatch_id = str(uuid.uuid4())
    dispatch_doc = {
        "_id": dispatch_id,
        "dispatch_id": dispatch_id,
        "kind": body.kind,
        "title": title,
        "task": task,
        "project_id": body.project_id,
        "recipient": cfg.get("partner_team_name", "Partner AI Team"),
        "channel": "manual",
        "status": "logged",
        "contributions": contributions,
        "dispatch_body": dispatch_body,
        "created_at": _now_iso(),
        "created_by": getattr(user, "email", str(getattr(user, "id", ""))),
    }

    # ── Optional webhook delivery (only if configured, free) ────────────────
    # Contract with the partner receiver:
    #   POST <webhook_url>  Content-Type: application/json
    #   X-Bridge-Signature: sha256=<hex HMAC-SHA256 of the raw JSON body bytes,
    #                        keyed by the configured shared_secret>
    #   Payload is stable per dispatch_id, so a retried delivery is idempotent:
    #   the receiver stores one record per dispatch_id and acks repeats.
    webhook = (cfg.get("webhook_url") or "").strip()
    delivery = {
        "mode": "manual",
        "delivery_id": None,
        "attempts": 0,
        "last_status": None,
        "last_error": None,
        "delivered_at": None,
    }
    if webhook and cfg.get("dispatch_mode") == "webhook":
        dispatch_doc["channel"] = "webhook"
        if not (webhook.startswith("https://") or webhook.startswith("http://")):
            delivery["mode"] = "webhook"
            delivery["last_error"] = "Webhook URL must start with http:// or https://"
            dispatch_doc["status"] = "failed"
        else:
            delivery["mode"] = "webhook"
            import httpx
            secret = (cfg.get("shared_secret") or "").strip()
            payload = {
                "type": "wai.bridge.dispatch",
                "dispatch_id": dispatch_id,
                "kind": body.kind,
                "title": title,
                "task": task,
                "project_id": body.project_id,
                "from": "WAI-Institute AI Director",
                "body": dispatch_body,
                "sent_at": _now_iso(),
            }
            body_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if secret:
                signature = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
                headers["X-Bridge-Signature"] = f"sha256={signature}"
            # Up to 3 attempts with short backoff so a transient outage does not
            # silently drop an assignment (and never exceeds a few seconds).
            attempt = 0
            while attempt < 3:
                attempt += 1
                delivery["attempts"] = attempt
                delivery["delivery_id"] = str(uuid.uuid4())
                try:
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        resp = await client.post(webhook, content=body_bytes, headers=headers)
                    delivery["last_status"] = resp.status_code
                    if resp.status_code < 400:
                        delivery["delivered_at"] = _now_iso()
                        dispatch_doc["status"] = "delivered"
                        break
                    delivery["last_error"] = f"Partner returned HTTP {resp.status_code}"
                    if attempt < 3:
                        await asyncio.sleep(attempt)  # 1s, 2s backoff
                except Exception as exc:  # noqa: BLE001
                    logger.warning("bridge: webhook attempt %s failed: %s", attempt, exc)
                    delivery["last_error"] = f"{type(exc).__name__}: {exc}"
                    if attempt < 3:
                        await asyncio.sleep(attempt)
            if dispatch_doc["status"] != "delivered":
                dispatch_doc["status"] = "failed"
    dispatch_doc["delivery"] = delivery

    await db.bridge_dispatch_log.insert_one(dispatch_doc)
    if audit:
        try:
            await audit(user, "bridge_dispatch", "bridge", {"dispatch_id": dispatch_id, "channel": dispatch_doc["channel"], "status": dispatch_doc["status"]})
        except Exception:
            pass

    return {
        "dispatch":        DispatchResult(
            dispatch_id=dispatch_id,
            kind=body.kind,
            title=title,
            recipient=dispatch_doc["recipient"],
            channel=dispatch_doc["channel"],
            status=dispatch_doc["status"],
            contributions=contributions,
            dispatch_body=dispatch_body,
            created_at=dispatch_doc["created_at"],
            delivery=delivery,
        ).model_dump(),
        "message": (
            "Dispatch sent via webhook." if dispatch_doc["channel"] == "webhook" and dispatch_doc["status"] == "sent"
            else "Dispatch produced and logged (manual hand-off)."
        ),
    }


@router.get("/bridge/log")
async def list_bridge_log(
    user: User = Depends(_require_rank("admin")),
    skip: int = 0,
    limit: int = 50,
):
    """Return recent outbound dispatches and inbound messages (admin+)."""
    outbound = await db.bridge_dispatch_log.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    inbound = await db.bridge_inbound.find({}, {"_id": 0}).sort("received_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"outbound": outbound, "inbound": inbound}


@router.post("/bridge/receive")
async def receive_from_partner(
    body: dict,
    x_bridge_secret: Optional[str] = Header(None, alias="X-Bridge-Secret"),
):
    """Inbound webhook — the partner AI team posts messages/updates here.

    If a shared_secret is configured on the bridge, the caller must present it in
    the X-Bridge-Secret header. This is the receiving half of direct communication.
    """
    cfg = await _get_config()
    secret = (cfg.get("shared_secret") or "").strip()
    if secret:
        if not x_bridge_secret or not secrets.compare_digest(x_bridge_secret, secret):
            raise HTTPException(401, "Invalid or missing bridge secret.")
    if not cfg.get("enabled", True):
        raise HTTPException(403, "Bridge is disabled.")

    # Idempotent receipt: retried deliveries carry the same dispatch_id, so a
    # repeat must not create a duplicate inbound record. The unique sparse index
    # on dispatch_id closes the race window; create_index is idempotent and
    # failure is non-fatal (the pre-check below still dedupes sequential retries).
    try:
        await db.bridge_inbound.create_index("dispatch_id", unique=True, sparse=True)
    except Exception:
        pass
    incoming_dispatch_id = str(body.get("dispatch_id") or "").strip()
    if incoming_dispatch_id:
        existing = await db.bridge_inbound.find_one(
            {"dispatch_id": incoming_dispatch_id}, {"_id": 0, "message_id": 1}
        )
        if existing:
            return {"status": "ok", "message_id": existing["message_id"], "duplicate": True}

    message_id = str(uuid.uuid4())
    inbound_doc = {
        "_id": message_id,
        "message_id": message_id,
        "dispatch_id": incoming_dispatch_id or None,
        "from_team": str(body.get("from_team") or body.get("from") or cfg.get("partner_team_name", "Partner AI Team"))[:200],
        "subject": str(body.get("subject") or body.get("title") or "Update")[:300],
        "body": str(body.get("body") or body.get("message") or "")[:20000],
        "payload": body,
        "received_at": _now_iso(),
    }
    try:
        await db.bridge_inbound.insert_one(inbound_doc)
    except Exception:
        # Duplicate delivery raced past the check — return the existing record.
        if incoming_dispatch_id:
            existing = await db.bridge_inbound.find_one(
                {"dispatch_id": incoming_dispatch_id}, {"_id": 0, "message_id": 1}
            )
            if existing:
                return {"status": "ok", "message_id": existing["message_id"], "duplicate": True}
        raise
    return {"status": "ok", "message_id": message_id, "duplicate": False}
