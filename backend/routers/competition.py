"""routers/competition.py — The Arena: 5-persona AI competition system (LIVE).

Restores the competition endpoints on the live backend. The original implementation
lived only in the dead `app/` tree (app/routes/competition.py) and was never wired
into the deployed server — the frontend `/arena` page called endpoints that 404'd.

Endpoints:
  POST /competition/task        — Commissioner assigns task, all 4 compete, scores
  POST /competition/score       — User submits their score for each result
  GET  /competition/leaderboard — Cumulative scores ranked with role assignments
  GET  /competition/projects    — All active projects with round status
  GET  /competition/ping        — Public liveness check

Notes:
  - AI calls route through the free-first `call_llm()` gateway (Groq → Cerebras →
    … → KB fallback) so no paid provider is ever called directly and keys set in
    the Provider Gateway UI are honored.
  - Access is admin+ (matches the frontend `<BoundedAdmin roles={["admin"]}>`).
  - MongoDB collection: competition_rounds

Shared state (db, current_user, audit, assert_role, xp_level) is bound by
server.py via bind() at include time — no circular imports.
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, ConfigDict, Field

from competition_personas import (
    COMMISSIONER_SYSTEM_PROMPT,
    MAX_RETRIES,
    PASS_THRESHOLD,
    PERSONA_PROMPTS,
    PERSONA_TAGLINES,
    TOTAL_ROUNDS,
)

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["competition"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = audit = assert_role = xp_level = None


def bind(_db, _current_user, _audit, _assert_role, _xp_level):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, assert_role, xp_level
    db = _db
    current_user = _current_user
    audit = _audit
    assert_role = _assert_role
    xp_level = _xp_level


# Mirrors server.py's role hierarchy for runtime require_role checks.
ROLE_RANK = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4, "creative_partner": 2}
Role = Literal["student", "instructor", "admin", "executive_admin", "creative_partner"]


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: Role = "student"
    associate: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    avatar_url: Optional[str] = None
    feature_tier: str = "free"


async def _dep_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Resolve the real current_user at REQUEST time (bind() sets it after import)."""
    return await current_user(authorization)


