"""Social Studies — Grade 1 (published core, fills Grade 1 gap: social_studies)."""

SOCIAL_STUDIES_GRADE_1 = {
    "slug": "social-studies-grade-1",
    "title": "Social Studies — Grade 1",
    "summary": "Families, communities, leaders, and how we help one another.",
    "description": "First-grade social studies explores families and communities, helpers and leaders, and traditions that honor heritage and service.",
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["1"],
    "grade_label": "Grade 1",
    "status": "published",
    "audience": "Grade 1 (ages 6–7), Foundations track.",
    "est_hours": 14,
    "passing_score": 80,
    "learning_objectives": ["Compare families and communities and their needs.", "Identify helpers and leaders who serve with care.", "Describe traditions that celebrate heritage."],
    "units": [
        {"slug": "families-communities", "title": "Families and Communities", "summary": "Needs, rules, and togetherness.", "order": 1, "lessons": [
            {"slug": "families-needs-and-rules", "title": "Families, Needs, and Rules", "order": 1, "minutes": 15, "summary": "Shared needs and fair rules.", "learn": [{"type": "p", "text": "Families meet needs — food, shelter, care, learning. Communities share needs too: clean water, safe streets, good schools. Fair rules help everyone thrive."}, {"type": "list", "items": ["Needs: food, shelter, learning, safety.", "Wants: extra treats and toys.", "Rules protect people and property."]}], "check": {"prompt": "Needs and rules.", "questions": [{"q": "Which is a need?", "options": ["clean water", "a new video game", "extra candy"], "answer": "clean water", "explain": "Water is needed for life."}, {"q": "Fair rules…", "options": ["help everyone be safe", "hurt everyone equally", "are never discussed"], "answer": "help everyone be safe", "explain": "Rules support safety and fairness."}]}},
            {"slug": "helpers-and-leaders", "title": "Helpers and Leaders", "order": 2, "minutes": 15, "summary": "Who serves and how we thank them.", "learn": [{"type": "p", "text": "Helpers and leaders serve — teachers, nurses, grocers, faith leaders, elders. Leadership means listening, telling the truth, and caring for the most vulnerable."}, {"type": "activity", "title": "Thank-you note", "text": "Write a thank-you note to a helper or leader you admire. Name one action they take for others."}], "check": {"prompt": "Helpers and leaders.", "questions": [{"q": "A community helper…", "options": ["serves neighbors", "hides from neighbors", "takes without giving"], "answer": "serves neighbors", "explain": "Helpers meet community needs."}, {"q": "Good leadership includes…", "options": ["listening and caring for the vulnerable", "never listening", "only caring for oneself"], "answer": "listening and caring for the vulnerable", "explain": "Leadership is service."}]}},
        ]},
        {"slug": "traditions-heritage", "title": "Traditions and Heritage", "summary": "Stories and celebrations.", "order": 2, "lessons": [
            {"slug": "traditions-heritage-celebration", "title": "Traditions, Heritage, and Celebration", "order": 3, "minutes": 15, "summary": "Honoring past and practicing pride.", "learn": [{"type": "p", "text": "Traditions carry memory — foods, songs, stories, gatherings. Heritage is the story of who we come from and how we carry their strength forward."}, {"type": "list", "items": ["Share a tradition your family loves.", "Name one community celebration and its meaning."]}], "check": {"prompt": "Heritage.", "questions": [{"q": "Heritage means…", "options": ["the story of who we come from", "a single game", "only a holiday"], "answer": "the story of who we come from", "explain": "Heritage connects past and present."}, {"q": "Celebrations help us…", "options": ["honor history and community", "forget history", "stay silent"], "answer": "honor history and community", "explain": "We gather to remember and rejoice."}]}},
            {"slug": "maps-and-neighborhood", "title": "Maps and Our Neighborhood", "order": 4, "minutes": 15, "summary": "Directions and places.", "learn": [{"type": "p", "text": "A map shows places from above. Neighborhood maps show homes, schools, parks, and stores. Directions help us navigate with care."}, {"type": "list", "items": ["Map symbols: home, school, park, store.", "Directions: north, south, east, west.", "Landmarks help us find our way."]}], "check": {"prompt": "Maps.", "questions": [{"q": "A map shows places from…", "options": ["above", "below", "inside a book only"], "answer": "above", "explain": "Maps are bird's-eye views."}, {"q": "Which direction is opposite north?", "options": ["south", "east", "north"], "answer": "south", "explain": "South is opposite north."}]}},
        ]},
    ],
}
