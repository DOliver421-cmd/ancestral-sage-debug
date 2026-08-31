"""ai/keyword_kb.py — Multi-layered zero-cost keyword knowledge base.

Platform policy (owner decision, August 2026):
  - Anonymous / public visitors get NO AI. They get this KB.
  - Customers at ANY tier (free / member / plus / pro / patron / executive)
    get NO platform-funded AI. Their AI runs on their own BYOK key when they
    have one; without BYOK they get this KB.
  - Platform-funded AI is reserved for admin / executive_admin staff only
    (internal operations).
  - Keyword KB answers are free, zero-token, and always available.

Matching layers (in order of specificity):
  L1  exact-intent match   — normalized intent phrase appears in the question
  L2  token-overlap score  — best entry whose intent tokens cover the question
  L3  category fallback    — topic-level guidance when only the category matches
  L4  generic fallback     — warm, helpful default (never a dead end)

Sources (merged; later sources override earlier ids):
  - built-in critical entries (crisis / eviction / legal / scam safety —
    always present even if the data file is missing)
  - ai/kb_entries.json      — DYNAMIC: reloaded when the file changes, so
    entries can be added/edited without a deploy
  - db.kb_entries            — optional MongoDB collection (best-effort,
    cached 5 minutes; never blocks a reply)
"""

from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
from pathlib import Path
from typing import Optional

logger = logging.getLogger("lcewai.keyword_kb")

_KB_FILE = Path(__file__).parent / "kb_entries.json"

# ── Built-in critical entries — always present, load even without the JSON ───
_CRITICAL_ENTRIES: list[dict] = [
    {
        "id": "crisis-immediate-danger",
        "category": "crisis",
        "intents": [
            "suicide", "want to kill myself", "kill myself", "self harm",
            "self-harm", "hurt myself", "end my life", "suicidal",
            "crisis", "in danger right now", "emergency help",
        ],
        "answer": (
            "You are not alone, and help is available right now. "
            "Call or text 988 to reach the Suicide and Crisis Lifeline — free, confidential, and available 24/7. "
            "If you or someone else is in immediate danger, call 911. "
            "For domestic violence support, call 1-800-799-7233 (National Domestic Violence Hotline), also 24/7. "
            "These lines are staffed by real people who care and want to help you. Please reach out now."
        ),
    },
    {
        "id": "housing-eviction-rights",
        "category": "housing",
        "intents": [
            "eviction notice", "getting evicted", "being evicted", "eviction",
            "landlord is kicking me out", "my landlord wants me out",
            "evicted", "evict",
        ],
        "answer": (
            "If you received an eviction notice, do not ignore it — you have rights. "
            "Read the notice carefully for the date, reason, and any deadline. "
            "Call 211 to find free legal aid in your area right away. "
            "You usually have a right to a court hearing before you can be removed. "
            "Document everything in writing, keep copies, and do not leave voluntarily without checking your options."
        ),
    },
    {
        "id": "legal-court-papers",
        "category": "legal",
        "intents": [
            "court papers", "summons", "lawsuit", "being sued", "sued",
            "court date", "legal papers", "legal help", "need a lawyer",
            "free legal aid",
        ],
        "answer": (
            "If you received court papers, respond before the deadline shown — ignoring them can lead to a default judgment against you. "
            "Call 211 to be connected to free or low-cost legal aid. "
            "Many courthouses have self-help centers where staff can explain your options. "
            "Write down every date, keep every document, and never miss a hearing."
        ),
    },
    {
        "id": "scams-warning",
        "category": "scams",
        "intents": [
            "scam", "is this a scam", "phishing", "fraud", "fake irs",
            "gift card scam", "they want gift cards", "social security scam",
            "irs calling me", "someone called me about my social security",
        ],
        "answer": (
            "This sounds like it could be a scam. Real government agencies like the IRS or Social Security "
            "Administration never call demanding immediate payment or gift cards. "
            "Never share personal information, Social Security numbers, or banking details with anyone who contacted you first. "
            "Hang up, block the number, and report it to the FTC at ReportFraud.ftc.gov. "
            "If you already sent money, contact your bank immediately."
        ),
    },
    {
        "id": "benefits-211",
        "category": "benefits",
        "intents": [
            "snap", "ebt", "food stamps", "wic", "medicaid", "benefits",
            "assistance programs", "help with food", "food assistance",
            "utility assistance", "liheap",
        ],
        "answer": (
            "You may qualify for food, health, or utility assistance programs. "
            "Call 211 — it is free, confidential, and available 24/7 — to find programs in your area. "
            "For SNAP (food stamps), apply at your local DHHS office or online at benefits.gov. "
            "For Medicaid, visit healthcare.gov or your state health department website. "
            "There is no shame in using programs you have paid into and that exist to help you."
        ),
    },
]

