"""
verify_new_engines.py — self-contained verification + stress test for the new
Sovereign / partnership-points / puzzle engines.

Runs WITHOUT a database, without secrets, without any Claude API calls. It uses an
in-memory async Mongo fake that enforces unique indexes, so idempotency and the full
solve loop are tested for real.

Run:  cd backend && python verify_new_engines.py
"""
import asyncio
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from partnership import points as P          # noqa: E402
from puzzles import engine as E              # noqa: E402
from sovereign.sovereign_loader import get_sovereign_prompt, build_sovereign_prompt  # noqa: E402


# ───────────────────────── in-memory async Mongo fake ─────────────────────────
class DuplicateKeyError(Exception):
    pass


def _match(doc, filt):
    return all(doc.get(k) == v for k, v in filt.items())


def _set_dotted(doc, key, val):
    parts = key.split(".")
    d = doc
    for p in parts[:-1]:
        d = d.setdefault(p, {})
    d[parts[-1]] = val


class _Cursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, key, direction=1):
        self._docs.sort(key=lambda d: d.get(key), reverse=(direction == -1))
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length=None):
        return self._docs if length is None else self._docs[:length]


class Coll:
    def __init__(self):
        self.docs = []
        self.indexes = []  # (fields, unique, sparse)

    async def create_index(self, keys, unique=False, sparse=False, **kw):
        fields = [keys] if isinstance(keys, str) else [k for k, _ in keys]
        self.indexes.append((fields, unique, sparse))
        return "idx"

    def _violates(self, doc):
        for fields, unique, sparse in self.indexes:
            if not unique:
                continue
            if sparse and any(f not in doc for f in fields):
                continue
            key = tuple(doc.get(f) for f in fields)
            for d in self.docs:
                if tuple(d.get(f) for f in fields) == key:
                    return True
        return False

    async def find_one(self, filt, projection=None):
        for d in self.docs:
            if _match(d, filt):
                return copy.deepcopy(d)
        return None

    def find(self, filt=None, projection=None):
        filt = filt or {}
        return _Cursor([copy.deepcopy(d) for d in self.docs if _match(d, filt)])

    async def insert_one(self, doc):
        if self._violates(doc):
            raise DuplicateKeyError("E11000 duplicate key error")
        self.docs.append(copy.deepcopy(doc))
        return type("R", (), {"inserted_id": len(self.docs)})()

    async def update_one(self, filt, update, upsert=False):
        target = next((d for d in self.docs if _match(d, filt)), None)
        inserted = False
        if target is None:
            if not upsert:
                return
            target = dict(filt)
            self.docs.append(target)
            inserted = True
        if inserted and "$setOnInsert" in update:
            for k, v in update["$setOnInsert"].items():
                _set_dotted(target, k, v)
        if "$set" in update:
            for k, v in update["$set"].items():
                _set_dotted(target, k, v)
        if "$inc" in update:
            for k, v in update["$inc"].items():
                target[k] = target.get(k, 0) + v
        if "$addToSet" in update:
            for k, v in update["$addToSet"].items():
                arr = target.setdefault(k, [])
                if v not in arr:
                    arr.append(v)

    async def delete_many(self, filt):
        before = len(self.docs)
        self.docs = [d for d in self.docs if not _match(d, filt)]
        return type("R", (), {"deleted_count": before - len(self.docs)})()


class DB:
    def __init__(self):
        self.c = {}

    def __getitem__(self, name):
        return self.c.setdefault(name, Coll())


async def main():
    db = DB()
    await P.ensure_indexes(db)

    # ── partnership: pure tier math ──
    assert P.tier_for(0)["tier"] == "Seed"
    assert P.tier_for(99)["tier"] == "Seed"
    r = P.tier_for(100)
    assert r["tier"] == "Rooted" and r["membership_unlocked"] is True
    assert P.tier_for(2500)["tier"] == "Elder" and P.tier_for(2500)["next_tier"] is None
    t = P.tier_for(250)
    assert t["next_tier"] == "Builder" and t["points_to_next"] == 50

    # ── partnership: award + idempotency + audit ──
    s = await P.award_points(db, "u1", 100, "test", ref="r1")
    assert s["awarded"] == 100 and s["tier"] == "Rooted"
    s = await P.award_points(db, "u1", 100, "test", ref="r1")  # same ref -> ignored
    assert s["awarded"] == 0 and s["duplicate"] and s["points"] == 100
    s = await P.award_points(db, "u1", 50, "noref")            # no ref -> allowed
    assert s["points"] == 150
    assert await P.get_points(db, "u1") == 150
    # audit ledger has the rows
    assert len(db["partnership_points_ledger"].docs) == 2

    # ── puzzles: pure ──
    assert E.check_answer(E._by_id("p13"), "manhood")       # caesar decode
    assert E.check_answer(E._by_id("p15"), "Sovereign!")    # unscramble + punctuation
    assert E.check_answer(E._by_id("p10"), "  A  GRIOT ")   # normalization
    assert not E.check_answer(E._by_id("p1"), "")
    assert E.level_for(0) == 1 and E.level_for(2) == 2 and E.level_for(999) == E.MAX_LEVEL
    assert E.pick_next(1, []) is not None
    assert E.pick_next(1, [p["id"] for p in E._BANK]) is None  # all solved
    assert "answers" not in E._public(E._by_id("p1"), 0)       # answer never leaks

    # ── puzzles: flow (wrong -> hint -> correct -> idempotent) ──
    r = await E.submit_answer(db, "u2", "p1", "nope")
    assert r["correct"] is False and r["hint"]
    r = await E.submit_answer(db, "u2", "p1", "candle")
    assert r["correct"] and r["points_awarded"] == 10
    r = await E.submit_answer(db, "u2", "p1", "candle")        # resubmit -> no double award
    assert r["correct"] and r["points_awarded"] == 0 and r["duplicate"]
    assert await P.get_points(db, "u2") == 10
    # anonymous solve earns nothing
    r = await E.submit_answer(db, None, "p2", "piano")
    assert r["correct"] and r["points_awarded"] == 0 and r["requires_login_to_earn"]

    # ── stress: one user solves the entire bank, totals must match ──
    answers = {p["id"]: p["answers"][0] for p in E._BANK}
    total = sum(p["points"] for p in E._BANK)
    for pid, ans in answers.items():
        assert (await E.submit_answer(db, "u3", pid, ans))["correct"]
    for pid, ans in answers.items():            # resubmit all -> no extra points
        await E.submit_answer(db, "u3", pid, ans)
    pts = await P.get_points(db, "u3")
    assert pts == total, (pts, total)
    assert (await E.next_puzzle(db, "u3"))["done"] is True

    # ── concurrency stress: 50 simultaneous awards of the same ref -> exactly one ──
    await asyncio.gather(*[P.award_points(db, "u4", 10, "x", ref="same") for _ in range(50)])
    assert await P.get_points(db, "u4") == 10, await P.get_points(db, "u4")

    # ── sovereign prompt assembles, memory injects, identity is male ──
    base = get_sovereign_prompt()
    assert "Black manhood" in base and "womanhood" not in base.lower()
    withmem = get_sovereign_prompt("WHAT YOU REMEMBER: he prefers HBCU bookings.")
    assert "HBCU" in withmem and len(withmem) > len(base)
    assert (await build_sovereign_prompt(None, "exec")) == base  # no-db safe

    print("ALL ENGINE + STRESS TESTS PASSED")
    print(f"  bank size={len(E._BANK)}  max points={total}  u3 tier={P.tier_for(pts)['tier']}")


if __name__ == "__main__":
    asyncio.run(main())
