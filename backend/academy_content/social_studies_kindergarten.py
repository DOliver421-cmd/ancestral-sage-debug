"""Social Studies — Kindergarten (published core, fills K gap: social_studies)."""

SOCIAL_STUDIES_KINDERGARTEN = {
    "slug": "social-studies-kindergarten",
    "title": "Social Studies — Kindergarten",
    "summary": "Family, community, helpers, and how we care for each other.",
    "description": "Kindergarten social studies starts with the communities children know — family, classroom, neighborhood — and the helpers and traditions that hold them together.",
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["K"],
    "grade_label": "Kindergarten",
    "status": "published",
    "audience": "Kindergarten (ages 5–6), Foundations track.",
    "est_hours": 14,
    "passing_score": 80,
    "learning_objectives": ["Describe family and classroom communities and rules that help us.", "Name community helpers and how they serve.", "Recognize traditions, celebrations, and ways we honor each other."],
    "units": [
        {"slug": "belonging", "title": "Belonging and Community", "summary": "Families, classrooms, and neighborhoods.", "order": 1, "lessons": [
            {"slug": "families-and-classrooms", "title": "Families and Classrooms", "order": 1, "minutes": 15, "summary": "People and roles at home and school.", "learn": [{"type": "p", "text": "A community is a group of people who live, learn, or work together. Your family and your classroom are your first communities. Each person has a role and a responsibility."}, {"type": "list", "items": ["Family roles: caregivers, children, elders.", "Classroom roles: learners, helpers, leaders.", "Rules help communities stay safe and fair."]}], "check": {"prompt": "Communities and roles.", "questions": [{"q": "Which is a community?", "options": ["a family", "a single chair", "a cloud"], "answer": "a family", "explain": "A community is people who care for each other."}, {"q": "Why do classrooms have rules?", "options": ["to keep everyone safe and fair", "to make the day longer", "to hide the books"], "answer": "to keep everyone safe and fair", "explain": "Rules help a community work together."}]}},
            {"slug": "community-helpers", "title": "Community Helpers", "order": 2, "minutes": 15, "summary": "Who helps the neighborhood thrive?", "learn": [{"type": "p", "text": "Community helpers keep neighborhoods safe and thriving — firefighters, teachers, grocers, healers, and elders who guide. When we thank helpers, we strengthen community bonds."}, {"type": "activity", "title": "Helper interview", "text": "Thank a helper you know. Ask one question: How do you help our community? Draw their answer."}], "check": {"prompt": "Helpers.", "questions": [{"q": "Which helper teaches children to read?", "options": ["a teacher", "a ladder", "a truck"], "answer": "a teacher", "explain": "Teachers guide learning."}, {"q": "Helpers are important because they…", "options": ["serve the community", "never speak", "stay home alone"], "answer": "serve the community", "explain": "Helpers serve needs together."}]}},
        ]},
        {"slug": "traditions", "title": "Traditions and Celebrations", "summary": "Stories, holidays, and heritage.", "order": 2, "lessons": [
            {"slug": "traditions-and-celebrations", "title": "Traditions and Celebrations", "order": 3, "minutes": 15, "summary": "Honoring heritage and sharing joy.", "learn": [{"type": "p", "text": "Traditions are practices we repeat with care — gatherings, foods, music, stories. Celebrations honor history and bring generations together."}, {"type": "list", "items": ["Name one family tradition and why it matters.", "Name one community celebration and who it honors.", "Sharing traditions builds pride and belonging."]}], "check": {"prompt": "Traditions.", "questions": [{"q": "A tradition is…", "options": ["a practice repeated with care across time", "a single loud noise", "a forgotten note"], "answer": "a practice repeated with care across time", "explain": "Traditions carry meaning across generations."}, {"q": "Why share celebrations?", "options": ["to honor history and build community", "to hide from neighbors", "to make the day shorter"], "answer": "to honor history and build community", "explain": "Celebrations strengthen belonging."}]}},
            {"slug": "rules-and-fairness", "title": "Rules and Fairness", "order": 4, "minutes": 15, "summary": "Making fair choices together.", "learn": [{"type": "p", "text": "Fair rules give everyone a chance to be heard and safe. We can make rules together and change them when needed."}, {"type": "activity", "title": "Fair rule", "text": "Write one rule for a game you play. Explain how it is fair to everyone."}], "check": {"prompt": "Fairness.", "questions": [{"q": "A fair rule…", "options": ["gives everyone a chance", "helps only one person", "cannot be changed"], "answer": "gives everyone a chance", "explain": "Fairness means shared opportunity."}, {"q": "Who can help make a rule fair?", "options": ["everyone affected", "no one", "only one person alone"], "answer": "everyone affected", "explain": "Listening to those affected makes rules better."}]}},
        ]},
    ],
}
