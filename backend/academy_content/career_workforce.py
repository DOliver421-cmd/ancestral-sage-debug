"""Career / Workforce (full published course)."""

CAREER_WORKFORCE = {
    "slug": "career-workforce",
    "title": "Career / Workforce",
    "summary": "Career exploration, skills identification, resumes, interviewing, workplace communication, digital skills, career planning, and continuing education.",
    "description": (
        "This workforce course prepares adult learners for successful careers. "
        "Students explore occupations, identify transferable skills, write resumes and "
        "cover letters, practice interviews, understand workplace expectations, build "
        "digital workplace skills, plan continuing education, and learn entrepreneurship basics."
    ),
    "subject": "career",
    "subject_label": "Career",
    "track": "career",
    "tracks": ["career"],
    "grades": ["adult"],
    "grade_label": "Adult",
    "status": "published",
    "audience": "Adult learners entering the workforce, changing careers, or upskilling.",
    "est_hours": 30,
    "passing_score": 80,
    "learning_objectives": [
        "Assess personal strengths, values, and career interests.",
        "Identify transferable skills and build a skills inventory.",
        "Write targeted resumes and cover letters.",
        "Interview confidently using structured preparation.",
        "Demonstrate professional workplace behavior.",
        "Use digital tools common in modern workplaces.",
        "Plan continuing education and skill development.",
    ],
    "units": [
        {
            "slug": "career-exploration-and-skills",
            "title": "Career Exploration and Skills",
            "summary": "Explore careers, assess skills, and set goals.",
            "order": 1,
            "lessons": [
                {
                    "slug": "career-exploration",
                    "title": "Career Exploration",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Identify interests, values, and potential occupations.",
                    "learn": [
                        {"type": "p", "text": "Career exploration matches your interests, values, and skills with real occupations. Research job duties, pay, education requirements, and growth. Use labor-market information to choose wisely."},
                        {"type": "list", "items": [
                            "Interests: what you enjoy doing.",
                            "Values: what matters most (income, flexibility, impact).",
                            "Skills: what you are good at (technical and soft).",
                            "Labor market: demand, salary, conditions.",
                        ]},
                        {"type": "activity", "title": "Career research", "text": "Pick three occupations you are curious about. Research each: duties, pay, education, and job outlook. Write a short comparison."},
                    ],
                    "check": {
                        "prompt": "Show what you know about career exploration.",
                        "questions": [
                            {"q": "Career exploration considers…", "options": ["interests, values, and skills", "only salary", "random choice"], "answer": "interests, values, and skills", "explain": "Good career choices align with what you enjoy, value, and can do."},
                        {"q": "Labor-market information includes…", "options": ["demand and salary data", "favorite colors", "weather"], "answer": "demand and salary data", "explain": "Labor-market data shows job availability and pay."},
                        ],
                    },
                },
                {
                    "slug": "skills-inventory",
                    "title": "Skills Identification and Inventory",
                    "order": 2,
                    "minutes": 18,
                    "summary": "List hard and soft skills with evidence.",
                    "learn": [
                        {"type": "p", "text": "A skills inventory lists what you can do. Hard skills are technical (coding, welding, accounting). Soft skills are interpersonal (communication, teamwork). For each skill, provide evidence: a job, class, or project."},
                        {"type": "list", "items": [
                            "Hard skills: specific, teachable, measurable.",
                            "Soft skills: communication, reliability, problem solving.",
                            "Evidence: 'Led a team of 4' is stronger than 'good leader'.",
                            "Gap analysis: what skills are missing for your target job?",
                        ]},
                        {"type": "activity", "title": "Skills inventory", "text": "Write a skills inventory with 10 hard skills and 10 soft skills. Rate each beginner/intermediate/advanced."},
                    ],
                    "check": {
                        "prompt": "Show what you know about skills inventories.",
                        "questions": [
                            {"q": "Which is a hard skill?", "options": ["welding", "teamwork", "punctuality"], "answer": "welding", "explain": "Hard skills are technical and measurable."},
                            {"q": "Evidence on a skills inventory should be…", "options": ["specific and verifiable", "vague", "invented"], "answer": "specific and verifiable", "explain": "Employers need proof of your claims."},
                        ],
                    },
                },
                {
                    "slug": "career-planning",
                    "title": "Career Planning and Goal Setting",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Create a career plan with SMART goals.",
                    "learn": [
                        {"type": "p", "text": "A career plan connects where you are to where you want to be. Use SMART goals for each step: gain a certification, complete an internship, earn a promotion."},
                        {"type": "list", "items": [
                            "Short-term (1 year), medium-term (2–5 years), long-term (5+ years).",
                            "SMART: Specific, Measurable, Achievable, Relevant, Time-bound.",
                            "Review the plan quarterly.",
                            "Find a mentor in your target field.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about career planning.",
                        "questions": [
                            {"q": "A SMART goal is…", "options": ["clear and trackable", "vague and dreamy", "impossible"], "answer": "clear and trackable", "explain": "SMART goals are structured so you know when you have succeeded."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "job-materials-and-interviews",
            "title": "Job Materials and Interviews",
            "summary": "Resumes, cover letters, applications, and interviews.",
            "order": 2,
            "lessons": [
                {
                    "slug": "resumes-and-cover-letters",
                    "title": "Resumes and Cover Letters",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Targeted, results-oriented application materials.",
                    "learn": [
                        {"type": "p", "text": "A resume is a one- to two-page summary of qualifications. Use action verbs and metrics. A cover letter tells a story: why this role, why this company, and why you. Tailor every application."},
                        {"type": "list", "items": [
                            "Contact info, summary, experience, education, skills.",
                            "Action verbs: led, built, improved, delivered.",
                            "Metrics: 'increased sales by 20%.'",
                            "Cover letter: 3–4 short paragraphs.",
                        ]},
                        {"type": "activity", "title": "Tailor a resume", "text": "Take a generic resume. Rewrite the experience bullets to target a specific job posting."},
                    ],
                    "check": {
                        "prompt": "Show what you know about resumes and cover letters.",
                        "questions": [
                            {"q": "Which is strongest on a resume?", "options": ["'Increased sales by 20%'", "'Did sales'", "'Sales'"], "answer": "'Increased sales by 20%'", "explain": "Metrics show concrete impact."},
                        ],
                    },
                },
                {
                    "slug": "interviewing",
                    "title": "Interviewing",
                    "order": 5,
                    "minutes": 20,
                    "summary": "Preparation, common questions, and professional presence.",
                    "learn": [
                        {"type": "p", "text": "Interviewing is a two-way conversation. Research the company. Prepare STAR stories. Dress slightly better than the job requires. Ask thoughtful questions at the end."},
                        {"type": "list", "items": [
                            "STAR: Situation, Task, Action, Result.",
                            "Common: 'Tell me about yourself,' 'Why this role,' 'Strengths and weaknesses.'",
                            "Questions for them: team, success metrics, growth path.",
                            "Follow-up: thank-you email within 24 hours.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about interviewing.",
                        "questions": [
                            {"q": "STAR helps you answer behavioral questions by…", "options": ["telling a specific story with context and results", "listing your hobbies", "talking only about pay"], "answer": "telling a specific story with context and results", "explain": "STAR stories provide evidence of past performance."},
                        {"q": "A good question to ask the interviewer is about…", "options": ["success metrics and team culture", "their salary only", "the weather"], "answer": "success metrics and team culture", "explain": "Asking about success and culture shows you care about fit."},
                        ],
                    },
                },
                {
                    "slug": "workplace-expectations",
                    "title": "Workplace Expectations and Digital Skills",
                    "order": 6,
                    "minutes": 20,
                    "summary": "Professional behavior and common digital tools.",
                    "learn": [
                        {"type": "p", "text": "Workplace expectations include punctuality, reliability, communication, and continuous learning. Digital skills: email, calendars, collaboration tools, and basic data entry are essential in most jobs."},
                        {"type": "list", "items": [
                            "Professional behavior: dress, tone, deadlines.",
                            "Communication: clear, respectful, concise.",
                            "Digital tools: email, spreadsheets, video calls.",
                            "Learning: adapt to new tools quickly.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about workplace expectations and digital skills.",
                        "questions": [
                            {"q": "Workplace reliability means…", "options": ["showing up and meeting commitments", "arriving late often", "ignoring emails"], "answer": "showing up and meeting commitments", "explain": "Reliability builds trust and leads to advancement."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "continuing-education-and-entrepreneurship",
            "title": "Continuing Education and Entrepreneurship",
            "summary": "Upskilling, credentials, and business fundamentals.",
            "order": 3,
            "lessons": [
                {
                    "slug": "continuing-education",
                    "title": "Continuing Education and Upskilling",
                    "order": 7,
                    "minutes": 18,
                    "summary": "Credentials, online learning, and career pathways.",
                    "learn": [
                        {"type": "p", "text": "Continuing education keeps you competitive. Credentials such as certificates, licenses, and degrees signal expertise. Online learning lets you upskill while working."},
                        {"type": "list", "items": [
                            "Certificate: short, focused, employer-recognized.",
                            "License: legally required for some jobs.",
                            "Online: self-paced, modular, affordable.",
                            "Learning plan: skill gaps → course → credential → application.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about continuing education.",
                        "questions": [
                            {"q": "A certificate shows…", "options": ["specific skill or knowledge", "your age", "your height"], "answer": "specific skill or knowledge", "explain": "Certificates verify focused expertise."},
                        ],
                    },
                },
                {
                    "slug": "entrepreneurship-fundamentals",
                    "title": "Entrepreneurship Fundamentals",
                    "order": 8,
                    "minutes": 18,
                    "summary": "Start small, validate ideas, and grow.",
                    "learn": [
                        {"type": "p", "text": "Entrepreneurship means creating a business to solve a problem. Start with a minimum viable product, get feedback, and iterate. Track cash flow and stay compliant with regulations."},
                        {"type": "list", "items": [
                            "Idea validation: talk to real customers before building.",
                            "MVP: simplest version that delivers value.",
                            "Cash flow: money in minus money out.",
                            "Legal: register business, pay taxes, get insurance.",
                        ]},
                        {"type": "activity", "title": "Lean canvas", "text": "Fill out a one-page lean canvas for a small business idea. Include problem, solution, customers, revenue, and cost."},
                    ],
                    "check": {
                        "prompt": "Show what you know about entrepreneurship fundamentals.",
                        "questions": [
                            {"q": "An MVP is…", "options": ["the simplest version that delivers value", "the most expensive product", "a business plan"], "answer": "the simplest version that delivers value", "explain": "An MVP tests demand before heavy investment."},
                            {"q": "Cash flow tracks…", "options": ["money in and out over time", "customer happiness", "website traffic"], "answer": "money in and out over time", "explain": "Cash flow shows whether a business can sustain operations."},
                        ],
                    },
                },
            ],
        },
    ],
}
