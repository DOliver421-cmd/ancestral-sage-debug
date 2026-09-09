"""English Language Arts — Grade 7 (published core)."""

ELA_GRADE_7 = {
    "slug": "ela-grade-7",
    "title": "English Language Arts — Grade 7",
    "summary": "Analyzing craft, argument, and research writing.",
    "description": "Seventh-grade ELA deepens literary analysis, argument evaluation, and research writing grounded in evidence and voice.",
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["7"],
    "grade_label": "Grade 7",
    "status": "published",
    "audience": "Grade 7 (ages 12–13), Foundations track.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": ["Analyze how authors craft language and structure to affect readers.", "Evaluate arguments for reasoning and evidence.", "Conduct short research and write with citation."],
    "units": [
        {"slug": "literature-craft", "title": "Literature: Craft and Meaning", "summary": "How writers shape meaning.", "order": 1, "lessons": [
            {"slug": "craft-and-structure-grade7", "title": "Craft and Structure", "order": 1, "minutes": 18, "summary": "Word choice, imagery, and structure.", "learn": [{"type": "p", "text": "Writers choose words that carry history and feeling. Structure — flashback, dialogue, repetition — guides the reader's attention and emotion."}, {"type": "list", "items": ["Figurative language builds meaning.", "Repetition can honor or emphasize.", "Structure reveals perspective."]}], "check": {"prompt": "Craft.", "questions": [{"q": "Repetition in a text often…", "options": ["emphasizes an idea", "hides the idea", "means nothing"], "answer": "emphasizes an idea", "explain": "Repeated language signals importance."}, {"q": "Word choice matters because words carry…", "options": ["history and feeling", "no meaning", "only numbers"], "answer": "history and feeling", "explain": "Connotation shapes impact."}]}},
            {"slug": "perspective-grade7", "title": "Perspective and Point of View", "order": 2, "minutes": 15, "summary": "Whose view shapes the story?", "learn": [{"type": "p", "text": "Point of view decides what the reader can know and feel. Comparing two perspectives on the same event deepens understanding and empathy."}, {"type": "activity", "title": "Rewrite perspective", "text": "Retell a scene from a different character's point of view. What changes?"}], "check": {"prompt": "Perspective.", "questions": [{"q": "Changing point of view can…", "options": ["change what the reader knows and feels", "never change anything", "only change punctuation"], "answer": "change what the reader knows and feels", "explain": "Narrator position shapes knowledge."}, {"q": "Comparing perspectives helps you…", "options": ["understand more deeply", "forget the story", "ignore evidence"], "answer": "understand more deeply", "explain": "Multiple lenses enrich meaning."}]}},
        ]},
        {"slug": "argument-research", "title": "Argument and Research", "summary": "Reason, sources, and voice.", "order": 2, "lessons": [
            {"slug": "evaluating-arguments-grade7", "title": "Evaluating Arguments", "order": 3, "minutes": 18, "summary": "Reasoning and evidence.", "learn": [{"type": "p", "text": "A strong argument has a clear claim, relevant reasons, credible evidence, and awareness of counterclaims. Weak arguments use emotion alone or misrepresent sources."}, {"type": "list", "items": ["Claim + reasons + evidence + counterclaim response.", "Credible sources cite methods and data.", "Sound reasoning avoids false cause and hasty conclusions."]}], "check": {"prompt": "Arguments.", "questions": [{"q": "Strong evidence is…", "options": ["relevant and from a credible source", "unrelated and vague", "only personal opinion"], "answer": "relevant and from a credible source", "explain": "Relevance and credibility matter."}, {"q": "Addressing a counterclaim…", "options": ["shows fairness and strengthens credibility", "always weakens your argument", "should be ignored"], "answer": "shows fairness and strengthens credibility", "explain": "Fair engagement builds trust."}]}},
            {"slug": "research-and-citation-grade7", "title": "Research and Citation", "order": 4, "minutes": 18, "summary": "Find, vet, and credit sources.", "learn": [{"type": "p", "text": "Research begins with a question. Use library and trusted sites, vet authors and dates, take notes in your own words, and cite sources so readers can verify."}, {"type": "list", "items": ["Question → sources → notes → outline → draft.", "Vet: who wrote it, when, what evidence.", "Cite: author, title, date, where you found it."]}], "check": {"prompt": "Research.", "questions": [{"q": "Vetting a source includes checking…", "options": ["author, date, and evidence", "only the font size", "only the cover color"], "answer": "author, date, and evidence", "explain": "Credibility requires who, when, and how."}, {"q": "Citing sources helps readers…", "options": ["verify your claims", "forget your claims", "hide your claims"], "answer": "verify your claims", "explain": "Citation enables verification."}]}},
        ]},
    ],
}
