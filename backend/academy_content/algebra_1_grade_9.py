"""Algebra 1 — Grade 9 (full published course)."""

ALGEBRA_1_GRADE_9 = {
    "slug": "algebra-1-grade-9",
    "title": "Algebra 1",
    "summary": "Linear and quadratic expressions, equations, and functions.",
    "description": (
        "Algebra 1 is the gateway to higher mathematics. This course builds from "
        "evaluating expressions and solving linear equations through systems of "
        "equations, exponents, polynomials, and quadratic functions. Each lesson "
        "emphasizes conceptual understanding and procedural fluency with a mastery check."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "scholar",
    "tracks": ["scholar", "foundations", "builder"],
    "grades": ["9"],
    "grade_label": "Grade 9",
    "status": "published",
    "audience": "Grade 9 (ages 14–15), Scholar track; also useful for advanced Foundations and Builder students.",
    "est_hours": 30,
    "passing_score": 80,
    "learning_objectives": [
        "Simplify and evaluate algebraic expressions.",
        "Solve linear equations and inequalities in one variable.",
        "Solve systems of linear equations by graphing and substitution.",
        "Apply exponent rules to simplify expressions.",
        "Graph linear and quadratic functions.",
        "Factor quadratic expressions and solve quadratic equations.",
    ],
    "units": [
        {
            "slug": "expressions-and-equations",
            "title": "Expressions and Equations",
            "summary": "Simplify, evaluate, and solve.",
            "order": 1,
            "lessons": [
                {
                    "slug": "evaluating-expressions",
                    "title": "Evaluating Expressions",
                    "order": 2,
                    "minutes": 15,
                    "summary": "Substitute values for variables and simplify.",
                    "learn": [
                        {"type": "p", "text": "An algebraic expression uses variables, numbers, and operations. To evaluate, replace each variable with its given value and compute using the order of operations."},
                        {"type": "example", "title": "Evaluate", "text": "Evaluate 2x² + 3 when x = 4. 2(4)² + 3 = 2(16) + 3 = 32 + 3 = 35."},
                    ],
                    "check": {
                        "prompt": "Show what you know about evaluating expressions.",
                        "questions": [
                            {"q": "Evaluate 3x + 2 when x = 5.", "options": ["17", "15", "13"], "answer": "17", "explain": "3(5) + 2 = 15 + 2 = 17."},
                            {"q": "In 4y², when y = 3, the value is…", "options": ["36", "12", "24"], "answer": "36", "explain": "4 × 3² = 4 × 9 = 36."},
                        ],
                    },
                },
                {
                    "slug": "solving-multi-step",
                    "title": "Solving Multi-Step Equations",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Use inverse operations and the distributive property.",
                    "learn": [
                        {"type": "p", "text": "A multi-step equation has more than one operation. Use inverse operations in reverse order. Distribute first if parentheses are present."},
                        {"type": "example", "title": "Worked example", "text": "2(x + 3) = 14. Distribute: 2x + 6 = 14. Subtract 6: 2x = 8. Divide by 2: x = 4."},
                    ],
                    "check": {
                        "prompt": "Show what you know about multi-step equations.",
                        "questions": [
                            {"q": "Solve: 3(x − 2) = 9.", "options": ["5", "3", "1"], "answer": "5", "explain": "3x − 6 = 9 → 3x = 15 → x = 5."},
                            {"q": "The first step in 4 + 2x = 14 is…", "options": ["subtract 4", "divide by 2", "add 4"], "answer": "subtract 4", "explain": "Undo addition before undoing multiplication."},
                        ],
                    },
                },
                {
                    "slug": "linear-inequalities",
                    "title": "Linear Inequalities",
                    "order": 4,
                    "minutes": 15,
                    "summary": "Solve and graph linear inequalities.",
                    "learn": [
                        {"type": "p", "text": "Inequalities use <, >, ≤, or ≥ instead of =. Solve them like equations, but flip the inequality sign when multiplying or dividing by a negative number."},
                        {"type": "example", "title": "Worked example", "text": "2x + 4 > 10. Subtract 4: 2x > 6. Divide by 2: x > 3."},
                    ],
                    "check": {
                        "prompt": "Show what you know about linear inequalities.",
                        "questions": [
                            {"q": "Solve: x − 5 < 3.", "options": ["x < 8", "x < 2", "x > 8"], "answer": "x < 8", "explain": "Add 5 to both sides: x < 8."},
                            {"q": "When you multiply an inequality by a negative number, you must…", "options": ["flip the inequality sign", "keep the sign", "make it an equation"], "answer": "flip the inequality sign", "explain": "Multiplying by a negative reverses the order."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "functions-and-graphing",
            "title": "Functions and Graphing",
            "summary": "Understand and graph linear and quadratic functions.",
            "order": 5,
            "lessons": [
                {
                    "slug": "linear-functions",
                    "title": "Linear Functions",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Write, graph, and interpret linear functions.",
                    "learn": [
                        {"type": "p", "text": "A linear function has a constant rate of change (slope). Its graph is a straight line. Slope-intercept form: y = mx + b. Standard form: Ax + By = C."},
                        {"type": "example", "title": "Graph from equation", "text": "y = 2x − 1. y-intercept = −1. Slope = 2 (up 2, right 1). Plot (0, −1) and (1, 1), then draw the line."},
                    ],
                    "check": {
                        "prompt": "Show what you know about linear functions.",
                        "questions": [
                            {"q": "In y = 3x + 2, the y-intercept is…", "options": ["2", "3", "−2"], "answer": "2", "explain": "b is the constant term."},
                            {"q": "The slope of y = −x + 4 is…", "options": ["−1", "1", "4"], "answer": "−1", "explain": "The coefficient of x is the slope."},
                            {"q": "A linear function's graph is…", "options": ["a straight line", "a curve", "a circle"], "answer": "a straight line", "explain": "Linear means the rate of change is constant, so the graph is straight."},
                        ],
                    },
                },
                {
                    "slug": "quadratic-functions",
                    "title": "Quadratic Functions",
                    "order": 7,
                    "minutes": 18,
                    "summary": "Graph and interpret parabolas.",
                    "learn": [
                        {"type": "p", "text": "A quadratic function has an x² term. Its graph is a parabola. The vertex is the highest or lowest point. The axis of symmetry is a vertical line through the vertex."},
                        {"type": "example", "title": "Graph from factored form", "text": "y = (x − 1)(x + 3). Zeros at x = 1 and x = −3. Vertex is halfway between zeros at x = −1. Evaluate y at x = −1 to find the vertex height."},
                    ],
                    "check": {
                        "prompt": "Show what you know about quadratic functions.",
                        "questions": [
                            {"q": "The graph of a quadratic function is called a…", "options": ["parabola", "line", "circle"], "answer": "parabola", "explain": "Quadratic functions graph as U-shaped curves called parabolas."},
                            {"q": "The vertex of a parabola that opens downward is…", "options": ["the highest point", "the lowest point", "the x-intercept"], "answer": "the highest point", "explain": "Downward-opening parabolas have a maximum vertex."},
                            {"q": "The zeros of a quadratic are…", "options": ["the x-values where y = 0", "the y-values where x = 0", "the vertex coordinates"], "answer": "the x-values where y = 0", "explain": "Zeros are where the graph crosses the x-axis."},
                        ],
                    },
                },
            ],
        },
    ],
}
