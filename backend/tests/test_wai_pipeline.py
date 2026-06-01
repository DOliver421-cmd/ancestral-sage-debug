"""
Tests for wai_institute pipeline modules.
Covers: CulturalScout, ContextualMatcher, AudioPipeline,
        TransactionNode, MerchPipeline, AnalyticsPipeline.
Run with: pytest backend/tests/test_wai_pipeline.py -v
All tests use mocks — no live APIs or DB needed.
"""
import sys
import os
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def make_mock_db(extra_collections=None):
    db = MagicMock()
    collections = [
        "scout_leads", "scout_scan_log", "scout_campaigns",
        "wai_product_pipeline", "audio_asset_meta",
        "merch_products", "checkout_links",
        "persona_tts_budgets", "system_events",
    ] + (extra_collections or [])
    for col in collections:
        c = MagicMock()
        c.find_one     = AsyncMock(return_value=None)
        c.insert_one   = AsyncMock(return_value=MagicMock(inserted_id="test"))
        c.update_one   = AsyncMock(return_value=MagicMock(modified_count=1))
        c.count_documents = AsyncMock(return_value=0)
        cursor = MagicMock()
        cursor.__aiter__ = MagicMock(return_value=iter([]))
        c.find = MagicMock(return_value=cursor)
        setattr(db, col, c)
    return db


# ═══════════════════════════════════════════════════════════════════════════════
# CulturalScout tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCulturalScout:

    def test_score_content_seeking_intent(self):
        from wai_institute.pipelines.cultural_scout import CulturalScout
        scout = CulturalScout()
        score, theme, intent = scout._score_content(
            "looking for poetry about grief and healing"
        )
        assert score > 0
        assert intent == "seeking"
        assert theme in ("grief", "healing")

    def test_score_content_low_score_noise(self):
        from wai_institute.pipelines.cultural_scout import CulturalScout
        scout = CulturalScout()
        score, theme, intent = scout._score_content(
            "buy this product now click here"
        )
        assert score == 0
        assert intent == "none"

    def test_score_content_sharing_intent(self):
        from wai_institute.pipelines.cultural_scout import CulturalScout
        scout = CulturalScout()
        score, theme, intent = scout._score_content(
            "this hits different crying about resilience and hope"
        )
        assert score > 0
        assert intent in ("sharing", "seeking")

    def test_score_content_theme_detection(self):
        from wai_institute.pipelines.cultural_scout import CulturalScout
        scout = CulturalScout()
        score, theme, intent = scout._score_content(
            "struggling with identity and blackness these days"
        )
        assert theme in ("identity", "blackness", "struggle")

    @pytest.mark.asyncio
    async def test_store_leads_deduplicates(self):
        from wai_institute.pipelines.cultural_scout import CulturalScout
        db = make_mock_db()

        # First call: no duplicate found
        db.scout_leads.find_one = AsyncMock(return_value=None)
        scout = CulturalScout(db)

        leads = [
            {"source_id": "reddit_abc123", "source": "reddit", "score": 3, "theme": "grief"},
        ]
        stored = await scout._store_leads(leads, "scan_1")
        assert stored == 1

    @pytest.mark.asyncio
    async def test_store_leads_skips_duplicates(self):
        from wai_institute.pipelines.cultural_scout import CulturalScout
        db = make_mock_db()

        # Simulate existing lead
        db.scout_leads.find_one = AsyncMock(return_value={"source_id": "reddit_abc123"})
        scout = CulturalScout(db)

        leads = [{"source_id": "reddit_abc123", "source": "reddit", "score": 3}]
        stored = await scout._store_leads(leads, "scan_2")
        assert stored == 0  # Duplicate — not stored

    @pytest.mark.asyncio
    async def test_no_db_graceful(self):
        from wai_institute.pipelines.cultural_scout import CulturalScout
        scout = CulturalScout(db=None)
        leads = await scout.get_unmatched_leads()
        assert leads == []


