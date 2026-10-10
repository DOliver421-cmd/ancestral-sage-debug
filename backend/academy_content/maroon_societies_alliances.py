"""Grade 4 Social Studies: Maroon Societies (published).

Grade 4 social studies rebuilt around self-emancipation rather than generic
'regions': Palmares in Brazil, the maroons of the Great Dismal Swamp, the
Florida Seminole–Black alliance, and the freedom settlement of Fort Mose —
with governance as the central lesson.
"""

MAROON_SOCIETIES_ALLIANCES = {
    "slug": "maroon-societies-alliances",
    "title": "Maroon Societies, Indigenous Alliances, and Early Freedom Settlements",
    "summary": "People who freed themselves: Palmares, the Great Dismal Swamp, Fort Mose, and the Seminole–Black alliance.",
    "description": (
        "Generic regional history leaves out the century-long freedom struggles that "
        "shaped the Americas. This course centers marronage, the act of self-"
        "emancipation, as a form of political organization. Students study the "
        "quilombo of Palmares in Brazil, the maroon towns of the Great Dismal Swamp, "
        "Fort Mose (the first free Black settlement in what is now the United States), "
        "and the alliance between Black Seminoles and the Seminole nation. The "
        "question throughout: how do people who are outnumbered build durable freedom?"
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations", "scholar"],
    "grades": ["4"],
    "grade_label": "Grade 4",
    "status": "published",
    "audience": "Grade 4 students studying self-emancipation and Indigenous–Black alliances.",
    "est_hours": 20,
    "passing_score": 80,
    "learning_objectives": [
        "Define maroon and marronage, and explain why enslaved people established maroon communities.",
        "Describe the government and economy of Palmares in Brazil.",
        "Explain how the Great Dismal Swamp sheltered maroon settlements.",
        "Identify Fort Mose as the first legally free Black settlement in North America.",
        "Explain the Seminole–Black alliance and its role in the Seminole Wars.",
        "Analyze how these communities organized defense, farming, and law.",
        "Compare maroon communities across Brazil, the Great Dismal Swamp, and Florida.",
    ],
    "units": [
        {
            "slug": "palmares",
            "title": "Palmares: A Country Inside a Country",
            "summary": "Brazil's great runaway settlement, 1605–1694.",
            "order": 1,
            "lessons": [
                {
                    "slug": "what-palmares-was",
                    "title": "What Palmares Was",
                    "order": 1,
                    "minutes": 20,
                    "summary": "A federation of settlements deep in the mountains of colonial Brazil.",
                    "learn": [
                        {"type": "p", "text": "In the mountains of northeastern Brazil, in what is now Alagoas, escaped enslaved Africans and their descendants built Palmares — a federation that lasted about ninety years and grew larger than many European cities of its time. Its capital, Macoco, was a walled main town, and surrounding settlements grew food, forged iron, and traded with each other and with free neighbours."},
                        {"type": "list", "items": [
                            "Founded early in the 1600s by people who ran away from Portuguese sugar plantations.",
                            "Grew into several mocambos (settlements) governed as one confederation under an elected leader.",
                            "At its height it held tens of thousands of people and survived repeated Portuguese and Dutch attacks.",
                        ]},
                        {"type": "example", "title": "How big?", "text": "Estimates of Palmares' population at its height run from 11,000 to over 30,000 — comparable to the European colonial capitals of the Americas."},
                        {"type": "tip", "text": "Zumbi, its most famous leader, is now a national hero in Brazil; November 20, the date of his death, is a national day of Black consciousness."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Palmares.",
                        "questions": [
                            {"q": "Palmares was a community built by…", "options": ["escaped enslaved Africans and their descendants", "European aristocrats", "Portuguese governors"], "answer": "escaped enslaved Africans and their descendants", "explain": "It was a maroon federation — self-emancipated people who built a state of their own."},
                            {"q": "Palmares was made of several…", "options": ["mocambos (settlements) federated together", "single small farms", "military forts"], "answer": "mocambos (settlements) federated together", "explain": "Independent settlements joined together for mutual defence and trade."},
                        ],
                    },
                },
                {
                    "slug": "government-and-economy",
                    "title": "How Palmares Governed and Fed Itself",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Voting, farming, and iron in the mountains.",
                    "learn": [
                        {"type": "p", "text": "Palmares is remembered for political invention. Leaders were chosen by the community, councils of elders decided cases, and land was farmed in common. Blacksmiths, potters, and weavers worked beside farmers — a working economy, not just a refugee camp. Its people also built palisaded towns and storehouses that withstood a decade of colonial assaults."},
                        {"type": "list", "items": [
                            "Leaders elected or acclaimed by community members and held accountable.",
                            "Communal farming: corn, beans, manioc, and bananas grown inside the settlement.",
                            "Ironworking and pottery produced tools locally, so the settlement was not dependent on colonial trade.",
                        ]},
                        {"type": "example", "title": "Compare", "text": "The same era's European colonies were ruled by distant kings. Palmares chose its own leaders in its own territory — an early American practice of self-government."},
                        {"type": "activity", "title": "Design a settlement", "text": "On grid paper, plan a settlement of 200 people: a palisade, corn fields, a smithy, and a council house. Label what each area protects."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Palmares' government.",
                        "questions": [
                            {"q": "Palmares chose its leaders by…", "options": ["selection or acclamation by the community", "inheritance from kings", "appointment by Portugal"], "answer": "selection or acclamation by the community", "explain": "It had its own democratic elements centuries before universal suffrage."},
                            {"q": "Growing food inside Palmares meant the settlement…", "options": ["did not depend on colonial trade", "was always starving", "could not grow anything"], "answer": "did not depend on colonial trade", "explain": "Local farming plus ironworking made it self-sufficient and harder to besiege."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "dismal-swamp-and-mose",
            "title": "The Great Dismal Swamp and Fort Mose",
            "summary": "Maroon towns in the Virginia–Carolina wetlands; the first free Black settlement in North America.",
            "order": 2,
            "lessons": [
                {
                    "slug": "dismal-swamp-maroons",
                    "title": "The Great Dismal Swamp",
                    "order": 3,
                    "minutes": 20,
                    "summary": "A refuge that required real skills to survive.",
                    "learn": [
                        {"type": "p", "text": "The Great Dismal Swamp between Virginia and North Carolina was once a million acres of impassable wetland. To colonists it was 'dismal'; to Africans who knew how to work wet environments, it was a refuge. Maroons built raised platforms, trapped game, farmed small plots, and traded with free Black riverboat workers and poor white neighbours. The settlement persisted from the early 1700s into the Civil War, and archaeological excavations have recovered objects that only a long-stable community leaves behind."},
                        {"type": "list", "items": [
                            "Raised platforms and small fields stayed dry when the swamp flooded.",
                            "Trade with outsiders: cash crops, game, and forest products exchanged for cloth, tools, and gunpowder.",
                            "Archaeology: artifacts and dwellings reveal continuous settlement for well over a century.",
                        ]},
                        {"type": "example", "title": "Skills mattered", "text": "Africans brought rice cultivation methods from West Africa — controlled water on raised beds — that were used not only on plantations but to farm in swamp water too."},
                        {"type": "tip", "text": "Maroon communities also exchanged information and helped people still in bondage move along routes toward freedom."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the Dismal Swamp maroons.",
                        "questions": [
                            {"q": "Maroons in the Great Dismal Swamp survived by…", "options": ["building raised platforms and trading with outsiders", "surrendering to the colonists", "building stone castles"], "answer": "building raised platforms and trading with outsiders", "explain": "Engineering the land for drainage and trading forest products sustained them."},
                            {"q": "Archaeology of the swamp shows…", "options": ["a long, stable community once lived there", "nobody ever lived there", "only hunting camps"], "answer": "a long, stable community once lived there", "explain": "Excavated dwellings and artifacts show continuous settlement for generations."},
                        ],
                    },
                },
                {
                    "slug": "fort-mose",
                    "title": "Fort Mose: The First Free Black Settlement",
                    "order": 4,
                    "minutes": 20,
                    "summary": "A legally sanctioned free Black town, founded 1738 in Spanish Florida.",
                    "learn": [
                        {"type": "p", "text": "In 1693 Spain offered freedom to enslaved Africans who fled British colonies and accepted Catholic baptism and military service. Many walked south. In 1738, about two miles north of St. Augustine, they established Gracia Real de Santa Teresa de Mose — Fort Mose — a fortified, legally free community. Colonial records name hundreds of its residents. Its people fought beside the Spanish in defending St. Augustine."},
                        {"type": "list", "items": [
                            "Spain's policy of sanctuary offered a legal route to freedom decades before the Underground Railroad.",
                            "Fort Mose had a wall, a church, homes, and its own militia.",
                            "Francisco Menéndez, a Fort Mose resident, was its captain and a soldier of Spain.",
                        ]},
                        {"type": "example", "title": "Why it matters", "text": "Fort Mose is the first legally free Black settlement in what would become the United States, and its people chose freedom and defended it as armed citizens."},
                        {"type": "activity", "title": "Timeline", "text": "Draw a timeline: 1693 (Spanish sanctuary), 1738 (Fort Mose), 1740 (British attack), 1752 (rebuilt), 1763 (Florida to Britain). Label each event with two words."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Fort Mose.",
                        "questions": [
                            {"q": "Fort Mose was founded as a settlement of legally free…", "options": ["Africans who fled British colonies to Spanish Florida", "Spanish aristocrats", "British soldiers"], "answer": "Africans who fled British colonies to Spanish Florida", "explain": "It was established under Spanish policy to offer freedom to runaways from British colonies."},
                            {"q": "Fort Mose is historically important because…", "options": ["it is the first legally free Black settlement in what is now the US", "it was a gold mine", "it never existed"], "answer": "it is the first legally free Black settlement in what is now the US", "explain": "It combined freedom, land, and civic responsibility decades before independence."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "seminole-black-alliance",
            "title": "The Seminole–Black Alliance",
            "summary": "Two peoples who fought together for their freedom.",
            "order": 3,
            "lessons": [
                {
                    "slug": "how-the-alliance-worked",
                    "title": "How the Alliance Worked",
                    "order": 5,
                    "minutes": 20,
                    "summary": "Shared land, shared crops, shared war.",
                    "learn": [
                        {"type": "p", "text": "From the early 1700s, Africans escaping Carolina plantations travelled south into Florida and joined the Seminole. Black Seminoles built their own towns, planted their own crops, and paid tribute in produce for protection and shared land. In exchange they fought alongside the Seminole — as allies, not servants — in the Seminole Wars against the United States."},
                        {"type": "list", "items": [
                            "Black Seminole towns grew crops and livestock and managed their own affairs.",
                            "They intermarried with the Seminole and took part in mutual defense.",
                            "They became some of the fiercest fighters against US forces in Florida.",
                        ]},
                        {"type": "example", "title": "Key facts", "text": "The longest, most expensive Indian war in US history ended because the Seminole nation — with Black Seminoles — never surrendered. Many Black Seminoles later moved to Mexico and Texas to stay free."},
                        {"type": "tip", "text": "Black Seminoles are recognized today as part of the Seminole Nation of Oklahoma and the Seminole Tribe of Florida."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the Seminole–Black alliance.",
                        "questions": [
                            {"q": "Black Seminoles' relationship with the Seminole was…", "options": ["an alliance of shared land and defense", "slavery in a new form", "temporary employment"], "answer": "an alliance of shared land and defense", "explain": "They lived in their own towns and fought alongside the Seminole as allies."},
                            {"q": "Many Black Seminoles later moved to Mexico to…", "options": ["escape US attempts to re-enslave them", "find gold", "build canals"], "answer": "escape US attempts to re-enslave them", "explain": "Fleeing south across the border to Mexican territory kept them out of reach of US slavery laws."},
                        ],
                    },
                },
                {
                    "slug": "maroon-civics",
                    "title": "Capstone: How Maroons Governed",
                    "order": 6,
                    "minutes": 22,
                    "summary": "Compare three communities' rules for defense, farming, and law.",
                    "learn": [
                        {"type": "p", "text": "Palmares, the Dismal Swamp maroons, and Fort Mose faced the same question: how do a small number of people stay free? Their answers differed by geography. Palmares federated mountain settlements. The Dismal Swamp used the wetlands as a wall. Fort Mose used law and alliance with a European power."},
                        {"type": "list", "items": [
                            "Defense: palisades, terrain, or a fort — each community's geography shaped its wall.",
                            "Food: communal farms, trade, or raids — each community fed itself from what the land allowed.",
                            "Law: elected councils, captains, or Spanish governors — but in each, decisions were made by rules the community recognized.",
                        ]},
                        {"type": "activity", "title": "Write the comparison", "text": "Write a paragraph comparing Palmares and Fort Mose. Use a topic sentence, one fact from each, and a closing sentence."},
                    ],
                    "check": {
                        "prompt": "Check what you know about maroon governance.",
                        "questions": [
                            {"q": "Maroon communities had to build systems for…", "options": ["defense, farming, and law", "only trade", "education alone"], "answer": "defense, farming, and law", "explain": "Survival required all three functions of a community."},
                            {"q": "The Great Dismal Swamp communities used…", "options": ["wetland terrain as protection", "stone walls as protection", "foreign armies as protection"], "answer": "wetland terrain as protection", "explain": "The swamp itself was their fortress — inaccessible to colonial forces."},
                        ],
                    },
                },
            ],
        },
    ],
}
