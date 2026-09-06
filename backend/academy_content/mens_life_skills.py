"""Men's Life Skills (full published course)."""

MENS_LIFE_SKILLS = {
    "slug": "mens-life-skills",
    "title": "Men's Life Skills",
    "summary": "Financial responsibility, employment, leadership, decision-making, digital literacy, and community participation.",
    "description": (
        "Men's Life Skills focuses on financial responsibility, budgeting, employment, "
        "career development, workplace skills, professional communication, leadership, "
        "decision-making, entrepreneurship, digital literacy, household responsibility, "
        "personal organization, economic resilience, and community participation."
    ),
    "subject": "life_skills",
    "subject_label": "Life Skills",
    "track": "life_skills",
    "tracks": ["life_skills"],
    "grades": ["adult"],
    "grade_label": "Adult",
    "status": "published",
    "audience": "Adult men building careers, households, and community leadership.",
    "est_hours": 28,
    "passing_score": 80,
    "learning_objectives": [
        "Manage personal finances and reduce debt.",
        "Succeed in job searches, interviews, and workplace roles.",
        "Communicate clearly and resolve conflicts professionally.",
        "Lead projects and develop entrepreneurial ideas.",
        "Use digital tools safely and productively.",
        "Organize personal and household responsibilities.",
        "Participate in community and civic life.",
    ],
    "units": [
        {
            "slug": "finance-and-employment",
            "title": "Finance and Employment",
            "summary": "Money management, job skills, and career planning.",
            "order": 1,
            "lessons": [
                {
                    "slug": "personal-finance",
                    "title": "Personal Finance and Budgeting",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Income, expenses, saving, and debt strategies.",
                    "learn": [
                        {"type": "p", "text": "Personal finance is about making your money work for you. Create a zero-based budget: income minus expenses minus savings equals zero. Attack high-interest debt first, then build savings."},
                        {"type": "list", "items": [
                            "Zero-based budget: every dollar has a job.",
                            "Debt snowball: smallest balance first for motivation.",
                            "Emergency fund prevents debt from setbacks.",
                            "Employer benefits: 401(k) match is free money.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about personal finance.",
                        "questions": [
                            {"q": "In a zero-based budget, all income is…", "options": ["assigned to expenses or savings", "spent randomly", "saved only"], "answer": "assigned to expenses or savings", "explain": "Zero-based budgeting gives every dollar a purpose."},
                            {"q": "High-interest debt should be paid…", "options": ["first", "last", "never"], "answer": "first", "explain": "High-interest debt costs the most over time, so pay it down quickly."},
                        ],
                    },
                },
                {
                    "slug": "workplace-skills",
                    "title": "Workplace Skills and Career Planning",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Resumes, interviews, professionalism, and growth.",
                    "learn": [
                        {"type": "p", "text": "Career planning means knowing your strengths, targeting roles, and marketing yourself. Resumes should be results-oriented. Interviews are conversations where you show fit. Soft skills separate good employees from great ones."},
                        {"type": "list", "items": [
                            "Resume: use action verbs and metrics.",
                            "Interview: research the company, ask good questions.",
                            "Soft skills: reliability, communication, problem solving.",
                            "Growth: seek feedback, learn new skills, build a portfolio.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about workplace skills.",
                        "questions": [
                            {"q": "A results-oriented resume focuses on…", "options": ["achievements with numbers", "long paragraphs", "personal hobbies"], "answer": "achievements with numbers", "explain": "Quantified results show concrete impact."},
                            {"q": "Soft skills are…", "options": ["interpersonal and thinking skills", "hard technical skills", "tools"], "answer": "interpersonal and thinking skills", "explain": "Soft skills include communication, reliability, and problem solving."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "leadership-and-organization",
            "title": "Leadership and Organization",
            "summary": "Decision making, organization, and community engagement.",
            "order": 2,
            "lessons": [
                {
                    "slug": "leadership-and-decision-making",
                    "title": "Leadership and Decision Making",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Influence, accountability, and strategic choices.",
                    "learn": [
                        {"type": "p", "text": "Leadership means taking responsibility, setting direction, and helping others succeed. Decision making works best when you gather facts, consider consequences, involve stakeholders, and review outcomes."},
                        {"type": "list", "items": [
                            "Accountability: own outcomes, good and bad.",
                            "Decision matrix: list options, score criteria, choose.",
                            "Strategic: align daily actions with long-term goals.",
                            "Communication: share the why, not just the what.",
                        ]},
                        {"type": "example", "title": "Decision matrix", "text": "Choosing a tool? Score each option on cost, durability, and ease of use. The highest total is the best fit."},
                    ],
                    "check": {
                        "prompt": "Show what you know about leadership and decision making.",
                        "questions": [
                            {"q": "Accountability means…", "options": ["owning your outcomes", "blaming others", "ignoring mistakes"], "answer": "owning your outcomes", "explain": "Accountability is taking responsibility for results."},
                            {"q": "A decision matrix helps you…", "options": ["compare options objectively", "avoid all decisions", "spend more money"], "answer": "compare options objectively", "explain": "A matrix turns subjective choices into scored comparisons."},
                        ],
                    },
                },
                {
                    "slug": "organization-and-community",
                    "title": "Organization and Community",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Personal organization, digital literacy, and community participation.",
                    "learn": [
                        {"type": "p", "text": "Organization reduces stress and increases productivity. Use calendars, to-do lists, and routines. Digital literacy keeps you safe and effective online. Community participation builds belonging and opportunity."},
                        {"type": "list", "items": [
                            "Calendar: block time for priorities.",
                            "To-do list: top 3 tasks each morning.",
                            "Digital literacy: verify sources, protect data, use productivity tools.",
                            "Community: volunteer, vote, mentor, support local.",
                        ]},
                        {"type": "activity", "title": "Weekly system", "text": "Design a weekly organization system. Include one calendar habit, one to-do list method, and one community action."},
                    ],
                    "check": {
                        "prompt": "Show what you know about organization and community.",
                        "questions": [
                            {"q": "A good morning habit is to…", "options": ["identify the top 3 tasks", "check social media for hours", "skip planning"], "answer": "identify the top 3 tasks", "explain": "Starting with priorities focuses your day."},
                            {"q": "Community participation includes…", "options": ["volunteering and voting", "staying home always", "arguing online"], "answer": "volunteering and voting", "explain": "Participation builds stronger communities."},
                        ],
                    },
                },
            ],
        },
    ],
}
