"""Leadership Foundations (full published course)."""

LEADERSHIP_FOUNDATIONS = {
    "slug": "leadership-foundations",
    "title": "Leadership",
    "summary": "Leadership fundamentals, communication, decision making, problem solving, conflict resolution, teamwork, and strategic thinking.",
    "description": (
        "Leadership Foundations teaches the core skills of leading people and projects. "
        "Topics include communication, decision making, accountability, problem solving, "
        "conflict resolution, teamwork, organizing, project planning, community leadership, "
        "ethical leadership, strategic thinking, responsibility, evaluating information, "
        "team management, and leadership under pressure."
    ),
    "subject": "leadership",
    "subject_label": "Leadership",
    "track": "leadership",
    "tracks": ["leadership"],
    "grades": ["adult"],
    "grade_label": "Adult",
    "status": "published",
    "audience": "Adult learners preparing for leadership roles at work and in community.",
    "est_hours": 32,
    "passing_score": 80,
    "learning_objectives": [
        "Apply core leadership principles and styles.",
        "Communicate vision, feedback, and expectations clearly.",
        "Make and implement effective decisions.",
        "Solve problems systematically under pressure.",
        "Resolve conflicts constructively.",
        "Plan and lead projects from start to finish.",
        "Evaluate information and manage teams ethically.",
    ],
    "units": [
        {
            "slug": "leadership-fundamentals",
            "title": "Leadership Fundamentals",
            "summary": "Styles, communication, and accountability.",
            "order": 1,
            "lessons": [
                {
                    "slug": "leadership-styles-and-ethics",
                    "title": "Leadership Styles and Ethics",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Identify styles and apply ethical principles.",
                    "learn": [
                        {"type": "p", "text": "Leadership styles include autocratic, democratic, transformational, and servant. Effective leaders adapt to context. Ethical leadership means doing the right thing even when it is hard — honesty, fairness, and respect for people."},
                        {"type": "list", "items": [
                            "Autocratic: leader decides alone — fast but may demotivate.",
                            "Democratic: team input — buy-in is high, slower.",
                            "Transformational: inspire change and growth.",
                            "Servant: put people first, serve the team.",
                        ]},
                        {"type": "example", "title": "Ethical dilemma", "text": "A leader discovers a team member cut a safety corner. Ethical action: correct the behavior, document it, retrain, and protect workers."},
                    ],
                    "check": {
                        "prompt": "Show what you know about leadership styles and ethics.",
                        "questions": [
                            {"q": "A democratic leader…", "options": ["includes the team in decisions", "decides alone", "avoids leadership"], "answer": "includes the team in decisions", "explain": "Democratic leaders seek input and build consensus."},
                            {"q": "Ethical leadership requires…", "options": ["honesty and fairness", "breaking rules", "ignoring safety"], "answer": "honesty and fairness", "explain": "Ethical leaders do the right thing, especially when difficult."},
                        ],
                    },
                },
                {
                    "slug": "communication-and-feedback",
                    "title": "Communication and Feedback",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Clear expectations, active listening, and constructive feedback.",
                    "learn": [
                        {"type": "p", "text": "Clear communication prevents mistakes and builds trust. State expectations specifically. Use active listening: paraphrase, ask questions, avoid interrupting. Give feedback that is specific, behavior-focused, and actionable."},
                        {"type": "list", "items": [
                            "Be specific: 'Submit reports by 5 PM Friday' not 'soon'.",
                            "Feedback: 'When X happened, I saw Y impact. Try Z next time.'",
                            "Listen first: understand before responding.",
                            "Nonverbal: eye contact, posture, and tone reinforce words.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about communication and feedback.",
                        "questions": [
                            {"q": "Effective feedback focuses on…", "options": ["specific behavior and impact", "personality", "the past only"], "answer": "specific behavior and impact", "explain": "Behavior-focused feedback helps people improve."},
                            {"q": "Active listening means…", "options": ["focusing fully on the speaker", "planning your reply", "interrupting often"], "answer": "focusing fully on the speaker", "explain": "Active listening shows respect and prevents misunderstandings."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "problem-solving-and-team-management",
            "title": "Problem Solving and Team Management",
            "summary": "Decision making, conflict resolution, and project planning.",
            "order": 2,
            "lessons": [
                {
                    "slug": "decision-making-and-problem-solving",
                    "title": "Decision Making and Problem Solving",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Systematic approaches and creative solutions.",
                    "learn": [
                        {"type": "p", "text": "Problem solving: define the problem, gather data, generate options, evaluate, implement, and review. Decision making uses the same steps but may be faster. Use tools such as mind maps and decision matrices."},
                        {"type": "list", "items": [
                            "Define the real problem, not the symptom.",
                            "Brainstorm without criticism.",
                            "Evaluate risks and resources.",
                            "Pilot small before full rollout.",
                        ]},
                        {"type": "example", "title": "Root cause analysis", "text": "Symptom: missed deadlines. Root cause: unclear priorities. Fix: weekly priority meeting with written assignments."},
                    ],
                    "check": {
                        "prompt": "Show what you know about decision making and problem solving.",
                        "questions": [
                            {"q": "The first step in problem solving is to…", "options": ["define the problem", "pick a solution", "blame someone"], "answer": "define the problem", "explain": "You cannot solve a problem you have not clearly defined."},
                            {"q": "Brainstorming works best when you…", "options": ["judge ideas later", "judge immediately", "ignore all ideas"], "answer": "judge ideas later", "explain": "Judgment during brainstorming kills creativity."},
                        ],
                    },
                },
                {
                    "slug": "conflict-resolution-and-team-management",
                    "title": "Conflict Resolution and Team Management",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Mediate disputes, build trust, and delegate effectively.",
                    "learn": [
                        {"type": "p", "text": "Conflict is normal. Resolve it by focusing on interests, not positions. Listen to each side, find common ground, and agree on next steps. Teams succeed when members trust each other and have clear roles."},
                        {"type": "list", "items": [
                            "Interests: what people need. Positions: what they say they want.",
                            "Delegate: match tasks to strengths and development goals.",
                            "Trust: consistency, competence, and care.",
                            "Review: regular check-ins and course corrections.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about conflict resolution and team management.",
                        "questions": [
                            {"q": "Resolving conflict by focusing on interests means…", "options": ["understanding what each side truly needs", "arguing harder", "ignoring the problem"], "answer": "understanding what each side truly needs", "explain": "Interests reveal underlying needs behind stated positions."},
                            {"q": "Effective delegation…", "options": ["matches tasks to strengths", "does everything yourself", "gives all work to one person"], "answer": "matches tasks to strengths", "explain": "Delegating to the right people builds capability and trust."},
                        ],
                    },
                },
                {
                    "slug": "project-planning-and-community-leadership",
                    "title": "Project Planning and Community Leadership",
                    "order": 5,
                    "minutes": 20,
                    "summary": "Plan, execute, and reflect on projects that serve communities.",
                    "learn": [
                        {"type": "p", "text": "A project plan has a goal, timeline, resources, roles, and success measures. Community leadership means mobilizing people around shared goals, listening to stakeholders, and celebrating progress."},
                        {"type": "list", "items": [
                            "Goal: clear and measurable.",
                            "Timeline: milestones and deadlines.",
                            "Resources: people, money, materials.",
                            "Success measure: how you know the project worked.",
                        ]},
                        {"type": "activity", "title": "Project plan", "text": "Plan a small community project (food drive, park cleanup, tutoring). Write goal, timeline, resources, roles, and success measure."},
                    ],
                    "check": {
                        "prompt": "Show what you know about project planning and community leadership.",
                        "questions": [
                            {"q": "A project success measure tells you…", "options": ["whether the goal was achieved", "the team's favorite color", "the weather"], "answer": "whether the goal was achieved", "explain": "Success measures are concrete ways to evaluate outcomes."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "strategic-and-pressure-leadership",
            "title": "Strategic and Pressure Leadership",
            "summary": "Strategic thinking, evaluating information, and leading under pressure.",
            "order": 3,
            "lessons": [
                {
                    "slug": "strategic-thinking-and-evaluation",
                    "title": "Strategic Thinking and Evaluating Information",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Think long-term and evaluate sources critically.",
                    "learn": [
                        {"type": "p", "text": "Strategic thinking connects today's actions to tomorrow's results. Ask: What is the goal? What are the trends? What resources do we have? Evaluate information by checking source, evidence, and bias."},
                        {"type": "list", "items": [
                            "Strategic thinking: long-term, systems view.",
                            "Evaluate: authority, accuracy, currency, bias.",
                            "Use data and evidence, not just opinion.",
                            "Scenario planning: prepare for multiple futures.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about strategic thinking and evaluation.",
                        "questions": [
                            {"q": "Strategic thinking focuses on…", "options": ["long-term goals and systems", "only today's tasks", "random ideas"], "answer": "long-term goals and systems", "explain": "Strategic thinking connects actions to future outcomes."},
                            {"q": "When evaluating information, you should check…", "options": ["source, evidence, and bias", "font and colors", "word count"], "answer": "source, evidence, and bias", "explain": "Critical evaluation examines credibility, facts, and perspective."},
                        ],
                    },
                },
                {
                    "slug": "leadership-under-pressure",
                    "title": "Leadership Under Pressure",
                    "order": 7,
                    "minutes": 18,
                    "summary": "Stay calm, prioritize, and make sound decisions during crises.",
                    "learn": [
                        {"type": "p", "text": "Pressure reveals character. Stay calm by breathing, focusing on facts, and prioritizing safety and critical tasks. Communicate clearly. After the crisis, review what worked and what did not."},
                        {"type": "list", "items": [
                            "Pause: take a breath before reacting.",
                            "Prioritize: safety first, then critical tasks.",
                            "Communicate: clear, short updates.",
                            "Review: after-action lessons build future resilience.",
                        ]},
                        {"type": "example", "title": "Crisis example", "text": "Server outage. Stay calm: check logs, prioritize restore, communicate timeline, and review prevention steps after."},
                    ],
                    "check": {
                        "prompt": "Show what you know about leadership under pressure.",
                        "questions": [
                            {"q": "In a crisis, the first priority should be…", "options": ["safety", "blame", "social media"], "answer": "safety", "explain": "Safety of people comes before all other concerns."},
                            {"q": "After-action review means…", "options": ["reviewing what happened to improve next time", "punishing the team", "forgetting the event"], "answer": "reviewing what happened to improve next time", "explain": "After-action reviews turn experience into learning."},
                        ],
                    },
                },
            ],
        },
    ],
}
