"""Science Grade 12 — Environmental & Earth Systems (published core)."""
SCIENCE_GRADE_12 = {
    "slug": "science-grade-12",
    "title": "Science — Grade 12",
    "summary": "Environmental science, climate, and earth systems with community stewardship.",
    "description": "Grade 12 environmental science integrates ecology, climate, and earth systems — with attention to community health and stewardship practices.",
    "subject": "science",
    "subject_label": "Science",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["12"],
    "grade_label": "Grade 12",
    "status": "published",
    "audience": "Grade 12 (ages 17-18)",
    "est_hours": 22,
    "passing_score": 80,
    "learning_objectives": [
        "Explain ecosystem dynamics and biodiversity.",
        "Interpret climate data and earth-system feedbacks.",
        "Evaluate stewardship choices for community health.",
    ],
    "units": [
        {"slug": "ecology-grade12", "title": "Ecology", "summary": "Systems and biodiversity.", "order": 1, "lessons": [
            {"slug": "ecosystems-grade12", "title": "Ecosystems", "order": 1, "minutes": 18, "summary": "Flows and cycles.", "learn": [{"type": "p", "text": "Ecosystems move energy from producers to consumers and cycle nutrients. Biodiversity increases resilience — a lesson visible in African agroforestry that polyculture sustains yield."}], "check": {"prompt": "Ecosystems.", "questions": [{"q": "Producers are", "options": ["organisms that make food from sunlight", "only predators", "only parasites"], "answer": "organisms that make food from sunlight", "explain": "They form the base of food webs."}]}},
            {"slug": "biodiversity-grade12", "title": "Biodiversity", "order": 2, "minutes": 18, "summary": "Why variety matters.", "learn": [{"type": "p", "text": "Biodiversity is the variety of life. Higher diversity stabilizes systems against shocks — a principle for both ecology and community economics."}], "check": {"prompt": "Biodiversity.", "questions": [{"q": "Higher biodiversity generally", "options": ["increases resilience", "always harms resilience", "has no effect"], "answer": "increases resilience", "explain": "More pathways buffer shocks."}]}},
        ]},
        {"slug": "climate-stewardship-grade12", "title": "Climate and Stewardship", "summary": "Data and choice.", "order": 2, "lessons": [
            {"slug": "climate-grade12", "title": "Climate and Earth Systems", "order": 3, "minutes": 18, "summary": "Feedbacks and data.", "learn": [{"type": "p", "text": "Climate is driven by greenhouse gases, ocean circulation, and land use. Feedback loops — ice albedo, permafrost methane — can amplify change. Local data and satellite imagery together tell the story."}], "check": {"prompt": "Climate.", "questions": [{"q": "A feedback loop that amplifies warming is", "options": ["ice melt lowering albedo", "planting trees", "collecting data"], "answer": "ice melt lowering albedo", "explain": "Less ice reflects less sunlight."}]}},
            {"slug": "stewardship-grade12", "title": "Stewardship", "order": 4, "minutes": 18, "summary": "Community practice.", "learn": [{"type": "p", "text": "Stewardship is active care — water catchment, soil health, and mutual-aid response networks. Traditional ecological knowledge and modern monitoring combine for durable solutions."}], "check": {"prompt": "Stewardship.", "questions": [{"q": "Stewardship emphasizes", "options": ["active care for land and community", "passive waiting", "only individual gain"], "answer": "active care for land and community", "explain": "Care is a practice."}]}},
        ]},
    ],
}
