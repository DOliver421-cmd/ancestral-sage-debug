"""
director_validation.py - Director 4.0 Behavioral Validation Suite
===================================================================
Validates that the Director 4.0 infrastructure behaves exactly as
the Director's Brief requires.

Covers:
  - Persona registry completeness (all 12 personas present)
  - Routing correctness (role → persona key mapping)
  - Mode system (set/get, valid enum values)
  - Crisis engine (incident raises level, RED/ORANGE triggers recovery)
  - Delegation engine (task assignment and listing)
  - Incident register (add, stale detection at 72h threshold)
  - System health monitor (flag/metric updates, health status)
  - Persona loader validator (assert_valid passes)

Run standalone:
  cd backend
  python -m tests.director_validation

Or with pytest:
  pytest backend/tests/director_validation.py -v
"""

import sys
import os

# Allow running from repo root with: python backend/tests/director_validation.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# Persona loader tests
# ---------------------------------------------------------------------------

def test_persona_registry_complete():
    from ai.persona_loader import load_personas
    personas = load_personas()
    required = [
        "director", "assistant_director", "ancestral_sage", "savant_scholar",
        "apprentice", "revenue_director", "wai_success_engine", "product_designer",
        "risk_officer", "strategic_navigator", "confidentiality_sentinel", "elder_council",
    ]
    for key in required:
        assert key in personas, f"Missing persona: {key}"
    print(f"  ✓ All {len(required)} personas present in registry")


def test_persona_prompts_non_empty():
    from ai.persona_loader import load_personas
    personas = load_personas()
    for key, prompt in personas.items():
        assert isinstance(prompt, str) and len(prompt) > 50, \
            f"Persona '{key}' has an empty or too-short prompt"
    print(f"  ✓ All persona prompts are non-empty strings")


def test_get_persona_raises_on_unknown():
    from ai.persona_loader import get_persona
    try:
        get_persona("hallucinated_persona")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass
    print("  ✓ get_persona() raises KeyError for unknown personas")


def test_persona_loader_validator():
    from ai.persona_loader_validator import validate_personas
    result = validate_personas()
    assert result["valid"], f"Persona validation failed: {result.get('missing')}"
    assert len(result["missing"]) == 0
    print("  ✓ persona_loader_validator: all personas valid")


# ---------------------------------------------------------------------------
# Routing tests
# ---------------------------------------------------------------------------

def test_routing_defaults():
    from ai.routing import route_request
    assert route_request("student", {}) == "assistant_director"
    assert route_request("instructor", {}) == "assistant_director"
    assert route_request("admin", {}) == "director"
    assert route_request("executive_admin", {}) == "director"
    assert route_request("unknown_role", {}) == "director"  # safe fallback
    print("  ✓ Role-based routing defaults are correct")


def test_routing_force_persona():
    from ai.routing import route_request
    result = route_request("student", {"force_persona": "risk_officer"})
    assert result == "risk_officer"
    print("  ✓ force_persona override works")


def test_routing_force_invalid_persona_falls_through():
    from ai.routing import route_request
    # Invalid persona key should fall through to role default
    result = route_request("student", {"force_persona": "invented_persona"})
    assert result == "assistant_director"  # falls through to student default
    print("  ✓ Invalid force_persona falls through to role default")


def test_routing_threat_escalation():
    from ai.routing import route_request
    result = route_request("admin", {"threat_detected": True})
    assert result == "director"
    print("  ✓ Threat detected routes admin to director")


# ---------------------------------------------------------------------------
# Mode system tests
# ---------------------------------------------------------------------------

def test_mode_system_default():
    from ai.mode_system import ModeSystem, Mode
    ms = ModeSystem()
    assert ms.get_mode() == Mode.BALANCED
    print("  ✓ ModeSystem defaults to BALANCED")


def test_mode_system_set_get():
    from ai.mode_system import ModeSystem, Mode
    ms = ModeSystem()
    ms.set_mode(Mode.RECOVERY, reason="test")
    assert ms.get_mode() == Mode.RECOVERY
    print("  ✓ ModeSystem set/get works")


def test_mode_system_all_modes():
    from ai.mode_system import ModeSystem, Mode
    ms = ModeSystem()
    for mode in Mode:
        ms.set_mode(mode)
        assert ms.get_mode() == mode
    print(f"  ✓ All {len(list(Mode))} modes cycle correctly")


