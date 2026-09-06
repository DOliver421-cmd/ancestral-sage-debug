"""Reading Foundations — Kindergarten (full published course)."""

READING_FOUNDATIONS_KINDERGARTEN = {
    "slug": "reading-foundations-kindergarten",
    "title": "Reading Foundations — Kindergarten",
    "summary": "Letter recognition, phonemic awareness, and first sounds.",
    "description": (
        "Kindergarteners begin the journey from spoken language to written language. "
        "This course focuses on print awareness, letter names and sounds, rhyming, and "
        "blending the first CVC words. Every lesson introduces a small, clear skill, "
        "shows examples, and checks understanding before the next lesson unlocks."
    ),
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["K"],
    "grade_label": "Kindergarten",
    "status": "published",
    "audience": "Kindergarten (ages 5–6), Foundations track; works for any pre-reader.",
    "est_hours": 16,
    "passing_score": 80,
    "learning_objectives": [
        "Recognize all 26 uppercase and lowercase letters by name.",
        "Produce the primary sound for each consonant and short vowel.",
        "Blend three phonemes into a simple CVC word.",
        "Segment a spoken CVC word into its individual sounds.",
        "Rhyme words and generate words that share a rime.",
        "Read high-frequency kindergarten sight words.",
    ],
    "units": [
        {
            "slug": "print-awareness-and-letters",
            "title": "Print Awareness and Letter Names",
            "summary": "How books work and naming the alphabet.",
            "order": 1,
            "lessons": [
                {
                    "slug": "how-books-work",
                    "title": "How Books Work",
                    "order": 2,
                    "minutes": 12,
                    "summary": "Learn how to hold a book and track print left to right.",
                    "learn": [
                        {"type": "p", "text": "A book has a front, a back, and pages that turn. We read from left to right, top to bottom. Words are made of letters, and letters stand for sounds."},
                        {"type": "list", "items": [
                            "Hold a book right-side up.",
                            "Start on the first page, top line, left side.",
                            "Point to each word as you read it.",
                            "Spaces separate words.",
                        ]},
                        {"type": "activity", "title": "Book walk", "text": "Pick a picture book. Turn the pages slowly. Point to the first word on the first page, then the last word. Say: 'We read left to right, top to bottom.'"},
                    ],
                    "check": {
                        "prompt": "Show what you know about how books work.",
                        "questions": [
                            {"q": "Which way do English words run across the page?", "options": ["left to right", "right to left", "bottom to top"], "answer": "left to right", "explain": "English is read from left to right, top to bottom."},
                            {"q": "What do spaces between words do?", "options": ["They separate words", "They end the story", "They are letters"], "answer": "They separate words", "explain": "Spaces help us see where one word stops and the next begins."},
                            {"q": "Where do we start reading a new page?", "options": ["top left", "bottom right", "the middle"], "answer": "top left", "explain": "Each new page starts at the top left corner."},
                        ],
                    },
                },
                {
                    "slug": "letter-names-a-m",
                    "title": "Letter Names A–M",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Name and write uppercase and lowercase A through M.",
                    "learn": [
                        {"type": "p", "text": "The alphabet has 26 letters. Each letter has an uppercase (big) form and a lowercase (small) form. Today we practice A through M."},
                        {"type": "list", "items": [
                            "A a — says /a/",
                            "B b — says /b/",
                            "C c — says /k/",
                            "D d — says /d/",
                            "E e — says /e/",
                            "F f — says /f/",
                            "G g — says /g/",
                            "H h — says /h/",
                            "I i — says /i/",
                            "J j — says /j/",
                            "K k — says /k/",
                            "L l — says /l/",
                            "M m — says /m/",
                        ]},
                        {"type": "activity", "title": "Letter sort", "text": "Write A–M on index cards in both cases. Mix them up. Sort them in order as fast as you can. Say each name and sound aloud."},
                    ],
                    "check": {
                        "prompt": "Show what you know about letters A–M.",
                        "questions": [
                            {"q": "Which letter comes after B?", "options": ["C", "A", "D"], "answer": "C", "explain": "The alphabet order is A, B, C, D…"},
                            {"q": "What is the lowercase form of M?", "options": ["m", "n", "w"], "answer": "m", "explain": "The lowercase (small) form of M is m."},
                            {"q": "What sound does H make?", "options": ["/h/", "/m/", "/a/"], "answer": "/h/", "explain": "H says /h/ as in hat and hop."},
                        ],
                    },
                },
                {
                    "slug": "letter-names-n-z",
                    "title": "Letter Names N–Z",
                    "order": 4,
                    "minutes": 15,
                    "summary": "Name and write uppercase and lowercase N through Z.",
                    "learn": [
                        {"type": "p", "text": "Finish the alphabet from N to Z. Keep practicing both uppercase and lowercase forms, because you will see both in books."},
                        {"type": "list", "items": [
                            "N n — says /n/",
                            "O o — says /o/",
                            "P p — says /p/",
                            "Q q — says /kw/",
                            "R r — says /r/",
                            "S s — says /s/",
                            "T t — says /t/",
                            "U u — says /u/",
                            "V v — says /v/",
                            "W w — says /w/",
                            "X x — says /ks/",
                            "Y y — says /y/",
                            "Z z — says /z/",
                        ]},
                        {"type": "activity", "title": "Alphabet song", "text": "Sing the alphabet song slowly and point to each letter as you name it. Then do it backward with a helper."},
                    ],
                    "check": {
                        "prompt": "Show what you know about letters N–Z.",
                        "questions": [
                            {"q": "Which letter comes after N?", "options": ["O", "M", "P"], "answer": "O", "explain": "After N comes O."},
                            {"q": "What sound does S make?", "options": ["/s/", "/z/", "/m/"], "answer": "/s/", "explain": "S usually says /s/ as in sun and sit."},
                            {"q": "What is the lowercase form of Z?", "options": ["z", "q", "n"], "answer": "z", "explain": "The lowercase form of Z is z."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "phonemic-awareness",
            "title": "Phonemic Awareness",
            "summary": "Hear, say, and play with the sounds in spoken words.",
            "order": 5,
            "lessons": [
                {
                    "slug": "rhyming-words",
                    "title": "Rhyming Words",
                    "order": 6,
                    "minutes": 12,
                    "summary": "Find and produce words that rhyme.",
                    "learn": [
                        {"type": "p", "text": "Rhyming words share the same ending sound. Cat and hat rhyme. Both end in -at. The beginning sound changes, but the rime stays the same."},
                        {"type": "list", "items": [
                            "Listen to the ending sound, not the beginning.",
                            "If two words end the same way, they rhyme.",
                            "You can make new rhymes by changing the first sound.",
                        ]},
                        {"type": "activity", "title": "Rhyme time", "text": "Say these words: pig, log, sun, rug. Which two rhyme? (pig and rug rhyme because they both end in -ug.)"},
                    ],
                    "check": {
                        "prompt": "Show what you know about rhyming.",
                        "questions": [
                            {"q": "Which word rhymes with cake?", "options": ["bake", "cup", "cat"], "answer": "bake", "explain": "Cake and bake both end in -ake."},
                            {"q": "Which word does NOT rhyme with hop?", "options": ["mop", "stop", "cup"], "answer": "cup", "explain": "Hop, mop, and stop end in -op. Cup ends in -up, so it does not rhyme."},
                            {"q": "To make a new rhyme for 'bell', you change the…", "options": ["beginning sound", "ending sound", "middle letter"], "answer": "beginning sound", "explain": "Keep the same ending and swap the first sound: bell, fell, sell."},
                        ],
                    },
                },
                {
                    "slug": "blending-sounds",
                    "title": "Blending Sounds",
                    "order": 7,
                    "minutes": 15,
                    "summary": "Put separate sounds together to say a word.",
                    "learn": [
                        {"type": "p", "text": "Blending means sliding sounds together without pausing. Hear /c/ … /a/ … /t/ and say 'cat.' This is the skill that turns phonemic awareness into real reading."},
                        {"type": "example", "title": "Three-sound blend", "text": "Say /m/ … /a/ … /n/ slowly. Now say it faster. man. That is blending."},
                        {"type": "activity", "title": "Sound slider", "text": "Use a toy car. Push it slowly as you say each sound in a CVC word. Push it fast for the whole word: /c/ /a/ /t/ → car zooms: 'cat!'"},
                    ],
                    "check": {
                        "prompt": "Show what you know about blending.",
                        "questions": [
                            {"q": "Blend these sounds into a word: /s/ /u/ /n/.", "options": ["sun", "sand", "run"], "answer": "sun", "explain": "Slide the three sounds together: sun."},
                            {"q": "Blend these sounds: /h/ /a/ /t/.", "options": ["hat", "hot", "hit"], "answer": "hat", "explain": "/h/ /a/ /t/ blended is hat."},
                            {"q": "Which skill helps you turn sounds into words?", "options": ["blending", "sorting", "writing"], "answer": "blending", "explain": "Blending slides separate sounds together to make a word."},
                        ],
                    },
                },
                {
                    "slug": "segmenting-sounds",
                    "title": "Segmenting Sounds",
                    "order": 8,
                    "minutes": 15,
                    "summary": "Break a spoken word into its separate sounds.",
                    "learn": [
                        {"type": "p", "text": "Segmenting is the reverse of blending. You hear a whole word and break it into individual sounds. 'Dog' becomes /d/ … /o/ … /g/."},
                        {"type": "list", "items": [
                            "Say the whole word slowly.",
                            "Tap once for each sound you hear.",
                            "Write the letters in order.",
                        ]},
                        {"type": "activity", "title": "Sound frames", "text": "Use three boxes (Elkonin boxes). Say 'pen.' Push a counter into the first box for /p/, the second for /e/, the third for /n/."},
                    ],
                    "check": {
                        "prompt": "Show what you know about segmenting.",
                        "questions": [
                            {"q": "How many sounds are in 'hen'?", "options": ["3", "2", "4"], "answer": "3", "explain": "hen = /h/ /e/ /n/ — three sounds."},
                            {"q": "Segment 'mud'.", "options": ["/m/ /u/ /d/", "/m/ /d/", "/m/ /u/ /r/"], "answer": "/m/ /u/ /d/", "explain": "mud breaks into three sounds: /m/, /u/, /d/."},
                            {"q": "Which is the first sound in 'fox'?", "options": ["/f/", "/o/", "/ks/"], "answer": "/f/", "explain": "The first sound in fox is /f/."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "short-vowels-and-cvc",
            "title": "Short Vowels and CVC Words",
            "summary": "Read and write simple CVC words using short vowel sounds.",
            "order": 9,
            "lessons": [
                {
                    "slug": "short-a-and-cvc",
                    "title": "Short A and CVC Words",
                    "order": 10,
                    "minutes": 15,
                    "summary": "Read and write CVC words with short a.",
                    "learn": [
                        {"type": "p", "text": "Short a says /a/ as in cat and hat. A CVC word is consonant-vowel-consonant: c-a-t. Read it sound by sound, then blend it fast."},
                        {"type": "list", "items": [
                            "cat, hat, bat, mat, sat, rat, pat, fat, van, fan, pan, man, tap, map, cap, lap",
                        ]},
                        {"type": "activity", "title": "Word build", "text": "Use letter tiles for C, A, T. Swap the first letter to make bat, hat, mat, pat, rat. Say each word aloud."},
                    ],
                    "check": {
                        "prompt": "Show what you know about short a CVC words.",
                        "questions": [
                            {"q": "Which word has the short a sound?", "options": ["cat", "bed", "pig"], "answer": "cat", "explain": "Cat has the short a sound /a/ in the middle."},
                            {"q": "Read the CVC word: b-a-t.", "options": ["bat", "bet", "bit"], "answer": "bat", "explain": "b-a-t blends to bat."},
                            {"q": "Which is NOT a CVC word?", "options": ["stop", "hat", "map"], "answer": "stop", "explain": "Stop has two beginning consonants blended, so it is CCVC, not CVC."},
                        ],
                    },
                },
                {
                    "slug": "short-i-o-u-and-cvc",
                    "title": "Short I, O, and U and CVC Words",
                    "order": 11,
                    "minutes": 15,
                    "summary": "Read and write CVC words with short i, o, and u.",
                    "learn": [
                        {"type": "p", "text": "Short i says /i/ as in pig. Short o says /o/ as in dog. Short u says /u/ as in cup. The CVC pattern works with any short vowel."},
                        {"type": "list", "items": [
                            "Short i: pig, wig, dig, lid, pin, win, fin, zip, lip, rip",
                            "Short o: dog, log, fog, mop, hop, pop, top, box, fox, pot",
                            "Short u: cup, pup, mud, bug, rug, tug, sun, fun, run, bun",
                        ]},
                        {"type": "activity", "title": "Vowel sort", "text": "Write these words on cards: pig, dog, cup, hat. Sort them into three piles by their middle vowel sound."},
                    ],
                    "check": {
                        "prompt": "Show what you know about short i, o, and u CVC words.",
                        "questions": [
                            {"q": "Which word has the short i sound?", "options": ["win", "hop", "sun"], "answer": "win", "explain": "Win has the short i sound in the middle."},
                            {"q": "Which word has the short o sound?", "options": ["dog", "pen", "bus"], "answer": "dog", "explain": "Dog has the short o sound in the middle."},
                            {"q": "Which word has the short u sound?", "options": ["cup", "map", "jam"], "answer": "cup", "explain": "Cup has the short u sound in the middle."},
                        ],
                    },
                },
                {
                    "slug": "sight-words-set-1",
                    "title": "Sight Words Set 1",
                    "order": 12,
                    "minutes": 12,
                    "summary": "Read high-frequency kindergarten sight words automatically.",
                    "learn": [
                        {"type": "p", "text": "Sight words are common words that we read instantly, without sounding out every letter. Practice them until you know them by heart."},
                        {"type": "list", "items": [
                            "the, of, and, a, to, in, is, you, that, it",
                            "Flash-card tip: say the word, cover it, say it again, then write it.",
                            "Tip: look for a small word inside a big word (it in bit).",
                        ]},
                        {"type": "activity", "title": "Flash-card sprint", "text": "Make ten flash cards with the words above. Time yourself for one minute. How many can you read?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about sight words.",
                        "questions": [
                            {"q": "Which word is a sight word?", "options": ["the", "block", "jumped"], "answer": "the", "explain": "The is one of the most common sight words in English."},
                            {"q": "Why do we practice sight words?", "options": ["So we read them instantly", "So we can spell them backwards", "So we can count them"], "answer": "So we read them instantly", "explain": "Sight words are high-frequency words we recognize instantly."},
                            {"q": "Which word is NOT in the set the, of, and, a, to?", "options": ["box", "the", "and"], "answer": "box", "explain": "box is not in that sight-word list."},
                        ],
                    },
                },
            ],
        },
    ],
}
