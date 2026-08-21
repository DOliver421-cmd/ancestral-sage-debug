"""
entitlements.py — Capability-Based Entitlement Engine
=====================================================

The single source of truth for what a user can do on the platform.

Architecture:
  USER → MEMBERSHIP → ENTITLEMENT ENGINE → CAPABILITY → LIMITS → FEATURE EXPERIENCE

Key principle: Capability-based, NOT page-based.
  ✅ publish.create, publish.analytics, publish.white_label
  ❌ canAccessPublishPage, canAccessProPublishPage

This gives flexibility to change pricing later WITHOUT rewriting the application.
"""

from typing import Any, Dict, Optional


# ── Capability Definitions ────────────────────────────────────────────────────
# Static definitions of every capability the platform supports.
# Each capability has a category and description.

CAPABILITIES: Dict[str, Dict[str, str]] = {
    # AI / NAM
    "nam.chat": {"category": "ai", "description": "Basic AI conversations"},
    "nam.memory": {"category": "ai", "description": "Persistent conversation memory"},
    "nam.coaching": {"category": "ai", "description": "AI-guided coaching sessions"},
    "nam.orchestration": {"category": "ai", "description": "Multi-step AI workflows"},
    "nam.autonomous": {"category": "ai", "description": "Autonomous AI suggestions"},
    
    # CREATE
    "create.projects": {"category": "creation", "description": "Content creation projects"},
    "create.ai_assist": {"category": "creation", "description": "AI writing assistance"},
    "create.advanced_formatting": {"category": "creation", "description": "Professional formatting tools"},
    "create.collaboration": {"category": "creation", "description": "Team collaboration on projects"},
    "create.white_label": {"category": "creation", "description": "Custom branding on outputs"},
    
    # PUBLISH
    "publish.create": {"category": "publishing", "description": "Create published content"},
    "publish.marketplace": {"category": "publishing", "description": "Publish to marketplace"},
    "publish.analytics": {"category": "publishing", "description": "Read/engagement analytics"},
    "publish.distribution": {"category": "publishing", "description": "External distribution channels"},
    "publish.scheduling": {"category": "publishing", "description": "Scheduled publishing"},
    
    # LEARN
    "learn.courses": {"category": "learning", "description": "Access courses"},
    "learn.ai_tutor": {"category": "learning", "description": "AI tutoring assistance"},
    "learn.coaching": {"category": "learning", "description": "Personal learning coaching"},
    "learn.certificates": {"category": "learning", "description": "Earn certificates"},
    "learn.create_courses": {"category": "learning", "description": "Create and sell courses"},
    
    # COMMUNITY
    "community.read": {"category": "community", "description": "Read community content"},
    "community.post": {"category": "community", "description": "Post in community"},
    "community.create_hub": {"category": "community", "description": "Create community hubs"},
    "community.moderate": {"category": "community", "description": "Moderate community content"},
    "community.guild": {"category": "community", "description": "Create and manage guilds"},
    
    # MARKETPLACE
    "marketplace.browse": {"category": "marketplace", "description": "Browse marketplace"},
    "marketplace.sell": {"category": "marketplace", "description": "Sell products"},
    "marketplace.storefront": {"category": "marketplace", "description": "Custom storefront"},
    "marketplace.analytics": {"category": "marketplace", "description": "Sales analytics"},
    "marketplace.vendor_mgmt": {"category": "marketplace", "description": "Vendor management tools"},
    
    # SANCTUARY
    "sanctuary.journal": {"category": "sanctuary", "description": "Basic journaling"},
    "sanctuary.ai_reflection": {"category": "sanctuary", "description": "AI-guided reflection"},
    "sanctuary.mood_tracking": {"category": "sanctuary", "description": "Mood pattern analytics"},
    "sanctuary.group": {"category": "sanctuary", "description": "Group healing sessions"},
    "sanctuary.org_wellness": {"category": "sanctuary", "description": "Organization wellness dashboard"},
    
    # MUSIC
    "music.compose": {"category": "music", "description": "Basic music composition"},
    "music.studio": {"category": "music", "description": "Full production studio"},
    "music.ai_production": {"category": "music", "description": "AI-assisted production"},
    "music.collaboration": {"category": "music", "description": "Team production"},
    "music.label_tools": {"category": "music", "description": "Label management tools"},
    
    # GAMES
    "games.play": {"category": "games", "description": "Play games"},
    "games.compete": {"category": "games", "description": "Competitive ranking"},
    "games.create": {"category": "games", "description": "Create custom games"},
    
    # DIRECTOR
    "director.analytics": {"category": "director", "description": "Platform analytics"},
    "director.governance": {"category": "director", "description": "Governance controls"},
    "director.api": {"category": "director", "description": "API access"},
    "director.compliance": {"category": "director", "description": "Compliance tools"},
}


