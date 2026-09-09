"""Science — Grade 4 (published core)."""

SCIENCE_GRADE_4 = {
    "slug": "science-grade-4",
    "title": "Science — Grade 4",
    "summary": "Energy, sound, animals, and Earth's systems.",
    "description": "Fourth-grade science explores energy transfer, sound and light, structure and function in animals, and Earth's changing surface.",
    "subject": "science",
    "subject_label": "Science",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["4"],
    "grade_label": "Grade 4",
    "status": "published",
    "audience": "Grade 4 (ages 9–10), Foundations track.",
    "est_hours": 16,
    "passing_score": 80,
    "learning_objectives": ["Trace energy transfer in systems.", "Explain how sound and light are detected.", "Describe animal structures and Earth processes."],
    "units": [
        {"slug": "energy-waves", "title": "Energy and Waves", "summary": "Sound and light.", "order": 1, "lessons": [
            {"slug": "energy-transfer-grade4", "title": "Energy Transfer", "order": 1, "minutes": 18, "summary": "How energy moves and changes.", "learn": [{"type": "p", "text": "Energy moves from one place to another and can change form — electrical to light, chemical to motion. Collisions transfer energy and may make sound."}, {"type": "list", "items": ["Sun is the ultimate source for most Earth energy.", "A ball hit by a bat gains motion energy.", "Friction changes motion into heat."]}], "check": {"prompt": "Energy.", "questions": [{"q": "When objects collide, energy…", "options": ["can transfer between them", "disappears completely", "is only light"], "answer": "can transfer between them", "explain": "Collisions transfer energy and may create sound/heat."}, {"q": "Electrical energy can change into…", "options": ["light and heat", "only water", "nothing"], "answer": "light and heat", "explain": "A lamp changes electrical energy."}]}},
            {"slug": "sound-light-grade4", "title": "Sound and Light", "order": 2, "minutes": 15, "summary": "Waves we hear and see.", "learn": [{"type": "p", "text": "Sound is vibration traveling through matter. Light travels in straight lines; we see when light enters our eyes after reflecting off objects or coming from a source."}, {"type": "list", "items": ["Sound needs vibrating matter.", "Light reflects off objects to our eyes.", "Shadows form when light is blocked."]}], "check": {"prompt": "Waves.", "questions": [{"q": "Sound travels as…", "options": ["vibrations through matter", "light through empty space only", "nothing moving"], "answer": "vibrations through matter", "explain": "Vibrating matter pushes air."}, {"q": "We see an apple because…", "options": ["light reflects off the apple into our eyes", "the apple makes its own light", "eyes send out light"], "answer": "light reflects off the apple into our eyes", "explain": "Light travels from source to object to eye."}]}},
        ]},
        {"slug": "life-earth", "title": "Life and Earth Systems", "summary": "Animals and Earth's surface.", "order": 2, "lessons": [
            {"slug": "animal-structures-grade4", "title": "Animal Structures and Function", "order": 3, "minutes": 15, "summary": "How bodies help survival.", "learn": [{"type": "p", "text": "Animal parts have jobs — claws grip, wings lift, camouflage hides. Internal structures like skeletons support and protect."}, {"type": "example", "title": "Match structure to function", "text": "Camouflage helps prey hide; sharp teeth help predators catch food."}], "check": {"prompt": "Structures.", "questions": [{"q": "A structure's function is…", "options": ["what it does to help survival", "only its color", "never important"], "answer": "what it does to help survival", "explain": "Structure and function are linked."}, {"q": "Camouflage helps by…", "options": ["hiding an animal", "making it louder", "removing its habitat"], "answer": "hiding an animal", "explain": "It blends the animal with its surroundings."}]}},
            {"slug": "earth-changes-grade4", "title": "Earth's Surface Changes", "order": 4, "minutes": 15, "summary": "Weathering, erosion, and landforms.", "learn": [{"type": "p", "text": "Water, wind, and living things weather and erode Earth's surface. Rivers carve valleys; volcanoes build mountains. Maps show how land changes over time."}, {"type": "list", "items": ["Weathering breaks rock.", "Erosion moves sediment.", "Deposition builds new landforms."]}], "check": {"prompt": "Earth.", "questions": [{"q": "Erosion is…", "options": ["movement of sediment", "growth of plants only", "silence"], "answer": "movement of sediment", "explain": "Wind and water move broken rock and soil."}, {"q": "Which builds land?", "options": ["deposition", "only erosion", "only weathering"], "answer": "deposition", "explain": "Deposited sediment builds deltas and beaches."}]}},
        ]},
    ],
}
