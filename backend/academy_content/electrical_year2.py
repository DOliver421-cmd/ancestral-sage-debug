"""Applied Electrical Engineering — Year 2 (full published course)."""

ELECTRICAL_YEAR_2 = {
    "slug": "electrical-year-2",
    "title": "Applied Electrical Engineering — Year 2",
    "summary": "AC power, wiring methods, and residential systems.",
    "description": (
        "Year 2 deepens the electrical pathway with alternating current theory, "
        "wiring methods and materials, and residential branch-circuit design. "
        "Students read NEC-style references, interpret wiring diagrams, and complete "
        "hands-on projects that mirror real contractor tasks."
    ),
    "subject": "trade",
    "subject_label": "Trade & Applied Skills",
    "track": "builder",
    "tracks": ["builder"],
    "grades": ["10", "11", "12"],
    "grade_label": "Grades 10–12",
    "status": "published",
    "audience": "Builder-track students in Year 2 of the electrical pathway.",
    "est_hours": 28,
    "passing_score": 80,
    "learning_objectives": [
        "Explain AC voltage, current, frequency, and power factor.",
        "Select wiring methods and materials for residential jobs.",
        "Size branch circuits using NEC load calculations.",
        "Read and create residential wiring diagrams.",
        "Apply code rules for grounding and bonding.",
    ],
    "units": [
        {
            "slug": "ac-power-and-motors",
            "title": "AC Power and Motors",
            "summary": "Alternating current, transformers, and single-phase motors.",
            "order": 1,
            "lessons": [
                {
                    "slug": "ac-fundamentals",
                    "title": "AC Fundamentals",
                    "order": 1,
                    "minutes": 20,
                    "summary": "Voltage, frequency, phase, and RMS values.",
                    "learn": [
                        {"type": "p", "text": "Alternating current (AC) changes direction many times per second. In the U.S., household AC is 60 Hz — 60 cycles each second. RMS (root mean square) voltage is the effective value: 120 V RMS household."},
                        {"type": "list", "items": [
                            "Frequency = cycles per second (Hz).",
                            "Voltage = electrical pressure.",
                            "Current = flow of electrons (amps).",
                            "Power in AC = V × I × power factor.",
                        ]},
                        {"type": "example", "title": "Sine wave", "text": "A sine wave goes positive, back through zero, negative, and back to zero. One complete trip is one cycle."},
                    ],
                    "check": {
                        "prompt": "Show what you know about AC fundamentals.",
                        "questions": [
                            {"q": "In the U.S., household AC frequency is…", "options": ["60 Hz", "50 Hz", "120 Hz"], "answer": "60 Hz", "explain": "North American household power is 60 Hz."},
                            {"q": "RMS voltage for a standard U.S. outlet is…", "options": ["120 V", "240 V", "12 V"], "answer": "120 V", "explain": "Standard household voltage is 120 V RMS."},
                        ],
                    },
                },
                {
                    "slug": "transformers-and-single-phase-motors",
                    "title": "Transformers and Single-Phase Motors",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Step up/down voltage and motor starting methods.",
                    "learn": [
                        {"type": "p", "text": "Transformers use electromagnetic induction to change AC voltage. Step-up transformers increase voltage (decrease current) for long-distance transmission. Step-down transformers reduce voltage for safe use."},
                        {"type": "example", "title": "Residential transformer", "text": "A pole transformer steps 7,200 V down to 120/240 V for houses. The secondary has a center tap giving two 120 V legs and a neutral."},
                        {"type": "tip", "text": "Single-phase motors need a starting mechanism. Common types: split-phase, capacitor-start, shaded-pole."},
                    ],
                    "check": {
                        "prompt": "Show what you know about transformers and motors.",
                        "questions": [
                            {"q": "A transformer that increases voltage is called…", "options": ["step-up", "step-down", "isolation"], "answer": "step-up", "explain": "Step-up transformers raise voltage and lower current."},
                            {"q": "Why transmit power at high voltage?", "options": ["to reduce current and heat loss", "to make it more dangerous", "to use thinner wires"], "answer": "to reduce current and heat loss", "explain": "Higher voltage means lower current for the same power, reducing I²R losses."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "wiring-and-residential",
            "title": "Wiring Methods and Residential Systems",
            "summary": "Cable types, conduit, branch circuits, and NEC basics.",
            "order": 2,
            "lessons": [
                {
                    "slug": "wiring-methods-and-materials",
                    "title": "Wiring Methods and Materials",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Cable types, conduit, boxes, and conductors.",
                    "learn": [
                        {"type": "p", "text": "Electricians choose wiring methods based on the job. Common options: NM (Romeo) cable for dry residential walls, conduit for commercial and exposed runs, and UF cable for underground."},
                        {"type": "list", "items": [
                            "NM-B: nonmetallic sheathed cable for dry interior residential.",
                            "PVC conduit: lightweight, corrosion-resistant.",
                            "EMT: thin-wall metal conduit for exposed commercial work.",
                            "Wire colors: black/red = hot, white = neutral, green/bare = ground.",
                        ]},
                        {"type": "activity", "title": "Identify cables", "text": "Find three types of electrical cable or conduit in a hardware store or online. Write their common names and typical uses."},
                    ],
                    "check": {
                        "prompt": "Show what you know about wiring methods.",
                        "questions": [
                            {"q": "Which cable is commonly used inside residential walls?", "options": ["NM-B (Romeo)", "UF cable", "rigid metal conduit"], "answer": "NM-B (Romeo)", "explain": "NM-B is the standard nonmetallic sheathed cable for dry residential interiors."},
                            {"q": "Which wire is the ground?", "options": ["green or bare", "white", "black"], "answer": "green or bare", "explain": "Ground wires are green or bare copper."},
                        ],
                    },
                },
                {
                    "slug": "residential-branch-circuits",
                    "title": "Residential Branch Circuits",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Circuit types, loads, overcurrent protection, and outlets.",
                    "learn": [
                        {"type": "p", "text": "A branch circuit carries power from the breaker panel to outlets and devices. NEC load calculations determine the required circuit size. General circuits are typically 15 A or 20 A at 120 V. Dedicated circuits serve large appliances."},
                        {"type": "example", "title": "15 A lighting circuit", "text": "A 15 A breaker protects a 14 AWG wire. Maximum load = 15 A × 120 V = 1,800 W. For continuous loads (on 3+ hours), use 80%: 1,440 W."},
                        {"type": "tip", "text": "GFCI protection is required in bathrooms, kitchens, garages, and outdoors."},
                    ],
                    "check": {
                        "prompt": "Show what you know about residential branch circuits.",
                        "questions": [
                            {"q": "A 20 A circuit on 120 V can safely carry up to…", "options": ["2,400 W", "2,880 W", "1,920 W"], "answer": "2,400 W", "explain": "Watts = volts × amps. 120 V × 20 A = 2,400 W. For continuous loads, use 80%."},
                            {"q": "Which NEC rule requires GFCI in bathrooms?", "options": ["all outlets must be GFCI protected", "only lights need GFCI", "no GFCI is required"], "answer": "all outlets must be GFCI protected", "explain": "NEC requires GFCI protection in bathrooms, kitchens, garages, and outdoors."},
                        ],
                    },
                },
                {
                    "slug": "grounding-and-bonding",
                    "title": "Grounding and Bonding",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Equipment grounding, grounding electrode, and bonding.",
                    "learn": [
                        {"type": "p", "text": "Grounding connects electrical systems to earth to limit voltage. Bonding connects all metal parts together so they are at the same potential. Together they protect people from electric shock and equipment from damage."},
                        {"type": "list", "items": [
                            "Equipment grounding conductor (EGC) carries fault current.",
                            "Grounding electrode connects the system to earth (rod, pipe, plate).",
                            "Bonding jumpers join metal raceways, enclosures, and pipes.",
                            "If a hot wire touches a metal box, the EGC trips the breaker.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about grounding and bonding.",
                        "questions": [
                            {"q": "The purpose of a grounding electrode is to…", "options": ["connect the system to earth", "increase voltage", "light the house"], "answer": "connect the system to earth", "explain": "Grounding electrodes provide a path to earth to stabilize voltage."},
                            {"q": "What does an EGC do during a fault?", "options": ["carries fault current to trip the breaker", "reduces power use", "increases resistance"], "answer": "carries fault current to trip the breaker", "explain": "The equipment grounding conductor provides a low-resistance path for fault current."},
                        ],
                    },
                },
                {
                    "slug": "wiring-diagrams-and-panels",
                    "title": "Wiring Diagrams and Panel Schedules",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Read single-line diagrams and create panel schedules.",
                    "learn": [
                        {"type": "p", "text": "A single-line diagram shows the path of power from the service through breakers to loads. A panel schedule lists each circuit, its breaker size, and its devices."},
                        {"type": "example", "title": "Sample single-line", "text": "Service → main breaker → branch breakers → outlets/lights. Each line represents a conductor or load."},
                        {"type": "activity", "title": "Draw a panel schedule", "text": "Create a panel schedule for a small garage workshop with at least six circuits."},
                    ],
                    "check": {
                        "prompt": "Show what you know about wiring diagrams.",
                        "questions": [
                            {"q": "A single-line diagram shows…", "options": ["the path of power through the electrical system", "wire colors", "personalities of electricians"], "answer": "the path of power through the electrical system", "explain": "Single-line diagrams simplify complex systems into single paths."},
                        ],
                    },
                },
            ],
        },
    ],
}
