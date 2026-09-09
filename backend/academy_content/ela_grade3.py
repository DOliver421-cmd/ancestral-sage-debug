"""English Language Arts — Grade 3 (published core, fills Grade 3 gap: ela)."""

ELA_GRADE_3 = {
    "slug": "ela-grade-3",
    "title": "English Language Arts — Grade 3",
    "summary": "Fluency, comprehension, and beginning essay writing.",
    "description": "Third-grade ELA builds confident readers and writers — fluent reading, finding main ideas, and writing clear paragraphs with evidence.",
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["3"],
    "grade_label": "Grade 3",
    "status": "published",
    "audience": "Grade 3 (ages 8–9), Foundations track.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": ["Read grade-level texts fluently and recount key details.", "Determine main idea and explain how details support it.", "Write informative paragraphs with topic sentences and evidence."],
    "units": [
        {"slug": "reading-fluency", "title": "Reading Fluency and Comprehension", "summary": "Read smoothly and know what you read.", "order": 1, "lessons": [
            {"slug": "fluency-and-recounting", "title": "Fluency and Recounting", "order": 1, "minutes": 18, "summary": "Read smoothly and retell the important parts.", "learn": [{"type": "p", "text": "Fluent reading sounds like talking. Pause at commas, stop at periods, lift your voice for questions. After reading, recount — who, where, problem, key events, ending."}, {"type": "list", "items": ["Track with a finger if needed, then read in phrases.", "Ask: who was there? what happened? why does it matter?", "Retell in order without adding extra details."]}], "check": {"prompt": "Fluency and recount.", "questions": [{"q": "Fluent reading…", "options": ["sounds like talking", "sounds like random words", "never pauses"], "answer": "sounds like talking", "explain": "Fluency is smooth, paced reading."}, {"q": "Recounting means…", "options": ["retelling key details in order", "copying every word", "guessing the ending only"], "answer": "retelling key details in order", "explain": "Recount focuses on the important parts."}]}},
            {"slug": "main-idea-and-details", "title": "Main Idea and Supporting Details", "order": 2, "minutes": 18, "summary": "What the text is mostly about.", "learn": [{"type": "p", "text": "The main idea is what a section is mostly about. Details explain, describe, or prove the main idea. Ask: what do most details point to?"}, {"type": "example", "title": "Find it", "text": "If a paragraph gives three examples of how bees help gardens, the main idea is likely: Bees help gardens thrive."}], "check": {"prompt": "Main idea.", "questions": [{"q": "Supporting details…", "options": ["explain or prove the main idea", "hide the main idea", "are always pictures"], "answer": "explain or prove the main idea", "explain": "Details support the central point."}, {"q": "To find the main idea, look for…", "options": ["what most details point to", "one small detail alone", "only the last word"], "answer": "what most details point to", "explain": "Main idea is what the details center on."}]}},
        ]},
        {"slug": "writing-paragraphs", "title": "Writing Paragraphs with Evidence", "summary": "Claim, evidence, and language.", "order": 2, "lessons": [
            {"slug": "informative-paragraph", "title": "Informative Paragraphs", "order": 3, "minutes": 18, "summary": "Topic sentence, details, conclusion.", "learn": [{"type": "p", "text": "An informative paragraph teaches the reader. Start with a clear topic sentence, add 2–3 details with evidence, and close with a concluding sentence."}, {"type": "example", "title": "Frame", "text": "Topic: Bees help our food grow. Details: They carry pollen, they visit many flowers, they help fruit form. Conclusion: Protecting bees protects our food."}], "check": {"prompt": "Paragraph structure.", "questions": [{"q": "A topic sentence…", "options": ["states the main idea", "asks only questions", "repeats the last detail"], "answer": "states the main idea", "explain": "It tells the reader what the paragraph teaches."}, {"q": "A concluding sentence…", "options": ["wraps up the idea", "adds a new unrelated idea", "is always the longest"], "answer": "wraps up the idea", "explain": "It restates the idea clearly."}]}},
            {"slug": "language-and-editing", "title": "Language and Editing", "order": 4, "minutes": 15, "summary": "Sentences, word choice, and fixing.", "learn": [{"type": "p", "text": "Strong sentences start with a capital and end with correct punctuation. Use precise verbs and sensory details. Edit for completeness before sharing."}, {"type": "list", "items": ["Capitalize beginnings and proper names.", "End with . ? or ! correctly.", "Swap a weak verb (get → gather)."]}], "check": {"prompt": "Language.", "questions": [{"q": "Which sentence is complete?", "options": ["The garden grows tomatoes in summer.", "tomatoes in summer", "grows tomatoes"], "answer": "The garden grows tomatoes in summer.", "explain": "It has a subject and a verb and correct punctuation."}, {"q": "Which verb is more precise than 'get'?", "options": ["gather", "have", "do"], "answer": "gather", "explain": "Gather is specific and vivid."}]}},
        ]},
    ],
}
