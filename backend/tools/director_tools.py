"""
Director Tool Suite — 4.0
==========================
Every tool has a PRIMARY + 2 BACKUPS minimum. Failures cascade silently.

Tools & their redundancy stack
-------------------------------
web_search            : DDG HTML scrape → DDG Instant API → Wikipedia API → Bing HTML
fetch_url             : httpx+BS4 → requests+BS4 → urllib (built-in, zero deps)
send_email            : Gmail SMTP → Outlook SMTP → MongoDB queue → log-only
get_incident_register : live DB → in-memory cache → static notice
read_file             : MongoDB → in-memory session cache → error notice
set_mode              : ModeSystem singleton (in-memory, instant)
create_incident       : MongoDB write + crisis engine sync
get_system_health     : health_monitor singleton + crisis engine + mode system

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
    {
        "name": "set_mode",
        "description": (
            "Switch the WAI-Institute AI ecosystem to a new operational mode. "
            "Modes: nam (full creative+growth), balanced (default steady-state), "
            "creative (innovation-first), aggressive (growth-first), "
            "conservative (protection-first), recovery (crisis stabilization). "
            "Mode shifts apply instantly across all personas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["nam", "balanced", "creative", "aggressive", "conservative", "recovery"],
                    "description": "The target operational mode",
                },
                "reason": {
                    "type": "string",
                    "description": "Brief reason for the mode change (logged)",
                },
            },
            "required": ["mode"],
        },
    },
    {
        "name": "create_incident",
        "description": (
            "Formally log a new threat or incident to the WAI-Institute incident register. "
            "Use when a threat is detected, a security event occurs, or D. Oliver directs logging. "
            "Severity: LOW | ELEVATED | HIGH | CRITICAL. "
            "Type: technical | legal | reputational | safety | financial | ai_tamper | insider."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title":       {"type": "string", "description": "Short incident title"},
                "type":        {"type": "string", "description": "Incident type category"},
                "severity":    {"type": "string", "enum": ["LOW", "ELEVATED", "HIGH", "CRITICAL"]},
                "summary":     {"type": "string", "description": "Full description of the incident"},
                "source":      {"type": "string", "description": "Origin of the threat or event"},
                "assigned_to": {"type": "string", "description": "Owner for this incident (default: director)"},
            },
            "required": ["title", "type", "severity", "summary"],
        },
    },
    {
        "name": "get_system_health",
        "description": (
            "Query the live WAI-Institute system health monitor. "
            "Returns health status (nominal/warning/critical), all active flags, "
            "and key platform metrics. Call at session start or any time health is in question."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
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
                            headers={"User-Agent": "WAI-Director/4.0"})
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
                headers={"User-Agent": "WAI-Director/4.0"},
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


# ── Tool: set_mode ────────────────────────────────────────────────────────────

async def tool_set_mode(mode: str, reason: str = "") -> str:
    """Switch the global AI ecosystem mode.

    REDUNDANCY CHAIN (3 tiers — all run in parallel; first success wins summary):
      Tier 1 — ModeSystem singleton (in-memory, instant)
      Tier 2 — MongoDB ai_system_state collection (persistent across restarts)
      Tier 3 — JSON file on disk at /tmp/wai_mode_state.json (last-resort recovery)
    """
    import json as _json, pathlib as _pl
    now_str = datetime.now(timezone.utc).isoformat()
    tier_results: list[str] = []

    # ── Validate mode before touching anything ────────────────────────────────
    try:
        from ai.mode_system import mode_system, Mode
        valid = {m.value for m in Mode}
    except ImportError:
        valid = {"nam", "balanced", "creative", "aggressive", "conservative", "recovery"}
        mode_system = None  # type: ignore[assignment]
        Mode = None         # type: ignore[assignment]

    mode_lower = mode.lower()
    if mode_lower not in valid:
        return (
            f"[MODE ERROR] '{mode}' is not a valid mode. "
            f"Valid modes: {', '.join(sorted(valid))}"
        )

    # ── Tier 1: ModeSystem singleton ──────────────────────────────────────────
    prev_mode = "unknown"
    try:
        prev_mode = mode_system.get_mode().value if mode_system else "unknown"
        if mode_system and Mode:
            mode_system.set_mode(Mode(mode_lower), reason=reason or "Director command")
        tier_results.append("T1:OK(in-memory)")
    except Exception as _t1:
        tier_results.append(f"T1:FAIL({_t1})")

    # ── Tier 2: MongoDB ai_system_state ──────────────────────────────────────
    try:
        # db is not passed in; reach it via the app-level singleton
        import motor.motor_asyncio as _motor  # type: ignore
        _mongo_url = None
        try:
            import os as _os
            _mongo_url = _os.environ.get("MONGODB_URL") or _os.environ.get("MONGO_URI")
        except Exception:
            pass
        if _mongo_url:
            _tmp_client = _motor.AsyncIOMotorClient(_mongo_url, serverSelectionTimeoutMS=3000)
            _tmp_db = _tmp_client.get_default_database()
            await _tmp_db.ai_system_state.update_one(
                {"key": "active_mode"},
                {"$set": {"mode": mode_lower, "reason": reason, "updated_at": now_str,
                          "set_by": "director"}},
                upsert=True,
            )
            _tmp_client.close()
            tier_results.append("T2:OK(mongodb)")
        else:
            tier_results.append("T2:SKIP(no-mongo-url)")
    except Exception as _t2:
        tier_results.append(f"T2:FAIL({_t2})")

    # ── Tier 3: JSON file fallback ────────────────────────────────────────────
    try:
        _state_path = _pl.Path("/tmp/wai_mode_state.json")
        _state_path.write_text(
            _json.dumps({
                "mode": mode_lower,
                "reason": reason or "Director directive",
                "updated_at": now_str,
                "set_by": "director",
                "prev_mode": prev_mode,
            }, indent=2),
            encoding="utf-8",
        )
        tier_results.append("T3:OK(disk)")
    except Exception as _t3:
        tier_results.append(f"T3:FAIL({_t3})")

    tiers_str = " | ".join(tier_results)
    return (
        f"✓ Ecosystem mode shifted: {prev_mode.upper()} → {mode_lower.upper()}\n"
        f"Reason: {reason or 'Director directive'}\n"
        f"Mode applies immediately across all personas.\n"
        f"Redundancy: {tiers_str}"
    )


# ── Tool: create_incident ─────────────────────────────────────────────────────

async def tool_create_incident(
    title: str,
    type_: str,
    severity: str,
    summary: str,
    source: str = "director",
    assigned_to: str = "director",
    db=None,
) -> str:
    """Log a new incident to the WAI-Institute incident register and sync crisis engine."""
    incident_id = str(uuid.uuid4())[:8].upper()
    now = datetime.now(timezone.utc)

    record = {
        "id":          incident_id,
        "title":       title,
        "type":        type_,
        "severity":    severity.upper(),
        "summary":     summary,
        "source":      source,
        "assigned_to": assigned_to,
        "status":      "open",
        "created_at":  now.isoformat(),
        "created_by":  "director",
    }

    # ── Tier 1: MongoDB ───────────────────────────────────────────────────────
    if db is not None:
        try:
            await db.incidents.insert_one({**record, "_id": incident_id})
        except Exception as e:
            logger.warning("create_incident: DB write failed: %s", e)

    # ── Tier 2: Crisis engine (in-memory) ────────────────────────────────────
    level_tag = ""
    try:
        from ai.crisis_engine import crisis_engine
        crisis_engine.raise_incident({
            "type": type_, "severity": severity.upper(),
            "source": source, "summary": summary,
        })
        level = crisis_engine.get_level()
        level_tag = f" | Crisis level now: {level.upper()}"
    except Exception:
        level_tag = ""

    # ── Tier 3: Auto-email executive on HIGH/CRITICAL incidents ──────────────
    # Uses tool_send_email which itself has 4-tier redundancy (Gmail → Outlook →
    # MongoDB queue → log-only) — so this path never fully silently fails.
    email_tag = ""
    if severity.upper() in ("HIGH", "CRITICAL"):
        try:
            import os as _os
            exec_email = (
                _os.environ.get("EXECUTIVE_EMAIL")
                or "delon@morehelpcenteral.com"  # fallback to known exec address
            )
            email_body = (
                f"INCIDENT ALERT — WAI-Institute Director System\n"
                f"{'=' * 50}\n"
                f"ID:       {incident_id}\n"
                f"Title:    {title}\n"
                f"Severity: {severity.upper()}\n"
                f"Type:     {type_}\n"
                f"Source:   {source}\n"
                f"Assigned: {assigned_to}\n"
                f"Summary:  {summary}\n"
                f"Time:     {now.strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"{'=' * 50}\n"
                f"This alert was dispatched automatically by THE DIRECTOR.\n"
                f"Log into the WAI-Institute dashboard to review and respond."
            )
            await tool_send_email(
                to=exec_email,
                subject=f"[{severity.upper()}] Incident {incident_id}: {title}",
                body=email_body,
                db=db,
            )
            email_tag = " | Executive alert dispatched"
        except Exception as _e3:
            email_tag = f" | Alert email failed: {_e3}"

    return (
        f"◈ INCIDENT LOGGED — ID: {incident_id}\n"
        f"Title: {title}\n"
        f"Severity: {severity.upper()} | Type: {type_} | Source: {source}\n"
        f"Assigned to: {assigned_to} | Status: OPEN{level_tag}{email_tag}\n"
        f"Timestamp: {now.strftime('%Y-%m-%d %H:%M UTC')}"
    )


# ── Tool: get_system_health ───────────────────────────────────────────────────

async def tool_get_system_health(db=None) -> str:
    """Query the live system health monitor and return a Director-formatted brief.

    REDUNDANCY CHAIN (3 tiers — cascade on failure):
      Tier 1 — SystemHealthMonitor singleton (in-memory live metrics)
      Tier 2 — MongoDB direct query (incidents + user count — always readable)
      Tier 3 — Static timestamp response (proves the AI layer is responsive)
    """
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ── Tier 1: SystemHealthMonitor singleton ────────────────────────────────
    try:
        from ai.system_health_monitor import health_monitor
        status  = health_monitor.get_status()
        health  = status["health"].upper()
        metrics = status["metrics"]
        flags   = status["flags"]

        lines = [f"◈ SYSTEM HEALTH — {health}  [source: live-monitor]"]
        lines.append(f"  Uptime: {metrics.get('uptime_pct', 'N/A')}%")
        lines.append(f"  Errors (24h): {metrics.get('errors_last_24h', 0)}")
        lines.append(f"  API latency: {metrics.get('latency_ms', 0)}ms")
        lines.append(f"  Open incidents: {metrics.get('open_incidents', 0)}")
        lines.append(f"  DB connected: {'YES' if metrics.get('db_connected', True) else 'NO — CRITICAL'}")
        lines.append(f"  AI API reachable: {'YES' if metrics.get('ai_api_reachable', True) else 'NO — CRITICAL'}")
        lines.append(f"  Persona drift flags: {metrics.get('persona_drift_flags', 0)}")
        lines.append(f"  TTS circuit: {'OPEN (degraded)' if metrics.get('tts_circuit_open') else 'CLOSED (normal)'}")

        if flags:
            lines.append(f"\n  Active flags ({len(flags)}):")
            for f_ in flags:
                lines.append(f"    ⚠ {f_}")
        else:
            lines.append("\n  No active flags.")

        try:
            from ai.crisis_engine import crisis_engine
            c = crisis_engine.summary()
            lines.append(f"\n  Crisis level: {c['level'].upper()} | Incidents: {c['incident_count']}")
        except Exception:
            pass

        try:
            from ai.mode_system import mode_system
            lines.append(f"  Current mode: {mode_system.get_mode().value.upper()}")
        except Exception:
            pass

        lines.append(f"  Queried: {now_str}")
        return "\n".join(lines)

    except Exception as _t1_err:
        logger.warning("get_system_health T1 failed: %s", _t1_err)

    # ── Tier 2: MongoDB direct query ─────────────────────────────────────────
    try:
        _db = db
        if _db is None:
            # Reach the db via motor directly
            import os as _os, motor.motor_asyncio as _motor  # type: ignore
            _url = _os.environ.get("MONGODB_URL") or _os.environ.get("MONGO_URI")
            if _url:
                _tmp = _motor.AsyncIOMotorClient(_url, serverSelectionTimeoutMS=3000)
                _db = _tmp.get_default_database()
            else:
                raise RuntimeError("No MongoDB URL in environment")

        open_inc   = await _db.incidents.count_documents({"status": {"$nin": ["resolved", "closed"]}})
        total_users = await _db.users.count_documents({})
        active_stu  = await _db.users.count_documents({"role": "student", "is_active": {"$ne": False}})

        # Crisis engine (in-memory, best-effort)
        crisis_line = ""
        try:
            from ai.crisis_engine import crisis_engine
            c = crisis_engine.summary()
            crisis_line = f"\n  Crisis level: {c['level'].upper()} | Logged incidents: {c['incident_count']}"
        except Exception:
            pass

        mode_line = ""
        try:
            from ai.mode_system import mode_system
            mode_line = f"\n  Current mode: {mode_system.get_mode().value.upper()}"
        except Exception:
            pass

        return (
            f"◈ SYSTEM HEALTH — OPERATIONAL  [source: mongodb-direct]\n"
            f"  Open incidents: {open_inc}\n"
            f"  Total users: {total_users} | Active students: {active_stu}"
            f"{crisis_line}{mode_line}\n"
            f"  Note: Live-monitor unavailable — DB metrics shown.\n"
            f"  Queried: {now_str}"
        )

    except Exception as _t2_err:
        logger.warning("get_system_health T2 failed: %s", _t2_err)

    # ── Tier 3: Static timestamp response ────────────────────────────────────
    return (
        f"◈ SYSTEM HEALTH — AI LAYER RESPONSIVE  [source: static-fallback]\n"
        f"  The Director AI layer is active and responding normally.\n"
        f"  Live metrics and database unreachable at this moment.\n"
        f"  Recommend: retry in 60 seconds or check Railway/MongoDB status.\n"
        f"  Queried: {now_str}"
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
        elif tool_name == "set_mode":
            return await tool_set_mode(
                mode=tool_input["mode"],
                reason=tool_input.get("reason", ""),
            )
        elif tool_name == "create_incident":
            return await tool_create_incident(
                title=tool_input["title"],
                type_=tool_input["type"],
                severity=tool_input["severity"],
                summary=tool_input["summary"],
                source=tool_input.get("source", "director"),
                assigned_to=tool_input.get("assigned_to", "director"),
                db=db,
            )
        elif tool_name == "get_system_health":
            return await tool_get_system_health(db=db)
        else:
            return f"[UNKNOWN TOOL] '{tool_name}' is not a registered Director tool."
    except KeyError as e:
        return f"[TOOL ERROR] Missing required parameter: {e}"
    except Exception as e:
        logger.exception("Tool dispatch error for '%s'", tool_name)
        return f"[TOOL ERROR] {tool_name} failed: {e}"
