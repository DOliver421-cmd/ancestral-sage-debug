"""Science — Grade 2 (full published course)."""

SCIENCE_GRADE_2 = {
    "slug": "science-grade-2",
    "title": "Science — Grade 2",
    "summary": "Plants and animals, matter, and earth's surface.",
    "description": (
        "Second-grade science explores the living and nonliving world. "
        "Students investigate plant and animal life cycles, the states of matter, "
        "and landforms and water on Earth. Hands-on observation and simple experiments "
        "help young scientists build vocabulary and reasoning skills."
    ),
    "subject": "science",
    "subject_label": "Science",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["2"],
    "grade_label": "Grade 2",
    "status": "published",
    "audience": "Grade 2 (ages 7–8), Foundations track.",
    "est_hours": 16,
    "passing_score": 80,
    "learning_objectives": [
        "Describe the life cycles of plants and animals.",
        "Identify properties of solids, liquids, and gases.",
        "Classify matter by observable properties.",
        "Identify major landforms and bodies of water.",
        "Understand how wind and water shape Earth's surface.",
    ],
    "units": [
        {
            "slug": "life-science",
            "title": "Life Science",
            "summary": "Plants, animals, and their habitats.",
            "order": 1,
            "lessons": [
                {
                    "slug": "plant-life-cycles",
                    "title": "Plant Life Cycles",
                    "order": 1,
                    "minutes": 15,
                    "summary": "From seed to flower to seed again.",
                    "learn": [
                        {"type": "p", "text": "Plants have a life cycle. Most flowering plants start as a seed. The seed grows roots, then a stem and leaves. The plant makes flowers, which produce new seeds. Then the cycle starts again."},
                        {"type": "list", "items": [
                            "Seed → germination (sprouting).",
                            "Seedling → adult plant.",
                            "Flower → pollination → seed.",
                            "Plants need sunlight, water, and soil to grow.",
                        ]},
                        {"type": "activity", "title": "Grow a bean", "text": "Put a bean seed in a clear cup with cotton and water. Watch it sprout over a week. Draw what you see each day."},
                    ],
                    "check": {
                        "prompt": "Show what you know about plant life cycles.",
                        "questions": [
                            {"q": "What does a seed need to grow?", "options": ["sunlight, water, and soil", "rocks and wind", "a computer"], "answer": "sunlight, water, and soil", "explain": "Plants need sunlight, water, and nutrients from soil to grow."},
                            {"q": "What is the first stage of a plant life cycle?", "options": ["seed", "flower", "fruit"], "answer": "seed", "explain": "The life cycle begins with a seed."},
                            {"q": "Which part of the plant often makes new seeds?", "options": ["the flower", "the root", "the leaf"], "answer": "the flower", "explain": "Flowers produce seeds after pollination."},
                        ],
                    },
                },
                {
                    "slug": "animal-life-cycles",
                    "title": "Animal Life Cycles",
                    "order": 2,
                    "minutes": 15,
                    "summary": "How animals grow and change.",
                    "learn": [
                        {"type": "p", "text": "Animals have life cycles too. Many animals look very different as babies than as adults. Think of a caterpillar turning into a butterfly — that is called metamorphosis."},
                        {"type": "list", "items": [
                            "Birds hatch from eggs and grow into adults.",
                            "Amphibians like frogs hatch from eggs into tadpoles.",
                            "Mammals are born live and grow into adults.",
                            "Metamorphosis means a big change in body form.",
                        ]},
                        {"type": "example", "title": "Butterfly metamorphosis", "text": "Egg → caterpillar (larva) → chrysalis (pupa) → butterfly (adult). Each stage looks completely different."},
                    ],
                    "check": {
                        "prompt": "Show what you know about animal life cycles.",
                        "questions": [
                            {"q": "What is metamorphosis?", "options": ["a big body change during a life cycle", "a type of rock", "a kind of plant"], "answer": "a big body change during a life cycle", "explain": "Metamorphosis means a dramatic change, like a caterpillar becoming a butterfly."},
                            {"q": "Which animal hatches from an egg and changes into an adult?", "options": ["a chicken", "a cat", "a dog"], "answer": "a chicken", "explain": "Chickens hatch from eggs and grow into adult chickens."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "earth-and-physical-science",
            "title": "Earth and Physical Science",
            "summary": "Matter, landforms, and water.",
            "order": 2,
            "lessons": [
                {
                    "slug": "states-of-matter",
                    "title": "Solids, Liquids, and Gases",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Identify properties of the three states of matter.",
                    "learn": [
                        {"type": "p", "text": "Everything around you is made of matter. Matter comes in three common states: solid, liquid, and gas. Solids hold their shape. Liquids flow and take the shape of their container. Gases spread out to fill a space."},
                        {"type": "list", "items": [
                            "Solid: rock, book, ice — has a fixed shape and volume.",
                            "Liquid: water, juice, honey — flows, has a fixed volume.",
                            "Gas: air, steam — has no fixed shape or volume.",
                            "Matter can change states when heated or cooled.",
                        ]},
                        {"type": "example", "title": "Water changes states", "text": "Ice (solid) melts into water (liquid). Water boils into steam (gas). Steam can condense back into water."},
                        {"type": "activity", "title": "Matter hunt", "text": "Find one solid, one liquid, and one gas in your home. Write them down. Could any change state with heat or cold?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about matter.",
                        "questions": [
                            {"q": "Which state of matter has a fixed shape?", "options": ["solid", "liquid", "gas"], "answer": "solid", "explain": "Solids keep their own shape. Liquids and gases take the shape of their container."},
                            {"q": "Water turning into steam is a change from…", "options": ["liquid to gas", "solid to liquid", "gas to liquid"], "answer": "liquid to gas", "explain": "When liquid water heats up, it becomes gas (steam)."},
                            {"q": "Which is an example of a liquid?", "options": ["milk", "a rock", "air"], "answer": "milk", "explain": "Milk flows and takes the shape of its container — it is a liquid."},
                        ],
                    },
                },
                {
                    "slug": "landforms-and-water",
                    "title": "Landforms and Water",
                    "order": 4,
                    "minutes": 15,
                    "summary": "Mountains, valleys, rivers, lakes, and oceans.",
                    "learn": [
                        {"type": "p", "text": "Earth's surface has many landforms. Some are made by forces inside Earth, like volcanoes and mountains. Others are shaped by wind and water over time."},
                        {"type": "list", "items": [
                            "Mountain: very high land.",
                            "Valley: low land between hills or mountains.",
                            "River: fresh water flowing downhill.",
                            "Lake: water surrounded by land.",
                            "Ocean: very large body of salt water.",
                        ]},
                        {"type": "example", "title": "Shaping the land", "text": "A river carves a canyon over thousands of years. Wind blows sand to make dunes. Rain can carve small gullies in dirt."},
                    ],
                    "check": {
                        "prompt": "Show what you know about landforms and water.",
                        "questions": [
                            {"q": "Which landform is low land between hills?", "options": ["valley", "mountain", "plateau"], "answer": "valley", "explain": "A valley sits between higher land such as hills or mountains."},
                            {"q": "What is the largest body of water on Earth?", "options": ["the ocean", "a lake", "a river"], "answer": "the ocean", "explain": "Oceans cover most of Earth's surface."},
                            {"q": "Which shapes land over time?", "options": ["wind and water", "books", "music"], "answer": "wind and water", "explain": "Wind and water slowly wear away rock and soil to shape landforms."},
                        ],
                    },
                },
            ],
        },
    ],
}
