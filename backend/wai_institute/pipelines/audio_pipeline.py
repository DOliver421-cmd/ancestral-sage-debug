"""
WAI-Institute Audio Production Pipeline
=========================================
Full spoken word MP3 production pipeline:

  1. Parse performance markup from text
     [whisper], [fire], [crescendo], [pause:0.8], etc.
  2. Generate audio via ElevenLabs (3-tier fallback)
  3. Store MP3 in MongoDB GridFS
  4. Return asset_id + access URL

For preview generation (15-second audio teasers):
  - Truncates text to ~150 chars (≈15s at average spoken word pace)
  - Uses same pipeline at lower quality

GridFS asset URL: GET /api/exec/audio/{asset_id}
(Endpoint added to server.py alongside this pipeline)
"""

import os
import io
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("lcewai.audio_pipeline")

# ElevenLabs voice IDs (defaults — overridden by env vars)
_CIPHER_VOICE_ID  = os.environ.get("CIPHER_VOICE_ID",  "pNInz6obpgDQGcFmaJgB")
_DEFAULT_VOICE_ID = _CIPHER_VOICE_ID

# Characters per second for spoken word (used for preview truncation)
CHARS_PER_SECOND = 12


class AudioPipeline:
    """
    Spoken word audio production pipeline.

    Usage:
        pipeline = AudioPipeline(db)
        asset = await pipeline.produce(
            text="I been carrying this truth...",
            persona="cipher",
            title="Carrying Truth",
        )
        print(asset["asset_id"], asset["access_url"])
    """

    def __init__(self, db=None):
        self.db = db

    # ── Full Production ───────────────────────────────────────────────────────

    async def produce(
        self,
        text: str,
        persona: str = "cipher",
        title: str = "",
        voice_id: str = "",
        force_tier: str = "",
        preview_only: bool = False,
    ) -> dict:
        """
        Full audio production cycle.

        Args:
            text:         Full text to synthesize
            persona:      Which persona voice to use
            title:        Product title (for metadata)
            voice_id:     Override voice ID
            force_tier:   Force "elevenlabs" | "openai" | "text"
            preview_only: Truncate to 15-second preview

        Returns:
            {
              asset_id, access_url, tier, duration_secs,
              char_count, title, persona, created_at
            }
        """
        if preview_only:
            preview_chars = CHARS_PER_SECOND * 15
            text = text[:preview_chars].rsplit(" ", 1)[0]  # Clean word boundary

        # ── Step 1: Parse performance markup ──────────────────────────────────
        try:
            from ai.elevenlabs_client import parse_performance_markup
            clean_text, voice_settings = parse_performance_markup(text)
        except Exception:
            clean_text    = text
            voice_settings = {}

        # ── Step 2: Generate audio (3-tier) ───────────────────────────────────
        audio_bytes = None
        tier_used   = "text"

        try:
            from ai.elevenlabs_client import cipher_speak
            result = await cipher_speak(
                text=clean_text,
                voice_id=voice_id or _DEFAULT_VOICE_ID,
                force_tier=force_tier,
                db=self.db,
            )
            tier_used = result.get("tier", "text")
            audio_bytes = result.get("audio")
        except Exception as e:
            logger.warning("AudioPipeline: cipher_speak failed — %s", e)

        # ── Step 3: Store in GridFS ────────────────────────────────────────────
        asset_id   = str(uuid.uuid4())
        access_url = None

        if audio_bytes and self.db is not None:
            try:
                from motor.motor_asyncio import AsyncIOMotorGridFSBucket
                bucket = AsyncIOMotorGridFSBucket(self.db, bucket_name="audio_assets")
                stream = io.BytesIO(audio_bytes)
                file_id = await bucket.upload_from_stream(
                    filename=f"{asset_id}.mp3",
                    source=stream,
                    metadata={
                        "asset_id":  asset_id,
                        "persona":   persona,
                        "title":     title,
                        "tier":      tier_used,
                        "preview":   preview_only,
                        "char_count": len(clean_text),
                    },
                )
                access_url = f"/api/exec/audio/{asset_id}"
                logger.info("AudioPipeline: stored %s in GridFS — %d bytes", asset_id, len(audio_bytes))
            except Exception as e:
                logger.warning("AudioPipeline: GridFS storage failed — %s", e)

        # ── Step 4: Metadata record ────────────────────────────────────────────
        now = datetime.now(timezone.utc).isoformat()
        meta = {
            "_id":         asset_id,
            "asset_id":    asset_id,
            "persona":     persona,
            "title":       title or clean_text[:60],
            "tier":        tier_used,
            "preview":     preview_only,
            "char_count":  len(clean_text),
            "has_audio":   audio_bytes is not None,
            "access_url":  access_url,
            "duration_secs": round(len(clean_text) / max(CHARS_PER_SECOND, 1), 1),
            "created_at":  now,
        }

        if self.db is not None:
            try:
                await self.db.audio_asset_meta.insert_one(meta)
            except Exception as e:
                logger.warning("AudioPipeline: meta insert failed — %s", e)

        return {k: v for k, v in meta.items() if k != "_id"}

    # ── Preview generation ────────────────────────────────────────────────────

    async def generate_preview(
        self,
        text: str,
        persona: str = "cipher",
        voice_id: str = "",
    ) -> dict:
        """
        Generate a 15-second audio preview (teaser).
        Used by the Conversational Engine before recommending a product.
        """
        return await self.produce(
            text=text,
            persona=persona,
            voice_id=voice_id,
            preview_only=True,
            title="Preview",
        )

    # ── Retrieve audio from GridFS ────────────────────────────────────────────

    async def get_audio_bytes(self, asset_id: str) -> Optional[bytes]:
        """
        Retrieve MP3 bytes from GridFS by asset_id.
        Used by GET /api/exec/audio/{asset_id}.
        """
        if self.db is None:
            return None
        try:
            from motor.motor_asyncio import AsyncIOMotorGridFSBucket
            bucket = AsyncIOMotorGridFSBucket(self.db, bucket_name="audio_assets")
            stream = io.BytesIO()
            # Find by filename (asset_id.mp3)
            async for grid_out in bucket.find({"filename": f"{asset_id}.mp3"}):
                await bucket.download_to_stream(grid_out._id, stream)
                return stream.getvalue()
        except Exception as e:
            logger.warning("get_audio_bytes error for %s: %s", asset_id, e)
        return None

    async def get_asset_meta(self, asset_id: str) -> dict:
        """Get metadata for an audio asset."""
        if self.db is None:
            return {}
        try:
            doc = await self.db.audio_asset_meta.find_one(
                {"asset_id": asset_id}, {"_id": 0}
            )
            return doc or {}
        except Exception:
            return {}

    async def list_assets(
        self,
        persona: str = "",
        preview_only: bool = False,
        limit: int = 20,
    ) -> list:
        """List audio assets, optionally filtered by persona."""
        if self.db is None:
            return []
        try:
            query: dict = {}
            if persona:
                query["persona"] = persona
            if preview_only:
                query["preview"] = True

            cursor = self.db.audio_asset_meta.find(
                query, {"_id": 0}
            ).sort("created_at", -1).limit(limit)

            assets = []
            async for doc in cursor:
                assets.append(doc)
            return assets
        except Exception as e:
            logger.warning("list_assets error: %s", e)
            return []
