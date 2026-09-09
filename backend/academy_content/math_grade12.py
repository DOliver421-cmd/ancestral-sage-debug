"""Mathematics — Grade 12 (published core, fills Grade 12 gap: math)."""

MATH_GRADE_12 = {
    "slug": "math-grade-12",
    "title": "Mathematics — Grade 12",
    "summary": "Advanced algebra, trigonometry, and modeling for college and work.",
    "description": "Twelfth-grade math integrates functions, trigonometry, and data modeling — preparing learners for college placement and career applications.",
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["12"],
    "grade_label": "Grade 12",
    "status": "published",
    "audience": "Grade 12 (ages 17–18), Scholar track; capstone year.",
    "est_hours": 20,
    "passing_score": 80,
    "learning_objectives": ["Model with advanced functions and trigonometry.", "Use units and precision to solve applied problems.", "Interpret models and communicate decisions."],
    "units": [
        {"slug": "functions-trig", "title": "Functions and Trigonometry", "summary": "Periodic and advanced patterns.", "order": 1, "lessons": [
            {"slug": "advanced-functions-grade12", "title": "Advanced Functions", "order": 1, "minutes": 18, "summary": "Composition and inverses.", "learn": [{"type": "p", "text": "Functions combine: composition applies one function after another; inverses undo a function when it is one-to-one. Transformations reveal symmetry and purpose."}, {"type": "list", "items": ["(f ∘ g)(x) = f(g(x)).", "If f undoes g, they are inverses.", "Graphs show shifts, stretches, and reflections."]}], "check": {"prompt": "Functions.", "questions": [{"q": "An inverse function…", "options": ["undoes the original when one-to-one", "never exists", "only adds 1"], "answer": "undoes the original when one-to-one", "explain": "Inverses reverse the mapping."}, {"q": "Composition f(g(x)) means…", "options": ["apply g, then f", "apply f only", "add f and g"], "answer": "apply g, then f", "explain": "Inside first, outside second."}]}},
            {"slug": "trigonometry-grade12", "title": "Trigonometry and Periodic Models", "order": 2, "minutes": 18, "summary": "Triangles and cycles.", "learn": [{"type": "p", "text": "Trigonometry models cycles — days, seasons, waves, and circles. Sine and cosine oscillate between -1 and 1; amplitude, period, and phase tell the story."}, {"type": "list", "items": ["sin and cos: period 2π, amplitude controls height.", "Applications: heights, waves, sound.", "Unit circle connects angles to coordinates."]}], "check": {"prompt": "Trig.", "questions": [{"q": "Sine has period…", "options": ["2π", "1", "π only"], "answer": "2π", "explain": "sin repeats every 2π radians."}, {"q": "Amplitude affects…", "options": ["how tall the wave is", "only the period", "only the phase"], "answer": "how tall the wave is", "explain": "Larger amplitude means larger peaks."}]}},
        ]},
        {"slug": "modeling", "title": "Applied Modeling", "summary": "Decide with math.", "order": 2, "lessons": [
            {"slug": "modeling-applications-grade12", "title": "Modeling Applications", "order": 3, "minutes": 18, "summary": "Choose and critique a model.", "learn": [{"type": "p", "text": "Applied modeling picks a function family, fits to data, predicts, and explains limits. Community questions — budgeting, building, health — gain clarity with a model and a story."}, {"type": "list", "items": ["Fit: compare linear vs exponential residuals.", "Predict: use the model for nearby values.", "Communicate: who benefits, who bears risk?"]}], "check": {"prompt": "Modeling.", "questions": [{"q": "A model is useful when it…", "options": ["fits the pattern and helps you decide", "hides the pattern", "is always perfect"], "answer": "fits the pattern and helps you decide", "explain": "Useful models guide action."}, {"q": "Residuals show…", "options": ["where the model misses the data", "nothing useful", "only the mean"], "answer": "where the model misses the data", "explain": "Patterns in residuals suggest better models."}]}},
            {"slug": "decision-and-communication-grade12", "title": "Decisions and Communication", "order": 4, "minutes": 15, "summary": "Explain with honesty.", "learn": [{"type": "p", "text": "Present results with uncertainty stated. Show the data, the model, and the trade-offs so the community can decide together."}, {"type": "activity", "title": "Recommendation memo", "text": "Write a one-page memo: question, data, model chosen, prediction, limits, and recommendation."}], "check": {"prompt": "Communication.", "questions": [{"q": "Good data communication includes…", "options": ["data, model, limits, and trade-offs", "only the conclusion", "no data at all"], "answer": "data, model, limits, and trade-offs", "explain": "Transparency builds trust."}, {"q": "Uncertainty should be…", "options": ["stated honestly", "hidden", "exaggerated only"], "answer": "stated honestly", "explain": "Honest bounds help decisions."}]}},
        ]},
    ],
}
