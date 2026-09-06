"""Mathematics — Grade 5 (full published course)."""

MATH_GRADE_5 = {
    "slug": "math-grade-5",
    "title": "Mathematics — Grade 5",
    "summary": "Decimals, fractions, volume, and coordinate graphing.",
    "description": (
        "Fifth graders extend their number sense beyond whole numbers. This course "
        "covers decimal place value and operations, fraction addition and subtraction "
        "with unlike denominators, volume of rectangular prisms, and graphing points "
        "on the coordinate plane. Every lesson pairs clear instruction with worked "
        "examples and a mastery check."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["5"],
    "grade_label": "Grade 5",
    "status": "published",
    "audience": "Grade 5 (ages 10–11), Foundations track; also useful for review.",
    "est_hours": 24,
    "passing_score": 80,
    "learning_objectives": [
        "Read, write, and compare decimals to thousandths.",
        "Add and subtract decimals using place value.",
        "Add and subtract fractions with unlike denominators.",
        "Multiply a fraction by a whole number and simplify.",
        "Find the volume of a rectangular prism.",
        "Graph points in the first quadrant of the coordinate plane.",
    ],
    "units": [
        {
            "slug": "decimals",
            "title": "Decimals",
            "summary": "Place value, comparison, and operations with decimals.",
            "order": 1,
            "lessons": [
                {
                    "slug": "decimal-place-value",
                    "title": "Decimal Place Value",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Read and write decimals to thousandths.",
                    "learn": [
                        {"type": "p", "text": "Decimals are another way to write fractions with denominators 10, 100, or 1000. The decimal point separates whole numbers from parts. The first place right of the point is tenths, then hundredths, then thousandths."},
                        {"type": "list", "items": [
                            "0.3 = 3 tenths",
                            "0.25 = 25 hundredths",
                            "0.125 = 125 thousandths",
                            "Use a place-value chart to keep the columns straight.",
                        ]},
                        {"type": "activity", "title": "Place-value race", "text": "Say a decimal aloud (e.g. 3.47). Write it in a place-value chart. Then say 0.509. Check each column."},
                    ],
                    "check": {
                        "prompt": "Show what you know about decimal place value.",
                        "questions": [
                            {"q": "What is the value of the 4 in 3.47?", "options": ["4 tenths", "4 ones", "4 hundredths"], "answer": "4 tenths", "explain": "The first place right of the decimal is tenths."},
                            {"q": "0.509 has how many decimal places?", "options": ["3", "2", "4"], "answer": "3", "explain": "The digits after the decimal are 5, 0, and 9 — three places."},
                            {"q": "How do you write 'three and twenty-five hundredths' as a decimal?", "options": ["3.25", "3.2", "325"], "answer": "3.25", "explain": "The whole number is 3, and 25 hundredths is .25."},
                        ],
                    },
                },
                {
                    "slug": "comparing-decimals",
                    "title": "Comparing Decimals",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Use >, <, and = with decimals to thousandths.",
                    "learn": [
                        {"type": "p", "text": "Line up the decimal points. Compare digits from left to right. The first place where digits differ decides which is larger."},
                        {"type": "example", "title": "Compare step by step", "text": "0.87 vs 0.8. Line up: 0.87 and 0.80. The tenths are equal (8 = 8). Hundredths: 7 > 0, so 0.87 > 0.8."},
                    ],
                    "check": {
                        "prompt": "Show what you know about comparing decimals.",
                        "questions": [
                            {"q": "Which is greater: 0.6 or 0.58?", "options": ["0.6", "0.58", "equal"], "answer": "0.6", "explain": "0.6 = 0.60, and 60 hundredths > 58 hundredths."},
                            {"q": "Order from least to greatest: 0.3, 0.25, 0.4.", "options": ["0.25, 0.3, 0.4", "0.3, 0.25, 0.4", "0.4, 0.3, 0.25"], "answer": "0.25, 0.3, 0.4", "explain": "0.25 is the smallest, then 0.3, then 0.4."},
                            {"q": "Which symbol makes 1.2 __ 1.19 true?", "options": [">", "<", "="], "answer": ">", "explain": "1.20 > 1.19."},
                        ],
                    },
                },
                {
                    "slug": "adding-subtracting-decimals",
                    "title": "Adding and Subtracting Decimals",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Use place value to add and subtract decimals accurately.",
                    "learn": [
                        {"type": "p", "text": "Write decimals in a column with the decimal points lined up. Add or subtract just like whole numbers, then bring the decimal point straight down into the answer."},
                        {"type": "example", "title": "Add decimals", "text": "4.7 + 2.35. Line up: 4.70 + 2.35 = 7.05."},
                        {"type": "example", "title": "Subtract decimals", "text": "6.5 − 2.38. Line up: 6.50 − 2.38 = 4.12."},
                    ],
                    "check": {
                        "prompt": "Show what you know about adding and subtracting decimals.",
                        "questions": [
                            {"q": "3.4 + 2.6 =", "options": ["6.0", "5.0", "6.10"], "answer": "6.0", "explain": "3.4 + 2.6 = 6.0."},
                            {"q": "5.8 − 2.35 =", "options": ["3.45", "3.53", "2.43"], "answer": "3.45", "explain": "Line up: 5.80 − 2.35 = 3.45."},
                            {"q": "Before adding decimals, you should…", "options": ["line up the decimal points", "round both numbers", "ignore the decimals"], "answer": "line up the decimal points", "explain": "Lining up decimal points keeps the place values aligned."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "fractions",
            "title": "Fractions",
            "summary": "Add, subtract, and multiply fractions.",
            "order": 5,
            "lessons": [
                {
                    "slug": "adding-fractions",
                    "title": "Adding Fractions with Unlike Denominators",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Find common denominators and add fractions.",
                    "learn": [
                        {"type": "p", "text": "To add fractions with different denominators, first rewrite them so they have the same denominator. A common denominator is a shared multiple of the two denominators."},
                        {"type": "example", "title": "Worked example", "text": "1/2 + 1/3. Common denominator = 6. 1/2 = 3/6 and 1/3 = 2/6. Now add: 3/6 + 2/6 = 5/6."},
                        {"type": "activity", "title": "Paper strip model", "text": "Fold one strip into halves and another into thirds. Compare sizes. Find a length that matches both: sixths."},
                    ],
                    "check": {
                        "prompt": "Show what you know about adding fractions.",
                        "questions": [
                            {"q": "1/4 + 1/2 =", "options": ["3/4", "2/6", "1/6"], "answer": "3/4", "explain": "Common denominator 4: 1/4 + 2/4 = 3/4."},
                            {"q": "What is a common denominator for 1/3 and 1/5?", "options": ["15", "8", "3"], "answer": "15", "explain": "15 is a multiple of both 3 and 5."},
                            {"q": "2/5 + 1/5 =", "options": ["3/5", "3/10", "2/10"], "answer": "3/5", "explain": "Same denominator: add numerators, keep the denominator."},
                        ],
                    },
                },
                {
                    "slug": "subtracting-fractions",
                    "title": "Subtracting Fractions with Unlike Denominators",
                    "order": 7,
                    "minutes": 18,
                    "summary": "Find common denominators and subtract fractions.",
                    "learn": [
                        {"type": "p", "text": "Subtracting works like adding: find a common denominator first, subtract the numerators, and keep the shared denominator."},
                        {"type": "example", "title": "Worked example", "text": "3/4 − 1/3. Common denominator = 12. 3/4 = 9/12, 1/3 = 4/12. 9/12 − 4/12 = 5/12."},
                    ],
                    "check": {
                        "prompt": "Show what you know about subtracting fractions.",
                        "questions": [
                            {"q": "3/4 − 1/4 =", "options": ["2/4", "2/8", "4/4"], "answer": "2/4", "explain": "Same denominator: subtract numerators."},
                            {"q": "1 − 1/2 =", "options": ["1/2", "0", "1 1/2"], "answer": "1/2", "explain": "1 = 2/2, so 2/2 − 1/2 = 1/2."},
                            {"q": "Which is a common denominator for 1/6 and 1/8?", "options": ["24", "14", "7"], "answer": "24", "explain": "24 is a multiple of both 6 and 8."},
                        ],
                    },
                },
                {
                    "slug": "multiplying-fractions-by-wholes",
                    "title": "Multiplying Fractions by Whole Numbers",
                    "order": 8,
                    "minutes": 15,
                    "summary": "Use repeated addition and models to multiply.",
                    "learn": [
                        {"type": "p", "text": "Multiplying a fraction by a whole number means repeated addition of the fraction. 3 × 2/5 = 2/5 + 2/5 + 2/5 = 6/5."},
                        {"type": "list", "items": [
                            "Multiply the numerator by the whole number.",
                            "Keep the same denominator.",
                            "Simplify if possible.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about multiplying fractions by whole numbers.",
                        "questions": [
                            {"q": "4 × 1/3 =", "options": ["4/3", "4/12", "1 1/3"], "answer": "4/3", "explain": "4 × 1/3 = 4/3."},
                            {"q": "2 × 3/5 =", "options": ["6/5", "5/6", "2/15"], "answer": "6/5", "explain": "Multiply the numerator: 2 × 3/5 = 6/5."},
                            {"q": "5 × 1/4 can be written as…", "options": ["1/4 + 1/4 + 1/4 + 1/4 + 1/4", "1/4 × 4", "5/1"], "answer": "1/4 + 1/4 + 1/4 + 1/4 + 1/4", "explain": "Multiplying by a whole number means repeated addition."},
                        ],
                    },
                },
                {
                    "slug": "volume",
                    "title": "Volume of Rectangular Prisms",
                    "order": 9,
                    "minutes": 18,
                    "summary": "Count unit cubes and use the volume formula.",
                    "learn": [
                        {"type": "p", "text": "Volume is the amount of space inside a solid. A rectangular prism filled with unit cubes has a volume of length × width × height cubic units."},
                        {"type": "example", "title": "Worked example", "text": "A box is 3 units long, 2 wide, and 4 tall. Volume = 3 × 2 × 4 = 24 cubic units."},
                        {"type": "activity", "title": "Box builder", "text": "Build a rectangular prism with connecting cubes. Count the cubes, then check with the formula."},
                    ],
                    "check": {
                        "prompt": "Show what you know about volume.",
                        "questions": [
                            {"q": "A prism 5 by 3 by 2 has a volume of…", "options": ["30", "10", "20"], "answer": "30", "explain": "5 × 3 × 2 = 30 cubic units."},
                            {"q": "Volume is measured in…", "options": ["cubic units", "square units", "linear units"], "answer": "cubic units", "explain": "Volume counts cubes, so the unit is cubic."},
                            {"q": "If length = 4, width = 4, and height = 4, the volume is…", "options": ["64", "12", "16"], "answer": "64", "explain": "4 × 4 × 4 = 64 cubic units."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "coordinate-plane",
            "title": "Coordinate Plane",
            "summary": "Graph points using ordered pairs in the first quadrant.",
            "order": 10,
            "lessons": [
                {
                    "slug": "ordered-pairs",
                    "title": "Ordered Pairs",
                    "order": 11,
                    "minutes": 15,
                    "summary": "Read and write ordered pairs (x, y).",
                    "learn": [
                        {"type": "p", "text": "A point on a coordinate plane is named by an ordered pair (x, y). The first number is the horizontal distance from the origin. The second number is the vertical distance."},
                        {"type": "list", "items": [
                            "Start at (0, 0).",
                            "Move right for positive x, left for negative x.",
                            "Move up for positive y, down for negative y.",
                            "Grade 5 uses the first quadrant only: x ≥ 0 and y ≥ 0.",
                        ]},
                        {"type": "activity", "title": "Plot points", "text": "Plot (2, 3), (4, 1), and (1, 5) on a first-quadrant grid. Name each point aloud."},
                    ],
                    "check": {
                        "prompt": "Show what you know about ordered pairs.",
                        "questions": [
                            {"q": "The ordered pair (3, 2) means…", "options": ["right 3, up 2", "right 2, up 3", "left 3, down 2"], "answer": "right 3, up 2", "explain": "First number is x (horizontal), second is y (vertical)."},
                            {"q": "Which point is farther to the right: (4, 1) or (2, 5)?", "options": ["(4, 1)", "(2, 5)", "same distance"], "answer": "(4, 1)", "explain": "The x-coordinate 4 is larger than 2."},
                            {"q": "In first quadrant, coordinates are…", "options": ["both positive", "both negative", "one positive, one negative"], "answer": "both positive", "explain": "First quadrant means x ≥ 0 and y ≥ 0."},
                        ],
                    },
                },
                {
                    "slug": "graphing-paths",
                    "title": "Graphing Paths",
                    "order": 12,
                    "minutes": 15,
                    "summary": "Graph a short path and describe it using coordinates.",
                    "learn": [
                        {"type": "p", "text": "A path on the grid is a series of points. You can describe it by listing the coordinates or by saying how to move from one point to the next."},
                        {"type": "example", "title": "Path example", "text": "Start at (2, 1). Go to (2, 4): up 3. Then to (5, 4): right 3."},
                        {"type": "activity", "title": "Treasure map", "text": "Draw a path from (1, 1) to (1, 5) to (4, 5). Write the coordinates in order."},
                    ],
                    "check": {
                        "prompt": "Show what you know about graphing paths.",
                        "questions": [
                            {"q": "To move from (3, 2) to (3, 6), you go…", "options": ["up 4", "right 4", "down 4"], "answer": "up 4", "explain": "The x stays 3 and y increases by 4."},
                            {"q": "To move from (1, 4) to (5, 4), you go…", "options": ["right 4", "up 4", "down 4"], "answer": "right 4", "explain": "The y stays 4 and x increases by 4."},
                            {"q": "Which point is directly above (2, 3)?", "options": ["(2, 6)", "(6, 2)", "(3, 2)"], "answer": "(2, 6)", "explain": "Same x, larger y — directly above."},
                        ],
                    },
                },
            ],
        },
    ],
}