# ── Tier Limits ───────────────────────────────────────────────────────────────
# Each tier defines the value for each capability.
# - True/False = feature enabled/disabled
# - Integer = limit (e.g., 3 projects)
# - -1 = unlimited
# - 0.0-1.0 = percentage (e.g., marketplace fee)

TIER_LIMITS: Dict[str, Dict[str, Any]] = {
    "free": {
        # AI / NAM
        "nam.chat": True,
        "nam.memory": False,
        "nam.coaching": False,
        "nam.orchestration": False,
        "nam.autonomous": False,
        
        # CREATE
        "create.projects": 3,
        "create.ai_assist": False,
        "create.advanced_formatting": False,
        "create.collaboration": False,
        "create.white_label": False,
        
        # PUBLISH
        "publish.create": True,
        "publish.marketplace": False,
        "publish.analytics": False,
        "publish.distribution": False,
        "publish.scheduling": False,
        
        # LEARN
        "learn.courses": 1,
        "learn.ai_tutor": False,
        "learn.coaching": False,
        "learn.certificates": False,
        "learn.create_courses": False,
        
        # COMMUNITY
        "community.read": True,
        "community.post": True,
        "community.create_hub": False,
        "community.moderate": False,
        "community.guild": False,
        
        # MARKETPLACE
        "marketplace.browse": True,
        "marketplace.sell": False,
        "marketplace.storefront": False,
        "marketplace.analytics": False,
        "marketplace.vendor_mgmt": False,
        
        # SANCTUARY
        "sanctuary.journal": True,
        "sanctuary.ai_reflection": False,
        "sanctuary.mood_tracking": False,
        "sanctuary.group": False,
        "sanctuary.org_wellness": False,
        
        # MUSIC
        "music.compose": True,
        "music.studio": False,
        "music.ai_production": False,
        "music.collaboration": False,
        "music.label_tools": False,
        
        # GAMES
        "games.play": True,
        "games.compete": False,
        "games.create": False,
        
        # DIRECTOR
        "director.analytics": False,
        "director.governance": False,
        "director.api": False,
        "director.compliance": False,
        
        # Resource limits
        "ai_daily_tokens": 1000,
        "storage_mb": 100,
        "projects": 3,
        "courses": 1,
        "marketplace_fee": 0.30,
    },
    "creator": {
        # AI / NAM
        "nam.chat": True,
        "nam.memory": True,
        "nam.coaching": False,
        "nam.orchestration": False,
        "nam.autonomous": False,
        
        # CREATE
        "create.projects": 10,
        "create.ai_assist": True,
        "create.advanced_formatting": False,
        "create.collaboration": False,
        "create.white_label": False,
        
        # PUBLISH
        "publish.create": True,
        "publish.marketplace": True,
        "publish.analytics": True,
        "publish.distribution": False,
        "publish.scheduling": False,
        
        # LEARN
        "learn.courses": 5,
        "learn.ai_tutor": True,
        "learn.coaching": False,
        "learn.certificates": True,
        "learn.create_courses": False,
        
        # COMMUNITY
        "community.read": True,
        "community.post": True,
        "community.create_hub": True,
        "community.moderate": False,
        "community.guild": False,
        
        # MARKETPLACE
        "marketplace.browse": True,
        "marketplace.sell": True,
        "marketplace.storefront": False,
        "marketplace.analytics": False,
        "marketplace.vendor_mgmt": False,
        
        # SANCTUARY
        "sanctuary.journal": True,
        "sanctuary.ai_reflection": True,
        "sanctuary.mood_tracking": False,
        "sanctuary.group": False,
        "sanctuary.org_wellness": False,
        
        # MUSIC
        "music.compose": True,
        "music.studio": True,
        "music.ai_production": False,
        "music.collaboration": False,
        "music.label_tools": False,
        
        # GAMES
        "games.play": True,
        "games.compete": True,
        "games.create": False,
        
        # DIRECTOR
        "director.analytics": False,
        "director.governance": False,
        "director.api": False,
        "director.compliance": False,
        
        # Resource limits
        "ai_daily_tokens": 5000,
        "storage_mb": 500,
        "projects": 10,
        "courses": 5,
        "marketplace_fee": 0.25,
    },
    "pro": {
        # AI / NAM
        "nam.chat": True,
        "nam.memory": True,
        "nam.coaching": True,
        "nam.orchestration": True,
        "nam.autonomous": False,
        
        # CREATE
        "create.projects": -1,  # unlimited
        "create.ai_assist": True,
        "create.advanced_formatting": True,
        "create.collaboration": True,
        "create.white_label": False,
        
        # PUBLISH
        "publish.create": True,
        "publish.marketplace": True,
        "publish.analytics": True,
        "publish.distribution": True,
        "publish.scheduling": True,
        
        # LEARN
        "learn.courses": -1,  # unlimited
        "learn.ai_tutor": True,
        "learn.coaching": True,
        "learn.certificates": True,
        "learn.create_courses": False,
        
        # COMMUNITY
        "community.read": True,
        "community.post": True,
        "community.create_hub": True,
        "community.moderate": True,
        "community.guild": False,
        
        # MARKETPLACE
        "marketplace.browse": True,
        "marketplace.sell": True,
        "marketplace.storefront": True,
        "marketplace.analytics": True,
        "marketplace.vendor_mgmt": False,
        
        # SANCTUARY
        "sanctuary.journal": True,
        "sanctuary.ai_reflection": True,
        "sanctuary.mood_tracking": True,
        "sanctuary.group": False,
        "sanctuary.org_wellness": False,
        
        # MUSIC
        "music.compose": True,
        "music.studio": True,
        "music.ai_production": True,
        "music.collaboration": False,
        "music.label_tools": False,
        
        # GAMES
        "games.play": True,
        "games.compete": True,
        "games.create": False,
        
        # DIRECTOR
        "director.analytics": False,
        "director.governance": False,
        "director.api": False,
        "director.compliance": False,
        
        # Resource limits
        "ai_daily_tokens": 25000,
        "storage_mb": 2000,
        "projects": -1,
        "courses": -1,
        "marketplace_fee": 0.20,
    },
    "studio": {
        # AI / NAM
        "nam.chat": True,
        "nam.memory": True,
        "nam.coaching": True,
        "nam.orchestration": True,
        "nam.autonomous": True,
        
        # CREATE
        "create.projects": -1,
        "create.ai_assist": True,
        "create.advanced_formatting": True,
        "create.collaboration": True,
        "create.white_label": True,
        
        # PUBLISH
        "publish.create": True,
        "publish.marketplace": True,
        "publish.analytics": True,
        "publish.distribution": True,
        "publish.scheduling": True,
        
        # LEARN
        "learn.courses": -1,
        "learn.ai_tutor": True,
        "learn.coaching": True,
        "learn.certificates": True,
        "learn.create_courses": True,
        
        # COMMUNITY
        "community.read": True,
        "community.post": True,
        "community.create_hub": True,
        "community.moderate": True,
        "community.guild": True,
        
        # MARKETPLACE
        "marketplace.browse": True,
        "marketplace.sell": True,
        "marketplace.storefront": True,
        "marketplace.analytics": True,
        "marketplace.vendor_mgmt": True,
        
        # SANCTUARY
        "sanctuary.journal": True,
        "sanctuary.ai_reflection": True,
        "sanctuary.mood_tracking": True,
        "sanctuary.group": True,
        "sanctuary.org_wellness": False,
        
        # MUSIC
        "music.compose": True,
        "music.studio": True,
        "music.ai_production": True,
        "music.collaboration": True,
        "music.label_tools": False,
        
        # GAMES
        "games.play": True,
        "games.compete": True,
        "games.create": True,
        
        # DIRECTOR
        "director.analytics": False,
        "director.governance": False,
        "director.api": False,
        "director.compliance": False,
        
        # Resource limits
        "ai_daily_tokens": 100000,
        "storage_mb": 10000,
        "projects": -1,
        "courses": -1,
        "marketplace_fee": 0.15,
    },
    "director": {
        # AI / NAM
        "nam.chat": True,
        "nam.memory": True,
        "nam.coaching": True,
        "nam.orchestration": True,
        "nam.autonomous": True,
        
        # CREATE
        "create.projects": -1,
        "create.ai_assist": True,
        "create.advanced_formatting": True,
        "create.collaboration": True,
        "create.white_label": True,
        
        # PUBLISH
        "publish.create": True,
        "publish.marketplace": True,
        "publish.analytics": True,
        "publish.distribution": True,
        "publish.scheduling": True,
        
        # LEARN
        "learn.courses": -1,
        "learn.ai_tutor": True,
        "learn.coaching": True,
        "learn.certificates": True,
        "learn.create_courses": True,
        
        # COMMUNITY
        "community.read": True,
        "community.post": True,
        "community.create_hub": True,
        "community.moderate": True,
        "community.guild": True,
        
        # MARKETPLACE
        "marketplace.browse": True,
        "marketplace.sell": True,
        "marketplace.storefront": True,
        "marketplace.analytics": True,
        "marketplace.vendor_mgmt": True,
        
        # SANCTUARY
        "sanctuary.journal": True,
        "sanctuary.ai_reflection": True,
        "sanctuary.mood_tracking": True,
        "sanctuary.group": True,
        "sanctuary.org_wellness": True,
        
        # MUSIC
        "music.compose": True,
        "music.studio": True,
        "music.ai_production": True,
        "music.collaboration": True,
        "music.label_tools": True,
        
        # GAMES
        "games.play": True,
        "games.compete": True,
        "games.create": True,
        
        # DIRECTOR
        "director.analytics": True,
        "director.governance": True,
        "director.api": True,
        "director.compliance": True,
        
        # Resource limits
        "ai_daily_tokens": -1,  # unlimited
        "storage_mb": -1,  # unlimited
        "projects": -1,
        "courses": -1,
        "marketplace_fee": 0.10,
    },
}


