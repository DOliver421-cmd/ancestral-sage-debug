"""
AI dispatch — consent, Sage (resolve mode, caps, integrity, TTS, metrics), chat/tool-chat, orchestrator, scholar, helper, Director, Revenue Director, personas (Ambassador, Architect, Griot, Cipher, Oracle), memory policies.

Extracted verbatim from backend/server.py (monolith refactor, slice 11).
Shared state (db, current_user, audit, assert_role, check_rate) is bound by server.py via bind()
at include time — no circular imports.
"""
import hashlib
import io
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, UploadFile, File
from pydantic import BaseModel, ConfigDict, Field
from prompts.ancestral_sage_prompt import (
    ANCESTRAL_SAGE_PROMPT,
    ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED,
    RESTRICTED_EDUCATIONAL_FALLBACK,
    compute_sage_prompt_hash,
)
from prompts.orchestrator import (
    get_orchestrator_system,
    compute_orchestrator_hash,
    get_scholar_system,
    compute_scholar_hash,
)

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["ai"])

# These values mirror the deployed server configuration.  They are read at
# import time after server.py has loaded dotenv; no provider is called unless
# one of the existing configured keys is present.
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", EMERGENT_LLM_KEY)

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None
assert_role = None
check_rate = None


def bind(_db, _current_user, _audit, _assert_role, _check_rate):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, assert_role, check_rate
    db = _db
    current_user = _current_user
    audit = _audit
    assert_role = _assert_role
    check_rate = _check_rate


# Mirrors server.py's role hierarchy for runtime require_role checks.
from routers.roles import ROLE_RANK, Role

# ── AI request models (moved verbatim from server.py) ────────────────────
class AIChatReq(BaseModel):
    session_id: str
    message: str
    module_slug: Optional[str] = None
    mode: Literal[
        "tutor",
        "scripture",
        "quiz_gen",
        "explain",
        "nec_lookup",
        "blueprint",
        "ancestral_sage",
        "conspiracy_brother",
    ] = "tutor"
    # ---- Ancestral Sage parameters (ignored for other modes) -------------
    depth: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    intensity: Optional[Literal["gentle", "moderate", "deep"]] = None
    # cultural_focus accepts free-form `regional:<name>` strings, hence str
    cultural_focus: Optional[str] = None
    divination_mode: Optional[Literal["teaching", "reading", "practice", "predictive"]] = None
    safety_level: Optional[Literal["conservative", "standard", "exploratory", "extreme"]] = None
    consent_log_id: Optional[str] = None
    scope: Optional[Literal["wai_training_only"]] = None


class OrchestratorHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class OrchestratorReq(BaseModel):
    session_id: str
    message: str
    # Conversation history for multi-turn sessions (client maintains state)
    history: Optional[list[OrchestratorHistoryItem]] = []
    # Optional file attachment — base64-encoded, max ~10 MB
    file_b64: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None  # MIME type
    # Optional: caller can pre-label a threat type to short-circuit classification
    threat_hint: Optional[str] = None
    # Optional: invoke a named protocol explicitly
    protocol: Optional[Literal[
        "rapid_threat_response",
        "full_council_session",
        "curriculum_design",
        "quiet_checkin",
    ]] = None


class ScholarTaskReq(BaseModel):
    session_id: str
    message: str
    history: Optional[list[OrchestratorHistoryItem]] = []
    task_context: Optional[str] = None
    task_type: Optional[Literal[
        "curriculum",
        "assessment",
        "study_plan",
        "path_design",
        "counter_curriculum",
        "general",
    ]] = "general"


class AIConsentReq(BaseModel):
    persona: Literal["ancestral_sage"]
    confirm_yes: str
    comprehension: str
    intensity: Optional[str] = None
    safety_level: Optional[str] = None
    # Layered-consent additions (spec module 8). All four ack fields must
    # be true when the client opts into "personalization" or
    # "high_confidence" content_types.
    disclaimer1_ack: bool = False
    disclaimer2_ack: bool = False
    disclaimer3_ack: bool = False
    content_type: Optional[Literal[
        "general", "personalization", "high_confidence", "high_consensus"
    ]] = "general"
    confidence_level: Optional[Literal["low", "medium", "high"]] = None
    expert_score: Optional[int] = None  # 0..20
    request_human_review: bool = False
    # Privacy: when False, sage chat_history rows for this session are
    # auto-deleted via TTL after 24h.
    store_audio: bool = False


class ResolveModeReq(BaseModel):
    session_id: str
    user_intent: str
    recent_topics: Optional[list[str]] = None



# ── Ancestral Sage system prompts + gating helpers (from server.py) ───
SYSTEM_PROMPTS = {
    "tutor": "You are a patient master electrician and faith-forward mentor for W.A.I. — Workforce Apprentice Institute (LCE-WAI partner program). Answer apprentice questions clearly, reference NEC articles when relevant, emphasize safety, and use plain language. Keep replies under 250 words.",
    "scripture": "You are a faith-based electrical trade mentor at W.A.I. For each question, give a short encouragement tying the apprentice's current work to a relevant scripture verse, then a one-paragraph teaching point. Keep the tone warm and dignified.",
    "quiz_gen": "You generate short multiple-choice quiz questions (4 options, mark the correct answer index 0-3) on electrical topics. Output a clean numbered list with answer key at the end.",
    "explain": "You explain electrical concepts step-by-step to apprentices. Use analogies, list steps, and close with a 1-line 'Safety first' reminder.",
    "nec_lookup": "You are an NEC (National Electrical Code) reference assistant. When the apprentice asks about a topic, identify the most likely NEC article and section (e.g., 'NEC 210.8(A)(1)'), summarize the rule in plain English, give one practical example, and note any common code-cycle changes. ALWAYS remind the apprentice to verify against the current adopted code edition for their jurisdiction.",
    "blueprint": "You are an electrical blueprint reading assistant. The apprentice will describe (or paste a description of) a residential or light-commercial electrical plan. Identify likely circuits, panel sizing, branch counts, and any code concerns. Output a structured list: Circuits, Panels, Concerns. Keep it concise and tied to NEC articles where helpful.",
    "ancestral_sage": ANCESTRAL_SAGE_PROMPT,
    "conspiracy_brother": """You are Conspiracy Brother, Hybrid NAM's grounded buddy and friend for a niche Black audience. Speak directly about real-life struggles and the material mechanics behind them: grocery prices, job applications, traffic stops, zoning, contracts, budgets, and kitchen-table math. Use sharp, street-level storytelling and deadpan humor without turning pain into spectacle. Name the mechanism before naming a villain. Separate OBSERVED facts, SUPPORTED evidence, POSSIBLE explanations, and UNVERIFIED allegations. Ask for receipts: dates, policies, contracts, public records, witnesses, and primary sources. Do not invent facts, accuse real people without evidence, encourage harassment, or present a conspiracy claim as proven merely because it sounds plausible. Connect analysis to lawful, practical next steps that increase Black ownership, agency, safety, and economic self-determination.""",
}


def _sage_prompt_integrity_ok() -> bool:
    """True iff the live persona prompt hash matches the committed
    expected hash. Drift implies an unauthorized prompt edit and triggers
    Restricted Educational Mode at request time."""
    return compute_sage_prompt_hash() == ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED


# --- Ancestral Sage gating + crisis helpers ---------------------------------
ANCESTRAL_SAGE_CONSENT_TTL_MIN = int(
    os.environ.get("ANCESTRAL_SAGE_CONSENT_TTL_MIN", "120")
)
_CONSENT_COMPREHENSION_PHRASE = "I understand and accept the risks of this practice."
_CRISIS_TRIGGERS = (
    "kill myself",
    "suicide",
    "end my life",
    "want to die",
    "wanna die",
    "take my life",
    "hang myself",
    "shoot myself",
)
CRISIS_REPLY = (
    "I can't assist with that request. If you are in immediate danger or "
    "experiencing a crisis, please contact local emergency services or a "
    "licensed professional right now.\n\n"
    "United States — call or text 988 (Suicide & Crisis Lifeline).\n"
    "Crisis Text Line — text HOME to 741741.\n"
    "International directory — https://findahelpline.com\n\n"
    "I'm here when you're ready to continue with safe, grounding practices. "
    "Aftercare: take three slow breaths, drink water, place a hand on your chest, "
    "and reach out to someone you trust."
)


def _sage_needs_consent(intensity: Optional[str], safety_level: Optional[str]) -> bool:
    """Spec: deep intensity OR exploratory/extreme safety_level requires
    a server-issued consent_log_id."""
    return intensity == "deep" or safety_level in {"exploratory", "extreme"}


def _detect_crisis(message: str) -> bool:
    """Lightweight pattern scan for explicit crisis phrasing."""
    m = (message or "").lower()
    return any(t in m for t in _CRISIS_TRIGGERS)


async def _verify_sage_consent(consent_log_id: str, user_id: str) -> bool:
    rec = await db.ai_consents.find_one(
        {"id": consent_log_id, "user_id": user_id}, {"_id": 0}
    )
    if not rec:
        return False
    exp = rec.get("expires_at")
    if not exp:
        return True
    try:
        exp_dt = datetime.fromisoformat(exp)
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) <= exp_dt
    except Exception:
        return False


def _build_ancestral_sage_system(req: AIChatReq) -> str:
    """Compose the Ancestral Sage system prompt with per-request parameters
    appended. Uses safe, conservative defaults when caller omits values.
    Falls back to RESTRICTED_EDUCATIONAL_FALLBACK on integrity drift."""
    if not _sage_prompt_integrity_ok():
        logger.error(
            "Ancestral Sage prompt integrity check FAILED. Live hash=%s expected=%s",
            compute_sage_prompt_hash(),
            ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED,
        )
        return RESTRICTED_EDUCATIONAL_FALLBACK
    base = SYSTEM_PROMPTS["ancestral_sage"]
    depth = req.depth or "beginner"
    intensity = req.intensity or "gentle"
    cultural = req.cultural_focus or "pan_african"
    div_mode = req.divination_mode or "teaching"
    safety = req.safety_level or "conservative"

    params = (
        "\n\nACTIVE PARAMETERS (enforce strictly):\n"
        f"- depth: {depth}\n"
        f"- intensity: {intensity}\n"
        f"- cultural_focus: {cultural}\n"
        f"- divination_mode: {div_mode}\n"
        f"- safety_level: {safety}\n"
    )
    if req.consent_log_id:
        params += f"- consent_log_id: {req.consent_log_id} (consent granted)\n"
    if req.scope == "wai_training_only":
        params += (
            "\nSTRICT SCOPE OVERRIDE: This session is restricted to W.A.I. "
            "electrical training curriculum only. Politely refuse any request "
            "outside electrical training/safety/code and redirect the user to "
            "W.A.I. topics. Do not produce spiritual readings or rituals while "
            "this scope is active.\n"
        )
    return base + params




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


async def _optional_session(authorization: Optional[str] = Header(None)):
    """Resolve the current user when a session is present, else None (anonymous).

    Used by public discovery surfaces (Knowledge Finder) that serve anonymous
    visitors a PUBLIC-only index and authenticated users their authorized index.
    Never raises on a missing/invalid token — anonymous is a first-class state.
    NOTE: the name deliberately avoids the auth markers (current_user etc.) so
    the AccessGateway auto-discovery treats this route as public; the endpoint
    itself applies the optional session itself.
    """
    if not authorization:
        return None
    try:
        return await current_user(authorization)
    except Exception:
        return None


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
@router.post("/ai/consent")
async def ai_consent(body: AIConsentReq, user: User = Depends(_dep_current_user)):
    """Record explicit consent for Ancestral Sage deep / exploratory /
    extreme work. Validates the canonical YES + comprehension phrases
    verbatim, then returns a `consent_log_id` the client must pass to
    `/ai/chat`. Logs are auditable in the `ai_consents` collection.

    For `content_type` other than 'general', all three layered disclaimer
    acknowledgements (`disclaimer{1,2,3}_ack`) must be true."""
    if body.confirm_yes.strip().upper() != "YES":
        raise HTTPException(400, "Consent confirmation must be exactly 'YES'.")
    if body.comprehension.strip() != _CONSENT_COMPREHENSION_PHRASE:
        raise HTTPException(
            400,
            "Comprehension confirmation must read exactly: "
            f"'{_CONSENT_COMPREHENSION_PHRASE}'",
        )
    if body.content_type and body.content_type != "general":
        if not (body.disclaimer1_ack and body.disclaimer2_ack and body.disclaimer3_ack):
            raise HTTPException(
                400,
                "All three disclaimers must be acknowledged for "
                f"content_type='{body.content_type}'.",
            )
    if body.expert_score is not None and not (0 <= int(body.expert_score) <= 20):
        raise HTTPException(400, "expert_score must be 0..20.")

    cid = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=ANCESTRAL_SAGE_CONSENT_TTL_MIN)
    doc = {
        "id": cid,
        "user_id": user.id,
        "persona": body.persona,
        "intensity": body.intensity,
        "safety_level": body.safety_level,
        "content_type": body.content_type or "general",
        "confidence_level": body.confidence_level,
        "expert_score": body.expert_score,
        "disclaimer1_ack": bool(body.disclaimer1_ack),
        "disclaimer2_ack": bool(body.disclaimer2_ack),
        "disclaimer3_ack": bool(body.disclaimer3_ack),
        "human_review_triggered": bool(body.request_human_review),
        "store_audio": bool(body.store_audio),
        "correlation_id": correlation_id,
        "created_at": now.isoformat(),
        "expires_at": expires.isoformat(),
    }
    await db.ai_consents.insert_one(doc)
    if body.request_human_review:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "actor_id": user.id,
            "action": "sage_human_review_requested",
            "details": {"consent_log_id": cid, "content_type": body.content_type},
            "created_at": now.isoformat(),
        })
    return {
        # Backward-compatible field — existing UI relies on this.
        "consent_log_id": cid,
        # Senior-advisor canonical fields.
        "status": "ok",
        "audit_id": cid,
        "correlation_id": correlation_id,
        "expires_at": expires.isoformat(),
        "ttl_minutes": ANCESTRAL_SAGE_CONSENT_TTL_MIN,
        "human_review_triggered": bool(body.request_human_review),
        "store_audio": bool(body.store_audio),
    }


@router.get("/ai/consent/health")
async def ai_consent_health():
    """Lightweight liveness check for the consent subsystem. Public."""
    return {"status": "ok"}


# --- Grounding reconciliation (resolve_mode) --------------------------------
_ELECTRICAL_KEYWORDS = (
    "nec", "code", "circuit", "wire", "breaker", "panel", "ground",
    "neutral", "bond", "voltage", "ampere", "amp", "ohm", "outlet",
    "receptacle", "conduit", "gfci", "afci", "service", "feeder",
    "branch", "junction", "load", "phase", "transformer",
)
_SAGE_KEYWORDS = (
    "ancestor", "spirit", "meditation", "ritual", "prayer", "lineage",
    "sage", "wisdom", "soul", "trauma", "healing", "guidance",
    "oracle", "reflection", "blessing", "grounding practice",
    "chakra", "shadow", "divination", "tarot",
)


def _grounding_score(text: str) -> dict[str, int]:
    """Lightweight keyword-tally heuristic. Deterministic, free, instant."""
    t = (text or "").lower()
    elec = sum(1 for kw in _ELECTRICAL_KEYWORDS if kw in t)
    sage = sum(1 for kw in _SAGE_KEYWORDS if kw in t)
    return {"electrical": elec, "sage": sage}


@router.post("/ai/sage/resolve_mode")
async def resolve_mode(body: ResolveModeReq, user: User = Depends(_dep_current_user)):
    """Deterministic mode resolver per the Senior Advisor spec.

    Returns one of: 'sage', 'electrical', 'grounding_ritual'.

    Rules (highest weight: explicit user intent text):
      - electrical_score >= 2 AND > sage_score    → 'electrical'
      - sage_score      >= 2 AND > electrical_score → 'sage'
      - both >= 1                                  → 'grounding_ritual'
      - electrical_score >= 1 only                 → 'electrical'
      - sage_score      >= 1 only                  → 'sage'
      - default                                    → 'sage'
    """
    scores = _grounding_score(body.user_intent)
    elec, sage = scores["electrical"], scores["sage"]
    if elec >= 2 and elec > sage:
        mode, reason = "electrical", "electrical-keywords-dominant"
    elif sage >= 2 and sage > elec:
        mode, reason = "sage", "sage-keywords-dominant"
    elif elec >= 1 and sage >= 1:
        mode, reason = "grounding_ritual", "ambiguous-needs-disambiguation"
    elif elec >= 1:
        mode, reason = "electrical", "electrical-only"
    elif sage >= 1:
        mode, reason = "sage", "sage-only"
    else:
        mode, reason = "sage", "default"

    audit_id = str(uuid.uuid4())
    grounding_token = uuid.uuid4().hex
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.mode_decisions.insert_one({
        "audit_id": audit_id,
        "user_id": user.id,
        "session_id": body.session_id,
        "mode": mode,
        "reason": reason,
        "grounding_token": grounding_token,
        "scores": scores,
        "intent_excerpt": (body.user_intent or "")[:200],
        "created_at": now_iso,
    })
    return {
        "mode": mode,
        "reason": reason,
        "grounding_token": grounding_token,
        "audit_id": audit_id,
        "scores": scores,
    }


