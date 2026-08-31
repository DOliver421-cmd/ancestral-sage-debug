"""
operational_engine.py — Hybrid NAM's 12 Operational Functions

Per the Assistant Director specification, this module provides concrete
operational intelligence across 12 institutional functions:

  1. Mission        — Protect and interpret the institutional purpose
  2. Strategy       — Help determine where the institution goes
  3. Memory         — Preserve institutional continuity
  4. Governance     — Apply constitutional principles
  5. Challenge      — Question leadership when warranted
  6. Ecosystem      — Coordinate the various AI/services
  7. Power          — Analyze authority, ownership and benefit
  8. Economics      — Track value creation and value capture
  9. Risk           — Detect threats and dependencies
 10. Accountability — Compare promises against results
 11. Crisis         — Provide structured intelligence during disruption
 12. Succession     — Preserve institutional capability beyond individuals

All functions follow the constitutional principle: "Loyalty to constitution
and mission, not to the founder's every decision."
"""

import uuid
from datetime import datetime
from typing import Optional


# ── Evidence Classification (per spec §7 Evidence Discipline) ────────────────

EVIDENCE_LEVELS = [
    "known",         # verified
    "documented",    # source-attributed
    "inferred",      # derived from available evidence
    "disputed",      # multiple conflicting accounts
    "unknown",       # no evidence available
    "recommendation", # value judgment, not a fact
]


# ── Resource Dimensions (per spec §2 Resource Allocation) ────────────────────

RESOURCE_DIMENSIONS = [
    "money",        # financial capital
    "time",         # hours and calendar
    "people",       # human capacity
    "compute",      # technical resources
    "attention",    # focus and visibility
    "credibility",  # institutional trust
]


# ── Risk Categories (per spec §3 Institutional Risk) ─────────────────────────

RISK_CATEGORIES = [
    "financial_dependency",
    "vendor_dependency",
    "technology_lock_in",
    "intellectual_property_loss",
    "data_control_loss",
    "reputational_risk",
    "legal_exposure",
    "leadership_concentration",
    "single_point_of_failure",
    "mission_drift",
    "partner_conflict",
    "ai_failure",
    "succession_problem",
]


# ── 1. MISSION ────────────────────────────────────────────────────────────────

def interpret_mission(
    action: dict,
    principles: list[str],
) -> dict:
    """
    Mission interpretation: protect and interpret the institutional purpose.
    Returns alignment, conflicts, and clarifying interpretation.
    """
    text = (action.get("description", "") + " " + action.get("purpose", "")).lower()

    alignments = []
    conflicts = []
    for principle in principles:
        p_lower = principle.lower()
        # Cheap heuristic: positive alignment if action text shares vocabulary
        keywords = [w for w in p_lower.split() if len(w) > 5]
        hits = sum(1 for k in keywords if k in text)
        if hits > 0:
            alignments.append({"principle": principle, "evidence_strength": "inferred", "keyword_hits": hits})
        else:
            conflicts.append({"principle": principle, "interpretation": "no direct alignment in description"})

    return {
        "mission_id": f"MSN-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "action": action.get("description", ""),
        "aligned_principles": alignments,
        "unaddressed_principles": conflicts[:5],
        "interpretation": (
            "Action's mission effect requires human judgment beyond lexical scan. "
            "Listed alignments are inferred from shared vocabulary, not verified."
        ),
        "evidence_discipline": "All alignments above are INFERRED, not KNOWN. Verify before action.",
    }


# ── 2. STRATEGY ───────────────────────────────────────────────────────────────

def strategic_planning(
    context: dict,
    time_horizons: list[str] = None,
) -> dict:
    """
    Strategy: where are we going, what should we build, what should we not,
    highest-value use of resources, dependencies, opportunities, missed.

    time_horizons defaults to ["30d", "90d", "365d"].
    """
    if not time_horizons:
        time_horizons = ["30d", "90d", "365d"]

    context_text = (context.get("situation", "") + " " + context.get("context", "")).lower()

    return {
        "plan_id": f"STR-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "situation_summary": context.get("situation", ""),
        "time_horizons": time_horizons,
        "questions": {
            "where_going": "Where is the institution going in this horizon? (requires human input)",
            "what_build": "What is the next concrete thing to build?",
            "what_not_build": "What should be explicitly deferred or declined?",
            "highest_value_use": "Where do limited resources produce the greatest strategic return?",
            "dependencies_forming": "What dependencies are forming across the horizon?",
            "opportunities_missed": "What opportunities are not being pursued and why?",
        },
        "evidence_discipline": "Strategic answers are RECOMMENDATIONS, not KNOWN facts.",
        "context_evidence_level": _classify_evidence(context_text),
    }


def _classify_evidence(text: str) -> str:
    """Classify the evidence level of a claim based on heuristics."""
    if not text:
        return "unknown"
    # Rough heuristic: more declarative statements with sources = documented
    if any(s in text for s in ["verified", "confirmed", "documented", "audit"]):
        return "documented"
    if any(s in text for s in ["might", "could", "possibly", "perhaps"]):
        return "inferred"
    return "inferred"


