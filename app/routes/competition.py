"""app/routes/competition.py — The Arena: 5-persona AI competition system.

Endpoints:
  POST /competition/task       — Commissioner assigns task, all 4 compete, Commissioner scores
  POST /competition/score      — User submits their score for each result
  GET  /competition/leaderboard — Cumulative scores ranked with role assignments
  GET  /competition/projects    — All active projects with round status

MongoDB collection: competition_rounds
"""
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import db
from app.models.user import User
from app.security.auth import require_role
from app.services.competition.personas import (
    COMMISSIONER_SYSTEM_PROMPT,
    MAX_RETRIES,
    PASS_THRESHOLD,
    PERSONA_PROMPTS,
    PERSONA_TAGLINES,
    TOTAL_ROUNDS,
)

logger = logging.getLogger("lcewai")
router = APIRouter()

# ── Provider config — uses Groq (Llama 3.3 70B) with Mistral fallback ─────────
_PROVIDERS = [
    {
        "key_env": "GROQ_API_KEY",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
    },
    {
        "key_env": "CEREBRAS_API_KEY",
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "model": "llama3.1-70b",
    },
    {
        "key_env": "MISTRAL_API_KEY",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "model": "mistral-large-latest",
    },
]


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
    """Call AI using first available provider (Groq → Cerebras → Mistral). OpenAI-compatible."""
    for provider in _PROVIDERS:
        api_key = os.environ.get(provider["key_env"], "")
        if not api_key:
            continue
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": provider["model"],
            "max_tokens": 4096,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(provider["url"], headers=headers, json=payload)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                logger.warning("Provider %s returned %s", provider["key_env"], resp.status_code)
        except Exception as e:
            logger.warning("Provider %s failed: %s", provider["key_env"], e)
            continue
    raise HTTPException(status_code=503, detail="No AI provider available. Check GROQ_API_KEY, CEREBRAS_API_KEY, or MISTRAL_API_KEY in Railway.")


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

@router.post("/competition/task")
async def assign_task(
    body: TaskRequest,
    user: User = Depends(require_role("executive_admin")),
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
    user: User = Depends(require_role("executive_admin")),
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
            {"_id": oid},
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
    user: User = Depends(require_role("executive_admin")),
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
    user: User = Depends(require_role("executive_admin")),
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
