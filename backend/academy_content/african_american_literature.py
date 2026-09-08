"""African American Literature Foundations (published course).

ELA course tracing foundational eras — Harlem Renaissance, Black Arts
Movement, and Afrofuturism — plus oral traditions from folklore to hip-hop,
building narrative and rhetorical writing skills.
"""

AFRICAN_AMERICAN_LITERATURE = {
    "slug": "african-american-literature-foundations",
    "title": "African American Literature Foundations",
    "summary": "Foundational eras of Black literary art — spirituals and folklore, the Harlem Renaissance, the Black Arts Movement, and Afrofuturism — with writing practice in narrative and rhetoric.",
    "description": (
        "African American Literature Foundations introduces students to the major movements "
        "and forms of Black literary tradition: folktales and spirituals, the Harlem "
        "Renaissance poets and novelists, the Black Arts Movement, contemporary "
        "speculative fiction and Afrofuturism, and the spoken-word lineage from the "
        "talking blues to hip-hop. Students analyze style and audience, then practice "
        "the same craft: persona, imagery, persuasive structure, and revision."
    ),
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "foundations",
    "tracks": ["foundations", "scholar"],
    "grades": ["8", "9", "10", "11"],
    "grade_label": "Grades 8–11",
    "status": "published",
    "audience": "Middle and high school students building literary analysis and writing skills.",
    "est_hours": 24,
    "passing_score": 80,
    "learning_objectives": [
        "Identify the major eras of African American literary history and one signature work from each.",
        "Analyze how trickster folklore and oral tradition shape narrative structure.",
        "Explain the spirituals' double meanings and their literary legacy.",
        "Interpret Harlem Renaissance poetry for theme, voice, and imagery.",
        "Describe the Black Arts Movement's goals and its argument about art and audience.",
        "Define Afrofuturism and analyze a contemporary speculative text or song.",
        "Write a narrative and a persuasive piece applying techniques from each tradition.",
        "Revise writing for voice, structure, and audience awareness.",
    ],
    "units": [
        {
            "slug": "oral-traditions",
            "title": "Oral Traditions: Folktales, Spirituals, and the Spoken Word",
            "summary": "The roots: Anansi, the signifying monkey, spirituals, and the talking blues.",
            "order": 1,
            "lessons": [
                {
                    "slug": "anansi-and-trickster-tales",
                    "title": "Anansi and the Trickster Tradition",
                    "order": 1,
                    "minutes": 20,
                    "summary": "A West African spider god travels the Middle Passage and becomes folklore's smartest survivor.",
                    "learn": [
                        {"type": "p", "text": "Anansi the Spider came from Akan folklore in West Africa and crossed the Atlantic with the people who carried it. In Caribbean and African American tales, Anansi is small but wins through wit — outsmarting stronger animals and foolish masters. Trickster tales taught listeners that intelligence beats power, a lesson with obvious stakes under slavery."},
                        {"type": "list", "items": [
                            "Trickster tales use humor, repetition, and escalation.",
                            "The weak-but-clever hero outwits the strong through planning.",
                            "Related figures: Br'er Rabbit, the Signifying Monkey, John the trickster-slave of tales told inside quarters.",
                        ]},
                        {"type": "example", "title": "Structure to borrow", "text": "Trickster tales often end with a reversal — the powerful character's own pride becomes the trap. That reversal is a plot device you can use in your own fiction."},
                        {"type": "activity", "title": "Write a trickster scene", "text": "Write a 3-paragraph scene where a small, clever character wins against a bigger, stronger one. Use at least one reversal."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of trickster tradition.",
                        "questions": [
                            {"q": "The core lesson of trickster tales is that…", "options": ["wit can defeat power", "strength always wins", "rules should never be questioned"], "answer": "wit can defeat power", "explain": "Trickster tales celebrate cleverness as a survival strategy for the powerless."},
                            {"q": "A 'reversal' in a story is when…", "options": ["the expected outcome flips, often by the hero's design", "the setting changes", "a new character arrives"], "answer": "the expected outcome flips, often by the hero's design", "explain": "Reversals create surprise and moral irony — the proud fall into their own trap."},
                        ],
                    },
                },
                {
                    "slug": "spirituals-double-meaning",
                    "title": "Spirituals and Double Meaning",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Coded hope in song — and the literary technique it built.",
                    "learn": [
                        {"type": "p", "text": "Spirituals were religious songs with layered meanings. 'Steal Away' could be a hymn — or a signal for a secret meeting. 'Follow the Drinking Gourd' encoded directions toward freedom. This double voice — saying one thing to outsiders and another to the community — became a foundation of Black literary style that writers like Ralph Ellison and Henry Louis Gates Jr. trace through fiction, poetry, and rap."},
                        {"type": "list", "items": [
                            "Coded songs: 'Wade in the Water,' 'Steal Away,' 'Follow the Drinking Gourd.'",
                            "Call-and-response: leader and congregation build the song together — a pattern that shapes sermon, jazz, and hip-hop.",
                            "Literary term: 'signifyin(g)' — speaking indirectly, with a wink the audience catches.",
                        ]},
                        {"type": "tip", "text": "When you write for two audiences at once — insiders who get every line and outsiders who get the surface — you're using the oldest technique in this tradition."},
                        {"type": "activity", "title": "Two-audience line", "text": "Write one sentence that means something safe on the surface and something bolder to a friend who shares your context."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the spirituals.",
                        "questions": [
                            {"q": "'Double meaning' in spirituals means the songs…", "options": ["carried surface and coded meanings for different audiences", "were sung twice", "used two languages"], "answer": "carried surface and coded meanings for different audiences", "explain": "Coded spirituals communicated hope, planning, and resistance under the cover of worship."},
                            {"q": "Call-and-response is a pattern where…", "options": ["a leader's line is answered by the group", "verses repeat exactly", "a chorus sings harmony"], "answer": "a leader's line is answered by the group", "explain": "Call-and-response builds community participation and echoes through gospel, jazz, and hip-hop."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "harlem-renaissance",
            "title": "The Harlem Renaissance",
            "summary": "Langston Hughes, Zora Neale Hurston, and the flowering of the 1920s.",
            "order": 2,
            "lessons": [
                {
                    "slug": "harlem-renaissance-context",
                    "title": "The Renaissance in Context",
                    "order": 3,
                    "minutes": 20,
                    "summary": "The Great Migration, Harlem, and a new claim on American art.",
                    "learn": [
                        {"type": "p", "text": "Between roughly 1918 and 1935, Harlem became the capital of Black America and of a literary movement that declared Black artists would define themselves. Fueled by the Great Migration and publications like The Crisis and Fire!!, writers, poets, musicians, and painters created work that was popular, political, and proudly Black — read by both Black and white audiences and debated fiercely about its purpose."},
                        {"type": "list", "items": [
                            "Key figures: Langston Hughes, Zora Neale Hurston, Countee Cullen, Claude McKay, Nella Larsen, Jean Toomer.",
                            "Venues and patrons: the Savoy Ballroom, the 135th Street library, magazines and salons.",
                            "Central debate: portray everyday Black life or 'uplift' through refinement — Hughes chose the everyday, famously.",
                        ]},
                        {"type": "example", "title": "Hughes's manifesto", "text": "In 'The Negro Artist and the Racial Mountain' (1926), Hughes wrote that a younger poet wanted to be known as a poet, not a Black poet — Hughes called that desire a 'mountain' standing in the way of true art."},
                        {"type": "activity", "title": "Take a position", "text": "Should art try to represent the community or challenge it? Write one paragraph choosing a side, using Hughes or Hurston as your example."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the Harlem Renaissance.",
                        "questions": [
                            {"q": "The Harlem Renaissance was fueled largely by…", "options": ["the Great Migration and a concentration of Black artists in Harlem", "the end of World War II", "government arts funding"], "answer": "the Great Migration and a concentration of Black artists in Harlem", "explain": "Millions of Black southerners moved north, and Harlem's density created the scene."},
                            {"q": "Hughes argued Black artists should…", "options": ["portray real Black life without apology", "avoid politics entirely", "imitate European poetry exactly"], "answer": "portray real Black life without apology", "explain": "Hughes championed the everyday language, music, and people of Black America as art."},
                        ],
                    },
                },
                {
                    "slug": "reading-hughes",
                    "title": "Close Reading: Langston Hughes",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Voice, blues form, and imagery in 'The Negro Speaks of Rivers' and 'Mother to Son.'",
                    "learn": [
                        {"type": "p", "text": "Hughes built poems the way blues songs work: repetition with variation, plain words, and a voice you can hear. 'The Negro Speaks of Rivers' connects Black history to the Euphrates, Nile, and Mississippi — deep time in nine lines. 'Mother to Son' uses a staircase metaphor in dialect to carry a whole philosophy of persistence."},
                        {"type": "list", "items": [
                            "Blues form in poetry: a line repeated, then answered — mirroring musical structure.",
                            "Extended metaphor: the 'crystal stair' versus the worn, splintered one.",
                            "Free verse with musical rhythm rather than fixed meter.",
                        ]},
                        {"type": "tip", "text": "Analysis template: name the device, quote it, explain its effect on the reader. Device → evidence → effect. That's a body paragraph."},
                        {"type": "activity", "title": "Write in blues form", "text": "Write a 4-line poem where line 2 repeats line 1 with one change, and line 4 answers the problem in line 3."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Hughes's craft.",
                        "questions": [
                            {"q": "In 'Mother to Son,' the staircase symbolizes…", "options": ["life's hard climb and persistence", "a real home renovation", "social climbing"], "answer": "life's hard climb and persistence", "explain": "The splintered stairs carry the mother's message: keep climbing regardless."},
                            {"q": "A strong analytical paragraph moves…", "options": ["device → evidence → effect", "opinion → summary → opinion", "evidence → opinion only"], "answer": "device → evidence → effect", "explain": "Naming the technique, quoting it, then explaining its effect makes analysis concrete."},
                        ],
                    },
                },
                {
                    "slug": "reading-hurston",
                    "title": "Close Reading: Zora Neale Hurston",
                    "order": 5,
                    "minutes": 20,
                    "summary": "Dialect as art and free indirect style in Their Eyes Were Watching God.",
                    "learn": [
                        {"type": "p", "text": "Hurston trained as an anthropologist and recorded Black folklore across the South. In Their Eyes Were Watching God (1937), she writes narration in standard English and dialogue in rich Black southern dialect — a deliberate, artistic choice that critics first attacked and later recognized as the novel's power. Her metaphor-rich narration and her heroine Janie's voice made the book a classic."},
                        {"type": "list", "items": [
                            "Opening line strategy: the novel begins with ships on the horizon — a metaphor for what watchers wait for.",
                            "Free indirect discourse: narration slides into a character's voice without quotation marks.",
                            "The porch as stage: storytelling as community entertainment and social court.",
                        ]},
                        {"type": "example", "title": "Quote to study", "text": "'There are years that ask questions and years that answer.' One sentence sets the novel's whole theory of time."},
                        {"type": "activity", "title": "Voice shift", "text": "Write a two-sentence narration of an event, then rewrite the same event as a character's spoken dialogue in their own voice."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Hurston's technique.",
                        "questions": [
                            {"q": "Hurston's use of dialect is best described as…", "options": ["a deliberate artistic choice rooted in folklore fieldwork", "an error corrected in later editions", "a minor detail"], "answer": "a deliberate artistic choice rooted in folklore fieldwork", "explain": "Her anthropological ear made dialogue the vehicle of character and community."},
                            {"q": "Free indirect discourse is when…", "options": ["narration slides into a character's inner voice", "characters quote each other", "the narrator breaks the fourth wall"], "answer": "narration slides into a character's inner voice", "explain": "It merges narrator and character perspective, deepening intimacy."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "black-arts-and-beyond",
            "title": "The Black Arts Movement and Afrofuturism",
            "summary": "Art as activism in the 1960s, and Black speculation from Delany to the stars.",
            "order": 3,
            "lessons": [
                {
                    "slug": "black-arts-movement",
                    "title": "The Black Arts Movement",
                    "order": 6,
                    "minutes": 20,
                    "summary": "The 1960s aesthetic of Amiri Baraka, Nikki Giovanni, and Sonia Sanchez.",
                    "learn": [
                        {"type": "p", "text": "The Black Arts Movement (c. 1965–1975) grew alongside Black Power. Its writers demanded art by, for, and about the Black community — theaters, presses, and journals owned by Black people. Amiri Baraka founded Black Arts Repertory Theatre in Harlem; Nikki Giovanni, Sonia Sanchez, Haki Madhubuti, and Audre Lorde shaped its poetry, which favored direct address, jazz rhythm, and political fire."},
                        {"type": "list", "items": [
                            "Key institutions: Black Arts Repertory Theatre, Third World Press, Broadside Press.",
                            "Signature style: free verse, street language, direct political address, performance.",
                            "Audre Lorde: 'Poetry is not a luxury' — art as a tool of survival and change.",
                        ]},
                        {"type": "tip", "text": "Compare eras directly: Hughes argued for everyday Black life; Baraka demanded art as community weapon. Both changed American letters — same purpose, different volume."},
                        {"type": "activity", "title": "Write a spoken poem", "text": "Write 6 lines meant to be heard, not read: use direct address ('you'), one repeated phrase, and rhythm you could tap out."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the Black Arts Movement.",
                        "questions": [
                            {"q": "The Black Arts Movement insisted art should be…", "options": ["by, for, and about the Black community", "apolitical and universal", "written only in classical forms"], "answer": "by, for, and about the Black community", "explain": "BAM artists built their own presses, theaters, and audiences rather than seeking outside approval."},
                            {"q": "Audre Lorde's phrase 'poetry is not a luxury' argues that…", "options": ["art is essential to survival and change", "poems should be short", "poetry is for the wealthy"], "answer": "art is essential to survival and change", "explain": "Lorde framed imagination and expression as necessities, not decorations."},
                        ],
                    },
                },
                {
                    "slug": "afrofuturism",
                    "title": "Afrofuturism: Speculating Black Futures",
                    "order": 7,
                    "minutes": 20,
                    "summary": "From Octavia Butler and Sun Ra to N.K. Jemisin and Janelle Monáe.",
                    "learn": [
                        {"type": "p", "text": "Afrofuturism combines science fiction, history, and Black culture to imagine futures where Black people thrive — and to critique the present through metaphor. Its roots run through W.E.B. Du Bois's early speculative fiction and Sun Ra's space-age music, mature in Octavia Butler's novels (Kindred, Parable of the Sower), and flourish today in N.K. Jemisin's Broken Earth trilogy, the film Black Panther, and Janelle Monáe's android albums."},
                        {"type": "list", "items": [
                            "Octavia Butler: first Black woman to gain mainstream sci-fi fame; Kindred sends a modern woman back to slavery — time travel as historical argument.",
                            "Afrofuturist aesthetics: ancient Egypt, cosmic imagery, technology, and African tradition braided together.",
                            "Worldbuilding question every Afrofuturist text asks: who gets to design the future?",
                        ]},
                        {"type": "example", "title": "Metaphor at work", "text": "In Parable of the Sower, Butler's collapsing America reads like near-future news. Good speculation holds a mirror up to the present."},
                        {"type": "activity", "title": "Design a future", "text": "Sketch a future community (place, values, one technology) that solves one problem in your own community. Name what your world keeps from today and what it changed."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Afrofuturism.",
                        "questions": [
                            {"q": "Afrofuturism imagines…", "options": ["Black futures through speculative fiction, music, and art", "only historical documents", "escapist fantasy with no social meaning"], "answer": "Black futures through speculative fiction, music, and art", "explain": "It blends futurism with Black history and culture, often critiquing the present."},
                            {"q": "In Kindred, time travel functions as…", "options": ["a way to make history experiential and urgent", "a literal physics lesson", "pure entertainment"], "answer": "a way to make history experiential and urgent", "explain": "Butler's device forces her protagonist — and readers — to confront slavery directly."},
                        ],
                    },
                },
                {
                    "slug": "hip-hop-literary",
                    "title": "From Spoken Word to Hip-Hop",
                    "order": 8,
                    "minutes": 20,
                    "summary": "The last word in the oral tradition: rap as poetry on the page.",
                    "learn": [
                        {"type": "p", "text": "Hip-hop is the oral tradition's newest chapter. Rap uses rhyme, meter, allusion, and metaphor at speeds and densities rivals of any poetic form — and spoken word poetry carries the same lineage from the griot through the sermon through the cypher. Studying a verse as literature (sound, image, argument) reveals the craft beneath the flow."},
                        {"type": "list", "items": [
                            "Devices to hunt in a verse: internal rhyme, assonance, metaphor, allusion, double entendre.",
                            "Spoken word: performance poetry built for the stage — tone, pause, and gesture carry meaning.",
                            "Bridge back: a rap verse, a Hughes blues poem, and a trickster tale share structure — setup, repetition, reversal.",
                        ]},
                        {"type": "tip", "text": "Choose a verse with lyrics you consider literary. Annotate for three devices, then write a paragraph arguing what makes it art — device, evidence, effect."},
                        {"type": "activity", "title": "Capstone draft", "text": "Draft your final piece for this course: either a narrative in trickster-reversal form or a spoken-word poem using call-and-response. Bring it through one full revision."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of hip-hop as literature.",
                        "questions": [
                            {"q": "Analyzing a rap verse as literature means examining…", "options": ["its rhyme, meter, imagery, and argument", "only its popularity", "only its beat"], "answer": "its rhyme, meter, imagery, and argument", "explain": "Literary analysis applies to any crafted language — the devices are the evidence."},
                            {"q": "The revision step of writing exists to…", "options": ["re-see the draft and improve voice, structure, and clarity", "fix spelling only", "copy someone else's style"], "answer": "re-see the draft and improve voice, structure, and clarity", "explain": "Revision is where drafts become finished work — every tradition in this course revised."}
                        ],
                    },
                },
            ],
        },
    ],
}
