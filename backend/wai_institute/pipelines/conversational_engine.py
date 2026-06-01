"""
WAI-Institute Conversational Engine
=====================================
Generates personalized, culturally authentic outreach responses
for high-intent cultural scout leads.

Pipeline:
  1. Receive lead + matched product from ContextualMatcher
  2. Use Cipher to write a personalized empathetic recommendation
  3. Generate a 15-second audio preview of the matched content
  4. Create a Lemon Squeezy checkout link via TransactionNode
  5. Package the full outreach response

The response is NEVER a cold sales pitch.
It opens with acknowledgment → creates resonance → offers the work.
The AI identifies itself as curator when appropriate.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.conversational_engine")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Response tone templates per intent type
RESPONSE_TONE = {
    "seeking":  "Someone is actively looking for this. Lead with deep empathy. Acknowledge the specific thing they said they need. Then offer the work.",
    "sharing":  "Someone shared something meaningful. Don't sell. First reflect their feeling back to them authentically. The work is secondary.",
    "trending": "This theme is moving culturally right now. Meet the energy. Don't chase it — be the grounded source.",
    "none":     "Soft presence. Don't push. Let the work speak for itself.",
}


class ConversationalEngine:
    """
    Generates outreach responses for scout leads.

    Usage:
        engine = ConversationalEngine(db)
        response = await engine.craft_response(lead, match_result)
    """

    def __init__(self, db=None):
        self.db = db

    async def craft_response(
        self,
        lead: dict,
        match_result: dict,
        include_preview: bool = True,
        include_checkout: bool = True,
    ) -> dict:
        """
        Craft a complete outreach response for a lead.

        Returns:
            {
              response_text,
              audio_preview (asset_id + url),
              checkout_url,
              product,
              platform,
              created_at,
            }
        """
        product  = match_result.get("product", {})
        strategy = match_result.get("strategy", "direct_recommendation")
        intent   = lead.get("intent", "none")
        theme    = lead.get("theme", "")
        lead_text = (lead.get("body", "") + " " + lead.get("title", ""))[:500]

        # ── Step 1: Generate the response text via Cipher ─────────────────────
        response_text = await self._generate_response(
            lead_text=lead_text,
            product=product,
            theme=theme,
            intent=intent,
            strategy=strategy,
        )

        # ── Step 2: Audio preview ─────────────────────────────────────────────
        audio_preview = None
        if include_preview and product.get("content"):
            try:
                from wai_institute.pipelines.audio_pipeline import AudioPipeline
                pipeline = AudioPipeline(self.db)
                audio_preview = await pipeline.generate_preview(
                    text=product["content"][:300],
                    persona="cipher",
                )
            except Exception as e:
                logger.warning("ConversationalEngine: preview generation failed — %s", e)

        # ── Step 3: Checkout link ─────────────────────────────────────────────
        checkout_url = None
        if include_checkout and product.get("platform_url"):
            checkout_url = product["platform_url"]
        elif include_checkout:
            try:
                from wai_institute.pipelines.transaction_node import TransactionNode
                tn = TransactionNode(self.db)
                checkout = await tn.create_checkout_link(product)
                checkout_url = checkout.get("checkout_url")
            except Exception as e:
                logger.warning("ConversationalEngine: checkout link failed — %s", e)

        # ── Step 4: Log the campaign ──────────────────────────────────────────
        campaign_id = await self._log_campaign(
            lead=lead,
            product=product,
            response_text=response_text,
            checkout_url=checkout_url,
            audio_preview=audio_preview,
        )

        return {
            "campaign_id":   campaign_id,
            "response_text": response_text,
            "audio_preview": audio_preview,
            "checkout_url":  checkout_url,
            "product":       {
                "name":        product.get("name"),
                "price":       f"${product.get('price_cents', 0) / 100:.2f}",
                "platform_url": product.get("platform_url"),
            },
            "platform":      lead.get("source"),
            "lead_score":    lead.get("score", 0),
            "intent":        intent,
            "created_at":    datetime.now(timezone.utc).isoformat(),
        }

    # ── Response generation ───────────────────────────────────────────────────

    async def _generate_response(
        self,
        lead_text: str,
        product: dict,
        theme: str,
        intent: str,
        strategy: str,
    ) -> str:
        """
        Use Cipher persona to write an empathetic, authentic recommendation.
        Falls back to template response if API unavailable.
        """
        if not ANTHROPIC_API_KEY:
            return self._template_response(product, theme, intent)

        tone = RESPONSE_TONE.get(intent, RESPONSE_TONE["none"])
        product_name = product.get("name", "this piece")
        product_desc = product.get("description", "")
        checkout_url = product.get("platform_url", "[link]")

        prompt = f"""You are THE CIPHER — spoken word artist and cultural witness.
