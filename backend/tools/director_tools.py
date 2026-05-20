"""
Director Tool Suite — v2
========================
Every tool has a PRIMARY + 2 BACKUPS minimum. Failures cascade silently.

Tools & their redundancy stack
-------------------------------
web_search     : DDG HTML scrape → DDG Instant API → Wikipedia API → Bing HTML
fetch_url      : httpx+BS4 → requests+BS4 → urllib (built-in, zero deps)
send_email     : Gmail SMTP → Outlook SMTP → MongoDB queue → log-only
get_incident_register : live DB → in-memory cache → static notice
read_file      : MongoDB → in-memory session cache → error notice

Zero paid APIs. Zero new external dependencies beyond httpx + beautifulsoup4.
"""
import asyncio
import html as _html
import logging
import os
import re
import smtplib
import socket
import urllib.request
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger(__name__)

# ── Environment ───────────────────────────────────────────────────────────────
GMAIL_USER          = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD  = os.environ.get("GMAIL_APP_PASSWORD", "")
OUTLOOK_USER        = os.environ.get("OUTLOOK_USER", "")
OUTLOOK_APP_PASSWORD= os.environ.get("OUTLOOK_APP_PASSWORD", "")
EXEC_EMAIL          = os.environ.get("EXEC_ADMIN_EMAIL", "delon.oliver@lightningcityelectric.com")

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_HEADERS = {"User-Agent": _UA, "Accept-Language": "en-US,en;q=0.9"}

# ── In-memory fallback caches ─────────────────────────────────────────────────
_INCIDENT_CACHE: dict = {"data": None, "ts": None}
_FILE_CACHE: dict[str, dict] = {}   # populated by upload endpoint