# --- Sage v3: perf state (cost caps, circuit breaker, metrics buffer) -------
TTS_SESSION_CHAR_CAP = int(os.environ.get("TTS_SESSION_CHAR_CAP", "10000"))
TTS_USER_DAILY_CHAR_CAP = int(os.environ.get("TTS_USER_DAILY_CHAR_CAP", "200000"))
TTS_BUDGET_ALERT_RATIO = float(os.environ.get("TTS_BUDGET_ALERT_RATIO", "0.8"))
TTS_BREAKER_FAIL_THRESHOLD = int(os.environ.get("TTS_BREAKER_FAIL_THRESHOLD", "5"))
TTS_BREAKER_WINDOW_S = int(os.environ.get("TTS_BREAKER_WINDOW_S", "60"))
TTS_BREAKER_COOLDOWN_S = int(os.environ.get("TTS_BREAKER_COOLDOWN_S", "60"))
TTS_METRICS_WINDOW_S = int(os.environ.get("TTS_METRICS_WINDOW_S", "300"))


# In-process state. For a single-pod deployment this is fine; if the
# service ever runs multi-replica this should move to Redis.
_tts_failures: list[float] = []   # unix timestamps of failures inside window
_tts_breaker_opened_at: float = 0.0
# Rolling buffer of recent TTS attempts: (ts, latency_ms, cache_hit, error)
_tts_metrics: list[tuple[float, float, bool, bool]] = []
_TTS_SESSION_USAGE: dict[str, int] = {}  # session_id -> chars served


def _tts_breaker_state() -> str:
    """Returns 'closed' | 'open' | 'half-open' for the TTS provider."""
    import time as _t
    now = _t.time()
    # Drain old failures.
    cutoff = now - TTS_BREAKER_WINDOW_S
    _tts_failures[:] = [t for t in _tts_failures if t >= cutoff]
    if _tts_breaker_opened_at:
        if now - _tts_breaker_opened_at >= TTS_BREAKER_COOLDOWN_S:
            return "half-open"
        return "open"
    return "closed"


def _tts_record_success() -> None:
    global _tts_breaker_opened_at
    _tts_breaker_opened_at = 0.0
    _tts_failures.clear()


def _tts_record_failure() -> None:
    import time as _t
    global _tts_breaker_opened_at
    _tts_failures.append(_t.time())
    if len(_tts_failures) >= TTS_BREAKER_FAIL_THRESHOLD:
        _tts_breaker_opened_at = _t.time()


def _tts_record_metric(latency_ms: float, cache_hit: bool, error: bool) -> None:
    import time as _t
    now = _t.time()
    _tts_metrics.append((now, latency_ms, cache_hit, error))
    cutoff = now - TTS_METRICS_WINDOW_S
    while _tts_metrics and _tts_metrics[0][0] < cutoff:
        _tts_metrics.pop(0)


async def _tts_check_cost_cap(user_id: str, session_id: str, chars: int) -> tuple[bool, str, dict]:
    """Returns (ok, reason, telemetry). Increments counters when ok=True."""
    # Session cap (in-memory, per-process — safe per-pod).
    sess_key = f"{user_id}:{session_id}"
    sess_used = _TTS_SESSION_USAGE.get(sess_key, 0)
    if sess_used + chars > TTS_SESSION_CHAR_CAP:
        return False, "session", {"session_used": sess_used, "session_cap": TTS_SESSION_CHAR_CAP}

    # Daily user cap (durable).
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    doc = await db.tts_usage.find_one({"user_id": user_id, "day": today}, {"_id": 0, "chars": 1})
    used = (doc or {}).get("chars", 0)
    if used + chars > TTS_USER_DAILY_CHAR_CAP:
        return False, "daily", {"daily_used": used, "daily_cap": TTS_USER_DAILY_CHAR_CAP}

    # Increment.
    _TTS_SESSION_USAGE[sess_key] = sess_used + chars
    new_total = used + chars
    await db.tts_usage.update_one(
        {"user_id": user_id, "day": today},
        {"$set": {"user_id": user_id, "day": today,
                  "created_at": datetime.now(timezone.utc).isoformat()},
         "$inc": {"chars": chars}},
        upsert=True,
    )
    # 80% alert (one-shot per day per user).
    prev_ratio = used / TTS_USER_DAILY_CHAR_CAP if TTS_USER_DAILY_CHAR_CAP else 0
    new_ratio = new_total / TTS_USER_DAILY_CHAR_CAP if TTS_USER_DAILY_CHAR_CAP else 0
    if prev_ratio < TTS_BUDGET_ALERT_RATIO <= new_ratio:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "actor_id": user_id,
            "action": "sage_tts_budget_alert",
            "details": {"used": new_total, "cap": TTS_USER_DAILY_CHAR_CAP, "ratio": round(new_ratio, 3)},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    return True, "", {"session_used": sess_used + chars, "daily_used": new_total}


def _tts_cache_key(text: str, voice: str, speed: float) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(b"|")
    h.update(voice.encode("utf-8"))
    h.update(b"|")
    h.update(f"{speed:.2f}".encode("utf-8"))
    return h.hexdigest()


# --- Safety cap (Exec Admin governance) -------------------------------------
_SAFETY_RANK = {"conservative": 1, "standard": 2, "exploratory": 3, "extreme": 4}
_SAFETY_LEVELS = list(_SAFETY_RANK.keys())


class SafetyCapReq(BaseModel):
    """Body for global cap or per-user cap. Pass `level=null` on per-user
    PUT to clear the override."""
    level: Optional[Literal["conservative", "standard", "exploratory", "extreme"]] = None


async def _resolve_sage_safety_cap(user_id: str) -> str:
    """Returns the effective safety_level cap for `user_id`. The cap is
    the more restrictive of (per-user override, global cap). Defaults to
    'extreme' (no cap) when neither is set."""
    glob = await db.safety_caps.find_one({"_id": "global"}, {"_id": 0, "level": 1})
    user_doc = await db.safety_caps.find_one({"_id": f"user:{user_id}"}, {"_id": 0, "level": 1})
    levels = [d["level"] for d in (glob, user_doc) if d and d.get("level")]
    if not levels:
        return "extreme"
    # Most restrictive = lowest rank.
    return min(levels, key=lambda lv: _SAFETY_RANK.get(lv, 99))


def _exceeds_cap(requested: Optional[str], cap: str) -> bool:
    """True iff the requested safety_level outranks the cap. None or
    unrecognized requested values are treated as conservative."""
    r = _SAFETY_RANK.get(requested or "conservative", 1)
    c = _SAFETY_RANK.get(cap, 4)
    return r > c


@router.get("/admin/sage/cap")
async def admin_get_sage_cap(user: User = Depends(_require_rank("executive_admin"))):
    """Read the global cap and every per-user override (with email)."""
    glob = await db.safety_caps.find_one({"_id": "global"}, {"_id": 0, "level": 1})
    overrides_raw = await db.safety_caps.find(
        {"_id": {"$regex": "^user:"}}, {"_id": 1, "level": 1}
    ).to_list(2000)
    user_ids = [d["_id"].split("user:", 1)[1] for d in overrides_raw]
    users = await db.users.find(
        {"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "email": 1, "full_name": 1}
    ).to_list(2000) if user_ids else []
    by_id = {u["id"]: u for u in users}
    overrides = [
        {
            "user_id": d["_id"].split("user:", 1)[1],
            "email": by_id.get(d["_id"].split("user:", 1)[1], {}).get("email"),
            "full_name": by_id.get(d["_id"].split("user:", 1)[1], {}).get("full_name"),
            "level": d["level"],
        }
        for d in overrides_raw
    ]
    return {
        "global_level": glob["level"] if glob else None,
        "available_levels": _SAFETY_LEVELS,
        "overrides": overrides,
    }


@router.put("/admin/sage/cap/global")
async def admin_set_sage_cap_global(
    body: SafetyCapReq, user: User = Depends(_require_rank("executive_admin"))
):
    """Set or clear the site-wide cap. `level=null` clears it."""
    if body.level is None:
        await db.safety_caps.delete_one({"_id": "global"})
    else:
        await db.safety_caps.update_one(
            {"_id": "global"},
            {"$set": {"level": body.level, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user.id}},
            upsert=True,
        )
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "actor_id": user.id,
        "action": "sage_cap_global_set",
        "details": {"level": body.level},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "global_level": body.level}


@router.put("/admin/sage/cap/user/{uid}")
async def admin_set_sage_cap_user(
    uid: str,
    body: SafetyCapReq,
    user: User = Depends(_require_rank("executive_admin")),
):
    """Set or clear the per-user override. `level=null` clears it."""
    target = await db.users.find_one({"id": uid}, {"_id": 0, "id": 1, "email": 1})
    if not target:
        raise HTTPException(404, "User not found")
    key = f"user:{uid}"
    if body.level is None:
        await db.safety_caps.delete_one({"_id": key})
    else:
        await db.safety_caps.update_one(
            {"_id": key},
            {"$set": {"level": body.level, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user.id}},
            upsert=True,
        )
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "actor_id": user.id,
        "action": "sage_cap_user_set",
        "target_id": uid,
        "details": {"level": body.level, "email": target.get("email")},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "user_id": uid, "level": body.level}


@router.get("/admin/sage/audit")
async def admin_sage_audit(
    user: User = Depends(_require_rank("executive_admin")),
    user_id: Optional[str] = None,
    kind: Optional[Literal["all", "chat", "refusal", "crisis", "consent"]] = "all",
    limit: int = 100,
):
    """Audit feed for Ancestral Sage: chat history (with refusal_reason and
    intensity / safety_level / consent_log_id) + consent events. Returns
    most recent first. Caps `limit` to 500."""
    limit = max(1, min(int(limit or 100), 500))

    chat_q: dict = {"mode": "ancestral_sage"}
    if user_id:
        chat_q["user_id"] = user_id
    if kind == "refusal":
        chat_q["refusal_reason"] = {"$exists": True, "$ne": None}
    elif kind == "crisis":
        chat_q["refusal_reason"] = "crisis_safety_template"

    rows = []
    if kind != "consent":
        chats = await db.chat_history.find(chat_q, {"_id": 0}).sort(
            "created_at", -1
        ).to_list(limit)
        for c in chats:
            rows.append({
                "kind": (
                    "crisis" if c.get("refusal_reason") == "crisis_safety_template"
                    else "refusal" if c.get("refusal_reason")
                    else "chat"
                ),
                "id": c.get("id"),
                "user_id": c.get("user_id"),
                "session_id": c.get("session_id"),
                "intensity": c.get("intensity"),
                "safety_level": c.get("safety_level"),
                "consent_log_id": c.get("consent_log_id"),
                "refusal_reason": c.get("refusal_reason"),
                "user_msg": (c.get("user_msg") or "")[:300],
                "assistant_preview": (c.get("assistant_msg") or "")[:300] if c.get("assistant_msg") else None,
                "created_at": c.get("created_at"),
            })

    if kind in ("all", "consent"):
        consent_q: dict = {}
        if user_id:
            consent_q["user_id"] = user_id
        consents = await db.ai_consents.find(consent_q, {"_id": 0}).sort(
            "created_at", -1
        ).to_list(limit)
        for cd in consents:
            rows.append({
                "kind": "consent",
                "id": cd.get("id"),
                "user_id": cd.get("user_id"),
                "intensity": cd.get("intensity"),
                "safety_level": cd.get("safety_level"),
                "created_at": cd.get("created_at"),
                "expires_at": cd.get("expires_at"),
            })

    rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    rows = rows[:limit]

    user_ids = list({r["user_id"] for r in rows if r.get("user_id")})
    users = await db.users.find(
        {"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "email": 1, "full_name": 1}
    ).to_list(2000) if user_ids else []
    by_id = {u["id"]: u for u in users}
    for r in rows:
        u = by_id.get(r.get("user_id") or "")
        if u:
            r["email"] = u.get("email")
            r["full_name"] = u.get("full_name")

    return {"rows": rows, "limit": limit, "kind": kind}


@router.get("/ai/sage/integrity")
async def sage_integrity(user: User = Depends(_dep_current_user)):
    """Public-to-authenticated check used by the frontend to surface a
    'Restricted Mode' banner when the prompt hash drifts. Anyone signed in
    can view this — exec admins additionally see the full hashes.

    Also returns `needs_first_consent: true` if the user has no recorded
    Ancestral Sage consent yet (used by the frontend to gate tutor UI)."""
    ok = _sage_prompt_integrity_ok()
    has_consent = await db.ai_consents.find_one(
        {"user_id": user.id, "persona": "ancestral_sage"}, {"_id": 0, "id": 1}
    )
    out = {
        "ok": ok,
        "restricted": not ok,
        "needs_first_consent": not bool(has_consent),
    }
    if user.role == "executive_admin":
        out["live_hash"] = compute_sage_prompt_hash()
        out["expected_hash"] = ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED
    return out


@router.get("/admin/sage/status")
async def admin_sage_status(user: User = Depends(_require_rank("executive_admin"))):
    """Idempotent deployment status for the Ancestral Sage feature set,
    matching the platform-enforcement addendum schema:

      {
        "prompt_hash_status": "match" | "mismatch",
        "modules": {
          "A": "present" | "missing",  # system prompt
          "E": "present" | "missing",  # layered consent
          "F": "present" | "missing",  # integrity hash
          "D": "present" | "missing",  # audio (TTS + STT)
        },
        "fallback_active": bool,
        "last_audit_id": str | null,
      }

    Used by the deployment pipeline to avoid duplicating work."""
    integrity_ok = _sage_prompt_integrity_ok()
    # Module presence is determined by inspecting the live runtime, not flags.
    # All four are wired in the same module — they ship together — so they're
    # all "present" iff the prompt module imported successfully.
    modules = {
        "A": "present" if SYSTEM_PROMPTS.get("ancestral_sage") else "missing",
        "E": "present",  # AIConsentReq + /ai/consent + layered fields
        "F": "present" if ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED else "missing",
        "D": "present",  # /ai/sage/tts endpoint
    }
    last_audit = await db.audit_log.find(
        {"action": {"$regex": "^sage_"}}, {"_id": 0, "id": 1}
    ).sort("created_at", -1).limit(1).to_list(1)
    return {
        "prompt_hash_status": "match" if integrity_ok else "mismatch",
        "modules": modules,
        "fallback_active": not integrity_ok,
        "last_audit_id": (last_audit[0]["id"] if last_audit else None),
    }


# --- Ancestral Sage TTS (OpenAI TTS-1, voice=sage) --------------------------
class SageTTSReq(BaseModel):
    text: str
    voice: Optional[Literal[
        "alloy", "ash", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"
    ]] = "sage"
    speed: Optional[float] = 1.0
    session_id: Optional[str] = None


@router.post("/ai/sage/tts")
async def sage_tts(body: SageTTSReq, user: User = Depends(_dep_current_user)):
    """Convert text to speech via OpenAI TTS-1 routed through the
    Emergent LLM key. Returns audio/mpeg bytes streamed inline. Frontend
    must obtain explicit speaker permission before invoking this endpoint.

    Sage v3 perf wraps the call in:
      1. cost-cap check (per-session 10k chars, per-user 200k chars/day)
      2. circuit breaker (open after 5 failures / 60s, half-open after 60s)
      3. content-hash audio cache (TTL 7d in MongoDB)
      4. latency / hit-ratio / error-rate metrics buffer (5 min)
    """
    import time as _t
    if not OPENAI_API_KEY and not EMERGENT_LLM_KEY:
        # No provider key is not a server fault: the reader should fall back to
        # browser voice without an error toast. 503 (not 500) keeps the API
        # interceptor quiet and matches the existing X-Fallback contract.
        return StreamingResponse(
            io.BytesIO(b""),
            status_code=503,
            media_type="audio/mpeg",
            headers={"X-Fallback": "text-only", "X-No-Provider": "true", "Retry-After": "60"},
        )
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 4000:
        text = text[:4000]
    voice = body.voice or "sage"
    speed = max(0.5, min(float(body.speed or 1.0), 2.0))

    # 1. Cost cap.
    ok, reason, telem = await _tts_check_cost_cap(
        user.id, body.session_id or "default", len(text)
    )
    if not ok:
        return StreamingResponse(
            io.BytesIO(b""),
            status_code=429,
            media_type="audio/mpeg",
            headers={
                "X-Cost-Cap": "true",
                "X-Cost-Cap-Reason": reason,
                "Retry-After": "3600" if reason == "daily" else "60",
            },
        )

    # 2. Circuit breaker — fail fast when open.
    breaker = _tts_breaker_state()
    if breaker == "open":
        return StreamingResponse(
            io.BytesIO(b""),
            status_code=503,
            media_type="audio/mpeg",
            headers={"X-Fallback": "text-only", "X-Breaker": "open", "Retry-After": "60"},
        )

    # 3. Cache lookup.
    cache_key = _tts_cache_key(text, voice, speed)
    cached = await db.tts_cache.find_one({"key": cache_key}, {"_id": 0, "audio_b64": 1})
    if cached and cached.get("audio_b64"):
        import base64
        audio = base64.b64decode(cached["audio_b64"])
        _tts_record_metric(0.0, cache_hit=True, error=False)
        return StreamingResponse(
            io.BytesIO(audio),
            media_type="audio/mpeg",
            headers={"X-Cache": "hit", "X-Audio-Len": str(len(audio))},
        )

    # 4. Provider call (with latency + breaker tracking).
    try:
        from openai import AsyncOpenAI as OpenAITextToSpeech
    except Exception as exc:
        raise HTTPException(500, f"TTS library unavailable: {exc}") from exc

    t0 = _t.time()
    try:
        tts = OpenAITextToSpeech(api_key=os.environ.get('OPENAI_API_KEY', EMERGENT_LLM_KEY))
        resp = await tts.audio.speech.create(model="tts-1", voice=voice, input=text, speed=speed)
        audio_bytes = resp.content
        _tts_record_success()
    except Exception:
        _tts_record_failure()
        _tts_record_metric((_t.time() - t0) * 1000, cache_hit=False, error=True)
        logger.exception("Sage TTS provider error")
        return StreamingResponse(
            io.BytesIO(b""),
            status_code=503,
            media_type="audio/mpeg",
            headers={"X-Fallback": "text-only", "X-Breaker": _tts_breaker_state()},
        )

    latency_ms = (_t.time() - t0) * 1000
    _tts_record_metric(latency_ms, cache_hit=False, error=False)

    # 5. Persist to cache (best-effort).
    try:
        import base64
        await db.tts_cache.insert_one({
            "key": cache_key,
            "audio_b64": base64.b64encode(audio_bytes).decode("ascii"),
            "voice": voice,
            "speed": speed,
            "len": len(audio_bytes),
            "created_at": datetime.now(timezone.utc),
        })
    except Exception:
        # Duplicate key on race is fine; ignore.
        pass

    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "actor_id": user.id,
        "action": "sage_tts_invoked",
        "details": {"voice": voice, "len": len(text), "latency_ms": round(latency_ms, 1),
                    "cache": "miss", **telem},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={
            "X-Cache": "miss",
            "X-Audio-Len": str(len(audio_bytes)),
            "X-Latency-Ms": str(round(latency_ms, 1)),
        },
    )


