"""Applied Science: Indigenous Astronomy and Maritime Navigation (published).

Astronomy from observation, not from a textbook slide deck: the Dogon
calendar cycle, the star lore of Namibian !Kung and Zambian Tonga farmers,
and African maritime navigation — then the modern pipeline of Black
aerospace contributors. Students build and verify a real observation.
"""

INDIGENOUS_ASTRONOMY_MARITIME_NAVIGATION = {
    "slug": "indigenous-astronomy-maritime-navigation",
    "title": "Indigenous Astronomy and Maritime Navigation",
    "summary": "Dogon star cycles, African agricultural calendars, and ocean navigation — plus Black aerospace today.",
    "description": (
        "This applied-science course reads the sky the way African societies did — as "
        "a clock, a calendar, and a chart — and then follows the same observational "
        "method into the modern pipeline. Students examine the Dogon cycle of Sirius "
        "carefully, test its claims rather than mythologize them, learn how African "
        "farmers set planting from the heliacal rising of stars, study monsoon "
        "navigation and Swahili and Phoenician-era East African seafaring, and finish "
        "with the physics and careers of Black aerospace professionals."
    ),
    "subject": "science",
    "subject_label": "Science",
    "track": "scholar",
    "tracks": ["scholar", "builder"],
    "grades": ["9", "10", "11", "12"],
    "grade_label": "Grades 9–12",
    "status": "published",
    "audience": "Applied science students studying astronomy and navigation.",
    "est_hours": 26,
    "passing_score": 80,
    "learning_objectives": [
        "Explain how rising and setting stars are used as calendars.",
        "Describe the Dogon Sirius tradition and evaluate its evidentiary status honestly.",
        "Explain how African farmers used star and moon phases to time planting.",
        "Describe how Swahili and Austronesian sailors navigated the Indian Ocean by stars, currents, and birds.",
        "Compute coordinates and calculate latitude from Polaris or the Southern Cross.",
        "Describe the pipeline of Black contributors to aerospace and the physics behind their fields.",
    ],
    "units": [
        {
            "slug": "sky-as-calendar",
            "title": "The Sky as Calendar",
            "summary": "Stars as a clock for farming and ritual.",
            "order": 1,
            "lessons": [
                {
                    "slug": "heliacal-rising",
                    "title": "Heliacal Rising and the Planting Calendar",
                    "order": 1,
                    "minutes": 26,
                    "summary": "A star appears before sunrise; the rains are coming.",
                    "learn": [
                        {"type": "p", "text": "A heliacal rising is the first appearance of a star at dawn after weeks of being lost in the sun's glare. Because it recurs on the same solar calendar date each year, it is an accurate calendar signal. Southern African farmers, Bantu-speaking and San alike, timed planting to star events; in West Africa, the heliacal rising of the Pleiades and of Canopus carried agricultural and ritual meaning."},
                        {"type": "list", "items": [
                            "Rising: a star reappears at dawn, same date each year — an annual calendar.",
                            "Pleiades: visible cluster used widely in African and Mediterranean farming calendars.",
                            "Moon phases and the 19-year Metonic cycle helped plan multi-year cycles.",
                        ]},
                        {"type": "example", "title": "A cross-check", "text": "The Pleiades rise just before the planting season in both East Africa and the Mediterranean — the same star serving the same function across cultures."},
                        {"type": "activity", "title": "Observe", "text": "Record the rise time of one bright star for five mornings. Predict the next rise and compare. Note the date and what season it indicates."},
                    ],
                    "check": {
                        "prompt": "Check what you know about star calendars.",
                        "questions": [
                            {"q": "A heliacal rising is useful as a calendar because it…", "options": ["recurs on the same solar date each year", "happens randomly", "only occurs in winter"], "answer": "recurs on the same solar date each year", "explain": "Its fixed solar-date return makes it a reliable annual marker."},
                            {"q": "Ancient farmers used the Pleiades to…", "options": ["time planting", "measure weight", "weave cloth"], "answer": "time planting", "explain": "Star events marked the agricultural year."},
                        ],
                    },
                },
                {
                    "slug": "dogon-sirius",
                    "title": "The Dogon Sirius Tradition, Evaluated",
                    "order": 2,
                    "minutes": 26,
                    "summary": "A famous claim, examined with evidence rather than awe or dismissal.",
                    "learn": [
                        {"type": "p", "text": "The Dogon people of Mali are reported by ethnographers to have known that Sirius has a companion star (Sirius B), an invisible dwarf detected by Western astronomy only in 1862. The claim is contested: anthropologists note that Dogon elders also describe the companion in terms that match modern telescopes, while other scholars document contact with French observers in the colonial period. The honest handling of this is a science lesson in itself: hold the claim, demand the evidence, state the uncertainty."},
                        {"type": "list", "items": [
                            "Report: Dogon tradition describes Sirius's companion and its short orbit.",
                            "Counter-evidence: accounts differ among informants, and colonial contact introduced astronomic ideas.",
                            "Standard of proof: extraordinary claims require documentary evidence of prior knowledge.",
                            "Outcome: the case is inconclusive, and it must be reported as such.",
                        ]},
                        {"type": "tip", "text": "Amazement and dismissal are both failures of reasoning; 'the evidence does not settle it' is the accurate answer."},
                        {"type": "activity", "title": "Evaluate", "text": "Write a half-page note on what evidence would settle the claim, and state which of those pieces are currently missing."},
                    ],
                    "check": {
                        "prompt": "Check your reasoning about the Dogon claim.",
                        "questions": [
                            {"q": "Sirius B was detected by western telescopes in…", "options": ["1862", "1990", "1 BCE"], "answer": "1862", "explain": "It was inferred by Alvan Clark from Sirius's wobble in 1862."},
                            {"q": "The best current statement of the Dogon Sirius evidence is that it is…", "options": ["inconclusive", "proven ancient and exact", "fraudulent and worthless"], "answer": "inconclusive", "explain": "Accounts conflict and colonial contact is documented, so the claim cannot be settled."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "navigation",
            "title": "Navigation: Ocean and Constellation",
            "summary": "Crossing an ocean with no instruments.",
            "order": 2,
            "lessons": [
                {
                    "slug": "swahili-and-indian-ocean",
                    "title": "East African Mariners",
                    "order": 3,
                    "minutes": 26,
                    "summary": "Monsoon sailing, star paths, and natural signs.",
                    "learn": [
                        {"type": "p", "text": "Swahili city-states — Kilwa, Mombasa, Zanzibar, Mogadishu — traded with Arabia, Persia, India, and Indonesia using dhows that sailed with the monsoons. Navigators held star paths in memory, read the ocean for swell patterns that indicate islands beyond the horizon, watched bird flight, and measured latitude with a kamal. The same observational craft crossed the Pacific from Madagascar and the Comoros."},
                        {"type": "list", "items": [
                            "Monsoon calendar: sail east in one season, west in the other.",
                            "Star paths: sequences of rising/setting stars held by a school of navigators.",
                            "Swell and bird signs: distant islands announced by waves and birds.",
                            "Kamal: a knotted board for measuring star altitude.",
                        ]},
                        {"type": "example", "title": "A measurement", "text": "A kamal with the board at the teeth gives the altitude of Polaris to within a degree or two — accurate enough for a latitude fix."},
                        {"type": "activity", "title": "Build a kamal", "text": "Make a kamal from string and card. Measure the altitude of Polaris (or the Southern Cross's foot) and compute your latitude."},
                    ],
                    "check": {
                        "prompt": "Check what you know about navigation.",
                        "questions": [
                            {"q": "Indian Ocean dhows used the monsoons to…", "options": ["sail east in one season and west in the other", "sail only north", "stay in port"], "answer": "sail east in one season and west in the other", "explain": "The monsoon system gives predictable winds in both directions."},
                            {"q": "A kamal measures…", "options": ["star altitude for latitude", "water depth", "wave height"], "answer": "star altitude for latitude", "explain": "The knotted board measures how high a star stands."},
                        ],
                    },
                },
                {
                    "slug": "compute-a-fix",
                    "title": "Compute a Fix",
                    "order": 4,
                    "minutes": 26,
                    "summary": "Latitude from a star, longitude from time.",
                    "learn": [
                        {"type": "p", "text": "Latitude comes from a celestial body's altitude above the horizon: latitude equals 90° minus the observed altitude of Polaris in the northern hemisphere, or from the Southern Cross by a similar construction. Longitude requires a clock: at local noon, compare the local time to the clock's home time; each hour of difference is 15 degrees of longitude."},
                        {"type": "list", "items": [
                            "Latitude = 90° − Polaris altitude (northern).",
                            "Southern Cross: estimate the south celestial pole's altitude.",
                            "Longitude: 15° per hour of time difference from home.",
                            "Practical: landfall is then combined with swell and bird observations.",
                        ]},
                        {"type": "example", "title": "Worked", "text": "Polaris altitude 41° gives latitude 49° N. Local noon at 3 pm home time means 45° west of home longitude."},
                        {"type": "activity", "title": "Fix yourself", "text": "From your altitude and clock readings, compute a latitude and longitude. Then compare with a phone and explain any difference."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of celestial navigation.",
                        "questions": [
                            {"q": "Latitude equals…", "options": ["90° minus Polaris' altitude", "15 times the hour", "the sun's diameter"], "answer": "90° minus Polaris' altitude", "explain": "Polaris sits over the pole, so its altitude equals your latitude."},
                            {"q": "Longitude can be found if you know…", "options": ["your local time compared to home time", "the moon's phase", "your shadow length"], "answer": "your local time compared to home time", "explain": "Time differences convert directly into degrees."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "aerospace-pipeline",
            "title": "Aerospace: The Modern Pipeline",
            "summary": "Physics, history, and the people who built the field.",
            "order": 3,
            "lessons": [
                {
                    "slug": "black-contributors-aerospace",
                    "title": "Black Contributors to Aerospace",
                    "order": 5,
                    "minutes": 26,
                    "summary": "From Katherine Johnson's orbits to Mae Jemison's flight to modern control rooms.",
                    "learn": [
                        {"type": "p", "text": "Black scientists and engineers shaped spaceflight from the beginning. Katherine Johnson computed the trajectory of the Friendship 7 flight and the Apollo lunar flights. Mary Jackson became NASA's first Black female engineer. Guion Bluford was the first African American in space and Mae Jemison the first African American woman. Ronald McNair, a physicist, died on Challenger. Today, Black engineers lead guidance, propulsion, and mission control teams across agencies and companies."},
                        {"type": "list", "items": [
                            "Katherine Johnson: orbital mechanics calculations verified by machine.",
                            "Mary Jackson: engineer and advocate for advancement.",
                            "Mae Jemison: physician, and founder of a science-literacy nonprofit.",
                            "Ronald McNair: laser physicist, STS-51-L crew.",
                        ]},
                        {"type": "example", "title": "The physics", "text": "Johnson's work applied Kepler's laws and Newtonian gravity to a two-body problem, then verified numerically before digital flight."},
                        {"type": "activity", "title": "Profile", "text": "Write a one-page profile of one contributor, naming the specific equations or discipline they worked in."},
                    ],
                    "check": {
                        "prompt": "Check what you know about aerospace contributors.",
                        "questions": [
                            {"q": "Katherine Johnson's work supported…", "options": ["orbital trajectory computation", "weather forecasting", "agriculture"], "answer": "orbital trajectory computation", "explain": "She computed the trajectories for Friendship 7 and the Apollo missions."},
                            {"q": "Mae Jemison is significant as…", "options": ["the first African American woman in space", "the first woman in space", "a moon walker"], "answer": "the first African American woman in space", "explain": "She flew on STS-47 in 1992 as a physician-astronaut."},
                        ],
                    },
                },
                {
                    "slug": "observe-and-report",
                    "title": "Capstone: Observe and Report",
                    "order": 6,
                    "minutes": 28,
                    "summary": "Make a genuine observation and write it up.",
                    "learn": [
                        {"type": "p", "text": "Your capstone is a real observation: track a bright star, planet, or the Moon for a week, record position and time, and analyze what you saw. Then compare your result with a source — and where they disagree, explain which is right and why."},
                        {"type": "list", "items": [
                            "Observe: date, time, altitude and direction of a chosen object.",
                            "Predict: where should it move each night? Compute it.",
                            "Compare: check against a data source, then explain any difference.",
                            "Report: method, data, analysis, and conclusion.",
                        ]},
                        {"type": "activity", "title": "Write the report", "text": "Complete your observation log and write a two-page report: method, data table, graph, and conclusion."},
                    ],
                    "check": {
                        "prompt": "Check what makes a good observation report.",
                        "questions": [
                            {"q": "A scientific observation report must include…", "options": ["date, time, method, and data", "only a photograph", "only a prediction"], "answer": "date, time, method, and data", "explain": "Reproducibility requires full documentation."},
                            {"q": "When prediction and observation disagree, you should…", "options": ["recheck the method and explain the difference", "delete the data", "ignore both"], "answer": "recheck the method and explain the difference", "explain": "Discrepancy is information, to be explained, not hidden."},
                        ],
                    },
                },
            ],
        },
    ],
}
