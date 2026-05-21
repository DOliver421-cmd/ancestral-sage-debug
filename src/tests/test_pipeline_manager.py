"""
src/tests/test_pipeline_manager.py
====================================
Full mocked test suite for PipelineManager.

Tests cover:
  - Input validation (empty, too short, OK)
  - Content blocking (spam patterns)
  - LLM intent analysis: correct payload structure to Anthropic, response parsing
  - LLM rate limit (429): raises, falls back to keyword scorer
  - LLM token expiry (401): falls back to keyword scorer
  - LLM JSON parse error: falls back to keyword scorer
  - Keyword fallback: theme detection, intent detection, viral detection, confidence cap
  - Route decisions: seeking→outreach, viral→merch, low-conf→discovery,
      neutral+none→neutral, sharing→outreach, trending→outreach
  - Edge cases: neutral theme + none intent, just below LOW_CONFIDENCE_THRESHOLD
  - process() end-to-end with mocked LLM and mocked pipeline imports
  - Cache: same text second call → cached=True, zero HTTP calls
  - Batch processing: concurrent results
  - Analysis dataclass structure: all required fields present

Run:
    python -m pytest src/tests/test_pipeline_manager.py -v
    python -m unittest src.tests.test_pipeline_manager -v
"""

import sys
import os
import asyncio
import json
import unittest
from unittest.mock import MagicMock, patch, AsyncMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.agents.pipeline_manager import (
    PipelineManager,
    IntentAnalysis,
    PipelineResult,
    ROUTE_OUTREACH,
    ROUTE_MERCH,
    ROUTE_DISCOVERY,
    ROUTE_NEUTRAL,
    ROUTE_BLOCKED,
    LOW_CONFIDENCE_THRESHOLD,
    HIGH_CONFIDENCE_THRESHOLD,
    VIRAL_SCORE_THRESHOLD,
)


# ── Test helpers ──────────────────────────────────────────────────────────────

def run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


def make_llm_response(
    theme="grief",
    intent="seeking",
    confidence=0.85,
    sentiment="negative",
    urgency="high",
    viral_potential=False,
    keywords=None,
):
    """Build a mock Anthropic API response body."""
    analysis = {
        "theme":           theme,
        "intent":          intent,
        "confidence":      confidence,
        "sentiment":       sentiment,
        "urgency":         urgency,
        "viral_potential": viral_potential,
        "keywords":        keywords or ["grief", "healing", "poetry"],
    }
    return {
        "id":    "msg_test",
        "type":  "message",
        "role":  "assistant",
        "model": "claude-haiku-4-5",
        "content": [{"type": "text", "text": json.dumps(analysis)}],
        "usage": {"input_tokens": 200, "output_tokens": 80},
    }


def make_mock_http_response(response_body, status_code=200, headers=None):
    """Create a mock httpx-style response for _post_to_anthropic."""
    resp             = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = response_body if response_body is not None else {}
    resp.headers     = headers or {}
    resp.text        = json.dumps(response_body or {})
    return resp


def patch_llm(manager, response_body, status_code=200, headers=None):
    """
    Context manager: patches manager._post_to_anthropic to return
    a fake HTTP response — replaces @patch('requests.post') from V1.

    Usage:
        with patch_llm(mgr, make_llm_response()) as mock_post:
            result = run(mgr.process("..."))
    """
    resp = make_mock_http_response(response_body, status_code, headers)
    return patch.object(manager, "_post_to_anthropic", new=AsyncMock(return_value=resp))


def make_manager(api_key="test_key_abc", db=None):
    return PipelineManager(db=db, anthropic_api_key=api_key)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Input validation
# ══════════════════════════════════════════════════════════════════════════════

