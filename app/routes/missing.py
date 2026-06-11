"""app/routes/missing.py — Missing persons tip submission."""
import logging
import os
import smtplib
from email.mime.text import MIMEText
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger("lcewai")
router = APIRouter()

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
ALERT_EMAIL = os.environ.get("GMAIL_USER", "youpickeddoliver@gmail.com")


class TipBody(BaseModel):
    name: str
    tip: str
    contact: Optional[str] = ""


@router.post("/missing/tip")
async def submit_tip(body: TipBody):
    msg_body = f"TIP FOR: {body.name}\n\n{body.tip}"
    if body.contact:
        msg_body += f"\n\nContact: {body.contact}"

    if GMAIL_USER and GMAIL_APP_PASSWORD:
        try:
            msg = MIMEText(msg_body)
            msg["Subject"] = f"MISSING PERSON TIP: {body.name}"
            msg["From"] = GMAIL_USER
            msg["To"] = ALERT_EMAIL
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                s.send_message(msg)
        except Exception as e:
            logger.error("Tip email failed: %s", e)

    logger.info("Missing person tip received for %s", body.name)
    return {"received": True}
