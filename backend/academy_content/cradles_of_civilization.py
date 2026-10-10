"""Grade 3 ELA & Social Studies: Cradles of Civilization (published).

Grade 3 social studies reframed as the study of early civilizations across the
world — with Kemet (Ancient Egypt) and Nubia/Kush at the center rather than
footnoted, and pre-colonial global trade networks including the Indus Valley
and Mesoamerica. Reading and writing are integrated: students read primary
sources, compare civilizations, and write explanatory paragraphs.
"""

CRADLES_OF_CIVILIZATION = {
    "slug": "cradles-of-civilization",
    "title": "Cradles of Civilization: Nile Valley, Indus, and Mesoamerica",
    "summary": "Kemet, Nubia, Harappa, and Tenochtitlan — the first great civilisations and the trade that linked them.",
    "description": (
        "Instead of a generic survey of 'early communities', Grade 3 studies the world's "
        "great civilisations on equal footing. Kemet (Ancient Egypt) and Nubia/Kush "
        "receive sustained attention, with the Nile Valley presented as the African "
        "cradle it was. The Indus Valley cities of Harappa and Mohenjo-daro, and "
        "Mesoamerican cities such as Teotihuacan and Tenochtitlan, are compared with "
        "them — geography, writing, government, and long-distance trade. The course "
        "teaches reading of primary sources and short informational writing as an "
        "integrated ELA skill."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies · ELA",
    "track": "foundations",
    "tracks": ["foundations", "scholar"],
    "grades": ["3"],
    "grade_label": "Grade 3",
    "status": "published",
    "audience": "Grade 3 students studying early civilizations with integrated literacy.",
    "est_hours": 24,
    "passing_score": 80,
    "learning_objectives": [
        "Locate Kemet, Nubia/Kush, the Indus Valley, and Mesoamerica on a map.",
        "Explain how rivers enabled the first civilizations.",
        "Describe Nubia/Kush as an independent power that was not merely Egypt's neighbour.",
        "Compare writing systems across three civilizations.",
        "Explain how long-distance trade moved goods and ideas before 1500 BCE.",
        "Read a short primary source and summarize what it shows.",
        "Write an informational paragraph with a topic sentence and two facts.",
    ],
    "units": [
        {
            "slug": "nile-valley-civilizations",
            "title": "The Nile Valley: Kemet and Nubia",
            "summary": "Two African civilizations, one river.",
            "order": 1,
            "lessons": [
                {
                    "slug": "kemet-gift-of-the-nile",
                    "title": "Kemet: The Gift of the Nile",
                    "order": 1,
                    "minutes": 22,
                    "summary": "How a river cycle built a civilization — and why it is called Black Land.",
                    "learn": [
                        {"type": "p", "text": "Kemet — the ancient name for Egypt — means 'Black Land', named for the dark soil left behind after the Nile's yearly flood. The Greeks later called it Aigyptos and the English 'Egypt'. Its people called themselves and their land Kemet, and it sat in eastern Africa."},
                        {"type": "list", "items": [
                            "The Nile floods each summer, leaving silt that fertilizes fields — a predictable food supply allowed specialization.",
                            "Farmers, scribes, priests, and builders could each focus on one craft.",
                            "The 365-day calendar, geometry for land measurement, and arithmetic were practical needs turned into mathematics.",
                        ]},
                        {"type": "example", "title": "Primary source", "text": "The Greek historian Herodotus, visiting in the 5th century BCE, called Egypt 'the gift of the Nile'. Scientists have since dated early agriculture in the Nile Valley to before 7000 BCE."},
                        {"type": "activity", "title": "Map it", "text": "Draw the Nile flowing north. Label Upper Egypt in the south, Lower Egypt in the north, Nubia below, and the delta at the top."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Kemet.",
                        "questions": [
                            {"q": "'Kemet' means…", "options": ["'Black Land', for the fertile flood soil", "'Golden Kingdom'", "'City of Priests'"], "answer": "'Black Land', for the fertile flood soil", "explain": "It is named for the dark silt the Nile leaves after flooding."},
                            {"q": "The yearly Nile flood helped civilization grow because it…", "options": ["produced a reliable food surplus", "kept people from trading", "made travel impossible"], "answer": "produced a reliable food surplus", "explain": "Predictable farming allowed people to specialize in other work."},
                        ],
                    },
                },
                {
                    "slug": "nubia-kush",
                    "title": "Nubia/Kush: A Kingdom of Its Own",
                    "order": 2,
                    "minutes": 22,
                    "summary": "South of Egypt was not 'lesser Egypt' — it was Kush.",
                    "learn": [
                        {"type": "p", "text": "South of Egypt lay Nubia, home to the civilization of Kush. Later historical writing treated Kush as a poor cousin of Egypt, but the evidence says otherwise: Kush had its own writing system (Meroitic), its own capital cities, and its own iron industry. Kush was the African power that at one point ruled Egypt itself."},
                        {"type": "list", "items": [
                            "Kerma (c. 2500 BCE): a walled city with palaces and a huge tomb tradition.",
                            "Napata and Meroë: Kushite capitals that controlled trade south into Africa and gold eastward.",
                            "Meroitic script: an African alphabet still only partly deciphered, written in two forms.",
                        ]},
                        {"type": "example", "title": "The 25th Dynasty", "text": "In the 8th century BCE the Kushite king Piye conquered northward and ruled Egypt as the 25th Dynasty. Kushite royalty were pharaohs — the power ran south to north, not only north to south."},
                        {"type": "tip", "text": "Textbooks used to say Kush 'copied' Egypt. Its own script, religion, and trade position make it an independent African civilization."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Kush.",
                        "questions": [
                            {"q": "Meroitic is the name of…", "options": ["Kush's own writing system", "an Egyptian pyramid", "a Nubian city wall"], "answer": "Kush's own writing system", "explain": "Meroitic is an African script from the Kushite city of Meroë."},
                            {"q": "The 25th Dynasty is important because…", "options": ["Kushite kings ruled Egypt", "Egypt fell to Rome", "Kush was empty"], "answer": "Kushite kings ruled Egypt", "explain": "Kush expanded north and its royalty became pharaohs of Egypt."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "indus-and-mesoamerica",
            "title": "Indus Valley and Mesoamerica",
            "summary": "Across the world, other great cities were rising.",
            "order": 2,
            "lessons": [
                {
                    "slug": "indus-valley",
                    "title": "The Indus Valley: Harappa and Mohenjo-daro",
                    "order": 3,
                    "minutes": 22,
                    "summary": "Planned cities, brick sewers, and an undeciphered script.",
                    "learn": [
                        {"type": "p", "text": "Around 2600 BCE, in what is now Pakistan and northwest India, cities such as Harappa and Mohenjo-daro rose along the Indus River and its tributaries. They were built on a grid of right-angle streets, with standardised bricks and covered drains — urban engineering far ahead of its time."},
                        {"type": "list", "items": [
                            "Grid streets and standard brick sizes suggest central planning.",
                            "Covered sewers and public baths show city-scale water engineering.",
                            "Seals with animal images and short scripts remain one of the world's undeciphered writing systems.",
                        ]},
                        {"type": "example", "title": "Compare", "text": "Kemet left pyramids and temples; the Indus cities left urban plumbing. Civilizations face different problems and so excel at different things."},
                        {"type": "activity", "title": "Write a comparison", "text": "Write one paragraph comparing the Indus Valley and Kemet: topic sentence, two facts, closing sentence."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the Indus cities.",
                        "questions": [
                            {"q": "Harappa and Mohenjo-daro were built with…", "options": ["grid streets and covered drains", "giant pyramids", "underground caves"], "answer": "grid streets and covered drains", "explain": "Their planning is remarkable for its date — roughly 4500 years ago."},
                            {"q": "The Indus script is still…", "options": ["undeciphered", "fully read by everyone", "not real"], "answer": "undeciphered", "explain": "The seals' short inscriptions have not yet been conclusively translated."},
                        ],
                    },
                },
                {
                    "slug": "mesoamerican-cities",
                    "title": "Mesoamerica: Teotihuacan and Tenochtitlan",
                    "order": 4,
                    "minutes": 22,
                    "summary": "Cities of the Americas before Columbus.",
                    "learn": [
                        {"type": "p", "text": "Teotihuacan in today's Mexico was one of the largest cities in the world around 450 CE, laid out along a long avenue between two great pyramids. Three hundred years later the Mexica built Tenochtitlan on an island in Lake Texcoco, with canals, causeways, floating gardens, and an aqueduct bringing fresh water."},
                        {"type": "list", "items": [
                            "Teotihuacan: the Pyramid of the Sun and Moon, housing for many cultures, mural art.",
                            "Chinampas: floating garden beds that produced several harvests a year.",
                            "Tenochtitlan's Spanish visitors described a city larger and cleaner than most in Europe.",
                        ]},
                        {"type": "tip", "text": "'Native American' history is often taught as beginning with European arrival. These cities were hundreds of years old before any European ship crossed."},
                        {"type": "activity", "title": "Draw a city", "text": "Draw a map of Tenochtitlan with its causeways and canals, labeling chinampa farms and the aqueduct."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Mesoamerican cities.",
                        "questions": [
                            {"q": "Tenochtitlan was built…", "options": ["on an island in Lake Texcoco", "in the Andes mountains", "on the coast of Florida"], "answer": "on an island in Lake Texcoco", "explain": "It was an island city connected by causeways, with canal transport."},
                            {"q": "Chinampas were…", "options": ["floating garden beds", "stone weapons", "golden masks"], "answer": "floating garden beds", "explain": "They were raised garden plots that produced high crop yields."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "trade-before-1500",
            "title": "Trade Before 1500 BCE",
            "summary": "Long-distance networks that carried goods and ideas.",
            "order": 3,
            "lessons": [
                {
                    "slug": "pre-colonial-trade",
                    "title": "Pre-Colonial Trade Networks",
                    "order": 5,
                    "minutes": 22,
                    "summary": "Africa, Asia, and the Americas traded long before Europeans sailed.",
                    "learn": [
                        {"type": "p", "text": "Thousands of years before the European 'age of exploration', the Old World was already linked. Caravans crossed the Sahara carrying gold, salt, and slaves. Indian Ocean dhows carried textiles and spices between East Africa, Arabia, India, and Southeast Asia. The Americas had their own networks, including the river routes of the Mississippi and the Andean road systems."},
                        {"type": "list", "items": [
                            "Trans-Saharan caravans: gold, salt, and manuscripts moved between West Africa and the Mediterranean.",
                            "Indian Ocean trade: Swahili, Arab, Gujarati, and Malay sailors shared monsoon navigation.",
                            "Intercontinental goods: glass beads, copper, iron, ivory, and ceramics travel these routes.",
                        ]},
                        {"type": "example", "title": "Routes carry ideas", "text": "Writing systems, religions, and crops travelled along the same roads as cargo. Trade moves culture as well as goods."},
                        {"type": "activity", "title": "Trace a good", "text": "Pick one good (gold, salt, iron, or glass). Draw the route it might take across three regions and label the cities."},
                    ],
                    "check": {
                        "prompt": "Check what you know about early trade.",
                        "questions": [
                            {"q": "Before 1500, the Sahara was crossed by…", "options": ["caravans carrying gold, salt, and manuscripts", "railway trains", "jet planes"], "answer": "caravans carrying gold, salt, and manuscripts", "explain": "Camel caravans linked West Africa to the Mediterranean world."},
                            {"q": "Trade routes carried goods and also…", "options": ["ideas, religions, and crops", "nothing else", "only coins"], "answer": "ideas, religions, and crops", "explain": "Routes move culture as well as cargo."},
                        ],
                    },
                },
                {
                    "slug": "reading-primary-sources",
                    "title": "Reading a Primary Source",
                    "order": 6,
                    "minutes": 22,
                    "summary": "Capstone: read closely, then write what you learned.",
                    "learn": [
                        {"type": "p", "text": "A primary source is something made at the time being studied — a seal, a wall carving, a city plan, a coin. Reading one closely means describing what you can see, then reasoning about what it tells you. A secondary source is made later, like a textbook written today."},
                        {"type": "list", "items": [
                            "Look: list what is actually there — shapes, animals, letters, numerals.",
                            "Think: what did people need in order to make this?",
                            "Write: an informational paragraph with one topic sentence and two facts.",
                        ]},
                        {"type": "example", "title": "Practice", "text": "Look at an Indus seal: a bull, a line of symbols, a unicorn figure. What could it be used for? Marking ownership of traded goods is one strong hypothesis."},
                        {"type": "activity", "title": "Write it up", "text": "Choose one civilization from this course. Write a five-sentence paragraph: topic sentence, three facts, closing sentence. Read it aloud to someone."},
                    ],
                    "check": {
                        "prompt": "Check what you know about sources.",
                        "questions": [
                            {"q": "A primary source is…", "options": ["something made at the time being studied", "a modern summary of the past", "always a book"], "answer": "something made at the time being studied", "explain": "Primary sources come from the period itself: carvings, coins, plans, seals."},
                            {"q": "A good informational paragraph has…", "options": ["a topic sentence, facts, and a closing", "only questions", "no sentences"], "answer": "a topic sentence, facts, and a closing", "explain": "It opens by naming the topic, supports it with facts, and closes it."},
                        ],
                    },
                },
            ],
        },
    ],
}
