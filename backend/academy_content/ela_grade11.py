"""ELA Grade 11 — American Literature & Rhetoric (published core)."""
ELA_GRADE_11 = {
    "slug": "ela-grade-11",
    "title": "English Language Arts — Grade 11",
    "summary": "American literature from founding documents to contemporary voices; rhetoric and research.",
    "description": "Grade 11 ELA traces American voices — founding documents, Harlem Renaissance, civil rights rhetoric, and contemporary literature — while building research and argument skills.",
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["11"],
    "grade_label": "Grade 11",
    "status": "published",
    "audience": "Grade 11 (ages 16-17)",
    "est_hours": 22,
    "passing_score": 80,
    "learning_objectives": [
        "Analyze American texts for theme, craft, and historical context.",
        "Evaluate rhetorical strategies in speeches and essays.",
        "Synthesize sources into a researched argument.",
    ],
    "units": [
        {"slug": "american-voices", "title": "American Voices", "summary": "Founding to modern.", "order": 1, "lessons": [
            {"slug": "founding-docs-grade11", "title": "Founding Documents", "order": 1, "minutes": 18, "summary": "Ideals and contradictions.", "learn": [{"type": "p", "text": "The Declaration and Constitution state ideals of liberty while the nation's economy relied on enslavement. Reading them closely shows both promise and contradiction — a tension Black writers have engaged for generations."}], "check": {"prompt": "Founding docs.", "questions": [{"q": "The Declaration's 'all men are created equal' was contested because", "options": ["the nation permitted slavery", "it was never published", "it only addressed farming"], "answer": "the nation permitted slavery", "explain": "The contradiction shaped American literature."}]}},
            {"slug": "harlem-renaissance-grade11", "title": "Harlem Renaissance", "order": 2, "minutes": 18, "summary": "Hughes, Hurston, McKay.", "learn": [{"type": "p", "text": "The Harlem Renaissance (1920s-30s) produced lasting American literature. Langston Hughes, Zora Neale Hurston, and Claude McKay wrote in distinct voices about Black life, joy, and resistance."}], "check": {"prompt": "Harlem Renaissance.", "questions": [{"q": "Hughes is known for", "options": ["blues-inflected poetry of Black life", "only scientific reports", "only translations"], "answer": "blues-inflected poetry of Black life", "explain": "Hughes centered everyday Black voice."}]}},
        ]},
        {"slug": "rhetoric-research-grade11", "title": "Rhetoric and Research", "summary": "Speeches and synthesis.", "order": 2, "lessons": [
            {"slug": "civil-rights-rhetoric-grade11", "title": "Civil Rights Rhetoric", "order": 3, "minutes": 18, "summary": "King, speeches, argument.", "learn": [{"type": "p", "text": "Speeches like King's Letter from Birmingham Jail use ethos, pathos, and logos together. Analyzing structure — repetition, allusion, and call to action — shows how rhetoric moves a nation."}], "check": {"prompt": "Rhetoric.", "questions": [{"q": "Letter from Birmingham Jail responds to", "options": ["white clergy urging patience", "a weather report", "a fictional story"], "answer": "white clergy urging patience", "explain": "King answers the call to wait."}]}},
            {"slug": "research-grade11", "title": "Research Paper", "order": 4, "minutes": 22, "summary": "Thesis, sources, citation.", "learn": [{"type": "p", "text": "A research paper makes a debatable claim, supports it with credible sources, and cites consistently so readers can verify."}], "check": {"prompt": "Research.", "questions": [{"q": "A strong thesis is", "options": ["debatable and specific", "vague and obvious", "copied verbatim"], "answer": "debatable and specific", "explain": "It can be argued and proved."}]}},
        ]},
    ],
}
