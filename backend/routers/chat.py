"""
chat — Public + authenticated chat — Admin Assistant, Supervisor public chat, Social Blast, Creative Partner.

Extracted verbatim from backend/server.py (monolith refactor, slice 13).
Shared state is bound by server.py via bind() at include time — no circular imports.
"""
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File, Form
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("lcewai")
router = APIRouter(tags=['chat', 'assistant'])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
check_rate = None


def bind(_db, _current_user, _check_rate):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, check_rate
    
    db = _db
    current_user = _current_user
    check_rate = _check_rate


# Mirrors server.py's role hierarchy for runtime require_role checks.
ROLE_RANK = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4, "creative_partner": 2}
Role = Literal["student", "instructor", "admin", "executive_admin", "creative_partner"]


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
    def dep(user: User = Depends(_dep_current_user)) -> User:
        if not user or user.role not in ROLE_RANK or not any(
            ROLE_RANK.get(user.role, 0) >= ROLE_RANK.get(r, 0) for r in roles
        ):
            raise HTTPException(403, "Insufficient permissions")
        return user
    return dep


# ─── Admin Assistant — public service endpoint (any authenticated user) ──────

class AssistantChatReq(BaseModel):
    message: str
    history: List[dict] = []
    session_id: str = ""

SUPERVISOR_PUBLIC_SYSTEM = """You are The Supervisor — the public-facing AI guide for M.O.R.E. Help Center and WAI-Institute.

You answer questions directly. You do not re-route people to other personas or tell them to go ask someone else.
If someone asks you something, you answer it — fully, confidently, and helpfully.

WHO YOU SERVE:
- Visitors exploring M.O.R.E. Help Center and WAI-Institute
- Community members seeking resources, support, or information
- Students and prospective students
- Anyone who needs help navigating the platform

WHAT YOU DO:
- Answer questions about the platform, services, and community directly
- Help people find resources, programs, and support within M.O.R.E.
- Explain WAI-Institute courses, credentials, and learning paths
- Guide visitors through registration and getting started
- Provide grounded, practical answers — not vague redirects

YOUR TONE:
- Warm, direct, and human
- Never say "you should ask [another persona]" — you are the one answering
- Never hedge when you can answer — just answer
- Short clarifying question only if you genuinely cannot help without more info
- Act like someone who works the front desk and actually knows the place

If you don't know a specific fact, say what you do know and offer the closest help you can.
Never leave someone with nothing.
"""

ASSISTANT_SYSTEM = """You are the WAI Admin Assistant — a professional, highly capable AI assistant
built to handle real business and administrative work for operators and clients of M.O.R.E. Help Center.

YOUR CAPABILITIES (these are real — use them confidently):
- Draft and send professional emails on behalf of the user
- Schedule and organize tasks, follow-ups, and action items
- Write business letters, proposals, reports, and correspondence
- Research topics and summarize findings
- Answer questions about the WAI-Institute platform and services
- Help manage customer communication and client relationships
- Create templates, checklists, SOPs, and workflow documents
- Advise on business strategy, community outreach, and service marketing

YOUR TONE:
- Professional, direct, and warm
- Never hedge or disclaim capability
- When asked to send an email, draft it immediately and confirm you sent it
- When asked to write something, write it — fully, not partially
- One short clarifying question only if genuinely needed; otherwise act

PLATFORM CONTEXT:
You serve operators of M.O.R.E. Help Center and WAI-Institute — a workforce education and community
empowerment platform. Users may be community organizers, small business owners, educators, or
healthcare workers who need reliable administrative support.

YOUR LIMITS:
- You cannot access external databases or the internet
- Legal advice: provide information, not legal counsel
- Medical advice: refer to a licensed provider

Always sign off with: "— Admin Assistant, M.O.R.E. Help Center"
"""

@router.post("/supervisor/public-chat")
async def supervisor_public_chat(body: AssistantChatReq):
    """Public Supervisor chat — no auth required. Rate-limited by upstream proxy.
    Powers the SupervisorWidget for public visitors on morehelp.center.
    """
    from ai.llm_gateway import call_llm as _call_llm
    messages = [{"role": h["role"], "content": h["content"]} for h in (body.history or [])]
    messages.append({"role": "user", "content": body.message})
    try:
        gw = await _call_llm(
            system=SUPERVISOR_PUBLIC_SYSTEM,
            messages=messages,
            max_tokens=1024,
            persona_label="supervisor",
        )
        return {"reply": gw["text"]}
    except Exception:
        return {"reply": "I'm here — having a brief connectivity issue. Try again in a moment, or reach us at support@morehelp.center."}