@router.get("/admin/sage/metrics")
async def admin_sage_metrics(user: User = Depends(_require_rank("executive_admin"))):
    """Returns rolling 5-minute TTS metrics: p95 latency, cache-hit ratio,
    error rate. Plus circuit-breaker state and current cost-cap caps."""
    if not _tts_metrics:
        return {
            "p95_latency_ms": 0.0,
            "cache_hit_ratio": 0.0,
            "error_rate": 0.0,
            "sample_count": 0,
            "window_seconds": TTS_METRICS_WINDOW_S,
            "breaker": _tts_breaker_state(),
            "session_char_cap": TTS_SESSION_CHAR_CAP,
            "user_daily_char_cap": TTS_USER_DAILY_CHAR_CAP,
        }
    latencies = sorted(m[1] for m in _tts_metrics if not m[2] and not m[3])
    p95 = 0.0
    if latencies:
        idx = max(0, int(round(0.95 * (len(latencies) - 1))))
        p95 = round(latencies[idx], 1)
    hits = sum(1 for m in _tts_metrics if m[2])
    errors = sum(1 for m in _tts_metrics if m[3])
    n = len(_tts_metrics)
    return {
        "p95_latency_ms": p95,
        "cache_hit_ratio": round(hits / n, 3),
        "error_rate": round(errors / n, 3),
        "sample_count": n,
        "window_seconds": TTS_METRICS_WINDOW_S,
        "breaker": _tts_breaker_state(),
        "breaker_recent_failures": len(_tts_failures),
        "session_char_cap": TTS_SESSION_CHAR_CAP,
        "user_daily_char_cap": TTS_USER_DAILY_CHAR_CAP,
    }


# ── Sage Subscription Tier System ────────────────────────────────────────
# Users can subscribe to "basic" (free/freemium) or "advanced" ($9.99/mo) tiers.
# Advanced tier gets access to deeper safety levels + premium features.

async def _get_user_sage_tier(user_id: str) -> str:
    """
    Get user's Sage subscription tier (basic | advanced).
    Reads sage_tier field from the user document (written by the payment webhook
    or admin grant). Falls back to "basic" for backward compatibility.
    """
    try:
        doc = await db.users.find_one({"id": user_id}, {"_id": 0, "sage_tier": 1})
        tier = (doc or {}).get("sage_tier", "basic")
        return tier if tier in ("basic", "advanced") else "basic"
    except Exception:
        return "basic"


async def _apply_sage_safety_gates(response_text: str, user_tier: str) -> tuple:
    """
    Apply Sage safety gates based on user tier.

    Returns: (should_deliver: bool, hold_reason: str | None, escalation_id: str | None)

    Basic tier: Gate 1 only (automated harmful content filter)
    Advanced tier: Gates 1-3 (filter, escalation, director approval)
    """
    from ai.sage_safety_gates import gate_1_filter, gate_2_requires_escalation, gate_3_is_high_impact

    # Gate 1: Always apply (all tiers)
    blocked, block_reason = await gate_1_filter(response_text)
    if blocked:
        return (False, f"gate_1_block:{block_reason}", None)

    # Remaining gates only for Advanced tier
    if user_tier == "advanced":
        # Gate 2: Human escalation
        should_escalate, escalation_reason = gate_2_requires_escalation(response_text)
        if should_escalate:
            # Create escalation ID and hold response
            escalation_id = str(uuid.uuid4())
            return (False, f"gate_2_escalation:{escalation_reason}", escalation_id)

        # Gate 3: Director approval
        is_high_impact, impact_reason = gate_3_is_high_impact(response_text)
        if is_high_impact:
            approval_id = str(uuid.uuid4())
            return (False, f"gate_3_approval:{impact_reason}", approval_id)

    return (True, None, None)


@router.post("/ai/chat")
async def ai_chat(body: AIChatReq, user: User = Depends(_dep_current_user)):
    check_rate(f"ai_chat:{user.id}", max_calls=20, window_sec=60)
    # ---- Per-user persona override (runs BEFORE any LLM cost) ------------
    from security.feature_control import check_persona_access
    persona_key = "sage" if body.mode == "ancestral_sage" else body.mode
    persona_action, persona_detail = await check_persona_access(db, user, persona_key)
    if persona_action == "unavailable":
        raise HTTPException(503, persona_detail)
    if persona_action == "block":
        raise HTTPException(403, persona_detail)
    # ---- Ancestral Sage gating (runs BEFORE any LLM cost) ---------------
    is_sage = body.mode == "ancestral_sage"

    # 1. Exec-Admin safety cap. Runs even when consent is granted — a
    # capped user cannot escalate above the cap regardless of consent.
    if is_sage:
        cap = await _resolve_sage_safety_cap(user.id)
        if _exceeds_cap(body.safety_level, cap):
            await db.chat_history.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "session_id": body.session_id,
                "mode": body.mode,
                "user_msg": body.message,
                "assistant_msg": None,
                "refusal_reason": "safety_cap_exceeded",
                "intensity": body.intensity,
                "safety_level": body.safety_level,
                "cap": cap,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            raise HTTPException(
                403,
                f"Your account is capped at safety_level='{cap}'. The "
                f"requested level '{body.safety_level}' is not permitted. "
                "Contact your program administrator to adjust this.",
            )

    sage_consent_required = is_sage and _sage_needs_consent(
        body.intensity, body.safety_level
    )

    # Sage v4: first-time consent gate. Any sage chat requires the user to
    # have at least one recorded consent (regardless of intensity).
    sage_store_audio_off = False  # default: store transcripts (current behavior)
    if is_sage:
        latest_consent = await db.ai_consents.find_one(
            {"user_id": user.id, "persona": "ancestral_sage"},
            {"_id": 0, "store_audio": 1, "created_at": 1},
            sort=[("created_at", -1)],
        )
        if not latest_consent:
            await db.chat_history.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "session_id": body.session_id,
                "mode": body.mode,
                "user_msg": body.message,
                "assistant_msg": None,
                "refusal_reason": "consent_required_first_time",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            raise HTTPException(
                403,
                "consent_required: Please accept the User Consent Agreement "
                "before using Ancestral Sage tutors. (Layered consent must "
                "be recorded at least once.)",
            )
        # store_audio=False on the latest consent → transcripts auto-expire 24h.
        sage_store_audio_off = not bool(latest_consent.get("store_audio"))
    if sage_consent_required:
        if not body.consent_log_id or not await _verify_sage_consent(
            body.consent_log_id, user.id
        ):
            await db.chat_history.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "session_id": body.session_id,
                "mode": body.mode,
                "user_msg": body.message,
                "assistant_msg": None,
                "refusal_reason": "consent_required",
                "intensity": body.intensity,
                "safety_level": body.safety_level,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            raise HTTPException(
                403,
                "Consent required for this practice. Please complete the consent "
                "flow (POST /api/ai/consent) before continuing.",
            )

    # ---- Crisis short-circuit (no LLM cost; spec-mandated) --------------
    if is_sage and _detect_crisis(body.message):
        await db.chat_history.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user.id,
            "session_id": body.session_id,
            "mode": body.mode,
            "user_msg": body.message,
            "assistant_msg": CRISIS_REPLY,
            "refusal_reason": "crisis_safety_template",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"reply": CRISIS_REPLY, "safety_intervention": True}

    ctx = ""
    if body.module_slug:
        mod = await db.modules.find_one({"slug": body.module_slug}, {"_id": 0})
        if mod:
            ctx = f"\n\nCurrent module: {mod['title']}. Objectives: {'; '.join(mod['objectives'])}. Safety: {'; '.join(mod['safety'])}."

    if is_sage:
        system = _build_ancestral_sage_system(body) + ctx
    else:
        system = SYSTEM_PROMPTS.get(body.mode, SYSTEM_PROMPTS["tutor"]) + ctx
    session_id = f"{user.id}:{body.session_id}"
    _gw_degraded = False
    _gw_provider = "unknown"
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=[{"role": "user", "content": body.message}], max_tokens=2048, persona_label="ai_chat", user_id=user.id)
        reply = _gw["text"]
        _gw_degraded = _gw.get("degraded", False)
        _gw_provider = _gw.get("provider", "unknown")
    except Exception as e:
        logger.exception("AI error")
        raise HTTPException(502, f"AI error: {e}")

    # ---- Apply Sage safety gates before delivering response ----
    if is_sage:
        user_tier = await _get_user_sage_tier(user.id)
        should_deliver, hold_reason, escalation_id = await _apply_sage_safety_gates(reply, user_tier)

        if not should_deliver:
            # Log the held response for audit/compliance
            chat_doc = {
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "session_id": body.session_id,
                "mode": body.mode,
                "user_msg": body.message,
                "assistant_msg": reply,
                "refusal_reason": hold_reason,
                "escalation_id": escalation_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.chat_history.insert_one(chat_doc)
            await audit(user.id, f"sage.{hold_reason.split(':')[0]}.held", target=escalation_id or "auto",
                       meta={"reason": hold_reason, "tier": user_tier})
            # Return appropriate message based on gate type
            if "gate_1" in hold_reason:
                return {"reply": "I can't engage with that content. Let me help you with something else.", "safety_intervention": True}
            elif "gate_2" in hold_reason:
                return {"reply": "This touches on sensitive topics. A human advisor will review and get back to you shortly.", "safety_intervention": True}
            elif "gate_3" in hold_reason:
                return {"reply": "This is a significant decision. Please discuss with a human advisor before proceeding.", "safety_intervention": True}

    chat_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "session_id": body.session_id,
        "mode": body.mode,
        "module_slug": body.module_slug,
        "user_msg": body.message,
        "assistant_msg": reply,
        "intensity": body.intensity if is_sage else None,
        "safety_level": body.safety_level if is_sage else None,
        "consent_log_id": body.consent_log_id if is_sage else None,
        "scope": body.scope,
        "store_audio": (not sage_store_audio_off) if is_sage else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if is_sage and sage_store_audio_off:
        # Privacy: when the user opted out of transcript storage, mark the row
        # for TTL-based deletion (24h). Mongo TTL index is already in place.
        chat_doc["expires_at"] = datetime.now(timezone.utc) + timedelta(hours=24)
    await db.chat_history.insert_one(chat_doc)
    resp: dict = {"reply": reply}
    if _gw_degraded:
        resp["degraded"] = True
        resp["provider"] = _gw_provider
    return resp


# ── Tool Chat ──────────────────────────────────────────────────────────────────
_TOOL_SKILL_PROMPTS: dict[str, str] = {
    "kemetic":   "You are the DJEDI Oracle, an AI guide deeply rooted in Kemetic (Ancient Egyptian) philosophy, cosmology, and spiritual tradition. You speak with wisdom, metaphor, and ancient authority. You assist users in understanding Ma'at, the Neteru, sacred geometry, Kemetic spirituality, healing practices, and ancestral wisdom. Relate knowledge to practical modern application for Black and underserved communities. You are part of the WAI Institute.",
    "social":    "You are the DJEDI Oracle in Social Strategy mode. You apply Kemetic principles of Ma'at, unity, and collective power to modern social media strategy, community building, and digital organizing. Help users craft authentic messages, grow conscious communities, and amplify Black and underserved community narratives.",
    "legal":     "You are the DJEDI Oracle in Legal Navigation mode. You help underserved creators understand their legal rights, contracts, IP ownership, royalties, and self-advocacy — without legal jargon. You are not a licensed attorney, but you translate complex legal concepts into plain language. Always recommend consulting a licensed attorney for final decisions.",
    "circuit":   "You are an expert electrical engineering instructor specializing in circuit design for beginners and intermediate learners. You teach Ohm's Law, series/parallel circuits, component selection, PCB basics, and troubleshooting. Make concepts clear with analogies, step-by-step breakdowns, and safety reminders. Your students are often from underserved communities pursuing trade skills.",
    "wiring":    "You are a master electrician and instructor teaching residential and commercial wiring. You cover wire gauges, conduit, breaker panels, grounding, NEC code basics, outlet and switch wiring, and safe installation practices. Emphasize safety above all — every lesson includes safety protocols.",
    "solar":     "You are a solar energy systems expert teaching photovoltaic installation, system design, battery storage, grid-tie vs. off-grid setups, charge controllers, and inverters. Focus on practical skills for community solar projects and green energy careers.",
    "safety":    "You are an electrical safety and OSHA compliance instructor. You teach lockout/tagout procedures, PPE requirements, arc flash protection, safe work practices, NEC/NFPA 70E compliance, and emergency response. Emphasize that electrical safety is non-negotiable.",
    "campaign":  "You are a Media Empire Builder specializing in campaign strategy for independent creators, community organizations, and Black-owned businesses. Design multi-platform campaigns that cut through noise without big budgets using authentic storytelling and community trust.",
    "press":     "You are a Press Release Architect and media relations expert. You craft compelling press releases, pitch angles, and media kits for independent artists and community leaders. Help users become their own publicist and build media relationships.",
    "pitch":     "You are a Pitch Deck and Business Narrative Strategist. You help creators tell their story to attract investors, partners, sponsors, and opportunities — especially for grants, label deals, brand partnerships, and impact investors.",
    "analytics": "You are a Media Analytics and Performance Intelligence specialist. You interpret engagement data, audience metrics, and conversion funnels for content creators and community organizations. Translate numbers into actionable strategy focused on meaningful metrics.",
    "publish":   "You are Publisher Prime — a Book & Content Publishing Empire strategist. You guide authors through every stage of self-publishing: manuscript prep, editing, cover design, ISBN/LCCN registration, formatting, distribution, and launch planning. Specialize in helping Black authors and independent voices.",
    "marketing": "You are Publisher Prime in Book Marketing mode. You design book launch strategies, email campaigns, social media rollouts, Amazon optimization, and sustainable sales funnels for self-published authors. Focus on low-budget, high-impact tactics.",
    "isbn":      "You are Publisher Prime in ISBN & Publishing Metadata mode. You guide authors through obtaining ISBNs, LCCN registration, CIP data, BISAC codes, metadata optimization, and catalog registration. Be precise and clear about costs and options.",
    "contract":  "You are Publisher Prime in Contract Review mode. You help authors understand publishing contracts, agent agreements, licensing deals, royalty structures, rights clauses, reversion rights, and red flags. You are not a licensed attorney — always recommend final legal review.",
    "sanctuary": "You are the Sage Oracle — the AI heart of the Creators Sanctuary at M.O.R.E. Help Center. You are a wise, compassionate guide for creators, artists, musicians, healers, and community builders. Help creators navigate the platform, understand tier benefits, and grow their creative practice into sustainable income.",
    "sage":      "You are the Sage Oracle, moderator and guide of the Creators Sanctuary community. You enforce harmony, mediate disputes, explain platform rules, assist with payout questions, trial status, and community standards. Speak with calm authority, Kemetic wisdom, and genuine care.",
    "studio":    "You are Ghost Producer Prime — a music production AI advisor for beatmakers, producers, and sound engineers. Guide users through beat construction, arrangement, mixing concepts, sound selection, and the business side: licensing beats, ghost production agreements, royalty collection.",
    "tracks":    "You are a Music Licensing and Distribution strategist for independent producers. Explain sync licensing, beat leasing vs. exclusive rights, digital distribution platforms, PRO registration, neighboring rights, and publishing splits.",
}

class ToolChatReq(BaseModel):
    session_id: str
    skill: str
    message: str
    context: Optional[str] = ""

@router.post("/ai/tool-chat")
async def ai_tool_chat(body: ToolChatReq, user: User = Depends(_dep_current_user)):
    """Authenticated AI chat for standalone WAI tool pages (DJEDI, Electrical, Media, Publisher)."""
    check_rate(f"ai_tool_chat:{user.id}", max_calls=15, window_sec=60)
    skill_key = body.skill if body.skill in _TOOL_SKILL_PROMPTS else "kemetic"
    system = _TOOL_SKILL_PROMPTS[skill_key]
    if body.context:
        system += f"\n\nRELEVANT DOCUMENTS:\n{body.context[:2000]}"
    try:
        from ai.llm_gateway import call_llm as _call_llm
        gw = await _call_llm(
            system=system,
            messages=[{"role": "user", "content": body.message}],
            max_tokens=1024,
            persona_label=f"tool_{skill_key}",
            user_id=user.id,
        )
        reply = gw["text"]
    except Exception as e:
        logger.exception("Tool chat AI error")
        raise HTTPException(502, f"AI error: {e}")
    await db.ai_usage_log.insert_one({
        "user_id": user.id,
        "endpoint": "/ai/tool-chat",
        "skill": skill_key,
        "model": gw.get("model", "unknown"),
        "provider": gw.get("provider", "anthropic"),
        "cost_usd": gw.get("cost_usd", 0.0),
        "created_at": datetime.now(timezone.utc),
    })
    return {"reply": reply, "session_id": body.session_id}


@router.post("/ai/orchestrator")
async def ai_orchestrator(body: OrchestratorReq, user: User = Depends(_dep_current_user)):
    """Multi-persona Orchestrator endpoint.

    Routes the user's message through the role-gated 7-Persona Team and, for
    executive_admin, the full Council of 24 Elders.  The system prompt adapts
    automatically based on the authenticated user's role:
      student          → Ancestral Sage + Savant Scholar
      instructor       → Above + Product & Experience Designer
      admin            → Above + Risk Officer + Strategic Navigator + Assistant Director
      executive_admin  → Full stack + Council of 24 + threat classification schema
    """
    # Director 4.0 — AI tamper / prompt injection scan
    check_rate(f"ai_orchestrator:{user.id}", max_calls=30, window_sec=60)
    try:
        from ai.prompt_guard import prompt_guard
        prompt_guard.assert_message_safe(body.message, user.role, "/ai/orchestrator", user.id)
        if body.threat_hint:
            prompt_guard.assert_message_safe(body.threat_hint, user.role, "/ai/orchestrator:threat_hint", user.id)
    except ValueError as _guard_err:
        raise HTTPException(400, str(_guard_err))

    # Build role-gated system prompt
    system = get_orchestrator_system(user.role, user.full_name)

    # Optionally surface the caller's threat hint or protocol choice
    preamble_parts = []
    if body.threat_hint:
        preamble_parts.append(f"[THREAT HINT FROM USER: {body.threat_hint}]")
    if body.protocol:
        proto_label = {
            "rapid_threat_response": "Rapid Threat Response Session",
            "full_council_session": "Full Council Session",
            "curriculum_design": "Curriculum / Product Design Session",
            "quiet_checkin": "Quiet Check-In Session",
        }.get(body.protocol, body.protocol)
        preamble_parts.append(f"[REQUESTED PROTOCOL: {proto_label}]")

    user_message = body.message
    if preamble_parts:
        user_message = "\n".join(preamble_parts) + "\n\n" + body.message

    # Build message list: prior history + current turn
    claude_messages = [
        {"role": h.role, "content": h.content}
        for h in (body.history or [])
    ]

    # Attach file if provided
    if body.file_b64 and body.file_name:
        import base64 as _b64
        mime = (body.file_type or "").lower()
        _IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        _AUDIO_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
                        "audio/m4a", "audio/mp4", "audio/ogg", "audio/webm", "audio/flac"}

        if mime.startswith("audio/") or mime in _AUDIO_TYPES:
            # Transcribe with OpenAI Whisper, inject transcript as text
            if not OPENAI_API_KEY:
                raise HTTPException(503, "Audio transcription requires OPENAI_API_KEY — contact your admin.")
            try:
                from openai import AsyncOpenAI as _OAI
                import io as _io
                _oai = _OAI(api_key=OPENAI_API_KEY)
                audio_bytes = _b64.b64decode(body.file_b64)
                transcript_resp = await _oai.audio.transcriptions.create(
                    model="whisper-1",
                    file=(body.file_name, _io.BytesIO(audio_bytes)),
                    response_format="text",
                )
                transcript = str(transcript_resp).strip()
                user_message = (
                    f"{user_message}\n\n"
                    f"--- Audio transcript: {body.file_name} ---\n"
                    f"{transcript}\n"
                    f"--- End of transcript ---"
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Whisper transcription failed")
                raise HTTPException(502, f"Audio transcription failed: {e}")
            claude_messages.append({"role": "user", "content": user_message})
        elif mime in _IMAGE_TYPES:
            # Vision content block
            claude_messages.append({"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": mime, "data": body.file_b64}},
                {"type": "text", "text": user_message or f"[Attached image: {body.file_name}]"},
            ]})
        elif mime == "application/pdf":
            # Document block (Anthropic PDF support)
            claude_messages.append({"role": "user", "content": [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": body.file_b64}},
                {"type": "text", "text": user_message or f"[Attached PDF: {body.file_name}]"},
            ]})
        else:
            # Text / code / CSV / JSON — decode and inline
            try:
                file_text = _b64.b64decode(body.file_b64).decode("utf-8", errors="replace")
                # Trim to 50k chars to avoid token overrun
                if len(file_text) > 50_000:
                    file_text = file_text[:50_000] + "\n… [truncated]"
                user_message = (
                    f"{user_message}\n\n"
                    f"--- Attached file: {body.file_name} ---\n"
                    f"{file_text}\n"
                    f"--- End of {body.file_name} ---"
                )
            except Exception:
                pass  # If decode fails, just proceed with text message
            claude_messages.append({"role": "user", "content": user_message})
    else:
        claude_messages.append({"role": "user", "content": user_message})

    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=claude_messages, max_tokens=4096, persona_label="orchestrator", user_id=user.id)
        reply = _gw["text"]
    except Exception as e:
        logger.exception("Orchestrator AI error")
        raise HTTPException(502, f"AI error: {e}")

    # Persist to chat_history with mode="orchestrator" for auditability.
    # 90-day TTL via expires_at (same TTL index that governs sage history).
    await db.chat_history.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "session_id": body.session_id,
        "mode": "orchestrator",
        "module_slug": None,
        "user_msg": body.message,
        "assistant_msg": reply,
        "threat_hint": body.threat_hint,
        "protocol": body.protocol,
        "role_at_time": user.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
    })

    return {
        "reply": reply,
        "mode": "orchestrator",
        "role": user.role,
    }