def _require_rank(*roles):
    """Runtime equivalent of server.py's require_role() — used in Depends()
    because require_role is bound after this module loads (no import-time call)."""
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: User = Depends(_dep_current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            logger.warning(
                "Unauthorized Arena access attempt (user=%s, role=%s)",
                user.id, user.role,
            )
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


# ── Pydantic models ───────────────────────────────────────────────────────────

class TaskRequest(BaseModel):
    task: str
    project_id: Optional[str] = None
    round_number: Optional[int] = None


class UserScoreEntry(BaseModel):
    round_id: str
    user_score: int  # 1-100


class UserScoreRequest(BaseModel):
    scores: list[UserScoreEntry]


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _call_ai(system_prompt: str, user_message: str) -> str:
    """Call AI through the free-first gateway (Groq → Cerebras → … → KB fallback).

Returns the response text. Raises HTTP 503 only if the gateway yields no usable
text at all.
    """
    try:
        from ai.llm_gateway import call_llm as _call_llm
        result = await _call_llm(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=4096,
            persona_label="arena",
        )
    except Exception as e:  # noqa: BLE001 - gateway must never crash the Arena
        logger.error("Arena gateway call failed: %s", e)
        raise HTTPException(status_code=503, detail="AI gateway unavailable. Check provider keys in the Provider Gateway.")

    text = (result or {}).get("text", "")
    if not text:
        raise HTTPException(
            status_code=503,
            detail="No AI provider available. Add a free provider key (e.g. GROQ_API_KEY) in the Provider Gateway.",
        )
    return text


async def _score_output(persona_name: str, task: str, output: str) -> dict:
    """Have Commissioner score a persona's output. Returns parsed score dict."""
    score_prompt = (
        f"The task given to {persona_name} was:\n\n{task}\n\n"
        f"Here is {persona_name}'s submission:\n\n{output}\n\n"
        "Score this submission now using your rubric. Return only the JSON object."
    )
    raw = await _call_ai(COMMISSIONER_SYSTEM_PROMPT, score_prompt)
    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Commissioner returned non-JSON score for %s: %s", persona_name, raw[:200])
        return {
            "score": 50,
            "verdict": "REJECT",
            "feedback": "Commissioner could not parse its own scoring output. Treating as rejection.",
            "strengths": [],
            "weaknesses": ["Scoring parse failure"],
        }


async def _run_persona(persona_name: str, task: str) -> dict:
    """Run a single persona's task with retry logic. Returns result dict."""
    system_prompt = PERSONA_PROMPTS[persona_name]
    output = None
    commissioner_result = None
    attempts = 0
    revision_context = task

    while attempts < MAX_RETRIES:
        attempts += 1
        try:
            output = await _call_ai(system_prompt, revision_context)
        except HTTPException as e:
            logger.error("AI call failed for %s attempt %d: %s", persona_name, attempts, e.detail)
            output = f"[{persona_name} failed to produce output after {attempts} attempt(s).]"
            break

        commissioner_result = await _score_output(persona_name, task, output)
        score = commissioner_result.get("score", 0)
        verdict = commissioner_result.get("verdict", "REJECT")

        if verdict == "PASS" and score >= PASS_THRESHOLD:
            break

        # Below threshold — prepare revision prompt with feedback
        feedback = commissioner_result.get("feedback", "")
        weaknesses = commissioner_result.get("weaknesses", [])
        weakness_text = "\n".join(f"- {w}" for w in weaknesses)
        revision_context = (
            f"Your original task:\n{task}\n\n"
            f"THE COMMISSIONER rejected your submission (score: {score}/100).\n"
            f"Feedback: {feedback}\n"
            f"Weaknesses to fix:\n{weakness_text}\n\n"
            "Revise and resubmit. Produce a complete, finished product that addresses all feedback."
        )

    return {
        "persona": persona_name,
        "tagline": PERSONA_TAGLINES[persona_name],
        "output": output or "[No output produced.]",
        "commissioner_score": commissioner_result.get("score", 0) if commissioner_result else 0,
        "commissioner_verdict": commissioner_result.get("verdict", "REJECT") if commissioner_result else "REJECT",
        "commissioner_feedback": commissioner_result.get("feedback", "") if commissioner_result else "",
        "commissioner_strengths": commissioner_result.get("strengths", []) if commissioner_result else [],
        "commissioner_weaknesses": commissioner_result.get("weaknesses", []) if commissioner_result else [],
        "attempts": attempts,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/competition/ping")
async def competition_ping():
    """Public liveness check — confirms competition routes are registered."""
    return {"status": "ok", "module": "competition"}


@router.post("/competition/task")
async def assign_task(
    body: TaskRequest,
    user: User = Depends(_require_rank("admin")),
):
    """Commissioner assigns a task to all 4 personas sequentially. Returns all results."""
    if not body.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty.")

    project_id = body.project_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Determine round number for this project
    if body.round_number:
        round_number = body.round_number
    else:
        existing_rounds = await db.competition_rounds.count_documents({"project_id": project_id})
        # Each round has 4 entries (one per persona)
        round_number = (existing_rounds // 4) + 1

    if round_number > TOTAL_ROUNDS:
        raise HTTPException(status_code=400, detail=f"Maximum {TOTAL_ROUNDS} rounds per project reached.")

    # Run each persona sequentially to avoid rate limits
    results = []
    for persona_name in ["AXIOM", "CIPHER", "MAVEN", "SAGE"]:
        result = await _run_persona(persona_name, body.task)
        results.append(result)

    # Persist all results to MongoDB
    inserted_ids = []
    for result in results:
        doc = {
            "project_id": project_id,
            "round_number": round_number,
            "task": body.task,
            "persona": result["persona"],
            "tagline": result["tagline"],
            "output": result["output"],
            "commissioner_score": result["commissioner_score"],
            "commissioner_verdict": result["commissioner_verdict"],
            "commissioner_feedback": result["commissioner_feedback"],
            "commissioner_strengths": result["commissioner_strengths"],
            "commissioner_weaknesses": result["commissioner_weaknesses"],
            "attempts": result["attempts"],
            "user_score": None,
            "average_score": None,
            "timestamp": now,
            "created_by": str(user.id) if hasattr(user, "id") else user.get("_id", ""),
        }
        round_id = str(uuid.uuid4())
        doc["round_id"] = round_id
        await db.competition_rounds.insert_one(doc)
        inserted_ids.append(round_id)

    # Build response with round IDs for subsequent scoring
    response_results = []
    for i, result in enumerate(results):
        response_results.append({
            "round_id": inserted_ids[i],
            **result,
        })

    return {
        "project_id": project_id,
        "round_number": round_number,
        "task": body.task,
        "results": response_results,
    }


@router.post("/competition/score")
async def submit_user_scores(
    body: UserScoreRequest,
    user: User = Depends(_require_rank("admin")),
):
    """User submits scores (1-100) for each result. Averages with Commissioner score."""
    updated = []
    for entry in body.scores:
        if not (1 <= entry.user_score <= 100):
            raise HTTPException(status_code=400, detail=f"Score must be 1-100, got {entry.user_score}.")

        doc = await db.competition_rounds.find_one({"round_id": entry.round_id})
        if not doc:
            raise HTTPException(status_code=404, detail=f"Round {entry.round_id} not found.")

        commissioner_score = doc.get("commissioner_score", 0)
        average_score = (commissioner_score + entry.user_score) / 2

        await db.competition_rounds.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "user_score": entry.user_score,
                "average_score": average_score,
            }},
        )
        updated.append({
            "round_id": entry.round_id,
            "persona": doc["persona"],
            "user_score": entry.user_score,
            "commissioner_score": commissioner_score,
            "average_score": average_score,
        })

    return {"updated": updated}


