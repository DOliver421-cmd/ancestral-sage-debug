"""
Director Tool Suite
===================
Zero-cost, fully redundant tool implementations for The Director AI endpoint.

Tools
-----
  web_search          — DuckDuckGo HTML scrape (free, no key) → DDG Instant API → graceful fallback
  fetch_url           — httpx + BeautifulSoup4, size-guarded → requests fallback
  send_email          — Gmail SMTP (smtplib built-in) → MongoDB queue fallback → log-only fallback
  get_incident_register — live MongoDB query, stale-flag detection
  read_file           — reads uploaded file content from MongoDB temp store (24h TTL)

No paid APIs. No new external dependencies beyond beautifulsoup4 + httpx (already in use).
"""
import asyncio
import html as _html
import logging
import os
import re
import smtplib
import socket
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger(__name__)

# ── Environment ───────────────────────────────────────────────────────────────
GMAIL_USER         = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
EXEC_EMAIL         = os.environ.get("EXEC_ADMIN_EMAIL", "delon.oliver@lightningcityelectric.com")

_DDG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Claude tool definitions ───────────────────────────────────────────────────
DIRECTOR_TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Search the live web for current information, news, entity profiles, "
            "legal filings, threats, or any research topic. Returns titles, URLs, "
            "and summaries. Chain with fetch_url to read full pages."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {
                    "type": "integer",
                    "description": "Max results to return (default 6, max 10)",
                    "default": 6,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_url",
        "description": (
            "Fetch and read the full text content of any public web page. "
            "Use after web_search to read specific articles, documents, or filings. "
            "Returns cleaned readable text with HTML stripped."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL to fetch (must begin with http:// or https://)",
                }
            },
            "required": ["url"],
        },
    },
    {
        "name": "send_email",
        "description": (
            "Send a branded WAI-Institute email. Use for executive briefs, alerts, "
            "task packages, or any formal communication. Pass 'executive' as the "
            "recipient to send directly to D. Oliver."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email. Use 'executive' to target D. Oliver.",
                },
                "subject": {"type": "string", "description": "Email subject line"},
                "body": {
                    "type": "string",
                    "description": "Email body. Plain text; markdown formatting is respected.",
                },
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "get_incident_register",
        "description": (
            "Pull WAI-Institute's live open incident register from the database. "
            "Returns all unresolved incidents with severity, status, owner, and age. "
            "Call on every status check, daily brief, or threat response."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "read_file",
        "description": (
            "Read the content of a file uploaded by the executive in this session. "
            "Returns full text content of documents, spreadsheets, code, or data files."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The file_id returned when the file was uploaded",
                }
            },
            "required": ["file_id"],
        },
    },
]


# ── Tool implementations ──────────────────────────────────────────────────────

