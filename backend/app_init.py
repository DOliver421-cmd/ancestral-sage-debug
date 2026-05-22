"""
WAI Institute FastAPI Application Initialization
Wires together all services: Stripe, database, CRM, billing, etc.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings, validate_config
from .database import init_database, close_database, db_manager
from .billing.stripe_service import StripeService, CreatorPayoutService
from .billing.financial_reporting import FinancialReportingService
from .billing import routes as billing_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown
    FastAPI will call this on startup and shutdown
    """
    # =====================================================================
    # STARTUP
    # =====================================================================
    try:
        logger.info("=" * 60)
        logger.info("🚀 WAI INSTITUTE STARTUP")
        logger.info("=" * 60)

        # Validate configuration
        validate_config()

        # Initialize database
        logger.info("📦 Initializing database...")
        await init_database()

        # Initialize Stripe service
        logger.info("💳 Initializing Stripe service...")
        stripe_service = StripeService(db_manager.db, settings.STRIPE_API_KEY)
        creator_payout_service = CreatorPayoutService(db_manager.db, settings.STRIPE_API_KEY)

        # Initialize financial reporting
        logger.info("📊 Initializing financial reporting...")
        financial_reporting = FinancialReportingService(db_manager.db)

        # Store in app state for access in routes
        app.state.db = db_manager.db
        app.state.stripe_service = stripe_service
        app.state.creator_payout_service = creator_payout_service
        app.state.financial_reporting = financial_reporting
        app.state.settings = settings

        logger.info("✅ All services initialized successfully")
        logger.info("=" * 60)

        yield

        # =====================================================================
        # SHUTDOWN
        # =====================================================================
    finally:
        logger.info("=" * 60)
        logger.info("🛑 WAI INSTITUTE SHUTDOWN")
        logger.info("=" * 60)

        await close_database()

        logger.info("✅ Cleanup complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    # Create app with lifespan
    app = FastAPI(
        title=settings.APP_NAME,
        description="WAI Institute Revenue Operations Platform",
        version="1.0.0",
        lifespan=lifespan,
    )

    # =====================================================================
    # MIDDLEWARE
    # =====================================================================

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # =====================================================================
    # ROUTES
    # =====================================================================

    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "stripe_enabled": settings.ENABLE_STRIPE,
        }

    # Billing routes
    app.include_router(billing_routes.router)

    # API documentation
    @app.get("/api/docs")
    async def api_docs():
        """API documentation"""
        return {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        }

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting WAI Institute application server...")
    uvicorn.run(
        "backend.app_init:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
