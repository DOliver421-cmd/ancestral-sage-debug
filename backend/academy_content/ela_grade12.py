"""English Language Arts — Grade 12 (published core, fills Grade 12 gap: ela)."""

ELA_GRADE_12 = {
    "slug": "ela-grade-12",
    "title": "English Language Arts — Grade 12",
    "summary": "Advanced analysis, research synthesis, and capstone writing.",
    "description": "Twelfth-grade ELA culminates in sophisticated reading and writing — synthesizing sources, crafting voice, and producing a capstone research essay.",
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["12"],
    "grade_label": "Grade 12",
    "status": "published",
    "audience": "Grade 12 (ages 17–18), Scholar track; capstone year.",
    "est_hours": 22,
    "passing_score": 80,
    "learning_objectives": ["Analyze complex texts for craft, structure, and argument.", "Synthesize multiple sources into a coherent claim.", "Produce a capstone research essay with citation and revision."],
    "units": [
        {"slug": "advanced-reading", "title": "Advanced Reading", "summary": "Craft and argument.", "order": 1, "lessons": [
            {"slug": "literary-craft-grade12", "title": "Literary Craft", "order": 1, "minutes": 18, "summary": "How language builds meaning.", "learn": [{"type": "p", "text": "In literature, choices about word, image, and form carry history. Close reading traces how a text honors or challenges the communities it depicts."}, {"type": "list", "items": ["Track motifs across chapters.", "Note how structure shapes time and power.", "Consider whose view is centered."]}], "check": {"prompt": "Craft.", "questions": [{"q": "A motif is…", "options": ["a recurring image or idea", "only a title", "only a footnote"], "answer": "a recurring image or idea", "explain": "Motifs repeat and gather meaning."}, {"q": "Structure shapes…", "options": ["time, emphasis, and power", "nothing at all", "only page numbers"], "answer": "time, emphasis, and power", "explain": "Order guides attention."}]}},
            {"slug": "rhetoric-grade12", "title": "Rhetoric and Argument", "order": 2, "minutes": 18, "summary": "Claims that persuade justly.", "learn": [{"type": "p", "text": "Rhetoric is reasoning with an audience in mind. Ethos (credibility), pathos (emotion), and logos (logic) work together — but logic and evidence must lead, and emotion must be honored honestly."}, {"type": "list", "items": ["Claims need reasons and credible evidence.", "Address counterclaims fairly.", "Cite so readers can verify."]}], "check": {"prompt": "Rhetoric.", "questions": [{"q": "Ethos appeals to…", "options": ["credibility", "only emotion", "only money"], "answer": "credibility", "explain": "Ethos is trust based on character and expertise."}, {"q": "Strong arguments address counterclaims by…", "options": ["acknowledging them fairly and responding", "ignoring them", "mocking them"], "answer": "acknowledging them fairly and responding", "explain": "Fair engagement builds trust."}]}},
        ]},
        {"slug": "capstone", "title": "Capstone Research and Writing", "summary": "Synthesis and voice.", "order": 2, "lessons": [
            {"slug": "synthesis-grade12", "title": "Synthesizing Sources", "order": 3, "minutes": 18, "summary": "Combine ideas into one claim.", "learn": [{"type": "p", "text": "Synthesis compares sources, finds agreements and tensions, and builds your own claim that respects the sources while adding insight."}, {"type": "list", "items": ["Map each source's claim and evidence.", "Note where sources agree, disagree, or complement.", "Your claim should be provable and specific."]}], "check": {"prompt": "Synthesis.", "questions": [{"q": "Synthesis means…", "options": ["combining sources into a new claim", "copying one source alone", "listing sources without comment"], "answer": "combining sources into a new claim", "explain": "It respects sources and adds your insight."}, {"q": "A provable claim is…", "options": ["specific and supported by evidence", "vague and untestable", "only opinion with no evidence"], "answer": "specific and supported by evidence", "explain": "Provable claims can be examined."}]}},
            {"slug": "capstone-essay-grade12", "title": "Capstone Essay", "order": 4, "minutes": 30, "summary": "Research essay with revision.", "learn": [{"type": "p", "text": "Choose a question that matters to your community. Gather sources, outline, draft, get feedback, revise, and cite in a consistent format. Your bibliography honors the people who helped you think."}, {"type": "activity", "title": "Capstone draft", "text": "Draft 1,000 words. Include introduction with claim, 3 body sections with evidence, and conclusion with implications."}], "check": {"prompt": "Capstone.", "questions": [{"q": "A bibliography helps readers…", "options": ["verify and follow your sources", "hide your sources", "forget your sources"], "answer": "verify and follow your sources", "explain": "Citation enables verification."}, {"q": "Revision should focus on…", "options": ["clarity, evidence, and voice", "only font size", "adding random facts"], "answer": "clarity, evidence, and voice", "explain": "Revise for meaning and persuasion."}]}},
        ]},
    ],
}
