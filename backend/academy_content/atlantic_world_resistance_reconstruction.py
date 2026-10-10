"""Grade 5 Social Studies: The Atlantic World, Resistance, and Reconstruction (published).

Grade 5 social studies rebuilt around the Atlantic world: the trade systems
that produced chattel slavery, the resistance that occurred before and
during it, the abolition movement led by Black abolitionists, and the
Reconstruction era taught as a real political project with real outcomes
rather than a footnote.
"""

ATLANTIC_WORLD_RESISTANCE_RECONSTRUCTION = {
    "slug": "atlantic-world-resistance-reconstruction",
    "title": "The Atlantic World, Resistance, and the Real Reconstruction",
    "summary": "Trade, slavery, resistance, abolition, and what Reconstruction actually built.",
    "description": (
        "Grade 5 social studies here traces the making of the Atlantic world: West "
        "African states and the trade networks that existed before European contact; "
        "the Middle Passage and the economics of chattel slavery; the constant "
        "resistance it produced, from the slave ships to the plantations; the "
        "abolition movement led by Black organizers; and Reconstruction, taught as a "
        "democratic experiment with schools, legislatures, and constitutions — and as "
        "a period actively dismantled."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations", "scholar"],
    "grades": ["5"],
    "grade_label": "Grade 5",
    "status": "published",
    "audience": "Grade 5 students studying the Atlantic world, abolition, and Reconstruction.",
    "est_hours": 24,
    "passing_score": 80,
    "learning_objectives": [
        "Describe the African and European sides of the Atlantic world before colonization.",
        "Explain the Middle Passage as a system with economic motives.",
        "Identify forms of resistance by enslaved Africans on ships and plantations.",
        "Name Black abolitionists and describe their strategies.",
        "Explain what Reconstruction governments achieved in education and law.",
        "Describe how Reconstruction was ended and what followed.",
        "Evaluate primary sources about slavery and emancipation.",
    ],
    "units": [
        {
            "slug": "atlantic-world-and-slavery",
            "title": "The Atlantic World and the Middle Passage",
            "summary": "How the trade systems worked and what they cost.",
            "order": 1,
            "lessons": [
                {
                    "slug": "africa-before-the-trade",
                    "title": "Africa Before the Atlantic Trade",
                    "order": 1,
                    "minutes": 22,
                    "summary": "States, scholarship, and gold — before and during the trade.",
                    "learn": [
                        {"type": "p", "text": "The trading states of West Africa — Mali, Songhai, the Kingdom of Benin, Asante, the Hausa city-states — controlled gold, ivory, and manufactured goods, with universities at Timbuktu and brass casting in Benin. Portugal's earliest European visitors did not conquer these states; they traded with them. The Atlantic slave trade did not begin because Africa was weak, and it did not begin because Africa had slavery of the kind Columbus would create."},
                        {"type": "list", "items": [
                            "Gold: West Africa was the source of most gold circulating in the medieval world.",
                            "Knowledge: Timbuktu's libraries, Benin's bronze casting, and sophisticated law codes.",
                            "Slavery existed in many societies, but chattel slavery — treating people as inheritable property with no rights — was the Atlantic system's invention.",
                        ]},
                        {"type": "example", "title": "Scale", "text": "Approximately 12.5 million Africans were carried across the Atlantic between the 1500s and 1800s; more than 10 million survived the crossing to be sold into lifelong, inheritable slavery."},
                        {"type": "activity", "title": "Source read", "text": "Look at a map of the Atlantic trade. Trace the triangular route and list what was carried on each leg."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the Atlantic trade.",
                        "questions": [
                            {"q": "Chattel slavery is defined by…", "options": ["people treated as inheritable property with no rights", "any kind of forced labor", "only work on ships"], "answer": "people treated as inheritable property with no rights", "explain": "Chattel slavery made enslaved people and their children property, forever."},
                            {"q": "Before the Atlantic trade, West Africa was known for…", "options": ["gold, scholarship, and strong states", "having no writing", "empty land"], "answer": "gold, scholarship, and strong states", "explain": "West African states controlled gold and produced centers of learning."},
                        ],
                    },
                },
                {
                    "slug": "middle-passage",
                    "title": "The Middle Passage",
                    "order": 2,
                    "minutes": 22,
                    "summary": "The voyage at the center of the system.",
                    "learn": [
                        {"type": "p", "text": "The Middle Passage was the crossing from West Africa to the Americas, planned by European and American slave traders for maximum profit. Captives were packed into ships' holds in the hundreds, chained, and kept in conditions designed to maximize the number who survived to be sold. Roughly one in six died on the crossing, and the system paid out against those losses."},
                        {"type": "list", "items": [
                            "Insurance: slave ships were insured like cargo, so deaths were calculated as risk, not tragedy.",
                            "Revolt: records document more than 500 uprisings aboard slave ships.",
                            "Culture: languages, music, crops, metallurgy, and agricultural knowledge survived the crossing.",
                        ]},
                        {"type": "example", "title": "Primary source", "text": "Olaudah Equiano's 1789 autobiography describes the holds of a slave ship; Ottobah Cugoano's 1787 tract demanded abolition from a writer who had been kidnapped in what is now Ghana."},
                        {"type": "activity", "title": "Write a response", "text": "Read one paragraph of Equiano's account. Write three sentences: what happened, how people responded, why it matters."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the Middle Passage.",
                        "questions": [
                            {"q": "Slave ships were insured because traders…", "options": ["treated captives as cargo and calculated losses", "cared nothing about the law", "wanted to help them"], "answer": "treated captives as cargo and calculated losses", "explain": "Insurance priced human lives as risk, a fact that shows the system's logic."},
                            {"q": "Records of resistance on slave ships show…", "options": ["captives fought back repeatedly", "no one resisted", "only crews revolted"], "answer": "captives fought back repeatedly", "explain": "More than 500 uprisings aboard slave ships are documented."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "resistance-and-abolition",
            "title": "Resistance and Abolition",
            "summary": "People who refused, and the movement that ended it.",
            "order": 2,
            "lessons": [
                {
                    "slug": "forms-of-resistance",
                    "title": "Forms of Resistance",
                    "order": 3,
                    "minutes": 22,
                    "summary": "From broken tools to open revolt.",
                    "learn": [
                        {"type": "p", "text": "Enslaved Africans resisted every day of the system. Resistance ran from slowdowns and 'accidents' that cost the slaveholder profit, to running away, to poisoning, to armed revolt. Nat Turner's 1831 revolt in Virginia, the German Coast rising of 1811 in Louisiana, and the Haitian Revolution (1791–1804) which created a nation, all forced slaveholders to spend heavily on control."},
                        {"type": "list", "items": [
                            "Everyday resistance: slow work, broken tools, pretending ignorance.",
                            "Escape: networks along what became the Underground Railroad.",
                            "Armed revolt: Nat Turner (1831), the German Coast uprising (1811), and many more.",
                            "Haiti (1791–1804): a revolution that defeated France, Spain, and Britain and founded a republic.",
                        ]},
                        {"type": "tip", "text": "Knowledge was resistance. Teaching people to read was a crime in many slave states — which is why secret schools existed anyway."},
                        {"type": "activity", "title": "Map resistance", "text": "On a map of the Americas, label three slave revolts and the routes of two escape paths. Add one sentence for each."},
                    ],
                    "check": {
                        "prompt": "Check what you know about resistance.",
                        "questions": [
                            {"q": "The Haitian Revolution ended with…", "options": ["the founding of an independent republic", "a return to slavery", "annexation by the US"], "answer": "the founding of an independent republic", "explain": "Haiti became the first state founded by formerly enslaved people."},
                            {"q": "Alleged 'laziness' under slavery was often actually…", "options": ["a form of everyday resistance", "a personal failing", "a natural trait"], "answer": "a form of everyday resistance", "explain": "Slowdowns reduced the slaveholder's profit and were a rational tactic."},
                        ],
                    },
                },
                {
                    "slug": "black-abolitionists",
                    "title": "Abolition Led by Black Organizers",
                    "order": 4,
                    "minutes": 22,
                    "summary": "Tubman, Truth, Douglass — the movement was Black-led.",
                    "learn": [
                        {"type": "p", "text": "Abolition was not white charity. It was organized and driven by Black writers, speakers, and former slaves. Frederick Douglass published the North Star and wrote three autobiographies that sold around the world. Sojourner Truth spoke across the North. William Wells Brown and Frances E. W. Harper wrote novels arguing against slavery. Harriet Tubman conducted about 13 rescue missions and freed roughly 70 enslaved people — and served as a Union spy and armed scout."},
                        {"type": "list", "items": [
                            "Frederick Douglass: editor, orator, and writer, and a founder of the movement's argument.",
                            "Sojourner Truth: 'Ain't I a Woman?' — linking abolition and women's rights.",
                            "Harriet Tubman: Underground Railroad conductor, nurse, and Union scout.",
                            "David Walker (1829): Appeal that demanded, not asked for, freedom.",
                        ]},
                        {"type": "example", "title": "Strategy", "text": "Black abolitionists used newspapers, speeches, and escaped-slave narratives to prove the system's cruelty from first-hand knowledge, which white audiences could not dismiss."},
                        {"type": "activity", "title": "Speech study", "text": "Read one paragraph of 'Ain't I a Woman?' What does Truth prove by speaking as she does? Write two sentences."},
                    ],
                    "check": {
                        "prompt": "Check what you know about abolition.",
                        "questions": [
                            {"q": "William Wells Brown was…", "options": ["a Black novelist and lecturer against slavery", "a slave trader", "a Southern governor"], "answer": "a Black novelist and lecturer against slavery", "explain": "His novel Clotel argued against slavery in fictional form."},
                            {"q": "Harriet Tubman's role in the Civil War was…", "options": ["Union scout, nurse, and spy", "only a cook", "a Confederate general"], "answer": "Union scout, nurse, and spy", "explain": "She served the Union Army behind enemy lines as well as on the Railroad."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "real-reconstruction",
            "title": "The Real Reconstruction",
            "summary": "A democracy born, and the coup that ended it.",
            "order": 3,
            "lessons": [
                {
                    "slug": "what-reconstruction-built",
                    "title": "What Reconstruction Built",
                    "order": 5,
                    "minutes": 22,
                    "summary": "Schools, constitutions, and elected office.",
                    "learn": [
                        {"type": "p", "text": "Between 1865 and 1877, formerly enslaved people voted, ran for office, and built public institutions across the South. They held state offices in every former Confederate state, served in Congress, and pushed constitutional guarantees — the 14th and 15th Amendments — through Congress. The South's first public school systems were built by Reconstruction governments."},
                        {"type": "list", "items": [
                            "About 2,000 Black officeholders held office during Reconstruction, including 16 in Congress.",
                            "Public school systems, hospitals, and asylums were established across the South.",
                            "Constitutions guaranteed citizenship, due process, and Black men's suffrage.",
                        ]},
                        {"type": "example", "title": "Reconstruction schools", "text": "A century later, the grandparents of the civil rights generation learned to read because Reconstruction established free public schooling where there had been none."},
                        {"type": "tip", "text": "Reconstruction is often taught as a failure. Measured by what was built — schools, laws, representation — it achieved more in twelve years than the century before it."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Reconstruction.",
                        "questions": [
                            {"q": "During Reconstruction, how many Black officeholders held office across the South?", "options": ["About 2,000", "Almost none", "More than 100,000"], "answer": "About 2,000", "explain": "Roughly two thousand African Americans held public office, including 16 in Congress."},
                            {"q": "Reconstruction governments built…", "options": ["the South's first public school systems", "only plantations", "no institutions"], "answer": "the South's first public school systems", "explain": "Free public schooling across the South was a Reconstruction achievement."},
                        ],
                    },
                },
                {
                    "slug": "how-it-ended",
                    "title": "How Reconstruction Ended",
                    "order": 6,
                    "minutes": 22,
                    "summary": "Violence, a political bargain, and the laws that replaced it.",
                    "learn": [
                        {"type": "p", "text": "Reconstruction was ended by force and by compromise. Paramilitary groups such as the Ku Klux Klan attacked voters and officeholders. The Compromise of 1877 resolved a disputed presidential election by withdrawing federal troops from the South in exchange for the presidency. With federal protection gone, Southern states passed Jim Crow laws, poll taxes, and literacy tests that removed Black voting for decades."},
                        {"type": "list", "items": [
                            "Paramilitary violence and assassinations of Black officeholders.",
                            "The Compromise of 1877 removed the federal army's enforcement.",
                            "Jim Crow laws, convict leasing, and sharecropping re-created servitude.",
                            "Plessy v. Ferguson (1896) legalized 'separate but equal'.",
                        ]},
                        {"type": "example", "title": "A Coup", "text": "In Wilmington, North Carolina, in 1898, an armed white mob overthrew an elected government — the only successful coup in US history — after Black men had been elected to office."},
                        {"type": "activity", "title": "Write the account", "text": "Write a paragraph: what did Reconstruction build, and how was it ended? Use two facts."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the end of Reconstruction.",
                        "questions": [
                            {"q": "The Compromise of 1877 ended Reconstruction by…", "options": ["withdrawing federal troops from the South", "declaring war on Spain", "abolishing public schools"], "answer": "withdrawing federal troops from the South", "explain": "Removing federal enforcement allowed the Jim Crow order to take over state governments."},
                            {"q": "Plessy v. Ferguson (1896) legalized…", "options": ["'separate but equal' segregation", "universal suffrage", "free public transit"], "answer": "'separate but equal' segregation", "explain": "It upheld racial segregation by law for over half a century."},
                        ],
                    },
                },
            ],
        },
    ],
}
