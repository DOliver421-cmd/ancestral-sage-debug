"""Science — Grade 1 (published core, fills Grade 1 gaps: science)."""

SCIENCE_GRADE_1 = {
    "slug": "science-grade-1",
    "title": "Science — Grade 1",
    "summary": "Light and sound, plants and animals, and observing the sky.",
    "description": "First-grade science builds curiosity: how light and sound move, how plants and animals grow, and how to observe patterns in the sky.",
    "subject": "science",
    "subject_label": "Science",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["1"],
    "grade_label": "Grade 1",
    "status": "published",
    "audience": "Grade 1 (ages 6–7), Foundations track.",
    "est_hours": 14,
    "passing_score": 80,
    "learning_objectives": ["Describe how light and sound travel and are detected.", "Compare plant and animal needs and life cycles.", "Observe and describe patterns of the sun, moon, and stars."],
    "units": [
        {"slug": "light-and-sound", "title": "Light and Sound", "summary": "How we see and hear.", "order": 1, "lessons": [
            {"slug": "light-and-shadows", "title": "Light and Shadows", "order": 1, "minutes": 15, "summary": "Sources, reflections, and shadows.", "learn": [{"type": "p", "text": "Light travels in straight lines from a source — the sun, a lamp, or a screen. When light hits an object, it can reflect or make a shadow."}, {"type": "list", "items": ["Light source → object → eye.", "Shadows form where light is blocked.", "Mirrors reflect light."]}], "check": {"prompt": "Light basics.", "questions": [{"q": "What makes a shadow?", "options": ["light being blocked", "music playing", "water pouring"], "answer": "light being blocked", "explain": "An object blocks light and leaves a shadow."}, {"q": "Which reflects light?", "options": ["a mirror", "a cave", "a shadow"], "answer": "a mirror", "explain": "Mirrors reflect light."}]}},
            {"slug": "sound-and-vibration", "title": "Sound and Vibration", "order": 2, "minutes": 15, "summary": "How sound moves.", "learn": [{"type": "p", "text": "Sound is made by vibrations. A vibrating string or drum head pushes air, and our ears feel those pushes as sound."}, {"type": "activity", "title": "Feel sound", "text": "Tap a drum or table lightly. Place your hand nearby. Describe the vibration."}], "check": {"prompt": "Sound.", "questions": [{"q": "Sound is made by…", "options": ["vibrations", "colors", "silence"], "answer": "vibrations", "explain": "Vibrating matter makes sound."}, {"q": "We hear with our…", "options": ["ears", "feet", "hats"], "answer": "ears", "explain": "Ears detect sound vibrations."}]}},
        ]},
        {"slug": "plants-animals-sky", "title": "Plants, Animals, and Sky", "summary": "Needs, growth, and sky patterns.", "order": 2, "lessons": [
            {"slug": "plant-animal-needs", "title": "What Plants and Animals Need", "order": 3, "minutes": 15, "summary": "Food, water, air, light, and shelter.", "learn": [{"type": "p", "text": "Both plants and animals need air and water. Plants use sunlight to make food; animals find food. Parents and caregivers meet young needs so learners can grow."}, {"type": "list", "items": ["Plants: soil, water, sunlight, air.", "Animals: food, water, air, shelter.", "Young plants and animals grow and change."]}], "check": {"prompt": "Needs.", "questions": [{"q": "Which do both plants and animals need?", "options": ["water and air", "only sunlight", "only music"], "answer": "water and air", "explain": "Air and water are shared needs."}, {"q": "Which makes its own food with sunlight?", "options": ["a plant", "a rock", "a car"], "answer": "a plant", "explain": "Plants make food via photosynthesis."}]}},
            {"slug": "sky-patterns", "title": "Patterns in the Sky", "order": 4, "minutes": 15, "summary": "Sun, moon, and stars over time.", "learn": [{"type": "p", "text": "The sun rises in the east and sets in the west. The moon changes shape across nights, and stars shine at night. Observing patterns helps us tell time and navigate."}, {"type": "activity", "title": "Sky log", "text": "For 3 nights, draw the moon's shape. Compare your drawings."}], "check": {"prompt": "Sky patterns.", "questions": [{"q": "The sun rises in the…", "options": ["east", "north", "south"], "answer": "east", "explain": "The sun appears in the east at dawn."}, {"q": "When is the sky darkest?", "options": ["at night", "at noon", "at breakfast"], "answer": "at night", "explain": "Stars are visible when the sun is below the horizon."}]}},
        ]},
    ],
}
