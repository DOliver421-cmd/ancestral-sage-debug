"""
src/tests/test_audio_service.py
====================================
Full mocked test suite for AudioService.

Tests cover:
  - ElevenLabs tier: correct payload structure, voice_settings merged, audio bytes returned
  - OpenAI TTS tier: correct payload structure, fallback invoked correctly
  - Text performance tier: always available, display_text built from markup
  - 429 rate limit: Retry-After respected, retries occur, AudioRateLimitError raised
  - 401 token expired: AudioTokenExpiredError raised immediately
  - Budget enforcement: within budget proceeds, at limit raises AudioBudgetExceededError
  - Budget tracking: used chars incremented after successful ElevenLabs call
  - Cache: second identical request returns cached bytes without HTTP call
  - Performance markup parsing: tags stripped, voice_settings averaged correctly
  - Preview truncation: long text truncated at word boundary within target char count
  - Tier fallback chain: ElevenLabs 429 → OpenAI → success; ElevenLabs 429 + OpenAI 429 → text tier
  - Text performance display_text: markup replaced with stage directions

Run:
    python -m pytest src/tests/test_audio_service.py -v
    # or
    python -m unittest src.tests.test_audio_service -v
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.services.audio_service import (
    AudioService,
    AudioRateLimitError,
    AudioTokenExpiredError,
    AudioBudgetExceededError,
    AudioNetworkError,
    AudioServiceError,
    PREVIEW_MAX_CHARS,
    CHARS_PER_SECOND,
    MARKUP_MAP,
    OPENAI_VOICE_MAP,
)

import requests as _requests


# ── Helpers ───────────────────────────────────────────────────────────────────

FAKE_AUDIO_BYTES = b"\xff\xfb\x90\x00" * 100   # fake MP3-ish bytes

def make_response(status_code=200, content=None, headers=None, json_body=None):
    resp             = MagicMock(spec=_requests.Response)
    resp.status_code = status_code
    resp.headers     = headers or {}
    resp.content     = content or b""
    resp.text        = ""
    if json_body is not None:
        resp.json.return_value = json_body
    return resp


def make_audio_200():
    return make_response(
        200,
        content=FAKE_AUDIO_BYTES,
        headers={"Content-Type": "audio/mpeg"},
    )


def make_service(**kwargs):
    defaults = {
        "elevenlabs_api_key":  "el_test_key",
        "openai_api_key":      "sk-test-openai",
        "monthly_char_budget": 10000,
        "budget_used":         0,
        "max_retries":         3,
    }
    defaults.update(kwargs)
    return AudioService(**defaults)


# ══════════════════════════════════════════════════════════════════════════════
# 1. ElevenLabs tier — payload structure
# ══════════════════════════════════════════════════════════════════════════════

class TestElevenLabsPayload(unittest.TestCase):

    @patch("src.services.audio_service.requests.post")
    def test_elevenlabs_called_with_correct_url(self, mock_post):
        """ElevenLabs request targets /v1/text-to-speech/{voice_id}."""
        mock_post.return_value = make_audio_200()
        svc = make_service()

        svc.generate(text="Test line.", voice_id="voice_abc", persona="cipher")

        call_url = mock_post.call_args[0][0]
        self.assertIn("/v1/text-to-speech/voice_abc", call_url)

    @patch("src.services.audio_service.requests.post")
    def test_elevenlabs_payload_contains_text(self, mock_post):
        """Payload must include the clean text (markup stripped)."""
        mock_post.return_value = make_audio_200()
        svc = make_service()

        svc.generate(text="[fire]Truth like a match[/fire]", voice_id="v_123")

        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["text"], "Truth like a match")
        self.assertIn("voice_settings", payload)

    @patch("src.services.audio_service.requests.post")
    def test_elevenlabs_payload_model_id(self, mock_post):
        """Payload must specify model_id = eleven_multilingual_v2."""
        mock_post.return_value = make_audio_200()
        svc = make_service()

        svc.generate(text="hello", voice_id="v_123")

        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["model_id"], "eleven_multilingual_v2")

    @patch("src.services.audio_service.requests.post")
    def test_elevenlabs_auth_header(self, mock_post):
        """xi-api-key header must be present with the correct key."""
        mock_post.return_value = make_audio_200()
        svc = make_service(elevenlabs_api_key="el_my_real_key")

        svc.generate(text="line", voice_id="v_123")

        headers = mock_post.call_args[1]["headers"]
        self.assertEqual(headers["xi-api-key"], "el_my_real_key")

    @patch("src.services.audio_service.requests.post")
    def test_elevenlabs_returns_audio_bytes(self, mock_post):
        """Result tier is 'elevenlabs' and audio is the raw bytes."""
        mock_post.return_value = make_audio_200()
        svc = make_service()

        result = svc.generate(text="Test", voice_id="v_123")

        self.assertEqual(result["tier"], "elevenlabs")
        self.assertEqual(result["audio"], FAKE_AUDIO_BYTES)
        self.assertFalse(result["cached"])

    @patch("src.services.audio_service.requests.post")
    def test_elevenlabs_voice_settings_from_markup(self, mock_post):
        """[fire] markup must modify stability/style in the voice_settings payload."""
        mock_post.return_value = make_audio_200()
        svc = make_service()

        svc.generate(text="[fire]I burn[/fire]", voice_id="v_123")

        payload = mock_post.call_args[1]["json"]
        vs = payload["voice_settings"]
        # fire tag: stability=0.30
        self.assertAlmostEqual(vs["stability"], MARKUP_MAP["fire"]["stability"], places=2)
        self.assertAlmostEqual(vs["style"],     MARKUP_MAP["fire"]["style"],     places=2)

    @patch("src.services.audio_service.requests.post")
    def test_budget_used_incremented_after_success(self, mock_post):
        """budget_used must increase by len(clean_text) after a real ElevenLabs call."""
        mock_post.return_value = make_audio_200()
        svc = make_service(budget_used=100)

        text = "A short line."
        svc.generate(text=text, voice_id="v_123")

        self.assertEqual(svc.budget_used, 100 + len(text))

    @patch("src.services.audio_service.requests.post")
    def test_budget_not_incremented_on_cache_hit(self, mock_post):
        """Cache hit must NOT increment budget_used (already counted on first call)."""
        mock_post.return_value = make_audio_200()
        svc = make_service(budget_used=0)

        text = "Cache test line."
        svc.generate(text=text, voice_id="v_999")   # 1st call — hits API
        budget_after_first = svc.budget_used

        svc.generate(text=text, voice_id="v_999")   # 2nd call — cache hit
        self.assertEqual(svc.budget_used, budget_after_first)
        self.assertEqual(mock_post.call_count, 1)   # API only called once


# ══════════════════════════════════════════════════════════════════════════════
# 2. OpenAI TTS tier — payload structure
# ══════════════════════════════════════════════════════════════════════════════

class TestOpenAIPayload(unittest.TestCase):

    @patch("src.services.audio_service.requests.post")
    def test_openai_payload_structure(self, mock_post):
        """OpenAI payload must have model, input, voice, response_format."""
        mock_post.return_value = make_audio_200()
        svc = make_service(elevenlabs_api_key="")   # No ElevenLabs → falls to OpenAI

        svc.generate(text="Truth speaks", persona="oracle")

        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["model"],           "tts-1")
        self.assertEqual(payload["input"],           "Truth speaks")
        self.assertEqual(payload["voice"],           OPENAI_VOICE_MAP["oracle"])
        self.assertEqual(payload["response_format"], "mp3")

    @patch("src.services.audio_service.requests.post")
    def test_openai_auth_header(self, mock_post):
        """OpenAI request must use Bearer token in Authorization header."""
        mock_post.return_value = make_audio_200()
        svc = make_service(elevenlabs_api_key="", openai_api_key="sk-test-key-xyz")

        svc.generate(text="hello", persona="cipher")

        headers = mock_post.call_args[1]["headers"]
        self.assertEqual(headers["Authorization"], "Bearer sk-test-key-xyz")

    @patch("src.services.audio_service.requests.post")
    def test_openai_tier_label_in_result(self, mock_post):
        """Result tier must be 'openai' when ElevenLabs is disabled."""
        mock_post.return_value = make_audio_200()
        svc = make_service(elevenlabs_api_key="")

        result = svc.generate(text="Test", persona="cipher")

        self.assertEqual(result["tier"], "openai")
        self.assertEqual(result["audio"], FAKE_AUDIO_BYTES)

    @patch("src.services.audio_service.requests.post")
    def test_openai_voice_defaults_for_unknown_persona(self, mock_post):
        """Unknown persona maps to default voice."""
        mock_post.return_value = make_audio_200()
        svc = make_service(elevenlabs_api_key="")

        svc.generate(text="Test", persona="unknown_persona")

        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["voice"], OPENAI_VOICE_MAP["default"])


# ══════════════════════════════════════════════════════════════════════════════
# 3. Text tier — always available
# ══════════════════════════════════════════════════════════════════════════════

class TestTextTier(unittest.TestCase):

    def test_text_tier_when_no_api_keys(self):
        """With no keys, result is text tier with no audio."""
        svc = AudioService(elevenlabs_api_key="", openai_api_key="")
        result = svc.generate(text="Healing words", force_tier="text")

        self.assertEqual(result["tier"], "text")
        self.assertIsNone(result["audio"])
        self.assertIn("display_text", result)

    def test_text_tier_display_text_replaces_markup(self):
        """[fire] markup should become ‹with intensity› in display_text."""
        svc = AudioService()
        result = svc.generate(text="[fire]I burn bright[/fire]", force_tier="text")

        self.assertIn("with intensity", result["display_text"])
        self.assertNotIn("[fire]", result["display_text"])

    def test_text_tier_returns_clean_text(self):
        """'text' key in result must have markup stripped."""
        svc = AudioService()
        result = svc.generate(text="[whisper]Soft truth[/whisper]", force_tier="text")

        self.assertEqual(result["text"], "Soft truth")
        self.assertNotIn("[whisper]", result["text"])

    def test_text_tier_char_count_correct(self):
        svc = AudioService()
        text = "A clean line of spoken word"
        result = svc.generate(text=text, force_tier="text")
        self.assertEqual(result["char_count"], len(text))


# ══════════════════════════════════════════════════════════════════════════════
# 4. Rate limit handling (429)
# ══════════════════════════════════════════════════════════════════════════════

class TestRateLimitHandling(unittest.TestCase):

    @patch("src.services.audio_service.time.sleep")
    @patch("src.services.audio_service.requests.post")
    def test_retries_on_429_then_succeeds(self, mock_post, mock_sleep):
        """429 with Retry-After → service waits and retries."""
        resp_429 = make_response(429, headers={"Retry-After": "3.0"})
        resp_200 = make_audio_200()
        mock_post.side_effect = [resp_429, resp_200]

        svc = make_service(max_retries=3)
        result = svc.generate(text="truth", voice_id="v_123")

        self.assertEqual(result["tier"], "elevenlabs")
        mock_sleep.assert_called_once_with(3.0)

    @patch("src.services.audio_service.time.sleep")
    @patch("src.services.audio_service.requests.post")
    def test_raises_rate_limit_error_after_max_retries(self, mock_post, mock_sleep):
        """Exhausting all retries on 429 raises AudioRateLimitError."""
        resp_429 = make_response(429, headers={"Retry-After": "1.0"})
        mock_post.return_value = resp_429

        svc = make_service(max_retries=2, openai_api_key="")

        with self.assertRaises(AudioRateLimitError) as ctx:
            svc._post_with_retry(
                provider="ElevenLabs",
                url="https://api.elevenlabs.io/v1/text-to-speech/v",
                headers={},
                json_payload={},
                expected_content_type="audio/",
            )

        self.assertEqual(ctx.exception.provider, "ElevenLabs")
        self.assertEqual(ctx.exception.retry_after, 1.0)

    @patch("src.services.audio_service.time.sleep")
    @patch("src.services.audio_service.requests.post")
    def test_elevenlabs_429_falls_through_to_openai(self, mock_post, mock_sleep):
        """ElevenLabs rate limit exhaustion falls through to OpenAI tier."""
        resp_429 = make_response(429, headers={"Retry-After": "0.1"})
        resp_200 = make_audio_200()

        # First max_retries+1 calls → 429; then OpenAI → 200
        svc = make_service(max_retries=1)
        mock_post.side_effect = [resp_429, resp_429, resp_200]

        result = svc.generate(text="fallback test", voice_id="v_el")

        self.assertEqual(result["tier"], "openai")

    @patch("src.services.audio_service.time.sleep")
    @patch("src.services.audio_service.requests.post")
    def test_both_tiers_rate_limited_returns_text(self, mock_post, mock_sleep):
        """Both ElevenLabs and OpenAI rate limited → falls to text tier."""
        resp_429 = make_response(429, headers={"Retry-After": "0.1"})
        svc = make_service(max_retries=1)
        mock_post.return_value = resp_429

        result = svc.generate(text="resilience", voice_id="v_el")

        self.assertEqual(result["tier"], "text")
        self.assertIsNone(result["audio"])


# ══════════════════════════════════════════════════════════════════════════════
# 5. Token expiry handling (401)
# ══════════════════════════════════════════════════════════════════════════════

class TestTokenExpiryHandling(unittest.TestCase):

    @patch("src.services.audio_service.requests.post")
    def test_elevenlabs_401_raises_token_expired(self, mock_post):
        """ElevenLabs 401 → AudioTokenExpiredError with provider='ElevenLabs'."""
        mock_post.return_value = make_response(401)
        svc = make_service(openai_api_key="")   # force ElevenLabs only path

        with self.assertRaises(AudioTokenExpiredError) as ctx:
            svc._post_with_retry(
                provider="ElevenLabs",
                url="https://api.elevenlabs.io/v1/text-to-speech/v",
                headers={},
                json_payload={},
                expected_content_type="audio/",
            )
        self.assertEqual(ctx.exception.provider, "ElevenLabs")

    @patch("src.services.audio_service.requests.post")
    def test_openai_401_raises_token_expired(self, mock_post):
        """OpenAI 401 → AudioTokenExpiredError with provider='OpenAI'."""
        mock_post.return_value = make_response(401)
        svc = make_service()

        with self.assertRaises(AudioTokenExpiredError) as ctx:
            svc._post_with_retry(
                provider="OpenAI",
                url="https://api.openai.com/v1/audio/speech",
                headers={},
                json_payload={},
                expected_content_type="audio/",
            )
        self.assertEqual(ctx.exception.provider, "OpenAI")

    @patch("src.services.audio_service.requests.post")
    def test_elevenlabs_401_falls_through_to_openai(self, mock_post):
        """ElevenLabs 401 in generate() → falls through to OpenAI tier."""
        resp_401 = make_response(401)
        resp_200 = make_audio_200()
        mock_post.side_effect = [resp_401, resp_200]

        svc = make_service()
        result = svc.generate(text="legacy truth", voice_id="v_el")

        self.assertEqual(result["tier"], "openai")


# ══════════════════════════════════════════════════════════════════════════════
# 6. Budget enforcement
# ══════════════════════════════════════════════════════════════════════════════

class TestBudgetEnforcement(unittest.TestCase):

    @patch("src.services.audio_service.requests.post")
    def test_within_budget_proceeds(self, mock_post):
        """With budget remaining, ElevenLabs call proceeds normally."""
        mock_post.return_value = make_audio_200()
        svc = make_service(monthly_char_budget=1000, budget_used=0)

        result = svc.generate(text="short", voice_id="v_123")
        self.assertEqual(result["tier"], "elevenlabs")

    @patch("src.services.audio_service.requests.post")
    def test_at_budget_limit_raises_budget_exceeded(self, mock_post):
        """At 100% budget, raises AudioBudgetExceededError."""
        svc = make_service(monthly_char_budget=100, budget_used=100)

        with self.assertRaises(AudioBudgetExceededError):
            svc.generate(text="any text", voice_id="v_123")

        mock_post.assert_not_called()

    @patch("src.services.audio_service.requests.post")
    def test_budget_check_includes_current_chars(self, mock_post):
        """Budget check adds current request chars before deciding."""
        svc = make_service(monthly_char_budget=100, budget_used=95)

        # "hello world" is 11 chars → 95+11=106 > 100 → budget exceeded
        with self.assertRaises(AudioBudgetExceededError):
            svc.generate(text="hello world", voice_id="v_123")

        mock_post.assert_not_called()

    def test_check_budget_returns_correct_structure(self):
        """_check_budget returns expected keys and correct arithmetic."""
        svc = make_service(monthly_char_budget=1000, budget_used=500)
        result = svc._check_budget(100)

        self.assertIn("ok",        result)
        self.assertIn("hard_stop", result)
        self.assertIn("pct_used",  result)
        self.assertIn("remaining", result)
        self.assertTrue(result["ok"])
        self.assertFalse(result["hard_stop"])
        self.assertAlmostEqual(result["pct_used"], 0.60, places=2)
        self.assertEqual(result["remaining"], 500)


# ══════════════════════════════════════════════════════════════════════════════
# 7. Audio cache
# ══════════════════════════════════════════════════════════════════════════════

class TestAudioCache(unittest.TestCase):

    @patch("src.services.audio_service.requests.post")
    def test_second_call_uses_cache(self, mock_post):
        """Same text + voice_id → second call returns from cache, no HTTP."""
        mock_post.return_value = make_audio_200()
        svc = make_service()

        r1 = svc.generate(text="cache me", voice_id="v_999")
        r2 = svc.generate(text="cache me", voice_id="v_999")

        self.assertEqual(mock_post.call_count, 1)
        self.assertTrue(r2["cached"])
        self.assertEqual(r1["audio"], r2["audio"])

    @patch("src.services.audio_service.requests.post")
    def test_different_voice_id_not_cached(self, mock_post):
        """Different voice_id → different cache key → two API calls."""
        mock_post.return_value = make_audio_200()
        svc = make_service()

        svc.generate(text="same text", voice_id="voice_A")
        svc.generate(text="same text", voice_id="voice_B")

        self.assertEqual(mock_post.call_count, 2)


# ══════════════════════════════════════════════════════════════════════════════
# 8. Performance markup parsing
# ══════════════════════════════════════════════════════════════════════════════

class TestMarkupParsing(unittest.TestCase):

    def test_single_tag_strips_and_maps_settings(self):
        svc = make_service()
        clean, settings = svc._parse_markup("[whisper]Soft truth[/whisper]")

        self.assertEqual(clean, "Soft truth")
        self.assertAlmostEqual(settings["stability"], MARKUP_MAP["whisper"]["stability"], places=3)

    def test_multiple_tags_averaged(self):
        svc = make_service()
        _, settings = svc._parse_markup("[fire]Burn[/fire] [whisper]and breathe[/whisper]")

        expected_stability = (MARKUP_MAP["fire"]["stability"] + MARKUP_MAP["whisper"]["stability"]) / 2
        self.assertAlmostEqual(settings["stability"], round(expected_stability, 3), places=2)

    def test_no_tags_returns_unchanged_text(self):
        svc = make_service()
        clean, settings = svc._parse_markup("Plain text no tags")

        self.assertEqual(clean, "Plain text no tags")
        self.assertEqual(settings, {})

    def test_unknown_tag_stripped_but_ignored_in_settings(self):
        svc = make_service()
        clean, settings = svc._parse_markup("[unknown]Text here[/unknown]")

        self.assertEqual(clean, "Text here")
        self.assertEqual(settings, {})


# ══════════════════════════════════════════════════════════════════════════════
# 9. Preview truncation
# ══════════════════════════════════════════════════════════════════════════════

class TestPreviewTruncation(unittest.TestCase):

    def test_short_text_not_truncated(self):
        svc = make_service()
        short = "Short line."
        result = svc._truncate_for_preview(short)
        self.assertEqual(result, short)

    def test_long_text_truncated_within_limit(self):
        svc = make_service()
        long_text = "word " * 500   # 2500 chars
        result = svc._truncate_for_preview(long_text)

        self.assertLessEqual(len(result), PREVIEW_MAX_CHARS + 10)

    def test_truncation_at_word_boundary(self):
        """Truncation must not cut in the middle of a word."""
        svc = make_service()
        # Use a distinctive word so a partial cut is easy to detect
        long_text = "spoken " * 500   # 3500 chars of "spoken " tokens
        result = svc._truncate_for_preview(long_text)

        # After truncation, last token must be the complete word "spoken"
        # (not a partial like "spok", "spo", etc.)
        last_token = result.rstrip().split()[-1]
        self.assertEqual(last_token, "spoken",
            f"Expected last word to be 'spoken' (complete), got '{last_token}'")

    def test_preview_flag_in_generate(self):
        """preview_only=True must produce char_count <= PREVIEW_MAX_CHARS + small buffer."""
        svc = AudioService()   # no keys → text tier
        long_text = "spoken word line " * 200
        result = svc.generate(text=long_text, preview_only=True, force_tier="text")

        self.assertLessEqual(result["char_count"], PREVIEW_MAX_CHARS + 20)


# ══════════════════════════════════════════════════════════════════════════════
# 10. Network errors
# ══════════════════════════════════════════════════════════════════════════════

class TestNetworkErrors(unittest.TestCase):

    @patch("src.services.audio_service.requests.post",
           side_effect=_requests.exceptions.ConnectionError("DNS failure"))
    def test_connection_error_raises_audio_network_error(self, _):
        svc = make_service(openai_api_key="")

        with self.assertRaises(AudioNetworkError):
            svc._post_with_retry(
                provider="ElevenLabs",
                url="https://api.elevenlabs.io/v1/text-to-speech/v",
                headers={},
                json_payload={},
                expected_content_type="audio/",
            )

    @patch("src.services.audio_service.requests.post",
           side_effect=_requests.exceptions.Timeout("timed out"))
    def test_timeout_raises_audio_network_error(self, _):
        svc = make_service()

        with self.assertRaises(AudioNetworkError):
            svc._post_with_retry(
                provider="OpenAI",
                url="https://api.openai.com/v1/audio/speech",
                headers={},
                json_payload={},
                expected_content_type="audio/",
            )


# ══════════════════════════════════════════════════════════════════════════════
# 11. Cache key uniqueness
# ══════════════════════════════════════════════════════════════════════════════

class TestCacheKey(unittest.TestCase):

    def test_same_inputs_same_key(self):
        k1 = AudioService._cache_key("hello", "v_1")
        k2 = AudioService._cache_key("hello", "v_1")
        self.assertEqual(k1, k2)

    def test_different_text_different_key(self):
        k1 = AudioService._cache_key("hello", "v_1")
        k2 = AudioService._cache_key("world", "v_1")
        self.assertNotEqual(k1, k2)

    def test_different_voice_different_key(self):
        k1 = AudioService._cache_key("same text", "voice_A")
        k2 = AudioService._cache_key("same text", "voice_B")
        self.assertNotEqual(k1, k2)

    def test_key_is_64_char_hex(self):
        key = AudioService._cache_key("text", "v_id")
        self.assertEqual(len(key), 64)
        int(key, 16)   # raises if not valid hex


# ══════════════════════════════════════════════════════════════════════════════
# 12. generate_preview convenience wrapper
# ══════════════════════════════════════════════════════════════════════════════

class TestGeneratePreview(unittest.TestCase):

    def test_generate_preview_delegates_with_preview_only(self):
        svc = AudioService()
        long_text = "x " * 500
        result = svc.generate_preview(text=long_text)

        self.assertLessEqual(result["char_count"], PREVIEW_MAX_CHARS + 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)
