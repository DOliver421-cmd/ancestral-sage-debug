"""Ethnomathematics & Black Pioneers in STEM (published course).

STEM course connecting African mathematical traditions — fractal patterns,
Great Zimbabwe's architecture, Egyptian and Timbuktu mathematics — with the
breakthroughs of Black scientists from Benjamin Banneker to Kizzmekia Corbett.
"""

ETHNOMATHEMATICS_STEM = {
    "slug": "ethnomathematics-black-pioneers",
    "title": "Ethnomathematics & Black Pioneers in STEM",
    "summary": "African mathematical and engineering traditions — fractals, architecture, and number systems — alongside the discoveries of Black scientists from Banneker to Katherine Johnson to Dr. Kizzmekia Corbett.",
    "description": (
        "Ethnomathematics & Black Pioneers in STEM teaches core math and science concepts "
        "through African and diaspora achievement. Students study fractal geometry in "
        "African village design and textiles, the engineering of Great Zimbabwe and "
        "Aksum, Egyptian and Timbuktu mathematics, and the lives and methods of pioneers "
        "like Benjamin Banneker, Dr. Charles Drew, Katherine Johnson, Gladys West, Mark "
        "Dean, and Dr. Kizzmekia Corbett. Each unit pairs the history with the actual "
        "math or science: ratios, scaling, geometry, statistics, and the scientific method."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "scholar",
    "tracks": ["foundations", "scholar", "builder"],
    "grades": ["7", "8", "9", "10"],
    "grade_label": "Grades 7–10",
    "status": "published",
    "audience": "Middle and high school students building math and science foundations.",
    "est_hours": 22,
    "passing_score": 80,
    "learning_objectives": [
        "Define ethnomathematics and give two examples from African cultures.",
        "Identify fractal self-similarity in African village layouts and textiles.",
        "Apply ratio and scale reasoning to explain adobe and stone construction.",
        "Describe Egyptian and Timbuktu contributions to numeration and astronomy.",
        "Explain the mathematical work of Benjamin Banneker and Katherine Johnson.",
        "Summarize Dr. Charles Drew's blood-banking science and Gladys West's GPS geodesy.",
        "Outline Dr. Kizzmekia Corbett's mRNA vaccine development process.",
        "Apply the scientific method to design a small experiment.",
    ],
    "units": [
        {
            "slug": "african-mathematical-traditions",
            "title": "African Mathematical Traditions",
            "summary": "Fractals, geometry, and number systems across the continent.",
            "order": 1,
            "lessons": [
                {
                    "slug": "fractals-in-africa",
                    "title": "Fractal Patterns in African Design",
                    "order": 1,
                    "minutes": 20,
                    "summary": "Self-similarity from villages to textiles — centuries before 'fractal' was named.",
                    "learn": [
                        {"type": "p", "text": "A fractal is a pattern that repeats itself at different scales: a shape made of smaller copies of itself. Mathematician Ron Eglash documented that many African villages, textiles, braids, and carvings use deliberate fractal structure — circular compounds within circular compounds, patterns that recurse three and four levels deep. European architecture of the same eras mostly used rectangles within rectangles; the fractal tradition is distinctively African and mathematically sophisticated."},
                        {"type": "list", "items": [
                            "Mokoulek (Cameroon): a village whose granary rings repeat at scaled sizes.",
                            "Ba-ila settlement (Zambia): livestock pens, family rings, and the whole village echo one circular form.",
                            "Adinkra and kente textiles: geometric motifs that repeat and scale.",
                        ]},
                        {"type": "example", "title": "Do the math", "text": "If a village's outer ring has radius 100 m and each nested ring is 1/3 the previous radius, the rings have radii 100, 33.3, 11.1, 3.7 m — a geometric sequence with ratio 1/3."},
                        {"type": "activity", "title": "Build a fractal", "text": "Draw a simple shape (circle, triangle, or rectangle). Inside it, draw a scaled copy at 1/3 size, then repeat twice more. Label each level's size as a fraction of the original."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of fractals in African design.",
                        "questions": [
                            {"q": "A fractal pattern is one that…", "options": ["repeats its structure at progressively smaller scales", "only contains circles", "never repeats"], "answer": "repeats its structure at progressively smaller scales", "explain": "Self-similarity across scales is the defining property of fractals."},
                            {"q": "If each nested ring is 1/3 the previous, ring radii form…", "options": ["a geometric sequence with ratio 1/3", "an arithmetic sequence adding 1/3", "a random series"], "answer": "a geometric sequence with ratio 1/3", "explain": "Each term is multiplied by the same ratio, which defines a geometric sequence."},
                        ],
                    },
                },
                {
                    "slug": "engineering-great-zimbabwe-aksum",
                    "title": "Engineering Great Zimbabwe and Aksum",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Load, balance, and scale in Africa's monumental architecture.",
                    "learn": [
                        {"type": "p", "text": "Great Zimbabwe's mortarless granite walls rise 11 meters and lean slightly inward — a stability strategy modern engineers recognize: angling a wall's face reduces the force pushing it outward at the base. Aksum's carved stelae, some over 30 meters, required quarrying, transporting, and raising multi-hundred-ton monoliths — problems in mass, friction, and leverage. Both were solved without modern tools, using empirical physics."},
                        {"type": "list", "items": [
                            "Dry-stone masonry: interlocking shapes distribute weight without mortar.",
                            "Inward wall slope ('batter') lowers the center of mass and resists tipping.",
                            "Raising a monolith: levers, earthen ramps, and ropes convert small input force into large lifting force.",
                        ]},
                        {"type": "example", "title": "Do the math", "text": "A lever with a 10:1 arm ratio lets 100 kg of downward force balance a 1,000 kg load: 100 × 10 = 1,000. Same principle, Aksum to today."},
                        {"type": "activity", "title": "Wall stability test", "text": "Build two small paper-card towers: one straight, one with the base wider than the top. Push both gently. Explain the result in terms of center of mass."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of African engineering.",
                        "questions": [
                            {"q": "Great Zimbabwe's walls lean slightly inward because…", "options": ["it lowers the center of mass and improves stability", "stone shrinks over time", "it was accidental"], "answer": "it lowers the center of mass and improves stability", "explain": "Battered walls resist tipping — the same physics used in dams and retaining walls."},
                            {"q": "A 10:1 lever lets 100 kg of force balance…", "options": ["1,000 kg", "10 kg", "100 kg"], "answer": "1,000 kg", "explain": "Mechanical advantage multiplies force by the arm ratio: 100 × 10 = 1,000."},
                        ],
                    },
                },
                {
                    "slug": "egyptian-timbuktu-math",
                    "title": "From Egypt to Timbuktu: African Mathematics in Writing",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Rhind papyrus, base-10 multiplication, and Sankore astronomy.",
                    "learn": [
                        {"type": "p", "text": "Egyptian scribes solved problems in the Rhind Papyrus (c. 1550 BCE) using multiplication by doubling — essentially binary arithmetic — and computed areas and slopes for pyramid construction. Centuries later, Timbuktu's manuscripts covered astronomy and mathematics: scholars at Sankore calculated prayer times and qibla directions, requiring spherical geometry and precise observation. Africa's written mathematical tradition is over 3,500 years old."},
                        {"type": "list", "items": [
                            "Doubling multiplication: 23 × 13 = 23×1 + 23×4 + 23×8 (13 = 1+4+8) — binary decomposition.",
                            "Egyptian unit fractions: every fraction written as a sum of fractions with numerator 1.",
                            "Sankore astronomy: timekeeping and geography problems solved with observation and trigonometry.",
                        ]},
                        {"type": "example", "title": "Try doubling", "text": "Compute 14 × 12: double 14 → 28, 56, 112; pick the rows for 12 = 8+4: 112 + 56 = 168. Check with a calculator: 14 × 12 = 168."},
                        {"type": "activity", "title": "Doubling drill", "text": "Use doubling multiplication to compute 15 × 11, writing which doubled rows you added."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Egyptian and Timbuktu mathematics.",
                        "questions": [
                            {"q": "Egyptian doubling multiplication is similar to…", "options": ["binary decomposition used in modern computers", "long division", "counting on fingers"], "answer": "binary decomposition used in modern computers", "explain": "Breaking a number into sums of powers of two is exactly how binary arithmetic works."},
                            {"q": "Sankore scholars needed spherical geometry to…", "options": ["calculate prayer times and directions on a curved Earth", "count livestock", "design textiles"], "answer": "calculate prayer times and directions on a curved Earth", "explain": "Timekeeping and orientation on a sphere require trigonometry and careful observation."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "black-pioneers-in-stem",
            "title": "Black Pioneers in Modern STEM",
            "summary": "Banneker, Drew, Johnson, West, Dean, Corbett — the science behind the stories.",
            "order": 2,
            "lessons": [
                {
                    "slug": "banneker-and-johnson",
                    "title": "Benjamin Banneker and Katherine Johnson: The Mathematicians",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Almanac astronomy and NASA trajectory math.",
                    "learn": [
                        {"type": "p", "text": "Benjamin Banneker (1731–1806), a free Black astronomer and self-taught mathematician, published almanacs with tide tables and eclipse predictions and helped survey the boundaries of Washington, D.C. Katherine Johnson (1918–2020), a NASA mathematician, calculated launch windows and re-entry trajectories by hand — her verification was trusted over early electronic computers, and John Glenn refused to fly until she checked the machine's numbers."},
                        {"type": "list", "items": [
                            "Banneker: predicted a 1789 solar eclipse; corresponded with Jefferson challenging claims of Black inferiority.",
                            "Johnson: calculated Apollo 11's lunar trajectory; awarded the Presidential Medal of Freedom in 2015.",
                            "Shared skill: orbital prediction — applying trigonometry and Newtonian physics to moving objects.",
                        ]},
                        {"type": "example", "title": "Do the math", "text": "An orbit's speed × time = distance traveled. If a spacecraft orbits at 7.8 km/s for 90 minutes (5,400 s), it covers 7.8 × 5,400 = 42,120 km — the basis of every trajectory calculation Johnson made."},
                        {"type": "activity", "title": "Trajectory drill", "text": "A spacecraft travels at 7.5 km/s for 45 minutes. Find the distance in km. Then find how long a 30,000 km journey takes at that speed."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the trajectory mathematicians.",
                        "questions": [
                            {"q": "Katherine Johnson's NASA work centered on…", "options": ["calculating flight trajectories and launch windows", "designing rocket engines", "astronaut training"], "answer": "calculating flight trajectories and launch windows", "explain": "Her hand-verified trajectory math was trusted for Mercury and Apollo missions."},
                            {"q": "At 7.8 km/s for 5,400 s, distance is…", "options": ["42,120 km", "780 km", "5,400 km"], "answer": "42,120 km", "explain": "Distance = speed × time: 7.8 × 5,400 = 42,120 km."},
                        ],
                    },
                },
                {
                    "slug": "drew-and-west",
                    "title": "Charles Drew and Gladys West: Blood Banks and GPS",
                    "order": 5,
                    "minutes": 20,
                    "summary": "Plasma science that saved millions, and the geodesy behind your phone's map.",
                    "learn": [
                        {"type": "p", "text": "Dr. Charles Drew (1904–1950) discovered that plasma — blood with cells removed — could be stored far longer than whole blood, and organized the first large-scale blood banks during World War II, saving thousands of lives. Gladys West (b. 1930), a mathematician at the Naval Proving Ground, spent decades building precise models of the Earth's shape — geodesy — whose data became the mathematical foundation of GPS."},
                        {"type": "list", "items": [
                            "Drew's insight: plasma storage doesn't require matching blood types, enabling mass battlefield transfusion.",
                            "West: programmed early computers to model sea-level gravity and satellite orbits; inducted into the Air Force Space and Missile Pioneers Hall of Fame in 2018.",
                            "Both worked within systems that segregated them — and produced science the whole world now depends on.",
                        ]},
                        {"type": "example", "title": "Do the math", "text": "GPS precision depends on timing: light travels about 30 cm in 1 nanosecond. A 10-ns timing error puts you ~3 m off — which is why West's error-reducing Earth models mattered."},
                        {"type": "activity", "title": "Precision problem", "text": "A GPS receiver has a 20-ns timing error. Estimate the position error in meters using 30 cm per nanosecond."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Drew and West.",
                        "questions": [
                            {"q": "Charles Drew's key discovery was that…", "options": ["plasma can be stored longer than whole blood", "blood types don't matter", "vitamin C prevents scurvy"], "answer": "plasma can be stored longer than whole blood", "explain": "Plasma storage enabled mass blood banking, transforming battlefield and emergency medicine."},
                            {"q": "Gladys West's work was essential to GPS because she…", "options": ["built precise mathematical models of Earth's shape", "invented satellites", "designed phone chips"], "answer": "built precise mathematical models of Earth's shape", "explain": "Accurate geodesy is what turns satellite signals into reliable positions."},
                        ],
                    },
                },
                {
                    "slug": "corbett-and-the-method",
                    "title": "Kizzmekia Corbett and the Scientific Method",
                    "order": 6,
                    "minutes": 20,
                    "summary": "mRNA vaccine science — and how a hypothesis becomes a verified result.",
                    "learn": [
                        {"type": "p", "text": "Dr. Kizzmekia Corbett led the team at NIH's Vaccine Research Center that designed the spike-protein immunogen behind the Moderna COVID-19 vaccine — developed from viral sequence to clinical trial in about 66 days. Her work rested on coronavirus structure research done for years before the pandemic. Her story is also a model of the scientific method: observe, hypothesize, design, test, verify, publish, and re-verify as evidence accumulates."},
                        {"type": "list", "items": [
                            "Coronavirus pre-work: spike protein stabilization research enabled the speed.",
                            "The method: sequence the virus → design the immunogen → preclinical tests → clinical trials → independent verification.",
                            "Corbett became a centerpiece of public science communication, explaining the vaccine to communities with justified vaccine distrust.",
                        ]},
                        {"type": "tip", "text": "Speed didn't replace rigor — prior research did. That's why baselines matter: build knowledge before the emergency."},
                        {"type": "activity", "title": "Design an experiment", "text": "Pick a question you can test this week (plant growth, memory, reaction time). Write your hypothesis, your variables, and how you'd know the result was reliable."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Corbett and scientific method.",
                        "questions": [
                            {"q": "Corbett's vaccine design targeted the coronavirus…", "options": ["spike protein", "lipid membrane", "RNA polymerase"], "answer": "spike protein", "explain": "Training the immune system against the spike blocks the virus from entering cells."},
                            {"q": "The final step that makes a scientific result trusted is…", "options": ["independent verification and replication", "a press release", "a strong opinion"], "answer": "independent verification and replication", "explain": "Replication by independent teams is what separates science from claim."},
                        ],
                    },
                },
            ],
        },
    ],
}