# ═══════════════════════════════════════════════════════════════════════════════
# ContextualMatcher tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestContextualMatcher:

    def test_keyword_overlap_exact(self):
        from wai_institute.pipelines.contextual_matcher import ContextualMatcher
        m = ContextualMatcher()
        score = m._keyword_overlap("grief healing poetry", "healing grief spoken word poetry")
        assert score > 0.3

    def test_keyword_overlap_no_match(self):
        from wai_institute.pipelines.contextual_matcher import ContextualMatcher
        m = ContextualMatcher()
        score = m._keyword_overlap("pizza recipe Italian", "coding tutorials python")
        assert score == 0.0

    def test_keyword_overlap_removes_stopwords(self):
        from wai_institute.pipelines.contextual_matcher import ContextualMatcher
        m = ContextualMatcher()
        # "the" and "is" are stopwords and shouldn't inflate the score
        score = m._keyword_overlap("the is a and", "the is a and but")
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_match_with_empty_catalog_uses_fallback(self):
        from wai_institute.pipelines.contextual_matcher import ContextualMatcher
        db = make_mock_db()
        # No products in catalog
        db.wai_product_pipeline.find = MagicMock(return_value=MagicMock(
            __aiter__=MagicMock(return_value=iter([]))
        ))
        m = ContextualMatcher(db)
        lead = {"theme": "grief", "body": "looking for healing poetry", "score": 3, "intent": "seeking"}
        result = await m.match(lead)
        assert result["matched"] is False
        assert result["product"] is not None  # Fallback product

    @pytest.mark.asyncio
    async def test_match_with_catalog_finds_product(self):
        from wai_institute.pipelines.contextual_matcher import ContextualMatcher
        db = make_mock_db()

        # Simulate catalog with one matching product
        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = MagicMock(return_value=iter([
            {
                "name": "Healing Through Words",
                "description": "A healing poetry collection for grief and loss",
                "content_type": "healing_content",
                "price_cents": 1499,
                "status": "published",
                "platform_url": "https://wai.lemonsqueezy.com/l/healing",
            }
        ]))
        db.wai_product_pipeline.find = MagicMock(return_value=mock_cursor)

        m = ContextualMatcher(db)
        lead = {"theme": "grief", "body": "looking for healing poetry about grief", "score": 3, "intent": "seeking"}
        result = await m.match(lead)

        assert result["matched"] is True
        assert result["confidence"] > 0
        assert "Healing" in result["product"]["name"]

    @pytest.mark.asyncio
    async def test_match_returns_strategy(self):
        from wai_institute.pipelines.contextual_matcher import ContextualMatcher
        m = ContextualMatcher(db=None)
        lead = {"theme": "joy", "body": "some text", "score": 2, "intent": "seeking"}
        result = await m.match(lead)
        assert result["strategy"] == "direct_recommendation"


# ═══════════════════════════════════════════════════════════════════════════════
# AudioPipeline tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAudioPipeline:

    @pytest.mark.asyncio
    async def test_produce_no_db_returns_meta(self):
        """AudioPipeline must return a meta dict even without DB or ElevenLabs."""
        from wai_institute.pipelines.audio_pipeline import AudioPipeline

        with patch("wai_institute.pipelines.audio_pipeline.AudioPipeline._produce_audio_tier",
                   new_callable=AsyncMock, side_effect=Exception("no key")) \
             if False else nullcontext():
            pipeline = AudioPipeline(db=None)
            # Mock the cipher_speak import
            with patch.dict("sys.modules", {"ai.elevenlabs_client": MagicMock(
                cipher_speak=AsyncMock(return_value={"tier": "text", "audio": None}),
                parse_performance_markup=lambda t: (t, {}),
            )}):
                result = await pipeline.produce(text="Test poem text", persona="cipher")

        assert "asset_id" in result
        assert result["persona"] == "cipher"
        assert result["tier"] == "text"

    @pytest.mark.asyncio
    async def test_preview_truncates_text(self):
        """Preview should truncate to approximately 15 seconds of content."""
        from wai_institute.pipelines.audio_pipeline import AudioPipeline, CHARS_PER_SECOND
        pipeline = AudioPipeline(db=None)

        long_text = "word " * 500  # 2500 chars
        max_preview = CHARS_PER_SECOND * 15

        with patch.dict("sys.modules", {"ai.elevenlabs_client": MagicMock(
            cipher_speak=AsyncMock(return_value={"tier": "text", "audio": None}),
            parse_performance_markup=lambda t: (t, {}),
        )}):
            result = await pipeline.produce(text=long_text, preview_only=True)

        assert result["char_count"] <= max_preview + 20  # small buffer for word boundary

    @pytest.mark.asyncio
    async def test_get_audio_bytes_no_db(self):
        from wai_institute.pipelines.audio_pipeline import AudioPipeline
        pipeline = AudioPipeline(db=None)
        result = await pipeline.get_audio_bytes("nonexistent_id")
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# TransactionNode tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestTransactionNode:

    @pytest.mark.asyncio
    async def test_create_checkout_uses_platform_url_fallback(self):
        from wai_institute.pipelines.transaction_node import TransactionNode
        db = make_mock_db()
        tn = TransactionNode(db)

        product = {
            "name": "Test Product",
            "price_cents": 999,
            "platform_url": "https://wai.lemonsqueezy.com/l/test",
            "platform_id": None,
        }
        result = await tn.create_checkout_link(product)
        assert result["checkout_url"] == "https://wai.lemonsqueezy.com/l/test"
        assert result["type"] == "direct_url"

    @pytest.mark.asyncio
    async def test_create_checkout_returns_unavailable_when_no_url(self):
        from wai_institute.pipelines.transaction_node import TransactionNode
        tn = TransactionNode(db=None)

        product = {"name": "No URL Product", "price_cents": 499}
        result = await tn.create_checkout_link(product)
        assert result["checkout_url"] is None
        assert result["type"] == "unavailable"

    @pytest.mark.asyncio
    async def test_record_conversion(self):
        from wai_institute.pipelines.transaction_node import TransactionNode
        db = make_mock_db()
        db.checkout_links.find_one = AsyncMock(return_value={"_id": "co_1", "campaign_id": "cam_1"})
        tn = TransactionNode(db)

        result = await tn.record_conversion("co_1", {"order_id": "ord_123"})
        assert result["status"] == "recorded"
        db.checkout_links.update_one.assert_awaited()


