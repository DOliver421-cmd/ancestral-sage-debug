"""app/security/feature_tiers.py — Commercial feature-tier matrix.

Single source of truth for what each tier can access.

Tiers:
  free      — M.O.R.E. Help Center, HTML/JS tools, browser-native audio ONLY.
              NO AI, NO legal tools, NO system controls, NO dashboards, NO TTS.
  premium   — Full AI personas, legal tools, dashboards, TTS/STT, API features.
  executive — All premium + autonomous pipeline, persona management, system controls.

sage_tier governs Sage AI DEPTH (independent of commercial tier):
  basic     — Gate 1 automated safety filter only
  advanced  — Full 3-gate safety escalation pipeline
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Literal, Optional

FeatureTierLabel = Literal["free", "premium", "executive"]
SageTierLabel    = Literal["basic", "advanced"]


# ── Individual feature flags ────────────────────────────────────────────────────

@dataclass(frozen=True)
class TierFeatures:
    """Describes exactly what a commercial tier can access."""
    label: str

    # ── AI
    ai_chat:             bool = False   # /ai/chat
    ai_orchestrator:     bool = False   # /ai/orchestrator
    ai_scholar:          bool = False   # /ai/scholar
    ai_helper:           bool = True    # /ai/helper — always allowed
    ai_director:         bool = False   # /ai/director (role-gated too: admin+)
    ai_revenue_director: bool = False   # /ai/revenue-director
    ai_sage_create:      bool = False   # /ai/sage/create
    ai_cipher:           bool = False   # /ai/cipher
    ai_oracle:           bool = False   # /ai/oracle
    ai_ambassador:       bool = False   # /ai/ambassador
    ai_architect:        bool = False   # /ai/architect
    ai_labs_feedback:    bool = False   # /labs/submissions/{id}/ai-feedback

    # ── Voice / TTS
    tts_sage_openai:     bool = False   # /ai/sage/tts (OpenAI TTS)
    tts_sage_elevenlabs: bool = False   # /ai/sage/elevenlabs/tts
    tts_director:        bool = False   # /ai/director/tts
    tts_cipher:          bool = False   # /ai/cipher/tts
    tts_revenue_director: bool = False  # /ai/revenue-director/tts

    # ── Legal tools (BOTH require premium + consent)
    legal_guide_feature_1: bool = False  # Legal Document Guide (type A)
    legal_guide_feature_2: bool = False  # Legal Situation Advisor (type B)

    # ── Dashboards
    director_dashboard:    bool = False  # Director greeting + pulse
    executive_dashboard:   bool = False  # /exec/dashboard
    analytics_platform:    bool = False  # Platform-wide analytics
    auditor_dashboard:     bool = False  # /auditor/*

    # ── System controls
    platform_flags:        bool = False  # /admin/platform/flags
    gateway_controls:      bool = False  # /admin/gateway/*
    ip_whitelist:          bool = False  # /admin/access/ipwhitelist
    mfa_config:            bool = False  # /admin/mfa/config
    rbac_matrix:           bool = False  # /admin/rbac/matrix
    failover_controls:     bool = False  # backup/switch/reset

    # ── Executive pipeline
    scout_pipeline:        bool = False  # /exec/scout/*
    audio_pipeline:        bool = False  # /exec/audio, /ai/cipher/generate-audio
    merch_pipeline:        bool = False  # /exec/merch/*
    persona_management:    bool = False  # /exec/personas/*
    product_pipeline:      bool = False  # /exec/products/*
    staff_meetings:        bool = False  # /exec/staff-meeting
    memory_policy:         bool = False  # /ai/memory/policy (write)
    break_glass:           bool = False  # executive override

    # ── API-as-a-Service
    api_keys:              bool = True   # /revenue/api-keys (base feature)
    course_licensing:      bool = True   # /revenue/courses/license
    sovereign_workspace:   bool = False  # /revenue/sovereign/workspace

    # ── Community (M.O.R.E. — always free)
    community_read:        bool = True
    community_post:        bool = True
    community_help_center: bool = True   # /ai/helper specifically

    # ── Adaptive learning
    adaptive_learning:     bool = False  # /adaptive/me (premium feature)


# ── Tier definitions ────────────────────────────────────────────────────────────

FREE_TIER = TierFeatures(
    label="free",
    # AI
    ai_helper=True,          # Only the public Helper is free
    # Community (M.O.R.E.) — free
    community_read=True,
    community_post=True,
    community_help_center=True,
    # API keys — base tier
    api_keys=True,
    course_licensing=True,
    # Everything else: False (default)
)

PREMIUM_TIER = TierFeatures(
    label="premium",
    # AI
    ai_chat=True,
    ai_orchestrator=True,
    ai_scholar=True,
    ai_helper=True,
    ai_labs_feedback=True,
    # Voice / TTS
    tts_sage_openai=True,
    tts_sage_elevenlabs=False,   # elevenlabs remains executive-only
    # Legal tools
    legal_guide_feature_1=True,
    legal_guide_feature_2=True,
    # Director dashboard (students see greeting only)
    director_dashboard=True,
    # Community
    community_read=True,
    community_post=True,
    community_help_center=True,
    # API
    api_keys=True,
    course_licensing=True,
    sovereign_workspace=True,
    # Adaptive learning
    adaptive_learning=True,
)

EXECUTIVE_TIER = TierFeatures(
    label="executive",
    # Full AI suite (all personas — also role-gated to admin+)
    ai_chat=True,
    ai_orchestrator=True,
    ai_scholar=True,
    ai_helper=True,
    ai_director=True,
    ai_revenue_director=True,
    ai_sage_create=True,
    ai_cipher=True,
    ai_oracle=True,
    ai_ambassador=True,
    ai_architect=True,
    ai_labs_feedback=True,
    # Voice / TTS — all tiers
    tts_sage_openai=True,
    tts_sage_elevenlabs=True,
    tts_director=True,
    tts_cipher=True,
    tts_revenue_director=True,
    # Legal tools
    legal_guide_feature_1=True,
    legal_guide_feature_2=True,
    # Dashboards
    director_dashboard=True,
    executive_dashboard=True,
    analytics_platform=True,
    auditor_dashboard=True,
    # System controls
    platform_flags=True,
    gateway_controls=True,
    ip_whitelist=True,
    mfa_config=True,
    rbac_matrix=True,
    failover_controls=True,
    # Executive pipeline
    scout_pipeline=True,
    audio_pipeline=True,
    merch_pipeline=True,
    persona_management=True,
    product_pipeline=True,
    staff_meetings=True,
    memory_policy=True,
    break_glass=True,
    # API
    api_keys=True,
    course_licensing=True,
    sovereign_workspace=True,
    # Adaptive
    adaptive_learning=True,
    # Community
    community_read=True,
    community_post=True,
    community_help_center=True,
)

TIER_MAP: Dict[str, TierFeatures] = {
    "free":      FREE_TIER,
    "premium":   PREMIUM_TIER,
    "executive": EXECUTIVE_TIER,
}


# ── Sage tier definitions ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class SageTierFeatures:
    """Governs depth of the Ancestral Sage AI safety gate pipeline."""
    label: str
    gate_1_enabled: bool = True    # Automated harmful content filter (always on)
    gate_2_enabled: bool = False   # Human escalation check
    gate_3_enabled: bool = False   # Director approval required for major decisions
    max_intensity:  str  = "moderate"  # light | moderate | deep | ceremonial
    max_safety_level: str = "exploratory"  # general | exploratory | advanced | unrestricted
    consent_ttl_minutes: int = 120


SAGE_TIER_MAP: Dict[str, SageTierFeatures] = {
    "basic": SageTierFeatures(
        label="basic",
        gate_1_enabled=True,
        gate_2_enabled=False,
        gate_3_enabled=False,
        max_intensity="moderate",
        max_safety_level="exploratory",
    ),
    "advanced": SageTierFeatures(
        label="advanced",
        gate_1_enabled=True,
        gate_2_enabled=True,
        gate_3_enabled=True,
        max_intensity="ceremonial",
        max_safety_level="unrestricted",
        consent_ttl_minutes=60,  # shorter TTL for advanced sessions
    ),
}


# ── Legal tool gating ────────────────────────────────────────────────────────────
# Both legal guide features share identical gating requirements.

@dataclass(frozen=True)
class LegalToolPolicy:
    """Policy that must be satisfied before any legal tool access is granted."""
    feature_name: str
    disclaimer_text: str
    requires_premium: bool = True
    requires_auth: bool = True
    requires_consent: bool = True
    log_every_access: bool = True
    consent_field: str = "legal_disclaimer_ack"


LEGAL_TOOL_POLICY_1 = LegalToolPolicy(
    feature_name="Legal Document Guide",
    disclaimer_text=(
        "This tool provides general legal information only and is NOT a substitute "
        "for advice from a licensed attorney. No attorney-client relationship is "
        "created by your use of this service. For legal advice specific to your "
        "situation, consult a licensed legal professional."
    ),
)

LEGAL_TOOL_POLICY_2 = LegalToolPolicy(
    feature_name="Legal Situation Advisor",
    disclaimer_text=(
        "This tool provides general legal information only and is NOT a substitute "
        "for advice from a licensed attorney. No attorney-client relationship is "
        "created by your use of this service. For legal advice specific to your "
        "situation, consult a licensed legal professional."
    ),
)

LEGAL_TOOL_POLICIES: Dict[str, LegalToolPolicy] = {
    "legal_guide_1": LEGAL_TOOL_POLICY_1,
    "legal_guide_2": LEGAL_TOOL_POLICY_2,
}


# ── Helper functions ─────────────────────────────────────────────────────────────

def get_tier_features(tier: str) -> TierFeatures:
    """Return the TierFeatures object for the given tier label."""
    return TIER_MAP.get(tier, FREE_TIER)


def get_sage_tier_features(sage_tier: str) -> SageTierFeatures:
    """Return the SageTierFeatures object for the given sage_tier label."""
    return SAGE_TIER_MAP.get(sage_tier, SAGE_TIER_MAP["basic"])


def feature_allowed(tier: str, feature_attr: str) -> bool:
    """Check if a specific feature attribute is enabled for the given tier."""
    features = get_tier_features(tier)
    return bool(getattr(features, feature_attr, False))


def tier_rank(tier: str) -> int:
    """Return numeric rank of the feature tier for comparison."""
    return {"free": 0, "premium": 1, "executive": 2}.get(tier, 0)


def tier_meets_minimum(user_tier: str, required_tier: str) -> bool:
    """Return True if user_tier >= required_tier."""
    return tier_rank(user_tier) >= tier_rank(required_tier)


# ── Frontend capability contract ─────────────────────────────────────────────────
# Returned by /api/auth/me and /api/auth/capabilities to drive UI visibility.

def build_capability_contract(
    role: str,
    feature_tier: str,
    sage_tier: str,
    more_member: bool = False,
) -> Dict[str, object]:
    """Build the full capability dictionary sent to the frontend."""
    from app.security.rbac import ROLE_RANK, effective_permissions

    features = get_tier_features(feature_tier)
    sage     = get_sage_tier_features(sage_tier)
    perms    = effective_permissions(role, feature_tier)
    rank     = ROLE_RANK.get(role, 0)

    return {
        "role":         role,
        "feature_tier": feature_tier,
        "sage_tier":    sage_tier,
        "more_member":  more_member,
        "rank":         rank,

        # ── AI capabilities
        "ai": {
            "chat":             features.ai_chat,
            "orchestrator":     features.ai_orchestrator,
            "scholar":          features.ai_scholar,
            "helper":           features.ai_helper,
            "director":         features.ai_director and rank >= 3,
            "revenue_director": features.ai_revenue_director and rank >= 3,
            "sage_create":      features.ai_sage_create and rank >= 3,
            "cipher":           features.ai_cipher and rank >= 3,
            "oracle":           features.ai_oracle and rank >= 3,
            "ambassador":       features.ai_ambassador and rank >= 3,
            "architect":        features.ai_architect and rank >= 3,
            "labs_feedback":    features.ai_labs_feedback and rank >= 2,
        },

        # ── Voice / TTS
        "tts": {
            "sage_openai":     features.tts_sage_openai,
            "sage_elevenlabs": features.tts_sage_elevenlabs and rank >= 4,
            "director":        features.tts_director and rank >= 3,
            "cipher":          features.tts_cipher and rank >= 3,
            "revenue_director": features.tts_revenue_director and rank >= 3,
        },

        # ── Legal tools
        "legal": {
            "guide_1_enabled": features.legal_guide_feature_1,
            "guide_2_enabled": features.legal_guide_feature_2,
            "requires_consent": True,
            "disclaimer_shown": False,  # frontend must set this after user confirms
        },

        # ── Dashboards
        "dashboards": {
            "director":    features.director_dashboard,
            "executive":   features.executive_dashboard and rank >= 4,
            "analytics":   features.analytics_platform and rank >= 3,
            "auditor":     features.auditor_dashboard and rank >= 3,
        },

        # ── System controls
        "system_controls": {
            "platform_flags":   features.platform_flags and rank >= 3,
            "gateway":          features.gateway_controls and rank >= 3,
            "ip_whitelist":     features.ip_whitelist and rank >= 3,
            "mfa_config":       features.mfa_config and rank >= 3,
            "rbac_matrix":      features.rbac_matrix and rank >= 3,
            "failover":         features.failover_controls and rank >= 3,
        },

        # ── Executive pipeline
        "executive": {
            "scout":           features.scout_pipeline and rank >= 4,
            "audio":           features.audio_pipeline and rank >= 4,
            "merch":           features.merch_pipeline and rank >= 4,
            "personas":        features.persona_management and rank >= 4,
            "products":        features.product_pipeline and rank >= 4,
            "staff_meetings":  features.staff_meetings and rank >= 4,
            "memory_policy":   features.memory_policy and rank >= 4,
            "break_glass":     features.break_glass and rank >= 4,
        },

        # ── Sage depth
        "sage_gates": {
            "gate_1": sage.gate_1_enabled,
            "gate_2": sage.gate_2_enabled,
            "gate_3": sage.gate_3_enabled,
            "max_intensity":    sage.max_intensity,
            "max_safety_level": sage.max_safety_level,
        },

        # ── Community
        "community": {
            "read":         features.community_read,
            "post":         features.community_post,
            "help_center":  features.community_help_center,
            "moderate":     rank >= 3,
        },

        # ── Permissions (flat set for quick frontend checks)
        "permissions": sorted(perms),
    }
