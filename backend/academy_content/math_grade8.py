"""Mathematics — Grade 8 (full published course)."""

MATH_GRADE_8 = {
    "slug": "math-grade-8",
    "title": "Mathematics — Grade 8",
    "summary": "Linear equations, functions, exponents, and the Pythagorean theorem.",
    "description": (
        "Eighth graders bridge middle school and high school math. This course "
        "covers linear equations and systems, slope and functions, integer exponents "
        "and scientific notation, transformations, and the Pythagorean theorem. "
        "Every lesson combines clear explanation with worked examples and a mastery check."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["8"],
    "grade_label": "Grade 8",
    "status": "published",
    "audience": "Grade 8 (ages 13–14), Foundations track; also useful for review.",
    "est_hours": 26,
    "passing_score": 80,
    "learning_objectives": [
        "Solve one- and two-step linear equations.",
        "Graph linear equations and identify slope and y-intercept.",
        "Understand functions as rules that assign exactly one output to each input.",
        "Apply exponent rules for integer exponents.",
        "Use the Pythagorean theorem to find missing lengths.",
        "Perform and describe transformations on the coordinate plane.",
    ],
    "units": [
        {
            "slug": "linear-equations",
            "title": "Linear Equations",
            "summary": "Solve, graph, and interpret linear equations.",
            "order": 1,
            "lessons": [
                {
                    "slug": "solving-one-step",
                    "title": "Solving One-Step Equations",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Use inverse operations to isolate the variable.",
                    "learn": [
                        {"type": "p", "text": "An equation states that two expressions are equal. To solve, use inverse operations to isolate the variable. Whatever you do to one side, do to the other."},
                        {"type": "list", "items": [
                            "Addition equation: subtract the same number from both sides.",
                            "Subtraction equation: add the same number to both sides.",
                            "Multiplication equation: divide both sides by the same number.",
                            "Division equation: multiply both sides by the same number.",
                        ]},
                        {"type": "example", "title": "Worked example", "text": "x + 7 = 12. Subtract 7 from both sides: x = 5. Check: 5 + 7 = 12. ✓"},
                    ],
                    "check": {
                        "prompt": "Show what you know about solving one-step equations.",
                        "questions": [
                            {"q": "Solve: x + 4 = 10.", "options": ["6", "14", "4"], "answer": "6", "explain": "Subtract 4 from both sides: x = 6."},
                            {"q": "Solve: 3x = 15.", "options": ["5", "12", "45"], "answer": "5", "explain": "Divide both sides by 3: x = 5."},
                            {"q": "To keep an equation balanced, you must…", "options": ["do the same thing to both sides", "only change the left side", "add 1 to both sides"], "answer": "do the same thing to both sides", "explain": "Equality means both sides stay the same when you operate."},
                        ],
                    },
                },
                {
                    "slug": "solving-two-step",
                    "title": "Solving Two-Step Equations",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Undo addition/subtraction first, then multiplication/division.",
                    "learn": [
                        {"type": "p", "text": "A two-step equation has two operations. Use inverse operations in reverse order: undo addition or subtraction first, then undo multiplication or division."},
                        {"type": "example", "title": "Worked example", "text": "2x + 6 = 14. Subtract 6: 2x = 8. Divide by 2: x = 4."},
                    ],
                    "check": {
                        "prompt": "Show what you know about solving two-step equations.",
                        "questions": [
                            {"q": "Solve: 3x − 9 = 0.", "options": ["3", "6", "9"], "answer": "3", "explain": "Add 9: 3x = 9. Divide by 3: x = 3."},
                            {"q": "Solve: 5 + 2x = 13.", "options": ["4", "9", "6.5"], "answer": "4", "explain": "Subtract 5: 2x = 8. Divide by 2: x = 4."},
                            {"q": "The first step in 4x − 5 = 11 is…", "options": ["add 5 to both sides", "divide by 4", "subtract 5 from both sides"], "answer": "add 5 to both sides", "explain": "Undo subtraction first: add 5."},
                        ],
                    },
                },
                {
                    "slug": "slope-and-y-intercept",
                    "title": "Slope and Y-Intercept",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Identify slope and y-intercept from equations and graphs.",
                    "learn": [
                        {"type": "p", "text": "A linear equation in slope-intercept form is y = mx + b. m is the slope (rise over run). b is the y-intercept, where the line crosses the y-axis."},
                        {"type": "example", "title": "Read the equation", "text": "y = 2x + 1. Slope = 2 (rise 2, run 1). Y-intercept = 1."},
                        {"type": "activity", "title": "Graph from equation", "text": "Graph y = 2x + 1. Start at (0, 1). Rise 2, run 1 to plot the next point."},
                    ],
                    "check": {
                        "prompt": "Show what you know about slope and y-intercept.",
                        "questions": [
                            {"q": "In y = 3x − 2, the slope is…", "options": ["3", "−2", "1"], "answer": "3", "explain": "m is the coefficient of x."},
                            {"q": "In y = 3x − 2, the y-intercept is…", "options": ["−2", "3", "2"], "answer": "−2", "explain": "b is the constant term."},
                            {"q": "Slope means…", "options": ["rise over run", "run over rise", "x divided by y"], "answer": "rise over run", "explain": "Slope = change in y ÷ change in x."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "pythagorean-theorem",
            "title": "Pythagorean Theorem",
            "summary": "Find missing side lengths in right triangles.",
            "order": 5,
            "lessons": [
                {
                    "slug": "pythagorean-basics",
                    "title": "Pythagorean Basics",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Use a² + b² = c² to find missing lengths.",
                    "learn": [
                        {"type": "p", "text": "In a right triangle, the longest side is the hypotenuse (c). The other two sides are legs (a and b). The Pythagorean theorem says a² + b² = c²."},
                        {"type": "example", "title": "Worked example", "text": "Legs 3 and 4. 3² + 4² = 9 + 16 = 25. √25 = 5. The hypotenuse is 5."},
                    ],
                    "check": {
                        "prompt": "Show what you know about the Pythagorean theorem.",
                        "questions": [
                            {"q": "In a right triangle, the hypotenuse is…", "options": ["the longest side opposite the right angle", "any side", "the shortest side"], "answer": "the longest side opposite the right angle", "explain": "The hypotenuse is always opposite the right angle."},
                            {"q": "If a = 6 and b = 8, c =", "options": ["10", "14", "48"], "answer": "10", "explain": "36 + 64 = 100, and √100 = 10."},
                            {"q": "Which equation represents the Pythagorean theorem?", "options": ["a² + b² = c²", "a + b = c", "a × b = c"], "answer": "a² + b² = c²", "explain": "The theorem states that the sum of the squares of the legs equals the square of the hypotenuse."},
                        ],
                    },
                },
                {
                    "slug": "pythagorean-applications",
                    "title": "Pythagorean Applications",
                    "order": 7,
                    "minutes": 15,
                    "summary": "Use the theorem to solve real-world distance problems.",
                    "learn": [
                        {"type": "p", "text": "The Pythagorean theorem works for any right triangle. Use it to find the straight-line distance between two points on a map or screen."},
                        {"type": "example", "title": "Distance across a field", "text": "A field is 30 meters by 40 meters. The diagonal is √(30² + 40²) = √2500 = 50 meters."},
                    ],
                    "check": {
                        "prompt": "Show what you know about Pythagorean applications.",
                        "questions": [
                            {"q": "A ladder leans against a wall. The base is 5 ft from the wall and the ladder is 13 ft long. How high is the top?", "options": ["12 ft", "8 ft", "18 ft"], "answer": "12 ft", "explain": "5² + h² = 13² → 25 + h² = 169 → h² = 144 → h = 12."},
                            {"q": "Which problem uses the Pythagorean theorem?", "options": ["Find the diagonal of a rectangle", "Find the perimeter", "Find the area"], "answer": "Find the diagonal of a rectangle", "explain": "The diagonal of a rectangle forms the hypotenuse of a right triangle."},
                        ],
                    },
                },
            ],
        },
    ],
}
