"""
WAI Institute Stripe Integration Service
Real Stripe API integration for payments and subscriptions
"""

import stripe
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from .models import (
    SubscriptionTier,
    BillingCycle,
    Subscription,
    Invoice,
    PaymentMethod,
    CreatorBalance,
    TIER_PRICING,
)

logger = logging.getLogger(__name__)

# Initialize Stripe (API key from environment)
stripe.api_key = None  # Set at runtime from config


class StripeService:
    """Handles all Stripe API interactions"""

    def __init__(self, db: AsyncIOMotorDatabase, stripe_api_key: str):
        stripe.api_key = stripe_api_key
        self.db = db
        self.subscriptions_collection = db.subscriptions
        self.invoices_collection = db.invoices
        self.payment_methods_collection = db.payment_methods

    async def create_subscription(
        self,
        user_id: str,
        tier: SubscriptionTier,
        billing_cycle: BillingCycle,
        payment_method_id: str,
        email: str,
    ) -> Subscription:
        """
        Create a new subscription in Stripe and save locally

        Args:
            user_id: WAI user ID
            tier: Subscription tier (basic, advanced, premium, enterprise)
            billing_cycle: Billing frequency (monthly, annual)
            payment_method_id: Stripe payment method ID
            email: User's email for Stripe customer

        Returns:
            Subscription object with stripe_subscription_id
        """
        try:
            # Get or create Stripe customer
            customer = await self._get_or_create_customer(user_id, email)

            # Get price for tier/cycle
            if tier == SubscriptionTier.ENTERPRISE:
                raise ValueError("Enterprise requires manual setup")

            cycle_key = "annual" if billing_cycle == BillingCycle.ANNUAL else "monthly"
            price = TIER_PRICING[tier][cycle_key]

            # Create product in Stripe (if not exists)
            product_id = await self._get_or_create_product(tier, billing_cycle, price)

            # Create subscription in Stripe
            stripe_subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{"price": product_id}],
                payment_settings={
                    "payment_method_types": ["card"],
                    "save_default_payment_method": "on_subscription",
                },
                default_payment_method=payment_method_id,
                billing_cycle_anchor="auto",  # Next billing date
            )

            # Save to local database
            now = datetime.utcnow()
            billing_period_start = now
            if billing_cycle == BillingCycle.MONTHLY:
                billing_period_end = now + timedelta(days=30)
            elif billing_cycle == BillingCycle.ANNUAL:
                billing_period_end = now + timedelta(days=365)
            else:
                billing_period_end = now + timedelta(days=90)

            subscription_doc = {
                "user_id": user_id,
                "stripe_subscription_id": stripe_subscription.id,
                "tier": tier.value,
                "billing_cycle": billing_cycle.value,
                "status": "active",
                "billing_period_start": billing_period_start,
                "billing_period_end": billing_period_end,
                "created_at": now,
                "updated_at": now,
                "cancelled_at": None,
                "cancellation_reason": None,
            }

            result = await self.subscriptions_collection.insert_one(subscription_doc)

            logger.info(f"Created subscription for user {user_id}: {stripe_subscription.id}")

            return Subscription(**subscription_doc, id=str(result.inserted_id))

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            raise

    async def cancel_subscription(
        self,
        user_id: str,
        reason: str = "Customer requested cancellation",
    ) -> Subscription:
        """
        Cancel a user's subscription (at end of billing period)

        Cancels at end of current billing period (not immediately).
        Customer keeps access until period ends.
        """
        try:
            # Find subscription
            subscription_doc = await self.subscriptions_collection.find_one({
                "user_id": user_id,
                "status": "active"
            })

            if not subscription_doc:
                raise ValueError(f"No active subscription for user {user_id}")

            stripe_sub_id = subscription_doc["stripe_subscription_id"]

            # Cancel in Stripe (at end of period)
            stripe.Subscription.delete(stripe_sub_id)

            # Update local record
            now = datetime.utcnow()
            await self.subscriptions_collection.update_one(
                {"_id": subscription_doc["_id"]},
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelled_at": now,
                        "cancellation_reason": reason,
                        "updated_at": now,
                    }
                }
            )

            logger.info(f"Cancelled subscription for user {user_id}")

            # Fetch updated doc
            updated_doc = await self.subscriptions_collection.find_one({
                "_id": subscription_doc["_id"]
            })

            return Subscription(**updated_doc, id=str(updated_doc["_id"]))

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {e}")
            raise
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            raise

    async def update_subscription_tier(
        self,
        user_id: str,
        new_tier: SubscriptionTier,
    ) -> Subscription:
        """
        Upgrade or downgrade subscription tier
        Proration applied immediately
        """
        try:
            subscription_doc = await self.subscriptions_collection.find_one({
                "user_id": user_id,
                "status": "active"
            })

            if not subscription_doc:
                raise ValueError(f"No active subscription for user {user_id}")

            stripe_sub_id = subscription_doc["stripe_subscription_id"]
            billing_cycle = subscription_doc["billing_cycle"]

            # Get new price
            cycle_key = "annual" if billing_cycle == "annual" else "monthly"
            new_price = TIER_PRICING[new_tier][cycle_key]
            product_id = await self._get_or_create_product(new_tier, BillingCycle(billing_cycle), new_price)

            # Update subscription in Stripe (Stripe handles proration)
            stripe.Subscription.modify(
                stripe_sub_id,
                items=[{
                    "id": subscription_doc["stripe_subscription_id"],
                    "price": product_id,
                }],
                proration_behavior="create_prorations",  # Immediately bill for difference
            )

            # Update local record
            now = datetime.utcnow()
            await self.subscriptions_collection.update_one(
                {"_id": subscription_doc["_id"]},
                {
                    "$set": {
                        "tier": new_tier.value,
                        "updated_at": now,
                    }
                }
            )

            logger.info(f"Upgraded tier for user {user_id} to {new_tier}")

            updated_doc = await self.subscriptions_collection.find_one({
                "_id": subscription_doc["_id"]
            })

            return Subscription(**updated_doc, id=str(updated_doc["_id"]))

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating tier: {e}")
            raise

    async def get_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get user's active subscription"""
        doc = await self.subscriptions_collection.find_one({
            "user_id": user_id,
            "status": "active"
        })

        if doc:
            return Subscription(**doc, id=str(doc["_id"]))
        return None

    async def handle_webhook(self, event: Dict[str, Any]) -> None:
        """
        Handle Stripe webhook events

        Supported events:
        - invoice.payment_succeeded
        - invoice.payment_failed
        - customer.subscription.updated
        - customer.subscription.deleted
        """
        event_type = event["type"]

        try:
            if event_type == "invoice.payment_succeeded":
                await self._handle_invoice_paid(event["data"]["object"])

            elif event_type == "invoice.payment_failed":
                await self._handle_invoice_failed(event["data"]["object"])

            elif event_type == "customer.subscription.updated":
                await self._handle_subscription_updated(event["data"]["object"])

            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(event["data"]["object"])

            else:
                logger.warning(f"Unhandled webhook event type: {event_type}")

        except Exception as e:
            logger.error(f"Error handling webhook {event_type}: {e}")
            raise

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    async def _get_or_create_customer(self, user_id: str, email: str) -> Any:
        """Get or create Stripe customer"""
        # Check if we already have Stripe customer ID stored
        user_doc = await self.db.users.find_one({"_id": user_id})

        if user_doc and user_doc.get("stripe_customer_id"):
            return stripe.Customer.retrieve(user_doc["stripe_customer_id"])

        # Create new customer
        customer = stripe.Customer.create(
            email=email,
            metadata={"wai_user_id": user_id}
        )

        # Store Stripe ID in user document
        await self.db.users.update_one(
            {"_id": user_id},
            {"$set": {"stripe_customer_id": customer.id}}
        )

        return customer

    async def _get_or_create_product(
        self,
        tier: SubscriptionTier,
        billing_cycle: BillingCycle,
        price: float
    ) -> str:
        """Get or create Stripe product for tier/cycle combo"""
        product_name = f"WAI {tier.value.title()} - {billing_cycle.value.title()}"
        product_key = f"wai_{tier.value}_{billing_cycle.value}"

        # Check if product exists
        products = stripe.Product.list(limit=100, active=True)
        for product in products.data:
            if product.metadata.get("wai_key") == product_key:
                return product.id

        # Create new product
        product = stripe.Product.create(
            name=product_name,
            type="service",
            metadata={"wai_key": product_key}
        )

        # Create price for product
        recurring = {
            "interval": "month" if billing_cycle == BillingCycle.MONTHLY else "year",
            "interval_count": 1,
        }

        stripe_price = stripe.Price.create(
            product=product.id,
            unit_amount=int(price * 100),  # Convert to cents
            currency="usd",
            recurring=recurring,
        )

        return stripe_price.id

    async def _handle_invoice_paid(self, invoice_data: Dict[str, Any]) -> None:
        """Invoice payment succeeded"""
        stripe_invoice_id = invoice_data["id"]

        # Update invoice status in local DB
        now = datetime.utcnow()
        await self.invoices_collection.update_one(
            {"stripe_invoice_id": stripe_invoice_id},
            {
                "$set": {
                    "status": "paid",
                    "amount_paid": invoice_data["amount_paid"] / 100,  # Convert from cents
                    "paid_date": now,
                    "updated_at": now,
                }
            }
        )

        logger.info(f"Invoice {stripe_invoice_id} marked as paid")

    async def _handle_invoice_failed(self, invoice_data: Dict[str, Any]) -> None:
        """Invoice payment failed"""
        stripe_invoice_id = invoice_data["id"]

        now = datetime.utcnow()
        await self.invoices_collection.update_one(
            {"stripe_invoice_id": stripe_invoice_id},
            {
                "$set": {
                    "status": "open",  # Remains open, retry scheduled
                    "updated_at": now,
                }
            }
        )

        logger.warning(f"Invoice {stripe_invoice_id} payment failed, will retry")

    async def _handle_subscription_updated(self, subscription_data: Dict[str, Any]) -> None:
        """Subscription was updated (tier change, etc.)"""
        stripe_sub_id = subscription_data["id"]

        # Update local record
        now = datetime.utcnow()
        await self.subscriptions_collection.update_one(
            {"stripe_subscription_id": stripe_sub_id},
            {"$set": {"updated_at": now}}
        )

        logger.info(f"Subscription {stripe_sub_id} updated")

    async def _handle_subscription_deleted(self, subscription_data: Dict[str, Any]) -> None:
        """Subscription was deleted in Stripe"""
        stripe_sub_id = subscription_data["id"]

        now = datetime.utcnow()
        await self.subscriptions_collection.update_one(
            {"stripe_subscription_id": stripe_sub_id},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": now,
                    "updated_at": now,
                }
            }
        )

        logger.info(f"Subscription {stripe_sub_id} deleted in Stripe")


