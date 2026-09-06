"""Adult Education Science (HSE preparation — full published course)."""

ADULT_ED_HSE_SCIENCE = {
    "slug": "adult-ed-hse-science",
    "title": "Adult Education Science",
    "summary": "Life science, physical science, earth/space, and scientific reasoning.",
    "description": (
        "This science course prepares adult learners for HSE/GED science tests "
        "and everyday scientific literacy. It covers life science, physical science, "
        "earth and space science, and the practices of scientific reasoning, "
        "data analysis, and experimental design."
    ),
    "subject": "adult_ed",
    "subject_label": "Adult Education",
    "track": "adult_ed",
    "tracks": ["adult_ed"],
    "grades": ["adult"],
    "grade_label": "Adult",
    "status": "published",
    "audience": "Adult learners preparing for HSE/GED science or workplace science literacy.",
    "est_hours": 30,
    "passing_score": 80,
    "learning_objectives": [
        "Explain cell structure and basic genetics.",
        "Describe ecosystems, food webs, and environmental issues.",
        "Identify properties and states of matter.",
        "Understand forces, motion, and energy transformations.",
        "Interpret maps, rock cycles, and basic astronomy.",
        "Design a simple experiment and read data tables and graphs.",
    ],
    "units": [
        {
            "slug": "life-and-physical-science",
            "title": "Life and Physical Science",
            "summary": "Cells, heredity, matter, and energy.",
            "order": 1,
            "lessons": [
                {
                    "slug": "cells-and-heredity",
                    "title": "Cells and Heredity",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Cell structure, function, and basic genetics.",
                    "learn": [
                        {"type": "p", "text": "The cell is the basic unit of life. Plant cells have cell walls and chloroplasts. Animal cells do not. DNA carries genetic instructions. Traits are passed from parents to offspring through genes."},
                        {"type": "list", "items": [
                            "Cell parts: nucleus, cytoplasm, cell membrane.",
                            "Plant-only: cell wall, chloroplasts, large vacuole.",
                            "DNA = genetic code.",
                            "Dominant and recessive traits.",
                        ]},
                        {"type": "example", "title": "Punnett square", "text": "Cross Bb × Bb. Offspring genotypes: 25% BB, 50% Bb, 25% bb. Phenotype ratio: 3 dominant : 1 recessive."},
                    ],
                    "check": {
                        "prompt": "Show what you know about cells and heredity.",
                        "questions": [
                            {"q": "Which structure contains DNA?", "options": ["nucleus", "cytoplasm", "cell wall"], "answer": "nucleus", "explain": "The nucleus is the control center containing DNA."},
                            {"q": "A trait that appears in offspring only when both parents contribute it is…", "options": ["recessive", "dominant", "co-dominant"], "answer": "recessive", "explain": "Recessive traits are masked by dominant ones unless both alleles are recessive."},
                        ],
                    },
                },
                {
                    "slug": "matter-and-energy",
                    "title": "Matter and Energy",
                    "order": 2,
                    "minutes": 18,
                    "summary": "States of matter, mixtures, and energy forms.",
                    "learn": [
                        {"type": "p", "text": "Matter has mass and takes up space. It exists as solid, liquid, or gas. Energy can be kinetic (motion) or potential (stored). It changes forms but is conserved."},
                        {"type": "list", "items": [
                            "Mixtures: heterogeneous (not uniform) and homogeneous (uniform).",
                            "Compounds: chemically combined elements.",
                            "Energy forms: thermal, chemical, light, sound, electrical.",
                            "Exothermic releases heat; endothermic absorbs heat.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about matter and energy.",
                        "questions": [
                            {"q": "Which is a homogeneous mixture?", "options": ["salt water", "sand and iron filings", "oil and water"], "answer": "salt water", "explain": "Salt water looks the same throughout."},
                            {"q": "Energy that is stored is called…", "options": ["potential energy", "kinetic energy", "thermal energy"], "answer": "potential energy", "explain": "Potential energy is stored energy ready to be released."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "earth-space-and-scientific-reasoning",
            "title": "Earth/Space and Scientific Reasoning",
            "summary": "Earth systems, space, and the scientific method.",
            "order": 2,
            "lessons": [
                {
                    "slug": "earth-and-space-science",
                    "title": "Earth and Space Science",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Rock cycle, weather, and the solar system.",
                    "learn": [
                        {"type": "p", "text": "Earth is made of layers and cycles. The rock cycle transforms igneous, sedimentary, and metamorphic rock. Weather and climate are driven by the sun. The solar system includes the sun, eight planets, and smaller bodies."},
                        {"type": "list", "items": [
                            "Igneous: cooled magma/lava.",
                            "Sedimentary: compressed layers of sediment.",
                            "Metamorphic: changed by heat and pressure.",
                            "Greenhouse effect traps heat; ozone blocks UV.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about earth and space science.",
                        "questions": [
                            {"q": "Which rock forms from cooled lava?", "options": ["igneous", "sedimentary", "metamorphic"], "answer": "igneous", "explain": "Igneous rock forms when magma or lava cools and hardens."},
                            {"q": "Which planet is known as the Red Planet?", "options": ["Mars", "Venus", "Jupiter"], "answer": "Mars", "explain": "Mars appears red due to iron oxide on its surface."},
                        ],
                    },
                },
                {
                    "slug": "scientific-reasoning-and-data",
                    "title": "Scientific Reasoning and Data",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Scientific method, variables, and interpreting data.",
                    "learn": [
                        {"type": "p", "text": "Science advances through the scientific method: ask a question, research, form a hypothesis, test with an experiment, analyze data, and draw conclusions."},
                        {"type": "list", "items": [
                            "Independent variable: what you change.",
                            "Dependent variable: what you measure.",
                            "Control variables: what you keep the same.",
                            "A good experiment has one independent variable.",
                        ]},
                        {"type": "example", "title": "Plant experiment", "text": "Question: Does fertilizer affect plant height? Independent: fertilizer amount. Dependent: plant height. Control: light, water, soil type, pot size."},
                    ],
                    "check": {
                        "prompt": "Show what you know about scientific reasoning.",
                        "questions": [
                            {"q": "In an experiment, the independent variable is…", "options": ["what the scientist changes", "what is measured", "what is kept the same"], "answer": "what the scientist changes", "explain": "The independent variable is the factor the experimenter manipulates."},
                            {"q": "A conclusion is…", "options": ["what the data show about the hypothesis", "the question asked", "a guess"], "answer": "what the data show about the hypothesis", "explain": "Conclusions are drawn from analyzed data, not guesses."},
                        ],
                    },
                },
                {
                    "slug": "reading-science-graphs",
                    "title": "Reading Science Graphs and Tables",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Bar graphs, line graphs, pie charts, and tables.",
                    "learn": [
                        {"type": "p", "text": "Scientists use graphs and tables to show data. Bar graphs compare groups. Line graphs show change over time. Pie charts show parts of a whole. Tables organize exact numbers."},
                        {"type": "example", "title": "Reading a line graph", "text": "The x-axis shows time. The y-axis shows temperature. To find the temperature at month 4, go up from 4 to the line and read the y-value."},
                        {"type": "activity", "title": "Graph it", "text": "Take a data table (e.g., daily high temperatures for a week). Draw a line graph. State one trend you see."},
                    ],
                    "check": {
                        "prompt": "Show what you know about science graphs.",
                        "questions": [
                            {"q": "A pie chart shows…", "options": ["parts of a whole", "change over time", "comparisons among groups"], "answer": "parts of a whole", "explain": "Pie charts display how a total is divided into categories."},
                            {"q": "In a line graph, the horizontal axis is usually…", "options": ["time or the independent variable", "always speed", "the dependent variable"], "answer": "time or the independent variable", "explain": "The x-axis shows the independent variable; the y-axis shows the dependent variable."},
                        ],
                    },
                },
            ],
        },
    ],
}
