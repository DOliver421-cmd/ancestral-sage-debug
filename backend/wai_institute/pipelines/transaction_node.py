"""
WAI-Institute Transaction Node
================================
Creates single-click checkout links for autonomous sales.

Primary: Lemon Squeezy checkout sessions (product already published)
Fallback: Lemon Squeezy product URL (direct to product page)
Last resort: Return product URL as-is

Also handles:
  - Tracking which checkout links were generated
  - Conversion tracking (when a purchase happens)
  - Revenue attribution per lead/campaign
"""

import os
import uuid
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger("lcewai.transaction_node")

LEMON_SQUEEZY_API_KEY  = os.environ.get("LEMON_SQUEEZY_API_KEY", "")
LEMON_SQUEEZY_STORE_ID = os.environ.get("LEMON_SQUEEZY_STORE_ID", "")


class TransactionNode:
    """
    Creates checkout links and tracks conversions.

    Usage:
        tn = TransactionNode(db)
        checkout = await tn.create_checkout_link(product)
        print(checkout["checkout_url"])
    """

    def __init__(self, db=None):
        self.db = db

    async def create_checkout_link(
        self,
        product: dict,
        campaign_id: str = "",
        custom_price: int = None,
    ) -> dict:
        """
        Create a single-click checkout URL for a product.

        Tries Lemon Squeezy checkout session first.
        Falls back to product URL if session creation fails.

        Args:
            product:      Product dict (must have platform_id or platform_url)
            campaign_id:  Optional campaign to attribute revenue to
            custom_price: Override price in cents (for custom offers)

        Returns:
            {checkout_url, type, product_name, price, checkout_id}
        """
        product_name = product.get("name", "WAI Product")
        price_cents  = custom_price if custom_price is not None else product.get("price_cents", 0)
        platform_url = product.get("platform_url", "")
        platform_id  = product.get("platform_id", "")

        # ── Lemon Squeezy checkout session ────────────────────────────────────
        if LEMON_SQUEEZY_API_KEY and platform_id:
            ls_checkout = await self._create_ls_checkout(
                product_id=platform_id,
                campaign_id=campaign_id,
                custom_price=custom_price,
            )
            if ls_checkout:
                checkout_id = await self._log_checkout(
                    product=product,
                    checkout_url=ls_checkout,
                    checkout_type="lemon_squeezy_session",
                    campaign_id=campaign_id,
                )
                return {
                    "checkout_url":  ls_checkout,
                    "type":          "lemon_squeezy_session",
                    "product_name":  product_name,
                    "price":         f"${price_cents / 100:.2f}",
                    "checkout_id":   checkout_id,
                }

        # ── Fallback: direct product URL ──────────────────────────────────────
        if platform_url:
            checkout_id = await self._log_checkout(
                product=product,
                checkout_url=platform_url,
                checkout_type="direct_url",
                campaign_id=campaign_id,
            )
            return {
                "checkout_url":  platform_url,
                "type":          "direct_url",
                "product_name":  product_name,
                "price":         f"${price_cents / 100:.2f}",
                "checkout_id":   checkout_id,
            }

        # ── Last resort: no URL available ─────────────────────────────────────
        logger.warning("TransactionNode: no checkout URL available for '%s'", product_name)
        return {
            "checkout_url":  None,
            "type":          "unavailable",
            "product_name":  product_name,
            "price":         f"${price_cents / 100:.2f}",
            "checkout_id":   None,
            "note":          "Product not yet published to a platform. Add LEMON_SQUEEZY_API_KEY to enable.",
        }

    async def _create_ls_checkout(
        self,
        product_id: str,
        campaign_id: str = "",
        custom_price: int = None,
    ) -> str | None:
        """
        Create a Lemon Squeezy checkout session.
        Returns checkout URL on success, None on failure.
        """
        headers = {
            "Authorization": f"Bearer {LEMON_SQUEEZY_API_KEY}",
            "Content-Type":  "application/vnd.api+json",
            "Accept":        "application/vnd.api+json",
        }

        # Build checkout attributes
        attributes: dict = {
            "checkout_options": {
                "media":       False,
                "description": False,
            },
            "checkout_data": {},
        }

        if custom_price is not None:
            attributes["custom_price"] = custom_price

        if campaign_id:
            attributes["checkout_data"]["custom"] = {"campaign_id": campaign_id}

        payload = {
            "data": {
                "type":       "checkouts",
                "attributes": attributes,
                "relationships": {
                    "store": {
                        "data": {"type": "stores", "id": str(LEMON_SQUEEZY_STORE_ID)}
                    },
                    "variant": {
                        "data": {"type": "variants", "id": str(product_id)}
                    },
                },
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    "https://api.lemonsqueezy.com/v1/checkouts",
                    headers=headers,
                    json=payload,
                )
            if r.status_code in (200, 201):
                checkout_url = (
                    r.json()
                    .get("data", {})
                    .get("attributes", {})
                    .get("url", "")
                )
                logger.info("TransactionNode: LS checkout created → %s", checkout_url)
                return checkout_url or None
            else:
                logger.warning("LS checkout failed: HTTP %d — %s", r.status_code, r.text[:200])
        except Exception as e:
            logger.warning("_create_ls_checkout error: %s", e)

        return None

    async def _log_checkout(
        self,
        product: dict,
        checkout_url: str,
        checkout_type: str,
        campaign_id: str = "",
    ) -> str:
        """Log checkout link creation for conversion tracking."""
        checkout_id = str(uuid.uuid4())
        if self.db is None:
            return checkout_id
        try:
            await self.db.checkout_links.insert_one({
                "_id":          checkout_id,
                "product_name": product.get("name"),
                "price_cents":  product.get("price_cents", 0),
                "checkout_url": checkout_url,
                "type":         checkout_type,
                "campaign_id":  campaign_id,
                "converted":    False,
                "created_at":   datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.warning("_log_checkout error: %s", e)
        return checkout_id

    async def record_conversion(self, checkout_id: str, order_data: dict = None) -> dict:
        """
        Mark a checkout as converted (called from Lemon Squeezy webhook).
        Updates checkout_links + scout_campaigns.
        """
        if self.db is None:
            return {"status": "no_db"}
        try:
            now = datetime.now(timezone.utc).isoformat()
            await self.db.checkout_links.update_one(
                {"_id": checkout_id},
                {"$set": {
                    "converted":    True,
                    "converted_at": now,
                    "order_data":   order_data or {},
                }},
            )
            # If there's a campaign, mark it converted too
            link = await self.db.checkout_links.find_one({"_id": checkout_id})
            if link and link.get("campaign_id"):
                await self.db.scout_campaigns.update_one(
                    {"_id": link["campaign_id"]},
                    {"$set": {"converted": True, "converted_at": now}},
                )
            logger.info("TransactionNode: conversion recorded for checkout %s", checkout_id)
            return {"status": "recorded", "checkout_id": checkout_id}
        except Exception as e:
            logger.warning("record_conversion error: %s", e)
            return {"status": "error", "message": str(e)}

    async def get_conversion_stats(self) -> dict:
        """Return conversion statistics."""
        if self.db is None:
            return {}
        try:
            total     = await self.db.checkout_links.count_documents({})
            converted = await self.db.checkout_links.count_documents({"converted": True})
            return {
                "total_checkouts": total,
                "conversions":     converted,
                "conversion_rate": round(converted / max(total, 1) * 100, 1),
            }
        except Exception as e:
            logger.warning("get_conversion_stats error: %s", e)
            return {}
