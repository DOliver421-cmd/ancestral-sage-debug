"""Multiplication, Division, and Fractions (Grade 4) — full published course."""

MATH_GRADE_4 = {
    "slug": "multiplication-division-fractions-grade-4",
    "title": "Multiplication, Division, and Fractions",
    "summary": "From equal groups to long division to real fractions.",
    "description": (
        "Fourth graders make the leap from counting to computing. This course builds "
        "multiplication from equal groups and arrays, carries it into one-digit-times-"
        "multi-digit problems, then treats division as the reverse — sharing, grouping, "
        "and the long-division algorithm. It finishes with fractions: equal parts, "
        "equivalence, comparing, and adding fractions with like denominators. Every "
        "lesson pairs a clear explanation with worked examples and a mastery check."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["4"],
    "grade_label": "Grade 4",
    "status": "published",
    "audience": "Grade 4 (ages 9–10), Foundations track; also useful for older students who need the arithmetic foundation.",
    "est_hours": 20,
    "passing_score": 80,
    "learning_objectives": [
        "Model multiplication with equal groups, arrays, and skip counting.",
        "Multiply a multi-digit number by a one-digit number, including with regrouping.",
        "Understand division as sharing and grouping, and divide with remainders.",
        "Use the standard long-division algorithm for 2- and 3-digit dividends.",
        "Read and write fractions, recognize equivalence, compare fractions, and add or subtract fractions with like denominators.",
        "Solve real-world word problems with multiplication and division.",
    ],
    "units": [
        {
            "slug": "multiplication",
            "title": "Multiplication",
            "summary": "Equal groups, arrays, and multiplying big numbers.",
            "order": 1,
            "lessons": [
                {
                    "slug": "multiplication-groups-arrays",
                    "title": "Equal Groups and Arrays",
                    "order": 1,
                    "minutes": 18,
                    "summary": "See multiplication as equal groups and as rows of an array.",
                    "learn": [
                        {"type": "p", "text": "Multiplication is fast counting of EQUAL groups. If 4 bags each hold 3 apples, you have 4 groups of 3. Instead of counting 3 + 3 + 3 + 3, multiply: 4 × 3 = 12."},
                        {"type": "p", "text": "Read the × symbol as \"groups of\": 4 × 3 means 4 groups of 3. The answer is called the PRODUCT."},
                        {"type": "example", "title": "Arrays make it visual", "text": "An array arranges things in rows. An array with 3 rows and 5 in each row has 3 × 5 = 15 dots. Rows × dots-per-row = total. Turning the array around (5 rows of 3) still gives 15 — that is the commutative property: 3 × 5 = 5 × 3."},
                        {"type": "activity", "title": "Build an array", "text": "Make a 2 × 6 array with coins or cereal pieces (2 rows, 6 in each row). Count the total: 2 × 6 = 12. Now turn it into 6 rows of 2. Same total!"},
                    ],
                    "check": {
                        "prompt": "Show what you know about equal groups and arrays.",
                        "questions": [
                            {"q": "There are 5 boxes with 4 crayons in each. Which expression counts all the crayons?", "options": ["5 × 4", "5 + 4", "5 − 4"], "answer": "5 × 4", "explain": "You have 5 groups of 4, which is 5 × 4 = 20."},
                            {"q": "An array has 4 rows with 6 dots in each row. How many dots in all?", "options": ["24", "10", "46"], "answer": "24", "explain": "4 rows of 6 is 4 × 6 = 24."},
                            {"q": "3 × 7 = 21, so 7 × 3 must equal…", "options": ["21", "10", "73"], "answer": "21", "explain": "Multiplication is commutative: 7 × 3 gives the same product as 3 × 7."},
                            {"q": "What do we call the answer to a multiplication problem?", "options": ["the product", "the sum", "the difference"], "answer": "the product", "explain": "Adding gives a sum, subtracting gives a difference, and multiplying gives a product."},
                        ],
                    },
                },
                {
                    "slug": "skip-counting-patterns",
                    "title": "Skip Counting and Multiplication Patterns",
                    "order": 2,
                    "minutes": 15,
                    "summary": "Count by groups to find products and spot the patterns.",
                    "learn": [
                        {"type": "p", "text": "Skip counting is counting by a number other than 1. Counting by 3s: 3, 6, 9, 12, 15, 18, 21, 24… Each number is one more group of 3, so skip counting IS multiplication."},
                        {"type": "list", "items": [
                            "Count by 2s: 2, 4, 6, 8, 10, 12, 14, 16, 18, 20.",
                            "Count by 5s: 5, 10, 15, 20, 25, 30, 35, 40, 45, 50.",
                            "Multiples of 10 all end in 0: 10, 20, 30, 40, 50…",
                            "Pattern to know: any number × 1 stays the same, and any number × 0 is 0.",
                        ]},
                        {"type": "example", "title": "Use skip counting to multiply", "text": "What is 6 × 4? Skip count by 4 six times: 4, 8, 12, 16, 20, 24. The sixth number is 24, so 6 × 4 = 24."},
                        {"type": "activity", "title": "Clap the counts", "text": "Count by 4s aloud to 40 while clapping on each number. Which numbers did you clap? Those are the multiples of 4."},
                    ],
                    "check": {
                        "prompt": "Show what you know about skip counting.",
                        "questions": [
                            {"q": "Skip counting by 3s, what comes after 12?", "options": ["15", "13", "16"], "answer": "15", "explain": "Add 3 each time: 12 + 3 = 15."},
                            {"q": "Use skip counting to find 5 × 4.", "options": ["20", "9", "54"], "answer": "20", "explain": "Count by 4 five times: 4, 8, 12, 16, 20."},
                            {"q": "What is any number times 0?", "options": ["0", "the number itself", "1"], "answer": "0", "explain": "Zero groups of anything is nothing: n × 0 = 0."},
                            {"q": "Which number is a multiple of 5?", "options": ["35", "32", "37"], "answer": "35", "explain": "Multiples of 5 end in 5 or 0. 35 = 7 groups of 5."},
                        ],
                    },
                },
                {
                    "slug": "multiplying-tens",
                    "title": "Multiplying by Tens",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Use place value to multiply by 10, 20, 30…",
                    "learn": [
                        {"type": "p", "text": "Multiplying by a multiple of ten is easy when you use place value. 4 × 30 means 4 groups of 30. Think of 30 as 3 tens: 4 × 3 tens = 12 tens = 120."},
                        {"type": "example", "title": "Multiply the basic fact, then add the zero", "text": "6 × 40: first do 6 × 4 = 24, then 40 has one zero, so the product is 240. Check with place value: 6 × 4 tens = 24 tens = 240."},
                        {"type": "p", "text": "Rule of thumb: multiply the nonzero digits, then count the total zeros in the factors and attach them. 3 × 200 → 3 × 2 = 6, two zeros → 600."},
                        {"type": "activity", "title": "Mental math sprint", "text": "Solve in your head: 7 × 30, 5 × 60, 4 × 200. Remember: basic fact first, then attach the zeros."},
                    ],
                    "check": {
                        "prompt": "Show what you know about multiplying by tens.",
                        "questions": [
                            {"q": "What is 4 × 30?", "options": ["120", "34", "12"], "answer": "120", "explain": "4 × 3 = 12, and 30 has one zero, so the product is 120."},
                            {"q": "What is 6 × 200?", "options": ["1,200", "206", "12"], "answer": "1,200", "explain": "6 × 2 = 12, and 200 has two zeros, so the product is 1,200."},
                            {"q": "Which expression equals 150?", "options": ["5 × 30", "5 × 3", "50 × 3 × 10"], "answer": "5 × 30", "explain": "5 × 3 = 15, then attach one zero → 150."},
                        ],
                    },
                },
                {
                    "slug": "one-digit-times-multidigit",
                    "title": "One-Digit Times Multi-Digit (Regrouping)",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Multiply step by step from right to left, carrying as you go.",
                    "learn": [
                        {"type": "p", "text": "To multiply a big number by a one-digit number, work from right to left — ones place first — and regroup (carry) when a place makes more than 9."},
                        {"type": "example", "title": "Worked example: 3 × 46", "text": "Step 1: 3 × 6 ones = 18 ones. Write the 8 in the ones place and carry 1 ten. Step 2: 3 × 4 tens = 12 tens. Add the carried 1 ten: 13 tens. Write 3 in the tens place and 1 in the hundreds place. Answer: 138."},
                        {"type": "example", "title": "Worked example: 4 × 237", "text": "4 × 7 = 28 → write 8, carry 2. 4 × 3 = 12, + 2 carried = 14 → write 4, carry 1. 4 × 2 = 8, + 1 carried = 9. Answer: 948."},
                        {"type": "activity", "title": "Line up and multiply", "text": "Set up 2 × 358 on paper. Multiply ones, carry, multiply tens, carry, multiply hundreds. Check your answer against a friend or calculator: 716."},
                    ],
                    "check": {
                        "prompt": "Show what you know about multiplying with regrouping.",
                        "questions": [
                            {"q": "What is 3 × 46?", "options": ["138", "136", "49"], "answer": "138", "explain": "3 × 6 = 18 (write 8, carry 1); 3 × 4 = 12 plus the carried 1 = 13 → 138."},
                            {"q": "What is 4 × 237?", "options": ["948", "928", "241"], "answer": "948", "explain": "4 × 7 = 28 (write 8, carry 2); 4 × 3 + 2 = 14 (write 4, carry 1); 4 × 2 + 1 = 9 → 948."},
                            {"q": "In 6 × 58, what do you carry after multiplying the ones?", "options": ["4", "5", "8"], "answer": "4", "explain": "6 × 8 = 48. Write the 8 in the ones place and carry 4 tens."},
                            {"q": "What is 2 × 358?", "options": ["716", "616", "710"], "answer": "716", "explain": "2 × 8 = 16 (write 6, carry 1); 2 × 5 + 1 = 11 (write 1, carry 1); 2 × 3 + 1 = 7 → 716."},
                        ],
                    },
                },
                {
                    "slug": "multiplication-word-problems",
                    "title": "Multiplication Word Problems",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Spot the equal groups hiding in real-world problems.",
                    "learn": [
                        {"type": "p", "text": "Word problems hide math inside a story. Your job is to find the equal groups. Look for clue ideas: \"each,\" \"per,\" \"rows of,\" \"boxes of,\" \"times as many.\" If one item repeats the same number of times, that is multiplication."},
                        {"type": "list", "items": [
                            "Ask: Is something being counted in equal groups?",
                            "Ask: Do I know how many groups AND how many in each group?",
                            "Multiply groups × amount-in-each to find the total.",
                        ]},
                        {"type": "example", "title": "Worked example", "text": "A bus has 6 rows of seats with 4 seats in each row. How many seats? Groups: 6 rows. In each group: 4 seats. 6 × 4 = 24 seats."},
                        {"type": "example", "title": "Worked example: times as many", "text": "Jada has 12 stickers. Marcus has 3 times as many. Marcus has 12 × 3 = 36 stickers."},
                        {"type": "activity", "title": "Write your own", "text": "Invent a story for 7 × 5 using the word \"each.\" Example: \"Seven bags each hold 5 oranges. How many oranges?\" Solve it."},
                    ],
                    "check": {
                        "prompt": "Show what you know about multiplication word problems.",
                        "questions": [
                            {"q": "A shelf has 4 rows with 8 books on each row. How many books in all?", "options": ["32", "12", "84"], "answer": "32", "explain": "4 groups of 8 books: 4 × 8 = 32."},
                            {"q": "Nina runs 5 laps each day for 6 days. How many laps in all?", "options": ["30", "11", "56"], "answer": "30", "explain": "6 days of 5 laps: 6 × 5 = 30."},
                            {"q": "Leo has 9 marbles and Mia has 4 times as many. How many marbles does Mia have?", "options": ["36", "13", "94"], "answer": "36", "explain": "4 times as many as 9 is 9 × 4 = 36."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "division",
            "title": "Division",
            "summary": "The reverse of multiplication — sharing, grouping, remainders, and long division.",
            "order": 2,
            "lessons": [
                {
                    "slug": "division-sharing-remainders",
                    "title": "Division: Sharing, Grouping, and Remainders",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Split a total into equal parts — and handle what is left over.",
                    "learn": [
                        {"type": "p", "text": "Division splits a total into equal parts. It is the reverse of multiplication: if 4 × 6 = 24, then 24 ÷ 4 = 6 and 24 ÷ 6 = 4. The answer to a division problem is the QUOTIENT."},
                        {"type": "p", "text": "Sometimes a total does not split evenly. 14 cookies shared by 3 children: each child gets 4 cookies (3 × 4 = 12), and 2 cookies are left over. We say 14 ÷ 3 = 4 remainder 2. The left-over part is the REMAINDER, and it must always be smaller than the divisor."},
                        {"type": "example", "title": "Two ways to divide", "text": "20 ÷ 5 can mean: (a) sharing — split 20 into 5 equal groups → 4 each; or (b) grouping — how many groups of 5 fit in 20? → 4 groups. Both give the quotient 4."},
                        {"type": "activity", "title": "Share the counters", "text": "Take 23 counters and share them into 4 equal piles. How many in each pile? How many are left over? 23 ÷ 4 = 5 remainder 3."},
                    ],
                    "check": {
                        "prompt": "Show what you know about division and remainders.",
                        "questions": [
                            {"q": "If 7 × 8 = 56, then 56 ÷ 7 = ?", "options": ["8", "7", "49"], "answer": "8", "explain": "Division reverses multiplication: 56 ÷ 7 = 8."},
                            {"q": "17 marbles are shared fairly among 5 children. What happens?", "options": ["Each gets 3, with 2 left over.", "Each gets 4, with none left.", "They cannot share at all."], "answer": "Each gets 3, with 2 left over.", "explain": "5 × 3 = 15, leaving 17 − 15 = 2. So 17 ÷ 5 = 3 remainder 2."},
                            {"q": "What do we call the answer to a division problem?", "options": ["the quotient", "the product", "the remainder"], "answer": "the quotient", "explain": "Multiplication gives a product; division gives a quotient."},
                            {"q": "A remainder must always be…", "options": ["smaller than the divisor", "bigger than the divisor", "equal to zero"], "answer": "smaller than the divisor", "explain": "If the remainder were as big as the divisor, you could make one more full group."},
                        ],
                    },
                },
                {
                    "slug": "long-division",
                    "title": "Long Division, Step by Step",
                    "order": 7,
                    "minutes": 22,
                    "summary": "Divide large numbers with the standard long-division algorithm.",
                    "learn": [
                        {"type": "p", "text": "Long division handles big numbers one place at a time. Remember the steps with D-M-S-B: Divide, Multiply, Subtract, Bring down. Repeat until no digits remain."},
                        {"type": "example", "title": "Worked example: 96 ÷ 4", "text": "Divide: how many 4s in 9? 2 (2 × 4 = 8). Multiply 2 × 4 = 8, write under the 9. Subtract: 9 − 8 = 1. Bring down the 6 to make 16. Divide: how many 4s in 16? 4. 4 × 4 = 16, subtract → 0. Quotient: 24. Check: 24 × 4 = 96."},
                        {"type": "example", "title": "Worked example with a remainder: 85 ÷ 3", "text": "3s in 8? 2 → 2 × 3 = 6, subtract → 2, bring down 5 → 25. 3s in 25? 8 → 8 × 3 = 24, subtract → 1. Quotient: 28 remainder 1. Check: 28 × 3 + 1 = 85."},
                        {"type": "activity", "title": "Try one and check it", "text": "Solve 72 ÷ 3 on paper using D-M-S-B. Then check by multiplying your quotient by 3. 72 ÷ 3 = 24 because 24 × 3 = 72."},
                    ],
                    "check": {
                        "prompt": "Show what you know about long division.",
                        "questions": [
                            {"q": "What is 96 ÷ 4?", "options": ["24", "23", "92"], "answer": "24", "explain": "2 in 9 → remainder 1, bring down 6 → 4 in 16 = 4. Quotient 24; 24 × 4 = 96."},
                            {"q": "What is 85 ÷ 3?", "options": ["28 remainder 1", "28 remainder 2", "27 remainder 4"], "answer": "28 remainder 1", "explain": "28 × 3 = 84, leaving 1. 85 ÷ 3 = 28 r1."},
                            {"q": "What is the first step of long division?", "options": ["Divide", "Multiply", "Bring down"], "answer": "Divide", "explain": "D-M-S-B starts with Divide, then Multiply, Subtract, and Bring down."},
                            {"q": "How do you check a division answer?", "options": ["Multiply the quotient by the divisor (and add the remainder)", "Add the quotient to the divisor", "Subtract the divisor twice"], "answer": "Multiply the quotient by the divisor (and add the remainder)", "explain": "quotient × divisor + remainder must give back the original number."},
                        ],
                    },
                },
                {
                    "slug": "division-word-problems",
                    "title": "Division Word Problems",
                    "order": 8,
                    "minutes": 15,
                    "summary": "Spot sharing and grouping problems in real life.",
                    "learn": [
                        {"type": "p", "text": "Division word problems ask two kinds of questions: SHARING — \"split evenly among…\" and GROUPING — \"how many groups of … fit in …?\" Both are division."},
                        {"type": "list", "items": [
                            "\"…shared equally among 6 children…\" → total ÷ 6.",
                            "\"How many buses are needed if each holds 40 students?\" → total ÷ 40, then round UP.",
                            "\"How many full boxes of 8 can she make?\" → total ÷ 8; the remainder is what is left over.",
                        ]},
                        {"type": "example", "title": "Worked example: sharing", "text": "48 pencils are shared equally by 6 students. 48 ÷ 6 = 8 pencils each."},
                        {"type": "example", "title": "Worked example: rounding up", "text": "35 students ride vans that hold 8 each. 35 ÷ 8 = 4 r3, so 4 vans are full and 3 students still need a ride → you need 5 vans."},
                        {"type": "activity", "title": "Check with multiplication", "text": "Solve 63 ÷ 9 as a grouping problem: how many 9s fit in 63? Answer 7, and 7 × 9 = 63 proves it."},
                    ],
                    "check": {
                        "prompt": "Show what you know about division word problems.",
                        "questions": [
                            {"q": "36 stickers are shared equally among 4 friends. How many does each get?", "options": ["9", "8", "40"], "answer": "9", "explain": "36 ÷ 4 = 9 stickers each."},
                            {"q": "Eggs come in cartons of 12. How many full cartons can be made from 50 eggs?", "options": ["4 cartons", "5 cartons", "38 cartons"], "answer": "4 cartons", "explain": "50 ÷ 12 = 4 remainder 2 — four full cartons and 2 eggs left over."},
                            {"q": "A van holds 8 passengers. How many vans are needed for 26 passengers?", "options": ["4 vans", "3 vans", "18 vans"], "answer": "4 vans", "explain": "26 ÷ 8 = 3 remainder 2 — three vans are full, so a 4th van is needed for the last 2 people."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "fractions",
            "title": "Fractions",
            "summary": "Equal parts, numerators and denominators, equivalence, comparing, adding.",
            "order": 3,
            "lessons": [
                {
                    "slug": "fractions-equal-parts",
                    "title": "Fractions: Equal Parts and Equivalence",
                    "order": 9,
                    "minutes": 20,
                    "summary": "What the top and bottom numbers mean — and equal-size pieces.",
                    "learn": [
                        {"type": "p", "text": "A fraction names PART of a whole, and the parts must be EQUAL in size. In the fraction 3/4, the bottom number (4) is the DENOMINATOR — it tells how many equal parts the whole is split into. The top number (3) is the NUMERATOR — it tells how many of those parts you have."},
                        {"type": "p", "text": "A fraction with numerator 1, like 1/2 or 1/4, is a UNIT fraction — one single equal part."},
                        {"type": "example", "title": "Equivalent fractions name the same amount", "text": "One bar split into 2 equal parts: each part is 1/2. Split the same bar into 4 equal parts and shade 2: that is 2/4. Same amount of bar! So 1/2 = 2/4. Splitting parts smaller does not change the amount — it just changes the name."},
                        {"type": "example", "title": "The whole", "text": "If the numerator equals the denominator, you have the whole thing: 4/4 = 1 and 8/8 = 1."},
                        {"type": "activity", "title": "Fold and compare", "text": "Fold a paper strip in half and shade 1/2. Fold another strip into eighths and shade 4/8. Lay them side by side — same length, different names: 1/2 = 4/8."},
                    ],
                    "check": {
                        "prompt": "Show what you know about fractions.",
                        "questions": [
                            {"q": "In the fraction 5/6, what does the 6 tell you?", "options": ["the whole is split into 6 equal parts", "you have 6 parts", "the fraction is bigger than 1"], "answer": "the whole is split into 6 equal parts", "explain": "The denominator (bottom number) tells how many equal parts the whole is divided into."},
                            {"q": "Which fraction names the same amount as 1/2?", "options": ["2/4", "1/4", "3/4"], "answer": "2/4", "explain": "2 of 4 equal parts is the same amount of the whole as 1 of 2 equal parts."},
                            {"q": "Which fraction equals one whole?", "options": ["5/5", "1/5", "5/1"], "answer": "5/5", "explain": "When the numerator equals the denominator, you have all the parts — the whole thing."},
                            {"q": "A pizza is cut into 8 equal slices and you eat 3. What fraction did you eat?", "options": ["3/8", "8/3", "3/11"], "answer": "3/8", "explain": "You ate 3 of the 8 equal parts: 3/8."},
                        ],
                    },
                },
                {
                    "slug": "fractions-compare-add",
                    "title": "Comparing and Adding Like Fractions",
                    "order": 10,
                    "minutes": 18,
                    "summary": "Compare fractions with the same denominator, then add and subtract them.",
                    "learn": [
                        {"type": "p", "text": "When two fractions share the SAME denominator, the pieces are the same size — so you compare by the numerator: 7/10 is bigger than 3/10 because 7 pieces beat 3 pieces."},
                        {"type": "example", "title": "Adding like fractions", "text": "Add the numerators, keep the denominator: 3/8 + 2/8 = (3 + 2)/8 = 5/8. Do NOT add the denominators — the pieces stay the same size."},
                        {"type": "example", "title": "Subtracting like fractions", "text": "7/10 − 4/10 = 3/10. Subtract numerators, keep the denominator."},
                        {"type": "activity", "title": "Draw the sums", "text": "Draw a bar, shade 2/5, then shade 1 more fifth. How much is shaded? 2/5 + 1/5 = 3/5. Check that the bar is 3 of 5 equal parts shaded."},
                    ],
                    "check": {
                        "prompt": "Show what you know about comparing and adding like fractions.",
                        "questions": [
                            {"q": "Which is greater: 7/10 or 3/10?", "options": ["7/10", "3/10", "they are equal"], "answer": "7/10", "explain": "Same denominator 10, so compare numerators: 7 > 3."},
                            {"q": "What is 3/8 + 2/8?", "options": ["5/8", "5/16", "6/8"], "answer": "5/8", "explain": "Add the numerators and keep the denominator: (3+2)/8 = 5/8."},
                            {"q": "What is 7/10 − 4/10?", "options": ["3/10", "3/0", "11/10"], "answer": "3/10", "explain": "Subtract numerators and keep the denominator: 7 − 4 = 3, so 3/10."},
                            {"q": "You eat 2/6 of a cake and then 1/6 more. How much have you eaten?", "options": ["3/6", "2/12", "1/6"], "answer": "3/6", "explain": "2/6 + 1/6 = 3/6 of the cake."},
                        ],
                    },
                },
            ],
        },
    ],
}
