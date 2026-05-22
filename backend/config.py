"""
WAI Institute Configuration & Environment Setup
Real configuration management for all services
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """All application settings from environment variables"""

    # =====================================================================
    # DATABASE
    # =====================================================================
    MONGODB_URI: str = os.getenv(
        "MONGODB_URI",
        "mongodb://localhost:27017/wai_institute"
    )
    DATABASE_NAME: str = "wai_institute"

    # =====================================================================
    # STRIPE
    # =====================================================================
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # =====================================================================
    # JWT & AUTH
    # =====================================================================
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # =====================================================================
    # EMAIL & NOTIFICATIONS
    # =====================================================================
    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@wai-institute.com")
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@wai-institute.com")
    NOREPLY_EMAIL: str = os.getenv("NOREPLY_EMAIL", "noreply@wai-institute.com")

    # =====================================================================
    # SLACK (for alerts, logging)
    # =====================================================================
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    SLACK_ALERTS_CHANNEL: str = "#alerts"

    # =====================================================================
    # APP SETTINGS
    # =====================================================================
    APP_NAME: str = "WAI Institute"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development, staging, production
    # Note: CORS_ORIGINS is intentionally NOT defined here.
    # server.py reads it directly via os.environ.get('CORS_ORIGINS', '*').
    # Defining it as `list` here causes pydantic-settings to expect JSON,
    # which crashes startup when the env var is a plain comma-separated string.

    # =====================================================================
    # BUSINESS SETTINGS
    # =====================================================================
    CREATOR_REVENUE_SHARE: float = 0.7  # Creator gets 70%
    PLATFORM_COMMISSION: float = 0.3  # Platform takes 30%
    CREATOR_PAYOUT_MINIMUM: float = 50.0  # Minimum $50 payout
    MONTHLY_PAYOUT_DAY: int = 1  # Pay creators on 1st of month

    # =====================================================================
    # FEATURE FLAGS
    # =====================================================================
    ENABLE_STRIPE: bool = bool(STRIPE_API_KEY)  # Only enable if key is set
    ENABLE_PAYOUTS: bool = ENABLE_STRIPE and os.getenv("ENABLE_PAYOUTS", "False").lower() == "true"
    ENABLE_EMAILS: bool = bool(SENDGRID_API_KEY)
    ENABLE_SLACK_ALERTS: bool = bool(SLACK_WEBHOOK_URL)

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance
settings = Settings()


# Validation at startup
def validate_config():
    """Validate critical configuration"""
    errors = []

    if not settings.STRIPE_API_KEY:
        errors.append("STRIPE_API_KEY not set")

    if settings.ENVIRONMENT == "production":
        if settings.DEBUG:
            errors.append("DEBUG cannot be True in production")
        if settings.JWT_SECRET == "dev-secret-change-in-production":
            errors.append("JWT_SECRET must be changed for production")

    if errors:
        raise ValueError("Configuration errors: " + "; ".join(errors))

    print(f"✅ Configuration validated ({settings.ENVIRONMENT} mode)")


if __name__ == "__main__":
    # Print all settings (for debugging)
    print("WAI INSTITUTE CONFIGURATION")
    print("=" * 50)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database: {settings.MONGODB_URI[:50]}...")
    print(f"Stripe: {'Enabled' if settings.ENABLE_STRIPE else 'Disabled'}")
    print(f"Emails: {'Enabled' if settings.ENABLE_EMAILS else 'Disabled'}")
    print(f"Slack: {'Enabled' if settings.ENABLE_SLACK_ALERTS else 'Disabled'}")
    print("=" * 50)
