"""Resistance, Rebellion, and the Counter-Narrative (published course).

Social studies course examining organized resistance by enslaved, colonized,
Indigenous, and exploited populations across the Americas, and how historical
narratives are constructed from competing sources.
"""

RESISTANCE_REBELLION_COUNTER_NARRATIVE = {
    "slug": "resistance-rebellion-counter-narrative",
    "title": "Resistance, Rebellion, and the Counter-Narrative",
    "summary": "Organized resistance by enslaved, colonized, Indigenous, and exploited populations, and how historical narratives are constructed.",
    "description": (
        "Students study organized resistance across the Americas and examine how historical "
        "narratives are constructed from competing sources. The course centers agency and "
        "resistance rather than victimization."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations", "scholar"],
    "grades": ["8", "9", "10", "11"],
    "grade_label": "Grades 8–11",
    "status": "published",
    "audience": "Middle and high school students studying world history and social studies.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": [
        "Define resistance in historical context.",
        "Analyze Maroon societies and their governance.",
        "Examine causes and organization of slave revolts.",
        "Evaluate the Haitian Revolution's global significance.",
        "Analyze Indigenous sovereignty movements.",
        "Examine African resistance to colonial rule.",
        "Identify women's roles in resistance movements.",
        "Analyze cross-racial labor coalition building.",
        "Evaluate cultural resistance as survival strategy.",
        "Compare competing historical narratives.",
        "Create a counter-narrative historical exhibition.",
    ],
    "units": [
        {
            "slug": "foundations-of-resistance",
            "title": "Foundations of Resistance",
            "summary": "What counts as resistance and the formation of Maroon societies.",
            "order": 1,
            "lessons": [
                {
                    "slug": "what-counts-as-resistance",
                    "title": "What Counts as Resistance?",
                    "order": 1,
                    "minutes": 20,
                    "summary": "Armed resistance, escape, work resistance, political organizing, cultural preservation, and economic resistance.",
                    "learn": [
                        {"type": "p", "text": "Resistance is not only armed revolt. It includes escape, work slowdowns, breaking tools, preserving language and religion, building parallel economies, and organizing secretly. Historians now use a broad definition because surviving sources often record only the rebellions that failed violently, while the quieter acts of survival and autonomy left fewer official traces but shaped everyday life."},
                        {"type": "list", "items": [
                            "Armed resistance: revolts, sabotage, and military defense.",
                            "Work resistance: slowdowns, feigned ignorance, tool-breaking, and flight.",
                            "Cultural preservation: language, religion, naming, and foodways carried across forced displacement.",
                            "Economic resistance: independent farming, trade networks, and mutual aid.",
                        ]},
                        {"type": "activity", "title": "Classification exercise", "text": "Classify eight historical acts into armed, work, cultural, and economic resistance. Identify one that could fit two categories and explain why."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of forms of resistance.",
                        "questions": [
                            {"q": "A broad definition of resistance is important because…", "options": ["it captures survival strategies that official histories often ignore", "armed revolts were the only effective form", "it makes all acts equally violent"], "answer": "it captures survival strategies that official histories often ignore", "explain": "Quiet acts of autonomy shaped everyday life even when they left fewer written records."},
                            {"q": "Work resistance includes…", "options": ["slowdowns, tool-breaking, and feigned ignorance", "only violent uprisings", "only political speeches"], "answer": "slowdowns, tool-breaking, and feigned ignorance", "explain": "Non-compliance with forced labor was a daily, widespread form of resistance."},
                        ],
                    },
                },
                {
                    "slug": "maroon-societies",
                    "title": "Maroon Societies",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Escaped communities, geography, governance, defense, and economic independence.",
                    "learn": [
                        {"type": "p", "text": "Maroons were people who escaped enslavement and formed independent communities in remote areas — mountains, swamps, and dense forests. In Jamaica, the Blue Mountains; in Suriname, rainforest interiors; in Florida, the Everglades. These communities governed themselves, cultivated land, traded with outsiders, and negotiated treaties with colonial powers. Their existence was a continuous threat: every escape encouraged others, and their armed defense proved that enslaved people could organize and fight successfully."},
                        {"type": "list", "items": [
                            "Geography as defense: mountains, swamps, and dense forest made military campaigns costly.",
                            "Governance: councils, communal labor, and shared defense responsibilities.",
                            "Treaties: some Maroon nations signed peace agreements that recognized autonomy — rare colonial concessions.",
                        ]},
                        {"type": "activity", "title": "Case study", "text": "Choose one Maroon community (Jamaican Windward Maroons, Jamaican Leeward Maroons, Suriname Maroons, or Seminole Maroons). Describe its geography, governance, and one treaty or agreement it made with a colonial power."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Maroon societies.",
                        "questions": [
                            {"q": "Maroon communities chose remote locations mainly because…", "options": ["geography made them harder for colonial armies to attack", "they preferred isolation for cultural reasons", "no farmland existed elsewhere"], "answer": "geography made them harder for colonial armies to attack", "explain": "Swamps, mountains, and dense forest provided natural fortifications."},
                            {"q": "Treaties with Maroon communities were significant because…", "options": ["they recognized autonomous political entities the colonial state had tried to eliminate", "they proved Maroons wanted to return to enslavement", "they had no lasting effect"], "answer": "they recognized autonomous political entities the colonial state had tried to eliminate", "explain": "Treaties forced colonial powers to acknowledge political actors they preferred to deny."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "revolutions",
            "title": "Revolutions",
            "summary": "Slave revolts in the Americas and the Haitian Revolution.",
            "order": 2,
            "lessons": [
                {
                    "slug": "slave-revolts-in-the-americas",
                    "title": "Slave Revolts in the Americas",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Causes, organization, communication, and government response.",
                    "learn": [
                        {"type": "p", "text": "Enslaved people revolted on every ship and in every colony. Some revolts were spontaneous eruptions after a specific cruelty; others were carefully planned over years using covert communication networks — songs, prayers, and work songs carried coded messages. The 1739 Stono Rebellion in South Carolina, the 1791 Haitian Revolution, and Nat Turner's 1831 rebellion in Virginia are among the best documented, but hundreds of smaller uprisings occurred."},
                        {"type": "list", "items": [
                            "Communication networks: songs, creole languages, and religious gatherings carried coded information.",
                            "Organization: trusted leaders recruited across plantations; coordination required secrecy over months.",
                            "Government response: harsher codes, patrols, and executions — but also concessions when revolt was ongoing.",
                        ]},
                        {"type": "activity", "title": "Communication network mapping", "text": "Map how news of a planned revolt might spread across three plantations. Identify the risks at each stage and one counter-method enslaved people might use."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of slave revolts.",
                        "questions": [
                            {"q": "Covert communication was essential to revolt planning because…", "options": ["enslavers monitored gatherings and punished open talk", "revolts never needed coordination", "enslaved people were forbidden to speak"], "answer": "enslavers monitored gatherings and punished open talk", "explain": "Secrecy was a survival requirement, not a preference."},
                            {"q": "Government responses to revolts typically included…", "options": ["harsher laws and violence, and sometimes concessions", "only immediate abolition", "no consequences for white populations"], "answer": "harsher laws and violence, and sometimes concessions", "explain": "Revolts made enslavers nervous; they responded with both repression and limited reform."},
                        ],
                    },
                },
                {
                    "slug": "the-haitian-revolution",
                    "title": "The Haitian Revolution",
                    "order": 4,
                    "minutes": 22,
                    "summary": "Saint-Domingue, enslavement, Toussaint Louverture, revolutionary leadership, and Haitian independence.",
                    "learn": [
                        {"type": "p", "text": "The Haitian Revolution (1791–1804) was the only successful slave revolt that created an independent nation. Saint-Domingue, France's richest colony, produced sugar, coffee, and indigo through brutal forced labor. In 1791, enslaved people rose under leaders including Boukman and later Toussaint Louverture, a former enslaved person who became a brilliant military and political strategist. After defeating French, Spanish, and British armies, Haiti declared independence in 1804 — a seismic event that terrified slaveholding powers and inspired abolition movements worldwide."},
                        {"type": "list", "items": [
                            "Saint-Domingue: the world's most profitable colony, with a rigid racial caste system.",
                            "Toussaint Louverture: military genius, diplomat, and governor who preserved Black autonomy under shifting alliances.",
                            "Global impact: Haiti's success made slavery indefensible in principle and terrified slaveholding states into harsher repression.",
                        ]},
                        {"type": "activity", "title": "Leadership analysis", "text": "Compare Toussaint Louverture's leadership to one other revolutionary leader from this course. In what ways did his military and political choices differ? What was the cost of those differences?"},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the Haitian Revolution.",
                        "questions": [
                            {"q": "The Haitian Revolution is historically unique because…", "options": ["it was the only successful large-scale slave revolt that founded an independent nation", "it ended all slavery in the Americas immediately", "it was led entirely by European powers"], "answer": "it was the only successful large-scale slave revolt that founded an independent nation", "explain": "Haiti became the first Black republic, defeating three European armies in the process."},
                            {"q": "Haiti's revolution had a global effect because…", "options": ["it made slavery politically and morally indefensible in principle", "it encouraged other nations to expand slavery", "it had no impact beyond the Caribbean"], "answer": "it made slavery politically and morally indefensible in principle", "explain": "Enslaved people's capacity for self-governance became an argument abolitionists could not ignore."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "sovereignty-and-colonial-resistance",
            "title": "Sovereignty and Colonial Resistance",
            "summary": "Indigenous sovereignty movements and African resistance to colonial rule.",
            "order": 3,
            "lessons": [
                {
                    "slug": "indigenous-sovereignty",
                    "title": "Indigenous Sovereignty",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Indigenous political systems, land sovereignty, treaty conflicts, and resistance to displacement.",
                    "learn": [
                        {"type": "p", "text": "Indigenous nations across the Americas had complex political systems — confederacies, councils, clan-based governance, and written treaties — long before European contact. Sovereignty means the right to govern one's own land, laws, and people. Treaties were supposed to recognize this, but colonial powers repeatedly violated agreements, seized land, and imposed assimilation policies. Resistance took legal, political, and armed forms, and continues today through land-back movements and legal advocacy."},
                        {"type": "list", "items": [
                            "Confederacies: the Haudenosaunee (Iroquois) Confederacy influenced U.S. constitutional ideas.",
                            "Treaty conflicts: written agreements broken by governments seeking land and resources.",
                            "Modern resistance: land-back movements, language revitalization, and treaty rights litigation.",
                        ]},
                        {"type": "activity", "title": "Treaty analysis", "text": "Read a short excerpt from a historical treaty between an Indigenous nation and a colonial government. Identify what was promised, what was taken, and how resistance continued after the treaty was signed."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Indigenous sovereignty.",
                        "questions": [
                            {"q": "Sovereignty in the Indigenous context means…", "options": ["the right to govern one's own land, laws, and people", "assimilation into the colonizer's legal system", "abandoning traditional governance"], "answer": "the right to govern one's own land, laws, and people", "explain": "Sovereignty is self-governance, not dependence on another power's permission."},
                            {"q": "Treaties between Indigenous nations and colonial powers often failed because…", "options": ["colonial governments repeatedly violated them to seize land", "Indigenous nations refused to sign them", "treaties were only about trade, not land"], "answer": "colonial governments repeatedly violated them to seize land", "explain": "Written agreements were enforced only when convenient for the stronger party."},
                        ],
                    },
                },
                {
                    "slug": "african-resistance-to-colonial-rule",
                    "title": "African Resistance to Colonial Rule",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Military resistance, political resistance, economic resistance, and cultural resistance.",
                    "learn": [
                        {"type": "p", "text": "African resistance to colonialism took many forms. Military leaders such as Samori Ture in West Africa and Menelik II in Ethiopia defeated or outlasted European armies. Political organizers formed nationalist parties demanding representation. Economic resistance included withholding labor and crops. Cultural resistance preserved language, religion, and art under policies designed to erase them. Together, these forms made colonial rule costly, unstable, and ultimately temporary."},
                        {"type": "list", "items": [
                            "Military resistance: Samori Ture's army held off the French for nearly two decades; Ethiopia defeated Italy at Adwa in 1896.",
                            "Political resistance: early nationalist parties, press organs, and professional associations.",
                            "Cultural resistance: mission schools became sites of anti-colonial intellectual formation.",
                        ]},
                        {"type": "activity", "title": "Resistance mapping", "text": "On a map of Africa, mark three forms of resistance in three different regions. Show how geography, colonial power, and local resources shaped the tactics used."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of African resistance.",
                        "questions": [
                            {"q": "Ethiopia's victory at the Battle of Adwa was significant because…", "options": ["it preserved Ethiopian independence and inspired anti-colonial movements across Africa", "it ended all colonialism in Africa immediately", "it had no effect outside Ethiopia"], "answer": "it preserved Ethiopian independence and inspired anti-colonial movements across Africa", "explain": "Adwa proved European armies could be defeated and became a symbol of resistance."},
                            {"q": "Economic resistance to colonialism included…", "options": ["withholding labor and crops to pressure colonial authorities", "only petitions to colonial governors", "voluntarily paying higher taxes"], "answer": "withholding labor and crops to pressure colonial authorities", "explain": "Colonial economies depended on African labor and exports; withholding them was powerful leverage."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "people-and-culture",
            "title": "People and Culture",
            "summary": "Women's roles, cross-racial labor movements, and cultural resistance.",
            "order": 4,
            "lessons": [
                {
                    "slug": "women-and-resistance",
                    "title": "Women and Resistance",
                    "order": 7,
                    "minutes": 18,
                    "summary": "Women's political organization, community leadership, underground networks, and labor resistance.",
                    "learn": [
                        {"type": "p", "text": "Women were organizers, fighters, and strategists in resistance movements across the Americas and Africa. They ran maroon settlements, carried intelligence across military lines, led food boycotts, organized labor unions, and preserved community networks when men were imprisoned or killed. Figures like Nanny of the Jamaican Maroons, Harriet Tubman, and the Igbo women who led the 1929 Aba Women's Tax Revolt show that women's resistance was not auxiliary — it was central."},
                        {"type": "list", "items": [
                            "Leadership: Nanny of the Maroons, Harriet Tubman, and thousands of unnamed organizers.",
                            "Intelligence and logistics: women moved more freely in some contexts, carrying messages and supplies.",
                            "Economic resistance: women led boycotts, market protests, and labor organizing.",
                        ]},
                        {"type": "activity", "title": "Biography analysis", "text": "Choose one woman from this lesson or another you know. Describe her resistance strategy, the risks she faced, and what made her approach effective."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of women and resistance.",
                        "questions": [
                            {"q": "Women's resistance was central rather than auxiliary because…", "options": ["women led settlements, carried intelligence, and organized economies of survival", "they only supported male fighters", "they rarely faced risk"], "answer": "women led settlements, carried intelligence, and organized economies of survival", "explain": "Women's roles spanned leadership, logistics, and direct confrontation."},
                            {"q": "The 1929 Aba Women's Tax Revolt demonstrates…", "options": ["organized mass protest against colonial economic policy", "a movement for voting rights only", "a spontaneous riot with no political aim"], "answer": "organized mass protest against colonial economic policy", "explain": "Thousands of Igbo women protested taxes imposed without representation."},
                        ],
                    },
                },
                {
                    "slug": "cross-racial-labor-movements",
                    "title": "Cross-Racial Labor Movements",
                    "order": 8,
                    "minutes": 18,
                    "summary": "Workers' organizations, industrial labor, immigrant workers, Black labor organizing, and coalition building.",
                    "learn": [
                        {"type": "p", "text": "When workers of different races recognized that employers used division to lower wages, they built cross-racial coalitions. The Industrial Workers of the World (IWW) recruited Black, immigrant, and white workers in the early 20th century, rejecting the racial exclusion common in craft unions. The Brotherhood of Sleeping Car Porters, led by A. Philip Randolph, organized Black railroad workers and later marched on Washington in 1941, forcing federal anti-discrimination action. Cross-racial solidarity was hard-won and uneven, but it repeatedly shifted power toward labor."},
                        {"type": "list", "items": [
                            "Inclusion strategy: the IWW welcomed all workers regardless of race, challenging craft-union exclusion.",
                            "Black union leadership: A. Philip Randolph and the Brotherhood of Sleeping Car Porters.",
                            "Coalition results: cross-race organizing won wage increases, safety rules, and anti-discrimination orders.",
                        ]},
                        {"type": "activity", "title": "Coalition-building case study", "text": "Choose one cross-racial labor coalition. Explain what shared interest overcame racial division, what obstacles remained, and what the coalition won."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of cross-racial labor movements.",
                        "questions": [
                            {"q": "Cross-racial labor coalitions form when workers recognize…", "options": ["employers use racial division to suppress wages and conditions for everyone", "that only one race can benefit from unionization", "that government always sides with workers"], "answer": "employers use racial division to suppress wages and conditions for everyone", "explain": "Shared economic interest is the foundation; overcoming racial fear and distrust is the work."},
                            {"q": "A. Philip Randolph is best known for…", "options": ["leading the Brotherhood of Sleeping Car Porters and pressuring federal anti-discrimination action", "organizing only white railroad workers", "opposing all union activity"], "answer": "leading the Brotherhood of Sleeping Car Porters and pressuring federal anti-discrimination action", "explain": "Randolph threatened the 1941 March on Washington, which led FDR to ban discrimination in defense industries."},
                        ],
                    },
                },
                {
                    "slug": "resistance-through-culture",
                    "title": "Resistance Through Culture",
                    "order": 9,
                    "minutes": 18,
                    "summary": "Language, religion, music, literature, education, and cultural survival.",
                    "learn": [
                        {"type": "p", "text": "Culture is resistance when the oppressor forbids language, bans religion, or rewrites history. Enslaved people preserved African languages in creole, kept African religious practices inside Christian worship, composed work songs that encoded escape routes, and built schools in secret. These acts were not passive tradition; they were assertions of identity, memory, and future possibility in the face of forced erasure."},
                        {"type": "list", "items": [
                            "Language: creole and Gullah preserved African grammar, vocabulary, and communication across colonial languages.",
                            "Religion: Vodou, Candomblé, and Ring Shout fused African spiritual systems with imposed Christianity as acts of survival.",
                            "Education: secret schools, Sabbath schools, and self-taught literacy movements defied laws against teaching enslaved people.",
                        ]},
                        {"type": "activity", "title": "Cultural-artifact analysis", "text": "Choose one cultural artifact (a song, recipe, prayer, or language feature). Explain how it carried resistance under conditions of forced assimilation."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of cultural resistance.",
                        "questions": [
                            {"q": "Cultural resistance is powerful because…", "options": ["it preserves identity and memory when physical resistance is too dangerous", "it always replaces violent resistance immediately", "it requires no courage or risk"], "answer": "it preserves identity and memory when physical resistance is too dangerous", "explain": "Culture kept communities intact and passed on resistance values across generations."},
                            {"q": "Secret schools were a form of resistance because…", "options": ["they defied laws forbidding literacy among the oppressed", "they only taught approved colonial curriculum", "they had no political significance"], "answer": "they defied laws forbidding literacy among the oppressed", "explain": "Literacy enabled legal defense, organizing, and the preservation of written history."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "method-and-capstone",
            "title": "Method and Capstone",
            "summary": "How histories get written and the counter-narrative exhibition.",
            "order": 5,
            "lessons": [
                {
                    "slug": "how-histories-get-written",
                    "title": "How Histories Get Written",
                    "order": 10,
                    "minutes": 20,
                    "summary": "Official narrative, participant narrative, later historian, and primary evidence.",
                    "learn": [
                        {"type": "p", "text": "History is not a fixed record. It is a conversation across sources. Official narratives — government reports, court records, and elite memoirs — reflect the interests of the powerful. Participant narratives — oral histories, letters, songs, and testimony from those who lived events — capture experience and motive that official sources omit. Later historians synthesize both, testing each against physical evidence. The result is often competing narratives that tell different truths depending on which sources are centered."},
                        {"type": "list", "items": [
                            "Official narrative: written by those in power; tends to justify decisions and omit dissent.",
                            "Participant narrative: oral testimony, diaries, letters, songs — preserves experience and subaltern perspective.",
                            "Primary evidence: physical objects, architecture, and material culture that confirm or contradict written accounts.",
                        ]},
                        {"type": "activity", "title": "Narrative-comparison exercise", "text": "Take one event from this course. Write a short official-style narrative, then a participant-style narrative. Compare what each includes and omits."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of historical narratives.",
                        "questions": [
                            {"q": "Official histories tend to reflect the interests of…", "options": ["those in power", "the oppressed majority", "neutral observers"], "answer": "those in power", "explain": "Those who control record-keeping often shape the narrative to protect their legitimacy."},
                            {"q": "A counter-narrative history…", "options": ["centers sources from participants and marginalized voices", "rejects all written sources", "is always fictional"], "answer": "centers sources from participants and marginalized voices", "explain": "Counter-narratives recover perspectives that dominant histories have suppressed or ignored."},
                        ],
                    },
                },
                {
                    "slug": "counter-narrative-historical-exhibition",
                    "title": "Counter-Narrative Historical Exhibition",
                    "order": 11,
                    "minutes": 30,
                    "summary": "Students create a counter-narrative historical exhibition with primary and secondary sources.",
                    "learn": [
                        {"type": "p", "text": "In this capstone you will curate a counter-narrative historical exhibition on a resistance topic of your choice. Your exhibition must contain 5–8 primary and secondary sources — documents, images, artifacts, or oral histories — and an explanation of why each source matters. The goal is to show a version of history that challenges dominant narratives by centering agency, resistance, and the voices of those who lived it."},
                        {"type": "list", "items": [
                            "Select a focus: a movement, community, leader, or theme covered in this course.",
                            "Choose sources: combine primary evidence (letters, images, objects) with secondary analysis.",
                            "Explain significance: for each source, state what it shows and why the dominant narrative missed or misrepresented it.",
                        ]},
                        {"type": "activity", "title": "Exhibition design", "text": "Draft an exhibition outline with eight sources. For each, write one sentence on what it proves and one sentence on why official histories have overlooked it."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the exhibition project.",
                        "questions": [
                            {"q": "A counter-narrative exhibition must…", "options": ["center sources that challenge dominant histories and explain their significance", "repeat official narratives without question", "use only modern textbook sources"], "answer": "center sources that challenge dominant histories and explain their significance", "explain": "The point is to shift perspective, not to reinforce the standard story."},
                            {"q": "Primary sources are valuable in a counter-narrative because…", "options": ["they carry direct evidence from participants rather than later interpretation", "they are always unbiased and complete", "they never need cross-checking"], "answer": "they carry direct evidence from participants rather than later interpretation", "explain": "First-hand evidence opens perspectives that filtered histories can hide."},
                        ],
                    },
                },
            ],
        },
    ],
}