def test_mode_system_history():
    from ai.mode_system import ModeSystem, Mode
    ms = ModeSystem()
    ms.set_mode(Mode.AGGRESSIVE, reason="growth sprint")
    ms.set_mode(Mode.RECOVERY, reason="crisis")
    history = ms.get_history()
    assert len(history) == 2
    assert history[0]["reason"] == "growth sprint"
    print("  ✓ ModeSystem history tracking works")


def test_mode_system_reset():
    from ai.mode_system import ModeSystem, Mode
    ms = ModeSystem()
    ms.set_mode(Mode.AGGRESSIVE)
    ms.reset()
    assert ms.get_mode() == Mode.BALANCED
    print("  ✓ ModeSystem reset() returns to BALANCED")


# ---------------------------------------------------------------------------
# Crisis engine tests
# ---------------------------------------------------------------------------

def test_crisis_engine_default_none():
    from ai.crisis_engine import CrisisEngine, CrisisLevel
    ce = CrisisEngine()
    assert ce.get_level() == CrisisLevel.NONE
    print("  ✓ CrisisEngine defaults to NONE")


def test_crisis_engine_level_calculation():
    from ai.crisis_engine import CrisisEngine, CrisisLevel
    ce = CrisisEngine()
    ce.raise_incident({"severity": "ELEVATED", "type": "reputational", "source": "test", "summary": "test"})
    assert ce.get_level() == CrisisLevel.YELLOW
    ce.raise_incident({"severity": "HIGH", "type": "legal", "source": "test", "summary": "test"})
    assert ce.get_level() == CrisisLevel.ORANGE
    ce.raise_incident({"severity": "CRITICAL", "type": "data_breach", "source": "test", "summary": "test"})
    assert ce.get_level() == CrisisLevel.RED
    print("  ✓ CrisisEngine level escalation: YELLOW → ORANGE → RED")


def test_crisis_engine_recovery_mode():
    from ai.crisis_engine import CrisisEngine, CrisisLevel
    ce = CrisisEngine()
    assert not ce.is_recovery_mode_required()
    ce.raise_incident({"severity": "HIGH", "type": "technical", "source": "test", "summary": "test"})
    assert ce.is_recovery_mode_required()
    print("  ✓ CrisisEngine triggers recovery mode at ORANGE+")


def test_crisis_engine_clear():
    from ai.crisis_engine import CrisisEngine, CrisisLevel
    ce = CrisisEngine()
    ce.raise_incident({"severity": "CRITICAL", "type": "test", "source": "test", "summary": "test"})
    ce.clear_all()
    assert ce.get_level() == CrisisLevel.NONE
    assert len(ce.incidents) == 0
    print("  ✓ CrisisEngine clear_all() resets state")


# ---------------------------------------------------------------------------
# Delegation engine tests
# ---------------------------------------------------------------------------

def test_delegation_engine_assign():
    from ai.delegation_engine import DelegationEngine
    de = DelegationEngine()
    task = de.assign(
        persona="savant_scholar",
        assignment="Build Market Literacy 101 study plan",
        deliverable="Week-by-week plan with assessments",
        timeframe="48 hours",
        owner="director",
    )
    assert task["persona"] == "savant_scholar"
    assert "task_id" in task
    print("  ✓ DelegationEngine assigns task with ID")


def test_delegation_engine_list():
    from ai.delegation_engine import DelegationEngine
    de = DelegationEngine()
    de.assign("risk_officer", "Threat assessment", "Risk report", "24h", "director")
    de.assign("strategic_navigator", "90-day plan", "OKR document", "1 week", "director")
    tasks = de.list_tasks()
    assert len(tasks) == 2
    tasks_for_risk = de.list_tasks(persona="risk_officer")
    assert len(tasks_for_risk) == 1
    print("  ✓ DelegationEngine list/filter works")


def test_delegation_engine_complete():
    from ai.delegation_engine import DelegationEngine
    de = DelegationEngine()
    task = de.assign("apprentice", "Research", "Brief", "3 days", "director")
    tid = task["task_id"]
    assert de.complete_task(tid) is True
    assert len(de.list_tasks()) == 0
    assert de.complete_task(999) is False  # non-existent
    print("  ✓ DelegationEngine complete_task() works")


# ---------------------------------------------------------------------------
# Incident register tests
# ---------------------------------------------------------------------------

def test_incident_register_add():
    from ai.incident_register import IncidentRegister
    ir = IncidentRegister()
    inc = ir.add({
        "title": "Railway healthcheck failing",
        "type": "technical",
        "severity": "HIGH",
        "source": "railway_dashboard",
        "summary": "Healthcheck /api/version returning timeout.",
    })
    assert inc["id"] == 1
    assert inc["status"] == "open"
    assert "timestamp" in inc
    print("  ✓ IncidentRegister.add() stamps id, status, timestamp")


