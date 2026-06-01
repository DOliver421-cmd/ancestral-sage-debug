"""
WAI-Institute Contextual Matcher
==================================
Pairs a cultural scout lead with the best matching product SKU
from the WAI catalog (db.wai_product_pipeline).

Matching logic:
  1. Keyword overlap between lead theme/text and product name/description
  2. Emotional theme alignment (grief → healing content, etc.)
  3. Price tier selection based on lead engagement score
  4. (Optional) LLM re-ranking for borderline matches

Returns a MatchResult with product + confidence score + recommended
response strategy.
"""

import json
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger("lcewai.contextual_matcher")

# Theme → product type mapping
THEME_PRODUCT_MAP = {
    "grief":       ["healing_content", "meditation_script", "healing_guide"],
    "loss":        ["healing_content", "healing_guide"],
    "healing":     ["healing_content", "meditation_script", "healing_guide"],
    "trauma":      ["healing_content", "healing_guide"],
    "love":        ["spoken_word", "digital_product", "chapbook"],
    "identity":    ["spoken_word", "digital_product"],
    "blackness":   ["spoken_word", "digital_product"],
    "resilience":  ["spoken_word", "digital_product"],
    "hope":        ["spoken_word", "meditation_script"],
    "community":   ["digital_product", "campaign_package"],
    "ancestry":    ["healing_content", "spoken_word"],
    "struggle":    ["spoken_word", "healing_content"],
    "joy":         ["spoken_word", "digital_product"],
    "rage":        ["spoken_word", "digital_product"],
    "justice":     ["spoken_word", "campaign_package"],
    "freedom":     ["spoken_word", "digital_product"],
    "loneliness":  ["healing_content", "meditation_script"],
    "purpose":     ["digital_product", "spoken_word"],
    "growth":      ["digital_product", "healing_guide"],
    "relationships": ["spoken_word", "digital_product"],
}

# Fallback products to recommend when no catalog match is found
FALLBACK_PRODUCTS = [
    {
        "name":        "WAI Healing Collection",
        "description": "A curated collection of spoken word and healing content from the WAI-Institute.",
        "price_cents": 999,
        "content_type": "digital_product",
        "platform_url": None,
        "fallback": True,
    }
]

# Intent → response strategy
INTENT_STRATEGY = {
    "seeking":  "direct_recommendation",   # Person is actively looking — respond directly
    "sharing":  "community_engagement",    # Person shared something — engage emotionally first
    "trending": "trend_response",          # Trending topic — create reactive content
    "none":     "passive_discovery",       # Low intent — add to audience pool
}


