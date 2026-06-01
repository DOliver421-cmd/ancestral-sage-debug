"""
Course Licensing & Electrical Contractor Market Revenue Stream
Handles training packages, team licenses, and contractor certifications.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class ContractorTier(str, Enum):
    """Course access tiers for contractors"""
    SOLO = "solo"           # Single contractor ($29/mo)
    TEAM_5 = "team_5"       # Up to 5 team members ($99/mo)
    TEAM_20 = "team_20"     # Up to 20 team members ($249/mo)
    ENTERPRISE = "enterprise"  # Custom licensing


CONTRACTOR_TIERS = {
    "solo": {
        "name": "Solo Contractor",
        "price": 29.00,
        "seats": 1,
        "description": "One contractor. Unlimited course access.",
        "features": [
            "Access to all 9 training labs",
            "Lifetime lab completion certificates",
            "Voltage drop & conduit calculators",
            "NFPA 70E compliance guides",
        ],
    },
    "team_5": {
        "name": "Small Crew (up to 5)",
        "price": 99.00,
        "seats": 5,
        "description": "Perfect for small shops and startups.",
        "features": [
            "All Solo features",
            "5 team member seats",
            "Shared completion dashboard",
            "Admin can manage team",
            "Bulk cert export",
        ],
    },
    "team_20": {
        "name": "Growing Crew (up to 20)",
        "price": 249.00,
        "seats": 20,
        "description": "For growing electrical shops.",
        "features": [
            "All Team features",
            "20 team member seats",
            "Advanced analytics & reporting",
            "Custom team branding",
            "Priority support",
            "Quarterly webinars",
        ],
    },
    "enterprise": {
        "name": "Enterprise License",
        "price": None,  # Custom
        "seats": None,  # Custom
        "description": "White-label, multi-office, custom needs.",
        "features": [
            "All Team features",
            "Unlimited seats",
            "Custom licensing terms",
            "API access",
            "Dedicated account manager",
        ],
    },
}


class CourseLicense(BaseModel):
    """A contractor's course access license"""
    contractor_id: str
    business_name: str
    tier: ContractorTier
    stripe_subscription_id: Optional[str] = None
    max_seats: int
    used_seats: int = 0
    language: str = "en"  # Default language (en, es, pt, fr)
    team_members: list = []  # [{"name": "...", "email": "...", "language": "es", "labs_completed": [...]}, ...]
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    auto_renew: bool = True


class CourseCompletion(BaseModel):
    """Record when a team member completes a lab"""
    contractor_id: str
    team_member_id: str
    lab_slug: str
    completed_at: datetime
    score: Optional[float] = None
    time_minutes: int
    certificate_issued: bool = False


class MarketingLead(BaseModel):
    """Electrical contractor lead in CRM"""
    company_name: str
    industry: str = "electrical_contracting"
    crew_size: int  # 1-500
    specialization: str  # "residential", "commercial", "industrial", "solar", "mixed"
    contact_email: str
    phone: Optional[str] = None
    source: str  # "web_search", "directory", "referral", "cold_outreach"
    stage: str  # "aware", "interested", "demo", "trial", "customer"
    estimated_value: float  # (crew_size / 5) * tier price * 12
    created_at: datetime = None


async def init_course_licensing(db: AsyncIOMotorDatabase) -> dict:
    """Initialize course licensing collections"""
    try:
        # Contractor licenses
        await db.course_licenses.create_index("contractor_id", unique=True)
        await db.course_licenses.create_index([("tier", 1), ("created_at", -1)])
        await db.course_licenses.create_index([("expires_at", 1)])

        # Course completions
        await db.course_completions.create_index([("contractor_id", 1), ("lab_slug", 1)])
        await db.course_completions.create_index([("completed_at", -1)])
        await db.course_completions.create_index([("contractor_id", 1), ("completed_at", -1)])

        # Contractor leads (for outreach)
        await db.contractor_leads.create_index([("source", 1), ("stage", 1)])
        await db.contractor_leads.create_index("company_name")
        await db.contractor_leads.create_index([("crew_size", 1)])
        await db.contractor_leads.create_index([("created_at", -1)])
        await db.contractor_leads.create_index("contact_email", unique=True, sparse=True)

        logger.info("✅ Course licensing collections initialized")
        return {"status": "success"}
    except Exception as e:
        logger.warning(f"Course licensing init (non-fatal): {e}")
        return {"status": "partial", "error": str(e)}


