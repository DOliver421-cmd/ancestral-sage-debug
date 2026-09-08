"""Pre-Colonial African Kingdoms & Empires (published course).

Social studies course covering the wealth, governance, and achievements of
ancient African empires — Mali, Songhai, Aksum, Great Zimbabwe, and more —
beginning Black history with sovereignty and achievement, not enslavement.
"""

AFRICAN_KINGDOMS = {
    "slug": "african-kingdoms-empires",
    "title": "African Kingdoms & Empires",
    "summary": "The wealth, governance, scholarship, and global reach of pre-colonial African empires — Mali, Songhai, Aksum, Great Zimbabwe, and the Swahili Coast.",
    "description": (
        "African Kingdoms & Empires surveys a thousand years of African statecraft, trade, "
        "and scholarship. Students study the Mali and Songhai empires and Mansa Musa's "
        "hajj, the gold-and-salt trade across the Sahara, the trading cities of Gao, "
        "Timbuktu, and Djenné, the Kingdom of Aksum and Ethiopian Christianity, Great "
        "Zimbabwe's stone architecture, the Swahili Coast city-states, and the standards "
        "of evidence historians use to reconstruct the African past."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations", "scholar"],
    "grades": ["6", "7", "8", "9", "10"],
    "grade_label": "Grades 6–10",
    "status": "published",
    "audience": "Middle and high school students studying world history.",
    "est_hours": 22,
    "passing_score": 80,
    "learning_objectives": [
        "Locate the major pre-colonial African empires and their trade networks.",
        "Explain how the gold-and-salt trade financed West African empires.",
        "Describe Mansa Musa's hajj and its effect on global perceptions of Mali.",
        "Analyze Timbuktu's role as a center of scholarship and manuscript production.",
        "Compare governance structures across Mali, Songhai, and Aksum.",
        "Describe the architecture and economy of Great Zimbabwe.",
        "Identify the Swahili Coast city-states and their Indian Ocean trade.",
        "Evaluate primary and archaeological evidence used to study ancient Africa.",
    ],
    "units": [
        {
            "slug": "west-african-empires",
            "title": "West African Empires: Ghana, Mali, Songhai",
            "summary": "Gold, salt, and the rise of three great Sahelian empires.",
            "order": 1,
            "lessons": [
                {
                    "slug": "gold-and-salt-trade",
                    "title": "Gold, Salt, and the Trans-Saharan Trade",
                    "order": 1,
                    "minutes": 20,
                    "summary": "How geography and trade built West Africa's first empires.",
                    "learn": [
                        {"type": "p", "text": "West Africa held some of the world's richest gold deposits, while the Sahara held salt — essential for human life and scarce in the south. Traders crossed the desert in camel caravans, exchanging salt for gold, and the empires that controlled the trade routes grew wealthy taxing every exchange."},
                        {"type": "list", "items": [
                            "Ghana (c. 700–1240): first great empire, controlled the gold-salt trade, called its ruler 'ghana' (war chief).",
                            "Mali (c. 1235–1600): rose after the Battle of Kirina; controlled cities including Timbuktu and Djenné.",
                            "Songhai (c. 1464–1591): largest of the three, centered on Gao and Timbuktu under Askia Muhammad.",
                        ]},
                        {"type": "tip", "text": "Trade routes are highways of ideas as well as goods. Islam, Arabic script, and university scholarship traveled the same caravan routes as gold and salt."},
                        {"type": "activity", "title": "Map the trade", "text": "Sketch the trans-Saharan routes connecting the Wangara goldfields to the Mediterranean coast. Label three trading cities and two goods traded in each direction."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the trans-Saharan trade.",
                        "questions": [
                            {"q": "Why was salt as valuable as gold in West Africa?", "options": ["It was scarce in the south but essential for life", "It was used as currency in Europe", "It made gold easier to mine"], "answer": "It was scarce in the south but essential for life", "explain": "Salt preserves food and sustains humans in hot climates; the Sahara supplied it to gold-rich but salt-poor regions."},
                            {"q": "Empires like Ghana and Mali grew wealthy mainly by…", "options": ["taxing and controlling trade routes", "selling enslaved people to Europe", "farming the Sahara"], "answer": "taxing and controlling trade routes", "explain": "Whoever controlled the caravan routes and taxed goods moving through them controlled the wealth of the region."},
                        ],
                    },
                },
                {
                    "slug": "mansa-musa-hajj",
                    "title": "Mansa Musa and the Famous Hajj",
                    "order": 2,
                    "minutes": 20,
                    "summary": "The 1324 pilgrimage that made Mali a global name.",
                    "learn": [
                        {"type": "p", "text": "In 1324, Mansa Musa, ruler of Mali, made the hajj (pilgrimage) to Mecca. His caravan reportedly included thousands of soldiers, officials, and camels carrying gold. In Cairo he gave away or spent so much gold that its value dropped — a story recorded by Arab chroniclers and still cited by economists today."},
                        {"type": "list", "items": [
                            "The hajj announced Mali's wealth and power to the Islamic world.",
                            "Musa brought scholars and architects home, expanding mosques and schools.",
                            "The Catalan Atlas of 1375 depicted Mansa Musa holding a gold nugget — Africa's wealth mapped in Europe.",
                        ]},
                        {"type": "example", "title": "Primary source", "text": "The historian al-Umari, visiting Cairo years later, recorded Egyptians' accounts of Musa's generosity. Historians compare such accounts against each other to estimate what actually happened."},
                        {"type": "activity", "title": "Source check", "text": "Why might a Cairo chronicler exaggerate Musa's wealth? Write two reasons, then explain how a historian would test the claim."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Mansa Musa's hajj.",
                        "questions": [
                            {"q": "Mansa Musa's hajj is historically significant because it…", "options": ["introduced Mali's wealth to the wider world", "ended the salt trade", "conquered Egypt"], "answer": "introduced Mali's wealth to the wider world", "explain": "The journey spread Mali's reputation through the Islamic world and Europe, where it appeared on maps."},
                            {"q": "A historian reading one glowing account of the hajj should…", "options": ["compare it with other independent sources", "accept it as exact fact", "discard all chronicles"], "answer": "compare it with other independent sources", "explain": "Corroboration across sources is the core method historians use to test claims."},
                        ],
                    },
                },
                {
                    "slug": "timbuktu-scholarship",
                    "title": "Timbuktu: City of Scholars and Manuscripts",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Africa's great university city and its manuscript libraries.",
                    "learn": [
                        {"type": "p", "text": "Timbuktu became one of the world's great centers of learning. Sankore and other madrasas taught law, astronomy, mathematics, and medicine, and families built private libraries of handwritten books. Some 700,000 manuscripts survive from the region — evidence of deep, organized African scholarship."},
                        {"type": "list", "items": [
                            "University of Sankore: jurists, astronomers, and mathematicians in residence.",
                            "Manuscripts covered astronomy, mathematics, law, poetry, and diplomacy.",
                            "Descendants of Timbuktu families still preserve private libraries today.",
                        ]},
                        {"type": "tip", "text": "The claim 'Africans had no writing' collapses under the manuscripts of Timbuktu, written in Arabic and in Ajami — African languages written with Arabic script."},
                        {"type": "activity", "title": "Library of your own", "text": "Choose one subject taught at Sankore. Write a short paragraph on what studying it in the 1500s might have looked like."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Timbuktu's scholarship.",
                        "questions": [
                            {"q": "Timbuktu was best known as a center of…", "options": ["scholarship and manuscript production", "iron mining", "shipbuilding"], "answer": "scholarship and manuscript production", "explain": "Its universities and libraries made Timbuktu a magnet for scholars across West Africa and beyond."},
                            {"q": "Ajami refers to…", "options": ["African languages written in Arabic script", "a West African gold coin", "a trade route"], "answer": "African languages written in Arabic script", "explain": "Ajami traditions show African languages recorded in writing for centuries."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "aksum-zimbabwe-swahili",
            "title": "Aksum, Great Zimbabwe, and the Swahili Coast",
            "summary": "Kingdoms of the east: obelisks, stone cities, and ocean trade.",
            "order": 2,
            "lessons": [
                {
                    "slug": "kingdom-of-aksum",
                    "title": "The Kingdom of Aksum",
                    "order": 4,
                    "minutes": 20,
                    "summary": "A Red Sea power with its own script, coinage, and monumental architecture.",
                    "learn": [
                        {"type": "p", "text": "Aksum, in today's Ethiopia and Eritrea, controlled Red Sea trade between Rome, India, and interior Africa from roughly 100–940 CE. It minted its own coins, developed the Ge'ez script still used in Ethiopia, and carved giant granite stelae — some over 30 meters tall — as royal grave markers. Its king Ezana adopted Christianity in the 4th century, making Aksum one of the earliest Christian states."},
                        {"type": "list", "items": [
                            "Trade exports: ivory, gold, frankincense, and exotic animals.",
                            "The Obelisk of Aksum: a 24-meter carved stele imitating a multi-story tower.",
                            "Ge'ez script: one of Africa's oldest still-used writing systems.",
                        ]},
                        {"type": "example", "title": "Written record", "text": "The Persian prophet Mani named Aksum one of the four great powers of his era, alongside Rome, Persia, and China."},
                        {"type": "activity", "title": "Compare the records", "text": "List three kinds of evidence for Aksum's power (coins, stelae, foreign writings) and what each one proves."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Aksum.",
                        "questions": [
                            {"q": "Aksum's giant carved stelae served as…", "options": ["royal grave markers", "grain silos", "lighthouses"], "answer": "royal grave markers", "explain": "The multi-story stelae marked elite burial chambers, showcasing engineering skill."},
                            {"q": "Aksum demonstrated state power through…", "options": ["its own coinage and script", "a large navy of war canoes", "pyramid building"], "answer": "its own coinage and script", "explain": "Independent currency and writing are markers of an advanced, literate state."},
                        ],
                    },
                },
                {
                    "slug": "great-zimbabwe",
                    "title": "Great Zimbabwe: A Stone City in Southern Africa",
                    "order": 5,
                    "minutes": 20,
                    "summary": "Masonry, cattle wealth, and gold trade behind a lost city — and the fight over who built it.",
                    "learn": [
                        {"type": "p", "text": "Between the 11th and 15th centuries, the Shona builders of Great Zimbabwe raised stone walls up to 11 meters high without mortar, covering about 720 hectares. The city controlled gold and ivory trade to the Swahili Coast. Colonial-era Europeans refused to believe Africans built it, attributing it to Phoenicians or the Queen of Sheba — archaeology proved the builders were the ancestors of the Shona people, and the nation of Zimbabwe takes its name from the site."},
                        {"type": "list", "items": [
                            "The Great Enclosure: the largest ancient structure south of the Sahara.",
                            "Soapstone birds found at the site are Zimbabwe's national symbol.",
                            "Evidence: Shona pottery, local granite masonry traditions, radiocarbon dating.",
                        ]},
                        {"type": "tip", "text": "The history of Great Zimbabwe is also a lesson in bias: when evidence contradicts prejudice, follow the evidence."},
                        {"type": "activity", "title": "Debate the evidence", "text": "Write two sentences explaining why radiocarbon dating and pottery analysis settled the question of who built Great Zimbabwe."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Great Zimbabwe.",
                        "questions": [
                            {"q": "Great Zimbabwe's walls were built…", "options": ["with shaped granite blocks and no mortar", "with imported Roman brick", "of wood and earth only"], "answer": "with shaped granite blocks and no mortar", "explain": "Dry-stone masonry using local granite is the site's signature achievement."},
                            {"q": "Early Europeans credited the city to outsiders because…", "options": ["their bias rejected African achievement", "the Shona had no records", "the stones bore inscriptions"], "answer": "their bias rejected African achievement", "explain": "Archaeology later confirmed the African builders, exposing the bias in earlier accounts."},
                        ],
                    },
                },
                {
                    "slug": "swahili-coast-city-states",
                    "title": "The Swahili Coast City-States",
                    "order": 6,
                    "minutes": 20,
                    "summary": "Kilwa, Mombasa, and a fusion culture on the Indian Ocean.",
                    "learn": [
                        {"type": "p", "text": "Along the East African coast, city-states like Kilwa, Mombasa, Lamu, and Zanzibar grew rich on Indian Ocean trade with Arabia, Persia, India, and China from about 800–1500 CE. Their language, Swahili, blends Bantu grammar with Arabic vocabulary — a living record of cultural exchange. Kilwa's great mosque and palace of Husuni Kubwa showed coral-stone architecture unique to the coast, and Chinese porcelain from shipwrecks and ruins confirms the trade's reach."},
                        {"type": "list", "items": [
                            "Exports: gold (from Great Zimbabwe's network), ivory, timber, iron.",
                            "Kilwa Kisiwani is a UNESCO World Heritage site today.",
                            "Swahili is now spoken by over 100 million people across East Africa.",
                        ]},
                        {"type": "example", "title": "Global trade", "text": "Chinese porcelain bowls have been found built into Swahili tomb pillars — trade goods used as architecture and status."},
                        {"type": "activity", "title": "Follow the goods", "text": "Trace one export (gold or ivory) from interior Africa to a buyer in China. List every stop and middleman along the way."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the Swahili Coast.",
                        "questions": [
                            {"q": "The Swahili language shows cultural exchange through…", "options": ["Bantu grammar blended with Arabic vocabulary", "identical structure to Latin", "having no written form"], "answer": "Bantu grammar blended with Arabic vocabulary", "explain": "Language records contact; Swahili formed from centuries of coastal trade."},
                            {"q": "Kilwa's wealth came mainly from…", "options": ["Indian Ocean trade including inland gold", "diamond mining", "taxing the Nile"], "answer": "Indian Ocean trade including inland gold", "explain": "Coastal cities linked interior trade networks to markets across the ocean."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "governance-and-evidence",
            "title": "Governance, Legacy, and Reading the Evidence",
            "summary": "How these empires were ruled, and how we know what we know.",
            "order": 3,
            "lessons": [
                {
                    "slug": "african-governance",
                    "title": "How African Empires Were Governed",
                    "order": 7,
                    "minutes": 20,
                    "summary": "Kings, councils, provincial governors, and law in pre-colonial states.",
                    "learn": [
                        {"type": "p", "text": "African empires were not random chiefdoms; they were organized states. Mali and Songhai appointed provincial governors and standardized weights and measures. Askia Muhammad created ministries and a professional bureaucracy. In many societies, councils of elders balanced the king's power, and griots — hereditary historians — served as living archives of law and lineage."},
                        {"type": "list", "items": [
                            "Askia Muhammad's reforms: taxation, ministries, standard measures, trade courts.",
                            "Griots: oral historians who preserved genealogy, law, and epic history.",
                            "Council systems: shared decision-making that checked royal power.",
                        ]},
                        {"type": "tip", "text": "Oral tradition is not the absence of history — it is a different archive, with its own methods of verification. Historians test griot accounts against archaeology and documents."},
                        {"type": "activity", "title": "Compare systems", "text": "Choose two of Mali, Songhai, Aksum, and Great Zimbabwe. List one similarity and one difference in how they governed."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of African governance.",
                        "questions": [
                            {"q": "Askia Muhammad is known for…", "options": ["building a professional bureaucracy and standardizing trade", "leading the first hajj", "inventing Ge'ez script"], "answer": "building a professional bureaucracy and standardizing trade", "explain": "His administrative reforms organized Songhai into a durable, governed state."},
                            {"q": "Griots functioned as…", "options": ["living archives of history and law", "gold merchants", "naval commanders"], "answer": "living archives of history and law", "explain": "Trained memory-keepers preserved genealogy, epic, and legal precedent across generations."},
                        ],
                    },
                },
                {
                    "slug": "reconstructing-african-history",
                    "title": "Reconstructing the African Past",
                    "order": 8,
                    "minutes": 20,
                    "summary": "Sources, bias, and why the empire story was long buried.",
                    "learn": [
                        {"type": "p", "text": "For centuries, popular history started Africa's story with enslavement, erasing a thousand years of sovereignty and scholarship. Historians rebuilt the record using four kinds of evidence: written chronicles (Arabic and Ajami), archaeology (Timbuktu manuscripts, Great Zimbabwe, Kilwa ruins), oral tradition, and linguistics. Each source corrects the others' blind spots."},
                        {"type": "list", "items": [
                            "Written: al-Umari, the Tarikh al-Sudan, Catalan Atlas.",
                            "Archaeological: stele of Aksum, manuscript libraries, porcelain and coins.",
                            "Oral: the Epic of Sundiata, griot lineages.",
                            "Linguistic: Swahili's blended vocabulary mapping trade contacts.",
                        ]},
                        {"type": "example", "title": "Modern scholarship", "text": "The UNESCO General History of Africa, written by hundreds of African and international scholars, is the standard reference that restored these empires to world history."},
                        {"type": "activity", "title": "Source it", "text": "Pick one claim from this course. Identify which kind of evidence supports it and how that evidence could be challenged."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of historical method.",
                        "questions": [
                            {"q": "Which is an archaeological source for African history?", "options": ["Chinese porcelain found at Swahili sites", "the Epic of Sundiata", "the Catalan Atlas"], "answer": "Chinese porcelain found at Swahili sites", "explain": "Physical remains excavated from sites are archaeological evidence; the others are literary and cartographic."},
                            {"q": "Historians verify oral tradition by…", "options": ["cross-checking it with archaeology and documents", "discarding it entirely", "treating every word as literal fact"], "answer": "cross-checking it with archaeology and documents", "explain": "Oral tradition is a valid archive when tested against independent evidence."},
                        ],
                    },
                },
                {
                    "slug": "legacy-today",
                    "title": "Legacy: Why These Kingdoms Matter Today",
                    "order": 9,
                    "minutes": 20,
                    "summary": "National symbols, repatriated treasures, and modern pride.",
                    "learn": [
                        {"type": "p", "text": "The empires live on in place names, national symbols, and restitution debates. Zimbabwe's name and its soapstone birds, Mali's griot traditions, Ethiopia's Ge'ez script and Aksum obelisk (repatriated from Italy in 2005), and Swahili as a language of over 100 million people all connect present-day identity to this history. For descendants of the diaspora, this record reframes heritage: pre-colonial Africa was wealthy, literate, and globally connected."},
                        {"type": "list", "items": [
                            "The Aksum obelisk: looted by Mussolini's forces in 1937, returned in 2005.",
                            "Benin Bronzes: ongoing repatriation from museums in Europe and the US.",
                            "Timbuktu manuscripts: digitized after the 2012–13 conflict, preserved worldwide.",
                        ]},
                        {"type": "tip", "text": "Knowing this history changes the starting point of every conversation about Africa: from loss backward to achievement forward."},
                        {"type": "activity", "title": "Explain it", "text": "In one paragraph, explain to a younger student why the empires of Mali, Aksum, and Great Zimbabwe matter to understanding Africa today."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of this legacy.",
                        "questions": [
                            {"q": "The return of the Aksum obelisk in 2005 is an example of…", "options": ["cultural repatriation", "archaeological dating", "oral tradition"], "answer": "cultural repatriation", "explain": "Repatriation returns looted cultural property to its nation of origin."},
                            {"q": "Studying pre-colonial African empires matters because it…", "options": ["replaces a deficit story with a record of achievement", "proves Africa never had contact with others", "only matters to archaeologists"], "answer": "replaces a deficit story with a record of achievement", "explain": "The evidence shows wealth, literacy, law, and global trade — the true starting point."},
                        ],
                    },
                },
            ],
        },
    ],
}
