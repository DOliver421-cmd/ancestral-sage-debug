"""Mathematics — Grade 6 (full published course)."""

MATH_GRADE_6 = {
    "slug": "math-grade-6",
    "title": "Mathematics — Grade 6",
    "summary": "Ratios, proportions, integer operations, and algebraic expressions.",
    "description": (
        "Sixth graders make the critical shift from arithmetic to algebraic thinking. "
        "This course introduces ratios and unit rates, proportions, operations with "
        "integers, and writing and evaluating algebraic expressions. Every lesson "
        "builds a concrete understanding before moving to abstract notation."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["6"],
    "grade_label": "Grade 6",
    "status": "published",
    "audience": "Grade 6 (ages 11–12), Foundations track; also useful for review.",
    "est_hours": 22,
    "passing_score": 80,
    "learning_objectives": [
        "Write and interpret ratios and unit rates.",
        "Solve proportion problems using equivalent ratios.",
        "Add, subtract, multiply, and divide integers.",
        "Use the distributive property with algebraic expressions.",
        "Evaluate expressions for given variable values.",
        "Solve one-step equations with addition and multiplication.",
    ],
    "units": [
        {
            "slug": "ratios-and-proportions",
            "title": "Ratios and Proportions",
            "summary": "Compare quantities with ratios and solve proportions.",
            "order": 1,
            "lessons": [
                {
                    "slug": "introduction-to-ratios",
                    "title": "Introduction to Ratios",
                    "order": 2,
                    "minutes": 15,
                    "summary": "Write and interpret ratios in three forms.",
                    "learn": [
                        {"type": "p", "text": "A ratio compares two quantities. You can write it as '3 to 2,' '3:2,' or '3/2.' The first quantity is first. Ratios can compare part to part or part to whole."},
                        {"type": "list", "items": [
                            "Part-to-part: 3 blue marbles to 2 red marbles.",
                            "Part-to-whole: 3 blue marbles out of 5 total.",
                            "Keep the order: 3 to 2 is not the same as 2 to 3.",
                        ]},
                        {"type": "activity", "title": "Ratio hunt", "text": "In your classroom, find two things and write a ratio. Example: 'There are 12 chairs to 1 teacher.'"},
                    ],
                    "check": {
                        "prompt": "Show what you know about ratios.",
                        "questions": [
                            {"q": "The ratio of 8 girls to 10 boys can be written as…", "options": ["8:10", "10:8", "8 + 10"], "answer": "8:10", "explain": "Ratios can be written with a colon."},
                            {"q": "If 3 of 5 pets are cats, what is the ratio of cats to total pets?", "options": ["3:5", "2:5", "3:2"], "answer": "3:5", "explain": "Part-to-whole compares one part to the total."},
                            {"q": "A ratio compares…", "options": ["two quantities", "two sums", "two differences"], "answer": "two quantities", "explain": "A ratio is a comparison of two amounts."},
                        ],
                    },
                },
                {
                    "slug": "unit-rates",
                    "title": "Unit Rates",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Find and use unit rates from ratios.",
                    "learn": [
                        {"type": "p", "text": "A unit rate is a ratio where the second quantity is 1. '50 miles in 2 hours' becomes '25 miles per hour.' Divide the first quantity by the second."},
                        {"type": "example", "title": "Find the unit rate", "text": "120 steps in 3 minutes. 120 ÷ 3 = 40 steps per minute."},
                    ],
                    "check": {
                        "prompt": "Show what you know about unit rates.",
                        "questions": [
                            {"q": "36 dollars for 4 books is a unit rate of…", "options": ["$9 per book", "$4 per book", "$10 per book"], "answer": "$9 per book", "explain": "36 ÷ 4 = 9 dollars per book."},
                            {"q": "A unit rate always has…", "options": ["a second quantity of 1", "a first quantity of 1", "no fractions"], "answer": "a second quantity of 1", "explain": "A unit rate compares to one unit of the second quantity."},
                            {"q": "15 miles in 3 hours is…", "options": ["5 miles per hour", "3 miles per hour", "45 miles per hour"], "answer": "5 miles per hour", "explain": "15 ÷ 3 = 5 miles per hour."},
                        ],
                    },
                },
                {
                    "slug": "proportions",
                    "title": "Proportions",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Solve proportions using equivalent ratios and cross products.",
                    "learn": [
                        {"type": "p", "text": "A proportion is an equation stating that two ratios are equal. 2/3 = 4/6 is a proportion. You can solve proportions with equivalent ratios or cross products."},
                        {"type": "example", "title": "Cross products", "text": "If 3/4 = x/8, cross multiply: 3 × 8 = 4 × x, so 24 = 4x and x = 6."},
                        {"type": "activity", "title": "Proportion balance", "text": "Use a balance or drawing to show that 1/2 = 2/4 = 3/6."},
                    ],
                    "check": {
                        "prompt": "Show what you know about proportions.",
                        "questions": [
                            {"q": "Which is a proportion?", "options": ["2/3 = 4/6", "2 + 3 = 4 + 6", "2 × 3 = 4 × 6"], "answer": "2/3 = 4/6", "explain": "A proportion states two ratios are equal."},
                            {"q": "If 5/6 = x/12, what is x?", "options": ["10", "6", "12"], "answer": "10", "explain": "Cross multiply: 5 × 12 = 6 × x → 60 = 6x → x = 10."},
                            {"q": "Cross products help you…", "options": ["solve proportions", "add fractions", "find area"], "answer": "solve proportions", "explain": "Cross products create an equation you can solve for the missing number."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "integers",
            "title": "Integers",
            "summary": "Order, compare, and operate with positive and negative numbers.",
            "order": 5,
            "lessons": [
                {
                    "slug": "positive-and-negative",
                    "title": "Positive and Negative Numbers",
                    "order": 6,
                    "minutes": 15,
                    "summary": "Understand integers and their order on a number line.",
                    "learn": [
                        {"type": "p", "text": "Integers are whole numbers and their opposites: ... −3, −2, −1, 0, 1, 2, 3 ... Negative numbers are less than zero. Positive numbers are greater than zero."},
                        {"type": "list", "items": [
                            "The farther right, the greater the number.",
                            "−1 is greater than −3 because it is to the right.",
                            "Opposites are the same distance from 0 on opposite sides.",
                        ]},
                        {"type": "activity", "title": "Number-line walk", "text": "Start at 0. Walk forward 4, back 6, forward 2. Where do you end up?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about positive and negative numbers.",
                        "questions": [
                            {"q": "Which is greater: −2 or −5?", "options": ["−2", "−5", "equal"], "answer": "−2", "explain": "−2 is to the right of −5, so it is greater."},
                            {"q": "The opposite of 4 is…", "options": ["−4", "4", "0"], "answer": "−4", "explain": "Opposites are the same distance from 0 on the other side."},
                            {"q": "Which integer is farthest to the left?", "options": ["−8", "3", "0"], "answer": "−8", "explain": "The farther left, the smaller the integer."},
                        ],
                    },
                },
                {
                    "slug": "adding-integers",
                    "title": "Adding Integers",
                    "order": 7,
                    "minutes": 15,
                    "summary": "Use a number line to add positive and negative integers.",
                    "learn": [
                        {"type": "p", "text": "Adding a positive moves right. Adding a negative moves left. 3 + (−5): start at 3, move left 5 → −2. Same signs: add and keep the sign. Different signs: subtract and keep the sign of the larger absolute value."},
                        {"type": "list", "items": [
                            "3 + 5 = 8 (both positive, add)",
                            "−3 + (−5) = −8 (both negative, add, keep negative)",
                            "3 + (−5) = −2 (different signs, subtract 3 from 5, keep negative)",
                            "−3 + 5 = 2 (different signs, subtract 3 from 5, keep positive)",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about adding integers.",
                        "questions": [
                            {"q": "−4 + (−3) =", "options": ["−7", "−1", "7"], "answer": "−7", "explain": "Same sign: add absolute values and keep the negative sign."},
                            {"q": "5 + (−8) =", "options": ["−3", "3", "13"], "answer": "−3", "explain": "Different signs: subtract 5 from 8 and keep the sign of 8."},
                            {"q": "−2 + 6 =", "options": ["4", "−4", "8"], "answer": "4", "explain": "Different signs: subtract 2 from 6 and keep the positive sign."},
                        ],
                    },
                },
                {
                    "slug": "algebraic-expressions",
                    "title": "Algebraic Expressions",
                    "order": 8,
                    "minutes": 18,
                    "summary": "Write, read, and evaluate expressions with variables.",
                    "learn": [
                        {"type": "p", "text": "An algebraic expression uses numbers, operations, and variables. A variable stands for a number. Evaluate means substitute a value for the variable and compute."},
                        {"type": "example", "title": "Evaluate", "text": "Evaluate 3x + 2 when x = 4. 3(4) + 2 = 12 + 2 = 14."},
                        {"type": "list", "items": [
                            "Use the dot (·) or parentheses for multiplication so x is not confused with ×.",
                            "3x means 3 × x.",
                            "Follow the order of operations.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about algebraic expressions.",
                        "questions": [
                            {"q": "What is the value of 2x + 5 when x = 3?", "options": ["11", "6", "8"], "answer": "11", "explain": "2(3) + 5 = 6 + 5 = 11."},
                            {"q": "4y means…", "options": ["4 × y", "4 + y", "4 − y"], "answer": "4 × y", "explain": "A number next to a variable means multiplication."},
                            {"q": "Evaluate 5 + 2x when x = 4.", "options": ["13", "10", "18"], "answer": "13", "explain": "5 + 2(4) = 5 + 8 = 13."},
                        ],
                    },
                },
            ],
        },
    ],
}
