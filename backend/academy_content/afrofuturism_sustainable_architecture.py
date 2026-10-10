"""Trade Elective: Afrofuturism, Sustainable Architecture, and Earth Construction (published).

A builder-track course joining historical African architectural engineering
(Great Zimbabwe, the adobe city of Djenné, Nubian vaults) with modern
off-grid, sustainable build practice. Students compute, design, and build.
"""

AFROFUTURISM_SUSTAINABLE_ARCHITECTURE = {
    "slug": "afrofuturism-sustainable-architecture",
    "title": "Afrofuturism, Sustainable Architecture, and Earth Construction",
    "summary": "Great Zimbabwe, Djenné, and Nubian vaults — and the off-grid build methods they teach today.",
    "description": (
        "This trade course treats African masonry and earth architecture as engineering "
        "traditions with measurable performance, not as ruins. Students study Great "
        "Zimbabwe's granite walls built without mortar, the adobe city of Djenné with "
        "its annual replaster, and the Nubian vault — a roof-spanning technique that "
        "needs no shuttering. They then compute heat gain, thermal mass, and embodied "
        "carbon, and design an off-grid structure using those same principles."
    ),
    "subject": "trade",
    "subject_label": "Trade & Applied Skills",
    "track": "builder",
    "tracks": ["builder", "architect"],
    "grades": ["9", "10", "11", "12"],
    "grade_label": "Grades 9–12",
    "status": "published",
    "audience": "Students in construction, trades, and design programs.",
    "est_hours": 26,
    "passing_score": 80,
    "learning_objectives": [
        "Describe how Great Zimbabwe's walls were built without mortar and why they stand.",
        "Explain how adobe construction manages heat and moisture.",
        "Explain how a Nubian vault spans a roof without formwork.",
        "Calculate thermal mass and its effect on indoor temperature.",
        "Compare embodied carbon of earth, concrete, and steel construction.",
        "Design a simple off-grid structure using passive and earth techniques.",
    ],
    "units": [
        {
            "slug": "african-masonry",
            "title": "African Masonry: Stone and Earth",
            "summary": "Technique first, then performance.",
            "order": 1,
            "lessons": [
                {
                    "slug": "great-zimbabwe",
                    "title": "Great Zimbabwe's Dry-Stone Walls",
                    "order": 1,
                    "minutes": 26,
                    "summary": "Granite blocks fitted without mortar, nine centuries standing.",
                    "learn": [
                        {"type": "p", "text": "The Great Enclosure at Great Zimbabwe, built from the 11th to 15th centuries, is a curved wall up to 11 meters tall and 250 meters long, built entirely of hand-cut granite blocks set with no mortar. Masons shaped each block so that it locked to its neighbors, and the slight batter (slope) and stepped profile give the wall stability against its own weight."},
                        {"type": "list", "items": [
                            "Battered walls: slight inward slope gives stability without mortar.",
                            "Stepped/chevron patterns: decorative and structural at once.",
                            "Local granite: split by thermal shock from fire and water, then shaped by hand.",
                        ]},
                        {"type": "example", "title": "Engineering check", "text": "Dry-stone walls carry load by friction and interlock, so block placement matters more than any glue. The technique is still taught to conservation masons today."},
                        {"type": "activity", "title": "Stack test", "text": "Build a small dry-stone wall from shaped clay blocks. Try removing one block and see whether the wall stands — then explain why."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Great Zimbabwe.",
                        "questions": [
                            {"q": "Great Zimbabwe's walls were built with…", "options": ["no mortar at all", "portland cement", "steel frames"], "answer": "no mortar at all", "explain": "Blocks were shaped to interlock by friction and gravity."},
                            {"q": "A battered wall is one that…", "options": ["slopes slightly inward for stability", "is perfectly straight like a plank", "leans outward"], "answer": "slopes slightly inward for stability", "explain": "Batter lowers the center of gravity and improves stability."},
                        ],
                    },
                },
                {
                    "slug": "djenne-adobe",
                    "title": "The Adobe City of Djenné",
                    "order": 2,
                    "minutes": 26,
                    "summary": "Mud brick that breathes, maintained by community.",
                    "learn": [
                        {"type": "p", "text": "Djenné in Mali is the largest mud-brick city in the world. Its Great Mosque and houses are built from adobe — sun-dried earth with straw — with palm beams projecting from the walls for maintenance and (traditionally) for repair work. Each year, the community replasters the surfaces before the rains, so the building is maintained by the whole town."},
                        {"type": "list", "items": [
                            "Adobe: earth mixed with straw, moulded, and sun-dried.",
                            "Thermal mass: thick walls absorb daytime heat and release it at night.",
                            "Projecting palm beams let workers climb and replaster the facade.",
                            "Community maintenance: annual repair as civic ritual.",
                        ]},
                        {"type": "example", "title": "Why it works", "text": "In a climate of 45°C days and 20°C nights, a thick earthen wall keeps the inside near the average — the same physics that makes modern passive-solar buildings efficient."},
                        {"type": "activity", "title": "Run the numbers", "text": "Given a wall with 300 mm thickness and specific heat of 1000 J/kg·K, compute the heat absorbed by one square meter for a 15 K temperature swing."},
                    ],
                    "check": {
                        "prompt": "Check what you know about adobe.",
                        "questions": [
                            {"q": "Adobe is made from…", "options": ["earth and straw, sun-dried", "fired clay brick only", "pure concrete"], "answer": "earth and straw, sun-dried", "explain": "It is a cast mud-straw mixture dried in the sun."},
                            {"q": "The annual replastering of Djenné shows that…", "options": ["earth buildings require planned maintenance", "mud never needs repair", "plaster is decorative only"], "answer": "earth buildings require planned maintenance", "explain": "Earthen architecture is maintained on a cycle, before the rains."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "vaults-and-offgrid",
            "title": "Vaults and Off-Grid Building",
            "summary": "Spanning without timber, and building without power.",
            "order": 2,
            "lessons": [
                {
                    "slug": "nubian-vault",
                    "title": "The Nubian Vault",
                    "order": 3,
                    "minutes": 26,
                    "summary": "A roof that needs no formwork and no timber.",
                    "learn": [
                        {"type": "p", "text": "Nubian vaulting, from Upper Egypt and Sudan, builds a permanent arched roof out of mud brick with no shuttering at all. A guide wall is built and bricks laid at a slight lean against it; the arch closes itself as the last brick is placed. The result is a self-supporting ceiling in a region with almost no timber."},
                        {"type": "list", "items": [
                            "Guide wall: temporary masonry curvature guides the leaning brick.",
                            "Arch action: compressive force travels to the walls.",
                            "No formwork, no tensile timber — roof in a timberless climate.",
                        ]},
                        {"type": "example", "title": "Modern revival", "text": "The Nubian Vault Association trains masons today to build rural housing this way, training a trade that uses one local material and one local technique."},
                        {"type": "activity", "title": "Sketch it", "text": "Draw the section of a Nubian vault in six steps: first brick, leaning, half-arch, guide wall removal, closing, and finish."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the Nubian vault.",
                        "questions": [
                            {"q": "A Nubian vault is built with…", "options": ["leaning mud brick against a guide wall", "steel I-beams", "timber trusses"], "answer": "leaning mud brick against a guide wall", "explain": "The arch is self-supporting once it closes."},
                            {"q": "The technique is useful where timber is scarce because…", "options": ["it uses no tensile timber", "it requires no skill", "it uses no local material"], "answer": "it uses no tensile timber", "explain": "It converts compression-only masonry into a roof."},
                        ],
                    },
                },
                {
                    "slug": "off-grid-design",
                    "title": "Designing Off-Grid",
                    "order": 4,
                    "minutes": 26,
                    "summary": "Passive first, active second.",
                    "learn": [
                        {"type": "p", "text": "Off-grid design follows a hierarchy: passive design first (orientation, thermal mass, shading, ventilation), then active systems (solar, wind), then storage. Afrofuturism enters here not as decoration but as design freedom: communities that never had forced hot water or air conditioning may build differently rather than replicate irrelevant grids."},
                        {"type": "list", "items": [
                            "Passive: orientation, insulation, thermal mass, shading, ventilation.",
                            "Active: photovoltaic sizing, batteries, water catchment.",
                            "Embodied carbon: earth and local materials beat concrete and steel per unit of performance.",
                            "Vernacular first: use the materials already on site.",
                        ]},
                        {"type": "example", "title": "Design spec", "text": "A 40 m2 dwelling: 40 m2 south glass aperture, 8 m3 of water catchment, a 1.5 kW PV array, and earth walls of 400 mm. Compute the water budget from local rainfall."},
                        {"type": "activity", "title": "Design brief", "text": "Design a 40 m2 off-grid learning space: site plan, passive features, active systems, and a materials list with embodied carbon estimates."},
                    ],
                    "check": {
                        "prompt": "Check what you know about off-grid design.",
                        "questions": [
                            {"q": "Off-grid design should begin with…", "options": ["passive measures", "generators", "large batteries"], "answer": "passive measures", "explain": "Passive design reduces demand before equipment is added."},
                            {"q": "Embodied carbon compares…", "options": ["the carbon released to produce materials", "only the paint color", "the roof slope"], "answer": "the carbon released to produce materials", "explain": "Earth materials usually carry far lower embodied carbon than cement and steel."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "codage-and-fabrication",
            "title": "Analysis and Fabrication",
            "summary": "Measurement, documentation, and building a piece.",
            "order": 3,
            "lessons": [
                {
                    "slug": "thermography-and-assessment",
                    "title": "Measure a Building",
                    "order": 5,
                    "minutes": 26,
                    "summary": "Performance is verified, not assumed.",
                    "learn": [
                        {"type": "p", "text": "A builder must be able to prove a building works. Thermal imaging finds heat leaks, a hygrometer reads humidity through a diurnal cycle, and a data logger records the lag between outside air temperature and inside surface temperature. The thicker and more massive the wall, the longer that lag."},
                        {"type": "list", "items": [
                            "Lag time: mass delays temperature change — good for comfort.",
                            "Air leakage: find and seal drafts before adding equipment.",
                            "Thermal bridges: metal or concrete paths that short-circuit insulation.",
                        ]},
                        {"type": "activity", "title": "Log it", "text": "Place a thermometer on a south-facing exterior wall and one inside; read them at 6 am and 4 pm. Compute the difference and the apparent lag."},
                    ],
                    "check": {
                        "prompt": "Check what you know about measurement.",
                        "questions": [
                            {"q": "Thermal mass creates a…", "options": ["lag between outside and inside temperature swings", "short circuit", "draft"], "answer": "lag between outside and inside temperature swings", "explain": "Mass absorbs and slowly releases heat, smoothing the swing."},
                            {"q": "A thermal bridge is…", "options": ["a material path that bypasses insulation", "a type of roof", "a paint finish"], "answer": "a material path that bypasses insulation", "explain": "Conductive materials let heat bypass insulated layers."},
                        ],
                    },
                },
                {
                    "slug": "capstone-build",
                    "title": "Capstone: Build One Component",
                    "order": 6,
                    "minutes": 30,
                    "summary": "Design and build a small earthen or masonry component.",
                    "learn": [
                        {"type": "p", "text": "The capstone is a physical piece: a brick arch, a Nubian vault section, or a rammed-earth panel at least 400 mm high, with calculations for load and material. Document the mix or joint, the build steps, and the measurements, and photograph the process."},
                        {"type": "list", "items": [
                            "Design: dimensions, materials, estimated load.",
                            "Build: document steps, proportions, and any failure.",
                            "Analyze: measured performance against your prediction.",
                            "Document: photos and a one-page build report.",
                        ]},
                        {"type": "tip", "text": "Masons learn by building and by breaking. Document every failure as carefully as a success."},
                        {"type": "activity", "title": "Build it", "text": "Complete the component and the report. Include the mix ratio, the build steps, and the measured result."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the capstone.",
                        "questions": [
                            {"q": "A build report should include…", "options": ["dimensions, materials, steps, and measured results", "only photographs", "only the date"], "answer": "dimensions, materials, steps, and measured results", "explain": "Documentation is what makes work repeatable and verifiable."},
                            {"q": "Documenting a failed build is useful because…", "options": ["failures reveal what to change next time", "it is bad luck", "no one will read it"], "answer": "failures reveal what to change next time", "explain": "Failures give the most specific information about limits."},
                        ],
                    },
                },
            ],
        },
    ],
}
