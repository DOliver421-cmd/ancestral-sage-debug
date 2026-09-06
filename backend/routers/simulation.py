"""routers/simulation.py — Student/Instructor Simulation Lab API.

Endpoints are restricted to admin/exec roles. All simulation entities carry
internal is_simulation=True flags. Normal learner-facing UI never displays
simulation labels.

Mount: /api (via server.py _ADDITIONAL_API_ROUTER_MODULES)
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from deps import dep_current_user, require_rank, get_db, audit_log
from simulation import (
    SimulationEngine,
    SimulationProfile,
    SimulationRun,
    SimulationEvent,
    STUDENT_PROFILES,
    INSTRUCTOR_PROFILES,
    SCENARIOS,
    get_engine,
)

logger = logging.getLogger("lcewai.simulation")
router = APIRouter(tags=["simulation"])

# ── Shared state ─────────────────────────────────────────────────────────────
db = current_user = audit = None
_sim_sim_app = None


def bind(_db, _current_user, _audit=None, _sim_app=None):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, _sim_sim_app
    db = _db
    current_user = _current_user
    audit = _audit
    _sim_sim_app = _sim_app


async def _dep_current_user(authorization: Optional[str] = None):
    if current_user is None:
        raise HTTPException(503, "Service starting up")
    return await current_user(authorization)


# ── Pydantic schemas ─────────────────────────────────────────────────────────
class ProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    type: str = Field(pattern="^(student|instructor)$")
    profile_key: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    behavior_config: dict = Field(default_factory=dict)


class ProfileOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    type: str
    profile_key: str
    description: str
    behavior_config: dict
    is_simulation: bool
    created_at: str


class RunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    scenario_id: str = Field(min_length=1)
    profile_ids: List[str] = Field(min_length=1)
    course_slugs: List[str] = Field(min_length=1)
    config: dict = Field(default_factory=dict)


class RunOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    scenario_id: str
    profile_ids: List[str]
    course_slugs: List[str]
    config: dict
    status: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    event_count: int = 0
    created_by: str
    created_at: str
    updated_at: str


class EventOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    run_id: str
    simulated_user_id: str
    event_type: str
    target_type: str
    target_id: str
    metadata: dict
    is_simulation: bool
    created_at: str


class AnalyticsOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    run_id: str
    total_events: int
    by_event_type: dict
    by_user: dict
    by_target_type: dict


# ── Helper ───────────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _doc_to_profile(doc: dict) -> ProfileOut:
    return ProfileOut(**doc)


def _doc_to_run(doc: dict) -> RunOut:
    return RunOut(**doc)


def _doc_to_event(doc: dict) -> EventOut:
    return EventOut(**doc)


# ── Profiles ─────────────────────────────────────────────────────────────────
@router.get("/simulation/profiles")
async def list_profiles(user=Depends(require_rank("admin"))):
    engine = get_engine(db, _sim_app)
    profiles = await engine.list_profiles()
    return {"profiles": [_doc_to_profile(p.to_doc()) for p in profiles]}


@router.post("/simulation/profiles")
async def create_profile(body: ProfileCreate, user=Depends(require_rank("admin"))):
    engine = get_engine(db, _sim_app)
    profile = await engine.create_profile(
        name=body.name,
        type=body.type,
        profile_key=body.profile_key,
        description=body.description,
        behavior_config=body.behavior_config,
    )
    return {"profile": _doc_to_profile(profile.to_doc())}


@router.get("/simulation/profiles/{profile_id}")
async def get_profile(profile_id: str, user=Depends(require_rank("admin"))):
    engine = get_engine(db, _sim_app)
    profile = await engine.get_profile(profile_id)
    if not profile:
        raise HTTPException(404, "Profile not found")
    return {"profile": _doc_to_profile(profile.to_doc())}


@router.get("/simulation/scenarios")
async def list_scenarios(user=Depends(require_rank("admin"))):
    return {"scenarios": [
        {"id": k, "name": v["name"], "description": v["description"], "config": v.get("config", {})}
        for k, v in SCENARIOS.items()
    ]}


# ── Runs ─────────────────────────────────────────────────────────────────────
@router.post("/simulation/runs")
async def create_run(body: RunCreate, user=Depends(require_rank("admin"))):
    engine = get_engine(db, _sim_app)
    run = await engine.create_run(
        name=body.name,
        description=body.description,
        scenario_id=body.scenario_id,
        profile_ids=body.profile_ids,
        course_slugs=body.course_slugs,
        config=body.config,
        created_by=user.id,
    )
    if audit:
        try:
            await audit(user.id, "simulation.run.create", target=run.id, meta={"scenario_id": body.scenario_id, "profiles": body.profile_ids})
        except Exception:
            logger.exception("audit failed")
    return {"run": _doc_to_run(run.to_doc())}


@router.get("/simulation/runs")
async def list_runs(user=Depends(require_rank("admin")), status: Optional[str] = None):
    engine = get_engine(db, _sim_app)
    runs = await engine.list_runs(status=status)
    return {"runs": [_doc_to_run(r.to_doc()) for r in runs]}


@router.get("/simulation/runs/{run_id}")
async def get_run(run_id: str, user=Depends(require_rank("admin"))):
    engine = get_engine(db, _sim_app)
    run = await engine.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return {"run": _doc_to_run(run.to_doc())}


@router.post("/simulation/runs/{run_id}/start")
async def start_run(run_id: str, user=Depends(require_rank("admin"))):
    engine = get_engine(db, _sim_app)
    run = await engine.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.status == "running":
        raise HTTPException(400, "Run is already running")
    task = __import__("asyncio").create_task(engine.start_run(run_id))
    engine._running_tasks[run_id] = task
    return {"ok": True, "run_id": run_id, "status": "started"}


@router.post("/simulation/runs/{run_id}/stop")
async def stop_run(run_id: str, user=Depends(require_rank("admin"))):
    engine = get_engine(db, _sim_app)
    run = await engine.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    await engine.stop_run(run_id)
    return {"ok": True, "run_id": run_id, "status": "stopped"}


# ── Events ───────────────────────────────────────────────────────────────────
@router.get("/simulation/runs/{run_id}/events")
async def get_events(run_id: str, user=Depends(require_rank("admin")), event_type: Optional[str] = None, limit: int = 500):
    engine = get_engine(db, _sim_app)
    run = await engine.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    events = await engine.get_events(run_id, event_type=event_type, limit=limit)
    return {"events": [_doc_to_event(e.to_doc()) for e in events]}


@router.get("/simulation/runs/{run_id}/analytics")
async def get_run_analytics(run_id: str, user=Depends(require_rank("admin"))):
    engine = get_engine(db, _sim_app)
    run = await engine.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    analytics = await engine.get_run_analytics(run_id)
    return {"analytics": analytics}


# ── Comparison analytics ─────────────────────────────────────────────────────
@router.get("/simulation/analytics/comparison")
async def get_comparison_analytics(user=Depends(require_rank("admin")), course_slug: Optional[str] = None):
    """Compare real vs simulated activity across runs."""
    real_events = await db.simulation_events.count_documents({"is_simulation": False})
    sim_events = await db.simulation_events.count_documents({"is_simulation": True})
    real_runs = await db.simulation_runs.count_documents({"status": "completed"})
    # Progress stats
    real_progress = await db.academy_progress.count_documents({})
    sim_students = await db.academy_students.count_documents({"parent_user_id": {"$regex": "^sim_"}})
    return {
        "real_events": real_events,
        "simulated_events": sim_events,
        "real_completed_runs": real_runs,
        "real_progress_records": real_progress,
        "simulated_student_profiles": sim_students,
    }
