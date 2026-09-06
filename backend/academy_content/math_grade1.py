"""Mathematics — Grade 1 (full published course)."""

MATH_GRADE_1 = {
    "slug": "math-grade-1",
    "title": "Mathematics — Grade 1",
    "summary": "Addition and subtraction within 20, place value, and shapes.",
    "description": (
        "First-grade math builds the foundation for all later computation. "
        "This course covers counting to 120, understanding tens and ones, "
        "adding and subtracting within 20, and identifying basic shapes. "
        "Each lesson uses visual models, story problems, and hands-on activities."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["1"],
    "grade_label": "Grade 1",
    "status": "published",
    "audience": "Grade 1 (ages 6–7), Foundations track.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": [
        "Count forward to 120 and read/write numerals.",
        "Understand tens and ones in two-digit numbers.",
        "Add and subtract within 20 using strategies.",
        "Solve word problems with addition and subtraction.",
        "Identify and describe basic two- and three-dimensional shapes.",
    ],
    "units": [
        {
            "slug": "addition-subtraction",
            "title": "Addition and Subtraction Within 20",
            "summary": "Build fluency with facts and strategies to 20.",
            "order": 1,
            "lessons": [
                {
                    "slug": "counting-120",
                    "title": "Counting to 120",
                    "order": 1,
                    "minutes": 15,
                    "summary": "Count forward, read numerals, and understand tens and ones.",
                    "learn": [
                        {"type": "p", "text": "First grade is all about building number sense. We count forward starting at any number, read and write numerals to 120, and break numbers into tens and ones."},
                        {"type": "list", "items": [
                            "Count by ones to 120: 1, 2, 3… 120.",
                            "Count by tens: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120.",
                            "The number 23 has 2 tens and 3 ones.",
                        ]},
                        {"type": "activity", "title": "Number hunt", "text": "Find numbers around your home from 1 to 120. Read each one aloud and say how many tens and ones it has."},
                    ],
                    "check": {
                        "prompt": "Show what you know about counting to 120.",
                        "questions": [
                            {"q": "What number has 3 tens and 5 ones?", "options": ["35", "53", "305"], "answer": "35", "explain": "3 tens is 30 plus 5 ones equals 35."},
                            {"q": "What comes after 118 when counting by ones?", "options": ["119", "120", "128"], "answer": "119", "explain": "118 + 1 = 119."},
                            {"q": "Count by tens from 20. What comes next?", "options": ["30", "21", "200"], "answer": "30", "explain": "Counting by tens adds 10 each time: 20, 30, 40…"},
                        ],
                    },
                },
                {
                    "slug": "addition-within-10",
                    "title": "Addition Within 10",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Use counting, number bonds, and pictures to add within 10.",
                    "learn": [
                        {"type": "p", "text": "Addition means putting together. You can use your fingers, drawings, or number bonds. A number bond shows how two smaller numbers make a larger one."},
                        {"type": "example", "title": "Number bond", "text": "To add 4 + 3, draw 4 circles and 3 circles. Count them all: 1, 2, 3, 4, 5, 6, 7. So 4 + 3 = 7."},
                        {"type": "tip", "text": "When adding, it helps to start with the bigger number and count on. For 3 + 5, start at 5 and count on 3 more: 6, 7, 8."},
                        {"type": "activity", "title": "Finger sums", "text": "Work with a partner. One partner says an addition problem within 10. The other shows the answer on fingers and explains how they got it."},
                    ],
                    "check": {
                        "prompt": "Show what you know about addition within 10.",
                        "questions": [
                            {"q": "What is 6 + 4?", "options": ["10", "9", "11"], "answer": "10", "explain": "6 + 4 makes a whole group of 10."},
                            {"q": "Which shows 2 + 5?", "options": ["7", "6", "8"], "answer": "7", "explain": "2 + 5 = 7."},
                            {"q": "If you have 3 apples and get 4 more, how many do you have?", "options": ["7", "8", "6"], "answer": "7", "explain": "3 + 4 = 7 apples."},
                        ],
                    },
                },
                {
                    "slug": "subtraction-within-10",
                    "title": "Subtraction Within 10",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Take away, compare, and find the missing part.",
                    "learn": [
                        {"type": "p", "text": "Subtraction means taking away or finding the difference. You can cross out drawings or count back on a number line."},
                        {"type": "example", "title": "Take-away subtraction", "text": "There are 8 cookies. You eat 3. Cross out 3 cookies. Count what is left: 5. So 8 − 3 = 5."},
                        {"type": "activity", "title": "Story problems", "text": "Write three subtraction stories about things in your home. Each story should have a total and a part that is taken away."},
                    ],
                    "check": {
                        "prompt": "Show what you know about subtraction within 10.",
                        "questions": [
                            {"q": "What is 9 − 4?", "options": ["5", "4", "6"], "answer": "5", "explain": "Start at 9 and count back 4: 8, 7, 6, 5."},
                            {"q": "You have 7 stickers and give 2 away. How many are left?", "options": ["5", "6", "9"], "answer": "5", "explain": "7 − 2 = 5 stickers left."},
                            {"q": "Which number completes 8 − ? = 3?", "options": ["5", "6", "11"], "answer": "5", "explain": "8 − 5 = 3."},
                        ],
                    },
                },
                {
                    "slug": "addition-subtraction-fact-families",
                    "title": "Addition and Subtraction Fact Families",
                    "order": 4,
                    "minutes": 15,
                    "summary": "See how addition and subtraction are related.",
                    "learn": [
                        {"type": "p", "text": "Numbers that belong together make a fact family. For 3, 4, and 7, the facts are 3 + 4 = 7, 4 + 3 = 7, 7 − 3 = 4, and 7 − 4 = 3. Knowing one fact helps you know three more."},
                        {"type": "example", "title": "Fact family triangle", "text": "Write 2, 5, and 7 in a triangle. The bottom is the whole (7). The top numbers are the parts (2 and 5). Write all four facts."},
                        {"type": "tip", "text": "If you forget 9 − 5, think: 5 + ? = 9. The answer is 4, so 9 − 5 = 4."},
                    ],
                    "check": {
                        "prompt": "Show what you know about fact families.",
                        "questions": [
                            {"q": "Which fact belongs with 3 + 6 = 9?", "options": ["9 − 6 = 3", "9 + 6 = 3", "3 − 6 = 9"], "answer": "9 − 6 = 3", "explain": "The same three numbers make addition and subtraction facts."},
                            {"q": "What is the whole in the fact family for 4, 5, and 9?", "options": ["9", "5", "4"], "answer": "9", "explain": "The whole is the largest number: 9."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "place-value-shapes",
            "title": "Place Value and Shapes",
            "summary": "Compare numbers and identify two- and three-dimensional shapes.",
            "order": 2,
            "lessons": [
                {
                    "slug": "comparing-two-digit-numbers",
                    "title": "Comparing Two-Digit Numbers",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Use >, <, and = to compare numbers to 120.",
                    "learn": [
                        {"type": "p", "text": "To compare two-digit numbers, look at the tens place first. If the tens are different, the number with more tens is bigger. If the tens are the same, compare the ones."},
                        {"type": "list", "items": [
                            "> means greater than (more).",
                            "< means less than (fewer).",
                            "= means equal (the same).",
                        ]},
                        {"type": "example", "title": "Compare 47 and 52", "text": "Tens: 4 in 47, 5 in 52. 5 > 4, so 52 > 47. We write 47 < 52."},
                        {"type": "tip", "text": "The alligator mouth always opens to the bigger number. < is the alligator that eats the bigger number."},
                    ],
                    "check": {
                        "prompt": "Show what you know about comparing two-digit numbers.",
                        "questions": [
                            {"q": "Which symbol makes this true: 68 ___ 78?", "options": ["<", ">", "="], "answer": "<", "explain": "68 has 6 tens and 78 has 7 tens, so 68 is less than 78."},
                            {"q": "Which is greater: 85 or 83?", "options": ["85", "83", "they are equal"], "answer": "85", "explain": "The tens are the same (8). Compare ones: 5 > 3, so 85 is greater."},
                            {"q": "What does the symbol = mean?", "options": ["equal to", "greater than", "less than"], "answer": "equal to", "explain": "= means the two amounts are the same."},
                        ],
                    },
                },
                {
                    "slug": "two-and-three-dimensional-shapes",
                    "title": "Two- and Three-Dimensional Shapes",
                    "order": 6,
                    "minutes": 15,
                    "summary": "Name, sort, and describe flat and solid shapes.",
                    "learn": [
                        {"type": "p", "text": "Two-dimensional (2D) shapes are flat: circle, triangle, square, rectangle, pentagon, hexagon. Three-dimensional (3D) shapes are solid: cube, rectangular prism, sphere, cone, cylinder."},
                        {"type": "list", "items": [
                            "2D shapes have sides and corners (vertices).",
                            "3D shapes have faces, edges, and vertices.",
                            "A square is a special rectangle because it has 4 sides and 4 right angles.",
                        ]},
                        {"type": "example", "title": "Identify shapes around you", "text": "A book is a rectangular prism. A can is a cylinder. A basketball is a sphere. A block is a cube."},
                        {"type": "activity", "title": "Shape scavenger hunt", "text": "Find one example of each 3D shape in your home. Draw or photograph it and write its name."},
                    ],
                    "check": {
                        "prompt": "Show what you know about shapes.",
                        "questions": [
                            {"q": "A solid shape with 6 square faces is a…", "options": ["cube", "cylinder", "triangle"], "answer": "cube", "explain": "A cube has 6 identical square faces."},
                            {"q": "Which shape has 5 sides?", "options": ["pentagon", "hexagon", "rectangle"], "answer": "pentagon", "explain": "A pentagon has 5 sides and 5 angles."},
                            {"q": "A ball is shaped like a…", "options": ["sphere", "cone", "cylinder"], "answer": "sphere", "explain": "A sphere is perfectly round, like a ball."},
                        ],
                    },
                },
            ],
        },
    ],
}
