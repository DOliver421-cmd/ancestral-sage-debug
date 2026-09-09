"""Science — Kindergarten (published core, fills K gap: science)."""

SCIENCE_KINDERGARTEN = {
    "slug": "science-kindergarten",
    "title": "Science — Kindergarten",
    "summary": "Observe, ask, and explore — living things, weather, and the sky above.",
    "description": "Kindergarten science invites young learners to look closely at the world: plants and animals, weather and seasons, and the sun, moon, and stars that guide community life.",
    "subject": "science",
    "subject_label": "Science",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["K"],
    "grade_label": "Kindergarten",
    "status": "published",
    "audience": "Kindergarten (ages 5–6), Foundations track.",
    "est_hours": 14,
    "passing_score": 80,
    "learning_objectives": ["Describe what living things need to grow.", "Compare weather and seasons through observation.", "Identify the sun, moon, and stars and how they help us."],
    "units": [
        {"slug": "living-things", "title": "Living Things Around Us", "summary": "Plants, animals, and what they need.", "order": 1, "lessons": [
            {"slug": "what-living-things-need", "title": "What Living Things Need", "order": 1, "minutes": 15, "summary": "Food, water, air, light, and space.", "learn": [{"type": "p", "text": "Living things grow and change. Plants need soil, water, sunlight, and air. Animals and people need food, water, air, and shelter. Families and gardens both thrive when their needs are met."}, {"type": "list", "items": ["Plants: soil, water, sunlight, air.", "Animals: food, water, air, shelter.", "People: food, water, air, home, care."]}], "check": {"prompt": "What do living things need?", "questions": [{"q": "Which do plants need to grow?", "options": ["sunlight and water", "only rocks", "only music"], "answer": "sunlight and water", "explain": "Plants need soil, water, sunlight, and air."}, {"q": "Which is a living thing?", "options": ["a bean plant", "a chair", "a cup"], "answer": "a bean plant", "explain": "A plant grows and needs care."}]}},
            {"slug": "plants-and-animals", "title": "Plants and Animals Nearby", "order": 2, "minutes": 15, "summary": "Name parts and sort by traits.", "learn": [{"type": "p", "text": "Look closely: roots hold a plant in soil, stems carry water, leaves make food from sunlight, and flowers can become fruit. Animals have different coverings and movements — fur, feathers, scales."}, {"type": "activity", "title": "Neighborhood walk", "text": "Draw one plant and one animal you see. Label one part of each."}], "check": {"prompt": "Parts and traits.", "questions": [{"q": "Which part makes food for a plant?", "options": ["leaves", "flowers", "soil"], "answer": "leaves", "explain": "Leaves use sunlight to make food."}, {"q": "Which covering belongs to a bird?", "options": ["feathers", "scales", "fur"], "answer": "feathers", "explain": "Birds have feathers."}]}},
        ]},
        {"slug": "sky-and-weather", "title": "Sky and Weather", "summary": "Sun, moon, stars, and seasons.", "order": 2, "lessons": [
            {"slug": "sun-moon-stars", "title": "Sun, Moon, and Stars", "order": 3, "minutes": 15, "summary": "What we see in the day and night sky.", "learn": [{"type": "p", "text": "The sun warms the day. The moon and stars shine at night. For generations, families have used the sky to mark time, tell stories, and find direction."}, {"type": "list", "items": ["Day sky: sun, clouds.", "Night sky: moon, stars.", "The sun gives light and heat."]}], "check": {"prompt": "Sky above.", "questions": [{"q": "What gives us light and heat in the day?", "options": ["the sun", "the moon", "a cloud"], "answer": "the sun", "explain": "The sun is our closest star."}, {"q": "When do you see stars best?", "options": ["at night", "at noon", "indoors"], "answer": "at night", "explain": "Stars shine when the sky is dark."}]}},
            {"slug": "weather-and-seasons", "title": "Weather and Seasons", "order": 4, "minutes": 15, "summary": "Observe and describe weather.", "learn": [{"type": "p", "text": "Weather is what the sky is doing today — sunny, cloudy, rainy, or windy. Seasons change slowly and bring different clothing, foods, and celebrations."}, {"type": "activity", "title": "Weather journal", "text": "For 5 days, draw the sky and write one word: sunny, cloudy, rainy, windy."}], "check": {"prompt": "Weather basics.", "questions": [{"q": "Which word describes weather?", "options": ["rainy", "sleepy", "quickly"], "answer": "rainy", "explain": "Rainy describes sky conditions."}, {"q": "Which season is usually warmest where you live?", "options": ["summer", "winter", "it is never warm"], "answer": "summer", "explain": "Summer is typically the warmest season."}]}},
        ]},
    ],
}
