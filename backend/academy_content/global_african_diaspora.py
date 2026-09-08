"""Global African Diaspora: Resistance, Culture, and Modern Identity (published).

Social Studies course for Grades 8–11 tracing the interconnected histories,
cultural retentions, and political movements across the African Diaspora after
the Transatlantic slave trade: maroon societies, the Haitian Revolution,
Pan-Africanism, Negritude, and Caribbean/Afro-Latin cultural synthesis.
"""

GLOBAL_AFRICAN_DIASPORA = {
    "slug": "global-african-diaspora",
    "title": "Global African Diaspora: Resistance, Culture, and Modern Identity",
    "summary": "Interconnected histories, cultural retentions, and political movements across the African Diaspora — the Haitian Revolution, Pan-Africanism, Negritude, and Caribbean/Afro-Latin cultural synthesis.",
    "description": (
        "Traces the African Diaspora after the Transatlantic slave trade: how communities "
        "were forcibly dispersed and how they rebuilt. Students study maroon societies, the "
        "Haitian Revolution as a turning point in world history, Pan-Africanism and the "
        "Negritude movement as political and cultural counter-projects, and the cultural "
        "synthesis that produced Caribbean and Afro-Latin traditions. The course closes with "
        "modern diasporic identity — migration, music, language, and global Black culture."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations", "scholar"],
    "grades": ["8", "9", "10", "11"],
    "grade_label": "Grades 8–11",
    "status": "published",
    "audience": "Middle and high school students studying world history through the African Diaspora.",
    "est_hours": 20,
    "passing_score": 80,
    "learning_objectives": [
        "Describe the scale and mechanics of the Transatlantic slave trade and where captives were taken.",
        "Explain how maroon societies preserved autonomy and African cultural practices.",
        "Narrate the causes, course, and global consequences of the Haitian Revolution.",
        "Compare emancipation experiences across the Americas and identify continuities of unfree labor.",
        "Trace Pan-Africanism from early congresses to Ghana's independence.",
        "Analyze Negritude and the Harlem Renaissance as linked cultural movements.",
        "Give examples of African cultural retention and synthesis in Caribbean and Afro-Latin traditions.",
        "Evaluate how diaspora communities build modern identity across national borders.",
    ],
    "units": [
        {
            "slug": "roots-and-rupture",
            "title": "Roots and Rupture",
            "summary": "How the diaspora formed — and how communities fought to remain whole.",
            "order": 1,
            "lessons": [
                {
                    "slug": "the-middle-passage-and-dispersal",
                    "title": "The Transatlantic Slave Trade and the Making of the Diaspora",
                    "order": 1,
                    "minutes": 25,
                    "summary": "Scale, routes, and destinations of the largest forced migration in history.",
                    "learn": [
                        {"type": "p", "text": "Between the 1500s and the 1860s, roughly 12.5 million African captives were forced onto ships bound for the Americas in the Transatlantic slave trade. About 10.7 million survived the Middle Passage. Most — nearly 5 million — were taken to Brazil; the British and French Caribbean and Spanish America took millions more, while only about 400,000 arrived in what became the United States. That fact surprises many students: the cultural heart of the diaspora by numbers is the Caribbean and Latin America, not North America."},
                        {"type": "list", "items": [
                            "Trade triangle: European goods to West Africa, captives to the Americas, plantation products (sugar, tobacco, cotton) back to Europe.",
                            "Effects on Africa: population loss, warfare driven by slave-raiding, and political destabilization of coastal kingdoms.",
                            "Cultural survival: captives carried languages, religions, music, foodways, and kinship systems that reshaped the Americas.",
                        ]},
                        {"type": "example", "title": "Read the data", "text": "Historians using ship logs estimate that the voyage averaged 1–2 months and mortality ranged widely — from under 10% to over 20% on some routes. Total captives ≈ 12.5 million; survivors ≈ 10.7 million. Ask: what does a mortality rate that high tell you about conditions, and why do records come mostly from traders rather than the enslaved?"},
                        {"type": "activity", "title": "Map the dispersal", "text": "Sketch the Atlantic. Label West Africa, Brazil, the Caribbean, and North America, and write approximate captive numbers next to each destination. Circle the largest single destination — check yourself against the lesson text."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the slave trade's scale and geography.",
                        "questions": [
                            {"q": "Roughly what share of enslaved Africans arrived in Brazil?", "options": ["Nearly half — the largest single destination", "About one in twenty", "Almost none"], "answer": "Nearly half — the largest single destination", "explain": "Brazil received close to 5 million captives — around 45% of the total — far more than North America."},
                            {"q": "The 'Middle Passage' refers to…", "options": ["the ocean voyage from Africa to the Americas", "a trade route across the Sahara", "the journey from the plantation to market"], "answer": "the ocean voyage from Africa to the Americas", "explain": "It was the middle leg of the triangle trade between Europe, Africa, and the Americas."},
                        ],
                    },
                },
                {
                    "slug": "maroon-societies",
                    "title": "Maroon Societies: Freedom Towns of the Americas",
                    "order": 2,
                    "minutes": 25,
                    "summary": "Jamaica's Maroons, Brazil's Palmares, Suriname's Saramaka — independent communities built by the escaped.",
                    "learn": [
                        {"type": "p", "text": "Maroons were enslaved people who escaped and formed independent communities, often in mountains and rainforests where colonial armies could not easily fight. Jamaica's Leeward and Windward Maroons, led in the 1730s by figures like Cudjoe and Queen Nanny, fought the British to a standoff and won treaties in 1739–1740 recognizing their autonomy. In Brazil, the quilombo of Palmares sustained a state of thousands of residents for most of a century (c. 1605–1694) under leaders including Ganga Zumba and Zumbi."},
                        {"type": "list", "items": [
                            "Jamaica: treaties of 1739–40 granted land and self-rule in exchange for peace terms — a rare formal recognition of maroon sovereignty.",
                            "Palmares (Brazil): organized villages (mocambos), agriculture, and elected leadership; destroyed only by a major military campaign in 1694.",
                            "Suriname: Saramaka, Ndyuka, and other maroon nations signed 1760s–1800s treaties and remain distinct peoples today.",
                        ]},
                        {"type": "tip", "text": "Maroon communities are evidence for two things at once: military resistance, and cultural preservation — languages (like Saramaccan), religions, and farming systems survived inside them."},
                        {"type": "activity", "title": "Compare and contrast", "text": "Make a two-column chart: how Palmares and the Jamaican Maroons each won and defended autonomy. Where did treaty-making work, and where did it fail?"},
                    ],
                    "check": {
                        "prompt": "Check your understanding of maroon societies.",
                        "questions": [
                            {"q": "A maroon society was…", "options": ["an independent community founded by people who escaped slavery", "a colonial trading post", "a European fort"], "answer": "an independent community founded by people who escaped slavery", "explain": "Maroons built self-governing communities, sometimes winning formal treaties recognizing them."},
                            {"q": "Palmares, the largest quilombo, was located in…", "options": ["Brazil", "Jamaica", "Haiti"], "answer": "Brazil", "explain": "Palmares endured for most of a century in northeastern Brazil before its destruction in 1694."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "revolution-and-freedom",
            "title": "Revolution and Freedom",
            "summary": "The Haitian Revolution and the long, incomplete fight for emancipation.",
            "order": 2,
            "lessons": [
                {
                    "slug": "haitian-revolution",
                    "title": "The Haitian Revolution: The Only Successful Slave Revolt to Found a Nation",
                    "order": 3,
                    "minutes": 30,
                    "summary": "From Bois Caïman to independence in 1804 — and the price Haiti paid for it.",
                    "learn": [
                        {"type": "p", "text": "Saint-Domingue, France's richest colony, produced about 40% of the world's sugar and 60% of its coffee using roughly half a million enslaved people — more than any other colony. In August 1791 the revolution began with coordinated uprisings; over thirteen years, leaders including Toussaint Louverture, Jean-Jacques Dessalines, and Henri Christophe defeated French, Spanish, and British forces. In 1804 Haiti declared independence — the first nation founded by formerly enslaved people, and the second republic in the Americas."},
                        {"type": "list", "items": [
                            "Context: the French Revolution's 1789 Declaration of the Rights of Man raised the question of whether those rights applied in the colonies.",
                            "Toussaint Louverture: a formerly enslaved military commander who outmaneuvered three empires before being captured by trickery in 1802.",
                            "Dessalines finished the war and proclaimed independence on January 1, 1804, naming the nation Haiti after an Indigenous Taíno name.",
                        ]},
                        {"type": "p", "text": "The consequences were global and costly. France demanded an indemnity of 150 million francs in 1825 (later reduced) as the price of recognition — Haiti borrowed at ruinous interest and was paying 'independence debt' into the 20th century, a New York Times 2022 investigation traced its lasting economic damage. Major powers, including the United States, refused recognition for decades because slaveholding nations feared the example."},
                        {"type": "example", "title": "Why it matters", "text": "The Haitian Revolution forced the question European philosophers avoided: what if the Enlightenment's 'universal rights' include the enslaved? Haiti answered it with the founding of a nation — and was punished economically for a century."},
                        {"type": "activity", "title": "Document study", "text": "Read an excerpt of Haiti's 1805 Constitution, which declared that all Haitians would be known by the generic name 'Black' regardless of complexion, and abolished slavery permanently. Write a paragraph: what message was Haiti sending to the world?"},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the Haitian Revolution.",
                        "questions": [
                            {"q": "Haiti's independence in 1804 was significant because…", "options": ["it was the first nation founded by formerly enslaved people", "it was the first European colony in the Americas", "it ended all slavery worldwide"], "answer": "it was the first nation founded by formerly enslaved people", "explain": "No other enslaved population had successfully revolted and founded an independent nation."},
                            {"q": "The 1825 French indemnity required Haiti to…", "options": ["pay France for the property — including people — slaveholders lost", "return Saint-Domingue to France", "ban trade with Britain"], "answer": "pay France for the property — including people — slaveholders lost", "explain": "Haiti was forced to compensate former enslavers, loading the new nation with debt that hampered it for generations."},
                        ],
                    },
                },
                {
                    "slug": "emancipation-and-its-limits",
                    "title": "Abolition, Emancipation, and Their Broken Promises",
                    "order": 4,
                    "minutes": 25,
                    "summary": "Legal freedom across the Americas — and the coercive labor systems that followed.",
                    "learn": [
                        {"type": "p", "text": "Slavery ended at different times across the Americas: Haiti 1804, the British Caribbean 1834 (with a forced 'apprenticeship' until 1838), the French colonies 1848, the United States 1865, Brazil 1888 — the last in the hemisphere. But legal emancipation rarely came with land, wages, or political rights, and planters immediately engineered systems to keep labor cheap and controllable."},
                        {"type": "list", "items": [
                            "British Caribbean: freedpeople sought independent villages; planters responded with high rents, vagrancy laws, and importing indentured laborers from India.",
                            "United States: after a brief hope in Reconstruction, sharecropping, Black Codes, and convict leasing re-created coerced labor under new names.",
                            "Brazil: freedpeople received no land or compensation; many formed quilombos, some of which still exist and hold land rights today.",
                        ]},
                        {"type": "tip", "text": "A useful test in history: when a system ends 'on paper,' look for the mechanisms that preserve its benefits. Rent, debt, and law replaced the whip — often with similar results."},
                        {"type": "activity", "title": "Case comparison", "text": "Choose two regions from the lesson. For each, name one post-emancipation mechanism that limited real freedom. Then write one sentence on how freedpeople resisted it."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of emancipation across the Americas.",
                        "questions": [
                            {"q": "Which country abolished slavery last in the Americas?", "options": ["Brazil (1888)", "The United States (1865)", "Britain (1834)"], "answer": "Brazil (1888)", "explain": "Brazil's Golden Law of 1888 ended slavery last in the hemisphere."},
                            {"q": "A common pattern after emancipation was…", "options": ["legal freedom combined with debt, rent, and law that kept labor coerced", "immediate land redistribution to the freed", "full political equality within a decade"], "answer": "legal freedom combined with debt, rent, and law that kept labor coerced", "explain": "Sharecropping, vagrancy laws, and high rents kept freedpeople economically bound after legal abolition."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "pan-africanism-and-cultural-reclamation",
            "title": "Pan-Africanism and Cultural Reclamation",
            "summary": "Political unity movements and the cultural renaissance they inspired.",
            "order": 3,
            "lessons": [
                {
                    "slug": "pan-africanism-movement",
                    "title": "Pan-Africanism: From Congresses to Ghana's Independence",
                    "order": 5,
                    "minutes": 25,
                    "summary": "Building a global political family across the Atlantic.",
                    "learn": [
                        {"type": "p", "text": "Pan-Africanism is the idea that people of African descent share linked histories and futures and should act together. Early voices include Henry Sylvester Williams, who organized the 1900 Pan-African Conference in London, and W. E. B. Du Bois, who convened a series of Pan-African Congresses. The movement's Fifth Congress, in Manchester in 1945 — organized with George Padmore and attended by Kwame Nkrumah and Jomo Kenyatta — turned decisively toward decolonization."},
                        {"type": "list", "items": [
                            "1900 London: first organized conference; demanded rights for 'subjects of the Empire.'",
                            "1945 Manchester: unions and independence leaders take over the agenda — colonialism's end becomes the explicit goal.",
                            "1957: Ghana becomes the first sub-Saharan British colony to win independence under Kwame Nkrumah, who declared Ghana's freedom 'meaningless unless linked up with the total liberation of Africa.'",
                            "1963: the Organization of African Unity is founded in Addis Ababa — Pan-Africanism becomes an institution.",
                        ]},
                        {"type": "example", "title": "Follow the people", "text": "Kwame Nkrumah studied in the United States and Britain, helped organize the 1945 Manchester Congress, and carried its program home to Ghana. The diaspora-to-Africa circuit ran in both directions: Du Bois moved to Ghana at Nkrumah's invitation and died there in 1963."},
                        {"type": "activity", "title": "Timeline build", "text": "Create a timeline with five Pan-Africanism milestones from 1900 to 1963. For each, note who organized it and what changed."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Pan-Africanism.",
                        "questions": [
                            {"q": "The 1945 Manchester Congress mattered because it…", "options": ["shifted Pan-Africanism toward organizing for independence from colonial rule", "created the United Nations", "was the last meeting ever held"], "answer": "shifted Pan-Africanism toward organizing for independence from colonial rule", "explain": "Attendees like Nkrumah and Kenyatta went on to lead Ghana and Kenya to independence."},
                            {"q": "Ghana's independence in 1957 was led by…", "options": ["Kwame Nkrumah", "W. E. B. Du Bois", "Marcus Garvey"], "answer": "Kwame Nkrumah", "explain": "Nkrumah, shaped by the Pan-African congresses, became Ghana's first prime minister."},
                        ],
                    },
                },
                {
                    "slug": "negritude-harlem-renaissance",
                    "title": "Negritude and the Harlem Renaissance: A Cultural Conversation Across the Atlantic",
                    "order": 6,
                    "minutes": 25,
                    "summary": "How Black writers in Paris and New York answered a century of racist 'science.'",
                    "learn": [
                        {"type": "p", "text": "In the 1930s, francophone Black students in Paris — Aimé Césaire (Martinique), Léopold Sédar Senghor (Senegal), and Léon-Gontran Damas (French Guiana) — founded Négritude: a movement asserting that African heritage was a source of value and art, not shame. It was a direct answer to colonial schooling that taught assimilation into French culture as the only path to worth. Meanwhile, the Harlem Renaissance of the 1920s — Langston Hughes, Zora Neale Hurston, Countee Cullen — celebrated Black American life and art; the two movements read and influenced each other through journals like La Revue du Monde Noir and The Crisis."},
                        {"type": "list", "items": [
                            "Césaire's 'Notebook of a Return to the Native Land' (1947) made Negritude a poetic force; Senghor later became Senegal's first president.",
                            "Harlem Renaissance writers debated 'heritage vs. modernity' — the same question Negritude posed in French.",
                            "Both movements insisted that Black culture be treated as a subject, not a problem.",
                        ]},
                        {"type": "tip", "text": "Read Césaire's line 'my negritude is not a stone… it thrusts into the red flesh of the soil' next to Hughes' 'I, Too.' Both answer exclusion with a claim to the future — compare their images."},
                        {"type": "activity", "title": "Cross-Atlantic reading", "text": "Read one Hughes poem and one Senghor or Césaire poem (translations are fine). Identify one shared theme and one difference in imagery. Cite a line for each."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Negritude and the Harlem Renaissance.",
                        "questions": [
                            {"q": "Negritude was founded by francophone writers including…", "options": ["Aimé Césaire and Léopold Sédar Senghor", "Langston Hughes and Zora Neale Hurston", "Marcus Garvey and Booker T. Washington"], "answer": "Aimé Césaire and Léopold Sédar Senghor", "explain": "The movement began among francophone students in 1930s Paris as an affirmation of African heritage."},
                            {"q": "Both Negritude and the Harlem Renaissance responded to…", "options": ["racist ideologies that treated African heritage as inferior", "the invention of photography", "the end of World War II"], "answer": "racist ideologies that treated African heritage as inferior", "explain": "Each movement asserted the value and artistry of Black culture against colonial and racist 'science.'"},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "modern-identity",
            "title": "Modern Identity",
            "summary": "Cultural synthesis in the Caribbean and Latin America — and diaspora identity today.",
            "order": 4,
            "lessons": [
                {
                    "slug": "caribbean-afro-latin-synthesis",
                    "title": "Caribbean and Afro-Latin Cultural Synthesis",
                    "order": 7,
                    "minutes": 25,
                    "summary": "Religion, music, and language as blended, living traditions.",
                    "learn": [
                        {"type": "p", "text": "Where enslaved Africans and colonial societies met, culture did not simply 'disappear' or 'copy' — it synthesized. Haitian Vodou wove West African Vodun spirits with Catholic saints' imagery; Cuban Santería (Lucumí) matched Yoruba orishas to saints; Brazil's Candomblé and capoeira preserved Yoruba and Central African elements under different covers. Music tells the same story: Haitian kompa, Cuban son (root of salsa), Brazilian samba, Jamaican reggae, and Trinidadian calypso and soca all carry African rhythmic structures — often the timeline-like clave pattern — recombined with European and Indigenous elements."},
                        {"type": "list", "items": [
                            "Clave: a repeating 3-2 (or 2-3) rhythmic pattern that structures Cuban son, salsa, and much of Afro-Caribbean music.",
                            "Language: Haitian Kreyòl, Papiamento, and Saramaccan are creole languages — new languages born from contact, with African grammar and vocabulary layered into European bases.",
                            "Carnival traditions from Trinidad to Brazil's Rio parades carry masking, procession, and social commentary from African festival practice.",
                        ]},
                        {"type": "example", "title": "Hear the structure", "text": "Clave (3-2): count 5 beats and clap the pattern short-short-short (pause) short-short. That syncopated skeleton underlies everything from Cuban rumba to 'Oye Como Va.' African timelines survived the Middle Passage inside rhythm."},
                        {"type": "activity", "title": "Trace a tradition", "text": "Pick one living tradition (a music genre, a religion, a festival). Identify its African element, its European or Indigenous element, and the new thing the combination created."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of cultural synthesis.",
                        "questions": [
                            {"q": "Cultural synthesis means…", "options": ["blending African and other traditions into new, distinct forms", "one culture completely erasing another", "copying Europe exactly"], "answer": "blending African and other traditions into new, distinct forms", "explain": "Vodou, Santería, salsa, and Kreyòl are new creations born from contact, not faded copies."},
                            {"q": "The clave pattern is best described as…", "options": ["a repeating rhythmic structure underlying much Afro-Caribbean music", "a West African language", "a type of drum"], "answer": "a repeating rhythmic structure underlying much Afro-Caribbean music", "explain": "Clave is the 3-2/2-3 timeline at the heart of son, salsa, and related genres."},
                        ],
                    },
                },
                {
                    "slug": "diaspora-today",
                    "title": "The Diaspora Today: Migration, Music, and Global Identity",
                    "order": 8,
                    "minutes": 25,
                    "summary": "How a billion people of African descent keep building a connected identity.",
                    "learn": [
                        {"type": "p", "text": "Today people of African descent number over a billion worldwide, including large communities in Brazil, the United States, the Caribbean, Europe, and West Africa itself. Migration flows both ways — Caribbean and African migration to global cities, and 'return' movements to Ghana (which offered citizenship pathways in 2019's Year of Return, marking 400 years since the first recorded enslaved arrival in Virginia). Culture travels instantly: Afrobeats from Lagos, amapiano from Johannesburg, dancehall from Kingston, and hip-hop from the Bronx continuously remix each other."},
                        {"type": "list", "items": [
                            "2015–2020s: the African Union declared the diaspora its 'sixth region,' formalizing ties with the continent.",
                            "Music genealogy: hip-hop and dancehall drew on Caribbean and African-American traditions; Afrobeats' global wave loops the influence back to Africa's biggest cities.",
                            "Identity debates: is diasporic identity one thing, many things, or a chosen connection? Writers like Stuart Hall answered: identity is 'production, never finished.'",
                        ]},
                        {"type": "tip", "text": "Avoid the two traps: pretending diaspora culture is 'just African' or 'just American/Caribbean/etc.' The honest description is a network — people, money, music, and ideas moving constantly in both directions."},
                        {"type": "activity", "title": "Map a connection", "text": "Choose one artist, athlete, writer, or movement with roots in two places (e.g., a UK grime artist of Ghanaian descent). Trace the two threads and how they combine."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the modern diaspora.",
                        "questions": [
                            {"q": "Ghana's 2019 'Year of Return' marked…", "options": ["400 years since the first recorded enslaved Africans arrived in Virginia, with invitations for the diaspora to reconnect", "Ghana's independence anniversary", "the founding of the African Union"], "answer": "400 years since the first recorded enslaved Africans arrived in Virginia, with invitations for the diaspora to reconnect", "explain": "Ghana used the 1619 anniversary to invite diasporans to visit, invest, and even seek citizenship."},
                            {"q": "Stuart Hall's view of cultural identity is that it is…", "options": ["continuously produced and changing, never finished", "a fixed essence inherited unchanged", "only a matter of citizenship papers"], "answer": "continuously produced and changing, never finished", "explain": "Hall argued diaspora identity is a production — built through history, media, and practice."},
                        ],
                    },
                },
            ],
        },
    ],
}
