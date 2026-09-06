"""Adult Education Language Arts (HSE preparation — full published course)."""

ADULT_ED_HSE_ELA = {
    "slug": "adult-ed-hse-ela",
    "title": "Adult Education Language Arts",
    "summary": "Reading comprehension, vocabulary, grammar, writing, argument, evidence, and literary analysis.",
    "description": (
        "This comprehensive adult-education language-arts course prepares learners "
        "for high-school equivalency reading and writing tests and for real-world "
        "communication. Lessons cover reading strategies, vocabulary, grammar, "
        "paragraph and essay structure, argumentation, and literary analysis."
    ),
    "subject": "adult_ed",
    "subject_label": "Adult Education",
    "track": "adult_ed",
    "tracks": ["adult_ed"],
    "grades": ["adult"],
    "grade_label": "Adult",
    "status": "published",
    "audience": "Adult learners preparing for HSE/GED language arts or workplace communication.",
    "est_hours": 36,
    "passing_score": 80,
    "learning_objectives": [
        "Use active reading strategies to understand complex texts.",
        "Determine word meanings from context, affixes, and roots.",
        "Apply grammar, punctuation, and sentence structure rules.",
        "Write focused paragraphs and multi-paragraph essays.",
        "Construct arguments supported by textual evidence.",
        "Analyze literary elements in fiction and nonfiction.",
    ],
    "units": [
        {
            "slug": "reading-and-vocabulary",
            "title": "Reading and Vocabulary",
            "summary": "Close reading, inference, and word-learning strategies.",
            "order": 1,
            "lessons": [
                {
                    "slug": "active-reading-strategies",
                    "title": "Active Reading Strategies",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Preview, annotate, question, and summarize.",
                    "learn": [
                        {"type": "p", "text": "Active reading means interacting with the text. Preview headings and images before reading. Annotate by underlining key ideas and writing margin notes. Pause to ask questions. Summarize each paragraph in your own words."},
                        {"type": "list", "items": [
                            "Preview: look at title, headings, and pictures.",
                            "Annotate: underline, circle, and margin-note.",
                            "Question: turn headings into questions and answer them.",
                            "Summarize: restate each section in one sentence.",
                        ]},
                        {"type": "activity", "title": "Read and annotate", "text": "Take a short news article. Preview it, annotate it, and write a three-sentence summary."},
                    ],
                    "check": {
                        "prompt": "Show what you know about active reading.",
                        "questions": [
                            {"q": "Which is an active reading strategy?", "options": ["annotating the text", "skimming without notes", "reading while distracted"], "answer": "annotating the text", "explain": "Active reading involves marking and interacting with the text."},
                            {"q": "Summarizing means…", "options": ["restating the main ideas in your own words", "copying the text", "skipping the ending"], "answer": "restating the main ideas in your own words", "explain": "Summaries compress ideas without copying exact words."},
                        ],
                    },
                },
                {
                    "slug": "vocabulary-in-context",
                    "title": "Vocabulary in Context",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Use context clues, affixes, and reference tools.",
                    "learn": [
                        {"type": "p", "text": "Strong readers figure out unknown words from surrounding text. They also know common prefixes, suffixes, and roots."},
                        {"type": "list", "items": [
                            "Prefix: un- (not), re- (again), pre- (before).",
                            "Suffix: -less (without), -tion (state of), -able (can be).",
                            "Root: port (carry), struct (build), spect (look).",
                            "Use a dictionary to confirm guesses and learn pronunciation.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about vocabulary.",
                        "questions": [
                            {"q": "The prefix 'un-' means…", "options": ["not", "again", "before"], "answer": "not", "explain": "Un- reverses meaning: unkind = not kind."},
                            {"q": "If you do not know a word, a good first step is…", "options": ["read the surrounding sentences", "skip it forever", "guess randomly"], "answer": "read the surrounding sentences", "explain": "Context clues often reveal meaning without a dictionary."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "writing-and-grammar",
            "title": "Writing and Grammar",
            "summary": "Paragraphs, essays, grammar, and punctuation.",
            "order": 2,
            "lessons": [
                {
                    "slug": "paragraph-and-essay-structure",
                    "title": "Paragraph and Essay Structure",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Topic sentences, support, transitions, and conclusions.",
                    "learn": [
                        {"type": "p", "text": "A paragraph has one main idea. An essay has an introduction, body paragraphs, and a conclusion. Each body paragraph needs a topic sentence, evidence, and a wrap-up."},
                        {"type": "list", "items": [
                            "Introduction: hook, background, thesis.",
                            "Body: topic sentence + evidence + explanation.",
                            "Transitions: however, furthermore, for example.",
                            "Conclusion: restate thesis in new words and end with a final thought.",
                        ]},
                        {"type": "example", "title": "Sample outline", "text": "Thesis: Learning a trade offers financial stability faster than a four-year degree. Body 1: earning potential. Body 2: lower training cost. Body 3: high demand."},
                    ],
                    "check": {
                        "prompt": "Show what you know about paragraph and essay structure.",
                        "questions": [
                            {"q": "The thesis states…", "options": ["the main argument of the essay", "a personal story", "the conclusion"], "answer": "the main argument of the essay", "explain": "The thesis tells the reader what you will prove."},
                            {"q": "A good transition shows…", "options": ["how ideas connect", "the end of the essay", "the font"], "answer": "how ideas connect", "explain": "Transitions guide the reader through your logic."},
                        ],
                    },
                },
                {
                    "slug": "grammar-and-punctuation",
                    "title": "Grammar and Punctuation",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Parts of speech, sentence structure, and punctuation rules.",
                    "learn": [
                        {"type": "p", "text": "Grammar is the system that makes sentences clear. Punctuation marks organize ideas and show relationships between clauses."},
                        {"type": "list", "items": [
                            "Complete sentence: subject + verb + complete thought.",
                            "Fragment: missing subject or verb.",
                            "Run-on: two complete thoughts without proper punctuation.",
                            "Semicolon joins closely related independent clauses.",
                        ]},
                        {"type": "activity", "title": "Fix the sentences", "text": "Rewrite these fragments and run-ons as complete, correct sentences."},
                    ],
                    "check": {
                        "prompt": "Show what you know about grammar and punctuation.",
                        "questions": [
                            {"q": "Which is a complete sentence?", "options": ["The dog barked.", "Barked loudly the.", "The dog."], "answer": "The dog barked.", "explain": "A complete sentence has a subject, verb, and complete thought."},
                            {"q": "A semicolon is used to…", "options": ["join two related independent clauses", "end a sentence", "show possession"], "answer": "join two related independent clauses", "explain": "Semicolons connect complete thoughts that are closely related."},
                        ],
                    },
                },
                {
                    "slug": "argument-and-evidence",
                    "title": "Argument and Evidence",
                    "order": 5,
                    "minutes": 20,
                    "summary": "Claims, reasons, evidence, and counterarguments.",
                    "learn": [
                        {"type": "p", "text": "An argument makes a claim and supports it with reasons and evidence. Address counterarguments to strengthen credibility."},
                        {"type": "list", "items": [
                            "Claim: the position you are arguing.",
                            "Reason: the general principle behind your claim.",
                            "Evidence: facts, statistics, quotes, or examples.",
                            "Counterargument: an opposing view you explain and refute.",
                        ]},
                        {"type": "example", "title": "Argument paragraph", "text": "Claim: Apprenticeships should be free. Reason: removing cost barriers opens opportunity. Evidence: data showing higher completion rates when tuition is waived."},
                    ],
                    "check": {
                        "prompt": "Show what you know about argument and evidence.",
                        "questions": [
                            {"q": "In an argument, evidence is…", "options": ["the facts that support the claim", "the main point", "an opposing view"], "answer": "the facts that support the claim", "explain": "Evidence proves or illustrates a reason."},
                            {"q": "A counterargument is…", "options": ["an opposing position you address", "your main claim", "a synonym"], "answer": "an opposing position you address", "explain": "Acknowledging opposing views makes your argument stronger."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "literary-and-informational-text",
            "title": "Literary and Informational Text",
            "summary": "Analyze fiction and nonfiction texts.",
            "order": 3,
            "lessons": [
                {
                    "slug": "informational-text-analysis",
                    "title": "Informational Text Analysis",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Main idea, text structure, and graphic features.",
                    "learn": [
                        {"type": "p", "text": "Informational texts teach facts. They use structures such as cause/effect, compare/contrast, problem/solution, and sequence. Headings, captions, and diagrams help readers find information quickly."},
                        {"type": "list", "items": [
                            "Main idea: what the passage is mostly about.",
                            "Supporting details: facts that prove the main idea.",
                            "Text structures: chronological, cause/effect, compare/contrast.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about informational text.",
                        "questions": [
                            {"q": "The main idea of a passage is…", "options": ["what the passage is mostly about", "the first sentence", "a random detail"], "answer": "what the passage is mostly about", "explain": "The main idea is the central point the author wants you to understand."},
                            {"q": "Which text structure explains reasons and results?", "options": ["cause/effect", "problem/solution", "compare/contrast"], "answer": "cause/effect", "explain": "Cause/effect shows why something happened and what happened because of it."},
                        ],
                    },
                },
                {
                    "slug": "literary-analysis-basics",
                    "title": "Literary Analysis Basics",
                    "order": 7,
                    "minutes": 20,
                    "summary": "Plot, character, setting, theme, and point of view.",
                    "learn": [
                        {"type": "p", "text": "Literary analysis looks at how authors use literary elements to create meaning. Plot is the sequence of events. Character is who acts in the story. Setting is when and where. Theme is the message about life."},
                        {"type": "list", "items": [
                            "Plot: exposition, rising action, climax, falling action, resolution.",
                            "Character: protagonist (main), antagonist (opposes).",
                            "Setting: time and place.",
                            "Theme: the universal message about life or human nature.",
                        ]},
                        {"type": "example", "title": "Theme example", "text": "In a story where a character learns that honesty matters more than winning, the theme is 'Honesty is more important than success.'"},
                    ],
                    "check": {
                        "prompt": "Show what you know about literary analysis.",
                        "questions": [
                            {"q": "The sequence of events in a story is the…", "options": ["plot", "theme", "setting"], "answer": "plot", "explain": "Plot is the ordered sequence of events in a narrative."},
                            {"q": "The main character in a story is the…", "options": ["protagonist", "antagonist", "narrator"], "answer": "protagonist", "explain": "The protagonist is the central character, often the hero."},
                        ],
                    },
                },
            ],
        },
    ],
}
