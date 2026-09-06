"""Ratios, Proportions, and Percent (Grade 7) — full published course.

Serves both the Foundations track (Grade 7 core math) and the Builder/Trade
track (trade math foundation) — e.g. the "Grade 7 → Builder → Mathematics"
selection from the owner's plan.
"""

MATH_GRADE_7 = {
    "slug": "ratios-proportions-percent-grade-7",
    "title": "Ratios, Proportions, and Percent",
    "summary": "Compare quantities, scale them up, and work with percent in the real world.",
    "description": (
        "Ratios let us compare quantities (3 apples for every 2 oranges); proportions let "
        "us scale those comparisons up and down (recipes, maps, blueprints); percent makes "
        "the comparisons easy to read (discounts, tax, tips, change). This course builds "
        "each idea from the ground up with worked examples drawn from everyday life and "
        "trade work, then checks mastery before the next lesson unlocks."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["7"],
    "grade_label": "Grade 7",
    "status": "published",
    "audience": "Grade 7 (ages 12–13), Foundations and Builder tracks.",
    "est_hours": 16,
    "passing_score": 80,
    "learning_objectives": [
        "Write and interpret ratios in three notations (3:4, 3 to 4, 3/4).",
        "Find unit rates and use them to compare deals and speeds.",
        "Solve proportions with cross multiplication.",
        "Use scale factors to read maps and blueprints.",
        "Recognize proportional relationships in tables, graphs, and the equation y = kx.",
        "Convert between fractions, decimals, and percents.",
        "Find a percent of a quantity, including discounts and tax.",
        "Compute percent increase and decrease.",
    ],
    "units": [
        {
            "slug": "ratios",
            "title": "Ratios and Rates",
            "summary": "Comparing quantities fairly.",
            "order": 1,
            "lessons": [
                {
                    "slug": "ratios-and-rates",
                    "title": "Ratios",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Compare quantities with ratios — part to part and part to whole.",
                    "learn": [
                        {"type": "p", "text": "A RATIO compares two quantities. If a bowl holds 3 apples and 2 oranges, the ratio of apples to oranges is 3 to 2. We can write it 3:2, \"3 to 2,\" or as the fraction 3/2. The ORDER matters: 3:2 is not the same as 2:3."},
                        {"type": "p", "text": "Ratios can compare PART to PART (apples to oranges) or PART to WHOLE (apples to all fruit = 3 to 5)."},
                        {"type": "example", "title": "Simplest form", "text": "A class has 12 boys and 8 girls. Boys : girls = 12:8. Both divide by 4, so the simplest form is 3:2. Ratios behave like fractions — simplify them the same way."},
                        {"type": "p", "text": "A RATE is a ratio that compares DIFFERENT kinds of units, like miles per hour or dollars per pound. When the second quantity is 1, it is a unit rate (see the next lesson)."},
                        {"type": "activity", "title": "Find ratios around you", "text": "Look at a jar of coins or a box of crayons. Write the ratio of red crayons to blue crayons (part:part) and red crayons to all crayons (part:whole). Simplify if you can."},
                    ],
                    "check": {
                        "prompt": "Show what you know about ratios.",
                        "questions": [
                            {"q": "A recipe uses 4 cups of flour and 1 cup of sugar. What is the ratio of flour to sugar?", "options": ["4:1", "1:4", "5:1"], "answer": "4:1", "explain": "Flour first, sugar second: 4 cups to 1 cup = 4:1."},
                            {"q": "Write 12:8 in simplest form.", "options": ["3:2", "6:4", "12:8"], "answer": "3:2", "explain": "Divide both parts by 4: 12 ÷ 4 = 3 and 8 ÷ 4 = 2."},
                            {"q": "A bag has 5 red and 7 blue marbles. What is the ratio of red marbles to ALL marbles?", "options": ["5:12", "5:7", "7:5"], "answer": "5:12", "explain": "There are 5 red and 12 marbles total, so red : total = 5:12."},
                            {"q": "Which is a rate, not just a ratio?", "options": ["60 miles per hour", "3 apples to 2 oranges", "2 left shoes and 2 right shoes"], "answer": "60 miles per hour", "explain": "A rate compares different kinds of units — here, miles and hours."},
                        ],
                    },
                },
                {
                    "slug": "unit-rates",
                    "title": "Unit Rates",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Rates scaled to \"per one\" — the key to comparing deals.",
                    "learn": [
                        {"type": "p", "text": "A UNIT RATE tells you the amount for ONE of something: miles per ONE hour, price per ONE item, cost per ONE pound. Unit rates let you compare deals fairly."},
                        {"type": "example", "title": "Finding a unit rate", "text": "A car travels 240 miles in 4 hours. Divide: 240 ÷ 4 = 60, so the unit rate is 60 miles per hour."},
                        {"type": "example", "title": "Comparing two deals", "text": "Deal A: $6 for 2 pounds → $3 per pound. Deal B: $10 for 4 pounds → $2.50 per pound. Deal B is cheaper per pound. Unit rates expose the better buy."},
                        {"type": "activity", "title": "Price check", "text": "Find two package sizes of the same snack at a store (or online). Compute each one's price per ounce. Which is the better unit rate?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about unit rates.",
                        "questions": [
                            {"q": "A runner covers 9 miles in 1.5 hours. What is her unit rate?", "options": ["6 miles per hour", "4.5 miles per hour", "13.5 miles per hour"], "answer": "6 miles per hour", "explain": "9 ÷ 1.5 = 6 miles per hour."},
                            {"q": "Which is the better deal: 5 pens for $4 or 8 pens for $6?", "options": ["8 pens for $6", "5 pens for $4", "they cost the same per pen"], "answer": "8 pens for $6", "explain": "$4 ÷ 5 = $0.80 per pen; $6 ÷ 8 = $0.75 per pen. The 8-pack is cheaper per pen."},
                            {"q": "A 12-ounce bag costs $3. What is the unit rate?", "options": ["$0.25 per ounce", "$3 per ounce", "$0.40 per ounce"], "answer": "$0.25 per ounce", "explain": "$3 ÷ 12 = $0.25 per ounce."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "proportions",
            "title": "Proportions",
            "summary": "Two equal ratios — and everything that scales with them.",
            "order": 2,
            "lessons": [
                {
                    "slug": "solving-proportions",
                    "title": "Solving Proportions",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Two equal ratios, one missing number — cross multiply to find it.",
                    "learn": [
                        {"type": "p", "text": "A PROPORTION says two ratios are equal. 1/2 = 2/4 is a proportion. Usually one number is missing, and you solve for it."},
                        {"type": "p", "text": "CROSS MULTIPLICATION: multiply across the equals sign — numerator × opposite denominator — and set the two products equal."},
                        {"type": "example", "title": "Worked example", "text": "Solve 3/4 = x/20. Cross multiply: 3 × 20 = 4 × x → 60 = 4x → x = 15. Check: 3/4 = 15/20, and both equal 0.75."},
                        {"type": "example", "title": "Worked example: recipes", "text": "A pancake recipe uses 2 eggs for 3 cups of mix. For 12 cups of mix, how many eggs? 2/3 = x/12 → 2 × 12 = 3x → 24 = 3x → x = 8 eggs."},
                        {"type": "activity", "title": "Scale the recipe", "text": "A lemonade recipe: 1 cup of juice to 4 cups of water. Set up a proportion to find the water needed for 3 cups of juice. (1/4 = 3/x → x = 12 cups.)"},
                    ],
                    "check": {
                        "prompt": "Show what you know about solving proportions.",
                        "questions": [
                            {"q": "Solve 3/4 = x/20.", "options": ["15", "16", "12"], "answer": "15", "explain": "3 × 20 = 4x → 60 = 4x → x = 15."},
                            {"q": "Solve 2/3 = x/12.", "options": ["8", "6", "18"], "answer": "8", "explain": "2 × 12 = 3x → 24 = 3x → x = 8."},
                            {"q": "If 5 apples cost $2.50, how much do 15 apples cost?", "options": ["$7.50", "$5.00", "$10.00"], "answer": "$7.50", "explain": "5/2.50 = 15/x → 5x = 37.50 → x = 7.50."},
                            {"q": "Which pair of ratios forms a true proportion?", "options": ["1/3 and 3/9", "1/3 and 3/6", "2/5 and 5/2"], "answer": "1/3 and 3/9", "explain": "Cross multiply: 1 × 9 = 9 and 3 × 3 = 9. The products match, so 1/3 = 3/9."},
                        ],
                    },
                },
                {
                    "slug": "scale-drawings",
                    "title": "Scale Drawings and Maps",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Blueprint scales: every inch on paper stands for real distance.",
                    "learn": [
                        {"type": "p", "text": "A SCALE tells you how a drawing compares to the real thing. A map scale of 1 inch = 10 miles means every inch you measure on the map stands for 10 real miles."},
                        {"type": "example", "title": "Worked example: map distance", "text": "Scale: 1 inch = 10 miles. Two towns are 3.5 inches apart on the map. Real distance: 3.5 × 10 = 35 miles."},
                        {"type": "example", "title": "Worked example: blueprint", "text": "A floor plan uses 1/4 inch = 1 foot. A wall measures 3 inches on the plan. Set up 0.25/1 = 3/x → x = 12 feet. The real wall is 12 feet long."},
                        {"type": "activity", "title": "Measure your room", "text": "Measure your bedroom's length in feet. Draw it using a scale of 1 inch = 1 foot. Check: the drawing should be as many inches long as the room is feet long."},
                    ],
                    "check": {
                        "prompt": "Show what you know about scale drawings.",
                        "questions": [
                            {"q": "A map says 1 inch = 25 miles. How far apart are two cities 4 inches apart on the map?", "options": ["100 miles", "25 miles", "6.25 miles"], "answer": "100 miles", "explain": "4 × 25 = 100 miles."},
                            {"q": "A blueprint uses 1/4 inch = 1 foot. A window is 1 inch wide on the plan. How wide is the real window?", "options": ["4 feet", "1 foot", "25 feet"], "answer": "4 feet", "explain": "1 inch is four 1/4-inch units, so the window is 4 × 1 = 4 feet."},
                            {"q": "A scale drawing shows a truck at 1/50th real size. The drawing is 4 inches long. How long is the real truck?", "options": ["200 inches", "50 inches", "54 inches"], "answer": "200 inches", "explain": "4 × 50 = 200 inches (about 16.7 feet)."},
                        ],
                    },
                },
                {
                    "slug": "proportional-relationships",
                    "title": "Proportional Relationships",
                    "order": 5,
                    "minutes": 18,
                    "summary": "When two quantities always change by the same multiplier, they are proportional.",
                    "learn": [
                        {"type": "p", "text": "Two quantities are PROPORTIONAL if their ratio is always the same. If 1 notebook costs $2, then 2 cost $4, 3 cost $6… The constant ratio (2 dollars per notebook) is called the CONSTANT OF PROPORTIONALITY, k."},
                        {"type": "p", "text": "Proportional relationships follow the equation y = kx. In tables, every y ÷ x gives the same k. In graphs, the points line up on a straight line that passes through (0, 0)."},
                        {"type": "example", "title": "Spot the constant", "text": "Table: x = 2 → y = 6; x = 5 → y = 15; x = 7 → y = 21. Check y ÷ x: 6÷2 = 3, 15÷5 = 3, 21÷7 = 3. Constant k = 3, so y = 3x. Proportional!"},
                        {"type": "example", "title": "Not proportional", "text": "x = 1 → y = 2; x = 2 → y = 3. y ÷ x gives 2 then 1.5 — not the same, so not proportional. The rule here is y = x + 1, which adds, not multiplies."},
                        {"type": "activity", "title": "Proportional or not?", "text": "Gas costs $3.50 per gallon. Is the cost proportional to the gallons? Yes — y = 3.5x, a constant rate. Now think of a counterexample: \"a $5 entry fee plus $2 per ride\" is NOT proportional, because y = 2x + 5."},
                    ],
                    "check": {
                        "prompt": "Show what you know about proportional relationships.",
                        "questions": [
                            {"q": "Which table shows a proportional relationship?", "options": ["y is always 3 times x", "y is always x plus 3", "y doubles only sometimes"], "answer": "y is always 3 times x", "explain": "A constant multiplier (y = 3x) means a constant ratio — that is proportional."},
                            {"q": "In the equation y = 7x, what is the constant of proportionality?", "options": ["7", "x", "y"], "answer": "7", "explain": "k is the number multiplying x: here k = 7."},
                            {"q": "The graph of a proportional relationship is…", "options": ["a straight line through (0, 0)", "any curve", "a line that never starts at zero"], "answer": "a straight line through (0, 0)", "explain": "Because y = kx, when x = 0, y = 0 — the line passes through the origin."},
                            {"q": "Which situation is proportional?", "options": ["$2 per pound of apples", "$5 fee plus $2 per visit", "free first month then $10/month"], "answer": "$2 per pound of apples", "explain": "A constant rate with no starting fee — total = 2 × pounds — is proportional. The others add a fixed amount, so their ratios change."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "percent",
            "title": "Percent",
            "summary": "Out of 100 — discounts, tax, tips, and change.",
            "order": 3,
            "lessons": [
                {
                    "slug": "percent-meaning",
                    "title": "What Percent Means",
                    "order": 6,
                    "minutes": 15,
                    "summary": "Percent is a ratio out of 100 — and it connects to decimals and fractions.",
                    "learn": [
                        {"type": "p", "text": "PERCENT means \"out of 100.\" The % symbol is a shortcut. 25% means 25 out of every 100 — which is the fraction 25/100 (simplified: 1/4) and the decimal 0.25."},
                        {"type": "list", "items": [
                            "To turn a percent into a decimal, move the decimal point two places LEFT: 25% → 0.25.",
                            "To turn a decimal into a percent, move it two places RIGHT: 0.4 → 40%.",
                            "Memorize the easy ones: 50% = 1/2, 25% = 1/4, 75% = 3/4, 10% = 1/10, 100% = 1 (the whole).",
                        ]},
                        {"type": "example", "title": "Conversions", "text": "3/4 = 0.75 = 75%. And 12% = 0.12 = 12/100 = 3/25."},
                        {"type": "activity", "title": "Percent square", "text": "Shade 30 small squares in a 10 × 10 grid (100 squares). You shaded 30% of the grid. How many squares are 50%? 100%?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about percents.",
                        "questions": [
                            {"q": "What does 35% mean?", "options": ["35 out of every 100", "35 out of every 10", "100 out of 35"], "answer": "35 out of every 100", "explain": "Percent means per hundred — 35% is 35/100."},
                            {"q": "Write 0.25 as a percent.", "options": ["25%", "2.5%", "250%"], "answer": "25%", "explain": "Move the decimal two places right: 0.25 → 25%."},
                            {"q": "Which is equal to 50%?", "options": ["1/2", "1/4", "5/100"], "answer": "1/2", "explain": "50% = 50/100, which simplifies to 1/2."},
                            {"q": "Write 8% as a decimal.", "options": ["0.08", "0.8", "8.0"], "answer": "0.08", "explain": "Move the decimal two places left: 8% → 0.08."},
                        ],
                    },
                },
                {
                    "slug": "percent-of-number",
                    "title": "Finding a Percent of a Number",
                    "order": 7,
                    "minutes": 20,
                    "summary": "Discounts, tax, and tips — the math of shopping.",
                    "learn": [
                        {"type": "p", "text": "To find \"p% of n,\" convert the percent to a decimal and MULTIPLY: p% of n = n × (p/100)."},
                        {"type": "example", "title": "Worked example: discount", "text": "A $40 jacket is 25% off. 25% of 40 = 40 × 0.25 = $10 off. Sale price: 40 − 10 = $30."},
                        {"type": "example", "title": "Worked example: sales tax", "text": "A $50 game has 6% tax. Tax = 50 × 0.06 = $3. Total = $53."},
                        {"type": "example", "title": "Worked example: finding the percent itself", "text": "What percent of 80 is 20? Set up: part/whole = 20/80 = 0.25 = 25%."},
                        {"type": "activity", "title": "Shopping math", "text": "A backpack costs $60. It is on sale for 20% off. First find the discount (60 × 0.20 = $12), then the sale price ($48). Add a 7% tax: 48 × 0.07 = $3.36, so total ≈ $51.36."},
                    ],
                    "check": {
                        "prompt": "Show what you know about percent of a number.",
                        "questions": [
                            {"q": "What is 25% of 80?", "options": ["20", "25", "40"], "answer": "20", "explain": "80 × 0.25 = 20."},
                            {"q": "A $60 jacket is 20% off. What is the sale price?", "options": ["$48", "$40", "$12"], "answer": "$48", "explain": "Discount = 60 × 0.20 = $12; sale price = 60 − 12 = $48."},
                            {"q": "Sales tax is 7%. What is the tax on a $200 purchase?", "options": ["$14", "$7", "$207"], "answer": "$14", "explain": "200 × 0.07 = $14."},
                            {"q": "What percent of 50 is 10?", "options": ["20%", "10%", "5%"], "answer": "20%", "explain": "10/50 = 0.20 = 20%."},
                        ],
                    },
                },
                {
                    "slug": "percent-change",
                    "title": "Percent Increase and Decrease",
                    "order": 8,
                    "minutes": 20,
                    "summary": "How much did something grow or shrink — as a percent?",
                    "learn": [
                        {"type": "p", "text": "Percent change compares the SIZE OF THE CHANGE to the ORIGINAL amount: percent change = (change ÷ original) × 100. A change that makes things bigger is an increase; smaller is a decrease."},
                        {"type": "example", "title": "Worked example: increase", "text": "A plant grows from 10 cm to 15 cm. Change = 5 cm. 5 ÷ 10 = 0.5 = 50% increase."},
                        {"type": "example", "title": "Worked example: decrease", "text": "A price falls from $80 to $60. Change = $20. 20 ÷ 80 = 0.25 = 25% decrease."},
                        {"type": "example", "title": "Watch the base", "text": "Going from 100 to 120 is a 20% increase. Going BACK from 120 to 100 is a decrease of 20 out of 120 = 16.7% — NOT 20%. Always divide by the ORIGINAL amount, and the original is different in each direction."},
                        {"type": "activity", "title": "Measure your own change", "text": "Measure a friend's height growth or the price change of a snack over a month. Compute the percent change and say whether it is an increase or decrease."},
                    ],
                    "check": {
                        "prompt": "Show what you know about percent change.",
                        "questions": [
                            {"q": "A price rises from $50 to $60. What is the percent increase?", "options": ["20%", "10%", "120%"], "answer": "20%", "explain": "Change = $10; 10 ÷ 50 = 0.20 = 20%."},
                            {"q": "A team's score drops from 80 to 60. What is the percent decrease?", "options": ["25%", "20%", "33%"], "answer": "25%", "explain": "Change = 20; 20 ÷ 80 = 0.25 = 25%."},
                            {"q": "A population grows from 200 to 250. What is the percent increase?", "options": ["25%", "20%", "50%"], "answer": "25%", "explain": "Change = 50; 50 ÷ 200 = 0.25 = 25%."},
                            {"q": "Why is a drop from 120 back to 100 NOT a 20% decrease?", "options": ["Because 20 is divided by the original 120, not by 100", "Because decreases cannot use percent", "Because 120 is an even number"], "answer": "Because 20 is divided by the original 120, not by 100", "explain": "20 ÷ 120 ≈ 0.167 = 16.7%. Percent change always divides by the original amount."},
                        ],
                    },
                },
            ],
        },
    ],
}