# ── Text normalization ────────────────────────────────────────────────────────
_CONTRACTIONS = {
    "i'm": "i am", "i've": "i have", "i'll": "i will", "i'd": "i would",
    "you're": "you are", "you've": "you have", "you'll": "you will", "you'd": "you would",
    "he's": "he is", "she's": "she is", "it's": "it is", "that's": "that is",
    "what's": "what is", "who's": "who is", "there's": "there is",
    "we're": "we are", "we've": "we have", "they're": "they are", "they've": "they have",
    "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "can't": "cannot", "couldn't": "could not", "wouldn't": "would not",
    "shouldn't": "should not", "won't": "will not", "isn't": "is not",
    "aren't": "are not", "wasn't": "was not", "weren't": "were not",
    "haven't": "have not", "hasn't": "has not", "hadn't": "had not",
    "let's": "let us", "gonna": "going to", "wanna": "want to", "gotta": "got to",
    "kinda": "kind of", "sorta": "sort of", "dunno": "do not know",
}

_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "for", "to",
    "of", "in", "on", "at", "by", "with", "from", "as", "is", "are", "was",
    "were", "be", "been", "being", "do", "does", "did", "have", "has", "had",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "its", "our", "their", "this", "that",
    "these", "those", "what", "which", "who", "whom", "how", "when", "where",
    "why", "can", "could", "will", "would", "should", "may", "might", "must",
    "shall", "about", "into", "over", "under", "again", "once", "here",
    "there", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "just", "please", "thanks", "thank", "hi", "hello", "hey",
    "someone", "something", "anything", "everything", "nothing", "anybody",
    "everyone", "one", "two", "need", "want", "know", "tell", "ask", "get",
    "going", "got", "am", "did", "does", "dont", "cant", "wont", "im", "ive",
})

_PUNCT_RE = re.compile(r"[^a-z0-9\s]+")


