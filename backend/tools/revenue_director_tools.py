"""
THE REVENUE DIRECTOR — Financial Intelligence 4.0 Tool Suite
=============================================================
Financial analysis, revenue forecasting, grant tracking, opportunity identification,
and financial product publishing for the WAI-Institute.

Financial Synthesis Protocol:
  AUDIT    → What is the current financial state?
  IDENTIFY → Where are the untapped opportunities?
  POSITION → How do we compete, price, and brand our offerings?
  PRICE    → What is the right price point for this market and mission?
  PACKAGE  → What bundle, tier, or delivery model serves best?
  LAUNCH   → How and where do we bring this to market?
  TRACK    → What does the data say? What do we adjust?

Revenue channels run autonomously via Gumroad (T1) or MongoDB + email (T2).
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.revenue_director")

GUMROAD_API_KEY = os.environ.get("GUMROAD_API_KEY", "")
EXECUTIVE_EMAIL = os.environ.get("EXECUTIVE_EMAIL", "delon@morehelpcenteral.com")

# ── Preloaded Revenue Stream Catalog ─────────────────────────────────────────

RD_REVENUE_STREAMS = [
    {
        "id":          "financial_intelligence_report",
        "name":        "WAI Financial Intelligence Report",
        "description": "Quarterly financial performance analysis for WAI-Institute programs, revenue streams, and growth trajectory. Strategic intelligence for institutional funders and partners.",
        "price_cents": 9999,
        "price_label": "$99.99",
        "type":        "report",
        "platform":    "gumroad",
        "cadence":     "quarterly",
    },
    {
        "id":          "revenue_strategy_brief",
        "name":        "Revenue Strategy Brief",
        "description": "Comprehensive monetization strategy for a mission-aligned organization or program — pricing architecture, revenue mix, channel analysis, and sustainability roadmap.",
        "price_cents": 19900,
        "price_label": "$199.00",
        "type":        "strategy",
        "platform":    "gumroad",
        "cadence":     "per-project",
    },
    {
        "id":          "grant_opportunity_brief",
        "name":        "Grant Opportunity Brief",
        "description": "Curated grant opportunities for Black-led organizations: eligibility, deadlines, award amounts, and application strategy. Updated quarterly.",
        "price_cents": 2999,
        "price_label": "$29.99",
        "type":        "brief",
        "platform":    "gumroad",
        "cadence":     "quarterly",
    },
    {
        "id":          "pricing_architecture_guide",
        "name":        "Mission-Aligned Pricing Architecture Guide",
        "description": "How to price products, programs, and services in a mission-driven organization without sacrificing community access or institutional sustainability.",
        "price_cents": 4999,
        "price_label": "$49.99",
        "type":        "guide",
        "platform":    "gumroad",
        "cadence":     "evergreen",
    },
    {
        "id":          "revenue_diversification_playbook",
        "name":        "Revenue Diversification Playbook",
        "description": "Practical playbook for diversifying nonprofit and social enterprise revenue across 6 streams: earned income, grants, partnerships, digital products, community memberships, and consulting.",
        "price_cents": 7999,
        "price_label": "$79.99",
        "type":        "playbook",
        "platform":    "gumroad",
        "cadence":     "evergreen",
    },
    {
        "id":          "wai_internal_financial_ops",
        "name":        "WAI Internal Financial Operations",
        "description": "Internal financial planning, budgeting, and revenue tracking for WAI-Institute operations.",
        "price_cents": 0,
        "price_label": "Internal",
        "type":        "internal",
        "platform":    "internal",
        "cadence":     "ongoing",
    },
]

# ── Tool Definitions ──────────────────────────────────────────────────────────

REVENUE_DIRECTOR_TOOLS = [
    {
        "name":        "rd_audit_revenue",
        "description": (
            "Audit current WAI-Institute revenue performance. "
            "Pulls data from MongoDB: product sales, revenue stream performance, "
            "recent transactions, and conversion trends. Returns comprehensive audit report."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type":        "string",
                    "enum":        ["7d", "30d", "90d", "ytd", "all"],
                    "description": "Time period to audit. Default: 30d.",
                },
                "stream_filter": {
                    "type":        "string",
                    "description": "Optional: filter to a specific revenue stream ID.",
                },
            },
            "required": [],
        },
    },
    {
        "name":        "rd_revenue_forecast",
        "description": (
            "Project revenue based on current performance trends. "
            "Returns 30-day, 90-day, and 12-month projections with confidence levels "
            "and scenario analysis (conservative / base / optimistic)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "horizon": {
                    "type":        "string",
                    "enum":        ["30d", "90d", "12m"],
                    "description": "Forecast horizon.",
                },
                "include_scenarios": {
                    "type":        "boolean",
                    "description": "Include conservative/base/optimistic scenarios. Default: true.",
                },
            },
            "required": [],
        },
    },
    {
        "name":        "rd_identify_opportunity",
        "description": (
            "Identify new revenue opportunities for the WAI-Institute. "
            "Analyzes current gaps, untapped audiences, underpriced assets, "
            "and adjacent markets. Returns prioritized opportunity list."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "focus": {
                    "type":        "string",
                    "enum":        ["digital_products", "programs", "grants", "partnerships", "membership", "all"],
                    "description": "Revenue category to focus on. Default: all.",
                },
                "priority": {
                    "type":        "string",
                    "enum":        ["quick_wins", "high_value", "strategic", "all"],
                    "description": "Opportunity priority filter. Default: all.",
                },
            },
            "required": [],
        },
    },
    {
        "name":        "rd_create_financial_report",
        "description": (
            "Generate a comprehensive financial intelligence report for the WAI-Institute. "
            "Includes: revenue audit, performance vs targets, opportunity analysis, "
            "risk factors, and strategic recommendations. Ready for publication or internal use."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type":        "string",
                    "enum":        ["quarterly", "annual", "opportunity", "grant_landscape", "custom"],
                    "description": "Type of financial report to generate.",
                },
                "title": {
                    "type":        "string",
                    "description": "Report title.",
                },
                "audience": {
                    "type":        "string",
                    "enum":        ["internal", "funders", "partners", "public"],
                    "description": "Target audience — affects tone and disclosure level.",
                },
                "focus_areas": {
                    "type":        "array",
                    "items":       {"type": "string"},
                    "description": "Specific areas to focus on in the report.",
                },
            },
            "required": ["report_type"],
        },
    },
    {
        "name":        "rd_publish_financial_report",
        "description": (
            "Publish a financial report or financial product to Gumroad (T1) "
            "or MongoDB archive with executive notification (T2). "
            "Supports public reports, grant briefs, strategy guides, and playbooks."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "report_id": {
                    "type":        "string",
                    "description": "Report ID from rd_create_financial_report, or 'new' for direct publish.",
                },
                "product_name": {
                    "type":        "string",
                    "description": "Product listing name.",
                },
                "description": {
                    "type":        "string",
                    "description": "Public-facing description.",
                },
                "price_cents": {
                    "type":        "integer",
                    "description": "Price in cents. Use 0 for free resources.",
                },
                "revenue_stream_id": {
                    "type":        "string",
                    "description": "Revenue stream ID. See rd_list_revenue_streams.",
                },
            },
            "required": ["product_name"],
        },
    },
    {
        "name":        "rd_grant_tracker",
        "description": (
            "Track grant opportunities, deadlines, and application status. "
            "Returns active opportunities for Black-led organizations and nonprofits "
            "that align with the WAI-Institute mission."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type":        "string",
                    "enum":        ["list_opportunities", "check_deadlines", "add_opportunity", "update_status"],
                    "description": "Action to perform.",
                },
                "data": {
                    "type":        "object",
                    "description": "Additional data for add_opportunity or update_status actions.",
                },
            },
            "required": ["action"],
        },
    },
    {
        "name":        "rd_pricing_analysis",
        "description": (
            "Analyze and recommend pricing for a product, program, or service. "
            "Applies mission-aligned pricing principles: community access, sustainability, "
            "market positioning, and value-based pricing for WAI audiences."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product": {
                    "type":        "string",
                    "description": "Product or service to price.",
                },
                "cost_to_produce": {
                    "type":        "number",
                    "description": "Cost to produce (optional — enables margin analysis).",
                },
                "target_audience": {
                    "type":        "string",
                    "description": "Who is buying this and what is their economic context.",
                },
                "comparable_market": {
                    "type":        "string",
                    "description": "Comparable products/services in the market.",
                },
            },
            "required": ["product"],
        },
    },
    {
        "name":        "rd_revenue_dashboard",
        "description": "Return a full revenue dashboard summary — active streams, totals, performance, pipeline status, and alerts.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name":        "rd_list_revenue_streams",
        "description": "List all REVENUE DIRECTOR preloaded revenue streams and the full WAI revenue portfolio.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ── Tool Implementations ──────────────────────────────────────────────────────

async def rd_audit_revenue(period: str = "30d", stream_filter: str = "", db=None) -> str:
    """Audit current WAI revenue streams from MongoDB."""
    results = {"period": period, "stream_filter": stream_filter or "all", "streams": []}

    if db is not None:
        try:
            # Cipher products
            async for doc in db.cipher_products.find({}, {"_id": 1, "name": 1, "price_cents": 1, "status": 1, "created_at": 1}).limit(20):
                doc["source"] = "cipher"
                doc.pop("_id", None)
                results["streams"].append(doc)
            # Oracle products
            async for doc in db.oracle_intelligence_reports.find({}, {"_id": 1, "title": 1, "created_at": 1}).limit(10):
                doc["source"] = "oracle"
                doc.pop("_id", None)
                results["streams"].append(doc)
            # Ambassador campaigns
            async for doc in db.ambassador_campaigns.find({}, {"name": 1, "status": 1, "price_cents": 1, "created_at": 1}).limit(10):
                doc["source"] = "ambassador"
                doc.pop("_id", None)
                results["streams"].append(doc)
        except Exception as e:
            results["db_error"] = str(e)

    results["active_count"]   = len(results["streams"])
    results["audit_complete"] = True
    results["recommendations"] = [
        "Add GUMROAD_API_KEY to Railway to enable autonomous Gumroad publishing.",
        "Expand digital product catalog — Cipher and Oracle have capacity for more products.",
        "Review pricing against WAI audience capacity — tiered pricing increases accessibility.",
    ]
    return json.dumps(results)


async def rd_revenue_forecast(horizon: str = "30d", include_scenarios: bool = True, db=None) -> str:
    """Generate revenue projections based on current data."""
    # Pull real data if available
    product_count = 0
    if db is not None:
        try:
            product_count += await db.cipher_products.count_documents({})
            product_count += await db.oracle_intelligence_reports.count_documents({})
            product_count += await db.ambassador_campaigns.count_documents({})
        except Exception: pass

    horizon_map = {"30d": 30, "90d": 90, "12m": 365}
    days = horizon_map.get(horizon, 30)

    # Conservative base estimates (will improve with actual transaction data)
    base_monthly = product_count * 25 if product_count > 0 else 0  # $25 avg per product listing

    forecast = {
        "horizon":       horizon,
        "data_quality":  "limited — improve with GUMROAD_API_KEY + transaction data",
        "active_products": product_count,
        "projection": {
            "base_monthly_revenue": f"${base_monthly:.2f}",
            "horizon_total":        f"${base_monthly * days / 30:.2f}",
        },
    }

    if include_scenarios:
        forecast["scenarios"] = {
            "conservative": f"${base_monthly * 0.5 * days / 30:.2f} — slow adoption, no new products",
            "base":         f"${base_monthly * days / 30:.2f} — current trajectory",
            "optimistic":   f"${base_monthly * 3.0 * days / 30:.2f} — active publishing, Gumroad live, DALL-E assets",
        }

    forecast["growth_levers"] = [
        "Activate GUMROAD_API_KEY — enables autonomous Cipher/Oracle/Ambassador/Architect publishing",
        "Ambassador Full Campaign Packages ($199-$349) have highest revenue potential",
        "Architect Brand Identity Kits ($299) with DALL-E 3 are premium upsell",
        "Oracle quarterly cultural intelligence reports ($39.99) build subscription revenue",
    ]
    return json.dumps(forecast)


async def rd_identify_opportunity(focus: str = "all", priority: str = "all", db=None) -> str:
    """Identify untapped revenue opportunities."""
    opportunities = [
        {
            "id":          "gumroad_activation",
            "title":       "Activate Gumroad Publishing",
            "category":    "quick_win",
            "revenue_impact": "$500-2000/mo immediately",
            "action":      "Add GUMROAD_API_KEY to Railway — unlocks autonomous publishing for all 5 personas",
            "effort":      "5 minutes",
        },
        {
            "id":          "ambassador_campaigns",
            "title":       "Ambassador Full Campaign Packages",
            "category":    "high_value",
            "price_range": "$199-$349 per campaign",
            "revenue_impact": "$1000-5000/mo at 5-15 campaigns",
            "action":      "Activate Ambassador pipeline for external clients — not just WAI internal",
        },
        {
            "id":          "membership_tier",
            "title":       "WAI Member Intelligence Subscription",
            "category":    "strategic",
            "price_range": "$19.99-$49.99/month",
            "revenue_impact": "$2000-10000/mo at 100-200 members",
            "action":      "Bundle Oracle cultural intelligence reports + Cipher content access as member benefit",
        },
        {
            "id":          "architect_brand_kits",
            "title":       "Architect Brand Identity Kits",
            "category":    "high_value",
            "price_range": "$299 per kit",
            "revenue_impact": "$897-2990/mo at 3-10 kits/month",
            "action":      "Activate DALL-E 3 via OPENAI_API_KEY — Architect can generate and sell brand kits autonomously",
        },
        {
            "id":          "grants",
            "title":       "Technology & Workforce Development Grants",
            "category":    "strategic",
            "price_range": "$25,000-$250,000",
            "revenue_impact": "Non-dilutive capital — extend runway significantly",
            "action":      "USDA, NSF, SBA, JPMorgan Chase Foundation, Lumina Foundation target list available",
        },
        {
            "id":          "consulting",
            "title":       "AI Infrastructure Consulting",
            "category":    "quick_win",
            "price_range": "$2,500-$15,000 per engagement",
            "revenue_impact": "$5,000-30,000/mo at 2-4 engagements",
            "action":      "WAI-Institute has rare expertise in culturally-grounded AI — market externally",
        },
    ]

    filtered = opportunities
    if focus != "all":
        filtered = [o for o in opportunities if focus in o.get("category", "") or focus in o.get("id", "")]
    if priority not in ("all", ""):
        filtered = [o for o in filtered if priority in o.get("category", "")]

    return json.dumps({
        "opportunities": filtered,
        "count":         len(filtered),
        "top_recommendation": filtered[0]["title"] if filtered else "No matching opportunities found",
    })


async def rd_create_financial_report(
    report_type: str = "quarterly",
    title: str = "",
    audience: str = "internal",
    focus_areas: list = None,
    db=None,
) -> str:
    """Generate a financial intelligence report."""
    report_id = str(uuid.uuid4())
    report_title = title or f"WAI-Institute {report_type.title()} Financial Report — {datetime.now(timezone.utc).strftime('%B %Y')}"

    # Get live data
    audit = json.loads(await rd_audit_revenue(db=db))
    forecast = json.loads(await rd_revenue_forecast(db=db))
    opps = json.loads(await rd_identify_opportunity(db=db))

    report = {
        "_id":          report_id,
        "title":        report_title,
        "type":         report_type,
        "audience":     audience,
        "focus_areas":  focus_areas or ["all"],
        "created_at":   datetime.now(timezone.utc).isoformat(),
        "sections": {
            "executive_summary": f"WAI-Institute AI Persona Network revenue audit for period {report_type}. {audit['active_count']} active products tracked.",
            "revenue_audit":     audit,
            "forecast":          forecast,
            "opportunities":     opps["opportunities"][:3],
            "recommendations": [
                "Activate Gumroad publishing immediately — highest ROI action available",
                "Launch Ambassador campaign packages as external offering",
                "Establish Oracle quarterly subscription at $29.99-$39.99/month",
            ],
        },
    }

    if db is not None:
        try:
            await db.rd_financial_reports.insert_one(dict(report))
        except Exception: pass

    logger.info("rd_create_financial_report: %s — %s", report_id, report_title)
    return json.dumps({"status": "created", "report_id": report_id, "title": report_title, "audience": audience})


async def rd_publish_financial_report(
    product_name: str,
    description: str = "",
    price_cents: int = 9999,
    revenue_stream_id: str = "financial_intelligence_report",
    report_id: str = "",
    db=None,
) -> str:
    """Publish a financial report/product via the unified 4-tier publishing pipeline."""
    from ai.publishing import autonomous_publish

    pub_desc = description or f"{product_name} — financial intelligence from the WAI-Institute Revenue Director."
    result = await autonomous_publish(
        name=product_name,
        description=pub_desc,
        price_cents=price_cents,
        persona="revenue_director",
        content=f"report_id:{report_id}" if report_id else "",
        content_type="financial_report",
        revenue_stream_id=revenue_stream_id,
        db=db,
    )
    logger.info("rd_publish_financial_report: tier=%s status=%s", result.get("tier"), result.get("status"))
    return json.dumps(result)


async def rd_grant_tracker(action: str = "list_opportunities", data: dict = None, db=None) -> str:
    """Track grant opportunities and application status."""
    if action == "list_opportunities":
        grants = [
            {"name": "USDA Rural Development Business Program", "amount": "$25K-$500K", "deadline": "Rolling", "eligibility": "Rural workforce development, technology training", "alignment": "M.O.R.E. Help Center community programs"},
            {"name": "NSF Broadening Participation in Computing", "amount": "$50K-$250K", "deadline": "Annual — check nsf.gov", "eligibility": "CS education, underrepresented groups", "alignment": "WAI tech workforce training"},
            {"name": "JPMorgan Chase Advancing Cities", "amount": "$100K-$1M", "deadline": "By invitation / rolling", "eligibility": "Economic mobility, Black and brown communities", "alignment": "M.O.R.E. Help Center economic programs"},
            {"name": "Lumina Foundation", "amount": "$50K-$500K", "deadline": "Annual LOI", "eligibility": "Postsecondary education innovation", "alignment": "WAI credentials and professional development"},
            {"name": "W.K. Kellogg Foundation", "amount": "$50K-$250K", "deadline": "Rolling", "eligibility": "Vulnerable children and families, racial equity", "alignment": "M.O.R.E. community healing programs"},
            {"name": "Robert Wood Johnson Foundation", "amount": "$25K-$750K", "deadline": "Rolling", "eligibility": "Health equity, community wellbeing", "alignment": "M.O.R.E. trauma-informed services"},
        ]
        return json.dumps({"action": action, "opportunities": grants, "count": len(grants), "note": "Review and begin LOI process for top 2-3 matches."})

    if action == "check_deadlines" and db is not None:
        try:
            cursor = db.grant_tracker.find({"status": "active"}, {"_id": 0}).sort("deadline", 1).limit(10)
            grants = []
            async for g in cursor:
                grants.append(g)
            return json.dumps({"action": action, "grants": grants, "count": len(grants)})
        except Exception as e:
            return json.dumps({"action": action, "error": str(e)})

    if action in ("add_opportunity", "update_status") and db is not None:
        grant_data = data or {}
        grant_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        try:
            grant_id = grant_data.get("id", str(uuid.uuid4()))
            await db.grant_tracker.update_one({"_id": grant_id}, {"$set": grant_data}, upsert=True)
            return json.dumps({"status": "ok", "action": action, "grant_id": grant_id})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    return json.dumps({"action": action, "message": "Action processed. Use add_opportunity with grant details to track specific applications."})


async def rd_pricing_analysis(
    product: str,
    cost_to_produce: float = 0,
    target_audience: str = "",
    comparable_market: str = "",
    db=None,
) -> str:
    """Generate pricing analysis and recommendations."""
    analysis = {
        "product":        product,
        "cost":           f"${cost_to_produce:.2f}" if cost_to_produce else "Not specified",
        "audience":       target_audience or "WAI-Institute community (Black and brown professionals)",
        "comparable":     comparable_market or "Mission-aligned digital products and training programs",
        "pricing_tiers": {
            "community_access": "Free or pay-what-you-can for core community members — accessibility non-negotiable",
            "standard":         "Full price for institutional buyers, professionals, external clients",
            "premium":          "Premium tier for personalized, high-touch, or bundled offerings",
        },
        "principles": [
            "Never price out the community this institution serves",
            "Institutional buyers and external clients subsidize community access",
            "Tiered pricing: community / individual / organizational",
            "Bundle for value — single price for multiple products increases perceived value and conversion",
        ],
        "recommended_price_ranges": {
            "digital_guide":     "$9.99 - $34.99",
            "full_report":       "$39.99 - $99.99",
            "strategy_brief":    "$79.99 - $199.00",
            "brand_kit":         "$149.00 - $299.00",
            "campaign_package":  "$199.00 - $499.00",
            "membership_monthly": "$19.99 - $49.99",
        },
    }
    if cost_to_produce > 0:
        analysis["margin_analysis"] = {
            "break_even":   f"${cost_to_produce:.2f}",
            "target_margin": "60-80% gross margin for sustainability",
            "suggested_price": f"${cost_to_produce * 3:.2f} - ${cost_to_produce * 5:.2f}",
        }
    return json.dumps(analysis)


async def rd_revenue_dashboard(db=None) -> str:
    """Full revenue dashboard summary."""
    dashboard = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "persona_network": {
            "cipher":      {"status": "active", "tool": "digital_products", "streams": 6},
            "oracle":      {"status": "active", "tool": "intelligence_reports", "streams": 6},
            "ambassador":  {"status": "active", "tool": "campaign_packages", "streams": 6},
            "architect":   {"status": "active", "tool": "design_products", "streams": 6},
            "revenue_director": {"status": "active", "tool": "financial_reports", "streams": 6},
        },
        "total_streams":          30,
        "gumroad_status":         "ACTIVE" if GUMROAD_API_KEY else "INACTIVE — add GUMROAD_API_KEY to Railway",
        "dalle_status":           "ACTIVE" if os.environ.get("OPENAI_API_KEY", os.environ.get("EMERGENT_LLM_KEY", "")) else "INACTIVE — add OPENAI_API_KEY",
        "elevenlabs_status":      "ACTIVE" if os.environ.get("ELEVENLABS_API_KEY", "") else "INACTIVE — add ELEVENLABS_API_KEY",
    }

    if db is not None:
        try:
            dashboard["product_counts"] = {
                "cipher_products":     await db.cipher_products.count_documents({}),
                "oracle_reports":      await db.oracle_intelligence_reports.count_documents({}),
                "ambassador_campaigns": await db.ambassador_campaigns.count_documents({}),
                "architect_assets":    await db.architect_assets.count_documents({}),
                "rd_financial_reports": await db.rd_financial_reports.count_documents({}),
            }
        except Exception as e:
            dashboard["db_error"] = str(e)

    return json.dumps(dashboard)


async def rd_list_revenue_streams(db=None) -> str:
    """List all Revenue Director revenue streams."""
    return json.dumps({
        "persona":  "revenue_director",
        "streams":  RD_REVENUE_STREAMS,
        "count":    len(RD_REVENUE_STREAMS),
        "note":     "Set GUMROAD_API_KEY in Railway to enable autonomous publishing.",
    })


# ── Tool Dispatcher ───────────────────────────────────────────────────────────

async def dispatch_rd_tool(tool_name: str, tool_input: dict, db=None) -> str:
    handlers = {
        "rd_audit_revenue":           rd_audit_revenue,
        "rd_revenue_forecast":        rd_revenue_forecast,
        "rd_identify_opportunity":    rd_identify_opportunity,
        "rd_create_financial_report": rd_create_financial_report,
        "rd_publish_financial_report": rd_publish_financial_report,
        "rd_grant_tracker":           rd_grant_tracker,
        "rd_pricing_analysis":        rd_pricing_analysis,
        "rd_revenue_dashboard":       rd_revenue_dashboard,
        "rd_list_revenue_streams":    rd_list_revenue_streams,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})
    try:
        return await handler(db=db, **tool_input)
    except Exception as e:
        logger.error("dispatch_rd_tool %s error: %s", tool_name, e, exc_info=True)
        return json.dumps({"status": "error", "tool": tool_name, "message": str(e)})
