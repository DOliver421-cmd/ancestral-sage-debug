"""English Language Arts — Grade 4 (published core)."""

ELA_GRADE_4 = {
    "slug": "ela-grade-4",
    "title": "English Language Arts — Grade 4",
    "summary": "Close reading, text structure, and essay foundations.",
    "description": "Fourth-grade ELA deepens comprehension and writing: text structure, point of view, and well-organized essays with evidence.",
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["4"],
    "grade_label": "Grade 4",
    "status": "published",
    "audience": "Grade 4 (ages 9–10), Foundations track.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": ["Explain text structure and point of view.", "Compare information across texts.", "Write organized essays with evidence and editing."],
    "units": [
        {"slug": "reading-grade4", "title": "Reading: Structure and Perspective", "summary": "How texts are built and whose view they show.", "order": 1, "lessons": [
            {"slug": "text-structure-grade4", "title": "Text Structure", "order": 1, "minutes": 18, "summary": "Cause/effect, compare/contrast, sequence.", "learn": [{"type": "p", "text": "Authors organize information on purpose. Common structures are cause and effect, compare and contrast, problem and solution, and chronological sequence."}, {"type": "list", "items": ["Cause/effect: why something happened.", "Compare/contrast: similarities and differences.", "Sequence: order in time or steps."]}], "check": {"prompt": "Structure.", "questions": [{"q": "Cause and effect explains…", "options": ["why something happened and what resulted", "only a character name", "only a picture"], "answer": "why something happened and what resulted", "explain": "Cause is why; effect is what happened."}, {"q": "Compare and contrast shows…", "options": ["similarities and differences", "only the ending", "only dialogue"], "answer": "similarities and differences", "explain": "It puts two things side by side."}]}},
            {"slug": "point-of-view-grade4", "title": "Point of View", "order": 2, "minutes": 15, "summary": "First, second, and third person.", "learn": [{"type": "p", "text": "Point of view is who tells the story. First person uses I; third person uses he/she/they. Perspective shapes what the reader learns and believes."}, {"type": "example", "title": "Spot it", "text": "\"I hurried to the market\" is first person. \"She hurried to the market\" is third person."}], "check": {"prompt": "Point of view.", "questions": [{"q": "First-person narration uses…", "options": ["I and we", "he and she only", "they always"], "answer": "I and we", "explain": "First person speaks as the narrator."}, {"q": "Perspective matters because it…", "options": ["shapes what the reader learns", "never matters", "hides all facts"], "answer": "shapes what the reader learns", "explain": "Who tells the story shapes the view."}]}},
        ]},
        {"slug": "writing-essay", "title": "Writing: Essay with Evidence", "summary": "Introduction, reasons, evidence, conclusion.", "order": 2, "lessons": [
            {"slug": "essay-structure-grade4", "title": "Essay Structure", "order": 3, "minutes": 18, "summary": "Build a short essay.", "learn": [{"type": "p", "text": "An essay has an introduction with a claim, body paragraphs with reasons and evidence, and a conclusion that restates the idea with strength."}, {"type": "example", "title": "Outline", "text": "Introduction: Community gardens help neighborhoods. Body: They provide food, build relationships, beautify streets — each with evidence. Conclusion: Gardens nourish bodies and community."}], "check": {"prompt": "Essay parts.", "questions": [{"q": "An essay introduction should…", "options": ["state a clear claim", "list random facts", "hide the idea"], "answer": "state a clear claim", "explain": "It tells the reader the big idea."}, {"q": "Body paragraphs need…", "options": ["reasons and evidence", "only questions", "only pictures"], "answer": "reasons and evidence", "explain": "Evidence supports the claim."}]}},
            {"slug": "editing-grade4", "title": "Editing and Language", "order": 4, "minutes": 15, "summary": "Fix for clarity.", "learn": [{"type": "p", "text": "Edit for capital letters, punctuation, subject-verb agreement, and precise word choice. Reading aloud helps you hear errors."}, {"type": "list", "items": ["Check sentences are complete.", "Use commas after introductory phrases.", "Choose vivid verbs."]}], "check": {"prompt": "Editing.", "questions": [{"q": "Editing helps writing become…", "options": ["clear and correct", "shorter always", "less meaningful"], "answer": "clear and correct", "explain": "Editing improves clarity and correctness."}, {"q": "Reading aloud helps you…", "options": ["hear errors", "hide errors", "add errors"], "answer": "hear errors", "explain": "Hearing reveals awkward spots."}]}},
        ]},
    ],
}