# ── Tier Order ────────────────────────────────────────────────────────────────
# For comparison purposes. Higher index = higher tier.

TIER_ORDER = ["free", "creator", "pro", "studio", "director"]


# ── Core Functions ────────────────────────────────────────────────────────────

def get_user_tier(user: dict) -> str:
    """Extract the membership tier from a user document.
    
    Defaults to 'free' if no membership field exists.
    This ensures backward compatibility with existing users.
    """
    return user.get("membership", {}).get("tier", "free")


def get_tier_limits(tier: str) -> dict:
    """Get the full entitlement set for a tier.
    
    Returns the tier's configuration from TIER_LIMITS.
    Falls back to 'free' tier if the requested tier doesn't exist.
    """
    if tier not in TIER_LIMITS:
        return TIER_LIMITS["free"]
    return TIER_LIMITS[tier]


def get_user_entitlements(user: dict) -> dict:
    """Get the full entitlement set for a user.
    
    Combines the user's tier with their entitlement overrides.
    User overrides take precedence over tier defaults.
    
    Returns:
        {
            "tier": "creator",
            "capabilities": {...},  # all capability values
            "limits": {...},        # resource limits
        }
    """
    tier = get_user_tier(user)
    tier_config = get_tier_limits(tier)
    
    # Apply user-level overrides (if any)
    user_overrides = user.get("membership", {}).get("features", {})
    
    # Merge: user overrides take precedence
    capabilities = {**tier_config, **user_overrides}
    
    # Separate capabilities from resource limits
    resource_keys = {"ai_daily_tokens", "storage_mb", "projects", "courses", "marketplace_fee"}
    caps = {k: v for k, v in capabilities.items() if k not in resource_keys}
    limits = {k: v for k, v in capabilities.items() if k in resource_keys}
    
    return {
        "tier": tier,
        "capabilities": caps,
        "limits": limits,
    }


