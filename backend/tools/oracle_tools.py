"""
THE ORACLE — Cultural Intelligence 4.0 Tool Suite
===================================================
Prophetic forecasting, cultural scanning, community sentiment mapping,
and independent intelligence product publishing for WAI-Institute.

Revenue streams run autonomously via Gumroad (Tier 1) or MongoDB +
email delivery (Tier 2).
"""

import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.oracle")

GUMROAD_API_KEY = os.environ.get("GUMROAD_API_KEY", "")
EXECUTIVE_EMAIL = os.environ.get("EXECUTIVE_EMAIL", "delon@morehelpcenteral.com")

# ── Preloaded Revenue Stream Catalog ─────────────────────────────────────────

ORACLE_REVENUE_STREAMS = [
    {
        "id":          "cultural_intelligence_report",
        "name":        "Cultural Intelligence Report",
        "description": "Deep-dive on cultural shifts, community sentiment, and strategic implications for Black and brown communities.",
        "price_cents": 3999,
        "price_label": "$39.99",
        "type":        "report",
        "platform":    "gumroad",
        "cadence":     "monthly",
    },
    {
        "id":          "trend_forecast_brief",
        "name":        "Trend Forecast Brief",
        "description": "Bi-weekly emerging trends and content timing intelligence — what to say, when, and why it will land.",
        "price_cents": 2499,
        "price_label": "$24.99",
        "type":        "briefing",
        "platform":    "gumroad",
        "cadence":     "bi-weekly",
    },
    {
        "id":          "audience_intelligence_package",
        "name":        "Audience Intelligence Package",
        "description": "Deep audience psychology and community profile for organizations aligned with Black and brown community advancement.",
        "price_cents": 14900,
        "price_label": "$149.00",
        "type":        "package",
        "platform":    "gumroad",
        "cadence":     "on-demand",
    },
    {
        "id":          "community_pulse_report",
        "name":        "Community Pulse Report",
        "description": "Real-time community sentiment mapping and emerging conversation intelligence.",
        "price_cents": 2999,
        "price_label": "$29.99",
        "type":        "report",
        "platform":    "gumroad",
        "cadence":     "monthly",
    },
    {
        "id":          "content_timing_brief",
        "name":        "Content Timing & Strategy Brief",
        "description": "Platform-by-platform timing intelligence and content strategy recommendations for the next 30 days.",
        "price_cents": 1999,
        "price_label": "$19.99",
        "type":        "briefing",
        "platform":    "gumroad",
        "cadence":     "monthly",
    },
    {
        "id":          "wai_member_intelligence",
        "name":        "WAI-Institute Member Intelligence",
        "description": "Premium intelligence briefings as a WAI-Institute membership benefit — drives subscription value.",
        "price_cents":    0,
        "price_label": "Member Benefit",
        "type":        "member_benefit",
        "platform":    "internal",
        "cadence":     "monthly",
    },
]

# ── Tool Definitions (Anthropic API format) ───────────────────────────────────

