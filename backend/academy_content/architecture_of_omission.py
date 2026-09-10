"""The Architecture of Omission: Exposing the Logic Gaps in U.S. History.

Published scholar-track social studies course for grades 9-12.
Students deconstruct historical narratives by cross-examining primary
source documents against institutional outcomes.
"""

ARCHITECTURE_OF_OMISSION = {
    "slug": "architecture-of-omission",
    "title": "The Architecture of Omission: Exposing the Logic Gaps in U.S. History",
    "summary": "Systematic analysis of standard curriculum omissions — expropriation, the legal mechanics of racial capitalism, and the sanitization of colonial expansion — through primary-source cross-examination.",
    "description": (
        "Students deconstruct historical narratives by cross-examining primary source documents against institutional outcomes. "
        "The course teaches historical criticism: detecting gaps, comparing competing narratives, and constructing a more complete history."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "scholar",
    "tracks": ["scholar"],
    "grades": ["9", "10", "11", "12"],
    "grade_label": "Grades 9–12",
    "status": "published",
    "audience": "High school students studying U.S. history and historical method.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": [
        "Explain how historical narratives are constructed.",
        "Identify missing voices in standard histories.",
        "Analyze primary sources against official narratives.",
        "Examine the legal mechanics of segregation and exclusion.",
        "Compare competing historical interpretations.",
        "Detect gaps between claims and evidence.",
        "Research an omitted historical subject.",
        "Create a 'Missing Chapter' for a U.S. history textbook.",
    ],
    "units": [
        {
            "slug": "how-narratives-are-built",
            "title": "How Narratives Are Built",
            "summary": "Selection, periodization, framing, and primary versus secondary sources.",
            "order": 1,
            "lessons": [
                {
                    "slug": "how-historical-narratives-are-built",
                    "title": "How Historical Narratives Are Built",
                    "order": 1,
                    "minutes": 20,
                    "summary": "How historians choose what to include.",
                    "learn": [
                        {"type": "p", "text": "A historical narrative is not simply 'what happened.' It is the product of deliberate choices: what to emphasize, what to leave out, where to begin, and what language to use. Every textbook is an argument about what matters."},
                        {"type": "list", "items": [
                            "Selection: deciding which events, people, and places are worthy of space.",
                            "Periodization: choosing where to draw the starting and ending lines of an era.",
                            "Framing: describing events through a chosen lens — economic, political, cultural.",
                            "Sources: relying on written records, oral testimony, material culture, or physical evidence.",
                        ]},
                        {"type": "example", "title": "Textbook selection", "text": "Compare the index of two U.S. history textbooks. Notice which topics get one page and which get chapters. That pattern is selection in action."},
                        {"type": "activity", "title": "Audit a chapter", "text": "Pick one textbook chapter. List the ten people most discussed. Ask: whose voices are absent from that list?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about narrative construction.",
                        "questions": [
                            {"q": "Selection in history-writing refers to…", "options": ["choosing which events and people to include", "counting casualties", "translating documents"], "answer": "choosing which events and people to include", "explain": "Selection is the core editorial act that shapes every historical narrative."},
                            {"q": "Periodization means…", "options": ["dividing history into named blocks of time", "writing in paragraphs", "measuring distance"], "answer": "dividing history into named blocks of time", "explain": "Periodization creates eras; the choice of where to cut shapes how events are connected."},
                        ],
                    },
                },
                {
                    "slug": "whose-voice-is-missing",
                    "title": "Whose Voice Is Missing?",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Enslaved people, Indigenous nations, women, workers, immigrants, and local communities.",
                    "learn": [
                        {"type": "p", "text": "For much of U.S. history, the people who wrote the records were wealthy, educated, and in power. Their words filled the archives. Other perspectives — enslaved people, Indigenous nations, women, workers, immigrants, local communities — were often unwritten, destroyed, or ignored."},
                        {"type": "list", "items": [
                            "Enslaved people: largely excluded from official records unless they appeared in court or sale documents.",
                            "Indigenous nations: oral traditions and treaty records often sidelined in favor of settler narratives.",
                            "Women: underrepresented as political actors despite continuous political action.",
                            "Workers and immigrants: labor actions and community struggles underreported in mainstream texts.",
                        ]},
                        {"type": "example", "title": "Slave schedules", "text": "U.S. census slave schedules listed only the age, sex, and color of enslaved people by owner name. The enslaved were nameless in the nation's most official record."},
                        {"type": "activity", "title": "Source identification", "text": "Choose one omitted group from this lesson. Find one primary source that speaks for that group and one secondary source that omits them. Briefly compare the two accounts."},
                    ],
                    "check": {
                        "prompt": "Show what you know about missing voices.",
                        "questions": [
                            {"q": "Enslaved people were most often excluded from historical records by…", "options": ["being counted only as property, not individuals", "refusing to participate", "lacking any written language"], "answer": "being counted only as property, not individuals", "explain": "Slave schedules and property records reduced people to items; self-expression was suppressed."},
                            {"q": "A historian recovering a missing voice should…", "options": ["look for unconventional sources and oral testimony", "ignore silence and move on", "accept the dominant account as complete"], "answer": "look for unconventional sources and oral testimony", "explain": "Court records, letters, songs, and interviews can all restore suppressed perspectives."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "expansion-and-displacement",
            "title": "Expansion and Displacement",
            "summary": "Treaties, removal, land transfer, and the economics of slavery.",
            "order": 2,
            "lessons": [
                {
                    "slug": "indigenous-land-and-expansion",
                    "title": "Indigenous Land and Expansion",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Treaties, removal, land transfer, and military conflict.",
                    "learn": [
                        {"type": "p", "text": "U.S. expansion across North America was not a peaceful migration. It was a legal and military project. Treaties were made, broken, or signed under duress. Removal policies — especially the Trail of Tears — transferred millions of acres from Indigenous nations to settlers and the federal government."},
                        {"type": "list", "items": [
                            "Treaties: 400+ treaties between the U.S. and Indigenous nations, most broken or renegotiated under pressure.",
                            "Removal: the Indian Removal Act of 1830 forced eastern nations onto western reservations.",
                            "Land transfer: federal surveys, allotment, and court rulings systematically reduced Indigenous landholdings.",
                            "Military conflict: wars, massacres, and scorched-earth campaigns accompanied every major push west.",
                        ]},
                        {"type": "example", "title": "Worcester v. Georgia", "text": "In 1832, the Supreme Court ruled that Georgia could not impose its laws on Cherokee territory. President Jackson refused to enforce the ruling, and removal proceeded anyway."},
                        {"type": "activity", "title": "Treaty analysis", "text": "Read one treaty between the U.S. and an Indigenous nation. List three promises the treaty made and three outcomes that contradicted them."},
                    ],
                    "check": {
                        "prompt": "Show what you know about land transfer narratives.",
                        "questions": [
                            {"q": "A treaty is best defined as…", "options": ["a formal agreement between two sovereign nations", "a state law", "an executive order"], "answer": "a formal agreement between two sovereign nations", "explain": "Treaties are international agreements; the U.S. Constitution treats them as the supreme law of the land."},
                            {"q": "The Trail of Tears is an example of…", "options": ["forced removal of Indigenous nations from their lands", "a voluntary migration", "a trade agreement"], "answer": "forced removal of Indigenous nations from their lands", "explain": "The Cherokee, Muscogee, Seminole, Chickasaw, and Choctaw nations were forcibly relocated, causing thousands of deaths."},
                        ],
                    },
                },
                {
                    "slug": "slavery-beyond-the-plantation",
                    "title": "Slavery Beyond the Plantation",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Finance, insurance, manufacturing, transportation, and law.",
                    "learn": [
                        {"type": "p", "text": "Slavery was not only an agricultural system. It was a national economic engine that touched banking, insurance, manufacturing, shipping, and law. Northern merchants, Southern planters, and European manufacturers all profited from enslaved labor."},
                        {"type": "list", "items": [
                            "Finance: banks accepted enslaved people as collateral for loans.",
                            "Insurance: companies wrote policies on enslaved lives and cargo.",
                            "Manufacturing: Northern textile mills processed Southern cotton.",
                            "Transportation: railroads and ships moved enslaved people and cash crops.",
                            "Law: court systems enforced contracts, sale deeds, and fugitive slave laws.",
                        ]},
                        {"type": "example", "title": "Insurance policy", "text": "An 1847 policy from a Rhode Island insurer covered 'the perils of the sea and insurrection' on a ship carrying 147 enslaved people. Human lives were cargo."},
                        {"type": "activity", "title": "Document comparison", "text": "Compare a Northern bank's ledger showing a mortgage on enslaved collateral with a Southern plantation's inventory of enslaved people. What does each document reveal about the economy of slavery?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about slavery's economic reach.",
                        "questions": [
                            {"q": "Northern banks participated in slavery by…", "options": ["accepting enslaved people as loan collateral", "buying cotton directly", "fighting in the Civil War"], "answer": "accepting enslaved people as loan collateral", "explain": "Collateralized loans tied Northern finance directly to enslaved human property."},
                            {"q": "Insurance companies wrote policies on…", "options": ["enslaved people treated as cargo or property", "only ships and cargo", "free laborers only"], "answer": "enslaved people treated as cargo or property", "explain": "Slave insurance listed enslaved people by name and value, confirming their treatment as commodities."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "reconstructing-the-narrative",
            "title": "Reconstructing the Narrative",
            "summary": "Constitutional amendments, Black political participation, schools, land, and white resistance.",
            "order": 3,
            "lessons": [
                {
                    "slug": "reconstruction-beyond-the-textbook-chapter",
                    "title": "Reconstruction Beyond the Textbook Chapter",
                    "order": 5,
                    "minutes": 20,
                    "summary": "Constitutional amendments, Black political participation, schools, land, and white resistance.",
                    "learn": [
                        {"type": "p", "text": "Standard textbooks often compress Reconstruction into a single failed chapter. In reality, it was a twelve-year revolution in governance, education, and citizenship. Black men voted, held office, built schools, and rewrote state constitensions before white resistance violently reversed many gains."},
                        {"type": "list", "items": [
                            "13th Amendment (1865): abolished chattel slavery.",
                            "14th Amendment (1868): guaranteed citizenship and equal protection.",
                            "15th Amendment (1870): prohibited denying the vote based on race.",
                            "Black political participation: over 2,000 Black men held public office during Reconstruction.",
                            "Schools: the first free, tax-supported public school systems in the South were built by biracial Reconstruction governments.",
                        ]},
                        {"type": "example", "title": "First Black congressmen", "text": "Hiram Revels (Mississippi, 1870) and Joseph Rainey (South Carolina, 1870) were among the first Black members of Congress. Over 600 served in state legislatures during Reconstruction."},
                        {"type": "activity", "title": "Amendment analysis", "text": "Read the text of the 14th Amendment. Write three ways it was designed to protect formerly enslaved people, then list one way those protections were undermined."},
                    ],
                    "check": {
                        "prompt": "Show what you know about Reconstruction omissions.",
                        "questions": [
                            {"q": "Which amendment abolished chattel slavery?", "options": ["13th Amendment", "14th Amendment", "15th Amendment"], "answer": "13th Amendment", "explain": "The 13th Amendment ended slavery; the 14th and 15th Amendments extended citizenship and voting rights."},
                            {"q": "During Reconstruction, Black political participation included…", "options": ["holding local, state, and federal office", "only voting in secret", "serving only in the military"], "answer": "holding local, state, and federal office", "explain": "More than 2,000 Black men held public office at every level during Reconstruction."},
                        ],
                    },
                },
                {
                    "slug": "the-legal-mechanics-of-segregation",
                    "title": "The Legal Mechanics of Segregation",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Jim Crow, courts, local government, and voting restrictions.",
                    "learn": [
                        {"type": "p", "text": "Segregation was not simply social custom; it was a legal architecture. After Reconstruction, Southern states passed Jim Crow laws mandating separate facilities. Courts upheld these laws. Local governments enforced them through zoning, licensing, and police power. The system was engineered, not organic."},
                        {"type": "list", "items": [
                            "Jim Crow laws: state and local statutes requiring racial segregation in schools, transit, restaurants, and restrooms.",
                            "Courts: Plessy v. Ferguson (1896) established 'separate but equal' as constitutional doctrine.",
                            "Voting: poll taxes, literacy tests, and white primaries disenfranchised Black voters.",
                            "Local government: zoning, building codes, and police enforced residential and commercial segregation.",
                        ]},
                        {"type": "example", "title": "Plessy v. Ferguson", "text": "Homer Plessy, who was seven-eighths white, sat in a whites-only railroad car in New Orleans in 1892 to challenge Louisiana's Separate Car Act. The Supreme Court rejected his challenge, ruling that separate facilities were constitutional if equal."},
                        {"type": "activity", "title": "Case study", "text": "Choose one Jim Crow law from your state or region. Identify who wrote it, who enforced it, and one legal argument used to defend it at the time."},
                    ],
                    "check": {
                        "prompt": "Show what you know about legal segregation mechanisms.",
                        "questions": [
                            {"q": "Plessy v. Ferguson established…", "options": ["the 'separate but equal' doctrine", "desegregation of schools", "the end of Jim Crow"], "answer": "the 'separate but equal' doctrine", "explain": "The 1896 decision allowed segregation to continue legally if facilities were nominally equal."},
                            {"q": "A poll tax was designed to…", "options": ["deter Black and poor voters by requiring payment to vote", "raise revenue for public schools", "register immigrants"], "answer": "deter Black and poor voters by requiring payment to vote", "explain": "Poll taxes were one of many financial and bureaucratic barriers designed to suppress Black voting."},
                        ],
                    },
                },
                {
                    "slug": "housing-and-wealth",
                    "title": "Housing and Wealth",
                    "order": 7,
                    "minutes": 18,
                    "summary": "Redlining, covenants, federal policy, and urban renewal.",
                    "learn": [
                        {"type": "p", "text": "Home ownership is the primary engine of middle-class wealth in the United States. Federal housing policy, redlining, racially restrictive covenants, and urban renewal systematically denied that wealth-building tool to Black families, creating a racial wealth gap that persists today."},
                        {"type": "list", "items": [
                            "Redlining: the HOLC rated neighborhoods by race; Black neighborhoods were colored red and denied mortgages.",
                            "Restrictive covenants: deeds explicitly barred Black and Jewish buyers from white neighborhoods.",
                            "Federal policy: the GI Bill, FHA loans, and VA loans were often denied to Black veterans and homebuyers.",
                            "Urban renewal: highways and 'slum clearance' destroyed Black neighborhoods, displacing families and businesses.",
                        ]},
                        {"type": "example", "title": "HOLC maps", "text": "Home Owners' Loan Corporation maps from the 1930s graded every American neighborhood. 'A' (green) received best lending; 'D' (red) received none. Race was the deciding factor."},
                        {"type": "activity", "title": "Map analysis", "text": "Find a HOLC map for your city online. Identify one 'D' graded neighborhood and one 'A' graded neighborhood. Compare the racial demographics and current wealth levels."},
                    ],
                    "check": {
                        "prompt": "Show what you know about housing policy.",
                        "questions": [
                            {"q": "Redlining refers to…", "options": ["denying mortgages to neighborhoods based on race", "building fences around cities", "painting houses red"], "answer": "denying mortgages to neighborhoods based on race", "explain": "The HOLC and lenders refused investment in Black neighborhoods, stunting generational wealth."},
                            {"q": "Racially restrictive covenants…", "options": ["were clauses in deeds barring non-white buyers", "required integrated housing", "funded public schools"], "answer": "were clauses in deeds barring non-white buyers", "explain": "These private contracts enforced segregation by law until the Supreme Court struck them down in 1948."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "labor-and-foreign-policy",
            "title": "Labor and Foreign Policy",
            "summary": "Workers, Black labor, immigration, unions, and economic expansion abroad.",
            "order": 4,
            "lessons": [
                {
                    "slug": "labor-and-industrial-america",
                    "title": "Labor and Industrial America",
                    "order": 8,
                    "minutes": 18,
                    "summary": "Workers, Black labor, immigration, unions, and company towns.",
                    "learn": [
                        {"type": "p", "text": "The story of American industrialism often focuses on inventors and captains of industry. The labor story — the workers who built the factories, extracted the resources, and risked their lives — is frequently minimized. Within that labor force, Black workers, immigrant workers, and women faced the sharpest exploitation."},
                        {"type": "list", "items": [
                            "Immigrant labor: Irish, Italian, Chinese, Mexican, and Eastern European workers filled dangerous, low-paying jobs.",
                            "Black labor: after emancipation, sharecropping and convict leasing trapped many in conditions close to slavery.",
                            "Unions: many craft unions excluded Black and immigrant workers; inclusive organizing changed the balance of power.",
                            "Company towns: employers controlled housing, stores, and law, keeping workers in permanent debt.",
                        ]},
                        {"type": "example", "title": "Company town", "text": "In Pullman, Illinois, the Pullman Company owned the houses, stores, and utilities. Workers were paid in company scrip usable only at company stores. When the company cut wages without cutting rents, the nationwide Pullman Strike of 1894 followed."},
                        {"type": "activity", "title": "Compare perspectives", "text": "Find a newspaper account of a strike from the 1870s–1890s. Compare it with a firsthand account from a worker. Identify two ways the narratives differ."},
                    ],
                    "check": {
                        "prompt": "Show what you know about labor history.",
                        "questions": [
                            {"q": "Company towns were designed primarily to…", "options": ["control workers and maximize profit", "provide affordable housing", "educate children"], "answer": "control workers and maximize profit", "explain": "By owning housing, stores, and currency, employers extracted labor at the lowest possible cost."},
                            {"q": "Black workers after emancipation were often trapped by…", "options": ["sharecropping and convict leasing", "high wages and benefits", "easy access to capital"], "answer": "sharecropping and convict leasing", "explain": "These systems bound Black workers to landowners and prisons through debt and criminal law."},
                        ],
                    },
                },
                {
                    "slug": "foreign-policy-and-economic-expansion",
                    "title": "Foreign Policy and Economic Expansion",
                    "order": 9,
                    "minutes": 18,
                    "summary": "Territories, trade, military power, and resources.",
                    "learn": [
                        {"type": "p", "text": "U.S. foreign policy is often narrated as a mission to spread democracy. A competing interpretation emphasizes economic and military expansion: acquiring territories, controlling trade routes, and securing raw materials. Both narratives exist; the task of the historian is to weigh the evidence for each."},
                        {"type": "list", "items": [
                            "Territories: Hawaii, Puerto Rico, Guam, the Philippines, and the U.S. Virgin Islands came under American control between 1898 and 1917.",
                            "Trade: the Open Door Policy in China and banana republic interventions secured markets for U.S. goods.",
                            "Military power: the Spanish-American War and subsequent occupations projected American force abroad.",
                            "Resources: sugar, tobacco, oil, rubber, and minerals drove much of the expansionist agenda.",
                        ]},
                        {"type": "example", "title": "Annexation of Hawaii", "text": "In 1893, U.S. Marines supported American planters in overthrowing Queen Liliuokalani. Hawaii was annexed in 1898. The planters' sugar interests and a naval coaling station were the primary motives."},
                        {"type": "activity", "title": "Policy analysis", "text": "Compare two newspaper editorials from the Spanish-American War era. One supporting annexation and one opposing it. Identify the economic and moral arguments each side uses."},
                    ],
                    "check": {
                        "prompt": "Show what you know about foreign policy narratives.",
                        "questions": [
                            {"q": "The Open Door Policy aimed to…", "options": ["secure equal trading rights in China", "end all foreign trade", "isolate the United States"], "answer": "secure equal trading rights in China", "explain": "The policy sought access to Chinese markets for American goods alongside European powers."},
                            {"q": "Economic interpretations of U.S. expansion emphasize…", "options": ["markets, resources, and strategic advantage", "purely ideological spread of democracy", "religious missions only"], "answer": "markets, resources, and strategic advantage", "explain": "Material interests — access to raw materials and consumers — have consistently driven territorial acquisition."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "method-and-capstone",
            "title": "Method and Capstone",
            "summary": "Evaluating competing narratives, researching omitted subjects, and building a more complete history.",
            "order": 5,
            "lessons": [
                {
                    "slug": "comparing-competing-historical-narratives",
                    "title": "Comparing Competing Historical Narratives",
                    "order": 10,
                    "minutes": 20,
                    "summary": "Multiple interpretations of the same event, identifying evidence, missing evidence, language choices, assumptions, and conclusions.",
                    "learn": [
                        {"type": "p", "text": "Most contested events have multiple narratives. Comparing them is not merely an exercise in opinion. It requires examining evidence, identifying what is missing, analyzing language and framing, and testing the logic of conclusions."},
                        {"type": "list", "items": [
                            "Evidence: what facts does each narrative accept? Which does it ignore?",
                            "Missing evidence: what documents, voices, or data are absent from each account?",
                            "Language choices: words like 'riot,' 'rebellion,' 'uprising,' and 'insurrection' carry moral weight.",
                            "Assumptions: every narrative rests on unstated premises. Identify them before judging the conclusion.",
                        ]},
                        {"type": "example", "title": "Two accounts of 1898", "text": "One account calls the Spanish-American War 'a splendid little war' that liberated Cuba. Another calls it an opportunistic seizure of territory. Compare the evidence each uses and the evidence each ignores."},
                        {"type": "activity", "title": "Side-by-side comparison", "text": "Find two textbook accounts of Reconstruction. Build a table with columns for: events covered, voices included, language used, and conclusions drawn. Rate each for completeness."},
                    ],
                    "check": {
                        "prompt": "Show what you know about evaluating narratives.",
                        "questions": [
                            {"q": "When comparing narratives, missing evidence should be…", "options": ["flagged as a potential gap or bias", "ignored if the story sounds convincing", "filled in with personal opinion"], "answer": "flagged as a potential gap or bias", "explain": "What is omitted often reveals more about an author's agenda than what is included."},
                            {"q": "The word 'rebellion' versus 'uprising' matters because…", "options": ["language shapes moral judgment", "they are exact synonyms", "spelling determines accuracy"], "answer": "language shapes moral judgment", "explain": "Framing language influences how readers assign blame and legitimacy."},
                        ],
                    },
                },
                {
                    "slug": "building-a-more-complete-history",
                    "title": "Building a More Complete History",
                    "order": 11,
                    "minutes": 22,
                    "summary": "Researching an omitted subject and integrating new evidence into a coherent narrative.",
                    "learn": [
                        {"type": "p", "text": "Building a more complete history is not simply adding one missing person to a textbook. It is a research process: identify the gap, locate sources, evaluate reliability, compare with existing narratives, and construct a revised account that holds up to scrutiny."},
                        {"type": "list", "items": [
                            "Identify the gap: What is missing from standard narratives?",
                            "Locate sources: Look for court records, oral histories, photographs, material culture, and community archives.",
                            "Evaluate reliability: Who produced the source? Under what conditions? For what purpose?",
                            "Compare: How does the new evidence confirm, complicate, or contradict existing accounts?",
                            "Construct: Write a clear, evidence-based revision that acknowledges uncertainty.",
                        ]},
                        {"type": "example", "title": "Zinn's method", "text": "Howard Zinn's A People's History of the United States (1980) used court records, songs, and personal letters to reconstruct labor and civil rights struggles omitted from standard texts."},
                        {"type": "activity", "title": "Research methodology", "text": "Choose one omitted topic from this course. Find two primary sources and two secondary sources. Evaluate each for perspective and reliability."},
                    ],
                    "check": {
                        "prompt": "Show what you know about historical research.",
                        "questions": [
                            {"q": "When locating sources for a missing chapter, historians prioritize…", "options": ["contemporary primary sources and cross-verified accounts", "only secondary textbooks", "memes and social media without context"], "answer": "contemporary primary sources and cross-verified accounts", "explain": "Primary sources created at the time, tested against other sources, provide the most reliable evidence."},
                            {"q": "Evaluating reliability means asking…", "options": ["who produced the source, under what conditions, and for what purpose", "only whether it matches the textbook", "whether the author is famous"], "answer": "who produced the source, under what conditions, and for what purpose", "explain": "Context determines trust; a plantation record and an enslaved person's diary have different purposes and biases."},
                        ],
                    },
                },
                {
                    "slug": "capstone-the-missing-chapter",
                    "title": "Capstone: The Missing Chapter",
                    "order": 12,
                    "minutes": 30,
                    "summary": "Create a missing chapter with primary sources, timeline, context, interpretations, and an evidence-based conclusion.",
                    "learn": [
                        {"type": "p", "text": "The capstone brings every skill together. You will select an omitted topic, gather primary sources, construct a timeline, identify competing interpretations, and write a conclusion grounded in evidence. Your 'missing chapter' should read like a chapter in a U.S. history textbook — but with the gaps filled."},
                        {"type": "list", "items": [
                            "Choose an omitted topic: an event, person, law, movement, or policy underrepresented in standard texts.",
                            "Gather at least four primary sources: documents, photographs, court records, interviews, or material objects.",
                            "Build a timeline: place your topic in chronological context with at least six dated events.",
                            "Compare interpretations: summarize the standard textbook account, then present your evidence-based revision.",
                            "Conclude: state your thesis in one paragraph and defend it with the evidence you gathered.",
                        ]},
                        {"type": "tip", "text": "Strong capstones use sources that are publicly accessible or held in local archives. Avoid relying solely on memory or family stories; seek documents that can be verified by others."},
                        {"type": "activity", "title": "Outline your chapter", "text": "Draft a one-page outline for your missing chapter. Include your thesis, the sources you plan to use, and one counter-argument you expect to address."},
                    ],
                    "check": {
                        "prompt": "Show you understand the capstone requirements.",
                        "questions": [
                            {"q": "A strong missing chapter should include…", "options": ["primary sources, a timeline, and an evidence-based conclusion", "only personal opinions", "no engagement with existing narratives"], "answer": "primary sources, a timeline, and an evidence-based conclusion", "explain": "The capstone mirrors professional historical method: source criticism, chronology, and argument."},
                            {"q": "Competing interpretations matter because…", "options": ["they reveal what is at stake in how history is told", "they make history too complicated to study", "only one narrative can be true"], "answer": "they reveal what is at stake in how history is told", "explain": "Conflicting accounts often reflect real conflicts over power, identity, and justice."},
                        ],
                    },
                },
            ],
        },
    ],
}
