"""Social Studies — Grade 4 (published core)."""

SOCIAL_STUDIES_GRADE_4 = {
    "slug": "social-studies-grade-4",
    "title": "Social Studies — Grade 4",
    "summary": "Regions, state and community history, and civic life.",
    "description": "Fourth-grade social studies examines regions, state and community histories often left out of standard texts, and the civic tools that shape daily life.",
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["4"],
    "grade_label": "Grade 4",
    "status": "published",
    "audience": "Grade 4 (ages 9–10), Foundations track.",
    "est_hours": 14,
    "passing_score": 80,
    "learning_objectives": ["Describe regions and how geography shapes communities.", "Explain community and state histories including often-omitted perspectives.", "Identify civic roles and how rules affect fairness."],
    "units": [
        {"slug": "regions-history", "title": "Regions and History", "summary": "Place and past.", "order": 1, "lessons": [
            {"slug": "regions-and-geography-grade4", "title": "Regions and Geography", "order": 1, "minutes": 15, "summary": "Northeast, Southeast, Midwest, West.", "learn": [{"type": "p", "text": "Regions group places with shared land, climate, and ways of life. Geography shapes what communities grow, build, and trade."}, {"type": "list", "items": ["Northeast: coasts, cities, forests.", "Southeast: rivers, farms, Gulf waters.", "Midwest: plains and Great Lakes.", "West: mountains, deserts, Pacific coast."]}], "check": {"prompt": "Regions.", "questions": [{"q": "A region groups places with…", "options": ["shared land and climate", "only the same name", "no connection"], "answer": "shared land and climate", "explain": "Regions share physical and human traits."}, {"q": "Which is in the West?", "options": ["Pacific coast", "Atlantic coast only", "no coast"], "answer": "Pacific coast", "explain": "The West borders the Pacific."}]}},
            {"slug": "state-community-history-grade4", "title": "Our State and Community History", "order": 2, "minutes": 15, "summary": "Many voices, one timeline.", "learn": [{"type": "p", "text": "State and local histories include Indigenous presence, migration, labor, and organizing — not just founding dates. Learning the fuller story builds a stronger community identity."}, {"type": "activity", "title": "Local history note", "text": "Ask an elder or librarian: What is one local history you wish every child knew? Write one paragraph."}], "check": {"prompt": "History.", "questions": [{"q": "Good local history includes…", "options": ["many voices and sources", "only one voice", "no sources"], "answer": "many voices and sources", "explain": "History is fuller when many are heard."}, {"q": "Primary sources include…", "options": ["photos, letters, interviews", "only textbooks", "only guesses"], "answer": "photos, letters, interviews", "explain": "Primary sources come from the time."}]}},
        ]},
        {"slug": "civics-economy", "title": "Civics and Economy", "summary": "Rules and trade.", "order": 2, "lessons": [
            {"slug": "civic-roles-grade4", "title": "Civic Roles and Rules", "order": 3, "minutes": 15, "summary": "Government and fairness.", "learn": [{"type": "p", "text": "Civic roles include voting, jury service, and speaking at public meetings. Rules should be fair, transparent, and accountable to the people they affect."}, {"type": "list", "items": ["Local, state, and national levels serve different needs.", "Fair process matters as much as outcomes.", "Communities can propose and change rules."]}], "check": {"prompt": "Civics.", "questions": [{"q": "Civic participation includes…", "options": ["voting and speaking at meetings", "staying silent always", "breaking all rules"], "answer": "voting and speaking at meetings", "explain": "Participation shapes policy."}, {"q": "Fair rules are…", "options": ["transparent and accountable", "secret and unchecked", "only for some"], "answer": "transparent and accountable", "explain": "Fairness needs openness and accountability."}]}},
            {"slug": "goods-services-grade4", "title": "Goods and Services", "order": 4, "minutes": 15, "summary": "What communities make and share.", "learn": [{"type": "p", "text": "Goods are products; services are help. Markets, cooperatives, and mutual aid all organize how goods and services move. Understanding alternatives builds economic imagination."}, {"type": "list", "items": ["Goods: food, books, tools.", "Services: health care, teaching, transit.", "Co-ops share ownership and decisions."]}], "check": {"prompt": "Economy.", "questions": [{"q": "A service is…", "options": ["help someone provides for others", "only a thing you can hold", "never needed"], "answer": "help someone provides for others", "explain": "Teaching and health care are services."}, {"q": "Cooperatives…", "options": ["share ownership and decisions", "hide all decisions", "have only one owner always"], "answer": "share ownership and decisions", "explain": "Co-ops model shared power."}]}},
        ]},
    ],
}
