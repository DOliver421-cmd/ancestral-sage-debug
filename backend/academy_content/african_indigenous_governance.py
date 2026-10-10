"""Grade 12 Social Studies / Government: Indigenous African Governance (published).

Grade 12 government rebuilt to compare African and Indigenous governance
traditions with modern constitutional systems: the Gadaa system of the
Oromo, the Iroquois Confederacy (Haudenosaunee), the Ashanti constitutional
council and the akyem, and the councils of the Akan, Igbo, and Somali — and
then to analyze modern constitutions in light of them.
"""

AFRICAN_INDIGENOUS_GOVERNANCE = {
    "slug": "african-indigenous-governance",
    "title": "African Indigenous Governance Systems & Modern Constitutional Law",
    "summary": "Gadaa, the Iroquois Confederacy, and the Ashanti constitutional council, compared with modern constitutions.",
    "description": (
        "Grade 12 government here studies governance systems usually left out of a "
        "standard civics course. The Gadaa system of the Oromo is a rotating "
        "democracy with an eight-year term limit, separation of functions, and a "
        "council of women with veto power. The Haudenosaunee (Iroquois) Confederacy "
        "federated nations under a Great Law of Peace, with clan mothers selecting "
        "and removing chiefs. The Ashanti kingdom had a constitutional council with "
        "a defined process for removing a king. Each is compared with the constitutions "
        "of modern republics — separation of powers, amendment procedure, judicial review."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies · Government",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["12"],
    "grade_label": "Grade 12",
    "status": "published",
    "audience": "Grade 12 students studying government and comparative constitutions.",
    "est_hours": 28,
    "passing_score": 80,
    "learning_objectives": [
        "Describe the structure of the Gadaa system and its limits on executive power.",
        "Explain how the Haudenosaunee Great Law of Peace federated nations and selected chiefs.",
        "Describe the Ashanti constitution and the council that could remove a king.",
        "Compare these systems with modern separation of powers and term limits.",
        "Explain how a constitution can be written, oral, or customary.",
        "Analyze a modern constitution's amendment and judicial review procedures.",
        "Evaluate how democratic principles appear across different political traditions.",
    ],
    "units": [
        {
            "slug": "gadaa-oro",
            "title": "The Gadaa System of the Oromo",
            "summary": "Eight-year terms, elected leaders, and a women's veto.",
            "order": 1,
            "lessons": [
                {
                    "slug": "gadaa-structure",
                    "title": "How Gadaa Works",
                    "order": 1,
                    "minutes": 26,
                    "summary": "A rotating democracy with mechanisms that modern constitutions would recognize.",
                    "learn": [
                        {"type": "p", "text": "The Oromo people of the Horn of Africa organized themselves for centuries under Gadaa: every eight years, power moved to a new grade of men who had trained and served in a series of age-sets, so executive, legislative, judicial, and ritual functions were separate. The Abba Gadaa (president) served a fixed eight-year term and could not immediately succeed himself. There were councils at every level, and an assembly of all adult men made law."},
                        {"type": "list", "items": [
                            "Age-set progression: education, military, and leadership duties by age class.",
                            "Fixed eight-year term for the Abba Gadaa; a new party takes power on schedule.",
                            "Separation: executive, judicial, and ritual roles distributed to different councils.",
                            "Accountability: leaders who abused power could be removed by the assembly.",
                        ]},
                        {"type": "example", "title": "Compare", "text": "The Twenty-second Amendment to the US Constitution limits presidents to two terms. Gadaa set a limit centuries earlier and enforced it by calendar."},
                        {"type": "activity", "title": "Diagram it", "text": "Draw an organizational chart of Gadaa with the abba gadaa, the council, the assembly, and the women's council. Label who selects and who can remove each."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Gadaa.",
                        "questions": [
                            {"q": "The Abba Gadaa serves a fixed term of…", "options": ["eight years", "four years", "life"], "answer": "eight years", "explain": "Power rotated to the next age-set every eight years."},
                            {"q": "Gadaa's separation of functions means…", "options": ["executive, judicial, and ritual roles were held by different bodies", "one person did everything", "there were no rules"], "answer": "executive, judicial, and ritual roles were held by different bodies", "explain": "Separation of powers is one of the system's defining features."},
                        ],
                    },
                },
                {
                    "slug": "womens-council-and-law",
                    "title": "The Women's Council and the Law",
                    "order": 2,
                    "minutes": 26,
                    "summary": "A constitutional veto, centuries before modern women's suffrage.",
                    "learn": [
                        {"type": "p", "text": "Gadaa's Siinqee institution gave Oromo women a formal political role: married women held a seat in the assembly through a representative (the atete or sinqee assembly) and had rights in marriage, property, and dispute resolution, including the right to refuse a marriage by a ritual act. A siinqee assembly could intervene in assemblies, and women's councils could veto decisions they judged harmful to the community."},
                        {"type": "list", "items": [
                            "Siinqee: a woman's staff, symbol of her right to refuse marriage and to protection.",
                            "Women's assembly: consulted on matters of public welfare.",
                            "Property and dispute rights recognized in customary law.",
                        ]},
                        {"type": "example", "title": "Compare", "text": "In the US Constitution, women's suffrage dates from 1920. In Oromo constitutional practice, women held formal political rights within Gadaa for centuries before that."},
                        {"type": "activity", "title": "Compare mechanisms", "text": "List two mechanisms that limit executive power in Gadaa and two in the US Constitution. Note which is older."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the women's council.",
                        "questions": [
                            {"q": "The siinqee is…", "options": ["a woman's staff symbolizing rights to refuse marriage and protection", "a king's crown", "a military banner"], "answer": "a woman's staff symbolizing rights to refuse marriage and protection", "explain": "It is a legal-religious institution of Oromo constitutional life."},
                            {"q": "The women's assembly in Gadaa could…", "options": ["consult and block harmful decisions", "appoint the king alone", "levy taxes only"], "answer": "consult and block harmful decisions", "explain": "It held a consultative and veto function in public life."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "haudenosaunee-confederacy",
            "title": "The Haudenosaunee Confederacy",
            "summary": "The Great Law of Peace and a federation of nations.",
            "order": 2,
            "lessons": [
                {
                    "slug": "great-law-of-peace",
                    "title": "The Great Law of Peace",
                    "order": 3,
                    "minutes": 26,
                    "summary": "Oral constitutional law binding six nations.",
                    "learn": [
                        {"type": "p", "text": "The Haudenosaunee (Iroquois) Confederacy is a federation of nations governed by the Great Law of Peace, an oral constitution recording the Peacemaker's work, wampum belts as legal records, and rules for confederation. The Grand Council's chiefs were selected by clan mothers — women who nominated and could remove them. Decisions were made by consensus among the nations, not by majority vote."},
                        {"type": "list", "items": [
                            "Nations: Mohawk, Oneida, Onondaga, Cayuga, Seneca, later Tuscarora.",
                            "Clan mothers select chiefs and may remove them for misconduct.",
                            "Consensus decision-making, with each nation retaining local power.",
                            "Wampum belts function as constitutions and treaties.",
                        ]},
                        {"type": "example", "title": "A constitution in wampum", "text": "The fact that the Haudenosaunee law is oral does not make it less of a constitution: it records powers, limits, succession, and amendment."},
                        {"type": "activity", "title": "Compare", "text": "In a table, compare Haudenosaunee consensus rule with majority rule in modern legislatures: strengths and weaknesses of each."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the Haudenosaunee.",
                        "questions": [
                            {"q": "Haudenosaunee chiefs were chosen by…", "options": ["clan mothers", "a king", "foreign powers"], "answer": "clan mothers", "explain": "Clan mothers nominated and could remove chiefs."},
                            {"q": "The Great Law of Peace is important because…", "options": ["it is an oral constitution with defined powers and limits", "it is a shopping list", "it was invented in 1900"], "answer": "it is an oral constitution with defined powers and limits", "explain": "It federated nations with specified rules of governance."},
                        ],
                    },
                },
                {
                    "slug": "federalism-origins",
                    "title": "Confederation and Modern Federalism",
                    "order": 4,
                    "minutes": 26,
                    "summary": "How federations divide power.",
                    "learn": [
                        {"type": "p", "text": "Both the Haudenosaunee Confederacy and earlier African federations divided power between a union and its members. Modern federal systems — the United States, Canada, Germany, Nigeria, Ethiopia — do the same, and each must answer the same questions: which powers belong to the union, which to the parts, and how disputes are resolved. Historians note that the Iroquois model was known to Benjamin Franklin and his peers, who proposed a similar 'Albany Plan' in 1754."},
                        {"type": "list", "items": [
                            "Enumerated powers: listed for the union; the rest reserved to members.",
                            "Supranational bodies: common defense, foreign affairs, trade.",
                            "Dispute resolution: courts, councils, or formal negotiation.",
                            "Amendment: who may change the compact.",
                        ]},
                        {"type": "example", "title": "A historical connection", "text": "Franklin's Albany Plan (1754) recommended a union of colonies 'after the model of the Six Nations' — an influence historians continue to debate."},
                        {"type": "activity", "title": "Design a confederation", "text": "Design a small confederation of five villages: list the powers held by the union, the powers held by villages, and how disputes are settled."},
                    ],
                    "check": {
                        "prompt": "Check what you know about federalism.",
                        "questions": [
                            {"q": "A federal system divides power between…", "options": ["a central government and its members", "two kings", "no one"], "answer": "a central government and its members", "explain": "Federalism allocates authority between levels."},
                            {"q": "Enumerated powers are…", "options": ["powers listed as belonging to the union", "powers that don't exist", "powers held only by cities"], "answer": "powers listed as belonging to the union", "explain": "Listing determines what the central government may do."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "ashanti-and-modern-law",
            "title": "Ashanti Constitution and Modern Law",
            "summary": "A council that could remove a king — and how modern constitutions do it.",
            "order": 3,
            "lessons": [
                {
                    "slug": "ashanti-constitution",
                    "title": "The Ashanti Constitution",
                    "order": 5,
                    "minutes": 26,
                    "summary": "A constitution that limited the king and guaranteed five freedoms.",
                    "learn": [
                        {"type": "p", "text": "The Ashanti kingdom (in modern Ghana) governed through a constitution known as the Seventy-Seven Laws of Komfo Anokye. Power was held by chiefs and by the Asanteman Council; the Asantehene (king) was enthroned — and could be removed — by the council, which could require the king to abdicate by removing his sandals and knocking his head on the ground three times. The constitution enumerated five freedoms including freedom of speech, movement, and assembly, and set rules for war, taxation, and inheritance."},
                        {"type": "list", "items": [
                            "King subject to law: the council could destool him.",
                            "A codified (oral but recorded) set of laws on many subjects.",
                            "Checks: quarterly obligations, accountability, and ritual constraints that functioned as legal checks.",
                        ]},
                        {"type": "example", "title": "A limit on power", "text": "Destoolment was a legal act of the council, not a coup — the office existed within a constitution that defined its removal."},
                        {"type": "activity", "title": "Compare removal", "text": "Compare Ashanti destoolment with modern impeachment: who holds the power, what is the standard, and what happens to the office?"},
                    ],
                    "check": {
                        "prompt": "Check what you know about the Ashanti system.",
                        "questions": [
                            {"q": "The Ashanti king could be removed by…", "options": ["a council that destooled him", "invading armies only", "a lottery"], "answer": "a council that destooled him", "explain": "Removal was a defined legal act of the governing council."},
                            {"q": "The Seventy-Seven Laws recorded…", "options": ["rules including enumerated freedoms", "only tax rates", "religious poetry"], "answer": "rules including enumerated freedoms", "explain": "It enumerated rights and duties across public life."},
                        ],
                    },
                },
                {
                    "slug": "modern-constitutional-law",
                    "title": "Modern Constitutional Law",
                    "order": 6,
                    "minutes": 26,
                    "summary": "Comparing the traditions with written constitutions.",
                    "learn": [
                        {"type": "p", "text": "Modern constitutions accomplish the same jobs the oral ones did: defining offices, limiting power, protecting rights, and providing amendment. The US Constitution sets separation of powers, bicameral legislation, judicial review (established in Marbury v. Madison), and a deliberately difficult amendment process in Article V. The constitutions of Nigeria, South Africa, and Ethiopia explicitly incorporate customary law and traditional authorities alongside modern courts."},
                        {"type": "list", "items": [
                            "Separation of powers: legislative, executive, judicial.",
                            "Judicial review: courts may strike laws down.",
                            "Amendment processes: supermajorities or referendums.",
                            "Plural legal systems: customary and modern law side by side.",
                        ]},
                        {"type": "example", "title": "Plural systems", "text": "In several African constitutions, customary courts and traditional councils coexist with constitutional courts — a legal fact, not nostalgia."},
                        {"type": "activity", "title": "Write the memo", "text": "Write a one-page memo: which principle from one of the three systems in this course should modern constitutions adopt, and why? Answer with evidence."},
                    ],
                    "check": {
                        "prompt": "Check what you know about modern constitutions.",
                        "questions": [
                            {"q": "Judicial review, established in Marbury v. Madison, allows…", "options": ["courts to strike down laws", "courts to make laws", "courts to tax citizens"], "answer": "courts to strike down laws", "explain": "Courts can invalidate laws that conflict with the constitution."},
                            {"q": "Plural legal systems means…", "options": ["customary law and modern law operate together", "no law operates", "only kings make law"], "answer": "customary law and modern law operate together", "explain": "Several constitutions recognize traditional and modern courts side by side."},
                        ],
                    },
                },
            ],
        },
    ],
}
