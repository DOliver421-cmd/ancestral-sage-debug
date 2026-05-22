"""
Course Licensing & Contractor Training API Routes
Endpoints for contractor license management, team members, and lab completions.
"""

from fastapi import APIRouter, Request, HTTPException, Query
from datetime import datetime
from .course_licensing import (
    init_course_licensing,
    create_contractor_license,
    add_team_member,
    record_lab_completion,
    get_contractor_dashboard,
    estimate_contractor_arv,
    CONTRACTOR_TIERS,
)
from .course_multilingual import (
    COURSE_LANGUAGES,
    UI_STRINGS,
    ONLINE_LABS_MULTILINGUAL,
    get_course_content,
    get_ui_string,
)

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/tiers")
async def list_contractor_tiers():
    """List available contractor training tiers"""
    return {
        "status": "success",
        "tiers": CONTRACTOR_TIERS,
    }


@router.get("/languages")
async def list_languages():
    """List available course languages"""
    return {
        "status": "success",
        "languages": COURSE_LANGUAGES,
    }


@router.get("/labs")
async def list_labs(language: str = Query("en")):
    """List all available labs in requested language"""
    if language not in COURSE_LANGUAGES:
        language = "en"

    labs = []
    for lab_slug, content in ONLINE_LABS_MULTILINGUAL.items():
        lab_content = get_course_content(lab_slug, language)
        if lab_content:
            labs.append({
                "slug": lab_slug,
                "title": lab_content.get("title", ""),
                "summary": lab_content.get("summary", ""),
                "language": language,
            })

    return {
        "status": "success",
        "language": language,
        "labs": labs,
    }


@router.get("/labs/{lab_slug}")
async def get_lab_details(lab_slug: str, language: str = Query("en")):
    """Get detailed course content for a specific lab in requested language"""
    if language not in COURSE_LANGUAGES:
        language = "en"

    content = get_course_content(lab_slug, language)
    if not content:
        raise HTTPException(status_code=404, detail="Lab not found")

    return {
        "status": "success",
        "slug": lab_slug,
        "language": language,
        "content": content,
    }


@router.get("/ui/{key}")
async def get_ui_text(key: str, language: str = Query("en")):
    """Get UI strings in requested language"""
    if language not in COURSE_LANGUAGES:
        language = "en"

    text = get_ui_string(key, language)
    return {
        "status": "success",
        "key": key,
        "language": language,
        "text": text,
    }


@router.post("/license/create")
async def create_license(
    contractor_id: str,
    business_name: str,
    tier: str,
    request: Request,
    language: str = Query("en"),
):
    """Create a new contractor training license"""
    db = request.app.state.db
    if language not in COURSE_LANGUAGES:
        language = "en"
    result = await create_contractor_license(db, contractor_id, business_name, tier, language)
    if result["status"] != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to create license"))
    return result


@router.get("/license/{contractor_id}")
async def get_license(
    contractor_id: str,
    request: Request,
):
    """Get contractor's license and team"""
    db = request.app.state.db
    license = await db.course_licenses.find_one({"contractor_id": contractor_id})
    if not license:
        raise HTTPException(status_code=404, detail="License not found")

    license["_id"] = str(license["_id"])
    return {"status": "success", "license": license}


@router.post("/license/{contractor_id}/add-member")
async def add_member(
    contractor_id: str,
    name: str,
    email: str,
    request: Request,
    language: str = Query(None),
):
    """Add a team member to contractor's license with optional language preference"""
    db = request.app.state.db
    if language and language not in COURSE_LANGUAGES:
        language = None
    result = await add_team_member(db, contractor_id, name, email, language)
    if result["status"] != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to add member"))
    return result


@router.post("/completion")
async def record_completion(
    contractor_id: str,
    team_member_id: str,
    lab_slug: str,
    time_minutes: int,
    score: float = None,
    request: Request = None,
):
    """Record a lab completion"""
    db = request.app.state.db
    result = await record_lab_completion(db, contractor_id, team_member_id, lab_slug, time_minutes, score)
    return result


