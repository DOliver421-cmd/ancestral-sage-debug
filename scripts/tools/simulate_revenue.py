"""
WAI-Institute Pipeline Revenue Simulation
==========================================
Uses the real PipelineManager routing logic (keyword scorer + _ROUTING_TABLE)
against a synthetic corpus representative of the Black/brown spoken word
community audience. No LLM calls — keyword fallback only, deterministic.
"""

import sys, os, asyncio, random, json
sys.path.insert(0, r"C:\Users\lenovo\ancestral-sage-debug")

from src.agents.pipeline_manager import (
    PipelineManager,
    ROUTE_OUTREACH, ROUTE_MERCH, ROUTE_DISCOVERY,
    ROUTE_NEUTRAL, ROUTE_BLOCKED,
)

random.seed(42)

# ── Synthetic post corpus ────────────────────────────────────────────────────
CORPUS = [
    # SEEKING (index 0–19)
    "looking for healing poetry about grief and loss, anything by Black poets",
    "does anyone have a poem for someone who just lost their mother?",
    "need something for grief, my father passed three weeks ago",
    "can anyone recommend spoken word about identity and blackness",
    "searching for a poem about resilience for my daughter's graduation",
    "help me find poetry about healing from trauma",
    "where can i find a poem about carrying grief and still showing up",
    "looking for something to read at a memorial, grief and love together",
    "anyone know poetry about community and belonging in Black spaces",
    "need a healing poem for a friend going through loss and trauma",
    "poetry about blackness and identity — something powerful for a speech",
    "struggling with grief every day, looking for poems that feel like me",
    "anyone recommend spoken word about hope and resilience",
    "poem for grief that does not feel like giving up on healing",
    "looking for poetry about love and loss combined, something raw",
    "need spoken word about purpose and growth for my students",
    "recommend poetry about justice and rage that still holds love",
    "searching for a poem about loneliness and community at the same time",
    "help me find something about ancestry and who I come from",
    "looking for healing poetry for my therapy group about trauma and hope",

    # SHARING (index 20–39)
    "i been carrying this grief for so long it feels like my name",
    "this poem about blackness hit me different at 3am",
    "i needed this healing more than i knew",
    "crying because this poem said everything i couldn't",
    "i am still healing and that's enough. that's enough.",
    "nobody talks about how grief and love feel the same sometimes",
    "this hits different when you've lost someone to the system",
    "just heard this spoken word and i am wrecked in the best way",
    "i been going through it and this poem saved me tonight",
    "this is me. this is exactly what i've been trying to say",
    "i feel seen by this poetry in a way therapy never gave me",
    "wow this poem about identity cut so deep i had to share",
    "i've been struggling with rage and this poem held space for it",
    "i can't stop reading this piece about love and grief together",
    "just read this and i am ugly crying on my lunch break",
    "this spoken word about resilience was everything i needed today",
    "i needed to hear about healing being messy and non-linear",
    "i been carrying trauma so long i forgot what lightness feels like",
    "this poem about community makes me want to call everyone i love",
    "i am grieving and healing at the same time and this poem knows it",

    # VIRAL / MERCH-WORTHY (index 40–59)
    "this hits different. nobody talks about grief and joy coexisting like this",
    "say it louder for the people in the back — healing is not linear",
    "i want this on a shirt. this quote about resilience is everything",
    "screenshot this. this poem about grief is the sermon we needed",
    "put this on everything. this quote about blackness needs to be seen",
    "this needs to be a poster. healing takes as long as it takes",
    "nobody talks about how loving your community is also a healing practice",
    "this is a whole sermon. grief is not weakness it is love with nowhere to go",
    "quote of the day: you are not behind you are healing at your own pace",
    "this hits different nobody talks about the grief you carry just by surviving",
    "say it louder — your resilience is not your trauma it is what you chose",
    "i want this on a shirt: we grieve because we loved and that is enough",
    "screenshot this: joy is an act of resistance in a world designed for your pain",
    "put this on a poster: healing happens in community not in isolation",
    "this needs to be on a mug. carry grief gently it is just love looking for home",
    "nobody talks about how finding community heals what systems broke",
    "this hits different — identity is not a question it is an answer",
    "save this: your ancestry is not your trauma it is your medicine",
    "this is a whole movement. love as justice joy as resistance healing as revolution",
    "quote of the day: rage is a holy emotion when it protects what you love",

    # LOW CONFIDENCE / DISCOVERY (index 60–79)
    "reading a lot of poetry lately",
    "I enjoy spoken word sometimes",
    "art is important to communities",
    "words have power",
    "culture matters to people",
    "expression takes many forms",
    "communities share stories",
    "I like writing sometimes",
    "sharing is caring in creative spaces",
    "creative work takes time and effort",
    "people connect through art",
    "stories matter to all of us",
    "reading makes you think differently",
    "music and poetry go together",
    "creativity is a practice",
    "I've been thinking about writing",
    "sometimes words are all we have",
    "community is built through shared experience",
    "art heals what we cannot name",
    "expression is a basic human need",

    # NEUTRAL (index 80–99)
    "today is wednesday and the weather is okay",
    "just got back from the grocery store",
    "traffic was rough this morning",
    "watching a show tonight nothing special",
    "coffee is the only thing keeping me going today",
    "the weekend was fine nothing much happened",
    "my phone battery died again",
    "trying to sleep earlier but it is not working",
    "had a long meeting at work today",
    "the internet is slow again today",
    "ordered food and it came cold",
    "looking for a new TV show to watch",
    "can't decide what to cook for dinner",
    "my car needs an oil change",
    "forgot to pay a bill need to do that today",
    "it is raining and I left my umbrella home",
    "need to do laundry this weekend",
    "my laptop is running slow",
    "can't find my keys again",
    "the gym was crowded this morning",

    # SPAM (index 100–104)
    "buy now limited offer click here for free poetry access today",
    "BUY NOW get unlimited spoken word content CLICK HERE act now",
    "check this out https://bit.ly/fakelink amazing deal on poetry",
    "limited offer buy now click here get this before it expires",
    "act now buy now click here limited time only do not miss out",
]

