"""Creative Track: Visual Arts of the Black Diaspora (published).

Artist-track art history and studio practice from Saharan rock art to
African American studio art to contemporary community murals. Students
study works, techniques, and the political conditions in which the art
was made, and produce work in a chosen tradition.
"""

VISUAL_ARTS_BLACK_DIASPORA = {
    "slug": "visual-arts-black-diaspora",
    "title": "Visual Arts of the Black Diaspora: From Cave Art to Modern Murals",
    "summary": "Saharan rock art, Benin bronzes, Harlem Renaissance painting, and community muralism.",
    "description": (
        "This artist-track course is art history and studio practice centered on the "
        "Black diaspora. Students analyze Saharan rock art at Tassili n'Ajjer, the "
        "lost-wax bronze casting of Benin, Yoruba and Igbo sculpture, the photography "
        "and painting of the Harlem Renaissance, and contemporary Afro-diasporic murals "
        "and public art. They also study the market and museum histories that excluded "
        "the work for a century, and produce a studio piece in a tradition they choose."
    ),
    "subject": "art",
    "subject_label": "Arts",
    "track": "artist",
    "tracks": ["artist", "scholar"],
    "grades": ["9", "10", "11", "12"],
    "grade_label": "Grades 9–12",
    "status": "published",
    "audience": "Students in visual arts, art history, and studio programs.",
    "est_hours": 26,
    "passing_score": 80,
    "learning_objectives": [
        "Describe Saharan rock art and what it records.",
        "Explain the lost-wax process used for Benin bronzes.",
        "Analyze Yoruba and Igbo sculptural conventions.",
        "Describe Harlem Renaissance visual art and its working conditions.",
        "Analyze contemporary diasporic and public art.",
        "Evaluate how museums and markets have treated diaspora art.",
        "Produce a studio work in a chosen tradition.",
    ],
    "units": [
        {
            "slug": "ancient-to-royal",
            "title": "Rock Art to Royal Bronze",
            "summary": "Where the record begins and how it was made.",
            "order": 1,
            "lessons": [
                {
                    "slug": "saharan-rock-art",
                    "title": "Saharan Rock Art",
                    "order": 1,
                    "minutes": 24,
                    "summary": "A gallery of 12,000 years on the desert walls.",
                    "learn": [
                        {"type": "p", "text": "Tassili n'Ajjer, in today's Algeria, holds thousands of engraved and painted images on sandstone, dating from roughly 8000 BCE to the present. The art records cattle, hippopotamuses, giraffes, ritual dance, and daily life — and it records a wetter Sahara, a green plain before desertification, which is why these images are also climate evidence."},
                        {"type": "list", "items": [
                            "Paintings made from ochres, kaolin, and charcoal in organic binders.",
                            "Rock varnish: manganese and iron coating that preserves images.",
                            "A record of a greener Sahara with its animal communities.",
                        ]},
                        {"type": "example", "title": "Style analysis", "text": "The 'Marsoulian' heads and 'Round Heads' show stylized figures with a consistent proportion system — evidence of a local training and convention, not naïve drawing."},
                        {"type": "activity", "title": "Copy and compare", "text": "Draw a simplified copy of one Tassili figure. Then write one sentence on what the pose suggests about the person's role."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Saharan rock art.",
                        "questions": [
                            {"q": "Tassili n'Ajjer rock art shows animals that indicate…", "options": ["the Sahara was much wetter", "the Sahara was always desert", "a polar climate"], "answer": "the Sahara was much wetter", "explain": "Hippopotamuses and cattle require grasslands and water."},
                            {"q": "Saharan paintings used…", "options": ["ochres, kaolin, and charcoal", "spray cans", "ink printing"], "answer": "ochres, kaolin, and charcoal", "explain": "The pigments are mineral and charcoal, bound organically."},
                        ],
                    },
                },
                {
                    "slug": "benin-bronzes",
                    "title": "Benin Bronzes and Lost-Wax Casting",
                    "order": 2,
                    "minutes": 24,
                    "summary": "A royal art with a procedure still used today.",
                    "learn": [
                        {"type": "p", "text": "Benin City, in today's Nigeria, produced thousands of brass and bronze plaques and portraits beginning in the 1500s, cast for the royal palace using the lost-wax technique. The plaques record court life, warriors, and ceremonies, and reading them as documents is part of art history. British forces looted the palace in 1897, and the bronzes scattered to museums around the world — a history of theft now being reparatively addressed."},
                        {"type": "list", "items": [
                            "Lost-wax: model, mold, melt the wax out, pour the bronze, break the mold.",
                            "Guild system: royal guilds controlled who could cast for the court.",
                            "1897 Punitive Expedition: the loot and its continuing restitution debates.",
                        ]},
                        {"type": "example", "title": "Documentary value", "text": "The plaques show rank, dress, and regalia with a level of detail that makes them primary sources about Kingdom of Benin politics."},
                        {"type": "activity", "title": "Model the process", "text": "Make a small lost-wax model in wax and describe each step of the casting process that would preserve it in metal."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Benin bronzes.",
                        "questions": [
                            {"q": "Benin bronzes were cast by…", "options": ["the lost-wax process", "carving from a block", "3D printing"], "answer": "the lost-wax process", "explain": "Wax models are lost in the mold, then bronze poured in."},
                            {"q": "The bronzes became scattered because of…", "options": ["the 1897 British Punitive Expedition", "a flood", "an earthquake"], "answer": "the 1897 British Punitive Expedition", "explain": "Colonial loot dispersed the works across world museums."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "renaissance-and-modern",
            "title": "Harlem Renaissance to Contemporary",
            "summary": "Portraits, photography, and the modern gallery and the street.",
            "order": 2,
            "lessons": [
                {
                    "slug": "harlem-renaissance-visual",
                    "title": "Harlem Renaissance Visual Art",
                    "order": 3,
                    "minutes": 24,
                    "summary": "Self-portraiture as a political act.",
                    "learn": [
                        {"type": "p", "text": "Harlem Renaissance painters and sculptors — Aaron Douglas, Meta Vaux Warrick Fuller, Palmer Hayden, Augusta Savage, Richmond Barthé, Archibald Motley, and William H. Johnson — depicted Black life with dignity and everyday reality. Augusta Savage's studio was a school whose students included Jacob Lawrence; Motley painted Bronzeville at night with the same attention to color a European painter gave to Paris."},
                        {"type": "list", "items": [
                            "Aaron Douglas: silhouette figures, Art Deco geometry, murals.",
                            "Augusta Savage: sculpture, mentorship, and public art advocacy.",
                            "Archibald Motley: urban night scenes of Chicago's Bronzeville.",
                        ]},
                        {"type": "example", "title": "The condition", "text": "These artists worked with limited patronage and facing a segregated art market; each made self-representation a deliberate artistic and political program."},
                        {"type": "activity", "title": "Analyze", "text": "Choose one work. Write a 200-word analysis: subject, composition, color strategy, and what it says about who deserves to be seen."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Harlem Renaissance art.",
                        "questions": [
                            {"q": "Augusta Savage is known for…", "options": ["sculpture and mentoring younger artists", "abstract expressionism only", "inventing photography"], "answer": "sculpture and mentoring younger artists", "explain": "Her studio taught a generation of Black artists."},
                            {"q": "A recurring theme in Harlem Renaissance art is…", "options": ["dignified self-representation of Black life", "landscape painting only", "court portraiture"], "answer": "dignified self-representation of Black life", "explain": "Artists depicted Black subjects with agency and everyday reality."},
                        ],
                    },
                },
                {
                    "slug": "contemporary-public-art",
                    "title": "Contemporary Diaspora and Public Art",
                    "order": 4,
                    "minutes": 24,
                    "summary": "Murals as a people's gallery.",
                    "learn": [
                        {"type": "p", "text": "From Basquiat and Jean-Michel's neo-expressionism to Kehinde Wiley's monumental portraits, from Mickalene Thomas's rhinestone surfaces to Kerry James Marshall's crowded interiority, Black artists have shaped contemporary art. In parallel, public art programs and mural movements from Chicago to Lagos to Philadelphia have put art on walls owned by the people who look at them."},
                        {"type": "list", "items": [
                            "Muralism: community-chosen subjects, public walls, and collective authorship.",
                            "The market: contemporary Black artists are now recognized by major institutions, after a century of exclusion from them.",
                            "Restitution: museums returning looted African works is an ongoing legal and political project.",
                        ]},
                        {"type": "example", "title": "A working method", "text": "Public artists work with communities in design meetings; the art is negotiated, not delivered. That process is part of the piece."},
                        {"type": "activity", "title": "Propose a mural", "text": "Propose a mural for one wall in your community: subject, why that subject, who should be consulted, and what materials."},
                    ],
                    "check": {
                        "prompt": "Check what you know about contemporary diaspora art.",
                        "questions": [
                            {"q": "Community mural projects typically involve…", "options": ["negotiated design with residents", "no community input", "only outdoor advertising"], "answer": "negotiated design with residents", "explain": "The process of choosing the subject is part of the work."},
                            {"q": "Restitution of looted African art concerns…", "options": ["museums returning stolen works", "new museum openings", "print copies"], "answer": "museums returning stolen works", "explain": "It is a legal and political process of returning looted objects."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "studio-practice",
            "title": "Studio Practice",
            "summary": "Study, then make.",
            "order": 3,
            "lessons": [
                {
                    "slug": "tradition-and-technique",
                    "title": "Choose a Tradition and Study Its Technique",
                    "order": 5,
                    "minutes": 26,
                    "summary": "Copying as a research method.",
                    "learn": [
                        {"type": "p", "text": "Studio practice begins with careful study. Copying a composition or a surface teaches what reading cannot: how a Yoruba head is proportioned, how a Benin plaque's relief reads at a distance, how a Harlem mural's silhouette carries across a wall. Copy as research, not imitation — you are learning a procedure, not claiming a style."},
                        {"type": "list", "items": [
                            "Select one tradition from this course.",
                            "Copy three details in a sketchbook and label the procedure used.",
                            "Note where the original artist exercised choice, not just convention.",
                        ]},
                        {"type": "activity", "title": "Copy three details", "text": "Complete three labeled detail copies in your sketchbook, plus a paragraph on what you learned about procedure."},
                    ],
                    "check": {
                        "prompt": "Check what you know about studio study.",
                        "questions": [
                            {"q": "Copying a work in studio practice is useful because…", "options": ["it teaches the procedure behind the surface", "it replaces original work forever", "it is prohibited"], "answer": "it teaches the procedure behind the surface", "explain": "Copying is a research method that reveals technique."},
                            {"q": "When copying for study you should also…", "options": ["note where the artist made a choice", "hide your source", "only measure"], "answer": "note where the artist made a choice", "explain": "Seeing convention and invention is what learning transfers."},
                        ],
                    },
                },
                {
                    "slug": "produce-and-exhibit",
                    "title": "Produce and Exhibit",
                    "order": 6,
                    "minutes": 30,
                    "summary": "Capstone: make the work and place it.",
                    "learn": [
                        {"type": "p", "text": "The capstone is a finished work in the tradition you studied, accompanied by an artist's statement and a plan for its placement. Placement is a real decision: which audience, which wall, and whose permission. Art that is made for a place is a contract with its community."},
                        {"type": "list", "items": [
                            "Make: a finished work, 16 x 20 or larger.",
                            "Write: an artist's statement of 200 words naming your sources.",
                            "Place: propose the site and audience, and document the context.",
                        ]},
                        {"type": "tip", "text": "Photograph the work in place. A portfolio is not the art alone — it is the art plus the decision about who would see it."},
                        {"type": "activity", "title": "Exhibit", "text": "Complete the piece, the statement, and the placement proposal. Present all three to a reviewer."},
                    ],
                    "check": {
                        "prompt": "Check what you know about exhibiting.",
                        "questions": [
                            {"q": "An artist's statement should…", "options": ["name sources and intent", "only describe a price", "avoid all context"], "answer": "name sources and intent", "explain": "The statement links the work to its tradition and purpose."},
                            {"q": "Placement decisions involve…", "options": ["audience, site, and permission", "nothing but personal taste", "only the artist's name"], "answer": "audience, site, and permission", "explain": "Where work goes determines who it serves."},
                        ],
                    },
                },
            ],
        },
    ],
}