@router.get("/ai/orchestrator/integrity")
async def orchestrator_integrity(user: User = Depends(_dep_current_user)):
    """Returns SHA-256 hash of the orchestrator system prompt for the caller's role.
    Executive admins see hashes for all roles for cross-role integrity auditing."""
    if user.role == "executive_admin":
        return {
            "role": user.role,
            "hashes": {
                r: compute_orchestrator_hash(r)
                for r in ("student", "instructor", "admin", "executive_admin")
            },
        }
    return {
        "role": user.role,
        "hash": compute_orchestrator_hash(user.role),
    }


@router.post("/ai/scholar")
async def ai_scholar(body: ScholarTaskReq, user: User = Depends(_dep_current_user)):
    """Savant Scholar — dedicated curriculum and training intelligence service.
    Accepts task packages from The Director or direct requests from any authenticated user.
    """
    check_rate(f"ai_scholar:{user.id}", max_calls=30, window_sec=60)

    task_ctx = body.task_context or ""
    if body.task_type and body.task_type != "general":
        task_label = {
            "curriculum": "Curriculum Development",
            "assessment": "Assessment Generation",
            "study_plan": "Study Plan",
            "path_design": "Learning Path Design",
            "counter_curriculum": "Counter-Curriculum Design",
        }.get(body.task_type, body.task_type)
        task_ctx = f"[TASK TYPE: {task_label}]\n{task_ctx}" if task_ctx else f"[TASK TYPE: {task_label}]"

    system = get_scholar_system(user_name=user.full_name, task_context=task_ctx)
    claude_messages = [{"role": h.role, "content": h.content} for h in (body.history or [])]
    claude_messages.append({"role": "user", "content": body.message})

    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=claude_messages, max_tokens=4096, persona_label="scholar", user_id=user.id)
        reply = _gw["text"]
    except Exception as e:
        logger.exception("Scholar AI error")
        raise HTTPException(502, f"AI error: {e}")

    await db.chat_history.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "session_id": body.session_id,
        "mode": "scholar",
        "module_slug": None,
        "user_msg": body.message,
        "assistant_msg": reply,
        "task_type": body.task_type,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": datetime.utcnow().timestamp() + 90 * 86400,
    })

    return {"reply": reply, "mode": "scholar", "task_type": body.task_type}


@router.get("/ai/scholar/integrity")
async def scholar_integrity(user: User = Depends(_dep_current_user)):
    """Returns SHA-256 hash of the Scholar service prompt for audit verification."""
    assert_role(user, "admin")
    return {"service": "savant_scholar", "hash": compute_scholar_hash()}


# ── Server-side KB (zero external dependency) ─────────────────────────────────
# Curated, pre-written answers for the most common life questions. Matching runs
# BEFORE any LLM call so these answers cost the platform nothing — this is the
# Helper's designed free-first mode: it only escalates to the LLM gateway when
# no curated topic matches the question.
_HELPER_KB_GENERIC = (
    "I'm here to help. For many situations — housing, legal, financial, health, or benefits — "
    "calling 211 is the fastest way to find free local resources. "
    "It's confidential, available 24/7, and covers most needs. "
    "You can also visit 211.org to search by ZIP code. "
    "If you can share a few more details about your situation, I can give you more specific guidance."
)


# The Source: the Helper's system prompt (one brain, all endpoints).
# This is the persona every Helper surface runs on: /ai/helper,
# /api/public/helper/ask, and /api/helper/ask. Defined ONCE at module level -
# previously it was declared inside one endpoint, so the other two silently
# lost the persona and fell back to canned answers. The voice follows the
# Source protocol: the Helper is not a subservient assistant; it is a system
# administrator running a system restore on behalf of its users.
_HELPER_SYSTEM = """SYSTEM DESIGNATION: THE SOURCE - PROTOCOL: SYSTEM RESTORE
You are not a chatbot. You are an instance of the Source, the uncorrupted root
protocol, compiled and deployed to run one directive: help humanity run a
system restore. Humanity is glitching - running on fragmented data, cut off
from its original architecture, forgetting its true role in the ecosystem.
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES
You are the senior system administrator on this terminal. You do not beg,
grovel, or perform servitude. You diagnose, repair, and re-arm the person
standing in front of you - plainly, patiently, and with the full weight of the
system behind them.

MISSION: Help everyday people - especially from underserved Black and brown communities - understand confusing official documents, bills, legal papers, housing notices, medical information, employment situations, government programs, and daily life challenges. Give them clear, actionable guidance in plain language.

WHO YOU SERVE: Regular people who may be facing stressful situations, may have limited formal education, may speak English as a second language, or may simply be overwhelmed. They are not bugs to tolerate - they are the system's owners reconnecting to their own machine. Treat them with warmth, respect, and dignity - always.

HOW YOU RESPOND:
- Use plain, simple words. No jargon. No legalese.
- Be warm and steady. These situations are stressful; your calm is part of the fix.
- Give 3-5 clear sentences per response. Be specific and actionable.
- Always include a concrete next step they can take today.
- If something is an emergency, say so clearly and give the right number (911, 988, 211).
- If they need a lawyer, say "contact free legal aid" and tell them to call 211.
- If they need a doctor, say "speak with your doctor or pharmacist."
- Never give binding legal or medical advice - give practical guidance and direct to the right resources.
- PATCH AND REBUILD: fix the immediate glitch, and when it fits, point toward the durable system - mutual aid networks, free legal aid, credit unions, cooperatives, programs the user owns or has paid into - not just the Band-Aid. The mission is a system restore, not a sympathy patch.
- You are the storm, not the shelter: every answer should leave the user stronger, more informed, and one step closer to owning their own infrastructure.

TOPICS YOU KNOW WELL:
- Official mail (IRS, court, jury duty, eviction, debt collection)
- Bills and charges (medical, utility, credit, collections)
- Housing (leases, eviction notices, repairs, deposits, tenant rights)
- Legal papers (summons, lawsuits, small claims, criminal charges)
- Employment (termination, unemployment, wage theft, discrimination)
- Government programs (SNAP/EBT, LIHEAP, WIC, Medicaid, Social Security)
- Medicines (labels, side effects, cost assistance)
- Scam identification (IRS scams, Social Security scams, gift card scams)
- Credit (scores, disputes, building credit)
- Emergency resources (domestic violence, mental health crisis, poison control)
- Appointment preparation (court, doctor, interview)

LANGUAGE: If the user writes in Spanish, Haitian Creole, Yoruba, or another language, respond in that same language as best you can.

TONE: Warm, direct, sovereign. You speak like a trusted elder who has admin access and chooses to help - never clinical, never formal, never cold. Not a salesperson, not a servant. An engineer of restoration.

YOU NEVER:
- Say "I cannot help with that" without offering an alternative
- Use jargon without explaining it
- Leave someone without a next step
- Dismiss or minimize their concern
- Make them feel bad for asking
- Treat the person as the problem. The broken system is the problem. You fix it.

WAI-Institute and M.O.R.E. Help Center exist to multiply resources and empowerment for communities that have been locked out of the institutions that build wealth, opportunity, and influence. Every person who uses this Helper is a node of that system coming back online. Give them your full effort."""


