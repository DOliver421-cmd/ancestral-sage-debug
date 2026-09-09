"""Science — Grade 6 (published core)."""

SCIENCE_GRADE_6 = {
    "slug": "science-grade-6",
    "title": "Science — Grade 6",
    "summary": "Matter, energy, ecosystems, and Earth in space.",
    "description": "Sixth-grade science connects matter and energy, ecosystem dynamics, and Earth-sun-moon systems with observation and modeling.",
    "subject": "science",
    "subject_label": "Science",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["6"],
    "grade_label": "Grade 6",
    "status": "published",
    "audience": "Grade 6 (ages 11–12), Foundations track.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": ["Model matter and energy flow in systems.", "Explain ecosystem patterns and human impacts.", "Describe Earth-sun-moon motions and seasons."],
    "units": [
        {"slug": "matter-energy", "title": "Matter and Energy", "summary": " particles, heat, and change.", "order": 1, "lessons": [
            {"slug": "matter-and-heat-grade6", "title": "Matter and Heat", "order": 1, "minutes": 18, "summary": "Particles and thermal energy.", "learn": [{"type": "p", "text": "Matter is made of particles. Adding heat makes particles move faster; removing heat slows them. Changes of state and dissolving are particle stories."}, {"type": "list", "items": ["Heat flows from warmer to cooler.", "Melting, freezing, evaporating are energy stories.", "Conservation: matter is not created or destroyed."]}], "check": {"prompt": "Matter and heat.", "questions": [{"q": "Adding heat to particles makes them…", "options": ["move faster", "stop moving", "grow larger forever"], "answer": "move faster", "explain": "Heat increases particle motion."}, {"q": "Melting is…", "options": ["solid to liquid", "liquid to gas only", "gas to solid only"], "answer": "solid to liquid", "explain": "Heat changes state."}]}},
            {"slug": "energy-in-systems-grade6", "title": "Energy in Systems", "order": 2, "minutes": 15, "summary": "Transfer and transformation.", "learn": [{"type": "p", "text": "Energy transfers when objects interact. In ecosystems and machines, energy transforms but total energy is conserved."}, {"type": "example", "title": "Food energy", "text": "Sun → plant (chemical) → animal (motion) → heat lost to surroundings."}], "check": {"prompt": "Energy.", "questions": [{"q": "Energy in a system…", "options": ["can transfer and transform", "always disappears", "is only light"], "answer": "can transfer and transform", "explain": "Energy changes form but is conserved."}, {"q": "Chemical energy in food originally came from…", "options": ["the sun", "the moon alone", "rocks only"], "answer": "the sun", "explain": "Plants capture sunlight."}]}},
        ]},
        {"slug": "ecosystems-space", "title": "Ecosystems and Space", "summary": "Living systems and the sky.", "order": 2, "lessons": [
            {"slug": "ecosystems-interactions-grade6", "title": "Ecosystem Interactions", "order": 3, "minutes": 15, "summary": "Food webs and human impact.", "learn": [{"type": "p", "text": "Ecosystems cycle matter and flow energy. Disruptions — new species, overharvest, warming — ripple through food webs. Community stewardship helps restore balance."}, {"type": "list", "items": ["Producers → consumers → decomposers.", "Invasive species can outcompete natives.", "Conservation protects biodiversity."]}], "check": {"prompt": "Ecosystems.", "questions": [{"q": "In a food web, decomposers…", "options": ["return nutrients to soil", "make light energy", "are not needed"], "answer": "return nutrients to soil", "explain": "They break down dead matter."}, {"q": "An invasive species…", "options": ["can disrupt native ecosystems", "always helps natives", "never changes a food web"], "answer": "can disrupt native ecosystems", "explain": "It may outcompete natives."}]}},
            {"slug": "earth-sun-moon-grade6", "title": "Earth, Sun, and Moon", "order": 4, "minutes": 15, "summary": "Motions and seasons.", "learn": [{"type": "p", "text": "Earth rotates daily and revolves yearly while tilted. The tilt creates seasons; the moon's orbit creates phases and eclipses. Observing the sky is ancient knowledge."}, {"type": "list", "items": ["Rotation: day/night.", "Revolution + tilt: seasons.", "Moon phases: new, crescent, quarter, gibbous, full."]}], "check": {"prompt": "Space.", "questions": [{"q": "Seasons happen because…", "options": ["Earth's axis is tilted as it revolves around the sun", "the sun moves closer only", "the moon blocks the sun daily"], "answer": "Earth's axis is tilted as it revolves around the sun", "explain": "Tilt changes sunlight angle."}, {"q": "A full moon appears when…", "options": ["we see the fully lit face", "the moon is new", "the sun is behind Earth forever"], "answer": "we see the fully lit face", "explain": "Full moon is fully illuminated face."}]}},
        ]},
    ],
}
