"""
src/services/audio_service.py
================================
Production-grade audio generation service.

Supports:
  - ElevenLabs TTS (primary tier)
  - OpenAI TTS (fallback tier)
  - Text performance mode (always-available final tier)

Handles:
  - Rate limiting  (429 Retry-After + exponential backoff)
  - Expired / revoked API tokens (401 → raises TokenExpiredError)
  - Monthly character budget enforcement
  - Audio file caching (SHA-256 keyed, in-memory)
  - Performance markup parsing ([whisper], [fire], [rise], etc.)

Usage:
    service = AudioService(
        elevenlabs_api_key="...",
        openai_api_key="...",
        monthly_char_budget=29500,
    )
    result = service.generate(
        text="I been carrying this truth like a match between my teeth",
        voice_id="your-voice-id",
        persona="cipher",
    )
    # result["tier"]  → "elevenlabs" | "openai" | "text"
    # result["audio"] → bytes | None
"""

import hashlib
import logging
import time
import json
import re
from typing import Any, Dict, Optional, Tuple

import requests

logger = logging.getLogger("services.audio")

# ── Custom Exceptions ─────────────────────────────────────────────────────────

class AudioServiceError(Exception):
    """Base class for all AudioService errors."""

class AudioRateLimitError(AudioServiceError):
    """Raised when all retry attempts are exhausted after 429s."""
    def __init__(self, provider: str, retry_after: float = 0):
        self.provider    = provider
        self.retry_after = retry_after
        super().__init__(
            f"{provider} rate limit exhausted. Retry after {retry_after:.1f}s"
        )

class AudioTokenExpiredError(AudioServiceError):
    """Raised when the API key is invalid or revoked (401)."""
    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"{provider} API key expired or invalid")

class AudioBudgetExceededError(AudioServiceError):
    """Raised when the monthly character budget is fully exhausted."""
    def __init__(self, used: int, limit: int):
        super().__init__(
            f"Monthly character budget exhausted: {used}/{limit} chars used"
        )

class AudioNetworkError(AudioServiceError):
    """Raised on connection or timeout failures."""

# ── Constants ─────────────────────────────────────────────────────────────────

ELEVENLABS_TTS_URL  = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
OPENAI_TTS_URL      = "https://api.openai.com/v1/audio/speech"

CHARS_PER_SECOND    = 12        # approx spoken chars per second at normal pace
PREVIEW_SECONDS     = 15        # preview truncation target
PREVIEW_MAX_CHARS   = CHARS_PER_SECOND * PREVIEW_SECONDS

MAX_RETRY_ATTEMPTS  = 4
RATE_BASE_WAIT      = 1.0
RATE_MAX_WAIT       = 60.0
DEFAULT_TIMEOUT     = 60        # TTS can be slow for long texts

BUDGET_WARNING_PCT  = 0.85      # warn at 85% usage
BUDGET_HARD_STOP    = 1.00      # refuse at 100% usage

# Performance markup → ElevenLabs voice settings
MARKUP_MAP: Dict[str, Dict[str, float]] = {
    "whisper":   {"stability": 0.90, "similarity_boost": 0.65, "style": 0.0},
    "fire":      {"stability": 0.30, "similarity_boost": 0.85, "style": 0.9},
    "rise":      {"stability": 0.45, "similarity_boost": 0.80, "style": 0.7},
    "crescendo": {"stability": 0.35, "similarity_boost": 0.80, "style": 0.8},
    "tender":    {"stability": 0.80, "similarity_boost": 0.70, "style": 0.2},
    "shout":     {"stability": 0.20, "similarity_boost": 0.90, "style": 1.0},
    "grief":     {"stability": 0.70, "similarity_boost": 0.75, "style": 0.5},
    "joy":       {"stability": 0.40, "similarity_boost": 0.85, "style": 0.75},
    "resolve":   {"stability": 0.60, "similarity_boost": 0.80, "style": 0.6},
}

DEFAULT_VOICE_SETTINGS = {
    "stability":        0.55,
    "similarity_boost": 0.75,
    "style":            0.5,
    "use_speaker_boost": True,
}

OPENAI_VOICE_MAP = {
    "cipher":           "onyx",
    "oracle":           "echo",
    "ancestral_sage":   "fable",
    "ambassador":       "alloy",
    "default":          "onyx",
}


# ── AudioService ──────────────────────────────────────────────────────────────

