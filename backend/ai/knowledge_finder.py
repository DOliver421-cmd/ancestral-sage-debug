"""ai/knowledge_finder.py — Knowledge Finder: deterministic zero-cost discovery.

Owner architecture (August 2026):
  - Everyone can DISCOVER knowledge. AI is an entitlement, not a requirement.
  - Anonymous / public / free users get a real keyword search over the
    platform's own indexed content: features, lessons, tools, resources,
    FAQs, policies, store items. Zero LLM, zero provider API, zero user key.
  - BYOK / authorized staff unlock the AI layer on top; the keyword search
    remains the deterministic base under it.
  - This is a first-class capability, NOT a fallback error screen.

SECURITY RULE (critical): the pipeline is
    authenticate -> determine access -> FILTER authorized documents ->
    keyword search -> rank -> return
It is NEVER "search everything then hide unauthorized results". Documents
marked internal_only are excluded from the index surface entirely; documents
beyond the caller's tier or role are filtered BEFORE matching. The matcher
never sees an unauthorized document.

Index fields (per document):
  id, title, keywords, aliases, description, category, feature, tier,
  public_access, roles, internal_only, content_type, route, tags, body

Sources (later sources override earlier ids):
  - backend FEATURE_REGISTRY (every platform feature)
  - PAYMENT_PRODUCTS (store catalog)
  - keyword_kb curated entries (common-question answers as documents)
  - ai/kb_documents.json (static curated docs — extendable without a deploy)
  - db.knowledge_docs (MongoDB — dynamic, access-filtered, cached 5 min)
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Optional

from ai.keyword_kb import _norm, _tokens  # same normalization as the KB

logger = logging.getLogger("lcewai.knowledge_finder")

_DOCS_FILE = Path(__file__).parent / "kb_documents.json"

TIER_RANK = {"free": 0, "member": 1, "plus": 2, "pro": 3, "patron": 4, "platinum": 5, "executive": 6}
STAFF_ROLES = ("instructor", "support_staff", "oversight", "admin", "executive_admin")

_cache = {
    "docs": [],          # enriched docs
    "by_id": {},
    "json_mtime": None,
    "db_loaded": 0.0,
}


class Access:
    """Caller access context. Anonymous = public role + free tier."""

    def __init__(self, role: str = "public", feature_tier: str = "free", byok: bool = False):
        self.role = role or "public"
        self.feature_tier = feature_tier or "free"
        self.byok = bool(byok)

    @property
    def tier_rank(self) -> int:
        return TIER_RANK.get(self.feature_tier, 0)

    @property
    def is_staff(self) -> bool:
        return self.role in STAFF_ROLES

    @property
    def is_anonymous(self) -> bool:
        return self.role in ("public", "")


# ── Access filter — applied BEFORE matching ──────────────────────────────────
def _allowed(doc: dict, access: Access) -> bool:
    if doc.get("internal_only"):
        return False
    if access.is_anonymous and not doc.get("public_access"):
        return False
    roles = doc.get("roles")
    if roles and access.role not in roles:
        return False
    tier = doc.get("tier") or "free"
    if TIER_RANK.get(tier, 0) > access.tier_rank and not access.is_staff:
        return False
    return True


# ── Document enrichment ───────────────────────────────────────────────────────
def _enrich(doc: dict) -> dict:
    d = dict(doc)
    title = str(d.get("title") or "")
    kw = [str(k) for k in (d.get("keywords") or []) if str(k).strip()]
    aliases = [str(a) for a in (d.get("aliases") or []) if str(a).strip()]
    d["_title_norm"] = _norm(title)
    d["_title_tokens"] = _tokens(title)
    d["_kw_norm"] = [_norm(k) for k in kw]
    d["_kw_tokens"] = sorted({t for k in kw for t in _tokens(k)})
    d["_alias_norm"] = [_norm(a) for a in aliases]
    d["_tag_tokens"] = sorted({t for t in _tokens(" ".join(d.get("tags") or []))})
    d["_desc_norm"] = _norm(str(d.get("description") or ""))
    return d


def _prefix_hit(q_tok: str, doc_tok: str) -> bool:
    """Cheap stemming: token equality or prefix match (min 4 chars)."""
    if q_tok == doc_tok:
        return True
    if len(q_tok) >= 4 and len(doc_tok) >= 4:
        return q_tok.startswith(doc_tok) or doc_tok.startswith(q_tok)
    return False


# ── Sources ───────────────────────────────────────────────────────────────────
def _from_registry() -> list[dict]:
    try:
        from routers.features import FEATURE_REGISTRY
    except Exception:
        return []
    docs = []
    for f in FEATURE_REGISTRY:
        tiers = f.get("default_tiers") or ["free"]
        tier = min(tiers, key=lambda t: TIER_RANK.get(t, 99))
        docs.append({
            "id": f"feature:{f.get('feature_id')}",
            "title": f.get("name") or f.get("feature_id"),
            "description": f.get("description") or "",
            "keywords": [f.get("navigation_label"), f.get("feature_id")],
            "aliases": [f.get("navigation_group")],
            "category": f.get("category") or "platform",
            "feature": f.get("feature_id"),
            "tier": tier,
            "public_access": bool(f.get("public_access")),
            "roles": None,
            "internal_only": bool(f.get("internal_only")),
            "content_type": "feature",
            "route": f.get("route") or "",
            "tags": [f.get("category"), f.get("ecosystem"), f.get("navigation_group")],
            "body": f.get("description") or "",
        })
    return docs


def _from_products() -> list[dict]:
    try:
        from routers.payments import PAYMENT_PRODUCTS
    except Exception:
        return []
    docs = []
    for key, p in PAYMENT_PRODUCTS.items():
        if p.get("physical") and not p.get("sold_online", True):
            continue
        docs.append({
            "id": f"product:{key}",
            "title": p.get("name") or key,
            "description": p.get("description") or "",
            "keywords": [key, p.get("name")],
            "aliases": [],
            "category": "store",
            "feature": "marketplace.store",
            "tier": "free",
            "public_access": True,
            "roles": None,
            "internal_only": False,
            "content_type": "product",
            "route": "/store",
            "tags": ["store", "marketplace", "buy", "product"],
            "body": p.get("description") or "",
        })
    return docs


def _from_kb() -> list[dict]:
    """Curated common-question answers as documents (public life-help + platform)."""
    try:
        raw = json.loads((Path(__file__).parent / "kb_entries.json").read_text(encoding="utf-8"))
        entries = raw.get("entries", []) if isinstance(raw, dict) else raw
    except Exception:
        return []
    docs = []
    for e in entries:
        if e.get("is_category"):
            continue
        category = e.get("category") or "general"
        intents = e.get("intents") or []
        label = (str(intents[0]).title() if intents else e.get("id"))[:60]
        docs.append({
            "id": f"kb:{e.get('id')}",
            "title": f"{category.title()}: {label}",
            "description": str(e.get("answer") or "")[:200],
            "keywords": e.get("intents") or [],
            "aliases": [],
            "category": category,
            "feature": None,
            "tier": "free",
            "public_access": category in ("housing", "legal", "money", "benefits", "jobs",
                                          "health", "scams", "family", "education", "utilities",
                                          "everyday", "crisis", "life"),
            "roles": None,
            "internal_only": category in ("internal",),
            "content_type": "answer",
            "route": None,
            "tags": [category, "help", "resources"],
            "body": str(e.get("answer") or ""),
        })
    return docs


def _from_static_json() -> list[dict]:
    try:
        if not _DOCS_FILE.exists():
            return []
        mtime = _DOCS_FILE.stat().st_mtime
        if _cache["json_mtime"] == mtime:
            return []
        raw = json.loads(_DOCS_FILE.read_text(encoding="utf-8"))
        docs = raw if isinstance(raw, list) else raw.get("documents", [])
        _cache["json_mtime"] = mtime
        logger.info("knowledge_finder: loaded %d docs from %s", len(docs), _DOCS_FILE.name)
        return docs
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("knowledge_finder: static docs unavailable (%s)", e)
        return []


async def _fetch_db_docs(db) -> list[dict]:
    if db is None:
        return []
    try:
        docs = await db.knowledge_docs.find({}, {"_id": 0}).to_list(5000)
        return list(docs)
    except Exception as e:
        logger.warning("knowledge_finder: db docs unavailable (%s)", e)
        return []


def load(db_docs: Optional[list[dict]] = None) -> None:
    """(Re)build the index from all sources. db_docs are pre-fetched async docs."""
    static = _from_static_json()
    new_db = db_docs if db_docs is not None else []
    if not static and not new_db and _cache["docs"]:
        return
    merged: dict[str, dict] = {}
    for doc in [*_from_registry(), *_from_products(), *_from_kb(), *static, *new_db]:
        if doc.get("id"):
            merged[doc["id"]] = _enrich(doc)
    _cache["docs"] = list(merged.values())
    _cache["by_id"] = merged
    logger.info("knowledge_finder: index has %d documents", len(_cache["docs"]))


async def refresh_with_db(db) -> None:
    """Async refresh of the dynamic MongoDB document source (cached 5 min)."""
    now = time.time()
    if db is None or now - _cache["db_loaded"] < 300:
        return
    _cache["db_loaded"] = now
    docs = await _fetch_db_docs(db)
    if docs:
        load(db_docs=docs)


# ── Search ────────────────────────────────────────────────────────────────────
def _score(doc: dict, q_norm: str, q_tokens: set) -> float:
    s = 0.0
    if q_norm and q_norm in doc["_title_norm"]:
        s += 10.0
    for kw in doc["_kw_norm"]:
        if kw and q_norm and kw in q_norm:
            s += 7.0
            break
    for al in doc["_alias_norm"]:
        if al and q_norm and al in q_norm:
            s += 5.0
            break
    title_toks = set(doc["_title_tokens"])
    if title_toks:
        hit = sum(1 for t in q_tokens if any(_prefix_hit(t, d) for d in title_toks))
        s += 5.0 * (hit / max(1, len(title_toks)))
    kw_toks = set(doc["_kw_tokens"])
    if kw_toks:
        hit = sum(1 for t in q_tokens if any(_prefix_hit(t, d) for d in kw_toks))
        s += 3.0 * (hit / max(1, len(kw_toks)))
    if q_tokens & set(doc["_tag_tokens"]):
        s += 1.0
    if q_norm and doc["_desc_norm"] and q_norm in doc["_desc_norm"]:
        s += 2.0
    return s


def search(query: str, access: Access | None = None, limit: int = 8) -> list[dict]:
    """Access-filtered keyword search. Returns ranked result dicts."""
    access = access or Access()
    load()
    q_norm = _norm(query)
    q_tokens = set(_tokens(query))
    if not q_tokens and not q_norm:
        return []
    scored = []
    for doc in _cache["docs"]:
        if not _allowed(doc, access):
            continue  # security rule: unauthorized docs never reach matching
        score = _score(doc, q_norm, q_tokens)
        if score >= 2.0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, doc in scored[:limit]:
        body = str(doc.get("body") or doc.get("description") or "")
        snippet = body[:160].strip()
        results.append({
            "title": doc.get("title"),
            "type": doc.get("content_type") or "resource",
            "category": doc.get("category"),
            "route": doc.get("route"),
            "tier": doc.get("tier") or "free",
            "snippet": snippet,
            "score": round(score, 2),
        })
    return results


def upgrade_prompt(access: Access) -> Optional[str]:
    """The honest commercial boundary: AI is an entitlement, not a requirement."""
    if access.byok or access.is_staff:
        return None
    if access.is_anonymous:
        return ("Want an AI-guided answer? Create a free account, then unlock AI "
                "with your own API key for a one-time $3.")
    return ("Want an AI-guided answer? Unlock AI with your own API key for a "
            "one-time $3 — live answers then run on your key, not the platform's.")


def render_reply(query: str, access: Access | None = None, max_results: int = 4) -> str:
    """One text answer for chat surfaces: curated answer > related resources >
    honest boundary. Never pretends to be AI."""
    access = access or Access()
    from ai.keyword_kb import best_match
    entry, _ = best_match(query)
    if entry and entry.get("answer"):
        return str(entry["answer"]).strip()

    results = search(query, access, limit=max_results)
    if results:
        lines = ["Here's what I found in the knowledge base:"]
        for r in results:
            title = r["title"]
            route = f" ({r['route']})" if r.get("route") else ""
            lines.append(f"• {title}{route}")
        prompt = upgrade_prompt(access)
        if prompt:
            lines.append("")
            lines.append(prompt)
        return "\n".join(lines)

    prompt = upgrade_prompt(access)
    base = (
        "I couldn't find a match in the knowledge base, and I won't pretend to "
        "answer from nowhere."
    )
    if prompt:
        base += " " + prompt
    return base


def doc_count() -> dict:
    """Honest inventory of the index."""
    load()
    return {
        "documents": len(_cache["docs"]),
        "public_documents": sum(1 for d in _cache["docs"] if d.get("public_access")),
        "types": sorted({d.get("content_type") for d in _cache["docs"]}),
    }
