"""
WAI Institute CRM Routes
Sales pipeline management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from .models import (
    Lead, LeadCreate, LeadStatus, LeadSource,
    Opportunity, OpportunityCreate, OpportunityUpdate, OpportunityStage,
    ActivityLogEntry, SalesMetrics, BudgetRange,
    DecisionMaker
)

router = APIRouter(prefix="/api/crm", tags=["crm"])


# ============================================================================
# LEAD ENDPOINTS
# ============================================================================

def _get_current_user(request: Request):
    """Extract current user from request state"""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


@router.post("/leads", response_model=Lead)
async def create_lead(
    lead_create: LeadCreate,
    request: Request,
    current_user: dict = Depends(_get_current_user)
):
    """
    Create a new sales lead

    ✅ Authentication required (admin/steward only)

    Example:
    {
        "company_name": "Acme Corp",
        "company_size": 500,
        "industry": "Technology",
        "budget_range": "100-500K",
        "decision_maker": {
            "name": "John Doe",
            "title": "CTO",
            "email": "john@acme.com",
            "phone": "+1-555-1234"
        },
        "source": "inbound",
        "notes": "Referred by existing customer ABC"
    }
    """
    # Verify authorization (admin/steward only)
    allowed_roles = ["admin", "steward", "elder", "executive_admin"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="CRM access requires admin or steward role")

    leads = request.app.state.db.leads

    lead_doc = {
        "company_name": lead_create.company_name,
        "company_size": lead_create.company_size,
        "industry": lead_create.industry,
        "budget_range": lead_create.budget_range.value if lead_create.budget_range else None,
        "decision_maker": lead_create.decision_maker.dict(),
        "source": lead_create.source.value,
        "status": lead_create.status.value,
        "score": 0,
        "owner_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_contact": None,
        "notes": lead_create.notes,
    }

    result = await leads.insert_one(lead_doc)

    return Lead(**lead_doc, id=str(result.inserted_id))


@router.get("/leads", response_model=List[Lead])
async def list_leads(
    request: Request,
    current_user: dict = Depends(_get_current_user),
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    score_min: int = Query(0),
    limit: int = Query(50, le=100),
    skip: int = Query(0),
):
    """
    List leads with filtering

    ✅ Authentication required (admin/steward only)

    Query params:
    - status: lead|prospect|opportunity|proposal|contract|customer|lost
    - source: inbound|referral|event|cold_outreach|partner|competitor_switch
    - owner_id: Sales rep assigned to lead
    - score_min: Minimum lead score (0-100)
    - limit: Number to return (default 50, max 100)
    - skip: Pagination offset (default 0)
    """
    # Verify authorization (admin/steward only)
    allowed_roles = ["admin", "steward", "elder", "executive_admin"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="CRM access requires admin or steward role")

    leads = request.app.state.db.leads

    filter_query = {}

    if status:
        filter_query["status"] = status
    if source:
        filter_query["source"] = source
    if owner_id:
        filter_query["owner_id"] = owner_id

    filter_query["score"] = {"$gte": score_min}

    lead_docs = await leads.find(filter_query) \
        .sort("score", -1) \
        .skip(skip) \
        .limit(limit) \
        .to_list(None)

    return [Lead(**doc, id=str(doc["_id"])) for doc in lead_docs]


@router.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str, request: Request):
    """Get a specific lead"""
    leads = request.app.state.db.leads

    lead_doc = await leads.find_one({"_id": ObjectId(lead_id)})

    if not lead_doc:
        raise HTTPException(status_code=404, detail="Lead not found")

    return Lead(**lead_doc, id=str(lead_doc["_id"]))


@router.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(
    lead_id: str,
    status: Optional[str] = None,
    owner_id: Optional[str] = None,
    score: Optional[int] = None,
    request: Request = None,
):
    """
    Update a lead

    Query params:
    - status: New status
    - owner_id: Assign to sales rep
    - score: Update lead score (0-100)
    """
    leads = request.app.state.db.leads

    update_data = {"updated_at": datetime.utcnow()}

    if status:
        update_data["status"] = status
    if owner_id:
        update_data["owner_id"] = owner_id
    if score is not None:
        update_data["score"] = min(100, max(0, score))

    result = await leads.update_one(
        {"_id": ObjectId(lead_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead_doc = await leads.find_one({"_id": ObjectId(lead_id)})
    return Lead(**lead_doc, id=str(lead_doc["_id"]))


# ============================================================================
# OPPORTUNITY ENDPOINTS
# ============================================================================

@router.post("/opportunities", response_model=Opportunity)
async def create_opportunity(
    opportunity_create: OpportunityCreate,
    request: Request
):
    """
    Create sales opportunity from a lead

    Example:
    {
        "lead_id": "507f1f77bcf86cd799439011",
        "deal_name": "Acme Corp Enterprise License",
        "deal_value": 150000,
        "stage": "discovery",
        "probability": 25,
        "expected_close_date": "2026-08-15",
        "notes": "Initial interest, scheduling demo"
    }
    """
    opportunities = request.app.state.db.opportunities
    leads = request.app.state.db.leads

    # Verify lead exists
    lead = await leads.find_one({"_id": ObjectId(opportunity_create.lead_id)})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    opportunity_doc = {
        "lead_id": opportunity_create.lead_id,
        "deal_name": opportunity_create.deal_name,
        "deal_value": opportunity_create.deal_value,
        "stage": opportunity_create.stage.value,
        "probability": opportunity_create.probability,
        "owner_id": None,
        "expected_close_date": opportunity_create.expected_close_date,
        "actual_close_date": None,
        "contract_id": None,
        "notes": opportunity_create.notes,
        "interactions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await opportunities.insert_one(opportunity_doc)

    # Update lead status to "opportunity"
    await leads.update_one(
        {"_id": ObjectId(opportunity_create.lead_id)},
        {"$set": {"status": "opportunity", "updated_at": datetime.utcnow()}}
    )

    return Opportunity(**opportunity_doc, id=str(result.inserted_id))


@router.get("/opportunities", response_model=List[Opportunity])
async def list_opportunities(
    request: Request,
    stage: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    probability_min: int = Query(0, le=100),
    limit: int = Query(50, le=100),
):
    """
    List opportunities by sales stage

    Query params:
    - stage: discovery|demo|proposal|negotiation|close|closed_won|closed_lost
    - owner_id: Filter by assigned sales rep
    - probability_min: Minimum probability (0-100)
    - limit: Number to return (default 50)
    """
    opportunities = request.app.state.db.opportunities

    filter_query = {"probability": {"$gte": probability_min}}

    if stage:
        filter_query["stage"] = stage
    if owner_id:
        filter_query["owner_id"] = owner_id

    opp_docs = await opportunities.find(filter_query) \
        .sort([("expected_close_date", 1), ("probability", -1)]) \
        .limit(limit) \
        .to_list(None)

    return [Opportunity(**doc, id=str(doc["_id"])) for doc in opp_docs]


@router.put("/opportunities/{opportunity_id}", response_model=Opportunity)
async def update_opportunity(
    opportunity_id: str,
    update: OpportunityUpdate,
    request: Request
):
    """Update an opportunity"""
    opportunities = request.app.state.db.opportunities

    update_data = {"updated_at": datetime.utcnow()}

    if update.stage:
        update_data["stage"] = update.stage.value
    if update.probability is not None:
        update_data["probability"] = min(100, max(0, update.probability))
    if update.deal_value:
        update_data["deal_value"] = update.deal_value
    if update.expected_close_date:
        update_data["expected_close_date"] = update.expected_close_date
    if update.notes:
        update_data["notes"] = update.notes

    result = await opportunities.update_one(
        {"_id": ObjectId(opportunity_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp_doc = await opportunities.find_one({"_id": ObjectId(opportunity_id)})
    return Opportunity(**opp_doc, id=str(opp_doc["_id"]))


@router.post("/opportunities/{opportunity_id}/close-won", response_model=Opportunity)
async def close_opportunity_won(opportunity_id: str, request: Request):
    """Close opportunity as won (move to customer)"""
    opportunities = request.app.state.db.opportunities
    leads = request.app.state.db.leads

    opp_doc = await opportunities.find_one({"_id": ObjectId(opportunity_id)})
    if not opp_doc:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Update opportunity
    now = datetime.utcnow()
    await opportunities.update_one(
        {"_id": ObjectId(opportunity_id)},
        {
            "$set": {
                "stage": "closed_won",
                "probability": 100,
                "actual_close_date": now,
                "updated_at": now,
            }
        }
    )

    # Update lead to customer
    await leads.update_one(
        {"_id": ObjectId(opp_doc["lead_id"])},
        {"$set": {"status": "customer", "updated_at": now}}
    )

    opp_doc = await opportunities.find_one({"_id": ObjectId(opportunity_id)})
    return Opportunity(**opp_doc, id=str(opp_doc["_id"]))


# ============================================================================
# SALES METRICS
# ============================================================================

@router.get("/metrics/pipeline")
async def get_pipeline_metrics(request: Request):
    """Get sales pipeline metrics"""
    opportunities = request.app.state.db.opportunities

    pipeline = [
        {
            "$group": {
                "_id": "$stage",
                "count": {"$sum": 1},
                "total_value": {"$sum": "$deal_value"},
                "avg_probability": {"$avg": "$probability"},
            }
        },
        {"$sort": {"_id": 1}}
    ]

    stages = await opportunities.aggregate(pipeline).to_list(None)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "by_stage": stages,
        "total_pipeline_value": sum(s["total_value"] for s in stages),
        "weighted_forecast": sum(
            s["total_value"] * (s["avg_probability"] / 100) for s in stages
        ),
    }


@router.get("/metrics/forecast")
async def get_sales_forecast(request: Request, months: int = Query(3, le=12)):
    """
    Get sales forecast by expected close date

    Returns revenue expected to close in each month
    """
    opportunities = request.app.state.db.opportunities

    closed_won = await opportunities.find({
        "stage": "closed_won"
    }).to_list(None)

    total_closed = sum(opp["deal_value"] for opp in closed_won)

    # Get weighted forecast (probability-adjusted)
    open_opps = await opportunities.find({
        "stage": {"$nin": ["closed_won", "closed_lost"]}
    }).to_list(None)

    weighted_forecast = sum(
        opp["deal_value"] * (opp["probability"] / 100)
        for opp in open_opps
    )

    return {
        "actual_closed_won": total_closed,
        "weighted_forecast_open": weighted_forecast,
        "total_forecast": total_closed + weighted_forecast,
    }


@router.get("/metrics/summary")
async def get_sales_summary(request: Request):
    """Get complete sales metrics summary"""
    opportunities = request.app.state.db.opportunities
    leads = request.app.state.db.leads

    total_leads = await leads.count_documents({})
    total_opportunities = await opportunities.count_documents({})
    closed_won = await opportunities.count_documents({"stage": "closed_won"})
    closed_lost = await opportunities.count_documents({"stage": "closed_lost"})

    win_rate = (closed_won / (closed_won + closed_lost) * 100) if (closed_won + closed_lost) > 0 else 0

    # Get total deal values
    closed_value = await opportunities.aggregate([
        {"$match": {"stage": "closed_won"}},
        {"$group": {"_id": None, "total": {"$sum": "$deal_value"}}}
    ]).to_list(1)

    open_value = await opportunities.aggregate([
        {"$match": {"stage": {"$nin": ["closed_won", "closed_lost"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$deal_value"}}}
    ]).to_list(1)

    return {
        "total_leads": total_leads,
        "total_opportunities": total_opportunities,
        "closed_won": closed_won,
        "closed_lost": closed_lost,
        "win_rate_percent": round(win_rate, 1),
        "closed_revenue": closed_value[0]["total"] if closed_value else 0,
        "open_pipeline_value": open_value[0]["total"] if open_value else 0,
    }
