"""Self-service position management.

Every member decides their own standing. No approval required.

When someone wants to leave or step down, the platform owner is notified
and given a chance to respond to any concerns — not to block the exit, but
because they genuinely want to understand and address what went wrong.
The exit processes automatically after 72 hours regardless.

Emergency override remains in executive_control.py, as required by law.
That system is separate, audited, and not connected to this flow.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database import db
from app.models.user import User
from app.security.auth import current_user
from app.utils.audit import audit, notify

router = APIRouter()

ROLE_DESCRIPTIONS = {
    "student": (
        "You are a member of this community. You have access to learning resources, "
        "the M.O.R.E. network, and shared community spaces."
    ),
    "instructor": (
        "You teach and support others here. You can create content, run courses, "
        "and guide learners in your area of knowledge."
    ),
    "admin": (
        "You help keep the platform running — managing members, content, and "
        "day-to-day operations. This role carries real responsibility."
    ),
    "executive_admin": (
        "You hold full platform authority. This role exists to satisfy legal requirements "
        "and for genuine emergencies only — not for ordinary control. If you hold it and "
        "don't need it, you are free to step down."
    ),
}

ROLE_LABELS = {
    "student": "Member",
    "instructor": "Instructor",
    "admin": "Administrator",
    "executive_admin": "Executive",
}

STEP_DOWN_TARGET = {
    "executive_admin": "admin",
    "admin": "instructor",
    "instructor": "student",
}

VALID_PROCEEDS = {"reinvest", "donate", "hold", "payout"}

# How long an exit request stays pending before auto-processing (hours)
EXIT_WINDOW_HOURS = 72


class StepDownReq(BaseModel):
    reason: str = Field(..., min_length=10, description="A few words on why — kept in the record, not used to block you.")


class ExitReq(BaseModel):
    reason: str = Field(..., min_length=10, description="What's on your mind. Shared with the platform owner so they can address it.")


class ProceedsReq(BaseModel):
    preference: str = Field(..., description="One of: reinvest, donate, hold, payout")


async def _notify_execs(title: str, body: str, link: str = "/admin/system"):
    """Send a notification to all active executive_admins."""
    execs = await db.users.find(
        {"role": "executive_admin", "is_active": True}, {"id": 1}
    ).to_list(length=20)
    for ex in execs:
        await notify(ex["id"], title, body, link=link, kind="warning")


# ── Position read ────────────────────────────────────────────────────────────

@router.get("/me/position")
async def get_my_position(me: User = Depends(current_user)):
    doc = await db.users.find_one({"id": me.id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Account not found.")

    pending = await db.exit_requests.find_one(
        {"user_id": me.id, "status": "pending"}
    )

    return {
        "id": me.id,
        "full_name": me.full_name,
        "email": me.email,
        "role": me.role,
        "role_description": ROLE_DESCRIPTIONS.get(me.role, ""),
        "role_label": ROLE_LABELS.get(me.role, me.role),
        "associate": doc.get("associate"),
        "is_active": doc.get("is_active", True),
        "more_member": doc.get("more_member", False),
        "more_member_since": doc.get("more_member_since"),
        "created_at": doc.get("created_at"),
        "can_step_down": me.role in STEP_DOWN_TARGET,
        "step_down_to": STEP_DOWN_TARGET.get(me.role),
        "step_down_to_label": ROLE_LABELS.get(STEP_DOWN_TARGET.get(me.role, ""), ""),
        "pending_exit": {
            "id": pending["id"],
            "reason": pending["reason"],
            "requested_at": pending["requested_at"],
            "auto_processes_at": pending["auto_processes_at"],
        } if pending else None,
    }


# ── Step down (immediate, owner notified) ───────────────────────────────────

@router.post("/me/step-down")
async def step_down(body: StepDownReq, me: User = Depends(current_user)):
    """Step down from the current role. No approval needed. Owner is notified."""
    if me.role not in STEP_DOWN_TARGET:
        raise HTTPException(400, "You are already at the base member level.")

    target_role = STEP_DOWN_TARGET[me.role]

    if me.role == "executive_admin":
        count = await db.users.count_documents(
            {"role": "executive_admin", "is_active": True}
        )
        if count <= 1:
            raise HTTPException(
                400,
                "You are the only active executive. The platform requires at least one "
                "for legal accountability. Designate someone else first, then step down.",
            )

    if me.role == "admin":
        count = await db.users.count_documents(
            {"role": {"$in": ["admin", "executive_admin"]}, "is_active": True}
        )
        if count <= 1:
            raise HTTPException(
                400,
                "You are the only active administrator. Please designate another admin "
                "before stepping down so the platform doesn't lose operational coverage.",
            )

    await db.users.update_one(
        {"id": me.id},
        {"$set": {"role": target_role, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await audit(
        me.id,
        "position.step_down",
        meta={
            "from_role": me.role,
            "to_role": target_role,
            "reason": body.reason,
            "self_initiated": True,
        },
    )
    await _notify_execs(
        f"{me.full_name} has stepped down",
        f"{me.full_name} stepped down from {ROLE_LABELS.get(me.role, me.role)} "
        f"to {ROLE_LABELS.get(target_role, target_role)}.\n\nTheir reason: \"{body.reason}\"",
        link="/admin/users",
    )
    return {
        "role": target_role,
        "message": f"You've stepped down to {ROLE_LABELS.get(target_role, target_role)}. "
                   "Your work and history here remain unchanged.",
    }


# ── Exit request (72-hour window, then auto-processes) ──────────────────────

@router.post("/me/request-exit")
async def request_exit(body: ExitReq, me: User = Depends(current_user)):
    """
    Request to go inactive. The platform owner is notified and given 72 hours
    to reach out and address any concerns. The exit processes automatically
    after that window — it is never blocked.
    """
    existing = await db.exit_requests.find_one({"user_id": me.id, "status": "pending"})
    if existing:
        raise HTTPException(400, "You already have a pending exit request.")

    if me.role == "executive_admin":
        count = await db.users.count_documents(
            {"role": "executive_admin", "is_active": True}
        )
        if count <= 1:
            raise HTTPException(
                400,
                "You are the only active executive. Transfer authority before going inactive.",
            )

    now = datetime.now(timezone.utc)
    auto_at = now + timedelta(hours=EXIT_WINDOW_HOURS)
    record = {
        "id": str(uuid.uuid4()),
        "user_id": me.id,
        "full_name": me.full_name,
        "email": me.email,
        "role": me.role,
        "reason": body.reason,
        "status": "pending",
        "requested_at": now.isoformat(),
        "auto_processes_at": auto_at.isoformat(),
    }
    await db.exit_requests.insert_one(record)
    await audit(
        me.id,
        "position.exit_requested",
        meta={"reason": body.reason, "auto_processes_at": auto_at.isoformat()},
    )
    await _notify_execs(
        f"{me.full_name} wants to leave",
        f"{me.full_name} ({ROLE_LABELS.get(me.role, me.role)}) has requested to go inactive.\n\n"
        f"Their reason: \"{body.reason}\"\n\n"
        f"You have 72 hours to reach out and address any concerns. "
        f"Their account will go inactive automatically on {auto_at.strftime('%B %d at %I:%M %p UTC')} "
        f"if unresolved.",
        link="/admin/users",
    )
    return {
        "requested_at": now.isoformat(),
        "auto_processes_at": auto_at.isoformat(),
        "message": (
            "Your request has been received. The platform owner has been notified "
            "and may reach out within 72 hours. If nothing changes, your account "
            "goes inactive automatically after that. You can cancel anytime."
        ),
    }


@router.post("/me/emergency-exit")
async def emergency_exit(body: ExitReq, me: User = Depends(current_user)):
    """
    Immediate exit — for genuine emergencies. No waiting period.
    The owner is still notified, but the account deactivates right now.
    This exists because safety matters more than process.
    """
    if me.role == "executive_admin":
        count = await db.users.count_documents(
            {"role": "executive_admin", "is_active": True}
        )
        if count <= 1:
            raise HTTPException(
                400,
                "You are the only active executive. Transfer authority before leaving.",
            )

    # Cancel any pending standard exit
    await db.exit_requests.update_many(
        {"user_id": me.id, "status": "pending"},
        {"$set": {"status": "superseded_by_emergency"}},
    )

    now = datetime.now(timezone.utc)
    await db.exit_requests.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": me.id,
        "full_name": me.full_name,
        "email": me.email,
        "role": me.role,
        "reason": body.reason,
        "status": "completed_emergency",
        "requested_at": now.isoformat(),
        "auto_processes_at": now.isoformat(),
        "emergency": True,
    })
    await db.users.update_one(
        {"id": me.id},
        {"$set": {"is_active": False, "deactivated_at": now.isoformat()}},
    )
    await db.sessions.delete_many({"user_id": me.id})
    await audit(
        me.id,
        "position.emergency_exit",
        meta={"reason": body.reason, "self_initiated": True, "emergency": True},
    )
    await _notify_execs(
        f"{me.full_name} has left",
        f"{me.full_name} ({ROLE_LABELS.get(me.role, me.role)}) chose to leave immediately.\n\n"
        f"They shared: \"{body.reason}\"\n\n"
        f"Their account is inactive. This was their decision and their right.",
        link="/admin/users",
    )
    return {
        "message": (
            "You've been signed out and your account is now inactive. "
            "The platform owner has been notified. Your contributions are preserved. "
            "You can always return."
        )
    }


@router.post("/me/cancel-exit")
async def cancel_exit(me: User = Depends(current_user)):
    """Cancel a pending exit request — no questions asked."""
    result = await db.exit_requests.update_one(
        {"user_id": me.id, "status": "pending"},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.modified_count == 0:
        raise HTTPException(400, "No pending exit request found.")
    await audit(me.id, "position.exit_cancelled", meta={"self_initiated": True})
    return {"message": "Exit request cancelled. You're still active."}


# ── Leave M.O.R.E. (immediate, owner notified) ──────────────────────────────

@router.post("/me/leave-more")
async def leave_more(me: User = Depends(current_user)):
    doc = await db.users.find_one({"id": me.id})
    if not doc or not doc.get("more_member"):
        raise HTTPException(400, "You are not currently a M.O.R.E. member.")

    await db.users.update_one(
        {"id": me.id},
        {"$set": {"more_member": False, "more_left_at": datetime.now(timezone.utc).isoformat()}},
    )
    await audit(me.id, "position.leave_more", meta={"self_initiated": True})
    await _notify_execs(
        f"{me.full_name} left M.O.R.E.",
        f"{me.full_name} has left the M.O.R.E. community membership. "
        f"Their main account remains active.",
        link="/admin/users",
    )
    return {"message": "You've left M.O.R.E. Your account is still active. You're welcome back anytime."}


# ── Proceeds preference ──────────────────────────────────────────────────────

@router.get("/me/position/history")
async def get_position_history(me: User = Depends(current_user)):
    """Personal position event log — the member's own record of their journey here."""
    events = await db.audit_log.find(
        {
            "actor_id": me.id,
            "action": {"$in": [
                "auth.register.success",
                "position.step_down",
                "position.exit_requested",
                "position.exit_cancelled",
                "position.emergency_exit",
                "position.leave_more",
                "position.proceeds_preference_set",
                "position.self_deactivate",
            ]},
        },
        {"_id": 0, "action": 1, "meta": 1, "at": 1},
    ).sort("at", -1).to_list(length=50)
    return {"history": events}


@router.get("/me/proceeds-preference")
async def get_proceeds(me: User = Depends(current_user)):
    doc = await db.users.find_one({"id": me.id}, {"proceeds_preference": 1})
    return {"preference": doc.get("proceeds_preference") if doc else None}


@router.post("/me/proceeds-preference")
async def set_proceeds(body: ProceedsReq, me: User = Depends(current_user)):
    if body.preference not in VALID_PROCEEDS:
        raise HTTPException(400, f"Invalid preference. Choose one of: {', '.join(VALID_PROCEEDS)}")
    await db.users.update_one(
        {"id": me.id},
        {"$set": {
            "proceeds_preference": body.preference,
            "proceeds_preference_set_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    await audit(
        me.id,
        "position.proceeds_preference_set",
        meta={"preference": body.preference, "self_initiated": True},
    )
    return {"preference": body.preference, "message": "Proceeds preference saved."}
