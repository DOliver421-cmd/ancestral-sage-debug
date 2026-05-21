"""
WAI-Institute Unified Publishing Client
========================================
Single publishing pipeline used by ALL personas.
Replaces the duplicated Gumroad code scattered across tool files.

Tier 1 — Lemon Squeezy (autonomous, no Stripe required for seller)
           Set: LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID
           Sign up at lemonsqueezy.com with Google — payouts via PayPal or bank

Tier 2 — Gumroad (autonomous, if GUMROAD_API_KEY is set)
           Set: GUMROAD_API_KEY
           Fallback if Lemon Squeezy unavailable

Tier 3 — MongoDB Archive (always works)
           Product stored in db.wai_product_pipeline with status "pending_publish"
           Survives until a T1/T2 key is added — then batch-publishable

Tier 4 — Executive Notification (always works)
           Logs to db.executive_notifications so NAM Oshun sees what's waiting
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.publishing")

LEMON_SQUEEZY_API_KEY = os.environ.get("LEMON_SQUEEZY_API_KEY", "")
LEMON_SQUEEZY_STORE_ID = os.environ.get("LEMON_SQUEEZY_STORE_ID", "")
GUMROAD_API_KEY = os.environ.get("GUMROAD_API_KEY", "")
EXECUTIVE_EMAIL = os.environ.get("EXECUTIVE_EMAIL", "delon@morehelpcenteral.com")


# ── Lemon Squeezy ─────────────────────────────────────────────────────────────

async def _publish_lemon_squeezy(
    name: str,
    description: str,
    price_cents: int,
    persona: str,
) -> dict | None:
    """
    Create a product + variant on Lemon Squeezy.
    Returns {url, product_id, variant_id} on success, None on failure.
    """
    if not LEMON_SQUEEZY_API_KEY or not LEMON_SQUEEZY_STORE_ID:
        return None

    headers = {
        "Authorization":  f"Bearer {LEMON_SQUEEZY_API_KEY}",
        "Content-Type":   "application/vnd.api+json",
        "Accept":         "application/vnd.api+json",
    }

    try:
        import httpx
        async with httpx.AsyncClient(timeout=20) as client:
            # Step 1: Create product
            product_payload = {
                "data": {
                    "type":       "products",
                    "attributes": {
                        "name":        name,
                        "description": description,
                        "status":      "published",
                    },
                    "relationships": {
                        "store": {
                            "data": {"type": "stores", "id": str(LEMON_SQUEEZY_STORE_ID)}
                        }
                    },
                }
            }
            r1 = await client.post(
                "https://api.lemonsqueezy.com/v1/products",
                headers=headers,
                json=product_payload,
            )
            if r1.status_code not in (200, 201):
                logger.warning("LemonSqueezy create product failed: HTTP %d — %s", r1.status_code, r1.text[:200])
                return None

            product_data = r1.json().get("data", {})
            product_id   = product_data.get("id")
            product_slug = product_data.get("attributes", {}).get("slug", "")
            if not product_id:
                return None

            # Step 2: Create variant (price)
            variant_payload = {
                "data": {
                    "type":       "variants",
                    "attributes": {
                        "name":       "Standard",
                        "price":      price_cents,
                        "is_subscription": False,
                    },
                    "relationships": {
                        "product": {
                            "data": {"type": "products", "id": product_id}
                        }
                    },
                }
            }
            r2 = await client.post(
                "https://api.lemonsqueezy.com/v1/variants",
                headers=headers,
                json=variant_payload,
            )

            variant_id = None
            if r2.status_code in (200, 201):
                variant_id = r2.json().get("data", {}).get("id")

            # Build product URL
            # LemonSqueezy store URL format: https://{store}.lemonsqueezy.com/l/{slug}
            # We may not have the store slug — fall back to dashboard URL
            store_info = None
            try:
                rs = await client.get(
                    f"https://api.lemonsqueezy.com/v1/stores/{LEMON_SQUEEZY_STORE_ID}",
                    headers=headers,
                )
                if rs.status_code == 200:
                    store_info = rs.json().get("data", {}).get("attributes", {})
            except Exception: pass

            if store_info and product_slug:
                store_slug = store_info.get("slug", "")
                url = f"https://{store_slug}.lemonsqueezy.com/l/{product_slug}"
            else:
                url = f"https://app.lemonsqueezy.com/products/{product_id}"

            logger.info("LemonSqueezy T1 OK: %s → %s (product %s)", name, url, product_id)
            return {"url": url, "product_id": product_id, "variant_id": variant_id}

    except Exception as e:
        logger.warning("LemonSqueezy exception: %s", e)
        return None


# ── Gumroad ───────────────────────────────────────────────────────────────────

async def _publish_gumroad(name: str, description: str, price_cents: int) -> dict | None:
    """Create a product on Gumroad. Returns {url, product_id} on success."""
    if not GUMROAD_API_KEY:
        return None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                "https://api.gumroad.com/v2/products",
                data={
                    "access_token": GUMROAD_API_KEY,
                    "name":         name,
                    "description":  description,
                    "price":        price_cents,
                    "published":    "true",
                },
            )
        if r.status_code in (200, 201):
            data = r.json().get("product", {})
            url  = data.get("short_url", "")
            pid  = data.get("id", "")
            logger.info("Gumroad T2 OK: %s → %s", name, url)
            return {"url": url, "product_id": pid}
        logger.warning("Gumroad failed: HTTP %d", r.status_code)
    except Exception as e:
        logger.warning("Gumroad exception: %s", e)
    return None


# ── Main Entry Point ──────────────────────────────────────────────────────────

async def autonomous_publish(
    name: str,
    description: str,
    price_cents: int,
    persona: str,
    content: str = "",
    content_type: str = "digital_product",
    revenue_stream_id: str = "",
    db=None,
) -> dict:
    """
    Publish a product through the 4-tier pipeline.

    Args:
        name:             Product listing name
        description:      Public-facing description
        price_cents:      Price in cents (0 = free)
        persona:          Which persona is publishing (cipher/oracle/ambassador/architect/etc.)
        content:          Full product content to archive (optional)
        content_type:     Product type tag for pipeline filtering
        revenue_stream_id: Revenue stream ID for tracking
        db:               MongoDB instance

    Returns dict with:
        tier:        "lemon_squeezy" | "gumroad" | "mongodb" | "notification_only"
        status:      "published" | "archived" | "notified"
        url:         Live product URL (if published to T1/T2)
        product_id:  Platform product ID
        pipeline_id: Internal MongoDB pipeline record ID
    """
    pipeline_id = str(uuid.uuid4())
    now         = datetime.now(timezone.utc).isoformat()

    # ── Archive to pipeline (always — before trying external platforms) ────────
    pipeline_doc = {
        "_id":              pipeline_id,
        "name":             name,
        "description":      description,
        "price_cents":      price_cents,
        "persona":          persona,
        "content":          content[:3000] if content else "",
        "content_type":     content_type,
        "revenue_stream_id": revenue_stream_id,
        "status":           "pending_publish",
        "platform":         None,
        "platform_url":     None,
        "platform_id":      None,
        "created_at":       now,
        "updated_at":       now,
    }
    if db is not None:
        try:
            await db.wai_product_pipeline.insert_one(dict(pipeline_doc))
        except Exception as e:
            logger.warning("pipeline archive failed: %s", e)

    # ── Tier 1: Lemon Squeezy ─────────────────────────────────────────────────
    if price_cents > 0 or LEMON_SQUEEZY_API_KEY:
        ls_result = await _publish_lemon_squeezy(name, description, price_cents, persona)
        if ls_result:
            if db is not None:
                try:
                    await db.wai_product_pipeline.update_one(
                        {"_id": pipeline_id},
                        {"$set": {
                            "status":       "published",
                            "platform":     "lemon_squeezy",
                            "platform_url": ls_result["url"],
                            "platform_id":  ls_result["product_id"],
                            "updated_at":   datetime.now(timezone.utc).isoformat(),
                        }},
                    )
                except Exception: pass
            return {
                "tier":        "lemon_squeezy",
                "status":      "published",
                "url":         ls_result["url"],
                "product_id":  ls_result["product_id"],
                "pipeline_id": pipeline_id,
                "name":        name,
                "price":       f"${price_cents / 100:.2f}",
            }

    # ── Tier 2: Gumroad ───────────────────────────────────────────────────────
    gr_result = await _publish_gumroad(name, description, price_cents)
    if gr_result:
        if db is not None:
            try:
                await db.wai_product_pipeline.update_one(
                    {"_id": pipeline_id},
                    {"$set": {
                        "status":       "published",
                        "platform":     "gumroad",
                        "platform_url": gr_result["url"],
                        "platform_id":  gr_result["product_id"],
                        "updated_at":   datetime.now(timezone.utc).isoformat(),
                    }},
                )
            except Exception: pass
        return {
            "tier":        "gumroad",
            "status":      "published",
            "url":         gr_result["url"],
            "product_id":  gr_result["product_id"],
            "pipeline_id": pipeline_id,
            "name":        name,
            "price":       f"${price_cents / 100:.2f}",
        }

    # ── Tier 3: MongoDB Archive ───────────────────────────────────────────────
    # Already archived above — just notify executive
    if db is not None:
        try:
            await db.executive_notifications.insert_one({
                "_id":         str(uuid.uuid4()),
                "type":        "product_pending_publish",
                "pipeline_id": pipeline_id,
                "persona":     persona,
                "name":        name,
                "price_cents": price_cents,
                "note":        (
                    "Product archived. Add LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID "
                    "to Railway to enable autonomous publishing. "
                    "View all pending products at GET /api/exec/products."
                ),
                "created_at":  now,
            })
        except Exception: pass

    logger.info("autonomous_publish T3 archived: %s — pipeline %s", name, pipeline_id)
    return {
        "tier":        "mongodb",
        "status":      "archived",
        "url":         None,
        "product_id":  None,
        "pipeline_id": pipeline_id,
        "name":        name,
        "price":       f"${price_cents / 100:.2f}",
        "note":        (
            "Archived in product pipeline. "
            "Add LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID to Railway "
            "to publish automatically. View at GET /api/exec/products."
        ),
    }


async def batch_publish_pending(db) -> dict:
    """
    Attempt to publish all pending_publish products in the pipeline.
    Call this after adding LEMON_SQUEEZY_API_KEY or GUMROAD_API_KEY.
    Returns summary of what was published vs what remains pending.
    """
    if db is None:
        return {"error": "Database unavailable"}

    published = []
    failed    = []

    try:
        cursor = db.wai_product_pipeline.find({"status": "pending_publish"}).limit(50)
        async for doc in cursor:
            try:
                result = await autonomous_publish(
                    name=doc["name"],
                    description=doc["description"],
                    price_cents=doc["price_cents"],
                    persona=doc.get("persona", "unknown"),
                    content=doc.get("content", ""),
                    content_type=doc.get("content_type", "digital_product"),
                    revenue_stream_id=doc.get("revenue_stream_id", ""),
                    db=None,  # Don't re-archive
                )
                if result["status"] == "published":
                    await db.wai_product_pipeline.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {
                            "status":       "published",
                            "platform":     result["tier"],
                            "platform_url": result.get("url"),
                            "platform_id":  result.get("product_id"),
                            "updated_at":   datetime.now(timezone.utc).isoformat(),
                        }},
                    )
                    published.append({"name": doc["name"], "url": result.get("url"), "tier": result["tier"]})
                else:
                    failed.append({"name": doc["name"], "reason": "No publishing platform active"})
            except Exception as e:
                failed.append({"name": doc.get("name", "unknown"), "reason": str(e)})
    except Exception as e:
        return {"error": str(e)}

    return {
        "published_count": len(published),
        "failed_count":    len(failed),
        "published":       published,
        "failed":          failed,
        "note":            "Run again after adding LEMON_SQUEEZY_API_KEY to publish remaining products.",
    }
