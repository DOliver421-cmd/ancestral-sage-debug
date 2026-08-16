"""
auditor — Platform Prices + The Auditor — price tiers CRUD, public pricing, read-only financial ledger, reporting, debt and risk tracking.

Extracted verbatim from backend/server.py (monolith refactor, slice 12).
Shared state (db, current_user, ...) is bound by server.py via bind()
at include time — no circular imports.
"""
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("lcewai")
router = APIRouter(tags=['admin', 'prices', 'auditor'])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None


def bind(_db, _current_user):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user
    
    db = _db
    current_user = _current_user


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
    def dep(user: User = Depends(_dep_current_user)) -> User:
        if not user or user.role not in ROLE_RANK or not any(
            ROLE_RANK.get(user.role, 0) >= ROLE_RANK.get(r, 0) for r in roles
        ):
            raise HTTPException(403, "Insufficient permissions")
        return user
    return dep


# ── Platform Prices ──────────────────────────────────────────────────────────
# Collection: platform_prices  { id, key, value, description, last_modified_by, last_modified_at }

@router.get("/admin/prices")
async def list_prices(user: User = Depends(_require_rank("admin"))):
    docs = await db.platform_prices.find({}, {"_id": 0}).sort("key", 1).to_list(length=500)
    return {"prices": docs}

@router.post("/admin/prices")
async def create_price(body: dict, user: User = Depends(_require_rank("admin"))):
    key   = (body.get("key") or "").strip()
    value = body.get("value")
    desc  = (body.get("description") or "").strip()
    if not key:
        raise HTTPException(400, "key is required")
    if value is None:
        raise HTTPException(400, "value is required")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise HTTPException(400, "value must be a number")
    existing = await db.platform_prices.find_one({"key": key})
    if existing:
        raise HTTPException(409, f"Price key '{key}' already exists — use PATCH to update")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "key": key,
        "value": value,
        "description": desc,
        "last_modified_by": user.id,
        "last_modified_at": now,
    }
    await db.platform_prices.insert_one(doc)
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "price_create", "actor": user.id,
        "detail": f"Created price key={key} value={value}", "at": now,
    })
    return {k: v for k, v in doc.items() if k != "_id"}

@router.patch("/admin/prices/{price_id}")
async def update_price(price_id: str, body: dict, user: User = Depends(_require_rank("admin"))):
    doc = await db.platform_prices.find_one({"id": price_id})
    if not doc:
        raise HTTPException(404, "Price not found")
    updates: dict = {}
    if "value" in body:
        try:
            updates["value"] = float(body["value"])
        except (TypeError, ValueError):
            raise HTTPException(400, "value must be a number")
    if "description" in body:
        updates["description"] = (body["description"] or "").strip()
    if "key" in body:
        new_key = (body["key"] or "").strip()
        if not new_key:
            raise HTTPException(400, "key cannot be empty")
        conflict = await db.platform_prices.find_one({"key": new_key, "id": {"$ne": price_id}})
        if conflict:
            raise HTTPException(409, f"Key '{new_key}' already in use")
        updates["key"] = new_key
    if not updates:
        raise HTTPException(400, "No fields to update")
    now = datetime.now(timezone.utc).isoformat()
    updates["last_modified_by"] = user.id
    updates["last_modified_at"] = now
    await db.platform_prices.update_one({"id": price_id}, {"$set": updates})
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "price_update", "actor": user.id,
        "detail": f"Updated price id={price_id} fields={list(updates.keys())}", "at": now,
    })
    updated = await db.platform_prices.find_one({"id": price_id}, {"_id": 0})
    return updated

@router.delete("/admin/prices/{price_id}")
async def delete_price(price_id: str, user: User = Depends(_require_rank("executive_admin"))):
    doc = await db.platform_prices.find_one({"id": price_id})
    if not doc:
        raise HTTPException(404, "Price not found")
    await db.platform_prices.delete_one({"id": price_id})
    now = datetime.now(timezone.utc).isoformat()
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "price_delete", "actor": user.id,
        "detail": f"Deleted price key={doc.get('key')} id={price_id}", "at": now,
    })
    return {"deleted": price_id}

@router.get("/prices/public")
async def public_prices():
    """Returns all price keys and values — no auth. Used by frontend to display current pricing."""
    docs = await db.platform_prices.find({}, {"_id": 0, "id": 1, "key": 1, "value": 1, "description": 1}).sort("key", 1).to_list(length=500)
    return {"prices": docs}

