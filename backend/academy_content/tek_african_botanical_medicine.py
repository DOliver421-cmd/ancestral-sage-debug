"""Grade 10 Science: Traditional Ecological Knowledge & African Botanical Medicine (published).

Grade 10 biology and chemistry grounded in African and diaspora science:
ethnobotany, agricultural innovation (including rice cultivation methods
enslaved West Africans brought and built), and sustainable land management
— presented as knowledge systems with methods, not as folklore.
"""

TEK_AFRICAN_BOTANICAL_MEDICINE = {
    "slug": "tek-african-botanical-medicine",
    "title": "Traditional Ecological Knowledge (TEK) & African Botanical Medicine",
    "summary": "Ethnobotany, African agricultural innovation, and the science of sustainable land management.",
    "description": (
        "This Grade 10 science course teaches chemistry and biology through African "
        "and diaspora knowledge systems. Students study ethnobotany — how plant "
        "knowledge is tested and transmitted; the agricultural engineering of West "
        "African and enslaved farmers who built the rice economy of the American South "
        "on techniques from the Senegal–Gambia basin; the life and science of George "
        "Washington Carver; and the soil, water, and forestry practices that sustained "
        "African agrarian societies for centuries. All of it is taught with the same "
        "rigor as any standard science: hypothesis, evidence, replication, transmission."
    ),
    "subject": "science",
    "subject_label": "Science",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["10"],
    "grade_label": "Grade 10",
    "status": "published",
    "audience": "Grade 10 biology and chemistry students studying ethnobotany and agricultural science.",
    "est_hours": 28,
    "passing_score": 80,
    "learning_objectives": [
        "Define traditional ecological knowledge and describe how it is transmitted and tested.",
        "Describe the methods ethnobotanists use to identify plant compounds.",
        "Explain how West African rice cultivation techniques built the South Atlantic rice economy.",
        "Describe the role of enslaved African rice builders in South Carolina and Georgia.",
        "Explain George Washington Carver's crop rotation and chemistry work.",
        "Analyze sustainable land management: soil, water, and agroforestry.",
        "Evaluate plant knowledge with the scientific method, including controls and replication.",
    ],
    "units": [
        {
            "slug": "ethnobotany",
            "title": "Ethnobotany: The Science of Plant Knowledge",
            "summary": "How people learn what plants do, and how science studies that learning.",
            "order": 1,
            "lessons": [
                {
                    "slug": "what-ethnobotany-is",
                    "title": "What Ethnobotany Is",
                    "order": 1,
                    "minutes": 26,
                    "summary": "A field with methods, not a collection of folklore.",
                    "learn": [
                        {"type": "p", "text": "Ethnobotany studies how peoples identify, classify, cultivate, and use plants — and how that knowledge is held and tested across generations. African taxonomies often distinguish plants European systems group together, based on use, habitat, or season. Naming is not decoration: a name like 'plant for fever that grows near standing water' carries a real classification."},
                        {"type": "list", "items": [
                            "Classification by use, habitat, and seasonal behavior.",
                            "Knowledge held by specialists: herbalists, farmers, birth attendants.",
                            "Transmission: apprenticeship, ritual instruction, and recorded trace.",
                        ]},
                        {"type": "example", "title": "Case study", "text": "The anti-sickle-cell compound appears in plants of West African pharmacopoeias that had long been used for blood disorders — knowledge that modern screening programms then validated chemically."},
                        {"type": "tip", "text": "'It was always used' is the start of an ethnobotanical inquiry, not the end of one. A claim is tested by extraction, dosing, and controls."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of ethnobotany.",
                        "questions": [
                            {"q": "Ethnobotany is a discipline that studies…", "options": ["human plant knowledge and its testing", "only ancient myths", "fossils only"], "answer": "human plant knowledge and its testing", "explain": "It examines how knowledge is formed, classified, and verified."},
                            {"q": "A plant claim from traditional knowledge should be…", "options": ["tested by extraction, dosing, and controls", "accepted without evidence", "ignored automatically"], "answer": "tested by extraction, dosing, and controls", "explain": "Traditional claims are research leads, confirmed or refuted experimentally."},
                        ],
                    },
                },
                {
                    "slug": "plant-chemistry",
                    "title": "Plant Chemistry and Bioactivity",
                    "order": 2,
                    "minutes": 26,
                    "summary": "From leaf to compound.",
                    "learn": [
                        {"type": "p", "text": "Plants make chemicals to defend themselves, signal, and attract. Those compounds — alkaloids, terpenoids, glycosides — are what traditional medicine uses, and what a laboratory isolates. African pharmacopoeias have supplied the world with compounds including ouabain, physostigmine, and derivatives used in heart and eye medicine, and many of today's anti-malarial drug lines trace back to cinchona and to Artemisia annua, whose use in China parallels African antimalarial plants."},
                        {"type": "list", "items": [
                            "Alkaloids: often act on the nervous system; include caffeine, quinine, physostigmine.",
                            "Terpenoids: scents, resins, and anti-inflammatories.",
                            "Extraction methods: water decoction, alcohol tincture, steam distillation.",
                        ]},
                        {"type": "example", "title": "Modern link", "text": "Strophanthus seed extract contains ouabain, used as a cardiac stimulant; it entered Western medicine through African traditional use documented by botanists."},
                        {"type": "activity", "title": "Titration lab", "text": "Steep one plant, test an indicator strip for pH, and record the result. Note how a healer's brewed tea is an administered dose with a concentration."},
                    ],
                    "check": {
                        "prompt": "Check what you know about plant chemistry.",
                        "questions": [
                            {"q": "Alkaloids are compounds that often…", "options": ["act on the nervous system", "make plants grow taller", "attract only humans"], "answer": "act on the nervous system", "explain": "Many alkaloids affect nerves, which is why they are pharmacologically active."},
                            {"q": "An ethnobotanical lead becomes scientific fact through…", "options": ["controlled experiments and dosage testing", "longer tradition alone", "old photographs"], "answer": "controlled experiments and dosage testing", "explain": "Tradition identifies candidates; experiment establishes effects."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "african-agricultural-science",
            "title": "Agricultural Science: Rice, Rotation, and Soil",
            "summary": "Engineering in the field, not only in the laboratory.",
            "order": 2,
            "lessons": [
                {
                    "slug": "rice-engineers",
                    "title": "The African Rice Builders",
                    "order": 3,
                    "minutes": 26,
                    "summary": "Techniques from the Senegal–Gambia basin made South Carolina's wealth.",
                    "learn": [
                        {"type": "p", "text": "The rice economy of South Carolina and Georgia was built on methods brought by enslaved Africans from the Senegal–Gambia basin and the Sierra Leone coast: precise tidal irrigation, field grading, mortar-and-pestle milling, and winnowing. Plantation records show planters paid extra for Africans from rice regions, and auction advertisements named specific ethnicities as 'rice hands'. The knowledge was the skill being purchased."},
                        {"type": "list", "items": [
                            "Tidal irrigation: fields graded so river water could flood and drain on schedule.",
                            "Dikes, trunks (gates), and canals engineered without modern surveying tools.",
                            "Banks and drying: paddy field drainage controlled to raise yields.",
                        ]},
                        {"type": "example", "title": "Proof by price", "text": "Prices for enslaved people advertised as 'born in Gambia' or 'of the Rice Coast' were higher specifically for rice skill — a record of African technical knowledge recognized by the slavers' own ledgers."},
                        {"type": "activity", "title": "Model a field", "text": "Draw an elevation cross-section of a tidal rice field: river, trunk, canal, field bank, drainage ditch. Label where water enters and leaves."},
                    ],
                    "check": {
                        "prompt": "Check what you know about African rice cultivation.",
                        "questions": [
                            {"q": "Planters paid more for Africans from the Rice Coast because…", "options": ["they brought rice-growing technique", "they had gold", "they spoke English"], "answer": "they brought rice-growing technique", "explain": "The skills of tidal irrigation and milling were the asset being valued."},
                            {"q": "Tidal rice irrigation requires engineering…", "options": ["graded fields with controlled water in and out", "no water at all", "mountain terraces"], "answer": "graded fields with controlled water in and out", "explain": "Water is managed by gravity through trunks and banks."},
                        ],
                    },
                },
                {
                    "slug": "carver-and-soil",
                    "title": "Carver, Crop Rotation, and Soil Chemistry",
                    "order": 4,
                    "minutes": 26,
                    "summary": "Fixing nitrogen by farming well.",
                    "learn": [
                        {"type": "p", "text": "George Washington Carver, born into slavery and one of America's great agricultural chemists, restored soils depleted by cotton by rotating in peanuts, cowpeas, and sweet potatoes. Legumes host bacteria in root nodules that fix nitrogen from the air into the soil — a process he promoted as a system, publishing bulletins teaching farmers how to use it. He also developed hundreds of products from peanuts and sweet potatoes to create markets for the new crops."},
                        {"type": "list", "items": [
                            "Cotton depletes nitrogen; legumes restore it via root-nodule bacteria.",
                            "Crop rotation reduces pests and rebuilds organic matter.",
                            "A new crop needs a market — Carver's bulletins supplied recipes and uses.",
                        ]},
                        {"type": "example", "title": "Chemistry", "text": "Nitrogen fixation converts atmospheric N2 into ammonia in the nodule — the single largest natural input of usable nitrogen to soils on Earth."},
                        {"type": "activity", "title": "Design a rotation", "text": "Plan a four-year rotation for a field that grows cotton: list the crops, why each follows the last, and what happens to the soil each year."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of crop rotation.",
                        "questions": [
                            {"q": "Nitrogen fixation happens in…", "options": ["root nodules of legumes with bacteria", "the leaves of cotton", "pure desert sand"], "answer": "root nodules of legumes with bacteria", "explain": "Symbiotic bacteria in nodules convert atmospheric nitrogen into a usable form."},
                            {"q": "Carver's crop rotation solved the problem of…", "options": ["soils depleted by cotton", "no sun for crops", "too much rain"], "answer": "soils depleted by cotton", "explain": "Monoculture cotton stripped nitrogen; legumes restored it."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "sustainable-land-management",
            "title": "Sustainable Land Management",
            "summary": "Agroforestry, water, and soil conservation as engineered systems.",
            "order": 3,
            "lessons": [
                {
                    "slug": "agroforestry-and-soil",
                    "title": "Agroforestry and Soil Conservation",
                    "order": 5,
                    "minutes": 26,
                    "summary": "Trees as farm infrastructure.",
                    "learn": [
                        {"type": "p", "text": "Many African farming systems combine trees with crops and livestock — a practice now promoted worldwide as agroforestry. Faidherbia albida drops its leaves in the rainy season, fertilizing soil and letting light in, and keeps its canopy in the dry season, shading and mulching — exactly what a field needs. Similar systems: parkland agroforestry of the Sahel, home gardens in Kerala and West Africa, and terracing in Ethiopia that fed populations for centuries."},
                        {"type": "list", "items": [
                            "Nitrogen-fixing trees feed the soil without fertilizer factories.",
                            "Deep-rooted trees pull up minerals; leaf fall returns them to topsoil.",
                            "Terracing on slopes slows runoff and prevents erosion.",
                        ]},
                        {"type": "example", "title": "A living mulch", "text": "Faidherbia albida reverses the usual tree-crop conflict: it gives shade when the crop is absent and loses leaves when the crop needs light."},
                        {"type": "activity", "title": "Design a parkland", "text": "Design a one-acre agroforestry plot: which trees, which crops, how are they spaced, what is the water plan?"},
                    ],
                    "check": {
                        "prompt": "Check what you know about sustainable land management.",
                        "questions": [
                            {"q": "Faidherbia albida is valuable because…", "options": ["it drops leaves in the rainy season and shades in the dry season", "it is poisonous to pests", "it grows only indoors"], "answer": "it drops leaves in the rainy season and shades in the dry season", "explain": "Its phenology matches crop needs — leaf fall fertilizes, dry-season canopy cools and mulches."},
                            {"q": "Terracing on hillsides prevents…", "options": ["soil erosion from runoff", "too much sunlight", "bird damage"], "answer": "soil erosion from runoff", "explain": "Steps slow water, letting it soak in instead of carrying topsoil away."},
                        ],
                    },
                },
                {
                    "slug": "investigate-a-plant",
                    "title": "Capstone: Investigate a Plant",
                    "order": 6,
                    "minutes": 30,
                    "summary": "Design an ethnobotanical study with a scientific method.",
                    "learn": [
                        {"type": "p", "text": "Every claim in this course was established by the scientific method. Your capstone designs the same investigation for a plant: a hypothesis, a controlled test, a measurable outcome, and a written conclusion. Traditional knowledge identifies the question — the method answers it."},
                        {"type": "list", "items": [
                            "Observation: which plant, and what is claimed about it?",
                            "Hypothesis: plant material contains a compound that produces effect X.",
                            "Experiment: extraction, dosage, control, and record of outcome.",
                            "Report: method, data, and conclusion; note limitations and safety.",
                        ]},
                        {"type": "example", "title": "Safety", "text": "Never ingest unknown plants. Work with extracts on indicator strips, microscopy, or literature analysis only, and cite the safety rules."},
                        {"type": "activity", "title": "Write the proposal", "text": "Write a one-page study proposal: question, hypothesis, method with control, expected result, and safety rules."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of scientific method.",
                        "questions": [
                            {"q": "A control in an experiment exists to…", "options": ["show what happens without the treatment", "make results look better", "remove the need for data"], "answer": "show what happens without the treatment", "explain": "The control isolates the effect of the variable being tested."},
                            {"q": "In ethnobotanical research, traditional knowledge serves as…", "options": ["the lead that directs the hypothesis", "a substitute for evidence", "an irrelevant story"], "answer": "the lead that directs the hypothesis", "explain": "Tradition supplies testable leads; controlled study confirms or refutes them."},
                        ],
                    },
                },
            ],
        },
    ],
}
