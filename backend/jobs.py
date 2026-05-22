"""
WAI Institute Scheduled Jobs
Automated background tasks: payouts, revenue recognition, reminders
"""

import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .database import db_manager
from .billing.stripe_service import CreatorPayoutService
from .billing.financial_reporting import RevenueRecognitionService
from .config import settings

logger = logging.getLogger(__name__)


class JobScheduler:
    """Manages all scheduled background jobs"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        """Start the job scheduler"""
        logger.info("Starting job scheduler...")

        # Monthly jobs
        self.scheduler.add_job(
            process_creator_payouts,
            CronTrigger(day=settings.MONTHLY_PAYOUT_DAY, hour=2, minute=0),
            id="process_creator_payouts",
            name="Process Creator Monthly Payouts",
            replace_existing=True,
        )

        self.scheduler.add_job(
            recognize_monthly_revenue,
            CronTrigger(day="last", hour=3, minute=0),
            id="recognize_monthly_revenue",
            name="Recognize Monthly Subscription Revenue",
            replace_existing=True,
        )

        # Daily jobs
        self.scheduler.add_job(
            check_renewal_deadlines,
            CronTrigger(hour=6, minute=0),
            id="check_renewal_deadlines",
            name="Check Enterprise Renewal Deadlines",
            replace_existing=True,
        )

        self.scheduler.add_job(
            check_failed_payments,
            CronTrigger(hour=7, minute=0),
            id="check_failed_payments",
            name="Check Failed Payments & Send Dunning",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("✅ Job scheduler started")

    async def stop(self):
        """Stop the job scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("✅ Job scheduler stopped")


# Global scheduler instance
job_scheduler = JobScheduler()


# ============================================================================
# JOB FUNCTIONS
# ============================================================================

async def process_creator_payouts():
    """
    Process monthly creator payouts
    Runs on 1st of month at 2am UTC
    """
    logger.info("=" * 60)
    logger.info("🚀 STARTING: Process Creator Monthly Payouts")
    logger.info("=" * 60)

    try:
        if not db_manager.db:
            logger.error("Database not initialized")
            return

        creator_payout_service = CreatorPayoutService(db_manager.db, settings.STRIPE_API_KEY)

        # Process monthly payouts
        stats = await creator_payout_service.process_monthly_payouts()

        logger.info(f"✅ Creator payouts processed: {stats['processed']} successful, {stats['failed']} failed")

        # Log to audit trail
        await log_job_execution(
            "creator_payouts",
            "success",
            {
                "processed": stats["processed"],
                "failed": stats["failed"],
            }
        )

    except Exception as e:
        logger.error(f"❌ Error processing creator payouts: {e}")
        await log_job_execution("creator_payouts", "failed", {"error": str(e)})

        # Alert ops team
        await send_alert(
            f"Creator payout job failed: {e}",
            "critical"
        )


async def recognize_monthly_revenue():
    """
    Recognize monthly subscription revenue for accounting
    Runs on last day of month at 3am UTC
    """
    logger.info("=" * 60)
    logger.info("🚀 STARTING: Recognize Monthly Subscription Revenue")
    logger.info("=" * 60)

    try:
        if not db_manager.db:
            logger.error("Database not initialized")
            return

        now = datetime.utcnow()
        year = now.year
        month = now.month

        revenue_service = RevenueRecognitionService(db_manager.db)

        # Recognize subscription revenue
        count = await revenue_service.recognize_monthly_subscription_revenue(year, month)

        logger.info(f"✅ Recognized revenue for {year}-{month:02d}: {count} subscription events")

        # Finalize previous month revenue
        if month == 1:
            prev_month = 12
            prev_year = year - 1
        else:
            prev_month = month - 1
            prev_year = year

        finalized = await revenue_service.finalize_monthly_revenue(prev_year, prev_month)
        logger.info(f"✅ Finalized revenue for {prev_year}-{prev_month:02d}: {finalized} events")

        await log_job_execution(
            "revenue_recognition",
            "success",
            {
                "recognized": count,
                "finalized": finalized,
                "period": f"{year}-{month:02d}",
            }
        )

    except Exception as e:
        logger.error(f"❌ Error recognizing revenue: {e}")
        await log_job_execution("revenue_recognition", "failed", {"error": str(e)})
        await send_alert(f"Revenue recognition job failed: {e}", "critical")


