"""Science — Grade 3 (published core, fills Grade 3 gap: science)."""

SCIENCE_GRADE_3 = {
    "slug": "science-grade-3",
    "title": "Science — Grade 3",
    "summary": "Forces, weather, and life cycles.",
    "description": "Third-grade science investigates pushes and pulls, weather and climate, and plant and animal life cycles.",
    "subject": "science",
    "subject_label": "Science",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["3"],
    "grade_label": "Grade 3",
    "status": "published",
    "audience": "Grade 3 (ages 8–9), Foundations track.",
    "est_hours": 16,
    "passing_score": 80,
    "learning_objectives": ["Describe balanced and unbalanced forces and motion.", "Observe and explain weather versus climate.", "Sequence life cycles and inherited traits."],
    "units": [
        {"slug": "forces-and-motion", "title": "Forces and Motion", "summary": "Push, pull, and change in motion.", "order": 1, "lessons": [
            {"slug": "forces-and-motion-grade3", "title": "Forces and Motion", "order": 1, "minutes": 18, "summary": "Balanced and unbalanced forces.", "learn": [{"type": "p", "text": "A force is a push or pull. Balanced forces keep motion the same; unbalanced forces change speed or direction. Friction slows things down."}, {"type": "list", "items": ["Balanced: two equal pulls — no change.", "Unbalanced: one pull wins — motion changes.", "Friction opposes sliding."]}], "check": {"prompt": "Forces.", "questions": [{"q": "An unbalanced force…", "options": ["changes motion", "never changes motion", "only makes sound"], "answer": "changes motion", "explain": "Unbalanced forces change speed or direction."}, {"q": "Friction…", "options": ["slows sliding", "speeds everything up", "only works on water"], "answer": "slows sliding", "explain": "Friction opposes motion."}]}},
            {"slug": "magnets-and-forces", "title": "Magnets and Forces", "order": 2, "minutes": 15, "summary": "Attract, repel, and distance.", "learn": [{"type": "p", "text": "Magnets pull some metals without touching. Like poles repel; opposite poles attract."}, {"type": "activity", "title": "Magnet test", "text": "Test 5 objects with a magnet. Sort into attracted vs not attracted."}], "check": {"prompt": "Magnets.", "questions": [{"q": "Magnets attract…", "options": ["some metals like iron", "all materials equally", "only wood"], "answer": "some metals like iron", "explain": "Only certain metals are magnetic."}, {"q": "Like magnetic poles…", "options": ["repel", "attract", "disappear"], "answer": "repel", "explain": "Like poles push apart; opposite poles pull."}]}},
        ]},
        {"slug": "weather-life", "title": "Weather, Climate, and Life Cycles", "summary": "Daily weather vs long-term climate; growth.", "order": 2, "lessons": [
            {"slug": "weather-vs-climate", "title": "Weather Versus Climate", "order": 3, "minutes": 15, "summary": "Today's weather vs years of patterns.", "learn": [{"type": "p", "text": "Weather is day-to-day conditions. Climate is the average weather in a place over many years. Measuring rain, temperature, and wind helps us see patterns."}, {"type": "list", "items": ["Weather: sunny today, rainy tomorrow.", "Climate: warm, wet summers year after year.", "Instruments: thermometer, rain gauge, wind vane."]}], "check": {"prompt": "Weather vs climate.", "questions": [{"q": "Weather is…", "options": ["day-to-day conditions", "the same every day forever", "only summer"], "answer": "day-to-day conditions", "explain": "Weather changes daily."}, {"q": "Climate describes…", "options": ["average weather over many years", "today's temperature only", "one storm"], "answer": "average weather over many years", "explain": "Climate is long-term pattern."}]}},
            {"slug": "life-cycles-and-traits", "title": "Life Cycles and Traits", "order": 4, "minutes": 15, "summary": "How living things grow and what they pass on.", "learn": [{"type": "p", "text": "Living things have life cycles — birth, growth, reproduction, and death. Some traits are inherited; some are learned."}, {"type": "example", "title": "Plant cycle", "text": "Seed -> sprout -> plant -> flower -> seed."}], "check": {"prompt": "Life cycles.", "questions": [{"q": "A life cycle shows…", "options": ["stages from birth to reproduction", "only the last stage", "only food"], "answer": "stages from birth to reproduction", "explain": "Life cycles include birth, growth, and reproduction."}, {"q": "An inherited trait is…", "options": ["passed from parents", "learned only at school", "random only"], "answer": "passed from parents", "explain": "Inherited traits come from parents."}]}},
        ]},
    ],
}
