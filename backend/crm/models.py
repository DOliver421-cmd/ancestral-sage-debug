"""
WAI Institute CRM Models
Sales pipeline tracking for enterprise deals
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class LeadSource(str, Enum):
    """Where the lead came from"""
    INBOUND = "inbound"  # Website, demo request
    REFERRAL = "referral"  # Existing customer or partner
    EVENT = "event"  # Conference, webinar
    COLD_OUTREACH = "cold_outreach"  # Sales team outreach
    PARTNER = "partner"  # Partner channel
    COMPETITOR_SWITCH = "competitor_switch"  # Switching from competitor


class LeadStatus(str, Enum):
    """Lead lifecycle"""
    LEAD = "lead"
    PROSPECT = "prospect"
    OPPORTUNITY = "opportunity"
    PROPOSAL = "proposal"
    CONTRACT = "contract"
    CUSTOMER = "customer"
    LOST = "lost"


class OpportunityStage(str, Enum):
    """Sales pipeline stage"""
    DISCOVERY = "discovery"
    DEMO = "demo"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSE = "close"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class BudgetRange(str, Enum):
    """Estimated customer budget"""
    UNDER_50K = "<50K"
    FIFTY_TO_100K = "50-100K"
    HUNDRED_TO_500K = "100-500K"
    FIVE_HUNDRED_K_TO_1M = "500K-1M"
    OVER_1M = ">1M"


# ============================================================================
# PYDANTIC MODELS (API contracts)
# ============================================================================

class DecisionMaker(BaseModel):
    """Key person at customer organization"""
    name: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=5, max_length=255)  # Basic email validation
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    verified: bool = False


class LeadBase(BaseModel):
    """Core lead information"""
    company_name: str = Field(..., min_length=1, max_length=500)
    company_size: Optional[int] = Field(None, ge=1, le=1000000)  # Number of employees (1 to 1M)
    industry: Optional[str] = Field(None, min_length=1, max_length=100)
    budget_range: Optional[BudgetRange] = None
    decision_maker: DecisionMaker
    source: LeadSource
    status: LeadStatus = LeadStatus.LEAD


class LeadCreate(LeadBase):
    """Create new lead"""
    notes: Optional[str] = Field(None, max_length=5000)


class Lead(LeadBase):
    """Lead with full details"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    score: int = 0  # 0-100 (how hot is this lead?)
    owner_id: Optional[str] = None  # Sales rep assigned
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_contact: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class OpportunityBase(BaseModel):
    """Core opportunity data"""
    lead_id: str
    deal_name: str
    deal_value: float  # Expected annual contract value (ACV)
    stage: OpportunityStage = OpportunityStage.DISCOVERY
    probability: int = 25  # 0-100, for pipeline forecasting


class OpportunityCreate(OpportunityBase):
    """Create new opportunity"""
    expected_close_date: datetime
    notes: Optional[str] = None


class OpportunityUpdate(BaseModel):
    """Update opportunity"""
    stage: Optional[OpportunityStage] = None
    probability: Optional[int] = None
    deal_value: Optional[float] = None
    expected_close_date: Optional[datetime] = None
    notes: Optional[str] = None


class Opportunity(OpportunityBase):
    """Opportunity with full details"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    owner_id: Optional[str] = None  # Sales rep
    expected_close_date: datetime
    actual_close_date: Optional[datetime] = None
    contract_id: Optional[str] = None  # Links to signed contract
    notes: Optional[str] = None
    interactions: List[str] = []  # Activity log: calls, emails, meetings
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ActivityLogEntry(BaseModel):
    """Record of interaction with lead/customer"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    opportunity_id: str
    activity_type: str  # 'call', 'email', 'meeting', 'proposal', 'demo'
    activity_date: datetime
    duration_minutes: Optional[int] = None
    notes: str
    created_by: str  # Sales rep who logged activity
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SalesMetrics(BaseModel):
    """Sales team performance metrics"""
    period: str  # "2026-Q2", "2026-05"
    total_pipeline_value: float
    stage_breakdown: dict  # {stage: value}
    conversion_rate: float  # %
    average_sales_cycle: int  # days
    deals_closed: int
    revenue_closed: float
    forecast_accuracy: float  # %
    win_rate: float  # % of proposals that close


# ============================================================================
# DATABASE MODELS
# ============================================================================

class CRMDatabase:
    """CRM database collections"""

    def __init__(self, db):
        self.db = db
        self.leads = db.leads
        self.opportunities = db.opportunities
        self.activity_log = db.activity_log
        self.contracts = db.contracts

    async def initialize(self):
        """Create indexes"""
        # Leads: Fast lookup by company, status
        await self.leads.create_index("company_name")
        await self.leads.create_index([("status", 1), ("score", -1)])
        await self.leads.create_index("source")

        # Opportunities: Fast lookup by stage, expected close
        await self.opportunities.create_index("lead_id")
        await self.opportunities.create_index([("stage", 1), ("expected_close_date", 1)])
        await self.opportunities.create_index([("probability", -1)])

        # Activity: Fast lookup by opportunity
        await self.activity_log.create_index("opportunity_id")
        await self.activity_log.create_index([("activity_date", -1)])

        # Contracts: Fast lookup by opportunity
        await self.contracts.create_index("opportunity_id", unique=True, sparse=True)
