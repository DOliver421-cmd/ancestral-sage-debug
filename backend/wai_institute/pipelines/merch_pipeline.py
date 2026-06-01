"""
WAI-Institute Merch Pipeline (Print-on-Demand)
===============================================
When a spoken word line goes viral, this pipeline automatically:

  1. Takes the viral text/stanza
  2. Generates a DALL-E 3 typography design (via Architect)
  3. Creates a Printify product (hoodie, poster, mug, tote)
  4. Publishes to Lemon Squeezy (digital mockup) or Shopify (physical)
  5. Logs to db.merch_products

Requires: PRINTIFY_API_KEY (free account at printify.com)
Optional: OPENAI_API_KEY for DALL-E 3 design generation

Without PRINTIFY_API_KEY:
  - Generates design concept + DALL-E mockup URL
  - Stores in db.merch_products as "draft" awaiting manual Printify upload
"""

import os
import uuid
import json
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger("lcewai.merch_pipeline")

PRINTIFY_API_KEY   = os.environ.get("PRINTIFY_API_KEY", "")
PRINTIFY_SHOP_ID   = os.environ.get("PRINTIFY_SHOP_ID", "")  # From Printify dashboard
OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))

# Printify blueprint IDs for common products
# Get full list at: GET https://api.printify.com/v1/catalog/blueprints.json
PRINTIFY_BLUEPRINTS = {
    "unisex_hoodie":   92,     # Unisex Heavy Blend™ Hooded Sweatshirt
    "classic_tee":     5,      # Unisex Jersey Short Sleeve Tee
    "poster_18x24":    101,    # Poster 18×24
    "tote_bag":        77,     # Heavy Tote Bag
    "mug_11oz":        35,     # White Glossy Mug
}

# WAI brand defaults for POD design
WAI_DESIGN_STYLE = {
    "background":  "deep black (#0A0A0A)",
    "text_color":  "deep gold (#C9A84C)",
    "accent":      "cream (#F5F0E8)",
    "typography":  "Bold, strong serif. Large. Cinematic.",
    "layout":      "Centered text. Generous whitespace. Nothing cluttered.",
}

# Merch price points
MERCH_PRICES = {
    "unisex_hoodie":  4999,   # $49.99
    "classic_tee":    2999,   # $29.99
    "poster_18x24":   2499,   # $24.99
    "tote_bag":       2299,   # $22.99
    "mug_11oz":       1799,   # $17.99
}