def cache_file(file_id: str, filename: str, content: str, content_type: str) -> None:
    """Called by the upload endpoint so read_file has a local fallback."""
    _FILE_CACHE[file_id] = {
        "filename": filename, "content": content,
        "content_type": content_type, "is_binary": False,
    }
    if len(_FILE_CACHE) > 100:
        oldest = next(iter(_FILE_CACHE))
        del _FILE_CACHE[oldest]


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
                    "description": "Max results (default 6, max 10)",
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
                    "description": "Full URL (must start with http:// or https://)",
                }
            },
            "required": ["url"],
        },
    },
    {
        "name": "send_email",
        "description": (
            "Send a branded WAI-Institute email. Use for executive briefs, alerts, "
            "task packages, or formal communication. Pass 'executive' as the "
            "recipient to send directly to D. Oliver."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email. Use 'executive' for D. Oliver.",
                },
                "subject": {"type": "string", "description": "Subject line"},
                "body": {"type": "string", "description": "Body text (markdown ok)"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "get_incident_register",
        "description": (
            "Pull WAI-Institute's live open incident register. "
            "Returns all unresolved incidents with severity, status, owner, age. "
            "Call on every status check, daily brief, or threat response."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "read_file",
        "description": (
            "Read content of a file uploaded by the executive in this session. "
            "Returns full text of documents, spreadsheets, code, or data files."
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


# ── Shared helpers ────────────────────────────────────────────────────────────

def _strip_html(raw: str, max_chars: int = 12_000) -> str:
    """Strip HTML tags and collapse whitespace. Works with or without bs4."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer",
                          "aside", "form", "noscript", "iframe", "svg"]):
            tag.decompose()
        body = soup.find("main") or soup.find("article") or soup.find("body") or soup
        text = body.get_text(separator="\n", strip=True)
    except ImportError:
        text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:max_chars]


def _build_email_html(body: str, ts: str) -> str:
    return (
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


# ── Tool: web_search ──────────────────────────────────────────────────────────
# Tier 1: DuckDuckGo HTML POST  (most complete, no key)
# Tier 2: DuckDuckGo Instant Answer API  (knowledge-graph, no key)
# Tier 3: Wikipedia Search API  (structured, no key)
# Tier 4: Bing HTML scrape  (broad coverage, no key)

async def tool_web_search(query: str, num_results: int = 6) -> str:
    num_results = max(1, min(int(num_results), 10))

    # ── Tier 1: DDG HTML ─────────────────────────────────────────────────────
    try:
        import httpx
        async with httpx.AsyncClient(timeout=12, follow_redirects=True, headers=_HEADERS) as c:
            r = await c.post("https://html.duckduckgo.com/html/",
                             data={"q": query, "kl": "us-en"})
            if r.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, "html.parser")
                results = []
                for el in soup.select(".result")[:num_results]:
                    title   = (el.select_one(".result__title") or el).get_text(strip=True)
                    snippet = (el.select_one(".result__snippet") or el).get_text(strip=True)
                    link    = el.select_one("a.result__url")
                    href    = link["href"] if link and link.get("href") else ""
                    if title:
                        results.append(f"**{title}**\n{href}\n{snippet}")
                if results:
                    return f"[DDG] Web search: '{query}'\n\n" + "\n\n".join(results)
    except Exception as e:
        logger.warning("web_search Tier1 (DDG HTML) failed: %s", e)

    # ── Tier 2: DDG Instant Answer API ───────────────────────────────────────
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get("https://api.duckduckgo.com/",
                            params={"q": query, "format": "json",
                                    "no_html": "1", "skip_disambig": "1"},
                            headers={"User-Agent": "WAI-Director/2.0"})
            data = r.json()
            results = []
            if data.get("Abstract"):
                results.append(f"SUMMARY: {data['Abstract']}\n{data.get('AbstractURL','')}")
            for t in data.get("RelatedTopics", [])[:num_results]:
                if isinstance(t, dict) and t.get("Text"):
                    results.append(f"- {t['Text']}\n  {t.get('FirstURL','')}")
            if results:
                return f"[DDG-API] Search: '{query}'\n\n" + "\n".join(results)
    except Exception as e:
        logger.warning("web_search Tier2 (DDG API) failed: %s", e)

    # ── Tier 3: Wikipedia Search API ─────────────────────────────────────────
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": query,
                        "format": "json", "srlimit": min(num_results, 5)},
                headers={"User-Agent": "WAI-Director/2.0"},
            )
            items = r.json().get("query", {}).get("search", [])
            results = []
            for item in items:
                title   = item.get("title", "")
                snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
                url     = f"https://en.wikipedia.org/wiki/{title.replace(' ','_')}"
                results.append(f"**{title}** (Wikipedia)\n{url}\n{snippet}")
            if results:
                return f"[Wikipedia] Search: '{query}'\n\n" + "\n\n".join(results)
    except Exception as e:
        logger.warning("web_search Tier3 (Wikipedia) failed: %s", e)

    # ── Tier 4: Bing HTML scrape ──────────────────────────────────────────────
    try:
        import httpx
        from bs4 import BeautifulSoup
        async with httpx.AsyncClient(timeout=12, follow_redirects=True, headers=_HEADERS) as c:
            r = await c.get(f"https://www.bing.com/search?q={query}&count={num_results}")
            soup = BeautifulSoup(r.text, "html.parser")
            results = []
            for el in soup.select(".b_algo")[:num_results]:
                title   = (el.select_one("h2") or el).get_text(strip=True)
                snippet = (el.select_one(".b_caption p") or el).get_text(strip=True)
                link    = el.select_one("a")
                href    = link.get("href", "") if link else ""
                if title:
                    results.append(f"**{title}**\n{href}\n{snippet}")
            if results:
                return f"[Bing] Search: '{query}'\n\n" + "\n\n".join(results)
    except Exception as e:
        logger.warning("web_search Tier4 (Bing) failed: %s", e)

    return (
        f"[SEARCH NOTICE] All four search providers unavailable for '{query}'. "
        "The Director is proceeding with institutional knowledge. "
        "Live verification recommended when connectivity is restored."
    )


# ── Tool: fetch_url ───────────────────────────────────────────────────────────
# Tier 1: httpx async + BeautifulSoup4
# Tier 2: requests (sync, executor) + BeautifulSoup4
# Tier 3: urllib.request (built-in, zero extra deps)

async def tool_fetch_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return f"[ERROR] Invalid URL — must start with http:// or https://"

    # Director 4.0 — SSRF protection: block private IPs and metadata endpoints
    try:
        from ai.prompt_guard import check_url_safe
        ssrf_check = check_url_safe(url)
        if not ssrf_check["safe"]:
            return f"[SECURITY BLOCK] {ssrf_check['reason']} — URL: {url[:100]}"
    except ImportError:
        pass  # Guard not loaded; proceed with basic check only

    MAX = 12_000

    # ── Tier 1: httpx ────────────────────────────────────────────────────────
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=_HEADERS) as c:
            r = await c.get(url)
            ct = r.headers.get("content-type", "")
            if "text/plain" in ct or "application/json" in ct:
                return f"[{url}]\n\n{r.text[:MAX]}"
            return f"[{url}]\n\n{_strip_html(r.text, MAX)}"
    except Exception as e:
        logger.warning("fetch_url Tier1 (httpx) failed for %s: %s", url, e)

    # ── Tier 2: requests (sync executor) ─────────────────────────────────────
    try:
        import requests as _req
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None,
            lambda: _req.get(url, timeout=12, headers={"User-Agent": _UA}).text,
        )
        return f"[{url}]\n\n{_strip_html(raw, MAX)}"
    except Exception as e:
        logger.warning("fetch_url Tier2 (requests) failed for %s: %s", url, e)

    # ── Tier 3: urllib (zero deps, always available) ──────────────────────────
    try:
        loop = asyncio.get_event_loop()
        def _urllib_fetch():
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=12) as resp:
                return resp.read().decode("utf-8", errors="replace")
        raw = await loop.run_in_executor(None, _urllib_fetch)
        return f"[{url}]\n\n{_strip_html(raw, MAX)}"
    except Exception as e:
        logger.warning("fetch_url Tier3 (urllib) failed for %s: %s", url, e)

    return f"[FETCH FAILED] All three fetch methods failed for {url}. Page may be protected or offline."


# ── Tool: send_email ──────────────────────────────────────────────────────────
# Tier 1: Gmail SMTP SSL (port 465)
# Tier 2: Outlook/Hotmail SMTP TLS (port 587)
# Tier 3: MongoDB email_queue (admin panel view + retry)
# Tier 4: log-only (nothing sent, full details preserved in logs)

_EXEC_ALIASES = {"executive", "exec", "d. oliver", "d.oliver", "delon",
                 "director", "nam oshun", "namoshun"}

async def tool_send_email(to: str, subject: str, body: str, db=None) -> str:
    if to.strip().lower() in _EXEC_ALIASES:
        to = EXEC_EMAIL

    ts           = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    full_subject = f"[WAI-Institute] {subject}"
    html_body    = _build_email_html(body, ts)

    def _build_msg(from_addr: str) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = full_subject
        msg["From"]    = f"WAI-Institute Director <{from_addr}>"
        msg["To"]      = to
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        return msg

    # ── Tier 1: Gmail SMTP (SSL 465) ─────────────────────────────────────────
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        try:
            msg  = _build_msg(GMAIL_USER)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: _send_gmail(msg))
            return f"✓ Email delivered via Gmail to {to}\nSubject: {full_subject}"
        except smtplib.SMTPAuthenticationError:
            logger.error("Gmail SMTP auth failed — check GMAIL_USER/GMAIL_APP_PASSWORD")
        except Exception as e:
            logger.warning("Gmail SMTP failed: %s", e)

    # ── Tier 2: Outlook SMTP (TLS 587) ───────────────────────────────────────
    if OUTLOOK_USER and OUTLOOK_APP_PASSWORD:
        try:
            msg  = _build_msg(OUTLOOK_USER)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: _send_outlook(msg))
            return f"✓ Email delivered via Outlook to {to}\nSubject: {full_subject}"
        except smtplib.SMTPAuthenticationError:
            logger.error("Outlook SMTP auth failed — check OUTLOOK_USER/OUTLOOK_APP_PASSWORD")
        except Exception as e:
            logger.warning("Outlook SMTP failed: %s", e)

    # ── Tier 3: MongoDB queue ─────────────────────────────────────────────────
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
                f"⚠ SMTP offline — email queued in database.\n"
                f"To: {to} | Subject: {full_subject}\n"
                "Configure GMAIL_USER + GMAIL_APP_PASSWORD or OUTLOOK_USER + OUTLOOK_APP_PASSWORD "
                "in Railway environment variables to enable live delivery."
            )
        except Exception as e:
            logger.error("Email queue insert failed: %s", e)

    # ── Tier 4: log-only ──────────────────────────────────────────────────────
    logger.info("EMAIL NOT SENT: to=%s | subject=%s | body=%s", to, subject, body[:200])
    return (
        f"[EMAIL LOGGED ONLY]\nTo: {to} | Subject: {full_subject}\n"
        "All three delivery methods unavailable. "
        "Add GMAIL_USER + GMAIL_APP_PASSWORD to Railway env vars to enable sending."
    )


def _send_gmail(msg: MIMEMultipart) -> None:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as s:
        s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        s.send_message(msg)


def _send_outlook(msg: MIMEMultipart) -> None:
    with smtplib.SMTP("smtp-mail.outlook.com", 587, timeout=15) as s:
        s.ehlo()
        s.starttls()
        s.login(OUTLOOK_USER, OUTLOOK_APP_PASSWORD)
        s.send_message(msg)


# ── Tool: get_incident_register ───────────────────────────────────────────────
# Tier 1: Live MongoDB query
# Tier 2: In-memory cache (survives brief DB hiccups)
# Tier 3: Static notice

async def tool_get_incident_register(db) -> str:
    # ── Tier 1: live DB ───────────────────────────────────────────────────────
    try:
        now = datetime.now(timezone.utc)
        incidents = await db.incidents.find(
            {"status": {"$nin": ["resolved", "closed"]}},
            {"_id": 0, "id": 1, "title": 1, "severity": 1,
             "status": 1, "created_at": 1, "assigned_to": 1},
        ).sort("created_at", -1).limit(20).to_list(20)

        if not incidents:
            result = "◈ INCIDENT REGISTER — ALL CLEAR\nNo open incidents. System nominal."
        else:
            lines = [f"◈ INCIDENT REGISTER — {len(incidents)} OPEN\n"]
            for inc in incidents:
                sev    = (inc.get("severity") or "unknown").upper()
                status = inc.get("status", "open")
                title  = inc.get("title", "Untitled")
                owner  = inc.get("assigned_to") or "Unassigned"
                stale  = ""
                try:
                    dt    = datetime.fromisoformat(inc.get("created_at","").replace("Z","+00:00"))
                    age_h = (now - dt).total_seconds() / 3600
                    if age_h > 72:
                        stale = f" ⚠ STALE ({int(age_h)}h)"
                except Exception:
                    pass
                lines.append(f"[{sev}] {title}\n  Status: {status} | Owner: {owner}{stale}")
            result = "\n".join(lines)

        # Update cache on success
        _INCIDENT_CACHE["data"] = result
        _INCIDENT_CACHE["ts"]   = datetime.now(timezone.utc)
        return result

    except Exception as e:
        logger.error("Incident register live query failed: %s", e)

    # ── Tier 2: in-memory cache ───────────────────────────────────────────────
    if _INCIDENT_CACHE["data"]:
        age_min = int((datetime.now(timezone.utc) - _INCIDENT_CACHE["ts"]).total_seconds() / 60)
        return f"[CACHED — {age_min}m ago — DB temporarily unavailable]\n{_INCIDENT_CACHE['data']}"

    # ── Tier 3: static notice ─────────────────────────────────────────────────
    return "[INCIDENT REGISTER UNAVAILABLE] Database is offline and no cache exists. Check MongoDB connection."


# ── Tool: read_file ───────────────────────────────────────────────────────────
# Tier 1: MongoDB director_uploads collection
# Tier 2: in-memory _FILE_CACHE (populated at upload time)
# Tier 3: descriptive error notice

async def tool_read_file(file_id: str, db) -> str:
    # ── Tier 1: MongoDB ───────────────────────────────────────────────────────
    try:
        doc = await db.director_uploads.find_one({"id": file_id}, {"_id": 0})
        if doc:
            if doc.get("is_binary"):
                return (f"[BINARY FILE] '{doc.get('filename')}' is binary "
                        f"({doc.get('content_type')}) — cannot read as text.")
            return f"[FILE: {doc.get('filename','unknown')}]\n\n{doc.get('content','')}"
    except Exception as e:
        logger.warning("read_file Tier1 (MongoDB) failed for %s: %s", file_id, e)

    # ── Tier 2: in-memory cache ───────────────────────────────────────────────
    cached = _FILE_CACHE.get(file_id)
    if cached:
        if cached.get("is_binary"):
            return f"[BINARY FILE] '{cached['filename']}' cannot be read as text."
        return f"[FILE (cached): {cached['filename']}]\n\n{cached['content']}"

    # ── Tier 3: error notice ──────────────────────────────────────────────────
    return (
        f"[FILE NOT FOUND] No file with id '{file_id}'. "
        "It may have expired (24h TTL) or the upload may not have completed."
    )


# ── Tool dispatcher ───────────────────────────────────────────────────────────

async def dispatch_tool(tool_name: str, tool_input: dict, db=None) -> str:
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