async def tool_web_search(query: str, num_results: int = 6) -> str:
    """
    Tier 1: DuckDuckGo HTML POST scrape (most complete results, no key needed)
    Tier 2: DuckDuckGo Instant Answer JSON API (knowledge-graph results)
    Tier 3: Graceful fallback with clear notice
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        BeautifulSoup = None

    num_results = max(1, min(int(num_results), 10))
    results: list[str] = []

    # ── Tier 1: DDG HTML ─────────────────────────────────────────────────────
    if BeautifulSoup:
        try:
            import httpx
            async with httpx.AsyncClient(
                timeout=12, follow_redirects=True, headers=_DDG_HEADERS
            ) as client:
                r = await client.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": query, "kl": "us-en"},
                )
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    for el in soup.select(".result")[:num_results]:
                        title   = (el.select_one(".result__title") or el).get_text(strip=True)
                        snippet = (el.select_one(".result__snippet") or el).get_text(strip=True)
                        url_el  = el.select_one("a.result__url")
                        href    = url_el["href"] if url_el and url_el.get("href") else ""
                        if title:
                            results.append(f"**{title}**\n{href}\n{snippet}")
                    if results:
                        return (
                            f"Web search: '{query}'\n\n"
                            + "\n\n".join(results)
                        )
        except Exception as e:
            logger.warning("DDG HTML search failed: %s", e)

    # ── Tier 2: DDG Instant Answer API ───────────────────────────────────────
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
                headers={"User-Agent": "WAI-Director/1.0"},
            )
            data = r.json()
            if data.get("Abstract"):
                results.append(f"SUMMARY: {data['Abstract']}\nSource: {data.get('AbstractURL','')}")
            for topic in data.get("RelatedTopics", [])[:num_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(f"- {topic['Text']}\n  {topic.get('FirstURL','')}")
            if results:
                return f"Search: '{query}'\n\n" + "\n".join(results)
    except Exception as e:
        logger.warning("DDG API fallback failed: %s", e)

    # ── Tier 3: Graceful degradation ─────────────────────────────────────────
    return (
        f"[SEARCH NOTICE] Live search for '{query}' is temporarily unavailable. "
        "The Director is proceeding with institutional knowledge. "
        "Live verification is recommended once connectivity is restored."
    )


async def tool_fetch_url(url: str) -> str:
    """
    Tier 1: httpx + BeautifulSoup4 — async, full HTML parsing
    Tier 2: requests (sync, run in executor) — fallback for sites that reject async clients
    """
    if not url.startswith(("http://", "https://")):
        return f"[ERROR] Invalid URL: must start with http:// or https://"

    MAX_CHARS = 12_000  # prevent token blowout on huge pages

    def _clean_html(raw: str) -> str:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer",
                              "aside", "form", "noscript", "iframe", "svg"]):
                tag.decompose()
            body = soup.find("main") or soup.find("article") or soup.find("body") or soup
            text = body.get_text(separator="\n", strip=True)
            return re.sub(r"\n{3,}", "\n\n", text)
        except ImportError:
            # Strip tags with regex if bs4 unavailable
            text = re.sub(r"<[^>]+>", " ", raw)
            return re.sub(r"\s{2,}", " ", text).strip()

    # ── Tier 1: httpx ────────────────────────────────────────────────────────
    try:
        import httpx
        async with httpx.AsyncClient(
            timeout=15, follow_redirects=True, headers=_DDG_HEADERS
        ) as client:
            r = await client.get(url)
            ct = r.headers.get("content-type", "")
            if "text/plain" in ct or "application/json" in ct:
                return f"[{url}]\n\n{r.text[:MAX_CHARS]}"
            text = _clean_html(r.text)[:MAX_CHARS]
            return f"[{url}]\n\n{text}"
    except Exception as e:
        logger.warning("fetch_url httpx failed for %s: %s", url, e)

    # ── Tier 2: requests (sync executor) ─────────────────────────────────────
    try:
        import requests as _req
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None,
            lambda: _req.get(url, timeout=10, headers={"User-Agent": "WAI-Director/1.0"}).text,
        )
        text = _clean_html(raw)[:MAX_CHARS]
        return f"[{url}]\n\n{text}"
    except Exception as e:
        logger.warning("fetch_url requests fallback failed for %s: %s", url, e)

    return f"[FETCH FAILED] Could not retrieve {url}. The page may be protected or unavailable."


async def tool_send_email(to: str, subject: str, body: str, db=None) -> str:
    """
    Tier 1: Gmail SMTP via smtplib (GMAIL_USER + GMAIL_APP_PASSWORD env vars)
    Tier 2: MongoDB email_queue (admin panel can view + retry)
    Tier 3: Log only with clear env-var instructions
    """
    # Resolve shorthand recipients
    _shortcuts = {
        "executive", "exec", "d. oliver", "d.oliver", "delon", "director", "nam oshun"
    }
    if to.strip().lower() in _shortcuts:
        to = EXEC_EMAIL

    ts          = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    full_subject = f"[WAI-Institute] {subject}"
    html_body = (
        '<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;'
        'background:#0A0F1E;color:#E8E8E8;padding:24px;border-radius:4px;">'
        '<div style="border-bottom:2px solid #C9A84C;padding-bottom:12px;margin-bottom:20px;">'
        '<span style="font-size:11px;letter-spacing:2px;color:#C9A84C;font-weight:700;">'
        "WAI-INSTITUTE — THE DIRECTOR</span></div>"
        f'<div style="white-space:pre-wrap;line-height:1.7;font-size:14px;">{_html.escape(body)}</div>'
        '<div style="margin-top:24px;border-top:1px solid #333;padding-top:12px;'
        f'font-size:10px;color:#555;letter-spacing:1px;">SENT {ts} · WAI-INSTITUTE EXECUTIVE INTELLIGENCE</div>'
        "</div>"
    )

    # ── Tier 1: Gmail SMTP ───────────────────────────────────────────────────
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = full_subject
            msg["From"]    = f"WAI-Institute Director <{GMAIL_USER}>"
            msg["To"]      = to
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: _smtp_send(msg),
            )
            return f"✓ Email delivered to {to}\nSubject: {full_subject}"
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP auth failed — verify GMAIL_USER / GMAIL_APP_PASSWORD")
        except (socket.timeout, smtplib.SMTPException, OSError) as e:
            logger.warning("SMTP send failed: %s", e)

    # ── Tier 2: MongoDB queue ────────────────────────────────────────────────
    if db is not None:
        try:
            await db.email_queue.insert_one({
                "id":         str(uuid.uuid4()),
                "to":         to,
                "subject":    full_subject,
                "body":       body,
                "html_body":  html_body,
                "status":     "queued",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source":     "director",
            })
            return (
                f"⚠ Email queued (SMTP offline).\n"
                f"To: {to} | Subject: {full_subject}\n"
                "Set GMAIL_USER and GMAIL_APP_PASSWORD in Railway environment variables "
                "to enable live delivery. Email is saved and can be retried."
            )
        except Exception as e:
            logger.error("Email queue insert failed: %s", e)

    # ── Tier 3: Log only ─────────────────────────────────────────────────────
    logger.info("EMAIL (not sent): to=%s subject=%s", to, subject)
    return (
        f"[EMAIL LOGGED — NOT SENT]\n"
        f"To: {to} | Subject: {full_subject}\n"
        "Add GMAIL_USER and GMAIL_APP_PASSWORD to your environment variables to enable sending."
    )


def _smtp_send(msg: MIMEMultipart) -> None:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as s:
        s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        s.send_message(msg)


async def tool_get_incident_register(db) -> str:
    """Live MongoDB incident query with stale-flag detection."""
    try:
        now = datetime.now(timezone.utc)
        incidents = await db.incidents.find(
            {"status": {"$nin": ["resolved", "closed"]}},
            {"_id": 0, "id": 1, "title": 1, "severity": 1,
             "status": 1, "created_at": 1, "assigned_to": 1},
        ).sort("created_at", -1).limit(20).to_list(20)

        if not incidents:
            return "◈ INCIDENT REGISTER — ALL CLEAR\nNo open incidents. System nominal."

        lines = [f"◈ INCIDENT REGISTER — {len(incidents)} OPEN\n"]
        for inc in incidents:
            sev    = (inc.get("severity") or "unknown").upper()
            status = inc.get("status", "open")
            title  = inc.get("title", "Untitled")
            owner  = inc.get("assigned_to") or "Unassigned"
            stale  = ""
            try:
                created = inc.get("created_at", "")
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                age_h = (now - dt).total_seconds() / 3600
                if age_h > 72:
                    stale = f" ⚠ STALE ({int(age_h)}h)"
            except Exception:
                pass
            lines.append(f"[{sev}] {title}\n  Status: {status} | Owner: {owner}{stale}")

        return "\n".join(lines)
    except Exception as e:
        logger.error("Incident register query error: %s", e)
        return "[INCIDENT REGISTER UNAVAILABLE] DB query failed — check MongoDB connection."


async def tool_read_file(file_id: str, db) -> str:
    """Read content of a temp-stored uploaded file."""
    try:
        doc = await db.director_uploads.find_one({"id": file_id}, {"_id": 0})
        if not doc:
            return (
                f"[FILE NOT FOUND] No file with id '{file_id}'. "
                "Files expire after 24 hours."
            )
        if doc.get("is_binary"):
            return (
                f"[BINARY FILE] '{doc.get('filename')}' is a binary file "
                f"({doc.get('content_type')}) and cannot be read as text."
            )
        return f"[FILE: {doc.get('filename', 'unknown')}]\n\n{doc.get('content', '')}"
    except Exception as e:
        logger.error("read_file error for %s: %s", file_id, e)
        return f"[READ ERROR] Could not read file '{file_id}'."


# ── Tool dispatcher ───────────────────────────────────────────────────────────

async def dispatch_tool(tool_name: str, tool_input: dict, db=None) -> str:
    """Route a Claude tool_use block to the correct implementation."""
    try:
        if tool_name == "web_search":
            return await tool_web_search(
                query=tool_input["query"],
                num_results=tool_input.get("num_results", 6),
            )
        elif tool_name == "fetch_url":
            return await tool_fetch_url(url=tool_input["url"])
        elif tool_name == "send_email":
            return await tool_send_email(
                to=tool_input["to"],
                subject=tool_input["subject"],
                body=tool_input["body"],
                db=db,
            )
        elif tool_name == "get_incident_register":
            return await tool_get_incident_register(db=db)
        elif tool_name == "read_file":
            return await tool_read_file(file_id=tool_input["file_id"], db=db)
        else:
            return f"[UNKNOWN TOOL] '{tool_name}' is not a registered Director tool."
    except KeyError as e:
        return f"[TOOL ERROR] Missing required parameter: {e}"
    except Exception as e:
        logger.exception("Tool dispatch error for '%s'", tool_name)
        return f"[TOOL ERROR] {tool_name} failed: {e}"