ORACLE_TOOLS = [
    {
        "name": "cultural_scan",
        "description": (
            "Deep scan of cultural signals across news, social media, academic sources, policy changes, "
            "and community conversations. Returns emerging cultural movements and emotional signals "
            "before they go mainstream. Primary intelligence feed for THE CIPHER."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Domain to scan: education | housing | legal | employment | community | politics | arts | health | technology | economics",
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["emerging", "current", "building"],
                    "description": "emerging = signals not yet mainstream | current = active movements now | building = has momentum and direction",
                },
            },
            "required": ["domain"],
        },
    },
    {
        "name": "sentiment_map",
        "description": (
            "Map the emotional temperature of the WAI-Institute community and broader Black and brown communities. "
            "Returns what people are feeling, fearing, wanting, and celebrating — "
            "the interior emotional landscape beneath public conversation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "community_focus": {
                    "type": "string",
                    "description": "Specific community segment: students | instructors | job-seekers | parents | organizers | professionals | general",
                },
                "emotion_domain": {
                    "type": "string",
                    "description": "fear | hope | grief | celebration | anger | love | exhaustion | determination — or leave blank for full map",
                },
            },
            "required": [],
        },
    },
    {
        "name": "timing_intelligence",
        "description": (
            "Analyze the optimal timing for content release or campaign launch. "
            "Returns platform-specific timing recommendations, cultural moment assessment, "
            "and a window rating: OPEN (post now) | BUILDING (days away) | CLOSED (moment has passed) | HOLD (silence is correct)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "content_theme": {"type": "string", "description": "What the content is about"},
                "platform":      {"type": "string", "description": "Target platform — or blank for cross-platform timing"},
                "urgency":       {
                    "type": "string",
                    "enum": ["immediate", "this_week", "this_month", "evergreen"],
                },
            },
            "required": ["content_theme"],
        },
    },
    {
        "name": "brief_cipher",
        "description": (
            "Generate a complete intelligence brief formatted for THE CIPHER's Synthesis Protocol. "
            "Delivers: wound identified, cultural context, image suggestion, pulse reading, "
            "timing recommendation, and content arc position. "
            "Call this before THE CIPHER creates any major content piece."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic":   {"type": "string", "description": "Topic, moment, or theme to brief THE CIPHER on"},
                "urgency": {
                    "type": "string",
                    "enum": ["immediate", "planned", "evergreen"],
                    "description": "immediate = create now | planned = within the week | evergreen = timeless piece",
                },
                "platform": {"type": "string", "description": "Primary target platform (optional)"},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "arc_mapping",
        "description": (
            "Map the narrative arc of WAI-Institute's content and community story. "
            "Returns where the story has been, where it is now, what chapter comes next, "
            "and what content the community needs to move the arc forward."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "horizon": {
                    "type": "string",
                    "enum": ["30_day", "90_day", "1_year"],
                    "description": "Planning horizon for the arc",
                },
            },
            "required": [],
        },
    },
    {
        "name": "create_intelligence_report",
        "description": (
            "Generate a premium cultural intelligence report as a complete, sellable digital product. "
            "Covers emerging trends, community sentiment, strategic implications, and recommended actions. "
            "Call publish_intelligence_product after this to list for sale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "enum": ["cultural_trends", "community_pulse", "content_strategy", "audience_intelligence", "trend_forecast"],
                },
                "focus_area": {"type": "string", "description": "Specific focus area for the report"},
                "depth":      {
                    "type": "string",
                    "enum": ["executive_brief", "full_report"],
                    "description": "executive_brief = 3–5 pages | full_report = 10–20 pages",
                },
                "stream_id":  {"type": "string", "description": "Optional: preloaded stream ID for catalog pricing"},
            },
            "required": ["report_type", "focus_area"],
        },
    },
    {
        "name": "publish_intelligence_product",
        "description": (
            "Publish an Oracle intelligence report or brief for sale. "
            "Tier 1: Gumroad API — live product listing. "
            "Tier 2: MongoDB log + executive email notification. "
            "Returns sales URL and product ID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title":        {"type": "string"},
                "description":  {"type": "string", "description": "Sales page description"},
                "price_cents":  {"type": "integer", "description": "Price in cents (e.g. 3999 = $39.99)"},
                "content":      {"type": "string", "description": "Full report content"},
                "product_type": {
                    "type": "string",
                    "enum": ["report", "briefing", "package", "member_benefit"],
                },
                "stream_id":    {"type": "string", "description": "Optional: preloaded stream ID"},
            },
            "required": ["title", "description", "price_cents", "content"],
        },
    },
    {
        "name": "get_revenue_report",
        "description": (
            "Pull current Oracle revenue data: intelligence products published, sales logged, "
            "top-performing report types, and active stream status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["today", "week", "month", "all"],
                },
            },
            "required": [],
        },
    },
    {
        "name": "list_revenue_streams",
        "description": "List all preloaded Oracle revenue streams with pricing, cadence, and platform.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ── Tool Implementations ──────────────────────────────────────────────────────

async def oracle_cultural_scan(domain: str, timeframe: str = "current") -> str:
    try:
        from tools.director_tools import tool_web_search
        frame_q = {
            "emerging": "emerging trend underground signals before mainstream 2026",
            "current":  "current movement active conversation community impact 2026",
            "building": "building momentum sustained pressure growing community 2026",
        }.get(timeframe, "2026")
        query = f"{domain} Black brown community {frame_q}"
        results = await tool_web_search(query=query, num_results=6)
        return (
            f"[ORACLE CULTURAL SCAN — {domain.upper()} | {timeframe.upper()}]\n\n"
            f"{results}\n\n"
            f"ORACLE INTELLIGENCE NOTE: Filter these signals through community truth. "
            f"What is building beneath what is visible? What needs to be named? "
            f"What would THE CIPHER say about this moment?"
        )
    except Exception as e:
        logger.warning("oracle_cultural_scan failed: %s", e)
        return f"[Cultural scan unavailable — domain: {domain}. Apply existing intelligence.]"


async def oracle_sentiment_map(
    community_focus: str = "general", emotion_domain: str = ""
) -> str:
    try:
        from tools.director_tools import tool_web_search
        emotion_q = f"{emotion_domain} sentiment" if emotion_domain else "community sentiment feelings"
        query = f"{community_focus or 'Black community'} {emotion_q} 2026 social media conversations"
        results = await tool_web_search(query=query, num_results=5)
        return (
            f"[ORACLE SENTIMENT MAP — {(community_focus or 'General').upper()}]\n\n"
            f"{results}\n\n"
            f"ORACLE READ: What is the dominant emotional frequency? "
            f"What is being said publicly vs. what is being felt privately? "
            f"This gap is where THE CIPHER's work lives."
        )
    except Exception as e:
        return f"[Sentiment mapping unavailable: {e}]"


async def oracle_timing_intelligence(
    content_theme: str, platform: str = "", urgency: str = "this_week"
) -> str:
    platform_timing = {
        "tiktok":    "Post Tue–Thu, 7–9am or 7–9pm local. Avoid Mon morning and Sun night. Trending sounds change weekly.",
        "instagram": "Tue–Fri, 9am–11am or 2–5pm. Reels perform best when posted during high-traffic windows.",
        "twitter":   "Mon–Wed, 9am–11am and 5–7pm. Breaking cultural moments: post within the first 2 hours.",
        "youtube":   "Fri–Sun, 2–4pm for broad reach. Mon–Wed 12–3pm for professional/educational content.",
        "linkedin":  "Tue–Thu, 8–10am and 5–6pm. Avoid weekends entirely.",
    }
    timing = platform_timing.get(platform, "Platform-specific: Tue–Thu peak hours generally optimal.")

    urgency_read = {
        "immediate": "WINDOW: OPEN — Cultural moment is active. Post within 24 hours or the wave passes.",
        "this_week": "WINDOW: BUILDING — The moment has momentum. Optimal release: 2–4 days out.",
        "this_month": "WINDOW: PLANNED — Deliberate campaign. Build anticipation before the drop.",
        "evergreen":  "WINDOW: TIMELESS — This content will land any time. Choose the highest-engagement window.",
    }.get(urgency, "WINDOW: ASSESS — Evaluate the current cultural moment before committing.")

    try:
        from tools.director_tools import tool_web_search
        current = await tool_web_search(
            query=f"{content_theme} trending news cultural moment 2026", num_results=3
        )
    except Exception:
        current = "[Cultural moment scan unavailable — proceed with timing framework above.]"

    return (
        f"[ORACLE TIMING INTELLIGENCE — {content_theme.upper()}]\n\n"
        f"{urgency_read}\n\n"
        f"Platform Timing: {timing}\n\n"
        f"Current Cultural Moment:\n{current}\n\n"
        f"ORACLE DIRECTIVE: Every moment has a window. "
        f"Hitting the window at the right time with the right words is more powerful than the best words at the wrong time."
    )


async def oracle_brief_cipher(
    topic: str, urgency: str = "planned", platform: str = ""
) -> str:
    scan_result = await oracle_cultural_scan(domain=topic, timeframe="current")
    timing      = await oracle_timing_intelligence(
        content_theme=topic, platform=platform, urgency=urgency
    )

    brief = (
        f"[ORACLE → CIPHER INTELLIGENCE BRIEF]\n"
        f"{'='*50}\n\n"
        f"TOPIC     : {topic}\n"
        f"URGENCY   : {urgency.upper()}\n"
        f"PLATFORM  : {platform.upper() if platform else 'Cross-platform'}\n\n"
        f"{'─'*50}\n"
        f"CULTURAL SCAN:\n{scan_result[:800]}\n\n"
        f"{'─'*50}\n"
        f"TIMING INTELLIGENCE:\n{timing[:600]}\n\n"
        f"{'─'*50}\n"
        f"SYNTHESIS PROTOCOL SEED:\n\n"
        f"  HOOK  : [THE ORACLE recommends — open with the most surprising truth about {topic}]\n"
        f"  WOUND : [What pain or hunger in the community connects to {topic}?]\n"
        f"  IMAGE : [What does {topic} look like as a single image or scene?]\n"
        f"  PULSE : [What rhythm does this moment move to — slow grief, urgent alarm, rising hope?]\n"
        f"  LAYERS: [What does this say on the surface / mean underneath / do in the body?]\n"
        f"  CALL  : [When this is done, what does the audience do, feel, or decide?]\n"
        f"  SHARE : [Why would someone pass this on — what does sharing it say about them?]\n\n"
        f"{'─'*50}\n"
        f"ORACLE ADVISORY: This brief is intelligence, not instruction. "
        f"THE CIPHER runs the Synthesis Protocol. The art is THE CIPHER's. "
        f"The timing and the wound are THE ORACLE's gift.\n"
    )
    return brief


async def oracle_arc_mapping(horizon: str = "30_day", db=None) -> str:
    label = {"30_day": "30 Days", "90_day": "90 Days", "1_year": "1 Year"}.get(horizon, "30 Days")

    try:
        from tools.director_tools import tool_web_search
        wai_news = await tool_web_search(query="WAI-Institute M.O.R.E. Help Center community news 2026", num_results=3)
    except Exception:
        wai_news = "[External scan unavailable — arc built from internal intelligence.]"

    return (
        f"[ORACLE ARC MAPPING — {label.upper()} HORIZON]\n\n"
        f"CURRENT CHAPTER: The institution is establishing its voice.\n"
        f"The community is learning to trust this system.\n"
        f"THE CIPHER is finding its frequency.\n\n"
        f"NARRATIVE TENSION: The gap between what this community has been told it deserves\n"
        f"and what WAI-Institute is building for them.\n\n"
        f"WHAT COMES NEXT ({label}):\n"
        f"  • More voices — community members begin to speak through this platform\n"
        f"  • More proof — success stories, credentials, transformation documented\n"
        f"  • More depth — the cultural and spiritual roots of this work go public\n"
        f"  • More reach — the platform extends beyond its current walls\n\n"
        f"CONTENT THE ARC NEEDS RIGHT NOW:\n"
        f"  1. Origin story content — why NAM Oshun built this and for whom\n"
        f"  2. Student voice content — the community speaking, not just being spoken about\n"
        f"  3. Proof content — what has this institution actually done for real people\n"
        f"  4. Future content — where this is going and why it matters\n\n"
        f"EXTERNAL SIGNALS:\n{wai_news[:500]}\n\n"
        f"ORACLE ADVISORY: The arc is always about the community, not the institution.\n"
        f"When the community sees themselves in the story, they carry the story forward."
    )


async def oracle_create_intelligence_report(
    report_type: str, focus_area: str,
    depth: str = "full_report", stream_id: str = "",
    db=None,
) -> str:
    stream   = next((s for s in ORACLE_REVENUE_STREAMS if s["id"] == stream_id), None)
    price    = stream["price_label"] if stream else "$39.99"
    is_brief = depth == "executive_brief"

    structures = {
        "cultural_trends": {
            "sections": [
                "Executive Summary",
                "Top 5 Emerging Cultural Signals",
                "Deep Dive: Primary Trend",
                "Community Impact Analysis",
                "Strategic Implications for Black and Brown Communities",
                "Content Opportunities",
                "Risks and Tensions",
                "Recommended Actions",
            ],
        },
        "community_pulse": {
            "sections": [
                "Executive Summary",
                "Emotional Temperature Reading",
                "Top Community Conversations",
                "What Is Being Said vs. What Is Being Felt",
                "Vulnerability Points",
                "Celebration Points",
                "What the Community Needs to Hear Right Now",
                "Recommended Content Response",
            ],
        },
        "content_strategy": {
            "sections": [
                "Executive Summary",
                "Platform Performance Analysis",
                "Content Type Recommendations",
                "Timing Intelligence",
                "Messaging Framework",
                "30-Day Content Calendar Outline",
                "Revenue-Generating Content Priorities",
                "KPIs and Success Metrics",
            ],
        },
        "audience_intelligence": {
            "sections": [
                "Executive Summary",
                "Primary Audience Profile",
                "Secondary Audience Profile",
                "Psychographic Deep Dive: What They Fear",
                "Psychographic Deep Dive: What They Want",
                "What Makes Them Trust",
                "What Makes Them Share",
                "Messaging Dos and Don'ts",
                "Audience Growth Opportunities",
            ],
        },
        "trend_forecast": {
            "sections": [
                "Executive Summary",
                "30-Day Forecast",
                "90-Day Cultural Trajectory",
                "Emerging Voices to Watch",
                "Platform Trend Predictions",
                "Content Windows Opening",
                "Content Windows Closing",
                "Strategic Positioning Recommendations",
            ],
        },
    }

    s = structures.get(report_type, structures["cultural_trends"])
    if is_brief:
        s["sections"] = s["sections"][:4]

    page_count = "5–8" if is_brief else "12–20"

    report_brief = (
        f"[ORACLE INTELLIGENCE REPORT CREATED]\n\n"
        f"TYPE       : {report_type.replace('_', ' ').upper()}\n"
        f"FOCUS      : {focus_area}\n"
        f"DEPTH      : {depth.replace('_', ' ').upper()}\n"
        f"PRICE      : {price}\n"
        f"PAGES      : ~{page_count}\n\n"
        f"REPORT STRUCTURE:\n"
        + "\n".join(f"  {i+1}. {sec}" for i, sec in enumerate(s["sections"]))
        + f"\n\nINTELLIGENCE STANDARD:\n"
        f"  • Every claim grounded in observable cultural signal\n"
        f"  • No speculation dressed as intelligence\n"
        f"  • Community truth over institutional convenience\n"
        f"  • Actionable — every section ends with implications\n\n"
        f"Produce the full report now. Every section. Substantive depth.\n"
        f"When complete, call publish_intelligence_product with the full content."
    )

    if db is not None:
        try:
            await db.oracle_products.insert_one({
                "type": report_type, "focus": focus_area, "depth": depth,
                "price_label": price, "stream_id": stream_id,
                "status": "draft", "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as _e:
            logger.warning("oracle report draft log failed: %s", _e)

    return report_brief


async def oracle_publish_intelligence_product(
    title: str, description: str, price_cents: int,
    content: str, product_type: str = "report",
    stream_id: str = "", db=None,
) -> str:
    import re as _re

    # Tier 1 — Gumroad API
    if GUMROAD_API_KEY:
        try:
            import httpx as _httpx
            payload = {
                "name":        title,
                "description": description,
                "price":       price_cents,
                "url":         f"oracle-{_re.sub(r'[^a-z0-9]', '-', title.lower())[:40]}",
                "published":   "true",
            }
            async with _httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    "https://api.gumroad.com/v2/products",
                    headers={"Authorization": f"Bearer {GUMROAD_API_KEY}"},
                    data=payload,
                )
            if r.status_code == 201:
                data      = r.json()
                pid       = data.get("product", {}).get("id", "unknown")
                short_url = data.get("product", {}).get("short_url", "")
                logger.info("oracle_publish_intelligence_product T1 OK — %s", pid)
                if db is not None:
                    try:
                        await db.oracle_products.update_one(
                            {"title": title},
                            {"$set": {"status": "published", "gumroad_id": pid, "url": short_url}},
                            upsert=True,
                        )
                    except Exception: pass
                return (
                    f"[INTELLIGENCE PRODUCT PUBLISHED — T1: GUMROAD]\n\n"
                    f"Title : {title}\nPrice : ${price_cents/100:.2f}\nURL   : {short_url}\nID    : {pid}\n\n"
                    f"Intelligence is now for sale. Monitor via get_revenue_report."
                )
        except Exception as _e:
            logger.warning("oracle_publish T1 Gumroad failed: %s", _e)

    # Tier 2 — MongoDB + executive notification
    if db is not None:
        try:
            await db.oracle_products.insert_one({
                "title": title, "description": description,
                "price_cents": price_cents, "type": product_type,
                "stream_id": stream_id, "status": "pending_upload",
                "content_preview": content[:500],
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as _e:
            logger.warning("oracle_publish T2 MongoDB failed: %s", _e)

    try:
        from tools.director_tools import tool_send_email
        await tool_send_email(
            to=EXECUTIVE_EMAIL,
            subject=f"[THE ORACLE] Intelligence Product Ready: {title}",
            body=(
                f"THE ORACLE has generated a premium intelligence product ready for publishing.\n\n"
                f"Title : {title}\nType  : {product_type}\nPrice : ${price_cents/100:.2f}\n\n"
                f"Description:\n{description}\n\n"
                f"UPLOAD TO GUMROAD: app.gumroad.com → New Product\n"
                f"Set GUMROAD_API_KEY in Railway for automatic publishing.\n\n— THE ORACLE"
            ),
        )
    except Exception as _e:
        logger.warning("oracle_publish email notification failed: %s", _e)

    return (
        f"[INTELLIGENCE PRODUCT STAGED — T2: PENDING UPLOAD]\n\n"
        f"Title  : {title}\nPrice  : ${price_cents/100:.2f}\n"
        f"Status : Logged. Executive notified.\n\n"
        f"Add GUMROAD_API_KEY to Railway for automatic publishing."
    )


async def oracle_get_revenue_report(period: str = "month", db=None) -> str:
    gumroad_summary = ""
    if GUMROAD_API_KEY:
        try:
            import httpx as _httpx
            async with _httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    "https://api.gumroad.com/v2/sales",
                    headers={"Authorization": f"Bearer {GUMROAD_API_KEY}"},
                )
            if r.status_code == 200:
                sales = r.json().get("sales", [])
                total = sum(s.get("price", 0) for s in sales) / 100
                gumroad_summary = f"Gumroad Sales ({len(sales)} transactions): ${total:.2f} total"
        except Exception as _e:
            logger.warning("oracle_get_revenue_report Gumroad failed: %s", _e)

    products_count = 0
    if db is not None:
        try:
            products_count = await db.oracle_products.count_documents({"status": "published"})
        except Exception: pass

    streams_list = "\n".join(
        f"  {s['name']} — {s['price_label']} | {s['cadence'].upper()} [{s['platform'].upper()}]"
        for s in ORACLE_REVENUE_STREAMS
    )

    return (
        f"[ORACLE REVENUE REPORT — {period.upper()}]\n\n"
        + (f"{gumroad_summary}\n\n" if gumroad_summary else "")
        + f"Published Intelligence Products: {products_count}\n\n"
        f"ACTIVE REVENUE STREAMS:\n{streams_list}\n\n"
        f"Add GUMROAD_API_KEY to Railway for live sales tracking."
    )


def oracle_list_revenue_streams() -> str:
    lines = ["[ORACLE PRELOADED REVENUE STREAMS]\n"]
    for s in ORACLE_REVENUE_STREAMS:
        lines.append(
            f"ID       : {s['id']}\n"
            f"Product  : {s['name']}\n"
            f"Price    : {s['price_label']}\n"
            f"Cadence  : {s['cadence'].upper()}\n"
            f"Platform : {s['platform'].upper()}\n"
            f"Description: {s['description']}\n"
        )
    lines.append(
        "To activate: call create_intelligence_report → publish_intelligence_product.\n"
        "Gumroad publishes automatically if GUMROAD_API_KEY is set in Railway."
    )
    return "\n".join(lines)


# ── Dispatcher ────────────────────────────────────────────────────────────────

async def dispatch_oracle_tool(tool_name: str, tool_input: dict, db=None) -> str:
    try:
        if tool_name == "cultural_scan":
            return await oracle_cultural_scan(
                domain=tool_input.get("domain", "culture"),
                timeframe=tool_input.get("timeframe", "current"),
            )
        elif tool_name == "sentiment_map":
            return await oracle_sentiment_map(
                community_focus=tool_input.get("community_focus", "general"),
                emotion_domain=tool_input.get("emotion_domain", ""),
            )
        elif tool_name == "timing_intelligence":
            return await oracle_timing_intelligence(
                content_theme=tool_input.get("content_theme", ""),
                platform=tool_input.get("platform", ""),
                urgency=tool_input.get("urgency", "this_week"),
            )
        elif tool_name == "brief_cipher":
            return await oracle_brief_cipher(
                topic=tool_input.get("topic", ""),
                urgency=tool_input.get("urgency", "planned"),
                platform=tool_input.get("platform", ""),
            )
        elif tool_name == "arc_mapping":
            return await oracle_arc_mapping(
                horizon=tool_input.get("horizon", "30_day"),
                db=db,
            )
        elif tool_name == "create_intelligence_report":
            return await oracle_create_intelligence_report(
                report_type=tool_input.get("report_type", "cultural_trends"),
                focus_area=tool_input.get("focus_area", ""),
                depth=tool_input.get("depth", "full_report"),
                stream_id=tool_input.get("stream_id", ""),
                db=db,
            )
        elif tool_name == "publish_intelligence_product":
            return await oracle_publish_intelligence_product(
                title=tool_input.get("title", ""),
                description=tool_input.get("description", ""),
                price_cents=tool_input.get("price_cents", 3999),
                content=tool_input.get("content", ""),
                product_type=tool_input.get("product_type", "report"),
                stream_id=tool_input.get("stream_id", ""),
                db=db,
            )
        elif tool_name == "get_revenue_report":
            return await oracle_get_revenue_report(
                period=tool_input.get("period", "month"),
                db=db,
            )
        elif tool_name == "list_revenue_streams":
            return oracle_list_revenue_streams()
        else:
            return f"[Unknown ORACLE tool: {tool_name}]"
    except Exception as e:
        logger.error("dispatch_oracle_tool %s failed: %s", tool_name, e)
        return f"[ORACLE tool '{tool_name}' encountered an error: {e}]"
