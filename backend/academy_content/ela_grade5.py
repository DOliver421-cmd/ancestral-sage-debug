"""English Language Arts — Grade 5 (full published course)."""

ELA_GRADE_5 = {
    "slug": "ela-grade-5",
    "title": "English Language Arts — Grade 5",
    "summary": "Reading across genres, text evidence, and structured writing.",
    "description": (
        "Fifth-grade ELA sharpens reading comprehension, vocabulary, and writing. "
        "Students read a range of genres, learn to cite textual evidence, "
        "and write clear, organized paragraphs and essays. Lessons include "
        "close-reading routines, vocabulary strategies, and writing workshops."
    ),
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["5"],
    "grade_label": "Grade 5",
    "status": "published",
    "audience": "Grade 5 (ages 10–11), Foundations track.",
    "est_hours": 24,
    "passing_score": 80,
    "learning_objectives": [
        "Identify elements of fiction and nonfiction texts.",
        "Use textual evidence to support inferences and claims.",
        "Determine meanings of unknown words using context and word parts.",
        "Write clear narrative and informative paragraphs.",
        "Edit for grammar, punctuation, and sentence structure.",
    ],
    "units": [
        {
            "slug": "reading-comprehension",
            "title": "Reading Comprehension",
            "summary": "Read closely, infer meaning, and find evidence.",
            "order": 1,
            "lessons": [
                {
                    "slug": "reading-genres",
                    "title": "Reading Across Genres",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Identify fiction, nonfiction, poetry, and drama features.",
                    "learn": [
                        {"type": "p", "text": "Genres are categories of texts. Fiction tells made-up stories with characters, setting, and plot. Nonfiction gives facts about real things. Poetry uses rhythm and imagery. Drama is written to be performed."},
                        {"type": "list", "items": [
                            "Fiction: characters, setting, plot, problem and solution.",
                            "Nonfiction: table of contents, headings, captions, glossary.",
                            "Poetry: stanzas, rhythm, rhyme, figurative language.",
                            "Drama: characters, dialogue, stage directions, acts and scenes.",
                        ]},
                        {"type": "activity", "title": "Genre sort", "text": "Collect short texts or book covers. Sort them into fiction, nonfiction, poetry, and drama. Explain your reasoning."},
                    ],
                    "check": {
                        "prompt": "Show what you know about reading genres.",
                        "questions": [
                            {"q": "Which genre is written to be performed on stage?", "options": ["drama", "nonfiction", "poetry"], "answer": "drama", "explain": "Drama includes dialogue and stage directions for actors."},
                            {"q": "Which text feature is most common in nonfiction?", "options": ["table of contents", "stanzas", "dialogue"], "answer": "table of contents", "explain": "Nonfiction books use tables of contents to help readers find information."},
                            {"q": "A story with made-up characters and events is…", "options": ["fiction", "nonfiction", "a biography"], "answer": "fiction", "explain": "Fiction tells imaginary stories with characters and events."},
                        ],
                    },
                },
                {
                    "slug": "text-evidence-and-inference",
                    "title": "Text Evidence and Inference",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Use details from the text to support inferences.",
                    "learn": [
                        {"type": "p", "text": "An inference is a smart guess based on clues in the text plus what you already know. To support an inference, you must quote or paraphrase exact details from the text."},
                        {"type": "example", "title": "Inference practice", "text": "Text: 'Maria hugged her jacket tight and looked at the gray sky.' Inference: Maria is cold. Evidence: she hugged her jacket and the sky was gray."},
                        {"type": "tip", "text": "Always use the phrase 'The author says…' or 'The text states…' when giving evidence. Then explain how that detail supports your idea."},
                    ],
                    "check": {
                        "prompt": "Show what you know about text evidence and inference.",
                        "questions": [
                            {"q": "Which sentence best supports the inference that a character is scared?", "options": ["'Her hands shook as she reached for the door.'", "'She ate a sandwich.'", "'The sun was bright.'"], "answer": "'Her hands shook as she reached for the door.'", "explain": "Shaking hands suggest fear or nervousness."},
                            {"q": "An inference is…", "options": ["a guess based on text clues and prior knowledge", "a fact stated directly in the text", "a question the reader asks"], "answer": "a guess based on text clues and prior knowledge", "explain": "Inferences combine what the text says with what you already know."},
                        ],
                    },
                },
                {
                    "slug": "vocabulary-strategies",
                    "title": "Vocabulary Strategies",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Use context clues, roots, and reference materials.",
                    "learn": [
                        {"type": "p", "text": "Good readers figure out unknown words by using clues in the surrounding text. They also know common Greek and Latin roots."},
                        {"type": "list", "items": [
                            "Context clues: words before and after the unknown word.",
                            "Roots: 'bio' means life, 'graph' means write, 'tele' means far.",
                            "Reference materials: dictionary, glossary, thesaurus.",
                        ]},
                        {"type": "activity", "title": "Root word hunt", "text": "Find five words with the root 'bio' in a book or online. Write each word and its meaning."},
                    ],
                    "check": {
                        "prompt": "Show what you know about vocabulary strategies.",
                        "questions": [
                            {"q": "The root 'tele' means…", "options": ["far", "life", "write"], "answer": "far", "explain": "Tele means far, as in telephone and television."},
                            {"q": "If you do not know a word, which clue is best?", "options": ["the words around it", "the cover of the book", "the font size"], "answer": "the words around it", "explain": "Context clues in the surrounding text often reveal meaning."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "writing-and-language",
            "title": "Writing and Language",
            "summary": "Paragraph structure, grammar, and editing.",
            "order": 2,
            "lessons": [
                {
                    "slug": "structured-writing",
                    "title": "Structured Writing: Paragraphs",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Write focused paragraphs with topic sentences and details.",
                    "learn": [
                        {"type": "p", "text": "A strong paragraph has a topic sentence, supporting details, and a concluding sentence. The topic sentence states the main idea. Details explain or give examples. The conclusion wraps up."},
                        {"type": "example", "title": "Sample paragraph", "text": "Topic sentence: 'Recess helps students learn better.' Supporting details: 'Movement increases blood flow to the brain. Social play builds communication skills. Fresh air improves mood.' Conclusion: 'Recess is an important part of the school day.'"},
                        {"type": "activity", "title": "Paragraph puzzle", "text": "Write a paragraph about your favorite animal. Include a topic sentence, three supporting details, and a concluding sentence."},
                    ],
                    "check": {
                        "prompt": "Show what you know about structured paragraphs.",
                        "questions": [
                            {"q": "What is the main job of a topic sentence?", "options": ["to state the main idea of the paragraph", "to give an example", "to end the paragraph"], "answer": "to state the main idea of the paragraph", "explain": "The topic sentence tells the reader what the paragraph is about."},
                            {"q": "Which sentence would be a good topic sentence for a paragraph about winter?", "options": ["Winter brings cold weather and fun activities.", "You can make a snowman.", "Snow is cold."], "answer": "Winter brings cold weather and fun activities.", "explain": "This sentence states a main idea that can be supported with details."},
                        ],
                    },
                },
                {
                    "slug": "grammar-and-punctuation",
                    "title": "Grammar and Punctuation",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Parts of speech, sentence types, and punctuation rules.",
                    "learn": [
                        {"type": "p", "text": "Sentences are built from parts of speech. Nouns name people, places, and things. Verbs show action or state. Adjectives describe nouns. Adverbs describe verbs, adjectives, or other adverbs."},
                        {"type": "list", "items": [
                            "Noun: dog, city, happiness.",
                            "Verb: runs, is, thinks.",
                            "Adjective: happy, blue, tall.",
                            "Adverb: quickly, very, quietly.",
                            "Use periods for statements, question marks for questions, and exclamation points for strong feeling.",
                        ]},
                        {"type": "activity", "title": "Sentence surgery", "text": "Take a short, boring sentence. Add an adjective, an adverb, and a strong verb to make it exciting."},
                    ],
                    "check": {
                        "prompt": "Show what you know about grammar and punctuation.",
                        "questions": [
                            {"q": "Which word is a verb?", "options": ["jumps", "table", "blue"], "answer": "jumps", "explain": "Jumps shows action, so it is a verb."},
                            {"q": "Which punctuation ends a question?", "options": ["?", "!", "."], "answer": "?", "explain": "A question mark signals that a sentence is asking something."},
                            {"q": "Which word describes a noun?", "options": ["adjective", "adverb", "pronoun"], "answer": "adjective", "explain": "Adjectives describe or modify nouns."},
                        ],
                    },
                },
            ],
        },
    ],
}
