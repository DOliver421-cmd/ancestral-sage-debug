"""Grade 12 ELA: Prose of Liberation (published).

Grade 12 ELA built on the political prose of the Black intellectual
tradition — Ida B. Wells, James Baldwin, Audre Lorde, Thomas Sankara,
C.L.R. James — teaching rhetoric, analysis, and public argument through
speeches, essays, and manifestos.
"""

PROSE_OF_LIBERATION = {
    "slug": "prose-of-liberation",
    "title": "Prose of Liberation: Rhetoric, Analysis, and Public Intellectualism",
    "summary": "Wells, Baldwin, Lorde, Sankara, and C.L.R. James — political prose read for rhetoric, evidence, and argument.",
    "description": (
        "Grade 12 English here reads the political prose of the Black intellectual "
        "tradition as primary texts of rhetoric and public philosophy. Ida B. Wells "
        "built investigative journalism against lynching; James Baldwin fused essay "
        "with moral argument; Audre Lorde wrote theory as poetry; Thomas Sankara "
        "made political speeches into manifestos; C.L.R. James wrote history and "
        "cultural criticism together. Students analyze each for claim, evidence, "
        "audience, and rhetorical strategy — and write argumentative essays of their own."
    ),
    "subject": "ela",
    "subject_label": "English Language Arts",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["12"],
    "grade_label": "Grade 12",
    "status": "published",
    "audience": "Grade 12 students studying rhetoric, political prose, and argument writing.",
    "est_hours": 30,
    "passing_score": 80,
    "learning_objectives": [
        "Analyze the claim, evidence, audience, and appeals in a political essay.",
        "Describe how Ida B. Wells used data to refute the justifications for lynching.",
        "Explain Baldwin's rhetorical method of addressing the reader directly.",
        "Analyze Lorde's use of poetry and aphorism as theoretical argument.",
        "Analyze Sankara's political rhetoric as a manifestos and mobilization.",
        "Describe C.L.R. James's method of political and cultural criticism.",
        "Write an argumentative essay with a claim, counterargument, and evidence.",
    ],
    "units": [
        {
            "slug": "data-and-argument",
            "title": "Data and Argument: Wells and Baldwin",
            "summary": "Evidence-driven journalism and moral address.",
            "order": 1,
            "lessons": [
                {
                    "slug": "ida-b-wells",
                    "title": "Ida B. Wells and the Arithmetic of Lynching",
                    "order": 1,
                    "minutes": 28,
                    "summary": "Investigative writing that refuted an official story with records.",
                    "learn": [
                        {"type": "p", "text": "Ida B. Wells (1862–1931) began as a teacher and newspaper editor in Memphis. After three friends were lynched in 1892, she investigated the official claim that lynching punished rape. Reading court records and newspaper accounts, she showed that in the great majority of cases no such charge existed — that lynching was economic and political terror. Her pamphlets Southern Horrors (1892) and The Red Record (1895) put the numbers in the hands of a national public."},
                        {"type": "list", "items": [
                            "Method: collect primary records, count cases, tabulate charges.",
                            "Finding: most lynchings were not for the stated reason.",
                            "Rhetoric: numbers, not adjectives, carried the argument.",
                            "Consequences: she was driven out of the South by threats on her life.",
                        ]},
                        {"type": "example", "title": "The rhetorical move", "text": "Wells made her argument as a research report with a moral conclusion. A reader who rejected the moral still had to deal with the figures."},
                        {"type": "activity", "title": "Rebuild the table", "text": "Read one page of The Red Record. Rebuild its categories in a table and write the conclusion in one sentence."},
                    ],
                    "check": {
                        "prompt": "Check your analysis of Wells.",
                        "questions": [
                            {"q": "Wells's investigation found that most lynchings were…", "options": ["not for the officially stated reason", "never recorded", "always for assault"], "answer": "not for the officially stated reason", "explain": "Her statistics refuted the claim that lynching punished rape."},
                            {"q": "Wells's method was primarily…", "options": ["collecting and counting primary records", "novel writing", "oral testimony alone"], "answer": "collecting and counting primary records", "explain": "She built a research-based case with counted cases."},
                        ],
                    },
                },
                {
                    "slug": "james-baldwin",
                    "title": "James Baldwin: The Essay as Address",
                    "order": 2,
                    "minutes": 28,
                    "summary": "Writing that speaks to the reader as a person.",
                    "learn": [
                        {"type": "p", "text": "James Baldwin used the essay to address a white American audience as a person, not a category: 'I am not a nigger. I am a man' in The Fire Next Time, aimed at his nephew, and a letter to his nephew made universally. His method combines autobiography, biblical cadence, and direct address; his argument is that the moral health of the reader, not only the victim's, is at stake."},
                        {"type": "list", "items": [
                            "Direct address ('you') places the reader in relation to the argument.",
                            "Biblical and sermonic structure shapes his rhythm.",
                            "The personal anecdote is evidence, not decoration.",
                            "Argument: Americans must change themselves, not merely others.",
                        ]},
                        {"type": "example", "title": "A famous formulation", "text": "'I am what time, circumstance, history, have made of me, certainly, but I am also much more than that.' — the essay form used to assert personhood against category."},
                        {"type": "activity", "title": "Rhetoric map", "text": "In one Baldwin essay, mark each move from anecdote to abstraction to address. Label the thesis sentence where it appears."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Baldwin.",
                        "questions": [
                            {"q": "Baldwin's essays frequently use direct address, placing…", "options": ["the reader inside the argument", "only the writer on stage", "no one in relation to the text"], "answer": "the reader inside the argument", "explain": "Direct address makes the reader a participant and a subject."},
                            {"q": "Baldwin claimed that what must change is…", "options": ["the reader's own moral relation", "only laws", "only distant institutions"], "answer": "the reader's own moral relation", "explain": "He insisted personal change was the root of political change."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "poetry-as-theory",
            "title": "Poetry as Theory: Lorde and Sankara",
            "summary": "Aphorism, denunciation, and mobilization.",
            "order": 2,
            "lessons": [
                {
                    "slug": "audre-lorde",
                    "title": "Audre Lorde: Theory as Poetry",
                    "order": 3,
                    "minutes": 28,
                    "summary": "Aphorism that rearranges the reader's categories.",
                    "learn": [
                        {"type": "p", "text": "Audre Lorde named herself a 'Black, lesbian, mother, warrior, poet' and wrote theory in the register of poetry. Sister Outsider (1984) collected essays in which aphorisms do the work of extended arguments: 'the master's tools will never dismantle the master's house.' Her method is to reject the demand that the oppressed explain themselves in the oppressor's idiom — a rhetorical and political choice,"},
                        {"type": "list", "items": [
                            "Aphorism as thesis: a short line that reorganizes a whole debate.",
                            "Difference as a resource, not an obstacle to solidarity.",
                            "The personal as political, used structurally rather than sentimentally.",
                        ]},
                        {"type": "example", "title": "The master's tools", "text": "The sentence is short, concrete, and architectural — a metaphor from building work, which is why it functions as both poetry and argument."},
                        {"type": "activity", "title": "Aphorism bank", "text": "Collect three Lorde aphorisms. For each, write the extended argument it compresses in two sentences."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Lorde.",
                        "questions": [
                            {"q": "Lorde's writing is characterized by…", "options": ["aphorisms that carry theoretical weight", "only narrative fiction", "scientific notation"], "answer": "aphorisms that carry theoretical weight", "explain": "Her short lines do the work of long arguments."},
                            {"q": "'The master's tools will never dismantle the master's house' argues that…", "options": ["liberation requires new means, not only borrowed ones", "one should use the master's best tools", "houses cannot be built"], "answer": "liberation requires new means, not only borrowed ones", "explain": "She rejects using oppressor's methods for liberation."},
                        ],
                    },
                },
                {
                    "slug": "thomas-sankara",
                    "title": "Thomas Sankara: Speech as Manifesto",
                    "order": 4,
                    "minutes": 28,
                    "summary": "A president who spoke directly to farmers and women.",
                    "learn": [
                        {"type": "p", "text": "Thomas Sankara led Burkina Faso from 1983 until his assassination in 1987, renaming the country from Upper Volta to 'land of upright people'. His speeches were acts of policy: against debt, for land and vaccine self-sufficiency, for women's participation in government and the army. He addressed farmers, women's groups, and students directly, making political argument a daily public act — and rejecting foreign aid as a form of dependence."},
                        {"type": "list", "items": [
                            "Against debt: 'Debt cannot be repaid, because we have nothing to do with it.'",
                            "Self-reliance: cotton processed at home, food self-sufficiency in three years.",
                            "Gender: women in cabinet, the military, and the courts.",
                            "Plain style: speaking to ordinary farmers in their own terms.",
                        ]},
                        {"type": "example", "title": "Rhetorical choice", "text": "Sankara used no diplomatic register at the Organization of African Unity in 1987 — an address to an assembly of heads of state, in the voice of a mobilizer."},
                        {"type": "activity", "title": "Write the speech", "text": "Write a 250-word Sankara-style speech for a modern summit: clear claim, concrete demand, plain words, no euphemism."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Sankara.",
                        "questions": [
                            {"q": "Sankara's argument at the OAU in 1987 was notable for…", "options": ["addressing heads of state in a plain mobilizing voice", "making a request for more aid", "quoting only European sources"], "answer": "addressing heads of state in a plain mobilizing voice", "explain": "He refused diplomatic register when speaking of dependence."},
                            {"q": "Burkina Faso's name means…", "options": ["'land of upright people'", "'land of gold'", "'land of rivers'"], "answer": "'land of upright people'", "explain": "The renaming expressed the revolution's moral claim."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "james-and-your-argument",
            "title": "C.L.R. James and Your Own Argument",
            "summary": "Cultural criticism, and the capstone essay.",
            "order": 3,
            "lessons": [
                {
                    "slug": "clr-james",
                    "title": "C.L.R. James: Criticism as Politics",
                    "order": 5,
                    "minutes": 28,
                    "summary": "Writing about cricket and revolutions in the same voice.",
                    "learn": [
                        {"type": "p", "text": "C.L.R. James (1901–1989) wrote Beyond a Boundary, half memoir half political theory, arguing that cricket encodes the colonial and post-colonial world. He also wrote The Black Jacobins, a history of the Haitian Revolution that placed enslaved people at the center as agents rather than passive victims. His method connects culture, sport, and politics as parts of one argument about power."},
                        {"type": "list", "items": [
                            "The Black Jacobins (1938): Haitian revolutionaries as historical actors.",
                            "Beyond a Boundary (1963): sport as the site of modern history.",
                            "Method: personal experience as evidence within a political analysis.",
                        ]},
                        {"type": "example", "title": "The argument", "text": "James said of the Haitian revolution that the enslaved had made their own revolution — a claim as much about agency as about the past."},
                        {"type": "activity", "title": "Apply the method", "text": "Pick a sport, genre of music, or game. Write one paragraph applying James's method: what does it reveal about power and history?"},
                    ],
                    "check": {
                        "prompt": "Check what you know about C.L.R. James.",
                        "questions": [
                            {"q": "The Black Jacobins tells the story of…", "options": ["the Haitian Revolution led by enslaved people", "the French monarchy", "a cricket tour"], "answer": "the Haitian Revolution led by enslaved people", "explain": "James centered the enslaved as actors in the revolution they made."},
                            {"q": "James's method treats culture and politics as…", "options": ["connected parts of one argument", "separate worlds", "irrelevant to each other"], "answer": "connected parts of one argument", "explain": "His work joins cultural criticism and political theory."},
                        ],
                    },
                },
                {
                    "slug": "capstone-argument",
                    "title": "Capstone: Your Argumentative Essay",
                    "order": 6,
                    "minutes": 32,
                    "summary": "Write, revise, and defend an argument.",
                    "learn": [
                        {"type": "p", "text": "The writers in this course all use the same four moves: a claim, evidence, an audience, and a counterargument. Your capstone is an argumentative essay of 800–1,000 words on a question raised by any text in this course. It must name its evidence, address the strongest opposing view, and conclude with what the reader should do or think."},
                        {"type": "list", "items": [
                            "Claim: a debatable sentence you can defend with evidence.",
                            "Evidence: quotations and facts, cited by source.",
                            "Counterargument: the strongest objection, answered.",
                            "Rhetorical appeal: logos plus pathos plus ethos — deliberately chosen.",
                        ]},
                        {"type": "tip", "text": "Every writer in this course was attacked for their claim. An argument you have never had to defend is not yet an argument."},
                        {"type": "activity", "title": "Write and revise", "text": "Draft the essay, exchange it with one reader, and revise once for evidence and counterargument."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of argument.",
                        "questions": [
                            {"q": "A strong counterargument in an essay does what?", "options": ["states the strongest objection and answers it", "restates the thesis with different words", "apologizes for the claim"], "answer": "states the strongest objection and answers it", "explain": "Addressing the best objection strengthens credibility."},
                            {"q": "A claim is a debatable sentence that…", "options": ["requires evidence to be believed", "is obviously true", "has no position"], "answer": "requires evidence to be believed", "explain": "Arguments exist only where reasonable people could disagree."},
                        ],
                    },
                },
            ],
        },
    ],
}
