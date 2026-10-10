"""Parent Handbook — Managing Your Child's Education (published).

The handbook that goes with the four student handbooks: it is for the adult
running the home education program. It covers what Florida law actually
requires of the parent (s. 1002.41, F.S.), how to start, how to keep the
records the statute asks for, how to judge mastery, how to plan high school,
how to run the annual evaluation, how to do it alongside work and multiple
children — and how to do all of it at zero cost.

Placed in the catalog like the student handbooks, free like everything else,
and scoped so every family can enrol it whatever grade or track their
students are on.
"""

PARENT_HANDBOOK = {
    "slug": "parent-handbook",
    "title": "Parent Handbook — Managing Your Child's Education",
    "summary": "The parent's operating manual: what Florida requires of you, how to start, how to keep records, how to judge mastery, how to plan high school, and how to do it all for free.",
    "description": (
        "You are the school. Under Florida law the parent — not a provider, not a platform — is the "
        "home education program administrator, and this handbook is written for that person. It walks "
        "through starting a program (the Notice of Intent, grade placement, and the Academy's enrolment "
        "flow), designing a year without a required number of days or hours, keeping the two records "
        "the statute actually asks you to keep (a contemporaneous activity log and work samples), judging "
        "mastery without burning your child out, planning and documenting high school credits and "
        "transcripts, running the annual evaluation, and doing all of it while working, while teaching "
        "more than one child, and at zero cost. Each chapter ends with a short check, the same as the "
        "student courses, so you can prove to yourself that you have the operating picture."
    ),
    "subject": "life_skills",
    "subject_label": "Parent Handbook",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar", "adult_ed", "life_skills", "leadership", "career", "entrepreneurship"],
    "grades": ["K", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "adult"],
    "grade_label": "Parents and guardians",
    "status": "published",
    "audience": "Any parent or guardian running a home education program, at any grade, in any state.",
    "est_hours": 4,
    "passing_score": 80,
    "learning_objectives": [
        "State what Florida law requires of the parent, and what it leaves to you.",
        "File a Notice of Intent and enrol students in the right grade and track.",
        "Keep the two portfolio records the statute names: an activity log and work samples.",
        "Design a school year and a weekly schedule that fits your family.",
        "Judge mastery fairly and decide when to move on or go back.",
        "Plan, document, and issue a high school transcript.",
        "Prepare for the annual evaluation and use the Academy's pre-audit.",
        "Run a multi-child, working-parent household at zero cost.",
    ],
    "units": [
        {
            "slug": "parent-handbook-chapters",
            "title": "Chapters",
            "summary": "Ten chapters for the parent running the program.",
            "order": 1,
            "lessons": [
                {
                    "slug": "you-are-the-school",
                    "title": "Chapter 1: You Are the School",
                    "order": 1,
                    "minutes": 14,
                    "summary": "What the law gives you, and what it asks of you.",
                    "learn": [
                        {"type": "p", "text": "In Florida, home education is defined by section 1002.41 of the statutes. The single most important thing in it is this: the PARENT is the home education program administrator. That means the responsibility for your child's education — choosing what is taught, keeping the records, arranging the annual evaluation, and issuing the final diploma — sits with you. It is not delegated to a curriculum provider, a website, or a tutor. That is also why the freedom is real: no district, no school board, and no platform gets to tell you how to run it."},
                        {"type": "list", "items": [
                            "What the statute asks of you: a written Notice of Intent, a kept portfolio, and an annual evaluation.",
                            "What the statute does NOT set: a required number of days, hours, subjects, or a specific curriculum.",
                            "What stays yours: the pace, the sequence, the method, and the record.",
                        ]},
                        {"type": "example", "title": "What this means in practice", "text": "A platform can teach, track, and generate documents. It cannot file your notice, sign your evaluation, or issue your child's diploma. Those are yours — which is why this handbook walks you through all three."},
                        {"type": "tip", "text": "Using the Academy does not enroll you anywhere and does not notify anyone. The Academy is your tool; the program is yours. Nothing is shared with a district unless you send it."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the roles.",
                        "questions": [
                            {"q": "Under Florida law, who is the home education program administrator?", "options": ["The parent", "The curriculum provider", "The school district"], "answer": "The parent", "explain": "s. 1002.41 puts the responsibility on the parent, which is also the source of the freedom."},
                            {"q": "Florida home education law requires which of these?", "options": ["A notice of intent, a portfolio, and an annual evaluation", "Exactly 180 days of instruction", "State-approved curriculum"], "answer": "A notice of intent, a portfolio, and an annual evaluation", "explain": "Those three are statutory. Days, hours, and curriculum choice are not."},
                            {"q": "Which of these is NOT set by the statute?", "options": ["A required number of instructional days", "Maintaining a portfolio", "An annual evaluation"], "answer": "A required number of instructional days", "explain": "Florida home education law does not mandate a day count; some other states do, so check yours."},
                        ],
                    },
                },
                {
                    "slug": "getting-started",
                    "title": "Chapter 2: Getting Started in a Week",
                    "order": 2,
                    "minutes": 14,
                    "summary": "Notice, grade placement, enrolment, and a first week that works.",
                    "learn": [
                        {"type": "p", "text": "You can be legitimately operating within a week. File the Notice of Intent with your county school district superintendent — Florida asks for it within 30 days of starting — then place your child, enrol them, and begin. The Academy's compliance page generates the letter for your specific district; you print, sign, and send it. Generating it is not filing it, and filing it is your step."},
                        {"type": "list", "items": [
                            "Day 1: create your parent account. You are the account holder; your child does not need one.",
                            "Day 2: generate the Notice of Intent on the Academy compliance page, fill in your child's date of birth and address, print, sign, and send it to your district.",
                            "Day 3: add each student from the family dashboard, choosing grade and learning track.",
                            "Day 4–5: open the curriculum, enrol, and complete the first lesson together so they see how mastery works.",
                            "Week 1: keep the log from the very first day — see Chapter 4.",
                        ]},
                        {"type": "tip", "text": "Grade placement is yours to choose, and you can move a student at any time from the family dashboard. Match where they are actually working, not where their age says."},
                        {"type": "example", "title": "Choosing a track", "text": "Foundations for the standard academic core; Builder for trades and applied skills; Scholar for advanced academic work; Artist for creative tracks; and the adult, career, leadership, life-skills, and entrepreneurship tracks for older students. A student can hold more than one through their enrolled courses."},
                    ],
                    "check": {
                        "prompt": "Check your start-up sequence.",
                        "questions": [
                            {"q": "The Notice of Intent is sent by you to…", "options": ["Your county school district superintendent", "The state legislature", "The platform"], "answer": "Your county school district superintendent", "explain": "It goes to the district; Florida asks for it within 30 days of beginning."},
                            {"q": "Who holds the account on the Academy?", "options": ["The parent", "The child", "Nobody — it is public"], "answer": "The parent", "explain": "Adult accounts only; your children have no login, which also protects their data."},
                            {"q": "Grade placement is decided by…", "options": ["You, based on where the student is working", "Their age", "The district"], "answer": "You, based on where the student is working", "explain": "Placement is the parent's call and can be changed at any time."},
                        ],
                    },
                },
                {
                    "slug": "designing-the-year",
                    "title": "Chapter 3: Designing Your Year",
                    "order": 3,
                    "minutes": 14,
                    "summary": "A scope, a sequence, and a schedule that survives real life.",
                    "learn": [
                        {"type": "p", "text": "Most home education burnout comes from copying a school day instead of designing one. The Academy's courses are already sequenced — units in order, lessons unlocking at 80% — so your planning work is about pace, not sequence. Decide how many lessons per school day, block the week, and protect one review day."},
                        {"type": "list", "items": [
                            "Pace: a course of 40 lessons at 2 per day finishes a year; at 3 it finishes in about 100 days.",
                            "Blocks: 60–90 minutes of core work before the energy dips; applied and creative work after.",
                            "Review: one day a week with no new material — retake checks, fix gaps, and do a project.",
                            "Breaks: plan them in. A family that rests finishes more than one that grinds.",
                        ]},
                        {"type": "example", "title": "A working week", "text": "Mon–Thu: new lessons. Fri: review, retakes, and the family-history project. Sat/Sun: life is the classroom — errands, museum, cooking. This is the single most common structure among experienced home educators."},
                        {"type": "tip", "text": "Record the plan somewhere you will actually look: three lines in a notebook beats a beautiful spreadsheet you abandon in October."},
                    ],
                    "check": {
                        "prompt": "Check your planning approach.",
                        "questions": [
                            {"q": "A course with 40 lessons at 2 lessons a day takes roughly…", "options": ["A school year", "A month", "Two weeks"], "answer": "A school year", "explain": "Pace arithmetic is the parent's main planning lever."},
                            {"q": "What should a review day contain?", "options": ["Retakes, gap-fixing, and a project", "New material only", "Nothing at all"], "answer": "Retakes, gap-fixing, and a project", "explain": "Review days are where mastery gets consolidated and gaps get closed."},
                            {"q": "The best plan is the one that…", "options": ["You will actually follow", "Is the most detailed", "Matches a school timetable"], "answer": "You will actually follow", "explain": "Adherence beats elegance every time."},
                        ],
                    },
                },
                {
                    "slug": "records-that-count",
                    "title": "Chapter 4: The Records That Actually Count",
                    "order": 4,
                    "minutes": 16,
                    "summary": "Two records satisfy the statute: the log and the samples.",
                    "learn": [
                        {"type": "p", "text": "Florida names two things a home education portfolio must contain: a log of educational activity made as it happens, with titles of reading materials, and work samples — writings, worksheets, and completed work. That is the statutory core. Everything else you keep is extra, and most of it can be generated from the Academy for you."},
                        {"type": "list", "items": [
                            "Contemporaneous activity log: WHAT you studied, WHEN, and the title of books/materials used. One line per session.",
                            "Work samples: the actual work — a composition, a completed knowledge check, a project artifact.",
                            "Supplementary (recommended): progress reports, reading lists, and a transcript for high school.",
                        ]},
                        {"type": "example", "text": "A log line that satisfies the statute: '2026-10-14 — Math: Linear Functions, Chapter 4, lessons 4.2–4.3 (patterns and slope), 45 min; ELA: read 'Narrative of the Life of Frederick Douglass', ch. 5–6, 30 min.' Date, subject, title, material, duration.", "title": "The log line that satisfies the statute"},
                        {"type": "tip", "text": "The Academy already stores dates, courses, lesson titles, scores, and best results per student. The student records page compiles it — your job is to keep the reading-material titles alongside it, which the log is for. Print it termly and file it; a portfolio kept as you go is the cheapest compliance there is."},
                    ],
                    "check": {
                        "prompt": "Check your records knowledge.",
                        "questions": [
                            {"q": "Florida's portfolio requirements include…", "options": ["An activity log with reading titles, and work samples", "Daily video evidence", "A signed textbook list"], "answer": "An activity log with reading titles, and work samples", "explain": "Those are the two things the statute names."},
                            {"q": "A contemporaneous log is one that is…", "options": ["Written as the activity happens", "Reconstructed at year end", "Written by the student only"], "answer": "Written as the activity happens", "explain": "'Contemporaneous' means made at the time — which is why you start on day one."},
                            {"q": "A work sample is…", "options": ["Actual completed work such as an essay or a finished check", "A list of textbook chapters", "A photo of the student"], "answer": "Actual completed work such as an essay or a finished check", "explain": "The artifact itself is the evidence."},
                        ],
                    },
                },
                {
                    "slug": "mastery-and-assessment",
                    "title": "Chapter 5: Judging Mastery Without Burning Them Out",
                    "order": 5,
                    "minutes": 15,
                    "summary": "The 80% rule, retakes, and the three decisions that matter.",
                    "learn": [
                        {"type": "p", "text": "The Academy's model is 80% on a knowledge check: below that, the lesson shows what to review and the student retries immediately. That is not arbitrary — it is the difference between recognising material and owning it. Your job is not to raise the bar to prove rigour, nor to lower it to avoid tears. Your job is to make one of three decisions when a student lands below 80."},
                        {"type": "list", "items": [
                            "Decision 1 — Retry now: they were careless or rushed. Read the explanations and try again.",
                            "Decision 2 — Go back one step: the prerequisite is shaky. Review the previous lesson first.",
                            "Decision 3 — Change the approach: if a concept has not landed after two honest tries, teach it differently — a hands-on version, a video, a real-world problem.",
                        ]},
                        {"type": "tip", "text": "Two retries is a signal, not a failure. A concept that has not landed after two honest attempts usually needs a different explanation, not more repetition."},
                        {"type": "example", "title": "The Coach", "text": "Every lesson has a Coach that knows which lesson the student is on. If it explains one way and the student still does not get it, ask it for 'a different example' — that is exactly what it is for, and it costs nothing beyond your own AI key."},
                    ],
                    "check": {
                        "prompt": "Check your mastery judgement.",
                        "questions": [
                            {"q": "The Academy's mastery threshold is…", "options": ["80%", "100%", "70%"], "answer": "80%", "explain": "80% on the knowledge check advances the student."},
                            {"q": "Two failed retries on the same concept usually means…", "options": ["The concept needs a different explanation", "The student should move on anyway", "The lesson is too easy"], "answer": "The concept needs a different explanation", "explain": "Repetition of the same explanation rarely fixes a misunderstanding."},
                            {"q": "Which is a reasonable response to a student just below 80?", "options": ["Review the explanations and retry", "Skip the lesson permanently", "Lower the passing score for everyone"], "answer": "Review the explanations and retry", "explain": "Immediate retry after feedback is where most of the learning happens."},
                        ],
                    },
                },
                {
                    "slug": "high-school",
                    "title": "Chapter 6: High School, Credits, and the Transcript",
                    "order": 6,
                    "minutes": 16,
                    "summary": "Turn four years of lessons into a document colleges accept.",
                    "learn": [
                        {"type": "p", "text": "A parent-issued transcript is accepted by colleges, employers, and scholarship programs when it is consistent and documented. One credit conventionally equals one year of a one-period course, and Florida's public university recommendations ask for four English, four mathematics (including Algebra I and Geometry), three science, three social studies, two sequential language, and electives. The Academy"
                        "does the mechanical part, not the judgement: the records page keeps completed"
                        "coursework with scores, and the compliance page generates a transcript document with a"
                        "letter grade and an unweighted GPA on a stated scale. YOU decide what counts as a credit"
                        "and which requirements each course satisfies — and you sign it."},
                        {"type": "list", "items": [
                            "Credits: record each completed course with its grade and the year it was completed.",
                            "Weighted and unweighted GPA: the Academy records best scores, so your calculation is straightforward and honest.",
                            "Keep the evidence: a submitted project in the portfolio is a stronger artifact than a grade alone.",
                            "Bright Futures: awarded on documented coursework — another reason the log from Chapter 4 matters.",
                        ]},
                        {"type": "tip", "text": "Do not wait until senior year. Keep the transcript current from grade 9; a page you have maintained for four years is trustworthy, and a rushed one is not. The transcript's GPA is calculated from your student's real mastery scores on a stated scale (A 90-100 = 4.0, B 80-89 = 3.0, C 70-79 = 2.0), and the document prints that scale so a reader can check the arithmetic."},
                        {"type": "example", "title": "What the transcript is", "text": "It is a parent-issued record of coursework, not a state-issued diploma. Say so plainly. That is normal, expected, and correct for home education — and it is why the disclaimer sits on the document itself."},
                    ],
                    "check": {
                        "prompt": "Check your high school knowledge.",
                        "questions": [
                            {"q": "A parent-issued transcript is…", "options": ["A document you produce, accepted when consistent", "A state diploma", "Invalid for college"], "answer": "A document you produce, accepted when consistent", "explain": "Home education transcripts are parent-issued and widely accepted."},
                            {"q": "Florida university recommendations generally include which mathematics?", "options": ["Four years including Algebra I and Geometry", "Two years of any math", "Statistics only"], "answer": "Four years including Algebra I and Geometry", "explain": "Check current requirements with the institution you are targeting."},
                            {"q": "You should start maintaining the transcript…", "options": ["From grade 9", "The summer before senior year", "After graduation"], "answer": "From grade 9", "explain": "A maintained document is credible; a reconstructed one is not."},
                        ],
                    },
                },
                {
                    "slug": "annual-evaluation",
                    "title": "Chapter 7: The Annual Evaluation",
                    "order": 7,
                    "minutes": 13,
                    "summary": "Choose an evaluator, prepare the portfolio, and use the pre-audit.",
                    "learn": [
                        {"type": "p", "text": "Florida requires an annual evaluation — a review of your child's progress, normally by a certified teacher you select and pay privately. Parents commonly spend $45–$100 per student per year for it. The preparation is what takes your time, and the Academy removes most of it: run a portfolio pre-audit first, then generate the annual evaluation packet, then bring it to your evaluator."},
                        {"type": "list", "items": [
                            "Select a Florida-certified teacher who understands home education — ask other home educators who they use.",
                            "Prepare: activity log, work samples, progress report, and any transcript entries.",
                            "Use the pre-audit: it flags gaps in core subject coverage before a stranger reviews it.",
                            "Meetings run five minutes when the file is organised; bring a copy and keep the original.",
                        ]},
                        {"type": "tip", "text": "The evaluation packet and the pre-audit live on the Academy compliance page, generated from your student's real records — not from anything you type twice."},
                    ],
                    "check": {
                        "prompt": "Check your evaluation knowledge.",
                        "questions": [
                            {"q": "Florida's annual evaluation is normally done by…", "options": ["A certified teacher you select", "A district employee", "Nobody"], "answer": "A certified teacher you select", "explain": "The parent chooses the evaluator."},
                            {"q": "Before meeting an evaluator you should…", "options": ["Run the portfolio pre-audit and fix any gaps", "Print nothing", "Wait for their opinion"], "answer": "Run the portfolio pre-audit and fix any gaps", "explain": "Preparation is what shortens the meeting and improves its outcome."},
                        ],
                    },
                },
                {
                    "slug": "the-real-life-chapter",
                    "title": "Chapter 8: Real Life — Work, Several Children, and Hard Days",
                    "order": 8,
                    "minutes": 14,
                    "summary": "The chapter most handbooks skip.",
                    "learn": [
                        {"type": "p", "text": "Home education runs inside a family, not a classroom. That is its advantage and its difficulty: schedules break, a toddler naps over a lesson, a parent works shifts. Design for interruption rather than against it. Independent tracks mean an older student can work while you attend to a younger one, and projects run in the background for weeks."},
                        {"type": "list", "items": [
                            "Run an independent block: the student does lesson work alone; you check in, not sit down.",
                            "Combine subjects: one family-history project covers social studies, writing, and oral history at once.",
                            "Two adults, one curriculum: a co-op, a grandparent, or a neighbour can cover a subject weekly.",
                            "Protect one protected hour: short and reliable beats long and aspirational.",
                        ]},
                        {"type": "tip", "text": "A short day that happens every day beats a perfect day that happens twice a month. Consistency is the entire trick."},
                    ],
                    "check": {
                        "prompt": "Check your real-life planning.",
                        "questions": [
                            {"q": "An independent block means…", "options": ["The student works lesson material alone while you check in", "No parent involvement", "Only independent projects"], "answer": "The student works lesson material alone while you check in", "explain": "It is what makes one adult able to run several students."},
                            {"q": "Consistency beats…", "options": ["Occasional long days", "Detailed plans", "New curriculum"], "answer": "Occasional long days", "explain": "A short daily habit outperforms sporadic marathon sessions."},
                        ],
                    },
                },
                {
                    "slug": "free-and-open",
                    "title": "Chapter 9: Doing It at Zero Cost",
                    "order": 9,
                    "minutes": 12,
                    "summary": "The library, the park, the kitchen, and the internet.",
                    "learn": [
                        {"type": "p", "text": "The commercial home education market runs on the assumption that a family must spend hundreds or thousands a year. Most of it is unnecessary. The Academy's curriculum, records, transcripts, compliance documents, projects, and portfolio are free for every registered family, and the best supplementary resources in the world are also free."},
                        {"type": "list", "items": [
                            "Library: interlibrary loans supply the reading lists the log asks you to title.",
                            "Public domain literature: Douglass, Wells, Césaire, Orwell, and most of the canon, free and legally shareable.",
                            "Kitchen and yard: measurement, chemistry, botany, ecology, and cooking — the applied sciences.",
                            "Museums, National Park Service, NASA, and public broadcasters: free curriculum-grade material.",
                        ]},
                        {"type": "tip", "text": "The Academy credits 17 creator resources on every course page. Those are their channels, free to their audiences, credited because they are not ours."},
                    ],
                    "check": {
                        "prompt": "Check your resource knowledge.",
                        "questions": [
                            {"q": "The Academy's curriculum, records, and compliance documents are…", "options": ["Free to every registered family", "Paid per child", "Paid per course"], "answer": "Free to every registered family", "explain": "There is no paywall inside the Academy; the rest of the site keeps its own tiers."},
                            {"q": "A good free source for the reading titles the log asks you to record is…", "options": ["The public library", "A paid curriculum publisher", "A private tutor"], "answer": "The public library", "explain": "Libraries supply reading lists, and interlibrary loan gets most books."},
                        ],
                    },
                },
                {
                    "slug": "your-first-term",
                    "title": "Chapter 10: Your First Term, in Order",
                    "order": 10,
                    "minutes": 12,
                    "summary": "The whole handbook as a checklist.",
                    "learn": [
                        {"type": "p", "text": "If you do nothing else, do this: notice filed, students enrolled, log started on day one, one project underway, and records printed termly. Everything else in this handbook is refinement."},
                        {"type": "list", "items": [
                            "Week 1: file the Notice of Intent; add students with grade and track.",
                            "Week 1: start the log — one line per session from the first lesson.",
                            "Week 2: begin a family-history project; it runs in the background all term.",
                            "Monthly: review progress on the family dashboard; move grade or track if needed.",
                            "Termly: print the student records page and file it with your saved work samples.",
                            "Annual: run the pre-audit, generate the evaluation packet, meet your evaluator.",
                        ]},
                        {"type": "tip", "text": "You are not expected to be an expert in every subject. You are expected to keep the record, choose the pace, and make sure the work gets done. That is the job, and this handbook is the whole of it."},
                    ],
                    "check": {
                        "prompt": "Final check — the whole operating picture.",
                        "questions": [
                            {"q": "The first things to get right are…", "options": ["Notice, enrolment, and the log", "A perfect timetable", "A classroom"], "answer": "Notice, enrolment, and the log", "explain": "Legal standing, then placement, then the contemporaneous record."},
                            {"q": "The portfolio's statutory core is…", "options": ["An activity log and work samples", "Video recordings", "A textbook receipt"], "answer": "An activity log and work samples", "explain": "Those two, kept as you go, satisfy the requirement."},
                            {"q": "Who issues the final diploma?", "options": ["The parent", "The platform", "The district"], "answer": "The parent", "explain": "The parent is the program administrator and issues the diploma."},
                        ],
                    },
                },
            ],
        },
    ],
}