class TestInputValidation(unittest.TestCase):

    def test_empty_string_returns_neutral_route(self):
        mgr    = make_manager()
        result = run(mgr.process(""))
        self.assertEqual(result.route, ROUTE_NEUTRAL)
        self.assertIsNotNone(result.error)

    def test_whitespace_only_returns_neutral_route(self):
        mgr    = make_manager()
        result = run(mgr.process("   \n\t  "))
        self.assertEqual(result.route, ROUTE_NEUTRAL)
        self.assertIsNotNone(result.error)

    def test_too_short_returns_neutral(self):
        mgr    = make_manager()
        result = run(mgr.process("ok"))   # 2 chars < MIN_TEXT_LENGTH=8
        self.assertEqual(result.route, ROUTE_NEUTRAL)
        self.assertIsNotNone(result.error)

    def test_valid_text_passes_validation(self):
        mgr = make_manager(api_key="")   # no key → keyword fallback
        result = run(mgr.process("I am looking for healing poetry about grief"))
        # Should NOT be NEUTRAL due to error (validation should pass)
        self.assertIsNone(result.error)

    def test_minimum_length_boundary(self):
        """Exactly MIN_TEXT_LENGTH chars must pass, MIN_TEXT_LENGTH-1 must fail."""
        from src.agents.pipeline_manager import MIN_TEXT_LENGTH
        mgr = make_manager(api_key="")

        short = "x" * (MIN_TEXT_LENGTH - 1)
        exact = "x" * MIN_TEXT_LENGTH

        result_short = run(mgr.process(short))
        result_exact = run(mgr.process(exact))

        self.assertIsNotNone(result_short.error)
        self.assertIsNone(result_exact.error)


# ══════════════════════════════════════════════════════════════════════════════
# 2. Content blocking
# ══════════════════════════════════════════════════════════════════════════════

class TestContentBlocking(unittest.TestCase):

    def test_spam_buy_now_is_blocked(self):
        mgr    = make_manager()
        result = run(mgr.process("buy now limited offer click here today"))
        self.assertEqual(result.route, ROUTE_BLOCKED)

    def test_bitly_link_is_blocked(self):
        mgr    = make_manager()
        result = run(mgr.process("check this out https://bit.ly/xyz amazing deal"))
        self.assertEqual(result.route, ROUTE_BLOCKED)

    def test_normal_text_is_not_blocked(self):
        mgr    = make_manager(api_key="")
        result = run(mgr.process("I been carrying this truth like a match between my teeth"))
        self.assertNotEqual(result.route, ROUTE_BLOCKED)

    def test_blocking_check_is_case_insensitive(self):
        mgr    = make_manager()
        result = run(mgr.process("BUY NOW and get unlimited access CLICK HERE"))
        self.assertEqual(result.route, ROUTE_BLOCKED)


# ══════════════════════════════════════════════════════════════════════════════
# 3. LLM intent analysis — payload structure
# ══════════════════════════════════════════════════════════════════════════════

class TestLLMIntentAnalysis(unittest.TestCase):

    def test_anthropic_called_with_correct_model(self):
        """LLM call must specify the correct Anthropic model."""
        mgr = make_manager()
        with patch_llm(mgr, make_llm_response()) as mock_post:
            run(mgr.process("looking for healing poetry about grief"))
            payload = mock_post.call_args[0][0]   # first positional arg = payload dict
        self.assertEqual(payload["model"], "claude-haiku-4-5")

    def test_anthropic_api_key_in_header(self):
        """x-api-key header must be the key passed to PipelineManager."""
        mgr = make_manager(api_key="sk-ant-specific-key")
        with patch_llm(mgr, make_llm_response()) as mock_post:
            run(mgr.process("looking for healing poetry about grief"))
            headers = mock_post.call_args[0][1]   # second positional arg = headers dict
        self.assertEqual(headers["x-api-key"], "sk-ant-specific-key")

    def test_text_included_in_prompt(self):
        """User text must appear in the LLM prompt."""
        mgr       = make_manager()
        test_text = "struggling with identity and blackness these days"
        with patch_llm(mgr, make_llm_response()) as mock_post:
            run(mgr.process(test_text))
            payload = mock_post.call_args[0][0]
        prompt = payload["messages"][0]["content"]
        self.assertIn(test_text, prompt)

    def test_analysis_fields_populated_from_llm(self):
        """Returned IntentAnalysis must contain all fields from LLM response."""
        mgr = make_manager()
        with patch_llm(mgr, make_llm_response(
            theme="grief", intent="seeking", confidence=0.9,
            sentiment="negative", urgency="high",
            viral_potential=False, keywords=["grief", "healing", "loss"],
        )):
            result = run(mgr.process("looking for something about grief"))

        a = result.analysis
        self.assertEqual(a.theme,    "grief")
        self.assertEqual(a.intent,   "seeking")
        self.assertAlmostEqual(a.confidence, 0.9, places=2)
        self.assertEqual(a.sentiment, "negative")
        self.assertEqual(a.urgency,   "high")
        self.assertFalse(a.viral_potential)
        self.assertIn("grief", a.keywords)
        self.assertEqual(a.analyzer, "llm")

    def test_anthropic_version_header_present(self):
        """anthropic-version header is required by the API."""
        mgr = make_manager()
        with patch_llm(mgr, make_llm_response()) as mock_post:
            run(mgr.process("healing poem for someone I lost"))
            headers = mock_post.call_args[0][1]
        self.assertIn("anthropic-version", headers)


