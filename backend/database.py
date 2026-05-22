"""
WAI Institute Database Initialization & Connection
Real database setup that creates collections and indexes
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connection and initialization"""

    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db: AsyncIOMotorDatabase = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URI)
            self.db = self.client[settings.DATABASE_NAME]

            # Test connection
            await self.db.command("ping")
            logger.info(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")

            return self.db

        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("✅ Disconnected from MongoDB")

    async def initialize_collections(self):
        """Create all collections and indexes"""
        if not self.db:
            raise RuntimeError("Database not connected. Call connect() first.")

        logger.info("Initializing database collections...")

        # =====================================================================
        # BILLING COLLECTIONS
        # =====================================================================

        # Subscriptions
        await self._ensure_collection("subscriptions")
        await self.db.subscriptions.create_index("user_id")
        await self.db.subscriptions.create_index("stripe_subscription_id", unique=True, sparse=True)
        await self.db.subscriptions.create_index([("status", 1), ("billing_period_end", 1)])
        logger.info("✅ Subscriptions collection ready")

        # Invoices
        await self._ensure_collection("invoices")
        await self.db.invoices.create_index("subscription_id")
        await self.db.invoices.create_index("stripe_invoice_id", unique=True, sparse=True)
        await self.db.invoices.create_index([("status", 1), ("due_date", 1)])
        logger.info("✅ Invoices collection ready")

        # Payment Methods
        await self._ensure_collection("payment_methods")
        await self.db.payment_methods.create_index("user_id")
        await self.db.payment_methods.create_index("stripe_payment_method_id", unique=True)
        logger.info("✅ Payment methods collection ready")

        # Usage Events (for usage-based billing)
        await self._ensure_collection("usage_events")
        await self.db.usage_events.create_index([("user_id", 1), ("billing_period_id", 1)])
        await self.db.usage_events.create_index([("recorded_at", -1)])
        logger.info("✅ Usage events collection ready")

        # Creator Balances
        await self._ensure_collection("creator_balances")
        await self.db.creator_balances.create_index("creator_id", unique=True)
        logger.info("✅ Creator balances collection ready")

        # Creator Payouts
        await self._ensure_collection("creator_payouts")
        await self.db.creator_payouts.create_index("creator_id")
        await self.db.creator_payouts.create_index("status")
        logger.info("✅ Creator payouts collection ready")

        # Revenue Events (for accounting)
        await self._ensure_collection("revenue_events")
        await self.db.revenue_events.create_index("contract_id")
        await self.db.revenue_events.create_index([("recognition_end_date", 1), ("status", 1)])
        logger.info("✅ Revenue events collection ready")

        # =====================================================================
        # CRM COLLECTIONS
        # =====================================================================

        # Leads
        await self._ensure_collection("leads")
        await self.db.leads.create_index("company_name")
        await self.db.leads.create_index([("status", 1), ("score", -1)])
        await self.db.leads.create_index("source")
        logger.info("✅ Leads collection ready")

        # Opportunities
        await self._ensure_collection("opportunities")
        await self.db.opportunities.create_index("lead_id")
        await self.db.opportunities.create_index([("stage", 1), ("expected_close_date", 1)])
        await self.db.opportunities.create_index([("probability", -1)])
        logger.info("✅ Opportunities collection ready")

        # Activity Log
        await self._ensure_collection("activity_log")
        await self.db.activity_log.create_index("opportunity_id")
        await self.db.activity_log.create_index([("activity_date", -1)])
        logger.info("✅ Activity log collection ready")

        # Contracts
        await self._ensure_collection("contracts")
        await self.db.contracts.create_index("opportunity_id", unique=True, sparse=True)
        await self.db.contracts.create_index("counterparty_id")
        logger.info("✅ Contracts collection ready")

        # =====================================================================
        # SUPPORT COLLECTIONS
        # =====================================================================

        # Support Tickets
        await self._ensure_collection("support_tickets")
        await self.db.support_tickets.create_index("user_id")
        await self.db.support_tickets.create_index([("status", 1), ("priority", -1)])
        await self.db.support_tickets.create_index("assigned_to")
        logger.info("✅ Support tickets collection ready")

        # =====================================================================
        # SYSTEM COLLECTIONS
        # =====================================================================

        # Audit Log (for compliance)
        await self._ensure_collection("audit_log")
        await self.db.audit_log.create_index([("user_id", 1), ("created_at", -1)])
        await self.db.audit_log.create_index([("action", 1), ("created_at", -1)])
        # TTL: Delete after 1 year
        await self.db.audit_log.create_index("created_at", expireAfterSeconds=365*24*3600)
        logger.info("✅ Audit log collection ready")

        # Notifications
        await self._ensure_collection("notifications")
        await self.db.notifications.create_index("user_id")
        await self.db.notifications.create_index([("read", 1), ("created_at", -1)])
        # TTL: Delete after 30 days
        await self.db.notifications.create_index("created_at", expireAfterSeconds=30*24*3600)
        logger.info("✅ Notifications collection ready")

        logger.info("✅ All collections initialized successfully")

    async def _ensure_collection(self, collection_name: str):
        """Ensure collection exists, create if not"""
        collections = await self.db.list_collection_names()
        if collection_name not in collections:
            await self.db.create_collection(collection_name)

    async def drop_all(self):
        """⚠️ DROP ALL COLLECTIONS (development only!)"""
        if settings.ENVIRONMENT == "production":
            raise RuntimeError("Cannot drop collections in production!")

        logger.warning("⚠️  DROPPING ALL COLLECTIONS")
        collections = await self.db.list_collection_names()
        for collection_name in collections:
            await self.db[collection_name].drop()
            logger.warning(f"Dropped collection: {collection_name}")


# Global database manager instance
db_manager = DatabaseManager()


async def init_database():
    """Initialize database connection and collections"""
    await db_manager.connect()
    await db_manager.initialize_collections()


async def close_database():
    """Close database connection"""
    await db_manager.disconnect()


# Helper function to get database in FastAPI dependencies
async def get_database() -> AsyncIOMotorDatabase:
    """Dependency for getting database in routes"""
    if not db_manager.db:
        raise RuntimeError("Database not initialized")
    return db_manager.db