# ── 3. MEMORY (institutional continuity) ─────────────────────────────────────

def continuity_record(
    item_type: str,
    title: str,
    content: str,
    people: list[str] = None,
    status: str = "active",
) -> dict:
    """
    Memory: preserve institutional continuity.
    Wraps items in a continuity record with provenance.
    """
    return {
        "continuity_id": f"CNT-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "item_type": item_type,  # decision | lesson | procedure | principle | relationship
        "title": title,
        "content": content,
        "people": people or [],
        "status": status,  # active | superseded | deprecated
        "succession_relevant": True,
    }


# ── 4. GOVERNANCE ─────────────────────────────────────────────────────────────

def governance_check(
    action: dict,
    constitutional_principles: list[str],
) -> dict:
    """
    Governance: apply constitutional principles. Returns verdict per principle.
    """
    text = (action.get("description", "") + " " + action.get("purpose", "")).lower()

    verdicts = []
    for principle in constitutional_principles:
        p_lower = principle.lower()
        # Heuristic: any explicit conflict keyword
        conflict_kw = ["never", "no ", "must not", "prohibited"]
        has_conflict = any(kw in p_lower and kw in text for kw in conflict_kw)
        keyword_overlap = sum(1 for w in p_lower.split() if len(w) > 4 and w in text)
        verdicts.append({
            "principle": principle,
            "verdict": "conflict" if has_conflict else ("aligned" if keyword_overlap > 0 else "silent"),
            "evidence": "inferred" if not has_conflict else "documented",
        })

    return {
        "governance_id": f"GOV-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "action": action.get("description", ""),
        "verdicts": verdicts,
        "requires_human_review": any(v["verdict"] == "conflict" for v in verdicts),
    }


# ── 5. CHALLENGE ──────────────────────────────────────────────────────────────

def challenge_leadership(
    claim: str,
    evidence: str,
    conflict_with: Optional[str] = None,
) -> dict:
    """
    Challenge: question leadership when warranted.
    Per spec: distinguish loyalty to constitution from obedience to founder.
    """
    return {
        "challenge_id": f"CHL-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "claim": claim,
        "evidence": evidence,
        "conflict_with_constitution": conflict_with,
        "principle": (
            "Loyalty is to the constitution and mission, not to the founder's every decision. "
            "If the founder ultimately overrides, the lesson must be preserved."
        ),
        "disposition": "challenge" if conflict_with else "question",
        "preservation_required": True,
    }


# ── 6. ECOSYSTEM (coordination) ──────────────────────────────────────────────

def ecosystem_coordination(
    services: list[dict],
    proposed_action: str,
) -> dict:
    """
    Ecosystem: coordinate the various AI/services.
    Identifies which services are affected, sequencing, conflicts.
    """
    affected = []
    for svc in services:
        svc_name = svc.get("name", "unknown")
        svc_role = svc.get("role", "")
        if any(kw in svc_role.lower() for kw in proposed_action.lower().split()):
            affected.append({"service": svc_name, "role": svc_role, "impact": "direct"})

    return {
        "coordination_id": f"ECO-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "proposed_action": proposed_action,
        "services_total": len(services),
        "services_directly_affected": len(affected),
        "affected": affected,
        "sequencing_required": len(affected) > 1,
        "evidence_discipline": "Service impact is INFERRED from role description overlap.",
    }


# ── 7. POWER (authority, ownership, benefit) ─────────────────────────────────

def power_benefit_analysis(
    actor: str,
    beneficiary: str,
    decision: str,
) -> dict:
    """
    Power: analyze authority, ownership, and benefit.
    Detects concentration, misaligned incentives.
    """
    return {
        "analysis_id": f"PWR-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "actor": actor,
        "beneficiary": beneficiary,
        "decision": decision,
        "alignment": "aligned" if actor == beneficiary else "divergent",
        "concerns": [] if actor == beneficiary else [
            "Actor-decision and beneficiary diverge. Review for principal-agent risk.",
        ],
        "evidence_discipline": "Alignment is INFERRED from string match.",
    }


# ── 8. ECONOMICS (value flow) ────────────────────────────────────────────────

def value_flow_analysis(
    project: str,
    creators: list[str] = None,
    owners: list[str] = None,
    distributors: list[str] = None,
    revenue_recipients: list[str] = None,
    risk_bearers: list[str] = None,
) -> dict:
    """
    Economics: track value creation and value capture (Build→Own→License→Scale).
    """
    creators = creators or []
    owners = owners or []
    distributors = distributors or []
    revenue_recipients = revenue_recipients or []
    risk_bearers = risk_bearers or []

    # Detect asymmetry
    notes = []
    if len(revenue_recipients) > len(creators):
        notes.append("More revenue recipients than creators — value capture broader than value creation.")
    if len(owners) == 1 and len(creators) > 1:
        notes.append("Single owner for multiple creators — concentration risk.")
    if not risk_bearers:
        notes.append("No risk bearers identified — risk may be unallocated.")

    return {
        "flow_id": f"VAL-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "project": project,
        "value_creation": creators,
        "value_ownership": owners,
        "value_distribution": distributors,
        "value_revenue": revenue_recipients,
        "value_risk": risk_bearers,
        "asymmetries": notes,
        "principle": "Build → Own → Collaborate → License → Scale → Reinvest → Preserve the source.",
    }


