"""Entrepreneurship Foundations (full published course)."""

ENTREPRENEURSHIP_FOUNDATIONS = {
    "slug": "entrepreneurship-foundations",
    "title": "Entrepreneurship",
    "summary": "Identifying opportunities, business models, finance, marketing, sales, operations, planning, and business strategy.",
    "description": (
        "Entrepreneurship Foundations teaches the full lifecycle of starting and growing a business. "
        "Topics include opportunity recognition, problem solving, customers, value creation, "
        "business models, finance, pricing, marketing, sales, operations, planning, record keeping, "
        "digital business, ethics, and strategy."
    ),
    "subject": "entrepreneurship",
    "subject_label": "Entrepreneurship",
    "track": "entrepreneurship",
    "tracks": ["entrepreneurship"],
    "grades": ["adult"],
    "grade_label": "Adult",
    "status": "published",
    "audience": "Adult learners starting or growing a small business.",
    "est_hours": 34,
    "passing_score": 80,
    "learning_objectives": [
        "Identify and evaluate business opportunities.",
        "Define a business model and value proposition.",
        "Calculate costs, pricing, and break-even points.",
        "Create a marketing plan and sales funnel.",
        "Plan operations and manage day-to-day execution.",
        "Keep financial records and interpret key metrics.",
        "Apply digital tools and ethical practices.",
        "Develop and test a business strategy.",
    ],
    "units": [
        {
            "slug": "opportunity-and-business-model",
            "title": "Opportunity and Business Model",
            "summary": "Find problems, design solutions, and map business models.",
            "order": 1,
            "lessons": [
                {
                    "slug": "identifying-opportunities",
                    "title": "Identifying Opportunities",
                    "order": 1,
                    "minutes": 20,
                    "summary": "Spot problems, validate demand, and design value.",
                    "learn": [
                        {"type": "p", "text": "Opportunities hide in frustrations, inefficiencies, and unmet needs. Listen to customers, observe behavior, and test assumptions before building."},
                        {"type": "list", "items": [
                            "Pain points: tasks people complain about.",
                            "Observation: watch how people actually behave.",
                            "Validation: interviews, landing pages, pre-orders.",
                            "Value proposition: what problem you solve and for whom.",
                        ]},
                        {"type": "activity", "title": "Opportunity journal", "text": "For one week, write down three frustrations you or others experience. Choose one that seems solvable and write a one-page opportunity brief."},
                    ],
                    "check": {
                        "prompt": "Show what you know about identifying opportunities.",
                        "questions": [
                            {"q": "A good opportunity often starts with…", "options": ["a customer pain point", "random luck", "copying a competitor"], "answer": "a customer pain point", "explain": "Solving a real problem creates genuine demand."},
                            {"q": "Validation means…", "options": ["testing demand before building", "guessing", "asking friends only"], "answer": "testing demand before building", "explain": "Validation reduces the risk of building something nobody wants."},
                        ],
                    },
                },
                {
                    "slug": "business-models",
                    "title": "Business Models and Value Creation",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Choose a model and design your value proposition.",
                    "learn": [
                        {"type": "p", "text": "A business model describes how you create, deliver, and capture value. Common models: product sales, subscription, marketplace, freemium, and service. A lean canvas maps the model on one page."},
                        {"type": "list", "items": [
                            "Revenue streams: how you make money.",
                            "Cost structure: fixed and variable costs.",
                            "Channels: how you reach customers.",
                            "Key metrics: CAC, LTV, churn, margin.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about business models.",
                        "questions": [
                            {"q": "A subscription model means…", "options": ["customers pay regularly for ongoing access", "one-time sale only", "free service"], "answer": "customers pay regularly for ongoing access", "explain": "Subscriptions create predictable recurring revenue."},
                            {"q": "CAC stands for…", "options": ["customer acquisition cost", "company annual cash", "cost of all customers"], "answer": "customer acquisition cost", "explain": "CAC is the average cost to acquire one customer."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "finance-marketing-and-operations",
            "title": "Finance, Marketing, and Operations",
            "summary": "Money, customers, and execution.",
            "order": 2,
            "lessons": [
                {
                    "slug": "finance-and-pricing",
                    "title": "Finance and Pricing",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Costs, pricing strategies, and break-even analysis.",
                    "learn": [
                        {"type": "p", "text": "Finance tracks money in and out. Fixed costs stay the same (rent). Variable costs change with volume (materials). Pricing must cover costs and reflect value. Break-even: how many units to cover total costs."},
                        {"type": "list", "items": [
                            "Revenue = price × quantity.",
                            "Gross profit = revenue − cost of goods sold.",
                            "Net profit = gross profit − expenses.",
                            "Break-even units = fixed costs ÷ (price − variable cost per unit).",
                        ]},
                        {"type": "example", "title": "Break-even", "text": "Fixed costs $1,000, price $20, variable cost $8 per unit. Break-even = 1,000 ÷ (20 − 8) ≈ 84 units."},
                    ],
                    "check": {
                        "prompt": "Show what you know about finance and pricing.",
                        "questions": [
                            {"q": "Break-even is the point where…", "options": ["revenue equals total costs", "you lose the most money", "customers are unhappy"], "answer": "revenue equals total costs", "explain": "At break-even, profit is zero; every sale after that contributes to profit."},
                            {"q": "Variable costs change with…", "options": ["volume of production", "time of year", "employee birthdays"], "answer": "volume of production", "explain": "Variable costs such as materials increase as you make more."},
                        ],
                    },
                },
                {
                    "slug": "marketing-and-sales",
                    "title": "Marketing and Sales",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Positioning, channels, and converting customers.",
                    "learn": [
                        {"type": "p", "text": "Marketing makes people aware and interested. Sales closes the deal. Start with positioning: how you are different and better. Choose channels your customers use. Measure conversion rates."},
                        {"type": "list", "items": [
                            "Positioning: unique benefit for a specific customer.",
                            "Channels: social media, email, SEO, ads, referrals.",
                            "Sales funnel: awareness → interest → decision → action.",
                            "Metrics: CAC, conversion rate, LTV, ROI.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about marketing and sales.",
                        "questions": [
                            {"q": "Positioning describes…", "options": ["how your product is different and better", "your logo color", "your office location"], "answer": "how your product is different and better", "explain": "Positioning tells customers why to choose you."},
                            {"q": "A sales funnel moves customers from…", "options": ["awareness to purchase", "random noise to confusion", "nothing"], "answer": "awareness to purchase", "explain": "Funnels guide people from knowing about you to buying from you."},
                        ],
                    },
                },
                {
                    "slug": "operations-and-record-keeping",
                    "title": "Operations and Record Keeping",
                    "order": 5,
                    "minutes": 20,
                    "summary": "Processes, quality, and financial records.",
                    "learn": [
                        {"type": "p", "text": "Operations turn ideas into delivered value. Design repeatable processes, set quality standards, and track performance. Record keeping supports tax compliance and smart decisions."},
                        {"type": "list", "items": [
                            "SOPs: step-by-step instructions for repeat tasks.",
                            "Quality control: checkpoints and standards.",
                            "Financial records: income, expenses, invoices.",
                            "Tools: spreadsheets, accounting software, CRM.",
                        ]},
                        {"type": "activity", "title": "Draft an SOP", "text": "Write a standard operating procedure for your most common daily task at work or in a side project."},
                    ],
                    "check": {
                        "prompt": "Show what you know about operations and record keeping.",
                        "questions": [
                            {"q": "An SOP is…", "options": ["a step-by-step procedure", "a sales pitch", "a tax form"], "answer": "a step-by-step procedure", "explain": "SOPs ensure tasks are done consistently and correctly."},
                            {"q": "Good record keeping helps with…", "options": ["taxes and decisions", "hiding losses", "forgetting customers"], "answer": "taxes and decisions", "explain": "Records prove income and expenses and reveal business trends."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "digital-business-and-strategy",
            "title": "Digital Business and Strategy",
            "summary": "Digital tools, ethics, and strategic planning.",
            "order": 3,
            "lessons": [
                {
                    "slug": "digital-business-tools",
                    "title": "Digital Business Tools",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Websites, e-commerce, automation, and data.",
                    "learn": [
                        {"type": "p", "text": "Digital tools extend reach and efficiency. A professional website builds trust. E-commerce platforms handle sales. Automation and analytics save time and guide decisions."},
                        {"type": "list", "items": [
                            "Website: clear value prop, fast load, mobile-friendly.",
                            "E-commerce: Shopify, WooCommerce, Stripe.",
                            "Automation: email sequences, invoicing, CRM.",
                            "Analytics: track traffic, conversion, and retention.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about digital business tools.",
                        "questions": [
                            {"q": "A key feature of a good business website is…", "options": ["clear value proposition and fast load", "many pop-ups", "no contact info"], "answer": "clear value proposition and fast load", "explain": "Users need to understand what you offer quickly and easily."},
                        ],
                    },
                },
                {
                    "slug": "business-ethics-and-strategy",
                    "title": "Business Ethics and Strategy",
                    "order": 7,
                    "minutes": 20,
                    "summary": "Ethical decisions, competitive advantage, and strategic planning.",
                    "learn": [
                        {"type": "p", "text": "Ethical businesses build lasting trust. Strategy is a plan to achieve goals in a competitive environment. Use SWOT (strengths, weaknesses, opportunities, threats) to assess position and choose actions."},
                        {"type": "list", "items": [
                            "Ethics: transparency, fairness, keeping promises.",
                            "SWOT: internal strengths/weaknesses, external opportunities/threats.",
                            "Competitive advantage: what you do better than rivals.",
                            "Review strategy quarterly and adjust.",
                        ]},
                        {"type": "example", "title": "SWOT example", "text": "Bakery: Strength = custom cakes. Weakness = limited seating. Opportunity = delivery apps. Threat = chain bakery nearby."},
                    ],
                    "check": {
                        "prompt": "Show what you know about business ethics and strategy.",
                        "questions": [
                            {"q": "SWOT analysis stands for…", "options": ["Strengths, Weaknesses, Opportunities, Threats", "Sales, Wages, Overtime, Taxes", "Social, Web, Operations, Technology"], "answer": "Strengths, Weaknesses, Opportunities, Threats", "explain": "SWOT is a framework for strategic assessment."},
                            {"q": "Ethical business practices…", "options": ["build long-term trust", "increase cheating", "reduce profit"], "answer": "build long-term trust", "explain": "Ethics protect reputation and create sustainable success."},
                        ],
                    },
                },
            ],
        },
    ],
}