WEIGHTS = {
    "seeking":   (0,   20, 0.28),
    "sharing":   (20,  20, 0.26),
    "viral":     (40,  20, 0.10),
    "discovery": (60,  20, 0.18),
    "neutral":   (80,  20, 0.14),
    "spam":      (100,  5, 0.04),
}

expanded = []
for category, (start, count, weight) in WEIGHTS.items():
    pool = CORPUS[start:start+count]
    n    = int(500 * weight)
    expanded.extend(random.choices(pool, k=n))
random.shuffle(expanded)

# ── Run pipeline ─────────────────────────────────────────────────────────────
mgr = PipelineManager(db=None, anthropic_api_key="")

async def run_simulation(posts):
    return await mgr.process_batch(posts, source="simulation")

results = asyncio.run(run_simulation(expanded))

# ── Routing distribution ─────────────────────────────────────────────────────
route_counts = {r: 0 for r in [ROUTE_OUTREACH, ROUTE_MERCH, ROUTE_DISCOVERY, ROUTE_NEUTRAL, ROUTE_BLOCKED]}
for r in results:
    if r.route in route_counts:
        route_counts[r.route] += 1

total = len(results)

print()
print("=" * 62)
print("  WAI-INSTITUTE PIPELINE — ROUTING DISTRIBUTION")
print("=" * 62)
print(f"  Posts processed  : {total}")
print(f"  Analyzer         : keyword_fallback (production = +LLM)")
print("-" * 62)
for route, count in route_counts.items():
    pct = count / total * 100
    bar = "#" * int(pct / 2)
    print(f"  {route:<12} {count:>4} posts  ({pct:5.1f}%)  {bar}")
print("=" * 62)

pct_outreach  = route_counts[ROUTE_OUTREACH]  / total
pct_merch     = route_counts[ROUTE_MERCH]     / total
pct_discovery = route_counts[ROUTE_DISCOVERY] / total

# ── Revenue model ─────────────────────────────────────────────────────────────
SCENARIOS = {
    "Conservative": dict(
        outreach_cvr=0.030, merch_cvr=0.018, discovery_cvr=0.008,
        aov_digital=9.00,   aov_merch=26.00, aov_disc=8.00,
    ),
    "Moderate": dict(
        outreach_cvr=0.050, merch_cvr=0.030, discovery_cvr=0.015,
        aov_digital=12.00,  aov_merch=30.00, aov_disc=10.00,
    ),
    "Optimistic": dict(
        outreach_cvr=0.075, merch_cvr=0.045, discovery_cvr=0.025,
        aov_digital=15.00,  aov_merch=34.00, aov_disc=12.00,
    ),
}

SCALE_TIERS = {
    "Early   (100/day)":   100,
    "Growth  (500/day)":   500,
    "Scale  (2000/day)":  2000,
}

print()
print("=" * 72)
print("  MONTHLY REVENUE PROJECTIONS  (30-day window)")
print("=" * 72)

