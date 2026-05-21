"""
Tests for wai_institute core — PersonaManager, PersonaRegistry, HierarchyEnforcer.
Run with: pytest backend/tests/test_wai_core.py -v
All tests use mock DB — no live MongoDB needed.
"""
import asyncio
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import AsyncMock, MagicMock, patch


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_mock_db():
    """Build a minimal mock MongoDB object."""
    db = MagicMock()
    # Every collection access returns an async-capable mock
    for col in [
        "persona_activations", "persona_tts_budgets", "governance_log"
    ]:
        c = MagicMock()
        c.find_one = AsyncMock(return_value=None)
        c.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test"))
        c.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        c.replace_one = AsyncMock(return_value=MagicMock(modified_count=1))
        cursor = MagicMock()
        cursor.__aiter__ = MagicMock(return_value=iter([]))
        c.find = MagicMock(return_value=cursor)
        setattr(db, col, c)
    return db


# ═══════════════════════════════════════════════════════════════════════════════
# PersonaManager tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPersonaManager:

    @pytest.mark.asyncio
    async def test_activate_new_persona(self):
        from wai_institute.core.persona_manager import PersonaManager
        db = make_mock_db()
        pm = PersonaManager(db)

        result = await pm.activate("cipher", config={"test": True}, activated_by="director")

        assert result["status"] == "activated"
        assert result["persona"] == "cipher"
        db.persona_activations.find_one.assert_awaited_once()
        db.persona_activations.insert_one.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_activate_existing_persona_updates(self):
        from wai_institute.core.persona_manager import PersonaManager
        db = make_mock_db()
        # Simulate persona already exists
        db.persona_activations.find_one = AsyncMock(return_value={"persona": "cipher", "status": "inactive"})
        pm = PersonaManager(db)

        result = await pm.activate("cipher")

        assert result["status"] == "activated"
        db.persona_activations.update_one.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_deactivate_persona(self):
        from wai_institute.core.persona_manager import PersonaManager
        db = make_mock_db()
        pm = PersonaManager(db)

        result = await pm.deactivate("oracle", reason="test deactivation")

        assert result["status"] == "deactivated"
        assert result["persona"] == "oracle"
        assert result["reason"] == "test deactivation"

    @pytest.mark.asyncio
    async def test_evolve_adds_capabilities(self):
        from wai_institute.core.persona_manager import PersonaManager
        db = make_mock_db()
        pm = PersonaManager(db)

        result = await pm.evolve(
            "cipher",
            add_capabilities=["shopify_publish", "printify_merch"],
            evolved_by="director",
        )

        assert result["status"] == "evolved"
        assert "shopify_publish" in result["added"]
        assert "printify_merch" in result["added"]

    @pytest.mark.asyncio
    async def test_clone_persona(self):
        from wai_institute.core.persona_manager import PersonaManager
        db = make_mock_db()
        db.persona_activations.find_one = AsyncMock(return_value={
            "persona": "cipher",
            "config": {"capabilities": ["spoken_word"]},
            "scope": ["revenue"],
        })
        pm = PersonaManager(db)

        result = await pm.clone("cipher", "cipher_2", overrides={"extra": True})

        assert result["status"] == "cloned"
        assert result["source"] == "cipher"
        assert result["new_persona"] == "cipher_2"

    @pytest.mark.asyncio
    async def test_merge_personas(self):
        from wai_institute.core.persona_manager import PersonaManager
        db = make_mock_db()
        db.persona_activations.find_one = AsyncMock(side_effect=[
            {"persona": "cipher", "config": {"capabilities": ["A", "B"], "memory_policy": {"semantic": True, "episodic": True}}, "scope": ["revenue"]},
            {"persona": "oracle", "config": {"capabilities": ["B", "C"], "memory_policy": {"semantic": True, "episodic": False}}, "scope": ["intelligence"]},
        ])
        pm = PersonaManager(db)

        result = await pm.merge("cipher", "oracle", "cipher_oracle")

        assert result["status"] == "merged"
        assert result["capabilities_count"] == 3  # union of A, B, C

    @pytest.mark.asyncio
    async def test_no_db_does_not_crash(self):
        """PersonaManager must work gracefully without DB (e.g. tests)."""
        from wai_institute.core.persona_manager import PersonaManager
        pm = PersonaManager(db=None)

        result = await pm.activate("cipher")
        assert result["status"] == "activated"

        result2 = await pm.status("cipher")
        assert result2["status"] == "not_found"


