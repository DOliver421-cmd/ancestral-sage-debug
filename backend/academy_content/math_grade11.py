"""Mathematics — Grade 11 (published core, fills Grade 11 gap: math)."""

MATH_GRADE_11 = {
    "slug": "math-grade-11",
    "title": "Mathematics — Grade 11",
    "summary": "Functions, quadratics, exponentials, and data analysis.",
    "description": "Eleventh-grade math deepens function analysis and data reasoning — modeling with quadratics and exponentials and interpreting data for community decisions.",
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["11"],
    "grade_label": "Grade 11",
    "status": "published",
    "audience": "Grade 11 (ages 16–17), Scholar track.",
    "est_hours": 20,
    "passing_score": 80,
    "learning_objectives": ["Analyze and graph quadratic and exponential functions.", "Solve quadratic equations and model motion.", "Summarize and interpret data with mean, median, and standard deviation."],
    "units": [
        {"slug": "quadratics", "title": "Quadratics and Modeling", "summary": "Parabolas and motion.", "order": 1, "lessons": [
            {"slug": "quadratic-functions-grade11", "title": "Quadratic Functions", "order": 1, "minutes": 18, "summary": "Form, vertex, roots.", "learn": [{"type": "p", "text": "A quadratic has form y = ax^2 + bx + c. Its graph is a parabola. The vertex is the highest or lowest point; roots are where y = 0."}, {"type": "list", "items": ["a > 0 opens up; a < 0 opens down.", "Vertex at -b/2a gives symmetry.", "Roots via factoring, completing the square, or quadratic formula."]}], "check": {"prompt": "Quadratics.", "questions": [{"q": "y = x^2 + 3x + 2 opens…", "options": ["up", "down", "sideways"], "answer": "up", "explain": "a = 1 > 0, so it opens upward."}, {"q": "Roots are where…", "options": ["y = 0", "x = 0 always", "y = 1"], "answer": "y = 0", "explain": "Roots are x-intercepts."}]}},
            {"slug": "exponentials-grade11", "title": "Exponential Functions", "order": 2, "minutes": 18, "summary": "Growth and decay.", "learn": [{"type": "p", "text": "Exponential functions y = a*b^x model fast growth or decay — populations, investments, and decay of materials. Doubling time is key insight for community planning."}, {"type": "list", "items": ["b > 1: growth.", "0 < b < 1: decay.", "Doubling/halving time reveals long-term impact."]}], "check": {"prompt": "Exponentials.", "questions": [{"q": "y = 100*(1.05)^x shows…", "options": ["growth by 5% per period", "decay by 5%", "no change"], "answer": "growth by 5% per period", "explain": "b = 1.05 > 1."}, {"q": "Doubling time helps you…", "options": ["see long-term growth impact", "hide growth", "only find yesterday"], "answer": "see long-term growth impact", "explain": "It projects forward."}]}},
        ]},
        {"slug": "data", "title": "Data and Reasoning", "summary": "Summaries and spread.", "order": 2, "lessons": [
            {"slug": "summarizing-data-grade11", "title": "Summarizing Data", "order": 3, "minutes": 18, "summary": "Center and spread.", "learn": [{"type": "p", "text": "Mean is the average; median is the middle; mode is most common. Range and standard deviation describe spread. Choose summaries that serve the question honestly."}, {"type": "list", "items": ["Mean sensitive to outliers; median resists them.", "Standard deviation: larger means more spread.", "Visualize with histograms and box plots."]}], "check": {"prompt": "Data summaries.", "questions": [{"q": "Which resists outliers?", "options": ["median", "mean only", "range only"], "answer": "median", "explain": "Median is the middle value."}, {"q": "Large standard deviation means…", "options": ["data are more spread out", "data are tightly clumped", "no data exists"], "answer": "data are more spread out", "explain": "Spread grows with variation."}]}},
            {"slug": "modeling-with-math-grade11", "title": "Modeling with Mathematics", "order": 4, "minutes": 15, "summary": "Choose a model for the context.", "learn": [{"type": "p", "text": "Models simplify reality to answer questions. Pick a function family that fits the pattern, check residuals, and explain what the model suggests for action."}, {"type": "activity", "title": "Choose a model", "text": "You track weekly community garden harvests. Would a linear or exponential model fit better? Explain using trend and residuals."}], "check": {"prompt": "Modeling.", "questions": [{"q": "A good model…", "options": ["fits the pattern and helps you act", "hides the pattern", "is always perfect"], "answer": "fits the pattern and helps you act", "explain": "Utility matters more than perfection."}, {"q": "Checking residuals helps you…", "options": ["see where the model misses", "ignore all data", "hide errors"], "answer": "see where the model misses", "explain": "Residuals show error patterns."}]}},
        ]},
    ],
}