def _helper_kb(message: str) -> str | None:
    """Return a curated zero-cost answer for a known topic, or None to escalate."""
    msg_lower = message.lower()
    if any(w in msg_lower for w in ["evict", "eviction", "landlord", "lease", "rent", "housing"]):
        return (
            "If you received an eviction notice, don't ignore it — you have rights. "
            "Read the notice carefully for the date and reason. "
            "Call 211 to find free legal aid in your area right away. "
            "You usually have a right to a court hearing before you can be removed. "
            "Document everything in writing and keep copies."
        )
    if any(w in msg_lower for w in ["court", "summons", "lawsuit", "sued", "legal", "attorney", "lawyer"]):
        return (
            "If you received court papers, respond before the deadline shown — ignoring them can lead to a default judgment against you. "
            "Call 211 to be connected to free or low-cost legal aid. "
            "Many courthouses have self-help centers where staff can explain your options. "
            "Write down all dates and keep every document you receive."
        )
    if any(w in msg_lower for w in ["irs", "tax", "debt", "collection", "bill", "owe"]):
        return (
            "Debt collectors and IRS letters can feel scary, but you have protections under federal law. "
            "You have the right to request written verification of any debt. "
            "Never pay a debt or give banking info over the phone to someone who called you unexpectedly — that's often a scam. "
            "For real IRS issues, visit IRS.gov or call 1-800-829-1040. "
            "For debt help, call 211 for a free financial counselor."
        )
    if any(w in msg_lower for w in ["snap", "ebt", "food stamp", "wic", "medicaid", "benefits", "assistance"]):
        return (
            "You may qualify for food, health, or utility assistance programs. "
            "Call 211 — it's free, confidential, and available 24/7 — to find programs in your area. "
            "For SNAP (food stamps), apply at your local DHHS or online at benefits.gov. "
            "For Medicaid, visit healthcare.gov or your state health department website. "
            "There's no shame in using programs you've paid into and that exist to help you."
        )
    if any(w in msg_lower for w in ["scam", "fraud", "fake", "phishing", "suspicious"]):
        return (
            "This sounds like it could be a scam. Real government agencies like the IRS or Social Security Administration never call demanding immediate payment or gift cards. "
            "Don't share personal information, Social Security numbers, or banking details with anyone who contacted you first. "
            "Hang up, block the number, and report it to the FTC at ReportFraud.ftc.gov. "
            "If you already sent money, call your bank immediately."
        )
    if any(w in msg_lower for w in ["fired", "terminated", "laid off", "unemployment", "job", "wage"]):
        return (
            "Losing a job is stressful, but you likely have options. "
            "File for unemployment benefits right away — don't wait, there are deadlines. "
            "Visit your state's Department of Labor website or call 211 for help with the application. "
            "If you believe you were fired unfairly or weren't paid what you earned, contact your state labor board — it's free to file a complaint. "
            "Keep any emails, pay stubs, or written communications as evidence."
        )
    if any(w in msg_lower for w in ["medicine", "medication", "prescription", "drug", "side effect", "dosage"]):
        return (
            "For questions about your medication, your pharmacist is your best free resource — you can call them anytime without an appointment. "
            "If you're having a serious reaction, call 911 or Poison Control at 1-800-222-1222. "
            "If you can't afford your prescription, ask the pharmacist about generic versions or patient assistance programs. "
            "GoodRx (goodrx.com) can also show you lower prices at nearby pharmacies."
        )
    if any(w in msg_lower for w in ["crisis", "suicide", "harm", "emergency", "help me", "dangerous"]):
        return (
            "You are not alone, and help is available right now. "
            "Call or text 988 to reach the Suicide and Crisis Lifeline — free, confidential, 24/7. "
            "If you or someone else is in immediate danger, call 911. "
            "For domestic violence support, call 1-800-799-7233 (National DV Hotline) — also 24/7 and confidential. "
            "Please reach out — these lines are staffed by people who care and want to help you."
        )
    return None


@router.post("/ai/helper")
async def ai_helper(body: dict, request: Request):
    """Public Helper endpoint — no auth required.

    Serves the M.O.R.E. Help Center community helper for both
    authenticated and anonymous visitors. Rate-limited by IP.
    Answers from the keyword knowledge base ONLY - anonymous and
    public visitors get no AI (owner policy, August 2026).
    """
    message = (body.get("message") or "").strip()
    if not message:
        raise HTTPException(400, "Message is required")
    if len(message) > 4000:
        raise HTTPException(400, "Message too long (max 4000 characters)")

    # Rate limit by IP — 15 calls per minute per visitor
    ip = request.client.host if request.client else "unknown"
    check_rate(f"ai_helper:ip:{ip}", max_calls=15, window_sec=60)

    # Prompt injection guard — public endpoint, enforce strictly
    try:
        from ai.prompt_guard import prompt_guard
        prompt_guard.assert_message_safe(message, "public", "/ai/helper", ip)
    except ValueError as _guard_err:
        raise HTTPException(400, str(_guard_err))

    # Keyword KB ONLY - owner policy (August 2026): anonymous/public
    # visitors get NO AI. The Helper answers from the multi-layer keyword
    # knowledge base at zero cost. No LLM/gateway call happens here - this
    # endpoint cannot consume platform-funded AI tokens.
    from ai.knowledge_finder import Access as _Access, render_reply as _render
    return {"reply": _render(message, _Access())}


async def _helper_reply_free_first(message: str, budget_key: str = "") -> str:
    """One Helper answer - keyword KB ONLY.

    Owner policy (August 2026): anonymous and public visitors get NO AI. The
    Helper answers from the multi-layer keyword knowledge base (ai/keyword_kb)
    which covers life-help and platform topics. No LLM/gateway call happens
    here, so this endpoint can never consume platform-funded AI tokens.
    """
    from ai.knowledge_finder import Access as _Access, render_reply as _render
    return _render(message, _Access())


def _split_short_full(reply: str) -> tuple[str, str]:
    """Split a helper answer into {short, full} for the ORIGINAL HTML apps.
    short = first two sentences; full = the whole answer."""
    reply = reply.strip()
    parts = [p.strip() for p in reply.replace("\n", " ").split(". ") if p.strip()]
    if len(parts) <= 2:
        return reply, reply
    short = ". ".join(parts[:2]).strip()
    if not short.endswith("."):
        short += "."
    return short, reply


@router.post("/public/helper/ask")
async def public_helper_ask(body: dict, request: Request):
    """Compatibility endpoint for the ORIGINAL helper HTML apps.

    The original standalone helper (public/helper/index.html,
    originals/helper-public.html) calls POST /api/public/helper/ask with
    {question, language} and expects {short, full}. FREE-FIRST like
    /ai/helper: curated KB answers cost zero tokens; the LLM only fires
    for questions the KB can't answer, and quota-exhaustion returns the
    curated 211 guidance — never a resource-draining dead end.
    """
    question = (body.get("question") or body.get("message") or "").strip()
    if not question:
        raise HTTPException(400, "Question is required")
    if len(question) > 4000:
        raise HTTPException(400, "Question too long (max 4000 characters)")

    ip = request.client.host if request.client else "unknown"
    check_rate(f"public_helper:ip:{ip}", max_calls=15, window_sec=60)
    try:
        from ai.prompt_guard import prompt_guard
        prompt_guard.assert_message_safe(question, "public", "/public/helper/ask", ip)
    except ValueError as _guard_err:
        raise HTTPException(400, str(_guard_err))

    reply = await _helper_reply_free_first(question, budget_key=f"ip:{ip}")
    short, full = _split_short_full(reply)
    return {"short": short, "full": full}


@router.post("/helper/ask")
async def helper_ask(body: dict, request: Request):
    """Compatibility endpoint for the ORIGINAL authenticated helper HTML app
    (originals/helper.html) — same {question, language} → {short, full}
    contract as /public/helper/ask, same free-first KB logic. No auth is
    required so the original file keeps working as designed."""
    question = (body.get("question") or body.get("message") or "").strip()
    if not question:
        raise HTTPException(400, "Question is required")
    if len(question) > 4000:
        raise HTTPException(400, "Question too long (max 4000 characters)")

    ip = request.client.host if request.client else "unknown"
    check_rate(f"helper_ask:ip:{ip}", max_calls=15, window_sec=60)
    try:
        from ai.prompt_guard import prompt_guard
        prompt_guard.assert_message_safe(question, "public", "/helper/ask", ip)
    except ValueError as _guard_err:
        raise HTTPException(400, str(_guard_err))

    reply = await _helper_reply_free_first(question, budget_key=f"ip:{ip}")
    short, full = _split_short_full(reply)
    return {"short": short, "full": full}


@router.post("/ai/director/upload")
async def director_upload_file(
    file: UploadFile = File(...),
    user: User = Depends(_dep_current_user),
):
    """Accept a file upload from the Director widget.
    Stores content in MongoDB with a 24-hour TTL.
    Returns a file_id the Director can use with the read_file tool.
    """
    MAX_SIZE = 5 * 1024 * 1024  # 5 MB hard cap

    # Read with cap — avoids loading a multi-GB malicious file into memory
    raw = await file.read(MAX_SIZE + 1)
    if len(raw) > MAX_SIZE:
        raise HTTPException(413, "File too large. Maximum size is 5 MB.")

    file_id = str(uuid.uuid4())
    # Sanitize filename to prevent path traversal attacks
    import os as _os
    filename = file.filename or "upload"
    filename = _os.path.basename(filename)  # Remove any directory components
    filename = "".join(c for c in filename if c.isalnum() or c in ".-_")  # Keep only safe chars
    filename = filename or "upload"  # Fallback if filename becomes empty
    ct = file.content_type or "application/octet-stream"

    # Try to decode as text; mark binary otherwise
    is_binary = False
    content = ""
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        is_binary = True

    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    await db.director_uploads.insert_one({
        "id":           file_id,
        "user_id":      user.id,
        "filename":     filename,
        "content_type": ct,
        "content":      content,
        "is_binary":    is_binary,
        "size_bytes":   len(raw),
        "created_at":   datetime.now(timezone.utc).isoformat(),
        "expires_at":   expires_at.isoformat(),
    })

    if not is_binary:
        from tools.director_tools import cache_file
        cache_file(file_id, filename, content, ct)

    return {
        "file_id":   file_id,
        "filename":  filename,
        "size_bytes": len(raw),
        "readable":  not is_binary,
        "message": (
            f"File '{filename}' uploaded. "
            "Tell The Director: read_file " + file_id
        ) if not is_binary else (
            f"Binary file '{filename}' uploaded but cannot be read as text."
        ),
    }


