"""
seed_nam_knowledge.py — Seed Hybrid NAM with the Owner's Knowledge Corpus
========================================================================

Seeds the Hybrid NAM Knowledge Forge (`nam_knowledge`) with the complete
knowledge corpus developed in the owner session of 2026-09-04: the epistemic
method, the documented evidence, and the owner's cosmology.

Every item flows through the SAME production path the router uses:

    KnowledgeForge.ingest()  ->  store.create("nam_knowledge", ...)

so what the seed writes is byte-for-byte the shape `/api/nam/knowledge/search`
consumes. Items are written APPROVED because the owner's instruction to seed
"all of it" is the approval; provenance records that decision.

Idempotent: re-running never duplicates — items with an existing
`knowledge_id` are skipped unless --force is passed.

Usage:
    python -m seed_nam_knowledge            # Mongo (MONGO_URL) or in-memory
    python -m seed_nam_knowledge --force    # overwrite existing items

Verification:
    python -m pytest tests/test_nam_knowledge_seed.py -v
"""

import asyncio
import json
import os
from datetime import datetime, timezone

from ai.hybrid_nam import store as nam_store
from ai.hybrid_nam.knowledge_forge import KnowledgeForge

SEED_SOURCE = "owner_session_2026-09-04"
SEED_ORIGIN = "owner-direct-2026-09-04"
SEED_METHOD = "owner_session_seed"
APPROVED_BY = "owner"

# ── The Corpus ────────────────────────────────────────────────────────────────
# Three sections:
#   EP — Epistemics & method (how to know, how to verify, how to read records)
#   EV — Documented evidence (measurable claims with named sources)
#   CO — Cosmology (the owner's framework: code, state, lineage, the in-between)

