"""Mathematics — Kindergarten (published core, fills K gap: math)."""

MATH_KINDERGARTEN = {
    "slug": "math-kindergarten",
    "title": "Mathematics — Kindergarten",
    "summary": "Counting, number sense to 20, comparing and composing numbers, and first shapes.",
    "description": (
        "Kindergarten math builds number sense through hands-on counting and comparing. "
        "Learners count to 100, work within 10, compare quantities, and sort shapes — "
        "rooted in everyday family and community contexts where numbers matter."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["K"],
    "grade_label": "Kindergarten",
    "status": "published",
    "audience": "Kindergarten (ages 5–6), Foundations track.",
    "est_hours": 16,
    "passing_score": 80,
    "learning_objectives": [
        "Count to 100 by ones and tens and write numerals to 20.",
        "Compare two groups and two numerals within 10.",
        "Add and subtract within 10 using objects and drawings.",
        "Compose and decompose numbers to 10 (e.g., 7 = 4 + 3).",
        "Describe and sort two- and three-dimensional shapes.",
    ],
    "units": [
        {
            "slug": "counting-and-numbers",
            "title": "Counting and Numbers to 20",
            "summary": "Number names, counting, and writing numerals.",
            "order": 1,
            "lessons": [
                {
                    "slug": "counting-to-100",
                    "title": "Counting to 100 and Writing Numerals",
                    "order": 1,
                    "minutes": 15,
                    "summary": "Count by ones and tens; write numbers 0–20.",
                    "learn": [
                        {"type": "p", "text": "We count every day — family members at the table, books on a shelf, steps to the park. Kindergarteners count to 100 by ones and tens and learn to write numerals 0–20 clearly."},
                        {"type": "list", "items": ["Count by ones: 1, 2, 3, … 100.", "Count by tens: 10, 20, 30, … 100.", "Write each numeral 0–20 with correct formation."]},
                        {"type": "activity", "title": "Home count", "text": "Count three collections at home (utensils, crayons, socks). Write how many in each group."},
                    ],
                    "check": {
                        "prompt": "Show counting to 100 and writing numerals.",
                        "questions": [
                            {"q": "What comes next when counting by tens: 10, 20, 30, __?", "options": ["40", "31", "100"], "answer": "40", "explain": "Counting by tens adds 10 each time."},
                            {"q": "Which is written correctly for fourteen?", "options": ["14", "41", "4"], "answer": "14", "explain": "Fourteen is 1 ten and 4 ones: 14."},
                            {"q": "Counting by ones from 97, what comes after 99?", "options": ["100", "90", "110"], "answer": "100", "explain": "99 + 1 = 100."},
                        ],
                    },
                },
                {
                    "slug": "comparing-numbers-within-10",
                    "title": "Comparing Quantities and Numerals Within 10",
                    "order": 2,
                    "minutes": 15,
                    "summary": "Use >, <, = for groups and numerals.",
                    "learn": [
                        {"type": "p", "text": "Comparing helps families make fair choices. We compare two groups or two numerals within 10 using greater than (>), less than (<), and equal to (=)."},
                        {"type": "list", "items": ["5 > 3 means 5 is greater than 3.", "4 < 7 means 4 is less than 7.", "6 = 6 means the amounts are equal."]},
                        {"type": "example", "title": "Compare groups", "text": "You have 6 apples and your cousin has 8. 6 < 8, so your cousin has more."},
                    ],
                    "check": {
                        "prompt": "Compare within 10.",
                        "questions": [
                            {"q": "Which symbol makes 3 __ 7 true?", "options": ["<", ">", "="], "answer": "<", "explain": "3 is less than 7."},
                            {"q": "Which is true?", "options": ["9 > 5", "4 > 9", "5 = 6"], "answer": "9 > 5", "explain": "9 has more ones than 5."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "operations-and-shapes",
            "title": "Operations Within 10 and Shapes",
            "summary": "Add, subtract, compose, and describe shapes.",
            "order": 2,
            "lessons": [
                {
                    "slug": "add-subtract-within-10",
                    "title": "Add and Subtract Within 10",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Put together, take apart, and make 10.",
                    "learn": [
                        {"type": "p", "text": "Addition is putting together; subtraction is taking apart. Draw, use fingers, or build with cubes. Making 10 is a powerful strategy."},
                        {"type": "example", "title": "Story", "text": "There are 7 crayons. You get 3 more. 7 + 3 = 10."},
                        {"type": "activity", "title": "Make 10", "text": "With 10 counters, show every pair that makes 10: 0+10, 1+9, … 10+0."},
                    ],
                    "check": {
                        "prompt": "Add and subtract within 10.",
                        "questions": [
                            {"q": "What is 4 + 6?", "options": ["10", "9", "11"], "answer": "10", "explain": "4 and 6 compose 10."},
                            {"q": "What is 10 − 3?", "options": ["7", "6", "8"], "answer": "7", "explain": "10 take away 3 is 7."},
                            {"q": "Which pair makes 8?", "options": ["5 and 3", "6 and 4", "7 and 4"], "answer": "5 and 3", "explain": "5 + 3 = 8."},
                        ],
                    },
                },
                {
                    "slug": "shapes-sort-and-describe",
                    "title": "Sort and Describe Shapes",
                    "order": 4,
                    "minutes": 15,
                    "summary": "Flat and solid shapes in the home and community.",
                    "learn": [
                        {"type": "p", "text": "Shapes are everywhere — quilts, murals, buildings. Circles, squares, triangles are flat (2D). Cubes, spheres, cones are solid (3D). Sort by sides, corners, and whether a shape stacks or rolls."},
                        {"type": "list", "items": ["Square: 4 equal sides, 4 corners.", "Triangle: 3 sides, 3 corners.", "Cube, sphere, cylinder are solid shapes."]},
                        {"type": "activity", "title": "Shape museum", "text": "Collect one example of each shape at home. Sort into 2D vs 3D and explain the rule you used."},
                    ],
                    "check": {
                        "prompt": "Describe and sort shapes.",
                        "questions": [
                            {"q": "Which shape rolls easily?", "options": ["sphere", "cube", "square"], "answer": "sphere", "explain": "Spheres have a curved surface and roll."},
                            {"q": "How many sides does a rectangle have?", "options": ["4", "3", "5"], "answer": "4", "explain": "A rectangle has 4 sides and 4 right angles."},
                            {"q": "A soup can is closest to a…", "options": ["cylinder", "cone", "cube"], "answer": "cylinder", "explain": "A can has two circular faces and a curved side: a cylinder."},
                        ],
                    },
                },
            ],
        },
    ],
}
