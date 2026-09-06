"""Adult Education Mathematics (HSE preparation — full published course)."""

ADULT_ED_HSE_MATH = {
    "slug": "adult-ed-hse-math",
    "title": "Adult Education Mathematics",
    "summary": "Arithmetic, fractions, decimals, percentages, ratios, algebra, geometry, and word problems.",
    "description": (
        "This comprehensive adult-education math course prepares learners for high-school equivalency "
        "and everyday numeracy. Topics span whole-number operations, fractions, decimals, percentages, "
        "ratios and proportions, basic algebra, geometry, and practical word problems."
    ),
    "subject": "adult_ed",
    "subject_label": "Adult Education",
    "track": "adult_ed",
    "tracks": ["adult_ed"],
    "grades": ["adult"],
    "grade_label": "Adult",
    "status": "published",
    "audience": "Adult learners preparing for HSE/GED or workplace numeracy.",
    "est_hours": 40,
    "passing_score": 80,
    "learning_objectives": [
        "Add, subtract, multiply, and divide whole numbers fluently.",
        "Work with fractions, decimals, and percentages.",
        "Solve ratio, proportion, and percent problems.",
        "Evaluate algebraic expressions and solve one-step equations.",
        "Calculate perimeter, area, and volume of basic shapes.",
        "Solve multi-step word problems.",
    ],
    "units": [
        {
            "slug": "number-sense-and-fractions",
            "title": "Number Sense and Fractions",
            "summary": "Whole numbers, factors, fractions, and decimals.",
            "order": 1,
            "lessons": [
                {
                    "slug": "whole-number-operations",
                    "title": "Whole Number Operations",
                    "order": 1,
                    "minutes": 20,
                    "summary": "Fluency with the four operations and place value.",
                    "learn": [
                        {"type": "p", "text": "Fluency with addition, subtraction, multiplication, and division is the foundation of every other math skill. Practice these until they feel automatic."},
                        {"type": "list", "items": [
                            "Addition/subtraction: line up place values.",
                            "Multiplication: multiply and carry.",
                            "Division: long-division steps D-M-S-B.",
                            "Always check work with estimation.",
                        ]},
                        {"type": "activity", "title": "Speed practice", "text": "Write 20 mixed facts and solve them in under 5 minutes. Check your answers."},
                    ],
                    "check": {
                        "prompt": "Show what you know about whole number operations.",
                        "questions": [
                            {"q": "What is 7 × 8?", "options": ["56", "48", "64"], "answer": "56", "explain": "7 × 8 = 56."},
                            {"q": "What is 144 ÷ 12?", "options": ["12", "11", "13"], "answer": "12", "explain": "12 × 12 = 144, so 144 ÷ 12 = 12."},
                        ],
                    },
                },
                {
                    "slug": "fractions-and-decimals",
                    "title": "Fractions and Decimals",
                    "order": 2,
                    "minutes": 22,
                    "summary": "Convert, compare, add, subtract, multiply, and divide.",
                    "learn": [
                        {"type": "p", "text": "Fractions and decimals name the same amounts in different ways. To convert a fraction to a decimal, divide the top number by the bottom number. To convert a decimal to a fraction, use place value."},
                        {"type": "list", "items": [
                            "½ = 0.5; ¼ = 0.25; ¾ = 0.75.",
                            "To add/subtract fractions: find a common denominator.",
                            "To multiply fractions: multiply top × top and bottom × bottom.",
                            "To divide fractions: multiply by the reciprocal.",
                        ]},
                        {"type": "example", "title": "Convert 3/8 to a decimal", "text": "3 ÷ 8 = 0.375."},
                    ],
                    "check": {
                        "prompt": "Show what you know about fractions and decimals.",
                        "questions": [
                            {"q": "What is 1/2 as a decimal?", "options": ["0.5", "0.2", "0.52"], "answer": "0.5", "explain": "1 divided by 2 equals 0.5."},
                            {"q": "What is 0.25 as a fraction?", "options": ["1/4", "1/2", "2/5"], "answer": "1/4", "explain": "25 hundredths = 25/100 = 1/4."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "algebra-and-percent",
            "title": "Algebra and Percent",
            "summary": "Expressions, equations, and real-world percent problems.",
            "order": 2,
            "lessons": [
                {
                    "slug": "ratios-and-percent",
                    "title": "Ratios and Percent",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Set up proportions and solve percent problems.",
                    "learn": [
                        {"type": "p", "text": "A ratio compares two quantities. A proportion states that two ratios are equal. Percent means 'per hundred.' Use proportions to find missing parts in real-world problems."},
                        {"type": "list", "items": [
                            "Percent to decimal: divide by 100 (50% = 0.50).",
                            "Decimal to percent: multiply by 100.",
                            "Percent of a number: multiply the decimal by the number.",
                            "Percent change: (new − old) ÷ old × 100.",
                        ]},
                        {"type": "example", "title": "Discount", "text": "A $40 shirt is 25% off. 0.25 × 40 = 10. Sale price = 40 − 10 = $30."},
                    ],
                    "check": {
                        "prompt": "Show what you know about ratios and percent.",
                        "questions": [
                            {"q": "What is 15% of 200?", "options": ["30", "15", "215"], "answer": "30", "explain": "0.15 × 200 = 30."},
                            {"q": "A ratio compares…", "options": ["two quantities", "three numbers", "areas"], "answer": "two quantities", "explain": "Ratios show how one quantity relates to another."},
                        ],
                    },
                },
                {
                    "slug": "basic-algebra",
                    "title": "Basic Algebra",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Evaluate expressions and solve one-step equations.",
                    "learn": [
                        {"type": "p", "text": "Algebra uses letters (variables) to stand for numbers. To solve an equation, isolate the variable using inverse operations. Keep the equation balanced by doing the same thing to both sides."},
                        {"type": "example", "title": "Solve 3x = 12", "text": "Divide both sides by 3: x = 4. Check: 3 × 4 = 12. ✓"},
                    ],
                    "check": {
                        "prompt": "Show what you know about basic algebra.",
                        "questions": [
                            {"q": "Solve: x + 7 = 15.", "options": ["8", "7", "22"], "answer": "8", "explain": "Subtract 7 from both sides: x = 8."},
                            {"q": "Solve: 5x = 35.", "options": ["7", "5", "175"], "answer": "7", "explain": "Divide both sides by 5: x = 7."},
                        ],
                    },
                },
                {
                    "slug": "geometry-basics",
                    "title": "Geometry Basics",
                    "order": 5,
                    "minutes": 20,
                    "summary": "Perimeter, area, volume, and the Pythagorean theorem.",
                    "learn": [
                        {"type": "p", "text": "Geometry measures space and shape. Perimeter is distance around. Area is surface coverage. Volume is interior space."},
                        {"type": "list", "items": [
                            "Rectangle: A = l × w; P = 2(l + w).",
                            "Triangle: A = ½ × b × h.",
                            "Circle: C = πd; A = πr².",
                            "Right triangle: a² + b² = c².",
                        ]},
                        {"type": "example", "title": "Room area", "text": "A 12 ft × 14 ft room has area 12 × 14 = 168 sq ft."},
                    ],
                    "check": {
                        "prompt": "Show what you know about geometry basics.",
                        "questions": [
                            {"q": "What is the area of a 5 ft by 8 ft rectangle?", "options": ["40 sq ft", "26 sq ft", "13 sq ft"], "answer": "40 sq ft", "explain": "5 × 8 = 40 square feet."},
                            {"q": "In a right triangle with legs 6 and 8, the hypotenuse is…", "options": ["10", "14", "48"], "answer": "10", "explain": "6² + 8² = 36 + 64 = 100. √100 = 10."},
                        ],
                    },
                },
                {
                    "slug": "word-problems",
                    "title": "Word Problems",
                    "order": 6,
                    "minutes": 20,
                    "summary": "Translate words into equations and solve.",
                    "learn": [
                        {"type": "p", "text": "Word problems hide math inside stories. Read carefully, underline the question, circle the numbers, and choose the right operation. Draw a picture or make a table if it helps."},
                        {"type": "list", "items": [
                            "Clue words: total, sum, altogether → add.",
                            "Difference, left, fewer → subtract.",
                            "Each, groups of, times → multiply.",
                            "Share, split, per, quotient → divide.",
                        ]},
                        {"type": "example", "title": "Distance problem", "text": "A car travels at 55 mph for 3 hours. Distance = rate × time = 55 × 3 = 165 miles."},
                    ],
                    "check": {
                        "prompt": "Show what you know about word problems.",
                        "questions": [
                            {"q": "A worker earns $14/hour and works 8 hours. What is gross pay?", "options": ["$112", "$22", "$22/hr"], "answer": "$112", "explain": "14 × 8 = 112 dollars."},
                            {"q": "If 3 bags of mulch cover 12 sq ft each, how much area do 5 bags cover?", "options": ["60 sq ft", "15 sq ft", "36 sq ft"], "answer": "60 sq ft", "explain": "5 × 12 = 60 square feet."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "data-and-probability",
            "title": "Data and Probability",
            "summary": "Mean, median, mode, graphs, and simple probability.",
            "order": 3,
            "lessons": [
                {
                    "slug": "mean-median-mode",
                    "title": "Mean, Median, and Mode",
                    "order": 7,
                    "minutes": 18,
                    "summary": "Calculate and compare measures of center.",
                    "learn": [
                        {"type": "p", "text": "Data sets have a 'center.' The mean is the average. The median is the middle value when ordered. The mode is the most frequent value. Outliers pull the mean but do not affect the median."},
                        {"type": "example", "title": "Scores", "text": "Scores: 80, 90, 70, 85, 90. Mean = (80+90+70+85+90)/5 = 83. Median = 85 (ordered). Mode = 90."},
                    ],
                    "check": {
                        "prompt": "Show what you know about mean, median, and mode.",
                        "questions": [
                            {"q": "What is the mode of 4, 6, 4, 8, 4, 10?", "options": ["4", "6", "8"], "answer": "4", "explain": "4 appears most often."},
                            {"q": "What is the median of 3, 7, 9, 12, 15?", "options": ["9", "7", "12"], "answer": "9", "explain": "Ordered: 3, 7, 9, 12, 15. The middle is 9."},
                        ],
                    },
                },
                {
                    "slug": "graphs-and-probability",
                    "title": "Graphs and Probability",
                    "order": 8,
                    "minutes": 18,
                    "summary": "Read bar graphs, line plots, and calculate simple probability.",
                    "learn": [
                        {"type": "p", "text": "Graphs turn numbers into pictures. Bar graphs compare categories. Line plots show frequency. Probability compares favorable outcomes to total possible outcomes."},
                        {"type": "list", "items": [
                            "Bar graph: height = amount.",
                            "Line plot: Xs stack to show frequency.",
                            "Probability = favorable outcomes / total outcomes.",
                            "Probability ranges from 0 (impossible) to 1 (certain).",
                        ]},
                        {"type": "activity", "title": "Survey and graph", "text": "Survey 10 people about their favorite snack. Make a bar graph of the results."},
                    ],
                    "check": {
                        "prompt": "Show what you know about graphs and probability.",
                        "questions": [
                            {"q": "What is the probability of rolling a 3 on a 6-sided die?", "options": ["1/6", "1/3", "3/6"], "answer": "1/6", "explain": "One favorable outcome out of six total outcomes."},
                            {"q": "A bar graph shows…", "options": ["comparisons among categories", "change over time", "parts of a whole"], "answer": "comparisons among categories", "explain": "Bar graphs are best for comparing different groups."},
                        ],
                    },
                },
            ],
        },
    ],
}
