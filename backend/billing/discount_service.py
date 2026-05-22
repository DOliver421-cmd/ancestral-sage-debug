"""
Discount Management Service

Handles creation, retrieval, and application of subscription discounts.
Supports percentage-based discounts with automatic expiration after 90 days.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import uuid
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class DiscountBase(BaseModel):
    """Base discount data"""
    percentage: int = Field(..., ge=0, le=100)
    active: bool = True
    notes: Optional[str] = None


class DiscountCreate(DiscountBase):
    """Create new discount"""
    pass


class Discount(DiscountBase):
    """Complete discount response"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime
    expires_at: datetime
    created_by: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DiscountResponse(Discount):
    """Discount response with computed fields"""
    days_remaining: int = Field(default=0)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ============================================================================
# DISCOUNT MANAGER
# ============================================================================

class DiscountManager:
    """Business logic for discount management"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.discounts

    async def ensure_indexes(self):
        """Create indexes for efficient queries"""
        await self.collection.create_index("created_at")
        await self.collection.create_index("expires_at")
        await self.collection.create_index("active")
        logger.info("Discount collection indexes ensured")

    async def create_discount(
        self,
        percentage: int,
        created_by: str,
        notes: Optional[str] = None,
    ) -> DiscountResponse:
        """
        Create a new discount.
        Only one discount can be active at a time.

        Args:
            percentage: Discount percentage (0-100)
            created_by: User ID of director creating the discount
            notes: Optional reason or campaign name

        Returns:
            Created Discount with response fields

        Raises:
            ValueError: If percentage is invalid
        """
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")

        # Deactivate any existing active discount
        await self.collection.update_many(
            {"active": True},
            {"$set": {"active": False}}
        )

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=90)

        discount_doc = {
            "id": str(uuid.uuid4()),
            "percentage": percentage,
            "active": True,
            "created_at": now,
            "expires_at": expires_at,
            "created_by": created_by,
            "notes": notes or "",
        }

        result = await self.collection.insert_one(discount_doc)
        discount_doc["_id"] = result.inserted_id

        logger.info(f"Created discount: {percentage}% by {created_by}")
        return self._build_response(discount_doc)

    async def get_active_discount(self) -> Optional[DiscountResponse]:
        """
        Get the currently active discount.

        Returns:
            Active discount or None
        """
        now = datetime.now(timezone.utc)

        # Find active discount that hasn't expired
        discount_doc = await self.collection.find_one({
            "active": True,
            "expires_at": {"$gt": now}
        })

        if discount_doc:
            return self._build_response(discount_doc)

        return None

    async def update_discount_percentage(
        self,
        percentage: int,
        notes: Optional[str] = None,
    ) -> Optional[DiscountResponse]:
        """
        Update the percentage of the active discount.
        Keeps the original 90-day expiration window.

        Args:
            percentage: New percentage (0-100)
            notes: Optional reason for change

        Returns:
            Updated discount or None if no active discount
        """
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")

        now = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {
                "active": True,
                "expires_at": {"$gt": now}
            },
            {
                "$set": {
                    "percentage": percentage,
                    "notes": notes or "",
                }
            },
            return_document=True
        )

        if result:
            logger.info(f"Updated discount to {percentage}%")
            return self._build_response(result)

        return None

    async def deactivate_discount(self) -> Optional[DiscountResponse]:
        """
        Deactivate the active discount.

        Returns:
            Deactivated discount or None
        """
        result = await self.collection.find_one_and_update(
            {"active": True},
            {"$set": {"active": False}},
            return_document=True
        )

        if result:
            logger.info("Deactivated discount")
            return self._build_response(result)

        return None

    def is_discount_expired(self, expires_at: datetime) -> bool:
        """
        Check if discount has expired.

        Args:
            expires_at: Expiration datetime

        Returns:
            True if expired, False otherwise
        """
        now = datetime.now(timezone.utc)
        return expires_at <= now

    def apply_discount_to_price(self, price: float, percentage: int) -> float:
        """
        Apply discount percentage to a price.

        Args:
            price: Original price
            percentage: Discount percentage (0-100)

        Returns:
            Discounted price rounded to 2 decimals
        """
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")

        if percentage == 0:
            return round(price, 2)

        discounted = price * (1 - percentage / 100)
        return round(discounted, 2)

    def get_pricing_with_discount(
        self,
        base_pricing: Dict[str, Dict[str, float]],
        discount: Optional[DiscountResponse],
    ) -> Dict[str, Any]:
        """
        Calculate pricing with discount applied.

        Args:
            base_pricing: Original tier pricing dict
            discount: Active discount or None

        Returns:
            Pricing dict with discounted prices
        """
        if not discount or not discount.active:
            return {"tiers": base_pricing, "active_discount": None}

        # Check expiration
        if self.is_discount_expired(discount.expires_at):
            return {"tiers": base_pricing, "active_discount": None}

        # Apply discount to all tiers
        discounted_pricing = {}
        for tier, cycles in base_pricing.items():
            discounted_pricing[tier] = {}
            for cycle, price in cycles.items():
                discounted_pricing[tier][cycle] = price  # Keep original
                discounted_pricing[tier][f"{cycle}_discounted"] = self.apply_discount_to_price(
                    price, discount.percentage
                )

        return {
            "tiers": discounted_pricing,
            "active_discount": {
                "percentage": discount.percentage,
                "expires_at": discount.expires_at.isoformat(),
                "message": f"Save {discount.percentage}% for the first 90 days!",
            }
        }

    def _build_response(self, doc: Dict[str, Any]) -> DiscountResponse:
        """Build DiscountResponse from database document"""
        doc.pop("_id", None)

        # Calculate days remaining
        now = datetime.now(timezone.utc)
        expires_at = doc["expires_at"]

        # Ensure timezone-aware comparison
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        days_remaining = (expires_at - now).days
        if days_remaining < 0:
            days_remaining = 0

        return DiscountResponse(
            **doc,
            days_remaining=days_remaining,
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def init_discount_service(db: AsyncIOMotorDatabase) -> DiscountManager:
    """Initialize discount service and ensure indexes"""
    manager = DiscountManager(db)
    await manager.ensure_indexes()
    return manager
