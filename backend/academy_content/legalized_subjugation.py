"""Legalized Subjugation: The Evolution of Structural Controls (published course)."""

LEGALIZED_SUBJUGATION = {
    "slug": "legalized-subjugation",
    "title": "Legalized Subjugation: The Evolution of Structural Controls",
    "summary": "Investigates how law and policy have been used to distribute rights, property, and opportunity unevenly across U.S. history.",
    "description": (
        "Students examine slavery, Black Codes, Jim Crow, redlining, disenfranchisement, and modern policy to understand how institutional law creates structural inequality. Students learn to read legislation as evidence and construct evidence-based conclusions."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "scholar",
    "tracks": ["scholar"],
    "grades": ["10", "11", "12"],
    "grade_label": "Grades 10–12",
    "status": "published",
    "audience": "High school students in grades 10–12 studying U.S. history and civics.",
    "est_hours": 22,
    "passing_score": 80,
    "learning_objectives": [
        "Define structural control and institutional power.",
        "Explain how laws can affect groups differently.",
        "Analyze primary historical documents.",
        "Explain the legal structure of slavery and its aftermath.",
        "Analyze the Black Codes and convict-leasing system.",
        "Explain the development and operation of Jim Crow.",
        "Analyze mechanisms of disenfranchisement.",
        "Explain the relationship between housing policy and wealth accumulation.",
        "Analyze redlining and restrictive covenants.",
        "Distinguish individual discrimination from institutional policy.",
        "Trace a historical policy through its enforcement and consequences.",
        "Compare competing interpretations of historical events.",
        "Identify gaps between a claim and the evidence supporting it.",
        "Construct an evidence-based historical argument.",
    ],
    "units": [
        {
            "slug": "law-as-a-system-of-power",
            "title": "Law as a System of Power",
            "summary": "How laws distribute rights, restrictions, and consequences differently.",
            "order": 1,
            "lessons": [
                {
                    "slug": "what-can-law-do",
                    "title": "What Can Law Do?",
                    "order": 1,
                    "minutes": 20,
                    "summary": "Laws as rules, intended and unintended consequences, and individual vs structural discrimination.",
                    "learn": [
                        {"type": "p", "text": "Laws are rules created by governments and enforced by institutions. They can grant rights — like the right to vote — or impose restrictions, like curfews. The people who write laws, enforce them, and benefit from them are rarely the same group. This mismatch is the starting point for understanding structural control."},
                        {"type": "p", "text": "Individual discrimination is a single person's biased action. Structural discrimination is built into laws, policies, and institutions — producing unequal outcomes even when no single person intends harm."},
                        {"type": "list", "items": [
                            "Who creates laws: legislators, courts, administrative agencies.",
                            "Who is subject to laws: everyone within the jurisdiction, but enforcement varies.",
                            "Who enforces laws: police, courts, federal agencies.",
                            "Who bears costs vs. who benefits: often different groups by design or neglect.",
                        ]},
                        {"type": "activity", "title": "Map a law's impact", "text": "Choose a local law (curfew, zoning rule, school discipline policy). List who creates it, who enforces it, who benefits, and who bears the costs."},
                    ],
                    "check": {
                        "prompt": "Show what you know about law as a system of power.",
                        "questions": [
                            {"q": "Structural discrimination differs from individual discrimination because…", "options": ["it is built into laws and institutions", "only one person is responsible", "it is always intentional"], "answer": "it is built into laws and institutions", "explain": "Structural discrimination produces unequal outcomes through systems, not just individual acts."},
                            {"q": "An unintended consequence of a law is…", "options": ["an outcome the law's authors did not plan or foresee", "a result written into the law's text", "a punishment for breaking the law"], "answer": "an outcome the law's authors did not plan or foresee", "explain": "Unintended consequences reveal how a law's effects can diverge from its stated purpose."},
                        ],
                    },
                },
                {
                    "slug": "reading-law-as-historical-evidence",
                    "title": "Reading Law as Historical Evidence",
                    "order": 2,
                    "minutes": 20,
                    "summary": "How to read statutes, court decisions, and regulations as primary sources.",
                    "learn": [
                        {"type": "p", "text": "Legal documents — statutes, court decisions, regulations — are primary sources. But they must be read carefully. What a law says on its face is not always how it worked in practice. Historians separate the text from its effects."},
                        {"type": "p", "text": "Legal terminology can obscure meaning. Words like 'freedom,' 'equal,' or 'citizen' have shifted across centuries. Read statutes alongside court decisions and enforcement records to see the full picture."},
                        {"type": "list", "items": [
                            "Statutes: laws passed by legislatures.",
                            "Court decisions: interpretations of law by judges.",
                            "Regulations: rules issued by agencies to implement statutes.",
                            "Context matters: who drafted the law, who lobbied for it, who signed it, and who opposed it.",
                        ]},
                        {"type": "activity", "title": "Annotate a historical law", "text": "Take one sentence from a historical law (for example, a vagrancy statute from the Black Codes). Circle the legal terms, underline the restrictions, and write one question about how it would be enforced."},
                    ],
                    "check": {
                        "prompt": "Show what you know about reading law as evidence.",
                        "questions": [
                            {"q": "A statute is best described as…", "options": ["a law passed by a legislature", "a judge's interpretation of law", "an agency's internal memo"], "answer": "a law passed by a legislature", "explain": "Statutes are enacted by legislative bodies; court decisions interpret them."},
                            {"q": "When historians read legal documents, they must…", "options": ["compare the text to its enforcement and effects", "accept the text as a complete account of what happened", "ignore the authors' intentions"], "answer": "compare the text to its enforcement and effects", "explain": "A law's real impact comes from how it was applied, not just what it says."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "slavery-and-the-legal-order",
            "title": "Slavery and the Legal Order",
            "summary": "How slavery was embedded in U.S. law and what changed after emancipation.",
            "order": 2,
            "lessons": [
                {
                    "slug": "slavery-as-a-legal-institution",
                    "title": "Slavery as a Legal Institution",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Property law, legal personhood, and the legal definition of enslavement.",
                    "learn": [
                        {"type": "p", "text": "In the United States, slavery was not just a social custom — it was a legal institution. State and federal law defined enslaved people as property, not persons. This legal status determined every aspect of life: family, labor, movement, and punishment."},
                        {"type": "p", "text": "Property law gave enslavers the right to buy, sell, bequeath, and discipline enslaved people. Court decisions reinforced this status. Even free Black people in slave states faced constant risk of being kidnapped and enslaved through legal fraud or corrupt courts."},
                        {"type": "list", "items": [
                            "Dred Scott v. Sandford (1857): Supreme Court ruled Black people were not citizens.",
                            "Slave codes: state laws restricting movement, assembly, and education.",
                            "Fugitive Slave Acts: federal law requiring capture and return of escaped enslaved people.",
                            "Family separation: enslaved people had no legal right to family integrity.",
                        ]},
                        {"type": "activity", "title": "Investigate a primary source", "text": "Read a section of a slave code or the Dred Scott decision. List three legal restrictions and explain what property law had to do with each."},
                    ],
                    "check": {
                        "prompt": "Show what you know about slavery as a legal institution.",
                        "questions": [
                            {"q": "Under U.S. slave law, an enslaved person was legally defined as…", "options": ["property, not a person", "a citizen with limited rights", "a ward of the state"], "answer": "property, not a person", "explain": "Slave law treated human beings as chattel property that could be bought, sold, and inherited."},
                            {"q": "The Dred Scott decision held that Black people…", "options": ["could not be U.S. citizens", "had the same legal rights as white citizens", "were entitled to full constitutional protection"], "answer": "could not be U.S. citizens", "explain": "The Supreme Court ruled African Americans were not intended to be included under the word 'citizens.'"},
                        ],
                    },
                },
                {
                    "slug": "emancipation-and-the-constitutional-order",
                    "title": "Emancipation and the Constitutional Order",
                    "order": 4,
                    "minutes": 20,
                    "summary": "The Reconstruction Amendments and the limits of constitutional change.",
                    "learn": [
                        {"type": "p", "text": "The Thirteenth, Fourteenth, and Fifteenth Amendments — the Reconstruction Amendments — transformed the Constitution. The 13th abolished slavery. The 14th guaranteed citizenship and equal protection. The 15th prohibited denying the vote based on race. But amendments are words; enforcement depends on institutions."},
                        {"type": "list", "items": [
                            "13th (1865): abolished slavery and involuntary servitude.",
                            "14th (1868): citizenship, due process, equal protection under the law.",
                            "15th (1870): voting rights cannot be denied based on race.",
                            "Federal vs. state authority: amendments restrict states, but states found ways to circumvent them.",
                        ]},
                        {"type": "activity", "title": "Timeline of change", "text": "Create a timeline from 1865 to 1877 showing what the Reconstruction Amendments promised and what federal policy actually did in the South."},
                    ],
                    "check": {
                        "prompt": "Show what you know about the Reconstruction Amendments.",
                        "questions": [
                            {"q": "The Thirteenth Amendment primarily…", "options": ["abolished slavery in the United States", "granted women the right to vote", "established the Supreme Court"], "answer": "abolished slavery in the United States", "explain": "The 13th Amendment ended chattel slavery except as punishment for a crime."},
                            {"q": "A major limitation of the Reconstruction Amendments was…", "options": ["they lacked strong enforcement mechanisms", "they applied only to the federal government", "they were never ratified"], "answer": "they lacked strong enforcement mechanisms", "explain": "Southern states used loopholes, violence, and later Jim Crow laws to circumvent the amendments for nearly a century."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "reconstruction-and-rebuilding-control",
            "title": "Reconstruction and the Rebuilding of Control",
            "summary": "Black Codes, convict leasing, and the legal restoration of hierarchy.",
            "order": 3,
            "lessons": [
                {
                    "slug": "the-black-codes",
                    "title": "The Black Codes",
                    "order": 5,
                    "minutes": 20,
                    "summary": "How Southern states criminalized freedom after emancipation.",
                    "learn": [
                        {"type": "p", "text": "After the Civil War, Southern legislatures passed Black Codes — laws designed to control the labor and movement of newly freed Black people. Vagrancy laws made unemployment a crime. Employment restrictions forced people into year-long labor contracts. Movement restrictions required passes for travel."},
                        {"type": "p", "text": "Criminal enforcement replaced the whip. Minor offenses — unemployment, loitering, 'insulting gestures' — led to arrest, fines, and forced labor. The legal system had shifted from slavery to criminalization as the primary tool of control."},
                        {"type": "list", "items": [
                            "Vagrancy laws: arrest anyone not employed.",
                            "Employment contracts: required annual labor agreements, often with former enslavers.",
                            "Movement restrictions: passes required for travel.",
                            "Criminal enforcement: minor offenses led to forced labor or convict leasing.",
                        ]},
                        {"type": "activity", "title": "Compare two systems", "text": "Create a two-column table comparing slavery law with the Black Codes. List three similarities and three differences in how each controlled labor and movement."},
                    ],
                    "check": {
                        "prompt": "Show what you know about the Black Codes.",
                        "questions": [
                            {"q": "A key purpose of the Black Codes was to…", "options": ["force freed people into exploitative labor", "grant full citizenship rights", "end all racial discrimination"], "answer": "force freed people into exploitative labor", "explain": "Black Codes criminalized unemployment and restricted movement to rebuild a coerced labor force."},
                            {"q": "Under Black Codes, vagrancy laws…", "options": ["made unemployment a criminal offense", "guaranteed a right to housing", "required free public education"], "answer": "made unemployment a criminal offense", "explain": "Vagrancy statutes arrested people without jobs, then fined or leased them to private employers."},
                        ],
                    },
                },
                {
                    "slug": "convict-leasing",
                    "title": "Convict Leasing",
                    "order": 6,
                    "minutes": 20,
                    "summary": "The system that turned criminal convictions into state-sanctioned labor extraction.",
                    "learn": [
                        {"type": "p", "text": "Convict leasing allowed Southern states to rent convicted people to private companies, plantations, and mines. The state received revenue; the lessee received free labor. Because convictions were easy to obtain under the Black Codes, the system supplied cheap labor and replicated many conditions of slavery."},
                        {"type": "p", "text": "Conditions were brutal. Mortality rates were high. There was little oversight. The system enriched states and corporations while denying the humanity of those incarcerated — most of whom were Black men convicted of minor offenses."},
                        {"type": "list", "items": [
                            "States leased prisoners to private employers.",
                            "Revenue from leasing replaced taxes and funded state budgets.",
                            "Conditions were often worse than slavery: no long-term investment in the worker.",
                            "The system lasted into the 20th century in some states.",
                        ]},
                        {"type": "activity", "title": "Evidence exercise", "text": "Find one newspaper account or government report about convict leasing. Identify the author, date, purpose, and what evidence the author uses to support their claims."},
                    ],
                    "check": {
                        "prompt": "Show what you know about convict leasing.",
                        "questions": [
                            {"q": "Convict leasing primarily benefited…", "options": ["private employers and state governments", "the incarcerated workers", "the federal government"], "answer": "private employers and state governments", "explain": "Lessees got free labor; states received revenue with minimal cost."},
                            {"q": "Most people caught up in convict leasing were…", "options": ["Black men convicted of minor offenses", "white-collar criminals", "political prisoners from the North"], "answer": "Black men convicted of minor offenses", "explain": "Discriminatory enforcement meant minor crimes led to long sentences for Black men."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "jim-crow-and-political-control",
            "title": "Jim Crow and Political Control",
            "summary": "Segregation laws, Supreme Court rulings, and the machinery of disenfranchisement.",
            "order": 4,
            "lessons": [
                {
                    "slug": "building-segregation",
                    "title": "Building Segregation",
                    "order": 7,
                    "minutes": 20,
                    "summary": "How segregation was legally constructed through Jim Crow laws and court decisions.",
                    "learn": [
                        {"type": "p", "text": "Jim Crow was not a set of informal customs. It was a legal system. Southern states passed laws requiring segregation in schools, transportation, restaurants, hospitals, and parks. The Supreme Court's 1896 Plessy v. Ferguson decision upheld 'separate but equal,' giving constitutional cover to segregation for nearly sixty years."},
                        {"type": "list", "items": [
                            "Plessy v. Ferguson (1896): 'separate but equal' is constitutional.",
                            "Segregated schools, railcars, waiting rooms, water fountains.",
                            "Anti-miscegenation laws: banned interracial marriage.",
                            "'Equal' facilities were almost never equal: Black schools received far less funding.",
                        ]},
                        {"type": "activity", "title": "Diagram a segregated space", "text": "Choose one type of segregated facility (schools, trains, hospitals). Draw a diagram showing how resources, access, and quality were divided by race."},
                    ],
                    "check": {
                        "prompt": "Show what you know about segregation under Jim Crow.",
                        "questions": [
                            {"q": "Plessy v. Ferguson established the doctrine that…", "options": ["separate but equal facilities are constitutional", "all public facilities must be integrated", "racial classification is unconstitutional"], "answer": "separate but equal facilities are constitutional", "explain": "The Court upheld state segregation laws, which were only overturned in Brown v. Board (1954)."},
                            {"q": "In practice, 'separate but equal' meant…", "options": ["Black facilities received far less funding and were inferior", "facilities were truly equal", "only private businesses could segregate"], "answer": "Black facilities received far less funding and were inferior", "explain": "States invested far more in white institutions; equality was a legal fiction."},
                        ],
                    },
                },
                {
                    "slug": "disenfranchisement",
                    "title": "Disenfranchisement",
                    "order": 8,
                    "minutes": 20,
                    "summary": "Poll taxes, literacy tests, grandfather clauses, and the Voting Rights Act.",
                    "learn": [
                        {"type": "p", "text": "After Reconstruction, Southern states systematically stripped Black citizens of the vote. Poll taxes made voting expensive. Literacy tests required impossible standards. Grandfather clauses exempted white voters if their ancestors had voted — a category no Black person could meet. White primaries excluded Black voters from the decisive party nomination."},
                        {"type": "list", "items": [
                            "Poll taxes: fee required to vote, often cumulative across years.",
                            "Literacy tests: administered arbitrarily; whites often got easy versions.",
                            "Grandfather clauses: waived restrictions if your grandfather had voted.",
                            "White primaries: Democratic Party excluded Black voters from primary elections.",
                        ]},
                        {"type": "activity", "title": "Compare rights with access", "text": "Make a chart showing that the 15th Amendment guaranteed voting rights, then list the legal mechanisms that blocked access for decades."},
                    ],
                    "check": {
                        "prompt": "Show what you know about disenfranchisement.",
                        "questions": [
                            {"q": "A grandfather clause worked by…", "options": ["waiving voting restrictions if your ancestors had voted", "requiring all voters to pass a history test", "giving extra votes to property owners"], "answer": "waiving voting restrictions if your ancestors had voted", "explain": "Because enslaved ancestors could not vote, Black people could not use the exemption."},
                            {"q": "The Voting Rights Act of 1965…", "options": ["banned racial discrimination in voting", "established poll taxes nationwide", "ended all literacy tests immediately"], "answer": "banned racial discrimination in voting", "explain": "The VRA outlawed practices like literacy tests and authorized federal oversight of elections."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "property-and-economic-control",
            "title": "Property and Economic Control",
            "summary": "Land, housing policy, redlining, and the roots of the wealth gap.",
            "order": 5,
            "lessons": [
                {
                    "slug": "land-ownership-and-opportunity",
                    "title": "Land, Ownership, and Opportunity",
                    "order": 9,
                    "minutes": 20,
                    "summary": "Why productive assets matter beyond income, and how access to property was restricted.",
                    "learn": [
                        {"type": "p", "text": "Income is money earned. Wealth is assets owned — land, homes, stocks, businesses. Wealth accumulates across generations through inheritance. Because Black people were systematically excluded from property ownership, they could not build the intergenerational wealth that white families took for granted."},
                        {"type": "p", "text": "After emancipation, some freed people acquired land — briefly. Most of it was lost through fraud, violence, discriminatory taxes, or legal manipulation. Without land, people had no collateral for loans, no rent income, and no asset to pass to children."},
                        {"type": "list", "items": [
                            "40 acres and a mule: Special Field Order 15 promised land, then was reversed.",
                            "Fraudulent sales and predatory contracts stole land from Black owners.",
                            "Discriminatory lending denied Black farmers access to credit.",
                            "Wealth gap: median Black household wealth is a fraction of white household wealth.",
                        ]},
                        {"type": "activity", "title": "Investigate local land history", "text": "Research one neighborhood in your region. Was it once a Black community that was displaced? What legal mechanisms were used — zoning, eminent domain, highway construction?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about land and wealth.",
                        "questions": [
                            {"q": "Wealth differs from income because wealth is…", "options": ["stock of assets that can be passed across generations", "money earned from a job", "the same as salary"], "answer": "stock of assets that can be passed across generations", "explain": "Wealth accumulates through ownership of property and investments, not just wages."},
                            {"q": "A major reason for the racial wealth gap is…", "options": ["centuries of exclusion from property ownership", "differences in work ethic", "natural economic cycles"], "answer": "centuries of exclusion from property ownership", "explain": "Legal barriers to land, housing, and lending prevented Black families from building intergenerational wealth."},
                        ],
                    },
                },
                {
                    "slug": "housing-policy-and-redlining",
                    "title": "Housing Policy and Redlining",
                    "order": 10,
                    "minutes": 20,
                    "summary": "Federal mortgage policy, redlining maps, and restrictive covenants.",
                    "learn": [
                        {"type": "p", "text": "In the 1930s, the Home Owners' Loan Corporation created color-coded maps to guide mortgage lending. 'Red' neighborhoods — home to Black, immigrant, and low-income residents — were marked high-risk. Banks refused loans. Real estate agents steered buyers away. Restrictive covenants barred Black people from buying homes in white neighborhoods."},
                        {"type": "list", "items": [
                            "Redlining: refusal to lend in certain neighborhoods based on racial composition.",
                            "Restrictive covenants: private contracts barring non-white buyers from deeds.",
                            "Blockbusting: real estate agents induced panic selling by importing Black families.",
                            "Steering: agents showed white buyers white neighborhoods and Black buyers Black neighborhoods.",
                        ]},
                        {"type": "activity", "title": "Map your city", "text": "Find the HOLC maps for your city online. Identify one 'redlined' neighborhood. What does that neighborhood look like today, and what evidence explains the change?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about housing policy and redlining.",
                        "questions": [
                            {"q": "Redlining was…", "options": ["refusal by banks to lend in certain neighborhoods based on race", "a type of home construction", "a government program to build affordable housing"], "answer": "refusal by banks to lend in certain neighborhoods based on race", "explain": "The HOLC maps institutionalized racial discrimination in mortgage lending."},
                            {"q": "Restrictive covenants were…", "options": ["private contracts barring non-white buyers from deeds", "government subsidies for homebuyers", "building codes for low-income housing"], "answer": "private contracts barring non-white buyers from deeds", "explain": "Covenants embedded racial exclusion into property law until ruled unenforceable in 1948."},
                        ],
                    },
                },
                {
                    "slug": "urban-renewal-and-displacement",
                    "title": "Urban Renewal and Displacement",
                    "order": 11,
                    "minutes": 18,
                    "summary": "Eminent domain, highway construction, and neighborhood destruction.",
                    "learn": [
                        {"type": "p", "text": "Urban renewal programs, backed by federal funding, allowed cities to seize 'blighted' neighborhoods through eminent domain. The results: vibrant Black communities were demolished for highways, stadiums, and commercial developments. Families received below-market compensation and were pushed into under-resourced neighborhoods."},
                        {"type": "list", "items": [
                            "Eminent domain: government power to take private property for public use.",
                            "Urban renewal: 1950s–60s federal program that destroyed many Black neighborhoods.",
                            "Highway construction: interstates were routed through Black and immigrant communities.",
                            "Displacement: families lost homes, businesses, and social networks.",
                        ]},
                        {"type": "activity", "title": "Trace a highway", "text": "Pick an interstate that runs through a city. Research what neighborhood it replaced and what happened to the displaced residents."},
                    ],
                    "check": {
                        "prompt": "Show what you know about urban renewal.",
                        "questions": [
                            {"q": "Urban renewal in the mid-20th century often resulted in…", "options": ["demolition of Black neighborhoods and displacement of residents", "construction of affordable housing for low-income families", "preservation of historic communities"], "answer": "demolition of Black neighborhoods and displacement of residents", "explain": "Federal highway and renewal programs displaced hundreds of thousands, disproportionately Black families."},
                            {"q": "Eminent domain allowed governments to…", "options": ["take private property for public use with compensation", "freeze rents in certain neighborhoods", "create new school districts"], "answer": "take private property for public use with compensation", "explain": "Eminent domain is the legal power to seize property, but 'just compensation' was often below market value."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "following-the-evidence",
            "title": "Following the Evidence",
            "summary": "Analytical tools for tracing policy, causation, and competing interpretations.",
            "order": 6,
            "lessons": [
                {
                    "slug": "from-policy-to-consequence",
                    "title": "From Policy to Consequence",
                    "order": 12,
                    "minutes": 18,
                    "summary": "How to trace a historical policy through enforcement and social effects.",
                    "learn": [
                        {"type": "p", "text": "A policy does not end when it is written. Its consequences flow through enforcement, access, behavior, and effects. To understand structural control, trace the full chain: policy → institution that enforces it → who is affected → what resources are denied → what long-term effects follow."},
                        {"type": "list", "items": [
                            "Policy: the law or rule itself.",
                            "Enforcement: the institution and agents who apply it.",
                            "Access: who can use rights, benefits, or resources.",
                            "Behavior: how people adjust their choices under the policy.",
                            "Effect: the long-term social and economic outcome.",
                        ]},
                        {"type": "activity", "title": "Case-study application", "text": "Choose one policy from this course (a Black Code, Jim Crow law, or redlining policy). Trace all five links in the chain and write one sentence for each."},
                    ],
                    "check": {
                        "prompt": "Show what you know about tracing policy to consequence.",
                        "questions": [
                            {"q": "The first step in tracing policy consequences is…", "options": ["identifying the policy and its stated purpose", "blaming the people affected", "ignoring enforcement"], "answer": "identifying the policy and its stated purpose", "explain": "You must understand what the policy says before you can analyze its effects."},
                            {"q": "Enforcement matters because…", "options": ["the same law can produce different outcomes depending on who enforces it", "laws enforce themselves automatically", "only federal laws have real power"], "answer": "the same law can produce different outcomes depending on who enforces it", "explain": "Discretion in policing, courts, and agencies shapes real-world outcomes."},
                        ],
                    },
                },
                {
                    "slug": "causation-vs-correlation",
                    "title": "Causation vs Correlation",
                    "order": 13,
                    "minutes": 18,
                    "summary": "How to distinguish causal claims from mere correlation in historical analysis.",
                    "learn": [
                        {"type": "p", "text": "Two things happening together does not prove one caused the other. Correlation is a pattern; causation is a mechanism. Historians ask: Is there evidence that A directly produced B? Or are both A and B caused by something else?"},
                        {"type": "list", "items": [
                            "Correlation: two trends move together.",
                            "Causation: one event directly produces another.",
                            "Confounding factors: a third cause explains both trends.",
                            "Evidence limitations: missing data, bias, or coincidence can mimic causation.",
                        ]},
                        {"type": "activity", "title": "Claim analysis exercise", "text": "Take this claim: 'Neighborhoods with high crime have more police.' Is this correlation or causation? What additional evidence would prove causation, and what alternative explanations exist?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about causation vs correlation.",
                        "questions": [
                            {"q": "The statement 'ice cream sales and drowning deaths both rise in summer' illustrates…", "options": ["correlation without causation", "direct causation", "no relationship at all"], "answer": "correlation without causation", "explain": "Both rise because of a third factor — summer heat — not because one causes the other."},
                            {"q": "To prove causation, historians look for…", "options": ["evidence of a direct mechanism linking cause and effect", "any two events that happened in the same year", "only numerical data"], "answer": "evidence of a direct mechanism linking cause and effect", "explain": "Mechanism, timing, and ruling out alternatives establish causation."},
                        ],
                    },
                },
                {
                    "slug": "competing-historical-interpretations",
                    "title": "Competing Historical Interpretations",
                    "order": 14,
                    "minutes": 18,
                    "summary": "How to evaluate official, participant, and historian accounts against primary evidence.",
                    "learn": [
                        {"type": "p", "text": "Every historical event generates multiple interpretations. The official government account may differ from a participant's memoir, which differs from a later historian's analysis. Each source has strengths and blind spots. Evaluate them by asking: Who wrote this? Who was the audience? What purpose did it serve? What does the primary evidence say?"},
                        {"type": "list", "items": [
                            "Official narrative: government record, often self-justifying.",
                            "Participant narrative: memoir, letter, interview — rich detail but partial.",
                            "Later historian: uses multiple sources, but may impose modern assumptions.",
                            "Primary evidence: the raw data — laws, court records, physical remains — closest to events.",
                        ]},
                        {"type": "activity", "title": "Source comparison", "text": "Take one event from this course (e.g., Plessy v. Ferguson). Find a newspaper editorial, a court opinion, and a modern historian's summary. Compare what each emphasizes and what each leaves out."},
                    ],
                    "check": {
                        "prompt": "Show what you know about competing historical interpretations.",
                        "questions": [
                            {"q": "A participant's memoir is valuable because…", "options": ["it provides insider detail and personal perspective", "it is always completely accurate", "it replaces the need for other sources"], "answer": "it provides insider detail and personal perspective", "explain": "Memoirs capture lived experience but may be selective or self-serving."},
                            {"q": "When interpretations conflict, the strongest evidence comes from…", "options": ["primary sources closest to the event", "whichever interpretation is most recent", "the most popular textbook"], "answer": "primary sources closest to the event", "explain": "Primary evidence — original documents and physical records — anchors historical conclusions."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "modern-connections",
            "title": "Modern Connections",
            "summary": "Historical continuity, institutional change, and present-day policy questions.",
            "order": 7,
            "lessons": [
                {
                    "slug": "institutions-change",
                    "title": "Institutions Change",
                    "order": 15,
                    "minutes": 18,
                    "summary": "Formal dismantling vs persistent practices, and accumulated advantages.",
                    "learn": [
                        {"type": "p", "text": "The United States formally dismantled slavery, Jim Crow, and many discriminatory laws. Yet institutions carry momentum. Practices once legal leave lasting patterns — in wealth distribution, neighborhood segregation, school funding, and criminal justice. Accumulated advantages mean that groups excluded from property, education, and political power for generations start behind today, even when the law is now neutral."},
                        {"type": "p", "text": "Important caveat: continuity of outcome does not prove identical causation. Modern disparities have multiple causes, including recent policy choices. The historical record explains part of the gap — not the whole story."},
                        {"type": "list", "items": [
                            "Formal change: laws and constitutions can be rewritten.",
                            "Institutional momentum: bureaucracies, markets, and norms persist.",
                            "Accumulated advantage: wealth, education, and connections compound across generations.",
                            "Multiple causes: history is one factor among many in present outcomes.",
                        ]},
                        {"type": "tip", "text": "Claiming that modern disparities are solely the result of past laws would be as wrong as claiming they have nothing to do with history. Complexity is not a flaw — it is the reality."},
                    ],
                    "check": {
                        "prompt": "Show what you know about institutional change and continuity.",
                        "questions": [
                            {"q": "Accumulated advantages explain why…", "options": ["past exclusion can produce present gaps even after laws change", "all modern disparities are caused by current law", "history has no effect on today"], "answer": "past exclusion can produce present gaps even after laws change", "explain": "Wealth, education, and social capital compound across generations; closing the law does not close the gap."},
                            {"q": "Continuity of outcome does not prove…", "options": ["identical modern causation", "that all institutions are racist", "that history is irrelevant", "that past law is the only cause"], "answer": "identical modern causation", "explain": "Similar outcomes can have different causes; historians must test claims, not assume them."},
                        ],
                    },
                },
                {
                    "slug": "rights-policy-and-present-day-questions",
                    "title": "Rights, Policy, and Present-Day Questions",
                    "order": 16,
                    "minutes": 18,
                    "summary": "Applying structural analysis to modern housing, voting, lending, and criminal justice.",
                    "learn": [
                        {"type": "p", "text": "The same analytical tools used for slavery, Jim Crow, and redlining apply to modern policy. Ask: Who creates the rule? Who enforces it? Who is affected? What resources are at stake? What does the evidence show about outcomes? This method works for voting laws, lending practices, school funding, and criminal sentencing."},
                        {"type": "list", "items": [
                            "Voting: ID laws, polling place closures, felon disenfranchisement.",
                            "Housing: zoning, lending discrimination, eviction patterns.",
                            "Education: school funding tied to property taxes.",
                            "Criminal justice: sentencing disparities, cash bail, policing patterns.",
                        ]},
                        {"type": "activity", "title": "Analyze a current policy", "text": "Choose one current policy debate (voter ID, cash bail, zoning reform). Apply the five-link chain: policy → institution → affected population → resources → effect."},
                    ],
                    "check": {
                        "prompt": "Show what you know about modern policy analysis.",
                        "questions": [
                            {"q": "When analyzing a modern policy through a structural lens, you should ask…", "options": ["who creates it, enforces it, and who is affected", "whether the policy sounds fair in a tweet", "only whether the people in charge are 'good' or 'bad'"], "answer": "who creates it, enforces it, and who is affected", "explain": "Structural analysis examines institutions and outcomes, not just stated intentions or individual character."},
                            {"q": "School funding tied to local property taxes produces inequality because…", "options": ["wealthy neighborhoods can spend far more per student", "all schools receive the same state funding", "teachers choose only to work in rich areas"], "answer": "wealthy neighborhoods can spend far more per student", "explain": "Property-tax-based funding links educational resources to neighborhood wealth, reproducing inequality."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "historical-investigation",
            "title": "Historical Investigation",
            "summary": "Building a structural case, evaluating sources, and constructing evidence-based arguments.",
            "order": 8,
            "lessons": [
                {
                    "slug": "building-a-structural-case",
                    "title": "Building a Structural Case",
                    "order": 17,
                    "minutes": 20,
                    "summary": "How to document policy, institution, enforcement, and consequences in a historical argument.",
                    "learn": [
                        {"type": "p", "text": "A strong historical argument is built like a case file. You document: the policy or law, the institution that enforced it, the population affected, the resources at stake, the consequences, any resistance, the reform efforts, and the long-term effects. Each element needs evidence — a statute, a court case, a letter, a census, a map."},
                        {"type": "list", "items": [
                            "Policy: the exact text or official rule.",
                            "Institution: which agency or court implemented it.",
                            "Enforcement: records of arrests, cases, or administrative actions.",
                            "Affected population: who bore the cost, with demographic evidence.",
                            "Resources: what was denied — land, money, votes, education.",
                            "Consequences: measurable outcomes — wealth, health, mobility, political power.",
                            "Resistance and reform: who fought back, and what changed.",
                            "Long-term effects: how the policy shaped outcomes decades later.",
                        ]},
                        {"type": "activity", "title": "Draft a case file", "text": "Choose one policy from this course. Write one paragraph for each element of the case file. Cite one primary source for each paragraph."},
                    ],
                    "check": {
                        "prompt": "Show what you know about building a structural case.",
                        "questions": [
                            {"q": "In a structural case, the 'enforcement' element asks…", "options": ["which institution applied the policy and how", "whether the law was popular", "who wrote the law"], "answer": "which institution applied the policy and how", "explain": "Enforcement is where policy becomes real impact; institutions matter."},
                            {"q": "Long-term effects are important because…", "options": ["they show how past policies shape present conditions", "they prove that no reform ever works", "they are always easy to measure"], "answer": "they show how past policies shape present conditions", "explain": "Structural inequality is often visible only when outcomes are traced across decades."},
                        ],
                    },
                },
                {
                    "slug": "primary-source-cross-examination",
                    "title": "Primary-Source Cross Examination",
                    "order": 18,
                    "minutes": 20,
                    "summary": "Author, audience, date, purpose, evidence, bias, and limitations.",
                    "learn": [
                        {"type": "p", "text": "No primary source is neutral. A law written by slaveholders reflects their interests. A court decision reflects the judges' ideology. A newspaper editorial reflects its publisher's audience. Cross examination means testing each source against others: Does the author have a motive to distort? Who was the intended audience? What does the source omit?"},
                        {"type": "list", "items": [
                            "Author: who created the source, and what was their role?",
                            "Audience: who was meant to read or hear it?",
                            "Date: when was it created, and what else was happening?",
                            "Purpose: what did the author want to achieve?",
                            "Evidence: what facts does it actually provide?",
                            "Bias: what perspective or interest shapes its claims?",
                            "Limitations: what does it leave out or obscure?",
                        ]},
                        {"type": "activity", "title": "Cross-examine a source", "text": "Take the Dred Scott decision. Identify the author (Justice Taney), audience (the nation), date (1857), purpose, evidence used, bias, and at least one limitation of the ruling as a historical source."},
                    ],
                    "check": {
                        "prompt": "Show what you know about evaluating primary sources.",
                        "questions": [
                            {"q": "When cross-examining a source, 'bias' refers to…", "options": ["the author's perspective or interest that shapes the account", "a rule about sourcing in essays", "whether the source is old or new"], "answer": "the author's perspective or interest that shapes the account", "explain": "Bias does not mean 'useless' — it means the source reflects a particular point of view."},
                            {"q": "A source's 'limitations' are…", "options": ["what the source omits or cannot show", "whether it is handwritten or typed", "the number of pages it contains"], "answer": "what the source omits or cannot show", "explain": "Every source has blind spots; identifying them strengthens historical reasoning."},
                        ],
                    },
                },
                {
                    "slug": "constructing-the-argument",
                    "title": "Constructing the Argument",
                    "order": 19,
                    "minutes": 22,
                    "summary": "Writing an evidence-based historical argument with thesis, context, evidence, and counterargument.",
                    "learn": [
                        {"type": "p", "text": "An evidence-based historical argument answers a question with a claim supported by primary and secondary sources. The thesis states the argument. Context explains the historical situation. Primary evidence — laws, court decisions, letters — provides proof. Secondary evidence — historians' analyses — connects the dots. A counterargument shows you understand complexity."},
                        {"type": "list", "items": [
                            "Thesis: a clear, arguable claim answering the prompt.",
                            "Historical context: the situation before the events you describe.",
                            "Primary evidence: original documents, laws, physical records.",
                            "Secondary evidence: historians' interpretations and synthesis.",
                            "Counterargument: a competing claim, then your rebuttal.",
                            "Conclusion: tie the evidence back to the thesis.",
                        ]},
                        {"type": "activity", "title": "Outline an essay", "text": "Choose one prompt: 'How did law create structural inequality after emancipation?' Draft a thesis statement and list three pieces of primary evidence you would use."},
                    ],
                    "check": {
                        "prompt": "Show what you know about constructing historical arguments.",
                        "questions": [
                            {"q": "A thesis in a historical essay should be…", "options": ["a clear, arguable claim", "a list of facts with no opinion", "a long summary of the topic"], "answer": "a clear, arguable claim", "explain": "A thesis takes a position that the rest of the essay must defend with evidence."},
                            {"q": "Including a counterargument…", "options": ["strengthens the essay by addressing competing views", "proves the thesis is wrong", "is not necessary for high school history"], "answer": "strengthens the essay by addressing competing views", "explain": "Rebuttal shows critical thinking and makes the original claim more persuasive."},
                        ],
                    },
                },
            ],
        },
    ],
}