@router.get("/competition/leaderboard")
async def get_leaderboard(
    user: User = Depends(_require_rank("admin")),
):
    """Returns cumulative average scores for all personas, ranked, with role badges."""
    personas = list(PERSONA_PROMPTS.keys())

    leaderboard = []
    for persona_name in personas:
        rounds = await db.competition_rounds.find(
            {"persona": persona_name, "average_score": {"$ne": None}}
        ).to_list(length=500)

        if not rounds:
            leaderboard.append({
                "persona": persona_name,
                "tagline": PERSONA_TAGLINES[persona_name],
                "cumulative_average": 0.0,
                "rounds_completed": 0,
                "role": "competitor",
            })
            continue

        total = sum(r["average_score"] for r in rounds)
        rounds_completed = len(set(r["round_number"] for r in rounds))
        cumulative_avg = total / len(rounds)

        leaderboard.append({
            "persona": persona_name,
            "tagline": PERSONA_TAGLINES[persona_name],
            "cumulative_average": round(cumulative_avg, 2),
            "rounds_completed": rounds_completed,
            "role": "competitor",  # assigned below
        })

    # Sort descending by cumulative average
    leaderboard.sort(key=lambda x: x["cumulative_average"], reverse=True)

    # Assign roles only after all TOTAL_ROUNDS are done
    max_rounds = max((p["rounds_completed"] for p in leaderboard), default=0)
    if max_rounds >= TOTAL_ROUNDS:
        for i, entry in enumerate(leaderboard):
            if i < 2:
                entry["role"] = "lead"
            else:
                entry["role"] = "support"
    else:
        for entry in leaderboard:
            entry["role"] = "competitor"

    return {
        "leaderboard": leaderboard,
        "total_rounds": TOTAL_ROUNDS,
        "competition_complete": max_rounds >= TOTAL_ROUNDS,
    }


@router.get("/competition/projects")
async def get_projects(
    user: User = Depends(_require_rank("admin")),
):
    """Returns all active projects with current round and status."""
    pipeline = [
        {
            "$group": {
                "_id": "$project_id",
                "latest_round": {"$max": "$round_number"},
                "latest_task": {"$last": "$task"},
                "latest_timestamp": {"$max": "$timestamp"},
                "total_entries": {"$sum": 1},
            }
        },
        {"$sort": {"latest_timestamp": -1}},
        {"$limit": 100},
    ]
    raw = await db.competition_rounds.aggregate(pipeline).to_list(length=100)

    projects = []
    for p in raw:
        project_id = p["_id"]
        current_round = p["latest_round"]
        is_complete = current_round >= TOTAL_ROUNDS

        # Check if current round is scored
        scored_count = await db.competition_rounds.count_documents({
            "project_id": project_id,
            "round_number": current_round,
            "average_score": {"$ne": None},
        })

        projects.append({
            "project_id": project_id,
            "current_round": current_round,
            "total_rounds": TOTAL_ROUNDS,
            "latest_task": p["latest_task"],
            "latest_timestamp": p["latest_timestamp"].isoformat() if p["latest_timestamp"] else None,
            "status": "complete" if is_complete else ("scoring" if scored_count > 0 else "active"),
            "round_scored": scored_count == 4,
        })

    return {"projects": projects}