# ══════════════════════════════════════════════════════════════════════════════
# 4. LLM error handling → keyword fallback
# ══════════════════════════════════════════════════════════════════════════════

class TestLLMErrorHandling(unittest.TestCase):

    def test_429_rate_limit_falls_back_to_keyword(self):
        """Anthropic 429 → falls back to keyword scoring, not an exception."""
        mgr = make_manager()
        with patch_llm(mgr, {}, status_code=429, headers={"Retry-After": "2"}):
            result = run(mgr.process("looking for healing poetry about grief"))

        self.assertIsNotNone(result.analysis)
        self.assertEqual(result.analysis.analyzer, "keyword_fallback")
        self.assertIsNotNone(result.analysis.error)   # error stored but not raised

    def test_401_expired_key_falls_back_to_keyword(self):
        """Anthropic 401 → falls back to keyword scoring."""
        mgr = make_manager()
        with patch_llm(mgr, {"error": "invalid key"}, status_code=401):
            result = run(mgr.process("struggling with grief and loss"))

        self.assertEqual(result.analysis.analyzer, "keyword_fallback")
        self.assertIsNotNone(result.analysis.error)

    def test_malformed_json_falls_back_to_keyword(self):
        """LLM returning non-JSON → falls back to keyword scorer."""
        mgr      = make_manager()
        bad_body = {"content": [{"type": "text", "text": "I cannot analyze this."}]}
        with patch_llm(mgr, bad_body):
            result = run(mgr.process("poetry about healing and grief"))

        self.assertEqual(result.analysis.analyzer, "keyword_fallback")

    def test_network_error_falls_back_to_keyword(self):
        """Network failure → falls back to keyword scorer gracefully."""
        mgr = make_manager()
        with patch.object(
            mgr, "_post_to_anthropic",
            new=AsyncMock(side_effect=Exception("network error")),
        ):
            result = run(mgr.process("need a healing poem for grief"))

        self.assertEqual(result.analysis.analyzer, "keyword_fallback")
        # Must still produce a usable result
        self.assertIsNotNone(result.route)

    def test_no_api_key_uses_keyword_fallback(self):
        """No API key → keyword fallback, no HTTP call at all."""
        mgr = PipelineManager(db=None, anthropic_api_key="")
        with patch.object(mgr, "_post_to_anthropic", new=AsyncMock()) as mock_http:
            result = run(mgr.process("I am looking for healing poetry about grief"))
            mock_http.assert_not_called()

        self.assertEqual(result.analysis.analyzer, "keyword_fallback")


# ══════════════════════════════════════════════════════════════════════════════
# 5. Keyword fallback scorer
# ══════════════════════════════════════════════════════════════════════════════

