"""Mathematics of the African Diaspora: Algorithms, Calendars, and Astronomy (published).

Mathematics course for Grades 6–9 deepening ethnomathematics beyond geometry
and architecture into complex time-keeping systems (Dogon astronomical
calculations), Yoruba base-20 arithmetic logic, and African maritime
navigation traditions.
"""

DIASPORA_MATHEMATICS = {
    "slug": "diaspora-mathematics-algorithms-astronomy",
    "title": "Mathematics of the African Diaspora: Algorithms, Calendars, and Astronomy",
    "summary": "Time-keeping systems (Dogon astronomical calculations), Yoruba base-20 arithmetic logic, and African maritime navigation traditions.",
    "description": (
        "A mathematics course built on African and diaspora knowledge systems. Students "
        "convert between number bases using Yoruba's vigesimal (base-20) arithmetic, model "
        "the astronomy behind Egyptian, Ethiopian, and Dogon calendars, compute with "
        "doubling-multiplication algorithms, and apply ratio, rate, and angle reasoning to "
        "Indian Ocean navigation traditions. Every unit pairs the history with the actual "
        "arithmetic, so the math is real and checkable."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "foundations",
    "tracks": ["foundations", "scholar"],
    "grades": ["6", "7", "8", "9"],
    "grade_label": "Grades 6–9",
    "status": "published",
    "audience": "Middle school students strengthening number sense, ratios, and angles through world mathematics.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": [
        "Convert numbers between base 10 and base 20 and explain Yoruba vigesimal structure.",
        "Use doubling (duplation) multiplication like Egyptian scribes and explain why it works.",
        "Explain how the Egyptian civil calendar and the Ethiopian calendar organize the year.",
        "Describe the Dogon people's knowledge of the Sirius system and evaluate the historical evidence.",
        "Compute star altitude and use it to estimate latitude in the Swahili coast navigation tradition.",
        "Apply rate reasoning (distance = rate × time) to monsoon sailing in the Indian Ocean trade.",
    ],
    "units": [
        {
            "slug": "number-systems",
            "title": "African Number Systems and Algorithms",
            "summary": "Base-20 arithmetic in Yoruba and doubling algorithms from Egypt.",
            "order": 1,
            "lessons": [
                {
                    "slug": "yoruba-base-twenty",
                    "title": "Yoruba Base-20: Arithmetic Built on Twenties",
                    "order": 1,
                    "minutes": 25,
                    "summary": "A vigesimal counting system with subtraction built in — and what it teaches about place value.",
                    "learn": [
                        {"type": "p", "text": "Most of the world counts in tens because we count on ten fingers. The Yoruba language of West Africa builds its numbers on twenty — fingers plus toes (ogójì = 20, literally 'all fingers complete'). Yoruba numerals are genuinely vigesimal (base-20) and are also famous for using subtraction: 35 is expressed as 'two twenties less five' (àárùn-ọ́-dín-lọ́gbọ̀n, literally 'five less from forty'). Numbers like 25 are additive (20 + 5), but 35, 45, 55… are subtractive."},
                        {"type": "list", "items": [
                            "Base 20 means place values go 1, 20, 400 (20²), 8000 (20³)… instead of 1, 10, 100, 1000.",
                            "Yoruba 35 = (2×20) − 5, and 45 = (3×20) − 15: subtraction from the next multiple of twenty.",
                            "Other base-20 (vigesimal) systems: the Maya and Aztec in the Americas, and Danish fractions in Europe.",
                        ]},
                        {"type": "example", "title": "Do the math", "text": "Convert the base-20 number 1·3·5 (one four-hundred, three twenties, five ones) to base 10: (1×400) + (3×20) + (5×1) = 465. Going the other way, 87 = 4 twenties + 7 → 4·7 in base-20 digits."},
                        {"type": "activity", "title": "Base-20 converter", "text": "Write 93, 140, and 200 in base-20 digit form (digits may be up to 19). Then convert the base-20 number 2·9 to base 10. Check with a classmate."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of vigesimal arithmetic.",
                        "questions": [
                            {"q": "In base 20, the third place value is…", "options": ["400 (20 × 20)", "100", "30"], "answer": "400 (20 × 20)", "explain": "Place values multiply by the base: 1, 20, 400, 8000…"},
                            {"q": "Yoruba expresses 35 as 'five less from forty,' which shows the system uses…", "options": ["subtraction toward the next multiple of twenty", "only addition", "decimals"], "answer": "subtraction toward the next multiple of twenty", "explain": "Vigesimal structure plus subtractive forms like 35 = 2×20 − 5 is the signature of Yoruba numerals."},
                        ],
                    },
                },
                {
                    "slug": "egyptian-doubling-algorithm",
                    "title": "Egyptian Multiplication: The Doubling Algorithm",
                    "order": 2,
                    "minutes": 25,
                    "summary": "How scribes multiplied by doubling — the same idea behind binary and Russian peasant multiplication.",
                    "learn": [
                        {"type": "p", "text": "Egyptian scribes multiplied without memorizing times tables. To compute A × B, they wrote a column of doublings of A (A, 2A, 4A, 8A…) and a column of powers of 2 (1, 2, 4, 8…), then picked the rows whose powers of 2 sum to B and added the matching A-values. This works because every whole number is a sum of distinct powers of 2 — the same fact that makes binary numbers and modern computers work."},
                        {"type": "list", "items": [
                            "Compute 23 × 13: doublings of 23 are 23, 46, 92; powers of 2 are 1, 2, 4, 8. Since 13 = 1 + 4 + 8, take 23 + 92 + 184 = 299.",
                            "This is sometimes called 'Russian peasant multiplication' or 'duplation' — and it survived in Ethiopian manuscript mathematics too.",
                            "Division used the reverse: double the divisor until you can assemble the dividend.",
                        ]},
                        {"type": "example", "title": "Try it", "text": "14 × 12: doublings 14, 28, 56, 112 for powers 1, 2, 4, 8. Now 12 = 4 + 8, so add 56 + 112 = 168. Calculator check: 14 × 12 = 168."},
                        {"type": "activity", "title": "Doubling drill", "text": "Use the doubling algorithm to compute 15 × 11 and 22 × 13. Write out both columns and circle the rows you add."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the doubling algorithm.",
                        "questions": [
                            {"q": "The doubling algorithm works because every whole number can be written as…", "options": ["a sum of distinct powers of 2", "a sum of primes", "a product of tens"], "answer": "a sum of distinct powers of 2", "explain": "Binary representation is exactly that sum — which is why the scribes' method always works."},
                            {"q": "In 23 × 13, which rows do you add if 13 = 1 + 4 + 8?", "options": ["23 + 92 + 184", "46 + 92", "23 + 46 + 92"], "answer": "23 + 92 + 184", "explain": "Row for 1 is 23, row for 4 is 92, row for 8 is 184; their sum is 299 = 23 × 13."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "calendars",
            "title": "Calendars of Africa",
            "summary": "Solar, stellar, and lunar timekeeping from Egypt to Ethiopia to the Dogon.",
            "order": 2,
            "lessons": [
                {
                    "slug": "egyptian-calendar",
                    "title": "Egypt: The 365-Day Calendar and the Star Sirius",
                    "order": 3,
                    "minutes": 25,
                    "summary": "How heliacal risings, floods, and civil calendars kept a 6-hour drift under control.",
                    "learn": [
                        {"type": "p", "text": "Egyptian priests noticed that the star Sopdet (Sirius) first becomes visible just before dawn each year — its 'heliacal rising' — right before the Nile flood. They built a 365-day civil calendar: 12 months of 30 days plus 5 festival days. But the true year is about 365.25 days, so the calendar drifted roughly one day every four years (6 hours × 4 = 24 hours). Instead of leap days, Egyptians let the calendar cycle and anchored it by watching Sirius — an early example of using a repeating astronomical event as a clock."},
                        {"type": "list", "items": [
                            "Three seasons: Akhet (flood), Peret (growing), Shemu (harvest) — time organized around the river.",
                            "The drift is 6 hours/year: 1,460 years for the civil New Year to return to the heliacal rising (the 'Sothic cycle').",
                            "Rome later adopted the leap-day fix (Julian calendar); Egypt's Ptolemaic decree of 238 BCE proposed one too, but it wasn't widely used for centuries.",
                        ]},
                        {"type": "example", "title": "Do the math", "text": "Drift per year ≈ 0.25 day. Over 100 years the civil calendar falls behind the seasons by about 25 days. What fraction of a full year is that? 25/365 ≈ 6.8%."},
                        {"type": "activity", "title": "Calendar math", "text": "If a calendar year is exactly 365 days and the true year is 365.2422 days, compute the drift after 10 years and after 40 years. Then state how many years until the drift equals one full month (30 days)."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the Egyptian calendar.",
                        "questions": [
                            {"q": "The Egyptian civil calendar drifted because…", "options": ["365 days is about a quarter day short of the true year", "the Nile flood changed length", "Egyptians counted 13 months"], "answer": "365 days is about a quarter day short of the true year", "explain": "A 365-day year loses ~6 hours per year, drifting a full day every 4 years."},
                            {"q": "Sirius's heliacal rising served Egyptians as…", "options": ["an annual astronomical marker coinciding with the Nile flood", "a unit of currency", "a form of writing"], "answer": "an annual astronomical marker coinciding with the Nile flood", "explain": "Tracking Sirius re-anchored the drifting civil calendar to the seasons each year."},
                        ],
                    },
                },
                {
                    "slug": "ethiopian-and-dogon-timekeeping",
                    "title": "Ethiopia's Calendar and the Dogon Astronomers",
                    "order": 4,
                    "minutes": 30,
                    "summary": "A calendar seven years behind Rome's — and one of the most debated astronomy stories in Africa.",
                    "learn": [
                        {"type": "p", "text": "Ethiopia keeps its own calendar (the Ge'ez calendar): 13 months (12 of 30 days plus a 13th of 5–6 days), running about 7–8 years behind the Gregorian calendar because of a different calculation of the year of the Annunciation. It is a living solar calendar with its own leap-year rule — proof that 'the calendar' is a cultural technology, not a fact of nature."},
                        {"type": "p", "text": "The Dogon people of Mali became famous in 20th-century anthropology when French ethnographers Marcel Griaule and Germaine Dieterlen reported that Dogon priests described the star Sirius as having an invisible companion — matching Sirius B, a white dwarf confirmed by astronomers in the 20th century. The reported knowledge included the companion's 50-year orbital period. Historians of astronomy debate what this means: skeptics argue the details may have been acquired from modern sources or misreported by the ethnographers, while others argue Dogon observation traditions were genuinely precise. The honest lesson is about evidence: extraordinary claims require documented chains of observation, and this one remains contested."},
                        {"type": "list", "items": [
                            "Sirius B orbits Sirius A about every 50 years at roughly the distance of Uranus from the Sun.",
                            "White dwarfs like Sirius B pack a star's mass into an Earth-sized body — invisible without a telescope.",
                            "The Dogon also maintained a sophisticated planting calendar keyed to celestial observations.",
                        ]},
                        {"type": "tip", "text": "In math and science, 'how do we know?' matters as much as 'what do we know?' The Dogon case is a real historical controversy — treat both the claim and the debate with rigor."},
                        {"type": "activity", "title": "Orbit math", "text": "Sirius B travels a circle around Sirius A in about 50 years. If the orbit's radius were modeled as 19 astronomical units (AU), compute the orbital circumference (C = 2πr) in AU, then the average speed in AU/year."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Ethiopian and Dogon timekeeping.",
                        "questions": [
                            {"q": "The Ethiopian calendar has…", "options": ["13 months, 12 of 30 days plus a short 13th month", "10 lunar months", "exactly the same months as the Gregorian calendar"], "answer": "13 months, 12 of 30 days plus a short 13th month", "explain": "The Ge'ez calendar's 13th month (Pagume) has 5 days, 6 in leap years."},
                            {"q": "The responsible way to describe Dogon knowledge of Sirius B is…", "options": ["a contested historical claim whose evidence is debated by historians", "proven pre-telescopic astronomy", "definitely borrowed and therefore worthless"], "answer": "a contested historical claim whose evidence is debated by historians", "explain": "Both the observation claim and the skepticism have serious proponents; the evidence chain is genuinely disputed."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "navigation",
            "title": "Mathematics of Navigation and the Indian Ocean World",
            "summary": "Star altitude, latitude, and monsoon rates on the Swahili coast.",
            "order": 3,
            "lessons": [
                {
                    "slug": "star-altitude-latitude",
                    "title": "Steering by Stars: Latitude from Star Altitude",
                    "order": 5,
                    "minutes": 25,
                    "summary": "Polaris, the Southern Cross, and the geometry that turns a star's height into a position.",
                    "learn": [
                        {"type": "p", "text": "On the Swahili coast (Kenya, Tanzania) and across the Indian Ocean, Arab, African, and Asian sailors navigated hundreds of years before GPS using star paths. A star that sits directly over the North Pole (Polaris) appears at an altitude above the horizon equal to your latitude — so measuring Polaris's height in degrees gives your north-south position. In southern waters, sailors used stars like those of the Southern Cross and remembered where specific stars rise and set: each bright star has a fixed 'house' (rising point) on the horizon."},
                        {"type": "list", "items": [
                            "Altitude of Polaris ≈ your latitude: at the equator it sits on the horizon (0°); at 30°N it is 30° high.",
                            "Kamal: an Arab navigation instrument — a small card on a cord held at arm's length — used to compare star altitude against known values between ports.",
                            "Horizon 'houses': memorized rising/setting points of 15–16 bright stars acted as a compass rose.",
                        ]},
                        {"type": "example", "title": "Do the math", "text": "A sailor measures Polaris at 12° above the horizon. Her latitude is about 12°N — near the Swahili port of Mogadishu. If she sails south until Polaris measures 5°, she has traveled about 7° of latitude. One degree of latitude ≈ 111 km, so ≈ 7 × 111 = 777 km sailed south."},
                        {"type": "activity", "title": "Latitude drill", "text": "Convert these Polaris altitudes to latitudes: 0°, 19°, 41°. Then compute the distance between the first and third positions using 111 km per degree."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of star-based latitude.",
                        "questions": [
                            {"q": "Polaris's altitude above the horizon equals…", "options": ["your latitude in degrees", "your longitude", "the current season"], "answer": "your latitude in degrees", "explain": "Because Polaris sits almost exactly over Earth's rotational north pole, its height mirrors your latitude."},
                            {"q": "One degree of latitude corresponds to about…", "options": ["111 km anywhere on Earth", "111 km only at the poles", "1,110 km"], "answer": "111 km anywhere on Earth", "explain": "Earth's circumference of ~40,000 km over 360 degrees gives about 111 km per degree of latitude."},
                        ],
                    },
                },
                {
                    "slug": "monsoon-rates",
                    "title": "Monsoon Sailing: Rates, Ratios, and the Indian Ocean Trade",
                    "order": 6,
                    "minutes": 25,
                    "summary": "The seasonal winds that made round-trip trade possible — computed with rate × time.",
                    "learn": [
                        {"type": "p", "text": "The Indian Ocean has a superpower the Atlantic lacks: monsoon winds that reverse direction with the seasons. Sailors from the Swahili coast rode the northeast monsoon (roughly November–March) toward India, and returned on the southwest monsoon (roughly June–September). ThePeriplus of the Erythraean Sea, a 1st-century Greek-Egyptian trading guide, describes these routes in detail, and Swahili coast ports like Kilwa and Mombasa grew wealthy as the western anchor of this system. Round-trip trade that was impossible elsewhere became routine mathematics here."},
                        {"type": "list", "items": [
                            "Distance = rate × time: a dhow averaging 5 knots (nautical miles/hour) covers 120 nautical miles in 24 hours.",
                            "Mogadishu to Calicut is roughly 3,600 nautical miles — about 30 sailing days at 5 knots, matching historical voyage lengths.",
                            "Monsoon timing created natural trade calendars: arrive, trade months, return — the year organized by wind.",
                        ]},
                        {"type": "example", "title": "Do the math", "text": "A dhow sails 3,600 nautical miles at an average 6 knots: time = distance ÷ rate = 3,600 ÷ 6 = 600 hours ≈ 25 days. If it waits 90 days in port, the whole round trip takes about 25 + 90 + 25 ≈ 140 days — under five months, all inside one monsoon cycle."},
                        {"type": "activity", "title": "Voyage planner", "text": "Plan a voyage: choose a rate (4–7 knots) and compute sailing days for a 3,600-mile leg. Add a 60-day port stay and compute your total trip. Then compare with a classmate who chose a different rate."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of monsoon navigation math.",
                        "questions": [
                            {"q": "Indian Ocean trade became reliable round-trip trade because…", "options": ["monsoon winds reverse seasonally, so ships can ride one wind out and another back", "ships were faster than in the Atlantic", "the ocean is smaller than the Atlantic"], "answer": "monsoon winds reverse seasonally, so ships can ride one wind out and another back", "explain": "Seasonal wind reversal made scheduled, repeatable voyages possible — the foundation of the trade."},
                            {"q": "At 5 knots, a 3,600-nautical-mile voyage takes about…", "options": ["30 days", "3 days", "300 days"], "answer": "30 days", "explain": "Time = 3,600 ÷ 5 = 720 hours = 30 days."},
                        ],
                    },
                },
            ],
        },
    ],
}
