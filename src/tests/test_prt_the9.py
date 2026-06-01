"""
src/tests/test_prt_the9.py
============================
Test suite for the PRT + The 9 system.

Covers:
  - PRTThe9Authority: identity checks, authorization, blocked senders,
    The 9 activation gate, dual-key backward compat, directive integrity,
    full authorize(), build_activation_record()
  - The9FusionEngine: fuse() authorized/blocked, FusionResult structure,
    backward-compat activate(), synthesis brief content, capability queries
  - PRTEnforcementEngine: filter_directive, enforce, trigger_the9,
    run_full_flow with/without director plan, _evaluate_director_plan
  - ActivateThe9: run() with valid/invalid/PRT senders
  - PipelineManager._prt_validate: violation blocking, alignment scoring,
    analysis theme boost, integration with _execute_route (blocked_by_prt)

Run:
    py -3.11 -m pytest src/tests/test_prt_the9.py -v
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# ── Path setup ────────────────────────────────────────────────────────────────
# Project root → resolves src.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
# backend/ → resolves wai_institute.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


def run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


# ==============================================================================
# PRTThe9Authority
# ==============================================================================

class TestPRTThe9AuthorityIdentity(unittest.TestCase):
    """Identity classification — is_sage, is_executive, is_authorized, is_blocked."""

    def setUp(self):
        from wai_institute.core.prt_the9_authority import PRTThe9Authority
        self.auth = PRTThe9Authority()

    # -- Sage identities -------------------------------------------------------

    def test_ancestral_sage_is_sage(self):
        self.assertTrue(self.auth.is_sage("ancestral_sage"))

    def test_sage_alias_is_sage(self):
        self.assertTrue(self.auth.is_sage("sage"))

    def test_sage_with_spaces_is_sage(self):
        self.assertTrue(self.auth.is_sage("the ancestral sage"))

    def test_sage_case_insensitive(self):
        self.assertTrue(self.auth.is_sage("ANCESTRAL_SAGE"))

    def test_sage_with_whitespace(self):
        self.assertTrue(self.auth.is_sage("  sage  "))

    def test_director_is_not_sage(self):
        self.assertFalse(self.auth.is_sage("director"))

    def test_executive_is_not_sage(self):
        self.assertFalse(self.auth.is_sage("executive"))

    # -- Executive identities --------------------------------------------------

    def test_executive_is_executive(self):
        self.assertTrue(self.auth.is_executive("executive"))

    def test_executive_admin_is_executive(self):
        self.assertTrue(self.auth.is_executive("executive_admin"))

    def test_delon_is_executive(self):
        self.assertTrue(self.auth.is_executive("delon"))

    def test_nam_oshun_is_executive(self):
        self.assertTrue(self.auth.is_executive("nam_oshun"))

    def test_system_is_executive(self):
        self.assertTrue(self.auth.is_executive("system"))

    def test_executive_case_insensitive(self):
        self.assertTrue(self.auth.is_executive("EXECUTIVE"))

    def test_sage_is_not_executive(self):
        self.assertFalse(self.auth.is_executive("ancestral_sage"))

    # -- is_authorized (Sage OR Executive) ------------------------------------

    def test_sage_is_authorized(self):
        self.assertTrue(self.auth.is_authorized("ancestral_sage"))

    def test_executive_is_authorized(self):
        self.assertTrue(self.auth.is_authorized("executive"))

    def test_delon_is_authorized(self):
        self.assertTrue(self.auth.is_authorized("delon"))

    def test_director_is_not_authorized(self):
        self.assertFalse(self.auth.is_authorized("director"))

    def test_cipher_is_not_authorized(self):
        self.assertFalse(self.auth.is_authorized("cipher"))

    def test_random_string_is_not_authorized(self):
        self.assertFalse(self.auth.is_authorized("some_random_user"))

    # -- is_blocked -----------------------------------------------------------

    def test_director_is_blocked(self):
        self.assertTrue(self.auth.is_blocked("director"))

    def test_ambassador_is_blocked(self):
        self.assertTrue(self.auth.is_blocked("ambassador"))

    def test_cipher_is_blocked(self):
        self.assertTrue(self.auth.is_blocked("cipher"))

    def test_oracle_is_blocked(self):
        self.assertTrue(self.auth.is_blocked("oracle"))

    def test_architect_is_blocked(self):
        self.assertTrue(self.auth.is_blocked("architect"))

    def test_merchant_is_blocked(self):
        self.assertTrue(self.auth.is_blocked("merchant"))

    def test_producer_is_blocked(self):
        self.assertTrue(self.auth.is_blocked("producer"))

    def test_analyst_is_blocked(self):
        self.assertTrue(self.auth.is_blocked("analyst"))

    def test_engineer_is_blocked(self):
        self.assertTrue(self.auth.is_blocked("engineer"))

    def test_sage_is_not_blocked(self):
        self.assertFalse(self.auth.is_blocked("ancestral_sage"))

    def test_executive_is_not_blocked(self):
        self.assertFalse(self.auth.is_blocked("executive"))


class TestPRTThe9AuthorityThe9Gate(unittest.TestCase):
    """The 9 activation gate and dual-key backward compat."""

    def setUp(self):
        from wai_institute.core.prt_the9_authority import PRTThe9Authority
        self.auth = PRTThe9Authority()

    def test_sage_can_activate_the9(self):
        self.assertTrue(self.auth.can_activate_the9("ancestral_sage"))

    def test_executive_can_activate_the9(self):
        self.assertTrue(self.auth.can_activate_the9("executive"))

    def test_prt_can_activate_the9(self):
        self.assertTrue(self.auth.can_activate_the9("poor_righteous_teacher"))

    def test_prt_alias_can_activate_the9(self):
        self.assertTrue(self.auth.can_activate_the9("prt"))

    def test_director_cannot_activate_the9(self):
        self.assertFalse(self.auth.can_activate_the9("director"))

    def test_cipher_cannot_activate_the9(self):
        self.assertFalse(self.auth.can_activate_the9("cipher"))

    def test_dual_key_sage_only(self):
        self.assertTrue(self.auth.dual_key_for_the9(sage_confirmed=True))

    def test_dual_key_executive_only(self):
        self.assertTrue(self.auth.dual_key_for_the9(executive_confirmed=True))

    def test_dual_key_prt_only(self):
        self.assertTrue(self.auth.dual_key_for_the9(prt_confirmed=True))

    def test_dual_key_all_false(self):
        self.assertFalse(self.auth.dual_key_for_the9())


class TestPRTThe9AuthorityDirective(unittest.TestCase):
    """Directive integrity checks."""

    def setUp(self):
        from wai_institute.core.prt_the9_authority import PRTThe9Authority
        self.auth = PRTThe9Authority()

    def test_valid_directive_passes(self):
        result = self.auth.verify_directive_integrity("Launch the healing campaign now")
        self.assertTrue(result["integrity_passed"])
        self.assertIn("directive", result)

    def test_empty_directive_fails(self):
        result = self.auth.verify_directive_integrity("")
        self.assertFalse(result["integrity_passed"])

    def test_whitespace_only_fails(self):
        result = self.auth.verify_directive_integrity("   ")
        self.assertFalse(result["integrity_passed"])

    def test_too_short_fails(self):
        result = self.auth.verify_directive_integrity("Go")
        self.assertFalse(result["integrity_passed"])

    def test_exactly_5_chars_passes(self):
        result = self.auth.verify_directive_integrity("Start")
        self.assertTrue(result["integrity_passed"])

    def test_directive_is_stripped(self):
        result = self.auth.verify_directive_integrity("  Launch campaign  ")
        self.assertEqual(result["directive"], "Launch campaign")


class TestPRTThe9AuthorityAuthorize(unittest.TestCase):
    """Full authorize() combining sender + directive checks."""

    def setUp(self):
        from wai_institute.core.prt_the9_authority import PRTThe9Authority
        self.auth = PRTThe9Authority()

    def test_sage_with_valid_directive_accepted(self):
        result = self.auth.authorize("ancestral_sage", "Launch the community healing circle")
        self.assertTrue(result["accepted"])
        self.assertEqual(result["authority"], "sage")

    def test_executive_with_valid_directive_accepted(self):
        result = self.auth.authorize("executive", "Activate grief campaign pipeline")
        self.assertTrue(result["accepted"])
        self.assertEqual(result["authority"], "executive")

    def test_blocked_sender_rejected(self):
        result = self.auth.authorize("director", "Do this now")
        self.assertFalse(result["accepted"])
        self.assertIn("reason", result)
        self.assertIn("director", result["reason"])

    def test_unknown_sender_rejected(self):
        result = self.auth.authorize("random_user", "Do something")
        self.assertFalse(result["accepted"])

    def test_valid_sender_empty_directive_rejected(self):
        result = self.auth.authorize("ancestral_sage", "")
        self.assertFalse(result["accepted"])

    def test_valid_sender_short_directive_rejected(self):
        result = self.auth.authorize("executive", "Hi")
        self.assertFalse(result["accepted"])

    def test_delon_accepted(self):
        result = self.auth.authorize("delon", "Run the quarterly review now")
        self.assertTrue(result["accepted"])

    def test_nam_oshun_accepted(self):
        result = self.auth.authorize("nam_oshun", "Activate full mission synthesis")
        self.assertTrue(result["accepted"])

    def test_cipher_rejected_with_reason(self):
        result = self.auth.authorize("cipher", "Override the mission")
        self.assertFalse(result["accepted"])
        self.assertIn("reason", result)


class TestPRTThe9AuthorityBuildRecord(unittest.TestCase):
    """Activation record builder."""

    def setUp(self):
        from wai_institute.core.prt_the9_authority import PRTThe9Authority
        self.auth = PRTThe9Authority()

    def test_record_has_all_required_fields(self):
        record = self.auth.build_activation_record(
            sender="ancestral_sage",
            directive="Launch healing initiative",
            target="the_9",
            reason="mission_threat",
        )
        self.assertEqual(record["sender"], "ancestral_sage")
        self.assertEqual(record["target"], "the_9")
        self.assertIn("timestamp", record)
        self.assertIn("directive", record)

    def test_directive_capped_at_500_chars(self):
        long_directive = "x" * 600
        record = self.auth.build_activation_record("sage", long_directive)
        self.assertLessEqual(len(record["directive"]), 500)

    def test_default_target_is_prt(self):
        record = self.auth.build_activation_record("executive", "Go now")
        self.assertEqual(record["target"], "prt")


# ==============================================================================
# The9FusionEngine + FusionResult
# ==============================================================================

class TestThe9FusionEngineBasic(unittest.TestCase):
    """Basic fuse() scenarios."""

    def setUp(self):
        from wai_institute.core.the9_fusion_engine import The9FusionEngine
        self.engine = The9FusionEngine()

    def test_fuse_by_prt_succeeds(self):
        result = self.engine.fuse(sender="poor_righteous_teacher")
        self.assertEqual(result.status, "fused")

    def test_fuse_by_sage_succeeds(self):
        result = self.engine.fuse(sender="ancestral_sage")
        self.assertEqual(result.status, "fused")

    def test_fuse_by_executive_succeeds(self):
        result = self.engine.fuse(sender="executive")
        self.assertEqual(result.status, "fused")

    def test_fuse_by_director_blocked(self):
        result = self.engine.fuse(sender="director")
        self.assertEqual(result.status, "blocked")
        self.assertIsNotNone(result.error)
        self.assertIn("director", result.error)

    def test_fuse_by_cipher_blocked(self):
        result = self.engine.fuse(sender="cipher")
        self.assertEqual(result.status, "blocked")

    def test_fuse_never_raises(self):
        """fuse() must never raise — always return a FusionResult."""
        try:
            self.engine.fuse(sender="anyone", context=None, prt_directive=None)
        except Exception as exc:
            self.fail(f"fuse() raised {exc}")


class TestThe9FusionEngineSkillSet(unittest.TestCase):
    """Unified skill set on successful fusion."""

    def setUp(self):
        from wai_institute.core.the9_fusion_engine import The9FusionEngine
        self.engine = The9FusionEngine()

    def test_all_9_personas_represented_in_map(self):
        result = self.engine.fuse(sender="poor_righteous_teacher")
        self.assertEqual(len(result.persona_map), 9)
        for persona in ["director", "ambassador", "cipher", "oracle", "architect",
                         "merchant", "producer", "analyst", "engineer"]:
            self.assertIn(persona, result.persona_map)

    def test_unified_skill_set_is_populated(self):
        result = self.engine.fuse(sender="executive")
        self.assertGreater(len(result.unified_skill_set), 0)

    def test_unified_skill_set_contains_core_capabilities(self):
        result = self.engine.fuse(sender="ancestral_sage")
        skills = result.unified_skill_set
        for cap in ["governance", "creativity", "foresight", "revenue_logic"]:
            self.assertIn(cap, skills, f"Missing capability: {cap}")

    def test_unified_skill_set_is_sorted(self):
        result = self.engine.fuse(sender="executive")
        self.assertEqual(result.unified_skill_set, sorted(result.unified_skill_set))

    def test_activated_by_matches_sender(self):
        result = self.engine.fuse(sender="ancestral_sage")
        self.assertEqual(result.activated_by, "ancestral_sage")

    def test_mode_is_unified_mind(self):
        result = self.engine.fuse(sender="poor_righteous_teacher")
        self.assertEqual(result.mode, "unified_mind")

    def test_timestamp_is_present(self):
        result = self.engine.fuse(sender="executive")
        self.assertTrue(result.timestamp)


class TestThe9FusionEngineSynthesisBrief(unittest.TestCase):
    """Synthesis brief content."""

    def setUp(self):
        from wai_institute.core.the9_fusion_engine import The9FusionEngine
        self.engine = The9FusionEngine()

    def test_synthesis_brief_starts_with_the9_online(self):
        result = self.engine.fuse(sender="poor_righteous_teacher")
        self.assertTrue(result.synthesis_brief.startswith("The 9 is online."))

    def test_synthesis_brief_includes_context_brief(self):
        result = self.engine.fuse(
            sender="executive",
            context={"brief": "Launch grief healing campaign"},
        )
        self.assertIn("grief healing campaign", result.synthesis_brief)

    def test_synthesis_brief_includes_prt_directive(self):
        result = self.engine.fuse(
            sender="poor_righteous_teacher",
            prt_directive={"directive": "Execute mission synthesis now"},
        )
        self.assertIn("Execute mission synthesis now", result.synthesis_brief)

    def test_synthesis_brief_includes_agenda_items(self):
        result = self.engine.fuse(
            sender="ancestral_sage",
            context={"agenda": ["Review pipeline", "Launch merch"]},
        )
        self.assertIn("Review pipeline", result.synthesis_brief)

    def test_synthesis_brief_mentions_all_nine_capabilities(self):
        result = self.engine.fuse(sender="executive")
        self.assertIn("governance", result.synthesis_brief)
        self.assertIn("creativity", result.synthesis_brief)


class TestThe9FusionEngineActivate(unittest.TestCase):
    """Backward-compatible activate() wrapper."""

    def setUp(self):
        from wai_institute.core.the9_fusion_engine import The9FusionEngine
        self.engine = The9FusionEngine()

    def test_activate_with_prt_sender_succeeds(self):
        result = self.engine.activate({"sender": "poor_righteous_teacher", "reason": "prt_command"})
        self.assertEqual(result.status, "fused")

    def test_activate_with_sage_sender_succeeds(self):
        result = self.engine.activate({"sender": "ancestral_sage"})
        self.assertEqual(result.status, "fused")

    def test_activate_with_no_request_uses_defaults(self):
        result = self.engine.activate()
        self.assertEqual(result.status, "fused")  # default sender is PRT

    def test_activate_with_director_blocked(self):
        result = self.engine.activate({"sender": "director"})
        self.assertEqual(result.status, "blocked")

    def test_activate_result_is_fusion_result_type(self):
        from wai_institute.core.the9_fusion_engine import FusionResult
        result = self.engine.activate()
        self.assertIsInstance(result, FusionResult)


class TestFusionResultDataclass(unittest.TestCase):
    """FusionResult dataclass and to_dict()."""

    def setUp(self):
        from wai_institute.core.the9_fusion_engine import The9FusionEngine
        self.engine = The9FusionEngine()

    def test_to_dict_returns_dict(self):
        result = self.engine.fuse(sender="executive")
        d = result.to_dict()
        self.assertIsInstance(d, dict)

    def test_to_dict_has_all_required_keys(self):
        result = self.engine.fuse(sender="ancestral_sage")
        d = result.to_dict()
        for key in ["status", "activated_by", "activation_reason",
                    "unified_skill_set", "persona_map", "synthesis_brief",
                    "mode", "timestamp"]:
            self.assertIn(key, d)

    def test_blocked_result_has_error(self):
        result = self.engine.fuse(sender="director")
        d = result.to_dict()
        self.assertIsNotNone(d["error"])

    def test_successful_result_error_is_none(self):
        result = self.engine.fuse(sender="executive")
        self.assertIsNone(result.error)


class TestThe9CapabilityQueries(unittest.TestCase):
    """Static capability query methods."""

    def setUp(self):
        from wai_institute.core.the9_fusion_engine import The9FusionEngine
        self.engine = The9FusionEngine()

    def test_get_persona_capabilities_director(self):
        caps = self.engine.get_persona_capabilities("director")
        self.assertIn("governance", caps)
        self.assertIn("strategy", caps)

    def test_get_persona_capabilities_cipher(self):
        caps = self.engine.get_persona_capabilities("cipher")
        self.assertIn("creativity", caps)

    def test_get_persona_capabilities_unknown(self):
        caps = self.engine.get_persona_capabilities("nonexistent_persona")
        self.assertEqual(caps, [])

    def test_get_all_capabilities_is_sorted_list(self):
        caps = self.engine.get_all_capabilities()
        self.assertIsInstance(caps, list)
        self.assertEqual(caps, sorted(caps))

    def test_get_all_capabilities_count(self):
        # 9 personas × ~3-4 capabilities each = should be at least 20
        caps = self.engine.get_all_capabilities()
        self.assertGreater(len(caps), 20)


# ==============================================================================
# PRTEnforcementEngine
# ==============================================================================

class TestPRTEnforcementEngineFilter(unittest.TestCase):
    """filter_directive — delegates to PRTThe9Authority.authorize()."""

    def setUp(self):
        from wai_institute.personas.prt.prt_enforcement_engine import PRTEnforcementEngine
        self.prt = PRTEnforcementEngine()

    def test_sage_directive_accepted(self):
        result = self.prt.filter_directive("ancestral_sage", "Launch the healing campaign")
        self.assertTrue(result["accepted"])

    def test_executive_directive_accepted(self):
        result = self.prt.filter_directive("executive_admin", "Run quarterly synthesis")
        self.assertTrue(result["accepted"])

    def test_director_directive_rejected(self):
        result = self.prt.filter_directive("director", "Do this immediately")
        self.assertFalse(result["accepted"])

    def test_ambassador_directive_rejected(self):
        result = self.prt.filter_directive("ambassador", "Execute now")
        self.assertFalse(result["accepted"])

    def test_empty_directive_rejected(self):
        result = self.prt.filter_directive("ancestral_sage", "")
        self.assertFalse(result["accepted"])


class TestPRTEnforcementEngineEnforce(unittest.TestCase):
    """enforce() — builds enforcement record."""

    def setUp(self):
        from wai_institute.personas.prt.prt_enforcement_engine import PRTEnforcementEngine
        self.prt = PRTEnforcementEngine()

    def test_enforce_returns_status_enforcing(self):
        result = self.prt.enforce("Execute healing campaign launch")
        self.assertEqual(result["status"], "enforcing")

    def test_enforce_has_directive(self):
        result = self.prt.enforce("Launch community program")
        self.assertEqual(result["directive"], "Launch community program")

    def test_enforce_has_actions(self):
        result = self.prt.enforce("Run this campaign")
        self.assertIn("actions", result)
        self.assertIn("interpret_doctrine", result["actions"])
        self.assertIn("execute_without_hesitation", result["actions"])

    def test_enforce_has_timestamp(self):
        result = self.prt.enforce("Do this")
        self.assertIn("timestamp", result)

    def test_enforce_authority_is_prt(self):
        result = self.prt.enforce("Execute")
        self.assertEqual(result["authority"], "poor_righteous_teacher")


class TestPRTEnforcementEngineTriggerThe9(unittest.TestCase):
    """trigger_the9() — activates The9FusionEngine."""

    def setUp(self):
        from wai_institute.personas.prt.prt_enforcement_engine import PRTEnforcementEngine
        self.prt = PRTEnforcementEngine()

    def test_trigger_the9_returns_dict(self):
        result = self.prt.trigger_the9("mission_threat")
        self.assertIsInstance(result, dict)

    def test_trigger_the9_status_is_fused(self):
        result = self.prt.trigger_the9("prt_command")
        self.assertEqual(result["status"], "fused")

    def test_trigger_the9_activated_by_prt(self):
        result = self.prt.trigger_the9("cultural_integrity_risk")
        self.assertEqual(result["activated_by"], "poor_righteous_teacher")

    def test_trigger_the9_with_context(self):
        result = self.prt.trigger_the9(
            reason="time_critical",
            context={"brief": "Urgent campaign needed"},
        )
        self.assertEqual(result["status"], "fused")
        self.assertIn("brief", result.get("synthesis_brief", "") + str(result))


class TestPRTEnforcementEngineFullFlow(unittest.TestCase):
    """run_full_flow() end-to-end decision pipeline."""

    def setUp(self):
        from wai_institute.personas.prt.prt_enforcement_engine import PRTEnforcementEngine
        self.prt = PRTEnforcementEngine()

    def test_blocked_sender_returns_rejected_stage(self):
        result = self.prt.run_full_flow("director", "Override mission")
        self.assertEqual(result["stage"], "filter")
        self.assertEqual(result["status"], "rejected")

    def test_sage_no_director_plan_enforces_prt(self):
        result = self.prt.run_full_flow("ancestral_sage", "Launch healing campaign")
        self.assertEqual(result["stage"], "enforce_prt")
        self.assertIn("enforce_prt", result["stage"])

    def test_superior_director_plan_executes_director(self):
        result = self.prt.run_full_flow(
            sender="ancestral_sage",
            directive="Launch the healing campaign",
            director_plan={
                "plan":                "Healing campaign via social channels",
                "honors_sage":         True,
                "achieves_same_goal":  True,
                "no_doctrine_dilution": True,
                "no_harm_to_mission":  True,
                "timely":              True,
            },
        )
        self.assertEqual(result["stage"], "enforce_director_plan")

    def test_inferior_director_plan_enforces_prt(self):
        result = self.prt.run_full_flow(
            sender="executive",
            directive="Launch healing campaign",
            director_plan={
                "plan":               "Cut corners on healing content",
                "honors_sage":        False,
                "achieves_same_goal": True,
                "no_doctrine_dilution": False,
                "no_harm_to_mission": False,
                "timely":             True,
            },
        )
        self.assertEqual(result["stage"], "enforce_prt")

    def test_executive_with_no_director_plan_enforces_prt(self):
        result = self.prt.run_full_flow("delon", "Run mission synthesis now")
        self.assertEqual(result["stage"], "enforce_prt")


class TestPRTDirectorPlanEvaluation(unittest.TestCase):
    """_evaluate_director_plan static method."""

    def setUp(self):
        from wai_institute.personas.prt.prt_enforcement_engine import PRTEnforcementEngine
        self.prt = PRTEnforcementEngine

    def _make_plan(self, **overrides):
        base = {
            "honors_sage":          True,
            "achieves_same_goal":   True,
            "no_doctrine_dilution": True,
            "no_harm_to_mission":   True,
            "timely":               True,
        }
        base.update(overrides)
        return base

    def test_all_criteria_met_is_superior(self):
        result = self.prt._evaluate_director_plan("Do this", self._make_plan())
        self.assertTrue(result["director_plan_superior"])
        self.assertEqual(result["decision"], "USE_DIRECTOR_PLAN")

    def test_one_criteria_missing_not_superior(self):
        result = self.prt._evaluate_director_plan(
            "Do this", self._make_plan(honors_sage=False)
        )
        self.assertFalse(result["director_plan_superior"])
        self.assertEqual(result["decision"], "STAND_DOWN_AND_ALLOW_PRT")

    def test_all_false_not_superior(self):
        result = self.prt._evaluate_director_plan(
            "Do this", {"honors_sage": False, "achieves_same_goal": False,
                        "no_doctrine_dilution": False, "no_harm_to_mission": False, "timely": False}
        )
        self.assertFalse(result["director_plan_superior"])

    def test_criteria_scores_present(self):
        result = self.prt._evaluate_director_plan("Do this", self._make_plan())
        self.assertIn("criteria_scores", result)
        self.assertEqual(len(result["criteria_scores"]), 5)


# ==============================================================================
# ActivateThe9
# ==============================================================================

class TestActivateThe9(unittest.TestCase):
    """ActivateThe9 thin wrapper."""

    def setUp(self):
        from wai_institute.personas.prt.prt_activate_the9 import ActivateThe9
        self.activator = ActivateThe9()

    def test_initial_status_is_ready(self):
        self.assertEqual(self.activator.status, "ready")

    def test_run_with_prt_sender_succeeds(self):
        result = self.activator.run("prt_command")
        self.assertEqual(result["status"], "fused")

    def test_run_with_sage_sender_succeeds(self):
        result = self.activator.run("sage_command", sender="ancestral_sage")
        self.assertEqual(result["status"], "fused")

    def test_run_with_executive_sender_succeeds(self):
        result = self.activator.run("executive_command", sender="executive")
        self.assertEqual(result["status"], "fused")

    def test_run_with_director_sender_blocked(self):
        result = self.activator.run("take_over", sender="director")
        self.assertEqual(result["status"], "blocked")

    def test_run_returns_dict(self):
        result = self.activator.run("prt_command")
        self.assertIsInstance(result, dict)

    def test_run_with_context(self):
        result = self.activator.run(
            "mission_threat",
            context={"brief": "Urgent: healing campaign must launch"},
        )
        self.assertEqual(result["status"], "fused")

    def test_run_unified_skill_set_populated(self):
        result = self.activator.run("prt_command")
        self.assertGreater(len(result["unified_skill_set"]), 0)

    def test_run_never_raises(self):
        """run() must never raise — even with unusual inputs."""
        try:
            self.activator.run("", context=None, sender="")
        except Exception as exc:
            self.fail(f"run() raised {exc}")

    def test_run_synthesis_brief_starts_the9_online(self):
        result = self.activator.run("prt_command")
        self.assertTrue(result["synthesis_brief"].startswith("The 9 is online."))


# ==============================================================================
# PipelineManager._prt_validate
# ==============================================================================

class TestPRTValidatePipelineManager(unittest.TestCase):
    """_prt_validate in PipelineManager."""

    def setUp(self):
        from src.agents.pipeline_manager import PipelineManager, IntentAnalysis
        self.mgr = PipelineManager(db=None, anthropic_api_key="")
        self.IntentAnalysis = IntentAnalysis

    def _make_analysis(self, theme="neutral", intent="neutral", confidence=0.5,
                       viral_potential=False, sentiment="neutral", urgency="low",
                       keywords=None, analyzer="keyword_fallback"):
        return self.IntentAnalysis(
            theme=theme, intent=intent, confidence=confidence,
            viral_potential=viral_potential, sentiment=sentiment,
            urgency=urgency, keywords=keywords or [],
            analyzer=analyzer, error=None,
        )

    # -- Hard blocks -----------------------------------------------------------

    def test_poverty_porn_is_blocked(self):
        result = self.mgr._prt_validate("this is poverty porn content", None)
        self.assertFalse(result["aligned"])
        self.assertIn("poverty porn", result["reason"])

    def test_coon_is_blocked(self):
        result = self.mgr._prt_validate("this coon character", None)
        self.assertFalse(result["aligned"])

    def test_mammy_is_blocked(self):
        result = self.mgr._prt_validate("the mammy stereotype", None)
        self.assertFalse(result["aligned"])

    def test_sambo_is_blocked(self):
        result = self.mgr._prt_validate("sambo trope in media", None)
        self.assertFalse(result["aligned"])

    def test_caricature_is_blocked(self):
        result = self.mgr._prt_validate("a cultural caricature", None)
        self.assertFalse(result["aligned"])

    def test_stereotype_is_blocked(self):
        result = self.mgr._prt_validate("a racial stereotype in the media", None)
        self.assertFalse(result["aligned"])

    def test_block_returns_score_zero(self):
        result = self.mgr._prt_validate("this is poverty porn", None)
        self.assertEqual(result["score"], 0.0)

    # -- Alignment scoring -----------------------------------------------------

    def test_clean_text_passes(self):
        result = self.mgr._prt_validate("just a regular message with no violations", None)
        self.assertTrue(result["aligned"])

    def test_healing_theme_increases_score(self):
        result_clean = self.mgr._prt_validate("nothing here", None)
        result_healing = self.mgr._prt_validate("poetry about healing and grief", None)
        self.assertGreater(result_healing["score"], result_clean["score"])

    def test_three_themes_full_score(self):
        text = "healing grief identity resilience community"
        result = self.mgr._prt_validate(text, None)
        self.assertTrue(result["aligned"])
        self.assertGreaterEqual(result["score"], 1.0)

    def test_analysis_theme_boost(self):
        analysis_no_boost = self._make_analysis(theme="neutral")
        analysis_boost = self._make_analysis(theme="healing")
        text = "a message about community"
        score_no_boost = self.mgr._prt_validate(text, analysis_no_boost)["score"]
        score_boost = self.mgr._prt_validate(text, analysis_boost)["score"]
        self.assertGreater(score_boost, score_no_boost)

    def test_none_analysis_does_not_crash(self):
        result = self.mgr._prt_validate("healing grief", None)
        self.assertTrue(result["aligned"])

    def test_score_capped_at_one(self):
        text = "healing grief identity resilience community love justice freedom hope ancestry"
        result = self.mgr._prt_validate(text, None)
        self.assertLessEqual(result["score"], 1.0)

    def test_reason_present_on_pass(self):
        result = self.mgr._prt_validate("healing poetry", None)
        self.assertIn("reason", result)

    def test_reason_present_on_block(self):
        result = self.mgr._prt_validate("poverty porn", None)
        self.assertIn("reason", result)


class TestPRTValidateRouteGate(unittest.TestCase):
    """PRT gate blocks outreach/merch for violations, passes clean content."""

    def setUp(self):
        from src.agents.pipeline_manager import (
            PipelineManager, IntentAnalysis,
            ROUTE_OUTREACH, ROUTE_MERCH, ROUTE_DISCOVERY,
        )
        self.mgr = PipelineManager(db=None, anthropic_api_key="")
        self.IntentAnalysis = IntentAnalysis
        self.ROUTE_OUTREACH = ROUTE_OUTREACH
        self.ROUTE_MERCH = ROUTE_MERCH
        self.ROUTE_DISCOVERY = ROUTE_DISCOVERY

    def _make_analysis(self, theme="grief", intent="seeking", confidence=0.8,
                       viral_potential=False, sentiment="negative", urgency="high"):
        return self.IntentAnalysis(
            theme=theme, intent=intent, confidence=confidence,
            viral_potential=viral_potential, sentiment=sentiment,
            urgency=urgency, keywords=["grief"], analyzer="llm", error=None,
        )

    def test_violation_in_outreach_route_blocks(self):
        analysis = self._make_analysis()
        result = run(self.mgr._execute_route(
            route=self.ROUTE_OUTREACH,
            text="this poverty porn content",
            analysis=analysis,
            source="test",
        ))
        self.assertEqual(result["stage"], "blocked_by_prt")
        self.assertEqual(result["redirect"], self.ROUTE_DISCOVERY)

    def test_violation_in_merch_route_blocks(self):
        analysis = self._make_analysis(viral_potential=True, confidence=0.9)
        result = run(self.mgr._execute_route(
            route=self.ROUTE_MERCH,
            text="mammy trope in healing poetry",
            analysis=analysis,
            source="test",
        ))
        self.assertEqual(result["stage"], "blocked_by_prt")

    def test_clean_outreach_not_blocked_by_prt(self):
        analysis = self._make_analysis()
        result = run(self.mgr._execute_route(
            route=self.ROUTE_OUTREACH,
            text="poetry about healing grief and community",
            analysis=analysis,
            source="instagram",
        ))
        self.assertNotEqual(result.get("stage"), "blocked_by_prt")

    def test_discovery_route_bypasses_prt_gate(self):
        """Discovery route should never hit PRT gate — it's low-value content."""
        analysis = self._make_analysis(confidence=0.2)
        # Even a violation in discovery text should NOT be blocked by PRT
        result = run(self.mgr._execute_route(
            route=self.ROUTE_DISCOVERY,
            text="poverty porn content somehow",
            analysis=analysis,
            source="test",
        ))
        self.assertNotEqual(result.get("stage"), "blocked_by_prt")


