"""
construction_pm.py — Electrical Project Management & Labor Engine
M.O.R.E. Help Center · construction domain · strictly isolated from help-center tables.

Staff-authenticated (Supabase JWT via server.current_user). Within the staff
boundary there are no tier gates, approval bottlenecks, or subscription locks.

Collections (MongoDB, database `db` bound at startup):
  construction_projects     — one doc per electrical project
  construction_division26   — master CSI Division 26 catalog
  construction_estimate_versions — immutable bid revision snapshots
  construction_line_items   — takeoff entries tied to an estimate version
  construction_crew_blends  — project-specific labor billing composition
  construction_daily_logs   — field productivity entries
  construction_benchmarks   — empirical labor benchmarks (trigger-refreshed)
  construction_blueprints   — uploaded plan-set metadata

REST contract:
  POST   /api/construction/projects                          create project
  GET    /api/construction/projects                          list staff projects
  GET    /api/construction/projects/{id}                     project detail
  POST   /api/construction/projects/{id}/estimates/calculate — compute extended cost/sell
  GET    /api/construction/projects/{id}/takeoff             line items + markups
  POST   /api/construction/projects/{id}/field-logs          submit daily crew log
  GET    /api/construction/projects/{id}/evm-metrics         SPI / CPI / EV / AC / PV
  POST   /api/construction/projects/{id}/blueprints/upload   register a blueprint
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId

from deps import get_db as _shared_db

logger = logging.getLogger("construction_pm")
router = APIRouter(tags=["construction-pm"])

# ── Auth ──────────────────────────────────────────────────────────────────────
# Reuse the canonical current_user dependency from server.py (JWT decode +
# token_version revocation + deactivation checks). Staff roles operate
# open-read/write within the construction domain — no tier gates.

_StaffRole = ("instructor", "support_staff", "oversight", "admin", "executive_admin")

_CURRENT_USER = None


def bind(current_user=None, audit=None, db=None, **kwargs):
    global _CURRENT_USER
    if current_user is not None:
        _CURRENT_USER = current_user


async def _staff_user(authorization: Optional[str] = Header(None)) -> dict:
    if _CURRENT_USER is None:
        raise HTTPException(503, "Service starting up")
    user = await _CURRENT_USER(authorization)
    if user.role not in _StaffRole:
        raise HTTPException(403, "Staff access required")
    return {
        "id": user.id,
        "role": user.role,
        "full_name": getattr(user, "full_name", "") or user.id,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")


def _serialize(doc: dict) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


# ── Models ────────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    job_number: str = Field(..., min_length=1)
    client_name: str = Field(..., min_length=1)
    site_address: str = ""
    contract_value: float = Field(default=0.0, ge=0)
    current_phase: str = Field(default="pre_con")  # pre_con | construction | turnover


class Division26Item(BaseModel):
    csi_code: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    uom: str = "ea"  # ea | lf | sf | ...
    default_material_cost: float = Field(default=0.0, ge=0)
    default_labor_hours: float = Field(default=0.0, ge=0)


class EstimateVersionCreate(BaseModel):
    target_margin: float = Field(default=0.20, ge=0, le=1)
    notes: str = ""


class LineItem(BaseModel):
    item_id: str = Field(..., min_length=1)
    quantity: float = Field(..., ge=0)
    applied_multipliers: List[float] = Field(default_factory=list)
    extended_material: float = Field(default=0.0, ge=0)
    extended_labor: float = Field(default=0.0, ge=0)


class CrewBlend(BaseModel):
    foreman_ratio: float = Field(default=0.2, ge=0, le=1)
    journeyman_ratio: float = Field(default=0.6, ge=0, le=1)
    apprentice_ratio: float = Field(default=0.2, ge=0, le=1)
    blended_hourly_rate: float = Field(default=0.0, ge=0)
    fringe_burden: float = Field(default=0.0, ge=0)


class DailyCrewLog(BaseModel):
    item_id: str = Field(..., min_length=1)
    actual_quantity_installed: float = Field(..., ge=0)
    actual_hours_spent: float = Field(..., ge=0)


class BlueprintCreate(BaseModel):
    sheet_number: str = Field(..., min_length=1)
    file_path: str = Field(..., min_length=1)
    scale_factor: float = Field(default=1.0, ge=0)
    layer_metadata: dict = Field(default_factory=dict)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _db():
    d = _shared_db()
    if d is None:
        raise HTTPException(503, "Database not initialized")
    return d


def _calc_extended(material_cost: float, labor_hours: float, qty: float,
                   multipliers: List[float], blended_rate: float, fringe: float):
    """Compute extended material, labor hours, direct cost, and sell price."""
    stack = 1.0
    for m in multipliers:
        stack *= max(m, 0.0)
    effective_labor_hours = labor_hours * stack
    extended_material = material_cost * qty
    extended_labor = effective_labor_hours * blended_rate * qty
    fringe_cost = fringe * qty
    direct_cost = extended_material + extended_labor + fringe_cost
    return {
        "extended_material": round(extended_material, 2),
        "extended_labor": round(extended_labor, 2),
        "fringe_cost": round(fringe_cost, 2),
        "direct_cost": round(direct_cost, 2),
    }


# ── PROJECTS ──────────────────────────────────────────────────────────────────

@router.post("/projects", status_code=201)
async def create_project(
    body: ProjectCreate,
    user: dict = Depends(_staff_user),
    request: Request = None,
):
    db = _db()
    now = _now()
    doc = {
        "job_number": body.job_number.strip(),
        "client_name": body.client_name.strip(),
        "site_address": body.site_address.strip(),
        "contract_value": body.contract_value,
        "current_phase": body.current_phase,
        "owner_id": user["id"],
        "owner_name": user["full_name"],
        "created_at": now,
        "updated_at": now,
        "created_by": user["id"],
        "updated_by": user["id"],
        "version": 1,
    }
    result = await db.construction_projects.insert_one(doc)
    doc["_id"] = result.inserted_id
    try:
        await db.audit_log.insert_one({
            "id": str(__import__("uuid").uuid4()),
            "actor_id": user["id"],
            "action": "construction_project_created",
            "target": str(result.inserted_id),
            "meta": {"job_number": body.job_number, "client": body.client_name},
            "at": now,
        })
    except Exception:
        pass
    return _serialize(doc)


@router.get("/projects")
async def list_projects(
    user: dict = Depends(_staff_user),
    phase: Optional[str] = Query(None),
):
    db = _db()
    q = {}
    if phase:
        q["current_phase"] = phase
    docs = await db.construction_projects.find(q).sort("updated_at", -1).limit(200).to_list(length=200)
    return {"projects": [_serialize(d) for d in docs], "total": len(docs)}


@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    user: dict = Depends(_staff_user),
):
    db = _db()
    doc = await db.construction_projects.find_one({"_id": _oid(project_id)})
    if not doc:
        raise HTTPException(404, "Project not found")
    return _serialize(doc)


# ── ESTIMATES ─────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/estimates/calculate")
async def calculate_estimate(
    project_id: str,
    body: EstimateVersionCreate,
    crew: CrewBlend,
    items: List[LineItem],
    user: dict = Depends(_staff_user),
):
    db = _db()
    project = await db.construction_projects.find_one({"_id": _oid(project_id)})
    if not project:
        raise HTTPException(404, "Project not found")

    # Blend must sum to ~1.0
    blend_sum = crew.foreman_ratio + crew.journeyman_ratio + crew.apprentice_ratio
    if abs(blend_sum - 1.0) > 0.001:
        raise HTTPException(400, detail="Crew blend ratios must sum to 1.0")

    # Resolve each line item against the Division 26 catalog
    resolved = []
    total_direct = 0.0
    total_labor_hours = 0.0
    for it in items:
        cat = await db.construction_division26.find_one({"item_id": it.item_id})
        if not cat:
            raise HTTPException(404, f"Division 26 item not found: {it.item_id}")
        mat_cost = cat.get("default_material_cost", 0.0)
        labor_hrs = cat.get("default_labor_hours", 0.0)
        calc = _calc_extended(
            mat_cost, labor_hrs, it.quantity, it.applied_multipliers,
            crew.blended_hourly_rate, crew.fringe_burden,
        )
        total_labor_hours += labor_hrs * it.quantity
        total_direct += calc["direct_cost"]
        resolved.append({
            "item_id": it.item_id,
            "csi_code": cat.get("csi_code"),
            "description": cat.get("description"),
            "uom": cat.get("uom"),
            "quantity": it.quantity,
            "applied_multipliers": it.applied_multipliers,
            "base_material_cost": mat_cost,
            "base_labor_hours": labor_hrs,
            **calc,
        })

    sell_price = total_direct / (1.0 - body.target_margin) if body.target_margin < 1.0 else 0.0
    gross_margin = (sell_price - total_direct) / sell_price if sell_price else 0.0

    version_doc = {
        "project_id": project_id,
        "version_number": int(project.get("version", 1)) + 1,
        "target_margin": body.target_margin,
        "notes": body.notes,
        "crew_blend": crew.model_dump(),
        "line_items": resolved,
        "total_direct_cost": round(total_direct, 2),
        "total_labor_hours": round(total_labor_hours, 2),
        "sell_price": round(sell_price, 2),
        "gross_margin": round(gross_margin, 4),
        "created_by": user["id"],
        "created_at": _now(),
    }
    result = await db.construction_estimate_versions.insert_one(version_doc)
    version_doc["id"] = str(result.inserted_id)

    # Bump project version for audit trace
    await db.construction_projects.update_one(
        {"_id": _oid(project_id)},
        {"$set": {"version": version_doc["version_number"], "updated_at": _now(), "updated_by": user["id"]}},
    )

    try:
        await db.audit_log.insert_one({
            "id": str(__import__("uuid").uuid4()),
            "actor_id": user["id"],
            "action": "construction_estimate_calculated",
            "target": project_id,
            "meta": {"version": version_doc["version_number"], "sell_price": version_doc["sell_price"]},
            "at": _now(),
        })
    except Exception:
        pass

    return version_doc


@router.get("/projects/{project_id}/takeoff")
async def get_takeoff(
    project_id: str,
    user: dict = Depends(_staff_user),
):
    db = _db()
    project = await db.construction_projects.find_one({"_id": _oid(project_id)})
    if not project:
        raise HTTPException(404, "Project not found")
    latest = await db.construction_estimate_versions.find_one(
        {"project_id": project_id}, sort=[("created_at", -1)]
    )
    blueprints = await db.construction_blueprints.find(
        {"project_id": project_id}
    ).sort("sheet_number", 1).to_list(length=200)
    return {
        "project": _serialize(project),
        "estimate": _serialize(latest) if latest else None,
        "blueprints": [_serialize(b) for b in blueprints],
    }


# ── FIELD LOGS + EVM ──────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/field-logs", status_code=201)
async def submit_field_log(
    project_id: str,
    body: DailyCrewLog,
    user: dict = Depends(_staff_user),
):
    db = _db()
    project = await db.construction_projects.find_one({"_id": _oid(project_id)})
    if not project:
        raise HTTPException(404, "Project not found")

    item = await db.construction_division26.find_one({"item_id": body.item_id})
    if not item:
        raise HTTPException(404, f"Division 26 item not found: {body.item_id}")

    log_doc = {
        "project_id": project_id,
        "item_id": body.item_id,
        "actual_quantity_installed": body.actual_quantity_installed,
        "actual_hours_spent": body.actual_hours_spent,
        "logged_by": user["id"],
        "recorded_date": _now(),
        "created_at": _now(),
    }
    result = await db.construction_daily_logs.insert_one(log_doc)

    # Event-driven benchmark refresh (replaces a Postgres trigger — same effect).
    try:
        pipeline = [
            {"$match": {"item_id": body.item_id}},
            {"$group": {
                "_id": "$item_id",
                "avg_hours": {"$avg": "$actual_hours_spent"},
                "count": {"$sum": 1},
            }},
        ]
        agg = await db.construction_daily_logs.aggregate(pipeline).to_list(length=1)
        if agg:
            avg = round(agg[0]["avg_hours"], 4)
            await db.construction_benchmarks.update_one(
                {"item_id": body.item_id},
                {
                    "$set": {
                        "item_id": body.item_id,
                        "historical_avg_hours_per_unit": avg,
                        "sample_count": agg[0]["count"],
                        "last_updated": _now(),
                    }
                },
                upsert=True,
            )
    except Exception:
        logger.exception("benchmark refresh failed")

    try:
        await db.audit_log.insert_one({
            "id": str(__import__("uuid").uuid4()),
            "actor_id": user["id"],
            "action": "construction_field_log_submitted",
            "target": project_id,
            "meta": {"item_id": body.item_id, "qty": body.actual_quantity_installed, "hours": body.actual_hours_spent},
            "at": _now(),
        })
    except Exception:
        pass

    return {"status": "logged", "id": str(result.inserted_id)}


@router.get("/projects/{project_id}/evm-metrics")
async def get_evm_metrics(
    project_id: str,
    user: dict = Depends(_staff_user),
):
    db = _db()
    project = await db.construction_projects.find_one({"_id": _oid(project_id)})
    if not project:
        raise HTTPException(404, "Project not found")

    latest = await db.construction_estimate_versions.find_one(
        {"project_id": project_id}, sort=[("created_at", -1)]
    )
    if not latest:
        raise HTTPException(400, "No estimate version to evaluate against")

    line_items = latest.get("line_items", [])
    total_estimated_hours = latest.get("total_labor_hours", 0.0)

    # Planned Value: estimated hours × scheduled percent complete (phase-based proxy)
    phase_weights = {"pre_con": 0.15, "construction": 0.70, "turnover": 0.15}
    scheduled_pct = phase_weights.get(project.get("current_phase", "construction"), 0.50)
    pv = total_estimated_hours * scheduled_pct

    # Earned Value: sum(base_labor_hours × item percent complete from logs)
    ev = 0.0
    item_detail = []
    for li in line_items:
        qty = li.get("quantity", 0)
        base_hours = li.get("base_labor_hours", 0) * qty
        # percent complete from accumulated logs / estimated quantity
        logs = await db.construction_daily_logs.find(
            {"project_id": project_id, "item_id": li["item_id"]}
        ).to_list(length=200)
        installed = sum(l.get("actual_quantity_installed", 0) for l in logs)
        pct = min(1.0, installed / qty) if qty else 0.0
        earned = base_hours * pct
        ev += earned
        item_detail.append({
            "item_id": li["item_id"],
            "csi_code": li.get("csi_code"),
            "quantity": qty,
            "installed": installed,
            "percent_complete": round(pct, 4),
            "earned_hours": round(earned, 4),
        })

    # Actual Cost: total labor hours logged in field journals
    all_logs = await db.construction_daily_logs.find({"project_id": project_id}).to_list(length=1000)
    ac = sum(l.get("actual_hours_spent", 0) for l in all_logs)

    cpi = ev / ac if ac else (1.0 if ev == 0 else None)
    spi = ev / pv if pv else (1.0 if ev == 0 else None)
    cv = ev - ac
    sv = ev - pv

    return {
        "project_id": project_id,
        "phase": project.get("current_phase"),
        "planned_value_hours": round(pv, 4),
        "earned_value_hours": round(ev, 4),
        "actual_cost_hours": round(ac, 4),
        "cost_performance_index": round(cpi, 4) if cpi is not None else None,
        "schedule_performance_index": round(spi, 4) if spi is not None else None,
        "cost_variance_hours": round(cv, 4),
        "schedule_variance_hours": round(sv, 4),
        "scheduled_percent_complete": round(scheduled_pct, 4),
        "items": item_detail,
    }


# ── BLUEPRINTS ────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/blueprints/upload", status_code=201)
async def upload_blueprint(
    project_id: str,
    body: BlueprintCreate,
    user: dict = Depends(_staff_user),
):
    db = _db()
    project = await db.construction_projects.find_one({"_id": _oid(project_id)})
    if not project:
        raise HTTPException(404, "Project not found")
    doc = {
        "project_id": project_id,
        "sheet_number": body.sheet_number.strip(),
        "file_path": body.file_path.strip(),
        "scale_factor": body.scale_factor,
        "layer_metadata": body.layer_metadata,
        "uploaded_by": user["id"],
        "uploaded_at": _now(),
    }
    result = await db.construction_blueprints.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)


# ── INDEXES ───────────────────────────────────────────────────────────────────

async def ensure_indexes(db):
    await db.construction_projects.create_index("owner_id")
    await db.construction_projects.create_index("job_number", unique=True)
    await db.construction_projects.create_index("current_phase")
    await db.construction_division26.create_index("csi_code", unique=True)
    await db.construction_estimate_versions.create_index("project_id")
    await db.construction_line_items.create_index("estimate_id") if False else None
    await db.construction_crew_blends.create_index("project_id")
    await db.construction_daily_logs.create_index("project_id")
    await db.construction_daily_logs.create_index("item_id")
    await db.construction_benchmarks.create_index("item_id", unique=True)
    await db.construction_blueprints.create_index("project_id")
