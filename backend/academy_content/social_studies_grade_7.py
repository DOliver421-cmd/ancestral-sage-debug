"""Social Studies — Grade 7 (full published course)."""

SOCIAL_STUDIES_GRADE_7 = {
    "slug": "social-studies-grade-7",
    "title": "Social Studies — Grade 7",
    "summary": "World geography, cultures, trade, and human-environment interaction.",
    "description": (
        "Seventh-grade social studies explores how people live across the world. "
        "This course covers geography tools, world regions, cultural patterns, "
        "trade networks, and how humans adapt to and change their environments. "
        "Every lesson connects facts to thinking skills and a mastery check."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["7"],
    "grade_label": "Grade 7",
    "status": "published",
    "audience": "Grade 7 (ages 12–13), Foundations track.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": [
        "Use latitude, longitude, and map projections to locate places.",
        "Compare cultural patterns across world regions.",
        "Explain how trade routes connect economies and spread ideas.",
        "Analyze how humans adapt to and change environments.",
        "Evaluate sources of geographic information.",
    ],
    "units": [
        {
            "slug": "geography-tools",
            "title": "Geography Tools",
            "summary": "Maps, globes, and coordinate systems.",
            "order": 1,
            "lessons": [
                {
                    "slug": "latitude-and-longitude",
                    "title": "Latitude and Longitude",
                    "order": 2,
                    "minutes": 15,
                    "summary": "Read and write coordinates on a globe or map.",
                    "learn": [
                        {"type": "p", "text": "Latitude lines run east-west and measure distance north or south of the Equator. Longitude lines run north-south and measure distance east or west of the Prime Meridian. Coordinates are written (latitude, longitude)."},
                        {"type": "list", "items": [
                            "Equator = 0° latitude.",
                            "Prime Meridian = 0° longitude.",
                            "North Pole = 90° N. South Pole = 90° S.",
                            "Lines of latitude are also called parallels. Lines of longitude are meridians.",
                        ]},
                        {"type": "activity", "title": "Coordinate hunt", "text": "Find the coordinates of your city, the capital of your state, and the capital of a country in another hemisphere."},
                    ],
                    "check": {
                        "prompt": "Show what you know about latitude and longitude.",
                        "questions": [
                            {"q": "Lines that run east-west are…", "options": ["latitude", "longitude", "meridians"], "answer": "latitude", "explain": "Latitude lines run east-west."},
                            {"q": "The Prime Meridian is at…", "options": ["0° longitude", "0° latitude", "90° E"], "answer": "0° longitude", "explain": "The Prime Meridian is 0° longitude."},
                            {"q": "Coordinates are written as…", "options": ["(latitude, longitude)", "(longitude, latitude)", "x, y"], "answer": "(latitude, longitude)", "explain": "Standard order is latitude first, then longitude."},
                        ],
                    },
                },
                {
                    "slug": "map-projections",
                    "title": "Map Projections",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Understand why no flat map shows Earth perfectly.",
                    "learn": [
                        {"type": "p", "text": "Earth is a sphere, but maps are flat. Any flat map distorts shape, area, distance, or direction. The Mercator projection preserves direction but makes polar regions look larger than they are."},
                        {"type": "list", "items": [
                            "Distortion: stretching or shrinking parts of Earth.",
                            "Mercator: good for navigation, bad for size comparison.",
                            "Equal-area maps: show true size but warp shape near the poles.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about map projections.",
                        "questions": [
                            {"q": "Why does every flat map distort Earth?", "options": ["Because Earth is a sphere but the map is flat", "Because mapmakers make mistakes", "Because the oceans move"], "answer": "Because Earth is a sphere but the map is flat", "explain": "Flattening a curved surface always causes some distortion."},
                            {"q": "The Mercator projection is best for…", "options": ["navigation", "comparing country sizes", "showing polar ice"], "answer": "navigation", "explain": "Mercator preserves direction, which helps sailors."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "cultures-and-trade",
            "title": "Cultures and Trade",
            "summary": "Cultural patterns, trade routes, and diffusion.",
            "order": 4,
            "lessons": [
                {
                    "slug": "cultural-patterns",
                    "title": "Cultural Patterns",
                    "order": 5,
                    "minutes": 15,
                    "summary": "Identify the elements that make up a culture.",
                    "learn": [
                        {"type": "p", "text": "Culture is the shared way of life of a group of people. It includes language, religion, food, clothing, music, art, and traditions. Cultures change over time through contact with other groups."},
                        {"type": "list", "items": [
                            "Language connects people and preserves knowledge.",
                            "Religion shapes values, holidays, and daily routines.",
                            "Food, clothing, and shelter adapt to climate and resources.",
                            "Migration and trade spread cultural ideas.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about cultural patterns.",
                        "questions": [
                            {"q": "Culture includes…", "options": ["language, religion, and food", "only food and clothing", "only language"], "answer": "language, religion, and food", "explain": "Culture covers many shared elements of daily life."},
                            {"q": "Trade helps cultures by…", "options": ["spreading ideas and goods", "keeping them isolated", "removing language"], "answer": "spreading ideas and goods", "explain": "Trade connects people and allows cultural diffusion."},
                        ],
                    },
                },
                {
                    "slug": "trade-routes",
                    "title": "Trade Routes",
                    "order": 6,
                    "minutes": 15,
                    "summary": "How historic trade routes connected regions.",
                    "learn": [
                        {"type": "p", "text": "Trade routes are paths merchants follow to exchange goods. The Silk Road connected China to the Mediterranean. The Trans-Saharan routes connected West Africa to North Africa and Europe."},
                        {"type": "list", "items": [
                            "Goods: silk, spices, gold, salt, textiles.",
                            "Ideas: religion, technology, art, science.",
                            "Cities along routes grew rich and became cultural centers.",
                            "Disease could also spread along trade routes.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about trade routes.",
                        "questions": [
                            {"q": "The Silk Road connected…", "options": ["China to the Mediterranean", "Africa to South America", "Europe to Australia"], "answer": "China to the Mediterranean", "explain": "The Silk Road ran across Asia to the Mediterranean Sea."},
                            {"q": "Besides goods, trade routes spread…", "options": ["ideas and technology", "only weapons", "only food"], "answer": "ideas and technology", "explain": "Trade routes were highways for culture, religion, and technology too."},
                        ],
                    },
                },
            ],
        },
    ],
}
