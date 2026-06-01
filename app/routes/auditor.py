"""app/routes/auditor.py — The Auditor ledger and reporting endpoints.

Extracted from backend/server.py lines 11121–11338. No logic changed.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.database import db
from app.models.user import User
from app.security.auth import require_role

router = APIRouter()

_AUDITOR_CATEGORIES = {"revenue_restored", "risk_eliminated", "cost_avoided", "debt_repaid", "governance"}
_AUDITOR_STATUSES   = {"PASS", "FAIL", "UNVERIFIED", "INCOMPLETE", "NO_EVIDENCE"}
_AUDITOR_RISK       = {"none", "low", "medium", "high", "critical"}


@router.get("/auditor/summary")
async def auditor_summary(user: User = Depends(require_role("admin"))):
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
    user: User = Depends(require_role("admin")),
):
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
async def auditor_add_entry(body: dict, user: User = Depends(require_role("admin"))):
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
async def auditor_update_entry(entry_id: str, body: dict, user: User = Depends(require_role("admin"))):
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
    user: User = Depends(require_role("admin")),
):
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
async def auditor_debt(user: User = Depends(require_role("admin"))):
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
async def auditor_risks(user: User = Depends(require_role("admin"))):
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