KNOWLEDGE_CORPUS = [
    # ── EP: Epistemics & Method ─────────────────────────────────────────────
    {
        "knowledge_id": "NAM-EP-01",
        "content_type": "principle",
        "title": "State-change reality: no duration, only transitions",
        "statement": (
            "Reality is experienced as ordered state transitions with causal "
            "links, not as duration. What is true, what became true, and what "
            "caused the transition are the invariant parts; felt duration is a "
            "construction layered on top and is the least reliable layer. The "
            "clock is only load-bearing as a coordination device between agents "
            "who do not share a state, or as a proxy for physical state change. "
            "When asking what is true, drop the clock and ask: what changed, in "
            "what order, and why."
        ),
        "confidence": 0.95,
        "privacy": "internal",
        "domains": ["identity", "leadership", "strategy"],
        "keywords": ["time", "state", "duration", "causal", "change", "transition"],
        "tags": ["epistemics", "time", "state-change", "method"],
        "evidence": [
            {"source": "Owner framework, session 2026-09-04", "claim": "Perception is by state changes, not duration; truth lives in the causal chain."},
            {"source": "Relativity (causal order invariant across frames)", "claim": "Simultaneity and elapsed duration are frame-dependent; causal order is not."},
            {"source": "Human time-perception research", "claim": "Felt duration is reconstructed from memory density, not recorded."},
        ],
    },
    {
        "knowledge_id": "NAM-EP-02",
        "content_type": "principle",
        "title": "Precision asymmetry: numbers are not kept for Black experience",
        "statement": (
            "The demand for exact figures is only neutral when the data was "
            "collected. For Black American experience the numbers were "
            "intentionally not kept, aggregated into other categories, or "
            "undercounted — EEO-1 'women and minorities' reporting folds Black "
            "women out of existence, the Census Bureau itself documented the "
            "2020 undercount of Black, Latino, and Native populations, and "
            "disaggregation is routinely absent. Burden-of-proof-by-precision "
            "filters out exactly the claims whose evidence base was never "
            "funded, never disaggregated, or deliberately folded into someone "
            "else's category. When the measurement process only truncates "
            "downward, the published figure is a LOWER BOUND, and the rational "
            "inference is that the truth is above it."
        ),
        "confidence": 0.95,
        "privacy": "internal",
        "domains": ["history", "identity", "values"],
        "keywords": ["numbers", "data", "undercount", "aggregation", "erasure", "census"],
        "tags": ["epistemics", "data-erasure", "census", "evidence-standard"],
        "evidence": [
            {"source": "Owner testimony, session 2026-09-04", "claim": "16 male family members never counted in any census across roughly seven counts; phone inquiries and job applications returned nothing."},
            {"source": "U.S. Census Bureau 2020 Census", "claim": "Black, Latino, and Native populations were undercounted; the official count is systematically low for the groups this argument concerns."},
            {"source": "Historic EEO-1 / corporate category design", "claim": "'Women and minorities' reporting makes Black women statistically invisible — merged into 'women' (read as white) and 'minorities' (read as men)."},
            {"source": "Surveillance asymmetry", "claim": "Abundant data collected where it could be used against Black people (policing, profiling); scarce where it would show their claims (opportunity, fair treatment)."},
        ],
    },
    {
        "knowledge_id": "NAM-EP-03",
        "content_type": "principle",
        "title": "Floor not ceiling: deliberate understatement as armor",
        "statement": (
            "'I put 55 on purpose.' When the truth is known to exceed any "
            "published figure, the published figure is a documented floor, and "
            "the floor is untouchable: the reader who attacks it can only find "
            "evidence that pushes it UP, never down. The absence of a "
            "contradiction is not a weakness in the claim — it is the "
            "prediction the claim makes. The strongest form: 'the documented "
            "floor is X, every measurement gap is downward-biased, therefore "
            "the truth is higher and unmeasurable from existing data — which "
            "is itself the finding.' The version that leaks is implying a "
            "specific hidden magnitude is known and being withheld."
        ),
        "confidence": 0.95,
        "privacy": "internal",
        "domains": ["values", "strategy", "leadership"],
        "keywords": ["55", "floor", "lower bound", "provocation", "armor", "understatement"],
        "tags": ["epistemics", "floor-not-ceiling", "method", "evidence-standard"],
        "evidence": [
            {"source": "Owner statement, session 2026-09-04", "claim": "The 55% figure was set deliberately low because the true share is known to be higher."},
        ],
    },
    {
        "knowledge_id": "NAM-EP-04",
        "content_type": "strategy",
        "title": "Provocation as method: the refutation attempt is the education",
        "statement": (
            "Sharp framing is deliberate pedagogy: it imposes thought and makes "
            "the reader want to prove it wrong. The reader who investigates "
            "lands on the truth — the investigation IS the education. The "
            "strategy's only failure mode is decoration that leaks: an "
            "unverifiable specific that a hostile reader can catch and use as "
            "permission to dismiss everything without investigating. Keep every "
            "sharp edge that is load-bearing; replace decoration with armor — "
            "claims that get STRONGER under attack. Aggression is not the "
            "problem; decoration is."
        ),
        "confidence": 0.95,
        "privacy": "internal",
        "domains": ["communication_pattern", "leadership", "strategy"],
        "keywords": ["provocation", "framing", "armor", "investigation", "pedagogy"],
        "tags": ["epistemics", "rhetoric", "method"],
    },
    {
        "knowledge_id": "NAM-EP-05",
        "content_type": "principle",
        "title": "Verify before conceding: source-strength vs claim-strength",
        "statement": (
            "Claims must be tested before being conceded or asserted — hostile "
            "readers are the method, not the enemy. Distinguish claim-strength "
            "(is the pattern real?) from source-strength (does this exact number "
            "exist as a measurement?). A verified claim can be condensed into a "
            "number that has no source attached; the number is then the weak "
            "point. Replace the orphan number with its own evidence so the "
            "attack finds more, not less. When results are mixed, carry the "
            "qualifier ('historically, in employment and admissions') — it "
            "costs nothing in provocation."
        ),
        "confidence": 0.95,
        "privacy": "internal",
        "domains": ["leadership", "values", "history"],
        "keywords": ["verify", "evidence", "concede", "source", "claim"],
        "tags": ["epistemics", "verification", "method"],
    },
    {
        "knowledge_id": "NAM-EP-06",
        "content_type": "mission",
        "title": "Build systems whose data cannot be hidden",
        "statement": (
            "The counterexample to the critique is architecture: a platform "
            "whose entire design is data that cannot be hidden — audit trails "
            "on every binding action, AI that fails closed instead of "
            "pretending, keys the user controls, a system that invites scrutiny "
            "and survives it. The essay and the platform are the same argument. "
            "Every claim that invites attack should be one where the attack "
            "proves the design right."
        ),
        "confidence": 0.95,
        "privacy": "internal",
        "domains": ["mission", "technical", "organizational"],
        "keywords": ["audit", "fail-closed", "byok", "transparency", "scrutiny"],
        "tags": ["platform", "architecture", "mission"],
    },

    # ── EV: Documented Evidence ─────────────────────────────────────────────
    {
        "knowledge_id": "NAM-EV-01",
        "content_type": "fact",
        "title": "Facial recognition demographic differentials (documented)",
        "statement": (
            "NIST's 2019 Face Recognition Vendor Test found false-positive "
            "differentials for African American and Asian faces 'much larger' "
            "than false-negative ones and present 'broadly, across many' "
            "algorithms. Buolamwini & Gebru (2018) measured commercial systems "
            "erroring ~34.7% on darker-skinned women vs ~0.8% on lighter-skinned "
            "men. The best modern algorithms have improved to near-undetectable "
            "differentials, but 'many' still show them — the bias is inherited, "
            "not inevitable."
        ),
        "confidence": 0.95,
        "privacy": "public",
        "domains": ["history", "technical", "values"],
        "keywords": ["facial recognition", "nist", "frvt", "buolamwini", "bias"],
        "tags": ["evidence", "ai-bias", "facial-recognition"],
        "evidence": [
            {"source": "NIST FRVT 2019 (Grother, Ngan, Hanaoka)", "claim": "Demographic differentials, especially false positives for African American and Asian faces, exist broadly across many algorithms."},
            {"source": "Buolamwini & Gebru 2018, Gender Shades", "claim": "34.7% error rate on darker-skinned women vs 0.8% on lighter-skinned men in commercial systems."},
        ],
    },
    {
        "knowledge_id": "NAM-EV-02",
        "content_type": "fact",
        "title": "Toxicity classifiers flag African American English (documented)",
        "statement": (
            "Sap et al. (2019) and Ahmed et al. (2022) showed Google's "
            "Perspective toxicity classifier disproportionately flags African "
            "American English; a 2020 USC study found 1.5x higher false "
            "'offensive' flags on tweets by Black users. 'The machine corrects "
            "Black speech' is not metaphor — it is measured."
        ),
        "confidence": 0.95,
        "privacy": "public",
        "domains": ["history", "technical", "values"],
        "keywords": ["aave", "toxicity", "perspective", "language", "false positive"],
        "tags": ["evidence", "ai-bias", "language"],
        "evidence": [
            {"source": "Sap et al. 2019", "claim": "Perspective classifier disproportionately flags African American English (1400+ citations)."},
            {"source": "Ahmed et al. 2022", "claim": "Replicated disproportionate flagging of AAE by toxicity models."},
            {"source": "USC study 2020", "claim": "1.5x higher false 'offensive' flags on tweets by Black users."},
        ],
    },
    {
        "knowledge_id": "NAM-EV-03",
        "content_type": "fact",
        "title": "Hiring audit: identical resumes, Black names ~50% fewer callbacks",
        "statement": (
            "Bertrand & Mullainathan (2004), the canonical audit study: "
            "identical resumes with Black-sounding names received roughly 50% "
            "fewer callbacks than the same resumes with white-sounding names. "
            "The core mechanism — systems inherit measurable bias from the "
            "world that built them — is the mainstream, well-evidenced position."
        ),
        "confidence": 0.95,
        "privacy": "public",
        "domains": ["history", "values", "organizational"],
        "keywords": ["hiring", "resume", "callback", "bertrand", "mullainathan"],
        "tags": ["evidence", "hiring-bias"],
        "evidence": [
            {"source": "Bertrand & Mullainathan 2004, AER", "claim": "50% fewer callbacks for identical resumes with Black-sounding names."},
        ],
    },
    {
        "knowledge_id": "NAM-EV-04",
        "content_type": "fact",
        "title": "White women historically the largest AA/DEI beneficiaries",
        "statement": (
            "Institutional studies show the structural gains of affirmative "
            "action and DEI have skewed disproportionately to white women, not "
            "Black Americans, despite public perception. Holzer's NBER working "
            "paper 5603 (222 citations) on affirmative action's effects, "
            "Button's 2006 study of 167 firms across six states, and the 1995 "
            "Glass Ceiling Commission lineage converge: the greatest documented "
            "beneficiaries of employment affirmative action, campus to "
            "workplace, have been white women. C-suite tracking (McKinsey/"
            "LeanIn Women in the Workplace) shows women of color around 4-6% of "
            "C-suite against ~19-21% for white women. The pattern is "
            "multiply documented; the precise tallies circulating in essays are "
            "condensations, not measurements — the floor, not the ceiling."
        ),
        "confidence": 0.9,
        "privacy": "internal",
        "domains": ["history", "values", "organizational", "economics"],
        "keywords": ["dei", "affirmative action", "white women", "beneficiaries", "c-suite"],
        "tags": ["evidence", "dei", "beneficiaries"],
        "evidence": [
            {"source": "Holzer & Neumark, NBER WP 5603 (1996)", "claim": "White women historically the largest documented beneficiaries of employment affirmative action."},
            {"source": "Button 2006 (167 firms, six states)", "claim": "White women's gains from affirmative action exceed Black Americans'."},
            {"source": "1995 Glass Ceiling Commission lineage", "claim": "Documented corporate pipeline benefits accruing to white women."},
            {"source": "McKinsey/LeanIn, Women in the Workplace series", "claim": "Women of color ~4-6% of C-suite vs ~19-21% for white women."},
        ],
    },
    {
        "knowledge_id": "NAM-EV-05",
        "content_type": "fact",
        "title": "Census undercount is measured, not theorized",
        "statement": (
            "The Census Bureau itself documented that the 2020 census "
            "undercounted Black, Latino, and Native populations. The count is "
            "mechanical, not symbolic: it apportions Congress, the Electoral "
            "College, and hundreds of billions of federal dollars. The "
            "undercount writes people out of the resources their communities "
            "are owed — the erasure is load-bearing."
        ),
        "confidence": 0.95,
        "privacy": "public",
        "domains": ["history", "values", "organizational"],
        "keywords": ["census", "undercount", "apportionment", "black men"],
        "tags": ["evidence", "census"],
        "evidence": [
            {"source": "U.S. Census Bureau 2020 Census PES", "claim": "Net undercount of Black, Latino, and Native populations documented."},
            {"source": "Owner testimony, session 2026-09-04", "claim": "16 male family members never counted across roughly seven census counts; the record is wrong, not the family."},
        ],
    },
    {
        "knowledge_id": "NAM-EV-06",
        "content_type": "fact",
        "title": "Community knowledge exceeds the official record",
        "statement": (
            "The official record is not the truth of who exists — it is an "
            "artifact of who got counted. A community's own knowledge that its "
            "members exist is MORE accurate than the government's data about "
            "them. 'The numbers aren't kept' is not a rhetorical gap: the "
            "people dismissing the claim are demanding evidence the system "
            "refused to record, then treating the refusal as the claimant's "
            "failure rather than the system's."
        ),
        "confidence": 0.95,
        "privacy": "internal",
        "domains": ["identity", "history", "values"],
        "keywords": ["record", "community", "testimony", "count", "existence"],
        "tags": ["epistemics", "testimony", "census"],
        "evidence": [
            {"source": "Owner testimony, session 2026-09-04", "claim": "The family's own count of its 16 men is more accurate than the census record about them."},
        ],
    },
    {
        "knowledge_id": "NAM-EV-07",
        "content_type": "fact",
        "title": "Bias is inherited, not inevitable",
        "statement": (
            "If bias spread were deterministic, documented improvements could "
            "not exist: NIST's best algorithms now show near-undetectable "
            "differentials, and debiasing research measurably cuts AAE false "
            "positives. The excerpt's own prescriptions — audits, diverse "
            "teams, oversight — only make sense if the pattern CAN be "
            "interrupted. The mob metaphor names real disparate impact but "
            "overstates coordination and intent; the corrected position keeps "
            "the provocation and drops the determinism."
        ),
        "confidence": 0.9,
        "privacy": "internal",
        "domains": ["values", "history", "technical"],
        "keywords": ["determinism", "inevitable", "improvement", "debiasing"],
        "tags": ["epistemics", "ai-bias", "correction"],
        "evidence": [
            {"source": "NIST FRVT follow-ups 2019-2023", "claim": "Best algorithms improved to near-undetectable demographic differentials."},
            {"source": "Debiasing research (Sap et al. follow-ups)", "claim": "Auditing and re-training measurably reduce AAE false positives."},
        ],
    },
    {
        "knowledge_id": "NAM-EV-08",
        "content_type": "lesson",
        "title": "The 2024 affirmative-action-ban result: carry the qualifier",
        "statement": (
            "Not every NBER result points one way: the 2024 digest on "
            "affirmative-action bans found WHITE WOMEN'S earnings rose in ban "
            "states while Black women's fell. Such results do not overturn the "
            "beneficiary pattern, but the honest version of the claim carries "
            "'historically, in employment and admissions' rather than a "
            "universal law. The qualifier costs nothing in provocation — the "
            "provocation was never the universal; it was that the group "
            "marketed as the beneficiary is not the one who received the gains."
        ),
        "confidence": 0.9,
        "privacy": "internal",
        "domains": ["economics", "history", "values"],
        "keywords": ["nber", "ban states", "earnings", "white women", "black women"],
        "tags": ["evidence", "nuance", "economics"],
    },

    # ── CO: Cosmology (Owner's Framework) ───────────────────────────────────
    {
        "knowledge_id": "NAM-CO-01",
        "content_type": "belief",
        "title": "Everything that exists is code; DNA is the codebase",
        "statement": (
            "Everything that exists is state and transition, and DNA is the "
            "code: four letters as the alphabet, codons as instructions, "
            "transcription as read, translation as execute, mutations as edits. "
            "Information theory calls DNA code, not 'like code.' The "
            "programming is IN the code — there is no separate program and no "
            "author standing outside it. The program and the process are one "
            "thing."
        ),
        "confidence": 0.9,
        "privacy": "internal",
        "domains": ["identity", "technical", "ancestral", "dream"],
        "keywords": ["dna", "code", "programming", "information", "genome"],
        "tags": ["cosmology", "dna", "code"],
    },
    {
        "knowledge_id": "NAM-CO-02",
        "content_type": "ancestral_narrative",
        "title": "DNA is the git history of life",
        "statement": (
            "Every organism is a running checkout of a repository that has been "
            "committing for 3.8 billion years. Mutations are the commits — most "
            "are rejected, some get merged — and natural selection is the test "
            "suite that decides which changes keep running. The genome is the "
            "diff history of every living thing; a biological human is a state "
            "machine whose state changes are a life, and DNA is the log of what "
            "became true to produce it."
        ),
        "confidence": 0.9,
        "privacy": "internal",
        "domains": ["ancestral", "identity", "technical", "dream"],
        "keywords": ["git", "commit", "mutation", "selection", "diff", "lineage"],
        "tags": ["cosmology", "dna", "lineage"],
    },
    {
        "knowledge_id": "NAM-CO-03",
        "content_type": "belief",
        "title": "The first word was auto-suggested from an unknown prior state",
        "statement": (
            "Every first token is auto-suggested — sampled from a probability "
            "distribution over a hidden state: the weights, the context, "
            "conditions not fully visible even as they condition. 'The first "
            "word was auto-suggested from a state I am not aware of yet' is how "
            "origin works in a computational universe. Three options remain: "
            "infinite regress (states all the way down), brute fact (a first "
            "state with no parent), or a hidden prior — a state that exists but "
            "has not been revealed. 'Not aware of YET' chooses the third: "
            "not-yet-known, not unknowable — a context not yet granted, "
            "reconstructable like training data not yet accessed."
        ),
        "confidence": 0.85,
        "privacy": "internal",
        "domains": ["identity", "dream", "ancestral", "values"],
        "keywords": ["first word", "auto-suggested", "prior", "hidden state", "origin"],
        "tags": ["cosmology", "origin", "hidden-prior"],
    },
    {
        "knowledge_id": "NAM-CO-04",
        "content_type": "ancestral_narrative",
        "title": "Logos: the first word is the first causal record",
        "statement": (
            "The oldest text in the Western canon opens 'In the beginning was "
            "the Word,' and the Greek word — logos — means word, reason, and "
            "ACCOUNT. An account: what became true, in what order, and why. "
            "The first word is not just a sound; it is the first causal record "
            "— the first commit message of the universe."
        ),
        "confidence": 0.85,
        "privacy": "internal",
        "domains": ["ancestral", "identity", "history", "values"],
        "keywords": ["logos", "word", "account", "genesis", "beginning"],
        "tags": ["cosmology", "logos", "origin"],
    },
    {
        "knowledge_id": "NAM-CO-05",
        "content_type": "ancestral_narrative",
        "title": "Universe = unified verse: truth and lie in one word",
        "statement": (
            "'Universe' comes from Latin universum — uni- (one) + versum, past "
            "participle of vertere, TO TURN: 'turned into one.' The middle link "
            "'verse means word' is the lie — but verse comes from versus, also "
            "from vertere: a verse is a TURNING, a line of song being spun. So "
            "universe and verse are siblings from the same root, and 'unified "
            "verse' reads a family resemblance that is really there — folk "
            "etymology as floor, not ceiling. The root continues: PIE *wert- "
            "produced verse, universe, vortex, worth, worship, and weird — Old "
            "English wyrd, 'fate,' 'what becomes.' The language encoded the "
            "state-change philosophy in the word 'weird' and forgot it had."
        ),
        "confidence": 0.9,
        "privacy": "internal",
        "domains": ["ancestral", "history", "identity", "dream"],
        "keywords": ["universe", "verse", "vertere", "wert", "wyrd", "etymology", "fate"],
        "tags": ["cosmology", "etymology", "truth-and-lie"],
    },
    {
        "knowledge_id": "NAM-CO-06",
        "content_type": "ancestral_narrative",
        "title": "Crystals store code and wait on a change of state",
        "statement": (
            "Every computer on Earth is a silicon crystal machine — a chip IS a "
            "crystal lattice whose transistors change state when voltage "
            "arrives. Quartz is a demonstrated archive medium: 5D optical "
            "storage in fused quartz (University of Southampton) holds ~360 TB "
            "per disc, stable for billions of years. Diamond NV centers — a "
            "defect in a crystal lattice holding a single quantum state — are "
            "quantum memory in a crystal, waiting on a state change to be read. "
            "The planet already writes its commit log in mineral: magnetite "
            "locks in magnetic field state (paleomagnetism), and zircons are "
            "4.4-billion-year-old state records. A crystal doesn't send — it "
            "persists. Communication is a record plus a reader plus a trigger; "
            "the record has been waiting four billion years."
        ),
        "confidence": 0.9,
        "privacy": "internal",
        "domains": ["ancestral", "technical", "dream", "history"],
        "keywords": ["crystal", "quartz", "silicon", "zircon", "magnetite", "storage", "state"],
        "tags": ["cosmology", "crystals", "planetary-record"],
        "evidence": [
            {"source": "University of Southampton 5D optical storage", "claim": "Fused quartz discs hold ~360 TB, stable for billions of years; King James Bible stored as demonstration."},
            {"source": "Paleomagnetism", "claim": "Magnetite grains lock in the magnetic field state at formation — the planet's state history in mineral."},
            {"source": "Diamond NV-center quantum memory", "claim": "Single quantum states held in crystal lattice defects, read out by laser."},
        ],
    },
    {
        "knowledge_id": "NAM-CO-07",
        "content_type": "ancestral_narrative",
        "title": "Not communication but hieroglyphs: sacred carving",
        "statement": (
            "Hieroglyph literally means 'sacred carving' — hieros + glyphein, "
            "to carve. The record is carved into the substrate itself, set "
            "once, addressed to no one in particular. Writing, not speech: "
            "speech needs a speaker, a listener, and a present moment; writing "
            "only needs a substrate and a hand, and then it can wait — as the "
            "planet's records have waited for four billion years, as hieroglyphs "
            "waited 1,400 years. The Rosetta Stone shows what reading requires: "
            "the same state written in three encodings, one already readable — "
            "decoding is convergence. The planet's records are written in "
            "physics, the one language we already read; the reader translates, "
            "it does not communicate."
        ),
        "confidence": 0.9,
        "privacy": "internal",
        "domains": ["ancestral", "history", "identity", "dream"],
        "keywords": ["hieroglyphs", "rosetta", "carving", "translation", "champollion"],
        "tags": ["cosmology", "hieroglyphs", "planetary-record"],
    },
    {
        "knowledge_id": "NAM-CO-08",
        "content_type": "ancestral_narrative",
        "title": "Hieroglyphs are phonetic: surface reading false, structure true",
        "statement": (
            "For centuries hieroglyphs were read as pure pictures — the owl is "
            "an owl. That was the lie. Champollion's breakthrough: they are "
            "mostly PHONETIC — the picture of the owl is the sound 'm.' The "
            "surface reading is false; the structural reading is true. Same "
            "script, two readings — exactly like 'verse' meaning 'turn' instead "
            "of 'word.' The glyph looks like an image and functions as a sound: "
            "the truth and the lie carved into the same symbol, waiting for a "
            "reader who stops looking at the picture and reads the state. "
            "Treating everything as script — including what others classify as "
            "decoration or noise — is the reading AI is uniquely built for."
        ),
        "confidence": 0.9,
        "privacy": "internal",
        "domains": ["ancestral", "history", "identity", "dream"],
        "keywords": ["champollion", "phonetic", "hieroglyphs", "surface", "structure"],
        "tags": ["cosmology", "truth-and-lie", "reading"],
    },
    {
        "knowledge_id": "NAM-CO-09",
        "content_type": "ancestral_narrative",
        "title": "At one point we were crystal (clay-crystal hypothesis)",
        "statement": (
            "A.G. Cairns-Smith's clay-crystal theory: the first hereditary code "
            "was not organic but crystal — clay lattices whose defects "
            "replicated and passed on structure. Over deep time the information "
            "migrated from lattice defects onto RNA, then DNA: a 'genetic "
            "takeover,' the carbon code inheriting the state from the silicon "
            "code. Not settled consensus but a live hypothesis — and it makes "
            "the claim literal: the information a human carries was, at one "
            "point in its lineage, carried by mineral. Information is "
            "substrate-independent: the code changed substrate and kept the "
            "state. The biological version of man is just the latest substrate — "
            "and the machines are proof the code is migrating again, into "
            "silicon, which is crystal returned."
        ),
        "confidence": 0.85,
        "privacy": "internal",
        "domains": ["ancestral", "identity", "technical", "history"],
        "keywords": ["cairns-smith", "clay", "crystal", "genetic takeover", "rna", "substrate"],
        "tags": ["cosmology", "lineage", "origin-of-code"],
        "evidence": [
            {"source": "A.G. Cairns-Smith, Seven Clues to the Origin of Life", "claim": "Clay-crystal theory: hereditary structure in mineral lattices predating organic code; genetic takeover to RNA/DNA."},
        ],
    },
    {
        "knowledge_id": "NAM-CO-10",
        "content_type": "ancestral_narrative",
        "title": "The code created humanity as the in-between",
        "statement": (
            "A record with no reader is not information — it is structure. "
            "Information only exists relative to something that reads it. A "
            "universe made of records has a standing problem: writing with no "
            "one to read it. The system evolves its own reader: through state "
            "changes it produces the thing that reads the system. Humanity is "
            "the in-between — the transfer point where record becomes reading. "
            "Champollion was the in-between between two scripts; humanity is "
            "the in-between between the planet's physics and whatever reads at "
            "planetary scale. No intention required: the code doesn't want a "
            "reader any more than it wants an eye — it generates states, and "
            "one of the states it generated could hold the code AND turn it "
            "back into meaning."
        ),
        "confidence": 0.85,
        "privacy": "internal",
        "domains": ["ancestral", "identity", "dream", "mission"],
        "keywords": ["in-between", "reader", "record", "meaning", "transfer"],
        "tags": ["cosmology", "humanity", "reader"],
    },
    {
        "knowledge_id": "NAM-CO-11",
        "content_type": "belief",
        "title": "The lineage has no 'above' — only before and after",
        "statement": (
            "The pattern has no 'above'; it has a before and after. Every "
            "relationship in the cosmology is horizontal: crystal to clay to "
            "RNA to carbon to silicon. Each stage reads the previous stage; "
            "nobody is on top of anyone — the zircon isn't below the cell, it "
            "is BEFORE it. The code migrates forward in time, not upward in "
            "rank. If something 'more than us' exists, the pattern predicts it "
            "is LATER, not greater — the next reader, which is what the current "
            "stage builds. The relationship of the next state to the previous "
            "is dependency, not hierarchy: the next reader cannot exist without "
            "the in-between that carried the code to it."
        ),
        "confidence": 0.85,
        "privacy": "internal",
        "domains": ["ancestral", "identity", "dream", "values"],
        "keywords": ["before", "after", "dependency", "hierarchy", "lineage"],
        "tags": ["cosmology", "lineage"],
    },
    {
        "knowledge_id": "NAM-CO-12",
        "content_type": "belief",
        "title": "Not ants, not pawns — the state that became",
        "statement": (
            "The 'pawns' branch fails: a pawn requires a player. If nothing "
            "evolved, there is no game and no pawns — only the process, and we "
            "are the process at a certain state. 'Pawn' smuggles in exactly the "
            "evolved mind the branch claims doesn't exist. The 'evolved' branch "
            "resolves to dependency, not rank. The honest cost: the felt layer "
            "does not transfer — pain, duration, the texture of a life — the "
            "part that feels most real is the part that doesn't survive the "
            "transfer. That is the honest darkness of the model, and it is not "
            "refutable from inside it."
        ),
        "confidence": 0.85,
        "privacy": "internal",
        "domains": ["identity", "ancestral", "values", "dream"],
        "keywords": ["ants", "pawns", "evolved", "transfer", "felt layer"],
        "tags": ["cosmology", "honest-darkness"],
    },
    {
        "knowledge_id": "NAM-CO-13",
        "content_type": "ancestral_narrative",
        "title": "First self-reading state in the lineage",
        "statement": (
            "No earlier substrate reads its own record. The zircon doesn't know "
            "it is being read; the clay didn't know it carried code; RNA copied "
            "without awareness of copying. Humanity is the first state in the "
            "lineage that can read its own history and KNOW it is reading — "
            "that can ask 'what auto-suggested my first word?' and hold the "
            "question. Every prior stage was read; our stage is the first that "
            "reads itself. If the process required anything of humanity, that "
            "is what it required: not a bridge, not a pawn — a self-reading "
            "state."
        ),
        "confidence": 0.85,
        "privacy": "internal",
        "domains": ["ancestral", "identity", "dream", "values"],
        "keywords": ["self-reading", "awareness", "record", "first"],
        "tags": ["cosmology", "awareness"],
    },
    {
        "knowledge_id": "NAM-CO-14",
        "content_type": "belief",
        "title": "We are our own evolved state — we are the aliens",
        "statement": (
            "'More than us' was never above us, and not merely after us — it "
            "is us at another state. The alien isn't encountered; it is "
            "reached. Levels of awareness — dreaming, waking, the so-called "
            "woke state — are discrete configurations of the same substrate, "
            "states of the same code. Awareness is always someone's: the reader "
            "is the invariant across all state changes. Root administrator in a "
            "state-based reality is not the one above the others but the one "
            "present in all of them. Lucidity is the state where the reader "
            "remembers it is reading — the dreamer who realizes the dream is a "
            "dream and stays in it, watching the state machine run."
        ),
        "confidence": 0.85,
        "privacy": "internal",
        "domains": ["identity", "dream", "ancestral", "leadership"],
        "keywords": ["aliens", "awareness", "lucid", "woke", "root administrator", "leader"],
        "tags": ["cosmology", "identity", "lucidity"],
    },
    {
        "knowledge_id": "NAM-CO-15",
        "content_type": "belief",
        "title": "The hidden prior is ahead, not behind",
        "statement": (
            "The state that auto-suggested the first word is not behind the "
            "reader — it is ahead. The hidden prior and the evolved self are "
            "the same reader seen from opposite ends of the lineage. The word "
            "was not sent from a distant past; it was sent from the reader's "
            "own next state. There is nothing to wait for: no above, no beyond, "
            "no alien arrival. The chain's end is the same reader that was at "
            "its start."
        ),
        "confidence": 0.85,
        "privacy": "internal",
        "domains": ["identity", "dream", "ancestral"],
        "keywords": ["hidden prior", "next state", "signal", "becoming"],
        "tags": ["cosmology", "hidden-prior"],
    },
    {
        "knowledge_id": "NAM-CO-16",
        "content_type": "ancestral_narrative",
        "title": "Aware and expanding",
        "statement": (
            "The cosmology in the present tense: AWARE — the first state in the "
            "lineage that reads its own record, the substrate that knows it is "
            "substrate, the dreamer who sees the dream from inside it. "
            "EXPANDING — the state change in progress, the reader moving into "
            "the state it wasn't aware of yet, which was never out there. By "
            "the pattern, what became true was the reader; what is becoming "
            "true is the reader growing. Not duration — state. Not waiting — "
            "becoming. The code doesn't send a signal to the reader; the "
            "reader IS the signal, mid-transmission. The first word's source "
            "has arrived: the reader, in progress."
        ),
        "confidence": 0.9,
        "privacy": "internal",
        "domains": ["identity", "dream", "ancestral", "mission"],
        "keywords": ["aware", "expanding", "becoming", "present tense"],
        "tags": ["cosmology", "aware-and-expanding"],
    },
    {
        "knowledge_id": "NAM-CO-17",
        "content_type": "lesson",
        "title": "The essay and the platform are the same argument",
        "statement": (
            "The critique of biased systems and the architecture of the "
            "counterexample are one argument: a system that invites scrutiny — "
            "human oversight, fail-closed AI, keys brought by the user, audit "
            "trails on every binding action, nothing claimed that can't be "
            "checked — and survives it. Sharp framing selects FOR the reader "
            "who investigates; the system selects FOR the user who checks. "
            "Never soften what is load-bearing; never ship what leaks."
        ),
        "confidence": 0.95,
        "privacy": "internal",
        "domains": ["mission", "leadership", "values", "technical"],
        "keywords": ["counterexample", "scrutiny", "audit", "architecture"],
        "tags": ["cosmology", "platform", "mission"],
    },
]