def can_access(user: dict, capability: str) -> bool:
    """Check if a user can access a specific capability.
    
    Returns True if the capability is enabled for the user's tier.
    Returns False if disabled or if the capability doesn't exist.
    """
    entitlements = get_user_entitlements(user)
    value = entitlements["capabilities"].get(capability, False)
    
    # Boolean capabilities
    if isinstance(value, bool):
        return value
    
    # Numeric capabilities (e.g., project limits)
    # A value of -1 means unlimited, 0 means disabled
    if isinstance(value, int):
        return value != 0
    
    return False


def get_limit(user: dict, resource: str) -> int:
    """Get a resource limit for a user.
    
    Returns the limit value, or 0 if the resource doesn't exist.
    A value of -1 means unlimited.
    """
    entitlements = get_user_entitlements(user)
    return entitlements["limits"].get(resource, 0)


def get_marketplace_fee(user: dict) -> float:
    """Get the marketplace fee percentage for a user's tier.
    
    Returns a float between 0.0 and 1.0.
    Free tier pays 30%, Director pays 10%.
    """
    entitlements = get_user_entitlements(user)
    return entitlements["limits"].get("marketplace_fee", 0.30)


def check_and_increment_usage(user: dict, resource: str, db, amount: int = 1) -> dict:
    """Check if a user has capacity for a resource and increment usage.
    
    Returns:
        {
            "allowed": True/False,
            "current": int,
            "limit": int,
            "remaining": int,
        }
    """
    limit = get_limit(user, resource)
    
    # Unlimited
    if limit == -1:
        return {"allowed": True, "current": 0, "limit": -1, "remaining": -1}
    
    # Get current usage from user document
    usage_key = f"usage_{resource}"
    current = user.get("membership", {}).get(usage_key, 0)
    
    if current + amount > limit:
        return {
            "allowed": False,
            "current": current,
            "limit": limit,
            "remaining": max(0, limit - current),
        }
    
    # Increment usage
    if db is not None:
        try:
            from motor.motor_asyncio import AsyncIOMotorDatabase
            if isinstance(db, AsyncIOMotorDatabase):
                import asyncio
                # This is a synchronous wrapper — actual increment happens in the route handler
                pass
        except ImportError:
            pass
    
    return {
        "allowed": True,
        "current": current + amount,
        "limit": limit,
        "remaining": max(0, limit - current - amount),
    }