# ── 9. RISK ───────────────────────────────────────────────────────────────────

def institutional_risk_scan(
    signals: list[dict],
) -> dict:
    """
    Risk: detect threats and dependencies across 13 categories.
    signals: list of {category, evidence, severity, evidence_level}
    """
    by_category = {cat: [] for cat in RISK_CATEGORIES}
    for sig in signals:
        cat = sig.get("category", "unknown")
        if cat in by_category:
            by_category[cat].append(sig)

    aggregate = {}
    for cat, items in by_category.items():
        if not items:
            continue
        severity = max((s.get("severity", 0.0) for s in items), default=0.0)
        aggregate[cat] = {
            "signal_count": len(items),
            "max_severity": severity,
            "evidence_levels": [s.get("evidence_level", "inferred") for s in items],
        }

    high_risk = [cat for cat, info in aggregate.items() if info["max_severity"] >= 0.7]

    return {
        "scan_id": f"RSK-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "categories_covered": RISK_CATEGORIES,
        "categories_with_signals": list(aggregate.keys()),
        "high_risk_categories": high_risk,
        "details": aggregate,
        "principle": "Risk is about what can kill the institution, not just what can improve it.",
    }


# ── 10. ACCOUNTABILITY ────────────────────────────────────────────────────────

def accountability_check(
    objective: str,
    owner: str,
    deadline: str,
    metric: str,
    result: str = None,
    variance: Optional[str] = None,
    explanation: Optional[str] = None,
    corrective_action: Optional[str] = None,
) -> dict:
    """
    Accountability: compare promises against results.
    """
    completed = result is not None
    return {
        "check_id": f"ACC-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "objective": objective,
        "owner": owner,
        "deadline": deadline,
        "metric": metric,
        "result": result,
        "completed": completed,
        "variance": variance,
        "explanation": explanation,
        "corrective_action": corrective_action,
        "principle": "Did we actually do what we said we would?",
    }


# ── 11. CRISIS ────────────────────────────────────────────────────────────────

def crisis_assessment(
    what_happened: str,
    what_we_know: list[str] = None,
    what_we_dont_know: list[str] = None,
    what_is_at_risk: list[str] = None,
    immediate_steps: list[str] = None,
    requires_human_authorization: list[str] = None,
) -> dict:
    """
    Crisis: structured intelligence during disruption.
    Per spec: normal operations are suspended; NAM reports, humans authorize.
    """
    return {
        "assessment_id": f"CRS-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "crisis_mode": True,
        "what_happened": what_happened,
        "what_we_know": what_we_know or [],
        "what_we_dont_know": what_we_dont_know or [],
        "what_is_at_risk": what_is_at_risk or [],
        "immediate_steps": immediate_steps or [],
        "requires_human_authorization": requires_human_authorization or [],
        "principle": (
            "NAM does not assume operational authority. NAM provides structured intelligence; "
            "humans authorize consequential action."
        ),
    }


# ── 12. SUCCESSION ────────────────────────────────────────────────────────────

def succession_record(
    capability: str,
    current_holder: str,
    knowledge_artifact_ids: list[str] = None,
    next_holder: Optional[str] = None,
    status: str = "identified",
) -> dict:
    """
    Succession: preserve institutional capability beyond individuals.
    Tracks the handoff envelope: decisions, unfinished work, principles,
    relationships, procedures, lessons.
    """
    return {
        "succession_id": f"SUC-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "capability": capability,
        "current_holder": current_holder,
        "next_holder": next_holder,
        "knowledge_artifact_ids": knowledge_artifact_ids or [],
        "status": status,  # identified | preparing | ready | transferred
        "continuity_envelope": [
            "decision_history",
            "unfinished_work",
            "principles",
            "relationships",
            "procedures",
            "lessons_learned",
        ],
        "principle": "NAM does not become the founder. NAM preserves capability beyond individuals.",
    }


# ── Conflict Resolution (per spec §5) ────────────────────────────────────────

def conflict_mediation(
    parties: list[str],
    positions: dict,
    interests: dict,
    evidence: dict,
    constitutional_principles: list[str],
) -> dict:
    """
    Conflict resolution: define the disagreement, identify interests,
    establish the evidence, identify the constitutional principles involved,
    present options, recommend a resolution, escalate when necessary.
    """
    options = []
    for principle in constitutional_principles:
        options.append({
            "principle": principle,
            "option": f"Apply '{principle}' to resolve tension",
        })

    return {
        "mediation_id": f"CNF-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "parties": parties,
        "positions": positions,
        "interests": interests,
        "evidence": evidence,
        "principles_invoked": constitutional_principles,
        "options": options,
        "recommendation": (
            "Recommendation: review options above. Per spec, NAM identifies options "
            "but does not decide. Escalate to human authority when stakes exceed "
            "NAM's mandate."
        ),
        "evidence_discipline": "Positions and interests are SELF-REPORTED, not verified.",
    }
