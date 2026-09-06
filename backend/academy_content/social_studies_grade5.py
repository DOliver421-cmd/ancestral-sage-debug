"""Social Studies — Grade 5 (full published course)."""

SOCIAL_STUDIES_GRADE_5 = {
    "slug": "social-studies-grade-5",
    "title": "Social Studies — Grade 5",
    "summary": "Early American history, founding documents, and civic principles.",
    "description": (
        "Fifth-grade social studies traces the story of the United States from early "
        "exploration through the founding era. Students examine primary sources, "
        "study the Declaration of Independence and the Constitution, and practice "
        "civic reasoning through simulations and discussions."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["5"],
    "grade_label": "Grade 5",
    "status": "published",
    "audience": "Grade 5 (ages 10–11), Foundations track.",
    "est_hours": 20,
    "passing_score": 80,
    "learning_objectives": [
        "Describe causes and effects of early exploration.",
        "Identify the purposes of the Declaration of Independence.",
        "Explain the structure and purposes of the U.S. Constitution.",
        "Understand the three branches of government.",
        "Evaluate how citizens participate in civic life.",
    ],
    "units": [
        {
            "slug": "early-american-history",
            "title": "Early American History",
            "summary": "Exploration, colonies, and the road to revolution.",
            "order": 1,
            "lessons": [
                {
                    "slug": "age-of-exploration",
                    "title": "The Age of Exploration",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Why Europeans explored and what they found.",
                    "learn": [
                        {"type": "p", "text": "In the 1400s and 1500s, European nations looked for new trade routes to Asia. Explorers like Columbus, da Gama, and Magellan sailed across oceans. Their voyages changed the world forever."},
                        {"type": "list", "items": [
                            "Motivations: trade routes, gold, spreading religion.",
                            "Technology: compass, astrolabe, better ships.",
                            "Consequences: Columbian Exchange, new colonies, conflict with Indigenous peoples.",
                        ]},
                        {"type": "example", "title": "Columbian Exchange", "text": "After Columbus reached the Americas, plants, animals, diseases, and people crossed the Atlantic. This is called the Columbian Exchange."},
                    ],
                    "check": {
                        "prompt": "Show what you know about the Age of Exploration.",
                        "questions": [
                            {"q": "Which explorer reached the Americas in 1492?", "options": ["Christopher Columbus", "Ferdinand Magellan", "Vasco da Gama"], "answer": "Christopher Columbus", "explain": "Columbus sailed for Spain in 1492."},
                            {"q": "What was the Columbian Exchange?", "options": ["the transfer of plants, animals, and diseases between continents", "a type of ship", "a peace treaty"], "answer": "the transfer of plants, animals, and diseases between continents", "explain": "The Columbian Exchange describes what traveled between the Old World and New World."},
                            {"q": "Which was NOT a motivation for exploration?", "options": ["finding new musical instruments", "trade routes", "gold"], "answer": "finding new musical instruments", "explain": "Explorers sought trade routes, gold, and religious spread."},
                        ],
                    },
                },
                {
                    "slug": "colonial-america",
                    "title": "Colonial America",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Life in the 13 colonies and tensions with Britain.",
                    "learn": [
                        {"type": "p", "text": "By the 1700s, thirteen British colonies thrived along the Atlantic coast. Colonists farmed, traded, and built towns. Britain taxed the colonies and controlled trade, causing growing anger."},
                        {"type": "list", "items": [
                            "New England colonies: shipbuilding, fishing, small farms.",
                            "Middle colonies: grain, trade, diverse populations.",
                            "Southern colonies: tobacco, rice, plantation economy.",
                            "Taxation without representation angered colonists.",
                        ]},
                        {"type": "activity", "title": "Colonial newspaper", "text": "Write a short newspaper headline and article from a colonist's point of view about a British tax."},
                    ],
                    "check": {
                        "prompt": "Show what you know about Colonial America.",
                        "questions": [
                            {"q": "Which phrase describes the colonists' complaint about British taxes?", "options": ["taxation without representation", "no taxation at all", "freedom of speech"], "answer": "taxation without representation", "explain": "Colonists wanted representatives in Parliament to vote on taxes."},
                            {"q": "The southern colonies' economy relied heavily on…", "options": ["tobacco and rice plantations", "shipbuilding", "fur trading"], "answer": "tobacco and rice plantations", "explain": "The warm southern climate supported labor-intensive cash crops."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "founding-documents-and-civics",
            "title": "Founding Documents and Civics",
            "summary": "Declaration of Independence, Constitution, and government.",
            "order": 2,
            "lessons": [
                {
                    "slug": "declaration-of-independence",
                    "title": "The Declaration of Independence",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Purposes, authors, and key ideas.",
                    "learn": [
                        {"type": "p", "text": "On July 4, 1776, the colonies declared independence from Britain. Thomas Jefferson wrote most of the Declaration. It states that all people have unalienable rights: life, liberty, and the pursuit of happiness."},
                        {"type": "list", "items": [
                            "Purpose: to explain why the colonies were leaving Britain.",
                            "Key idea: governments exist to protect people's rights.",
                            "When a government fails, the people can change it.",
                        ]},
                        {"type": "example", "title": "Preamble", "text": "'We hold these truths to be self-evident, that all men are created equal, that they are endowed by their Creator with certain unalienable Rights…'"},
                    ],
                    "check": {
                        "prompt": "Show what you know about the Declaration of Independence.",
                        "questions": [
                            {"q": "When did the colonies declare independence?", "options": ["July 4, 1776", "July 4, 1783", "December 25, 1776"], "answer": "July 4, 1776", "explain": "The Declaration of Independence was adopted on July 4, 1776."},
                            {"q": "Which document declared independence?", "options": ["the Declaration of Independence", "the Constitution", "the Bill of Rights"], "answer": "the Declaration of Independence", "explain": "This document announced that the colonies were free from Britain."},
                        ],
                    },
                },
                {
                    "slug": "constitution-and-branches",
                    "title": "The Constitution and Three Branches",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Structure, separation of powers, and checks and balances.",
                    "learn": [
                        {"type": "p", "text": "The Constitution is the supreme law of the United States. Written in 1787, it created three branches of government so that no single branch could become too powerful."},
                        {"type": "list", "items": [
                            "Legislative (Congress): makes laws.",
                            "Executive (President): carries out laws.",
                            "Judicial (Courts): interprets laws.",
                            "Checks and balances let each branch limit the others.",
                        ]},
                        {"type": "example", "title": "Checks and balances", "text": "The President can veto a law. Congress can override a veto with a two-thirds vote. The courts can declare a law unconstitutional."},
                    ],
                    "check": {
                        "prompt": "Show what you know about the Constitution and branches.",
                        "questions": [
                            {"q": "Which branch makes laws?", "options": ["Legislative", "Executive", "Judicial"], "answer": "Legislative", "explain": "Congress (the legislative branch) makes laws."},
                            {"q": "Which branch can declare a law unconstitutional?", "options": ["Judicial", "Legislative", "Executive"], "answer": "Judicial", "explain": "The Supreme Court and other federal courts interpret laws."},
                        ],
                    },
                },
            ],
        },
    ],
}
