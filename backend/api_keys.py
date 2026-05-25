"""
API Key management for WAI API-as-a-Service.
Supports tiered rate limits, key revocation, and usage tracking.
"""

import hashlib
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("lcewai.api_keys")

TIERS = {
    "free":    {"requests_per_hour": 100,   "max_tokens_per_call": 1024,  "models": ["claude-haiku-4-5"]},
    "starter": {"requests_per_hour": 1000,  "max_tokens_per_call": 4096,  "models": ["claude-haiku-4-5"]},
    "pro":     {"requests_per_hour": 10000, "max_tokens_per_call": 8192,  "models": ["claude-haiku-4-5", "claude-sonnet-4-6"]},
    "enterprise": {"requests_per_hour": 100000, "max_tokens_per_call": 16384, "models": ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-5"]},
}


def generate_key() -> str:
    """Generate a scoped API key: wai_ prefix for easy identification."""
    return f"wai_{secrets.token_hex(32)}"


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def create_api_key(db, label: str, tier: str, user_id: str) -> dict:
    """Create a new API key for external access."""
    if tier not in TIERS:
        raise ValueError(f"Invalid tier: {tier}. Valid: {list(TIERS.keys())}")
    raw = generate_key()
    doc = {
        "key_hash": hash_key(raw),
        "label": label,
        "tier": tier,
        "user_id": user_id,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used_at": None,
        "usage_count": 0,
        "rate_window": [],
    }
    await db.api_keys.insert_one(doc)
    return {"key": raw, "label": label, "tier": tier}


async def list_api_keys(db, user_id: str) -> list:
    """List keys (without the raw key — hash only)."""
    cursor = db.api_keys.find(
        {"user_id": user_id},
        {"_id": 0, "key_hash": 1, "label": 1, "tier": 1, "active": 1,
         "created_at": 1, "last_used_at": 1, "usage_count": 1},
    ).sort("created_at", -1)
    return await cursor.to_list(length=50)


async def revoke_api_key(db, key_hash: str, user_id: str) -> bool:
    """Revoke an API key."""
    result = await db.api_keys.update_one(
        {"key_hash": key_hash, "user_id": user_id},
        {"$set": {"active": False}},
    )
    return result.modified_count > 0


async def verify_api_key(db, raw_key: str) -> Optional[dict]:
    """Verify a raw API key and return tier info. None if invalid."""
    kh = hash_key(raw_key)
    doc = await db.api_keys.find_one({"key_hash": kh, "active": True}, {"_id": 0})
    if not doc:
        return None
    tier_config = TIERS.get(doc["tier"], TIERS["free"])

    # Rate limit check (sliding window)
    now = datetime.now(timezone.utc).timestamp()
    window_start = now - 3600
    doc["rate_window"] = [t for t in doc.get("rate_window", []) if t > window_start]
    if len(doc["rate_window"]) >= tier_config["requests_per_hour"]:
        return {"error": "rate_limit_exceeded", "tier": doc["tier"], "limit": tier_config["requests_per_hour"]}

    # Update usage
    doc["rate_window"].append(now)
    await db.api_keys.update_one(
        {"key_hash": kh},
        {"$set": {"last_used_at": datetime.now(timezone.utc).isoformat(), "rate_window": doc["rate_window"]},
         "$inc": {"usage_count": 1}},
    )
    return {
        "valid": True,
        "tier": doc["tier"],
        "label": doc["label"],
        "limits": tier_config,
    }


async def get_usage_stats(db, user_id: str) -> dict:
    """Get aggregate usage stats for all keys owned by user."""
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$tier",
            "count": {"$sum": 1},
            "total_usage": {"$sum": "$usage_count"},
            "active": {"$sum": {"$cond": ["$active", 1, 0]}},
        }},
    ]
    cursor = db.api_keys.aggregate(pipeline)
    tiers = await cursor.to_list(length=10)
    total_keys = await db.api_keys.count_documents({"user_id": user_id})
    return {"total_keys": total_keys, "by_tier": tiers}
