"""K–2 Early ELA: Storytelling Traditions of the Global African Diaspora (published).

Early literacy — phonics, vocabulary, and comprehension — connected to the
story traditions African peoples carried across the Atlantic: West African
proverbs, Caribbean folklore, and African American spirituals. A beginning
reader practices sounds and sentences on literature that was written to be
performed.
"""

STORYTELLING_DIASPORA_K2 = {
    "slug": "storytelling-diaspora-k2",
    "title": "Storytelling Traditions of the Global African Diaspora",
    "summary": "Learning to read and listen with West African proverbs, Caribbean folklore, and African American spirituals.",
    "description": (
        "This early ELA course builds the same phonics, vocabulary, and comprehension "
        "skills as any first reading program, using material the African diaspora "
        "actually produced. Students learn to sound out words through call-and-response, "
        "perform folktales, decode the calling songs of enslaved people, and read the "
        "coded vocabulary of spirituals. Reading here begins with listening, because "
        "these traditions were made to be heard."
    ),
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "foundations",
    "tracks": ["foundations"],
    "grades": ["K", "1", "2"],
    "grade_label": "Grades K–2",
    "status": "published",
    "audience": "Beginning readers learning phonics, comprehension, and oral performance.",
    "est_hours": 14,
    "passing_score": 80,
    "learning_objectives": [
        "Identify the sounds of beginning, middle, and ending in spoken words.",
        "Retell a folktale in sequence using a beginning, middle, and end.",
        "Explain what a proverb is and give examples from African traditions.",
        "Recognize how meaning is carried in rhythm, repetition, and rhyme.",
        "Identify story elements: character, problem, and solution.",
        "Perform a short piece aloud with rhythm and expression.",
    ],
    "units": [
        {
            "slug": "call-and-response",
            "title": "Call and Response: Reading Aloud Together",
            "summary": "Where reading meets rhythm.",
            "order": 1,
            "lessons": [
                {
                    "slug": "sounds-in-words",
                    "title": "Hearing the Sounds in Words",
                    "order": 1,
                    "minutes": 15,
                    "summary": "Beginning, middle, and ending sounds, practiced on diaspora words.",
                    "learn": [
                        {"type": "p", "text": "Every word is made of sounds. Kente starts with the /k/ sound, balafon with the /b/ sound, and spirit with the /s/ sound. When you can hear those pieces, you can read words you have never seen before by putting the sounds together."},
                        {"type": "list", "items": [
                            "Beginning sound: dambe starts with /d/.",
                            "Middle sound: kora has /or/ in the middle.",
                            "Ending sound: djembe ends with /e/.",
                        ]},
                        {"type": "example", "title": "Say it out loud", "text": "Anansi begins with short a, next comes n, then a, then n, then s, then i. Six sounds make one spider's name."},
                        {"type": "tip", "text": "Words that rhyme share their ending sounds. In oral storytelling, rhyme helps listeners remember a long tale."},
                    ],
                    "check": {
                        "prompt": "Check the sounds you heard.",
                        "questions": [
                            {"q": "What is the beginning sound in the word 'kora'?", "options": ["/k/", "/r/", "/s/"], "answer": "/k/", "explain": "Kora starts with the /k/ sound made at the back of the mouth."},
                            {"q": "Rhyming words share their…", "options": ["ending sounds", "first letters", "number of letters"], "answer": "ending sounds", "explain": "Rhyme matches the ending sounds, which helps a listener remember lines."},
                        ],
                    },
                },
                {
                    "slug": "call-and-response-songs",
                    "title": "Call and Response",
                    "order": 2,
                    "minutes": 18,
                    "summary": "A leader sings, the group answers — and everyone learns the words.",
                    "learn": [
                        {"type": "p", "text": "Call and response is one of Africa's great gifts to world music and worship. One voice sings a line, and the group answers. The leader can change the verses, and the group still catches them — because response is built into the pattern. In churches, fields, and later in jazz and hip-hop, call and response keeps everyone inside the song."},
                        {"type": "list", "items": [
                            "The caller sings a line; the group answers with a repeated phrase.",
                            "It teaches words by memory before they are read by eye.",
                            "Jazz, gospel, reggae, and hip-hop all use it today.",
                        ]},
                        {"type": "example", "title": "Try it", "text": "Caller: 'Who built the pyramids?' — Group: 'Not aliens!' Caller: 'Who built the pyramids?' — Group: 'We did!' This pattern is how praise, protest, and teaching songs were made."},
                        {"type": "activity", "title": "Write a call and response", "text": "Write three lines you could sing as the caller, and one answer the whole class could shout back."},
                    ],
                    "check": {
                        "prompt": "Check what you know about call and response.",
                        "questions": [
                            {"q": "In call and response, the group's job is to…", "options": ["answer the leader with a repeated phrase", "stay silent", "read from a book"], "answer": "answer the leader with a repeated phrase", "explain": "The group answers a set phrase, so everyone can join the performance."},
                            {"q": "Call and response teaches words by…", "options": ["memory, through repetition", "spelling tests", "silent reading only"], "answer": "memory, through repetition", "explain": "Repeating the response fixes the words in memory before they are read."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "proverbs-and-tales",
            "title": "Proverbs and Tales",
            "summary": "Short sayings and long stories, and how each teaches.",
            "order": 2,
            "lessons": [
                {
                    "slug": "west-african-proverbs",
                    "title": "West African Proverbs",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Sentences that carry a whole lesson.",
                    "learn": [
                        {"type": "p", "text": "A proverb is a short sentence that carries a lot of meaning. Yoruba, Akan, Wolof, Gikuyu, Igbo and hundreds of other African languages hold thousands of them. Proverbs live inside everyday speech — a parent ends an argument by quoting one, and the argument ends."},
                        {"type": "list", "items": [
                            "Yoruba: 'However far the stream flows, it never forgets its source.'",
                            "Akan: 'When a king dies, his wife will know where he buried his tongue.'",
                            "Igbo: 'A man who makes trouble for others is also making one for himself.'",
                        ]},
                        {"type": "example", "title": "Word work", "text": "The proverb 'Wisdom is like a baobab tree; no one person can embrace it' contains the long a sound in tree, baobab, and embrace. Read them aloud and listen for the same vowel."},
                        {"type": "activity", "title": "Proverb hunt", "text": "Ask an elder in your family for a proverb in any language they speak. Write it, draw what it means, and read it aloud to the class."},
                    ],
                    "check": {
                        "prompt": "Check what you know about proverbs.",
                        "questions": [
                            {"q": "A proverb is…", "options": ["a short sentence that carries a deep meaning", "a long novel", "a type of number"], "answer": "a short sentence that carries a deep meaning", "explain": "Proverbs compress a full lesson into a few words."},
                            {"q": "Which is an example of a proverb?", "options": ["'However far the stream flows, it never forgets its source'", "'The dog is brown'", "'7 + 1 = 8'"], "answer": "'However far the stream flows, it never forgets its source'", "explain": "It carries a meaning about remembering origins, rather than stating a fact about a stream."},
                        ],
                    },
                },
                {
                    "slug": "story-parts",
                    "title": "Character, Problem, Solution",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Every tale has the same bones — learn them and you can retell any story.",
                    "learn": [
                        {"type": "p", "text": "Folktales across the diaspora share a skeleton: a character (often small or overlooked), a problem, and a solution won by wit. Anansi faces a tiger; Br'er Rabbit faces Br'er Fox; Anansi's cousin Trickster gets out of trouble. Naming the parts makes it easy to retell the story in order."},
                        {"type": "list", "items": [
                            "Character: who the story is about, and what they want.",
                            "Problem: what stands in the way.",
                            "Solution: how the character wins — usually by cleverness, not strength.",
                        ]},
                        {"type": "example", "title": "Retell it", "text": "The goat says 'I can't come down the hill' (problem). The rabbit goads the goat and they survive the fox (solution). Br'er Rabbit tales were retold across the American South and became a whole Walt Disney company, from African and Indigenous sources."},
                        {"type": "activity", "title": "Three-box retelling", "text": "Draw three boxes for character, problem, solution. Fill them in for a story you heard this week, then read it aloud to someone."},
                    ],
                    "check": {
                        "prompt": "Check the parts of a story.",
                        "questions": [
                            {"q": "In a folktale, the problem is…", "options": ["what stands in the character's way", "the name of the story", "the last sentence"], "answer": "what stands in the character's way", "explain": "The problem is the obstacle the character must overcome."},
                            {"q": "Anansi-type tales are usually solved by…", "options": ["cleverness rather than strength", "an earthquake", "a magic ruler"], "answer": "cleverness rather than strength", "explain": "Trickster heroes win with wit, which is why small characters defeat large ones."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "spirituals-and-songs",
            "title": "Spirituals: Singing the Meaning",
            "summary": "Reading and listening to African American sacred songs.",
            "order": 3,
            "lessons": [
                {
                    "slug": "spirituals-double-meaning",
                    "title": "Spirituals and Their Double Meanings",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Faith on the surface, freedom underneath.",
                    "learn": [
                        {"type": "p", "text": "Spirituals are African American religious songs created largely under slavery by African people and their descendants. Many carried a plain meaning about heaven and a hidden meaning about escape: the Jordan River was the Ohio, 'wade in the water' washed away tracking dogs, and the 'chariot' was the Underground Railroad. Skilled singers used coded lines to warn and guide."},
                        {"type": "list", "items": [
                            "'Wade in the Water' — escape along riverbanks to break scent trails.",
                            "'Steal Away' — a signal that a meeting or escape was near.",
                            "'Swing Low, Sweet Chariot' — the chariot means a ride to freedom.",
                        ]},
                        {"type": "example", "title": "Reading for meaning", "text": "Read 'Go Down, Moses' and ask: what is the plain story? What is the coded story? Two meanings in one song is a reading skill — you will use it in every poem and essay you read later."},
                        {"type": "activity", "title": "Two meanings", "text": "Pick one spiritual line. Draw the plain meaning at the top and the hidden meaning at the bottom, and label both."},
                    ],
                    "check": {
                        "prompt": "Check what you know about spirituals.",
                        "questions": [
                            {"q": "Many spirituals carried…", "options": ["two meanings: a sacred one and a hidden one", "only one meaning", "no lyrics"], "answer": "two meanings: a sacred one and a hidden one", "explain": "Songs like 'Wade in the Water' taught faith and marked escape routes at the same time."},
                            {"q": "'Wade in the water' helped fugitives by…", "options": ["hiding their scent from tracking dogs", "finding clean drinking water", "making better fishing"], "answer": "hiding their scent from tracking dogs", "explain": "Water breaks the scent trail that dogs follow."},
                        ],
                    },
                },
                {
                    "slug": "perform-your-story",
                    "title": "Perform Your Own Tale",
                    "order": 6,
                    "minutes": 20,
                    "summary": "Capstone: write, rehearse, and perform a short tale.",
                    "learn": [
                        {"type": "p", "text": "A written story becomes alive when it is performed. Your voice can change for each character, a drum can carry a rhythm, and the audience can answer. Performers of oral tradition add rhythm, repetition, and gesture so a listener can picture the story."},
                        {"type": "list", "items": [
                            "Choose a character with a want.",
                            "Create a problem that must be solved with cleverness.",
                            "Use repetition and rhyme so the group can chant with you.",
                            "Perform it: two characters, a problem, a solution, and a response.",
                        ]},
                        {"type": "tip", "text": "Griots do not read their tales, and storytellers in the Caribbean do not recite from paper. Performance is how the tradition survives."},
                        {"type": "activity", "title": "Performance", "text": "Write and perform a short call-and-response tale with a character, problem, and solution. Invite the audience to answer your repeating line."},
                    ],
                    "check": {
                        "prompt": "Check what makes a performance work.",
                        "questions": [
                            {"q": "Repetition in a tale helps listeners…", "options": ["join in and remember the story", "forget the story", "fall asleep"], "answer": "join in and remember the story", "explain": "Repeated lines let a listener become part of the telling."},
                            {"q": "Before performing you should…", "options": ["rehearse aloud several times", "read it once silently", "never practice"], "answer": "rehearse aloud several times", "explain": "Rehearsal builds rhythm, timing, and volume."},
                        ],
                    },
                },
            ],
        },
    ],
}
