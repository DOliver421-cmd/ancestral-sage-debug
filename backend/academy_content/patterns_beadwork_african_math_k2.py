"""K–2 Early Math: Patterns, Beadwork, and Counting in African Art (published).

Counting, place value, and geometry taught through African mathematical
traditions: Yoruba base-20 counting games (Ayo/Oware and counting systems),
Kente and Bogolanfini textile patterns, Adinkra symbols, Bamum numerals,
and the fractal architecture of the Ba'ilé and of southern African villages.
Mathematics is presented as a cultural achievement, not a blank slate.
"""

PATTERNS_BEADWORK_AFRICAN_MATH_K2 = {
    "slug": "patterns-beadwork-african-math-k2",
    "title": "Patterns, Beadwork, and Counting in African Art",
    "summary": "Count, group, and find shapes in Kente cloth, Yoruba counting games, and African architecture.",
    "description": (
        "Early mathematics is taught here through African systems that are thousands "
        "of years old. The Yoruba count in base twenty, not tens. Weavers in Ghana, "
        "Mali, and Cameroon build geometric patterns into cloth that carry proverbs. "
        "Mappers of Ba'ilé villages draw self-similar geometry centuries before "
        "fractals were named. Students count, group, sort, and measure — and see "
        "African mathematics as the source."),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "foundations",
    "tracks": ["foundations"],
    "grades": ["K", "1", "2"],
    "grade_label": "Grades K–2",
    "status": "published",
    "audience": "Early learners counting, grouping, and identifying patterns and shapes.",
    "est_hours": 14,
    "passing_score": 80,
    "learning_objectives": [
        "Count to 20 by ones and to 100 by tens.",
        "Explain how a base-20 (vigesimal) counting system works and contrast it with base-10.",
        "Copy, extend, and create repeating patterns.",
        "Sort objects by two attributes at once (attribute grids).",
        "Identify squares, triangles, and circles in African textile and architectural motifs.",
        "Use nonstandard and standard units to measure a length.",
    ],
    "units": [
        {
            "slug": "counting-yoruba",
            "title": "Counting: The Yoruba Way",
            "summary": "A base-20 number system from West Africa.",
            "order": 1,
            "lessons": [
                {
                    "slug": "base-twenty",
                    "title": "Why Twenty? The Yoruba Count",
                    "order": 1,
                    "minutes": 15,
                    "summary": "Counting on fingers and toes.",
                    "learn": [
                        {"type": "p", "text": "In English we count in base 10 — likely because we have ten fingers. The Yoruba people of Nigeria and Benin count in base 20: all ten fingers and all ten toes. Yoruba arithmetic is vigesimal, and it is one of the most sophisticated counting systems on the continent."},
                        {"type": "list", "items": [
                            "Base 10 groups by tens: 10 ones make one ten.",
                            "Base 20 groups by twenties: 20 ones make one score.",
                            "Yes, twelve is 'a dozen' in English — base-20 counting survives in English too, as the word score (an old tally unit).",
                        ]},
                        {"type": "example", "title": "Try it", "text": "In Yoruba, the numbers from 'ogun' (twenty) to 'ogoji' (forty) build on twenty the way English builds on tens. Count your fingers and toes to see why twenty is natural."},
                        {"type": "tip", "text": "The French 'quatre-vingts' (four twenties) is also vigesimal. Base-20 counting is really an African contribution used around the world."},
                    ],
                    "check": {
                        "prompt": "Check what you know about number systems.",
                        "questions": [
                            {"q": "A base-20 counting system groups by…", "options": ["twenties", "tens", "fifties"], "answer": "twenties", "explain": "Vigesimal systems group by twenty rather than ten."},
                            {"q": "The Yoruba count in base 20 because…", "options": ["they count fingers and toes together", "they have twenty fingers", "there are no other numbers"], "answer": "they count fingers and toes together", "explain": "Ten fingers plus ten toes gives twenty, a natural grouping."},
                        ],
                    },
                },
                {
                    "slug": "ayo-ware-game",
                    "title": "Ayo (Oware): A Counting Game",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Sowing seeds by the rule of two — a math game with African roots.",
                    "learn": [
                        {"type": "p", "text": "Ayo, called Oware in Ghana and Warri elsewhere, is played on a board with two rows of six cups and forty-eight seeds. Players 'sow' seeds one at a time around the board, capturing by rule. Children learn even and odd numbers, and count without being told they are doing arithmetic."},
                        {"type": "list", "items": [
                            "Forty-eight seeds across twelve cups — an even number shared into equal parts.",
                            "Six cups per side, twelve in all: groups, halves, and quarters.",
                            "Sowing one seed at a time is counting; planning several moves ahead is algebra.",
                        ]},
                        {"type": "example", "title": "The rule", "text": "If you drop seed number two on a cup and it holds exactly two or three seeds, you capture them. The rules of capture force you to count backward — careful counting becomes a winning strategy."},
                        {"type": "activity", "title": "Play a round", "text": "Make an Ayo board out of an egg carton and buttons. Play three rounds with a partner and count the seeds captured each turn."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the Ayo game.",
                        "questions": [
                            {"q": "Ayoand Oware are the same kind of game as…", "options": ["a seed-sowing math game", "a board game bought in a shop", "a card game"], "answer": "a seed-sowing math game", "explain": "It is an African strategy game played by sowing seeds around a board."},
                            {"q": "Playing Ayo trains which skill?", "options": ["careful counting and planning", "spelling", "singing"], "answer": "careful counting and planning", "explain": "You must count seeds and plan several moves ahead."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "patterns-in-cloth",
            "title": "Patterns in Cloth",
            "summary": "Geometry woven, dyed, and stamped.",
            "order": 2,
            "lessons": [
                {
                    "slug": "kente-bogolanfini",
                    "title": "Kente, Bogolanfini, and Adinkra",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Repeating geometric patterns with meanings.",
                    "learn": [
                        {"type": "p", "text": "Kente is handwoven cloth from Ghana, originally silk and cotton, with named strip patterns each carrying a proverb or a history. Bogolanfini (mudcloth) is made in Mali by painting fermented mud over handspun cloth — repeating geometry in indigo and brown. Adinkra symbols are stamped from calabash, each one standing for an idea such as wisdom or endurance."},
                        {"type": "list", "items": [
                            "Kente strips repeat in a strict sequence, like a colour-coded number pattern.",
                            "Adinkra symbols each carry a proverb — they are writing in the form of pictures.",
                            "Bogolanfini patterns are dyed and mud-painted; the negative space is measured as carefully as the lines.",
                        ]},
                        {"type": "example", "title": "Read the pattern", "text": "Blue-yellow-blue-yellow is an AB pattern. Square-triangle-square-triangle is AB too. Look at a Kente strip: can you find an AAB or ABB pattern in the weaving?"},
                        {"type": "activity", "title": "Weave a pattern", "text": "Weave strips of paper (over-under, over-under). Choose a repeating colour rule and write the pattern rule you used — for example, AAB."},
                    ],
                    "check": {
                        "prompt": "Check what you know about cloth patterns.",
                        "questions": [
                            {"q": "Kente cloth is made by…", "options": ["weaving strips in a repeating pattern", "printing with a machine", "carving from stone"], "answer": "weaving strips in a repeating pattern", "explain": "It is handwoven in strips whose sequences carry meaning."},
                            {"q": "An ABAB pattern of square-triangle-square-triangle means…", "options": ["the same two shapes alternate", "the shapes are random", "only squares are used"], "answer": "the same two shapes alternate", "explain": "ABAB alternates two elements: square, triangle, square, triangle."},
                        ],
                    },
                },
                {
                    "slug": "shapes-in-buildings",
                    "title": "Geometry in African Architecture",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Circles, squares, and triangles people actually live in.",
                    "learn": [
                        {"type": "p", "text": "African builders have used circles, rectangles, and triangles for centuries. Rondavels in southern Africa, the conical roofs of Bamileke and Dogon homes, the great dome of the Great Mosque of Djenne in Mali, and the adobe towers of the Swahili coast all use geometry for strength and shade. Builders arrange shapes in grids that a child can see."},
                        {"type": "list", "items": [
                            "Circle: the rondavel and grain store, strongest shape against wind.",
                            "Triangle: the cone of a roof, which sheds rain.",
                            "Rectangle: courtyard walls of Djenne laid in rows.",
                        ]},
                        {"type": "example", "title": "Measure it", "text": "Lay your foot heel-to-toe across a room and count the steps. Then compare with a friend's steps. The room is the same; only the unit changed — which is exactly how ancient builders compared sizes without rulers."},
                        {"type": "tip", "text": "Ba'ilé villages in Côte d'Ivoire are drawn in fractal patterns — each hut looks like a copy of the whole village. That is self-similarity, a geometry Europeans named fractal only in the 1970s."},
                        {"type": "activity", "title": "Shape hunt", "text": "Walk your home or street and find three examples each of circles, rectangles, and triangles. Draw and label them."},
                    ],
                    "check": {
                        "prompt": "Check what you know about shapes.",
                        "questions": [
                            {"q": "Which shape is strongest against wind and is used for rondavels?", "options": ["circle", "square", "triangle"], "answer": "circle", "explain": "Circular walls shed pressure from wind with no corners to break."},
                            {"q": "A fractal pattern is one where…", "options": ["each small part looks like the whole", "there is no repetition", "only circles are used"], "answer": "each small part looks like the whole", "explain": "Fractals are self-similar — the same shape at every scale."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "measure-and-sort",
            "title": "Measure and Sort",
            "summary": "Grouping, comparing, and measuring with African models.",
            "order": 3,
            "lessons": [
                {
                    "slug": "sorting-like-a-merchant",
                    "title": "Sorting Like a Merchant",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Two attributes at once: colour and shape.",
                    "learn": [
                        {"type": "p", "text": "Market traders in Kano, Kumasi, and Lagos for centuries have sorted beads, kola, and cloth by two features at once — colour and shape, or size and use. Sorting by two attributes builds the same thinking that a spreadsheet or a database uses today."},
                        {"type": "list", "items": [
                            "One attribute at a time: all the blue together, all the red together.",
                            "Two attributes at once: blue squares, blue triangles, red squares, red triangles.",
                            "A grid of four boxes shows every combination — a sorting table.",
                        ]},
                        {"type": "activity", "title": "Make a two-way sort", "text": "Collect eight buttons or seeds. Sort by size (big/small) and colour (dark/light) into four groups. Draw the grid and count each box."},
                    ],
                    "check": {
                        "prompt": "Check what you know about sorting.",
                        "questions": [
                            {"q": "Sorting by two attributes at once creates…", "options": ["groups for every combination", "only one pile", "no piles"], "answer": "groups for every combination", "explain": "Two attributes make four groups: each value of one combined with each value of the other."},
                            {"q": "Sorting objects is useful because it…", "options": ["makes comparing and counting easier", "hides the objects", "is only for counting"], "answer": "makes comparing and counting easier", "explain": "Sorted groups can be counted and compared quickly."},
                        ],
                    },
                },
                {
                    "slug": "measuring-our-world",
                    "title": "Measuring Our World",
                    "order": 6,
                    "minutes": 15,
                    "summary": "Longer, shorter, heavier — and why a standard unit helps.",
                    "learn": [
                        {"type": "p", "text": "Before standard units, traders needed to compare quantities fairly, so they used shells, cloth lengths, and weights. SALT WAS ONCE SANDS BY MEASURE — a stick of measure marked in inches. Standard units make a trade fair in every market."},
                        {"type": "list", "items": [
                            "Measure a table with your hand: count hand-spans from end to end.",
                            "Compare with a friend: smaller hand, more spans — the same table.",
                            "Standard units like the inch and the centimetre make the count agree for everyone.",
                        ]},
                        {"type": "example", "title": "Cowrie currency", "text": "Cowrie shells became money across the Indian Ocean and were used to count, weigh, and trade wealth in West Africa. Money began as a counting problem."},
                        {"type": "activity", "title": "Measure three things", "text": "Measure three objects at home with a hand-span and then with a ruler. Write both numbers for each and explain the difference."},
                    ],
                    "check": {
                        "prompt": "Check what you know about measuring.",
                        "questions": [
                            {"q": "Measuring the same table with two different hands gives…", "options": ["different counts, same length", "the same count", "no numbers"], "answer": "different counts, same length", "explain": "Smaller hands need more spans; the object did not change."},
                            {"q": "Standard units help because…", "options": ["everyone gets the same answer", "they are shorter", "they are mysterious"], "answer": "everyone gets the same answer", "explain": "A shared unit makes measurements comparable in every market and classroom."},
                        ],
                    },
                },
            ],
        },
    ],
}