def _norm(text: str) -> str:
    """Lowercase, strip accents, expand contractions, collapse whitespace."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    for k, v in _CONTRACTIONS.items():
        t = t.replace(k, v)
    t = _PUNCT_RE.sub(" ", t)
    return " ".join(t.split())


def _tokens(text: str) -> list[str]:
    return [w for w in _norm(text).split() if w not in _STOPWORDS and len(w) > 1]


# ── Load / index state ────────────────────────────────────────────────────────
_cache = {
    "entries": [],          # list of dict (enriched with _norm_intents, _tokens)
    "exact": [],            # sorted [(intent_norm, entry_index)] longest first
    "by_id": {},            # id -> entry dict
    "json_mtime": None,     # mtime of kb_entries.json last loaded
    "db_loaded": 0.0,       # timestamp of last db load
}


def _enrich(e: dict) -> dict:
    e = dict(e)
    e["_norm_intents"] = [_norm(i) for i in (e.get("intents") or []) if _norm(i)]
    e["_tokens"] = sorted({t for i in e["_norm_intents"] for t in _tokens(i)})
    return e


def _rebuild(entries: list[dict]) -> None:
    dedup: dict[str, dict] = {}
    for e in entries:
        dedup[e.get("id")] = _enrich(e)  # later sources override earlier ids
    enriched = list(dedup.values())
    exact: list[tuple[str, int]] = []
    for idx, e in enumerate(enriched):
        for phrase in e["_norm_intents"]:
            if phrase:
                exact.append((phrase, idx))
    exact.sort(key=lambda p: len(p[0]), reverse=True)
    _cache["entries"] = enriched
    _cache["exact"] = exact
    _cache["by_id"] = {e["id"]: e for e in enriched}


def _load_json() -> list[dict]:
    try:
        if not _KB_FILE.exists():
            return []
        mtime = _KB_FILE.stat().st_mtime
        if _cache["json_mtime"] == mtime:
            return []
        raw = json.loads(_KB_FILE.read_text(encoding="utf-8"))
        entries = raw if isinstance(raw, list) else raw.get("entries", [])
        _cache["json_mtime"] = mtime
        logger.info("keyword_kb: loaded %d entries from %s", len(entries), _KB_FILE.name)
        return entries
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("keyword_kb: could not load %s (%s)", _KB_FILE.name, e)
        return []


async def _fetch_db_entries(db) -> list[dict]:
    """Best-effort async load from db.kb_entries. Never raises."""
    if db is None:
        return []
    try:
        docs = await db.kb_entries.find({}, {"_id": 0}).to_list(20000)
        return list(docs)
    except Exception as e:
        logger.warning("keyword_kb: db entries unavailable (%s)", e)
        return []


def load(db_entries: Optional[list[dict]] = None) -> None:
    """(Re)load critical + JSON (+ optional db entries) and rebuild the index."""
    json_entries = _load_json()
    new_entries = db_entries if db_entries is not None else []
    if not json_entries and not new_entries and _cache["entries"]:
        # nothing changed upstream — keep what we have
        return
    _rebuild([*_CRITICAL_ENTRIES, *json_entries, *new_entries])


async def refresh_with_db(db) -> None:
    """Async refresh: pull optional db.kb_entries (cached 5 min) and rebuild.

    Safe to call from a running event loop (FastAPI handlers, the gateway).
    Missing db / errors are non-fatal — the code + JSON entries still serve.
    """
    now = time.time()
    if db is None or now - _cache["db_loaded"] < 300:
        return
    _cache["db_loaded"] = now
    docs = await _fetch_db_entries(db)
    if docs:
        load(db_entries=docs)


def best_match(question: str) -> tuple[Optional[dict], int]:
    """Return (entry, layer) for the best match, or (None, 0)."""
    q = _norm(question)
    q_tokens = _tokens(q)
    if not q_tokens and not q:
        return None, 0
    load()
    entries = _cache["entries"]
    if not entries:
        return None, 0

    # L1 — exact intent phrase (longest first, substring match)
    for phrase, idx in _cache["exact"]:
        if phrase in q:
            return entries[idx], 1

    # L2 — token F1 against non-category entries: 2*inter/(|q|+|e|).
    # Harmonic precision/recall avoids rewarding long generic entries while
    # still matching short questions like "reset password".
    best_e, best_s, best_n = None, 0.0, 0
    qtok_set = set(q_tokens)
    q_len = len(qtok_set)
    for e in entries:
        if e.get("is_category"):
            continue
        toks = e["_tokens"]
        if not toks:
            continue
        inter = len(qtok_set & set(toks))
        if inter == 0:
            continue
        f1 = (2.0 * inter) / (q_len + len(toks))
        if f1 > best_s or (f1 == best_s and len(toks) > best_n):
            best_e, best_s, best_n = e, f1, len(toks)
    if best_e and best_s >= 0.5:
        return best_e, 2

    # L3 — category fallback (generic topic guidance)
    for e in entries:
        if not e.get("is_category"):
            continue
        if set(q_tokens) & set(e["_tokens"]):
            return e, 3

    return None, 0


_GENERIC_ANSWER = (
    "I can't answer that from the free knowledge base, and I won't pretend to. "
    "Live AI here runs on YOUR key — and free keys exist: Groq (console.groq.com), "
    "Cerebras (cloud.cerebras.ai), and Google Gemini (aistudio.google.com) all offer "
    "free API tiers. To unlock live AI: open the BYOK page (/byok), complete the "
    "one-time $3 unlock, and paste a free key from any of the three providers — "
    "about 2-3 minutes total. Your AI then runs on your own key, not the platform's. "
    "For life-help needs (housing, legal, health, benefits), 211 is free and "
    "confidential 24/7. For account or platform issues, a real person answers at "
    "the M.O.R.E. Help Center (/help-center)."
)


def reply(question: str) -> str:
    """Best keyword-KB answer for the question (always returns a string)."""
    entry, layer = best_match(question)
    if entry and entry.get("answer"):
        return str(entry["answer"]).strip()
    return _GENERIC_ANSWER


def entry_count() -> dict:
    """Honest inventory: curated answers, matchable intent patterns, layers."""
    load()
    entries = _cache["entries"]
    intents = sum(len(e["_norm_intents"]) for e in entries)
    exact = len(_cache["exact"])
    return {
        "answers": len(entries),
        "intent_phrases": intents,
        "exact_matchable_phrases": exact,
        "categories": len({e.get("category") for e in entries if e.get("category")}),
        "layers": ["exact", "token_overlap", "category", "generic"],
    }
