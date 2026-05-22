"""
WAI Institute Financial Reporting
Real financial metrics, dashboards, and revenue tracking
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class FinancialReportingService:
    """Financial metrics and reporting"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.subscriptions = db.subscriptions
        self.invoices = db.invoices
        self.creator_payouts = db.creator_payouts
        self.creator_balances = db.creator_balances

    async def get_monthly_revenue_summary(self, year: int, month: int) -> Dict[str, Any]:
        """
        Get complete revenue summary for a specific month

        Returns:
        {
            "period": "2026-05",
            "total_revenue": 45000.50,
            "by_tier": {
                "basic": 5000,
                "advanced": 15000,
                "premium": 25000,
                "enterprise": 0
            },
            "new_subscriptions": 42,
            "cancelled_subscriptions": 3,
            "active_subscriptions": 1250,
            "churn_rate": 0.24,  # 3 cancelled / 1250 active = 0.24%
            "creator_payouts": 15000,
            "net_margin": 0.18,  # Revenue - payouts / Revenue
        }
        """
        try:
            # Define month boundaries
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            # Revenue by tier (from invoices paid this month)
            revenue_pipeline = [
                {"$match": {
                    "status": "paid",
                    "paid_date": {"$gte": start_date, "$lt": end_date}
                }},
                {"$lookup": {
                    "from": "subscriptions",
                    "localField": "subscription_id",
                    "foreignField": "_id",
                    "as": "subscription"
                }},
                {"$unwind": "$subscription"},
                {"$group": {
                    "_id": "$subscription.tier",
                    "amount": {"$sum": "$amount_paid"}
                }}
            ]

            revenue_by_tier = {}
            total_revenue = 0
            async for doc in self.invoices.aggregate(revenue_pipeline):
                tier = doc["_id"] or "unknown"
                amount = doc["amount"]
                revenue_by_tier[tier] = amount
                total_revenue += amount

            # New subscriptions this month
            new_subs = await self.subscriptions.count_documents({
                "created_at": {"$gte": start_date, "$lt": end_date}
            })

            # Cancelled subscriptions this month
            cancelled_subs = await self.subscriptions.count_documents({
                "cancelled_at": {"$gte": start_date, "$lt": end_date}
            })

            # Active subscriptions at month end
            active_subs = await self.subscriptions.count_documents({
                "status": "active",
                "created_at": {"$lt": end_date}
            })

            # Churn rate
            churn_rate = (cancelled_subs / active_subs * 100) if active_subs > 0 else 0

            # Creator payouts this month
            creator_payouts_pipeline = [
                {"$match": {
                    "status": "paid",
                    "paid_date": {"$gte": start_date, "$lt": end_date}
                }},
                {"$group": {
                    "_id": None,
                    "total": {"$sum": "$amount_paid"}
                }}
            ]

            creator_payouts = 0
            async for doc in self.creator_payouts.aggregate(creator_payouts_pipeline):
                creator_payouts = doc["total"]

            # Net margin (revenue - payouts / revenue)
            net_margin = ((total_revenue - creator_payouts) / total_revenue) if total_revenue > 0 else 0

            return {
                "period": f"{year:04d}-{month:02d}",
                "total_revenue": round(total_revenue, 2),
                "by_tier": {k: round(v, 2) for k, v in revenue_by_tier.items()},
                "new_subscriptions": new_subs,
                "cancelled_subscriptions": cancelled_subs,
                "active_subscriptions": active_subs,
                "churn_rate_percent": round(churn_rate, 2),
                "creator_payouts": round(creator_payouts, 2),
                "net_margin_percent": round(net_margin * 100, 2),
            }

        except Exception as e:
            logger.error(f"Error generating monthly revenue summary: {e}")
            raise

    async def get_mrr(self) -> float:
        """
        Calculate Monthly Recurring Revenue (MRR)
        Sum of all active monthly subscriptions + (annual subs / 12)
        """
        try:
            pipeline = [
                {"$match": {"status": "active"}},
                {"$group": {
                    "_id": None,
                    "monthly_subs": {
                        "$sum": {"$cond": [{"$eq": ["$billing_cycle", "monthly"]}, 30, 0]}
                    },
                    "annual_subs": {
                        "$sum": {"$cond": [{"$eq": ["$billing_cycle", "annual"]}, 1, 0]}
                    },
                    "quarterly_subs": {
                        "$sum": {"$cond": [{"$eq": ["$billing_cycle", "quarterly"]}, 1, 0]}
                    }
                }}
            ]

            # This is simplified; real MRR needs pricing lookup
            # For now, returns count of active subscriptions
            result = await self.subscriptions.aggregate(pipeline).to_list(1)

            if result:
                return result[0].get("monthly_subs", 0)
            return 0

        except Exception as e:
            logger.error(f"Error calculating MRR: {e}")
            raise

    async def get_cohort_analysis(self) -> Dict[str, Any]:
        """
        Analyze subscription retention by cohort

        Returns:
        {
            "2026-01": {
                "initial_count": 100,
                "month_1_retained": 95,
                "month_2_retained": 90,
                "month_3_retained": 87,
                "retention_rate_3m": 87%
            },
            ...
        }
        """
        try:
            # Get all subscription creation dates (month buckets)
            cohorts = {}

            pipeline = [
                {"$group": {
                    "_id": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"}
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}}
            ]

            async for doc in self.subscriptions.aggregate(pipeline):
                year = doc["_id"]["year"]
                month = doc["_id"]["month"]
                cohort_key = f"{year:04d}-{month:02d}"
                cohorts[cohort_key] = {
                    "initial_count": doc["count"],
                    "months_retained": {}
                }

            # For each cohort, calculate retention at each month
            # This is simplified; real cohort analysis requires tracking user churn
            # For now, returns initial counts

            return cohorts

        except Exception as e:
            logger.error(f"Error calculating cohort analysis: {e}")
            raise

    async def get_ltv_cac(self) -> Dict[str, float]:
        """
        Calculate Lifetime Value (LTV) and Customer Acquisition Cost (CAC)

        LTV = (average revenue per user) * (average customer lifetime in months)
        CAC = (total marketing spend) / (number of new customers)

        For now, simplified calculation
        """
        try:
            # Average subscription value
            avg_subscription_value = 30  # Placeholder

            # Average customer lifetime (in months)
            # Look at average billing cycle
            monthly_subs = await self.subscriptions.count_documents({
                "billing_cycle": "monthly",
                "status": {"$ne": "cancelled"}
            })
            annual_subs = await self.subscriptions.count_documents({
                "billing_cycle": "annual",
                "status": {"$ne": "cancelled"}
            })

            if (monthly_subs + annual_subs) == 0:
                return {"ltv": 0, "cac": 0}

            avg_months = (monthly_subs * 12 + annual_subs * 12) / (monthly_subs + annual_subs)

            ltv = avg_subscription_value * avg_months

            # CAC would need marketing spend data
            # Placeholder: estimate from acquisition channels
            cac = 50  # Placeholder

            return {
                "ltv": round(ltv, 2),
                "cac": round(cac, 2),
                "ltv_cac_ratio": round(ltv / cac, 2) if cac > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error calculating LTV/CAC: {e}")
            raise

    async def get_nrr(self) -> float:
        """
        Calculate Net Revenue Retention (NRR)
        Measures how much revenue is retained from existing customers
        (including upsells/downgrades)

        NRR = (Beginning Revenue + New Revenue - Lost Revenue) / Beginning Revenue * 100

        For now, simplified: assumes all revenue is retained
        """
        try:
            current_month_revenue = await self.get_monthly_revenue_summary(
                datetime.utcnow().year,
                datetime.utcnow().month
            )

            # Simplified: not accounting for churn in NRR calculation
            # Real NRR would track month-over-month retention

            return 100.0  # Placeholder

        except Exception as e:
            logger.error(f"Error calculating NRR: {e}")
            raise

    async def get_cash_flow_forecast(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Forecast cash flow for the next N months

        Returns: List of {month, expected_revenue, expected_expenses, expected_net}
        """
        try:
            forecast = []
            current_date = datetime.utcnow()

            for month_offset in range(months):
                future_date = current_date + timedelta(days=30 * month_offset)
                year = future_date.year
                month = future_date.month

                revenue_summary = await self.get_monthly_revenue_summary(year, month)

                forecast.append({
                    "month": revenue_summary["period"],
                    "expected_revenue": revenue_summary["total_revenue"],
                    "expected_creator_payouts": revenue_summary["creator_payouts"],
                    "expected_net": revenue_summary["total_revenue"] - revenue_summary["creator_payouts"],
                })

            return forecast

        except Exception as e:
            logger.error(f"Error generating cash flow forecast: {e}")
            raise

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Complete dashboard summary for monthly review

        Returns all key metrics at once
        """
        try:
            # Get current month
            now = datetime.utcnow()
            monthly_revenue = await self.get_monthly_revenue_summary(now.year, now.month)
            ltv_cac = await self.get_ltv_cac()
            cash_forecast = await self.get_cash_flow_forecast(3)

            return {
                "current_month": monthly_revenue,
                "ltv_cac": ltv_cac,
                "cash_forecast_3m": cash_forecast,
                "dashboard_generated_at": now.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            raise


# ============================================================================
# REVENUE RECOGNITION (Accounting)
# ============================================================================

class RevenueRecognitionService:
    """Handle ASC 606 revenue recognition for accounting"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.revenue_events = db.revenue_events
        self.invoices = db.invoices

    async def recognize_monthly_subscription_revenue(self, year: int, month: int) -> int:
        """
        Recognize subscription revenue for a month
        Called at end of month: identify all subscriptions active in month, recognize monthly amount

        Returns: Count of revenue events created
        """
        try:
            # Define month boundaries
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            # Get all subscriptions active during this month
            pipeline = [
                {"$match": {
                    "$or": [
                        {
                            "created_at": {"$lt": end_date},
                            "cancelled_at": {"$gte": start_date}
                        },
                        {
                            "created_at": {"$lt": end_date},
                            "cancelled_at": None,
                            "status": "active"
                        }
                    ]
                }}
            ]

            count = 0
            async for subscription in self.db.subscriptions.aggregate(pipeline):
                # Create revenue event for this subscription
                monthly_amount = 30  # Placeholder (would look up from pricing)

                revenue_event = {
                    "contract_id": str(subscription["_id"]),
                    "revenue_type": "subscription",
                    "amount": monthly_amount,
                    "recognition_start_date": start_date,
                    "recognition_end_date": end_date,
                    "monthly_amount": monthly_amount,
                    "actual_amount_collected": 0,  # Will update when invoice paid
                    "status": "pending",
                    "created_at": datetime.utcnow(),
                }

                await self.revenue_events.insert_one(revenue_event)
                count += 1

            logger.info(f"Recognized subscription revenue for {year}-{month:02d}: {count} events")
            return count

        except Exception as e:
            logger.error(f"Error recognizing subscription revenue: {e}")
            raise

    async def finalize_monthly_revenue(self, year: int, month: int) -> int:
        """
        Update actual collected amounts and mark revenue as recognized
        Called after month-end invoice settlement
        """
        try:
            # Get all revenue events for this month
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            result = await self.revenue_events.update_many(
                {
                    "recognition_end_date": {"$lte": end_date},
                    "status": "pending"
                },
                {
                    "$set": {
                        "status": "recognized",
                        "actual_amount_collected": "$monthly_amount"
                    }
                }
            )

            logger.info(f"Finalized {result.modified_count} revenue events for {year}-{month:02d}")
            return result.modified_count

        except Exception as e:
            logger.error(f"Error finalizing monthly revenue: {e}")
            raise
