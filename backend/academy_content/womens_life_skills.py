"""Women's Life Skills (full published course)."""

WOMENS_LIFE_SKILLS = {
    "slug": "womens-life-skills",
    "title": "Women's Life Skills",
    "summary": "Financial independence, career development, workplace navigation, leadership, and community participation.",
    "description": (
        "Women's Life Skills focuses on financial independence, career development, "
        "workplace navigation, entrepreneurship, leadership, professional communication, "
        "digital literacy, decision-making, household and family planning, economic "
        "resilience, and community participation."
    ),
    "subject": "life_skills",
    "subject_label": "Life Skills",
    "track": "life_skills",
    "tracks": ["life_skills"],
    "grades": ["adult"],
    "grade_label": "Adult",
    "status": "published",
    "audience": "Adult women building independence, careers, and leadership.",
    "est_hours": 28,
    "passing_score": 80,
    "learning_objectives": [
        "Build and maintain a personal budget and savings plan.",
        "Navigate workplace dynamics and negotiate fairly.",
        "Develop an entrepreneurial mindset and basic business knowledge.",
        "Communicate with confidence in professional settings.",
        "Lead projects and influence positive community change.",
    ],
    "units": [
        {
            "slug": "financial-and-career-development",
            "title": "Financial and Career Development",
            "summary": "Budgeting, workplace navigation, and career growth.",
            "order": 1,
            "lessons": [
                {
                    "slug": "financial-independence",
                    "title": "Financial Independence",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Budgeting, saving, and building financial security.",
                    "learn": [
                        {"type": "p", "text": "Financial independence means having control over your money. Track spending, set savings goals, build an emergency fund, and understand your rights and options with credit."},
                        {"type": "list", "items": [
                            "Track every expense for one month.",
                            "Pay yourself first: save before discretionary spending.",
                            "Understand paychecks: gross vs. net, deductions.",
                            "Know your rights under equal-pay laws.",
                        ]},
                        {"type": "activity", "title": "Monthly budget", "text": "Create a one-page monthly budget for a hypothetical income. Include income, fixed costs, variable costs, and savings."},
                    ],
                    "check": {
                        "prompt": "Show what you know about financial independence.",
                        "questions": [
                            {"q": "Paying yourself first means…", "options": ["saving before spending", "buying new clothes first", "giving all money away"], "answer": "saving before spending", "explain": "Paying yourself first treats savings as a non-negotiable expense."},
                            {"q": "Gross pay is…", "options": ["earnings before deductions", "take-home pay", "a tax"], "answer": "earnings before deductions", "explain": "Gross pay is what you earn before taxes and other deductions are removed."},
                        ],
                    },
                },
                {
                    "slug": "career-development",
                    "title": "Career Development and Workplace Navigation",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Skill building, resumes, interviews, and advancement.",
                    "learn": [
                        {"type": "p", "text": "Career development is a continuous process. Know your skills and values. Build a resume that shows results, not just duties. Prepare for interviews with stories that demonstrate competence. Ask for feedback and seek mentors."},
                        {"type": "list", "items": [
                            "Resume: action verbs, numbers, results.",
                            "Interview: prepare STAR stories (Situation, Task, Action, Result).",
                            "Negotiation: know your worth, research market rates, practice asking.",
                            "Networking: relationships open doors.",
                        ]},
                        {"type": "example", "title": "STAR story", "text": "Situation: team fell behind. Task: I took ownership. Action: created a tracker. Result: finished two days early."},
                    ],
                    "check": {
                        "prompt": "Show what you know about career development.",
                        "questions": [
                            {"q": "A STAR story is used in…", "options": ["interviews", "budgeting", "cooking"], "answer": "interviews", "explain": "STAR stories structure answers about past performance."},
                            {"q": "Networking means…", "options": ["building professional relationships", "using the internet only", "working alone"], "answer": "building professional relationships", "explain": "Networking creates connections that can lead to opportunities."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "leadership-and-community",
            "title": "Leadership and Community",
            "summary": "Leadership, decision making, and community participation.",
            "order": 2,
            "lessons": [
                {
                    "slug": "leadership-and-entrepreneurship",
                    "title": "Leadership and Entrepreneurship",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Lead projects, start ventures, and build influence.",
                    "learn": [
                        {"type": "p", "text": "Leadership is influence, not title. It means setting direction, supporting others, and taking responsibility. Entrepreneurship is creating value by solving problems. Both require confidence, planning, and resilience."},
                        {"type": "list", "items": [
                            "Lead by example: show the behavior you want to see.",
                            "Delegate: trust others with responsibility.",
                            "Business model: who pays, what for, how delivered.",
                            "Resilience: learn from failure and adjust.",
                        ]},
                        {"type": "activity", "title": "Mini-business plan", "text": "Write a one-page plan for a small service business. Name the service, customers, price, and one marketing idea."},
                    ],
                    "check": {
                        "prompt": "Show what you know about leadership and entrepreneurship.",
                        "questions": [
                            {"q": "Good leadership includes…", "options": ["taking responsibility and supporting others", "blaming the team", "avoiding decisions"], "answer": "taking responsibility and supporting others", "explain": "Leaders model the behavior they expect from others."},
                            {"q": "A business model answers…", "options": ["who pays and what for", "the color of the logo", "the number of employees"], "answer": "who pays and what for", "explain": "A business model describes how a company creates and captures value."},
                        ],
                    },
                },
                {
                    "slug": "community-participation",
                    "title": "Community Participation",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Volunteering, advocacy, and local engagement.",
                    "learn": [
                        {"type": "p", "text": "Strong communities depend on participation. Volunteer, attend meetings, support local businesses, and advocate for issues that matter. Community engagement builds networks and creates change."},
                        {"type": "list", "items": [
                            "Volunteer: donate time and skills.",
                            "Advocate: write, speak, or organize for a cause.",
                            "Local: shop local, attend events, vote locally.",
                            "Networking: community ties can lead to jobs and support.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about community participation.",
                        "questions": [
                            {"q": "Community participation can lead to…", "options": ["networks and change", "isolation", "higher taxes"], "answer": "networks and change", "explain": "Active participation builds connections and influences community decisions."},
                        ],
                    },
                },
            ],
        },
    ],
}