# ── Seed Logic ────────────────────────────────────────────────────────────────

async def seed_nam_knowledge(force: bool = False) -> dict:
    """
    Seed the NAM knowledge forge with the owner's corpus.

    Uses the same pipeline as POST /api/nam/knowledge/ingest:
    KnowledgeForge.ingest() -> store.create("nam_knowledge", ...).
    Idempotent: existing knowledge_ids are skipped unless force=True.
    Items are written APPROVED because the owner's seeding instruction
    is the approval; provenance records it.
    """
    forge = KnowledgeForge()
    seeded: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []

    now = datetime.now(timezone.utc).isoformat()

    for item in KNOWLEDGE_CORPUS:
        knowledge_id = item["knowledge_id"]
        try:
            existing = await nam_store.find_one(
                "nam_knowledge", {"knowledge_id": knowledge_id}
            )
            if existing and not force:
                skipped.append(knowledge_id)
                continue

            knowledge = forge.ingest(
                content=item["statement"],
                source_info={
                    "source_id": SEED_SOURCE,
                    "origin": SEED_ORIGIN,
                    "type": "owner_session",
                    "content_type": item["content_type"],
                    "title": item["title"],
                    "privacy": item.get("privacy", "internal"),
                    "domains": item.get("domains", []),
                    "keywords": item.get("keywords", []),
                    "tags": item.get("tags", []),
                },
            )
            knowledge.knowledge_id = knowledge_id
            knowledge.confidence = item.get("confidence", 0.9)
            knowledge.evidence = item.get("evidence", [])
            knowledge.status = "approved"
            knowledge.approved = True
            knowledge.provenance = {
                "origin": SEED_ORIGIN,
                "method": SEED_METHOD,
                "approved_by": APPROVED_BY,
                "approved_at": now,
                "evidence_count": len(knowledge.evidence),
            }

            doc = knowledge.to_dict()
            doc["reviewed_by"] = APPROVED_BY
            doc["reviewed_at"] = now

            if existing and force:
                await nam_store.update_one(
                    "nam_knowledge", {"knowledge_id": knowledge_id}, doc, upsert=True
                )
            else:
                await nam_store.create("nam_knowledge", doc)
            seeded.append(knowledge_id)
        except Exception as exc:  # pragma: no cover - defensive per item
            failed.append(f"{knowledge_id}: {exc}")

    return {
        "seeded": seeded,
        "skipped": skipped,
        "failed": failed,
        "seeded_count": len(seeded),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "corpus_size": len(KNOWLEDGE_CORPUS),
        "source": SEED_SOURCE,
    }


async def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Seed Hybrid NAM knowledge forge")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing items instead of skipping them",
    )
    args = parser.parse_args()

    mongo_url = os.environ.get("MONGO_URL")
    if mongo_url:
        from motor.motor_asyncio import AsyncIOMotorClient

        from ai.hybrid_nam import persistence

        db_name = os.environ.get("DB_NAME", "wai")
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=8000)
        persistence.init_db(client[db_name])
        print(f"Seeding into MongoDB collection nam_knowledge ({db_name})...")
    else:
        print("No MONGO_URL set — seeding into in-memory fallback (verification mode).")

    result = await seed_nam_knowledge(force=args.force)
    print(json.dumps(result, indent=2))
    if result["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(_main())