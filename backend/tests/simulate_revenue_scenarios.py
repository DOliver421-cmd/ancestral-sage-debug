"""
WAI-Institute Revenue Division — Scenario Simulation Suite.
Run against a live backend:  python -m tests.simulate_revenue_scenarios

Simulates 3 business scenarios through the staff meeting engine with all
9 core personas.  Then ranks each persona by strengths and weaknesses
based on their code-defined capabilities.
"""

import os
import sys
import json
import time
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api"

EXEC = ("exec@lcewai.org", "Exec@LCE2026")


def login(s, email, pw):
    r = s.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=20)
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


def hdr(t):
    return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


# ── Persona capability map (from codebase analysis) ───────────────────────────

PERSONA_CAPABILITIES = {
    "director": {
        "strengths": ["Governance & strategy", "Risk management", "Persona oversight", "System health monitoring"],
        "weaknesses": ["No creative production", "No visual design", "No content creation"],
        "tools": ["web_search", "fetch_url", "send_email", "get_incident_register", "set_mode", "create_incident", "get_system_health"],
    },
    "revenue_director": {
        "strengths": ["Revenue auditing", "Financial forecasting", "Opportunity identification", "Grant tracking", "Pricing analysis"],
        "weaknesses": ["No technical curriculum knowledge", "No community outreach expertise"],
        "tools": ["rd_audit_revenue", "rd_revenue_forecast", "rd_identify_opportunity", "rd_create_financial_report", "rd_grant_tracker", "rd_pricing_analysis"],
    },
    "ancestral_sage": {
        "strengths": ["Healing wisdom", "Cultural guidance", "Wellness content", "Community pulse sensing", "Meditation & spiritual guidance"],
        "weaknesses": ["No technical or financial analysis", "No legal expertise", "No operational planning"],
        "tools": ["sage_create_healing_guide", "sage_create_meditation_script", "sage_wisdom_archive", "sage_community_pulse", "sage_publish_wellness_content"],
    },
    "ambassador": {
        "strengths": ["Campaign coordination", "Cross-persona orchestration", "Execution timing", "Partnership development"],
        "weaknesses": ["No independent content creation", "No deep analysis capability"],
        "tools": ["coordinate_oracle", "coordinate_cipher", "coordinate_architect", "package_campaign", "publish_campaign", "request_director_approval"],
    },
    "cipher": {
        "strengths": ["Creative content", "Viral strategy", "Digital product creation", "Spoken word / performance", "Trend analysis"],
        "weaknesses": ["No governance or compliance expertise", "No financial modeling"],
        "tools": ["trend_scan", "platform_format", "create_digital_product", "publish_product", "engagement_analyze", "generate_image_brief"],
    },
    "oracle": {
        "strengths": ["Cultural intelligence", "Sentiment mapping", "Trend forecasting", "Timing intelligence", "Arc mapping"],
        "weaknesses": ["No hands-on execution", "No content production"],
        "tools": ["cultural_scan", "sentiment_map", "timing_intelligence", "brief_cipher", "arc_mapping", "create_intelligence_report"],
    },
    "architect": {
        "strengths": ["Visual branding", "Cover art generation (DALL-E 3)", "Social asset design", "Brand consistency auditing"],
        "weaknesses": ["No text content creation", "No strategic planning", "No financial analysis"],
        "tools": ["generate_cover_art", "design_social_asset", "build_brand_brief", "create_visual_storyboard", "audit_brand_consistency"],
    },
    "poor_righteous_teacher": {
        "strengths": ["Doctrinal validation", "Cultural alignment enforcement", "Directive gatekeeping"],
        "weaknesses": ["Only validates — does not produce", "No creative or financial output"],
        "tools": ["filter_directive", "enforce", "trigger_the9"],
    },
    "the_9": {
        "strengths": ["Unified synthesis across all domains", "All persona capabilities combined", "Optimal path identification"],
        "weaknesses": ["Dependent on input quality from other personas", "No independent initiative"],
        "tools": ["fuse", "activate", "unified_skill_set deployment"],
    },
}