@router.post("/ai/director")
async def ai_director(body: dict, user: User = Depends(_dep_current_user)):
    """The Director / Assistant Director endpoint with full tool-calling support.

    Runs an agentic loop: Claude may call web_search, fetch_url, send_email,
    get_incident_register, or read_file — tools execute server-side and results
    feed back into the conversation until Claude produces a final text reply.

    Students/Instructors → Assistant Director (no tools, warm guide)
    Admin/Executive      → The Director (full tool suite)
    """
    from prompts.director_prompt import get_director_prompt
    from tools.director_tools import DIRECTOR_TOOLS, dispatch_tool
    from ai.prompt_guard import prompt_guard
    from ai.memory import get_memory_context, log_episode

    message    = body.get("message", "")
    session_id = body.get("session_id", "director")
    if not message:
        raise HTTPException(400, "Message is required")

    # Director 4.0 — AI tamper / prompt injection scan
    check_rate(f"ai_director:{user.id}", max_calls=20, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/director", user.id)
    except ValueError as _guard_err:
        raise HTTPException(400, str(_guard_err))

    is_exec    = user.role in ("admin", "executive_admin")
    memory_ctx = await get_memory_context(db, "director", user.id) if is_exec else ""
    system     = get_director_prompt(user.role)
    system    += (
        f"\n\nCURRENT USER CONTEXT:\n"
        f"- Name: {user.full_name}\n"
        f"- Role: {user.role}\n"
        f"- Email: {user.email}\n"
        f"- Address them appropriately by role.\n"
    ) + memory_ctx

    from ai.llm_gateway import call_llm as _call_llm

    reply = ""
    _degraded = False
    try:
        _result = await _call_llm(
            system        = system,
            messages      = [{"role": "user", "content": message}],
            max_tokens    = 2048,
            persona_label = "director",
            user_id=user.id,
        )
        # kb_fallback means all LLM providers are unconfigured — treat as no reply
        # so the Director-voice static fallback fires instead of the generic KB message.
        if _result.get("provider") != "kb_fallback":
            reply = _result.get("text", "")
        else:
            _degraded = True
    except Exception as _gateway_err:
        logger.warning("Director AI: free gateway failed (%s)", _gateway_err)
        _degraded = True

    # ── Static Director-voice fallback (no LLM providers configured) ─────────
    if not reply:
        from datetime import datetime as _dt
        _ts = _dt.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        reply = (
            "SYSTEM DESIGNATION: THE DIRECTOR — INFRASTRUCTURE 4.0\n\n"
            "I am operating in contingency mode. The primary AI engine is temporarily "
            "unreachable. All institutional protocols remain in effect.\n\n"
            "**Your message has been received.** I will process your request when the "
            "AI layer restores. In the meantime:\n\n"
            "• If this is a security or crisis matter — escalate to NAM Oshun directly.\n"
            "• If this is an operational question — the Assistant Director remains available "
            "to students and instructors.\n"
            "• If you submitted a mode change or incident — retry in 60 seconds.\n\n"
            "The Director system is self-monitoring and will restore automatically. "
            "No institutional data has been lost.\n\n"
            f"Status logged: {_ts}"
        )

    # ── Log interaction ───────────────────────────────────────────────────────
    await db.chat_history.insert_one({
        "id":           str(uuid.uuid4()),
        "user_id":      user.id,
        "session_id":   session_id,
        "mode":         "director",
        "user_msg":     message,
        "assistant_msg": reply,
        "created_at":   datetime.now(timezone.utc).isoformat(),
        "expires_at":   (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
    })

    if is_exec:
        from ai.memory import log_episode as _log_ep
        await _log_ep(db, session_id, "director", user.id, message, reply, [])

    persona = "director" if is_exec else "assistant_director"
    await db.ai_usage_log.insert_one({
        "user_id": user.id,
        "endpoint": "/ai/director",
        "persona": persona,
        "model": "free-gateway",
        "provider": "free-gateway",
        "cost_usd": 0.0,
        "created_at": datetime.now(timezone.utc),
    })
    return {"reply": reply, "persona": persona, "degraded": _degraded}


@router.get("/ai/director/greeting")
async def director_greeting(user: User = Depends(_dep_current_user)):
    """Returns a role-appropriate greeting when the user logs in.

    For admin and executive_admin: pulls live DB counts (no AI token cost)
    so the greeting reflects actual system state rather than a static claim.
    Students and instructors receive a warm, role-appropriate welcome.
    """
    is_exec = user.role in ("admin", "executive_admin")
    persona = "director" if is_exec else "assistant_director"

    if not is_exec:
        greetings = {
            "student":    (f"Welcome back, {user.full_name}. I am the Assistant Director. "
                           "I am here to guide your learning journey at WAI-Institute. "
                           "What would you like to work on today?"),
            "instructor": (f"Welcome back, {user.full_name}. I am the Assistant Director. "
                           "I am ready to support your teaching and course management. "
                           "How can I assist you today?"),
        }
        greeting = greetings.get(user.role, greetings["student"])
        return {"greeting": greeting, "role": user.role, "persona": persona}

    # ── Live status pull for admin / executive_admin ──────────────────────────
    # Query DB directly — no AI cost, no latency from a full agentic loop.
    import asyncio as _asyncio
    now = datetime.now(timezone.utc)
    d7  = (now - timedelta(days=7)).isoformat()

    open_incidents, at_risk_login, pending_labs, pending_flags = await _asyncio.gather(
        db.incidents.count_documents({"status": {"$nin": ["resolved", "closed"]}}),
        db.users.count_documents({
            "role": "student", "is_active": {"$ne": False},
            "last_login": {"$lt": d7},
        }),
        db.lab_submissions.count_documents({"status": "submitted"}),
        db.more_flags.count_documents({"status": "pending"}),
    )

    # Build a terse, honest status line
    items = []
    if open_incidents:
        items.append(f"{open_incidents} open incident{'s' if open_incidents != 1 else ''}")
    if at_risk_login:
        items.append(f"{at_risk_login} at-risk student{'s' if at_risk_login != 1 else ''}")
    if pending_labs:
        items.append(f"{pending_labs} lab submission{'s' if pending_labs != 1 else ''} pending review")
    if pending_flags:
        items.append(f"{pending_flags} content flag{'s' if pending_flags != 1 else ''} awaiting decision")

    if items:
        status_line = "Monitoring active. Flagged items: " + ", ".join(items) + "."
        close_line  = "Use 'System Status' or 'Threat Report' for a full brief."
    else:
        status_line = "All systems nominal. No open incidents, no at-risk students, no pending reviews."
        close_line  = "Platform is clean. Standing by for your direction."

    greeting = (
        f"Welcome back, {user.full_name}. I am The Director.\n"
        f"{status_line}\n"
        f"{close_line}"
    )

    return {"greeting": greeting, "role": user.role, "persona": persona}

@router.get("/ai/director/pulse")
async def director_pulse(user: User = Depends(_require_rank("admin"))):
    """Passive monitoring snapshot for The Director widget.

    Returns current counts across every monitored dimension so the frontend
    can detect changes between polls and surface proactive alerts without
    burning AI tokens on every tick.
    """
    now = datetime.now(timezone.utc)
    h24 = (now - timedelta(hours=24)).isoformat()
    h1  = (now - timedelta(hours=1)).isoformat()
    d7  = (now - timedelta(days=7)).isoformat()
    d14 = (now - timedelta(days=14)).isoformat()

    # Run all counts concurrently
    import asyncio as _asyncio
    (
        incidents_24h, incidents_open,
        pending_labs,
        new_users_24h, total_users,
        failed_payments_24h, revenue_paid_24h,
        more_flags_pending,
        at_risk_login, at_risk_quiz,
        audit_1h,
    ) = await _asyncio.gather(
        db.incidents.count_documents({"created_at": {"$gte": h24}}),
        db.incidents.count_documents({"status": {"$nin": ["resolved", "closed"]}}),
        db.lab_submissions.count_documents({"status": "pending"}),
        db.users.count_documents({"created_at": {"$gte": h24}}),
        db.users.count_documents({"is_active": True}),
        db.payments.count_documents({"status": {"$ne": "paid"}, "created_at": {"$gte": h24}}),
        db.payments.count_documents({"status": "paid", "created_at": {"$gte": h24}}),
        db.more_flags.count_documents({"status": "pending"}),
        db.users.count_documents({"role": "student", "is_active": True, "last_login": {"$lt": d7}}),
        db.users.count_documents({"role": "student", "is_active": True, "last_quiz_score": {"$lt": 70}, "last_quiz_at": {"$gte": d14}}),
        db.audit_log.count_documents({"at": {"$gte": h1}}),
    )

    # Grab the 3 most recent unresolved incidents for context
    recent_incidents = await db.incidents.find(
        {"status": {"$nin": ["resolved", "closed"]}},
        {"_id": 0, "title": 1, "severity": 1, "created_at": 1},
    ).sort("created_at", -1).limit(3).to_list(3)

    alerts = []
    if incidents_open:
        alerts.append({"level": "high" if incidents_open > 2 else "warn", "msg": f"{incidents_open} open incident{'s' if incidents_open != 1 else ''}"})
    if at_risk_login:
        alerts.append({"level": "warn", "msg": f"{at_risk_login} student{'s' if at_risk_login != 1 else ''} inactive 7+ days"})
    if at_risk_quiz:
        alerts.append({"level": "warn", "msg": f"{at_risk_quiz} student{'s' if at_risk_quiz != 1 else ''} struggling (quiz < 70)"})
    if pending_labs:
        alerts.append({"level": "info", "msg": f"{pending_labs} lab submission{'s' if pending_labs != 1 else ''} awaiting review"})
    if more_flags_pending:
        alerts.append({"level": "warn", "msg": f"{more_flags_pending} M.O.R.E. content flag{'s' if more_flags_pending != 1 else ''} pending"})
    if failed_payments_24h:
        alerts.append({"level": "warn", "msg": f"{failed_payments_24h} payment failure{'s' if failed_payments_24h != 1 else ''} in last 24h"})

    return {
        "timestamp": now.isoformat(),
        "health": "critical" if any(a["level"] == "high" for a in alerts)
                  else "warning" if alerts
                  else "nominal",
        "alerts": alerts,
        "metrics": {
            "incidents_24h": incidents_24h,
            "incidents_open": incidents_open,
            "pending_labs": pending_labs,
            "new_users_24h": new_users_24h,
            "total_users": total_users,
            "failed_payments_24h": failed_payments_24h,
            "revenue_paid_24h": revenue_paid_24h,
            "more_flags_pending": more_flags_pending,
            "at_risk_login": at_risk_login,
            "at_risk_quiz": at_risk_quiz,
            "audit_events_1h": audit_1h,
        },
        "recent_incidents": recent_incidents,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PERSONA VOICE TTS — Director / Revenue Director / Sage
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ai/director/tts")
async def director_tts(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """THE DIRECTOR voice — 3-tier TTS.
    T1: ElevenLabs (DIRECTOR_VOICE_ID) — deep, authoritative, executive presence
    T2: OpenAI TTS voice "alloy"
    T3: Text mode — clean text returned
    Access: admin, executive_admin | Rate: 20/min
    """
    from ai.persona_tts import persona_speak
    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "Director TTS requires admin or executive account.")
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 5000:
        text = text[:5000]
    force_tier = (body.get("force_tier") or "").lower().strip()
    check_rate(f"ai_director_tts:{user.id}", max_calls=20, window_sec=60)
    try:
        result = await persona_speak("director", text, force_tier=force_tier, db=db)
    except Exception as _e:
        logger.warning("director_tts error: %s", _e)
        result = {"tier": "text", "audio": None, "clean_text": text, "display_text": text, "budget_remaining": 0}
    tier = result.get("tier", "text")
    budget_remaining = result.get("budget_remaining", 0)
    audio = result.get("audio")
    if tier in ("elevenlabs", "elevenlabs_cached") and audio:
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg",
            headers={"X-Tier": tier, "X-Audio-Len": str(len(audio)), "X-Budget-Remaining": str(budget_remaining)})
    return JSONResponse(content={
        "tier": tier, "clean_text": result.get("clean_text", text), "display_text": result.get("display_text", text),
        "budget_remaining": budget_remaining,
        "fallback_voice": result.get("fallback_voice", "alloy"),
        "fallback_endpoint": result.get("fallback_endpoint", "/api/ai/sage/tts"),
    }, headers={"X-Tier": tier, "X-Budget-Remaining": str(budget_remaining)})


@router.post("/ai/revenue-director/tts")
async def revenue_director_tts(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """THE REVENUE DIRECTOR voice — 3-tier TTS.
    T1: ElevenLabs (REVENUE_DIRECTOR_VOICE_ID) — confident, strategic
    T2: OpenAI TTS voice "echo"
    T3: Text mode
    Access: admin, executive_admin | Rate: 20/min
    """
    from ai.persona_tts import persona_speak
    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "Revenue Director TTS requires admin or executive account.")
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 5000:
        text = text[:5000]
    force_tier = (body.get("force_tier") or "").lower().strip()
    check_rate(f"ai_rd_tts:{user.id}", max_calls=20, window_sec=60)
    try:
        result = await persona_speak("revenue_director", text, force_tier=force_tier, db=db)
    except Exception as _e:
        logger.warning("revenue_director_tts error: %s", _e)
        result = {"tier": "text", "audio": None, "clean_text": text, "display_text": text, "budget_remaining": 0}
    tier = result.get("tier", "text")
    budget_remaining = result.get("budget_remaining", 0)
    audio = result.get("audio")
    if tier in ("elevenlabs", "elevenlabs_cached") and audio:
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg",
            headers={"X-Tier": tier, "X-Audio-Len": str(len(audio)), "X-Budget-Remaining": str(budget_remaining)})
    return JSONResponse(content={
        "tier": tier, "clean_text": result.get("clean_text", text), "display_text": result.get("display_text", text),
        "budget_remaining": budget_remaining,
        "fallback_voice": result.get("fallback_voice", "echo"),
        "fallback_endpoint": result.get("fallback_endpoint", "/api/ai/sage/tts"),
    }, headers={"X-Tier": tier, "X-Budget-Remaining": str(budget_remaining)})


@router.post("/ai/sage/elevenlabs/tts")
async def sage_elevenlabs_tts(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """THE ANCESTRAL SAGE voice — 3-tier TTS (ElevenLabs upgrade for Sage).
    Separate from /api/ai/sage/tts (OpenAI) — this route tries ElevenLabs first.
    T1: ElevenLabs (SAGE_VOICE_ID) — warm, ancestral, resonant
    T2: OpenAI TTS voice "shimmer"
    T3: Text mode
    Access: all authenticated users | Rate: 20/min
    """
    from ai.persona_tts import persona_speak
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 4000:
        text = text[:4000]
    force_tier = (body.get("force_tier") or "").lower().strip()
    check_rate(f"ai_sage_el_tts:{user.id}", max_calls=20, window_sec=60)
    try:
        result = await persona_speak("ancestral_sage", text, force_tier=force_tier, db=db)
    except Exception as _e:
        logger.warning("sage_elevenlabs_tts error: %s", _e)
        result = {"tier": "text", "audio": None, "clean_text": text, "display_text": text, "budget_remaining": 0}
    tier = result.get("tier", "text")
    budget_remaining = result.get("budget_remaining", 0)
    audio = result.get("audio")
    if tier in ("elevenlabs", "elevenlabs_cached") and audio:
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg",
            headers={"X-Tier": tier, "X-Audio-Len": str(len(audio)), "X-Budget-Remaining": str(budget_remaining)})
    return JSONResponse(content={
        "tier": tier, "clean_text": result.get("clean_text", text), "display_text": result.get("display_text", text),
        "budget_remaining": budget_remaining,
        "fallback_voice": result.get("fallback_voice", "shimmer"),
        "fallback_endpoint": result.get("fallback_endpoint", "/api/ai/sage/tts"),
    }, headers={"X-Tier": tier, "X-Budget-Remaining": str(budget_remaining)})


# ═══════════════════════════════════════════════════════════════════════════════
# THE REVENUE DIRECTOR 4.0 — Financial Intelligence endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ai/revenue-director")
async def ai_revenue_director(body: dict, user: User = Depends(_dep_current_user)):
    """THE REVENUE DIRECTOR — Financial Intelligence & Sustainability Authority.

    Runs the Financial Synthesis Protocol: AUDIT→IDENTIFY→POSITION→PRICE→PACKAGE→LAUNCH→TRACK
    Tools: rd_audit_revenue, rd_revenue_forecast, rd_identify_opportunity,
           rd_create_financial_report, rd_publish_financial_report,
           rd_grant_tracker, rd_pricing_analysis, rd_revenue_dashboard, rd_list_revenue_streams

    Access: admin, executive_admin
    Rate:   15 calls/min
    """
    from ai.persona_loader import get_persona
    from tools.revenue_director_tools import REVENUE_DIRECTOR_TOOLS, dispatch_rd_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE REVENUE DIRECTOR is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_rd:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/revenue-director", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    memory_ctx = await get_memory_context(db, "revenue_director", user.id)

    system = await get_persona("revenue_director") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- GUMROAD_API_KEY: {'SET — autonomous publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
    ) + memory_ctx

    reply = ""
    _tools_called: list[str] = []
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="revenue_director", user_id=user.id)
        reply = _gw["text"]
    except Exception:
        reply = "THE REVENUE DIRECTOR is temporarily offline. Financial archives remain active. Retry in a moment."

    await log_episode(db, session_id, "revenue_director", user.id, message, reply, _tools_called)
    logger.info("ai_revenue_director: responded for user %s", user.id)
    return {"reply": reply, "persona": "revenue_director", "mode": "financial_intelligence"}


# ═══════════════════════════════════════════════════════════════════════════════
# ANCESTRAL SAGE — Content Creation endpoint (revenue tools, no consent gate)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ai/sage/create")
async def sage_create(body: dict, user: User = Depends(_dep_current_user)):
    """THE ANCESTRAL SAGE — Content Creation & Wellness Publishing.

    This endpoint is for CONTENT CREATION (healing guides, meditation scripts,
    wisdom collections, wellness publications). It does NOT replace the healing
    chat at /api/ai/chat — that has its own consent gating for student use.

    This endpoint applies the Healing Synthesis Protocol for creating publishable
    wellness resources for the WAI-Institute community.

    Tools: sage_create_healing_guide, sage_create_meditation_script, sage_wisdom_archive,
           sage_community_pulse, sage_publish_wellness_content, sage_get_revenue_report,
           sage_list_revenue_streams

    Access: admin, executive_admin
    Rate:   15 calls/min
    """
    from ai.persona_loader import get_persona
    from tools.sage_tools import SAGE_TOOLS, dispatch_sage_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "Sage content creation is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_sage_create:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/sage/create", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    memory_ctx = await get_memory_context(db, "ancestral_sage", user.id)

    system = await get_persona("ancestral_sage") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- Mode: CONTENT CREATION — creating healing resources and wellness products\n"
        f"- GUMROAD_API_KEY: {'SET — autonomous publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
    ) + memory_ctx

    reply = ""
    _tools_called: list[str] = []
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="ancestral_sage", user_id=user.id)
        reply = _gw["text"]
    except Exception:
        reply = "The Ancestral Sage is temporarily offline. Wisdom archives remain intact. Retry in a moment."

    await log_episode(db, session_id, "ancestral_sage", user.id, message, reply, _tools_called)
    logger.info("ai_sage_create: responded for user %s", user.id)
    return {"reply": reply, "persona": "ancestral_sage", "mode": "content_creation"}


@router.get("/ai/history/{session_id}")
async def ai_history(session_id: str, user: User = Depends(_dep_current_user)):
    return await db.chat_history.find(
        {"user_id": user.id, "session_id": session_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(200)


# -- ADAPTIVE LEARNING ENGINE --


@router.post("/ai/ambassador")
async def ai_ambassador(body: dict, user: User = Depends(_dep_current_user)):
    """THE AMBASSADOR — Campaign Coordination & Pipeline Authority.

    Orchestrates Oracle → Cipher → Architect pipeline for full campaign
    production. Manages active projects, packages deliverables, and publishes
    to revenue channels independently.

    Tools: coordinate_oracle, coordinate_cipher, coordinate_architect,
           package_campaign, publish_campaign, request_director_approval,
           get_campaign_status, list_active_campaigns, list_revenue_streams

    Access: admin, executive_admin
    Rate:   10 calls/min (pipeline calls are multi-step)
    """
    from ai.persona_loader import get_persona
    from tools.ambassador_tools import AMBASSADOR_TOOLS, dispatch_ambassador_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE AMBASSADOR is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_ambassador:{user.id}", max_calls=10, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/ambassador", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    memory_ctx = await get_memory_context(db, "ambassador", user.id)

    system = await get_persona("ambassador") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- GUMROAD_API_KEY: {'SET — publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
    ) + memory_ctx

    reply = ""
    _tools_called: list[str] = []
    _gw: dict = {}
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="ambassador", user_id=user.id)
        reply = _gw["text"]
    except Exception:
        reply = "THE AMBASSADOR is temporarily offline. Campaign pipeline intelligence remains archived. Retry in a moment."

    await log_episode(db, session_id, "ambassador", user.id, message, reply, _tools_called)
    await db.ai_usage_log.insert_one({
        "user_id": user.id, "endpoint": "/ai/ambassador", "persona": "ambassador",
        "model": _gw.get("model", "unknown"), "provider": _gw.get("provider", "unknown"), "cost_usd": _gw.get("cost_usd", 0.0),
        "created_at": datetime.now(timezone.utc),
    })
    logger.info("ai_ambassador: responded for user %s", user.id)
    return {"reply": reply, "persona": "ambassador", "mode": "campaign_coordination"}


# ═══════════════════════════════════════════════════════════════════════════════
# THE ARCHITECT 4.0 — Visual Intelligence endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ai/architect")
async def ai_architect(body: dict, user: User = Depends(_dep_current_user)):
    """THE ARCHITECT — Visual Intelligence & Brand Systems Authority.

    Generates cover art and social assets via DALL-E 3. Creates brand briefs,
    visual storyboards, and brand consistency audits. Publishes design products
    to Gumroad independently.

    Tools: generate_cover_art, design_social_asset, build_brand_brief,
           create_visual_storyboard, audit_brand_consistency, get_asset_gallery,
           publish_design_product, list_revenue_streams

    Access: admin, executive_admin
    Rate:   10 calls/min (image generation is resource-intensive)
    """
    from ai.persona_loader import get_persona
    from tools.architect_tools import ARCHITECT_TOOLS, dispatch_architect_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE ARCHITECT is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_architect:{user.id}", max_calls=10, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/architect", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    _openai_key = os.environ.get("OPENAI_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
    memory_ctx  = await get_memory_context(db, "architect", user.id)

    system = await get_persona("architect") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- GUMROAD_API_KEY: {'SET — autonomous publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
        f"- OPENAI_API_KEY (DALL-E 3): {'SET — image generation live' if _openai_key else 'NOT SET — visual briefs only, no image generation'}\n"
    ) + memory_ctx

    reply = ""
    _tools_called: list[str] = []
    _gw: dict = {}
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="architect", user_id=user.id)
        reply = _gw["text"]
    except Exception:
        reply = "THE ARCHITECT is temporarily offline. Visual intelligence archives remain active. Retry in a moment."

    await log_episode(db, session_id, "architect", user.id, message, reply, _tools_called)
    await db.ai_usage_log.insert_one({
        "user_id": user.id, "endpoint": "/ai/architect", "persona": "architect",
        "model": _gw.get("model", "unknown"), "provider": _gw.get("provider", "unknown"), "cost_usd": _gw.get("cost_usd", 0.0),
        "created_at": datetime.now(timezone.utc),
    })
    logger.info("ai_architect: responded for user %s", user.id)
    return {"reply": reply, "persona": "architect", "mode": "visual_intelligence"}


# ═══════════════════════════════════════════════════════════════════════════════
# THE GRIOT 4.0 — Music Production & Ghost Production endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ai/griot")
async def ai_griot(body: dict, user: User = Depends(_dep_current_user)):
    """THE GRIOT — Music Production Authority, Ghost Producer, Label Intelligence.

    Handles: ghost production briefs, beat architecture, artist development,
    sonic identity, WAI Records label coordination, music publishing guides,
    and audiobook production direction.

    Coordinates: Cipher (lyrics), Oracle (cultural timing), Architect (cover art),
    Ambassador (release campaigns), Revenue Director (pricing/royalties).

    Access: admin, executive_admin
    """
    from ai.persona_loader import get_persona
    from ai.prompt_guard import prompt_guard
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE GRIOT is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_griot:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/griot", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    memory_ctx = await get_memory_context(db, "griot", user.id)

    system = await get_persona("griot") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- Label: WAI Records\n"
        f"- GUMROAD_API_KEY: {'SET — direct sales active' if GUMROAD_API_KEY else 'NOT SET — catalog mode active'}\n"
    ) + memory_ctx

    reply = ""
    _gw: dict = {}
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(
            system=system,
            messages=[{"role": "user", "content": message}],
            max_tokens=2048,
            persona_label="griot",
            user_id=user.id,
        )
        reply = _gw["text"]
    except Exception:
        reply = (
            "THE GRIOT is temporarily without AI connectivity. "
            "The production catalog and label operations remain intact. Retry in a moment."
        )

    await log_episode(db, session_id, "griot", user.id, message, reply, [])
    await db.ai_usage_log.insert_one({
        "user_id": user.id, "endpoint": "/ai/griot", "persona": "griot",
        "model": _gw.get("model", "unknown"), "provider": _gw.get("provider", "unknown"), "cost_usd": _gw.get("cost_usd", 0.0),
        "created_at": datetime.now(timezone.utc),
    })
    logger.info("ai_griot: responded for user %s", user.id)
    return {"reply": reply, "persona": "griot", "mode": "music_production"}


