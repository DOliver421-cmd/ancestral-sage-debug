"""
Revenue Operations System Integration
Integrates billing, CRM, financial reporting, and scheduled jobs into main FastAPI app.
Called from server.py on_startup/on_shutdown.
"""

import logging
import os
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorDatabase
from .jobs import job_scheduler

logger = logging.getLogger(__name__)


async def init_revenue_operations(db: AsyncIOMotorDatabase) -> dict:
    """
    Initialize all revenue operations collections and indexes.
    Called in on_startup() - idempotent, safe to call multiple times.

    Returns:
        dict with initialization status
    """
    try:
        # ── Billing Collections ──────────────────────────────────────────────────
        await db.subscriptions.create_index([("user_id", 1), ("status", 1)])
        await db.subscriptions.create_index("stripe_subscription_id", unique=True, sparse=True)
        await db.subscriptions.create_index([("created_at", -1)])

        await db.invoices.create_index([("user_id", 1), ("status", 1)])
        await db.invoices.create_index("stripe_invoice_id", unique=True, sparse=True)
        await db.invoices.create_index([("created_at", -1)])
        await db.invoices.create_index("due_date")

        await db.payment_methods.create_index([("user_id", 1)])
        await db.payment_methods.create_index("stripe_payment_method_id", unique=True)
        await db.payment_methods.create_index([("created_at", -1)])

        # ── Usage & Creator Finance ──────────────────────────────────────────────
        await db.usage_events.create_index([("user_id", 1), ("timestamp", -1)])
        await db.usage_events.create_index([("created_at", -1)])

        await db.creator_balances.create_index("creator_id", unique=True)

        await db.creator_payouts.create_index([("creator_id", 1), ("created_at", -1)])
        await db.creator_payouts.create_index([("status", 1), ("created_at", -1)])
        await db.creator_payouts.create_index([("created_at", -1)])

        # ── Revenue Recognition ──────────────────────────────────────────────────
        await db.revenue_events.create_index([("subscription_id", 1)])
        await db.revenue_events.create_index([("period", 1), ("status", 1)])
        await db.revenue_events.create_index([("created_at", -1)])

        # ── Sales Pipeline (CRM) ─────────────────────────────────────────────────
        await db.leads.create_index([("source", 1), ("status", 1)])
        await db.leads.create_index([("owner_id", 1)])
        await db.leads.create_index("company_name")
        await db.leads.create_index([("created_at", -1)])
        await db.leads.create_index([("score", -1)])  # For lead ranking

        await db.opportunities.create_index([("lead_id", 1)])
        await db.opportunities.create_index([("owner_id", 1), ("stage", 1)])
        await db.opportunities.create_index([("stage", 1), ("probability", -1)])  # Pipeline view
        await db.opportunities.create_index([("created_at", -1)])
        await db.opportunities.create_index("expected_close_date")

        await db.activity_log.create_index([("opportunity_id", 1)])
        await db.activity_log.create_index([("created_at", -1)])

        # ── Contracts ────────────────────────────────────────────────────────────
        await db.contracts.create_index([("counterparty_id", 1), ("status", 1)])
        await db.contracts.create_index([("type", 1), ("status", 1)])
        await db.contracts.create_index("end_date")  # For renewal reminders
        await db.contracts.create_index([("created_at", -1)])

        # ── Job Execution Audit Trail ────────────────────────────────────────────
        await db.job_execution_log.create_index([("job_name", 1), ("executed_at", -1)])
        await db.job_execution_log.create_index([("status", 1)])
        # Auto-delete job logs after 1 year for space management
        await db.job_execution_log.create_index("executed_at", expireAfterSeconds=365 * 24 * 3600)

        logger.info("✅ Revenue operations collections and indexes initialized")
        return {"status": "success", "collections": 11}

    except Exception as e:
        logger.warning(f"Revenue operations initialization (non-fatal): {e}")
        return {"status": "partial", "error": str(e)}


async def start_revenue_operations(db: AsyncIOMotorDatabase) -> None:
    """Start scheduled jobs for revenue operations."""
    try:
        await job_scheduler.start()
        logger.info("✅ Revenue operations job scheduler started")
    except Exception as e:
        logger.warning(f"Job scheduler startup failed (non-fatal): {e}")


def stop_revenue_operations() -> None:
    """Stop scheduled jobs on shutdown."""
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule stop as a task if loop is running
            asyncio.create_task(job_scheduler.stop())
        else:
            # If loop is not running, we're likely in shutdown - just stop directly
            job_scheduler.scheduler.shutdown(wait=False)
        logger.info("✅ Revenue operations job scheduler stopped")
    except Exception as e:
        logger.warning(f"Job scheduler shutdown (non-fatal): {e}")


def init_revenue_services(app: FastAPI, db: AsyncIOMotorDatabase) -> None:
    """Initialize revenue operations services and attach to app.state"""
    try:
        from .billing.stripe_service import StripeService, CreatorPayoutService
        from .billing.financial_reporting import FinancialReportingService

        stripe_key = os.environ.get("STRIPE_API_KEY", "")

        app.state.stripe_service = StripeService(db, stripe_key)
        app.state.creator_payout_service = CreatorPayoutService(db, stripe_key)
        app.state.financial_service = FinancialReportingService(db)

        logger.info("✅ Revenue services initialized")
    except Exception as e:
        logger.warning(f"Revenue services initialization (non-fatal): {e}")


def get_revenue_routers():
    """Returns all revenue operations API routers to be included in main app."""
    routers = []

    try:
        from .billing.routes import router as billing_router
        routers.append(billing_router)
        logger.info("✅ Billing router loaded")
    except Exception as e:
        logger.warning(f"Could not load billing router: {e}")

    try:
        from .crm.routes import router as crm_router
        routers.append(crm_router)
        logger.info("✅ CRM router loaded")
    except Exception as e:
        logger.warning(f"Could not load CRM router: {e}")

    return routers
