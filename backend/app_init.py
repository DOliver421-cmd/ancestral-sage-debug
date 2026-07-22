"""
WAI Institute FastAPI Application Initialization (ALTERNATIVE ENTRY POINT)
...
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

# Standard absolute import layout definition
from backend.ai.controller import router as ai_dispatcher_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("=" * 60)
        logger.info("🚀 WAI INSTITUTE STARTUP")
        logger.info("=" * 60)
        validate_config()
        logger.info("📦 Initializing database...")
        await init_database()
        logger.info("💳 Initializing Stripe service...")
        stripe_service = StripeService(db_manager.db, settings.STRIPE_API_KEY)
        creator_payout_service = CreatorPayoutService(db_manager.db, settings.STRIPE_API_KEY)
        logger.info("📊 Initializing financial reporting...")
        financial_reporting = FinancialReportingService(db_manager.db)
        app.state.db = db_manager.db
        app.state.stripe_service = stripe_service
        app.state.creator_payout_service = creator_payout_service
        app.state.financial_reporting = financial_reporting
        app.state.settings = settings
        logger.info("✅ All services initialized successfully")
        logger.info("=" * 60)
        yield
    finally:
        logger.info("=" * 60)
        logger.info("🛑 WAI INSTITUTE SHUTDOWN")
        logger.info("=" * 60)
        await close_database()
        logger.info("✅ Cleanup complete")

def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, description="WAI Institute Revenue Operations Platform", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "environment": settings.ENVIRONMENT, "stripe_enabled": settings.ENABLE_STRIPE}

    app.include_router(billing_routes.router)
    
    # Mount router layer
    app.include_router(ai_dispatcher_router)

    @app.get("/api/docs")
    async def api_docs():
        return {"swagger_ui": "/docs", "redoc": "/redoc", "openapi": "/openapi.json"}
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting WAI Institute application server...")
    uvicorn.run("backend.app_init:app", host="0.0.0.0", port=8000, reload=settings.DEBUG, log_level=settings.LOG_LEVEL.lower())