async def create_contractor_license(
    db: AsyncIOMotorDatabase,
    contractor_id: str,
    business_name: str,
    tier: str,
    language: str = "en",
) -> dict:
    """Create a new contractor license"""
    tier_info = CONTRACTOR_TIERS.get(tier)
    if not tier_info:
        return {"status": "error", "message": f"Invalid tier: {tier}"}

    # Validate language
    from .course_multilingual import COURSE_LANGUAGES
    if language not in COURSE_LANGUAGES:
        language = "en"

    license_doc = {
        "contractor_id": contractor_id,
        "business_name": business_name,
        "tier": tier,
        "language": language,
        "max_seats": tier_info["seats"] or 999,
        "used_seats": 1,
        "team_members": [{"name": business_name, "email": None, "language": language}],
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=365),
        "auto_renew": True,
    }

    result = await db.course_licenses.insert_one(license_doc)
    logger.info(f"Created course license for {business_name} ({tier}) in {language}")
    return {"status": "success", "license_id": str(result.inserted_id)}


async def add_team_member(
    db: AsyncIOMotorDatabase,
    contractor_id: str,
    name: str,
    email: str,
    language: str = None,
) -> dict:
    """Add a team member to contractor's license"""
    license = await db.course_licenses.find_one({"contractor_id": contractor_id})
    if not license:
        return {"status": "error", "message": "License not found"}

    if license["used_seats"] >= license["max_seats"]:
        return {"status": "error", "message": "License capacity reached"}

    # Use team member's language preference or license default
    if language is None:
        language = license.get("language", "en")

    new_member = {
        "id": f"{contractor_id}_{len(license['team_members'])}",
        "name": name,
        "email": email,
        "language": language,
        "labs_completed": [],
        "added_at": datetime.utcnow(),
    }

    await db.course_licenses.update_one(
        {"contractor_id": contractor_id},
        {
            "$push": {"team_members": new_member},
            "$inc": {"used_seats": 1},
        },
    )
    logger.info(f"Added {name} to {contractor_id}'s license (language: {language})")
    return {"status": "success", "member_id": new_member["id"]}


async def record_lab_completion(
    db: AsyncIOMotorDatabase,
    contractor_id: str,
    team_member_id: str,
    lab_slug: str,
    time_minutes: int,
    score: Optional[float] = None,
) -> dict:
    """Record when a team member completes a lab"""
    completion = {
        "contractor_id": contractor_id,
        "team_member_id": team_member_id,
        "lab_slug": lab_slug,
        "completed_at": datetime.utcnow(),
        "score": score,
        "time_minutes": time_minutes,
        "certificate_issued": False,
    }

    await db.course_completions.insert_one(completion)

    # Update team member's completion list
    await db.course_licenses.update_one(
        {"contractor_id": contractor_id, "team_members.id": team_member_id},
        {"$push": {"team_members.$.labs_completed": lab_slug}},
    )

    logger.info(f"{team_member_id} completed {lab_slug}")
    return {"status": "success"}


async def get_contractor_dashboard(
    db: AsyncIOMotorDatabase,
    contractor_id: str,
) -> dict:
    """Get dashboard showing license, team, and completion stats"""
    license = await db.course_licenses.find_one({"contractor_id": contractor_id})
    if not license:
        return {"status": "error", "message": "License not found"}

    # Aggregate stats
    completions = list(
        await db.course_completions.find(
            {"contractor_id": contractor_id}
        ).to_list(None)
    )

    labs_by_member = {}
    for m in license["team_members"]:
        labs_by_member[m["id"]] = len(m.get("labs_completed", []))

    return {
        "status": "success",
        "license": {
            "tier": license["tier"],
            "business_name": license["business_name"],
            "seats_used": license["used_seats"],
            "seats_max": license["max_seats"],
        },
        "team": license["team_members"],
        "stats": {
            "total_completions": len(completions),
            "avg_time_minutes": sum(c["time_minutes"] for c in completions) / len(completions) if completions else 0,
            "labs_by_member": labs_by_member,
        },
    }


def estimate_contractor_arv(crew_size: int, specialization: str) -> float:
    """
    Estimate Annual Recurring Value (ARV) for a contractor based on crew size.
    Used for sales pipeline forecasting.
    """
    # Base tiers
    if crew_size == 1:
        base = 29.00
    elif crew_size <= 5:
        base = 99.00
    elif crew_size <= 20:
        base = 249.00
    else:
        base = 249.00 + (crew_size - 20) * 10  # $10 per additional seat

    # Specialization uplift (contractors with certifications spend more)
    uplift = 1.0
    if specialization == "commercial":
        uplift = 1.3
    elif specialization == "industrial":
        uplift = 1.5
    elif specialization == "solar":
        uplift = 1.2

    return base * 12 * uplift