class MerchPipeline:
    """
    Print-on-demand pipeline for viral spoken word content.

    Usage:
        pipeline = MerchPipeline(db)
        result = await pipeline.create_merch_from_text(
            text="I been carrying this truth like a match between my teeth",
            product_types=["classic_tee", "poster_18x24"],
        )
    """

    def __init__(self, db=None):
        self.db = db

    async def create_merch_from_text(
        self,
        text: str,
        title: str = "",
        product_types: list = None,
        persona: str = "cipher",
    ) -> dict:
        """
        Full POD pipeline from viral text to live product.

        Args:
            text:          The viral line or stanza to put on merch
            title:         Product title override
            product_types: Which products to create (default: tee + poster)
            persona:       Which persona authored this content

        Returns:
            {products: [...], design_url, status}
        """
        product_types = product_types or ["classic_tee", "poster_18x24"]
        product_title = title or self._generate_title(text)

        # ── Step 1: Generate DALL-E design image ──────────────────────────────
        design_url     = None
        design_prompt  = self._build_design_prompt(text)
        revised_prompt = design_prompt

        if OPENAI_API_KEY:
            design_result = await self._generate_design_image(design_prompt)
            design_url    = design_result.get("url")
            revised_prompt = design_result.get("revised_prompt", design_prompt)
            logger.info("MerchPipeline: design generated → %s", design_url)
        else:
            logger.info("MerchPipeline: no OPENAI_API_KEY — skipping DALL-E design generation")

        # ── Step 2: Create Printify products ──────────────────────────────────
        products = []
        for ptype in product_types:
            if ptype not in PRINTIFY_BLUEPRINTS:
                logger.warning("MerchPipeline: unknown product type '%s'", ptype)
                continue

            product_result = await self._create_printify_product(
                text=text,
                title=f"{product_title} — {ptype.replace('_', ' ').title()}",
                product_type=ptype,
                design_url=design_url,
                persona=persona,
            )
            products.append(product_result)

        # ── Step 3: Publish to Lemon Squeezy ──────────────────────────────────
        for product in products:
            if product.get("status") == "draft" and product.get("mockup_url"):
                try:
                    from ai.publishing import autonomous_publish
                    pub = await autonomous_publish(
                        name=product["title"],
                        description=product.get("description", ""),
                        price_cents=product.get("price_cents", 2999),
                        persona=persona,
                        content=f"merch_id:{product.get('merch_id')}",
                        content_type="merch_product",
                        db=self.db,
                    )
                    product["publish_result"] = pub
                    product["platform_url"] = pub.get("url")
                except Exception as e:
                    logger.warning("MerchPipeline: publish failed — %s", e)

        summary = {
            "title":          product_title,
            "text":           text[:200],
            "design_url":     design_url,
            "design_prompt":  revised_prompt,
            "products":       products,
            "total_created":  len(products),
            "printify_active": bool(PRINTIFY_API_KEY),
            "created_at":     datetime.now(timezone.utc).isoformat(),
        }

        logger.info("MerchPipeline: created %d products for '%s'", len(products), product_title)
        return summary

    # ── DALL-E Design ─────────────────────────────────────────────────────────

    def _build_design_prompt(self, text: str) -> str:
        """Build a DALL-E 3 prompt for typography merch design."""
        style = WAI_DESIGN_STYLE
        return (
            f"Typography poster design on {style['background']} background. "
            f"Large, bold serif text in {style['text_color']}: \"{text[:80]}\". "
            f"Style: {style['typography']} {style['layout']} "
            f"Afro-centric, cultural, powerful. No clutter. High contrast. "
            f"No photographic elements. Pure typography art. "
            f"Suitable for print-on-demand apparel and posters."
        )

    async def _generate_design_image(self, prompt: str) -> dict:
        """Call DALL-E 3 for the merch design."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            response = await client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            data = response.data[0]
            return {
                "url":            data.url,
                "revised_prompt": getattr(data, "revised_prompt", prompt),
            }
        except Exception as e:
            logger.warning("_generate_design_image error: %s", e)
            return {"url": None, "revised_prompt": prompt}

    def _generate_title(self, text: str) -> str:
        """Generate a product title from the text."""
        words = text.strip().split()[:6]
        return " ".join(words).title() + "..."

    # ── Printify ──────────────────────────────────────────────────────────────

    async def _create_printify_product(
        self,
        text: str,
        title: str,
        product_type: str,
        design_url: str = None,
        persona: str = "cipher",
    ) -> dict:
        """
        Create a product on Printify.
        If no API key, returns a draft with design concept.
        """
        merch_id    = str(uuid.uuid4())
        blueprint   = PRINTIFY_BLUEPRINTS[product_type]
        price_cents = MERCH_PRICES.get(product_type, 2999)

        meta = {
            "merch_id":    merch_id,
            "title":       title,
            "text":        text[:200],
            "product_type": product_type,
            "blueprint_id": blueprint,
            "price_cents": price_cents,
            "design_url":  design_url,
            "persona":     persona,
            "description": (
                f"Original spoken word design by WAI-Institute. "
                f"Featuring: \"{text[:80]}...\" "
                f"Printed on demand. Ships worldwide."
            ),
        }

        if not PRINTIFY_API_KEY or not PRINTIFY_SHOP_ID:
            # Draft mode — no Printify API key
            meta["status"]    = "draft"
            meta["mockup_url"] = design_url
            meta["note"]      = "Add PRINTIFY_API_KEY + PRINTIFY_SHOP_ID to Railway to enable auto-publishing."
            logger.info("MerchPipeline: no Printify key — saved as draft: %s", title)
        else:
            # Live Printify creation
            result = await self._post_to_printify(meta)
            meta.update(result)

        if self.db is not None:
            try:
                await self.db.merch_products.insert_one({"_id": merch_id, **meta})
            except Exception as e:
                logger.warning("MerchPipeline: DB save failed — %s", e)

        return meta

    async def _post_to_printify(self, meta: dict) -> dict:
        """
        POST product to Printify API.
        Returns update dict with printify_id, mockup_url, status.
        """
        headers = {
            "Authorization": f"Bearer {PRINTIFY_API_KEY}",
            "Content-Type":  "application/json",
        }

        # Printify requires a print_provider_id (supplier)
        # Default: Printify Choice (id=99) — auto-selects best supplier
        print_provider_id = 99

        product_payload = {
            "title":            meta["title"],
            "description":      meta["description"],
            "blueprint_id":     meta["blueprint_id"],
            "print_provider_id": print_provider_id,
            "variants": [
                {
                    "id":         meta["blueprint_id"] * 1000,  # placeholder
                    "price":      meta["price_cents"],
                    "is_enabled": True,
                }
            ],
        }

        # If we have a design image, add print areas
        if meta.get("design_url"):
            product_payload["print_areas"] = [
                {
                    "variant_ids": [meta["blueprint_id"] * 1000],
                    "placeholders": [
                        {
                            "position": "front",
                            "images": [
                                {
                                    "id":     "external",
                                    "src":    meta["design_url"],
                                    "x":      0.5,
                                    "y":      0.5,
                                    "scale":  1.0,
                                    "angle":  0,
                                }
                            ],
                        }
                    ],
                }
            ]

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"https://api.printify.com/v1/shops/{PRINTIFY_SHOP_ID}/products.json",
                    headers=headers,
                    json=product_payload,
                )

            if r.status_code in (200, 201):
                data = r.json()
                printify_id = data.get("id", "")
                logger.info("MerchPipeline: Printify product created — %s", printify_id)
                return {
                    "status":       "created",
                    "printify_id":  printify_id,
                    "mockup_url":   meta.get("design_url"),  # Real mockup requires separate API call
                }
            else:
                logger.warning("Printify API failed: HTTP %d — %s", r.status_code, r.text[:200])
                return {"status": "api_error", "error": r.text[:200]}

        except Exception as e:
            logger.warning("_post_to_printify error: %s", e)
            return {"status": "exception", "error": str(e)}

    async def get_merch_products(self, status: str = "all", limit: int = 20) -> list:
        """Retrieve merch products from MongoDB."""
        if self.db is None:
            return []
        try:
            query = {} if status == "all" else {"status": status}
            cursor = self.db.merch_products.find(
                query, {"_id": 0}
            ).sort("created_at" if "created_at" in query else "$natural", -1).limit(limit)
            products = []
            async for doc in cursor:
                products.append(doc)
            return products
        except Exception as e:
            logger.warning("get_merch_products error: %s", e)
            return []