Someone posted this online: "{lead_text}"

Their emotional theme: {theme}
Their intent: {intent}
Tone directive: {tone}

You're recommending this work to them:
Product: {product_name}
Description: {product_desc}

Write a SHORT (3-5 sentences), authentic, human response.
Rules:
- Do NOT sound like an ad or bot
- Acknowledge what they actually said or felt
- Offer the work as something that might meet them where they are
- End with a soft invitation, not a hard sell
- If appropriate, mention: "I'm an AI curator built by WAI-Institute"
- Do NOT include the purchase link — that's added separately
- Write in plain text, no markdown"""

        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
            msg = await client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=300,
                system="You are THE CIPHER — spoken word artist, authentic, never salesy.",
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(b.text for b in msg.content if hasattr(b, "text"))
        except Exception as e:
            logger.warning("ConversationalEngine: LLM response failed — %s", e)
            return self._template_response(product, theme, intent)

    def _template_response(self, product: dict, theme: str, intent: str) -> str:
        """Fallback template when API is unavailable."""
        name = product.get("name", "this piece")
        if intent == "seeking":
            return (
                f"If you're looking for something that touches {theme}, "
                f"'{name}' was built for exactly that moment. "
                f"It holds the thing you're searching for. "
                f"I'm an AI curator for WAI-Institute — this one felt right for what you said."
            )
        elif intent == "sharing":
            return (
                f"What you shared resonated. '{name}' sits in that same space. "
                f"Might be worth a listen."
            )
        else:
            return (
                f"'{name}' explores {theme if theme else 'themes you might connect with'}. "
                f"From WAI-Institute."
            )

    # ── Logging ───────────────────────────────────────────────────────────────

    async def _log_campaign(
        self,
        lead: dict,
        product: dict,
        response_text: str,
        checkout_url: str,
        audio_preview: dict,
    ) -> str:
        """Log outreach attempt to db.scout_campaigns."""
        campaign_id = str(uuid.uuid4())
        if self.db is None:
            return campaign_id

        try:
            await self.db.scout_campaigns.insert_one({
                "_id":           campaign_id,
                "lead_source_id": lead.get("source_id"),
                "lead_platform":  lead.get("source"),
                "lead_theme":     lead.get("theme"),
                "product_name":   product.get("name"),
                "product_url":    product.get("platform_url"),
                "response_text":  response_text[:1000],
                "checkout_url":   checkout_url,
                "audio_preview":  audio_preview,
                "status":         "drafted",
                "converted":      False,
                "created_at":     datetime.now(timezone.utc).isoformat(),
            })

            # Mark lead as actioned
            if lead.get("source_id"):
                await self.db.scout_leads.update_one(
                    {"source_id": lead["source_id"]},
                    {"$set": {
                        "actioned":    True,
                        "campaign_id": campaign_id,
                        "actioned_at": datetime.now(timezone.utc).isoformat(),
                    }},
                )
        except Exception as e:
            logger.warning("ConversationalEngine._log_campaign error: %s", e)

        return campaign_id

    async def get_campaigns(self, status: str = "all", limit: int = 20) -> list:
        """Get outreach campaigns from db.scout_campaigns."""
        if self.db is None:
            return []
        try:
            query = {} if status == "all" else {"status": status}
            cursor = self.db.scout_campaigns.find(
                query, {"_id": 0}
            ).sort("created_at", -1).limit(limit)
            campaigns = []
            async for doc in cursor:
                campaigns.append(doc)
            return campaigns
        except Exception as e:
            logger.warning("get_campaigns error: %s", e)
            return []
