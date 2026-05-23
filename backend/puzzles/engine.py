"""
puzzles/engine.py — escalating puzzle game that awards partnership points.

- Built-in BANK across levels 1..MAX_LEVEL (easy -> hard, escalating).
- next_puzzle(): serve the next unsolved puzzle at the member's current level.
- submit_answer(): verify SERVER-SIDE; on success award points once (idempotent via
  ref="puzzle:<id>") and advance; on failure reveal the next hint.
- "Never impossible": every puzzle ships with a solution + progressive hints; the top
  level is still solvable from its hints.
- The answer is NEVER sent to the client. Points require a logged-in user_id
  (anonymous visitors can view/attempt, but must register to bank points).

SAFETY: db wrappers guard all failures; pure helpers are deterministic + unit-tested.
"""
import logging
import re

from partnership import points as points_engine

logger = logging.getLogger("puzzles.engine")

PROGRESS_COLLECTION = "puzzle_progress"
MAX_LEVEL = 5
SOLVES_PER_LEVEL = 2  # solves needed to advance a level (capped at MAX_LEVEL)

# Escalating bank. Themed to NAM Oshun's culture at the higher levels.
_BANK = [
    # ---- Level 1 (easy) ----
    {"id": "p1", "level": 1, "points": 10,
     "question": "I'm tall when I'm young and short when I'm old. What am I?",
     "answers": ["candle", "a candle"], "hints": ["You light me.", "I melt over time."]},
    {"id": "p2", "level": 1, "points": 10,
     "question": "What has keys but can't open locks?",
     "answers": ["piano", "a piano", "keyboard", "a keyboard"], "hints": ["You play me.", "Black and white keys."]},
    {"id": "p3", "level": 1, "points": 10,
     "question": "What gets wetter the more it dries?",
     "answers": ["towel", "a towel"], "hints": ["You reach for me after a shower."]},
    # ---- Level 2 ----
    {"id": "p4", "level": 2, "points": 20,
     "question": "The more you take, the more you leave behind. What are they?",
     "answers": ["footsteps", "steps", "footprints"], "hints": ["You make them as you walk."]},
    {"id": "p5", "level": 2, "points": 20,
     "question": "What word becomes shorter when you add two letters to it?",
     "answers": ["short", "shorter"], "hints": ["Add the letters 'e' and 'r'."]},
    {"id": "p6", "level": 2, "points": 20,
     "question": "What has a head and a tail but no body?",
     "answers": ["coin", "a coin"], "hints": ["You flip me to decide."]},
    # ---- Level 3 ----
    {"id": "p7", "level": 3, "points": 35,
     "question": "Multiply all the numbers on a phone keypad together. What do you get?",
     "answers": ["0", "zero"], "hints": ["There is a zero on the keypad."]},
    {"id": "p8", "level": 3, "points": 35,
     "question": "Six letters it contains; remove one and twelve remains. What word?",
     "answers": ["dozens"], "hints": ["Twelve = a dozen."]},
    {"id": "p9", "level": 3, "points": 35,
     "question": "Forward I am heavy, backward I am not. What am I?",
     "answers": ["ton", "a ton"], "hints": ["Reverse the letters of the word."]},
    # ---- Level 4 (hard, themed) ----
    {"id": "p10", "level": 4, "points": 50,
     "question": "A West African keeper of oral history, central to NAM Oshun's lineage — a 5-letter word for a poet-storyteller of the people. What is it?",
     "answers": ["griot", "a griot"], "hints": ["The tradition NAM Oshun carries.", "Starts with G."]},
    {"id": "p11", "level": 4, "points": 50,
     "question": "Ubuntu, in one word: 'I am because ___ are.'",
     "answers": ["we", "we are"], "hints": ["Community over self.", "Two letters."]},
    {"id": "p12", "level": 4, "points": 50,
     "question": "The Yoruba orisha of love, beauty, rivers, and art — a name carried with intention. Who?",
     "answers": ["oshun"], "hints": ["Yoruba lineage.", "NAM ___."]},
    # ---- Level 5 (hardest, still solvable from hints) ----
    {"id": "p13", "level": 5, "points": 75,
     "question": "Caesar cipher, shift each letter back by 3: 'PDQKRRG'. What word?",
     "answers": ["manhood"], "hints": ["P->M, D->A, Q->N ...", "It's what everything here is about."]},
    {"id": "p14", "level": 5, "points": 75,
     "question": "Planted by elders who will never sit in its shade. What am I? (one word)",
     "answers": ["tree", "a tree", "seed", "a seed"], "hints": ["Also the first rung of the partnership ladder.", "Seed -> ... -> Elder."]},
    {"id": "p15", "level": 5, "points": 75,
     "question": "Unscramble 'NEVARGOSI' — a 9-letter word for self-rule; one who answers only to conscience.",
     "answers": ["sovereign"], "hints": ["This very persona's name.", "Starts with S, ends with N."]},
]


def _norm(s: str) -> str:
    """Normalize an answer: lowercase, drop punctuation, collapse whitespace."""
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _by_id(pid: str):
    return next((p for p in _BANK if p["id"] == pid), None)