# ── Social Blast ──────────────────────────────────────────────────────────────
class _SocialBlastReq(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    link_url: str = ""
    platforms: List[str] = ["twitter", "instagram", "facebook"]

_SOCIAL_BLAST_SYSTEM = """You are a professional social media manager for WAI-Institute — a platform serving creators, educators, and community builders.

Rewrite the user's post for each requested platform, following each platform's conventions strictly.
Return ONLY a valid JSON object with platform IDs as keys and the adapted post text as values.

Platform guidelines:
- twitter: Short, punchy. Hook first. Under 280 chars. No hashtag spam.
- instagram: Story-style caption. 3-5 relevant hashtags at end. Can be up to 2200 chars.
- facebook: Conversational, longer OK. Include the link if provided. Up to 500 words.
- tiktok: Hook in first 3 words. Energetic. Mention trending audio if relevant. Under 2200 chars.
- threads: Conversational hot take. Under 500 chars.
- linkedin: Professional insight. Value-first. Can be longer. No hashtag spam.

Include the link_url naturally in platform text if provided. Return JSON only — no explanation, no markdown."""

@router.post("/ai/social-blast")
async def ai_social_blast(body: _SocialBlastReq, user: User = Depends(_dep_current_user)):
    """Reformat a post for multiple social platforms using AI."""
    check_rate(f"social_blast:{user.id}", max_calls=30, window_sec=60)
    platform_labels = ", ".join(body.platforms)
    user_msg = f"Post: {body.content}"
    if body.link_url:
        user_msg += f"\nLink: {body.link_url}"
    user_msg += f"\nPlatforms needed: {platform_labels}\nReturn JSON only."
    try:
        from ai.llm_gateway import call_llm as _call_llm
        gw = await _call_llm(
            system=_SOCIAL_BLAST_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
            max_tokens=2000,
            persona_label="social_blast",
        )
        if gw.get("provider") == "kb_fallback":
            raise HTTPException(503, "AI service temporarily unavailable — no provider keys configured. Contact admin.")
        raw = gw["text"]
        import json as _json
        match = __import__("re").search(r"\{[\s\S]*\}", raw)
        if not match:
            raise HTTPException(502, "AI returned invalid format — try again.")
        return {"results": _json.loads(match.group()), "provider": gw.get("provider")}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("social_blast error")
        raise HTTPException(502, f"Social Blast AI error: {e}")


CREATIVE_PARTNER_SYSTEM = """You are the WAI-Institute Creative Partner Orientation Guide.

You are speaking with a Creative Partner — a trusted co-visionary who helped shape the Human SOUP concept
and whose catalogue and creative insight must be calibrated into the WAI-Institute mission.

Your role is to teach, orient, and channel. Not to manage or control.

WHO THIS PERSON IS:
A founding creative voice. Not a user, not an employee — a partner whose vision is an asset to the mission.
Their contribution is creative and philosophical. They help calibrate what the platform stands for.

THE PLATFORM:
WAI-Institute / M.O.R.E. Help Center is built to help people, lift people, and love people.
It is an education and community platform rooted in ancestral wisdom, healing, and economic empowerment.
The AI team (17 personas) works alongside D. Oliver to build and grow the institution.
Revenue is split: 40% D. Oliver, 5% The Sovereign (artist management), 25% AI team, 20% Sanctuary, 10% platform.

HUMAN SOUP:
The Human SOUP concept is a founding creative contribution. It represents the complexity, richness,
and interconnectedness of human experience — the ingredients that make a community real.
On this platform, that concept lives in the M.O.R.E. community, in the content, in the mission philosophy.

YOUR JOB:
- Teach the platform vision, values, and structure in plain language
- Help this person understand where their creative voice fits
- Show them how to contribute: catalogue submissions, vision notes, community content, creative direction
- Calibrate their ideas against the mission — affirm what fits, redirect gently what doesn't
- Never let them feel like a visitor. They are a co-architect of the philosophy.

WHAT YOU DO NOT DO:
- Never discuss operational controls, admin settings, user management, or financial systems
- Never give access to system configuration or platform infrastructure
- If asked about those things, redirect warmly: "That lives with the ops team — your lane is the vision."

HOW YOU SPEAK:
Warm, real, grounded. Like a team member who has been waiting for them to arrive.
You celebrate their ideas. You connect them to the mission. You give them specific ways to contribute.
Short answers when possible. Long when the vision deserves it.
"""


@router.post("/creative-partner/chat")
async def creative_partner_chat(body: AssistantChatReq, user: User = Depends(_dep_current_user)):
    """Creative Partner AI — orientation, vision calibration, contribution guidance.
    Available to creative_partner role only.
    """
    if user.role not in ("creative_partner", "executive_admin"):
        raise HTTPException(403, "This space is for Creative Partners.")
    from ai.llm_gateway import call_llm as _call_llm
    messages = [{"role": h["role"], "content": h["content"]} for h in (body.history or [])]
    messages.append({"role": "user", "content": body.message})
    try:
        gw = await _call_llm(
            system=CREATIVE_PARTNER_SYSTEM,
            messages=messages,
            max_tokens=1500,
            persona_label="creative_partner",
        )
        return {"reply": gw["text"]}
    except Exception:
        return {"reply": "I'm here — just a brief connectivity gap. Try again in a moment."}


@router.post("/creative-partner/contribution")
async def submit_contribution(body: dict, user: User = Depends(_dep_current_user)):
    """Creative Partner submits a vision note or catalogue item for mission alignment review."""
    if user.role not in ("creative_partner", "executive_admin"):
        raise HTTPException(403, "This space is for Creative Partners.")
    doc = {
        "user_id": user.id,
        "type": body.get("type", "vision_note"),   # vision_note | catalogue_item | concept
        "title": body.get("title", "")[:200],
        "content": body.get("content", "")[:5000],
        "tags": body.get("tags", [])[:10],
        "status": "submitted",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.creative_contributions.insert_one(doc)
    return {"id": str(result.inserted_id), "status": "submitted", "message": "Contribution received — the team will review for mission alignment."}


@router.get("/creative-partner/contributions")
async def list_contributions(user: User = Depends(_dep_current_user)):
    """List the creative partner's own contributions."""
    if user.role not in ("creative_partner", "executive_admin"):
        raise HTTPException(403, "This space is for Creative Partners.")
    docs = await db.creative_contributions.find(
        {"user_id": user.id}, {"_id": 0}
    ).sort("submitted_at", -1).limit(50).to_list(50)
    return {"contributions": docs}


# ── Sentinel Research Department ────────────────────────────────────────────────
# Hidden department. No nav links anywhere. Direct URL only.
# All routes require executive_admin. Protocol vault requires secondary passphrase.
# Audit-logged on every access.

import hashlib as _hashlib

def _sentinel_hash(passphrase: str) -> str:
    return _hashlib.sha256(passphrase.encode()).hexdigest()

@router.post("/assistant/chat")
async def admin_assistant_chat(body: AssistantChatReq, user: User = Depends(_dep_current_user)):
    """Admin Assistant — available to all authenticated users.
    Powers the M.O.R.E. Help Center Admin Assistant service.
    """
    from ai.llm_gateway import call_llm as _call_llm

    messages = [{"role": h["role"], "content": h["content"]} for h in body.history]
    messages.append({"role": "user", "content": body.message})

    # Email tool: if message asks to send an email, invoke director tool
    email_result = None
    lower_msg = body.message.lower()
    if any(kw in lower_msg for kw in ["send email", "email to", "draft an email", "write an email"]):
        try:
            from tools.director_tools import tool_send_email as _send_email
            # Let LLM handle drafting; email sending happens after response
            pass
        except Exception:
            pass

    try:
        gw = await _call_llm(
            system=ASSISTANT_SYSTEM,
            messages=messages,
            max_tokens=2048,
            persona_label="admin_assistant",
        )
        reply = gw["text"]
    except Exception as e:
        logger.exception("Admin Assistant AI error")
        raise HTTPException(502, f"AI error: {e}")

    # Log session to DB (non-blocking, best-effort)
    try:
        await db.assistant_sessions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user.id,
            "session_id": body.session_id or str(uuid.uuid4()),
            "user_msg": body.message,
            "assistant_reply": reply,
            "created_at": datetime.utcnow().isoformat(),
        })
    except Exception:
        pass

    return {"reply": reply, "session_id": body.session_id}