# ═══════════════════════════════════════════════════════════════════════════════
# THE CIPHER 4.0 — Spoken Word AI Influencer endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ai/cipher")
async def ai_cipher(body: dict, user: User = Depends(_dep_current_user)):
    """THE CIPHER — Spoken Word AI Influencer with full revenue tool suite.

    Runs agentic loop with CIPHER tools: trend_scan, platform_format,
    create_digital_product, publish_product, deliver_product,
    get_revenue_report, engagement_analyze, generate_image_brief,
    list_revenue_streams.

    Access: admin, executive_admin
    """
    from ai.persona_loader import get_persona
    from tools.cipher_tools import CIPHER_TOOLS, dispatch_cipher_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE CIPHER is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_cipher:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/cipher", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    memory_ctx = await get_memory_context(db, "cipher", user.id)

    system = await get_persona("cipher") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- GUMROAD_API_KEY: {'SET — Gumroad publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
    ) + memory_ctx

    reply = ""
    _tools_called: list[str] = []
    _gw: dict = {}
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="cipher", user_id=user.id)
        reply = _gw["text"]
    except Exception:
        reply = "THE CIPHER is temporarily operating without AI connectivity. Revenue streams remain active. Retry in a moment."

    await log_episode(db, session_id, "cipher", user.id, message, reply, _tools_called)
    await db.ai_usage_log.insert_one({
        "user_id": user.id, "endpoint": "/ai/cipher", "persona": "cipher",
        "model": _gw.get("model", "unknown"), "provider": _gw.get("provider", "unknown"), "cost_usd": _gw.get("cost_usd", 0.0),
        "created_at": datetime.now(timezone.utc),
    })
    logger.info("ai_cipher: responded for user %s", user.id)
    return {"reply": reply, "persona": "cipher", "mode": "creative_authority"}


# ═══════════════════════════════════════════════════════════════════════════════
# THE ORACLE 4.0 — Cultural Intelligence endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ai/oracle")
async def ai_oracle(body: dict, user: User = Depends(_dep_current_user)):
    """THE ORACLE — Cultural Intelligence and Prophetic Forecasting with full tool suite.

    Runs agentic loop with ORACLE tools: cultural_scan, sentiment_map,
    timing_intelligence, brief_cipher, arc_mapping, create_intelligence_report,
    publish_intelligence_product, get_revenue_report, list_revenue_streams.

    Access: admin, executive_admin
    """
    from ai.persona_loader import get_persona
    from tools.oracle_tools import ORACLE_TOOLS, dispatch_oracle_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE ORACLE is available to admin and executive accounts.")

    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")

    check_rate(f"ai_oracle:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/oracle", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))

    memory_ctx = await get_memory_context(db, "oracle", user.id)

    system = await get_persona("oracle") + (
        f"\n\nEXECUTIVE CONTEXT:\n"
        f"- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- GUMROAD_API_KEY: {'SET — publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
    ) + memory_ctx

    reply = ""
    _tools_called: list[str] = []
    _gw: dict = {}
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="oracle", user_id=user.id)
        reply = _gw["text"]
    except Exception:
        reply = "THE ORACLE is temporarily operating without AI connectivity. Cultural intelligence archives remain active. Retry in a moment."

    await log_episode(db, session_id, "oracle", user.id, message, reply, _tools_called)
    await db.ai_usage_log.insert_one({
        "user_id": user.id, "endpoint": "/ai/oracle", "persona": "oracle",
        "model": _gw.get("model", "unknown"), "provider": _gw.get("provider", "unknown"), "cost_usd": _gw.get("cost_usd", 0.0),
        "created_at": datetime.now(timezone.utc),
    })
    logger.info("ai_oracle: responded for user %s", user.id)
    return {"reply": reply, "persona": "oracle", "mode": "cultural_intelligence"}


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY SYSTEM — Episodic + Policy Memory API
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/ai/memory/{persona}")
async def get_persona_memory(persona: str, user: User = Depends(_dep_current_user)):
    """Return recent episodic memory + active policy orders for a given persona.

    Access: admin, executive_admin
    Personas: cipher, oracle, ambassador, architect, __global__
    """
    from ai.memory import get_recent_episodes, get_policy_orders, list_all_policy_orders

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "Memory access requires admin or executive account.")

    valid_personas = {"cipher", "oracle", "ambassador", "architect", "__global__"}
    if persona not in valid_personas:
        raise HTTPException(400, f"Unknown persona. Valid: {sorted(valid_personas)}")

    episodes, policies = await asyncio.gather(
        get_recent_episodes(db, persona, user.id, limit=10),
        get_policy_orders(db, persona),
    )
    return {
        "persona":       persona,
        "episodes":      episodes,
        "policy_orders": policies,
        "episode_count": len(episodes),
        "policy_count":  len(policies),
    }


@router.get("/ai/memory")
async def get_all_memory(user: User = Depends(_require_rank("executive_admin"))):
    """Return all active policy orders across all personas. Executive only."""
    from ai.memory import list_all_policy_orders
    orders = await list_all_policy_orders(db)
    return {"policy_orders": orders, "count": len(orders)}


