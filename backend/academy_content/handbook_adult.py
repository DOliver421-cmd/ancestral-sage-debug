"""Student Handbook — Adult Learner Edition (free ebook course).

For adults returning to structured learning: beating the rust, studying
around a job and a life, using the Academy's adult education, life-skills,
career, and entrepreneurship tracks, and turning coursework into credentials
and income.
"""

HANDBOOK_ADULT = {
    "slug": "handbook-adult",
    "title": "Student Handbook — Adult Learner Edition",
    "summary": "The adult's guide to coming back: beating the rust, studying around work and life, building credentials that pay, and using every adult track the Academy offers.",
    "description": (
        "The Adult Student Handbook is a free ebook-style course for adults returning to structured "
        "learning — whether that's the high-school-equivalency track, career and workforce courses, "
        "trade study, or entrepreneurship. It covers the psychology of coming back (rust, doubt, "
        "and how to handle both), study methods that work around a job and family, how to choose "
        "the right track for your goal, how to convert coursework into credentials and income, and "
        "how to finish what you start. Short chapters, zero condescension, real techniques."
    ),
    "subject": "adult_ed",
    "subject_label": "Adult Education",
    "track": "adult_ed",
    "tracks": ["adult_ed", "life_skills", "career", "leadership", "entrepreneurship"],
    "grades": ["Adult"],
    "grade_label": "Adult learners",
    "status": "published",
    "audience": "Adults returning to learning — HSE prep, career change, trade study, or business.",
    "est_hours": 3,
    "passing_score": 80,
    "learning_objectives": [
        "Identify and counter the three doubts that stop adult learners.",
        "Apply study methods that fit a work-and-family schedule.",
        "Choose the right Academy track for a specific goal.",
        "Convert completed coursework into credentials, records, and income.",
        "Build a finishing system: minimums, accountability, and momentum.",
    ],
    "units": [
        {
            "slug": "handbook-adult-chapters",
            "title": "Chapters",
            "summary": "Five chapters for the returning learner.",
            "order": 1,
            "lessons": [
                {
                    "slug": "coming-back",
                    "title": "Chapter 1: Coming Back — the Rust Is Normal",
                    "order": 1,
                    "minutes": 12,
                    "summary": "The three doubts every returning adult has, and the truth about each.",
                    "learn": [
                        {"type": "p", "text": "Almost every adult who returns to learning carries the same three doubts: 'I'm too old for this,' 'I was never good at school,' and 'I don't have time.' Here's the truth about each. Too old: adult brains learn differently — slower to memorize, far better at connecting ideas to experience — which is an advantage in everything except cramming. Never good at school: most people who 'weren't good at school' were in systems that taught one way to every brain; you're in a self-paced system now, and pace changes everything. No time: you don't need more time, you need smaller units — 20 focused minutes a day outruns a fantasy of Saturday marathons."},
                        {"type": "list", "items": [
                            "Self-paced mastery means nobody sees your first attempts. The 80% gates exist to protect YOUR foundation.",
                            "The knowledge checks are private and retryable. Failure here costs nothing and teaches plenty.",
                            "Your life experience is course credit in disguise — you've already solved real problems the textbooks only describe.",
                            "Start smaller than feels impressive. Two lessons a week for a month beats ten lessons in week one and zero in week two.",
                        ]},
                        {"type": "tip", "text": "Your first goal is a streak, not a diploma: open a lesson every day, even for five minutes. Momentum is the whole game in week one."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 1.",
                        "questions": [
                            {"q": "Compared to younger students, adult brains are generally…", "options": ["slower to memorize but better at connecting ideas to experience", "worse at everything", "faster at cramming"], "answer": "slower to memorize but better at connecting ideas to experience", "explain": "Experience-linked learning is the adult advantage — play to it."},
                            {"q": "The realistic study unit for a busy adult is…", "options": ["20 focused minutes a day", "a full Saturday marathon", "waiting until life calms down"], "answer": "20 focused minutes a day", "explain": "Small daily units compound; marathons don't survive contact with real life."},
                        ],
                    },
                },
                {
                    "slug": "studying-around-a-life",
                    "title": "Chapter 2: Studying Around a Job, Kids, and a Life",
                    "order": 2,
                    "minutes": 12,
                    "summary": "Scheduling, environment, and energy management for adults.",
                    "learn": [
                        {"type": "p", "text": "Adults don't schedule study time — they schedule everything else and hope. Flip it: study gets a fixed, protected slot like a job shift, and it goes where your energy actually is. Most adults have one reliably decent window (early morning before the house wakes, lunch hour, or after kids' bedtime). Find yours and defend it."},
                        {"type": "list", "items": [
                            "Same time, same place, every session. Consistency removes the daily negotiation with yourself.",
                            "Phone in another room — the same rule as the kids' handbook, because your attention is attacked by the same machines.",
                            "Match task to energy: hard new material in your best window; review and easy reading when tired.",
                            "Tell your household what the slot is. Protected time only works if the people around you know it's protected.",
                            "Have a 'minimum session' plan: on terrible days, 10 minutes of review still counts. Streaks survive bad days; perfection doesn't.",
                        ]},
                        {"type": "tip", "text": "Anchor study to an existing habit: 'after my coffee, before I open email.' Habit-stacking beats willpower every week of the year."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 2.",
                        "questions": [
                            {"q": "Study time for adults works best when it's…", "options": ["a fixed protected slot at your high-energy time", "whenever there's leftover time", "only on weekends"], "answer": "a fixed protected slot at your high-energy time", "explain": "Fixed slots at good-energy times remove negotiation and use your real capacity."},
                            {"q": "On a terrible day, the right move is…", "options": ["the 10-minute minimum session to keep the streak alive", "skip entirely", "double up tomorrow"], "answer": "the 10-minute minimum session to keep the streak alive", "explain": "Minimum sessions preserve identity and momentum — 'I'm someone who shows up.'"},
                        ],
                    },
                },
                {
                    "slug": "choosing-your-track",
                    "title": "Chapter 3: Choosing Your Track — Start From the Goal",
                    "order": 3,
                    "minutes": 12,
                    "summary": "HSE, career, trade, life skills, or business — matching the Academy to the outcome.",
                    "learn": [
                        {"type": "p", "text": "Adults waste years collecting random courses. Start from the outcome and walk backwards: what do you want to be true in 18 months — a diploma in hand, a license, a higher wage, your own business? Then pick the track that serves it. The Academy's adult tracks exist for exactly this."},
                        {"type": "list", "items": [
                            "Adult Education track: high-school-equivalency prep (language arts, math, science, social studies) — choose this if the credential is the gate to your next step.",
                            "Career / Workforce: job skills, professional development, and interview-ready competencies — choose this for employment and advancement now.",
                            "Builder / Trade: real trade skills, including applied electrical engineering — choose this for licensure-path and high-demand hands-on work.",
                            "Life Skills & Leadership: personal finance, independent living, leading at work — the foundations everything else stands on.",
                            "Entrepreneurship: starting and running the business — pair it with a first customer conversation, not just coursework.",
                        ]},
                        {"type": "tip", "text": "Pick ONE primary track and a start date. A chosen track can be changed next month; an unchosen one guarantees drift."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 3.",
                        "questions": [
                            {"q": "The right way to choose a track is…", "options": ["start from your 18-month goal and work backwards", "take every course", "let the algorithm decide"], "answer": "start from your 18-month goal and work backwards", "explain": "Goal-first selection is what turns coursework into outcomes."},
                            {"q": "If a diploma or equivalency is the gate to your next step, your track is…", "options": ["Adult Education (HSE prep)", "Entrepreneurship", "whatever's shortest"], "answer": "Adult Education (HSE prep)", "explain": "The Adult Ed track exists to clear exactly that gate."},
                        ],
                    },
                },
                {
                    "slug": "turning-work-into-credentials",
                    "title": "Chapter 4: Turning Coursework Into Credentials and Income",
                    "order": 4,
                    "minutes": 12,
                    "summary": "Records, portfolios, certificates, and the paper trail that pays.",
                    "learn": [
                        {"type": "p", "text": "Coursework you can't show is a hobby. Every Academy course you complete generates printable records — mastery scores, lessons completed, dates. Collect them deliberately: a folder (digital or physical) that becomes your portfolio. When an employer, licensing board, or client asks 'what can you do,' your answer is documentation, not adjectives."},
                        {"type": "list", "items": [
                            "Print your records at the end of every course — don't trust yourself to 'do it later.'",
                            "Build a simple portfolio page or PDF: who you are, what you've completed, what you can demonstrably do.",
                            "Pair records with proof-of-work: projects from lessons (the trade and entrepreneurship courses produce real artifacts — use them).",
                            "List completed coursework on résumés and profiles under Education & Training — self-paced mastery with documentation is credible and respectable.",
                            "Employers pay for demonstrated skill; your records are the demonstration.",
                        ]},
                        {"type": "tip", "text": "The Records page can generate documentation any time — schedule a 15-minute 'paperwork Friday' once a month and stay current forever."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 4.",
                        "questions": [
                            {"q": "Coursework becomes credible to outsiders when…", "options": ["it's documented — records, portfolio, and proof of work", "you say you did it", "you finish it fast"], "answer": "it's documented — records, portfolio, and proof of work", "explain": "Documentation turns learning into a credential anyone can verify."},
                            {"q": "The habit that keeps your portfolio current is…", "options": ["a monthly 15-minute paperwork session printing records", "reconstructing everything in year five", "keeping it all in your head"], "answer": "a monthly 15-minute paperwork session printing records", "explain": "Small regular maintenance beats a painful reconstruction later."},
                        ],
                    },
                },
                {
                    "slug": "finishing-what-you-start",
                    "title": "Chapter 5: Finishing What You Start",
                    "order": 5,
                    "minutes": 12,
                    "summary": "The adult learner's real superpower: completion.",
                    "learn": [
                        {"type": "p", "text": "The adult education world is littered with abandoned Chapter 3s. What separates adults who transform their situation from adults who collect half-finished courses is not talent — it's a completion system: minimums, accountability, and visible progress. You already proved you can finish hard things; this is just the next one, with better tools."},
                        {"type": "list", "items": [
                            "Define the finish line before you start: which course, by when, and what you'll do with it after.",
                            "Minimums rule: your bad-day session still counts. Never miss twice in a row — one miss is life, two is a pattern.",
                            "Accountability: one person who sees your weekly progress. A text message with your progress bar screenshot works.",
                            "Make progress visible: your classroom progress bars, a wall calendar with X's, the printed records stacking up.",
                            "When a course stalls, diagnose before quitting: too hard (drop to review), wrong track (change tracks deliberately), or just a bad week (minimum session and continue).",
                        ]},
                        {"type": "tip", "text": "Finish the course you're in before buying the next one. Completion is a skill, and like every skill, it strengthens with repetition."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 5.",
                        "questions": [
                            {"q": "The rule that protects a study streak is…", "options": ["never miss twice in a row", "never miss ever", "only study when motivated"], "answer": "never miss twice in a row", "explain": "One miss is life; two is the start of quitting. Minimum sessions break the chain of two."},
                            {"q": "When a course stalls, the first move is…", "options": ["diagnose: too hard, wrong track, or bad week", "delete the account", "start three new courses"], "answer": "diagnose: too hard, wrong track, or bad week", "explain": "Each cause has a different fix — guessing leads to abandoning good courses."},
                        ],
                    },
                },
            ],
        },
    ],
}
