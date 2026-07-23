import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

manifest_lock = threading.Lock()

# Resolve manifest path relative to the repo root (/app in container, project root locally)
# controller.py lives at backend/ai/controller.py — go up two levels to reach repo root
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST_PATH = os.path.join(_REPO_ROOT, "memory", "project_state.json")

router = APIRouter(prefix="/ai", tags=["AI Dispatcher"])

class DispatchRequest(BaseModel):
    command: str = Field(..., description="The architectural command string from Jamil")
    priority: int = Field(default=1, ge=1, le=5, description="Priority execution layer (1-5)")
    context_update: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Payload updates")

def update_manifest_state(action_name: str, status_str: str, details: str, revenue_delta: float = 0.0, current_task: str = ""):
    with manifest_lock:
        try:
            os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
            if os.path.exists(MANIFEST_PATH):
                with open(MANIFEST_PATH, "r") as f:
                    data = json.load(f)
            else:
                data = {
                    "manifest_version": "1.0.0",
                    "project_state": {"current_branch": "main", "system_status": "OPERATIONAL", "active_agents": []},
                    "revenue_targets": {"currency": "USD", "current_mrr": 0.0},
                    "action_logs": []
                }

            data["last_updated"] = datetime.utcnow().isoformat() + "Z"
            data["project_state"]["system_status"] = status_str
            if current_task:
                data["project_state"]["active_agent_task"] = current_task

            if revenue_delta != 0.0:
                data["revenue_targets"]["current_mrr"] = max(0.0, data["revenue_targets"].get("current_mrr", 0.0) + revenue_delta)

            log_fragment = {
                "timestamp": data["last_updated"],
                "action": action_name,
                "status": status_str,
                "details": details
            }
            if "action_logs" not in data:
                data["action_logs"] = []
            data["action_logs"].append(log_fragment)
            data["action_logs"] = data["action_logs"][-100:]

            temp_path = f"{MANIFEST_PATH}.tmp"
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, MANIFEST_PATH)
            return log_fragment
        except Exception as e:
            print(f"[FATAL MANIFEST FAILURE]: {str(e)}")
            return None

@router.post("/dispatch")
async def dispatch_command(payload: DispatchRequest):
    action_name = "command_dispatch"
    if "override" in payload.command.lower() and payload.priority < 4:
        log = update_manifest_state(action_name, "SECURITY_VIOLATION", "Rejected unauthorized override command restriction.")
        raise HTTPException(status_code=403, detail={"error": "RBAC rejection", "log": log})

    try:
        revenue_delta = payload.context_update.get("revenue_delta", 0.0) if payload.context_update else 0.0
        execution_details = f"Successfully prioritized logic stream layer [{payload.priority}]."
        log_entry = update_manifest_state(
            action_name=action_name,
            status_str="OPERATIONAL",
            details=execution_details,
            revenue_delta=revenue_delta,
            current_task="IDLE"
        )
        return {"status": "success", "action_log": log_entry}
    except Exception as fatal_error:
        log_entry = update_manifest_state(
            action_name=action_name,
            status_str="RECOVERY_REQUIRED",
            details=f"Isolating operational runtime error: {str(fatal_error)}",
            current_task="ERROR_HALT"
        )
        return {"status": "failure", "system_status": "RECOVERY_REQUIRED", "action_log": log_entry}