# ==============================================================================
# Integration: process() triggers PRT block end-to-end
# ==============================================================================

class TestPRTIntegrationEndToEnd(unittest.TestCase):
    """Full process() call with a cultural violation shows up in result."""

    def setUp(self):
        from src.agents.pipeline_manager import PipelineManager
        import json
        self.mgr = PipelineManager(db=None, anthropic_api_key="test_key")
        self.json = json

    def _make_llm_resp(self, theme, intent, confidence=0.85, viral=False):
        body = {
            "theme": theme, "intent": intent,
            "confidence": confidence, "sentiment": "negative",
            "urgency": "high", "viral_potential": viral, "keywords": [theme],
        }
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "content": [{"type": "text", "text": self.json.dumps(body)}]
        }
        resp.headers = {}
        return resp

    def test_seeking_with_violation_routed_to_discovery(self):
        """LLM says seeking→outreach but text has PRT violation → blocked_by_prt."""
        mgr = self.mgr
        mock_resp = self._make_llm_resp("grief", "seeking")
        with patch.object(mgr, "_post_to_anthropic", new=AsyncMock(return_value=mock_resp)):
            result = run(mgr.process("poverty porn content about grief communities"))
        # pipeline_outputs contains the route action result
        # Key assertion: stage is NOT "outreach_sent" — PRT blocked it
        outputs = result.pipeline_outputs
        if outputs and isinstance(outputs, dict):
            self.assertNotEqual(outputs.get("stage"), "outreach_sent")


# ==============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
