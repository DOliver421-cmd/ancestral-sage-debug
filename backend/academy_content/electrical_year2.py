"""Applied Electrical Engineering — Year 2 (full published course)."""

ELECTRICAL_YEAR_2 = {
    "slug": "electrical-year-2",
    "title": "Applied Electrical Engineering — Year 2",
    "summary": "AC power, distribution, wiring methods, and residential system design.",
    "description": (
        "Year 2 deepens the electrical pathway with alternating current theory, "
        "power calculations, transformers, motors, distribution systems, wiring methods, "
        "grounding and bonding, three-phase systems, electrical drawings, troubleshooting, "
        "residential system design, code research, and a capstone design project. "
        "Students read NEC-style references, interpret diagrams, and complete "
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
    "est_hours": 32,
    "passing_score": 80,
    "learning_objectives": [
        "Explain AC voltage, current, frequency, power factor, and single-phase power calculations.",
        "Describe transformer operation and basic turns-ratio calculations.",
        "Explain motor starting methods and control circuit fundamentals.",
        "Describe electrical distribution hierarchy including feeders, branch circuits, panels, and disconnects.",
        "Select and apply overcurrent, GFCI, and AFCI protection devices.",
        "Apply grounding and bonding rules, including fault-current paths.",
        "Interpret three-phase system concepts and basic power relationships.",
        "Read and create electrical drawings, schematics, and panel schedules.",
        "Apply systematic troubleshooting techniques using meters and isolation methods.",
        "Design a residential electrical system including loads, circuits, panel schedule, and conductor selection.",
        "Locate applicable NEC requirements using code organization and lookup methods.",
        "Produce and defend a complete electrical design package for a hypothetical project.",
    ],
    "units": [
        {
            "slug": "ac-power-and-transformers",
            "title": "Unit 1 — AC Power and Transformers",
            "summary": "AC fundamentals, single-phase power, transformers, and motor controls.",
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
                        {"type": "tip", "text": "RMS values let us treat AC like DC for power calculations. A 120 V RMS sine wave peaks at about 170 V."},
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
                    "slug": "ac-power-and-single-phase-systems",
                    "title": "AC Power and Single-Phase Systems",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Frequency, RMS, single-phase power calculations, and voltage-current relationships.",
                    "learn": [
                        {"type": "p", "text": "Single-phase AC power is calculated using volts, amps, and power factor. Apparent power (VA) equals volts × amps. Real power (W) equals VA × power factor. Power factor represents how effectively current is converted into useful work."},
                        {"type": "list", "items": [
                            "Apparent power (S) = V × I (measured in volt-amps).",
                            "Real power (P) = V × I × power factor (measured in watts).",
                            "Reactive power (Q) = V × I × sin(φ) (measured in VAR).",
                            "Resistive loads have power factor near 1.0.",
                            "Inductive loads (motors, transformers) lower power factor.",
                        ]},
                        {"type": "example", "title": "Single-phase motor", "text": "A motor draws 10 A at 120 V with power factor 0.8. Apparent power = 1,200 VA. Real power = 960 W. Reactive power = 720 VAR."},
                        {"type": "tip", "text": "Power factor correction with capacitors reduces reactive current and improves efficiency in inductive circuits."},
                    ],
                    "check": {
                        "prompt": "Show what you know about single-phase AC power.",
                        "questions": [
                            {"q": "A load draws 8 A at 120 V with power factor 0.9. Real power is closest to…", "options": ["864 W", "960 W", "1,066 W"], "answer": "864 W", "explain": "Real power = 120 V × 8 A × 0.9 = 864 W."},
                            {"q": "Which type of load typically has the lowest power factor?", "options": ["inductive motor", "resistive heater", "LED lamp"], "answer": "inductive motor", "explain": "Inductive loads like motors have power factors well below 1.0."},
                        ],
                    },
                },
                {
                    "slug": "transformers",
                    "title": "Transformers",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Step-up/step-down operation, control transformers, and basic calculations.",
                    "learn": [
                        {"type": "p", "text": "Transformers use electromagnetic induction to change AC voltage. Primary and secondary windings share a magnetic core. Step-up transformers increase voltage (decrease current) for long-distance transmission. Step-down transformers reduce voltage for safe end use."},
                        {"type": "list", "items": [
                            "Turns ratio = secondary turns ÷ primary turns.",
                            "Voltage ratio equals turns ratio: Vp/Vs = Np/Ns.",
                            "Current ratio is inverse of turns ratio.",
                            "Control transformers step 120/240 V down to 24 V or 12 V for controls.",
                        ]},
                        {"type": "example", "title": "Transformer turns ratio", "text": "A transformer with 500 primary turns and 100 secondary turns steps 240 V down to 48 V. Current steps up by the same 5:1 ratio."},
                        {"type": "tip", "text": "Transformers only work with AC. DC causes no changing magnetic field, so no induction occurs."},
                    ],
                    "check": {
                        "prompt": "Show what you know about transformer operation.",
                        "questions": [
                            {"q": "A step-down transformer with a 4:1 turns ratio fed with 240 V produces approximately…", "options": ["60 V", "960 V", "240 V"], "answer": "60 V", "explain": "Voltage steps down by the turns ratio: 240 V ÷ 4 = 60 V."},
                            {"q": "A control transformer typically outputs…", "options": ["24 V or 12 V", "480 V", "120/240 V"], "answer": "24 V or 12 V", "explain": "Control transformers step voltage down to safe levels for control circuits."},
                        ],
                    },
                },
                {
                    "slug": "motors-and-controls",
                    "title": "Motors and Controls",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Motor fundamentals, starters, contactors, overload protection, and basic control circuits.",
                    "learn": [
                        {"type": "p", "text": "Electric motors convert electrical energy into mechanical rotation. Single-phase motors need a starting mechanism because single-phase AC does not produce a rotating magnetic field by itself."},
                        {"type": "list", "items": [
                            "Split-phase motors use an extra start winding.",
                            "Capacitor-start motors add a capacitor for higher starting torque.",
                            "Shaded-pole motors use a copper shading coil for small low-torque loads.",
                            "Contactors are electrically controlled switches for motor starting.",
                            "Overload relays protect motors from sustained overcurrent.",
                        ]},
                        {"type": "example", "title": "Motor starter wiring", "text": "A three-phase motor starter has a contactor, overload relay, and start/stop push buttons. Pressing start energizes the contactor coil, closing the main contacts."},
                        {"type": "tip", "text": "Always size overload heaters to the motor full-load current (FLC) from the nameplate."},
                        {"type": "activity", "title": "Trace a control circuit", "text": "Find a simple motor ladder diagram online. Trace the current path from L1 through the start button, stop button, overload contact, and contactor coil back to L2."},
                    ],
                    "check": {
                        "prompt": "Show what you know about motors and controls.",
                        "questions": [
                            {"q": "The purpose of an overload relay is to…", "options": ["protect the motor from sustained overcurrent", "start the motor automatically", "increase motor speed"], "answer": "protect the motor from sustained overcurrent", "explain": "Overload relays open when current exceeds the motor FLC for too long."},
                            {"q": "A contactor is best described as…", "options": ["an electrically controlled switch", "a type of capacitor", "a ground-fault detector"], "answer": "an electrically controlled switch", "explain": "Contactors close and open high-current motor circuits using a small control signal."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "distribution-and-service",
            "title": "Unit 2 — Distribution and Service",
            "summary": "Electrical distribution, overcurrent protection, GFCI/AFCI, and residential service.",
            "order": 2,
            "lessons": [
                {
                    "slug": "electrical-distribution",
                    "title": "Electrical Distribution",
                    "order": 5,
                    "minutes": 20,
                    "summary": "Service, feeders, branch circuits, panels, and disconnects.",
                    "learn": [
                        {"type": "p", "text": "Electrical distribution moves power from the utility service to final loads. The hierarchy starts at the service entrance, passes through feeders to subpanels, then through branch circuits to devices."},
                        {"type": "list", "items": [
                            "Service entrance: utility connection to building.",
                            "Service equipment: main breaker and meter base.",
                            "Feeders: conductors between main panel and subpanels.",
                            "Branch circuits: final conductors to outlets and lights.",
                            "Panels distribute power through individual breakers.",
                            "Disconnects provide safe isolation for maintenance.",
                        ]},
                        {"type": "example", "title": "Distribution hierarchy", "text": "Utility → service drop → meter → main panel (100 A) → feeder to garage subpanel → 20 A branch circuit to garage outlets."},
                        {"type": "tip", "text": "Always size feeders for voltage drop, especially for long runs or large loads."},
                    ],
                    "check": {
                        "prompt": "Show what you know about electrical distribution.",
                        "questions": [
                            {"q": "A conductor that runs from the main panel to a subpanel is called a…", "options": ["feeder", "branch circuit", "grounding electrode"], "answer": "feeder", "explain": "Feeders carry power between panels; branch circuits go to final outlets."},
                            {"q": "The main purpose of a disconnect is to…", "options": ["provide a safe isolation point", "reduce voltage", "measure power use"], "answer": "provide a safe isolation point", "explain": "Disconnects allow workers to de-energize equipment safely for service."},
                        ],
                    },
                },
                {
                    "slug": "overcurrent-protection",
                    "title": "Overcurrent Protection",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Breakers, fuses, circuit protection, short circuits, and overloads.",
                    "learn": [
                        {"type": "p", "text": "Overcurrent protection prevents wires and equipment from overheating due to excessive current. Circuit breakers and fuses interrupt fault current quickly. Overload protection guards against sustained overcurrent below fault levels."},
                        {"type": "list", "items": [
                            "Circuit breakers trip and can be reset.",
                            "Fuses melt and must be replaced.",
                            "Short-circuit current can be thousands of amps.",
                            "Thermal-magnetic breakers combine heat and magnetic trip elements.",
                            "Breaker rating must match conductor ampacity.",
                        ]},
                        {"type": "example", "title": "Breaker trip curve", "text": "A 20 A breaker may hold 20 A indefinitely but trip in seconds at 40 A. The exact curve depends on the manufacturer."},
                        {"type": "tip", "text": "Never replace a breaker with a higher ampacity. The wire, not the breaker, limits safe current."},
                    ],
                    "check": {
                        "prompt": "Show what you know about overcurrent protection.",
                        "questions": [
                            {"q": "What is the primary difference between a fuse and a circuit breaker?", "options": ["A fuse must be replaced after tripping", "A breaker trips slower", "A fuse is reusable"], "answer": "A fuse must be replaced after tripping", "explain": "Fuses melt and are destroyed; breakers mechanically open and can be reset."},
                            {"q": "Overload protection guards against…", "options": ["sustained overcurrent below short-circuit levels", "lightning strikes", "voltage spikes"], "answer": "sustained overcurrent below short-circuit levels", "explain": "Overloads are moderate overcurrents that cause overheating over time."},
                        ],
                    },
                },
                {
                    "slug": "gfci-and-afci-protection",
                    "title": "GFCI and AFCI Protection",
                    "order": 7,
                    "minutes": 18,
                    "summary": "Purpose, applications, testing, and common installation scenarios.",
                    "learn": [
                        {"type": "p", "text": "Ground-fault circuit interrupters (GFCIs) protect people from electric shock by detecting imbalance between hot and neutral. Arc-fault circuit interrupters (AFCIs) protect against dangerous arcing conditions that can cause fires."},
                        {"type": "list", "items": [
                            "GFCI trips when leakage current exceeds ~5 mA.",
                            "AFCIs detect series and parallel arcs.",
                            "NEC requires GFCI in bathrooms, kitchens, garages, and outdoors.",
                            "NEC requires AFCI in most residential living areas.",
                            "Test GFCI and AFCI devices monthly.",
                        ]},
                        {"type": "example", "title": "Personnel protection", "text": "A GFCI trips in 25 ms at 6 mA — fast enough to prevent ventricular fibrillation."},
                        {"type": "tip", "text": "GFCI protects people; AFCI protects property. Modern devices combine both functions."},
                    ],
                    "check": {
                        "prompt": "Show what you know about GFCI and AFCI protection.",
                        "questions": [
                            {"q": "A GFCI trips when it detects leakage current of approximately…", "options": ["5 mA", "50 mA", "500 mA"], "answer": "5 mA", "explain": "GFCIs trip at around 5 mA to protect people from lethal shock."},
                            {"q": "The primary purpose of an AFCI is to…", "options": ["prevent fires from arcing faults", "prevent electric shock", "reduce power consumption"], "answer": "prevent fires from arcing faults", "explain": "AFCIs detect dangerous arcing conditions that can ignite building materials."},
                        ],
                    },
                },
                {
                    "slug": "residential-service-systems",
                    "title": "Residential Service Systems",
                    "order": 8,
                    "minutes": 18,
                    "summary": "Service equipment, metering, main disconnect, and distribution.",
                    "learn": [
                        {"type": "p", "text": "The residential service entrance brings utility power into the building. It includes the service drop or lateral, meter, main disconnect, service panel, and grounding electrode system."},
                        {"type": "list", "items": [
                            "Service drop: overhead conductors from utility pole.",
                            "Service lateral: underground conductors.",
                            "Meter base measures energy use.",
                            "Main disconnect isolates the entire building.",
                            "Service panel distributes power through branch breakers.",
                            "Grounding electrode connects system to earth.",
                        ]},
                        {"type": "example", "title": "Typical residential service", "text": "A 200 A single-family home usually has a 200 A main breaker, a meter base, and a 120/240 V single-phase service with center-tapped neutral."},
                        {"type": "tip", "text": "The service disconnect must be readily accessible and clearly marked."},
                    ],
                    "check": {
                        "prompt": "Show what you know about residential service systems.",
                        "questions": [
                            {"q": "The main purpose of the service disconnect is to…", "options": ["isolate all building power", "measure energy use", "step down voltage"], "answer": "isolate all building power", "explain": "The service disconnect is the primary means to de-energize the entire building."},
                            {"q": "An underground utility connection to a house is called a…", "options": ["service lateral", "service drop", "feeder"], "answer": "service lateral", "explain": "Service laterals run underground; service drops are overhead."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "wiring-methods-and-conductors",
            "title": "Unit 3 — Wiring Methods and Conductors",
            "summary": "Cable types, branch circuits, grounding, bonding, and three-phase systems.",
            "order": 3,
            "lessons": [
                {
                    "slug": "wiring-methods-and-materials",
                    "title": "Wiring Methods and Materials",
                    "order": 9,
                    "minutes": 20,
                    "summary": "Cable types, conduit, boxes, and conductors.",
                    "learn": [
                        {"type": "p", "text": "Electricians choose wiring methods based on the job. Common options: NM (Romex) cable for dry residential walls, conduit for commercial and exposed runs, and UF cable for underground."},
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
                            {"q": "Which cable is commonly used inside residential walls?", "options": ["NM-B (Romex)", "UF cable", "rigid metal conduit"], "answer": "NM-B (Romex)", "explain": "NM-B is the standard nonmetallic sheathed cable for dry residential interiors."},
                            {"q": "Which wire is the ground?", "options": ["green or bare", "white", "black"], "answer": "green or bare", "explain": "Ground wires are green or bare copper."},
                        ],
                    },
                },
                {
                    "slug": "residential-branch-circuits",
                    "title": "Residential Branch Circuits",
                    "order": 10,
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
                    "order": 11,
                    "minutes": 18,
                    "summary": "Equipment grounding, grounding electrode, bonding, and fault-current paths.",
                    "learn": [
                        {"type": "p", "text": "Grounding connects electrical systems to earth to limit voltage. Bonding connects all metal parts together so they are at the same potential. Together they protect people from electric shock and equipment from damage."},
                        {"type": "list", "items": [
                            "Equipment grounding conductor (EGC) carries fault current.",
                            "Grounding electrode connects the system to earth (rod, pipe, plate).",
                            "Bonding jumpers join metal raceways, enclosures, and pipes.",
                            "If a hot wire touches a metal box, the EGC trips the breaker.",
                        ]},
                        {"type": "example", "title": "Fault-current path", "text": "When a hot conductor touches a metal panel, the EGC provides a low-resistance path back to the source. High fault current trips the breaker quickly, clearing the hazard."},
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
                    "slug": "three-phase-systems",
                    "title": "Three-Phase Systems",
                    "order": 12,
                    "minutes": 18,
                    "summary": "Phase relationships, wye/delta concepts, three-phase loads, and basic calculations.",
                    "learn": [
                        {"type": "p", "text": "Three-phase power uses three AC waveforms spaced 120 degrees apart. It is the standard for commercial and industrial power because it delivers more power with less conductor material than single-phase."},
                        {"type": "list", "items": [
                            "Wye (Y) connection has a neutral and phase voltage lower than line voltage.",
                            "Delta (Δ) connection has no neutral and equal line and phase voltage.",
                            "Three-phase power = √3 × V_line × I_line.",
                            "Balanced loads draw equal current on all three phases.",
                        ]},
                        {"type": "example", "title": "Wye vs delta", "text": "In a 120/208 V wye system, phase voltage is 120 V and line voltage is 208 V. In a 120 V delta system, both phase and line voltage are 120 V."},
                        {"type": "tip", "text": "Three-phase motors are simpler, more efficient, and self-starting compared to single-phase motors."},
                    ],
                    "check": {
                        "prompt": "Show what you know about three-phase systems.",
                        "questions": [
                            {"q": "In a balanced 208 V wye system, the phase voltage is closest to…", "options": ["120 V", "208 V", "360 V"], "answer": "120 V", "explain": "In a wye system, V_line = √3 × V_phase, so V_phase = 208 V ÷ √3 ≈ 120 V."},
                            {"q": "Three-phase power is preferred for commercial buildings because it…", "options": ["delivers more power with less conductor material", "is safer than single-phase", "uses lower voltage"], "answer": "delivers more power with less conductor material", "explain": "Three-phase transmission reduces conductor material and I²R losses."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "drawings-and-troubleshooting",
            "title": "Unit 4 — Drawings and Troubleshooting",
            "summary": "Electrical drawings, schematics, panel schedules, and systematic troubleshooting.",
            "order": 4,
            "lessons": [
                {
                    "slug": "electrical-drawings",
                    "title": "Electrical Drawings",
                    "order": 13,
                    "minutes": 18,
                    "summary": "Schematics, one-lines, wiring diagrams, and panel schedules.",
                    "learn": [
                        {"type": "p", "text": "Electrical drawings communicate design intent to installers and inspectors. Common types include one-line diagrams, schematics, wiring diagrams, and panel schedules."},
                        {"type": "list", "items": [
                            "One-line diagram: simplified power path from service to loads.",
                            "Schematic: shows functional relationships between components.",
                            "Wiring diagram: shows physical connections and wire routing.",
                            "Panel schedule: lists each circuit, breaker size, and connected loads.",
                        ]},
                        {"type": "activity", "title": "Create a panel schedule", "text": "Create a panel schedule for a small garage workshop with at least six circuits. Include circuit numbers, breaker sizes, descriptions, and loads."},
                    ],
                    "check": {
                        "prompt": "Show what you know about electrical drawings.",
                        "questions": [
                            {"q": "A one-line diagram shows…", "options": ["the simplified path of power through the system", "individual wire colors", "physical wire routing"], "answer": "the simplified path of power through the system", "explain": "One-line diagrams use single lines to represent multi-conductor paths."},
                            {"q": "A panel schedule lists…", "options": ["circuit numbers, breaker sizes, and loads", "wire insulation types", "conductor lengths"], "answer": "circuit numbers, breaker sizes, and loads", "explain": "Panel schedules organize circuit information for panels."},
                        ],
                    },
                },
                {
                    "slug": "troubleshooting",
                    "title": "Troubleshooting",
                    "order": 14,
                    "minutes": 20,
                    "summary": "Diagnostic process, meter use, continuity, voltage testing, and fault isolation.",
                    "learn": [
                        {"type": "p", "text": "Systematic troubleshooting uses a logical process to locate and repair faults. The basic steps: gather information, analyze symptoms, isolate the fault, repair, and verify."},
                        {"type": "list", "items": [
                            "Gather information: ask about symptoms and recent changes.",
                            "Analyze symptoms: use schematics to predict behavior.",
                            "Isolate: divide the circuit into sections and test.",
                            "Measure voltage, continuity, and current as needed.",
                            "Repair: replace failed components safely.",
                            "Verify: confirm normal operation before closing the job.",
                        ]},
                        {"type": "example", "title": "Dead outlet", "text": "A dead outlet could be a tripped GFCI, tripped breaker, open neutral, or loose connection. Start at the panel, then move toward the outlet, checking each section."},
                        {"type": "tip", "text": "Always verify absence of voltage before touching energized parts. Use a known-good tester first."},
                        {"type": "activity", "title": "Diagnose a simulated fault", "text": "A motor control circuit will not start. List the five most likely causes and the order you would test them."},
                    ],
                    "check": {
                        "prompt": "Show what you know about troubleshooting.",
                        "questions": [
                            {"q": "The first step in systematic troubleshooting is to…", "options": ["gather information about symptoms", "replace every component", "call the utility"], "answer": "gather information about symptoms", "explain": "Understanding what happened and when guides efficient diagnosis."},
                            {"q": "Before touching any conductor, you should…", "options": ["verify absence of voltage with a tester", "assume it is de-energized", "wear rubber gloves only"], "answer": "verify absence of voltage with a tester", "explain": "Always test-then-touch. A known-good tester confirms the circuit is truly dead."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "design-and-code",
            "title": "Unit 5 — Design and Code",
            "summary": "Residential system design and NEC code research methods.",
            "order": 5,
            "lessons": [
                {
                    "slug": "residential-system-design",
                    "title": "Residential System Design",
                    "order": 15,
                    "minutes": 22,
                    "summary": "Design a hypothetical residential electrical system including loads, circuits, panel schedule, conductor selections, protection, grounding and bonding.",
                    "learn": [
                        {"type": "p", "text": "Residential system design connects code requirements to real projects. A complete design package includes load calculations, circuiting, panel schedule, conductor sizing, protection ratings, and grounding/bonding details."},
                        {"type": "list", "items": [
                            "Calculate total connected and demand loads.",
                            "Size branch circuits and feeders per NEC Article 220.",
                            "Select conductors based on ampacity and temperature rating.",
                            "Choose breakers and fuses matching conductor size.",
                            "Design grounding electrode and bonding system.",
                            "Create a panel schedule and one-line diagram.",
                        ]},
                        {"type": "example", "title": "Design workflow", "text": "1) List loads. 2) Calculate demand. 3) Size branch circuits. 4) Size feeders. 5) Select panel. 6) Draw one-line. 7) Write panel schedule."},
                        {"type": "tip", "text": "Always check for voltage drop on long feeders. Keep branch-circuit voltage drop under 3% total."},
                    ],
                    "check": {
                        "prompt": "Show what you know about residential system design.",
                        "questions": [
                            {"q": "The first step in residential system design is to…", "options": ["list and calculate loads", "select wire colors", "install the panel"], "answer": "list and calculate loads", "explain": "Load calculation determines how much power the building needs before any other design decisions."},
                            {"q": "NEC Article 220 primarily covers…", "options": ["load calculations", "grounding rules", "motor circuits"], "answer": "load calculations", "explain": "Article 220 provides rules for calculating electrical loads."},
                        ],
                    },
                },
                {
                    "slug": "code-research",
                    "title": "Code Research",
                    "order": 16,
                    "minutes": 18,
                    "summary": "How to locate applicable NEC requirements using code organization and lookup methods.",
                    "learn": [
                        {"type": "p", "text": "The National Electrical Code (NEC) is organized into chapters and articles. Learning to navigate the NEC efficiently is essential for design, inspection, and troubleshooting."},
                        {"type": "list", "items": [
                            "Chapter 1: General — definitions and scope.",
                            "Chapter 2: Wiring and Protection — overcurrent, conductors, grounding.",
                            "Chapter 3: Wiring Methods and Materials — cables, conduits, boxes.",
                            "Chapter 4: Equipment for General Use — panels, receptacles, lamps.",
                            "Articles are numbered by subject.",
                            "Use the index and table of contents first.",
                        ]},
                        {"type": "example", "title": "Code lookup", "text": "To find GFCI requirements for garages, look under Article 210.8(A) — Dwelling Units. It lists garages, bathrooms, kitchens, and outdoors."},
                        {"type": "tip", "text": "Read the entire article and any exceptions. Exceptions often override the general rule for specific cases."},
                    ],
                    "check": {
                        "prompt": "Show what you know about code research.",
                        "questions": [
                            {"q": "NEC Article 210 primarily covers…", "options": ["branch circuits", "transformers", "motors"], "answer": "branch circuits", "explain": "Article 210 covers branch-circuit requirements including outlets and loads."},
                            {"q": "The best first step when researching a code question is to…", "options": ["use the index or table of contents", "start reading at Article 100", "guess based on memory"], "answer": "use the index or table of contents", "explain": "The index and table of contents lead directly to the relevant article."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "case-studies-and-capstone",
            "title": "Unit 6 — Case Studies and Capstone",
            "summary": "Practical troubleshooting case studies and a comprehensive Year 2 capstone project.",
            "order": 6,
            "lessons": [
                {
                    "slug": "practical-troubleshooting-case-studies",
                    "title": "Practical Troubleshooting Case Studies",
                    "order": 17,
                    "minutes": 20,
                    "summary": "Diagnose simulated faults using case-study methodology.",
                    "learn": [
                        {"type": "p", "text": "Case studies present realistic electrical problems. Analyzing multiple faults builds pattern recognition and reinforces systematic troubleshooting."},
                        {"type": "list", "items": [
                            "Read the full symptom description before testing.",
                            "Identify safety concerns first.",
                            "Use schematics to predict expected measurements.",
                            "Isolate the fault into smallest possible sections.",
                            "Document measurements and repair steps.",
                        ]},
                        {"type": "example", "title": "Case study approach", "text": "A 3-phase motor hums but does not turn. Possible causes: single-phase condition, seized rotor, incorrect voltage, or open start winding. Check each in order of ease and safety."},
                        {"type": "tip", "text": "When case-study data is limited, state assumptions clearly before proceeding."},
                    ],
                    "check": {
                        "prompt": "Show what you know about troubleshooting case studies.",
                        "questions": [
                            {"q": "When analyzing a case study, you should first…", "options": ["identify safety concerns", "replace all breakers", "call the utility"], "answer": "identify safety concerns", "explain": "Safety must come first in any troubleshooting scenario."},
                            {"q": "Dividing a circuit into sections to test is called…", "options": ["isolation", "estimation", "calibration"], "answer": "isolation", "explain": "Isolation narrows the fault to a smaller and smaller section until found."},
                        ],
                    },
                },
                {
                    "slug": "year-2-capstone",
                    "title": "Year 2 Capstone",
                    "order": 18,
                    "minutes": 25,
                    "summary": "Produce a complete electrical design package for a hypothetical project and defend design choices.",
                    "learn": [
                        {"type": "p", "text": "The capstone project pulls together every skill from Year 2. You will design a complete residential electrical system, document it with drawings and schedules, and justify every decision with code references."},
                        {"type": "list", "items": [
                            "Calculate total electrical load.",
                            "Size branch circuits and feeders.",
                            "Select conductors and conduit fill.",
                            "Specify overcurrent, GFCI, and AFCI protection.",
                            "Design grounding and bonding system.",
                            "Create one-line diagram and panel schedule.",
                            "Cite NEC articles for major design decisions.",
                        ]},
                        {"type": "example", "title": "Capstone deliverable", "text": "Submit a design package: load calculations, one-line diagram, panel schedule, conductor schedule, protection schedule, grounding plan, and a one-page NEC justification memo."},
                        {"type": "tip", "text": "Defend your design by stating the NEC requirement and explaining how your design satisfies it."},
                    ],
                    "check": {
                        "prompt": "Show what you know about the Year 2 capstone.",
                        "questions": [
                            {"q": "A complete residential design package must include all of the following EXCEPT…", "options": ["a list of preferred wire brands", "load calculations", "panel schedule"], "answer": "a list of preferred wire brands", "explain": "Brand selection is an installer or owner choice, not a design package requirement."},
                            {"q": "When defending design choices, you should…", "options": ["cite the relevant NEC article and explain compliance", "state opinions only", "copy code verbatim without explanation"], "answer": "cite the relevant NEC article and explain compliance", "explain": "Good defenses connect design decisions to code requirements with clear reasoning."},
                        ],
                    },
                },
            ],
        },
    ],
}
