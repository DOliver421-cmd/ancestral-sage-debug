import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

# Thread lock to guarantee atomic writes to the manifest state machine
manifest_lock = threading.Lock()
MANIFEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../memory/project_state.json"))

router = APIRouter(prefix="/ai", tags=["AI Dispatcher"])

class DispatchRequest(BaseModel):
    command: str = Field(..., description="The architectural command string from Jamil")
    priority: int = Field(default=1, ge=1, le=5, description="Priority execution layer (1-5)")
    context_update: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Payload updates")

def update_manifest_state(action_name: str, status_str: str, details: str, revenue_delta: float = 0.0, current_task: str = ""):
    """
    Atomic State Machine Writer. Updates the project state tracking manifest safely.
    """
    with manifest_lock:
        try:
            # Ensure the directory structural foundation exists
            os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
            
            # Load existing manifest state or initialize a safe fallback
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
            
            # Apply System Logic State updates
            data["last_updated"] = datetime.utcnow().isoformat() + "Z"
            data["project_state"]["system_status"] = status_str
            if current_task:
                data["project_state"]["active_agent_task"] = current_task
                
            if revenue_delta != 0.0:
                data["revenue_targets"]["current_mrr"] = max(0.0, data["revenue_targets"].get("current_mrr", 0.0) + revenue_delta)
            
            # Log the operational log fragment
            log_fragment = {
                "timestamp": data["last_updated"],
                "action": action_name,
                "status": status_str,
                "details": details
            }
            if "action_logs" not in data:
                data["action_logs"] = []
            data["action_logs"].append(log_fragment)
            
            # Keep action log memory optimized (slice to last 100 entries if necessary)
            data["action_logs"] = data["action_logs"][-100:]
            
            # Atomic structural write via a temporary sibling file
            temp_path = f"{MANIFEST_PATH}.tmp"
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, MANIFEST_PATH)
            
            return log_fragment
        except Exception as e:
            # Fallback fail-safe mechanism if state preservation itself fails
            print(f"[FATAL MANIFEST FAILURE]: {str(e)}")
            return None

@router.post("/dispatch")
async def dispatch_command(payload: DispatchRequest):
    """
    The Gateway Hook: Captures structural prompts, screens them, 
    and handles execution with absolute error isolation.
    """
    action_name = "command_dispatch"
    current_task = f"Executing: {payload.command[:30]}"
    
    # Placeholder validation boundary against backend/security architecture
    # In full rollout, this hooks directly into your custom RBAC validation logic
    if "override" in payload.command.lower() and payload.priority < 4:
        log = update_manifest_state(action_name, "SECURITY_VIOLATION", "Rejected unauthorized override command restriction.")
        raise HTTPException(status_code=403, detail={"error": "RBAC rejection", "log": log})
        
    try:
        # --- Logic Execution Pipeline ---
        # Your target operations go here. Hooking into database connections if required:
        # Example tracking structural logic variations
        revenue_delta = payload.context_update.get("revenue_delta", 0.0) if payload.context_update else 0.0
        
        # Simulating processing of commands...
        execution_details = f"Successfully prioritized logic stream layer [{payload.priority}]."
        
        # Update manifest autonomously on successful completion execution
        log_entry = update_manifest_state(
            action_name=action_name,
            status_str="OPERATIONAL",
            details=execution_details,
            revenue_delta=revenue_delta,
            current_task="IDLE"
        )
        return {"status": "success", "action_log": log_entry}
        
    except Exception as fatal_error:
        # Error Isolation Protection Layer: The system must never crash
        error_msg = f"Isolating operational runtime error: {str(fatal_error)}"
        log_entry = update_manifest_state(
            action_name=action_name,
            status_str="RECOVERY_REQUIRED",
            details=error_msg,
            current_task="ERROR_HALT"
        )
        # Safely reply with a structural 500 state capture, keeping the system up
        return {
            "status": "failure", 
            "system_status": "RECOVERY_REQUIRED", 
            "action_log": log_entry
        }
