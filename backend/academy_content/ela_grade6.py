"""English Language Arts — Grade 6 (published core)."""

ELA_GRADE_6 = {
    "slug": "ela-grade-6",
    "title": "English Language Arts — Grade 6",
    "summary": "Analyzing literature and informational texts; argument writing.",
    "description": "Sixth-grade ELA strengthens close reading, comparing perspectives across texts, and writing structured arguments with evidence.",
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["6"],
    "grade_label": "Grade 6",
    "status": "published",
    "audience": "Grade 6 (ages 11–12), Foundations track.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": ["Analyze theme and point of view in literature.", "Compare claims and evidence across informational texts.", "Write arguments with reasons and relevant evidence."],
    "units": [
        {"slug": "reading-lit-info", "title": "Reading Literature & Information", "summary": "Theme, perspective, and evidence.", "order": 1, "lessons": [
            {"slug": "theme-and-development-grade6", "title": "Theme and How It Develops", "order": 1, "minutes": 18, "summary": "What a story teaches.", "learn": [{"type": "p", "text": "A theme is a message about life revealed through characters, plot, and imagery. Track how a theme is introduced and deepened across chapters."}, {"type": "example", "title": "Track theme", "text": "In a story about a community garden, perseverance grows as neighbors overcome setbacks together."}], "check": {"prompt": "Theme.", "questions": [{"q": "A theme is…", "options": ["a message about life revealed through the story", "only the setting", "only the title"], "answer": "a message about life revealed through the story", "explain": "Theme is a big idea the story explores."}, {"q": "To find theme, examine…", "options": ["how characters change and what they learn", "only the cover image", "only the author's name"], "answer": "how characters change and what they learn", "explain": "Character change reveals theme."}]}},
            {"slug": "comparing-texts-grade6", "title": "Comparing Claims Across Texts", "order": 2, "minutes": 18, "summary": "Two texts, one topic.", "learn": [{"type": "p", "text": "Informational texts make claims and support them with evidence. Comparing two texts on the same topic reveals bias, emphasis, and strength of evidence."}, {"type": "list", "items": ["Identify each author's claim.", "List the evidence given.", "Compare: which evidence is stronger?"]}], "check": {"prompt": "Compare texts.", "questions": [{"q": "A claim is…", "options": ["a statement the author tries to prove", "a random question", "only a fact"], "answer": "a statement the author tries to prove", "explain": "Claims require evidence."}, {"q": "Comparing evidence helps you…", "options": ["judge which argument is stronger", "ignore both texts", "copy one text fully"], "answer": "judge which argument is stronger", "explain": "Comparison builds critical thinking."}]}},
        ]},
        {"slug": "writing-argument-grade6", "title": "Writing Argument", "summary": "Reason and evidence.", "order": 2, "lessons": [
            {"slug": "argument-structure-grade6", "title": "Building an Argument", "order": 3, "minutes": 18, "summary": "Claim, reasons, evidence, counterclaim.", "learn": [{"type": "p", "text": "An argument states a claim, gives reasons supported by evidence, acknowledges a counterclaim fairly, and closes with a strong conclusion."}, {"type": "example", "title": "Outline", "text": "Claim: Schools should have community mentorship. Reasons: belonging, skills, networks — each with evidence. Counterclaim addressed respectfully."}], "check": {"prompt": "Argument.", "questions": [{"q": "A counterclaim is…", "options": ["an opposing view you acknowledge fairly", "repeating your claim louder", "ignoring other views"], "answer": "an opposing view you acknowledge fairly", "explain": "Fair acknowledgment builds credibility."}, {"q": "Evidence should be…", "options": ["relevant and credible", "unrelated and vague", "only opinions"], "answer": "relevant and credible", "explain": "Good evidence fits the claim and comes from trustworthy sources."}]}},
            {"slug": "language-editing-grade6", "title": "Language and Revision", "order": 4, "minutes": 15, "summary": "Style and correctness.", "learn": [{"type": "p", "text": "Choose precise nouns and verbs, vary sentence length, and fix fragment and run-on sentences. Revise for clarity, not just correctness."}, {"type": "list", "items": ["Swap vague verbs for vivid ones.", "Use commas for clarity.", "Read aloud to catch flow."]}], "check": {"prompt": "Revision.", "questions": [{"q": "Revising means…", "options": ["improving ideas and flow", "only fixing spelling", "deleting everything"], "answer": "improving ideas and flow", "explain": "Revision improves meaning."}, {"q": "A fragment is…", "options": ["an incomplete sentence", "a complete sentence", "a paragraph"], "answer": "an incomplete sentence", "explain": "Fragments lack a subject or verb or full thought."}]}},
        ]},
    ],
}
