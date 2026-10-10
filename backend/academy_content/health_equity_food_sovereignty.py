"""Adult Education / General Elective: Health Equity, Environmental Justice, and Food Sovereignty (published).

Adult-track course connecting environmental racism, the Black agrarian
movement (Fannie Lou Hamer's Freedom Farms Corporation), urban agriculture,
and ancestral nutrition — as applied knowledge an adult learner can use to
grow, cook, and organize in their own community.
"""

HEALTH_EQUITY_FOOD_SOVEREIGNTY = {
    "slug": "health-equity-environmental-justice",
    "title": "Health Equity, Environmental Justice, and Food Sovereignty",
    "summary": "Environmental racism, Freedom Farms, urban agriculture, and ancestral nutrition — and how to act on them.",
    "description": (
        "This adult general elective teaches the history and practice of food "
        "sovereignty in Black American life. Students study the geography of health "
        "disparities, the environmental-justice movement that named and measured them, "
        "the Freedom Farms Cooperative founded by Fannie Lou Hamer in 1969 as an "
        "economic survival program, and modern urban agriculture. They also learn "
        "practical skills: planning a garden, reading a food label for ancestral "
        "nutrition, mapping their own neighborhood's food access, and organizing a "
        "food sovereignty project."
    ),
    "subject": "life_skills",
    "subject_label": "Adult Education · Life Skills",
    "track": "adult_ed",
    "tracks": ["adult_ed", "life_skills", "leadership"],
    "grades": ["adult"],
    "grade_label": "Adult",
    "status": "published",
    "audience": "Adult learners studying health equity, food systems, and community organizing.",
    "est_hours": 20,
    "passing_score": 80,
    "learning_objectives": [
        "Define environmental justice and identify its historical roots.",
        "Describe the mapping evidence linking hazardous land use to race.",
        "Describe Fannie Lou Hamer's Freedom Farms Cooperative and its methods.",
        "Analyze food deserts and food access with real data.",
        "Plan a small-scale garden or cooperative project.",
        "Explain ancestral nutrition and evaluate a modern diet against it.",
        "Design a community food sovereignty project with an organizing plan.",
    ],
    "units": [
        {
            "slug": "environmental-justice",
            "title": "Environmental Justice",
            "summary": "Where pollution goes, and who lives there.",
            "order": 1,
            "lessons": [
                {
                    "slug": "mapping-environmental-racism",
                    "title": "Mapping Environmental Racism",
                    "order": 1,
                    "minutes": 24,
                    "summary": "The same map data that documents the disagreement.",
                    "learn": [
                        {"type": "p", "text": "The environmental justice movement began with ordinary people documenting patterns. In 1982, residents of Warren County, North Carolina — a predominantly Black community — protested a landfill siting and were jailed, and the NAACP's Benjamin Chavis documented more than 3,000 landfills and 75 percent of hazardous waste facilities placed in Black communities. Robert Bullard's Dumping in Dixie (1990) proved the geographical pattern with census and facility data."},
                        {"type": "list", "items": [
                            "Warren County 1982: the protest often credited as the movement's beginning.",
                            "Bullard's evidence: race predicted facility siting more reliably than income.",
                            "Flint (2014), Cancer Alley (Louisiana), and Altgeld Gardens (Chicago) are later documented cases.",
                        ]},
                        {"type": "example", "title": "Read a map", "text": "Overlay a census tract's racial composition with the locations of regulated facilities. Bullard's method is reproducible with public data — you can run it on your own city."},
                        {"type": "activity", "title": "Map your area", "text": "Map the food outlets and regulated facilities in your ZIP code. Note the distribution and write one paragraph of findings."},
                    ],
                    "check": {
                        "prompt": "Check what you know about environmental justice.",
                        "questions": [
                            {"q": "Bullard's Dumping in Dixie showed that facility siting was predicted by…", "options": ["race more reliably than income", "altitude only", "population density only"], "answer": "race more reliably than income", "explain": "Race was the strongest predictor in his analysis."},
                            {"q": "The Warren County protest is significant because…", "options": ["it is credited with starting the EJ movement", "it ended zoning", "it built a power plant"], "answer": "it is credited with starting the EJ movement", "explain": "It organized national attention to environmental racism."},
                        ],
                    },
                },
                {
                    "slug": "health-disparities",
                    "title": "Health Outcomes and Their Causes",
                    "order": 2,
                    "minutes": 24,
                    "summary": "Asthma, heat, lead, and access.",
                    "learn": [
                        {"type": "p", "text": "Environmental inequality produces measurable health differences. Black children have asthma rates about twice those of white children, which tracks with housing stock, air quality, and access to medication. Lead exposure tracks with older housing. Heat vulnerability tracks with tree cover, which itself follows the same historic redlining lines that Holt's neighborhood grading once drew."},
                        {"type": "list", "items": [
                            "Air quality: proximity to highways and industry raises asthma and cardiac risk.",
                            "Housing: older, poorly maintained housing carries lead and mold.",
                            "Tree canopy: historically redlined neighborhoods are hotter.",
                            "Access: distance to care and to fresh food shapes outcomes.",
                        ]},
                        {"type": "example", "title": "A single figure", "text": "Neighborhood tree canopy maps and historical HOLC grades, overlaid, show measurable temperature differences in the same city — a policy legacy you can walk through in one afternoon."},
                        {"type": "activity", "title": "Trace one cause", "text": "Pick one health outcome. Trace it back to one environmental cause and one policy cause, then name the intervention."},
                    ],
                    "check": {
                        "prompt": "Check what you know about health disparities.",
                        "questions": [
                            {"q": "Black children's asthma rates are higher with higher…", "options": ["proximity to air pollution and poor housing", "altitude", "exercise"], "answer": "proximity to air pollution and poor housing", "explain": "Both environmental exposure and dwelling quality contribute."},
                            {"q": "Tree canopy differences are associated with…", "options": ["historic redlining", "soil type only", "random chance"], "answer": "historic redlining", "explain": "Holt grades from the 1930s correlate with today's canopy cover and temperature."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "freedom-farms",
            "title": "The Black Agrarian Tradition",
            "summary": "Fannie Lou Hamer's cooperative, and the sovereignty it built.",
            "order": 2,
            "lessons": [
                {
                    "slug": "freedom-farms-cooperative",
                    "title": "Freedom Farms Cooperative",
                    "order": 3,
                    "minutes": 24,
                    "summary": "A voting-rights organizer who fed 1,500 families.",
                    "learn": [
                        {"type": "p", "text": "Fannie Lou Hamer is remembered for registering voters and for the testimony that moved the 1964 credentials committee, but her deepest work was economic. After being evicted for trying to register to vote, she founded the Freedom Farms Cooperative in 1969: pig farming, vegetable gardens, and a cooperative purchasing program in Sunflower County, Mississippi. At its height it fed around 1,500 families and gave Black sharecroppers income they owned rather than wages they were owed."},
                        {"type": "list", "items": [
                            "Inputs: pigs, vegetable gardens, and a cooperative store.",
                            "Owners: the people who worked the land, not a distant boss.",
                            "Purpose: hunger relief, income, and economic power for voter protection.",
                        ]},
                        {"type": "example", "title": "Politics through farming", "text": "Hamer argued a family who depends on a white boss for groceries cannot safely register to vote; food independence was therefore voting rights work."},
                        {"type": "activity", "title": "Plan a pig bank", "text": "Design a cooperative pig bank for ten families: who raises, who sells, how profits are split, and how new members join."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Freedom Farms.",
                        "questions": [
                            {"q": "Fannie Lou Hamer's Freedom Farms Cooperative combined farming with…", "options": ["voting rights and economic independence", "real estate speculation", "industrial mining"], "answer": "voting rights and economic independence", "explain": "Economic independence protected political participation."},
                            {"q": "The Cooperative's structure gave its members…", "options": ["ownership of the output they produced", "wages set by a distant boss", "no income"], "answer": "ownership of the output they produced", "explain": "Sharecroppers became owners, which is the definition of food sovereignty."},
                        ],
                    },
                },
                {
                    "slug": "food-desert-to-sovereignty",
                    "title": "From Food Desert to Food Sovereignty",
                    "order": 4,
                    "minutes": 24,
                    "summary": "Naming the problem, then owning the answer.",
                    "learn": [
                        {"type": "p", "text": "A food desert is a census-tract definition: low-income residents with low access to a supermarket. Food sovereignty describes something different and more powerful: a community's right to define its own food system. Urban agriculture, community gardens, farmers' markets, cooperatives, and food hubs are the practical tools; organizing is the political condition. Detroit, Oakland, Philly, and many small towns have all rebuilt food systems with these tools."},
                        {"type": "list", "items": [
                            "Desert definition: income and distance-based.",
                            "Sovereignty: community control over production, distribution, and culture.",
                            "Tools: gardens, co-ops, markets, kitchens, and skills.",
                            "Policy: zoning, land trusts, and food policy councils.",
                        ]},
                        {"type": "activity", "title": "Inventory your area", "text": "Within a mile of your home, count gardens, markets, groceries, and kitchens. Then write the one gap they leave."},
                    ],
                    "check": {
                        "prompt": "Check what you know about food sovereignty.",
                        "questions": [
                            {"q": "Food sovereignty differs from food assistance in that it emphasizes…", "options": ["community control of the food system", "waiting for donations", "larger distribution centers"], "answer": "community control of the food system", "explain": "Sovereignty is about power and ownership, not charity."},
                            {"q": "Urban agriculture is one tool among…", "options": ["gardens, co-ops, markets, and kitchens", "only large farms", "only grocery stores"], "answer": "gardens, co-ops, markets, and kitchens", "explain": "Food systems need production, distribution, and preparation."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "practical-sovereignty",
            "title": "Practical Sovereignty",
            "summary": "Grow, eat, and organize.",
            "order": 3,
            "lessons": [
                {
                    "slug": "ancestral-nutrition",
                    "title": "Ancestral Nutrition",
                    "order": 5,
                    "minutes": 24,
                    "summary": "Traditional food patterns as a standard for evaluating a modern diet.",
                    "learn": [
                        {"type": "p", "text": "Ancestral nutrition asks what the diets of West, Central, and Southern African peoples contained before the mid-passage diet: leafy greens, beans, yams, millet, sorghum, plantains, peanuts, okra, peppers, and fish where available — largely plant-forward, high in fiber, and paired with whole grains. Modern processed diets invert this with refined grains, added sugars, and added fat, and the differences are measurable in metabolic disease rates. The point is not nostalgia but evidence."},
                        {"type": "list", "items": [
                            "Traditional: whole grains, legumes, greens, tubers, peppers, seeds.",
                            "Change: processing, sugar, and portion size.",
                            "Soul food: historically vegetables and pot liquor; post-war changes made it heavier.",
                            "Practical: cook okra, greens, yams, beans, and grains; label logic.",
                        ]},
                        {"type": "example", "title": "Cook it", "text": "Make a pot-likor greens or an okra soup with whole grains. Compare the fiber content per serving with a packaged snack."},
                        {"type": "activity", "title": "Menu for a week", "text": "Plan a week of ancestral-style meals and a shopping list. Price it, then compare with your current week."},
                    ],
                    "check": {
                        "prompt": "Check what you know about ancestral nutrition.",
                        "questions": [
                            {"q": "A traditional West African diet pattern is characterized by…", "options": ["whole grains, legumes, greens, and tubers", "refined sugar and white flour", "mostly dairy"], "answer": "whole grains, legumes, greens, and tubers", "explain": "The historical diet was plant-forward and high-fiber."},
                            {"q": "The strongest argument for ancestral nutrition is…", "options": ["documented differences in diet and metabolic disease", "fashion", "that it is new"], "answer": "documented differences in diet and metabolic disease", "explain": "It rests on evidence about diets and health outcomes."},
                        ],
                    },
                },
                {
                    "slug": "capstone-organize",
                    "title": "Capstone: Organize a Food Project",
                    "order": 6,
                    "minutes": 28,
                    "summary": "A plan your community could actually run.",
                    "learn": [
                        {"type": "p", "text": "Your capstone is a working plan: a garden bed, a cooperative purchase, a community kitchen, or a market, with a budget, a land source, a labor plan, and a distribution plan. Fannie Lou Hamer's project worked because it had land, a store, and an owner. Your plan needs the same specifics."},
                        {"type": "list", "items": [
                            "Scope: a garden bed, a co-op buy, a kitchen, or a market.",
                            "Budget: seeds, soil, tools, water, insurance.",
                            "Land: whose, under what terms, and for how long.",
                            "Labor and division: who works, who decides, who is paid.",
                            "Distribution: who eats, how much, and on what terms.",
                        ]},
                        {"type": "tip", "text": "Most food projects fail on land and labor, not on seeds. Write those two sections first."},
                        {"type": "activity", "title": "Write and pitch", "text": "Write the plan (two pages) and pitch it to two people in a position to help. Revise once from their feedback."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the capstone plan.",
                        "questions": [
                            {"q": "A food sovereignty plan must specify…", "options": ["land, labor, and distribution terms", "only crop choices", "only a name"], "answer": "land, labor, and distribution terms", "explain": "Those three decide whether the project survives."},
                            {"q": "The most common project failure point is…", "options": ["land and labor, not seeds", "the weather", "soil"], "answer": "land and labor, not seeds", "explain": "Projects collapse from unclear land access and labor terms."},
                        ],
                    },
                },
            ],
        },
    ],
}
