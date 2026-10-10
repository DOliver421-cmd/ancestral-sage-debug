"""Grade 11 Social Studies: Black Political Thought (published).

Grade 11 social studies moving from anti-colonialism to civil rights:
the Pan-African congresses, Marcus Garvey, civil rights organizations,
the Black Panther Party, African and Caribbean revolutions, and global
solidarity movements — taught as political theory and political action.
"""

BLACK_POLITICAL_THOUGHT = {
    "slug": "black-political-thought",
    "title": "Black Political Thought: From Anti-Colonialism to Civil Rights",
    "summary": "Garvey, the Pan-African congresses, the civil rights movement, the Black Panther Party, and anti-colonial revolutions.",
    "description": (
        "Grade 11 social studies here presents Black political thought as a coherent "
        "tradition of political theory and organization. Students read the arguments "
        "of Marcus Garvey and the UNIA, the resolutions of the Pan-African Congresses "
        "from 1900 through 1945, the platforms of civil rights organizations, the Ten "
        "Point Program of the Black Panther Party, and the revolutionary literature of "
        "African and Caribbean decolonization. Global solidarity is treated as a "
        "structural force: anticolonial movements communicated, funded, and supported "
        "each other."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["11"],
    "grade_label": "Grade 11",
    "status": "published",
    "audience": "Grade 11 students studying political theory and movements.",
    "est_hours": 28,
    "passing_score": 80,
    "learning_objectives": [
        "Describe Marcus Garvey's program and the scale of the UNIA.",
        "Explain the five Pan-African Congresses and their outcomes.",
        "Compare civil rights strategies: legal, direct action, and economic boycott.",
        "Describe the Black Panther Party's Ten Point Program and its community programs.",
        "Analyze anticolonial revolutions in Ghana, Kenya, Algeria, and Cuba.",
        "Trace the global solidarity network between Black American and African movements.",
        "Analyze primary political documents for argument and tactic.",
    ],
    "units": [
        {
            "slug": "garvey-and-pan-africanism",
            "title": "Garvey and Pan-Africanism",
            "summary": "A movement of millions and a series of congresses.",
            "order": 1,
            "lessons": [
                {
                    "slug": "marcus-garvey-unia",
                    "title": "Marcus Garvey and the UNIA",
                    "order": 1,
                    "minutes": 26,
                    "summary": "The largest Black mass movement of its era.",
                    "learn": [
                        {"type": "p", "text": "Marcus Garvey, born in Jamaica, founded the Universal Negro Improvement Association (UNIA) in Harlem in 1919 and built it into a movement claiming millions of members worldwide. The UNIA published the Negro World, ran businesses (the Black Star shipping line), and preached self-reliance and Black pride. Garvey's programme — economic independence, political self-determination, and pride in African heritage — influenced every later movement from the Nation of Islam to Pan-Africanism."},
                        {"type": "list", "items": [
                            "'Africa for the Africans' — self-determination, not petitions.",
                            "Black Star Line: Black ownership and control of trade and transport.",
                            "African fundamentalism: pride in African identity and history.",
                        ]},
                        {"type": "example", "title": "Why it mattered", "text": "Garvey's movement reached the Caribbean, Central America, and Africa — a global organization at a time when worldwide Black communication was slow and expensive."},
                        {"type": "activity", "title": "Read the program", "text": "Read the UNIA's Declaration of Rights. Identify three concrete demands and state who would have to act on each."},
                    ],
                    "check": {
                        "prompt": "Check what you know about Garvey.",
                        "questions": [
                            {"q": "The UNIA is significant for…", "options": ["building a mass global Black movement", "founding a university only", "creating a single charity"], "answer": "building a mass global Black movement", "explain": "It claimed millions of members across several continents."},
                            {"q": "The Black Star Line was…", "options": ["a Black-owned shipping company", "a newspaper", "a political party"], "answer": "a Black-owned shipping company", "explain": "Garvey believed economic infrastructure had to be Black-controlled."},
                        ],
                    },
                },
                {
                    "slug": "pan-african-congresses",
                    "title": "The Pan-African Congresses",
                    "order": 2,
                    "minutes": 26,
                    "summary": "Five meetings from 1900 to 1945 that put decolonization on the agenda.",
                    "learn": [
                        {"type": "p", "text": "The Pan-African Congresses were a series of meetings linking Africans and people of African descent across the world to demand self-government. The first, in London in 1900, was organized by Trinidadian Henry Sylvester Williams. W.E.B. Du Bois convened the fourth in 1919 and the fifth in Manchester in 1945 — which brought in Nkrumah, Kenyatta, and others who would lead their nations to independence."},
                        {"type": "list", "items": [
                            "1900 London: first Pan-African conference; petition to Queen Victoria.",
                            "1919 Paris/1919 New York (Du Bois): linked to the Paris peace talks.",
                            "1945 Manchester: Nkrumah, Kenyatta, Padmore, and the colonial question taken up by Africans themselves.",
                        ]},
                        {"type": "example", "title": "Outcomes", "text": "The 1945 congress's resolutions anticipated the independence of British and French colonies within a decade — which is roughly what happened."},
                        {"type": "activity", "title": "Resolution writing", "text": "Write a three-clause resolution for a modern issue as if for a 1945 congress. State the demand, who acts, and by when."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the congresses.",
                        "questions": [
                            {"q": "The 1945 Manchester Pan-African Congress helped launch the leadership of…", "options": ["Nkrumah and Kenyatta", "Mussolini and Hitler", "Napoleon"], "answer": "Nkrumah and Kenyatta", "explain": "Both attended and went on to lead Ghana and Kenya."},
                            {"q": "The Pan-African Congresses' central demand was…", "options": ["self-government for colonized peoples", "greater colonial taxes", "modest local offices only"], "answer": "self-government for colonized peoples", "explain": "They asserted the right of colonized Africans to govern themselves."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "civil-rights-era",
            "title": "The Civil Rights Era",
            "summary": "Legal strategy, direct action, boycott, and revolution.",
            "order": 2,
            "lessons": [
                {
                    "slug": "strategies-of-the-movement",
                    "title": "Strategies of the Movement",
                    "order": 3,
                    "minutes": 26,
                    "summary": "Three approaches, one goal.",
                    "learn": [
                        {"type": "p", "text": "The civil rights movement was not one organization but a coalition of tactics. The NAACP pursued court cases (culminating in Brown v. Board, 1954). SCLC under Martin Luther King Jr. used nonviolent direct action — marches, sit-ins, boycotts. Student organizations like SNCC organized local communities and voter registration. Ella Baker's low-key organizing philosophy insisted on leadership from the grassroots rather than a single leader."},
                        {"type": "list", "items": [
                            "Legal: NAACP Legal Defense Fund's cases that repealed 'separate but equal'.",
                            "Direct action: Montgomery bus boycott (1955–56), sit-ins, Birmingham campaign, Selma to Montgomery.",
                            "Economic boycott: the Montgomery boycott removed 75% of bus revenue.",
                            "Grassroots: SNCC's Freedom Summer (1964) registered voters and built the MFDP.",
                        ]},
                        {"type": "example", "title": "Legislation", "text": "Civil Rights Act (1964), Voting Rights Act (1965), and the Fair Housing Act (1968) came out of those tactics winning public opinion and political leverage."},
                        {"type": "activity", "title": "Compare tactics", "text": "In a chart, list legal, direct action, and boycott strategies with one example each and one cost or risk of each."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the civil rights movement.",
                        "questions": [
                            {"q": "Brown v. Board (1954) overturned…", "options": ["'separate but equal' from Plessy v. Ferguson", "the Voting Rights Act", "school taxes"], "answer": "'separate but equal' from Plessy v. Ferguson", "explain": "It declared separate educational facilities inherently unequal."},
                            {"q": "Ella Baker is known for arguing…", "options": ["leadership should develop at the grassroots", "only charismatic leaders matter", "organization is unnecessary"], "answer": "leadership should develop at the grassroots", "explain": "She emphasized group-centered leadership over a single leader."},
                        ],
                    },
                },
                {
                    "slug": "black-panther-party",
                    "title": "The Black Panther Party",
                    "order": 4,
                    "minutes": 26,
                    "summary": "Revolutionary politics and community service.",
                    "learn": [
                        {"type": "p", "text": "Founded in Oakland in 1966 by Huey Newton and Bobby Seale, the Black Panther Party combined armed self-policing of its neighborhoods with community programs: the Free Breakfast for Children Program (which predated school breakfast programs in the district), free medical clinics, and legal-aid offices. Its Ten Point Program stated what Black communities wanted: freedom, employment, housing, education, and an end to police violence."},
                        {"type": "list", "items": [
                            "Point 7: an immediate end to police brutality and murder of Black people.",
                            "Point 2: full employment for the people — an economic demand.",
                            "The Panther breakfast program fed thousands of children and pushed the USDA to adopt school breakfast.",
                        ]},
                        {"type": "example", "title": "Context", "text": "The FBI's COINTELPRO program actively disrupted the Panthers, assassinating or jailing leaders — a record released under Freedom of Information Act litigation."},
                        {"type": "activity", "title": "Read the platform", "text": "Read the Ten Point Program. For three points, write the policy you would draft today to achieve them."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the Black Panther Party.",
                        "questions": [
                            {"q": "The Panther Party's Ten Point Program demanded…", "options": ["employment, housing, education, and an end to police brutality", "only armed patrols", "white withdrawal"], "answer": "employment, housing, education, and an end to police brutality", "explain": "It was a political platform with economic and social demands."},
                            {"q": "The Free Breakfast program demonstrated that the Panthers…", "options": ["delivered community services alongside politics", "only published newspapers", "fought only in courts"], "answer": "delivered community services alongside politics", "explain": "Their community programs were as central as their public politics."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "anti-colonial-revolutions",
            "title": "Anti-Colonial Revolutions and Solidarity",
            "summary": "From Ghana and Cuba to global solidarity networks.",
            "order": 3,
            "lessons": [
                {
                    "slug": "decolonization",
                    "title": "Decolonization in Africa and the Caribbean",
                    "order": 5,
                    "minutes": 26,
                    "summary": "Independence won, and the challenges that followed.",
                    "learn": [
                        {"type": "p", "text": "Between 1957 and the late 1970s most of Africa and the Caribbean won formal independence. Ghana's independence in 1957 made Kwame Nkrumah a world figure — he had written Toward Colonial Freedom and used strikes and positive action to force handover of power. Algeria won independence from France in 1962 after an eight-year war. Cuba's 1959 revolution put an anti-imperialist state in the Caribbean. Independence did not automatically end economic dependence, which became the next stage of struggle — the subject of Nkrumah's Neo-Colonialism: The Last Stage of Imperialism."},
                        {"type": "list", "items": [
                            "Ghana (1957): first sub-Saharan colony to win independence.",
                            "Algeria (1962): a war that cost over a million Algerian lives.",
                            "Cuba (1959): anti-imperialist revolution and international solidarity.",
                            "Neo-colonialism: political independence with continued economic control.",
                        ]},
                        {"type": "example", "title": "Read Nkrumah", "text": "Nkrumah's argument was that the same states that granted flags kept the mines, trade, and debt — so the struggle had to shift from politics to economics."},
                        {"type": "activity", "title": "Timeline of decolonization", "text": "Build a 1957–1975 timeline with five African or Caribbean independences and note one consequence for each."},
                    ],
                    "check": {
                        "prompt": "Check what you know about decolonization.",
                        "questions": [
                            {"q": "Ghana's independence in 1957 is notable because…", "options": ["it was the first in sub-Saharan Africa", "it was the last in Africa", "it never happened"], "answer": "it was the first in sub-Saharan Africa", "explain": "Ghana became the model and the inspiration for other colonies."},
                            {"q": "Nkrumah's concept of neo-colonialism describes…", "options": ["political independence with continued economic control", "new colonies in space", "friendly trade partners"], "answer": "political independence with continued economic control", "explain": "Power changed hands formally, but economics stayed in foreign hands."},
                        ],
                    },
                },
                {
                    "slug": "global-solidarity",
                    "title": "Global Solidarity",
                    "order": 6,
                    "minutes": 26,
                    "summary": "Movements that talked to each other.",
                    "learn": [
                        {"type": "p", "text": "Black American and African movements were connected by travel, print, and money. Malcolm X's Organization of Afro-American Unity drew directly on the Pan-African tradition; the Student Nonviolent Coordinating Committee found allies in Ghana; Cuban troops fought in Angola; and the anti-apartheid movement built boycotts across the world. Angela Davis's politics linked prison abolition to anti-colonialism. This network made the whole movement more than the sum of its national parts."},
                        {"type": "list", "items": [
                            "Malcolm X's OAAU: Pan-Africanism applied in the United States.",
                            "SNCC and the liberation committees: exchange of strategy and people.",
                            "Anti-apartheid: divestment campaigns in the US and Europe.",
                        ]},
                        {"type": "example", "title": "One network", "text": "Moscow-Beijing-Washington-Havana-Accra-London-Harare: the circulation of leaders and print built a common vocabulary of rights and self-determination."},
                        {"type": "activity", "title": "Trace the connection", "text": "Pick two movements (e.g. anti-apartheid and US civil rights). List three concrete exchanges between them and note their effect."},
                    ],
                    "check": {
                        "prompt": "Check what you know about solidarity.",
                        "questions": [
                            {"q": "The Organization of Afro-American Unity drew on…", "options": ["Pan-African political thought", "European feudalism", "isolationist theory"], "answer": "Pan-African political thought", "explain": "It applied Pan-African analysis to the African American struggle."},
                            {"q": "Anti-apartheid movements used…", "options": ["boycotts and divestment campaigns", "only prayer meetings", "military aid only"], "answer": "boycotts and divestment campaigns", "explain": "Economic pressure coordinated internationally helped isolate the regime."},
                        ],
                    },
                },
            ],
        },
    ],
}
