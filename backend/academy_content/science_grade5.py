"""Science — Grade 5 (full published course)."""

SCIENCE_GRADE_5 = {
    "slug": "science-grade-5",
    "title": "Science — Grade 5",
    "summary": "Matter and energy, ecosystems, and earth systems.",
    "description": (
        "Fifth-grade science connects the very small to the very large. This course "
        "starts with the structure of matter and energy, moves into ecosystems and "
        "food webs, and finishes with earth's systems — water, weather, and planets. "
        "Every lesson includes hands-on thinking and a mastery check."
    ),
    "subject": "science",
    "subject_label": "Science",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["5"],
    "grade_label": "Grade 5",
    "status": "published",
    "audience": "Grade 5 (ages 10–11), Foundations track; works for any curious learner.",
    "est_hours": 20,
    "passing_score": 80,
    "learning_objectives": [
        "Describe matter as something made of tiny particles too small to see.",
        "Explain how energy transfers and transforms.",
        "Identify producers, consumers, and decomposers in an ecosystem.",
        "Trace the flow of energy through a food web.",
        "Describe how water moves through Earth's systems.",
        "Explain how the Sun's energy drives weather and the water cycle.",
    ],
    "units": [
        {
            "slug": "matter-and-energy",
            "title": "Matter and Energy",
            "summary": "Particles, states of matter, and energy changes.",
            "order": 1,
            "lessons": [
                {
                    "slug": "what-is-matter",
                    "title": "What Is Matter?",
                    "order": 2,
                    "minutes": 15,
                    "summary": "Understand that all material things are made of matter.",
                    "learn": [
                        {"type": "p", "text": "Matter is anything that has mass and takes up space. Your desk, the air, and your water bottle are all matter. Matter is made of tiny particles — atoms and molecules — too small to see."},
                        {"type": "list", "items": [
                            "Mass: how much matter is in something.",
                            "Volume: how much space matter takes up.",
                            "Atoms are the basic particles of matter.",
                            "Molecules are atoms joined together.",
                        ]},
                        {"type": "activity", "title": "Matter hunt", "text": "Find three solids, two liquids, and one gas in the room. Name the matter and guess whether it is made of atoms."},
                    ],
                    "check": {
                        "prompt": "Show what you know about matter.",
                        "questions": [
                            {"q": "Which is NOT matter?", "options": ["sunlight", "rock", "water"], "answer": "sunlight", "explain": "Sunlight is energy, not matter. Rock and water have mass and volume."},
                            {"q": "Matter is made of tiny particles called…", "options": ["atoms", "clouds", "colors"], "answer": "atoms", "explain": "Atoms are the basic particles of matter."},
                            {"q": "Volume measures…", "options": ["how much space something takes up", "how heavy something is", "how fast something moves"], "answer": "how much space something takes up", "explain": "Volume is a measure of space."},
                        ],
                    },
                },
                {
                    "slug": "states-of-matter",
                    "title": "States of Matter",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Identify solids, liquids, and gases and how they change.",
                    "learn": [
                        {"type": "p", "text": "Most matter on Earth is solid, liquid, or gas. Solids hold their shape. Liquids take the shape of their container. Gases spread to fill their container."},
                        {"type": "list", "items": [
                            "Solid: particles close together in a fixed arrangement.",
                            "Liquid: particles close but free to slide past each other.",
                            "Gas: particles far apart and moving fast.",
                            "Melting = solid → liquid. Freezing = liquid → solid.",
                        ]},
                        {"type": "activity", "title": "Ice melt", "text": "Place an ice cube in a bowl. Observe it melting. Draw the water level and label the state change."},
                    ],
                    "check": {
                        "prompt": "Show what you know about states of matter.",
                        "questions": [
                            {"q": "Which state has particles that slide past each other?", "options": ["liquid", "solid", "gas"], "answer": "liquid", "explain": "Liquid particles stay close but can move around."},
                            {"q": "When ice melts, it changes from…", "options": ["solid to liquid", "liquid to gas", "gas to solid"], "answer": "solid to liquid", "explain": "Melting turns a solid into a liquid."},
                            {"q": "A gas…", "options": ["fills its container", "holds its shape", "sinks to the bottom"], "answer": "fills its container", "explain": "Gas particles spread out to fill all available space."},
                        ],
                    },
                },
                {
                    "slug": "energy-transfers",
                    "title": "Energy Transfers",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Trace how energy moves and changes form.",
                    "learn": [
                        {"type": "p", "text": "Energy is the ability to cause change. It moves from place to place and can change form. The Sun is the main energy source for Earth's systems."},
                        {"type": "list", "items": [
                            "Light energy from the Sun warms the land and water.",
                            "Plants change light energy into stored chemical energy (food).",
                            "Animals get energy by eating plants or other animals.",
                            "Energy can transfer as heat, light, or motion.",
                        ]},
                        {"type": "example", "title": "Energy chain", "text": "Sun → plant (photosynthesis) → rabbit (eats plant) → fox (eats rabbit). Energy flows through the food chain."},
                    ],
                    "check": {
                        "prompt": "Show what you know about energy transfers.",
                        "questions": [
                            {"q": "The main energy source for Earth is…", "options": ["the Sun", "wind", "rocks"], "answer": "the Sun", "explain": "The Sun provides light and heat energy that drives Earth's systems."},
                            {"q": "Plants change light energy into…", "options": ["stored chemical energy (food)", "motion", "sound"], "answer": "stored chemical energy (food)", "explain": "Photosynthesis stores sunlight in the bonds of glucose."},
                            {"q": "A fox eating a rabbit gets energy from…", "options": ["the rabbit's food", "the Sun directly", "the soil"], "answer": "the rabbit's food", "explain": "Energy moves through the food chain: Sun → plants → animals."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "ecosystems",
            "title": "Ecosystems",
            "summary": "Food webs, energy flow, and matter cycles.",
            "order": 5,
            "lessons": [
                {
                    "slug": "food-webs",
                    "title": "Food Webs",
                    "order": 6,
                    "minutes": 15,
                    "summary": "Trace who eats whom and why it matters.",
                    "learn": [
                        {"type": "p", "text": "An ecosystem includes all living things and their physical environment. A food web shows how energy flows as one organism eats another. Producers make their own food. Consumers eat other organisms."},
                        {"type": "list", "items": [
                            "Producers (plants) capture energy from the Sun.",
                            "Herbivores eat plants.",
                            "Carnivores eat other animals.",
                            "Decomposers break down dead organisms and return nutrients.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about food webs.",
                        "questions": [
                            {"q": "Which organism makes its own food?", "options": ["producer", "consumer", "decomposer"], "answer": "producer", "explain": "Producers such as plants capture energy from the Sun."},
                            {"q": "A rabbit eating grass is a…", "options": ["herbivore", "carnivore", "decomposer"], "answer": "herbivore", "explain": "Herbivores eat plants."},
                            {"q": "Decomposers return…", "options": ["nutrients to the soil", "energy to the Sun", "water to the sky"], "answer": "nutrients to the soil", "explain": "Decomposers break down dead material so nutrients can be reused."},
                        ],
                    },
                },
                {
                    "slug": "water-cycle",
                    "title": "The Water Cycle",
                    "order": 7,
                    "minutes": 15,
                    "summary": "Follow water as it moves through Earth's systems.",
                    "learn": [
                        {"type": "p", "text": "The water cycle moves water between the atmosphere, land, and oceans. The Sun's energy drives evaporation, and gravity pulls water back down as precipitation."},
                        {"type": "list", "items": [
                            "Evaporation: liquid water becomes water vapor (gas).",
                            "Condensation: water vapor cools into liquid (clouds).",
                            "Precipitation: water falls as rain, snow, sleet, or hail.",
                            "Collection: water gathers in rivers, lakes, and oceans.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about the water cycle.",
                        "questions": [
                            {"q": "Evaporation is when liquid water becomes…", "options": ["water vapor", "ice", "rain"], "answer": "water vapor", "explain": "Evaporation turns liquid into gas."},
                            {"q": "Clouds form during…", "options": ["condensation", "evaporation", "precipitation"], "answer": "condensation", "explain": "Condensation turns water vapor back into liquid drops."},
                            {"q": "What drives the water cycle?", "options": ["the Sun's energy", "the Moon's gravity", "wind only"], "answer": "the Sun's energy", "explain": "The Sun provides the energy for evaporation."},
                        ],
                    },
                },
            ],
        },
    ],
}