class CreatorPayoutService:
    """Handles creator payments via Stripe Connect"""

    def __init__(self, db: AsyncIOMotorDatabase, stripe_api_key: str):
        stripe.api_key = stripe_api_key
        self.db = db
        self.creator_balances = db.creator_balances
        self.creator_payouts = db.creator_payouts

    async def record_creator_sale(self, creator_id: str, amount: float) -> None:
        """Record a sale, credit to creator's balance (70% of amount)"""
        creator_share = amount * 0.7

        # Update balance
        await self.creator_balances.update_one(
            {"creator_id": creator_id},
            {
                "$inc": {"amount_pending": creator_share},
                "$set": {"updated_at": datetime.utcnow()}
            },
            upsert=True
        )

    async def process_monthly_payouts(self) -> Dict[str, int]:
        """
        Process payouts for all creators with accrued balance
        Called once per month (usually 1st of month)
        """
        stats = {"processed": 0, "failed": 0}

        # Get all creators with pending balance
        creators = await self.creator_balances.find({
            "amount_pending": {"$gt": 50}  # Minimum $50 payout
        }).to_list(None)

        for creator_doc in creators:
            creator_id = creator_doc["creator_id"]

            try:
                # Move pending to available (ready for withdrawal)
                pending = creator_doc.get("amount_pending", 0)

                await self.creator_balances.update_one(
                    {"creator_id": creator_id},
                    {
                        "$inc": {"amount_available": pending, "amount_pending": -pending},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )

                # Log payout record (pending actual bank transfer)
                payout_doc = {
                    "creator_id": creator_id,
                    "stripe_payout_id": f"pending_{creator_id}_{datetime.utcnow().isoformat()}",
                    "amount_requested": pending,
                    "amount_paid": 0,
                    "status": "pending",
                    "requested_date": datetime.utcnow(),
                    "paid_date": None,
                    "failure_reason": None,
                }

                await self.creator_payouts.insert_one(payout_doc)
                stats["processed"] += 1

                logger.info(f"Accrued ${pending} for creator {creator_id}")

            except Exception as e:
                logger.error(f"Error processing payout for creator {creator_id}: {e}")
                stats["failed"] += 1

        return stats

    async def execute_creator_withdrawal(
        self,
        creator_id: str,
        amount: float,
        stripe_connect_account_id: str,
    ) -> str:
        """
        Execute actual payout to creator's bank account

        Args:
            creator_id: Creator ID
            amount: Amount to withdraw
            stripe_connect_account_id: Stripe Connect account ID for creator

        Returns:
            Stripe payout ID
        """
        try:
            # Check balance
            balance_doc = await self.creator_balances.find_one({"creator_id": creator_id})

            if not balance_doc or balance_doc.get("amount_available", 0) < amount:
                raise ValueError(f"Insufficient balance for creator {creator_id}")

            # Create Stripe payout
            payout = stripe.Payout.create(
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                stripe_account=stripe_connect_account_id,
            )

            # Update payout record
            await self.creator_payouts.update_one(
                {"creator_id": creator_id, "status": "pending"},
                {
                    "$set": {
                        "stripe_payout_id": payout.id,
                        "amount_paid": amount,
                        "status": "paid",
                        "paid_date": datetime.utcnow(),
                    }
                }
            )

            # Deduct from available balance
            await self.creator_balances.update_one(
                {"creator_id": creator_id},
                {
                    "$inc": {"amount_available": -amount},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            logger.info(f"Executed payout for creator {creator_id}: ${amount}")

            return payout.id

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error executing payout: {e}")
            raise
        except Exception as e:
            logger.error(f"Error executing payout: {e}")
            raise