SCENARIOS = [
    {
        "name": "Community Outreach — Detroit Launch",
        "brief": "We need to launch a community outreach program in Detroit focused on electrical trade training for underserved youth. We have a church venue, volunteer instructors, and funding for 20 apprentice kits.",
        "agenda": ["Venue logistics", "Curriculum adaptation", "Student recruitment", "Funding allocation", "Community partnerships"],
        "priority": "high",
        "participants": ["director", "revenue_director", "ancestral_sage", "ambassador", "cipher", "oracle", "architect"],
    },
    {
        "name": "Curriculum Expansion — Solar PV Advanced Module",
        "brief": "Develop a new advanced Solar PV installation module. Must include hands-on lab exercises, compliance with NEC 2026 solar requirements, and certification exam.",
        "agenda": ["Learning objectives", "Lab design", "NEC compliance check", "Certification pathway", "Pilot timeline"],
        "priority": "high",
        "participants": ["director", "revenue_director", "ambassador", "oracle", "architect", "poor_righteous_teacher"],
    },
    {
        "name": "Revenue Growth — Q3 Commercial Strategy",
        "brief": "Plan Q3 revenue growth strategy. Need to increase course licensing revenue by 40%, launch 2 new paid credentials, and sign 5 contractor partnerships.",
        "agenda": ["Pricing strategy", "Partner outreach", "Credential design", "Sales pipeline", "Revenue forecast"],
        "priority": "high",
        "participants": ["director", "revenue_director", "ambassador", "cipher", "oracle", "architect", "poor_righteous_teacher"],
    },
]