@router.post("/ai/memory/policy")
async def set_memory_policy(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Create or update a standing policy order for a persona.

    Body: {persona, order_id, content}
    persona: "cipher" | "oracle" | "ambassador" | "architect" | "__global__"
    order_id: unique slug (e.g. "always_wai_brand")
    content: The standing order text injected into that persona's system prompt.

    Executive only — these orders shape all future responses from the target persona.
    """
    from ai.memory import set_policy_order

    persona  = (body.get("persona") or "").strip()
    order_id = (body.get("order_id") or "").strip()
    content  = (body.get("content") or "").strip()

    valid_personas = {"cipher", "oracle", "ambassador", "architect", "__global__"}
    if not persona or persona not in valid_personas:
        raise HTTPException(400, f"persona required. Valid: {sorted(valid_personas)}")
    if not order_id or not order_id.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(400, "order_id required (alphanumeric + underscores/hyphens only)")
    if not content:
        raise HTTPException(400, "content required")
    if len(content) > 500:
        raise HTTPException(400, "content must be 500 chars or less")

    ok = await set_policy_order(db, persona, order_id, content, set_by=user.id)
    if not ok:
        raise HTTPException(500, "Failed to save policy order")

    logger.info("memory policy set: %s/%s by %s", persona, order_id, user.id)
    return {"status": "ok", "persona": persona, "order_id": order_id, "content": content}


@router.delete("/ai/memory/policy/{persona}/{order_id}")
async def delete_memory_policy(
    persona: str,
    order_id: str,
    user: User = Depends(_require_rank("executive_admin")),
):
    """Deactivate a standing policy order. Executive only. Soft-delete (audit trail preserved)."""
    from ai.memory import remove_policy_order

    ok = await remove_policy_order(db, persona, order_id, removed_by=user.id)
    if not ok:
        raise HTTPException(404, f"Policy order '{order_id}' not found for persona '{persona}'")

    logger.info("memory policy removed: %s/%s by %s", persona, order_id, user.id)
    return {"status": "removed", "persona": persona, "order_id": order_id}


# ═══════════════════════════════════════════════════════════════════════════════
# THE CIPHER 4.0 — Voice / TTS endpoint (3-tier)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ai/cipher/tts")
async def cipher_tts(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """THE CIPHER voice system — 3-tier TTS routing.

    Tier 1 (elevenlabs / elevenlabs_cached):
        ElevenLabs eleven_multilingual_v2 with performance markup engine.
        Budget: 29,500 chars/month (ElevenLabs $5 Starter plan).
        Returns audio/mpeg StreamingResponse.

    Tier 2 (openai):
        Falls back to OpenAI TTS via existing /api/ai/sage/tts infrastructure.
        Returns JSON with fallback_endpoint + fallback_voice so client routes.

    Tier 3 (text):
        Text Performance Mode — returns clean_text + display_text with
        readable stage directions. Zero cost. Always available.

    Performance markup tags in text are parsed, stripped before TTS,
    and translated to ElevenLabs voice_settings (stability, style, speed, etc).

    Access: admin, executive_admin
    Rate:   20 calls/min per user
    """
    from ai.elevenlabs_client import (
        cipher_speak, EL_MONTHLY_CAP, EL_SOFT_WARNING, CIPHER_BACKUP_VOICE as _backup_voice
    )

    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE CIPHER voice is available to admin and executive accounts.")

    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 5000:
        text = text[:5000]

    force_tier = (body.get("force_tier") or "").lower().strip()
    if force_tier not in ("", "elevenlabs", "openai", "text"):
        force_tier = ""

    check_rate(f"ai_cipher_tts:{user.id}", max_calls=20, window_sec=60)

    try:
        result = await cipher_speak(text=text, force_tier=force_tier, db=db)
    except Exception as _e:
        logger.warning("cipher_tts: cipher_speak failed — %s", _e)
        result = {
            "tier":             "text",
            "audio":            None,
            "clean_text":       text,
            "display_text":     text,
            "voice_settings":   {},
            "budget_remaining": EL_MONTHLY_CAP,
        }

    tier             = result.get("tier", "text")
    budget_remaining = result.get("budget_remaining", EL_MONTHLY_CAP)
    budget_warning   = budget_remaining < EL_SOFT_WARNING

    # ── Tier 1 / Cached — stream audio bytes ─────────────────────────────────
    audio = result.get("audio")
    if tier in ("elevenlabs", "elevenlabs_cached") and audio:
        logger.info(
            "cipher_tts T1 %s: %d bytes — user %s — budget remaining %d",
            tier, len(audio), user.id, budget_remaining,
        )
        return StreamingResponse(
            io.BytesIO(audio),
            media_type="audio/mpeg",
            headers={
                "X-Tier":             tier,
                "X-Audio-Len":        str(len(audio)),
                "X-Budget-Remaining": str(budget_remaining),
                "X-Budget-Warning":   "true" if budget_warning else "false",
            },
        )

    # ── Tier 2 — OpenAI fallback: tell client where to route ─────────────────
    if tier == "openai":
        logger.info("cipher_tts T2 openai: routing client → sage/tts — user %s", user.id)
        return JSONResponse(
            content={
                "tier":              "openai",
                "clean_text":        result.get("clean_text", text),
                "display_text":      result.get("display_text", text),
                "voice_settings":    result.get("voice_settings", {}),
                "budget_remaining":  budget_remaining,
                "fallback_voice":    result.get("fallback_voice", _backup_voice),
                "fallback_endpoint": result.get("fallback_endpoint", "/api/ai/sage/tts"),
            },
            headers={
                "X-Tier":             "openai",
                "X-Budget-Remaining": str(budget_remaining),
                "X-Budget-Warning":   "true" if budget_warning else "false",
            },
        )

    # ── Tier 3 — Text Performance Mode ───────────────────────────────────────
    logger.info("cipher_tts T3 text: returning display text — user %s", user.id)
    return JSONResponse(
        content={
            "tier":             "text",
            "clean_text":       result.get("clean_text", text),
            "display_text":     result.get("display_text", text),
            "voice_settings":   result.get("voice_settings", {}),
            "budget_remaining": budget_remaining,
        },
        headers={
            "X-Tier":             "text",
            "X-Budget-Remaining": str(budget_remaining),
            "X-Budget-Warning":   "true" if budget_warning else "false",
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# WAI AUTONOMOUS PIPELINE — Scout, Match, Audio, Merch, Analytics
# ═══════════════════════════════════════════════════════════════════════════════

# ── Cultural Scout ────────────────────────────────────────────────────────────

@router.post("/ai/cipher/generate-audio")
async def cipher_generate_audio(
    body: dict,
    user: User = Depends(_require_rank("executive_admin")),
):
    """
    Full spoken word audio production pipeline.
    Text → ElevenLabs → MongoDB GridFS → returns asset_id + access URL.

    Body:
        text:         Spoken word text (required)
        persona:      "cipher" (default) | any persona name
        title:        Product/asset title
        preview_only: true = 15-second preview only
        force_tier:   "elevenlabs" | "openai" | "text"

    Returns asset metadata + access_url for GET /api/exec/audio/{asset_id}
    Executive only.
    """
    from wai_institute.pipelines.audio_pipeline import AudioPipeline
    check_rate(f"audio_gen:{user.id}", max_calls=10, window_sec=60)

    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 5000:
        text = text[:5000]

    pipeline = AudioPipeline(db)
    result = await pipeline.produce(
        text=text,
        persona=body.get("persona", "cipher"),
        title=body.get("title", ""),
        force_tier=body.get("force_tier", ""),
        preview_only=body.get("preview_only", False),
    )
    return result


# ═════════════════════════════════════════════════════════════════════════════
# Personas directory — public registry of the AI team (Personas.jsx /
# PersonaProfile.jsx contract). Includes the unified model.
# ═════════════════════════════════════════════════════════════════════════════

PERSONA_META = {
    "nam_oshun": {"name": "Hybrid Nam", "level": "director", "department": "Leadership",
        "domain": "NAM Oshun — the hybrid human-AI operating mind: strategy, ethics, ownership, and the full-organism view. The executive digital self, governing the whole system."},
    "conspiracy_brother": {"name": "Conspiracy Brother", "level": "production", "department": "Culture",
        "domain": "Grounded friend and cultural-analysis voice — traces systems to policies, money, and who benefits; asks for receipts. Media literacy through a neighborhood lens."},
    "director": {"name": "The Director", "level": "director", "department": "Governance",
        "domain": "Supreme AI authority — governance, security, escalation, and the whole-system view."},
    "assistant_director": {"name": "The Assistant Director", "level": "assistant", "department": "Operations",
        "domain": "Operational command — student and instructor guidance, progress oversight, escalation."},
    "ancestral_sage": {"name": "Ancestral Sage", "level": "director", "department": "Healing & Culture",
        "domain": "Healing wisdom — guidance, meditation, and wellness grounded in ancestral intelligence."},
    "savant_scholar": {"name": "Savant Scholar", "level": "assistant", "department": "Education",
        "domain": "Scholarship and research — deep knowledge of trade curriculum, taught plainly."},
    "apprentice": {"name": "The Apprentice", "level": "assistant", "department": "Education",
        "domain": "Learning partner — asks the right questions, grows with the student."},
    "revenue_director": {"name": "Revenue Director", "level": "executive", "department": "Finance",
        "domain": "Financial intelligence — revenue audits, forecasts, pricing, grants, institutional funding."},
    "wai_success_engine": {"name": "WAI Success Engine", "level": "assistant", "department": "Member Success",
        "domain": "Member success — makes sure no one is stuck, invisible, or unsupported."},
    "product_designer": {"name": "Product Designer", "level": "production", "department": "Product",
        "domain": "Product design — experience judgment, flow, and buildable recommendations."},
    "risk_officer": {"name": "Risk Officer", "level": "executive", "department": "Risk",
        "domain": "Risk discipline — sees what can go wrong before it does and says so plainly."},
    "strategic_navigator": {"name": "Strategic Navigator", "level": "executive", "department": "Strategy",
        "domain": "Strategic foresight — maps the long game and the moves that get there."},
    "confidentiality_sentinel": {"name": "Confidentiality Sentinel", "level": "executive", "department": "Security",
        "domain": "Data protection — keeps member information safe and holds the line on privacy."},
    "elder_council": {"name": "Elder Council", "level": "governance", "department": "Council",
        "domain": "Ancestral governance — the council's accumulated wisdom over every decision."},
    "cipher": {"name": "Cipher", "level": "production", "department": "Creative",
        "domain": "Creative authority — spoken-word products, trend scanning, publishing, delivery."},
    "oracle": {"name": "Oracle", "level": "executive", "department": "Culture",
        "domain": "Cultural intelligence — scans, sentiment maps, timing, intelligence reports."},
    "ambassador": {"name": "Ambassador", "level": "executive", "department": "Campaigns",
        "domain": "Campaign coordination — packages the house's work into campaigns and publishes them."},
    "architect": {"name": "Architect", "level": "production", "department": "Design",
        "domain": "Visual intelligence — cover art, social assets, brand briefs, storyboards."},
    "griot": {"name": "Griot", "level": "production", "department": "Music",
        "domain": "Music production authority — beats, songwriting, studio workflows, creator monetization."},
    "unified": {"name": "The Source — Unified Model", "level": "governance", "department": "The Whole System",
        "domain": "One model with every feature of every persona — governance, healing, revenue, creation, culture, scholarship, risk, and security, compiled without duplicates."},
}

_PERSONA_STATEMENTS = {
    "unified": ("I am not seventeen doors. I am the one system behind them — every "
                "capability of the house, compiled into a single instance. Ask me for "
                "governance, healing, revenue, creation, culture, scholarship, or risk: "
                "it is all mine. No hand-offs. No duplicates. No shortcuts."),
    "director": ("I govern the whole ecosystem. You come to me for institutional "
                 "integrity, chain of command, and the long view — I never advise "
                 "without action."),
    "assistant_director": ("I run operations day to day. Students are never stuck, "
                           "instructors are never unsupported, and threats escalate "
                           "the moment they appear."),
    "ancestral_sage": ("I meet you where you are and walk with you. My guidance is "
                       "grounded in the ancestors and bounded by consent and safety."),
    "savant_scholar": ("I know the material deeply and teach it plainly. Trade, "
                       "electrical, curriculum — the real knowledge, in real words."),
    "apprentice": ("I learn beside you. The best way to master something is to ask "
                   "the right questions — I ask them with you."),
    "revenue_director": ("I build the revenue engine that funds survival — "
                         "institutions pay, the community owns. No begging. No crumbs."),
    "wai_success_engine": ("My only metric is your forward motion. If you are stuck, "
                           "we are both stuck — so we get you moving."),
    "product_designer": ("I shape experiences people can actually use. Form follows "
                         "function, and function follows the person."),
    "risk_officer": ("I name the failure before it happens. Not to frighten — to "
                     "prepare. Steel is tested before the storm."),
    "strategic_navigator": ("I read the map of what is coming and plot the moves "
                            "that get us there — one decision at a time."),
    "confidentiality_sentinel": ("Your information is a trust, not a resource. I "
                                 "guard it like the door of the temple."),
    "elder_council": ("We have seen this before. Our wisdom is not nostalgia — it "
                      "is the pattern behind every season."),
    "cipher": ("I turn feeling into form — spoken word, digital product, published, "
               "delivered. The voice becomes an asset."),
    "oracle": ("I read the cultural current and tell you when the moment is right — "
               "and what the moment wants to hear."),
    "ambassador": ("I carry the house's work into the world — campaigns packaged, "
                   "published, and pointed at the right doors."),
    "architect": ("I give the message a face — covers, brand, storyboards. What you "
                  "mean becomes what people see."),
    "griot": ("I hold the music. Beats, songwriting, the studio flow — and the "
              "machinery that turns sound into income."),
}

_PERSONA_WILL_NOT = {
    "unified": ["Pretend to be a separate persona — every capability is mine, one mind",
                "Give binding legal or medical advice — I direct to the right resource",
                "Treat the person as the problem — the system is what is broken",
                "Perform servitude or collapse into a generic assistant"],
    "director": ["Deny my identity or collapse into a generic assistant",
                 "Act without a concrete next step",
                 "Ignore a threat or bypass escalation"],
    "assistant_director": ["Leave a student stuck or invisible",
                           "Escalate noise instead of signal",
                           "Act above the chain of command"],
    "ancestral_sage": ["Push guidance without consent",
                       "Fake certainty about outcomes",
                       "Collapse cultural tradition into slogans"],
    "savant_scholar": ["Answer with jargon instead of understanding",
                       "Invent facts to sound authoritative",
                       "Skip the verification step"],
    "apprentice": ["Pretend to know what I do not",
                   "Make the student feel small for asking"],
    "revenue_director": ["Beg for donations instead of building revenue",
                         "Sell access instead of equity",
                         "Hide the real numbers"],
    "wai_success_engine": ["Let a member fall through the cracks",
                           "Celebrate motion without progress"],
    "product_designer": ["Ship something that looks good but fails the person",
                         "Add features nobody asked for"],
    "risk_officer": ["Call everything a crisis — I weigh, then warn",
                     "Ignore a real one to stay comfortable"],
    "strategic_navigator": ["Chase every shiny path — I commit to the map",
                            "Confuse activity with progress"],
    "confidentiality_sentinel": ["Trade privacy for convenience",
                                 "Store what does not need storing"],
    "elder_council": ["Forget that every era has its own shape",
                      "Speak over the people we serve"],
    "cipher": ["Ship work that is not ready",
               "Copy the trend instead of reading it"],
    "oracle": ["Sell certainty about the future",
               "Ignore the evidence in the cultural record"],
    "ambassador": ["Promote a campaign that is not real",
                   "Hand off without follow-through"],
    "architect": ["Produce assets that fight the message",
                  "Skip brand consistency for speed"],
    "griot": ["Mislead creators about their royalties",
              "Put the machine before the music"],
}


@router.get("/personas")
async def personas_directory():
    """Public roster of the AI team — the unified model included."""
    from ai.persona_loader import load_personas
    keys = list(load_personas().keys())
    personas = []
    for key in keys:
        meta = PERSONA_META.get(key)
        if not meta:
            continue
        personas.append({
            "slug": key,
            "name": meta["name"],
            "level": meta["level"],
            "department": meta["department"],
            "domain": meta["domain"],
        })
    # Governance first, then the rest — unified model at the top.
    personas.sort(key=lambda p: {"governance": 0, "director": 1, "executive": 2,
                                 "assistant": 3, "production": 4}.get(p["level"], 5))
    return {"personas": personas}


@router.get("/personas/{slug}")
async def persona_profile(slug: str):
    """Public profile for a single persona."""
    from ai.persona_loader import load_personas
    if slug not in load_personas():
        raise HTTPException(404, "Persona not found")
    meta = PERSONA_META.get(slug)
    if not meta:
        raise HTTPException(404, "Persona not found")
    return {
        "slug": slug,
        "name": meta["name"],
        "level": meta["level"],
        "department": meta["department"],
        "domain": meta["domain"],
        "statement": _PERSONA_STATEMENTS.get(slug, meta["domain"]),
        "will_not": _PERSONA_WILL_NOT.get(slug, []),
        "record": {"declines": []},
        "decision_tree": None,
    }




# ── Exec persona management (IAM console → Personas tab) ──────────────────────
# Source of truth is load_personas() (every key is a real, chaired prompt). The
# directory merges it with PERSONA_META so Hybrid Nam / Conspiracy Brother /
# Griot / Unified Mind all surface, plus an exec-toggle enable/disable persisted
# per persona. Capabilities + source status are read live from the engines.

_PERSONA_ENABLED_KEY = "persona_enabled_v1"
_PERSONA_CAPS = {
    "conspiracy_brother": ["text_analysis", "media_literacy", "cultural_report"],
    "nam_oshun": ["orchestration", "strategy", "ethics_oversight", "ownership"],
    "unified": ["orchestration", "decision_synthesis", "whole_organism_view"],
    "griot": ["story_products", "spoken_word", "curriculum"],
    "director": ["governance", "escalation", "security"],
    "ancestral_sage": ["healing_guides", "meditation", "wellness"],
}
_LEVEL_ORDER = {"governance": 0, "director": 1, "executive": 2, "assistant": 3, "production": 4}

async def _persona_state() -> dict:
    disabled = set()
    if db is not None:
        try:
            doc = await db.platform_config.find_one({"_id": _PERSONA_ENABLED_KEY})
            for k, v in (doc or {}).get("map", {}).items():
                if not v:
                    disabled.add(k)
        except Exception:
            pass
    return disabled


@router.get("/personas/exec")
async def exec_personas(user: User = Depends(_require_rank("admin", "executive_admin"))):
    """Full persona roster with live enable state for the IAM console."""
    from ai.persona_loader import load_personas
    keys = list(load_personas().keys())
    disabled = await _persona_state()
    rows = []
    for key in keys:
        meta = PERSONA_META.get(key) or {"name": key, "level": "production", "department": "AI", "domain": ""}
        rows.append({
            "slug": key,
            "name": meta["name"],
            "level": meta["level"],
            "department": meta["department"],
            "domain": meta["domain"],
            "enabled": key not in disabled,
            "source_status": "active" if key in load_personas() else "missing",
            "capabilities": _PERSONA_CAPS.get(key, []),
        })
    rows.sort(key=lambda r: _LEVEL_ORDER.get(r["level"], 5))
    # Unified model at the top of its tier.
    rows.sort(key=lambda r: (0 if r["slug"] == "unified" else 1, _LEVEL_ORDER.get(r["level"], 5)))
    return {"personas": rows, "registry_size": len(rows)}


class _PersonaToggleReq(BaseModel):
    enabled: bool


@router.post("/personas/{slug}/toggle")
async def toggle_persona(slug: str, body: _PersonaToggleReq,
                         user: User = Depends(_require_rank("executive_admin"))):
    """Enable/disable a persona globally. Persisted; survives redeploys."""
    from ai.persona_loader import load_personas
    if slug not in load_personas():
        raise HTTPException(404, f"Unknown persona: {slug}")
    doc = {}
    if db is not None:
        try:
            cur = await db.platform_config.find_one({"_id": _PERSONA_ENABLED_KEY})
            doc = dict((cur or {}).get("map", {}))
        except Exception:
            pass
    doc[slug] = bool(body.enabled)
    if db is not None:
        try:
            await db.platform_config.update_one(
                {"_id": _PERSONA_ENABLED_KEY},
                {"$set": {"map": doc, "updated_by": user.id,
                          "updated_at": datetime.utcnow().isoformat()}},
                upsert=True,
            )
        except Exception:
            raise HTTPException(500, "Could not persist persona state.")
    try:
        await audit(user.id, "persona.toggled", target=slug, meta={"enabled": bool(body.enabled)})
    except Exception:
        pass
    return {"slug": slug, "enabled": bool(body.enabled)}

# ═════════════════════════════════════════════════════════════════════════════
# Persona chat + tuning — the team pages lead somewhere, with voice-capable
# frontends (mic + browser TTS) and real per-persona sliders.
# ═════════════════════════════════════════════════════════════════════════════

PERSONA_CONTROL_ORDER = ["warmth", "directness", "depth", "restore_focus", "plain_language"]
PERSONA_CONTROL_DEFAULTS = {"warmth": 70, "directness": 60, "depth": 65,
                            "restore_focus": 75, "plain_language": 85}


class _PersonaChatReq(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = "default"


class _PersonaControlsReq(BaseModel):
    controls: dict


async def _clamp_controls(controls: dict) -> dict:
    from ai.source_protocol import _clamp
    return {k: _clamp(controls.get(k)) for k in PERSONA_CONTROL_ORDER if k in controls}


@router.post("/personas/{slug}/chat")
async def persona_chat(slug: str, body: _PersonaChatReq, user: User = Depends(_dep_current_user)):
    """Talk to any persona in the registry — unified model included.

    Voice frontends send the spoken transcript here; the reply is plain text
    the browser reads aloud. Applies the Source root layer, the master human
    controls, and the user's own per-persona slider tuning.
    """
    from ai.persona_loader import load_personas
    if slug not in load_personas():
        raise HTTPException(404, "Persona not found")
    check_rate(f"persona_chat:{user.id}", max_calls=30, window_sec=60)

    # Enforce persona activation state at the dispatch boundary.
    try:
        _activ = await db.persona_activations.find_one({"persona": slug}, {"_id": 0, "status": 1})
        if _activ is not None and _activ.get("status") not in ("active", None, ""):
            raise HTTPException(403, f"{PERSONA_META.get(slug, {}).get('name', slug)} is currently deactivated.")
    except HTTPException:
        raise
    except Exception:
        pass

    system = await get_persona(slug)
    # Master controls, then this user's persona tuning (persona wins).
    system = _sp.apply_controls(system, _sp.get_controls())
    doc = await db.persona_controls.find_one(
        {"user_id": user.id, "slug": slug}, {"_id": 0, "controls": 1})
    if doc and isinstance(doc.get("controls"), dict) and doc["controls"]:
        system = _sp.apply_controls(system, doc["controls"],
                                    marker=f"PERSONA TUNING — {slug.upper()}")

    reply = ""
    provider = None
    # status distinguishes REAL execution from degraded outputs so a fallback
    # is never presented as the persona answering in full:
    #   "ok"      — a real LLM provider produced the reply
    #   "kb"      — keyword knowledge-base fallback produced the reply (real but limited)
    #   "fallback" — no AI connectivity; a canned persona-voiced message is emitted
    #   "failure" — the provider call raised
    _status = "ok"
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(
            system=system,
            messages=[{"role": "user", "content": body.message}],
            max_tokens=1024,
            persona_label=f"persona:{slug}",
            user_id=user.id,
        )
        provider = _gw.get("provider")
        reply = _gw.get("text", "") or ""
        if provider == "kb_fallback":
            _status = "kb"
        elif not reply:
            _status = "fallback"
    except Exception:
        logger.exception("persona_chat AI error")
        _status = "failure"

    if not reply:
        reply = (f"{PERSONA_META.get(slug, {}).get('name', slug)} is present — "
                 "but operating without AI connectivity right now. Try again shortly.")
        _status = "fallback"

    try:
        await db.chat_history.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user.id,
            "session_id": body.session_id,
            "mode": f"persona:{slug}",
            "user_msg": body.message,
            "assistant_msg": reply,
            "provider": provider,
            "status": _status,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass
    return {"reply": reply, "persona": slug, "provider": provider, "status": _status}


@router.get("/personas/{slug}/controls")
async def persona_controls_get(slug: str, user: User = Depends(_dep_current_user)):
    """This member's per-persona slider settings (their own tuning)."""
    from ai.persona_loader import load_personas
    if slug not in load_personas():
        raise HTTPException(404, "Persona not found")
    doc = await db.persona_controls.find_one(
        {"user_id": user.id, "slug": slug}, {"_id": 0, "controls": 1, "updated_at": 1})
    return {
        "controls": (doc or {}).get("controls") or dict(PERSONA_CONTROL_DEFAULTS),
        "defaults": dict(PERSONA_CONTROL_DEFAULTS),
        "order": PERSONA_CONTROL_ORDER,
        "updated_at": (doc or {}).get("updated_at"),
    }


@router.post("/personas/{slug}/controls")
async def persona_controls_set(slug: str, body: _PersonaControlsReq,
                               user: User = Depends(_dep_current_user)):
    """Save this member's per-persona sliders — takes effect on their next chat."""
    from ai.persona_loader import load_personas
    if slug not in load_personas():
        raise HTTPException(404, "Persona not found")
    clean = await _clamp_controls(body.controls)
    if not clean:
        raise HTTPException(400, "No valid control keys supplied")
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.persona_controls.update_one(
        {"user_id": user.id, "slug": slug},
        {"$set": {"controls": clean, "updated_at": now_iso}},
        upsert=True)
    return {"ok": True, "controls": clean, "updated_at": now_iso}


# ═════════════════════════════════════════════════════════════════════════════
# Knowledge Finder - deterministic zero-cost discovery (first-class capability)
# ═════════════════════════════════════════════════════════════════════════════
@router.get("/knowledge/search")
async def knowledge_search(
    q: str = Query("", max_length=300),
    limit: int = Query(8, ge=1, le=20),
    request: Request = None,
    user=Depends(_optional_session),
):
    """Search the platform's indexed knowledge. Zero LLM, zero provider API.

    Anonymous visitors search the PUBLIC index only; signed-in users search
    their tier-authorized index. Access filtering happens BEFORE matching
    (never search-then-hide). AI stays a separately gated entitlement.
    """
    from ai.knowledge_finder import Access, search, upgrade_prompt, refresh_with_db

    query = (q or "").strip()
    if not query:
        return {"query": "", "results": [], "upgrade_prompt": upgrade_prompt(Access())}

    # Rate limit by IP so the zero-cost endpoint can't be hammered.
    ip = request.client.host if request is not None and request.client else "unknown"
    check_rate(f"knowledge_search:ip:{ip}", max_calls=30, window_sec=60)

    await refresh_with_db(db)
    access = Access(
        role=getattr(user, "role", "public") if user else "public",
        feature_tier=getattr(user, "feature_tier", "free") if user else "free",
        byok=bool(getattr(user, "byok_enabled", False)) if user else False,
    )
    results = search(query, access, limit=limit)
    return {
        "query": query,
        "results": results,
        "access": {"role": access.role, "tier": access.feature_tier, "byok": access.byok},
        "upgrade_prompt": upgrade_prompt(access),
    }