# ── The Auditor — read-only ledger, reporting, and value tracking ─────────────
# Collection: auditor_ledger
# Schema: { id, delivery_date, commit_sha, category, description, dollar_value,
#           evidence, status, risk_level, created_at, created_by }
#
# Categories: revenue_restored | risk_eliminated | cost_avoided | debt_repaid | governance
# Statuses:   PASS | FAIL | UNVERIFIED | INCOMPLETE | NO_EVIDENCE
# Risk levels: none | low | medium | high | critical
#
# Access: admin+ (read). Only The Director or Finance Director adds entries.
# The Auditor persona never modifies state.

_AUDITOR_CATEGORIES = {"revenue_restored", "risk_eliminated", "cost_avoided", "debt_repaid", "governance"}
_AUDITOR_STATUSES   = {"PASS", "FAIL", "UNVERIFIED", "INCOMPLETE", "NO_EVIDENCE"}
_AUDITOR_RISK       = {"none", "low", "medium", "high", "critical"}

@router.get("/auditor/summary")
async def auditor_summary(user: User = Depends(_require_rank("admin"))):
    """Running ledger totals by category. Read-only."""
    pipeline = [
        {"$group": {
            "_id": "$category",
            "total_value": {"$sum": "$dollar_value"},
            "count": {"$sum": 1},
            "verified_value": {"$sum": {"$cond": [{"$eq": ["$status", "PASS"]}, "$dollar_value", 0]}},
            "unverified_count": {"$sum": {"$cond": [{"$eq": ["$status", "UNVERIFIED"]}, 1, 0]}},
        }},
        {"$sort": {"total_value": -1}},
    ]
    by_category = await db.auditor_ledger.aggregate(pipeline).to_list(length=20)
    total = sum(r["total_value"] for r in by_category)
    verified = sum(r["verified_value"] for r in by_category)
    unverified = sum(r["unverified_count"] for r in by_category)
    risk_counts = {}
    async for doc in db.auditor_ledger.find({}, {"_id": 0, "risk_level": 1}):
        lvl = doc.get("risk_level", "none")
        risk_counts[lvl] = risk_counts.get(lvl, 0) + 1
    recent = await db.auditor_ledger.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    return {
        "total_dollar_value": total,
        "verified_dollar_value": verified,
        "unverified_count": unverified,
        "by_category": by_category,
        "risk_distribution": risk_counts,
        "recent_entries": recent,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/auditor/ledger")
async def auditor_ledger_list(
    category: str = None,
    status: str = None,
    risk_level: str = None,
    limit: int = 50,
    skip: int = 0,
    user: User = Depends(_require_rank("admin")),
):
    """Paginated ledger. All filters optional. Read-only."""
    q: dict = {}
    if category and category in _AUDITOR_CATEGORIES:
        q["category"] = category
    if status and status in _AUDITOR_STATUSES:
        q["status"] = status
    if risk_level and risk_level in _AUDITOR_RISK:
        q["risk_level"] = risk_level
    limit = min(max(1, limit), 200)
    skip = max(0, skip)
    docs = await db.auditor_ledger.find(q, {"_id": 0}).sort("delivery_date", -1).skip(skip).limit(limit).to_list(limit)
    total_count = await db.auditor_ledger.count_documents(q)
    return {"entries": docs, "total": total_count, "limit": limit, "skip": skip}

@router.post("/auditor/ledger")
async def auditor_add_entry(body: dict, user: User = Depends(_require_rank("admin"))):
    """Director or Finance Director records a verified delivery. The Auditor does not call this."""
    required = ["description", "category", "dollar_value", "evidence", "status"]
    for f in required:
        if f not in body or body[f] is None:
            raise HTTPException(400, f"Field '{f}' is required")
    if body["category"] not in _AUDITOR_CATEGORIES:
        raise HTTPException(400, f"category must be one of: {sorted(_AUDITOR_CATEGORIES)}")
    if body["status"] not in _AUDITOR_STATUSES:
        raise HTTPException(400, f"status must be one of: {sorted(_AUDITOR_STATUSES)}")
    risk = body.get("risk_level", "none")
    if risk not in _AUDITOR_RISK:
        raise HTTPException(400, f"risk_level must be one of: {sorted(_AUDITOR_RISK)}")
    try:
        dollar_value = float(body["dollar_value"])
    except (TypeError, ValueError):
        raise HTTPException(400, "dollar_value must be a number")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "delivery_date": body.get("delivery_date") or now,
        "commit_sha": (body.get("commit_sha") or "").strip() or None,
        "category": body["category"],
        "description": body["description"].strip(),
        "dollar_value": dollar_value,
        "evidence": body["evidence"].strip(),
        "status": body["status"],
        "risk_level": risk,
        "created_at": now,
        "created_by": user.id,
    }
    await db.auditor_ledger.insert_one(doc)
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "auditor.entry.added", "actor": user.id,
        "detail": f"Auditor entry: {body['description'][:80]} | ${dollar_value:.2f} | {body['status']}", "at": now,
    })
    return {k: v for k, v in doc.items() if k != "_id"}

