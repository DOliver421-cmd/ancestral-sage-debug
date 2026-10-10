"""K–2 Early Social Studies: Oral Histories, Anansi, and Ancestral Foundations (published).

Foundational social studies built on oral tradition rather than generic
"family and helpers" units. Students meet West African storytelling
(Anansi tales, the Sundiata epic), the role of elders and griots, community
leadership, and intergenerational respect — the way many African societies
have passed law, history, and ethics for centuries before writing.
"""

ORAL_HISTORIES_ANCESTRAL_FOUNDATIONS = {
    "slug": "oral-histories-ancestral-foundations",
    "title": "Oral Histories, Anansi, and Ancestral Foundations",
    "summary": "Where history comes from storytelling: Anansi tales, the Sundiata epic, griots, elders, and how a community remembers itself.",
    "description": (
        "This early social studies course replaces generic 'helpers' units with the "
        "knowledge traditions African societies actually built. Students learn that for "
        "most of human history, history, law, and ethics were carried in speech and song "
        "— memorized by specialists and performed in community. They meet the Anansi "
        "spider tales of the Akan and Caribbean, the Sundiata epic of the Mande, the "
        "griots of West Africa, the Namibian |Gui//Gowa of the Ju|'hoansi, and the "
        "protocols of respect that hold a family and village together. The through-line: "
        "a community that remembers its elders keeps its future."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "foundations",
    "tracks": ["foundations"],
    "grades": ["K", "1", "2"],
    "grade_label": "Grades K–2",
    "status": "published",
    "audience": "Early learners beginning history, geography, and community studies.",
    "est_hours": 14,
    "passing_score": 80,
    "learning_objectives": [
        "Explain what an oral tradition is and how history is carried without writing.",
        "Identify oral storytelling from at least three African regions.",
        "Retell an Anansi tale and state its lesson.",
        "Describe the Sundiata story and what it teaches about leadership.",
        "Explain a griot's (jeli's) role in West African communities.",
        "Identify how elders carry knowledge in families and villages.",
        "Practice respectful listening and questioning as a way of learning.",
    ],
    "units": [
        {
            "slug": "stories-carry-history",
            "title": "Stories Carry History",
            "summary": "How speech and song remember a people.",
            "order": 1,
            "lessons": [
                {
                    "slug": "oral-tradition",
                    "title": "What Is an Oral Tradition?",
                    "order": 1,
                    "minutes": 15,
                    "summary": "History carried in memory before it was carried on paper.",
                    "learn": [
                        {"type": "p", "text": "Long before people wrote things down, they remembered them by telling them. A grandmother teaches a child the name of the river where the family came from. A singer performs a story so the village knows who its founders were. This is oral tradition: knowledge kept alive in words, songs, and performance."},
                        {"type": "list", "items": [
                            "Oral = spoken aloud, not written.",
                            "A tradition is something passed down through many generations.",
                            "Oral tradition keeps history, law, family names, music, and science alive.",
                        ]},
                        {"type": "example", "title": "Think about it", "text": "Your family already uses oral tradition. Recipes taught by watching, family stories told at holidays, lullabies a parent hums — all of these are knowledge carried without writing."},
                        {"type": "tip", "text": "When people wrote that Africans 'had no history' because they had no writing, they were wrong: the history existed — it was performed and remembered instead of filed."},
                    ],
                    "check": {
                        "prompt": "Check what you know about oral tradition.",
                        "questions": [
                            {"q": "Oral tradition is knowledge that is…", "options": ["carried by speech, song, and memory", "written in a book", "found only on the internet"], "answer": "carried by speech, song, and memory", "explain": "Oral tradition passes knowledge down by telling and performing it, not by writing it."},
                            {"q": "Why is it wrong to say a people 'had no history' because they did not write?", "options": ["Their history was carried in stories and memory", "Because everyone wrote in Africa", "Because written history is never true"], "answer": "Their history was carried in stories and memory", "explain": "History kept and performed in oral tradition is still history."},
                        ],
                    },
                },
                {
                    "slug": "anansi-tales",
                    "title": "Anansi: The Spider Who Teaches",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Akan spider stories that crossed the ocean and became a whole world's trickster tales.",
                    "learn": [
                        {"type": "p", "text": "Anansi (also Anancy, Aunt Nancy, or Compair Lapin in the French Caribbean) is a small, clever spider who wins by thinking. The stories come from the Akan people of Ghana. When Africans were carried across the Atlantic, they carried Anansi with them — and today children in Jamaica, Trinidad, Suriname, Curaçao, and the American South still know him."},
                        {"type": "list", "items": [
                            "Anansi is a culture hero: small, clever, funny, and sometimes foolish.",
                            "His stories teach that a small person can solve a big problem with wit.",
                            "Anansi tales travelled on ships of survival and were retold on every island where Africans were taken.",
                        ]},
                        {"type": "example", "title": "A retelling", "text": "Anansi wanted all the stories in the world for himself, so the sky god gave him three impossible tasks. He used his web, his cleverness, and help from his family — and every story we tell today is called a 'spider story' in his honor."},
                        {"type": "activity", "title": "Tell it back", "text": "Retell an Anansi story in your own words to someone at home. Then answer: what mistake did Anansi make, and what did he learn?"},
                    ],
                    "check": {
                        "prompt": "Check what you know about Anansi stories.",
                        "questions": [
                            {"q": "Anansi comes originally from the stories of which people?", "options": ["The Akan of Ghana", "The Norse of Scandinavia", "The Maya of Mexico"], "answer": "The Akan of Ghana", "explain": "Anansi is an Akan spider-trickster whose tales then spread through the African diaspora."},
                            {"q": "What do Anansi stories teach?", "options": ["Cleverness can beat raw size and strength", "Stories should never be told", "Only kings matter in a village"], "answer": "Cleverness can beat raw size and strength", "explain": "Anansi is small but wins by thinking, which is why his tales travelled so far."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "elders-and-griots",
            "title": "Griots and Elders: The People Who Remember",
            "summary": "Professionals of memory and the elders who hold a family together.",
            "order": 2,
            "lessons": [
                {
                    "slug": "sundiata-lion-of-mali",
                    "title": "Sundiata: The Lion of Mali",
                    "order": 3,
                    "minutes": 18,
                    "summary": "The Mande epic that remembers the founding of an empire.",
                    "learn": [
                        {"type": "p", "text": "Sundiata Keita was the son of the king of Niani who, belittled and exiled, grew into the leader who unified the Mande kingdoms into the empire of Mali around 1235. His story is not written in one book — it is performed by griots (jeliw) who have kept it alive for centuries, accompanied by the kora, a twenty-one-string harp-lute."},
                        {"type": "list", "items": [
                            "The epic is performed, not read: each griot makes it live for their audience.",
                            "It names villages, clans, and ancestors, so listeners learn their family history inside the story.",
                            "Every Mande person today is said to belong to a family named in the Sundiata.",
                        ]},
                        {"type": "example", "title": "Griot families", "text": "Griot families train from childhood for years in genealogy, praise songs, and the kora. They are living libraries: ask a jeli your family line and they can sing it back to you."},
                        {"type": "activity", "title": "Make a timeline of a hero", "text": "Draw five boxes for Sundiata's story: child, exile, learning, return as leader, founding of Mali. Put one word in each box."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the Sundiata story.",
                        "questions": [
                            {"q": "Who performs the Sundiata epic?", "options": ["Griots (jeliw)", "Novelists", "Cartographers"], "answer": "Griots (jeliw)", "explain": "Griots are trained memory-keepers who perform the epic with music."},
                            {"q": "Why is the Sundiata important to Mande families today?", "options": ["It names the clans and ancestors each family belongs to", "It is a math textbook", "It is a map of West Africa"], "answer": "It names the clans and ancestors each family belongs to", "explain": "The epic links every Mande lineage to the founding of the nation."},
                        ],
                    },
                },
                {
                    "slug": "respect-and-community",
                    "title": "Respect, Elders, and Working Together",
                    "order": 4,
                    "minutes": 15,
                    "summary": "The rules of relationship that make a community strong.",
                    "learn": [
                        {"type": "p", "text": "In many African societies there are everyday courtesies that keep a household or village in balance. Ubuntu is a Southern African idea often translated as 'I am because we are' — a person's humanity is found in relation to other people. Harambee in Swahili means 'all pull together.' These are not decorations; they are how work gets done and how conflicts end."},
                        {"type": "list", "items": [
                            "Greet elders first; use respectful titles and gestures appropriate to your family.",
                            "Serve and be served: meals, chores, and healing are shared, not individual.",
                            "Ubuntu: my wellbeing is tied to the wellbeing of the people around me.",
                            "Harambee: communities raise a barn, a school, or a well by pulling together.",
                        ]},
                        {"type": "example", "title": "A real practice", "text": "In many villages across the continent, neighbours plant and harvest one another's fields together on fixed days. Everyone's crop comes in, and no family goes hungry because everyone was working on all the fields, not just their own."},
                        {"type": "activity", "title": "Circle of respect", "text": "Write one thing you learned from an elder this year, and one way you could help a neighbour. Share it at dinner."},
                    ],
                    "check": {
                        "prompt": "Check what you know about community values.",
                        "questions": [
                            {"q": "Ubuntu is best described as…", "options": ["'I am because we are'", "'every person for themselves'", "'follow written rules only'"], "answer": "'I am because we are'", "explain": "Ubuntu makes humanity something shared: our wellbeing depends on each other."},
                            {"q": "Harambee teaches that a community…", "options": ["accomplishes big work by pulling together", "should keep work private", "must wait for outside help"], "answer": "accomplishes big work by pulling together", "explain": "Harambee means 'all pull together' — shared labour gets large jobs done."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "stories-are-ours",
            "title": "Stories Are Ours: Listening Well",
            "summary": "How to listen, question, and thank a storyteller.",
            "order": 3,
            "lessons": [
                {
                    "slug": "riding-the-story",
                    "title": "How to Listen to a Story",
                    "order": 5,
                    "minutes": 15,
                    "summary": "Listening is a skill, and it is how oral cultures learn.",
                    "learn": [
                        {"type": "p", "text": "In oral cultures, learning happens by listening, then repeating, then asking. A griot expects interruptions — questions are a compliment, not a nuisance. Good listeners keep the pattern of the story, not every single word, so they can carry it to someone else."},
                        {"type": "list", "items": [
                            "Listen for the shape: who is the hero, what is the problem, what is the lesson?",
                            "Repeat it in your own words — that is how it becomes yours.",
                            "Ask afterwards: what does this teach us?",
                            "Thank the teller; in oral cultures telling a story is a gift of labour.",
                        ]},
                        {"type": "tip", "text": "Griots improvise verses for the people in the room. The story changes when your family is in the room — and that is the point: the tradition stays alive because it responds to its listeners."},
                    ],
                    "check": {
                        "prompt": "Check your thinking about listening.",
                        "questions": [
                            {"q": "A good listener of oral stories listens for…", "options": ["the shape of the story and its lesson", "every single word", "nothing at all"], "answer": "the shape of the story and its lesson", "explain": "Carrying the pattern lets you retell the story accurately to someone else."},
                            {"q": "In oral cultures, asking questions during a story is…", "options": ["a compliment that keeps the story alive", "a form of rudeness", "not allowed"], "answer": "a compliment that keeps the story alive", "explain": "Traditions respond to listeners; questions show engagement."},
                        ],
                    },
                },
                {
                    "slug": "our-family-history",
                    "title": "My Family's Living History",
                    "order": 6,
                    "minutes": 20,
                    "summary": "Collect the oral history of your own household.",
                    "learn": [
                        {"type": "p", "text": "You are already part of an oral tradition. Your family knows things that are written nowhere: where your grandparents grew up, why the family moved, what songs they sing, what disaster they survived. An oral history interview is how you record it before it is lost."},
                        {"type": "list", "items": [
                            "Prepare three open questions: Where did you grow up? What work did you do? Who taught you the most?",
                            "Ask permission, and record with a phone if your elder agrees.",
                            "Write down names, places, and dates exactly as they are said.",
                            "Keep the recording and share it with the family.",
                        ]},
                        {"type": "example", "title": "Open question", "text": "'Tell me about the year you moved' gets a story. 'Did you move in 1984?' gets a yes or no. Open questions are the work of the oral historian."},
                        {"type": "activity", "title": "Interview an elder", "text": "Interview a parent, grandparent, or family elder with three open questions. Write one paragraph from the answers and add it to your portfolio."},
                    ],
                    "check": {
                        "prompt": "Check what you know about oral history.",
                        "questions": [
                            {"q": "An open question is one that…", "options": ["asks for a story rather than yes or no", "is always about dates", "has no answer"], "answer": "asks for a story rather than yes or no", "explain":"Open questions let the teller decide what matters."},
                            {"q": "When recording a family interview you should always…", "options": ["ask permission and keep names and places exactly", "record secretly", "translate everything into English"], "answer": "ask permission and keep names and places exactly", "explain": "Consent and accurate detail make the recording usable and respectful."},
                        ],
                    },
                },
            ],
        },
    ],
}