class AudioService:
    """
    Multi-tier TTS service with rate limit handling and budget enforcement.

    Tier 1 — ElevenLabs (premium quality, budget-tracked)
    Tier 2 — OpenAI TTS (fallback, not budget-tracked here)
    Tier 3 — Text Performance Mode (zero-cost, always available)

    Args:
        elevenlabs_api_key:  ElevenLabs API key (sk-...)
        openai_api_key:      OpenAI API key
        monthly_char_budget: ElevenLabs monthly character allowance
        budget_used:         Characters already used this month (load from DB)
        max_retries:         Retry attempts on 429
        timeout:             Request timeout in seconds
    """

    def __init__(
        self,
        elevenlabs_api_key:  str = "",
        openai_api_key:      str = "",
        monthly_char_budget: int = 29500,
        budget_used:         int = 0,
        max_retries:         int = MAX_RETRY_ATTEMPTS,
        timeout:             int = DEFAULT_TIMEOUT,
    ):
        self.elevenlabs_api_key  = elevenlabs_api_key
        self.openai_api_key      = openai_api_key
        self.monthly_char_budget = monthly_char_budget
        self.budget_used         = budget_used
        self.max_retries         = max_retries
        self.timeout             = timeout

        self._cache: Dict[str, bytes] = {}   # SHA-256 → audio bytes

    # ── Public entry point ────────────────────────────────────────────────────

    def generate(
        self,
        text:         str,
        voice_id:     str = "",
        persona:      str = "cipher",
        preview_only: bool = False,
        force_tier:   Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate audio for the given text.

        Args:
            text:         Raw text, may include performance markup tags
            voice_id:     ElevenLabs voice ID (leave blank to skip ElevenLabs)
            persona:      Persona name (used for OpenAI voice selection)
            preview_only: Truncate to ~15 seconds of audio
            force_tier:   "elevenlabs" | "openai" | "text" — skip lower tiers

        Returns dict:
            {
                "tier":       "elevenlabs" | "openai" | "text",
                "audio":      bytes | None,
                "text":       str (clean text, markup stripped),
                "char_count": int,
                "cached":     bool,
                "budget_remaining": int,   (ElevenLabs tier only)
                "display_text": str,       (text tier only)
            }
        """
        clean_text, voice_settings = self._parse_markup(text)

        if preview_only:
            clean_text = self._truncate_for_preview(clean_text)

        char_count = len(clean_text)

        # ── Tier 1: ElevenLabs ────────────────────────────────────────────────
        if force_tier in (None, "elevenlabs") and self.elevenlabs_api_key and voice_id:
            budget_check = self._check_budget(char_count)
            if budget_check["ok"]:
                try:
                    audio_bytes, cached = self._elevenlabs_tts(
                        text=clean_text,
                        voice_id=voice_id,
                        voice_settings=voice_settings,
                    )
                    if not cached:
                        self.budget_used += char_count
                    remaining = self.monthly_char_budget - self.budget_used
                    if remaining / self.monthly_char_budget < (1 - BUDGET_WARNING_PCT):
                        logger.warning(
                            "ElevenLabs budget at %.0f%% — %d chars remaining",
                            (self.budget_used / self.monthly_char_budget) * 100,
                            remaining,
                        )
                    return {
                        "tier":             "elevenlabs",
                        "audio":            audio_bytes,
                        "text":             clean_text,
                        "char_count":       char_count,
                        "cached":           cached,
                        "budget_remaining": remaining,
                    }
                except (AudioRateLimitError, AudioTokenExpiredError) as exc:
                    logger.warning("ElevenLabs failed (%s) — falling back to OpenAI", exc)
                except AudioServiceError as exc:
                    logger.warning("ElevenLabs error (%s) — falling back", exc)
            else:
                logger.warning(
                    "ElevenLabs budget exceeded (%s/%s chars) — skipping to OpenAI",
                    self.budget_used, self.monthly_char_budget,
                )
                if budget_check["hard_stop"]:
                    raise AudioBudgetExceededError(self.budget_used, self.monthly_char_budget)

        # ── Tier 2: OpenAI TTS ────────────────────────────────────────────────
        if force_tier in (None, "openai", "elevenlabs") and self.openai_api_key:
            try:
                audio_bytes = self._openai_tts(
                    text=clean_text,
                    persona=persona,
                )
                return {
                    "tier":       "openai",
                    "audio":      audio_bytes,
                    "text":       clean_text,
                    "char_count": char_count,
                    "cached":     False,
                }
            except (AudioRateLimitError, AudioTokenExpiredError) as exc:
                logger.warning("OpenAI TTS failed (%s) — falling back to text", exc)
            except AudioServiceError as exc:
                logger.warning("OpenAI TTS error (%s) — falling back", exc)

        # ── Tier 3: Text Performance Mode ─────────────────────────────────────
        display_text = self._build_text_performance(text)
        return {
            "tier":         "text",
            "audio":        None,
            "text":         clean_text,
            "char_count":   char_count,
            "cached":       False,
            "display_text": display_text,
        }

    def generate_preview(self, text: str, **kwargs) -> Dict[str, Any]:
        """Convenience wrapper — always generates a 15-second preview."""
        return self.generate(text=text, preview_only=True, **kwargs)

    # ── ElevenLabs ────────────────────────────────────────────────────────────

    def _elevenlabs_tts(
        self,
        text:           str,
        voice_id:       str,
        voice_settings: Dict,
    ) -> Tuple[bytes, bool]:
        """
        Call ElevenLabs TTS API with retry logic.
        Returns (audio_bytes, was_cached).
        """
        cache_key = self._cache_key(text, voice_id)
        if cache_key in self._cache:
            logger.debug("ElevenLabs cache hit — %s chars", len(text))
            return self._cache[cache_key], True

        url     = ELEVENLABS_TTS_URL.format(voice_id=voice_id)
        headers = {
            "xi-api-key":    self.elevenlabs_api_key,
            "Content-Type":  "application/json",
            "Accept":        "audio/mpeg",
        }
        payload = {
            "text":           text,
            "model_id":       "eleven_multilingual_v2",
            "voice_settings": {**DEFAULT_VOICE_SETTINGS, **voice_settings},
        }

        audio_bytes = self._post_with_retry(
            provider="ElevenLabs",
            url=url,
            headers=headers,
            json_payload=payload,
            expected_content_type="audio/",
        )

        self._cache[cache_key] = audio_bytes
        return audio_bytes, False

    # ── OpenAI TTS ────────────────────────────────────────────────────────────

    def _openai_tts(self, text: str, persona: str = "cipher") -> bytes:
        """Call OpenAI TTS API with retry logic. Returns audio bytes."""
        voice = OPENAI_VOICE_MAP.get(persona, OPENAI_VOICE_MAP["default"])
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model":           "tts-1",
            "input":           text,
            "voice":           voice,
            "response_format": "mp3",
        }

        return self._post_with_retry(
            provider="OpenAI",
            url=OPENAI_TTS_URL,
            headers=headers,
            json_payload=payload,
            expected_content_type="audio/",
        )

    # ── Shared HTTP dispatcher with retry ─────────────────────────────────────

    def _post_with_retry(
        self,
        provider:             str,
        url:                  str,
        headers:              Dict,
        json_payload:         Dict,
        expected_content_type: str = "audio/",
    ) -> bytes:
        """
        POST to a TTS endpoint, handling rate limits and token expiry.

        Args:
            provider:              "ElevenLabs" | "OpenAI" — used in log/error messages
            url:                   Full endpoint URL
            headers:               Request headers (including auth)
            json_payload:          JSON body to POST
            expected_content_type: Prefix to validate response Content-Type

        Returns raw response bytes on success.
        Raises AudioRateLimitError, AudioTokenExpiredError, or AudioServiceError.
        """
        attempt = 0

        while attempt <= self.max_retries:
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=json_payload,
                    timeout=self.timeout,
                )
            except requests.exceptions.ConnectionError as exc:
                raise AudioNetworkError(f"{provider} connection failed: {exc}") from exc
            except requests.exceptions.Timeout as exc:
                raise AudioNetworkError(
                    f"{provider} request timed out after {self.timeout}s"
                ) from exc

            # ── Success ───────────────────────────────────────────────────────
            if response.status_code in (200, 201):
                ct = response.headers.get("Content-Type", "")
                if expected_content_type and not ct.startswith(expected_content_type):
                    # Parse error body from JSON response instead of audio
                    try:
                        err = response.json()
                    except Exception:
                        err = response.text[:300]
                    raise AudioServiceError(
                        f"{provider} returned unexpected content type {ct!r}: {err}"
                    )
                return response.content

            # ── 429 Rate Limited ──────────────────────────────────────────────
            if response.status_code == 429:
                attempt += 1
                if attempt > self.max_retries:
                    retry_after = self._parse_retry_after(response)
                    raise AudioRateLimitError(provider=provider, retry_after=retry_after)

                wait = self._calc_backoff(attempt, response)
                logger.warning(
                    "%s 429 rate limit — waiting %.1fs (attempt %d/%d)",
                    provider, wait, attempt, self.max_retries,
                )
                time.sleep(wait)
                continue

            # ── 401 Token expired / invalid ───────────────────────────────────
            if response.status_code == 401:
                raise AudioTokenExpiredError(provider=provider)

            # ── 403 Forbidden ─────────────────────────────────────────────────
            if response.status_code == 403:
                raise AudioServiceError(
                    f"{provider} 403 Forbidden — check API key permissions"
                )

            # ── Other 4xx ─────────────────────────────────────────────────────
            if 400 <= response.status_code < 500:
                try:
                    err = response.json()
                except Exception:
                    err = response.text[:300]
                raise AudioServiceError(f"{provider} error {response.status_code}: {err}")

            # ── 5xx — unexpected (HTTPAdapter handles 502/503/504 internally)
            raise AudioServiceError(
                f"{provider} server error {response.status_code}"
            )

        raise AudioServiceError(
            f"{provider} request failed after {self.max_retries} retries"
        )

    # ── Budget helpers ────────────────────────────────────────────────────────

    def _check_budget(self, chars_to_use: int) -> Dict[str, Any]:
        """
        Check whether using `chars_to_use` chars is within budget.

        Returns:
            {ok: bool, hard_stop: bool, pct_used: float, remaining: int}
        """
        projected = self.budget_used + chars_to_use
        pct       = projected / max(self.monthly_char_budget, 1)
        remaining = self.monthly_char_budget - self.budget_used
        return {
            "ok":        pct < BUDGET_HARD_STOP,
            "hard_stop": pct >= BUDGET_HARD_STOP,
            "pct_used":  round(pct, 4),
            "remaining": remaining,
        }

    # ── Backoff helpers ───────────────────────────────────────────────────────

    def _parse_retry_after(self, response: requests.Response) -> float:
        val = response.headers.get("Retry-After", "")
        try:
            return float(val)
        except (ValueError, TypeError):
            return 2.0

    def _calc_backoff(self, attempt: int, response: requests.Response) -> float:
        retry_after = self._parse_retry_after(response)
        if retry_after > 0:
            return min(retry_after, RATE_MAX_WAIT)
        return min(RATE_BASE_WAIT * (2 ** attempt), RATE_MAX_WAIT)

    # ── Markup / Text helpers ─────────────────────────────────────────────────

    def _parse_markup(self, text: str) -> Tuple[str, Dict[str, float]]:
        """
        Parse performance markup tags from text.
        Returns (clean_text, averaged_voice_settings).

        Example:
            "[fire]I been carrying this truth[/fire]"
            → ("I been carrying this truth", {"stability": 0.30, ...})
        """
        pattern = r"\[(\w+)\]"
        found_tags = re.findall(pattern, text)
        clean_text = re.sub(r"\[/?[^\]]+\]", "", text).strip()

        if not found_tags:
            return clean_text, {}

        matched = [MARKUP_MAP[t] for t in found_tags if t in MARKUP_MAP]
        if not matched:
            return clean_text, {}

        # Average all matched settings
        keys = matched[0].keys()
        averaged = {
            k: round(sum(m[k] for m in matched) / len(matched), 3)
            for k in keys
        }
        return clean_text, averaged

    def _truncate_for_preview(self, text: str) -> str:
        """Truncate text to approximately PREVIEW_SECONDS of audio at a word boundary."""
        if len(text) <= PREVIEW_MAX_CHARS:
            return text
        cut = text[:PREVIEW_MAX_CHARS]
        # Walk back to the last space to avoid mid-word cuts
        last_space = cut.rfind(" ")
        if last_space > PREVIEW_MAX_CHARS * 0.5:
            cut = cut[:last_space]
        return cut.rstrip()

    def _build_text_performance(self, text: str) -> str:
        """
        Convert markup tags to readable stage directions for text-mode display.
        [fire] → ‹with intensity›
        """
        stage_map = {
            "whisper":   "‹softly›",
            "fire":      "‹with intensity›",
            "rise":      "‹voice rising›",
            "crescendo": "‹building›",
            "tender":    "‹tenderly›",
            "shout":     "‹full voice›",
            "grief":     "‹heavy›",
            "joy":       "‹bright›",
            "resolve":   "‹with conviction›",
        }
        result = text
        for tag, direction in stage_map.items():
            result = result.replace(f"[{tag}]", f" {direction} ")
            result = result.replace(f"[/{tag}]", "")
        # Clean up multiple spaces
        result = re.sub(r" {2,}", " ", result).strip()
        return result

    @staticmethod
    def _cache_key(text: str, voice_id: str) -> str:
        """SHA-256 cache key from text + voice_id."""
        payload = f"{voice_id}:{text}".encode()
        return hashlib.sha256(payload).hexdigest()
