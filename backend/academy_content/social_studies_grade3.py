"""Social Studies — Grade 3 (published core)."""

SOCIAL_STUDIES_GRADE_3 = {
    "slug": "social-studies-grade-3",
    "title": "Social Studies — Grade 3",
    "summary": "Communities, culture, and how places connect.",
    "description": "Third-grade social studies explores local communities, cultural traditions, and how geography connects people and trade.",
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["3"],
    "grade_label": "Grade 3",
    "status": "published",
    "audience": "Grade 3 (ages 8–9), Foundations track.",
    "est_hours": 14,
    "passing_score": 80,
    "learning_objectives": ["Describe community and cultural traditions.", "Use maps to locate places and explain connections.", "Explain how people trade goods and services."],
    "units": [
        {"slug": "communities-culture", "title": "Communities and Culture", "summary": "Traditions and shared life.", "order": 1, "lessons": [
            {"slug": "cultures-and-traditions-grade3", "title": "Cultures and Traditions", "order": 1, "minutes": 15, "summary": "How communities honor heritage.", "learn": [{"type": "p", "text": "Culture includes food, music, stories, and celebrations. Traditions pass knowledge across generations and strengthen belonging."}, {"type": "list", "items": ["Name a tradition you love and why it matters.", "Celebrations honor history and hope."]}], "check": {"prompt": "Culture.", "questions": [{"q": "Culture includes…", "options": ["food, music, stories, celebrations", "only one game", "nothing shared"], "answer": "food, music, stories, celebrations", "explain": "Culture is shared practice."}, {"q": "Traditions…", "options": ["pass knowledge across generations", "are never shared", "hide history"], "answer": "pass knowledge across generations", "explain": "Traditions carry meaning."}]}},
            {"slug": "citizenship-grade3", "title": "Citizenship and Community", "order": 2, "minutes": 15, "summary": "Rights, rules, and service.", "learn": [{"type": "p", "text": "Citizens care for shared spaces and for each other. Good citizenship means listening, telling the truth, and helping set fair rules."}, {"type": "activity", "title": "Community helper", "text": "Interview a neighbor or helper. Ask how they serve the community."}], "check": {"prompt": "Citizenship.", "questions": [{"q": "Good citizenship includes…", "options": ["helping and following fair rules", "ignoring others", "breaking shared rules"], "answer": "helping and following fair rules", "explain": "Citizenship is care for the commons."}, {"q": "Fair rules…", "options": ["help everyone be safe", "hurt everyone", "are never fair"], "answer": "help everyone be safe", "explain": "Rules support safety."}]}},
        ]},
        {"slug": "geography-trade", "title": "Geography and Exchange", "summary": "Maps and trade.", "order": 2, "lessons": [
            {"slug": "maps-and-geography-grade3", "title": "Maps and Geography", "order": 3, "minutes": 15, "summary": "Reading maps to find places.", "learn": [{"type": "p", "text": "Maps show land, water, and where people live. A key, compass rose, and scale help us read them. Geography shapes how communities live and trade."}, {"type": "list", "items": ["Key explains symbols.", "Compass rose shows direction.", "Scale shows distance."]}], "check": {"prompt": "Maps.", "questions": [{"q": "The map key tells you…", "options": ["what symbols mean", "the book title", "the date"], "answer": "what symbols mean", "explain": "The key explains symbols."}, {"q": "Which shows direction?", "options": ["compass rose", "glossary", "calendar"], "answer": "compass rose", "explain": "It shows north, south, east, west."}]}},
            {"slug": "trade-and-exchange-grade3", "title": "Trade and Exchange", "order": 4, "minutes": 15, "summary": "Goods and services move.", "learn": [{"type": "p", "text": "People trade goods (things) and services (help). Historically, trade routes like those across Africa and the Americas moved knowledge as well as products."}, {"type": "list", "items": ["Goods are objects; services are actions.", "Trade connects communities.", "Fair trade respects makers and buyers."]}], "check": {"prompt": "Trade.", "questions": [{"q": "A service is…", "options": ["help someone provides", "only a toy", "only a rock"], "answer": "help someone provides", "explain": "Services are actions that help others."}, {"q": "Trade helps communities…", "options": ["connect and share", "stay isolated forever", "hide everything"], "answer": "connect and share", "explain": "Trade builds connections."}]}},
        ]},
    ],
}
