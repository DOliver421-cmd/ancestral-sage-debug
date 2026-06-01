"""
partnership/points.py — Partnership Points + Membership Tiers (backend engine).

Award points (with an append-only audit ledger), read a member's status, and compute
their tier from the Seed->Elder ladder. Used by the puzzle game: solve a puzzle ->
earn points -> rise toward a free Basic membership.

SAFETY (project rules): every DB call is wrapped — failures degrade to safe defaults
and NEVER raise into a request path. No asyncio.wait_for around Motor.
IDEMPOTENCY: an award may carry a `ref` (e.g. "puzzle:p13"); the same (user_id, ref)
is never awarded twice (checked + backed by a unique sparse index).
LEGAL/AUDIT (project rule): every award writes a ledger row for a full audit trail.
"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger("partnership.points")

POINTS_COLLECTION = "partnership_points"         # one running-total doc per user
LEDGER_COLLECTION = "partnership_points_ledger"  # append-only audit trail

# Membership ladder — 20-rung partnership progression (NAM Oshun's design).
# (name, min_points), ordered low -> high.
TIERS = [
    ("Seed I", 0),
    ("Seed II", 300),
    ("Seed III", 700),
    ("Rooted I", 1200),
    ("Rooted II", 1800),
    ("Rooted III", 2500),
    ("Builder I", 3500),
    ("Builder II", 5000),
    ("Builder III", 7000),
    ("Steward I", 9500),
    ("Steward II", 12500),
    ("Steward III", 16000),
    ("Griot", 20000),
    ("Sankofa", 25000),
    ("Ubuntu", 31000),
    ("Elder I", 38000),
    ("Elder II", 46000),
    ("Elder III", 55000),
    ("Ancestor", 65000),
    ("Sovereign", 80000),
]
# Free Basic membership stays reachable: it unlocks by POINTS (decoupled from the
# 20 tier names) so the "earn your way to a free membership" intent survives the
# longer ladder. Reaching the 2nd rung (Seed II) earns it.
MEMBERSHIP_UNLOCK_POINTS = 300


def _rank(tier_name: str) -> int:
    for i, (name, _) in enumerate(TIERS):
        if name == tier_name:
            return i
    return 0


def tier_for(points) -> dict:
    """Pure: map a point total to its tier + progress to the next tier."""
    points = max(0, int(points or 0))
    current = TIERS[0]
    nxt = None
    for i, (name, threshold) in enumerate(TIERS):
        if points >= threshold:
            current = (name, threshold)
            nxt = TIERS[i + 1] if i + 1 < len(TIERS) else None
        else:
            break
    result = {
        "points": points,
        "tier": current[0],
        "tier_min": current[1],
        "membership_unlocked": points >= MEMBERSHIP_UNLOCK_POINTS,
        "next_tier": nxt[0] if nxt else None,
        "points_to_next": max(0, nxt[1] - points) if nxt else 0,
    }
    return result


async def ensure_indexes(db) -> None:
    """Idempotent indexes. Call from on_startup (caller wraps in try/except)."""
    if db is None:
        return
    try:
        await db[POINTS_COLLECTION].create_index("user_id", unique=True)
        await db[LEDGER_COLLECTION].create_index(
            [("user_id", 1), ("ref", 1)], unique=True, sparse=True
        )
    except Exception as e:
        logger.error(f"partnership ensure_indexes failed: {e}")


async def get_points(db, user_id: str) -> int:
    if db is None or not user_id:
        return 0
    try:
        doc = await db[POINTS_COLLECTION].find_one({"user_id": user_id}, {"_id": 0, "points": 1})
        return int((doc or {}).get("points", 0) or 0)
    except Exception as e:
        logger.error(f"partnership get_points failed: {e}")
        return 0


async def get_status(db, user_id: str) -> dict:
    return tier_for(await get_points(db, user_id))


async def award_points(db, user_id: str, amount: int, reason: str, ref: str = None) -> dict:
    """Award points; return new status. Idempotent when `ref` is given. Never raises."""
    status = await get_status(db, user_id)
    if db is None or not user_id or not amount or int(amount) <= 0:
        return {**status, "awarded": 0, "duplicate": False}
    amount = int(amount)
    entry = {"user_id": user_id, "amount": amount, "reason": reason,
             "ts": datetime.now(timezone.utc)}
    if ref:
        entry["ref"] = ref

    # Insert the audit-ledger row FIRST. The unique (user_id, ref) index makes this the
    # race-free idempotency gate: a duplicate ref -> DuplicateKeyError -> no double award.
    try:
        await db[LEDGER_COLLECTION].insert_one(entry)
    except Exception as e:
        if ref and (type(e).__name__ == "DuplicateKeyError" or "duplicate key" in str(e).lower()):
            return {**status, "awarded": 0, "duplicate": True}
        logger.error(f"partnership ledger insert failed: {e}")
        return {**status, "awarded": 0, "duplicate": False}

    try:
        await db[POINTS_COLLECTION].update_one(
            {"user_id": user_id},
            {"$inc": {"points": amount}, "$set": {"updated_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
    except Exception as e:
        logger.error(f"partnership increment failed: {e}")
        return {**status, "awarded": 0, "duplicate": False}

    new_status = await get_status(db, user_id)
    new_status.update({"awarded": amount, "duplicate": False})
    return new_status