# ═══════════════════════════════════════════════════════════════════════════════
# PersonaRegistry tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPersonaRegistry:

    def test_get_registry_returns_all_personas(self):
        from wai_institute.core.persona_registry import get_registry
        reg = get_registry()
        assert "personas" in reg
        assert len(reg["personas"]) == 7
        for name in ["director", "cipher", "oracle", "ambassador", "architect", "revenue_director", "ancestral_sage"]:
            assert name in reg["personas"]

    def test_get_persona_config_returns_correct_tier(self):
        from wai_institute.core.persona_registry import get_persona_config
        cfg = get_persona_config("cipher")
        assert cfg["tier"] == 4
        assert cfg["reports_to"] == "ambassador"

    def test_get_persona_config_director_has_no_reports_to(self):
        from wai_institute.core.persona_registry import get_persona_config
        cfg = get_persona_config("director")
        assert cfg["reports_to"] is None

    def test_get_persona_config_unknown_returns_empty(self):
        from wai_institute.core.persona_registry import get_persona_config
        cfg = get_persona_config("nonexistent_persona")
        assert cfg == {}

    def test_list_templates_returns_list(self):
        from wai_institute.core.persona_registry import list_templates
        templates = list_templates()
        assert isinstance(templates, list)
        # May be empty if template files not yet created — that's OK


# ═══════════════════════════════════════════════════════════════════════════════
# HierarchyEnforcer tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestHierarchyEnforcer:

    @pytest.mark.asyncio
    async def test_director_required_actions_are_blocked(self):
        from wai_institute.core.hierarchy_enforcer import HierarchyEnforcer
        enforcer = HierarchyEnforcer(db=None)

        for action in ["system_changes", "persona_creation", "merge_personas"]:
            result = await enforcer.check_action("ambassador", action)
            assert result["approved"] is False
            assert result["approver"] == "director_required"

    @pytest.mark.asyncio
    async def test_high_value_publish_requires_director(self):
        from wai_institute.core.hierarchy_enforcer import HierarchyEnforcer
        enforcer = HierarchyEnforcer(db=None)

        result = await enforcer.check_action(
            "ambassador", "campaign_publish", {"price_cents": 19900}
        )
        assert result["approved"] is False
        assert "director" in result["approver"]

    @pytest.mark.asyncio
    async def test_normal_publish_is_approved(self):
        from wai_institute.core.hierarchy_enforcer import HierarchyEnforcer
        enforcer = HierarchyEnforcer(db=None)

        result = await enforcer.check_action(
            "cipher", "campaign_publish", {"price_cents": 1999}
        )
        assert result["approved"] is True

    @pytest.mark.asyncio
    async def test_audio_budget_ok(self):
        from wai_institute.core.hierarchy_enforcer import HierarchyEnforcer
        db = make_mock_db()
        db.persona_tts_budgets.find_one = AsyncMock(return_value={
            "persona": "cipher", "chars_used_this_month": 5000
        })
        enforcer = HierarchyEnforcer(db)

        result = await enforcer.check_audio_budget("cipher", 1000)
        assert result["approved"] is True
        assert result["status"] == "OK"

    @pytest.mark.asyncio
    async def test_audio_budget_hard_cap_blocked(self):
        from wai_institute.core.hierarchy_enforcer import HierarchyEnforcer
        db = make_mock_db()
        db.persona_tts_budgets.find_one = AsyncMock(return_value={
            "persona": "cipher", "chars_used_this_month": 29_400
        })
        enforcer = HierarchyEnforcer(db)

        result = await enforcer.check_audio_budget("cipher", 200)
        assert result["approved"] is False
        assert result["status"] == "HARD_CAP_REACHED"

    def test_free_first_policy_free_tool_passes(self):
        from wai_institute.core.hierarchy_enforcer import HierarchyEnforcer
        enforcer = HierarchyEnforcer(db=None)
        result = enforcer.enforce_free_first({"name": "canva_free", "cost": 0})
        assert result["approved"] is True

    def test_free_first_policy_paid_tool_blocked(self):
        from wai_institute.core.hierarchy_enforcer import HierarchyEnforcer
        enforcer = HierarchyEnforcer(db=None)
        result = enforcer.enforce_free_first({"name": "adobe_illustrator", "cost": 55})
        assert result["approved"] is False

    def test_cultural_alignment_blocks_violations(self):
        from wai_institute.core.hierarchy_enforcer import HierarchyEnforcer
        enforcer = HierarchyEnforcer(db=None)
        result = enforcer.check_cultural_alignment("this is poverty porn content")
        assert result["aligned"] is False

    def test_cultural_alignment_passes_clean_content(self):
        from wai_institute.core.hierarchy_enforcer import HierarchyEnforcer
        enforcer = HierarchyEnforcer(db=None)
        result = enforcer.check_cultural_alignment("I been carrying truth like a torch")
        assert result["aligned"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
