"""Student Handbook — Elementary Edition (K–5, free ebook course).

A guide for young students and their parents: how lessons work, how mastery
unlocks work, how to build great learning habits, and how families use the
Academy together. Placed in the course catalog, free like everything else.
"""

HANDBOOK_ELEMENTARY = {
    "slug": "handbook-elementary",
    "title": "Student Handbook — Elementary Edition (K–5)",
    "summary": "A friendly guide for young learners and their parents: how lessons work, how mastery unlocks work, and how to build great learning habits at home.",
    "description": (
        "The Elementary Student Handbook is a free ebook-style course for K–5 learners and "
        "the grown-ups helping them. It walks through how the Academy works (lessons, knowledge "
        "checks, and the 80% mastery unlock), how to set up a learning space and routine, how to "
        "read carefully and ask good questions, how to keep going when something feels hard, and "
        "how families celebrate progress together. Short chapters, simple words, and a review at "
        "the end of each one."
    ),
    "subject": "life_skills",
    "subject_label": "Student Handbook",
    "track": "foundations",
    "tracks": ["foundations"],
    "grades": ["K", "1", "2", "3", "4", "5"],
    "grade_label": "Grades K–5 (with a parent)",
    "status": "published",
    "audience": "Young learners and their parents, together.",
    "est_hours": 3,
    "passing_score": 80,
    "learning_objectives": [
        "Explain how lessons, knowledge checks, and mastery unlocks work.",
        "Set up a learning space and a daily routine that works.",
        "Use careful reading and good questions to learn faster.",
        "Use three strategies for working through hard problems.",
        "Track your own progress and celebrate it with your family.",
    ],
    "units": [
        {
            "slug": "handbook-elementary-chapters",
            "title": "Chapters",
            "summary": "Five short chapters for young students and their parents.",
            "order": 1,
            "lessons": [
                {
                    "slug": "welcome-to-your-academy",
                    "title": "Chapter 1: Welcome to Your Academy",
                    "order": 1,
                    "minutes": 12,
                    "summary": "What this school is and how a lesson works.",
                    "learn": [
                        {"type": "p", "text": "Welcome! You are now a student of the Homeschool Academy, and this handbook is your guide. Your school lives inside MoreHelp Center, and it works a little differently from a regular school: YOU move at your own speed. When you finish a lesson and show you understand it, the next one unlocks. Nobody rushes you, and nobody holds you back."},
                        {"type": "list", "items": [
                            "A lesson has three parts: read (or watch), practice, and show what you know.",
                            "The knowledge check is not a test to fear — it's how the website learns you're ready for more.",
                            "Score 80 or higher and the next lesson opens immediately.",
                            "Score below 80? The lesson shows you what to review, and you can try again right away. Retrying is how strong learners are made.",
                        ]},
                        {"type": "tip", "text": "For parents: every course page shows the full unit and lesson map, so you always know what's ahead. Progress is saved automatically after every check."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 1.",
                        "questions": [
                            {"q": "What happens when you pass a lesson's knowledge check at 80% or higher?", "options": ["The next lesson unlocks", "You start the course over", "Nothing at all"], "answer": "The next lesson unlocks", "explain": "Passing a check shows you're ready, so the next lesson opens right away."},
                            {"q": "If you score below 80%, what can you do?", "options": ["Review the explanations and try again right away", "Wait a whole year", "Nothing — it's over"], "answer": "Review the explanations and try again right away", "explain": "Retrying is built in on purpose — it's how mastery works."},
                        ],
                    },
                },
                {
                    "slug": "your-learning-space",
                    "title": "Chapter 2: Your Learning Space and Routine",
                    "order": 2,
                    "minutes": 12,
                    "summary": "Where you learn matters almost as much as what you learn.",
                    "learn": [
                        {"type": "p", "text": "Great learners have a great spot. It doesn't need to be fancy — a table, good light, and your supplies in one place. What it needs most is to be the place where school happens, so your brain switches into learning mode when you sit down."},
                        {"type": "list", "items": [
                            "Pick one spot and use it every day. Keep pencils, paper, and water nearby.",
                            "Choose a start time. Homeschool is flexible, but a routine makes learning easy to start.",
                            "Work in short blocks. 20–30 minutes of focus, then a movement break — brains grow with rest in between.",
                            "End each day by telling your parent one thing you learned. Saying it out loud makes it stick.",
                        ]},
                        {"type": "tip", "text": "For parents: young students do best with the same 3–4 subjects most days, in the same order. Predictability lowers resistance and builds independence."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 2.",
                        "questions": [
                            {"q": "Why does using the same learning spot every day help?", "options": ["It helps your brain switch into learning mode", "It's just prettier", "It doesn't help at all"], "answer": "It helps your brain switch into learning mode", "explain": "A consistent space becomes a signal: sitting here means school time."},
                            {"q": "What's a smart way to structure focus time?", "options": ["Short focused blocks with movement breaks", "Six hours with no breaks", "Only study when you feel like it"], "answer": "Short focused blocks with movement breaks", "explain": "Young brains learn best in 20–30 minute blocks with breaks in between."},
                        ],
                    },
                },
                {
                    "slug": "reading-and-questions",
                    "title": "Chapter 3: Read Carefully, Ask Great Questions",
                    "order": 3,
                    "minutes": 12,
                    "summary": "The two superpowers every learner owns.",
                    "learn": [
                        {"type": "p", "text": "Reading carefully means reading to understand, not just to finish. Slow down when a sentence feels important. If your mind wanders, go back one paragraph — that's not failing, that's technique."},
                        {"type": "list", "items": [
                            "Before you read: look at the title and pictures and guess what it's about.",
                            "While you read: stop after each section and say it back in your own words.",
                            "When confused, ask: 'What part don't I get?' — then reread just that part.",
                            "Great questions are specific: not 'I don't get it' but 'Why does 3 × 4 mean 4 + 4 + 4?'",
                        ]},
                        {"type": "tip", "text": "Your lesson Coach can help explain ideas — but it will never give you the knowledge-check answers. That's on purpose: the point is YOUR understanding."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 3.",
                        "questions": [
                            {"q": "What is a great question to ask when you're confused?", "options": ["A specific one, like 'why does this step work?'", "'I don't get it'", "No question at all"], "answer": "A specific one, like 'why does this step work?'", "explain": "Specific questions point your brain — and your helper — at exactly the stuck part."},
                            {"q": "If your mind wanders while reading, you should…", "options": ["Go back a paragraph and reread", "Keep going and pretend it's fine", "Stop reading forever"], "answer": "Go back a paragraph and reread", "explain": "Rereading a small chunk is a technique strong readers use all the time."},
                        ],
                    },
                },
                {
                    "slug": "when-it-feels-hard",
                    "title": "Chapter 4: When It Feels Hard",
                    "order": 4,
                    "minutes": 12,
                    "summary": "Three tools for the stuck moments.",
                    "learn": [
                        {"type": "p", "text": "Every learner gets stuck. Feeling stuck is not a sign you're bad at something — it's the exact feeling of your brain growing. Here are three tools for that moment."},
                        {"type": "list", "items": [
                            "Tool 1 — Break it smaller: big problems are just small problems wearing a trench coat. Split the task and do one piece.",
                            "Tool 2 — Try a different way: draw it, say it out loud, use objects, or explain it to a stuffed animal. Teaching it is the fastest way to learn it.",
                            "Tool 3 — Take a real break: walk, stretch, get water. Your brain keeps working on the problem while you move.",
                            "Then come back and try again. Most 'impossible' problems crack on the second look.",
                        ]},
                        {"type": "tip", "text": "For parents: praise effort and strategy ('you tried a new way!') more than being smart. Kids praised for effort keep trying longer."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 4.",
                        "questions": [
                            {"q": "Feeling stuck is a sign that…", "options": ["your brain is growing — it's the moment to use a strategy", "you should quit", "you're bad at learning"], "answer": "your brain is growing — it's the moment to use a strategy", "explain": "Productive struggle is where learning actually happens."},
                            {"q": "Which is a 'break it smaller' move?", "options": ["Split the problem and do one piece at a time", "Look at the whole thing and panic", "Copy someone"], "answer": "Split the problem and do one piece at a time", "explain": "Small pieces make hard things doable — that's the whole trick."},
                        ],
                    },
                },
                {
                    "slug": "your-progress-your-pride",
                    "title": "Chapter 5: Your Progress, Your Pride",
                    "order": 5,
                    "minutes": 12,
                    "summary": "Watching yourself get better — on purpose.",
                    "learn": [
                        {"type": "p", "text": "In your classroom, green bars and mastery scores aren't decoration — they're a diary of your effort. Every lesson you pass is proof you did something yesterday that you couldn't do before. Check your progress at the end of each week with your parent and pick one thing to be proud of."},
                        {"type": "list", "items": [
                            "Weekly check-in: look at your progress bars, celebrate one win, pick one focus for next week.",
                            "Keep a 'I learned this' notebook — one line a day. By June it's a book about how much you grew.",
                            "Finished a whole course? Print your record and put it somewhere you'll see it. You earned it.",
                            "Be the teacher sometimes: explain today's lesson to your family at dinner. If you can teach it, you own it.",
                        ]},
                        {"type": "tip", "text": "For parents: your student's Records page can generate printable course records any time — great for portfolios, evaluators, and the fridge door."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 5.",
                        "questions": [
                            {"q": "Why check your progress every week?", "options": ["To see your growth and pick one focus", "To compare with strangers", "No reason"], "answer": "To see your growth and pick one focus", "explain": "Watching your own progress builds motivation and direction."},
                            {"q": "The fastest way to prove you understand something is to…", "options": ["teach it to someone else", "skip the next lesson", "read it faster"], "answer": "teach it to someone else", "explain": "Explaining forces your brain to organize what it knows — gaps show up instantly."},
                        ],
                    },
                },
            ],
        },
    ],
}
