"""African Philosophy and Ethics: Systems of Thought and Governance (published).

Humanities/Philosophy/Civics course for Grades 9–12 examining classical and
contemporary African philosophical frameworks — Ubuntu, Akan proverb philosophy,
communal epistemology — contrasted with Western ethical traditions, with a
capstone philosophical portfolio.
"""

AFRICAN_PHILOSOPHY_ETHICS = {
    "slug": "african-philosophy-ethics",
    "title": "African Philosophy and Ethics: Systems of Thought and Governance",
    "summary": "Classical and contemporary African philosophical frameworks — Ubuntu, Akan proverb philosophy, communal epistemology — contrasted with Western ethical traditions.",
    "description": (
        "Examines classical and contemporary African philosophical frameworks: epistemology "
        "and worldview, Ubuntu's relational personhood, Akan proverb philosophy, consensus "
        "governance, and modern thinkers including Frantz Fanon, Kwasi Wiredu, and Sylvia "
        "Wynter — each contrasted with Western ethical traditions. The capstone is a "
        "philosophical portfolio in which students defend a comparative claim in their own "
        "voice."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "scholar",
    "tracks": ["scholar"],
    "grades": ["9", "10", "11", "12"],
    "grade_label": "Grades 9–12",
    "status": "published",
    "audience": "High school students preparing for advanced humanities and civics study.",
    "est_hours": 21,
    "passing_score": 80,
    "learning_objectives": [
        "Explain ontology and epistemology and how oral traditions function as rigorous knowledge systems.",
        "Contrast Ubuntu's relational personhood with Western individualist autonomy.",
        "Interpret Akan proverbs as compressed ethical and legal frameworks.",
        "Describe consensus-based governance in traditional African councils and its modern applications.",
        "Summarize Fanon's critique of colonialism and Wiredu's program for conceptual decolonization.",
        "Evaluate a Western ethical framework (utilitarian or Kantian) against an African communal one on a real case.",
        "Compose a defensible comparative philosophical argument in the capstone portfolio.",
    ],
    "units": [
        {
            "slug": "epistemology-and-worldview",
            "title": "Mapping the Terrain: Epistemology and Worldview",
            "summary": "How knowledge is validated, structured, and transmitted in African and Western frameworks.",
            "order": 1,
            "lessons": [
                {
                    "slug": "what-counts-as-knowledge",
                    "title": "What Counts as Knowledge? Ontology, Epistemology, and Oral Tradition",
                    "order": 1,
                    "minutes": 30,
                    "summary": "Eurocentric universalism critiqued — and oral tradition examined as a rigorous system of record.",
                    "learn": [
                        {"type": "p", "text": "Ontology asks: what exists, and what is a person? Epistemology asks: how do we know, and what makes a belief justified? European Enlightenment philosophy (Descartes' 'I think, therefore I am') treated the isolated individual mind as the starting point of knowledge. Many African traditions start elsewhere: personhood and knowledge are constituted in community — through lineage, lived experience, and tested sayings. In the 20th century, philosophers like Kwasi Wiredu and Paulin Hountondji argued that treating European categories as the universal standard was itself a philosophical error, not a neutral one — the critique of Eurocentric hegemony in philosophy."},
                        {"type": "p", "text": "Is oral tradition 'just stories'? Test it like any system of record. Oral historians used formal training, designated memory-keepers, cross-checking against multiple reciters, ritual settings that discourage error, and public accountability — a griot who misstates a king's genealogy answers to the court. Historians now use oral tradition alongside documents and archaeology (for example, in reconstructing the history of the Mali Empire's regions). The medium differs from writing; the rigor can be real."},
                        {"type": "list", "items": [
                            "Epistemology: the study of knowledge — justification, truth, and belief.",
                            "Communal epistemology: knowledge is validated through community consensus, elders' testimony, and lived experience, not only individual reasoning.",
                            "Wiredu's test: every philosophical claim should be examined for unexamined cultural bias — including the claim that there is no bias.",
                        ]},
                        {"type": "activity", "title": "Deliverable: comparison matrix", "text": "Build an Epistemological Comparison Matrix: three columns (Source of knowledge, How truth is validated, Who is a knower). Fill one column for Descartes-style rationalism, one for a West African communal tradition, one for your own school/community. Identify one strength and one risk of each."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of epistemology and oral tradition.",
                        "questions": [
                            {"q": "Epistemology is the branch of philosophy that studies…", "options": ["knowledge and justification", "the nature of beauty", "moral duty"], "answer": "knowledge and justification", "explain": "Epistemology asks what knowledge is and what makes beliefs justified; aesthetics studies beauty, ethics studies duty."},
                            {"q": "A rigorous oral tradition differs from mere rumor because it includes…", "options": ["trained memory-keepers, cross-checking, and public accountability", "longer stories", "written footnotes"], "answer": "trained memory-keepers, cross-checking, and public accountability", "explain": "Validation mechanisms — not the medium — distinguish a knowledge system from mere hearsay."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "ubuntu-and-personhood",
            "title": "The Logic of Being: Ubuntu and Relational Personhood",
            "summary": "'I am because we are' — analyzed as ontology and ethics, then applied to justice.",
            "order": 2,
            "lessons": [
                {
                    "slug": "ubuntu-personhood",
                    "title": "Ubuntu: Relational Personhood versus Individualist Autonomy",
                    "order": 2,
                    "minutes": 30,
                    "summary": "Cogito, ergo sum versus 'I am because we are' — and what each implies about moral duty.",
                    "learn": [
                        {"type": "p", "text": "Ubuntu, a Southern African framework (the phrase 'umuntu ngumuntu ngabantu' — a person is a person through other persons — is Zulu), holds that personhood is not a possession you are born with but an achievement built through relationships of care, dignity, and recognition. This is a direct ontological contrast with Descartes' isolated thinking self and with social-contract traditions (Hobbes, Locke) that imagine individuals first and society second. In Ubuntu thinking, moral obligation is not created by contract; human dignity is inherent in the web of relations that makes you a person at all."},
                        {"type": "list", "items": [
                            "Descartes: the certain starting point is the alone mind. Ubuntu: the certain starting point is the community that names, teaches, and recognizes you.",
                            "Moral implication: harming the community's dignity harms you, because you are partly constituted by it — self-interest and other-interest are not opposites.",
                            "Legal expression: South Africa's post-apartheid Constitutional Court has cited Ubuntu in rulings on dignity and restorative justice.",
                        ]},
                        {"type": "example", "title": "Test the idea", "text": "Consider an infant: born with capacities, but constituted as a person through being cared for, named, and taught. Descartes asks what the mind can know alone; Ubuntu asks who made the mind's knowing possible. Both positions are serious — the exercise is to see they genuinely disagree."},
                        {"type": "activity", "title": "Concept map", "text": "Draw two concept maps: 'person' under radical individualism (autonomous, rights-bearing, pre-social) and under Ubuntu (relational, duty-bearing, constituted in community). Mark where the two maps agree — that overlap is where real dialogue happens."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Ubuntu.",
                        "questions": [
                            {"q": "Ubuntu's central claim about personhood is that a person is…", "options": ["constituted through relationships with others", "an isolated mind that exists before society", "defined by legal citizenship"], "answer": "constituted through relationships with others", "explain": "'A person is a person through other persons' — personhood is relational by definition."},
                            {"q": "Compared with social-contract theory, Ubuntu grounds moral obligation in…", "options": ["inherent communal ties rather than an agreement among separate individuals", "fear of punishment", "self-interest only"], "answer": "inherent communal ties rather than an agreement among separate individuals", "explain": "Ubuntu rejects the pre-social individual picture: obligation flows from the relations that constitute you."},
                        ],
                    },
                },
                {
                    "slug": "ubuntu-restorative-justice",
                    "title": "Ubuntu in Practice: Restorative Justice and Conflict Resolution",
                    "order": 3,
                    "minutes": 25,
                    "summary": "A case study contrasting punitive and restorative frameworks.",
                    "learn": [
                        {"type": "p", "text": "Punitive justice asks: what law was broken, who broke it, and what punishment do they deserve? Restorative justice asks: what harm was done, to whom, and what will repair it? Traditional Southern African dispute resolution — the inkundla/lekgotla gathering — aimed at restoring relationships between offender, victim, and community, with reconciliation as the explicit goal. South Africa's Truth and Reconciliation Commission (1995–2002) deliberately adapted elements of this ethos to national scale, trading punishment for truth-telling and amnesty conditions — with results still debated by scholars."},
                        {"type": "list", "items": [
                            "Restorative circle: all affected parties speak; the outcome is a repair plan, not only a sentence.",
                            "Critique 1: can reconciliation without punishment truly deter or satisfy justice? (a serious Western objection).",
                            "Critique 2: can purely punitive systems ever repair relationships? (Ubuntu's objection).",
                        ]},
                        {"type": "activity", "title": "Case analysis (Deliverable)", "text": "Take one case: a student vandalizes the school's community garden. Write two resolutions: one through a punitive model (rule broken, penalty assigned) and one through an Ubuntu restorative model (harm identified, repair negotiated). Then answer: what does each model optimize for, and which harms does each leave unaddressed?"},
                    ],
                    "check": {
                        "prompt": "Check your understanding of restorative frameworks.",
                        "questions": [
                            {"q": "The central question of restorative justice is…", "options": ["what harm occurred and how it can be repaired", "which law was broken and what punishment fits", "who has the most power"], "answer": "what harm occurred and how it can be repaired", "explain": "Restorative frameworks center harm and repair; punitive frameworks center rule and penalty."},
                            {"q": "South Africa's Truth and Reconciliation Commission is an example of…", "options": ["adapting restorative principles to national-scale political healing", "a purely punitive war-crimes tribunal", "an ordinary criminal court"], "answer": "adapting restorative principles to national-scale political healing", "explain": "The TRC traded amnesty conditions for public truth-telling, drawing on reconciliation-centered traditions."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "proverbs-and-governance",
            "title": "The Wisdom of Language: Akan Proverbs and Consensus Governance",
            "summary": "Proverbs as compressed philosophy — and councils that governed by consent.",
            "order": 3,
            "lessons": [
                {
                    "slug": "akan-proverb-philosophy",
                    "title": "Akan Proverb Philosophy: Nyansa, Symbols, and Sankofa",
                    "order": 4,
                    "minutes": 30,
                    "summary": "How aphorisms function as ethical frameworks and legal precedent.",
                    "learn": [
                        {"type": "p", "text": "Among the Akan people of Ghana, philosophy lives in proverbs (mmara kasEE — literally 'marriage of language,' but understood as compressed legal-moral sayings). The Akan concept nyansa means wisdom: the judgment to apply the right proverb to the right situation. Proverbs function as precedent: in traditional courts, citing the apt proverb is like citing case law — it invokes a whole moral framework in one line. Adinkra symbols compress the same ideas visually; sankofa ('go back and fetch it') teaches the critical retrieval of the past for present use."},
                        {"type": "list", "items": [
                            "'Obi nnim obrempon ahyɛase' — no one knows the beginnings of a great one: humility before origins; every greatness started small.",
                            "'Se wo were fi na wosankofa a yenkyi' — it is not wrong to go back for what you forgot: critical retrieval, not nostalgia.",
                            "'Nsa baako nkura adesoa' — one hand cannot lift the burden: collective labor and mutual obligation.",
                            "Comparison: Aesop's fables and Benjamin Franklin's aphorisms perform the same compress-and-transmit function in Western culture.",
                        ]},
                        {"type": "tip", "text": "Reading a proverb philosophy is an exercise in unpacking: state the claim, name the value it protects, and test when it would NOT apply. Wisdom is knowing the boundary of the rule — that is nyansa."},
                        {"type": "activity", "title": "Proverb analysis (Deliverable)", "text": "Choose one Akan proverb (above or researched) and one Western aphorism. For each: state its claim in plain language, the value it protects, and one situation where it fails as advice. Write 150–200 words."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Akan proverb philosophy.",
                        "questions": [
                            {"q": "In Akan practice, proverbs function in traditional courts most like…", "options": ["precedent — invoking a whole moral framework for a case", "entertainment between hearings", "written statutes with fixed penalties"], "answer": "precedent — invoking a whole moral framework for a case", "explain": "Citing the apt proverb brings an entire tested moral judgment to bear, the way precedent does in case law."},
                            {"q": "The sankofa principle teaches…", "options": ["critically retrieving what was lost from the past for present use", "that the past should be forgotten", "blind imitation of ancestors"], "answer": "critically retrieving what was lost from the past for present use", "explain": "Sankofa is retrieval with judgment — going back to fetch what serves the present."},
                        ],
                    },
                },
                {
                    "slug": "consensus-governance",
                    "title": "Consensus Governance: Councils, Oaths, and Accountability",
                    "order": 5,
                    "minutes": 25,
                    "summary": "How chief-in-council systems distributed power — and the checks that constrained chiefs.",
                    "learn": [
                        {"type": "p", "text": "Many African political systems distributed power through councils. In the Ashanti (Asante) state, the Asantehene (king) governed with the Asanteman Council of chiefs; among the Igbo of Nigeria, many communities were famously stateless — governed by village assemblies, age grades, and title societies rather than kings. The Tswana kgotla (Botswana) remains a legal tradition today: a public meeting where any adult may speak before the chief, and consensus is sought. The direction of accountability ran upward: chiefs who ruled against counsel could be deposed."},
                        {"type": "list", "items": [
                            "Kgotla (Botswana): constitutionally recognized; used for everything from land disputes to national policy consultation.",
                            "Igbo statelessness: power spread across assemblies, age grades, and oracular checks — a real alternative to monarchy.",
                            "Oaths and office: chiefs were installed and constrained by oaths to the people; breach could end a reign.",
                            "Modern echo: deliberative democracy and citizens' assemblies borrow the same logic — legitimacy through inclusive deliberation.",
                        ]},
                        {"type": "example", "title": "Compare", "text": "Athenian democracy is the West's famous direct-democracy precedent; the kgotla and Igbo assemblies are its equally serious African counterparts — with a different signature: consensus-seeking rather than majority vote, and accountability of rulers to assembly."},
                        {"type": "activity", "title": "Design a council", "text": "Design a five-member student council that governs by consensus: define who speaks, how dissent is recorded, and how a decision can be revisited. Identify one weakness of consensus governance and your safeguard for it."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of consensus governance.",
                        "questions": [
                            {"q": "The Botswana kgotla is best described as…", "options": ["a public assembly where any adult may speak before the chief", "a secret royal court", "a colonial invention with no African roots"], "answer": "a public assembly where any adult may speak before the chief", "explain": "The kgotla is a living precolonial tradition, constitutionally recognized in modern Botswana."},
                            {"q": "Igbo political organization before colonization is notable for…", "options": ["governing large communities without kings, through assemblies and age grades", "having the most powerful absolute monarchy in Africa", "rejecting all forms of assembly"], "answer": "governing large communities without kings, through assemblies and age grades", "explain": "Igbo communities are a classic case of ordered, stateless governance by councils and associations."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "modern-thinkers-and-capstone",
            "title": "Modern Thinkers and the Capstone Portfolio",
            "summary": "Fanon, Wiredu, and Wynter — then a defended comparative argument of your own.",
            "order": 4,
            "lessons": [
                {
                    "slug": "fanon-wiredu-wynter",
                    "title": "Fanon, Wiredu, and Wynter: Philosophy Confronts the Modern World",
                    "order": 6,
                    "minutes": 30,
                    "summary": "Colonialism's mental effects, conceptual decolonization, and the reinvention of 'Man.'",
                    "learn": [
                        {"type": "p", "text": "Frantz Fanon (Martinique/Algeria), in 'Black Skin, White Masks' (1952) and 'The Wretched of the Earth' (1961), analyzed how colonialism damages the colonized person's self-concept — racism as a system that forces people to live as objects in someone else's story. Kwasi Wiredu (Ghana), in 'Philosophy and an African Culture' (1980), proposed conceptual decolonization: auditing inherited philosophical terms (from language to institutions) and replacing distortions with concepts that fit African experience — his consensual democracy proposal draws exactly on the council traditions above. Sylvia Wynter (Jamaica) argued that 'Man' — the Western concept of the human — is one invented genre of being, not the only possible one, and that our current crises require re-telling what a human is."},
                        {"type": "list", "items": [
                            "Fanon's sociogenic thesis: the harms of colonial racism are made by social systems, so they can be unmade by changed systems — an ethical, not just political, program.",
                            "Wiredu's method: take a received concept, ask what it assumes, test it against local experience, revise — philosophy as repair.",
                            "Wynter's move: examine the story a society tells about 'the human,' because the story determines who counts.",
                        ]},
                        {"type": "tip", "text": "These three are not 'African footnotes' to philosophy — they are central 20th-century voices on power, language, and the human, read in every serious philosophy program."},
                        {"type": "activity", "title": "Claim and evidence", "text": "Pick one of the three thinkers. State their central claim in one sentence, then find one concrete example (historical or current) that supports it and one that challenges it."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the modern thinkers.",
                        "questions": [
                            {"q": "Wiredu's 'conceptual decolonization' asks philosophers to…", "options": ["audit inherited concepts for cultural distortion and revise them from African experience", "abandon all Western philosophy unread", "translate everything into French"], "answer": "audit inherited concepts for cultural distortion and revise them from African experience", "explain": "Wiredu's program is critical examination and repair, not rejection — concepts are tested, then revised."},
                            {"q": "Wynter's argument about 'Man' is that the Western concept of the human is…", "options": ["one invented genre of being among possible others, with consequences for who counts", "a scientific fact beyond question", "identical across all cultures"], "answer": "one invented genre of being among possible others, with consequences for who counts", "explain": "Wynter treats 'Man' as a constructed genre whose limits need re-telling — a central idea in contemporary critical theory."},
                        ],
                    },
                },
                {
                    "slug": "capstone-portfolio",
                    "title": "Capstone: The Philosophical Portfolio",
                    "order": 7,
                    "minutes": 35,
                    "summary": "Defend one comparative claim across at least two traditions.",
                    "learn": [
                        {"type": "p", "text": "A philosophy portfolio is a set of connected pieces that develop one defensible claim. Your capstone: choose a question where an African framework and a Western framework genuinely disagree — personhood, justice, knowledge, wealth, or the human — and argue, with evidence from both sides, for a considered position. Strong portfolios quote primary sources sparingly and accurately, treat the opposing view seriously, and acknowledge what remains open."},
                        {"type": "list", "items": [
                            "Component 1 (from Lesson 1): your Epistemological Comparison Matrix.",
                            "Component 2 (from Lesson 3): your restorative-vs-punitive case analysis.",
                            "Component 3 (from Lesson 4): your proverb analysis.",
                            "Component 4 (capstone essay, 500–700 words): the defended comparative argument, citing at least one thinker from each tradition.",
                        ]},
                        {"type": "example", "title": "Sample claims", "text": "'Restorative justice better satisfies the moral aims of punishment than retributive justice, though it needs a public-truth mechanism to work.' Or: 'Personhood understood relationally (Ubuntu) explains moral duties to strangers better than social-contract theory, because…' — both are arguable, sourced, and precise."},
                        {"type": "activity", "title": "Portfolio assembly (Deliverable)", "text": "Assemble your four components with a one-paragraph introduction stating your question and claim. Exchange with a peer: each of you must state the other's claim back in one sentence and pose one serious objection. Revise after the exchange."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the capstone requirements.",
                        "questions": [
                            {"q": "A strong comparative philosophy argument must…", "options": ["engage the strongest version of the opposing view, with evidence from both traditions", "describe only one tradition favorably", "avoid taking any position"], "answer": "engage the strongest version of the opposing view, with evidence from both traditions", "explain": "Steelmanning the opposition and citing both traditions is what separates philosophy from opinion."},
                            {"q": "The purpose of the peer objection step is to…", "options": ["surface weaknesses in your argument while there is still time to revise", "prove who is smarter", "replace evidence with consensus"], "answer": "surface weaknesses in your argument while there is still time to revise", "explain": "Formal objection is a tool of rigor — Socratic method and African council deliberation alike."},
                        ],
                    },
                },
            ],
        },
    ],
}
