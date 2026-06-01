"""
WAI Institute Billing Models
Real subscription, invoice, and payment tracking
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import uuid


class SubscriptionTier(str, Enum):
    """Available subscription tiers"""
    BASIC = "basic"
    ADVANCED = "advanced"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription lifecycle states"""
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    EXPIRED = "expired"


class BillingCycle(str, Enum):
    """Billing frequency"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class InvoiceStatus(str, Enum):
    """Invoice states"""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


# ============================================================================
# PYDANTIC MODELS (API contracts)
# ============================================================================

class PaymentMethodBase(BaseModel):
    """Payment method data model"""
    type: str  # 'card' or 'bank_account'
    last_4: str
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    is_default: bool = False


class PaymentMethodCreate(PaymentMethodBase):
    """Create payment method (with token from Stripe)"""
    stripe_payment_method_id: str


class PaymentMethod(PaymentMethodBase):
    """Payment method response"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    stripe_payment_method_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SubscriptionBase(BaseModel):
    """Core subscription data"""
    tier: SubscriptionTier
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE


class SubscriptionCreate(SubscriptionBase):
    """Create new subscription"""
    user_id: str
    payment_method_id: str  # User's payment method ID


class SubscriptionUpdate(BaseModel):
    """Update subscription (tier, cycle, etc.)"""
    tier: Optional[SubscriptionTier] = None
    billing_cycle: Optional[BillingCycle] = None
    status: Optional[SubscriptionStatus] = None


class Subscription(SubscriptionBase):
    """Subscription with full details"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    stripe_subscription_id: Optional[str] = None
    billing_period_start: datetime
    billing_period_end: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class InvoiceLineItem(BaseModel):
    """Line item on an invoice"""
    description: str
    quantity: float
    unit_price: float
    amount: float


class InvoiceBase(BaseModel):
    """Core invoice data"""
    subscription_id: str
    amount_due: float
    status: InvoiceStatus = InvoiceStatus.DRAFT


class InvoiceCreate(InvoiceBase):
    """Create invoice"""
    line_items: list[InvoiceLineItem]


class Invoice(InvoiceBase):
    """Invoice with full details"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    stripe_invoice_id: Optional[str] = None
    amount_paid: float = 0.0
    issued_date: datetime
    due_date: datetime
    paid_date: Optional[datetime] = None
    line_items: list[InvoiceLineItem]
    pdf_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UsageEvent(BaseModel):
    """Usage-based billing event (for Research API, etc.)"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    billing_period_id: str  # References invoice period
    metric_name: str  # 'api_calls', 'data_queries', etc.
    quantity: float
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


class CreatorBalance(BaseModel):
    """Creator's payment balance (accrued earnings)"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    creator_id: str
    amount_available: float = 0.0  # Ready to withdraw
    amount_held_chargebacks: float = 0.0  # Held due to chargeback risk
    amount_pending: float = 0.0  # From this month's sales (not yet paid)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreatorPayout(BaseModel):
    """Record of payment sent to creator"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    creator_id: str
    stripe_payout_id: str
    amount_requested: float
    amount_paid: float
    status: str  # 'pending', 'paid', 'failed'
    requested_date: datetime = Field(default_factory=datetime.utcnow)
    paid_date: Optional[datetime] = None
    failure_reason: Optional[str] = None


class RevenueEvent(BaseModel):
    """For accounting: tracks revenue recognition per ASC 606"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    contract_id: str  # Links to subscription or one-time purchase
    revenue_type: str  # 'subscription', 'one-time', 'license', 'pass-through'
    amount: float
    recognition_start_date: datetime
    recognition_end_date: datetime
    monthly_amount: float  # For subscriptions, monthly recognition
    actual_amount_collected: float
    status: str  # 'pending', 'recognized', 'adjusted'
    journal_entry_id: Optional[str] = None  # Links to accounting entry
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# DATABASE INITIALIZATION & SCHEMA
# ============================================================================

class BillingDatabase:
    """Initialize billing database collections and indexes"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.subscriptions = db.subscriptions
        self.invoices = db.invoices
        self.payment_methods = db.payment_methods
        self.usage_events = db.usage_events
        self.creator_balances = db.creator_balances
        self.creator_payouts = db.creator_payouts
        self.revenue_events = db.revenue_events

    async def initialize(self):
        """Create indexes for performance"""

        # Subscriptions: Fast lookup by user_id, stripe_subscription_id
        await self.subscriptions.create_index("user_id")
        await self.subscriptions.create_index("stripe_subscription_id", unique=True, sparse=True)
        await self.subscriptions.create_index([("status", 1), ("billing_period_end", 1)])

        # Invoices: Fast lookup by subscription, status
        await self.invoices.create_index("subscription_id")
        await self.invoices.create_index("stripe_invoice_id", unique=True, sparse=True)
        await self.invoices.create_index([("status", 1), ("due_date", 1)])

        # Payment methods: Fast lookup by user_id
        await self.payment_methods.create_index("user_id")
        await self.payment_methods.create_index("stripe_payment_method_id", unique=True)

        # Usage events: Fast time-based lookup for billing period
        await self.usage_events.create_index([("user_id", 1), ("billing_period_id", 1)])
        await self.usage_events.create_index([("recorded_at", -1)])

        # Creator tracking: Fast lookup by creator
        await self.creator_balances.create_index("creator_id", unique=True)
        await self.creator_payouts.create_index("creator_id")
        await self.creator_payouts.create_index("status")

        # Revenue: Fast lookup for accounting
        await self.revenue_events.create_index("contract_id")
        await self.revenue_events.create_index([("recognition_end_date", 1), ("status", 1)])


# ============================================================================
# PRICING CONFIGURATION
# ============================================================================

TIER_PRICING = {
    SubscriptionTier.BASIC: {
        "monthly": 9.99,
        "annual": 99.99,
    },
    SubscriptionTier.ADVANCED: {
        "monthly": 29.99,
        "annual": 299.99,
    },
    SubscriptionTier.PREMIUM: {
        "monthly": 99.99,
        "annual": 999.99,
    },
    # ENTERPRISE: Custom pricing, negotiated per customer
}


def get_tier_price(tier: SubscriptionTier, cycle: BillingCycle) -> float:
    """Get price for tier and billing cycle"""
    if tier == SubscriptionTier.ENTERPRISE:
        raise ValueError("Enterprise pricing must be negotiated")

    cycle_key = "annual" if cycle == BillingCycle.ANNUAL else "monthly"
    return TIER_PRICING[tier][cycle_key]


def calculate_proration(
    current_cycle_start: datetime,
    current_cycle_end: datetime,
    days_used: int,
    full_cycle_price: float,
) -> float:
    """Calculate prorated refund for early cancellation"""
    total_days = (current_cycle_end - current_cycle_start).days
    daily_rate = full_cycle_price / total_days
    days_remaining = total_days - days_used
    return days_remaining * daily_rate