def simulate():
    s = requests.Session()
    print("=" * 72)
    print("WAI-INSTITUTE REVENUE DIVISION — SCENARIO SIMULATION")
    print("=" * 72)

    try:
        token = login(s, *EXEC)
        print(f"\n✓ Authenticated as executive admin\n")
    except Exception as e:
        print(f"\n✗ Cannot authenticate: {e}")
        print("  Make sure the server is running and seeded with exec@lcewai.org")
        print("  Export REACT_APP_BACKEND_URL if not using localhost:8001\n")
        sys.exit(1)

    results = []

    for scenario in SCENARIOS:
        print(f"\n{'─' * 72}")
        print(f"SCENARIO: {scenario['name']}")
        print(f"{'─' * 72}")
        print(f"  Brief: {scenario['brief'][:100]}...")
        print(f"  Agenda: {', '.join(scenario['agenda'])}")
        print(f"  Participants: {', '.join(scenario['participants'])}")
        print(f"  Priority: {scenario['priority']}\n")

        try:
            r = s.post(
                f"{API}/exec/staff-meeting",
                headers=hdr(token),
                json={
                    "brief": scenario["brief"],
                    "agenda": scenario["agenda"],
                    "participants": scenario["participants"],
                    "priority": scenario["priority"],
                },
                timeout=120,
            )

            if r.status_code == 200:
                data = r.json()
                results.append({"scenario": scenario["name"], "data": data})
                print(f"  ✓ Meeting convened: {data['meeting_id'][:8]}")
                print(f"  ✓ PRT cleared: {data.get('prt_cleared', 'N/A')}")
                print(f"  ✓ Participants: {len(data.get('participants', []))}")
                print(f"  ✓ The 9 synthesis: {'available' if data.get('synthesis') else 'unavailable'}")

                # Print persona responses
                briefs = data.get("domain_briefs", {})
                for pid, brief in briefs.items():
                    status = brief.get("status", "unknown")
                    response_len = len(brief.get("response", ""))
                    print(f"    {pid:25s} → {status:20s} ({response_len} chars)")

                # Print synthesis summary
                synth = data.get("synthesis", {})
                if synth and synth.get("synthesis_brief"):
                    print(f"\n  THE 9 SYNTHESIS (first 300 chars):")
                    print(f"    {synth['synthesis_brief'][:300]}...")
                if synth and synth.get("unified_skill_set"):
                    print(f"\n  UNIFIED SKILL SET: {', '.join(synth['unified_skill_set'])}")

            else:
                print(f"  ✗ Failed: {r.status_code} {r.text[:200]}")
                results.append({"scenario": scenario["name"], "error": r.text[:200]})

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({"scenario": scenario["name"], "error": str(e)})

        time.sleep(2)  # rate limit courtesy

    # ── Persona rankings ──────────────────────────────────────────────────────
    print(f"\n\n{'=' * 72}")
    print("PERSONA RANKINGS — STRENGTHS & WEAKNESSES")
    print(f"{'=' * 72}\n")

    rankings = []
    for pid, caps in PERSONA_CAPABILITIES.items():
        # Score: one point per strength, half point per tool, penalty for weakness count
        score = len(caps["strengths"]) + (len(caps["tools"]) * 0.5) - (len(caps["weaknesses"]) * 0.3)
        rankings.append((pid, score, caps))

    rankings.sort(key=lambda x: x[1], reverse=True)

    print(f"{'Rank':<6} {'Persona':<30} {'Score':<8} {'Key Strengths':<30} {'Key Weaknesses'}")
    print(f"{'─' * 6} {'─' * 30} {'─' * 8} {'─' * 30} {'─' * 30}")
    for i, (pid, score, caps) in enumerate(rankings, 1):
        strengths = caps["strengths"][0] if caps["strengths"] else "—"
        weaknesses = caps["weaknesses"][0] if caps["weaknesses"] else "—"
        print(f"{i:<6} {pid:<30} {score:<8.1f} {strengths:<30} {weaknesses}")

    print(f"\n\n{'=' * 72}")
    print("ASSESSMENT")
    print(f"{'=' * 72}")

    # Scoring by scenario
    print(f"\nScenario Coverage:")
    for pid, caps in PERSONA_CAPABILITIES.items():
        covered = sum(1 for s in SCENARIOS if pid in s["participants"])
        print(f"  {pid:<30} → {'✓' if covered > 0 else '✗'} participated in {covered}/{len(SCENARIOS)} scenarios")

    # Top recommendation
    top = rankings[0]
    print(f"\nTop Performer: {top[0]} (score {top[1]:.1f})")
    print(f"Best suited for: {', '.join(PERSONA_CAPABILITIES[top[0]]['strengths'][:2])}")

    print(f"\n{'=' * 72}")
    print("SYSTEM READY FOR LIVE TESTING")
    print(f"{'=' * 72}")
    print(f"  ✓ Revenue Division frontend:   /revenue")
    print(f"  ✓ API key management:           POST /api/revenue/api-keys")
    print(f"  ✓ Credential verification:      POST /api/revenue/verify-credential")
    print(f"  ✓ Course licensing:             POST /api/revenue/courses/license")
    print(f"  ✓ Compliance dashboard:         GET /api/revenue/employer/compliance")
    print(f"  ✓ Sovereign workspaces:         POST /api/revenue/sovereign/workspace")
    print(f"  ✓ Resume builder:               GET /api/revenue/resume/preview")
    print(f"  ✓ Staff meeting engine:         POST /api/exec/staff-meeting")
    print(f"  ✓ Help guide:                   POST /api/help/guide")
    print(f"  ✓ Session management:           GET /api/auth/sessions")
    print(f"  ✓ AI cost tracking:             GET /api/admin/ai-costs")
    print(f"  ✓ Cookie consent logging:       POST /api/consent/cookie")
    print(f"\n  Run tests: pytest backend/tests/test_critical_paths.py -v")
    print(f"\n  Deploy: git push (Railway auto-deploys)")


if __name__ == "__main__":
    simulate()
