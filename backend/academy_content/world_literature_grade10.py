"""World Literature — Grade 10 (full published course)."""

WORLD_LITERATURE_GRADE_10 = {
    "slug": "world-literature-grade-10",
    "title": "World Literature",
    "summary": "Global literary traditions, analysis, and academic writing.",
    "description": (
        "World Literature explores stories, poems, and essays from diverse cultures. "
        "Students read works from Africa, Asia, Latin America, and the Middle East, "
        "analyze literary elements, and write analytical essays with textual evidence."
    ),
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "scholar",
    "tracks": ["scholar"],
    "grades": ["10"],
    "grade_label": "Grade 10",
    "status": "published",
    "audience": "Grade 10 (ages 15–16), Scholar track.",
    "est_hours": 26,
    "passing_score": 80,
    "learning_objectives": [
        "Identify literary elements across world texts.",
        "Analyze how culture and context shape literature.",
        "Write analytical paragraphs with a clear thesis and evidence.",
        "Compare themes across different literary traditions.",
        "Research and cite sources using MLA style.",
    ],
    "units": [
        {
            "slug": "global-traditions",
            "title": "Global Literary Traditions",
            "summary": "Read and analyze works from multiple cultures.",
            "order": 1,
            "lessons": [
                {
                    "slug": "introduction-to-world-literature",
                    "title": "Introduction to World Literature",
                    "order": 1,
                    "minutes": 18,
                    "summary": "What is world literature and why does it matter?",
                    "learn": [
                        {"type": "p", "text": "World literature includes works from many cultures and time periods. Reading widely builds empathy and helps us see universal human concerns — love, loss, justice, identity — through different lenses."},
                        {"type": "list", "items": [
                            "Oral tradition: stories passed down by word of mouth.",
                            "Epic: long narrative poems about heroes.",
                            "Novella/novel: extended prose fiction.",
                            "Poetry: compressed language with rhythm and imagery.",
                        ]},
                        {"type": "example", "title": "The Epic of Gilgamesh", "text": "One of the oldest known stories, from ancient Mesopotamia. It explores friendship, mortality, and the search for meaning."},
                    ],
                    "check": {
                        "prompt": "Show what you know about world literature.",
                        "questions": [
                            {"q": "What is a common theme across many world literatures?", "options": ["the quest for meaning", "sports", "technology"], "answer": "the quest for meaning", "explain": "Human concerns such as love, loss, and purpose appear in stories worldwide."},
                            {"q": "Which form is typically passed down orally?", "options": ["epic poetry", "a novel", "a textbook"], "answer": "epic poetry", "explain": "Many epics were first shared through oral tradition before being written."},
                        ],
                    },
                },
                {
                    "slug": "literary-analysis",
                    "title": "Literary Analysis Basics",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Close reading, theme, and literary devices.",
                    "learn": [
                        {"type": "p", "text": "Literary analysis asks 'What is the author doing and how?' You examine plot, character, setting, point of view, symbolism, and tone to support an argument."},
                        {"type": "list", "items": [
                            "Theme: the central message or insight about life.",
                            "Symbol: an object that represents a larger idea.",
                            "Tone: the author's attitude toward the subject.",
                            "Close reading: re-reading and annotating key passages.",
                        ]},
                        {"type": "example", "title": "Analyzing a symbol", "text": "In many stories, light represents hope and darkness represents fear. If the author uses light when a character is safe, the symbol reinforces the theme."},
                        {"type": "activity", "title": "Annotate a passage", "text": "Read a short poem from another culture. Circle images, underline repeated words, and write two questions in the margin."},
                    ],
                    "check": {
                        "prompt": "Show what you know about literary analysis.",
                        "questions": [
                            {"q": "A theme is…", "options": ["the central message about life", "the physical setting", "the number of characters"], "answer": "the central message about life", "explain": "Theme is the insight about life that the author explores."},
                            {"q": "A symbol is…", "options": ["an object representing a larger idea", "the main character", "the title"], "answer": "an object representing a larger idea", "explain": "Symbols carry meaning beyond their literal use."},
                        ],
                    },
                },
                {
                    "slug": "academic-writing",
                    "title": "Academic Writing and MLA",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Thesis statements, paragraphs, and MLA citations.",
                    "learn": [
                        {"type": "p", "text": "Academic writing in literature begins with a clear thesis: one sentence stating your argument about the text. Body paragraphs use the TIQQEL structure: Topic sentence, Introduce quote, Quote, Explain, Link."},
                        {"type": "list", "items": [
                            "Thesis: a claim about the text that others could disagree with.",
                            "Evidence: direct quotes and paraphrases with page numbers.",
                            "MLA in-text citation: (Author page).",
                            "Works Cited page lists all sources alphabetically.",
                        ]},
                        {"type": "example", "title": "Sample thesis", "text": "In 'The Lottery,' Shirley Jackson uses ordinary setting details to build horror, showing that evil can hide in daily life."},
                    ],
                    "check": {
                        "prompt": "Show what you know about academic writing.",
                        "questions": [
                            {"q": "A thesis statement is…", "options": ["a claim you will prove with evidence", "a summary of the plot", "a list of characters"], "answer": "a claim you will prove with evidence", "explain": "A thesis makes an arguable claim, not just a fact."},
                            {"q": "In MLA, a parenthetical citation looks like…", "options": ["(Author page)", "[Author]", "footnote"], "answer": "(Author page)", "explain": "MLA in-text citations are brief and point to the Works Cited."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "comparative-study",
            "title": "Comparative Study",
            "summary": "Compare themes and styles across cultures.",
            "order": 2,
            "lessons": [
                {
                    "slug": "theme-comparison",
                    "title": "Theme Comparison Across Cultures",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Identify shared and contrasting themes.",
                    "learn": [
                        {"type": "p", "text": "Comparing texts from different cultures reveals both universal concerns and unique cultural expressions. You might compare how two societies treat heroes, how they explain suffering, or how they view family duty."},
                        {"type": "list", "items": [
                            "Choose texts with a shared theme (e.g., coming of age).",
                            "Note similarities and differences in how each culture treats the theme.",
                            "Use specific evidence from both texts.",
                            "Conclude what the comparison reveals about human experience.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about theme comparison.",
                        "questions": [
                            {"q": "A good theme comparison looks at…", "options": ["similarities and differences across texts", "only one text", "the author's biography"], "answer": "similarities and differences across texts", "explain": "Comparison examines how different texts treat the same idea."},
                        ],
                    },
                },
                {
                    "slug": "research-and-sources",
                    "title": "Research and Sources",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Find, evaluate, and cite scholarly sources.",
                    "learn": [
                        {"type": "p", "text": "Literary research means asking a question, finding credible sources, and building an argument. Evaluate sources for authority, accuracy, and bias."},
                        {"type": "list", "items": [
                            "Use library databases and academic journals.",
                            "Take careful notes with page numbers.",
                            "Cite every idea that is not your own.",
                            "Avoid plagiarism by quoting, paraphrasing, and citing correctly.",
                        ]},
                        {"type": "activity", "title": "Source evaluation", "text": "Find one article about a world author you have read. Evaluate whether the source is credible and write a one-paragraph summary."},
                    ],
                    "check": {
                        "prompt": "Show what you know about research and sources.",
                        "questions": [
                            {"q": "What should you check when evaluating a source?", "options": ["authority and accuracy", "font size", "number of pages"], "answer": "authority and accuracy", "explain": "Credible sources are written by experts and are factually accurate."},
                        ],
                    },
                },
            ],
        },
    ],
}