@router.patch("/auditor/ledger/{entry_id}")
async def auditor_update_entry(entry_id: str, body: dict, user: User = Depends(_require_rank("admin"))):
    """Correct status, dollar value, or evidence on an existing entry. Audit-logged."""
    doc = await db.auditor_ledger.find_one({"id": entry_id})
    if not doc:
        raise HTTPException(404, "Entry not found")
    allowed_fields = {"status", "dollar_value", "evidence", "risk_level", "description", "commit_sha"}
    updates: dict = {}
    for field in allowed_fields:
        if field in body:
            if field == "status" and body[field] not in _AUDITOR_STATUSES:
                raise HTTPException(400, f"Invalid status: {body[field]}")
            if field == "risk_level" and body[field] not in _AUDITOR_RISK:
                raise HTTPException(400, f"Invalid risk_level: {body[field]}")
            if field == "dollar_value":
                try:
                    updates[field] = float(body[field])
                except (TypeError, ValueError):
                    raise HTTPException(400, "dollar_value must be a number")
            else:
                updates[field] = body[field]
    if not updates:
        raise HTTPException(400, "No valid fields to update")
    now = datetime.now(timezone.utc).isoformat()
    updates["updated_at"] = now
    updates["updated_by"] = user.id
    await db.auditor_ledger.update_one({"id": entry_id}, {"$set": updates})
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "auditor.entry.updated", "actor": user.id,
        "detail": f"Updated entry {entry_id}: fields={list(updates.keys())}", "at": now,
    })
    updated = await db.auditor_ledger.find_one({"id": entry_id}, {"_id": 0})
    return updated

@router.get("/auditor/report")
async def auditor_report(
    start: str = None,
    end: str = None,
    user: User = Depends(_require_rank("admin")),
):
    """Full report for a date range. Includes ledger, totals, debt, risks."""
    q: dict = {}
    if start:
        q.setdefault("delivery_date", {})["$gte"] = start
    if end:
        q.setdefault("delivery_date", {})["$lte"] = end
    entries = await db.auditor_ledger.find(q, {"_id": 0}).sort("delivery_date", -1).to_list(500)
    total = sum(e.get("dollar_value", 0) for e in entries)
    verified = sum(e.get("dollar_value", 0) for e in entries if e.get("status") == "PASS")
    by_cat: dict = {}
    for e in entries:
        cat = e.get("category", "unknown")
        by_cat[cat] = by_cat.get(cat, 0) + e.get("dollar_value", 0)
    debt_items = [e for e in entries if e.get("status") in ("INCOMPLETE", "FAIL")]
    risk_items = [e for e in entries if e.get("risk_level") in ("high", "critical")]
    unverified = [e for e in entries if e.get("status") == "UNVERIFIED"]
    return {
        "report_period": {"start": start or "all-time", "end": end or "present"},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": user.id,
        "summary": {
            "total_entries": len(entries),
            "total_dollar_value": total,
            "verified_dollar_value": verified,
            "unverified_dollar_value": total - verified,
        },
        "by_category": by_cat,
        "entries": entries,
        "debt_items": debt_items,
        "risk_items": risk_items,
        "unverified_items": unverified,
        "flags": {
            "unverified_count": len(unverified),
            "incomplete_count": len([e for e in entries if e.get("status") == "INCOMPLETE"]),
            "high_risk_count": len(risk_items),
            "no_evidence_count": len([e for e in entries if e.get("status") == "NO_EVIDENCE"]),
        },
    }

@router.get("/auditor/debt")
async def auditor_debt(user: User = Depends(_require_rank("admin"))):
    """Outstanding technical debt and incomplete items. Read-only."""
    items = await db.auditor_ledger.find(
        {"status": {"$in": ["INCOMPLETE", "FAIL", "UNVERIFIED"]}},
        {"_id": 0},
    ).sort("risk_level", -1).to_list(200)
    total_debt_value = sum(i.get("dollar_value", 0) for i in items if i.get("status") in ("INCOMPLETE", "FAIL"))
    return {
        "debt_items": items,
        "total_debt_count": len(items),
        "total_debt_value": total_debt_value,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/auditor/risks")
async def auditor_risks(user: User = Depends(_require_rank("admin"))):
    """Unresolved risk items. Read-only."""
    items = await db.auditor_ledger.find(
        {"risk_level": {"$in": ["high", "critical"]}},
        {"_id": 0},
    ).sort("delivery_date", -1).to_list(200)
    return {
        "risk_items": items,
        "critical_count": sum(1 for i in items if i.get("risk_level") == "critical"),
        "high_count": sum(1 for i in items if i.get("risk_level") == "high"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