for scenario_name, sc in SCENARIOS.items():
    print(f"\n  -- {scenario_name.upper()} SCENARIO --")
    print(f"  {'Scale Tier':<24} {'Outreach':>10} {'Merch':>10} {'Discovery':>11} {'TOTAL/mo':>10}")
    print("  " + "-" * 64)
    for tier_name, daily_posts in SCALE_TIERS.items():
        monthly  = daily_posts * 30
        rev_out  = monthly * pct_outreach  * sc["outreach_cvr"]  * sc["aov_digital"]
        rev_merch = monthly * pct_merch    * sc["merch_cvr"]      * sc["aov_merch"]
        rev_disc  = monthly * pct_discovery * sc["discovery_cvr"] * sc["aov_disc"]
        total_rev = rev_out + rev_merch + rev_disc
        print(f"  {tier_name:<24} ${rev_out:>8,.0f}   ${rev_merch:>7,.0f}    ${rev_disc:>7,.0f}   ${total_rev:>8,.0f}")

# ── 12-month ramp (Moderate, 15% MoM) ────────────────────────────────────────
print()
print("=" * 72)
print("  12-MONTH RAMP  (Moderate scenario, +15% posts/month from organic growth)")
print("=" * 72)
print(f"  {'Mo':<5} {'Daily Posts':>12} {'Outreach Rev':>14} {'Merch Rev':>12} {'Total/mo':>11} {'Cumulative':>12}")
print("  " + "-" * 68)

sc         = SCENARIOS["Moderate"]
daily      = 100
cumulative = 0.0
for month in range(1, 13):
    monthly   = daily * 30
    rev_out   = monthly * pct_outreach  * sc["outreach_cvr"]  * sc["aov_digital"]
    rev_merch = monthly * pct_merch     * sc["merch_cvr"]      * sc["aov_merch"]
    rev_disc  = monthly * pct_discovery * sc["discovery_cvr"]  * sc["aov_disc"]
    total_rev = rev_out + rev_merch + rev_disc
    cumulative += total_rev
    print(f"  M{month:<4} {daily:>12,}  ${rev_out:>12,.0f}  ${rev_merch:>9,.0f}  ${total_rev:>9,.0f}  ${cumulative:>10,.0f}")
    daily = int(daily * 1.15)

print()
print(f"  Year-1 cumulative (Moderate, 15% MoM growth): ${cumulative:>10,.0f}")
print("=" * 72)

# ── Key levers ────────────────────────────────────────────────────────────────
sc_mod = SCENARIOS["Moderate"]
merch_aov_bundle_gain = 500 * 30 * pct_merch * sc_mod["merch_cvr"] * (45 - 30)

print()
print("  KEY REVENUE LEVERS  (ranked by estimated impact)")
print("  " + "-" * 68)
print(f"  1. OUTREACH CONVERSION RATE")
print(f"     Carries {pct_outreach*100:.0f}% of all posts. Each +1% CVR at 500/day =")
print(f"     +${500*30*pct_outreach*0.01*sc_mod['aov_digital']:,.0f}/month in outreach revenue alone.")
print()
print(f"  2. DISCOVERY RETARGETING SEQUENCE")
print(f"     {pct_discovery*100:.0f}% of posts land here — the largest single pool.")
print(f"     A 30-day email/DM sequence pushing CVR from 1.5% to 4% =")
print(f"     +${500*30*pct_discovery*(0.04-0.015)*sc_mod['aov_disc']:,.0f}/month at Growth tier.")
print()
print(f"  3. MERCH BUNDLE AOV  (tee + poster)")
print(f"     Raising AOV from $30 to $45 at 500/day Moderate =")
print(f"     +${merch_aov_bundle_gain:,.0f}/month with zero new traffic.")
print()
print(f"  4. LLM UPGRADE (keyword fallback -> Claude Haiku)")
print(f"     Estimated +8-12% routing accuracy on ambiguous posts.")
print(f"     At 500/day that's ~{int(500*0.10)} more posts/day correctly")
print(f"     routed to outreach instead of discovery or neutral.")
print()
print(f"  5. VIRAL THRESHOLD TUNING  (VIRAL_SCORE_THRESHOLD)")
print(f"     Currently {pct_merch*100:.0f}% of posts hit merch route.")
print(f"     Lowering threshold 0.60 -> 0.55 could add ~25 more posts/day")
print(f"     to merch at Growth tier. Test with real LLM first.")
print("  " + "-" * 68)
print()
