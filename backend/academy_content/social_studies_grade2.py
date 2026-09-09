"""Social Studies — Grade 2 (published core, fills Grade 2 gap: social_studies)."""

SOCIAL_STUDIES_GRADE_2 = {
    "slug": "social-studies-grade-2",
    "title": "Social Studies — Grade 2",
    "summary": "Communities over time, maps, and citizenship.",
    "description": "Second-grade social studies examines how communities were, are, and can be — through maps, timelines, and stories of service.",
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["2"],
    "grade_label": "Grade 2",
    "status": "published",
    "audience": "Grade 2 (ages 7–8), Foundations track.",
    "est_hours": 14,
    "passing_score": 80,
    "learning_objectives": ["Use maps and timelines to show place and change over time.", "Describe community needs, services, and civic roles.", "Explain how traditions and histories shape communities."],
    "units": [
        {"slug": "maps-and-time", "title": "Maps and Time", "summary": "Place and change.", "order": 1, "lessons": [
            {"slug": "maps-and-places", "title": "Maps and Places", "order": 1, "minutes": 15, "summary": "Read simple maps.", "learn": [{"type": "p", "text": "A map uses symbols and a key. It shows where things are and how places connect — home to school to library to park."}, {"type": "list", "items": ["Title, key, compass rose.", "Symbols for buildings and roads.", "Directions help us travel safely."]}], "check": {"prompt": "Maps.", "questions": [{"q": "What tells you what a map symbol means?", "options": ["the map key", "the border", "the title only"], "answer": "the map key", "explain": "The key explains symbols."}, {"q": "Which tool shows direction on a map?", "options": ["compass rose", "glossary", "calendar"], "answer": "compass rose", "explain": "The compass rose shows north, south, east, west."}]}},
            {"slug": "timelines-then-and-now", "title": "Timelines: Then and Now", "order": 2, "minutes": 15, "summary": "Order events over time.", "learn": [{"type": "p", "text": "A timeline orders events from past to present. Looking at then and now helps us see how communities changed and what stayed caring."}, {"type": "activity", "title": "Family timeline", "text": "With a caregiver, place 4 family events on a line from earliest to now."}], "check": {"prompt": "Timelines.", "questions": [{"q": "A timeline shows…", "options": ["order of events over time", "only the present day", "only the future"], "answer": "order of events over time", "explain": "Timelines sequence past to present."}, {"q": "Which comes earlier?", "options": ["last year", "tomorrow", "next week"], "answer": "last year", "explain": "Last year is in the past."}]}},
        ]},
        {"slug": "citizenship", "title": "Citizenship and Service", "summary": "Rights, responsibilities, and helping.", "order": 2, "lessons": [
            {"slug": "being-a-good-citizen", "title": "Being a Good Citizen", "order": 3, "minutes": 15, "summary": "Rights and responsibilities.", "learn": [{"type": "p", "text": "Citizens have rights — to be safe, to learn, to be heard — and responsibilities — to be kind, to follow fair rules, to help others."}, {"type": "list", "items": ["Rights: safety, learning, voice.", "Responsibilities: care, honesty, participation."]}], "check": {"prompt": "Citizenship.", "questions": [{"q": "Which is a responsibility?", "options": ["helping a neighbor", "hiding from a neighbor", "taking without asking"], "answer": "helping a neighbor", "explain": "Citizenship includes service."}, {"q": "Rights include…", "options": ["being heard", "being ignored", "being silenced"], "answer": "being heard", "explain": "Voice is a right."}]}},
            {"slug": "community-services", "title": "Community Services", "order": 4, "minutes": 15, "summary": "How neighborhoods meet needs.", "learn": [{"type": "p", "text": "Services meet shared needs — library, health clinic, food market, transit. When services are fair and reachable, communities thrive."}, {"type": "list", "items": ["Goods vs services: goods are things, services are help.", "Libraries share knowledge for all.", "Health services care for bodies and minds."]}], "check": {"prompt": "Services.", "questions": [{"q": "A library provides…", "options": ["books and learning help", "only music videos", "only food"], "answer": "books and learning help", "explain": "Libraries are learning services."}, {"q": "Services should be…", "options": ["fair and reachable", "hidden and rare", "only for some"], "answer": "fair and reachable", "explain": "Shared services should serve everyone."}]}},
        ]},
    ],
}
