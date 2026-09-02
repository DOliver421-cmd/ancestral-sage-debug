"""
system_rollback.py — Dual-Trigger Visual Rollback System (owner directive).

Zero-cost state-preservation safety net for the M.O.R.E. Help Center:

  * Retains exactly N (default 3) chronological restore points.
  * Each restore point stores: Railway deployment id, git commit sha,
    a CONFIGURATION snapshot (feature/flag/policy collections) and an
    optional visual screenshot (gzip+base64) supplied by the free
    GitHub Actions capture workflow.
  * Two triggers:
      - Internal : /api/admin/system/rollback        (admin/executive_admin
                    session, via the Feature Control Center panel)
      - External : /api/v1/system/emergency-revert   (HMAC-SHA256 signed,
                    X-MORE-Signature header)
  * Rollback engine:
      1. Replaces CONFIGURATION collections from the snapshot.
      2. Redeploys the prior Railway deployment image (Railway GraphQL
         `deploymentRedeploy`).
  * Ledger lockdown (hard-coded, non-negotiable): creator earnings,
    payments, purchases, scholarships, BYOK keys, API keys, user
    credentials, users, and the audit log are NEVER touched by a rollback.
    The config-restore loop refuses to run against any excluded name.
  * Payment webhooks are deferred (persisted + HTTP 503 so the provider
    retries) while a rollback lock is active, so paid entitlements are
    never dropped mid-rollback.

Zero-cost policy: no paid services. Screenshots arrive from the free
GitHub Actions workflow (scripts/visual-capture.mjs) into
/api/v1/system/visual-state; the rebuild uses Railway's own GraphQL API
with the existing service token; storage is the existing MongoDB.

Bound by server.py: db, current_user, assert_role, audit, notify.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("lcewai.system_rollback")

router = APIRouter(tags=["system-rollback"])

# ── server.py binding ──────────────────────────────────────────────────────
db = None
current_user = None
assert_role = None
audit = None
notify = None


def bind(_db, _current_user, _assert_role, _audit, _notify):
    global db, current_user, assert_role, audit, notify
    db = _db
    current_user = _current_user
    assert_role = _assert_role
    audit = _audit
    notify = _notify


# ── Policy constants ───────────────────────────────────────────────────────
MAX_RESTORE_POINTS = int(os.environ.get("MORE_RESTORE_POINTS", "3"))

# Configuration-only collections a rollback may restore.  Everything a human
# or an agent can accidentally break is here; everything that represents
# money, identity, or user data is excluded below.
RESTORE_CONFIG_COLLECTIONS = (
    "feature_configs",
    "platform_flags",
    "page_access",
    "user_feature_overrides",
    "authz_matrix",
)

# State-protection exclusion list.  A rollback must never write, delete, or
# replace anything in these collections — creator earnings, payment
# transactions, BYOK keys, credentials, users, and the audit trail survive
# every rollback by construction.
LEDGER_COLLECTIONS = (
    "creator_earnings",
    "creator_payout_profiles",
    "creator_payout_requests",
    "payments",
    "payment_pending",
    "payment_failures",
    "media_purchases",
    "media_checkout_pending",
    "webhook_events",
    "deferred_webhooks",
    "scholarship_pledges",
    "scholarship_funds",
    "user_byok_keys",
    "api_keys",
    "api_providers",
    "user_credentials",
    "users",
    "audit_log",
    "system_restore_points",
)

ROLLBACK_LOCK_KEY = "rollback"
ROLLBACK_LOCK_TTL_SECONDS = 300

PUBLIC_APP_URL = os.environ.get("PUBLIC_APP_URL", "https://charming-analysis-morehelpcenter.up.railway.app")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "DOliver421-cmd/ancestral-sage-debug")
RAILWAY_GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"


# ── Env accessors (read live so tests can patch) ──────────────────────────
def webhook_secret() -> str:
    return os.environ.get("MORE_ROLLBACK_WEBHOOK_SECRET", "")


def railway_token() -> str:
    return os.environ.get("RAILWAY_TOKEN", "")


def current_deployment_id() -> str:
    return os.environ.get("RAILWAY_DEPLOYMENT_ID", "")


def current_git_sha() -> str:
    return (
        os.environ.get("RAILWAY_GIT_COMMIT_SHA")
        or os.environ.get("COMMIT_SHA")
        or os.environ.get("GITHUB_SHA")
        or "unknown"
    )


def github_dispatch_token() -> str:
    return os.environ.get("MORE_GITHUB_DISPATCH_TOKEN", "")


# ── HMAC signature (external triggers) ──────────────────────────────────────
def sign_ok(payload: bytes, provided: Optional[str]) -> bool:
    secret = webhook_secret()
    if not secret or not provided:
        return False
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(provided.strip().lower(), expected)


# ── Snapshot / restore of CONFIGURATION collections ────────────────────────
async def _snapshot_config(_db):
    snapshot = {}
    for coll in RESTORE_CONFIG_COLLECTIONS:
        docs = []
        cursor = _db[coll].find({}, {"_id": 0})
        async for doc in cursor:
            docs.append(doc)
        snapshot[coll] = docs
    return snapshot


async def _restore_config(_db, config: dict):
    """Replace configuration collections from a snapshot.

    Refuses (raise) to touch any ledger/excluded collection even if the
    snapshot were poisoned — the ledger lockdown is enforced in code, not
    by convention.
    """
    for coll in config:
        if coll not in RESTORE_CONFIG_COLLECTIONS:
            raise HTTPException(500, f"Refusing to restore non-configuration collection: {coll}")
    for coll, docs in config.items():
        col = _db[coll]
        await col.delete_many({})
        for doc in docs:
            clean = {k: v for k, v in doc.items() if k != "_id"}
            await col.insert_one(clean)
    return {coll: len(docs) for coll, docs in config.items()}


# ── N-3 FIFO rotation ───────────────────────────────────────────────────────
async def _rotate_restore_points(_db):
    keep = await _db.system_restore_points.find(
        {}, sort=[("created_at", -1), ("_id", -1)]
    ).to_list(MAX_RESTORE_POINTS)
    keep_ids = [d["_id"] for d in keep]
    result = await _db.system_restore_points.delete_many({"_id": {"$nin": keep_ids}})
    return getattr(result, "deleted_count", 0)


# ── Rollback lock (payment webhook deferral window) ─────────────────────────
async def set_rollback_lock(_db, reason: str):
    await _db.system_state.update_one(
        {"key": ROLLBACK_LOCK_KEY},
        {
            "$set": {
                "active": True,
                "reason": reason,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": datetime.now(timezone.utc).timestamp() + ROLLBACK_LOCK_TTL_SECONDS,
            }
        },
        upsert=True,
    )


async def clear_rollback_lock(_db):
    await _db.system_state.update_one(
        {"key": ROLLBACK_LOCK_KEY},
        {"$set": {"active": False, "cleared_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )


async def is_rollback_locked(_db) -> bool:
    lock = await _db.system_state.find_one({"key": ROLLBACK_LOCK_KEY})
    if not lock or not lock.get("active"):
        return False
    expires = lock.get("expires_at") or 0
    if expires and expires < datetime.now(timezone.utc).timestamp():
        # TTL expired — treat as unlocked (but leave the record for audit).
        return False
    return True


async def payment_webhook_maybe_defer(_db, provider: str, payload: bytes, headers: dict) -> bool:
    """Queue a payment webhook when a rollback is in progress.

    Returns True when the caller must return HTTP 503 (provider retries
    delivery) and the payload is preserved in the deferred queue for audit
    and manual replay. Returns False when the webhook may be processed.
    """
    if not await is_rollback_locked(_db):
        return False
    safe_headers = {
        k: v
        for k, v in (headers or {}).items()
        if k.lower() not in ("authorization", "cookie", "x-more-signature")
    }
    await _db.deferred_webhooks.insert_one({
        "provider": provider,
        "payload_b64": base64.b64encode(payload).decode("ascii"),
        "headers": safe_headers,
        "status": "deferred_by_rollback",
        "received_at": datetime.now(timezone.utc).isoformat(),
        "attempt": 1,
    })
    logger.warning("system_rollback: deferred %s webhook during rollback window", provider)
    return True


# ── Railway redeploy engine ─────────────────────────────────────────────────
_railway_redeploy_impl = None  # test injection point


async def _railway_redeploy(deployment_id: str) -> dict:
    if _railway_redeploy_impl is not None:
        return await _railway_redeploy_impl(deployment_id)
    token = railway_token()
    if not token:
        raise HTTPException(
            503,
            "RAILWAY_TOKEN is not configured — rollback cannot redeploy. "
            "Set RAILWAY_TOKEN (service account or project token) in Railway → Variables.",
        )
    if not deployment_id:
        raise HTTPException(500, "Restore point has no railway_deployment_id to redeploy.")

    query = """
    mutation RedeployDeployment($id: String!) {
      deploymentRedeploy(id: $id) { id status }
    }
    """

    async def _post():
        import urllib.request

        body = json.dumps({"query": query, "variables": {"id": deployment_id}}).encode("utf-8")
        req = urllib.request.Request(
            RAILWAY_GRAPHQL_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        result = await asyncio.to_thread(_post)
    except Exception as exc:
        logger.exception("Railway redeploy failed")
        raise HTTPException(502, f"Railway redeploy request failed: {type(exc).__name__}")
    errors = result.get("errors")
    if errors:
        raise HTTPException(502, f"Railway redeploy rejected: {errors[0].get('message', errors)}")
    return result.get("data", {}).get("deploymentRedeploy", {})


# ── GitHub Actions screenshot dispatch (optional on-demand; scheduled anyway) ─
async def _dispatch_visual_capture() -> dict:
    token = github_dispatch_token()
    if not token:
        return {
            "dispatched": False,
            "reason": "MORE_GITHUB_DISPATCH_TOKEN not configured — the scheduled GitHub Actions workflow still captures screenshots.",
        }

    async def _post():
        import urllib.request

        body = json.dumps({"event_type": "capture-visual-state"}).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.github.com/repos/{GITHUB_REPOSITORY}/dispatches",
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status

    try:
        status = await asyncio.to_thread(_post)
        return {"dispatched": status in (200, 202, 204), "http_status": status}
    except Exception as exc:
        logger.warning("system_rollback: visual-capture dispatch failed: %s", exc)
        return {"dispatched": False, "reason": type(exc).__name__}


# ── Restore-point lifecycle ──────────────────────────────────────────────────
async def create_restore_point(actor: str, trigger: str, screenshot_item: Optional[dict] = None) -> dict:
    config = await _snapshot_config(db)
    now = datetime.now(timezone.utc).isoformat()
    rp = {
        "id": uuid.uuid4().hex,
        "created_at": now,
        "trigger": trigger,
        "actor": actor,
        "railway_deployment_id": current_deployment_id(),
        "git_commit_sha": current_git_sha(),
        "config": config,
        "screenshot_item": screenshot_item and {k: v for k, v in screenshot_item.items() if k != "_id"},
    }
    await db.system_restore_points.insert_one(rp)
    pruned = await _rotate_restore_points(db)
    return {"restore_point": rp, "pruned": pruned}


async def _latest_restore_point():
    doc = await db.system_restore_points.find({}, sort=[("created_at", -1), ("_id", -1)]).to_list(1)
    return doc[0] if doc else None


async def _run_rollback(rp: dict, actor: str, trigger: str) -> dict:
    """Execute the rollback engine with the ledger lockdown and webhook lock.

    Order: lock payments → restore configuration → unlock → redeploy prior
    image.  The redeploy runs outside the lock so provider retries land once
    the config layer is already consistent; ledgers are untouched throughout.
    """
    deployment_id = rp.get("railway_deployment_id") or ""
    if not deployment_id:
        raise HTTPException(500, "Restore point has no railway_deployment_id — cannot redeploy.")

    await set_rollback_lock(db, f"{trigger} rollback of {rp.get('id')}")
    try:
        restored = await _restore_config(db, rp.get("config") or {})
    finally:
        await clear_rollback_lock(db)

    redeploy = await _railway_redeploy(deployment_id)

    outcome = {
        "rolled_back": True,
        "restore_point_id": rp.get("id"),
        "deployment_id": deployment_id,
        "git_commit_sha": rp.get("git_commit_sha"),
        "config_collections_restored": restored,
        "redeploy": redeploy,
        "trigger": trigger,
        "actor": actor,
        "ledgers": "untouched",
    }
    return outcome


# ── Admin endpoints (internal trigger) ───────────────────────────────────────
class RollbackReq(BaseModel):
    restore_point_id: str
    confirm: bool = False


class RestorePointSummary(BaseModel):
    id: str
    created_at: str
    trigger: str
    actor: str
    railway_deployment_id: str
    git_commit_sha: str
    has_screenshot: bool
    config_collections: list




def _actor_name(user) -> str:
    """Derive an actor label from either the pydantic User model or a plain dict."""
    if isinstance(user, dict):
        return str(user.get("id") or user.get("email") or "unknown")
    return str(getattr(user, "id", None) or getattr(user, "email", None) or "unknown")

@router.get("/admin/system/health")
async def admin_health(user: dict = Depends(lambda: current_user)):
    assert_role(user, "admin", "executive_admin")
    return {
        "engine": "dual-trigger visual rollback",
        "webhook_secret_configured": bool(webhook_secret()),
        "railway_token_configured": bool(railway_token()),
        "current_deployment_id": current_deployment_id(),
        "current_git_sha": current_git_sha(),
        "max_restore_points": MAX_RESTORE_POINTS,
        "rollback_lock_active": await is_rollback_locked(db),
        "config_collections": list(RESTORE_CONFIG_COLLECTIONS),
        "ledger_collections_protected": len(LEDGER_COLLECTIONS),
    }


@router.get("/admin/system/restore-points")
async def list_restore_points(user: dict = Depends(lambda: current_user)):
    assert_role(user, "admin", "executive_admin")
    docs = await db.system_restore_points.find({}, sort=[("created_at", -1)]).to_list(50)
    return {
        "restore_points": [
            {
                "id": d.get("id"),
                "created_at": d.get("created_at"),
                "trigger": d.get("trigger"),
                "actor": d.get("actor"),
                "railway_deployment_id": d.get("railway_deployment_id"),
                "git_commit_sha": d.get("git_commit_sha"),
                "has_screenshot": bool(d.get("screenshot_item")),
                "config_collections": list((d.get("config") or {}).keys()),
            }
            for d in docs
        ]
    }


@router.get("/admin/system/restore-points/{restore_point_id}")
async def get_restore_point(restore_point_id: str, user: dict = Depends(lambda: current_user)):
    assert_role(user, "admin", "executive_admin")
    doc = await db.system_restore_points.find_one({"id": restore_point_id})
    if not doc:
        raise HTTPException(404, "Restore point not found")
    return {"restore_point": doc}


@router.post("/admin/system/restore-points")
async def create_restore_point_route(user: dict = Depends(lambda: current_user)):
    assert_role(user, "admin", "executive_admin")
    actor = _actor_name(user)
    rp = await create_restore_point(actor=actor, trigger="admin")
    dispatch = await _dispatch_visual_capture()
    await audit(
        actor,
        "system.restore_point.created",
        target=rp["restore_point"]["id"],
        meta={"pruned": rp["pruned"], "screenshot_dispatch": dispatch},
    )
    return {"created": True, "restore_point": rp["restore_point"], "screenshot_dispatch": dispatch}


@router.post("/admin/system/rollback")
async def admin_rollback(body: RollbackReq, user: dict = Depends(lambda: current_user)):
    assert_role(user, "admin", "executive_admin")
    if not body.confirm:
        raise HTTPException(400, "Rollback requires confirm=true — this operation restores configuration and redeploys a prior image.")
    rp = await db.system_restore_points.find_one({"id": body.restore_point_id})
    if not rp:
        raise HTTPException(404, "Restore point not found")
    actor = _actor_name(user)
    outcome = await _run_rollback(rp, actor=actor, trigger="admin")
    await audit(actor, "system.rollback.executed", target=rp.get("id"), meta=outcome)
    return outcome


@router.get("/admin/system/webhook-queue")
async def webhook_queue(user: dict = Depends(lambda: current_user)):
    assert_role(user, "admin", "executive_admin")
    docs = await db.deferred_webhooks.find({}, sort=[("received_at", -1)]).to_list(100)
    return {
        "deferred": [
            {
                "provider": d.get("provider"),
                "status": d.get("status"),
                "received_at": d.get("received_at"),
                "payload_b64": d.get("payload_b64"),
            }
            for d in docs
        ]
    }


# ── External trigger endpoints ───────────────────────────────────────────────
@router.post("/v1/system/emergency-revert")
async def emergency_revert(request: Request):
    """External emergency rollback webhook (HMAC-SHA256, X-MORE-Signature).

    Rolls the platform back to the most recent restore point: restores the
    configuration snapshot and redeploys that deployment.  Ledgers are
    untouched.  Requires MORE_ROLLBACK_WEBHOOK_SECRET in the environment.
    """
    if not webhook_secret():
        raise HTTPException(503, "MORE_ROLLBACK_WEBHOOK_SECRET is not configured — emergency revert is disabled.")
    payload = await request.body()
    provided = request.headers.get("x-more-signature", "")
    if not sign_ok(payload, provided):
        raise HTTPException(401, "Invalid X-MORE-Signature")
    rp = await _latest_restore_point()
    if not rp:
        raise HTTPException(404, "No restore point exists yet — create one before requesting a revert.")
    outcome = await _run_rollback(rp, actor="webhook:emergency-revert", trigger="webhook")
    await audit("webhook:emergency-revert", "system.rollback.executed", target=rp.get("id"), meta={
        "deployment_id": outcome["deployment_id"], "config_collections_restored": outcome["config_collections_restored"],
    })
    return outcome


@router.post("/v1/system/visual-state")
async def ingest_visual_state(request: Request):
    """Ingest screenshots from the free GitHub Actions capture workflow.

    Body: {"urls": {"landing": "<gzip+base64>", "login": "...", "dashboard": "..."},
           "captured_at": "..."}.  Signed with the same
    MORE_ROLLBACK_WEBHOOK_SECRET (X-MORE-Signature).  Attaches to the latest
    restore point; creates one when none exists yet.
    """
    if not webhook_secret():
        raise HTTPException(503, "MORE_ROLLBACK_WEBHOOK_SECRET is not configured — visual-state ingest is disabled.")
    payload = await request.body()
    provided = request.headers.get("x-more-signature", "")
    if not sign_ok(payload, provided):
        raise HTTPException(401, "Invalid X-MORE-Signature")
    try:
        body = json.loads(payload)
    except Exception:
        raise HTTPException(400, "Invalid JSON body")
    urls = body.get("urls") or {}
    if not isinstance(urls, dict) or not any(str(v) for v in urls.values()):
        raise HTTPException(400, "Body must include at least one screenshot under 'urls'")
    item = {
        "urls": {k: str(v) for k, v in urls.items() if v},
        "captured_at": body.get("captured_at") or datetime.now(timezone.utc).isoformat(),
    }
    rp = await _latest_restore_point()
    if rp:
        await db.system_restore_points.update_one(
            {"id": rp.get("id")},
            {"$set": {"screenshot_item": item}},
        )
        target = rp.get("id")
    else:
        created = await create_restore_point(actor="workflow:visual-state", trigger="visual", screenshot_item=item)
        target = created["restore_point"]["id"]
    await audit("workflow:visual-state", "system.visual_state.ingested", target=target, meta={"urls": list(item["urls"])})
    return {"ingested": True, "restore_point_id": target, "urls": list(item["urls"])}