def check_answer(puzzle: dict, answer: str) -> bool:
    """Pure: is `answer` acceptable for `puzzle`?"""
    if not puzzle:
        return False
    a = _norm(answer)
    return bool(a) and any(a == _norm(x) for x in puzzle.get("answers", []))


def level_for(solved_count: int) -> int:
    """Pure: current level from number of puzzles solved (capped)."""
    return max(1, min(MAX_LEVEL, 1 + int(solved_count or 0) // SOLVES_PER_LEVEL))


def pick_next(level: int, solved_ids) -> dict:
    """Pure: next unsolved puzzle at `level`; climb up, then fall back; None if all solved."""
    solved = set(solved_ids or [])
    level = max(1, min(MAX_LEVEL, int(level or 1)))
    order = list(range(level, MAX_LEVEL + 1)) + list(range(level - 1, 0, -1))
    for lvl in order:
        for p in _BANK:
            if p["level"] == lvl and p["id"] not in solved:
                return p
    return None


def _public(puzzle: dict, hints_shown: int = 0) -> dict:
    """Strip the answer; expose question + already-revealed hints only."""
    if not puzzle:
        return {}
    hints = puzzle.get("hints", [])
    return {
        "id": puzzle["id"],
        "level": puzzle["level"],
        "points": puzzle["points"],
        "question": puzzle["question"],
        "hints_shown": hints[:max(0, hints_shown)],
        "hints_available": len(hints),
    }


async def _get_progress(db, user_id: str) -> dict:
    default = {"solved": [], "level": 1, "attempts": {}}
    if db is None or not user_id:
        return default
    try:
        doc = await db[PROGRESS_COLLECTION].find_one({"user_id": user_id}, {"_id": 0})
    except Exception as e:
        logger.error(f"puzzle _get_progress failed: {e}")
        return default
    if not doc:
        return default
    doc.setdefault("solved", [])
    doc.setdefault("attempts", {})
    doc["level"] = level_for(len(doc["solved"]))
    return doc


async def next_puzzle(db, user_id: str) -> dict:
    """Serve the next unsolved puzzle for the user (or anonymous if user_id is None)."""
    prog = await _get_progress(db, user_id)
    level = level_for(len(prog["solved"]))
    p = pick_next(level, prog["solved"])
    if not p:
        return {"done": True, "level": level, "solved_count": len(prog["solved"]),
                "message": "You've solved them all. The Sovereign bows to you."}
    shown = int((prog.get("attempts") or {}).get(p["id"], 0))
    return {"done": False, "level": level, "solved_count": len(prog["solved"]),
            "requires_login_to_earn": not bool(user_id),
            "puzzle": _public(p, hints_shown=shown)}


async def submit_answer(db, user_id: str, puzzle_id: str, answer: str) -> dict:
    """Verify an answer; award points once on success. Points require a logged-in user."""
    p = _by_id(puzzle_id)
    if not p:
        return {"error": "unknown_puzzle"}

    prog = await _get_progress(db, user_id)
    attempts_map = dict(prog.get("attempts") or {})
    attempts = int(attempts_map.get(puzzle_id, 0)) + 1
    attempts_map[puzzle_id] = attempts

    if not check_answer(p, answer):
        hints = p.get("hints", [])
        shown = min(len(hints), attempts)  # reveal one more hint each miss (never impossible)
        if db is not None and user_id:
            try:
                await db[PROGRESS_COLLECTION].update_one(
                    {"user_id": user_id},
                    {"$set": {f"attempts.{puzzle_id}": attempts},
                     "$setOnInsert": {"solved": []}},
                    upsert=True,
                )
            except Exception as e:
                logger.error(f"puzzle attempt persist failed: {e}")
        return {"correct": False, "try_again": True,
                "hint": hints[shown - 1] if 0 < shown <= len(hints) else None,
                "hints_shown": hints[:shown]}

    # Correct answer.
    if not user_id:
        # Anonymous solve: confirm, but no points until they register.
        return {"correct": True, "requires_login_to_earn": True, "points_awarded": 0,
                "message": "Correct! Create a free account to bank these points toward membership."}

    already = puzzle_id in set(prog.get("solved", []))
    if db is not None:
        try:
            await db[PROGRESS_COLLECTION].update_one(
                {"user_id": user_id},
                {"$addToSet": {"solved": puzzle_id},
                 "$set": {f"attempts.{puzzle_id}": attempts}},
                upsert=True,
            )
        except Exception as e:
            logger.error(f"puzzle solved persist failed: {e}")

    award = await points_engine.award_points(
        db, user_id, p["points"], reason=f"puzzle:{puzzle_id}", ref=f"puzzle:{puzzle_id}"
    )
    new_solved = set(prog.get("solved", [])) | {puzzle_id}
    return {
        "correct": True,
        "already_solved": already,
        "points_awarded": award.get("awarded", 0),
        "duplicate": award.get("duplicate", False),
        "status": {k: award.get(k) for k in
                   ("points", "tier", "next_tier", "points_to_next", "membership_unlocked")},
        "next_level": level_for(len(new_solved)),
    }
