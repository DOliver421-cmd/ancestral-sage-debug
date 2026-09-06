"""Mathematics — Grade 3 (full published course)."""

MATH_GRADE_3 = {
    "slug": "math-grade-3",
    "title": "Mathematics — Grade 3",
    "summary": "Multiplication, division, fractions, area, and perimeter.",
    "description": (
        "Third graders move from additive to multiplicative thinking. This course "
        "builds multiplication from equal groups and arrays, introduces division as "
        "sharing and grouping, and connects both to area and perimeter. It finishes "
        "with fractions as parts of a whole and on the number line. Every lesson "
        "pairs clear instruction with worked examples and a mastery check."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["3"],
    "grade_label": "Grade 3",
    "status": "published",
    "audience": "Grade 3 (ages 8–9), Foundations track; also useful for review.",
    "est_hours": 22,
    "passing_score": 80,
    "learning_objectives": [
        "Interpret multiplication as equal groups and arrays.",
        "Fluently multiply and divide within 100.",
        "Solve one-step word problems with multiplication and division.",
        "Understand fractions as parts of a whole and on a number line.",
        "Find equivalent fractions and compare fractions with like numerators or denominators.",
        "Find perimeter and area of rectangles on a grid.",
    ],
    "units": [
        {
            "slug": "multiplication-and-division",
            "title": "Multiplication and Division",
            "summary": "From equal groups to facts within 100.",
            "order": 1,
            "lessons": [
                {
                    "slug": "multiplication-as-groups",
                    "title": "Multiplication as Equal Groups",
                    "order": 2,
                    "minutes": 18,
                    "summary": "See multiplication as repeated addition of equal groups.",
                    "learn": [
                        {"type": "p", "text": "Multiplication is fast counting of EQUAL groups. 4 bags with 3 apples each: 4 groups of 3. 3 + 3 + 3 + 3 = 12, or simply 4 × 3 = 12. The × symbol means 'groups of.'"},
                        {"type": "list", "items": [
                            "The first factor is the number of groups.",
                            "The second factor is the size of each group.",
                            "The answer is called the product.",
                            "Arrays show rows × columns = total.",
                        ]},
                        {"type": "activity", "title": "Array build", "text": "Draw a 3 × 5 array of dots. Count by groups: 3 rows of 5 = 15. Now turn it: 5 rows of 3 still equals 15."},
                    ],
                    "check": {
                        "prompt": "Show what you know about multiplication as groups.",
                        "questions": [
                            {"q": "3 groups of 4 is written as…", "options": ["3 × 4", "3 + 4", "3 − 4"], "answer": "3 × 4", "explain": "3 groups of 4 is 3 × 4 = 12."},
                            {"q": "An array has 5 rows with 2 in each row. How many in all?", "options": ["10", "7", "52"], "answer": "10", "explain": "5 rows of 2 is 5 × 2 = 10."},
                            {"q": "What is the answer to a multiplication problem called?", "options": ["product", "sum", "difference"], "answer": "product", "explain": "Multiplying gives the product."},
                        ],
                    },
                },
                {
                    "slug": "division-as-sharing",
                    "title": "Division as Sharing",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Understand division as sharing equally into groups.",
                    "learn": [
                        {"type": "p", "text": "Division means sharing equally. If 12 cookies go onto 3 plates, each plate gets 4 cookies: 12 ÷ 3 = 4. Division is the reverse of multiplication."},
                        {"type": "list", "items": [
                            "The dividend is what you are sharing.",
                            "The divisor is how many groups you share into.",
                            "The quotient is how many each group gets.",
                            "Multiplication and division are fact families.",
                        ]},
                        {"type": "example", "title": "Fact family", "text": "3 × 4 = 12, so 12 ÷ 3 = 4 and 12 ÷ 4 = 3. Same numbers, different operations."},
                    ],
                    "check": {
                        "prompt": "Show what you know about division.",
                        "questions": [
                            {"q": "15 ÷ 3 =", "options": ["5", "3", "12"], "answer": "5", "explain": "3 groups of 5 make 15, so 15 ÷ 3 = 5."},
                            {"q": "Which multiplication fact helps you solve 24 ÷ 6?", "options": ["4 × 6 = 24", "6 × 6 = 36", "3 × 6 = 18"], "answer": "4 × 6 = 24", "explain": "If 4 groups of 6 make 24, then 24 ÷ 6 = 4."},
                            {"q": "In 18 ÷ 2 = 9, the 9 is called the…", "options": ["quotient", "divisor", "dividend"], "answer": "quotient", "explain": "The answer in division is the quotient."},
                        ],
                    },
                },
                {
                    "slug": "multiplying-by-0-1-10",
                    "title": "Multiplying by 0, 1, and 10",
                    "order": 4,
                    "minutes": 12,
                    "summary": "Master the easy but essential facts.",
                    "learn": [
                        {"type": "p", "text": "Some multiplication facts have simple rules. n × 0 = 0. n × 1 = n. n × 10 attaches a zero (because 10 = 1 ten)."},
                        {"type": "list", "items": [
                            "7 × 0 = 0",
                            "7 × 1 = 7",
                            "7 × 10 = 70",
                            "Use place value: 7 × 10 = 7 tens = 70.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about 0, 1, and 10.",
                        "questions": [
                            {"q": "What is 9 × 0?", "options": ["0", "9", "1"], "answer": "0", "explain": "Any number times 0 is 0."},
                            {"q": "What is 9 × 1?", "options": ["9", "1", "90"], "answer": "9", "explain": "Any number times 1 stays the same."},
                            {"q": "What is 9 × 10?", "options": ["90", "100", "91"], "answer": "90", "explain": "9 × 10 = 9 tens = 90."},
                        ],
                    },
                },
                {
                    "slug": "properties-of-multiply",
                    "title": "Properties of Multiplication",
                    "order": 5,
                    "minutes": 15,
                    "summary": "Use commutative, associative, and distributive properties.",
                    "learn": [
                        {"type": "p", "text": "Multiplication has helpful properties. The commutative property says 3 × 5 = 5 × 3. The associative property lets you regroup: (2 × 3) × 4 = 2 × (3 × 4). The distributive property splits a hard fact into easier ones: 6 × 7 = 6 × 5 + 6 × 2."},
                        {"type": "example", "title": "Distributive shortcut", "text": "To find 8 × 7, think 8 × 5 + 8 × 2 = 40 + 16 = 56."},
                    ],
                    "check": {
                        "prompt": "Show what you know about multiplication properties.",
                        "questions": [
                            {"q": "Which shows the commutative property?", "options": ["3 × 5 = 5 × 3", "(2 × 3) × 4 = 2 × (3 × 4)", "6 × 7 = 6 × 5 + 6 × 2"], "answer": "3 × 5 = 5 × 3", "explain": "Commutative means you can swap the order."},
                            {"q": "8 × 6 = 8 × 5 + 8 × ?", "options": ["1", "6", "11"], "answer": "1", "explain": "Split 6 into 5 + 1 to use the distributive property."},
                            {"q": "(2 × 4) × 3 = 2 × (4 × 3) shows…", "options": ["associative property", "distributive property", "identity property"], "answer": "associative property", "explain": "Associative means you can regroup factors without changing the product."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "fractions",
            "title": "Fractions",
            "summary": "Parts of a whole, equivalence, and comparison.",
            "order": 6,
            "lessons": [
                {
                    "slug": "unit-fractions",
                    "title": "Unit Fractions",
                    "order": 7,
                    "minutes": 15,
                    "summary": "Name and write fractions as parts of one whole.",
                    "learn": [
                        {"type": "p", "text": "A fraction names parts of a whole. The bottom number, the denominator, tells how many equal parts the whole is cut into. The top number, the numerator, tells how many parts you have."},
                        {"type": "list", "items": [
                            "1/2 = one of two equal parts",
                            "1/3 = one of three equal parts",
                            "1/4 = one of four equal parts",
                            "Equal parts must be the same size.",
                        ]},
                        {"type": "activity", "title": "Paper fold", "text": "Fold a paper in half, then in fourths, then in eighths. Label each piece with its fraction."},
                    ],
                    "check": {
                        "prompt": "Show what you know about unit fractions.",
                        "questions": [
                            {"q": "In 1/4, the 4 tells you…", "options": ["how many equal parts", "how many parts you have", "the whole number"], "answer": "how many equal parts", "explain": "The denominator tells how many equal parts make the whole."},
                            {"q": "Which picture shows 1/3?", "options": ["one of three equal pieces", "one of two equal pieces", "three whole pieces"], "answer": "one of three equal pieces", "explain": "1/3 means one part of three equal parts."},
                            {"q": "If a pizza is cut into 4 equal slices, each slice is…", "options": ["1/4", "4/1", "1/5"], "answer": "1/4", "explain": "Each of 4 equal slices is one-fourth of the pizza."},
                        ],
                    },
                },
                {
                    "slug": "equivalent-fractions",
                    "title": "Equivalent Fractions",
                    "order": 8,
                    "minutes": 15,
                    "summary": "Find fractions that name the same amount.",
                    "learn": [
                        {"type": "p", "text": "Equivalent fractions name the same amount. 1/2 = 2/4 = 3/6. If you cut a whole into more pieces, you need more pieces to cover the same amount."},
                        {"type": "list", "items": [
                            "Multiply the numerator and denominator by the same number.",
                            "1/2 × 2/2 = 2/4.",
                            "Equivalent fractions line up on a number line.",
                        ]},
                        {"type": "activity", "title": "Number-line hunt", "text": "Mark 0, 1/2, and 1 on a number line. Now mark 2/4 and 3/6. Do they land on the same spots?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about equivalent fractions.",
                        "questions": [
                            {"q": "Which fraction is equivalent to 1/2?", "options": ["2/4", "1/3", "3/4"], "answer": "2/4", "explain": "1/2 = 2/4 because both name the same amount."},
                            {"q": "To find an equivalent fraction, you can…", "options": ["multiply numerator and denominator by the same number", "add 1 to both", "subtract 1 from both"], "answer": "multiply numerator and denominator by the same number", "explain": "Multiplying both by the same number keeps the value the same."},
                            {"q": "1/3 = ?/6", "options": ["2", "3", "1"], "answer": "2", "explain": "Multiply top and bottom by 2: 1/3 = 2/6."},
                        ],
                    },
                },
                {
                    "slug": "comparing-fractions",
                    "title": "Comparing Fractions",
                    "order": 9,
                    "minutes": 15,
                    "summary": "Use symbols >, <, and = to compare fractions.",
                    "learn": [
                        {"type": "p", "text": "When fractions have the same numerator or denominator, comparison is easy. Same denominator: more pieces means a larger amount. Same numerator: larger pieces means a larger amount."},
                        {"type": "list", "items": [
                            "3/5 > 2/5 because thirds are bigger than fifths? No — same denominator, so more pieces wins: 3/5 > 2/5.",
                            "1/2 > 1/4 because halves are bigger than fourths.",
                            "Draw or model to compare when unsure.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about comparing fractions.",
                        "questions": [
                            {"q": "Which is greater: 3/8 or 5/8?", "options": ["5/8", "3/8", "they are equal"], "answer": "5/8", "explain": "Same denominator, so the larger numerator wins."},
                            {"q": "Which is greater: 1/3 or 1/4?", "options": ["1/3", "1/4", "equal"], "answer": "1/3", "explain": "Same numerator, so the smaller denominator (bigger piece) wins."},
                            {"q": "Compare: 2/6 and 1/3.", "options": ["2/6 = 1/3", "2/6 > 1/3", "2/6 < 1/3"], "answer": "2/6 = 1/3", "explain": "2/6 simplifies to 1/3, so they are equal."},
                        ],
                    },
                },
                {
                    "slug": "area-and-perimeter",
                    "title": "Area and Perimeter",
                    "order": 10,
                    "minutes": 18,
                    "summary": "Find the perimeter and area of rectangles.",
                    "learn": [
                        {"type": "p", "text": "Perimeter is the distance around a shape. Area is the space inside. For a rectangle, add the side lengths for perimeter, and multiply length × width for area."},
                        {"type": "example", "title": "Worked example", "text": "A rectangle is 5 cm long and 3 cm wide. Perimeter = 5 + 3 + 5 + 3 = 16 cm. Area = 5 × 3 = 15 square cm."},
                        {"type": "activity", "title": "Grid drawing", "text": "Draw rectangles on grid paper with area 12, 16, and 20 square units. Find their perimeters."},
                    ],
                    "check": {
                        "prompt": "Show what you know about area and perimeter.",
                        "questions": [
                            {"q": "The perimeter of a rectangle is…", "options": ["the distance around it", "the space inside it", "its length"], "answer": "the distance around it", "explain": "Perimeter measures the outside edge."},
                            {"q": "A rectangle 4 by 6 has an area of…", "options": ["24", "20", "10"], "answer": "24", "explain": "Area = length × width = 4 × 6 = 24 square units."},
                            {"q": "A square has sides 5. Its perimeter is…", "options": ["20", "25", "10"], "answer": "20", "explain": "4 sides × 5 = 20."},
                        ],
                    },
                },
            ],
        },
    ],
}