# ═══════════════════════════════════════════════════════════════════════════════
# MerchPipeline tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMerchPipeline:

    def test_build_design_prompt_contains_text(self):
        from wai_institute.pipelines.merch_pipeline import MerchPipeline
        pipeline = MerchPipeline()
        prompt = pipeline._build_design_prompt("I been carrying this truth")
        assert "carrying this truth" in prompt
        assert "typography" in prompt.lower()

    def test_generate_title(self):
        from wai_institute.pipelines.merch_pipeline import MerchPipeline
        pipeline = MerchPipeline()
        title = pipeline._generate_title("I been carrying this truth like a match")
        assert "I Been Carrying This Truth" in title

    @pytest.mark.asyncio
    async def test_create_merch_draft_without_printify(self):
        """Without PRINTIFY_API_KEY, products should be created as drafts."""
        from wai_institute.pipelines.merch_pipeline import MerchPipeline
        db = make_mock_db()

        with patch.dict(os.environ, {
            "PRINTIFY_API_KEY": "",
            "PRINTIFY_SHOP_ID": "",
            "OPENAI_API_KEY": "",
        }):
            pipeline = MerchPipeline(db)
            result = await pipeline.create_merch_from_text(
                text="Truth like a match between my teeth",
                product_types=["classic_tee"],
            )

        assert result["total_created"] == 1
        product = result["products"][0]
        assert product["status"] == "draft"
        assert "PRINTIFY_API_KEY" in product.get("note", "")


# ═══════════════════════════════════════════════════════════════════════════════
# AnalyticsPipeline tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnalyticsPipeline:

    @pytest.mark.asyncio
    async def test_full_report_no_db(self):
        from wai_institute.pipelines.analytics_pipeline import AnalyticsPipeline
        analytics = AnalyticsPipeline(db=None)
        report = await analytics.generate_full_report()
        assert "scout" in report
        assert "audio" in report
        assert "merch" in report
        assert "revenue" in report
        assert "recommendations" in report

    def test_recommendations_suggests_scan_when_no_leads(self):
        from wai_institute.pipelines.analytics_pipeline import AnalyticsPipeline
        analytics = AnalyticsPipeline(db=None)
        recs = analytics._generate_recommendations(
            scout={"total_leads": 0},
            revenue={"published_products": 0},
            merch={"draft": 0},
        )
        actions = [r["action"] for r in recs]
        assert any("Scout" in a for a in actions)

    def test_recommendations_empty_when_healthy(self):
        from wai_institute.pipelines.analytics_pipeline import AnalyticsPipeline
        analytics = AnalyticsPipeline(db=None)
        recs = analytics._generate_recommendations(
            scout={"total_leads": 50, "match_rate": "80%"},
            revenue={"published_products": 10},
            merch={"draft": 0},
        )
        # With healthy stats, fewer critical recommendations
        high_priority = [r for r in recs if r.get("priority") == "HIGH"]
        assert len(high_priority) == 0


# ── Helper ────────────────────────────────────────────────────────────────────
from contextlib import contextmanager

@contextmanager
def nullcontext():
    yield


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
