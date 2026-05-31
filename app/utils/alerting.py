"""app/utils/alerting.py — External alerting helpers.

Supports:
  - Sentry: unhandled exceptions, critical errors
  - Slack webhook: security events (break-glass, account lockout, breaker trips)

Both are opt-in via environment variables:
  SENTRY_DSN          — Sentry project DSN (omit to disable)
  SLACK_ALERT_WEBHOOK — Slack incoming webhook URL (omit to disable)

Sentry is initialised once at import time. Slack alerts are fire-and-forget
async calls; failures are logged but never raise.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("lcewai")

# ── Sentry initialisation ─────────────────────────────────────────────────────

def init_sentry() -> bool:
    """Initialise Sentry SDK if SENTRY_DSN is configured. Returns True if active."""
    from app.config import SENTRY_DSN, APP_VERSION, APP_ENV
    if not SENTRY_DSN:
        return False
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            release=f"wai-platform@{APP_VERSION}",
            environment=APP_ENV,
            integrations=[StarletteIntegration(), FastApiIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
        logger.info("Sentry initialised (env=%s)", APP_ENV)
        return True
    except ImportError:
        logger.warning("sentry_sdk not installed — Sentry alerting disabled.")
        return False
    except Exception as exc:
        logger.warning("Sentry init failed: %s", exc)
        return False


# ── Slack security alert ──────────────────────────────────────────────────────

async def slack_alert(event: str, detail: str, level: str = "warning", user_id: Optional[str] = None) -> None:
    """Send a security alert to the configured Slack webhook (fire-and-forget).

    Args:
        event:   Short event name, e.g. "break_glass.activated"
        detail:  Human-readable description of what happened
        level:   "info" | "warning" | "critical"
        user_id: Actor user ID (if applicable)
    """
    from app.config import SLACK_ALERT_WEBHOOK, APP_ENV
    if not SLACK_ALERT_WEBHOOK:
        return
    try:
        import httpx as _httpx
        colour = {"info": "#36a64f", "warning": "#ff9800", "critical": "#e53935"}.get(level, "#888888")
        payload = {
            "attachments": [{
                "color": colour,
                "title": f"[{APP_ENV.upper()}] Security Event: {event}",
                "text": detail,
                "fields": [{"title": "Actor", "value": user_id or "system", "short": True}],
                "footer": "WAI Platform Alerting",
            }]
        }
        async with _httpx.AsyncClient(timeout=5.0) as client:
            await client.post(SLACK_ALERT_WEBHOOK, json=payload)
    except Exception as exc:
        logger.warning("Slack alert failed (non-fatal): %s", exc)


async def alert_break_glass(actor_id: str, scope: str, reason: str) -> None:
    await slack_alert(
        "break_glass.activated",
        f"Actor `{actor_id}` activated break-glass override.\nScope: {scope}\nReason: {reason}",
        level="critical",
        user_id=actor_id,
    )


async def alert_account_locked(email: str) -> None:
    await slack_alert(
        "auth.account_locked",
        f"Account locked after 10 failed login attempts: `{email}`",
        level="warning",
    )


async def alert_circuit_breaker(service: str, detail: str) -> None:
    await slack_alert(
        f"circuit_breaker.tripped.{service}",
        detail,
        level="critical",
    )