async def check_renewal_deadlines():
    """
    Check for upcoming enterprise contract renewals
    Send reminder emails if renewal is within 90 days
    Runs daily at 6am UTC
    """
    logger.info("🔍 Checking enterprise renewal deadlines...")

    try:
        if not db_manager.db:
            return

        contracts = db_manager.db.contracts
        now = datetime.utcnow()
        renewal_cutoff = now + timedelta(days=90)

        upcoming_renewals = await contracts.find({
            "status": "active",
            "end_date": {
                "$gte": now,
                "$lte": renewal_cutoff
            }
        }).to_list(None)

        for contract in upcoming_renewals:
            days_until_renewal = (contract["end_date"] - now).days

            # Send renewal reminder (simplistic implementation)
            logger.info(f"📧 Renewal reminder due in {days_until_renewal} days for {contract['counterparty_id']}")

            # TODO: Send actual email via SendGrid
            # await send_renewal_email(contract)

        logger.info(f"✅ Checked renewal deadlines: {len(upcoming_renewals)} contracts need attention")

    except Exception as e:
        logger.error(f"❌ Error checking renewals: {e}")
        await send_alert(f"Renewal check failed: {e}", "warning")


async def check_failed_payments():
    """
    Check for failed payment invoices
    Send payment reminder emails (dunning)
    Runs daily at 7am UTC
    """
    logger.info("🔍 Checking for failed payments...")

    try:
        if not db_manager.db:
            return

        invoices = db_manager.db.invoices
        now = datetime.utcnow()

        # Find overdue invoices
        overdue = await invoices.find({
            "status": "open",
            "due_date": {"$lte": now}
        }).to_list(None)

        for invoice in overdue:
            days_overdue = (now - invoice["due_date"]).days

            logger.info(f"⚠️  Invoice {invoice['_id']} is {days_overdue} days overdue")

            # TODO: Send payment reminder via SendGrid
            # await send_payment_reminder_email(invoice)

        logger.info(f"✅ Checked failed payments: {len(overdue)} overdue invoices found")

    except Exception as e:
        logger.error(f"❌ Error checking failed payments: {e}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def log_job_execution(job_name: str, status: str, metadata: dict = None):
    """Log job execution for audit trail"""
    if not db_manager.db:
        return

    try:
        job_log = {
            "job_name": job_name,
            "status": status,
            "executed_at": datetime.utcnow(),
            "metadata": metadata or {},
        }

        await db_manager.db.job_execution_log.insert_one(job_log)

    except Exception as e:
        logger.error(f"Failed to log job execution: {e}")


async def send_alert(message: str, severity: str = "warning"):
    """Send alert to ops team (Slack, email, etc.)"""
    logger.warning(f"ALERT [{severity}]: {message}")

    # TODO: Send Slack alert if webhook configured
    # if settings.SLACK_WEBHOOK_URL:
    #     await send_slack_message(settings.SLACK_WEBHOOK_URL, message, severity)

    # TODO: Send email alert if critical
    # if severity == "critical" and settings.ENABLE_EMAILS:
    #     await send_email(settings.ADMIN_EMAIL, f"WAI Alert: {message}")


# ============================================================================
# STARTUP/SHUTDOWN INTEGRATION
# ============================================================================

async def start_job_scheduler():
    """Start job scheduler (called on app startup)"""
    await job_scheduler.start()


async def stop_job_scheduler():
    """Stop job scheduler (called on app shutdown)"""
    await job_scheduler.stop()