class TestKeywordScorer(unittest.TestCase):

    def _score(self, text):
        mgr = PipelineManager(db=None, anthropic_api_key="")
        return mgr._keyword_score(text)

    def test_detects_seeking_intent_from_keywords(self):
        a = self._score("looking for healing poetry about grief")
        self.assertEqual(a.intent, "seeking")
        self.assertGreater(a.confidence, 0)

    def test_detects_sharing_intent(self):
        a = self._score("I been carrying this truth for years")
        self.assertEqual(a.intent, "sharing")

    def test_detects_known_theme(self):
        a = self._score("struggling with grief and loss every day")
        self.assertIn(a.theme, ["grief", "loss", "struggle"])

    def test_neutral_theme_on_unrecognized_text(self):
        a = self._score("today is wednesday and the sky is blue")
        self.assertEqual(a.theme, "neutral")
        self.assertEqual(a.intent, "none")

    def test_viral_detected_when_indicator_present(self):
        a = self._score("this hits different. nobody talks about this pain")
        self.assertTrue(a.viral_potential)

    def test_confidence_capped_at_0_55_for_keyword_fallback(self):
        """Keyword fallback must never exceed 0.55 confidence."""
        a = self._score(
            "looking for grief healing trauma loss struggle love identity blackness "
            "resilience hope this hits different nobody talks about"
        )
        self.assertLessEqual(a.confidence, 0.55)

    def test_positive_sentiment_detected(self):
        a = self._score("filled with joy and hope and love today")
        self.assertEqual(a.sentiment, "positive")

    def test_negative_sentiment_detected(self):
        a = self._score("drowning in grief and trauma every day")
        self.assertEqual(a.sentiment, "negative")

    def test_analyzer_label_is_keyword_fallback(self):
        a = self._score("some text about healing")
        self.assertEqual(a.analyzer, "keyword_fallback")

    def test_keywords_list_populated(self):
        a = self._score("healing grief love hope identity resilience")
        self.assertIsInstance(a.keywords, list)
        self.assertGreater(len(a.keywords), 0)


# ══════════════════════════════════════════════════════════════════════════════
# 6. Route decision logic
# ══════════════════════════════════════════════════════════════════════════════

class TestRouteDecision(unittest.TestCase):

    def _route(self, **kwargs) -> str:
        """Build an IntentAnalysis and run _decide_route."""
        defaults = dict(
            theme="grief", intent="seeking", confidence=0.85,
            sentiment="negative", urgency="high",
            viral_potential=False, keywords=["grief"],
            analyzer="llm", raw_score=4,
        )
        defaults.update(kwargs)
        analysis = IntentAnalysis(**defaults)
        return PipelineManager()._decide_route(analysis)

    def test_seeking_high_confidence_routes_to_outreach(self):
        r = self._route(intent="seeking", confidence=0.85)
        self.assertEqual(r, ROUTE_OUTREACH)

    def test_seeking_medium_confidence_still_outreach(self):
        r = self._route(intent="seeking", confidence=0.40)
        self.assertEqual(r, ROUTE_OUTREACH)

    def test_sharing_routes_to_outreach(self):
        r = self._route(intent="sharing", confidence=0.70)
        self.assertEqual(r, ROUTE_OUTREACH)

    def test_trending_routes_to_outreach(self):
        r = self._route(intent="trending", confidence=0.75)
        self.assertEqual(r, ROUTE_OUTREACH)

    def test_viral_high_confidence_routes_to_merch(self):
        r = self._route(intent="sharing", confidence=0.80, viral_potential=True)
        self.assertEqual(r, ROUTE_MERCH)

    def test_viral_below_threshold_does_not_route_to_merch(self):
        r = self._route(
            intent="sharing",
            confidence=VIRAL_SCORE_THRESHOLD - 0.01,
            viral_potential=True,
        )
        # Below viral threshold — should be outreach or discovery, not merch
        self.assertNotEqual(r, ROUTE_MERCH)

    def test_low_confidence_routes_to_discovery(self):
        r = self._route(confidence=LOW_CONFIDENCE_THRESHOLD - 0.01)
        self.assertEqual(r, ROUTE_DISCOVERY)

    def test_exactly_at_low_confidence_threshold_is_discovery(self):
        """Just BELOW LOW_CONFIDENCE_THRESHOLD → discovery."""
        r = self._route(confidence=LOW_CONFIDENCE_THRESHOLD - 0.001, intent="none")
        self.assertEqual(r, ROUTE_DISCOVERY)

    def test_neutral_theme_no_intent_routes_to_neutral(self):
        r = self._route(theme="neutral", intent="none", confidence=0.80)
        self.assertEqual(r, ROUTE_NEUTRAL)

    def test_neutral_theme_but_seeking_intent_is_not_neutral(self):
        """Even with neutral theme, seeking intent should get a route."""
        r = self._route(theme="neutral", intent="seeking", confidence=0.70)
        self.assertNotEqual(r, ROUTE_NEUTRAL)

    def test_known_theme_no_clear_intent_goes_to_discovery(self):
        """Has theme but no intent → discovery pool."""
        r = self._route(theme="grief", intent="none", confidence=0.45)
        self.assertEqual(r, ROUTE_DISCOVERY)

    def test_merch_takes_priority_over_outreach_for_viral_content(self):
        """Viral + high confidence → merch wins over outreach."""
        r = self._route(
            intent="sharing", confidence=0.85, viral_potential=True
        )
        self.assertEqual(r, ROUTE_MERCH)


