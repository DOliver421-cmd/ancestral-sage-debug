"""Grade 10 ELA: Pan-African and Diasporic Literature (published).

Grade 10 ELA built around the Pan-African literary tradition: Achebe,
Césaire, Fanon, Emecheta, Soyinka, Hurston, McKay. Students study voice,
narrative structure, and rhetoric in texts that defined debates about
empire, race, language, and liberation — and use those texts to write
literary analysis.
"""

PAN_AFRICAN_DIASPORIC_LITERATURE = {
    "slug": "pan-african-diasporic-literature",
    "title": "Pan-African and Diasporic Literature",
    "summary": "Achebe, Césaire, Fanon, Emecheta, Soyinka, Hurston, and Claude McKay — the Pan-African literary tradition, read closely.",
    "description": (
        "Grade 10 English here reads the canon of the Pan-African and diasporic "
        "tradition instead of a generic world-literature survey. Chinua Achebe's "
        "Things Fall Apart answers Conrad from the inside; Aimé Césaire's Discourse "
        "on Colonialism indicts the colonizer with his own language; Frantz Fanon "
        "diagnoses colonial psychology; Buchi Emecheta and Wole Soyinka write womanhood "
        "and tragic comedy; Zora Neale Hurston's anthropology-in-fiction and Claude "
        "McKay's sonnets carry the resistance across the Atlantic. Students practice "
        "close reading, literary analysis, and comparative essay writing with these texts."
    ),
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["10"],
    "grade_label": "Grade 10",
    "status": "published",
    "audience": "Grade 10 students studying literature, rhetoric, and literary analysis.",
    "est_hours": 30,
    "passing_score": 80,
    "learning_objectives": [
        "Analyze how Achebe structures Things Fall Apart to answer colonial narratives.",
        "Explain Césaire's argument in Discourse on Colonialism and its rhetorical method.",
        "Describe Fanon's concept of colonial alienation and its use in later thought.",
        "Compare Hurston's fiction with her ethnographic method.",
        "Analyze how Emecheta uses form to depict women's resistance.",
        "Analyze Soyinka's tragicomedy in Death and the King's Horseman.",
        "Analyze the sonnet form in Claude McKay's protest sonnets.",
        "Write a comparative literary analysis with a thesis and textual evidence.",
    ],
    "units": [
        {
            "slug": "answering-empire",
            "title": "Answering Empire: Achebe and Conrad",
            "summary": "Who gets to tell the story of Africa.",
            "order": 1,
            "lessons": [
                {
                    "slug": "things-fall-apart-structure",
                    "title": "Things Fall Apart: Structure and Voice",
                    "order": 1,
                    "minutes": 30,
                    "summary": "Achebe's three-part novel and its answer to Heart of Darkness.",
                    "learn": [
                        {"type": "p", "text": "Chinua Achebe's 1958 novel is in three parts: Igbo life before the missionaries, the arrival of the Europeans and the courts, and the collapse of Umofia under colonial law. Achebe wrote it deliberately against Joseph Conrad's Heart of Darkness, in which Africa is a blank backdrop. Achebe gives Umuofia a full civic life — courts, religion, crops, wrestling — before the first missionary speaks."},
                        {"type": "list", "items": [
                            "Part One: Okonkwo's world, its rituals, and its own justice.",
                            "Part Two: missionaries, colonial courts, and the split in the community.",
                            "Part Three: the district commissioner's book — Africans become a paragraph in someone else's story.",
                        ]},
                        {"type": "example", "title": "The famous line", "text": "The District Commissioner decides Okonkwo's story is 'not worth a paragraph' and writes a 'reasonable paragraph' about pacification. That line is Achebe's indictment."},
                        {"type": "tip", "text": "Achebe writes in English on purpose, using Igbo proverbs inside English sentences — turning the colonizer's language into a vehicle for Igbo thought."},
                    ],
                    "check": {
                        "prompt": "Check your analysis of Achebe.",
                        "questions": [
                            {"q": "Achebe wrote Things Fall Apart partly in response to…", "options": ["Heart of Darkness by Joseph Conrad", "Moby-Dick by Melville", "Things Fall Apart responds only to Chinua himself"], "answer": "Heart of Darkness by Joseph Conrad", "explain": "Achebe deliberately answered Conrad's rendering of Africa as a blank backdrop."},
                            {"q": "The district commissioner's 'reasonable paragraph' symbolizes…", "options": ["colonial reduction of African life to a footnote", "the triumph of Igbo law", "the power of newspapers"], "answer": "colonial reduction of African life to a footnote", "explain": "The colonizer writes the colonized into one convenient line."},
                        ],
                    },
                },
                {
                    "slug": "cesaire-discourse",
                    "title": "Césaire's Discourse on Colonialism",
                    "order": 2,
                    "minutes": 30,
                    "summary": "Rhetoric as a weapon turned back.",
                    "learn": [
                        {"type": "p", "text": "Aimé Césaire, the poet-politician of Martinique, published Discourse on Colonialism in 1950 and made an argument nobody had made as sharply: Europe created 'savages' wherever it went, and no European could be called civilized while colonialism existed. He wrote it in the language of the colonizer — the technique of the négritude movement he founded with Léopold Senghor."},
                        {"type": "list", "items": [
                            "Césaire names the colonizer as the barbarian.",
                            "He indicts not 'bad individuals' but the system's logic.",
                            "He uses the colonizer's own prestigious rhetorical style to carry the charge.",
                        ]},
                        {"type": "example", "title": "Famous formulation", "text": "Césaire's closing images — 'the barbarism of the West', 'the Nazi-Christian' — refuse separation between European colonial violence and European fascism."},
                        {"type": "activity", "title": "Rhetoric hunt", "text": "In one paragraph of Césaire, mark three rhetorical strategies (anaphora, ironic praise, quotation of respectable Europeans). Explain what each does."},
                    ],
                    "check": {
                        "prompt": "Check your reading of Césaire.",
                        "questions": [
                            {"q": "Césaire's central argument is that…", "options": ["colonialism itself brutalized the colonizer", "colonists were all villains", "colonialism ended in 1950"], "answer": "colonialism itself brutalized the colonizer", "explain": "He argued the system corrupts and degrades the civilization that practices it."},
                            {"q": "Writing in French is an example of…", "options": ["using the colonizer's tools for liberation", "agreeing with colonialism", "avoiding the subject"], "answer": "using the colonizer's tools for liberation", "explain": "Négritude turned the colonial language into a vehicle for Black self-definition."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "diagnosis-and-interiority",
            "title": "Fanon, Hurston, and Interior Life",
            "summary": "Colonial psychology, and the black interior written from the inside.",
            "order": 2,
            "lessons": [
                {
                    "slug": "fanon-black-skin",
                    "title": "Fanon: Black Skin, White Masks",
                    "order": 3,
                    "minutes": 30,
                    "summary": "How a system gets inside the mind.",
                    "learn": [
                        {"type": "p", "text": "Frantz Fanon, the Martinican psychiatrist and Algerian revolutionary, argued in Black Skin, White Masks (1952) that colonialism works as much by psychology as by force. The colonized person is taught to see himself through the colonizer's eyes, and the result is a kind of doubled consciousness that Fanon had seen as a doctor in French psychiatric wards."},
                        {"type": "list", "items": [
                            "The look: a child on a train points and names 'Negro'; Fanon's self becomes fixed by that gaze.",
                            "Language: mastery of the colonizer's language is treated as evidence of humanity.",
                            "Masculinity, desire, and shame are all colonially constructed.",
                        ]},
                        {"type": "example", "title": "Legacy", "text": "Fanon's analysis shaped the Black Power movement, feminist theory, and post-colonial studies; Notes Toward a Theory of the Afro-American Surge onward cite him directly."},
                        {"type": "activity", "title": "Apply the concept", "text": "Identify one modern example of Fanon's 'look' — a moment where someone is defined by another's gaze. Explain it in 100 words."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Fanon.",
                        "questions": [
                            {"q": "Fanon argues colonialism operates on…", "options": ["psychology as well as force", "only markets", "only armies"], "answer": "psychology as well as force", "explain": "He shows how the colonial system colonizes perception and self-image."},
                            {"q": "The famous 'look' scene in Black Skin, White Masks involves…", "options": ["a child naming Fanon as 'Negro' on a train", "a courtroom verdict", "a plantation uprising"], "answer": "a child naming Fanon as 'Negro' on a train", "explain": "The child's fixed label shows how identity is imposed from outside."},
                        ],
                    },
                },
                {
                    "slug": "hurston-and-emecheta",
                    "title": "Hurston and Emecheta: Interior Women",
                    "order": 4,
                    "minutes": 30,
                    "summary": "Fiction and ethnography, resistance and structure.",
                    "learn": [
                        {"type": "p", "text": "Zora Neale Hurston trained as an anthropologist, collecting African American folktales in Florida and Black Caribbean storytelling in Haiti. Her novel Their Eyes Were Watching God puts Verna's interior life — desire, marriage, self-definition — at the center, written in speech rhythms that carry public address into private growth. Buchi Emecheta's Second Class Citizen makes the form of a Nigerian immigrant woman's marginalization the subject: the book's flat prose mirrors the flattened possibilities her characters fight."},
                        {"type": "list", "items": [
                            "Hurston: novels written out of fieldwork, and a novel whose center is a woman's self-realization.",
                            "Emecheta: Nigerian women in Lagos and London, class, and labor; she published 21 books.",
                            "Both: women's consciousness is the subject, not a decoration on a male plot.",
                        ]},
                        {"type": "example", "title": "Form as meaning", "text": "Their Eyes Were Watching God moves between free indirect discourse and quoted speech — the form enacts a woman speaking her own story after being spoken about."},
                        {"type": "activity", "title": "Compare", "text": "Write a paragraph comparing how Hurston and Emecheta use dialogue to show a woman's self-definition."},
                    ],
                    "check": {
                        "prompt": "Check what you know about these writers.",
                        "questions": [
                            {"q": "Zora Neale Hurston's fiction is informed by her work as…", "options": ["an anthropologist collecting folklore", "a lawyer", "a naval officer"], "answer": "an anthropologist collecting folklore", "explain": "Her field research into Southern and Caribbean speech shaped her style."},
                            {"q": "Emecheta's work centers…", "options": ["Nigerian women in Lagos and London", "British royalty", "French merchants"], "answer": "Nigerian women in Lagos and London", "explain": "Her novels follow women navigating class, labor, and migration."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "ritual-riteme-and-protest",
            "title": "Ritual, Ritual, and Protest Sonnets",
            "summary": "Soyinka's tragicomedy and McKay's sonnets.",
            "order": 3,
            "lessons": [
                {
                    "slug": "soyinka-horseman",
                    "title": "Soyinka: Death and the King's Horseman",
                    "order": 5,
                    "minutes": 30,
                    "summary": "A ritual interrupted by colonial administration.",
                    "learn": [
                        {"type": "p", "text": "Wole Soyinka's 1975 play is based on a real 1944 Yoruba death ritual: the horseman Elesin must accompany his king's spirit to the ancestral world. British colonial police intervene to save his life, and the interruption breaks the ritual — with tragic consequences. Soyinka uses Yoruba ritual, market language, and English administrative discourse in one play, refusing a European realist frame."},
                        {"type": "list", "items": [
                            "The play moves among market women, divination chants, colonial colonials, and ritual drumming.",
                            "Soyinka calls the play 'not a clash of cultures' but the consequences of one culture preventing another's passage.",
                            "Tragedy is enacted as communal and ritual, not individual psychology alone.",
                        ]},
                        {"type": "example", "title": "Famous statement", "text": "Soyinka wrote the play as an African tragedy with an African dramatic idiom, not an African answer to an English question."},
                        {"type": "activity", "title": "Stage it", "text": "Cast the scene of the colonial district officer's interruption with a partner and perform two minutes."},
                    ],
                    "check": {
                        "prompt": "Check your analysis of Soyinka.",
                        "questions": [
                            {"q": "The ritual Elesin must perform is…", "options": ["to accompany the king's spirit to the ancestors", "to crown a new king", "to trade with the British"], "answer": "to accompany the king's spirit to the ancestors", "explain": "The horseman's ritual death binds the king's passage."},
                            {"q": "Soyinka's dramatic form in the play is…", "options": ["a mix of Yoruba ritual and English administrative language", "strict Shakespearean verse", "silent film"], "answer": "a mix of Yoruba ritual and English administrative language", "explain": "He refuses a European realist form and writes in African dramatic idiom."},
                        ],
                    },
                },
                {
                    "slug": "mckay-protest-sonnets",
                    "title": "Claude McKay: Protest Sonnets",
                    "order": 6,
                    "minutes": 30,
                    "summary": "The Harlem Renaissance turns a European form against itself.",
                    "learn": [
                        {"type": "p", "text": "Claude McKay, born in Jamaica, wrote the Harlem Renaissance's most quoted protest sonnet, 'If We Must Die' (1919), during the Chicago race riots. The sonnet — Shakespeare's fourteen-line form — is usually love poetry; McKay fills it with defiance, urging 'kinsmen' to face a 'murderous, cowardly pack'. He also wrote 'America', a sonnet that loves and hates its subject in the same breath."},
                        {"type": "list", "items": [
                            "Sonnet form: 14 lines, a volta (turn), and a rhyme scheme.",
                            "McKay uses the form associated with high culture to carry political protest.",
                            "His work links the Caribbean, Harlem, and the Atlantic working class.",
                        ]},
                        {"type": "example", "title": "The turn", "text": "In 'America' McKay writes 'Although she feeds me bread of bitterness' and ends 'Like men we'll face the murderous, cowardly pack'. Hating the bowl, loving the fight — the volta is the poem's turn of feeling."},
                        {"type": "activity", "title": "Write a sonnet", "text": "Write a 14-line sonnet with a turn at line 9, on any injustice you have observed. Keep the rhyme scheme."},
                    ],
                    "check": {
                        "prompt": "Check what you know about McKay.",
                        "questions": [
                            {"q": "'If We Must Die' uses a form usually associated with…", "options": ["love poetry", "cooking", "news reports"], "answer": "love poetry", "explain": "McKay fills the love sonnet's form with a defiant political argument."},
                            {"q": "Claude McKay's background included…", "options": ["Jamaica and Harlem", "only England", "only the American south"], "answer": "Jamaica and Harlem", "explain": "His life links the Caribbean, Harlem, and the Atlantic working class."},
                        ],
                    },
                },
            ],
        },
    ],
}