class ContextualMatcher:
    """
    Matches scout leads to catalog products.

    Usage:
        matcher = ContextualMatcher(db)
        result = await matcher.match(lead)
        print(result["product"]["name"], result["confidence"])
    """

    def __init__(self, db=None):
        self.db = db

    async def match(self, lead: dict) -> dict:
        """
        Find the best matching product for a given lead.

        Args:
            lead: dict from db.scout_leads (has theme, body, score, intent)

        Returns:
            {
              matched: bool,
              product: dict or None,
              confidence: float (0.0–1.0),
              strategy: str,
              rationale: str,
            }
        """
        theme   = lead.get("theme", "")
        body    = (lead.get("body", "") + " " + lead.get("title", "")).lower()
        score   = lead.get("score", 0)
        intent  = lead.get("intent", "none")
        strategy = INTENT_STRATEGY.get(intent, "passive_discovery")

        # ── Step 1: Get target content types for this theme ───────────────────
        target_types = THEME_PRODUCT_MAP.get(theme, ["digital_product", "spoken_word"])

        # ── Step 2: Search catalog for matching products ───────────────────────
        catalog = await self._get_catalog(content_types=target_types)

        # ── Step 3: Score each catalog item ───────────────────────────────────
        best_product = None
        best_score   = 0.0

        for product in catalog:
            product_text = (
                (product.get("name", "") + " " + product.get("description", "")).lower()
            )
            sim = self._keyword_overlap(body, product_text)

            # Boost if content_type matches target
            if product.get("content_type") in target_types:
                sim += 0.2

            # Boost for published products (have a real URL)
            if product.get("platform_url"):
                sim += 0.15

            if sim > best_score:
                best_score   = sim
                best_product = product

        # ── Step 4: Fallback if no catalog match ──────────────────────────────
        if best_product is None or best_score < 0.1:
            return {
                "matched":    False,
                "product":    FALLBACK_PRODUCTS[0],
                "confidence": 0.0,
                "strategy":   strategy,
                "rationale":  f"No catalog match found for theme '{theme}'. Using fallback product.",
                "lead_score": score,
            }

        # ── Step 5: Mark lead as matched in DB ────────────────────────────────
        await self._mark_matched(lead, best_product)

        return {
            "matched":    True,
            "product":    best_product,
            "confidence": round(min(best_score, 1.0), 3),
            "strategy":   strategy,
            "rationale":  f"Matched '{theme}' lead to '{best_product.get('name')}' (confidence {best_score:.0%})",
            "lead_score": score,
        }

    async def match_batch(self, leads: list) -> list:
        """
        Match a batch of leads concurrently. Returns list of match results.
        """
        import asyncio
        tasks   = [self.match(lead) for lead in leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            r if not isinstance(r, Exception) else {
                "matched": False, "error": str(r)
            }
            for r in results
        ]

    # ── Catalog ───────────────────────────────────────────────────────────────

    async def _get_catalog(
        self,
        content_types: list = None,
        status: str = "published",
        limit: int = 50,
    ) -> list:
        """
        Pull products from db.wai_product_pipeline.
        Falls back to all products if none match content_types.
        """
        if self.db is None:
            return []

        try:
            query: dict = {}
            if status:
                query["status"] = status
            if content_types:
                query["content_type"] = {"$in": content_types}

            cursor = self.db.wai_product_pipeline.find(query, {"_id": 0}).limit(limit)
            products = []
            async for doc in cursor:
                products.append(doc)

            # If typed search returns nothing, broaden to all published
            if not products and content_types:
                cursor2 = self.db.wai_product_pipeline.find(
                    {"status": "published"}, {"_id": 0}
                ).limit(limit)
                async for doc in cursor2:
                    products.append(doc)

            return products

        except Exception as e:
            logger.warning("_get_catalog error: %s", e)
            return []

    # ── Similarity ────────────────────────────────────────────────────────────

    def _keyword_overlap(self, text_a: str, text_b: str) -> float:
        """
        Simple keyword overlap score (Jaccard-style).
        Returns 0.0 – 1.0.
        """
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        # Remove stopwords
        stops = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "is", "are", "was", "be",
            "this", "that", "it", "as", "by", "from", "i", "you",
            "my", "me", "we", "our", "have", "has", "been", "not",
        }
        words_a -= stops
        words_b -= stops

        if not words_a or not words_b:
            return 0.0

        intersection = words_a & words_b
        union        = words_a | words_b
        return len(intersection) / len(union)

    # ── DB helpers ────────────────────────────────────────────────────────────

    async def _mark_matched(self, lead: dict, product: dict) -> None:
        """Update scout lead to show it's been matched."""
        if self.db is None:
            return
        try:
            source_id = lead.get("source_id")
            if source_id:
                await self.db.scout_leads.update_one(
                    {"source_id": source_id},
                    {"$set": {
                        "matched":          True,
                        "matched_product":  product.get("name"),
                        "matched_pipeline_id": product.get("pipeline_id"),
                        "matched_at":       datetime.now(timezone.utc).isoformat(),
                    }},
                )
        except Exception as e:
            logger.warning("_mark_matched error: %s", e)

    async def get_match_stats(self) -> dict:
        """Return matching statistics from db.scout_leads."""
        if self.db is None:
            return {}
        try:
            total    = await self.db.scout_leads.count_documents({})
            matched  = await self.db.scout_leads.count_documents({"matched": True})
            actioned = await self.db.scout_leads.count_documents({"actioned": True})
            return {
                "total_leads":    total,
                "matched_leads":  matched,
                "actioned_leads": actioned,
                "match_rate":     round(matched / max(total, 1) * 100, 1),
                "action_rate":    round(actioned / max(total, 1) * 100, 1),
            }
        except Exception as e:
            logger.warning("get_match_stats error: %s", e)
            return {}