@router.get("/dashboard/{contractor_id}")
async def get_dashboard(
    contractor_id: str,
    request: Request,
):
    """Get contractor dashboard with license, team, and completion stats"""
    db = request.app.state.db
    result = await get_contractor_dashboard(db, contractor_id)
    if result["status"] != "success":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


@router.post("/estimate-arv")
async def estimate_arv(
    crew_size: int,
    specialization: str = "mixed",
):
    """Estimate annual recurring value for sales pipeline forecasting"""
    arv = estimate_contractor_arv(crew_size, specialization)
    return {
        "status": "success",
        "crew_size": crew_size,
        "specialization": specialization,
        "estimated_monthly": arv / 12,
        "estimated_annual": arv,
    }


@router.get("/leads")
async def list_contractor_leads(
    request: Request,
    stage: str = Query(None),
    source: str = Query(None),
    min_crew_size: int = Query(0),
    skip: int = Query(0),
    limit: int = Query(100),
):
    """List contractor leads from CRM"""
    db = request.app.state.db
    filter_dict = {"industry": "electrical_contracting"}
    if stage:
        filter_dict["stage"] = stage
    if source:
        filter_dict["source"] = source
    if min_crew_size > 0:
        filter_dict["crew_size"] = {"$gte": min_crew_size}

    leads = await db.contractor_leads.find(filter_dict).skip(skip).limit(limit).to_list(limit)
    for lead in leads:
        lead["_id"] = str(lead["_id"])

    total = await db.contractor_leads.count_documents(filter_dict)

    return {
        "status": "success",
        "total": total,
        "leads": leads,
    }


@router.post("/leads/import")
async def import_contractor_lead(
    company_name: str,
    crew_size: int,
    specialization: str,
    contact_email: str,
    request: Request,
    phone: str = None,
    source: str = "web_search",
):
    """Add a contractor lead to CRM for sales outreach"""
    db = request.app.state.db
    arv = estimate_contractor_arv(crew_size, specialization)

    lead_doc = {
        "company_name": company_name,
        "industry": "electrical_contracting",
        "crew_size": crew_size,
        "specialization": specialization,
        "contact_email": contact_email,
        "phone": phone,
        "source": source,
        "stage": "aware",
        "estimated_value": arv,
        "created_at": datetime.utcnow(),
    }

    result = await db.contractor_leads.insert_one(lead_doc)

    return {
        "status": "success",
        "lead_id": str(result.inserted_id),
        "estimated_annual_value": arv,
    }


@router.get("/analytics/contractor-market")
async def contractor_market_analytics(
    request: Request,
):
    """Analytics: contractor market size, growth, conversion"""
    db = request.app.state.db

    # Total contractors
    total_contractors = await db.course_licenses.count_documents({})

    # By tier
    tier_dist = await db.course_licenses.aggregate([
        {"$group": {"_id": "$tier", "count": {"$sum": 1}}},
    ]).to_list(None)

    # Average team size
    licenses = await db.course_licenses.find({}).to_list(None)
    avg_team_size = sum(l["used_seats"] for l in licenses) / len(licenses) if licenses else 0

    # MRR from courses
    mrr = 0
    for license in licenses:
        tier_info = CONTRACTOR_TIERS.get(license["tier"], {})
        price = tier_info.get("price", 0)
        if price:
            mrr += price

    # Leads in pipeline
    leads_aware = await db.contractor_leads.count_documents({"stage": "aware"})
    leads_interested = await db.contractor_leads.count_documents({"stage": "interested"})
    leads_demo = await db.contractor_leads.count_documents({"stage": "demo"})
    leads_trial = await db.contractor_leads.count_documents({"stage": "trial"})

    return {
        "status": "success",
        "market": {
            "total_contractors": total_contractors,
            "avg_team_size": round(avg_team_size, 1),
            "mrr": round(mrr, 2),
            "estimated_annual": round(mrr * 12, 2),
        },
        "by_tier": {item["_id"]: item["count"] for item in tier_dist},
        "pipeline": {
            "aware": leads_aware,
            "interested": leads_interested,
            "demo": leads_demo,
            "trial": leads_trial,
            "total": leads_aware + leads_interested + leads_demo + leads_trial,
        },
    }