# ══════════════════════════════════════════════════════════════════════════════
# 7. End-to-end process() with mocked pipelines
# ══════════════════════════════════════════════════════════════════════════════

class TestEndToEnd(unittest.TestCase):

    def test_seeking_leads_to_outreach_pipeline_call(self):
        """process() with seeking intent triggers the outreach pipeline."""
        mock_matcher = AsyncMock(return_value={
            "matched": True,
            "product": {"name": "Healing"},
            "confidence": 0.8,
            "strategy": "direct_recommendation",
        })
        mock_engine = AsyncMock(return_value={
            "response_text": "Here is something for you",
            "checkout_url": "https://wai.lemonsqueezy.com/l/test",
        })

        mgr = make_manager()

        with patch_llm(mgr, make_llm_response(intent="seeking", confidence=0.88)):
            with patch.dict("sys.modules", {
                "wai_institute": MagicMock(),
                "wai_institute.pipelines": MagicMock(),
                "wai_institute.pipelines.contextual_matcher": MagicMock(
                    ContextualMatcher=MagicMock(
                        return_value=MagicMock(match=mock_matcher)
                    )
                ),
                "wai_institute.pipelines.conversational_engine": MagicMock(
                    ConversationalEngine=MagicMock(
                        return_value=MagicMock(craft_response=mock_engine)
                    )
                ),
            }):
                result = run(mgr.process("looking for healing poetry about grief and loss"))

        self.assertEqual(result.route, ROUTE_OUTREACH)
        self.assertIn("stage", result.pipeline_outputs)
        self.assertEqual(result.pipeline_outputs["stage"], "outreach")

    def test_viral_content_triggers_merch_pipeline(self):
        """Viral content with high confidence → merch route."""
        mock_merch_result = {
            "title": "I Been Carrying This Truth...",
            "products": [{"status": "draft"}],
            "total_created": 1,
        }
        mock_merch_pipeline = AsyncMock(return_value=mock_merch_result)

        mgr = make_manager()

        with patch_llm(
            mgr,
            make_llm_response(intent="sharing", confidence=0.90, viral_potential=True),
        ):
            with patch.dict("sys.modules", {
                "wai_institute": MagicMock(),
                "wai_institute.pipelines": MagicMock(),
                "wai_institute.pipelines.merch_pipeline": MagicMock(
                    MerchPipeline=MagicMock(
                        return_value=MagicMock(
                            create_merch_from_text=mock_merch_pipeline
                        )
                    )
                ),
            }):
                result = run(mgr.process("this hits different. nobody talks about carrying truth"))

        self.assertEqual(result.route, ROUTE_MERCH)

    def test_neutral_intent_no_pipeline_executed(self):
        """Neutral theme + no intent → ROUTE_NEUTRAL, no pipeline calls."""
        mgr    = PipelineManager(db=None, anthropic_api_key="")
        result = run(mgr.process("today is a regular wednesday afternoon"))

        self.assertEqual(result.route, ROUTE_NEUTRAL)
        self.assertEqual(result.pipeline_outputs.get("action"), "skipped")

    def test_result_contains_execution_ms(self):
        """Every result must include a non-negative execution_ms."""
        mgr    = make_manager(api_key="")
        result = run(mgr.process("I am looking for healing poetry today"))
        self.assertGreaterEqual(result.execution_ms, 0)

    def test_result_to_dict_is_serializable(self):
        """PipelineResult.to_dict() must return a plain dict (JSON-serializable)."""
        mgr    = make_manager(api_key="")
        result = run(mgr.process("struggling with grief and loss"))
        d      = result.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("route",      d)
        self.assertIn("analysis",   d)
        self.assertIn("input_text", d)
        # Must be JSON-serializable
        json.dumps(d)


# ══════════════════════════════════════════════════════════════════════════════
# 8. Cache behavior
# ══════════════════════════════════════════════════════════════════════════════