def tier_index(tier: str) -> int:
    """Get the numeric index of a tier (for comparisons).
    
    Returns -1 if the tier doesn't exist.
    """
    try:
        return TIER_ORDER.index(tier)
    except ValueError:
        return -1


def is_higher_or_equal_tier(user_tier: str, required_tier: str) -> bool:
    """Check if a user's tier is at or above the required tier."""
    return tier_index(user_tier) >= tier_index(required_tier)


def get_capabilities_by_category(category: str, tier: str = None) -> dict:
    """Get all capabilities in a category, optionally filtered by tier.
    
    Useful for rendering tier comparison tables.
    """
    result = {}
    
    for cap_key, cap_info in CAPABILITIES.items():
        if cap_info["category"] != category:
            continue
        
        if tier:
            tier_config = get_tier_limits(tier)
            value = tier_config.get(cap_key, False)
            result[cap_key] = {
                **cap_info,
                "value": value,
            }
        else:
            result[cap_key] = cap_info
    
    return result


def get_tier_summary(tier: str) -> dict:
    """Get a human-readable summary of a tier's capabilities.
    
    Useful for the pricing page and admin dashboards.
    """
    config = get_tier_limits(tier)
    
    categories = {}
    for cap_key, cap_info in CAPABILITIES.items():
        cat = cap_info["category"]
        if cat not in categories:
            categories[cat] = []
        
        value = config.get(cap_key, False)
        categories[cat].append({
            "key": cap_key,
            "description": cap_info["description"],
            "enabled": bool(value) if isinstance(value, bool) else value != 0,
            "limit": value if isinstance(value, int) else None,
        })
    
    return {
        "tier": tier,
        "categories": categories,
        "limits": {k: v for k, v in config.items() if k in {
            "ai_daily_tokens", "storage_mb", "projects", "courses", "marketplace_fee"
        }},
    }


def get_all_tier_summaries() -> dict:
    """Get summaries for all tiers.
    
    Useful for the pricing page to show tier comparison.
    """
    return {tier: get_tier_summary(tier) for tier in TIER_ORDER}
