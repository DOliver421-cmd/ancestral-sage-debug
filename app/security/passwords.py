"""app/security/passwords.py — Password hashing, token helpers, and email senders.

Extracted from backend/server.py lines 645–802.
No logic changed.
"""
import asyncio
import hashlib
import logging
import os
import secrets
from typing import Optional

from passlib.context import CryptContext

from app.config import (
    RESEND_API_KEY,
    RESEND_FROM,
    GMAIL_USER,
    GMAIL_APP_PASSWORD,
    RESET_TOKEN_TTL_MIN,
)

logger = logging.getLogger("lcewai")

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_pw(p: str) -> str:
    return pwd_ctx.hash(p)


def verify_pw(p: str, h: str) -> bool:
    return pwd_ctx.verify(p, h)


def _hash_token(raw: str) -> str:
    """Stable sha256 hash of the raw token. We never store the raw token
    in MongoDB — only the hash. Lookups use the hash."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _make_reset_token() -> tuple[str, str]:
    """Returns (raw_token, sha256_hex). The raw token is shown ONCE."""
    raw = secrets.token_urlsafe(32)
    return raw, _hash_token(raw)


def _build_reset_url(raw_token: str, base: Optional[str] = None) -> str:
    base = (base or os.environ.get("PUBLIC_APP_URL") or "").rstrip("/")
    if not base:
        return f"/reset-password?token={raw_token}"
    return f"{base}/reset-password?token={raw_token}"


def _reset_email_html(full_name: str, reset_url: str) -> tuple[str, str]:
    """Returns (subject, html) for a password reset email."""
    subject = "Reset your W.A.I. password"
    html = f"""
    <div style="font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#0a0e14">
      <h2 style="margin:0 0 8px">Reset your password</h2>
      <p>Hi {full_name},</p>
      <p>We received a request to reset your W.A.I. password. The link below is single-use and expires in {RESET_TOKEN_TTL_MIN} minutes.</p>
      <p style="margin:28px 0">
        <a href="{reset_url}" style="background:#0a0e14;color:#fff;padding:12px 20px;text-decoration:none;font-weight:600">Reset Password</a>
      </p>
      <p style="font-size:12px;color:#666">If you didn't ask for this, you can safely ignore this message — your password won't change.</p>
      <p style="font-size:12px;color:#666">Or paste this URL into your browser:<br><code style="word-break:break-all">{reset_url}</code></p>
    </div>
    """
    return subject, html


async def _send_via_resend(to_email: str, subject: str, html: str) -> bool:
    """Send via Resend API. Returns True on success."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as cx:
            r = await cx.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}",
                         "Content-Type": "application/json"},
                json={"from": RESEND_FROM, "to": [to_email],
                      "subject": subject, "html": html},
            )
        if r.status_code >= 400:
            logger.warning("Resend send failed %s: %s", r.status_code, r.text[:300])
            return False
        return True
    except Exception:
        logger.exception("Resend send raised")
        return False


async def _send_via_gmail(to_email: str, subject: str, html: str) -> bool:
    """Send via Gmail SMTP using an App Password. Returns True on success."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        return False
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    def _send():
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"W.A.I. Institute <{GMAIL_USER}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as smtp:
            smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            smtp.sendmail(GMAIL_USER, to_email, msg.as_string())

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send)
        logger.info("Gmail SMTP: sent email to %s", to_email)
        return True
    except Exception:
        logger.exception("Gmail SMTP send raised")
        return False


async def _send_reset_email(to_email: str, raw_token: str, full_name: str = "there") -> bool:
    """Send password reset email. Tries Resend first, falls back to Gmail SMTP."""
    reset_url = _build_reset_url(raw_token)
    if reset_url.startswith("/"):
        logger.warning("PUBLIC_APP_URL not set — cannot build absolute reset URL for email.")
        return False
    subject, html = _reset_email_html(full_name, reset_url)

    if RESEND_API_KEY:
        sent = await _send_via_resend(to_email, subject, html)
        if sent:
            return True
        logger.warning("Resend failed — falling back to Gmail SMTP")

    if GMAIL_USER and GMAIL_APP_PASSWORD:
        return await _send_via_gmail(to_email, subject, html)

    logger.warning("No email provider configured.")
    return False


async def _send_welcome_email(to_email: str, full_name: str) -> bool:
    """Send welcome email on registration."""
    app_url = os.environ.get("PUBLIC_APP_URL", "https://wai-institute.org")
    subject = "Welcome to WAI-Institute — You're In"
    html = f"""
    <div style="font-family:sans-serif;max-width:540px;margin:0 auto;padding:32px 24px;background:#fff;">
      <div style="background:#2e1065;border-radius:12px;padding:28px 24px;text-align:center;margin-bottom:24px;">
        <h1 style="color:#FFD100;font-size:26px;margin:0 0 8px;">Welcome, {full_name}.</h1>
        <p style="color:rgba(255,255,255,0.8);font-size:15px;margin:0;">You are now part of the WAI-Institute community.</p>
      </div>
      <p style="color:#2b1f15;font-size:15px;line-height:1.7;">Your account is active. Start with free modules — no paywall, no waiting.</p>
      <div style="text-align:center;margin:28px 0;">
        <a href="{app_url}/modules" style="background:#0d7377;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;">Start Learning Free</a>
      </div>
      <p style="color:#5a4e42;font-size:13px;">Need help? Reply to this email or visit the <a href="{app_url}/help-center" style="color:#0d7377;">Help Center</a>.</p>
      <hr style="border:none;border-top:1px solid #e0d6cc;margin:24px 0;">
      <p style="color:#9ca3af;font-size:11px;text-align:center;">WAI-Institute · MORE Help Center</p>
    </div>"""
    if RESEND_API_KEY:
        sent = await _send_via_resend(to_email, subject, html)
        if sent:
            return True
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        return await _send_via_gmail(to_email, subject, html)
    logger.warning("Welcome email not sent — no email provider configured.")
    return False
