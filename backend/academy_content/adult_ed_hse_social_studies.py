"""Adult Education Social Studies (HSE preparation — full published course)."""

ADULT_ED_HSE_SOCIAL_STUDIES = {
    "slug": "adult-ed-hse-social-studies",
    "title": "Adult Education Social Studies",
    "summary": "Civics, government, history, economics, geography, and evidence-based reasoning.",
    "description": (
        "This course builds the knowledge and reasoning skills needed for HSE/GED "
        "social studies and active citizenship. Topics span U.S. government and civics, "
        "world and U.S. history, economics, geography, and the analysis of primary "
        "and secondary sources."
    ),
    "subject": "adult_ed",
    "subject_label": "Adult Education",
    "track": "adult_ed",
    "tracks": ["adult_ed"],
    "grades": ["adult"],
    "grade_label": "Adult",
    "status": "published",
    "audience": "Adult learners preparing for HSE/GED social studies or community involvement.",
    "est_hours": 30,
    "passing_score": 80,
    "learning_objectives": [
        "Describe the structure and functions of U.S. government.",
        "Identify rights and responsibilities of citizens.",
        "Analyze primary and secondary historical sources.",
        "Understand basic economic principles and systems.",
        "Read and interpret maps, charts, and political cartoons.",
        "Evaluate evidence-based arguments about social issues.",
    ],
    "units": [
        {
            "slug": "civics-and-government",
            "title": "Civics and Government",
            "summary": "Constitution, branches, elections, and citizenship.",
            "order": 1,
            "lessons": [
                {
                    "slug": "constitution-and-branches",
                    "title": "The Constitution and Branches of Government",
                    "order": 1,
                    "minutes": 20,
                    "summary": "Structure, separation of powers, and amendments.",
                    "learn": [
                        {"type": "p", "text": "The U.S. Constitution, written in 1787, is the supreme law. It creates three branches with separate powers to prevent tyranny. The first ten amendments are the Bill of Rights."},
                        {"type": "list", "items": [
                            "Legislative: makes laws (Congress: House + Senate).",
                            "Executive: carries out laws (President).",
                            "Judicial: interprets laws (Supreme Court).",
                            "Checks and balances limit each branch.",
                        ]},
                        {"type": "example", "title": "Amendments", "text": "1st Amendment: freedom of speech, religion, press, assembly, petition. 2nd: right to bear arms. 19th: women's suffrage."},
                    ],
                    "check": {
                        "prompt": "Show what you know about the Constitution and branches.",
                        "questions": [
                            {"q": "Which article creates the legislative branch?", "options": ["Article I", "Article II", "Article III"], "answer": "Article I", "explain": "Article I establishes Congress."},
                            {"q": "What are the first ten amendments called?", "options": ["Bill of Rights", "Preamble", "Articles"], "answer": "Bill of Rights", "explain": "The Bill of Rights guarantees fundamental freedoms."},
                        ],
                    },
                },
                {
                    "slug": "citizenship-and-rights",
                    "title": "Citizenship and Rights",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Rights, responsibilities, and civic participation.",
                    "learn": [
                        {"type": "p", "text": "Citizenship means membership in a country with both rights and responsibilities. Rights include speech, vote, and due process. Responsibilities include obeying laws, paying taxes, serving on juries, and voting."},
                        {"type": "list", "items": [
                            "Natural-born or naturalized citizenship.",
                            "Vote in federal, state, and local elections.",
                            "Serve on a jury when called.",
                            "Pay federal, state, and local taxes.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about citizenship.",
                        "questions": [
                            {"q": "Which is a responsibility of citizenship?", "options": ["paying taxes", "ignoring laws", "avoiding juries"], "answer": "paying taxes", "explain": "Paying taxes is a legal and civic duty."},
                            {"q": "Who can vote in U.S. federal elections?", "options": ["citizens 18 and older", "everyone living here", "only men"], "answer": "citizens 18 and older", "explain": "The 26th Amendment set the voting age at 18."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "history-economics-geography",
            "title": "History, Economics, and Geography",
            "summary": "Key events, economic systems, and geographic literacy.",
            "order": 2,
            "lessons": [
                {
                    "slug": "us-and-world-history",
                    "title": "U.S. and World History",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Major eras, movements, and turning points.",
                    "learn": [
                        {"type": "p", "text": "History is the study of past events and their causes. Understanding history helps us make better decisions today. Key themes include revolution, industrialization, civil rights, and globalization."},
                        {"type": "list", "items": [
                            "Revolutionary War: independence from Britain.",
                            "Civil War: union preservation and slavery.",
                            "Civil Rights Movement: equality under law.",
                            "Industrialization: machines, factories, cities.",
                        ]},
                        {"type": "example", "title": "Cause and effect", "text": "Taxation without representation caused colonial protest, which led to the Declaration of Independence."},
                    ],
                    "check": {
                        "prompt": "Show what you know about U.S. and world history.",
                        "questions": [
                            {"q": "The Civil War was fought over…", "options": ["slavery and union", "taxes only", "religion"], "answer": "slavery and union", "explain": "Disputes over slavery and states' rights led to the Civil War."},
                            {"q": "Which movement fought for equal rights in the 1950s and 1960s?", "options": ["Civil Rights Movement", "Labor Movement", "Temperance Movement"], "answer": "Civil Rights Movement", "explain": "The Civil Rights Movement worked to end segregation and discrimination."},
                        ],
                    },
                },
                {
                    "slug": "economics-and-geography",
                    "title": "Economics and Geography",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Supply and demand, GDP, and map reading.",
                    "learn": [
                        {"type": "p", "text": "Economics studies how people use resources. Supply is how much is available; demand is how much people want. Geography looks at places, regions, and human-environment interaction."},
                        {"type": "list", "items": [
                            "Supply up → price down; demand up → price up.",
                            "GDP = total value of goods and services produced.",
                            "Maps show location, scale, direction, and symbols.",
                            "Choropleth maps use color to show data by region.",
                        ]},
                        {"type": "example", "title": "Market example", "text": "If a hurricane destroys orange crops, supply drops and prices rise."},
                    ],
                    "check": {
                        "prompt": "Show what you know about economics and geography.",
                        "questions": [
                            {"q": "If demand increases and supply stays the same, price tends to…", "options": ["rise", "fall", "stay the same"], "answer": "rise", "explain": "More buyers competing for the same goods pushes prices up."},
                            {"q": "On a map, the legend explains…", "options": ["what symbols mean", "the compass direction", "the population"], "answer": "what symbols mean", "explain": "A map key or legend explains symbols, colors, and lines."},
                        ],
                    },
                },
                {
                    "slug": "primary-and-secondary-sources",
                    "title": "Primary and Secondary Sources",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Evaluate documents for bias, purpose, and reliability.",
                    "learn": [
                        {"type": "p", "text": "A primary source is a direct account from the time of an event (diary, letter, speech, photograph). A secondary source interprets or analyzes (textbook, documentary). Evaluate all sources for author, date, purpose, and bias."},
                        {"type": "list", "items": [
                            "Primary: created at the time by someone who witnessed the event.",
                            "Secondary: created later by someone analyzing the event.",
                            "Bias: a preference that may skew the account.",
                            "Corroboration: check multiple sources.",
                        ]},
                        {"type": "activity", "title": "Source sort", "text": "Given a list of documents about a historical event, sort them into primary and secondary. Write two questions you would ask each author."},
                    ],
                    "check": {
                        "prompt": "Show what you know about primary and secondary sources.",
                        "questions": [
                            {"q": "A diary written during a war is a…", "options": ["primary source", "secondary source", "tertiary source"], "answer": "primary source", "explain": "Primary sources are first-hand accounts from the time of the event."},
                            {"q": "A history textbook is a…", "options": ["secondary source", "primary source", "propaganda"], "answer": "secondary source", "explain": "Secondary sources interpret and summarize primary sources."},
                        ],
                    },
                },
            ],
        },
    ],
}
