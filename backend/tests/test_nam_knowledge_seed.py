"""Regression tests for the Hybrid NAM knowledge seed (seed_nam_knowledge.py).

Verifies:
1. The full owner corpus ingests through the production path
   (KnowledgeForge.ingest -> store.create("nam_knowledge")) and lands APPROVED.
2. Seeding is idempotent — re-runs never duplicate.
3. Seeded items are retrievable through the exact function the
   /api/nam/knowledge/search endpoint uses (knowledge_graph.retrieve).
4. The forge preserves domains/keywords at ingestion (the fields retrieve()
   scores by) — regression for the historical drop that made API-ingested
   items invisible to domain-scoped search.

Convention: sync test functions wrapping asyncio.run() — this repo has no
pytest-asyncio plugin (see test_system_rollback.py).
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ai.hybrid_nam import store as nam_store
from ai.hybrid_nam import persistence
from ai.hybrid_nam.knowledge_forge import KnowledgeForge
from ai.hybrid_nam.knowledge_graph import retrieve

from seed_nam_knowledge import KNOWLEDGE_CORPUS, seed_nam_knowledge

CORPUS_SIZE = len(KNOWLEDGE_CORPUS)


def _ids(items):
    return sorted(i.get("knowledge_id", "") for i in items)


def _run(coro):
    return asyncio.run(coro)


# ── Seeding ──────────────────────────────────────────────────────────────────

def test_seed_ingests_full_corpus_approved():
    persistence.clear_fallback()
    result = _run(seed_nam_knowledge())

    assert result["failed_count"] == 0, result["failed"]
    assert result["seeded_count"] == CORPUS_SIZE
    assert result["skipped_count"] == 0

    items = _run(nam_store.find_many("nam_knowledge", limit=9999))
    assert len(items) == CORPUS_SIZE

    for item in items:
        assert item["approved"] is True, item["knowledge_id"]
        assert item["status"] == "approved", item["knowledge_id"]
        assert item["provenance"]["approved_by"] == "owner"
        assert item["domains"], f"{item['knowledge_id']} missing domains"
        assert item["keywords"], f"{item['knowledge_id']} missing keywords"


def test_seed_idempotent():
    persistence.clear_fallback()
    first = _run(seed_nam_knowledge())
    second = _run(seed_nam_knowledge())

    assert first["seeded_count"] == CORPUS_SIZE
    assert second["seeded_count"] == 0
    assert second["skipped_count"] == CORPUS_SIZE

    items = _run(nam_store.find_many("nam_knowledge", limit=9999))
    assert len(items) == CORPUS_SIZE


def test_seed_force_overwrites_without_duplicating():
    persistence.clear_fallback()
    _run(seed_nam_knowledge())
    forced = _run(seed_nam_knowledge(force=True))

    assert forced["seeded_count"] == CORPUS_SIZE
    items = _run(nam_store.find_many("nam_knowledge", limit=9999))
    assert len(items) == CORPUS_SIZE


# ── Retrieval through the live search path ──────────────────────────────────

def test_seed_retrievable_evidence():
    persistence.clear_fallback()
    _run(seed_nam_knowledge())
    knowledge_base = _run(nam_store.find_many("nam_knowledge", limit=9999))

    result = retrieve(query="census undercount black men", knowledge_base=knowledge_base)
    found = _ids(result["context"]["context_items"])
    assert "NAM-EV-05" in found

    result = retrieve(query="facial recognition bias", knowledge_base=knowledge_base)
    found = _ids(result["context"]["context_items"])
    assert "NAM-EV-01" in found

    result = retrieve(
        query="white women affirmative action beneficiaries",
        knowledge_base=knowledge_base,
    )
    found = _ids(result["context"]["context_items"])
    assert "NAM-EV-04" in found


def test_seed_retrievable_cosmology_with_synthetic_flag():
    persistence.clear_fallback()
    _run(seed_nam_knowledge())
    knowledge_base = _run(nam_store.find_many("nam_knowledge", limit=9999))

    # Default: synthetic narratives (dream / ancestral_narrative) are excluded
    result = retrieve(query="crystal code planet", knowledge_base=knowledge_base)
    found = _ids(result["context"]["context_items"])
    assert "NAM-CO-06" not in found

    # Explicit opt-in: the cosmology is retrievable
    result = retrieve(
        query="crystal code planet",
        knowledge_base=knowledge_base,
        include_synthetic=True,
    )
    found = _ids(result["context"]["context_items"])
    assert "NAM-CO-06" in found


# ── Forge field preservation (router ingest path) ───────────────────────────

def test_forge_ingest_preserves_domains_and_keywords():
    """Regression: knowledge_graph.retrieve() scores by domains/keywords, so
    ingestion must carry them through — the historical behavior dropped them,
    making every API-ingested item invisible to domain-scoped search."""
    forge = KnowledgeForge()
    item = forge.ingest(
        content="Test statement about testable claims.",
        source_info={
            "source_id": "test",
            "origin": "test",
            "content_type": "fact",
            "title": "Test",
            "domains": ["values", "history"],
            "keywords": ["claim", "evidence"],
        },
    )
    data = item.to_dict()
    assert data["domains"] == ["values", "history"]
    assert data["keywords"] == ["claim", "evidence"]


def test_corpus_ids_unique():
    ids = [i["knowledge_id"] for i in KNOWLEDGE_CORPUS]
    assert len(ids) == len(set(ids)), "duplicate knowledge_id in corpus"