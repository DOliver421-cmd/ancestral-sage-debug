"""app/routes/team_ops.py — Team operational dashboard.

Read-only endpoints exposing the autonomous action log so humans can
verify that the AI team is running itself. executive_admin only.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.models.user import User
from app.security.auth import require_role

router = APIRouter()


@router.get("/team/actions")
async def list_team_actions(
    limit: int = Query(100, le=500),
    action: Optional[str] = None,
    user: User = Depends(require_role("executive_admin")),
):
    """Return team.supervisor actions, newest first."""
    from app.database import db
    filt: dict = {"actor": "team.supervisor"}
    if action:
        filt["action"] = {"$regex": action, "$options": "i"}
    docs = (
        await db.team_actions.find(filt, {"_id": 0})
        .sort("at", -1)
        .limit(min(limit, 500))
        .to_list(500)
    )
    human_count = await db.team_actions.count_documents({"human_initiated": True})
    auto_count  = await db.team_actions.count_documents({"human_initiated": False})
    return {
        "actions":      docs,
        "total":        len(docs),
        "human_count":  human_count,
        "auto_count":   auto_count,
    }


@router.get("/team/monitor/status")
async def monitor_status(user: User = Depends(require_role("executive_admin"))):
    """Current in-process monitor state: failure counts, degraded providers."""
    from app.services.team_monitor import _failure_counts, _degraded, MONITOR_INTERVAL_SEC, FAILURE_THRESHOLD
    return {
        "interval_sec":      MONITOR_INTERVAL_SEC,
        "failure_threshold": FAILURE_THRESHOLD,
        "failure_counts":    dict(_failure_counts),
        "degraded":          list(_degraded),
    }