class TestCacheBehavior(unittest.TestCase):

    def test_second_identical_call_is_cached(self):
        """Same text called twice → second result is cached=True, no extra HTTP call."""
        mgr  = make_manager()
        text = "looking for healing poetry about grief and loss today"

        with patch_llm(mgr, make_llm_response()) as mock_http:
            r1 = run(mgr.process(text))
            r2 = run(mgr.process(text))

        self.assertFalse(r1.cached)
        self.assertTrue(r2.cached)
        self.assertEqual(mock_http.call_count, 1)   # LLM only called once

    def test_different_texts_not_cached(self):
        """Different texts must each trigger a new LLM call."""
        mgr = make_manager()

        with patch_llm(mgr, make_llm_response()) as mock_http:
            run(mgr.process("healing poetry about grief"))
            run(mgr.process("identity and blackness in poetry"))

        self.assertEqual(mock_http.call_count, 2)

    def test_cache_is_case_and_whitespace_normalized(self):
        """'  GRIEF POETRY  ' and 'grief poetry' should hit same cache entry."""
        mgr = make_manager()

        with patch_llm(mgr, make_llm_response()) as mock_http:
            run(mgr.process("grief poetry about healing"))
            run(mgr.process("  GRIEF POETRY ABOUT HEALING  "))   # normalized → same key

        self.assertEqual(mock_http.call_count, 1)


# ══════════════════════════════════════════════════════════════════════════════
# 9. Batch processing
# ══════════════════════════════════════════════════════════════════════════════

class TestBatchProcessing(unittest.TestCase):

    def test_batch_returns_one_result_per_input(self):
        mgr   = make_manager()
        texts = [
            "looking for healing poetry about grief",
            "I been carrying this truth for years",
            "this hits different nobody talks about this",
        ]

        with patch_llm(mgr, make_llm_response()):
            results = run(mgr.process_batch(texts))

        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIsInstance(r, PipelineResult)

    def test_batch_with_empty_items_still_returns_results(self):
        mgr    = make_manager(api_key="")
        texts  = ["", "healing poetry", "   "]
        results = run(mgr.process_batch(texts))

        self.assertEqual(len(results), 3)
        # Empty/short items → neutral with error
        self.assertIsNotNone(results[0].error)


# ══════════════════════════════════════════════════════════════════════════════
# 10. IntentAnalysis dataclass structure
# ══════════════════════════════════════════════════════════════════════════════

class TestIntentAnalysisStructure(unittest.TestCase):

    def test_all_required_fields_present(self):
        """IntentAnalysis must have all required fields."""
        a = IntentAnalysis(
            theme="grief", intent="seeking", confidence=0.8,
            sentiment="negative", urgency="high", viral_potential=False,
        )
        self.assertTrue(hasattr(a, "theme"))
        self.assertTrue(hasattr(a, "intent"))
        self.assertTrue(hasattr(a, "confidence"))
        self.assertTrue(hasattr(a, "sentiment"))
        self.assertTrue(hasattr(a, "urgency"))
        self.assertTrue(hasattr(a, "viral_potential"))
        self.assertTrue(hasattr(a, "keywords"))
        self.assertTrue(hasattr(a, "analyzer"))
        self.assertTrue(hasattr(a, "raw_score"))
        self.assertTrue(hasattr(a, "error"))

    def test_keywords_defaults_to_empty_list(self):
        a = IntentAnalysis(
            theme="joy", intent="sharing", confidence=0.7,
            sentiment="positive", urgency="low", viral_potential=False,
        )
        self.assertEqual(a.keywords, [])

    def test_analyzer_defaults_to_llm(self):
        a = IntentAnalysis(
            theme="hope", intent="seeking", confidence=0.9,
            sentiment="positive", urgency="medium", viral_potential=False,
        )
        self.assertEqual(a.analyzer, "llm")

    def test_pipeline_result_to_dict_includes_analysis(self):
        a = IntentAnalysis(
            theme="grief", intent="seeking", confidence=0.8,
            sentiment="negative", urgency="high", viral_potential=False,
        )
        r = PipelineResult(input_text="test", analysis=a, route=ROUTE_OUTREACH)
        d = r.to_dict()
        self.assertIsInstance(d["analysis"], dict)
        self.assertEqual(d["analysis"]["theme"], "grief")


if __name__ == "__main__":
    unittest.main(verbosity=2)
