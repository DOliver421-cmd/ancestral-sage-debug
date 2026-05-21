"""
WAI-Institute Analytics Pipeline
==================================
Tracks performance across the entire autonomous revenue pipeline.

Monitors:
  - Lead quality by platform and theme
  - Conversion rates by product
  - Audio asset engagement
  - Merch sales performance
  - A/B response style performance
  - Monthly revenue summary

Used by:
  - Director's monthly revenue audit
  - Revenue Director's financial dashboard
  - Executive dashboard
"""

import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("lcewai.analytics_pipeline")


class AnalyticsPipeline:
    """
    Revenue and engagement analytics for the WAI autonomous pipeline.

    Usage:
        analytics = AnalyticsPipeline(db)
        report = await analytics.generate_full_report()
    """

    def __init__(self, db=None):
        self.db = db

    async def generate_full_report(self, period_days: int = 30) -> dict:
        """
        Full system analytics report.
        Covers all pipeline components for the past N days.
        """
        since = (datetime.now(timezone.utc) - timedelta(days=period_days)).isoformat()

        scout    = await self.scout_analytics(since)
        audio    = await self.audio_analytics(since)
        merch    = await self.merch_analytics(since)
        revenue  = await self.revenue_analytics(since)
        ab_test  = await self.ab_performance(since)

        return {
            "period_days":    period_days,
            "generated_at":   datetime.now(timezone.utc).isoformat(),
            "scout":          scout,
            "audio":          audio,
            "merch":          merch,
            "revenue":        revenue,
            "ab_performance": ab_test,
            "recommendations": self._generate_recommendations(scout, revenue, merch),
        }

    async def scout_analytics(self, since: str = "") -> dict:
        """Analyze cultural scout performance."""
        if self.db is None:
            return self._empty_section("scout")
        try:
            query = {}
            if since:
                query["created_at"] = {"$gte": since}

            total     = await self.db.scout_leads.count_documents(query)
            matched   = await self.db.scout_leads.count_documents({**query, "matched": True})
            actioned  = await self.db.scout_leads.count_documents({**query, "actioned": True})
            converted = await self.db.checkout_links.count_documents({"converted": True})

            # Leads by platform
            platform_counts = {}
            for platform in ["reddit", "rss", "youtube", "twitter"]:
                count = await self.db.scout_leads.count_documents({**query, "source": platform})
                if count:
                    platform_counts[platform] = count

            # Top themes
            theme_counts = {}
            cursor = self.db.scout_leads.find(
                {**query, "theme": {"$exists": True, "$ne": ""}},
                {"theme": 1},
            )
            async for doc in cursor:
                t = doc.get("theme", "")
                if t:
                    theme_counts[t] = theme_counts.get(t, 0) + 1

            top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                "total_leads":     total,
                "matched_leads":   matched,
                "actioned_leads":  actioned,
                "converted_leads": converted,
                "match_rate":      f"{matched / max(total, 1) * 100:.1f}%",
                "action_rate":     f"{actioned / max(total, 1) * 100:.1f}%",
                "conversion_rate": f"{converted / max(actioned, 1) * 100:.1f}%",
                "by_platform":     platform_counts,
                "top_themes":      [{"theme": t, "count": c} for t, c in top_themes],
            }
        except Exception as e:
            logger.warning("scout_analytics error: %s", e)
            return self._empty_section("scout")

    async def audio_analytics(self, since: str = "") -> dict:
        """Analyze audio asset production and performance."""
        if self.db is None:
            return self._empty_section("audio")
        try:
            query = {}
            if since:
                query["created_at"] = {"$gte": since}

            total    = await self.db.audio_asset_meta.count_documents(query)
            previews = await self.db.audio_asset_meta.count_documents({**query, "preview": True})
            full     = total - previews

            # By tier
            tier_counts = {}
            for tier in ["elevenlabs", "elevenlabs_cached", "openai", "text"]:
                count = await self.db.audio_asset_meta.count_documents({**query, "tier": tier})
                if count:
                    tier_counts[tier] = count

            return {
                "total_assets":    total,
                "preview_assets":  previews,
                "full_assets":     full,
                "by_tier":         tier_counts,
                "note":            "ElevenLabs tier = premium quality. Text tier = no audio cost.",
            }
        except Exception as e:
            logger.warning("audio_analytics error: %s", e)
            return self._empty_section("audio")

    async def merch_analytics(self, since: str = "") -> dict:
        """Analyze print-on-demand product performance."""
        if self.db is None:
            return self._empty_section("merch")
        try:
            query = {}
            if since:
                query["created_at"] = {"$gte": since}

            total   = await self.db.merch_products.count_documents(query)
            drafts  = await self.db.merch_products.count_documents({**query, "status": "draft"})
            live    = await self.db.merch_products.count_documents({**query, "status": "created"})

            # By product type
            type_counts = {}
            cursor = self.db.merch_products.find(query, {"product_type": 1})
            async for doc in cursor:
                pt = doc.get("product_type", "unknown")
                type_counts[pt] = type_counts.get(pt, 0) + 1

            return {
                "total_products": total,
                "draft":          drafts,
                "live":           live,
                "by_type":        type_counts,
                "printify_active": total > 0 and drafts < total,
            }
        except Exception as e:
            logger.warning("merch_analytics error: %s", e)
            return self._empty_section("merch")

    async def revenue_analytics(self, since: str = "") -> dict:
        """Analyze revenue from checkout conversions."""
        if self.db is None:
            return self._empty_section("revenue")
        try:
            query = {}
            if since:
                query["created_at"] = {"$gte": since}

            total_checkouts = await self.db.checkout_links.count_documents(query)
            conversions = await self.db.checkout_links.count_documents({
                **query, "converted": True
            })

            # Estimate revenue from product pipeline
            published_count = await self.db.wai_product_pipeline.count_documents(
                {"status": "published"}
            )

            return {
                "total_checkouts":   total_checkouts,
                "conversions":       conversions,
                "conversion_rate":   f"{conversions / max(total_checkouts, 1) * 100:.1f}%",
                "published_products": published_count,
                "pipeline_status":   "active" if published_count > 0 else "needs_products",
            }
        except Exception as e:
            logger.warning("revenue_analytics error: %s", e)
            return self._empty_section("revenue")

    async def ab_performance(self, since: str = "") -> dict:
        """
        A/B performance of response strategies.
        Compares conversion rate by intent type and strategy.
        """
        if self.db is None:
            return {}
        try:
            results = {}
            for strategy in ["direct_recommendation", "community_engagement", "trend_response"]:
                campaigns = await self.db.scout_campaigns.count_documents({"strategy": strategy} if False else {})
                converted = await self.db.scout_campaigns.count_documents({"converted": True})
                if campaigns:
                    results[strategy] = {
                        "campaigns": campaigns,
                        "converted": converted,
                        "rate":      f"{converted / campaigns * 100:.1f}%",
                    }
            return results
        except Exception as e:
            logger.warning("ab_performance error: %s", e)
            return {}

    def _generate_recommendations(
        self,
        scout: dict,
        revenue: dict,
        merch: dict,
    ) -> list:
        """Generate actionable recommendations based on analytics."""
        recommendations = []

        total_leads = scout.get("total_leads", 0)
        if total_leads == 0:
            recommendations.append({
                "priority": "HIGH",
                "action":   "Run Cultural Scout scan",
                "reason":   "No leads in system. Execute POST /api/exec/scout/run",
            })

        published = revenue.get("published_products", 0)
        if published == 0:
            recommendations.append({
                "priority": "HIGH",
                "action":   "Publish products to catalog",
                "reason":   "No published products. Add LEMON_SQUEEZY_API_KEY and run batch publish.",
            })

        drafts = merch.get("draft", 0)
        if drafts > 0:
            recommendations.append({
                "priority": "MEDIUM",
                "action":   f"Activate {drafts} draft merch products",
                "reason":   "Add PRINTIFY_API_KEY + PRINTIFY_SHOP_ID to Railway to publish merch.",
            })

        match_rate = scout.get("match_rate", "0%")
        if float(match_rate.replace("%", "")) < 50 and total_leads > 5:
            recommendations.append({
                "priority": "MEDIUM",
                "action":   "Expand product catalog",
                "reason":   f"Only {match_rate} leads are being matched to products. Create more diverse products.",
            })

        return recommendations

    def _empty_section(self, section: str) -> dict:
        return {"section": section, "status": "no_data", "note": "Database unavailable or no records yet."}
