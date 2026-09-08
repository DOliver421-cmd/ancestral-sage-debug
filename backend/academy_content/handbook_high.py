"""Student Handbook — High School Edition (Grades 9–12, free ebook course).

A guide for students AND parents: transcripts, GPAs, credit tracking, college
and career planning, Bright Futures alignment, and using the Academy's records
and Florida compliance tools well.
"""

HANDBOOK_HIGH = {
    "slug": "handbook-high-school",
    "title": "Student Handbook — High School Edition (Grades 9–12)",
    "summary": "A guide for high school students and their parents: credits, transcripts, GPA, college and career planning, Bright Futures, and finishing homeschool strong.",
    "description": (
        "The High School Student Handbook is a free ebook-style course for grades 9–12 and their "
        "parents. High school homeschool runs on records: credits, transcripts, and deadlines. "
        "This handbook explains how credits are earned and tracked, how a homeschool transcript is "
        "built (and how the Academy's Records page generates one), how GPA works, how Florida's "
        "Bright Futures scholarship requirements map onto your four-year plan, how to research "
        "college and career paths, and how to run the final year — testing, applications, and the "
        "Florida annual evaluation — without panic."
    ),
    "subject": "life_skills",
    "subject_label": "Student Handbook",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["9", "10", "11", "12"],
    "grade_label": "Grades 9–12 (students + parents)",
    "status": "published",
    "audience": "High school students and their parents planning toward graduation and beyond.",
    "est_hours": 4,
    "passing_score": 80,
    "learning_objectives": [
        "Explain how homeschool credits are counted and what a year of coursework includes.",
        "Describe how a homeschool transcript is structured and generate one from Academy records.",
        "Calculate a GPA and explain why course rigor matters alongside it.",
        "Map Bright Futures scholarship requirements onto a four-year high school plan.",
        "Build a post-graduation plan: college, trade, work, or entrepreneurship.",
        "Run the senior year: Florida annual evaluation, testing, and applications on schedule.",
    ],
    "units": [
        {
            "slug": "handbook-high-chapters",
            "title": "Chapters",
            "summary": "Six chapters for students and parents planning the four-year run.",
            "order": 1,
            "lessons": [
                {
                    "slug": "how-credits-work",
                    "title": "Chapter 1: Credits — the Currency of High School",
                    "order": 1,
                    "minutes": 15,
                    "summary": "What a credit is, what a year of study includes, and how to count yours.",
                    "learn": [
                        {"type": "p", "text": "A high school 'credit' (in Florida, one full-year course) represents roughly 120–180 hours of study — the standard is about an hour a day for a school year. As a homeschooler, you and your parents decide what counts, which is freedom and responsibility at once: your transcript must be honest and defensible, because colleges and evaluators will read it as your family's word."},
                        {"type": "list", "items": [
                            "A typical Florida-track load: 4 English, 4 math, 3 science (with labs), 3 social studies, plus electives — about 24 credits to graduate on the standard track.",
                            "One Academy course at ~20 hours is a strong semester elective or a component of a year course — parents combine resources and log hours honestly.",
                            "Keep a credit log per subject: course name, materials used, hours, and mastery evidence. Your Academy records page does most of this automatically.",
                            "Dual enrollment, online courses, and documented work experience can all become credits — anything real and documented can be recorded.",
                        ]},
                        {"type": "tip", "text": "For parents: decide your credit policy in 9th grade, write it down, and apply it consistently. Evaluators and colleges care less about your specific choices than about consistency and documentation."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 1.",
                        "questions": [
                            {"q": "One full-year high school credit represents roughly…", "options": ["120–180 hours of study", "40 hours", "however long you feel like"], "answer": "120–180 hours of study", "explain": "The standard is about an hour a day across a school year."},
                            {"q": "The most important quality of a homeschool transcript is that it's…", "options": ["honest, consistent, and documented", "short", "full of AP classes only"], "answer": "honest, consistent, and documented", "explain": "It's your family's word — evaluators and colleges read consistency as credibility."},
                        ],
                    },
                },
                {
                    "slug": "transcripts-and-gpa",
                    "title": "Chapter 2: Transcripts and GPA, Demystified",
                    "order": 2,
                    "minutes": 15,
                    "summary": "What goes on the document, how the number is computed, and who signs it.",
                    "learn": [
                        {"type": "p", "text": "A homeschool transcript is a one-to-two page document you and your parent create: student information, every course taken by year with credits and final grades, cumulative GPA, graduation date, and the parent's signature as school official. That last part matters — in a homeschool, the parent IS the school administrator; the signature is what makes the document official, and it is a serious one."},
                        {"type": "list", "items": [
                            "GPA: standard unweighted scale assigns A=4.0, B=3.0, C=2.0, D=1.0. Multiply each course grade's value by its credits, add them, divide by total credits.",
                            "Weighted GPAs (adding e.g. 1.0 for AP/dual-enrollment) vary by college — always provide the unweighted number and note the scale you used.",
                            "Course titles should be recognizable: 'Algebra 1' beats 'Math We Did.' Descriptions of materials can go in a course-description appendix.",
                            "The Academy's Records page generates transcript-style summaries from your mastery data — parents review, assign final grades, and finalize.",
                        ]},
                        {"type": "example", "title": "Do the math", "text": "Four courses: A (1.0 cr), B (1.0), A (0.5), C (0.5). Points: 4.0 + 3.0 + 2.0 + 1.0 = 10.0 ÷ 3.0 credits = 3.33 GPA. One semester of C dragged it — that's how the math feels every choice."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 2.",
                        "questions": [
                            {"q": "Who signs a homeschool transcript as the school official?", "options": ["The parent", "The student", "The Academy website"], "answer": "The parent", "explain": "In a homeschool, the parent is the school administrator — the signature makes it official."},
                            {"q": "Unweighted GPA assigns an A the value of…", "options": ["4.0", "5.0", "100"], "answer": "4.0", "explain": "A=4, B=3, C=2, D=1 on the standard unweighted scale; weighted scales add rigor bonuses."},
                        ],
                    },
                },
                {
                    "slug": "bright-futures-and-florida",
                    "title": "Chapter 3: Bright Futures and the Florida Map",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Florida's scholarship for homeschoolers — requirements and the four-year plan.",
                    "learn": [
                        {"type": "p", "text": "Florida's Bright Futures Scholarship pays a large share of Florida public college tuition for students who meet GPA, coursework, test-score, and volunteer-service requirements. Homeschoolers qualify — the key is that YOU plan for the requirements early, because several are course-and-clock based and can't be rushed in senior year."},
                        {"type": "list", "items": [
                            "The award tiers (Florida Academic / Medallion) differ mainly in GPA, test scores, and service hours — check current requirements at the Florida DOE site; numbers adjust periodically.",
                            "Coursework alignment: Bright Futures expects a college-prep distribution — the same 4 English / 4 math / 3 science / 3 social studies shape from Chapter 1.",
                            "Volunteer service hours must be documented and approved — start logging in 9th grade, not 12th.",
                            "Test scores (SAT/ACT) matter — plan a first attempt in 11th grade so there's time to retake.",
                            "Homeschool students submit their parent-signed transcript as part of the application — Chapter 2's document is the one.",
                        ]},
                        {"type": "tip", "text": "For parents: pair Bright Futures planning with your Florida homeschool compliance (Notice of Intent, annual evaluation — see the Academy's Compliance page). One calendar, two checklists, zero panic."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 3.",
                        "questions": [
                            {"q": "The smartest time to start logging volunteer service hours is…", "options": ["9th grade", "senior year", "after graduation"], "answer": "9th grade", "explain": "Service hours accumulate over time — they can't be rushed in the final year."},
                            {"q": "Homeschoolers applying for Bright Futures submit…", "options": ["a parent-signed transcript meeting the course distribution", "a GED", "nothing — they're exempt"], "answer": "a parent-signed transcript meeting the course distribution", "explain": "The transcript is the homeschool's official academic record for the application."},
                        ],
                    },
                },
                {
                    "slug": "college-career-and-beyond",
                    "title": "Chapter 4: College, Trade, Work, or Build — Choosing on Purpose",
                    "order": 4,
                    "minutes": 15,
                    "summary": "Four real paths after graduation and how to research each.",
                    "learn": [
                        {"type": "p", "text": "College is one path, not the definition of success. The honest question for 11th grade is not 'where do I apply?' but 'what do I want my ordinary Tuesday to look like at 25?' — then work backwards. Four paths dominate: university, trade/technical certification, direct workforce, and entrepreneurship. Each has a research method."},
                        {"type": "list", "items": [
                            "University: research programs (not just campuses), net price after aid, and homeschool admission requirements — most welcome homeschoolers and expect the transcript + test scores + essays.",
                            "Trade/technical: certifications, apprenticeships, and licensing hours — often paid-to-learn, high demand, faster to income. The Academy's Builder/Trade track feeds this directly.",
                            "Workforce: entry now, credentials later — the pattern of stacking certificates while employed beats waiting for perfect.",
                            "Entrepreneurship: the Academy's Entrepreneurship courses are the starter kit; the real prerequisite is a customer conversation, so start small and start now.",
                        ]},
                        {"type": "tip", "text": "Shadow someone for a day in any path you're considering. One day of real observation beats a hundred hours of guessing."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 4.",
                        "questions": [
                            {"q": "The best first question for post-graduation planning is…", "options": ["what do I want my ordinary Tuesday at 25 to look like?", "where are my friends going?", "what's the easiest path?"], "answer": "what do I want my ordinary Tuesday at 25 to look like?", "explain": "Starting from the life you want and working backwards beats starting from applications."},
                            {"q": "A common fast path to strong income is…", "options": ["trade certification and apprenticeships — often paid to learn", "collecting more unspent years", "waiting for inspiration"], "answer": "trade certification and apprenticeships — often paid to learn", "explain": "Skilled trades are high-demand with earn-while-you-learn structures."},
                        ],
                    },
                },
                {
                    "slug": "running-your-four-year-plan",
                    "title": "Chapter 5: Your Four-Year Plan on One Page",
                    "order": 5,
                    "minutes": 15,
                    "summary": "Milestones by grade year — a checklist you can actually follow.",
                    "learn": [
                        {"type": "p", "text": "High school feels overwhelming when every year is generic. It gets simple when each year has a job. Here is the whole four-year plan on one page."},
                        {"type": "list", "items": [
                            "9th: Set the credit policy and transcript format. Choose a rigorous-but-sustainable course load. Start the service-hours log. Explore everything.",
                            "10th: Deepen the load. Take a first PSAT-style practice test. Try one serious extracurricular commitment. First job or long project.",
                            "11th: The heavy year — real SAT/ACT attempt, college/trade research visits, one deep extracurricular leadership role, begin essay drafts.",
                            "12th: Execution — retake tests if needed, applications and FAFSA early, complete the Florida annual evaluation, finish strong (senior-year grades still count), order the final transcript.",
                        ]},
                        {"type": "tip", "text": "Put these five milestones on a family calendar now. High school panic is almost always just milestones discovered late."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 5.",
                        "questions": [
                            {"q": "Which year is the designated 'heavy' year for tests and research?", "options": ["11th grade", "9th grade", "there's no pattern"], "answer": "11th grade", "explain": "Junior year leaves time to retake tests and refine choices before applications."},
                            {"q": "Senior-year course performance…", "options": ["still counts — colleges review the final transcript", "doesn't matter after acceptance", "can be skipped"], "answer": "still counts — colleges review the final transcript", "explain": "Acceptances are conditional on the final record; finish strong."},
                        ],
                    },
                },
                {
                    "slug": "the-final-year-florida-checklist",
                    "title": "Chapter 6: Senior Year — The Florida Finishing Checklist",
                    "order": 6,
                    "minutes": 15,
                    "summary": "Evaluation, records, graduation, and the paperwork that ends well.",
                    "learn": [
                        {"type": "p", "text": "Florida homeschoolers close out high school with a short, known checklist. Done in order, it's a few afternoons of paperwork, not a crisis."},
                        {"type": "list", "items": [
                            "Complete the annual evaluation with your Florida-certified evaluator — bring your Academy records and mastery data; most evaluations take under an hour.",
                            "Finalize the transcript: every course, credit, and final grade, parent-signed, dated graduation.",
                            "File applications: colleges (with FAFSA), trade programs, or your business registrations — whatever Chapter 4's plan chose.",
                            "Request any needed records (dual-enrollment transcripts, test scores) early — offices run on their own clocks.",
                            "Graduate: the parent issues the diploma. In Florida, a parent-issued homeschool diploma is real — accepted by colleges, employers, and the military, backed by your transcript.",
                        ]},
                        {"type": "tip", "text": "Print your Records page transcripts each year of high school. Four printed snapshots make the final transcript a 30-minute assembly job instead of a reconstruction project."},
                    ],
                    "check": {
                        "prompt": "A quick review of Chapter 6.",
                        "questions": [
                            {"q": "In Florida, the homeschool diploma is issued by…", "options": ["the parent, as school administrator", "the state automatically", "the local school board"], "answer": "the parent, as school administrator", "explain": "Parent-issued homeschool diplomas are real and widely accepted, backed by the transcript."},
                            {"q": "The annual evaluation goes best when you bring…", "options": ["your records and mastery documentation from the year", "nothing at all", "only your report card from 3rd grade"], "answer": "your records and mastery documentation from the year", "explain": "Evaluators work from evidence — the Academy's records are exactly that."},
                        ],
                    },
                },
            ],
        },
    ],
}