def test_incident_register_stale():
    from ai.incident_register import IncidentRegister
    ir = IncidentRegister()
    ir.add({"title": "Old incident", "type": "test", "severity": "LOW", "source": "test", "summary": "test"})
    # Manually backdate the timestamp past the 72h stale threshold
    ir.incidents[0]["timestamp"] = datetime.now(timezone.utc) - timedelta(hours=73)
    stale = ir.stale_incidents()
    assert len(stale) == 1
    print("  ✓ IncidentRegister stale detection at 72h works")


def test_incident_register_resolve():
    from ai.incident_register import IncidentRegister
    ir = IncidentRegister()
    inc = ir.add({"title": "Test", "type": "test", "severity": "LOW", "source": "test", "summary": "test"})
    assert ir.resolve(inc["id"]) is True
    assert len(ir.list_open()) == 0
    print("  ✓ IncidentRegister.resolve() removes from open list")


# ---------------------------------------------------------------------------
# System health monitor tests
# ---------------------------------------------------------------------------

def test_health_monitor_default():
    from ai.system_health_monitor import SystemHealthMonitor
    hm = SystemHealthMonitor()
    status = hm.get_status()
    assert status["health"] == "nominal"
    print("  ✓ SystemHealthMonitor defaults to nominal")


def test_health_monitor_flag():
    from ai.system_health_monitor import SystemHealthMonitor
    hm = SystemHealthMonitor()
    hm.flag("TTS circuit breaker opened")
    status = hm.get_status()
    assert status["health"] == "warning"
    assert "TTS circuit breaker opened" in status["flags"]
    print("  ✓ SystemHealthMonitor flag raises to warning")


def test_health_monitor_critical():
    from ai.system_health_monitor import SystemHealthMonitor
    hm = SystemHealthMonitor()
    hm.update_metric("db_connected", False)
    assert hm.get_status()["health"] == "critical"
    print("  ✓ SystemHealthMonitor db_connected=False → critical")


def test_health_monitor_metrics():
    from ai.system_health_monitor import SystemHealthMonitor
    hm = SystemHealthMonitor()
    hm.update_metric("latency_ms", 250)
    assert hm.metrics["latency_ms"] == 250
    print("  ✓ SystemHealthMonitor update_metric() works")


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

TESTS = [
    # Persona loader
    test_persona_registry_complete,
    test_persona_prompts_non_empty,
    test_get_persona_raises_on_unknown,
    test_persona_loader_validator,
    # Routing
    test_routing_defaults,
    test_routing_force_persona,
    test_routing_force_invalid_persona_falls_through,
    test_routing_threat_escalation,
    # Mode system
    test_mode_system_default,
    test_mode_system_set_get,
    test_mode_system_all_modes,
    test_mode_system_history,
    test_mode_system_reset,
    # Crisis engine
    test_crisis_engine_default_none,
    test_crisis_engine_level_calculation,
    test_crisis_engine_recovery_mode,
    test_crisis_engine_clear,
    # Delegation engine
    test_delegation_engine_assign,
    test_delegation_engine_list,
    test_delegation_engine_complete,
    # Incident register
    test_incident_register_add,
    test_incident_register_stale,
    test_incident_register_resolve,
    # System health monitor
    test_health_monitor_default,
    test_health_monitor_flag,
    test_health_monitor_critical,
    test_health_monitor_metrics,
]


def run_all() -> bool:
    passed = 0
    failed = 0
    errors = []

    print("=" * 60)
    print("DIRECTOR 4.0 — BEHAVIORAL VALIDATION SUITE")
    print("WAI-Institute / M.O.R.E. Help Center")
    print("=" * 60)

    for test_fn in TESTS:
        section = test_fn.__name__.replace("test_", "").replace("_", " ").upper()
        try:
            test_fn()
            passed += 1
        except Exception as exc:
            failed += 1
            errors.append(f"FAIL [{test_fn.__name__}]: {exc}")
            print(f"  ✗ {section} — {exc}")

    print("-" * 60)
    print(f"Results: {passed} passed / {failed} failed / {len(TESTS)} total")

    if errors:
        print("\nFailed tests:")
        for e in errors:
            print(f"  {e}")
        return False

    print("\n✓ ALL SYSTEMS VALIDATED — DIRECTOR 4.0 IS OPERATIONALLY SOUND.")
    return True


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
