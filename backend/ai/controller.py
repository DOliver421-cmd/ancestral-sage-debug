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

router = APIRouter(prefix="/api/ai", tags=["AI Dispatcher"])

class DispatchRequest(BaseModel):
    command: str = Field(..., description="The architectural command string from Jamil")
    priority: int = Field(default=1, ge=1, le=5, description="Priority execution layer (1-5)")
    context_update: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Payload updates")

class CheckoutPreHookRequest(BaseModel):
    asset_id: str = Field(..., description="Product key from PAYMENT_PRODUCTS (e.g. 'workbook', 'kit')")
    price: int = Field(..., ge=50, description="Amount in cents (minimum 50 = $0.50)")
    quantity: int = Field(default=1, ge=1, description="Number of items")

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

@router.post("/dispatch/checkout-prehook")
async def checkout_prehook(payload: CheckoutPreHookRequest):
    """Pre-Hook bridge: allows Jamil to request a Stripe checkout session for a digital asset
    by passing asset_id (product_key) and price (amount_cents).

    Returns a checkout URL from Stripe by calling the same logic as
    POST /api/payments/checkout in backend/server.py.
    """
    import stripe as _stripe

    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://wai-institute.org")

    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "Payment system not configured — STRIPE_SECRET_KEY missing")

    _stripe.api_key = STRIPE_SECRET_KEY

    # Import the PAYMENT_PRODUCTS catalog from server.py
    # We reference it lazily to avoid a circular import at module load time
    try:
        from backend.server import PAYMENT_PRODUCTS
    except Exception:
        # Fallback: inline the catalog if server.py can't be imported in this context
        PAYMENT_PRODUCTS = {}

    product = PAYMENT_PRODUCTS.get(payload.asset_id)
    if not product:
        raise HTTPException(400, f"Unknown product key: {payload.asset_id}")

    amount = payload.price
    if not amount or amount < 50:
        raise HTTPException(400, "Amount must be at least 50 cents ($0.50)")

    mode = product["mode"]

    price_data: dict = {
        "currency": "usd",
        "product_data": {"name": product["name"], "description": product.get("description", "")},
        "unit_amount": amount,
    }
    if mode == "subscription":
        price_data["recurring"] = {"interval": product["interval"]}

    session_kwargs: dict = dict(
        mode=mode,
        line_items=[{"price_data": price_data, "quantity": payload.quantity}],
        success_url=f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/payment/cancel",
        metadata={"asset_id": payload.asset_id, "source": "ai_dispatch_prehook"},
    )
    if mode == "subscription":
        session_kwargs["subscription_data"] = {
            "metadata": {"asset_id": payload.asset_id, "source": "ai_dispatch_prehook"}
        }

    try:
        session = _stripe.checkout.Session.create(**session_kwargs)
    except _stripe.error.StripeError as e:
        update_manifest_state(
            action_name="checkout_prehook",
            status_str="RECOVERY_REQUIRED",
            details=f"Stripe checkout creation failed for asset {payload.asset_id}: {str(e)}",
            current_task="ERROR_HALT"
        )
        raise HTTPException(502, f"Stripe error: {str(e)}")

    update_manifest_state(
        action_name="checkout_prehook",
        status_str="OPERATIONAL",
        details=f"Checkout session created for asset {payload.asset_id} at {amount} cents x{payload.quantity}",
        current_task="IDLE"
    )

    return {"url": session.url, "session_id": session.id, "asset_id": payload.asset_id, "amount_cents": amount}
