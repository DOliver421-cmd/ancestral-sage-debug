"""Reading Foundations — Grade 2 (full published course)."""

READING_FOUNDATIONS_GRADE_2 = {
    "slug": "reading-foundations-grade-2",
    "title": "Reading Foundations — Grade 2",
    "summary": "Fluent decoding, vocabulary, and comprehension of short texts.",
    "description": (
        "Second graders deepen decoding stamina and start reading for meaning. "
        "This course covers multisyllable words, common prefixes and suffixes, "
        "fluency practice, and comprehension strategies for short stories and "
        "informational paragraphs. Every lesson teaches a focused skill and checks "
        "mastery before moving on."
    ),
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["2"],
    "grade_label": "Grade 2",
    "status": "published",
    "audience": "Grade 2 (ages 7–8), Foundations track; useful for any reader building fluency.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": [
        "Decode two-syllable words using common syllable patterns.",
        "Read words with common prefixes and suffixes.",
        "Read grade-level text fluently with accuracy and expression.",
        "Use context and text features to determine word meanings.",
        "Retell a story with key details and make a simple prediction.",
        "Identify the main idea and supporting details in a short text.",
    ],
    "units": [
        {
            "slug": "multisyllable-words",
            "title": "Multisyllable Words",
            "summary": "Break long words into chunks using common syllable patterns.",
            "order": 1,
            "lessons": [
                {
                    "slug": "syllable-clapping",
                    "title": "Clap the Syllables",
                    "order": 2,
                    "minutes": 15,
                    "summary": "Hear and count syllables in spoken words.",
                    "learn": [
                        {"type": "p", "text": "Every syllable has one vowel sound. Clap once for each syllable. 'Rabbit' = /rab/ /bit/ — two claps. 'Butterfly' = /but/ /ter/ /fly/ — three claps."},
                        {"type": "list", "items": [
                            "Clap and say the word slowly.",
                            "Each hand clap lands on a new syllable.",
                            "Count the claps to find the number of syllables.",
                        ]},
                        {"type": "activity", "title": "Syllable hunt", "text": "Find three objects in the room with two syllables (ta-ble, pen-cil, win-dow). Clap and say each word."},
                    ],
                    "check": {
                        "prompt": "Show what you know about syllables.",
                        "questions": [
                            {"q": "How many syllables are in 'paper'?", "options": ["2", "1", "3"], "answer": "2", "explain": "pa-per — two vowel sounds, two claps."},
                            {"q": "How many syllables are in 'elephant'?", "options": ["3", "2", "4"], "answer": "3", "explain": "el-e-phant — three vowel sounds, three claps."},
                            {"q": "What tells you a syllable has a vowel sound?", "options": ["You hear one vowel sound", "You see one consonant", "You feel one breath"], "answer": "You hear one vowel sound", "explain": "Each syllable has one vowel sound."},
                        ],
                    },
                },
                {
                    "slug": "closed-syllables",
                    "title": "Closed Syllables",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Read two-syllable words with short vowels in each closed syllable.",
                    "learn": [
                        {"type": "p", "text": "A closed syllable ends in a consonant. The vowel says its short sound. 'Rabbit' = closed + closed. 'Cabin' = closed + closed. Read each chunk, then blend the chunks."},
                        {"type": "example", "title": "Chunk it", "text": "rab-bit: read 'rab' then 'bit,' then say the whole word: rabbit. The short vowel in each chunk helps you decode."},
                        {"type": "activity", "title": "Chunk and read", "text": "Use a highlighter to split these words into closed syllables: mitten, rotten, kitten, cotton, happen. Read each chunk, then the whole word."},
                    ],
                    "check": {
                        "prompt": "Show what you know about closed syllables.",
                        "questions": [
                            {"q": "Which word has two closed syllables?", "options": ["kitten", "he", "she"], "answer": "kitten", "explain": "kit-ten: both chunks end in consonants and have short vowels."},
                            {"q": "In 'mitten', the first syllable 'mit' has a…", "options": ["short i", "long i", "silent e"], "answer": "short i", "explain": "Closed syllables usually have short vowels."},
                            {"q": "How do you read a two-syllable word with closed chunks?", "options": ["Read each chunk then blend", "Sound out every letter", "Guess from the picture"], "answer": "Read each chunk then blend", "explain": "Chunking makes long words easier to decode."},
                        ],
                    },
                },
                {
                    "slug": "prefixes-and-suffixes",
                    "title": "Common Prefixes and Suffixes",
                    "order": 4,
                    "minutes": 15,
                    "summary": "Recognize and read words with un-, re-, -ed, and -ing.",
                    "learn": [
                        {"type": "p", "text": "A prefix attaches to the front of a base word. A suffix attaches to the end. They can change the meaning of the word."},
                        {"type": "list", "items": [
                            "un- means 'not' or 'reverse': unhappy, unlock",
                            "re- means 'again': replay, reread",
                            "-ed shows past tense: walked, jumped",
                            "-ing shows an action happening now: walking, jumping",
                        ]},
                        {"type": "activity", "title": "Word changer", "text": "Start with the base word 'do.' Add un- to make undo. Add re- to make redo. Add -ed to make did. What does each new word mean?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about prefixes and suffixes.",
                        "questions": [
                            {"q": "What does the prefix un- mean in 'unhappy'?", "options": ["not happy", "very happy", "happy again"], "answer": "not happy", "explain": "un- often means not or reverse."},
                            {"q": "Which word has the suffix -ing?", "options": ["jumping", "reread", "undo"], "answer": "jumping", "explain": "-ing is a suffix that goes at the end of a word."},
                            {"q": "What does re- mean in 'reread'?", "options": ["read again", "read fast", "read aloud"], "answer": "read again", "explain": "re- means again."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "fluency-and-comprehension",
            "title": "Fluency and Comprehension",
            "summary": "Read aloud smoothly and understand what you read.",
            "order": 5,
            "lessons": [
                {
                    "slug": "reading-fluently",
                    "title": "Reading Fluently",
                    "order": 6,
                    "minutes": 15,
                    "summary": "Practice reading with accuracy, speed, and expression.",
                    "learn": [
                        {"type": "p", "text": "Fluency means reading accurately, at a good pace, and with expression — like you are talking. Practice makes fluent."},
                        {"type": "list", "items": [
                            "Read the same short passage three times.",
                            "First time: focus on correct words.",
                            "Second time: read a little faster.",
                            "Third time: add expression — sound excited, soft, or curious.",
                        ]},
                        {"type": "activity", "title": "Partner read", "text": "Read the same short paragraph with a partner. Listen for smoothness and expression. Then switch."},
                    ],
                    "check": {
                        "prompt": "Show what you know about fluency.",
                        "questions": [
                            {"q": "Fluency includes…", "options": ["accuracy, speed, and expression", "guessing hard words", "skipping punctuation"], "answer": "accuracy, speed, and expression", "explain": "Fluent readers read correctly, at a good pace, and with expression."},
                            {"q": "What should you do when you see a period?", "options": ["Pause and lower your voice", "Read faster", "Skip it"], "answer": "Pause and lower your voice", "explain": "Punctuation tells readers how to use expression."},
                            {"q": "The best way to build fluency is to…", "options": ["practice the same passage repeatedly", "only read easy books", "never re-read"], "answer": "practice the same passage repeatedly", "explain": "Repeated reading builds accuracy, pace, and expression."},
                        ],
                    },
                },
                {
                    "slug": "context-clues",
                    "title": "Context Clues",
                    "order": 7,
                    "minutes": 15,
                    "summary": "Use the rest of the sentence to figure out a new word.",
                    "learn": [
                        {"type": "p", "text": "When you meet an unfamiliar word, do not skip it. Look at the other words in the sentence — they are clues."},
                        {"type": "list", "items": [
                            "Definition clue: the sentence tells you what the word means.",
                            "Example clue: the sentence gives examples.",
                            "Opposite clue: the sentence uses a word with the opposite meaning.",
                        ]},
                        {"type": "example", "title": "Clue in action", "text": "The arid desert had almost no rain. From the phrase 'almost no rain' you can guess that arid means very dry."},
                    ],
                    "check": {
                        "prompt": "Show what you know about context clues.",
                        "questions": [
                            {"q": "Which clue helps you figure out 'gigantic' in 'The gigantic pumpkin weighed 500 pounds'?", "options": ["weighed 500 pounds", "the pumpkin", "gigantic"], "answer": "weighed 500 pounds", "explain": "The weight gives a clue that gigantic means very big."},
                            {"q": "If you read 'The cozy cabin was warm and snug,' what does cozy mean?", "options": ["warm and comfortable", "very large", "cold"], "answer": "warm and comfortable", "explain": "Warm and snug are clues that cozy means comfortable."},
                            {"q": "What should you do when you see an unfamiliar word?", "options": ["Look for clues in the sentence", "Skip every hard word", "Ask for the answer"], "answer": "Look for clues in the sentence", "explain": "Context clues help you figure out new words while you read."},
                        ],
                    },
                },
                {
                    "slug": "main-idea-and-details",
                    "title": "Main Idea and Details",
                    "order": 8,
                    "minutes": 15,
                    "summary": "Find the big idea and the facts that support it.",
                    "learn": [
                        {"type": "p", "text": "Every paragraph has a main idea — the most important thing the author wants you to know. Details are the smaller facts that support the main idea."},
                        {"type": "list", "items": [
                            "Ask: What is this mostly about?",
                            "The first and last sentences often state the main idea.",
                            "Details answer questions like who, what, when, where, and how.",
                        ]},
                        {"type": "activity", "title": "Main-idea hunt", "text": "Read a short paragraph about bees. Circle the main idea and underline three supporting details."},
                    ],
                    "check": {
                        "prompt": "Show what you know about main idea and details.",
                        "questions": [
                            {"q": "The main idea of a paragraph is…", "options": ["what the paragraph is mostly about", "the first sentence", "a list of facts"], "answer": "what the paragraph is mostly about", "explain": "The main idea is the most important message of the paragraph."},
                            {"q": "Details…", "options": ["support the main idea", "replace the main idea", "are always opinions"], "answer": "support the main idea", "explain": "Details are facts that back up the main idea."},
                            {"q": "A good place to look for the main idea is…", "options": ["the first or last sentence", "the longest word", "a picture"], "answer": "the first or last sentence", "explain": "Writers often state the main idea near the start or end."},
                        ],
                    },
                },
            ],
        },
    ],
}
