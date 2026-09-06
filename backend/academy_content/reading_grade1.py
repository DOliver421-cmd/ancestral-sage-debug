"""Reading Foundations (Grade 1) — full published course content."""

READING_GRADE_1 = {
    "slug": "reading-foundations-grade-1",
    "title": "Reading Foundations: Phonics and First Stories",
    "summary": "Sounds → words → sentences → stories. A complete first-grade reading course.",
    "description": (
        "First graders turn spoken language into written language. This course moves in "
        "four careful steps: short vowel sounds and blends, digraphs and the silent e, "
        "sight words and smooth sentence reading, and finally real first stories with "
        "characters, settings, and plots. Each lesson teaches a small, clear skill, shows "
        "examples, and checks understanding before the next lesson unlocks."
    ),
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["1"],
    "grade_label": "Grade 1",
    "status": "published",
    "audience": "Grade 1 (ages 6–7), Foundations track; works for any beginner reader.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": [
        "Read words with short vowels, consonant blends, digraphs, and the silent-e pattern.",
        "Read high-frequency sight words automatically.",
        "Read sentences with correct capitalization, punctuation, and phrasing.",
        "Identify characters, settings, and events in a short story.",
        "Retell a story in order and make a simple prediction.",
    ],
    "units": [
        {
            "slug": "letters-and-sounds",
            "title": "Letters and Sounds",
            "summary": "The sound-spelling patterns that build first words.",
            "order": 1,
            "lessons": [
                {
                    "slug": "short-vowels",
                    "title": "Short Vowel Sounds",
                    "order": 1,
                    "minutes": 15,
                    "summary": "Learn the short sounds of a, e, i, o, and u in three-letter words.",
                    "learn": [
                        {"type": "p", "text": "Every word is built from letters. Vowels are the letters A, E, I, O, and U. Each vowel has a short sound that we hear in small words."},
                        {"type": "list", "items": [
                            "Short a says /a/ as in cat and hat.",
                            "Short e says /e/ as in bed and hen.",
                            "Short i says /i/ as in pig and win.",
                            "Short o says /o/ as in dog and hop.",
                            "Short u says /u/ as in cup and sun.",
                        ]},
                        {"type": "p", "text": "A word like c-a-t has a consonant, a vowel, then a consonant. We call it a CVC word. Read it left to right: /c/ /a/ /t/ — cat!"},
                        {"type": "example", "title": "Try this pattern", "text": "Say the word bug slowly. Do you hear the short u in the middle? bug = /b/ /u/ /g/."},
                        {"type": "activity", "title": "Sound hunt", "text": "Look around your room. Find one thing whose name has a short vowel in the middle (like cup, bed, fan, pot, pig). Say it slowly and name the vowel sound you hear."},
                    ],
                    "check": {
                        "prompt": "Show what you know about short vowel sounds.",
                        "questions": [
                            {"q": "Which word has the short a sound like in cat?", "options": ["sun", "hat", "bed"], "answer": "hat", "explain": "Hat says /h/ /a/ /t/. The middle sound is short a, just like in cat."},
                            {"q": "Which word has the short i sound like in pig?", "options": ["win", "hop", "cup"], "answer": "win", "explain": "Win says /w/ /i/ /n/. Its middle sound is short i, like in pig."},
                            {"q": "The word hen has a short vowel in the middle. Which vowel is it?", "options": ["e", "a", "o"], "answer": "e", "explain": "Hen says /h/ /e/ /n/. The short e is the middle sound."},
                            {"q": "What do we call a word built like consonant-vowel-consonant, such as dog?", "options": ["a CVC word", "a long word", "a question"], "answer": "a CVC word", "explain": "dog = consonant (d) + vowel (o) + consonant (g), so it is a CVC word."},
                        ],
                    },
                },
                {
                    "slug": "consonant-blends",
                    "title": "Consonant Blends",
                    "order": 2,
                    "minutes": 15,
                    "summary": "Slide two consonants together at the start or end of a word.",
                    "learn": [
                        {"type": "p", "text": "Sometimes two consonants stand side by side, and you hear BOTH sounds. That is a blend. In stop you hear /s/ and /t/ together: s-t-op."},
                        {"type": "list", "items": [
                            "Beginning blends: bl (blue), cl (clap), fl (flag), gl (glad), pl (play), sl (sled).",
                            "More beginning blends: br (bring), cr (crab), dr (drum), fr (frog), gr (green), pr (print), tr (truck).",
                            "s-blends: sc (scarf), sk (skip), sm (smile), sn (snake), sp (spin), st (stop), sw (swim).",
                            "Ending blends: -nd (hand), -nt (ant), -mp (jump), -st (fast), -lk (milk).",
                        ]},
                        {"type": "example", "title": "Slide the sounds", "text": "For the word flag, do not stop between /f/ and /l/. Slide them: /fl/ … /a/ … /g/ → flag."},
                        {"type": "activity", "title": "Blend sort", "text": "Say each word: stop, crab, milk, swim. Which one has a blend at the END? (Answer: milk has -lk at the end. The others start with blends.)"},
                    ],
                    "check": {
                        "prompt": "Show what you know about blends.",
                        "questions": [
                            {"q": "Which word begins with the /st/ blend?", "options": ["stop", "hop", "frog"], "answer": "stop", "explain": "Stop starts with s and t together — /st/ is a blend."},
                            {"q": "In the word drum, which two letters slide together at the start?", "options": ["dr", "um", "du"], "answer": "dr", "explain": "drum begins with d and r together: /dr/."},
                            {"q": "Which word has a blend at the END?", "options": ["cat", "hand", "bed"], "answer": "hand", "explain": "hand ends with -nd: /n/ and /d/ slide together at the end of the word."},
                            {"q": "How many sounds do you hear in the blend /sl/ of sled?", "options": ["two sounds", "one sound", "three sounds"], "answer": "two sounds", "explain": "A blend keeps BOTH consonant sounds — /s/ and /l/ — so you hear two sounds."},
                        ],
                    },
                },
                {
                    "slug": "digraphs",
                    "title": "Digraphs: sh, ch, th, wh, and ck",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Two letters that make ONE new sound.",
                    "learn": [
                        {"type": "p", "text": "A digraph is two letters that come together to make ONE brand-new sound. They are different from blends because you do not hear each letter by itself."},
                        {"type": "list", "items": [
                            "sh makes the quiet sound at the start of ship and the end of fish.",
                            "ch makes the choo sound in chip and lunch.",
                            "th has two sounds: the one in thumb (no voice) and the one in this (voice).",
                            "wh makes the sound at the start of when and white.",
                            "ck makes the /k/ sound at the end of duck and back.",
                        ]},
                        {"type": "example", "title": "One sound, two letters", "text": "Look at fish. The last two letters, sh, make only ONE sound — the quiet /sh/. f-i-sh = three sounds."},
                        {"type": "activity", "title": "Digraph tap", "text": "Tap once for each SOUND in the word chip: /ch/ … /i/ … /p/ = three taps, even though chip has four letters."},
                    ],
                    "check": {
                        "prompt": "Show what you know about digraphs.",
                        "questions": [
                            {"q": "Which word has the sh sound like in ship?", "options": ["fish", "chip", "this"], "answer": "fish", "explain": "Fish ends with sh, which makes the same quiet /sh/ sound as the start of ship."},
                            {"q": "Which two letters make the /k/ sound at the end of duck?", "options": ["ck", "ch", "sh"], "answer": "ck", "explain": "ck at the end of duck makes one /k/ sound."},
                            {"q": "How is a digraph different from a blend?", "options": ["A digraph makes ONE new sound; a blend keeps both sounds.", "A digraph uses only vowels.", "A digraph is three letters."], "answer": "A digraph makes ONE new sound; a blend keeps both sounds.", "explain": "In a digraph like sh, two letters join to make one new sound. In a blend like st, you still hear both sounds."},
                            {"q": "Which word starts with the digraph wh?", "options": ["when", "wet", "spin"], "answer": "when", "explain": "when begins with wh — two letters that work together."},
                        ],
                    },
                },
                {
                    "slug": "silent-e",
                    "title": "Silent E and Long Vowels",
                    "order": 4,
                    "minutes": 15,
                    "summary": "The bossy e that makes a vowel say its name.",
                    "learn": [
                        {"type": "p", "text": "Sometimes a word ends with a silent e. The e does not make a sound, but it gives a job to the vowel before it: the vowel says its NAME (a long sound)."},
                        {"type": "list", "items": [
                            "cap → cape (a now says its name: /ā/)",
                            "kit → kite (i says its name: /ī/)",
                            "hop → hope (o says its name: /ō/)",
                            "cub → cube (u says its name: /yoo/ or /ū/)",
                            "pet → Pete (e says its name: /ē/)",
                        ]},
                        {"type": "example", "title": "See the pattern", "text": "Compare tap and tape. In tap, a is short: /t/ /a/ /p/. Add silent e and the word becomes tape: /t/ /ā/ /p/."},
                        {"type": "activity", "title": "Word ladder", "text": "Change one letter to make a new word: pin → pine? No! pin + e = pine. Now try: not → note, rid → ride. Say each new word and listen to the long vowel."},
                    ],
                    "check": {
                        "prompt": "Show what you know about silent e.",
                        "questions": [
                            {"q": "What does the silent e do to the vowel in the word kite?", "options": ["It makes the i say its name (/ī/).", "It makes the i silent.", "It makes the word plural."], "answer": "It makes the i say its name (/ī/).", "explain": "In kite, the silent e makes i say its name: /k/ /ī/ /t/."},
                            {"q": "Which word has a long vowel sound?", "options": ["hope", "hop", "hot"], "answer": "hope", "explain": "hope has a silent e, so o says its name: /h/ /ō/ /p/."},
                            {"q": "What is the word when you add silent e to cub?", "options": ["cube", "cub", "cute"], "answer": "cube", "explain": "cub + silent e = cube, and u says its name: /k/ /yoo/ /b/."},
                            {"q": "Which pair shows the same short→long change as cap → cape?", "options": ["kit → kite", "cat → cut", "dog → dot"], "answer": "kit → kite", "explain": "kit → kite is the same pattern: short i becomes long i when the silent e is added."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "reading-words",
            "title": "Reading Words",
            "summary": "Sight words, sentence sense, and smooth reading.",
            "order": 2,
            "lessons": [
                {
                    "slug": "sight-words",
                    "title": "Sight Words and Reading Fluently",
                    "order": 5,
                    "minutes": 15,
                    "summary": "Read the most common words in a snap.",
                    "learn": [
                        {"type": "p", "text": "Some words appear on almost every page — the, and, of, you, said, was, are, they. Many do not follow simple sound rules, so good readers learn to recognize them in a SNAP, without sounding them out."},
                        {"type": "list", "items": [
                            "the, and, of, to, in, is, you, that, it, he",
                            "was, for, on, are, as, with, his, they, I, at",
                            "be, this, have, from, or, one, had, by, word, but",
                            "said, what, we, when, your, can, there, use, an, each",
                        ]},
                        {"type": "p", "text": "Fluency means reading words so fast and smoothly that your brain can think about the MEANING of the sentence instead of working on each letter."},
                        {"type": "example", "title": "Snap reading", "text": "Cover this word list and have someone point at the word the. Can you say it instantly? That is snap reading. Practice five words at a time until each one is instant."},
                        {"type": "activity", "title": "Sight word sprint", "text": "Write the, was, said, they, have, what on cards. Read them as fast as you can. Then hide the cards and repeat the list from memory."},
                    ],
                    "check": {
                        "prompt": "Show what you know about sight words.",
                        "questions": [
                            {"q": "Why do we learn sight words by heart?", "options": ["They appear very often and many break the usual sound rules.", "They are the longest words in English.", "They are only found in fairy tales."], "answer": "They appear very often and many break the usual sound rules.", "explain": "Words like the and was are everywhere, and their spellings are tricky, so readers memorize them."},
                            {"q": "Which word is a sight word you should read in a snap?", "options": ["said", "cat", "stop"], "answer": "said", "explain": "said is one of the very common words that good readers know instantly; cat and stop follow regular sound patterns."},
                            {"q": "When you can read words instantly and smoothly, you are building…", "options": ["fluency", "handwriting", "alphabet order"], "answer": "fluency", "explain": "Fluency is reading smoothly and automatically so you can focus on meaning."},
                        ],
                    },
                },
                {
                    "slug": "sentence-sense",
                    "title": "Sentence Sense: Capitals and Punctuation",
                    "order": 6,
                    "minutes": 15,
                    "summary": "Capitals, periods, and question marks tell you how a sentence sounds.",
                    "learn": [
                        {"type": "p", "text": "A sentence is a group of words that tells a complete idea. Three helpers show where sentences begin and end: capital letters, periods, and question marks."},
                        {"type": "list", "items": [
                            "Every sentence starts with a capital letter: The dog ran.",
                            "A telling sentence ends with a period (.): We read a book.",
                            "An asking sentence ends with a question mark (?): Where is my hat?",
                            "A sentence that shows strong feeling can end with an exclamation point (!): Look out!",
                        ]},
                        {"type": "example", "title": "Read the end marks", "text": "Compare: You are going. (a fact) · You are going? (a question) · You are going! (excited). The end mark changes the sound of your voice."},
                        {"type": "activity", "title": "Fix the sentence", "text": "Fix this sentence so it is correct: \"my cat is soft\" → \"My cat is soft.\" What two things did you change? (Capital M and a period at the end.)"},
                    ],
                    "check": {
                        "prompt": "Show what you know about sentences.",
                        "questions": [
                            {"q": "How should every sentence begin?", "options": ["with a capital letter", "with a period", "with a question"], "answer": "with a capital letter", "explain": "Every sentence starts with a capital letter."},
                            {"q": "Which ending mark belongs on an asking sentence?", "options": ["?", ".", ","], "answer": "?", "explain": "A question like Where is my hat? ends with a question mark."},
                            {"q": "Which sentence is written correctly?", "options": ["the sun is bright.", "The sun is bright.", "the sun is bright"], "answer": "The sun is bright.", "explain": "It starts with a capital T and ends with a period."},
                        ],
                    },
                },
                {
                    "slug": "reading-with-rhythm",
                    "title": "Reading with Rhythm and Expression",
                    "order": 7,
                    "minutes": 15,
                    "summary": "Pause at punctuation and make your reading sound like talking.",
                    "learn": [
                        {"type": "p", "text": "Reading is not robot talking. Good readers pause at commas, stop at periods, let their voice go up at question marks, and sound excited at exclamation points. That is called expression."},
                        {"type": "list", "items": [
                            "Pause (short) at a comma: I like apples, pears, and plums.",
                            "Stop (longer) at a period: We went home. Then we ate.",
                            "Voice goes up at a question mark: Is it time for lunch?",
                            "Voice shows feeling at an exclamation point: What a big dog!",
                        ]},
                        {"type": "example", "title": "Robot vs. reader", "text": "Read this like a robot: \"The. sun. is. hot.\" Now read it like a person: \"The sun is hot.\" Feel the difference? Punctuation tells your voice when to breathe and when to stop."},
                        {"type": "activity", "title": "Partner reading", "text": "Read one page to a grown-up or a pet. Watch the end marks. Can you make your voice sound like talking, not spelling?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about expressive reading.",
                        "questions": [
                            {"q": "What does a period tell your voice to do?", "options": ["stop", "go up", "shout"], "answer": "stop", "explain": "A period ends a telling sentence, so your voice stops."},
                            {"q": "Where do good readers pause for just a moment?", "options": ["at a comma", "at the start of a word", "never"], "answer": "at a comma", "explain": "A comma marks a short pause inside a sentence."},
                            {"q": "If you see an exclamation point, your voice should…", "options": ["show strong feeling", "whisper", "stop completely"], "answer": "show strong feeling", "explain": "An exclamation point means excitement or strong feeling — let your voice show it."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "first-stories",
            "title": "First Stories",
            "summary": "Characters, settings, events — and retelling what you read.",
            "order": 3,
            "lessons": [
                {
                    "slug": "story-parts",
                    "title": "Story Parts: Characters, Setting, and Events",
                    "order": 8,
                    "minutes": 15,
                    "summary": "Find who is in the story, where it happens, and what happens.",
                    "learn": [
                        {"type": "p", "text": "Every story has building blocks. The CHARACTERS are the people or animals in the story. The SETTING is where and when the story happens. The EVENTS are the things that happen, one after another."},
                        {"type": "list", "items": [
                            "Characters: who the story is about (the fox, the girl, the robot).",
                            "Setting: where and when (in a forest, at night, at school in the morning).",
                            "Events: what happens first, next, and last (the beginning, middle, and end).",
                        ]},
                        {"type": "example", "title": "Find the parts", "text": "Story: \"Sam the squirrel looked for nuts in the park. First he checked under the big oak. Then he found a whole pile! Last, he hid them in his tree.\" Characters: Sam. Setting: the park. Events: looks for nuts → finds them under the oak → hides them in his tree."},
                        {"type": "activity", "title": "Three questions", "text": "Open any picture book. Ask: 1) Who is in this story? 2) Where does it happen? 3) What happens first, next, and last?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about story parts.",
                        "questions": [
                            {"q": "Who are the characters in a story?", "options": ["the people or animals the story is about", "the place where it happens", "the pictures on the cover"], "answer": "the people or animals the story is about", "explain": "Characters are who the story is about — people, animals, or even talking objects."},
                            {"q": "In a story about a bear fishing in a river at sunset, what is the setting?", "options": ["the river at sunset", "the bear", "the fish"], "answer": "the river at sunset", "explain": "The setting is where and when the story happens: the river at sunset."},
                            {"q": "The events of a story are…", "options": ["the things that happen, in order", "the title", "the author's name"], "answer": "the things that happen, in order", "explain": "Events are what happens — first, next, and last."},
                        ],
                    },
                },
                {
                    "slug": "retelling-predicting",
                    "title": "Retelling and Predicting",
                    "order": 9,
                    "minutes": 15,
                    "summary": "Tell a story back in order — and guess what comes next.",
                    "learn": [
                        {"type": "p", "text": "After you read, a great reader can RETELL the story: who it was about, where it happened, and the events in the right order. Retelling shows you understood what you read."},
                        {"type": "list", "items": [
                            "Start with the characters and setting: \"This story is about a cat named Max. It happens at the beach.\"",
                            "Tell the events in order using time words: first, then, next, last.",
                            "End with how the story finishes.",
                        ]},
                        {"type": "p", "text": "PREDICTING means using clues to guess what will happen next. When the character looks at dark clouds and grabs an umbrella, a good reader predicts: it is going to rain."},
                        {"type": "example", "title": "Retell in three sentences", "text": "Story: Max the cat chases a red ball. First the ball rolls into the sea. Then Max is too scared to swim. Last, a kind dog fetches the ball. Retell: \"This is about Max the cat at the beach. The ball rolled into the sea. Max would not swim, but a dog brought the ball back.\""},
                        {"type": "activity", "title": "Stop and predict", "text": "Read a page of a new book but stop before the last page. Say your prediction: \"I think ___ will happen next because ___.\" Then read on and check your guess."},
                    ],
                    "check": {
                        "prompt": "Show what you know about retelling and predicting.",
                        "questions": [
                            {"q": "What does it mean to retell a story?", "options": ["to say the story in your own words, in order", "to memorize the whole book", "to draw the cover"], "answer": "to say the story in your own words, in order", "explain": "Retelling is telling the story back — characters, setting, and events in the right order — in your own words."},
                            {"q": "Which word helps you tell events in order?", "options": ["first", "blue", "soft"], "answer": "first", "explain": "Time words like first, then, next, and last show the order of events."},
                            {"q": "A character puts on a coat and grabs an umbrella. What is a good prediction?", "options": ["She thinks it may rain.", "She is going to bed.", "She is baking a cake."], "answer": "She thinks it may rain.", "explain": "The clues — coat and umbrella — point to rain. A prediction uses clues to guess what comes next."},
                        ],
                    },
                },
            ],
        },
    ],
}
