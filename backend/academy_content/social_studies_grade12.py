"""Social Studies Grade 12 — Civics & Economics (published core)."""
SOCIAL_STUDIES_GRADE_12 = {
    "slug": "social-studies-grade-12",
    "title": "Social Studies — Grade 12",
    "summary": "Civics, government, and economics for participation.",
    "description": "Grade 12 civics and economics prepare students to participate — how government works, how the economy allocates, and how communities build power.",
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["12"],
    "grade_label": "Grade 12",
    "status": "published",
    "audience": "Grade 12 (ages 17-18)",
    "est_hours": 24,
    "passing_score": 80,
    "learning_objectives": [
        "Explain constitutional structure and civic participation.",
        "Analyze how supply, demand, and institutions shape the economy.",
        "Evaluate policy choices and community strategies for well-being.",
    ],
    "units": [
        {"slug": "civics-grade12", "title": "Civics and Government", "summary": "Constitution and participation.", "order": 1, "lessons": [
            {"slug": "constitution-grade12", "title": "The Constitution", "order": 1, "minutes": 18, "summary": "Structure and rights.", "learn": [{"type": "p", "text": "The Constitution structures power into branches with checks and balances. The Bill of Rights and later amendments — including those won through Black freedom struggle — expand who 'we the people' includes."}], "check": {"prompt": "Constitution.", "questions": [{"q": "Checks and balances means", "options": ["branches limit each other", "one branch rules alone", "no government at all"], "answer": "branches limit each other", "explain": "Separation of powers."}]}},
            {"slug": "civic-participation-grade12", "title": "Civic Participation", "order": 2, "minutes": 18, "summary": "From voting to organizing.", "learn": [{"type": "p", "text": "Voting, petitioning, and organizing are complementary. Cooperative districts and mutual-aid histories show participation beyond the ballot — building institutions that last."}], "check": {"prompt": "Participation.", "questions": [{"q": "Effective civic participation includes", "options": ["voting plus organizing and institution-building", "only complaining online", "never voting"], "answer": "voting plus organizing and institution-building", "explain": "Multiple levers together."}]}},
        ]},
        {"slug": "economics-grade12", "title": "Economics", "summary": "Markets and community.", "order": 2, "lessons": [
            {"slug": "markets-grade12", "title": "Markets", "order": 3, "minutes": 18, "summary": "Supply, demand, and power.", "learn": [{"type": "p", "text": "Markets coordinate through supply and demand, but power shapes markets — who owns, who lends, who decides. Cooperative economics and Black Wall Street histories show alternative market designs."}], "check": {"prompt": "Markets.", "questions": [{"q": "When demand rises and supply is fixed, price tends to", "options": ["rise", "fall to zero", "stay unrelated"], "answer": "rise", "explain": "Scarcity pushes price up."}]}},
            {"slug": "policy-economics-grade12", "title": "Policy and Well-Being", "order": 4, "minutes": 18, "summary": "Fiscal and community policy.", "learn": [{"type": "p", "text": "Fiscal policy (spending, taxation) and monetary policy shape opportunity. Community measures — local ownership, credit unions, land trusts — translate policy into lived well-being."}], "check": {"prompt": "Policy.", "questions": [{"q": "A community land trust helps by", "options": ["keeping land affordable in collective stewardship", "only raising rents", "removing all housing"], "answer": "keeping land affordable in collective stewardship", "explain": "Collective ownership model."}]}},
        ]},
    ],
}
