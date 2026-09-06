"""Mathematics — Grade 2 (full published course)."""

MATH_GRADE_2 = {
    "slug": "math-grade-2",
    "title": "Mathematics — Grade 2",
    "summary": "Place value to 1,000, addition/subtraction fluency, and measurement.",
    "description": (
        "Second-grade math deepens number sense and introduces three-digit place value. "
        "Students become fluent with addition and subtraction within 100, tell time, "
        "measure lengths, and work with money. Every lesson connects math to everyday situations."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["2"],
    "grade_label": "Grade 2",
    "status": "published",
    "audience": "Grade 2 (ages 7–8), Foundations track.",
    "est_hours": 20,
    "passing_score": 80,
    "learning_objectives": [
        "Read and write numbers to 1,000 using place value.",
        "Add and subtract within 100 with and without regrouping.",
        "Tell and write time to the nearest five minutes.",
        "Measure lengths using standard units.",
        "Solve word problems involving money.",
    ],
    "units": [
        {
            "slug": "place-value-addition-subtraction",
            "title": "Place Value and Operations",
            "summary": "Three-digit place value and fluent addition and subtraction.",
            "order": 1,
            "lessons": [
                {
                    "slug": "place-value-to-1000",
                    "title": "Place Value to 1,000",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Understand hundreds, tens, and ones.",
                    "learn": [
                        {"type": "p", "text": "A three-digit number has hundreds, tens, and ones. The number 347 has 3 hundreds, 4 tens, and 7 ones. This is called expanded form: 300 + 40 + 7."},
                        {"type": "list", "items": [
                            "Count by hundreds: 100, 200, 300…",
                            "Skip count by 5s, 10s, and 100s.",
                            "A bundle of ten tens is one hundred.",
                        ]},
                        {"type": "example", "title": "Build 529", "text": "Hundreds: 5 bundles of 100. Tens: 2 bundles of 10. Ones: 9 single cubes. Expanded form: 500 + 20 + 9."},
                        {"type": "activity", "title": "Base-ten blocks", "text": "Use base-ten blocks or drawings to show 286. Say the expanded form aloud."},
                    ],
                    "check": {
                        "prompt": "Show what you know about place value to 1,000.",
                        "questions": [
                            {"q": "In 462, how many tens are there?", "options": ["6", "4", "2"], "answer": "6", "explain": "The tens digit is 6, meaning 6 tens (60)."},
                            {"q": "What is 300 + 40 + 8?", "options": ["348", "3048", "38"], "answer": "348", "explain": "300 + 40 + 8 = 348."},
                            {"q": "Which number has 5 hundreds, 0 tens, and 3 ones?", "options": ["503", "530", "53"], "answer": "503", "explain": "5 hundreds = 500, 0 tens = 0, 3 ones = 3. Total 503."},
                        ],
                    },
                },
                {
                    "slug": "addition-within-100",
                    "title": "Addition Within 100",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Add two-digit numbers with and without regrouping.",
                    "learn": [
                        {"type": "p", "text": "Add two-digit numbers by adding ones and then tens. Sometimes the ones make 10 or more — that means you regroup 10 ones into 1 ten."},
                        {"type": "example", "title": "Add 45 + 28", "text": "Ones: 5 + 8 = 13. Write 3 in the ones place and carry 1 ten. Tens: 4 + 2 + 1 carried = 7. Answer: 73."},
                        {"type": "tip", "text": "Always add the ones column first. If the sum is 10 or more, regroup by moving one group of ten to the tens column."},
                        {"type": "activity", "title": "Spin and add", "text": "Spin two number wheels (10–90) and add them. Check your work with a partner."},
                    ],
                    "check": {
                        "prompt": "Show what you know about addition within 100.",
                        "questions": [
                            {"q": "What is 37 + 24?", "options": ["61", "51", "71"], "answer": "61", "explain": "7 + 4 = 11 (write 1, carry 1); 3 + 2 + 1 = 6. Answer 61."},
                            {"q": "What is 59 + 33?", "options": ["92", "82", "72"], "answer": "92", "explain": "9 + 3 = 12 (write 2, carry 1); 5 + 3 + 1 = 9. Answer 92."},
                        ],
                    },
                },
                {
                    "slug": "subtraction-within-100",
                    "title": "Subtraction Within 100",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Subtract two-digit numbers, borrowing when needed.",
                    "learn": [
                        {"type": "p", "text": "Subtract two-digit numbers by subtracting the ones first. If the top ones digit is smaller than the bottom ones digit, borrow 1 ten (10 ones) from the tens place."},
                        {"type": "example", "title": "Subtract 52 − 27", "text": "Ones: 2 is smaller than 7, so borrow 1 ten from 5, making it 4. The 2 becomes 12. 12 − 7 = 5. Tens: 4 − 2 = 2. Answer: 25."},
                        {"type": "activity", "title": "Check with addition", "text": "Solve 64 − 38. Then check by adding your answer to 38: 26 + 38 = 64. Does it match?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about subtraction within 100.",
                        "questions": [
                            {"q": "What is 64 − 28?", "options": ["36", "46", "26"], "answer": "36", "explain": "14 − 8 = 6 (borrow 1 ten); 5 − 2 = 3. Answer 36."},
                            {"q": "What is 81 − 47?", "options": ["34", "44", "24"], "answer": "34", "explain": "11 − 7 = 4 (borrow 1 ten); 7 − 4 = 3. Answer 34."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "measurement",
            "title": "Measurement and Data",
            "summary": "Length, time, and money.",
            "order": 2,
            "lessons": [
                {
                    "slug": "length-measurement",
                    "title": "Measuring Length",
                    "order": 4,
                    "minutes": 15,
                    "summary": "Use inches and centimeters to measure objects.",
                    "learn": [
                        {"type": "p", "text": "We measure length to see how long something is. Common tools are rulers, yardsticks, and measuring tapes. Standard units are inches (in.) and centimeters (cm)."},
                        {"type": "list", "items": [
                            "Line up the zero end of the ruler with one end of the object.",
                            "Read the mark where the other end lines up.",
                            "Estimate first, then measure to check.",
                        ]},
                        {"type": "activity", "title": "Measure your desk", "text": "Measure your desk or table in inches. Write the length. Now measure the same edge in centimeters. Which number is bigger? Why?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about measuring length.",
                        "questions": [
                            {"q": "Which tool would you use to measure a pencil?", "options": ["a ruler", "a clock", "a scale"], "answer": "a ruler", "explain": "A ruler measures length."},
                            {"q": "If an eraser is 3 inches long, about how many centimeters is it?", "options": ["7.5", "3", "12"], "answer": "7.5", "explain": "1 inch is about 2.5 cm, so 3 inches is about 7.5 cm."},
                        ],
                    },
                },
                {
                    "slug": "time-and-money",
                    "title": "Time and Money",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Tell time to the nearest five minutes and count coins.",
                    "learn": [
                        {"type": "p", "text": "An analog clock has an hour hand and a minute hand. When the minute hand points to 12, it is exactly o'clock. When it points to 3, it is quarter past."},
                        {"type": "list", "items": [
                            "Hour hand = shorter hand. Minute hand = longer hand.",
                            "Skip count by 5s to read minutes: 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55.",
                            "A penny = 1¢, nickel = 5¢, dime = 10¢, quarter = 25¢.",
                        ]},
                        {"type": "example", "title": "Reading 2:30", "text": "Hour hand is halfway between 2 and 3. Minute hand points to 6 (30 minutes). It is 2:30."},
                        {"type": "activity", "title": "Clock hunt", "text": "Look at clocks around your house. Write down three different times you see."},
                    ],
                    "check": {
                        "prompt": "Show what you know about time and money.",
                        "questions": [
                            {"q": "When the minute hand points to 6, how many minutes have passed?", "options": ["30", "6", "60"], "answer": "30", "explain": "Each number on the clock is 5 minutes: 6 × 5 = 30."},
                            {"q": "What is the value of 3 dimes and 2 pennies?", "options": ["32¢", "5¢", "12¢"], "answer": "32¢", "explain": "3 × 10¢ + 2 × 1¢ = 30¢ + 2¢ = 32¢."},
                            {"q": "The clock shows the hour hand between 8 and 9 and the minute hand on 3. What time is it?", "options": ["8:15", "9:15", "8:45"], "answer": "8:15", "explain": "Hour hand is past 8 but not to 9; minute hand at 3 is 15 minutes."},
                        ],
                    },
                },
            ],
        },
    ],
}
