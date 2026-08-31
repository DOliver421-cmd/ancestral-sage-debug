"""
Executive Tools — Unified Tool Access for the Executive Suite & Hybrid NAM
=========================================================================

Wraps the existing director_tools.py functions (web_search, fetch_url,
send_email, etc.) as HTTP endpoints. These tools are FREE — zero paid APIs,
zero external service keys required for web search and URL fetch.

The email tool works with Gmail/Outlook SMTP (free tiers) or queues to DB.
Social Blast generates platform-specific copy-paste posts (no platform API).

All endpoints require admin+ role (executive tools are staff-only).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, List

logger = logging.getLogger("lcewai")
router = APIRouter(prefix="/api/exec/tools", tags=["executive-tools"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None

def bind(_db, _current_user, _audit):
    global db, current_user, audit
    db = _db
    current_user = _current_user
    audit = _audit

# ── Auth ──────────────────────────────────────────────────────────────────────
from fastapi import Depends

async def _dep_current_user(authorization: Optional[str] = Header(None)):
    return await current_user(authorization)

def _require_admin():
    from routers.roles import ROLE_RANK
    def dep(user=Depends(_dep_current_user)):
        if ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 6):
            raise HTTPException(403, "Executive tools require admin+ role")
        return user
    return dep


# ── Request Models ────────────────────────────────────────────────────────────

class WebSearchReq(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    num_results: int = Field(default=6, ge=1, le=10)

class FetchUrlReq(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)

class SendEmailReq(BaseModel):
    to: str = Field(..., min_length=1, description="Recipient email or 'executive' for D. Oliver")
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=10000)

class KnowledgeSearchReq(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    domains: str = ""

class KnowledgeIngestReq(BaseModel):
    content: str = Field(..., min_length=1)
    title: str = ""
    content_type: str = "fact"
    domains: List[str] = []
    keywords: List[str] = []


# ── Tool Endpoints ────────────────────────────────────────────────────────────

@router.post("/web-search")
async def web_search(body: WebSearchReq, user=Depends(_require_admin())):
    """Search the live web — FREE, zero API keys. Uses DuckDuckGo + Wikipedia + Bing."""
    from tools.director_tools import tool_web_search
    result = await tool_web_search(query=body.query, num_results=body.num_results)
    return {"result": result, "tool": "web_search", "cost": "free"}

@router.post("/fetch-url")
async def fetch_url(body: FetchUrlReq, user=Depends(_require_admin())):
    """Fetch and read any public web page — FREE, zero API keys."""
    from tools.director_tools import tool_fetch_url
    result = await tool_fetch_url(url=body.url)
    return {"result": result, "tool": "fetch_url", "cost": "free"}

@router.post("/send-email")
async def send_email(body: SendEmailReq, user=Depends(_require_admin())):
    """Send a branded WAI email. Uses Gmail/Outlook SMTP (free tiers) or queues to DB."""
    from tools.director_tools import tool_send_email
    result = await tool_send_email(to=body.to, subject=body.subject, body=body.body, db=db)
    return {"result": result, "tool": "send_email", "cost": "free"}

@router.post("/knowledge-search")
async def knowledge_search(body: KnowledgeSearchReq, user=Depends(_require_admin())):
    """Search the Knowledge Forge — institutional knowledge, zero AI cost."""
    from ai.hybrid_nam.store import find_many
    from ai.hybrid_nam.knowledge_graph import retrieve, classify_domains
    kb = await find_many("nam_knowledge", limit=500)
    domains = [d.strip() for d in body.domains.split(",") if d.strip()] if body.domains else None
    result = retrieve(query=body.query, knowledge_base=kb, domains=domains)
    return {"result": result, "tool": "knowledge_search", "cost": "free"}

@router.post("/knowledge-ingest")
async def knowledge_ingest(body: KnowledgeIngestReq, user=Depends(_require_admin())):
    """Ingest new knowledge into the Knowledge Forge."""
    from ai.hybrid_nam.store import create
    from ai.hybrid_nam.knowledge_forge import KnowledgeForge
    forge = KnowledgeForge()
    item = forge.ingest(
        content=body.content,
        source_info={
            "origin": "executive_tools",
            "type": "manual",
            "content_type": body.content_type,
            "title": body.title,
            "domains": body.domains,
            "keywords": body.keywords,
        },
    )
    item_dict = item.to_dict() if hasattr(item, "to_dict") else item
    item_dict["ingested_by"] = user.id if hasattr(user, "id") else "admin"
    await create("nam_knowledge", item_dict)
    return {"status": "ingested", "tool": "knowledge_ingest", "cost": "free"}

@router.get("/system-health")
async def system_health(user=Depends(_require_admin())):
    """Query live system health — incidents, mode, active flags."""
    from tools.director_tools import tool_get_system_health
    result = await tool_get_system_health()
    return {"result": result, "tool": "system_health", "cost": "free"}

@router.get("/incident-register")
async def incident_register(user=Depends(_require_admin())):
    """Pull the live open incident register."""
    from tools.director_tools import tool_get_incident_register
    result = await tool_get_incident_register()
    return {"result": result, "tool": "incident_register", "cost": "free"}
