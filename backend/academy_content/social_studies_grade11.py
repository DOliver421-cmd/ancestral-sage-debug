"""Social Studies Grade 11 — U.S. History (published core)."""
SOCIAL_STUDIES_GRADE_11 = {
    "slug": "social-studies-grade-11",
    "title": "Social Studies — Grade 11",
    "summary": "U.S. history from Reconstruction to the present — with primary sources.",
    "description": "Grade 11 U.S. history centers primary sources from Reconstruction through the present, including Black organizing traditions and community institution-building.",
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["11"],
    "grade_label": "Grade 11",
    "status": "published",
    "audience": "Grade 11 (ages 16-17)",
    "est_hours": 24,
    "passing_score": 80,
    "learning_objectives": [
        "Interpret primary sources from key eras in U.S. history.",
        "Explain how organizing and law shaped outcomes after Reconstruction.",
        "Connect past policy to present community conditions and choices.",
    ],
    "units": [
        {"slug": "reconstruction-to-great-migration", "title": "Reconstruction to Great Migration", "summary": "Promise and reversal.", "order": 1, "lessons": [
            {"slug": "reconstruction-grade11", "title": "Reconstruction", "order": 1, "minutes": 18, "summary": "Amendments and reversal.", "learn": [{"type": "p", "text": "The 13th, 14th, and 15th Amendments promised freedom, citizenship, and voting. Black institutions — schools, churches, and cooperatives — grew rapidly. Redemption governments then reversed many gains through law and violence."}], "check": {"prompt": "Reconstruction.", "questions": [{"q": "The 14th Amendment addresses", "options": ["citizenship and equal protection", "only farming techniques", "only maritime law"], "answer": "citizenship and equal protection", "explain": "It defines citizenship and protection."}]}},
            {"slug": "great-migration-grade11", "title": "Great Migration", "order": 2, "minutes": 18, "summary": "Movement and city-building.", "learn": [{"type": "p", "text": "Between 1916 and 1970, six million Black Americans moved from the South to the North and West, building new neighborhoods, music, and labor power — while facing restrictive covenants and redlining."}], "check": {"prompt": "Great Migration.", "questions": [{"q": "The Great Migration was migration", "options": ["from the South to North/West cities", "only within one town", "only overseas"], "answer": "from the South to North/West cities", "explain": "A massive demographic shift."}]}},
        ]},
        {"slug": "civil-rights-to-present-grade11", "title": "Civil Rights to the Present", "summary": "Organizing and policy.", "order": 2, "lessons": [
            {"slug": "civil-rights-grade11", "title": "Civil Rights Movement", "order": 3, "minutes": 18, "summary": "Law, protest, and power.", "learn": [{"type": "p", "text": "Brown v. Board, the Montgomery Bus Boycott, and the Civil Rights Acts show how litigation, direct action, and community institutions work together. Read speeches and court opinions as primary sources."}], "check": {"prompt": "Civil Rights.", "questions": [{"q": "Brown v. Board ruled school segregation", "options": ["unconstitutional", "mandatory", "irrelevant"], "answer": "unconstitutional", "explain": "Separate is inherently unequal."}]}},
            {"slug": "policy-today-grade11", "title": "Policy and Community Today", "order": 4, "minutes": 18, "summary": "From history to action.", "learn": [{"type": "p", "text": "Housing, education, and economic policy today carry the imprint of earlier law — from redlining maps to school funding formulas. Understanding the line helps students choose effective action."}], "check": {"prompt": "Policy today.", "questions": [{"q": "Redlining maps historically", "options": ["graded neighborhoods and guided lending", "only listed churches", "were never used"], "answer": "graded neighborhoods and guided lending", "explain": "Maps shaped decades of investment."}]}},
        ]},
    ],
}
