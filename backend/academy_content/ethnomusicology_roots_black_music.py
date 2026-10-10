"""Creative Track: Ethnomusicology — Roots of Black Music (published).

Artist-track music history and practice from West African polyrhythm to
hip-hop. Students learn the rhythmic systems that all of the music shares,
follow the historical arc across continents, and produce a rhythm of their own.
"""

ETHNOMUSICOLOGY_ROOTS_BLACK_MUSIC = {
    "slug": "ethnomusicology-roots-black-music",
    "title": "Ethnomusicology: Roots of Black Music (From Polyrhythms to Hip-Hop)",
    "summary": "West African polyrhythm, spirituals, blues, jazz, reggae, Afrobeat, and hip-hop as one continuing tradition.",
    "description": (
        "This artist-track course traces the world's most widely circulated popular "
        "music tradition to its sources. Students learn polyrhythm as a system, not a "
        "quirk; follow the call-and-response into spirituals, the blues, gospel, and "
        "jazz; then follow the same structures into reggae, Afrobeat, highlife, funk, "
        "and hip-hop. They study the political history in each period, and end by "
        "composing and rehearsing a rhythm of their own using the tools in this course."
    ),
    "subject": "music",
    "subject_label": "Music",
    "track": "artist",
    "tracks": ["artist", "scholar"],
    "grades": ["9", "10", "11", "12"],
    "grade_label": "Grades 9–12",
    "status": "published",
    "audience": "Students in music performance, composition, and production.",
    "est_hours": 24,
    "passing_score": 80,
    "learning_objectives": [
        "Explain what polyrhythm is and how cross-rhythm patterns are built.",
        "Describe how West African rhythm shaped diaspora music.",
        "Explain call and response in work songs, spirituals, blues, and hip-hop.",
        "Trace the development of blues, jazz, gospel, and soul.",
        "Describe reggae, Afrobeat, and highlife in their political contexts.",
        "Analyze hip-hop's four elements and its relation to griot oral tradition.",
        "Compose and rehearse a rhythm using polyrhythm and call-and-response.",
    ],
    "units": [
        {
            "slug": "polyrhythm",
            "title": "Polyrhythm: The Shared System",
            "summary": "Many rhythms, one timeline.",
            "order": 1,
            "lessons": [
                {
                    "slug": "cross-rhythm",
                    "title": "How Polyrhythm Works",
                    "order": 1,
                    "minutes": 24,
                    "summary": "The mathematics of the groove.",
                    "learn": [
                        {"type": "p", "text": "Polyrhythm means several rhythm patterns happening at once, each complete, together. The simplest example is 3 against 2: three beats in the time another performer plays two. West African drumming typically places one pattern in the drumheads, another in the bells, and a bell pattern — a timeline — that repeats the master cell. Every player in the ensemble knows where the pattern's one is, and the groove holds because they agree."},
                        {"type": "list", "items": [
                            "Timeline: a repeating pattern (a bell or shaker) that anchors the rhythm.",
                            "3 against 2: three beats fitting into the space of two.",
                            "Clave patterns: two-bar patterns shared across the diaspora.",
                            "The pattern is a cycle, not a downbeat — it has no beginning.",
                        ]},
                        {"type": "example", "title": "Math of rhythm", "text": "A cycle of 12 eighth-notes can be divided into 3 groups of 4, 4 groups of 3, or 6 pairs — the same length supporting different structures of beat."},
                        {"type": "activity", "title": "Play it", "text": "Play a bell pattern of 3 against 2 with one hand while another percussion or voice holds 2. Repeat for two minutes without stopping."},
                    ],
                    "check": {
                        "prompt": "Check what you know about polyrhythm.",
                        "questions": [
                            {"q": "'Three against two' means…", "options": ["three beats in the space of two", "three instruments in one bar", "three songs at once"], "answer": "three beats in the space of two", "explain": "It is two simultaneous groupings of the same tempo."},
                            {"q": "A timeline in African drumming is…", "options": ["a repeating anchor pattern", "the loudest drum", "a stopwatch"], "answer": "a repeating anchor pattern", "explain": "The timeline keeps all players aligned across the cycle."},
                        ],
                    },
                },
                {
                    "slug": "call-and-response-and-scales",
                    "title": "Call and Response",
                    "order": 2,
                    "minutes": 24,
                    "summary": "The form that lets everyone join.",
                    "learn": [
                        {"type": "p", "text": "Call and response is the second organizing principle. A leader sings or plays; the group answers. It teaches by repetition, it lets performers extend solos without rehearsing the whole song, and it appears in nearly every descendant genre: work songs, spirituals, ring shout, gospel, blues, jazz, rumba, reggae, funk, and hip-hop. The form is also democratic in function — the answer belongs to the crowd."},
                        {"type": "list", "items": [
                            "Leader line, group answer — repeated structure.",
                            "In jazz, call-and-response becomes trading fours and choruses.",
                            "In hip-hop, the emcee's line and the crowd's shout or echo.",
                        ]},
                        {"type": "example", "title": "One form, many genres", "text": "A single measure: 4 calls, 4 answers. That structure carries a field holler and a rap chorus with the same logic."},
                        {"type": "activity", "title": "Arrange it", "text": "Take any school song and arrange it in call-and-response for two groups. Perform it twice."},
                    ],
                    "check": {
                        "prompt": "Check what you know about call and response.",
                        "questions": [
                            {"q": "Call and response is common in the tradition because it…", "options": ["lets the crowd participate and extends solos", "saves sheet music", "removes rhythm"], "answer": "lets the crowd participate and extends solos", "explain": "It is a participatory and an extensible form."},
                            {"q": "In jazz, call and response appears as…", "options": ["trading phrases between players", "silence only", "one long solo"], "answer": "trading phrases between players", "explain": "Trading fours is call and response between musicians."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "the-arc",
            "title": "The Arc: Spirituals to Hip-Hop",
            "summary": "How the tradition crossed the Atlantic and kept developing.",
            "order": 2,
            "lessons": [
                {
                    "slug": "spirituals-blues-jazz",
                    "title": "Spirituals, Blues, and Jazz",
                    "order": 3,
                    "minutes": 26,
                    "summary": "Faith, work, and improvisation.",
                    "learn": [
                        {"type": "p", "text": "From work songs and ring shouts came spirituals, with call-and-response and coded meanings. From field hollers came the blues, built on a twelve-bar form and blue notes. From blues, ragtime, brass bands, and New Orleans syncopation came jazz, which made improvisation and polyrhythm into public art. Gospel added the church organ and the shout. These are not separate inventions: they are one tradition changing as its communities changed."},
                        {"type": "list", "items": [
                            "Spirituals: call-and-response, coded meaning, community singing.",
                            "Blues: twelve-bar form, blue notes, and the AAB lyric.",
                            "Jazz: improvisation, swing feel, and polyrhythmic ensembles.",
                            "Gospel: church roots, call-and-response, and the Hammond organ.",
                        ]},
                        {"type": "example", "title": "The connections", "text": "W.C. Handy, the 'father of the blues', learned the form from a Delta guitar player using a knife as a slide — the tradition recording itself."},
                        {"type": "activity", "title": "Timeline", "text": "Build a timeline of five events in the arc, from the 19th century to the 1950s, naming the community and the innovation."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the musical arc.",
                        "questions": [
                            {"q": "The blues form uses…", "options": ["a twelve-bar structure and blue notes", "a fixed sonata form", "no repetition"], "answer": "a twelve-bar structure and blue notes", "explain": "The twelve-bar blues is the standard harmonic structure."},
                            {"q": "Jazz's major innovation over its sources is…", "options": ["improvisation as composition", "electrical amplification only", "written-out parts"], "answer": "improvisation as composition", "explain": "Jazz formalizes spontaneous invention as the music itself."},
                        ],
                    },
                },
                {
                    "slug": "reggae-afrobeat-hiphop",
                    "title": "Reggae, Afrobeat, and Hip-Hop",
                    "order": 4,
                    "minutes": 26,
                    "summary": "Tradition returning across continents.",
                    "learn": [
                        {"type": "p", "text": "From the Caribbean came reggae, built on one-drop riddims and conscious lyrics in Jamaica in the 1960s. From West Africa came highlife and, in Nigeria, Fela Kuti's Afrobeat, which used long horns sections and political protest. In the Bronx in the 1970s, Jamaican DJ traditions, African polyrhythmic heritage, gospel, funk, and soul converged into hip-hop's four elements — DJing, emceeing, breakdancing, and graffiti — with the emcee's role literally that of a praise poet and a griot."},
                        {"type": "list", "items": [
                            "Reggae: one-drop rhythm, sound-system culture, and conscious lyrics.",
                            "Afrobeat: Fela Kuti's horns, long forms, protest and Shrine.",
                            "Hip-hop: four elements, sampling as a rhythm technique, and the emcee as oral poet.",
                        ]},
                        {"type": "example", "title": "A full circle", "text": "Sampling is a rhythm technique: producers compose new rhythms from old records, exactly as a drummer composes from pattern vocabulary."},
                        {"type": "activity", "title": "Analyze", "text": "Find the call-and-response and timeline pattern in one reggae, Afrobeat, and hip-hop track each. Label them."},
                    ],
                    "check": {
                        "prompt": "Check what you know about reggae, Afrobeat, and hip-hop.",
                        "questions": [
                            {"q": "The 'one-drop' rhythm is associated with…", "options": ["reggae", "blues ballad", "opera"], "answer": "reggae", "explain": "One-drop shifts the emphasis away from the first beat."},
                            {"q": "Hip-hop's four elements include…", "options": ["DJing, emceeing, breakdancing, and graffiti", "only DJing", "only rapping"], "answer": "DJing, emceeing, breakdancing, and graffiti", "explain": "The four elements define the culture, not just the music."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "compose-and-perform",
            "title": "Compose and Perform",
            "summary": "Build a rhythm, write a verse, perform.",
            "order": 3,
            "lessons": [
                {
                    "slug": "build-a-groove",
                    "title": "Build a Groove",
                    "order": 5,
                    "minutes": 26,
                    "summary": "Use the structure you have studied.",
                    "learn": [
                        {"type": "p", "text": "A composition capstone begins with the structure: pick a timeline pattern, then add a cross-rhythm and an answering line. Performances need a fixed cycle so every player knows where the pattern's one lands. Rehearsing the cycle is what makes improvisation possible — freedom inside a shared form."},
                        {"type": "list", "items": [
                            "Pick a timeline (bell or shaker) and repeat it.",
                            "Add one cross-rhythm (3 against 2 or similar).",
                            "Add a call-and-response vocal or instrumental answer.",
                            "Rehearse the cycle until it holds, then add variations.",
                        ]},
                        {"type": "activity", "title": "Rehearse", "text": "Rehearse your groove for 10 minutes, adding one variation every two minutes. Record a one-minute performance."},
                    ],
                    "check": {
                        "prompt": "Check what you know about building a groove.",
                        "questions": [
                            {"q": "A fixed cycle in a groove lets performers…", "options": ["improvise and still hold together", "play anything at random", "stop listening"], "answer": "improvise and still hold together", "explain": "Shared structure is what enables freedom."},
                            {"q": "Cross-rhythm requires that every player…", "options": ["knows where the pattern's one falls", "plays the loudest", "plays only downbeats"], "answer": "knows where the pattern's one falls", "explain": "Alignment is what makes several patterns cohere."},
                        ],
                    },
                },
                {
                    "slug": "verse-and-performance",
                    "title": "Verse and Performance",
                    "order": 6,
                    "minutes": 28,
                    "summary": "Capstone: a performed piece with words.",
                    "learn": [
                        {"type": "p", "text": "The final capstone is a two-minute piece combining your groove and an emceed verse in the lineage of this tradition: a praise poem, a protest line, or a story. This is the same work a griot or a praise poet does. Perform it, and then write one paragraph on what method you used and whose lineage it follows."},
                        {"type": "list", "items": [
                            "Write a verse with a clear line and an answering chorus.",
                            "Rehearse it over your groove.",
                            "Perform in front of an audience and record it.",
                            "Write the method note naming your sources.",
                        ]},
                        {"type": "tip", "text": "In this tradition, the emcee's test is response: does the audience answer? A verse is not finished until it has been tried in the room."},
                        {"type": "activity", "title": "Perform it", "text": "Perform your two-minute piece and write the method note. Submit both."},
                    ],
                    "check": {
                        "prompt": "Check what you know about performance.",
                        "questions": [
                            {"q": "The emcee's role in this tradition resembles…", "options": ["the griot or praise poet", "a court clerk", "a librarian"], "answer": "the griot or praise poet", "explain": "Both carry the community's words and its response."},
                            {"q": "A method note should…", "options": ["name the lineages and choices used", "avoid explanation", "only give a title"], "answer": "name the lineages and choices used", "explain": "It documents how you used the tradition."},
                        ],
                    },
                },
            ],
        },
    ],
}
