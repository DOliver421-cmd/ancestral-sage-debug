"""Student Handbook — Middle School Edition (Grades 6–8, free ebook course).

For students taking real ownership of their learning: study systems, digital
focus, self-advocacy with parents, and planning their own schedule.
"""

HANDBOOK_MIDDLE = {
    "slug": "handbook-middle-school",
    "title": "Student Handbook — Middle School Edition (Grades 6–8)",
    "summary": "Your operating manual for middle school: study systems that actually work, beating distraction, planning your own schedule, and taking ownership of your learning.",
    "description": (
        "The Middle School Student Handbook is a free ebook-style course for grades 6–8. Middle "
        "school is where school stops being done to you and starts being done by you — this "
        "handbook gives you the systems: how to take notes you'll actually use, how to study with "
        "retrieval practice instead of rereading, how to manage screens and focus, how to plan "
        "your own week, and how to speak up when you need help. Short chapters, real techniques, "
        "and a review at the end of each."
    ),
    "subject": "life_skills",
    "subject_label": "Student Handbook",
    "track": "foundations",
    "tracks": ["foundations", "scholar"],
    "grades": ["6", "7", "8"],
    "grade_label": "Grades 6–8",
    "status": "published",
    "audience": "Middle school students learning to run their own education.",
    "est_hours": 3,
    "passing_score": 80,
    "learning_objectives": [
        "Take notes using a method you can actually study from.",
        "Study with retrieval practice and spaced review instead of rereading.",
        "Design a weekly schedule and protect your focus from screens.",
        "Self-advocate: ask specific questions and request help the right way.",
        "Explain how the Academy's mastery system maps onto your goals.",
    ],
    "units": [
        {
            "slug": "handbook-middle-chapters",
            "title": "Chapters",
            "summary": "Five chapters on running your own learning.",
            "order": 1,
            "lessons": [
                {
                    "slug": "owning-your-education",
                    "title": "Chapter 1: You're the Boss Now (Sort Of)",
                    "order": 1,
                    "minutes": 12,
                    "summary": "What changes in middle school — and the deal you make with yourself.",
                    "learn": [
                        {"type": "p", "text": "In elementary school, adults mostly ran your learning. In middle school, the balance shifts: your parents still set the schedule, but the daily work — the reading, the checks, the honest effort — is yours. That's not a burden; it's a promotion. Here's the deal: the Academy gives you full control of your pace, and you agree to actually use it."},
                        {"type": "list", "items": [
                            "The mastery system means no moving on with gaps: 80% on a knowledge check before the next lesson unlocks.",
                            "Failed a check? The lesson shows exactly what to review. Retrying is a feature, not a punishment.",
                            "Your classroom page shows progress bars for every course — that's your dashboard, check it weekly.",
                            "The parent sets the when and where; you own the how well.",
                        ]},
                        {"type": "tip", "text": "Make one agreement with your parent this week: what time school starts, where it happens, and what 'done for the day' means. Write it down. Fewer arguments, more learning."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 1.",
                        "questions": [
                            {"q": "What does the 80% mastery gate guarantee?", "options": ["You don't move on with gaps in understanding", "You're the smartest kid", "Lessons get easier"], "answer": "You don't move on with gaps in understanding", "explain": "Mastery before advancement is the whole design — no sinking foundations."},
                            {"q": "In the Academy, who owns 'how well' the daily work gets done?", "options": ["You do", "Your parent", "The website"], "answer": "You do", "explain": "Parents set schedule and structure; quality of effort is your department."},
                        ],
                    },
                },
                {
                    "slug": "notes-that-work",
                    "title": "Chapter 2: Notes You'll Actually Use",
                    "order": 2,
                    "minutes": 14,
                    "summary": "Note-taking as thinking, not copying.",
                    "learn": [
                        {"type": "p", "text": "Copying every word isn't note-taking — it's transcription, and your brain checks out while your hand keeps moving. Real notes are decisions about what matters. The easiest powerful method: split your page. Main ideas on the left, details and examples on the right, and a 2–3 sentence summary at the bottom in your own words."},
                        {"type": "list", "items": [
                            "Write questions in the margin instead of underlining ('why does the ratio trick work?') — questions are study material.",
                            "Use your own words. If you can't translate it, you didn't understand it — flag it to ask about.",
                            "Symbols beat sentences: arrows for cause-effect, stars for must-know, '?' for confused.",
                            "Review notes within 24 hours for 5 minutes. That tiny review doubles what sticks.",
                        ]},
                        {"type": "tip", "text": "In Academy lessons, the learn blocks are already organized — your job is the margin questions and the summary. Those two moves are what turn reading into learning."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 2.",
                        "questions": [
                            {"q": "Why is copying every word bad note-taking?", "options": ["Your brain checks out when your hand transcribes", "It wastes ink", "It's actually the best method"], "answer": "Your brain checks out when your hand transcribes", "explain": "Notes should be decisions about what matters, not transcription."},
                            {"q": "The best thing to write in your margins is…", "options": ["questions", "nothing", "the date"], "answer": "questions", "explain": "Margin questions are ready-made study material and confusion detectors."},
                        ],
                    },
                },
                {
                    "slug": "study-smart-not-long",
                    "title": "Chapter 3: Study Smart, Not Long",
                    "order": 3,
                    "minutes": 14,
                    "summary": "Retrieval practice and spacing — the two most proven techniques in learning science.",
                    "learn": [
                        {"type": "p", "text": "Rereading feels productive and mostly isn't — it builds familiarity, not memory. The two techniques with the strongest evidence in learning science are retrieval practice (testing yourself) and spacing (spreading review over days). Good news: your Academy's knowledge checks ARE retrieval practice, built in."},
                        {"type": "list", "items": [
                            "Retrieval: close the lesson and write what you remember. What you can't recall is exactly what to restudy.",
                            "Spacing: review today's lesson for 5 minutes tomorrow, 5 minutes in three days, 5 minutes next week.",
                            "Interleave: mix problem types in one session instead of blocking one type — harder, but far stickier.",
                            "Sleep is study time: memory consolidation happens overnight. Cramming trades tomorrow's learning for tonight's grade.",
                        ]},
                        {"type": "example", "title": "Do it now", "text": "Close this lesson. On paper, list the four study techniques above from memory. Check. Whatever you missed — that's your spaced-review homework for tomorrow."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 3.",
                        "questions": [
                            {"q": "Why is rereading a weak study method?", "options": ["It builds familiarity, not memory", "It takes too much paper", "It's only for little kids"], "answer": "It builds familiarity, not memory", "explain": "Recognizing text isn't the same as being able to recall and use it."},
                            {"q": "Retrieval practice means…", "options": ["testing yourself from memory, then checking what you missed", "rereading your notes twice", "highlighting everything important"], "answer": "testing yourself from memory, then checking what you missed", "explain": "Pulling information OUT of your head is what strengthens the memory."},
                        ],
                    },
                },
                {
                    "slug": "focus-and-screens",
                    "title": "Chapter 4: Focus in a Distracted World",
                    "order": 4,
                    "minutes": 14,
                    "summary": "Designing your environment so attention is the default.",
                    "learn": [
                        {"type": "p", "text": "You don't have a focus problem; you have an environment problem. Willpower is a terrible strategy against apps engineered by teams of experts to capture attention. Change the environment instead: make focus easy and distraction annoying."},
                        {"type": "list", "items": [
                            "Phone in another room during lessons. Not face-down — another room. Distance beats discipline.",
                            "One tab rule: the lesson, nothing else. Every extra tab is a toll booth on your attention.",
                            "Work in blocks: 25–30 minutes on, 5–10 off. Set a timer; breaks are scheduled, not stolen.",
                            "Tell your brain what 'done' means: finish the lesson and pass the check, then screens are yours.",
                        ]},
                        {"type": "tip", "text": "Track your focus for three days: every time you drift, make a tally mark on paper. Most students find their drift count drops in half just from noticing — that's the point."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 4.",
                        "questions": [
                            {"q": "The best defense against phone distraction is…", "options": ["physical distance — another room", "willpower", "face-down on the desk"], "answer": "physical distance — another room", "explain": "Environment design beats willpower; distance removes the choice."},
                            {"q": "A good focused work block is…", "options": ["25–30 minutes on, 5–10 off, with a timer", "as long as you can stand", "whenever the mood hits"], "answer": "25–30 minutes on, 5–10 off, with a timer", "explain": "Scheduled blocks with scheduled breaks sustain attention across a whole school day."},
                        ],
                    },
                },
                {
                    "slug": "speak-up-speak-specific",
                    "title": "Chapter 5: Speak Up, Speak Specific",
                    "order": 5,
                    "minutes": 12,
                    "summary": "Self-advocacy: getting unstuck faster with better questions.",
                    "learn": [
                        {"type": "p", "text": "The strongest students aren't the ones who never get stuck — they're the ones who get unstuck fast. That's a skill called self-advocacy, and it starts with a specific question. 'I don't get it' gives a helper nothing to work with. 'I understand steps 1 and 2 but not why we divide here' gets an answer in one minute."},
                        {"type": "list", "items": [
                            "Name what you DO understand first, then the exact stuck point.",
                            "Use your Coach panel in lessons for concepts — it explains differently every time and never hands over answers.",
                            "Ask your parent for a weekly 15-minute review: what went well, what got stuck, what changes next week.",
                            "When a lesson check keeps beating you, retake it after reviewing — and if it's still stuck after two honest tries, escalate. That's not weakness; that's process.",
                        ]},
                        {"type": "tip", "text": "Keep a 'stuck list' — one line per confusing idea. Bring it to your weekly review. Problems that get named get solved; problems that stay vague stay stuck."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 5.",
                        "questions": [
                            {"q": "A good help-seeking question includes…", "options": ["what you understand plus the exact stuck point", "as few words as possible", "a complaint about the lesson"], "answer": "what you understand plus the exact stuck point", "explain": "Specific questions get specific answers — that's self-advocacy."},
                            {"q": "If a check beats you twice after honest review, you should…", "options": ["escalate — bring the stuck list to your parent or Coach", "quit the course", "guess until it passes"], "answer": "escalate — bring the stuck list to your parent or Coach", "explain": "Two honest tries then escalate is a process, not a failure."},
                        ],
                    },
                },
            ],
        },
    ],
}
