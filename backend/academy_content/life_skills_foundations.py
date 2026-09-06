"""Life Skills Foundations (full published course)."""

LIFE_SKILLS_FOUNDATIONS = {
    "slug": "life-skills-foundations",
    "title": "Life Skills",
    "summary": "Financial literacy, communication, decision making, digital literacy, household management, and career planning.",
    "description": (
        "Life Skills Foundations prepares adults for independent living and workplace success. "
        "Units cover financial literacy, communication, time management, digital literacy, "
        "household management, consumer knowledge, navigating systems, and career planning."
    ),
    "subject": "life_skills",
    "subject_label": "Life Skills",
    "track": "life_skills",
    "tracks": ["life_skills"],
    "grades": ["adult"],
    "grade_label": "Adult",
    "status": "published",
    "audience": "Adult learners building independence, workplace skills, and personal organization.",
    "est_hours": 36,
    "passing_score": 80,
    "learning_objectives": [
        "Create and maintain a personal budget.",
        "Use banking tools and understand credit and debt.",
        "Communicate professionally in writing and in person.",
        "Manage time, set goals, and make decisions.",
        "Stay safe online and evaluate information.",
        "Navigate household tasks and common adult systems.",
        "Plan a career path and prepare job materials.",
    ],
    "units": [
        {
            "slug": "financial-literacy",
            "title": "Financial Literacy",
            "summary": "Budgeting, banking, credit, debt, taxes, and consumer decisions.",
            "order": 1,
            "lessons": [
                {
                    "slug": "budgeting-and-banking",
                    "title": "Budgeting and Banking",
                    "order": 1,
                    "minutes": 20,
                    "summary": "Build a budget and understand bank accounts.",
                    "learn": [
                        {"type": "p", "text": "A budget is a plan for your money. List income and expenses. Save before you spend. A bank account keeps money safe and makes payments easy."},
                        {"type": "list", "items": [
                            "Income: wages, benefits, gifts.",
                            "Fixed expenses: rent, utilities, insurance.",
                            "Variable expenses: food, gas, entertainment.",
                            "Emergency fund: 3–6 months of expenses.",
                        ]},
                        {"type": "example", "title": "Sample budget", "text": "Monthly income $2,400. Rent $800, utilities $150, transportation $200, food $300, savings $240. Remaining: $710."},
                    ],
                    "check": {
                        "prompt": "Show what you know about budgeting and banking.",
                        "questions": [
                            {"q": "What is a fixed expense?", "options": ["a cost that stays the same each month", "a cost that changes", "savings"], "answer": "a cost that stays the same each month", "explain": "Fixed expenses such as rent do not vary month to month."},
                            {"q": "An emergency fund should cover…", "options": ["3–6 months of expenses", "one month only", "nothing"], "answer": "3–6 months of expenses", "explain": "An emergency fund prepares you for unexpected costs."},
                        ],
                    },
                },
                {
                    "slug": "credit-debt-and-taxes",
                    "title": "Credit, Debt, and Taxes",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Credit scores, loans, and income taxes.",
                    "learn": [
                        {"type": "p", "text": "Credit lets you borrow money with interest. A credit score shows how reliably you repay debt. High scores get lower interest rates. Debt that grows faster than income becomes a burden."},
                        {"type": "list", "items": [
                            "Credit score factors: payment history, amounts owed, length of history.",
                            "Interest = cost of borrowing.",
                            "Taxes fund government services.",
                            "File taxes annually; withholdings reduce surprise bills.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about credit, debt, and taxes.",
                        "questions": [
                            {"q": "Which factor most affects your credit score?", "options": ["payment history", "your age", "your height"], "answer": "payment history", "explain": "Paying bills on time is the biggest factor."},
                            {"q": "What is interest?", "options": ["the cost of borrowing money", "a bank bonus", "tax"], "answer": "the cost of borrowing money", "explain": "Interest is what you pay to use someone else's money."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "communication-and-organization",
            "title": "Communication and Organization",
            "summary": "Professional communication, time management, and goal setting.",
            "order": 2,
            "lessons": [
                {
                    "slug": "professional-communication",
                    "title": "Professional Communication",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Email, meetings, conflict resolution, and listening.",
                    "learn": [
                        {"type": "p", "text": "Communication is more than words. Tone, timing, and listening matter. In the workplace, clear emails, respectful meetings, and calm conflict resolution build trust."},
                        {"type": "list", "items": [
                            "Email: clear subject, short paragraphs, professional tone.",
                            "Meetings: arrive on time, listen first, speak concisely.",
                            "Conflict: use 'I' statements, focus on the problem, not the person.",
                            "Listening: eye contact, nodding, ask clarifying questions.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about professional communication.",
                        "questions": [
                            {"q": "A good email subject line is…", "options": ["specific and short", "empty", "all capital letters"], "answer": "specific and short", "explain": "Short subjects help busy readers understand your message quickly."},
                            {"q": "'I feel frustrated when the report is late' is an example of…", "options": ["an 'I' statement", "blaming", "a question"], "answer": "an 'I' statement", "explain": "'I' statements express feelings without attacking others."},
                        ],
                    },
                },
                {
                    "slug": "time-management-and-goals",
                    "title": "Time Management and Goal Setting",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Prioritize, schedule, and track progress.",
                    "learn": [
                        {"type": "p", "text": "Time management is choosing what matters most. SMART goals are Specific, Measurable, Achievable, Relevant, and Time-bound. Use a planner or digital calendar to block time for priorities."},
                        {"type": "list", "items": [
                            "Urgent/important matrix: do important first.",
                            "Time blocking: assign tasks to fixed slots.",
                            "SMART goals give clear targets.",
                            "Review goals weekly and adjust as needed.",
                        ]},
                        {"type": "activity", "title": "Weekly plan", "text": "Write a SMART goal for this week. Create a time-blocked schedule for three days to achieve it."},
                    ],
                    "check": {
                        "prompt": "Show what you know about time management and goals.",
                        "questions": [
                            {"q": "A SMART goal is…", "options": ["specific, measurable, achievable, relevant, time-bound", "always easy", "written in all caps"], "answer": "specific, measurable, achievable, relevant, time-bound", "explain": "SMART criteria make goals clear and reachable."},
                            {"q": "The urgent/important matrix helps you…", "options": ["prioritize tasks", "sleep more", "spend money"], "answer": "prioritize tasks", "explain": "The matrix sorts tasks so you focus on what matters most."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "digital-literacy-and-systems",
            "title": "Digital Literacy and Systems",
            "summary": "Online safety, information literacy, household tasks, and navigating services.",
            "order": 3,
            "lessons": [
                {
                    "slug": "digital-literacy-and-safety",
                    "title": "Digital Literacy and Online Safety",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Evaluate information, protect privacy, and use digital tools.",
                    "learn": [
                        {"type": "p", "text": "Digital literacy means using technology effectively and safely. Not everything online is true. Protect your personal information. Use strong passwords and two-factor authentication."},
                        {"type": "list", "items": [
                            "Fact-check: who wrote it, when, and why?",
                            "Strong password: long, unique, with numbers and symbols.",
                            "Phishing: fake messages asking for personal info.",
                            "Digital footprint: everything you post stays online.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about digital literacy and safety.",
                        "questions": [
                            {"q": "A red flag for phishing is…", "options": ["a message asking for your password", "a message from your friend", "a website address"], "answer": "a message asking for your password", "explain": "Legitimate organizations will not ask for passwords by email or text."},
                            {"q": "A strong password should be…", "options": ["long and unique", "your birthday", "the word 'password'"], "answer": "long and unique", "explain": "Long, unique passwords are harder to guess or crack."},
                        ],
                    },
                },
                {
                    "slug": "household-and-systems-navigation",
                    "title": "Household Management and Navigating Systems",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Home maintenance, community resources, and civic systems.",
                    "learn": [
                        {"type": "p", "text": "Managing a home includes cleaning schedules, maintenance tasks, and knowing how to access community resources such as libraries, health clinics, and social services."},
                        {"type": "list", "items": [
                            "Home maintenance: change air filters, test smoke detectors, unclog drains.",
                            "Community resources: libraries, food banks, health clinics.",
                            "Civic systems: DMV, courts, voting, public schools.",
                            "Keep important documents organized and backed up.",
                        ]},
                        {"type": "activity", "title": "Resource map", "text": "List three community resources near you. For each, write the address, hours, and what they provide."},
                    ],
                    "check": {
                        "prompt": "Show what you know about household and systems navigation.",
                        "questions": [
                            {"q": "How often should smoke detector batteries be tested?", "options": ["monthly", "yearly", "never"], "answer": "monthly", "explain": "Test smoke alarms monthly and replace batteries yearly."},
                            {"q": "The DMV handles…", "options": ["driver licenses and vehicle registration", "tax returns", "health insurance"], "answer": "driver licenses and vehicle registration", "explain": "DMV offices manage driver services and vehicle records."},
                        ],
                    },
                },
                {
                    "slug": "career-planning-and-professionalism",
                    "title": "Career Planning and Professionalism",
                    "order": 7,
                    "minutes": 20,
                    "summary": "Career exploration, resumes, interviews, and workplace behavior.",
                    "learn": [
                        {"type": "p", "text": "Career planning starts with self-assessment: What do you enjoy? What are you good at? Research occupations, build a resume, practice interviews, and demonstrate professionalism through punctuality, dress, and attitude."},
                        {"type": "list", "items": [
                            "Resume: contact, objective, experience, education, skills.",
                            "Interview: dress neat, arrive early, answer with examples.",
                            "Soft skills: teamwork, reliability, communication.",
                            "Professionalism: show up on time, follow directions, take feedback.",
                        ]},
                        {"type": "activity", "title": "Resume draft", "text": "Draft a one-page resume with contact info, objective, three bullet points of experience, and three skills."},
                    ],
                    "check": {
                        "prompt": "Show what you know about career planning.",
                        "questions": [
                            {"q": "Which belongs on a resume?", "options": ["contact info, experience, and skills", "your age and height", "your employer's salary"], "answer": "contact info, experience, and skills", "explain": "Resumes focus on qualifications and contact information."},
                            {"q": "Professionalism includes…", "options": ["punctuality and respect", "being late and casual", "ignoring feedback"], "answer": "punctuality and respect", "explain": "Professionalism is shown through reliable, respectful behavior."},
                        ],
                    },
                },
                {
                    "slug": "decision-making-and-problem-solving",
                    "title": "Decision Making and Problem Solving",
                    "order": 8,
                    "minutes": 18,
                    "summary": "Evaluate options, anticipate consequences, and solve problems step by step.",
                    "learn": [
                        {"type": "p", "text": "Good decisions weigh pros and cons, consider long-term effects, and align with values. Problem solving follows steps: define the problem, brainstorm solutions, choose one, act, and review results."},
                        {"type": "list", "items": [
                            "Define the problem clearly.",
                            "Brainstorm without judging.",
                            "Evaluate options against values and goals.",
                            "Act and review: did it work? adjust.",
                        ]},
                        {"type": "example", "title": "Decision matrix", "text": "Choosing a car? List options, then score each on cost, reliability, and fuel efficiency. The highest total wins."},
                    ],
                    "check": {
                        "prompt": "Show what you know about decision making and problem solving.",
                        "questions": [
                            {"q": "The first step in problem solving is to…", "options": ["define the problem", "blame someone", "ignore it"], "answer": "define the problem", "explain": "You cannot solve a problem you have not clearly identified."},
                            {"q": "A decision matrix helps you…", "options": ["compare options against criteria", "make you rich", "write a grocery list"], "answer": "compare options against criteria", "explain": "A matrix scores each option on what matters most."},
                        ],
                    },
                },
            ],
        },
    ],
}
