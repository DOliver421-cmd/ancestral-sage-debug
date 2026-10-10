"""cultural_integration.py — the Academy's cultural integration layer.

The owner's directive: culture is a *connected part of every subject*, not a
separate curriculum competing with core academics. Each entry below is a
complete, teachable unit attached to an EXISTING published course by
`attach_cultural_integration()` in academy_content/__init__.py.

Nothing here replaces or rewrites existing lessons. Each unit stands beside a
course's own content, carries the same hard requirements (learning objectives,
instructional blocks, a graded knowledge check whose answer is an exact option
string with an explanation), and must add value to the subject rather than
repeat a standalone history course.

Represented cultures: African (continental), African American, Caribbean,
Afro-Latin, and Indigenous — each named accurately and kept distinct rather
than blended.
"""

# ── ADULT TRACK ────────────────────────────────────────────────────────────

ADULT_ED_HSE_ELA = {
    "slug": "diaspora-literacy",
    "title": "Literacy the Diaspora Built",
    "summary": "Practise reading, writing, and comprehension on writing that African Americans used to win their freedom.",
    "order": 4,
    "lessons": [
        {
            "slug": "reading-freedom-writing",
            "title": "Reading and Writing Freedom",
            "order": 8,
            "minutes": 25,
            "summary": "Why literacy was forbidden law, and what people wrote anyway.",
            "learn": [
                {"type": "p", "text": "Many American slave states made it a crime to teach an enslaved person to read. That tells you exactly what the people in power knew: writing is power. Text is how you file a claim, sign a contract, publish a demand, and record what happened. African American writers worked under that threat anyway — newspapers like Freedom's Journal (1827, the first Black-owned newspaper in the United States) and the North Star (Frederick Douglass, 1847) carried arguments to a national public."},
                {"type": "list", "items": [
                    "Slave narratives: first-person accounts read by abolitionists on both sides of the Atlantic.",
                    "Black newspapers: journalism that reported what white papers would not print.",
                    "The Negro World (Marcus Garvey, 1918): millions of copies, in English and other languages.",
                ]},
                {"type": "example", "title": "Reading strategy", "text": "When you read any argument, first ask: who is it written TO, and what is it asking the reader to DO? Those two questions work on a slave narrative, a lease agreement, and a news article alike."},
            ],
            "check": {
                "prompt": "Check your reading comprehension.",
                "questions": [
                    {"q": "Making literacy illegal for enslaved people shows that the law knew…", "options": ["reading and writing were a route to power", "reading was dangerous for health", "letters were expensive"], "answer": "reading and writing were a route to power", "explain": "Banning it is evidence that the powerful understood its threat."},
                    {"q": "Freedom's Journal (1827) was important as…", "options": ["the first Black-owned newspaper in the US", "a cookbook", "a novel written in London"], "answer": "the first Black-owned newspaper in the US", "explain": "Black journalism gave a community its own public voice."},
                ],
            },
        },
        {
            "slug": "writing-your-document",
            "title": "Write a Document That Counts",
            "order": 9,
            "minutes": 25,
            "summary": "Draft a one-page letter or account in clear, specific language.",
            "learn": [
                {"type": "p", "text": "A working document asks for one thing and supports it with facts. Ida B. Wells wrote to record, expose, and persuade — using court records, not adjectives. Every adult needs three of these in a lifetime: a complaint letter to an agency, a letter asserting a right, and a short written account of an event that happened to you."},
                {"type": "list", "items": [
                    "Date, recipient, and subject line at the top.",
                    "One sentence naming what you are asking for.",
                    "Two or three facts with dates, names, and numbers.",
                    "One sentence naming the outcome you expect and by when.",
                ]},
                {"type": "tip", "text": "Keep dates, full names, and copies of everything. Marcus Garvey and Frederick Douglass both won arguments partly because their paperwork survived."},
                {"type": "activity", "title": "Write it", "text": "Write a one-page letter to a landlord, school, agency, or employer on an issue in your life. Use the four-part structure. Read it aloud to check whether the request is unmistakable."},
            ],
            "check": {
                "prompt": "Check your writing structure.",
                "questions": [
                    {"q": "The strongest request letter names…", "options": ["one specific ask, supported by dated facts", "several vague complaints", "an apology"], "answer": "one specific ask, supported by dated facts", "explain": "Specificity is what makes a request answerable."},
                    {"q": "Ida B. Wells built her argument mainly from…", "options": ["court records and counted cases", "personal opinion only", "rumour"], "answer": "court records and counted cases", "explain": "Evidence, not assertion, carried the argument."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Explain why literacy was forbidden and how African Americans built publishing institutions.",
        "Identify author, audience, and purpose in any argumentative text.",
        "Distinguish a factual claim from an opinion in a primary source.",
        "Write a one-page request letter with a specific ask and dated facts.",
    ],
}

ADULT_ED_HSE_MATH = {
    "slug": "math-that-measures",
    "title": "Math That Measures Our World",
    "summary": "Percent, ratio, and statistics applied to wealth, work, and the way African societies counted.",
    "order": 4,
    "lessons": [
        {
            "slug": "percent-and-the-wealth-gap",
            "title": "Percent, Ratio, and the Wealth Gap",
            "order": 9,
            "minutes": 25,
            "summary": "Read the numbers behind disparities without being misled by them.",
            "learn": [
                {"type": "p", "text": "A percentage only means something with its base attached. 'Assets fell 40%' and 'assets fell 40 percentage points' are different claims, and writers pick whichever sounds larger. The federal Survey of Consumer Finances reports median household wealth; the median is the honest summary for wealth data because a few very large fortunes pull the mean away from everyone else's experience."},
                {"type": "list", "items": [
                    "Median: the middle value — unaffected by extreme outliers.",
                    "Mean: pulled up by very large values, useful for totals, not for 'typical'.",
                    "Percent change: (new − old) / old × 100.",
                    "Ratio: compares two quantities; always name both.",
                ]},
                {"type": "example", "title": "Worked example", "text": "Family A holds $24,000 in assets. Family B holds $188,000. B holds 7.8 times as much. If a policy raised A's assets by 50% and B's by 3%, the gap shrinks — but in dollars it may still widen. Say which you mean."},
                {"type": "activity", "title": "Calculate", "text": "Take two known figures (for example median home values in two neighbourhoods). Compute the ratio and the percent difference, then write one sentence stating which measure you used and why."},
            ],
            "check": {
                "prompt": "Check your understanding of percent and ratio.",
                "questions": [
                    {"q": "For wealth data, the median is preferred because…", "options": ["it is not dragged up by a few very large fortunes", "it is always larger", "it ignores all data"], "answer": "it is not dragged up by a few very large fortunes", "explain": "Outliers distort the mean; the median stays with the typical household."},
                    {"q": "'A 40% fall' compared with 'a 40 percentage-point fall' differ because…", "options": ["percent change is relative to the starting value, a percentage point is absolute", "they are identical", "one is always wrong"], "answer": "percent change is relative to the starting value, a percentage point is absolute", "explain": "A percentage change depends on the base; a percentage point does not."},
                ],
            },
        },
        {
            "slug": "counting-other-ways",
            "title": "Counting Other Ways",
            "order": 10,
            "minutes": 25,
            "summary": "Vigesimal counting, and why systems of measurement are choices.",
            "learn": [
                {"type": "p", "text": "The Yoruba count in base 20 — ten fingers and ten toes — and twentieth-century mathematics calls this a vigesimal system. Base-20 survives in English too: a 'score' is twenty, and French still says quatre-vingts (four twenties) for eighty. The point for an adult learner is that no counting system is natural; each is a set of choices, and the choices shape what is easy to compute."},
                {"type": "list", "items": [
                    "Base 10: groups of ten — the system most adults were taught.",
                    "Base 20: groups of twenty — used across much of West Africa.",
                    "Base 60: Sumerian and still used for minutes, degrees, and time.",
                    "Binary: base 2 — the system your phone runs on.",
                ]},
                {"type": "tip", "text": "Ayo (also Oware) is played with 48 seeds in 12 cups. Every move is counting; playing several moves ahead is planning."},
                {"type": "activity", "title": "Convert", "text": "Write the numbers 1–30 in a base-20 system of your own design, then convert 1840 into base 20 and into binary."},
            ],
            "check": {
                "prompt": "Check your understanding of number systems.",
                "questions": [
                    {"q": "A base-20 system groups by…", "options": ["twenties", "tens", "fifties"], "answer": "twenties", "explain": "Vigesimal systems use twenty as the grouping unit."},
                    {"q": "Adults today still use base-60 for…", "options": ["minutes and degrees", "counting money", "measuring length"], "answer": "minutes and degrees", "explain": "Time and angle still use sexagesimal subdivisions."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Compute percent change and ratios correctly and state the base used.",
        "Choose mean or median appropriately for real data.",
        "Explain how a base-20 counting system works and where it survives today.",
        "Apply percent and ratio to a real household or community figure.",
    ],
}

ADULT_ED_HSE_SCIENCE = {
    "slug": "science-the-diaspora-built",
    "title": "Science the Diaspora Built",
    "summary": "African American and African scientists, and the agricultural engineering that fed a hemisphere.",
    "order": 3,
    "lessons": [
        {
            "slug": "black-scientists-and-their-work",
            "title": "Black Scientists and Their Work",
            "order": 6,
            "minutes": 25,
            "summary": "Named, specific contributions — not a list of names.",
            "learn": [
                {"type": "p", "text": "Science is a method, and African American scientists used it to solve material problems. George Washington Carver, born into slavery, restored nitrogen-depleted soils by rotating legumes and published the chemistry so other farmers could use it. Percy Julian synthesised physostigmine for glaucoma and built a steroid industry. Katherine Johnson computed the trajectories for Friendship 7 and the Apollo lunar flights by hand. Charles Drew built the blood-plasma storage system that made large-scale blood banking possible."},
                {"type": "list", "items": [
                    "Carver: crop rotation, nitrogen fixation, and products from peanuts and sweet potatoes.",
                    "Julian: organic synthesis at industrial scale.",
                    "Johnson: orbital mechanics, verified numerically before digital flight.",
                    "Drew: blood preservation and the modern plasma bank.",
                ]},
                {"type": "example", "title": "The method is the story", "text": "Each of these scientists published enough detail for others to reproduce the result. That reproducibility is what separates science from claim."},
            ],
            "check": {
                "prompt": "Check what you know about these scientists.",
                "questions": [
                    {"q": "Carver's crop rotation addressed…", "options": ["soils stripped of nitrogen by cotton", "a shortage of water", "a lack of sunlight"], "answer": "soils stripped of nitrogen by cotton", "explain": "Legumes restore nitrogen via root-nodule bacteria."},
                    {"q": "Katherine Johnson's contribution to spaceflight was…", "options": ["computing trajectories", "designing rocket fuel", "building the launch pad"], "answer": "computing trajectories", "explain": "She calculated the flight paths that carried astronauts into orbit."},
                ],
            },
        },
        {
            "slug": "rice-coast-engineering",
            "title": "The Rice Coast: Agriculture as Engineering",
            "order": 7,
            "minutes": 25,
            "summary": "Water management that built an economy — and its ecological cost.",
            "learn": [
                {"type": "p", "text": "The rice economy of South Carolina and Georgia was built on engineering knowledge Africans brought from the Senegal–Gambia basin and Sierra Leone: tidal irrigation, field banks, trunk gates, and controlled draining. Plantation records show enslavers paid more for people advertised as 'born in Gambia' or 'of the Rice Coast' — the skill was the asset. The knowledge was real water engineering, and the system that exploited it was a crime."},
                {"type": "list", "items": [
                    "Graded fields: gravity moves water in and out without pumps.",
                    "Trunks and banks: controlled flood and drain on the tidal cycle.",
                    "Winnowing and milling: fanner baskets and large mortars brought from West Africa.",
                    "Ecology: swamp drainage created habitat for mosquitoes and disease.",
                ]},
                {"type": "tip", "text": "Separating the achievement from the crime is part of honest history: the engineering is African, the plantation is not an achievement."},
                {"type": "activity", "title": "Draw it", "text": "Sketch a tidal rice field: river, trunk, canal, field bank, drainage ditch. Label where water enters, rests, and leaves."},
            ],
            "check": {
                "prompt": "Check your understanding of Rice Coast engineering.",
                "questions": [
                    {"q": "Tidal irrigation works by…", "options": ["using gravity to flood and drain graded fields", "pumping water uphill", "collecting rainfall only"], "answer": "using gravity to flood and drain graded fields", "explain": "Slope and tides do the work, controlled by banks and trunks."},
                    {"q": "Enslavers priced some Africans higher because…", "options": ["they carried rice-growing skill", "they were taller", "they spoke English"], "answer": "they carried rice-growing skill", "explain": "The ledgers themselves record the value of the technical knowledge."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Describe specific named contributions to American science and their methods.",
        "Explain how tidal rice cultivation functions as water engineering.",
        "Distinguish a scientific claim from an unsupported one.",
        "Connect African knowledge systems to documented technical practice.",
    ],
}

ADULT_ED_HSE_SOCIAL_STUDIES = {
    "slug": "black-political-thought-adult",
    "title": "Black Political Thought",
    "summary": "The arguments African Americans and Africans made about freedom, citizenship, and power.",
    "order": 3,
    "lessons": [
        {
            "slug": "the-argument-tradition",
            "title": "An Argument Tradition",
            "order": 6,
            "minutes": 25,
            "summary": "From petitions to the UN: four centuries of organised political argument.",
            "learn": [
                {"type": "p", "text": "Black political thought is a body of argument, not a series of protests. Enslaved and free Black petitioners asked colonial legislatures and the British crown for relief from the 1700s onward; David Walker's 1829 Appeal demanded rather than requested; the Pan-African Congresses (1900–1945) put colonial self-government on the world agenda; W.E.B. Du Bois, Ida B. Wells, and the NAACP argued in courts and newspapers; Ella Baker built organisations that trained local leaders rather than heroes."},
                {"type": "list", "items": [
                    "Petition and legal argument: the oldest tools, still in use.",
                    "Newspapers and pamphlets: reaching a public that could vote or act.",
                    "Organisation: building institutions that outlive a campaign.",
                    "International argument: Pan-Africanism framed colonial rule as a global illegality.",
                ]},
                {"type": "example", "title": "The tool still works", "text": "A modern zoning objection, a school board comment, and a labour complaint are the same instruments used by 18th-century petitioners: a written, dated, specific claim."},
            ],
            "check": {
                "prompt": "Check what you know about the argument tradition.",
                "questions": [
                    {"q": "David Walker's Appeal (1829) was notable for…", "options": ["demanding freedom rather than asking for it", "asking politely for mercy", "avoiding the subject"], "answer": "demanding freedom rather than asking for it", "explain": "Its tone was itself an argument about standing."},
                    {"q": "The Pan-African Congresses advanced the claim that…", "options": ["colonised peoples had a right to self-government", "colonies should be taxed more", "empire was eternal"], "answer": "colonised peoples had a right to self-government", "explain": "They took self-determination onto an international agenda."},
                ],
            },
        },
        {
            "slug": "voting-rights-and-power",
            "title": "Voting, Power, and the Work",
            "order": 7,
            "minutes": 25,
            "summary": "How rights are won, kept, and used.",
            "learn": [
                {"type": "p", "text": "Rights are won by organisation and defended by vigilance. Fannie Lou Hamer was beaten for trying to register to vote; her answer was to found the Freedom Farms Cooperative, because a family dependent on a boss for food cannot safely register. Freedom Summer (1964) brought students South to register voters and expose the violence that blocked them. The Voting Rights Act of 1965 followed — and parts of it were weakened by Shelby County v. Holder (2013), which is why registration work continues."},
                {"type": "list", "items": [
                    "Economic independence supports political courage.",
                    "Registration, literacy, and access are continuous work, not one-time events.",
                    "Courts can remove protection as well as grant it.",
                ]},
                {"type": "tip", "text": "Hamer's insight is practical: build the economic base first when you can, because it determines what you can risk."},
                {"type": "activity", "title": "Trace one law", "text": "Pick the Voting Rights Act or the Civil Rights Act. Trace one clause to the campaign that produced it, and name what happened to it afterwards."},
            ],
            "check": {
                "prompt": "Check what you know about voting and power.",
                "questions": [
                    {"q": "Hamer founded Freedom Farms because she understood that…", "options": ["economic dependence blocks political courage", "farming was fashionable", "food was expensive"], "answer": "economic dependence blocks political courage", "explain": "Food independence protected her ability to organise."},
                    {"q": "Shelby County v. Holder (2013) is significant because it…", "options": ["weakened federal voting-rights protections", "ended slavery", "created public schools"], "answer": "weakened federal voting-rights protections", "explain": "It removed the preclearance formula from the Voting Rights Act."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Trace the argument strategies Black Americans used to claim rights.",
        "Explain the relationship between economic independence and political action.",
        "Describe how voting rights were won and how they can be lost.",
        "Identify a present-day civic action available to you.",
    ],
}

HANDBOOK_ADULT = {
    "slug": "handbook-to-action",
    "title": "From Handbook to Action",
    "summary": "Turn the handbook into household documents, a family record, and a plan.",
    "order": 2,
    "lessons": [
        {
            "slug": "family-records-matter",
            "title": "Build the Family Record",
            "order": 6,
            "minutes": 25,
            "summary": "The documents that make you legible to institutions.",
            "learn": [
                {"type": "p", "text": "Institutions decide on paper. A family that can produce a birth certificate, a marriage record, deeds, enlistment papers, and a school transcript can claim benefits, correct errors, and tell its own story. Reconstruction-era Black institutions understood this: schools, mutual aid societies, and newspapers all existed partly to create a record where there had been none."},
                {"type": "list", "items": [
                    "Vital records: birth, marriage, death — get certified copies.",
                    "Property: deeds, wills, tax records, and receipts.",
                    "Migration: shipping lists, naturalisation papers, census entries.",
                    "Education: diplomas, transcripts, certificates, military records.",
                ]},
                {"type": "example", "title": "Freedmen's Bureau records", "text": "After the Civil War the Freedmen's Bureau recorded marriages, labour contracts, and school records. Many families today find those documents are the only written trace of an ancestor — and they are searchable online."},
                {"type": "activity", "title": "Start the file", "text": "Create one folder (physical or digital) labelled 'family records'. Add three documents you already own and list three you need to obtain."},
            ],
            "check": {
                "prompt": "Check what you know about family records.",
                "questions": [
                    {"q": "A certified copy is preferred over a photocopy because…", "options": ["institutions require a verifiable original record", "it looks nicer", "copies are always wrong"], "answer": "institutions require a verifiable original record", "explain": "Agencies act on documents they can authenticate."},
                    {"q": "Freedmen's Bureau records are valuable because they…", "options": ["document marriages, contracts, and schools after emancipation", "are written in code", "were never kept"], "answer": "document marriages, contracts, and schools after emancipation", "explain": "They are often the only written trace of newly emancipated families."},
                ],
            },
        },
        {
            "slug": "interview-an-elder",
            "title": "Interview an Elder",
            "order": 7,
            "minutes": 25,
            "summary": "Oral history preserves what no certificate holds.",
            "learn": [
                {"type": "p", "text": "Every family holds information that exists nowhere else: where a grandmother grew up, why the family moved, what names changed and when, what songs were sung. Oral history is how you keep it. The Federal Writers' Project interviews of the 1930s recorded more than 2,000 formerly enslaved people speaking in their own voices — those accounts exist because someone asked."},
                {"type": "list", "items": [
                    "Ask permission, and offer to let the person stop at any time.",
                    "Use open questions: 'Tell me about the year you moved'.",
                    "Record names, places, and dates exactly as spoken.",
                    "Keep the recording and give the elder a copy.",
                ]},
                {"type": "tip", "text": "Write down what you do NOT know. A clear gap is more useful to the next researcher than a confident guess."},
                {"type": "activity", "title": "Three questions", "text": "Interview one elder with three open questions. Write one page from the answers and add it to your family file."},
            ],
            "check": {
                "prompt": "Check what you know about oral history.",
                "questions": [
                    {"q": "An open question is one that…", "options": ["invites a story rather than yes or no", "is always about dates", "has no answer"], "answer": "invites a story rather than yes or no", "explain": "Open questions let the speaker decide what matters."},
                    {"q": "The 1930s Federal Writers' Project interviews matter because they…", "options": ["recorded formerly enslaved people in their own words", "were all fictional", "were written by politicians"], "answer": "recorded formerly enslaved people in their own words", "explain": "They preserve first-person accounts of slavery."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "List the family documents institutions rely on and start a family file.",
        "Conduct and record one oral-history interview.",
        "Locate one public record set relevant to your family.",
    ],
}

CAREER_WORKFORCE = {
    "slug": "black-trades-and-invention",
    "title": "Black Trades, Engineering, and Invention",
    "summary": "Who built the trades, the patents, and the infrastructure — named specifically.",
    "order": 4,
    "lessons": [
        {
            "slug": "black-inventors-and-builders",
            "title": "Black Inventors and Builders",
            "order": 9,
            "minutes": 25,
            "summary": "Patents, structures, and companies with names attached.",
            "learn": [
                {"type": "p", "text": "Black Americans built industries while being denied credit to own them. Lewis H. Latimer drafted the patent drawings for Alexander Graham Bell's telephone and developed the carbon filament that made Edison's bulb practical. Garrett A. Morgan patented the three-position traffic signal and a safety hood used by fire departments. Norbert Rillieux's multiple-effect evaporator made sugar refining efficient worldwide — he built it in Louisiana and took it to France after discrimination. Otis Boykin's components went into pacemakers and computers. Lonnie Johnson's Super Soaker funded his energy research."},
                {"type": "list", "items": [
                    "Latimer: patent drafting, carbon filament, and electric-lighting engineering.",
                    "Morgan: traffic signal and the safety hood adopted by fire brigades.",
                    "Rillieux: industrial sugar refining, built in Louisiana.",
                    "Boykin: precision resistors used in medical and computing devices.",
                ]},
                {"type": "example", "title": "Read a patent", "text": "A patent is public. Look up one of these inventors and read the abstract — it names the problem, the method, and the claim in plain language. That is exactly how you describe your own work on a résumé."},
            ],
            "check": {
                "prompt": "Check what you know about Black inventors.",
                "questions": [
                    {"q": "Lewis Latimer's work on the carbon filament…", "options": ["made electric light practical", "invented the telephone", "designed the traffic signal"], "answer": "made electric light practical", "explain": "The carbon filament extended bulb life and improved efficiency."},
                    {"q": "Garrett Morgan's three-position signal is the ancestor of…", "options": ["the modern traffic light", "the telegraph", "the radio"], "answer": "the modern traffic light", "explain": "His signal introduced the intermediate warning position."},
                ],
            },
        },
        {
            "slug": "trades-and-entrepreneurship",
            "title": "From Trade to Business",
            "order": 10,
            "minutes": 25,
            "summary": "How skilled trades become ownership.",
            "learn": [
                {"type": "p", "text": "A trade is a wage; a business built on that trade is an asset. Black Wall Street in Tulsa, Oklahoma held more than 300 Black-owned businesses — barbers, grocers, hotels, banks, and doctors — before it was destroyed in 1921. John Merrick, a barber in Durham, North Carolina, pooled money with others to found North Carolina Mutual Life Insurance, which became one of the largest Black-owned businesses in America. The pattern is consistent: skill, saving, pooling, and lending to each other."},
                {"type": "list", "items": [
                    "Skill first: a trade you can do better than most people.",
                    "Save deliberately, then pool: mutual aid societies and credit unions.",
                    "Lend inside the community when banks will not.",
                    "Insure the risks: liability, health, property.",
                ]},
                {"type": "tip", "text": "North Carolina Mutual survived two centuries by combining insurance with investment in Black businesses — the same logic as a modern community development financial institution."},
                {"type": "activity", "title": "Your plan", "text": "Write a one-page plan: your trade, the three tools you would need, how you would fund them, and who your first five customers are."},
            ],
            "check": {
                "prompt": "Check what you know about trade and ownership.",
                "questions": [
                    {"q": "The businesses of Black Wall Street in Tulsa were destroyed by…", "options": ["the 1921 Tulsa race massacre", "a flood", "a tax law"], "answer": "the 1921 Tulsa race massacre", "explain": "The district was attacked and burned; its wealth was destroyed."},
                    {"q": "North Carolina Mutual Life Insurance began as…", "options": ["pooled money from a small community of barbers and workers", "a government program", "a single wealthy family's fortune"], "answer": "pooled money from a small community of barbers and workers", "explain": "It grew from pooled small contributions."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Name specific Black inventors and describe what they built.",
        "Explain how a skilled trade becomes a business and an asset.",
        "Describe the pooling and lending pattern behind historic Black business districts.",
    ],
}

RADICAL_WEALTH_LITERACY = {
    "slug": "credit-cooperatives-practice",
    "title": "Credit, Cooperatives, and Practice",
    "summary": "Credit, contracts, and the cooperative institutions people build when banks will not serve them.",
    "order": 6,
    "lessons": [
        {
            "slug": "credit-and-contracts",
            "title": "Credit and Contracts",
            "order": 14,
            "minutes": 25,
            "summary": "How money is priced, and what a contract actually binds you to.",
            "learn": [
                {"type": "p", "text": "Credit is money rented at a price, and the price (APR) is only part of the cost. Redlining — the denial of mortgages to whole neighbourhoods from the 1930s onward — meant entire communities could not convert income into property, which is the single largest source of household wealth. The Fair Housing Act of 1968 made that discrimination illegal and the Community Reinvestment Act of 1977 obliged banks to serve low- and moderate-income neighbourhoods; both come from that history."},
                {"type": "list", "items": [
                    "APR: the yearly cost of borrowing, including fees.",
                    "Predatory terms: balloon payments, prepayment penalties, and flip-repayment scams.",
                    "A contract binds both sides — read the default and the exit clauses first.",
                    "Credit unions: member-owned, not shareholder-owned.",
                ]},
                {"type": "example", "title": "Why it compounds", "text": "Property appreciates; rent does not. A denied mortgage is not one bad year — it is the loss of decades of appreciation, inherited by children."},
            ],
            "check": {
                "prompt": "Check what you know about credit and contracts.",
                "questions": [
                    {"q": "Redlining refers to…", "options": ["denying credit to whole neighbourhoods", "marking roads on a map", "raising interest rates on everyone"], "answer": "denying credit to whole neighbourhoods", "explain": "Neighbourhoods were graded and credit refused based on that grading."},
                    {"q": "In a contract, the clauses to read first are…", "options": ["the default and termination terms", "the title page", "the signatures"], "answer": "the default and termination terms", "explain": "They define what happens when something goes wrong and how to leave."},
                ],
            },
        },
        {
            "slug": "mutual-aid-today",
            "title": "Mutual Aid Is a System, Not a Favour",
            "order": 15,
            "minutes": 25,
            "summary": "Pooling money and risk: from the Free African Society to a credit union charter.",
            "learn": [
                {"type": "p", "text": "The Free African Society, founded in Philadelphia in 1787 by Richard Allen and Absalom Jones, pooled dues to pay for burials, supporting widows, and helping the sick. That structure is the ancestor of the modern credit union and of cooperative insurance. A credit union takes deposits, lends them to members, and returns profit as dividends — because the members are the owners. Formation is legal, ordinary, and available."},
                {"type": "list", "items": [
                    "Pooling: small regular contributions create a capital base.",
                    "Risk sharing: everyone pays, so a bad year hits no one family alone.",
                    "Ownership: one member, one vote — not one share, one vote.",
                    "Chartering: a credit union or cooperative files with a state or federal regulator.",
                ]},
                {"type": "tip", "text": "Ujamaa — Swahili for familyhood and cooperative economics — became a formal principle of Kwanzaa in 1966. The idea is economic democracy, not charity."},
                {"type": "activity", "title": "Draft a charter", "text": "Draft the bylaws for a mutual aid group of ten people: dues, what the pool covers, who decides, and what happens when someone leaves."},
            ],
            "check": {
                "prompt": "Check what you know about mutual aid.",
                "questions": [
                    {"q": "The Free African Society (1787) pooled money to…", "options": ["pay burial costs and support widows and the sick", "buy land abroad", "fund a printing press"], "answer": "pay burial costs and support widows and the sick", "explain": "Early mutual aid societies covered death, illness, and family support."},
                    {"q": "In a credit union, profits are returned to…", "options": ["members as dividends", "outside shareholders", "the government"], "answer": "members as dividends", "explain": "Members are the owners, so surplus flows back to them."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Explain how redlining shaped household wealth and what law changed it.",
        "Read a contract for its default and exit terms.",
        "Describe how a credit union or cooperative is structured and formed.",
    ],
}


COOPERATIVE_ECONOMICS_MUTUAL_AID = {
    "slug": "freedom-farms-and-coops",
    "title": "Freedom Farms and Modern Cooperatives",
    "summary": "The cooperative as a survival instrument: Fannie Lou Hamer's Freedom Farms and the co-ops it inspires.",
    "order": 6,
    "lessons": [
        {
            "slug": "freedom-farms-cooperative",
            "title": "Freedom Farms Cooperative",
            "order": 12,
            "minutes": 25,
            "summary": "Pigs, gardens, a store, and 1,500 families fed.",
            "learn": [
                {"type": "p", "text": "Fannie Lou Hamer is remembered for voter registration; her deepest work was economic. After being beaten and evicted for trying to vote, she founded the Freedom Farms Cooperative in 1969 in Sunflower County, Mississippi. It ran pig banks, vegetable gardens, and a cooperative store, and fed roughly 1,500 families. Members owned what they produced, which is the definition of food sovereignty — and Hamer argued that economic independence was what made voter registration safe."},
                {"type": "list", "items": [
                    "Pig bank: the co-op breeds pigs, families raise them and share the keep.",
                    "Gardens: vegetables grown and sold inside the community.",
                    "Store: buying power held by the members, not an outside merchant.",
                    "Purpose: hunger relief, income, and protection for voting-rights work.",
                ]},
                {"type": "example", "title": "The logic", "text": "A family that depends on a white boss for groceries cannot safely register. Food independence was therefore a civil-rights strategy, not a side project."},
            ],
            "check": {
                "prompt": "Check what you know about Freedom Farms.",
                "questions": [
                    {"q": "Freedom Farms was structured as…", "options": ["a cooperative owned by its members", "a charity handout", "a government farm"], "answer": "a cooperative owned by its members", "explain": "Members owned the output they produced."},
                    {"q": "Hamer connected food independence to voting because…", "options": ["economic dependence limits political courage", "food prices affect ballots", "farmers vote more"], "answer": "economic dependence limits political courage", "explain": "Owning your food supply reduces what you can be threatened with."},
                ],
            },
        },
        {
            "slug": "start-your-cooperative",
            "title": "Start Your Cooperative",
            "order": 13,
            "minutes": 25,
            "summary": "Structure, capital, and the parts that make or break a co-op.",
            "learn": [
                {"type": "p", "text": "A cooperative is a legal business form: members buy a share, vote one member one vote, and share the surplus. It can buy, sell, produce, lend, or house. What makes one work is the same three things that made Freedom Farms work — a defined capital base, a product people actually want, and records everyone can see."},
                {"type": "list", "items": [
                    "Structure: bylaws, membership rules, and an elected board.",
                    "Capital: member shares, retained earnings, and sometimes a CDFI loan.",
                    "Operations: a product or service with paying customers.",
                    "Governance: one member one vote, published accounts.",
                ]},
                {"type": "tip", "text": "Most cooperatives fail on land access and labour terms, not on product. Decide who provides land and who works before you decide what to sell."},
                {"type": "activity", "title": "Draft it", "text": "Draft a two-page cooperative plan: what it does, how members join, how money flows, and how decisions are made."},
            ],
            "check": {
                "prompt": "Check what you know about starting a cooperative.",
                "questions": [
                    {"q": "In a cooperative, voting rights are…", "options": ["one member, one vote", "proportional to shares", "held by the board alone"], "answer": "one member, one vote", "explain": "Democratic ownership is the defining feature."},
                    {"q": "The most common failure points are…", "options": ["land access and labour terms", "choosing a name", "the colour of the sign"], "answer": "land access and labour terms", "explain": "Those decide whether the work can happen at all."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Describe Freedom Farms Cooperative's structure and its civil-rights purpose.",
        "Explain how a cooperative is formed, capitalised, and governed.",
        "Identify the land and labour questions that decide a co-op's survival.",
    ],
}

ENTREPRENEURSHIP_FOUNDATIONS = {
    "slug": "black-business-history",
    "title": "Black Business History and the Entrepreneur",
    "summary": "Who built Black enterprise, what blocked it, and what the record shows about what works.",
    "order": 4,
    "lessons": [
        {
            "slug": "from-madam-walker-to-now",
            "title": "From Madam C.J. Walker to Now",
            "order": 8,
            "minutes": 25,
            "summary": "Named businesses, the markets they built, and the obstacles they faced.",
            "learn": [
                {"type": "p", "text": "Madam C.J. Walker built a haircare company from a door-to-door product into a manufacturing and training business employing thousands of women sales agents; she is generally credited as the first self-made American woman millionaire. Robert S. Abbott published the Chicago Defender from a boarding room and built a national newspaper. John H. Johnson founded Ebony and Jet magazines. Berry Gordy took Motown from a Detroit house to a global label. BET, founded by Robert L. Johnson, sold for billions. The pattern is a specific customer, a repeatable product, and distribution."},
                {"type": "list", "items": [
                    "Walker: direct sales, manufacturing, and a training college.",
                    "Abbott: the Chicago Defender — distributed by railroad porters across the South.",
                    "Johnson (Robert S.): publishing built on a readership others ignored.",
                    "Gordy: Motown — quality control and a distribution pipeline.",
                ]},
                {"type": "example", "title": "The common thread", "text": "Each one identified a customer mainstream businesses were not serving, then built the distribution to reach that customer directly."},
            ],
            "check": {
                "prompt": "Check what you know about Black business history.",
                "questions": [
                    {"q": "Madam C.J. Walker's business was built on…", "options": ["haircare products and a sales-agent network", "railroads", "banking only"], "answer": "haircare products and a sales-agent network", "explain": "She manufactured a product and trained women to sell it."},
                    {"q": "The Chicago Defender reached readers across the South through…", "options": ["railroad porters who distributed copies", "television", "the telephone"], "answer": "railroad porters who distributed copies", "explain": "Porters carried papers along the rail lines, bypassing Southern bans."},
                ],
            },
        },
        {
            "slug": "obstacles-and-evidence",
            "title": "The Obstacles, Documented",
            "order": 9,
            "minutes": 25,
            "summary": "Why the record looks the way it does — and how to plan around it.",
            "learn": [
                {"type": "p", "text": "Black enterprise faced documented, specific obstacles: denial of credit by the Home Owners' Loan Corporation's neighbourhood grading, the destruction of Black business districts (Tulsa 1921, Wilmington 1898, Rosewood 1923), segregated markets, and exclusion from procurement. Studying those obstacles is not pessimism — it tells you which funding and distribution channels to build."},
                {"type": "list", "items": [
                    "Credit: build a relationship with a credit union or CDFI early.",
                    "Insurance: use cooperative and mutual aid structures that already exist.",
                    "Distribution: control your channel rather than rent someone else's.",
                    "Records: keep clean books — they are what a lender or partner can actually see.",
                ]},
                {"type": "tip", "text": "Tulsa, Rosewood, and Wilmington are documented events, not folklore. The reparations and restitution legal debates continue today."},
                {"type": "activity", "title": "Write the risk page", "text": "Write one page on your venture's three biggest risks and the specific structure that reduces each."},
            ],
            "check": {
                "prompt": "Check what you know about the obstacles Black enterprise faced.",
                "questions": [
                    {"q": "The Tulsa race massacre of 1921 destroyed…", "options": ["a district of Black-owned businesses", "a single home", "a government building"], "answer": "a district of Black-owned businesses", "explain": "The Greenwood district's concentrated wealth was destroyed."},
                    {"q": "For a new venture, the practical lesson from these obstacles is to…", "options": ["secure funding and distribution channels you control", "avoid keeping records", "wait for outside investors"], "answer": "secure funding and distribution channels you control", "explain": "Owning capital and channel reduces dependence on hostile ones."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Name specific Black businesses and describe the market each built.",
        "Explain the documented obstacles Black enterprise faced.",
        "Identify funding and distribution strategies that work around them.",
    ],
}

ASCENSION_PROTOCOLS = {
    "slug": "protocols-in-practice",
    "title": "Protocols in Practice",
    "summary": "The Ascension Protocols applied as a daily discipline, not an abstraction.",
    "order": 2,
    "lessons": [
        {
            "slug": "protocol-as-discipline",
            "title": "The Protocol as Discipline",
            "order": 3,
            "minutes": 20,
            "summary": "Turning principles into a repeatable practice.",
            "learn": [
                {"type": "p", "text": "A protocol is a written procedure that produces a repeatable result. That is a working definition, and it comes from ordinary practice: a mason's sequence, a farmer's rotation, a nurse's checklist. The worth of a protocol is whether the result repeats when you follow it. Write yours down, follow it, and record what happened."},
                {"type": "list", "items": [
                    "State the outcome in one sentence.",
                    "Write the steps in the order you actually do them.",
                    "Note the check that tells you it worked.",
                    "Record when it did not — that is the data.",
                ]},
                {"type": "tip", "text": "Griot traditions worked exactly this way: the story is a protocol for transmitting law, lineage, and ethics without writing it down."},
            ],
            "check": {
                "prompt": "Check what you know about protocols.",
                "questions": [
                    {"q": "A protocol is best defined as…", "options": ["a written procedure giving a repeatable result", "a personal promise", "a religious text"], "answer": "a written procedure giving a repeatable result", "explain": "Repeatability under the same steps is the test."},
                    {"q": "The value of recording when a protocol failed is that…", "options": ["it tells you what to change", "it proves nothing", "it is bad luck"], "answer": "it tells you what to change", "explain": "Failures give the most specific information about limits."},
                ],
            },
        },
        {
            "slug": "seven-day-protocol",
            "title": "A Seven-Day Protocol",
            "order": 4,
            "minutes": 20,
            "summary": "Write, run, and review one week of practice.",
            "learn": [
                {"type": "p", "text": "Pick one thing you want to change and build a seven-day protocol for it. Keep it small enough that you can complete it on your worst day, and write the one-line review each evening. This is the same method a farmer keeps a field diary, or a trader keeps a journal: short, dated, honest."},
                {"type": "list", "items": [
                    "One behaviour, one time of day, seven days.",
                    "One sentence a day: what happened, not what you intended.",
                    "End of week: what would you change in the protocol?",
                ]},
                {"type": "activity", "title": "Run the protocol", "text": "Write the protocol, run it for seven days, and submit the diary plus your revision."},
            ],
            "check": {
                "prompt": "Check what you know about running a protocol.",
                "questions": [
                    {"q": "A seven-day protocol should be small enough that…", "options": ["you can complete it on your worst day", "it impresses other people", "it takes an hour"], "answer": "you can complete it on your worst day", "explain": "Protocols fail by being too ambitious to sustain."},
                    {"q": "A daily log is most useful when it records…", "options": ["what actually happened", "only successes", "intentions"], "answer": "what actually happened", "explain": "Honest records are what make revision possible."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Define a protocol in terms of a repeatable procedure and result.",
        "Write a seven-day protocol and keep a daily log.",
        "Revise a protocol based on what the log shows.",
    ],
}

LEADERSHIP_FOUNDATIONS = {
    "slug": "african-leadership-traditions",
    "title": "African Leadership Traditions",
    "summary": "Ubuntu, harambee, councils, and the leaders who worked through institutions.",
    "order": 4,
    "lessons": [
        {
            "slug": "servant-and-council-leadership",
            "title": "Servant and Council Leadership",
            "order": 8,
            "minutes": 25,
            "summary": "Models of authority that answer to the community.",
            "learn": [
                {"type": "p", "text": "African political traditions include several working models of leadership that answer to the community. Ubuntu — 'I am because we are' — makes a leader's legitimacy rest on the group's wellbeing. Harambee, Swahili for 'all pull together', describes collective labour organised by agreement. The Oromo Gadaa system rotated an elected council every eight years with a women's veto. In many Ghanaian societies a queen mother (nana) nominates and can remove the chief. In the Haudenosaunee Confederacy, clan mothers selected chiefs."},
                {"type": "list", "items": [
                    "Ubuntu: legitimacy through shared wellbeing.",
                    "Harambee: work organised collectively, by agreement.",
                    "Gadaa: fixed terms, councils, and formal vetoes.",
                    "Clan mothers and queen mothers: nomination and removal power.",
                ]},
                {"type": "example", "title": "The common feature", "text": "In each, the leader holds office by serving the community and can be removed by it. Authority is accountable, not absolute."},
            ],
            "check": {
                "prompt": "Check what you know about African leadership traditions.",
                "questions": [
                    {"q": "Ubuntu holds that leadership legitimacy rests on…", "options": ["the wellbeing of the group", "personal wealth", "military force"], "answer": "the wellbeing of the group", "explain": "'I am because we are' ties authority to collective welfare."},
                    {"q": "In Gadaa, the women's assembly could…", "options": ["consult and block harmful decisions", "appoint the king alone", "levy taxes only"], "answer": "consult and block harmful decisions", "explain": "It held a consultative and veto function in public life."},
                ],
            },
        },
        {
            "slug": "organisers-not-heroes",
            "title": "Organisers, Not Heroes",
            "order": 9,
            "minutes": 25,
            "summary": "Ella Baker's method: build leadership that outlives you.",
            "learn": [
                {"type": "p", "text": "Ella Baker, working for decades across the NAACP, SCLC, and SNCC, argued against movements built around single charismatic leaders. Her method was group-centred leadership: train local people, keep power distributed, and build institutions that survive the loss of any one person. Fannie Lou Hamer, Septima Clark, and Bob Moses all worked this way — the schools, citizenship schools, and voter-registration projects they built outlasted the campaigns that started them."},
                {"type": "list", "items": [
                    "Train people, do not recruit followers.",
                    "Distribute the jobs so the work is not one person's knowledge.",
                    "Build a structure with records and succession.",
                    "Measure success by how many people can now do the work.",
                ]},
                {"type": "tip", "text": "Baker's test is uncomfortable and useful: if you disappeared, would the work continue?"},
                {"type": "activity", "title": "Audit your group", "text": "For a group you belong to, list who holds what knowledge. Write the two steps that would make it survive your absence."},
            ],
            "check": {
                "prompt": "Check what you know about organising.",
                "questions": [
                    {"q": "Group-centred leadership means…", "options": ["power and knowledge are distributed", "one person decides", "no one decides"], "answer": "power and knowledge are distributed", "explain": "Baker argued movements die when they depend on a single leader."},
                    {"q": "Septima Clark is known for building…", "options": ["citizenship schools that taught literacy and voting", "a newspaper", "a bank"], "answer": "citizenship schools that taught literacy and voting", "explain": "Her schools trained people to pass literacy tests and register."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Describe African leadership models in which authority is accountable.",
        "Explain the difference between a movement and an institution.",
        "Apply group-centred leadership to an organisation you know.",
    ],
}

LIFE_SKILLS_FOUNDATIONS = {
    "slug": "ancestral-nutrition-and-community-care",
    "title": "Ancestral Nutrition, Health, and Community Care",
    "summary": "Food, health, and care as skills and as inheritance.",
    "order": 4,
    "lessons": [
        {
            "slug": "ancestral-nutrition",
            "title": "Ancestral Nutrition",
            "order": 9,
            "minutes": 25,
            "summary": "What the historical diet actually contained, and why it matters now.",
            "learn": [
                {"type": "p", "text": "Historic West and Central African diets were largely plant-forward: greens, beans, yams, millet, sorghum, plantains, peanuts, okra, peppers, and fish where available — high in fibre and paired with whole grains. Soul food historically looked similar (greens, pot liquor, beans, corn) until the twentieth century changed what was affordable. Modern diets add refined grains, sugar, and fat, and metabolic disease followed. This is evidence about diet, not nostalgia about the past."},
                {"type": "list", "items": [
                    "Traditional: whole grains, legumes, greens, tubers, peppers, seeds.",
                    "Cook techniques: pot liquor, slow greens, okra as thickener.",
                    "Reading labels: added sugar and sodium per serving, not per package.",
                    "Budget: dried beans and seasonal vegetables are cheaper than processed staples.",
                ]},
                {"type": "example", "title": "A comparison", "text": "Cook one ancestral-pattern meal and one typical convenience meal. Compare fibre and sodium per serving from the labels and note the price per serving for each."},
            ],
            "check": {
                "prompt": "Check what you know about ancestral nutrition.",
                "questions": [
                    {"q": "Historic West African diets were characterised by…", "options": ["whole grains, legumes, and greens", "refined sugar and white flour", "mostly dairy"], "answer": "whole grains, legumes, and greens", "explain": "The traditional pattern was plant-forward and high-fibre."},
                    {"q": "The strongest argument for ancestral-pattern eating is…", "options": ["documented differences in diet and metabolic disease", "that it is new", "that it is fashionable"], "answer": "documented differences in diet and metabolic disease", "explain": "It rests on evidence, not preference."},
                ],
            },
        },
        {
            "slug": "community-care",
            "title": "Community Care as a Practice",
            "order": 10,
            "minutes": 25,
            "summary": "Care networks that are not optional extras.",
            "learn": [
                {"type": "p", "text": "Care in Black communities has always been organised, not only personal. Midwives, church auxiliaries, mutual aid societies, the Black Panther Party's free breakfast and free clinics, and health cooperatives all delivered care where formal systems would not. Those structures are models, not history lessons: a neighbourhood care network needs a roster, a referral list, and a way to pay for supplies."},
                {"type": "list", "items": [
                    "Know your referral list: clinic, pharmacy, dentist, mental health, transport.",
                    "Keep a care roster: who checks on whom, and how often.",
                    "Emergency information in one place: allergies, medications, next of kin.",
                    "Privacy: consent before you share anyone's information.",
                ]},
                {"type": "tip", "text": "The Panthers' breakfast program was evidence, not charity — it showed that basic care could be delivered reliably by community organisation."},
            ],
            "check": {
                "prompt": "Check what you know about community care.",
                "questions": [
                    {"q": "A community care network needs at minimum…", "options": ["a roster, a referral list, and a funding plan", "a title", "a logo"], "answer": "a roster, a referral list, and a funding plan", "explain": "Structure is what makes it survive contact with real life."},
                    {"q": "Before sharing anyone's care information you should…", "options": ["get their consent", "post it publicly", "wait for an emergency"], "answer": "get their consent", "explain": "Privacy protection is part of the practice."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Describe the historic diet pattern and evaluate a modern diet against it.",
        "Build a personal and family referral list.",
        "Explain how community care structures are organised and why consent matters.",
    ],
}

MENS_LIFE_SKILLS = {
    "slug": "manhood-mentorship-stewardship",
    "title": "Manhood, Mentorship, and Stewardship",
    "summary": "Responsibility, mentorship, and the economic work of family and community.",
    "order": 3,
    "lessons": [
        {
            "slug": "mentorship-and-responsibility",
            "title": "Mentorship and Responsibility",
            "order": 5,
            "minutes": 22,
            "summary": "What a mentor does, and what stewardship actually requires.",
            "learn": [
                {"type": "p", "text": "Across many African and diasporic cultures, manhood is defined by responsibility to others — to family, to younger people, to the community — rather than by dominance. Mentorship is the mechanism: you pass on what you know to someone younger. The test is practical — what can the other person now do that they could not do before?"},
                {"type": "list", "items": [
                    "Teach one concrete skill, not a lecture.",
                    "Show up on a schedule; reliability is most of the message.",
                    "Open doors: introductions, references, first customers.",
                    "Hold confidence: what you are told stays with you.",
                ]},
                {"type": "tip", "text": "Mentoring also means saying the hard sentence. A mentor who never corrects is a cheerleader, not a teacher."},
            ],
            "check": {
                "prompt": "Check what you know about mentorship.",
                "questions": [
                    {"q": "The practical test of mentorship is…", "options": ["what the other person can now do", "how long you talked", "how many people know about it"], "answer": "what the other person can now do", "explain": "Mentorship is measured in capability transfer."},
                    {"q": "Reliability in mentoring matters because…", "options": ["it is the substance of the commitment", "it looks impressive", "it is a formality"], "answer": "it is the substance of the commitment", "explain": "Consistent presence signals that the person matters."},
                ],
            },
        },
        {
            "slug": "the-economics-of-manhood",
            "title": "The Economics of Manhood",
            "order": 6,
            "minutes": 22,
            "summary": "Budgets, insurance, and the work of building rather than consuming.",
            "learn": [
                {"type": "p", "text": "Stewardship has a balance sheet: an emergency fund, insurance where you can get it, a will if you have dependents, and a plan that survives a bad month. Black families have historically had to build this themselves, because access to mainstream credit and insurance was refused. Credit unions and fraternal mutual aid societies are the institutions that filled the gap — they still exist for exactly this purpose."},
                {"type": "list", "items": [
                    "Emergency fund: three months of core expenses, built in small steps.",
                    "Insurance: life and health are the first two for anyone with dependents.",
                    "A will and beneficiary designations: what happens to what you have.",
                    "Pooled savings: a rotating savings group or a credit union.",
                ]},
                {"type": "activity", "title": "Your sheet", "text": "Write a one-page balance sheet of your own: what you own, what you owe, and the one gap you will close this quarter."},
            ],
            "check": {
                "prompt": "Check what you know about stewardship.",
                "questions": [
                    {"q": "The first financial gap to close is usually…", "options": ["an emergency fund", "an investment portfolio", "a luxury purchase"], "answer": "an emergency fund", "explain": "It is what prevents a bad month becoming a disaster."},
                    {"q": "Rotating savings groups work by…", "options": ["each member contributing regularly and receiving the pooled amount in turn", "borrowing from a bank", "lottery"], "answer": "each member contributing regularly and receiving the pooled amount in turn", "explain": "The pool circulates among members as a form of mutual credit."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Describe what mentorship transfers and how to do it reliably.",
        "Build a personal balance sheet and close one gap.",
        "Explain how pooled savings institutions work.",
    ],
}

WOMENS_LIFE_SKILLS = {
    "slug": "womanhood-building-and-the-village",
    "title": "Womanhood, Building, and the Village",
    "summary": "Women's institutions, economic building, and the work that moved a country.",
    "order": 3,
    "lessons": [
        {
            "slug": "womens-institutions",
            "title": "Women's Institutions",
            "order": 5,
            "minutes": 22,
            "summary": "Clan mothers, councils, and the organisations women actually built.",
            "learn": [
                {"type": "p", "text": "Women's public authority has deep roots: Haudenosaunee clan mothers selected and could remove chiefs; Ashanti queen mothers hold a role in governance; in Oromo Gadaa a women's assembly could veto harmful decisions. In the United States, Black women built the institutions that moved policy — Septima Clark's citizenship schools taught literacy and voting, Ella Baker organised across three major organisations, Fannie Lou Hamer fed 1,500 families while registering voters, and Madam C.J. Walker employed thousands of women agents."},
                {"type": "list", "items": [
                    "Clan mothers and queen mothers: nomination and removal power.",
                    "Gadaa women's assembly: a formal veto.",
                    "Citizenship schools: literacy as the tool of suffrage.",
                    "Sales cooperatives: Walker's agents as an economic network.",
                ]},
                {"type": "example", "title": "The pattern", "text": "In every case, women's authority was institutional — written into rules — rather than informal favour. Structures outlast individuals."},
            ],
            "check": {
                "prompt": "Check what you know about women's institutions.",
                "questions": [
                    {"q": "In the Haudenosaunee system, clan mothers…", "options": ["selected chiefs and could remove them", "had no public role", "only farmed"], "answer": "selected chiefs and could remove them", "explain": "Appointment and removal were institutional powers."},
                    {"q": "Septima Clark's citizenship schools taught…", "options": ["literacy and the steps to voting", "first aid", "accounting"], "answer": "literacy and the steps to voting", "explain": "They trained people to pass literacy tests and register to vote."},
                ],
            },
        },
        {
            "slug": "building-the-village",
            "title": "Building the Village",
            "order": 6,
            "minutes": 22,
            "summary": "A practical structure for care, income, and mutual support.",
            "learn": [
                {"type": "p", "text": "A village is a structure you can actually build: a small group that pools money, covers emergencies, mentors children, and buys collectively. The Free African Society (1787) did exactly this with dues, burial aid, and support for widows. Yours needs three things — a membership list, a written rule for the money, and a way to decide."},
                {"type": "list", "items": [
                    "Membership: who is in, and how someone joins.",
                    "The money: dues, what it covers, and how decisions to spend it are made.",
                    "The work: who calls, who records, and who holds the cash.",
                    "Privacy: nothing about a member is shared without her agreement.",
                ]},
                {"type": "activity", "title": "Draft the rules", "text": "Draft one page of rules for a support group of 6–12 people: membership, dues, what the pool covers, decision rules, and privacy."},
            ],
            "check": {
                "prompt": "Check what you know about building a village.",
                "questions": [
                    {"q": "A support group's rules should specify first…", "options": ["membership and how the money is handled", "a name", "a meeting place"], "answer": "membership and how the money is handled", "explain": "Most groups fail on those two points."},
                    {"q": "Privacy in a support group means…", "options": ["no member's information is shared without agreement", "everyone tells everything", "only the leader knows"], "answer": "no member's information is shared without agreement", "explain": "Consent is the structural protection."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Describe women's institutional authority in African and diasporic traditions.",
        "Name specific Black women who built organisations and what they built.",
        "Draft workable rules for a mutual support group.",
    ],
}


# ── HIGH SCHOOL (9–12) ─────────────────────────────────────────────────────

ALGEBRA_1_GRADE_9 = {
    "slug": "algebra-in-african-engineering",
    "title": "Algebra in African Engineering",
    "summary": "Linear functions, ratios, and self-similar geometry in African architecture.",
    "order": 3,
    "lessons": [
        {
            "slug": "scaling-and-the-fractal-city",
            "title": "Scaling and the Fractal City",
            "order": 6,
            "minutes": 25,
            "summary": "Self-similarity as a geometry, discovered in villages and named in the 1970s.",
            "learn": [
                {"type": "p", "text": "Ba'ilé villages in Côte d'Ivoire are laid out so that each hut looks like a copy of the whole village: a rectangle of houses with the same proportions, repeated. That is self-similarity — the same shape at every scale — a geometry that mathematicians named 'fractal' only in the 1970s. For algebra, self-similarity gives you a direct proportionality: if the small scale has perimeter p, the scale-2 version has 2p, the scale-3 version 3p. Linear relationships are exactly how a village scales without redesigning it."},
                {"type": "list", "items": [
                    "Self-similar: each small part has the same shape as the whole.",
                    "Direct variation: y = kx — double x, double y.",
                    "Scale factor: lengths scale linearly, areas scale with the square.",
                    "Great Zimbabwe's and Djenné's walls show proportional modules repeated.",
                ]},
                {"type": "example", "title": "Worked", "text": "A village module is a rectangle 4 m by 6 m, perimeter 20 m. A scale-2 module is 8 m by 12 m, perimeter 40 m. Area scales 9× from scale 1 to scale 3 (4·6 = 24 → 36·... : k² × 24)."},
                {"type": "activity", "title": "Model it", "text": "Draw a self-similar layout at scales 1, 2 and 3. Write the linear rule for perimeter and the quadratic rule for area."},
            ],
            "check": {
                "prompt": "Check your understanding of scaling.",
                "questions": [
                    {"q": "If a shape is self-similar and lengths double, the area becomes…", "options": ["four times larger", "twice larger", "the same"], "answer": "four times larger", "explain": "Area scales with the square of the linear scale factor."},
                    {"q": "A fractal pattern is one in which…", "options": ["each small part resembles the whole", "nothing repeats", "only curves appear"], "answer": "each small part resembles the whole", "explain": "Self-similarity at every scale is the defining property."},
                ],
            },
        },
        {
            "slug": "djenne-vault-geometry",
            "title": "Geometry of the Vault",
            "order": 7,
            "minutes": 25,
            "summary": "Arches, slopes, and load — algebra and geometry in masonry.",
            "learn": [
                {"type": "p", "text": "A Nubian vault spans a room with no timber: bricks lean against a guide wall until the arch closes, and then the load travels as compression to the walls. The arch's geometry is described by a parabola y = ax(h − x), with a controlling the rise. Batter — the slight inward slope of a wall — is a linear relationship between height and horizontal offset that lowers the centre of gravity."},
                {"type": "list", "items": [
                    "Parabolic arch: y = ax(h−x), zero at the two abutments.",
                    "Compression: the load travels along the curve to the supports.",
                    "Batter: a wall leaning inward gains stability at no material cost.",
                    "Great Zimbabwe: dry-stone masonry held by friction and interlock, with no mortar.",
                ]},
                {"type": "example", "title": "Worked", "text": "A 4 m span with a 1 m crown rise has a = 0.25 in y = ax(4−x) — check: at x = 2, y = 0.25·2·2 = 1 m."},
                {"type": "activity", "title": "Sketched section", "text": "Draw the section of a vault and derive the coefficients for a 5 m span and a 1.25 m rise."},
            ],
            "check": {
                "prompt": "Check your understanding of the geometry.",
                "questions": [
                    {"q": "A modelled arch y = ax(h−x) is zero at…", "options": ["the two abutments x=0 and x=h", "the crown", "the centre only"], "answer": "the two abutments x=0 and x=h", "explain": "The abutments are where the curve meets the supports."},
                    {"q": "Batter improves a wall's stability by…", "options": ["moving mass inward and lowering the centre of gravity", "adding weight at the top", "removing mass"], "answer": "moving mass inward and lowering the centre of gravity", "explain": "The wall resists overturning better."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Model self-similar geometry with a scale factor and a direct variation rule.",
        "Write the parabolic arch for a given span and rise.",
        "Explain batter and interlock as stability mechanisms.",
    ],
}

BIOLOGY_CELLS_GENES = {
    "slug": "african-botanical-medicine-cells",
    "title": "African Botanical Medicine and Cells",
    "summary": "Cells, compounds, and the pharmacology that began in plant knowledge.",
    "order": 4,
    "lessons": [
        {
            "slug": "compounds-and-cells",
            "title": "Compounds and Cells",
            "order": 9,
            "minutes": 25,
            "summary": "How plant chemicals act on cells, and the method that verifies it.",
            "learn": [
                {"type": "p", "text": "Plants make chemicals to defend themselves, and those chemicals act on cells — ours included. Alkaloids act on nerve cells, glycosides on heart muscle, terpenoids as anti-inflammatories. African pharmacopoeias supplied compounds now used in Western medicine, including ouabain (from Strophanthus, used as a cardiac stimulant) and physostigmine (from the Calabar bean, for glaucoma). Ethnobotany is the study of how people identified, classified, and transmitted that knowledge."},
                {"type": "list", "items": [
                    "Alkaloids: act on the nervous system — quinine, caffeine, physostigmine.",
                    "Glycosides: act on the heart — ouabain from Strophanthus.",
                    "Terpenoids: scents, resins, anti-inflammatories.",
                    "Method: extraction, dose, control, replication.",
                ]},
                {"type": "example", "title": "Cell-level story", "text": "Physostigmine inhibits acetylcholinesterase, so the neurotransmitter stays active longer in the synapse — the same mechanism modern glaucoma drugs target. The plant was known long before the enzyme was."},
            ],
            "check": {
                "prompt": "Check your understanding of plant chemistry.",
                "questions": [
                    {"q": "Physostigmine comes from…", "options": ["the Calabar bean", "a fungus", "a fish"], "answer": "the Calabar bean", "explain": "It was derived from the Calabar bean and is used for glaucoma."},
                    {"q": "Alkaloids typically act on…", "options": ["the nervous system", "bone density", "blood clotting"], "answer": "the nervous system", "explain": "Many alkaloids affect nerve signalling, which is why they are pharmacologically active."},
                ],
            },
        },
        {
            "slug": "screen-a-plant",
            "title": "Screen a Plant, Honestly",
            "order": 10,
            "minutes": 25,
            "summary": "Doing the experiment that turns tradition into science.",
            "learn": [
                {"type": "p", "text": "A plant claim from traditional knowledge is a hypothesis. The scientific method tests it: extract, dose, control, replicate. The control shows what happens without the treatment, and a sample of one is not data. Traditional communities often held this same rigour — healers recorded which preparation, which part of the plant, which season, and what dose — the information that a laboratory still needs."},
                {"type": "list", "items": [
                    "Observation: which plant, part, preparation, and claimed effect.",
                    "Hypothesis: a compound produces effect X.",
                    "Experiment: extraction, dosing, control, and recorded outcome.",
                    "Conclusion: what the data support — and what they do not.",
                ]},
                {"type": "tip", "text": "Never ingest unknown plants. Work with microscopy, indicator strips, or literature analysis, and document your safety rules."},
                {"type": "activity", "title": "Proposal", "text": "Write a one-page study proposal: question, hypothesis, method with control, expected result, and safety rules."},
            ],
            "check": {
                "prompt": "Check what you know about screening.",
                "questions": [
                    {"q": "The purpose of a control is to…", "options": ["show what happens without the treatment", "make results look better", "reduce cost"], "answer": "show what happens without the treatment", "explain": "The control isolates the effect of the variable being tested."},
                    {"q": "Traditional plant claims function in research as…", "options": ["leads that direct the hypothesis", "conclusions", "irrelevant stories"], "answer": "leads that direct the hypothesis", "explain": "Tradition supplies testable leads; controlled study confirms or refutes them."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Describe classes of plant compounds and the cells they act on.",
        "Name compounds from African pharmacopoeias in modern medicine.",
        "Design a controlled test for a plant claim.",
    ],
}

APPLIED_ELECTRICAL_YEAR_1 = {
    "slug": "black-electrical-engineering",
    "title": "Black Electrical Engineering",
    "summary": "Filaments, components, and computers — the Black engineers behind them.",
    "order": 4,
    "lessons": [
        {
            "slug": "latimer-boykin-dean",
            "title": "Latimer, Boykin, Dean",
            "order": 9,
            "minutes": 25,
            "summary": "What specific engineers designed, and how the systems worked.",
            "learn": [
                {"type": "p", "text": "Lewis H. Latimer drafted the patent drawings for Bell's telephone and developed the carbon filament that made Edison's bulb practical — he also wrote the technical book on incandescent lighting installation. Otis Boykin designed precision resistors used in pacemakers, guided missiles, and IBM computers. Mark Dean, an IBM engineer, holds patents fundamental to the personal computer, including the ISA bus architecture that let peripherals connect to the machine. Each of these is circuit-level work you can reason about."},
                {"type": "list", "items": [
                    "Latimer: carbon filament — high resistance, long life, and uniform glow.",
                    "Boykin: precision resistors — low tolerance, essential to medical and computing circuits.",
                    "Dean: ISA bus — the interface between a CPU and its peripherals.",
                ]},
                {"type": "example", "title": "Why the filament matters", "text": "A filament must have high resistance to heat and high melting point to last. Carbon beat the alternatives on both; Latimer's process made it manufacturable."},
            ],
            "check": {
                "prompt": "Check what you know about Black electrical engineers.",
                "questions": [
                    {"q": "Latimer's carbon filament improved the light bulb by…", "options": ["lasting longer with a more uniform glow", "using less glass", "needing no current"], "answer": "lasting longer with a more uniform glow", "explain": "Carbon's resistivity and thermal characteristics were superior."},
                    {"q": "Mark Dean's work at IBM contributed to…", "options": ["the PC's internal bus architecture", "the telegraph", "dynamo design"], "answer": "the PC's internal bus architecture", "explain": "His patents cover the interface standard that connected devices to a CPU."},
                ],
            },
        },
        {
            "slug": "rice-coast-water-engineering",
            "title": "Water Engineering: The Rice Coast",
            "order": 10,
            "minutes": 25,
            "summary": "Tidal irrigation, control gates, and energy in water.",
            "learn": [
                {"type": "p", "text": "The rice economy of the American South was built on water engineering that Africans brought from the Senegal–Gambia basin: graded fields, trunk gates, canals, and controlled draining. Hydraulically it is a control system: flow in is throttled, flow out is throttled, and the field holds a set depth. The energy in falling water, P = ρghQ, is a quantity an electrician already reads on a meter — the same physics drives a water wheel and a hydroelectric turbine."},
                {"type": "list", "items": [
                    "Trunk: a gate at the field inlet, throttled against the tide.",
                    "Drainage ditch: controlled outflow to prevent waterlogging.",
                    "Energy: P = ρ g h Q — density, gravity, head, and flow.",
                    "Failure modes: seepage, blockage, and tidal timing.",
                ]},
                {"type": "activity", "title": "Compute", "text": "For a head of 1.5 m and a flow of 0.2 m³/s, compute the available power and compare it to a typical household load."},
            ],
            "check": {
                "prompt": "Check what you know about water engineering.",
                "questions": [
                    {"q": "Tidal rice irrigation needs a way to…", "options": ["throttle inflow and outflow independently", "raise water with pumps only", "avoid all water"], "answer": "throttle inflow and outflow independently", "explain": "Field depth is set by controlling both directions of flow."},
                    {"q": "The power in falling water is given by…", "options": ["P = ρghQ", "V = IR", "P = I²R"], "answer": "P = ρghQ", "explain": "Hydraulic power depends on density, gravity, head, and flow rate."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Name Black electrical engineers and describe their circuit-level work.",
        "Explain tidal irrigation as a hydraulic control system.",
        "Compute hydraulic power and compare with an electrical load.",
    ],
}

DIGITAL_ART_GRADE_9 = {
    "slug": "diaspora-visual-language",
    "title": "Diaspora Visual Language, Digitised",
    "summary": "Adinkra, Kente, and the diaspora visual tradition rendered in digital media.",
    "order": 3,
    "lessons": [
        {
            "slug": "symbol-systems-aesthetic",
            "title": "Symbol Systems as Aesthetic",
            "order": 6,
            "minutes": 22,
            "summary": "Adinkra symbols and Kente strips as designed systems, not decoration.",
            "learn": [
                {"type": "p", "text": "Adinkra symbols are stamped from calabash and each carries a proverb — they are writing in picture form, and the symbols are drawn from geometry, plants, and architecture. Kente is handwoven in strips whose sequences carry meaning. Both are systems: a vocabulary, a syntax of repetition, and a colour logic. That makes them ideal for digital work, because a digital artist works in systems too."},
                {"type": "list", "items": [
                    "Adinkra: a named symbol per proverb — e.g. Gye Nyame (except God), Sankofa (return and take).",
                    "Kente: strip patterns repeated in a fixed order, with named rules.",
                    "Both are built on a grid, so they transfer to a pixel or vector canvas.",
                ]},
                {"type": "example", "title": "Design exercise", "text": "Take one Adinkra symbol. Reconstruct it on a vector grid and then create a variant that expresses a new saying of your own. You are now doing exactly what traditional weavers and stampers do."},
            ],
            "check": {
                "prompt": "Check what you know about Adinkra and Kente.",
                "questions": [
                    {"q": "Adinkra symbols are…", "options": ["stamped symbols that carry proverbs", "painted portraits", "sculpted masks"], "answer": "stamped symbols that carry proverbs", "explain": "Each symbol stands for a specific saying."},
                    {"q": "Kente is organised as…", "options": ["woven strips in a repeating named sequence", "loose threads", "printed repeats from a machine"], "answer": "woven strips in a repeating named sequence", "explain": "Strip patterns and their order carry meaning."},
                ],
            },
        },
        {
            "slug": "afrofuturism-and-the-mural",
            "title": "Afrofuturism and the Mural",
            "order": 7,
            "minutes": 22,
            "summary": "The future tense and the public wall.",
            "learn": [
                {"type": "p", "text": "Afrofuturism is a creative movement that treats Black culture as a future-facing tradition rather than a historical exhibit — from Sun Ra's cosmic philosophy to Octavia Butler's fiction to contemporary artists and musicians. Its visual language combines African motifs with technology, space, and speculative architecture. Murals, meanwhile, are the public wall as a gallery: community-chosen subjects on surfaces everyone sees. Digital tools make both reproducible and shareable."},
                {"type": "list", "items": [
                    "Afrofuturism: African motifs + speculative futures.",
                    "The mural: negotiated subject, public wall, collective authorship.",
                    "Digital work: scalable, versioned, and documented.",
                ]},
                {"type": "activity", "title": "Make a poster", "text": "Design a poster for a community project using one diaspora motif and one futuristic element. Write the artist's statement naming your sources."},
            ],
            "check": {
                "prompt": "Check what you know about Afrofuturism.",
                "questions": [
                    {"q": "Afrofuturism generally combines…", "options": ["African and diasporic motifs with speculative futures", "only historical scenes", "Abstract fields of colour"], "answer": "African and diasporic motifs with speculative futures", "explain": "It is defined by treating Black culture as a future-facing tradition."},
                    {"q": "A community mural project is distinctive because…", "options": ["the subject is negotiated with the community", "it is never photographed", "it uses only one colour"], "answer": "the subject is negotiated with the community", "explain": "The process of choosing the subject is part of the work."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Describe Adinkra and Kente as systems and reconstruct one symbol.",
        "Explain Afrofuturism's visual vocabulary.",
        "Produce a digital poster citing its sources.",
    ],
}

CHEMISTRY_GRADE_10 = {
    "slug": "african-botanical-chemistry",
    "title": "African Botanical Chemistry",
    "summary": "Extraction, alkaloids, and the chemistry of plant knowledge.",
    "order": 3,
    "lessons": [
        {
            "slug": "extraction-and-compounds",
            "title": "Extraction and Compounds",
            "order": 7,
            "minutes": 25,
            "summary": "Water decoction, tincture, steam distillation, and what comes out.",
            "learn": [
                {"type": "p", "text": "A healer's prepared tea is a chemistry lab: water extraction pulls polar compounds, alcohol tinctures pull less polar ones, and steam distillation carries volatile oils. Traditional systems chose methods deliberately — a decoction (boiling) extracts more from tough material than an infusion (steeping). Knowing the method lets you reason about what is in the cup."},
                {"type": "list", "items": [
                    "Infusion: steeping — gentler, fewer dissolved compounds.",
                    "Decoction: boiling — fuller extraction from bark, root, seed.",
                    "Tincture: alcohol extraction — different solubility profile.",
                    "Steam distillation: volatile oils out without burning the material.",
                ]},
                {"type": "example", "title": "Chemistry in the kitchen", "text": "A decoction of ground bark is more concentrated than an infusion of the same mass, because solubility rises with temperature and contact time. That is Le Chatelier's principle at work on a stove."},
            ],
            "check": {
                "prompt": "Check what you know about extraction.",
                "questions": [
                    {"q": "A decoction differs from an infusion in that it…", "options": ["is boiled, giving fuller extraction", "uses cold water only", "uses alcohol"], "answer": "is boiled, giving fuller extraction", "explain": "Higher temperature generally increases solubility."},
                    {"q": "A tincture uses alcohol because alcohol…", "options": ["dissolves compounds water does not", "is cheaper", "preserves colours"], "answer": "dissolves compounds water does not", "explain": "Different solvents dissolve different compound classes."},
                ],
            },
        },
        {
            "slug": "carver-and-crop-chemistry",
            "title": "Carver and Crop Chemistry",
            "order": 8,
            "minutes": 25,
            "summary": "Nitrogen fixation, soil chemistry, and industrial use of crops.",
            "learn": [
                {"type": "p", "text": "George Washington Carver's work was applied chemistry on exhausted soils: cotton strips nitrogen, legumes restore it through root-nodule bacteria that convert atmospheric N₂ into ammonia. He also developed hundreds of products from peanuts and sweet potatoes — flour, oil, dye, plastic, cosmetics — so that farmers rotating crops had markets for the rotation. The chemistry is stoichiometry, catalysis, and product development, taught in bulletins any farmer could read."},
                {"type": "list", "items": [
                    "Nitrogen fixation: N₂ → NH₃ in the nodule by bacterial enzyme.",
                    "Crop rotation: alternate nitrogen-demanding and nitrogen-fixing crops.",
                    "Product development: creating demand for the rotation's output.",
                    "Soil organic matter: rotation rebuilds it; monoculture depletes it.",
                ]},
                {"type": "activity", "title": "Balance it", "text": "Write the balanced half-reaction for nitrogen fixation, then plan a four-year rotation and state what happens to soil nitrogen each year."},
            ],
            "check": {
                "prompt": "Check what you know about Carver's chemistry.",
                "questions": [
                    {"q": "Nitrogen fixation converts atmospheric N₂ into…", "options": ["ammonia in the root nodule", "carbon dioxide", "nitric acid in the leaf"], "answer": "ammonia in the root nodule", "explain": "Bacterial enzymes in nodules reduce nitrogen to ammonia."},
                    {"q": "Carver developed products from peanuts so that…", "options": ["farmers rotating crops had markets for the rotation", "peanuts tasted better", "soil needed less water"], "answer": "farmers rotating crops had markets for the rotation", "explain": "Rotation only works if the new crops have buyers."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Compare extraction methods and reason about what each dissolves.",
        "Explain nitrogen fixation chemically and its role in crop rotation.",
        "Connect soil chemistry to agricultural economics.",
    ],
}

ELECTRICAL_YEAR_2 = {
    "slug": "energy-sovereignty-and-vaults",
    "title": "Energy Sovereignty and Earth Construction",
    "summary": "Off-grid design, embodied carbon, and the engineering of Djenne and the Nubian vault.",
    "order": 7,
    "lessons": [
        {
            "slug": "passive-first-energy",
            "title": "Passive First",
            "order": 19,
            "minutes": 25,
            "summary": "Orientation, mass, shading, and ventilation before any equipment.",
            "learn": [
                {"type": "p", "text": "Off-grid design has a hierarchy: passive first, active second. Orientation, thermal mass, shading, and ventilation reduce the demand before a panel or a battery is sized. Thick adobe walls of Djené absorb daytime heat and release it at night — that lag is the same physics that makes a modern passive-solar house efficient. Sizing comes after: if you do not know the load, you cannot size the array."},
                {"type": "list", "items": [
                    "Passive: orientation, insulation, thermal mass, shading, ventilation.",
                    "Load first: list appliances, runtime, and wattage.",
                    "Array sizing: daily energy demand ÷ (peak sun hours × system derating).",
                    "Storage: battery capacity for the nights you must cover.",
                ]},
                {"type": "example", "title": "Worked", "text": "A 40 m² dwelling needing 1.5 kWh/day with 5 peak sun hours and 0.7 derating needs a 1.5 / (5 × 0.7) ≈ 0.43 kW array — about four 110 W panels."},
            ],
            "check": {
                "prompt": "Check what you know about passive design.",
                "questions": [
                    {"q": "Off-grid design should begin with…", "options": ["passive measures", "generators", "larger batteries"], "answer": "passive measures", "explain": "Reducing demand first is cheaper and more reliable."},
                    {"q": "Array size is found by…", "options": ["dividing daily demand by derated peak sun hours", "counting outlets", "guessing"], "answer": "dividing daily demand by derated peak sun hours", "explain": "System output must cover the load after losses."},
                ],
            },
        },
        {
            "slug": "embodied-carbon",
            "title": "Embodied Carbon",
            "order": 20,
            "minutes": 25,
            "summary": "Comparing materials honestly.",
            "learn": [
                {"type": "p", "text": "Embodied carbon is the carbon released to produce and transport a material. Concrete and steel are high; earth and local timber are low. This is the argument of the Nubian vault and adobe practice, made numerically: a wall built from the soil under your feet has minimal transport cost, and the wall itself continues to work for centuries with maintenance."},
                {"type": "list", "items": [
                    "Concrete: high embodied carbon from cement production.",
                    "Fired brick: medium — from firing energy.",
                    "Adobe and rammed earth: very low — local soil, sun-dried.",
                    "Local materials: lower transport emissions and local employment.",
                ]},
                {"type": "activity", "title": "Compare", "text": "Compare two wall systems for a 100 m² wall: adobe and fired brick. Compute the material carbon per m² and the difference."},
            ],
            "check": {
                "prompt": "Check what you know about embodied carbon.",
                "questions": [
                    {"q": "Embodied carbon measures…", "options": ["the emissions released to produce and transport material", "the energy used by occupants", "the building's height"], "answer": "the emissions released to produce and transport material", "explain": "It is the upstream cost of the material itself."},
                    {"q": "Adobe typically has lower embodied carbon than fired brick because…", "options": ["it is dried by the sun rather than fired in a kiln", "it is heavier", "it contains cement"], "answer": "it is dried by the sun rather than fired in a kiln", "explain": "Firing requires energy; sun-drying does not."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Apply the passive-first hierarchy and size a small off-grid system.",
        "Compute and compare embodied carbon of wall systems.",
        "Explain the engineering behind adobe cities and Nubian vaults.",
    ],
}

WORLD_LITERATURE_GRADE_10 = {
    "slug": "reading-the-pan-african-canon",
    "title": "Reading the Pan-African Canon",
    "summary": "Place Achebe, Césaire, and Soyinka beside the standard world-literature list.",
    "order": 3,
    "lessons": [
        {
            "slug": "two-narratives-of-africa",
            "title": "Two Narratives of Africa",
            "order": 6,
            "minutes": 25,
            "summary": "Conrad's backdrop and Achebe's answer.",
            "learn": [
                {"type": "p", "text": "Joseph Conrad's Heart of Darkness uses Africa as a backdrop against which Europeans discover themselves; Chinua Achebe called it dehumanising and answered it with Things Fall Apart, in which Umuofia has courts, religion, and conflict before a missionary arrives. Reading both together is a lesson in narrative perspective: who tells the story, whose interior life is shown, and who is scenery."},
                {"type": "list", "items": [
                    "Conrad: Africa as exterior; the European psychology is the subject.",
                    "Achebe: Igbo civic life; colonial law as the antagonist.",
                    "Aimé Césaire's A Tempest rewrites Shakespeare with Caliban and Ariel as Black actors.",
                    "Reading method: ask who speaks, who is described, and who decides.",
                ]},
                {"type": "example", "title": "Compare a scene", "text": "In both Conrad and Achebe, a river carries meaning. Conrad's river leads into darkness; Achebe's river is the life of a village. Same landscape, opposite camera angle."},
            ],
            "check": {
                "prompt": "Check what you know about these texts.",
                "questions": [
                    {"q": "Achebe wrote Things Fall Apart partly to…", "options": ["answer Conrad's rendering of Africa", "praise British rule", "repudue the novel"], "answer": "answer Conrad's rendering of Africa", "explain": "He deliberately rewrote the perspective Conrad used."},
                    {"q": "Aime Césaire's A Tempest reworks Shakespeare by…", "options": ["casting Caliban and Ariel as Black colonised figures", "removing all characters", "setting it in China"], "answer": "casting Caliban and Ariel as Black colonised figures", "explain": "He turned a colonial subtext into the subject."},
                ],
            },
        },
        {
            "slug": "oral-and-written-together",
            "title": "Oral and Written Together",
            "order": 7,
            "minutes": 25,
            "summary": "The epic, the novel, and the sonnet in one tradition.",
            "learn": [
                {"type": "p", "text": "Much of the world's literature began in performance: the Sundiata epic is performed by griots with a kora, Homer was sung before it was read, and African praise poetry still functions as public address. Claude McKay took the European sonnet — a love form — and filled it with political protest in 'If We Must Die'. Seeing these together shows that literary forms travel across cultures and can be redirected."},
                {"type": "list", "items": [
                    "Oral epic: performed, with improvisation for the audience present.",
                    "The novel: a form that can carry interior life and history.",
                    "The sonnet: fourteen lines with a turn — portable and quotable.",
                ]},
                {"type": "activity", "title": "Compare forms", "text": "Compare one oral epic episode and one novel chapter. Write one paragraph on how each maintains audience attention."},
            ],
            "check": {
                "prompt": "Check what you know about literary forms.",
                "questions": [
                    {"q": "McKay used the sonnet form to…", "options": ["carry political protest", "describe a garden", "teach arithmetic"], "answer": "carry political protest", "explain": "He repurposed a love form for an argument."},
                    {"q": "The Sundiata epic is characterised by…", "options": ["live performance with improvisation", "being read silently", "being recited without music"], "answer": "live performance with improvisation", "explain": "Griots adapt each telling to the audience."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Compare narrative perspective in Conrad and Achebe.",
        "Identify how oral and written forms interact in the tradition.",
        "Analyse how a literary form is repurposed.",
    ],
}

ELA_GRADE_11 = {
    "slug": "rhetoric-of-liberation",
    "title": "Rhetoric of Liberation",
    "summary": "Argument, evidence, and audience in the Black intellectual tradition.",
    "order": 3,
    "lessons": [
        {
            "slug": "wells-baldwin-sankara",
            "title": "Wells, Baldwin, Sankara",
            "order": 5,
            "minutes": 25,
            "summary": "Three rhetorical methods for three different fights.",
            "learn": [
                {"type": "p", "text": "Ida B. Wells built an argument from court records, tabulating lynching charges to refute the official story. James Baldwin addressed the reader personally, putting the audience inside the moral problem. Thomas Sankara spoke plainly to farmers and assemblies, refusing diplomatic register when speaking of debt. Three different rhetorical strategies, each matched to its audience — which is the core skill of rhetorical analysis."},
                {"type": "list", "items": [
                    "Logos: counted evidence, as in Wells's Red Record.",
                    "Pathos and ethos: direct address and personal witness, as in Baldwin.",
                    "Plain style: concrete demands in everyday language, as in Sankara.",
                ]},
                {"type": "example", "title": "Analyse", "text": "In one paragraph of each writer, mark the claim, the evidence, and the move aimed at the audience. Then state which strategy would work on your intended reader."},
            ],
            "check": {
                "prompt": "Check your rhetorical analysis.",
                "questions": [
                    {"q": "Wells's strongest appeal was…", "options": ["counted evidence from records", "emotional description only", "quotation of authorities"], "answer": "counted evidence from records", "explain": "Her case rested on compiled court data."},
                    {"q": "Sankara's distinctive choice was…", "options": ["plain mobilising language before heads of state", "formal legal prose", "silence"], "answer": "plain mobilising language before heads of state", "explain": "He refused register to match the urgency of the subject."},
                ],
            },
        },
        {
            "slug": "write-the-argument",
            "title": "Write the Argument",
            "order": 6,
            "minutes": 25,
            "summary": "Compose and defend a piece of public writing.",
            "learn": [
                {"type": "p", "text": "Public writing is written for a reader who may disagree, and it survives only if it answers the strongest objection. Take a position on a real question raised by any text in this course. Name the evidence, answer the counterargument, and close with what you are asking the reader to do or think."},
                {"type": "list", "items": [
                    "Claim: a debatable sentence you can defend with evidence.",
                    "Evidence: quotation and fact, cited by source.",
                    "Counterargument: the strongest objection, answered.",
                    "Call: the specific action or belief you want from the reader.",
                ]},
                {"type": "activity", "title": "Draft and swap", "text": "Draft 800 words, exchange with a reader, and revise for evidence and counterargument."},
            ],
            "check": {
                "prompt": "Check your writing plan.",
                "questions": [
                    {"q": "An argumentative essay's strongest counterargument…", "options": ["states the best objection and answers it", "is left out", "only restates the thesis"], "answer": "states the best objection and answers it", "explain": "Addressing the strongest objection is what earns credibility."},
                    {"q": "A claim is debatable, which means…", "options": ["reasonable people could disagree", "it is a fact", "it has no position"], "answer": "reasonable people could disagree", "explain": "Arguments are needed only where disagreement is possible."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Analyse claim, evidence, and audience in three rhetorical texts.",
        "Distinguish logos, pathos, and ethos as strategies.",
        "Write and revise an argumentative essay with a counterargument.",
    ],
}


MATH_GRADE_11 = {
    "slug": "data-and-algorithmic-bias",
    "title": "Data and Algorithmic Bias",
    "summary": "Sampling, correlation, and disparate impact measured with real statistics.",
    "order": 3,
    "lessons": [
        {
            "slug": "redlining-data-analysis",
            "title": "Case Study: Redlining, Measured",
            "order": 5,
            "minutes": 25,
            "summary": "Run the analysis on published HOLC data.",
            "learn": [
                {"type": "p", "text": "The Home Owners' Loan Corporation graded neighbourhoods A–D in the 1930s; low-graded areas were denied mortgage credit and were disproportionately Black and immigrant. Because the data are public, the analysis can be done with ordinary statistics: compare mean home values or health outcomes by block grade and compute the effect size. This is a two-sample comparison — the same tool used for any controlled study."},
                {"type": "list", "items": [
                    "Data: HOLC grade by block, with present-day values.",
                    "Statistic: difference in means, expressed in standard deviations.",
                    "Confounder: segregation is the mechanism; HOLC grade is correlated with it.",
                    "Conclusion: state what the data show and what they do not.",
                ]},
                {"type": "example", "title": "The point", "text": "This analysis is reproducible. That reproducibility is what separates a measurable legacy from an opinion about it."},
            ],
            "check": {
                "prompt": "Check what you know about the redlining case study.",
                "questions": [
                    {"q": "HOLC grades were used to…", "options": ["deny credit to whole neighbourhoods", "fund schools", "plant trees"], "answer": "deny credit to whole neighbourhoods", "explain": "Low-graded areas were cut off from mortgage investment."},
                    {"q": "An effect size is best expressed to a reader as…", "options": ["a difference in standard deviations", "a percentage of the sample", "a photograph"], "answer": "a difference in standard deviations", "explain": "Standardised difference lets readers compare across measures."},
                ],
            },
        },
        {
            "slug": "audit-a-model",
            "title": "Audit a Model",
            "order": 6,
            "minutes": 25,
            "summary": "Detecting disparate impact by computing error rates by group.",
            "learn": [
                {"type": "p", "text": "A classifier trained on historical data learns historical patterns, including discrimination. If approval rates differ by group in the training data, a model can reproduce the pattern even when race is not an input — ZIP code and loan amount carry the same information. Disparate impact is detected numerically: compute true positive and false positive rates for each group and compare them."},
                {"type": "list", "items": [
                    "Proxy variable: an allowed attribute correlated with a protected one.",
                    "Label bias: labels record past decisions rather than truth.",
                    "Fairness test: error rates by group must be equal.",
                    "Remedy: re-weighting, re-sampling, or changing the decision variable.",
                ]},
                {"type": "activity", "title": "Run the audit", "text": "Using a public dataset, compute error rates for two groups defined in the data. Report whether they are equal and what could cause a gap."},
            ],
            "check": {
                "prompt": "Check what you know about algorithmic bias.",
                "questions": [
                    {"q": "A proxy variable lets a model…", "options": ["recover a protected attribute indirectly", "run faster", "use less memory"], "answer": "recover a protected attribute indirectly", "explain": "Correlated allowed variables leak forbidden information."},
                    {"q": "To test for disparate impact you compute…", "options": ["error rates by group", "the model's file size", "training time"], "answer": "error rates by group", "explain": "Different error rates across groups are a measurable fairness failure."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Run a two-sample comparison on published redlining data.",
        "Compute and interpret an effect size.",
        "Detect disparate impact by computing error rates by group.",
    ],
}

SCIENCE_GRADE_11 = {
    "slug": "environmental-justice-methods",
    "title": "Environmental Justice and Science Methods",
    "summary": "Measure air, water, and soil in a community, and act on the result.",
    "order": 3,
    "lessons": [
        {
            "slug": "measure-your-environment",
            "title": "Measure Your Environment",
            "order": 6,
            "minutes": 25,
            "summary": "The methods that turned a complaint into a case.",
            "learn": [
                {"type": "p", "text": "Environmental justice began with measurement. Residents of Warren County, North Carolina documented a landfill siting in 1982; Robert Bullard then correlated facility locations with census data and found race predicted siting more reliably than income. Air, water, and soil can be measured with modest instruments, and a well-kept log with dates and locations is what an agency must answer."},
                {"type": "list", "items": [
                    "Air: PM monitoring, and distance to traffic or industry.",
                    "Water: pH, turbidity, and bacterial tests from a lab.",
                    "Soil: lead testing, especially near older paint or industry.",
                    "Documentation: dated logs, GPS, and photographs.",
                ]},
                {"type": "example", "title": "Method matters", "text": "One reading is an anecdote; twenty dated readings across a season are evidence. Design the sampling before you start."},
            ],
            "check": {
                "prompt": "Check what you know about environmental measurement.",
                "questions": [
                    {"q": "Bullard's Dumping in Dixie showed that facility siting was predicted by…", "options": ["race more reliably than income", "altitude", "rainfall"], "answer": "race more reliably than income", "explain": "Race was the strongest predictor in his analysis."},
                    {"q": "A defensible environmental study must have…", "options": ["dated, located, repeatable measurements", "one reading", "anonymous reports"], "answer": "dated, located, repeatable measurements", "explain": "Reproducibility is what makes a measurement useful."},
                ],
            },
        },
        {
            "slug": "act-on-the-evidence",
            "title": "Act on the Evidence",
            "order": 7,
            "minutes": 25,
            "summary": "From a log to a filing to a fix.",
            "learn": [
                {"type": "p", "text": "Evidence changes nothing until it reaches someone with authority. A log becomes a complaint to a state environmental agency, a request for a health consultation, or testimony at a public hearing. The same discipline — dated, located, reproducible — is what makes an agency respond."},
                {"type": "list", "items": [
                    "Complaint: file with the state environmental or health agency.",
                    "Hearing: written public comment, submitted on time.",
                    "Request: ask for the facility's monitoring records.",
                    "Follow-up: keep the log going and record responses.",
                ]},
                {"type": "activity", "title": "Draft the filing", "text": "Using your measurements, draft a two-page letter of complaint with dates, locations, and the specific request."},
            ],
            "check": {
                "prompt": "Check what you know about acting on evidence.",
                "questions": [
                    {"q": "An environmental complaint should name…", "options": ["dates, locations, measurements, and the specific request", "only your feelings", "nothing specific"], "answer": "dates, locations, measurements, and the specific request", "explain": "Specific documentation is what an agency can act on."},
                    {"q": "Requesting a facility's own monitoring records…", "options": ["is a normal part of the process", "is illegal", "never works"], "answer": "is a normal part of the process", "explain": "Facilities are often required to report and can be asked for the data."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Design a sampling plan for air, water, or soil.",
        "Keep dated, located environmental records.",
        "Draft a complaint letter with a specific request.",
    ],
}

SOCIAL_STUDIES_GRADE_11 = {
    "slug": "political-thought-and-solidarity",
    "title": "Political Thought and Global Solidarity",
    "summary": "From the Pan-African congresses to anti-apartheid, one connected movement.",
    "order": 3,
    "lessons": [
        {
            "slug": "congresses-to-revolutions",
            "title": "Congress to Revolution",
            "order": 5,
            "minutes": 25,
            "summary": "How the argument became independence.",
            "learn": [
                {"type": "p", "text": "The Pan-African Congresses of 1900, 1919, and others culminated in Manchester 1945, where Kwame Nkrumah and Jomo Kenyatta attended; Ghana became independent in 1957, the first in sub-Saharan Africa, and Algeria won its independence from France in 1962. Nkrumah's Neo-Colonialism: The Last Stage of Imperialism argued that political independence had to be followed by economic independence — mines, trade, and debt."},
                {"type": "list", "items": [
                    "1945 Manchester: Africans take up the colonial question themselves.",
                    "Ghana 1957: the first sub-Saharan independence.",
                    "Algeria 1962: after an eight-year war.",
                    "Neo-colonialism: flags change, economics does not.",
                ]},
                {"type": "example", "title": "Continuing argument", "text": "The dependency argument — that independent states could still be bound by trade and debt — remains a live debate in international economics."},
            ],
            "check": {
                "prompt": "Check what you know about decolonization.",
                "questions": [
                    {"q": "The 1945 Manchester Pan-African Congress helped launch…", "options": ["Nkrumah and Kenyatta", "Mussolini", "Napoleon"], "answer": "Nkrumah and Kenyatta", "explain": "Both attended and went on to lead Ghana and Kenya."},
                    {"q": "Nkrumah's concept of neo-colonialism describes…", "options": ["political independence with continued economic control", "new colonies in space", "friendly trade"], "answer": "political independence with continued economic control", "explain": "Power changed hands formally, but economics stayed in foreign hands."},
                ],
            },
        },
        {
            "slug": "solidarity-in-practice",
            "title": "Solidarity in Practice",
            "order": 6,
            "minutes": 25,
            "summary": "Boycotts, divestment, and the network that linked movements.",
            "learn": [
                {"type": "p", "text": "Movements communicated and materially supported each other. Malcolm X's Organization of Afro-American Unity applied Pan-African analysis in the United States. SNCC organisers exchanged strategy with liberation committees. The global anti-apartheid movement used boycotts and divestment campaigns that isolated South Africa economically until apartheid ended in the early 1990s. Solidarity was a strategy with mechanisms, not a sentiment."},
                {"type": "list", "items": [
                    "Boycott: withdrawal of consumer or investment support.",
                    "Divestment: institutional selling of shares to pressure policy.",
                    "Exchange: strategy, people, and print between movements.",
                    "Documentation: what happened, so pressure can be applied where it bites.",
                ]},
                {"type": "activity", "title": "Trace a mechanism", "text": "Pick one boycott or divestment campaign. Identify who it targeted, what it cost them, and how it ended."},
            ],
            "check": {
                "prompt": "Check what you know about solidarity.",
                "questions": [
                    {"q": "The divestment strategy against apartheid worked by…", "options": ["institutions selling South African holdings to increase pressure", "sending troops", "only writing letters"], "answer": "institutions selling South African holdings to increase pressure", "explain": "Economic isolation raised the cost of maintaining apartheid."},
                    {"q": "The OAAU applied…", "options": ["Pan-African analysis to the African American struggle", "isolationism", "feudal law"], "answer": "Pan-African analysis to the African American struggle", "explain": "It connected domestic struggle to a global movement."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Trace Pan-African organisation from congress to independence.",
        "Explain the difference between colonial and neo-colonial control.",
        "Describe the mechanisms by which solidarity movements applied pressure.",
    ],
}

ELA_GRADE_12 = {
    "slug": "public-intellectualism",
    "title": "Public Intellectualism",
    "summary": "C.L.R. James, Audre Lorde, and the essay as a public act.",
    "order": 3,
    "lessons": [
        {
            "slug": "james-and-lorde",
            "title": "James and Lorde",
            "order": 5,
            "minutes": 25,
            "summary": "Criticism as politics, and theory written as poetry.",
            "learn": [
                {"type": "p", "text": "C.L.R. James wrote The Black Jacobins, a history of the Haitian Revolution that placed enslaved people at the centre as actors, and Beyond a Boundary, which argued that cricket encodes colonial and post-colonial history. Audre Lorde wrote theory in the register of poetry: 'the master's tools will never dismantle the master's house' compresses an argument into an architectural image. Both critics work across the line between art and argument."},
                {"type": "list", "items": [
                    "James: cultural criticism and political history as one method.",
                    "Lorde: aphorism as thesis; difference as a resource.",
                    "Both: personal experience as evidence within a political analysis.",
                ]},
                {"type": "example", "title": "Apply the method", "text": "Take a sport, music genre, or social platform. Apply James's method: what does it reveal about power? Take one Lorde aphorism and write the argument it compresses in two sentences."},
            ],
            "check": {
                "prompt": "Check what you know about these critics.",
                "questions": [
                    {"q": "The Black Jacobins is a history of…", "options": ["the Haitian Revolution led by enslaved people", "the French monarchy", "a cricket tour"], "answer": "the Haitian Revolution led by enslaved people", "explain": "James centred the enslaved as agents of the revolution they made."},
                    {"q": "'The master's tools will never dismantle the master's house' argues that…", "options": ["liberation requires new means", "the house cannot be built", "tools are irrelevant"], "answer": "liberation requires new means", "explain": "She rejects achieving liberation through the oppressor's methods."},
                ],
            },
        },
        {
            "slug": "write-the-criticism",
            "title": "Write the Criticism",
            "order": 6,
            "minutes": 25,
            "summary": "A critical essay on a cultural object.",
            "learn": [
                {"type": "p", "text": "Choose a cultural object — a song, film, game, building, or tradition — and write a piece of criticism that treats it as evidence about the world it came from. Name what you are reading, state your claim, cite specifics, and acknowledge the strongest objection."},
                {"type": "list", "items": [
                    "Choose an object you know well.",
                    "Claim: what does it reveal about the society that made it?",
                    "Evidence: specific detail, not impression.",
                    "Counterargument: the strongest objection to your reading.",
                ]},
                {"type": "activity", "title": "Write it", "text": "Write 800–1000 words of criticism and revise once for evidence and counterargument."},
            ],
            "check": {
                "prompt": "Check what you know about criticism.",
                "questions": [
                    {"q": "Cultural criticism treats the object as…", "options": ["evidence about the world that produced it", "only entertainment", "irrelevant"], "answer": "evidence about the world that produced it", "explain": "The object is read for what it reveals about its conditions."},
                    {"q": "The evidence in criticism should be…", "options": ["specific and citable", "general impressions", "personal mood"], "answer": "specific and citable", "explain": "Specifics are what make a reading checkable."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Describe C.L.R. James's and Audre Lorde's methods.",
        "Apply cultural criticism to a chosen object.",
        "Write and revise a critical essay with evidence and counterargument.",
    ],
}

MATH_GRADE_12 = {
    "slug": "economic-modeling-wealth-gap",
    "title": "Economic Modelling: The Wealth Gap",
    "summary": "Linear and exponential models applied to income, assets, and inheritance.",
    "order": 3,
    "lessons": [
        {
            "slug": "compound-vs-linear",
            "title": "Compound vs Linear",
            "order": 5,
            "minutes": 25,
            "summary": "Why the wealth gap grows faster than the income gap.",
            "learn": [
                {"type": "p", "text": "Wages accumulate approximately linearly; assets accumulate exponentially because interest, dividends, and property appreciation compound. Over 40 years, a 5% annual return more than multiplies assets by seven. This is why disparities in wealth persist even when income gaps narrow: the base itself keeps growing."},
                {"type": "list", "items": [
                    "Linear: W(t) = at + b — constant annual increase.",
                    "Exponential: A(t) = P(1 + r)^t — growth on the whole balance.",
                    "Crossover: the exponential eventually exceeds any linear function.",
                    "Inheritance: the base passes to the next generation.",
                ]},
                {"type": "example", "title": "Worked", "text": "$1,000 saved per year for 40 years at 0% gives $40,000. The same at 5% gives about $120,800. The difference is compounding, not saving more."},
            ],
            "check": {
                "prompt": "Check what you know about growth models.",
                "questions": [
                    {"q": "Over a long horizon, exponential growth eventually…", "options": ["exceeds any linear growth", "falls behind linear growth", "equals it"], "answer": "exceeds any linear growth", "explain": "Compounding multiplies the whole balance each period."},
                    {"q": "The wealth gap can grow faster than the income gap because…", "options": ["assets compound while wages often do not", "assets are taxed more", "wages are inherited"], "answer": "assets compound while wages often do not", "explain": "Returns accumulate on the existing stock of wealth."},
                ],
            },
        },
        {
            "slug": "model-mobility",
            "title": "Model Mobility",
            "order": 6,
            "minutes": 25,
            "summary": "Interpreting mobility statistics without over-claiming.",
            "learn": [
                {"type": "p", "text": "Economic mobility is measured as the probability of moving between income quintiles. 'Ran' and 'mobility' are different: a high level of mobility means children's outcomes are less tied to their parents'; a low one means inherited advantage persists. In modelling, the danger is the reverse-causation trap — correlation between parents' and children's income is not evidence of any single cause."},
                {"type": "list", "items": [
                    "Mobility: how strongly children's income tracks parents' income.",
                    "Absolute vs relative mobility: rising incomes vs rank change.",
                    "Correlation is not causation: identify confounders before claiming a mechanism.",
                ]},
                {"type": "activity", "title": "Interpret", "text": "Find mobility statistics for two countries. Write one paragraph interpreting them and one sentence naming a confounder."},
            ],
            "check": {
                "prompt": "Check what you know about mobility.",
                "questions": [
                    {"q": "High economic mobility means…", "options": ["children's income is less tied to their parents'", "everyone is rich", "incomes are equal"], "answer": "children's income is less tied to their parents'", "explain": "Mobility measures the strength of the parent-child income link."},
                    {"q": "A correlation between parental and child income…", "options": ["does not by itself identify a cause", "proves genetics is the only factor", "is meaningless"], "answer": "does not by itself identify a cause", "explain": "Multiple mechanisms produce the same correlation."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Model income and wealth with linear and exponential functions.",
        "Explain why wealth can diverge from income.",
        "Interpret mobility statistics with stated confounders.",
    ],
}

SCIENCE_GRADE_12 = {
    "slug": "black-scientists-and-research-ethics",
    "title": "Black Scientists and Research Ethics",
    "summary": "Drew, Johnson, Jemison — and the Tuskegee Study as a permanent ethics lesson.",
    "order": 3,
    "lessons": [
        {
            "slug": "medicine-and-physics",
            "title": "Medicine, Physics, and Space",
            "order": 5,
            "minutes": 25,
            "summary": "Specific work, and the institutions it built.",
            "learn": [
                {"type": "p", "text": "Charles Drew developed blood-plasma storage methods that made large-scale blood banking possible. Patricia Bath invented a device for cataract removal and co-founded the American Institute for the Prevention of Blindness. Mae Jemison became the first African American woman in space in 1992. Katherine Johnson computed the trajectories for Friendship 7 and Apollo. Ronald McNair, a laser physicist, died on Challenger. Each contribution is tied to a specific technique or institution."},
                {"type": "list", "items": [
                    "Drew: plasma preservation and the scale of blood banking.",
                    "Bath: the Laserphaco Probe for cataract removal.",
                    "Jemison: physician-astronaut and science-literacy advocate.",
                    "Johnson: trajectory computation before digital flight.",
                ]},
                {"type": "example", "title": "Institution building", "text": "Bath co-founded a non-profit institute; Jemison runs a science-technology education company. Science advances when someone builds the structure that keeps it going."},
            ],
            "check": {
                "prompt": "Check what you know about these scientists.",
                "questions": [
                    {"q": "Charles Drew's work enabled…", "options": ["large-scale blood banking", "the satellite", "the transistor"], "answer": "large-scale blood banking", "explain": "His plasma storage methods made blood banks possible."},
                    {"q": "Patricia Bath co-founded…", "options": ["an institute for the prevention of blindness", "a space agency", "a software company"], "answer": "an institute for the prevention of blindness", "explain": "She built the institution to continue the work."},
                ],
            },
        },
        {
            "slug": "tuskegee-and-ethics",
            "title": "Tuskegee and Research Ethics",
            "order": 6,
            "minutes": 25,
            "summary": "A study that was stopped by journalists, not by review boards.",
            "learn": [
                {"type": "p", "text": "The US Public Health Service's Tuskegee Study (1932–1972) denied treatment to African American men with syphilis so researchers could observe the disease's untreated course. Participants were not informed and were actively prevented from receiving penicillin after it became standard treatment. The study was exposed by a journalist (Jean Heller, Associated Press, 1972), stopped by public outcry, and led directly to the 1974 National Research Act, which created institutional review boards and the Belmont Report."},
                {"type": "list", "items": [
                    "Informed consent: participants must know and agree.",
                    "Beneficence: do no harm, and maximise benefit.",
                    "Justice: the burdens and benefits of research must be shared fairly.",
                    "Oversight: an independent board reviews before and during.",
                ]},
                {"type": "tip", "text": "Every clinical trial today is governed by the rules that existed because of this study. The ethics are not abstract — they are written in response to a specific crime."},
            ],
            "check": {
                "prompt": "Check what you know about research ethics.",
                "questions": [
                    {"q": "The Tuskegee Study ended because…", "options": ["a journalist exposed it and public pressure forced a stop", "the researchers finished on schedule", "participants withdrew quietly"], "answer": "a journalist exposed it and public pressure forced a stop", "explain": "Jean Heller's 1972 report led to its termination."},
                    {"q": "The Belmont Report's three principles include…", "options": ["respect for persons, beneficence, and justice", "speed, cost, and secrecy", "profit, peer review, and patents"], "answer": "respect for persons, beneficence, and justice", "explain": "These three govern human-subjects research today."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Describe specific Black contributions to medicine, physics, and spaceflight.",
        "Explain the Tuskegee Study and its consequences for research ethics.",
        "Apply informed consent and justice principles to a research design.",
    ],
}

SOCIAL_STUDIES_GRADE_12 = {
    "slug": "governance-and-constitutional-law",
    "title": "Governance and Constitutional Law",
    "summary": "Gadaa, Haudenosaunee, and Ashanti systems beside modern constitutions.",
    "order": 3,
    "lessons": [
        {
            "slug": "three-constitutions",
            "title": "Three Constitutions",
            "order": 5,
            "minutes": 25,
            "summary": "Fixed terms, clan mothers, and a council that could depose a king.",
            "learn": [
                {"type": "p", "text": "The Gadaa system of the Oromo rotated an elected leader every eight years, distributed executive, judicial, and ritual functions across councils, and gave a women's assembly a veto. The Haudenosaunee Great Law of Peace federated nations, with clan mothers selecting and removing chiefs and decisions made by consensus. The Ashanti kingdom had a codified law set, with a council that could destool a king. Each is a constitution: powers, limits, and succession."},
                {"type": "list", "items": [
                    "Gadaa: fixed terms, distributed powers, formal veto.",
                    "Haudenosaunee: federation, consensus, clan mothers.",
                    "Ashanti: codified law and a defined removal procedure.",
                ]},
                {"type": "example", "title": "Compare", "text": "The US Constitution limits executive tenure by amendment, allows judicial review, and makes amendment deliberately hard. The older systems achieved limits of their own — by calendar, by consensus, or by removal."},
            ],
            "check": {
                "prompt": "Check what you know about these systems.",
                "questions": [
                    {"q": "The Abba Gadaa served a fixed term of…", "options": ["eight years", "four years", "life"], "answer": "eight years", "explain": "Power rotated to the next age-set every eight years."},
                    {"q": "In Ashanti governance, 'destoolment' was…", "options": ["a defined legal act of the council", "a military coup", "a random event"], "answer": "a defined legal act of the council", "explain": "Removal was written into the constitutional structure."},
                ],
            },
        },
        {
            "slug": "modern-comparison",
            "title": "Modern Comparison",
            "order": 6,
            "minutes": 25,
            "summary": "Enumerated powers, judicial review, and plural legal systems.",
            "learn": [
                {"type": "p", "text": "Modern constitutions answer the same questions: what powers the centre holds, how they are limited, and how disputes are resolved. Judicial review was established in Marbury v. Madison (1803). African constitutions today often recognise customary courts and traditional authorities alongside constitutional courts — a legal fact, not nostalgia. The comparison teaches that separation of powers and term limits are design choices with varied histories."},
                {"type": "list", "items": [
                    "Enumerated powers: what the centre may do.",
                    "Amendment: supermajorities or referendums.",
                    "Judicial review: courts may strike laws down.",
                    "Plural systems: customary and modern law side by side.",
                ]},
                {"type": "activity", "title": "Write the memo", "text": "Name one principle from one of the three systems that a modern constitution should adopt, and defend it in one page with evidence."},
            ],
            "check": {
                "prompt": "Check what you know about modern constitutions.",
                "questions": [
                    {"q": "Judicial review allows…", "options": ["courts to strike down laws", "courts to make laws", "courts to levy taxes"], "answer": "courts to strike down laws", "explain": "Courts can invalidate laws that conflict with the constitution."},
                    {"q": "A plural legal system means…", "options": ["customary and modern law operate together", "no law operates", "one law only"], "answer": "customary and modern law operate together", "explain": "Several constitutions recognise both traditional and modern courts."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Describe three non-Western constitutional systems with limits on power.",
        "Compare them with modern constitutional mechanisms.",
        "Evaluate a principle worth adopting across traditions.",
    ],
}

HANDBOOK_HIGH_SCHOOL = {
    "slug": "transcript-portfolio-next-steps",
    "title": "Transcripts, Portfolios, and Next Steps",
    "summary": "What this handbook becomes after graduation, and how to record the work.",
    "order": 2,
    "lessons": [
        {
            "slug": "transcript-and-portfolio",
            "title": "Transcript and Portfolio",
            "order": 7,
            "minutes": 22,
            "summary": "The record that travels, and the work that proves it.",
            "learn": [
                {"type": "p", "text": "A parent-issued transcript lists courses, credits, grades, and a grading scale, and is accepted by colleges, employers, and scholarship programs when it is consistent and documented. The portfolio is the other half: actual work — essays, projects, performances, artifacts — with dates and a description of what it demonstrates. Bright Futures scholarships in Florida are awarded on documented coursework, which is why the Academy keeps the records."},
                {"type": "list", "items": [
                    "Transcript: course titles, credits, grade scale, and a signature.",
                    "Portfolio: the artifacts, each with a date and a one-line description.",
                    "Keep both: the transcript asserts the record, the portfolio proves it.",
                ]},
                {"type": "example", "title": "Record as you go", "text": "Every assignment in the Academy is already dated. Collect one piece of work per course as you finish it — you are building the portfolio without extra effort."},
            ],
            "check": {
                "prompt": "Check what you know about transcripts and portfolios.",
                "questions": [
                    {"q": "A portfolio should contain…", "options": ["actual work with dates and descriptions", "only a list of grades", "only certificates"], "answer": "actual work with dates and descriptions", "explain": "The work is the evidence; the transcript is the claim."},
                    {"q": "Bright Futures scholarships require…", "options": ["documented coursework", "only a portfolio", "only test scores"], "answer": "documented coursework", "explain": "Florida's scholarships are awarded on documented coursework."},
                ],
            },
        },
        {
            "slug": "from-school-to-work",
            "title": "From School to Work",
            "order": 8,
                "minutes": 22,
            "summary": "Turning coursework into a first job, a first business, or a first degree.",
            "learn": [
                {"type": "p", "text": "The path from schooling to work is documented: coursework → a skill → a piece of work that shows the skill → a route to a paying customer or a program. Black institutions from the Tuskegee Institute onward built exactly this sequence — trades taught, work made, markets found. The Academy's career, entrepreneurship, and trade tracks are the same sequence."},
                {"type": "list", "items": [
                    "Skill: finish the course and pass the mastery check.",
                    "Work: build one artifact you can show (project, product, performance).",
                    "Route: a client, a job posting, a program application, or a micro-business.",
                    "Record: keep the dates and the evidence for the transcript.",
                ]},
                {"type": "activity", "title": "Plan the next step", "text": "Write a one-page plan: the skill, the artifact, the audience, and the date you will complete each."},
            ],
            "check": {
                "prompt": "Check what you know about the path to work.",
                "questions": [
                    {"q": "The document that proves a skill is…", "options": ["a piece of work you can show", "a verbal claim", "a school certificate alone"], "answer": "a piece of work you can show", "explain": "A demonstrated artifact is the strongest evidence."},
                    {"q": "A plan for the next step should name…", "options": ["skill, artifact, audience, and dates", "only a goal", "only a salary"], "answer": "skill, artifact, audience, and dates", "explain": "Specific time-bound steps make a plan real."},
                ],
            },
        },
    ],
    "learning_objectives": [
        "Explain the difference between a transcript and a portfolio.",
        "Convert coursework into documented, demonstrable skill.",
        "Write a next-step plan with a skill, artifact, audience, and dates.",
    ],
}


# ── Attachment map: course slug -> culturally integrated unit ──────────────
CULTURAL_INTEGRATION_UNITS = {
    # Adult
    "adult-ed-hse-ela": ADULT_ED_HSE_ELA,
    "adult-ed-hse-math": ADULT_ED_HSE_MATH,
    "adult-ed-hse-science": ADULT_ED_HSE_SCIENCE,
    "adult-ed-hse-social-studies": ADULT_ED_HSE_SOCIAL_STUDIES,
    "handbook-adult": HANDBOOK_ADULT,
    "career-workforce": CAREER_WORKFORCE,
    "radical-wealth-literacy": RADICAL_WEALTH_LITERACY,
    "cooperative-economics-mutual-aid": COOPERATIVE_ECONOMICS_MUTUAL_AID,
    "entrepreneurship-foundations": ENTREPRENEURSHIP_FOUNDATIONS,
    "ascension-protocols": ASCENSION_PROTOCOLS,
    "leadership-foundations": LEADERSHIP_FOUNDATIONS,
    "life-skills-foundations": LIFE_SKILLS_FOUNDATIONS,
    "mens-life-skills": MENS_LIFE_SKILLS,
    "womens-life-skills": WOMENS_LIFE_SKILLS,
    # High school
    "algebra-1-grade-9": ALGEBRA_1_GRADE_9,
    "biology-cells-grade-9": BIOLOGY_CELLS_GENES,
    "applied-electrical-year-1": APPLIED_ELECTRICAL_YEAR_1,
    "digital-art-grade-9": DIGITAL_ART_GRADE_9,
    "chemistry-grade-10": CHEMISTRY_GRADE_10,
    "electrical-year-2": ELECTRICAL_YEAR_2,
    "world-literature-grade-10": WORLD_LITERATURE_GRADE_10,
    "ela-grade-11": ELA_GRADE_11,
    "math-grade-11": MATH_GRADE_11,
    "science-grade-11": SCIENCE_GRADE_11,
    "social-studies-grade-11": SOCIAL_STUDIES_GRADE_11,
    "ela-grade-12": ELA_GRADE_12,
    "math-grade-12": MATH_GRADE_12,
    "science-grade-12": SCIENCE_GRADE_12,
    "social-studies-grade-12": SOCIAL_STUDIES_GRADE_12,
    "handbook-high-school": HANDBOOK_HIGH_SCHOOL,
}


def attach_cultural_integration(courses):
    """Append each integration unit to its published course (idempotent).

    Runs after the catalog is assembled so a redeploy never duplicates units:
    if a unit slug is already present on the course, it is left alone.
    """
    attached = []
    for course in courses:
        unit = CULTURAL_INTEGRATION_UNITS.get(course.get("slug"))
        if not unit or course.get("status") != "published":
            continue
        if any(u.get("slug") == unit["slug"] for u in course.get("units", [])):
            continue
        units = course.setdefault("units", [])
        # Continue the course's own numbering rather than assuming it starts
        # where a standalone file would start.
        next_unit_order = max((u.get("order", 0) or 0) for u in units) + 1
        all_lessons = [l for u in units for l in u.get("lessons", [])]
        next_lesson_order = max((l.get("order", 0) or 0) for l in all_lessons) + 1

        merged = {k: v for k, v in unit.items() if k != "order"}
        merged["order"] = next_unit_order
        for lesson in merged.get("lessons", []):
            lesson["order"] = next_lesson_order
            next_lesson_order += 1
        units.append(merged)
        attached.append(course["slug"])
    return attached
