"""
Per-persona AI cost tracking.
Tracks token usage and estimated cost per persona per day.
Stores in MongoDB collection `ai_costs`.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.ai_cost_tracker")

# Approximate cost per 1K tokens (USD) — update when model pricing changes
_MODEL_RATES = {
    "claude-sonnet-4-6":        {"input": 0.003, "output": 0.015},
    "claude-haiku-4-5":         {"input": 0.0008, "output": 0.004},
    "claude-haiku-4-5-20251001": {"input": 0.0008, "output": 0.004},
    "claude-3-haiku-20240307":  {"input": 0.00025, "output": 0.00125},
}

DEFAULT_RATE = {"input": 0.002, "output": 0.010}


async def record_ai_call(
    db,
    persona: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    user_id: str = None,
    endpoint: str = None,
):
    """Record an AI call for cost tracking."""
    rate = _MODEL_RATES.get(model, DEFAULT_RATE)
    estimated_cost = (input_tokens / 1000 * rate["input"]) + (output_tokens / 1000 * rate["output"])
    entry = {
        "persona": persona,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost": round(estimated_cost, 6),
        "user_id": user_id,
        "endpoint": endpoint,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await db.ai_costs.insert_one(entry)
    except Exception as e:
        logger.warning("cost_tracker: insert failed — %s", e)


async def get_persona_costs(db, persona: str = None, days: int = 7) -> list:
    """Get cost summary per persona for the last N days."""
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    match = {"created_at": {"$gte": cutoff}}
    if persona:
        match["persona"] = persona
    try:
        cursor = db.ai_costs.aggregate([
            {"$match": match},
            {"$group": {
                "_id": "$persona",
                "total_calls": {"$sum": 1},
                "total_tokens": {"$sum": "$total_tokens"},
                "total_cost": {"$sum": "$estimated_cost"},
                "models": {"$addToSet": "$model"},
            }},
            {"$sort": {"total_cost": -1}},
        ])
        return await cursor.to_list(length=50)
    except Exception as e:
        logger.warning("cost_tracker: aggregate failed — %s", e)
        return []


async def get_total_cost(db, days: int = 30) -> dict:
    """Get total AI cost for the last N days."""
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        cursor = db.ai_costs.aggregate([
            {"$match": {"created_at": {"$gte": cutoff}}},
            {"$group": {
                "_id": None,
                "total_calls": {"$sum": 1},
                "total_tokens": {"$sum": "$total_tokens"},
                "total_cost": {"$sum": "$estimated_cost"},
            }},
        ])
        result = await cursor.to_list(length=1)
        if result:
            return result[0]
        return {"total_calls": 0, "total_tokens": 0, "total_cost": 0}
    except Exception as e:
        logger.warning("cost_tracker: total cost failed — %s", e)
        return {"total_calls": 0, "total_tokens": 0, "total_cost": 0}
