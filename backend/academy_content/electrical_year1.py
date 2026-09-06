"""Applied Electrical Engineering — Year 1 (Grades 9–12, Builder/Trade) — full course.

Covers exactly the Year-1 topics from the owner's plan: charge and current,
Ohm's Law, series circuits, parallel circuits, electrical safety, and code —
plus the supporting ideas of voltage, resistance, and power. Theory-only and
simulation-based; no live-wire work is ever instructed. Students should always
follow their local code and a qualified instructor for real electrical work.
"""

ELECTRICAL_YEAR_1 = {
    "slug": "applied-electrical-year-1",
    "title": "Applied Electrical Engineering — Year 1",
    "summary": "Charge, current, Ohm's Law, series and parallel circuits, safety, and code.",
    "description": (
        "Year 1 of the trade pathway turns theory into usable skill. Students start at the "
        "atom — where charge comes from — and follow it into current, voltage, and "
        "resistance. Ohm's Law becomes a working tool for series and parallel circuits, "
        "power calculations size real loads, and the course closes where every real "
        "electrician starts: safety, grounding, and the electrical code. Worked circuit "
        "math, safety-first habits, and code awareness throughout. No live-wire work."
    ),
    "subject": "trade",
    "subject_label": "Trade & Applied Skills",
    "track": "builder",
    "tracks": ["builder"],
    "grades": ["9", "10", "11", "12"],
    "grade_label": "Grades 9–12",
    "status": "published",
    "audience": "High-school Builder/Trade students (ages 14–18) starting a trade pathway; pairs with the site's hands-on lab program.",
    "est_hours": 20,
    "passing_score": 80,
    "learning_objectives": [
        "Explain charge at the atomic level and classify conductors, insulators, and semiconductors.",
        "Define electric current and measure it in amperes.",
        "Apply Ohm's Law (V = IR) to find voltage, current, or resistance.",
        "Analyze series circuits: one path, shared current, additive resistance.",
        "Analyze parallel circuits: branch paths, shared voltage, additive currents.",
        "Compute electric power (P = VI) and energy consumption.",
        "Identify electrical shock hazards and apply safe-work practices (never work live, lockout/tagout, GFCI protection).",
        "Explain why grounding and the electrical code exist and how code protects people and property.",
    ],
    "units": [
        {
            "slug": "charge-and-current",
            "title": "Charge and Current",
            "summary": "Where electricity comes from and how it flows.",
            "order": 1,
            "lessons": [
                {
                    "slug": "charge-atoms",
                    "title": "Charge: Inside the Atom",
                    "order": 1,
                    "minutes": 20,
                    "summary": "Protons, electrons, and why some materials carry current.",
                    "learn": [
                        {"type": "p", "text": "Electricity starts inside the atom. An atom's nucleus holds positively charged PROTONS and neutral NEUTRONS; negatively charged ELECTRONS orbit around them. Opposite charges attract; like charges repel."},
                        {"type": "p", "text": "In many materials the outermost electrons are loosely held. When electrons move from atom to atom, that movement IS electricity. A material's ability to give up electrons decides how it behaves:"},
                        {"type": "list", "items": [
                            "CONDUCTORS — electrons flow easily: copper, aluminum, silver, gold (that is why wire is copper).",
                            "INSULATORS — electrons are tightly bound and do not flow: rubber, glass, plastic, air (wire jackets are insulators).",
                            "SEMICONDUCTORS — in between, controllable: silicon and germanium, the basis of every electronic chip.",
                        ]},
                        {"type": "example", "title": "Static charge you can feel", "text": "Rub a balloon on your hair and it sticks to the wall. Friction moved electrons from your hair to the balloon, giving the balloon a negative charge — static electricity. Current electricity is the same idea, but the electrons keep moving."},
                        {"type": "activity", "title": "Classify the materials", "text": "Sort these into conductor, insulator, or semiconductor: copper pipe (conductor), rubber boot (insulator), glass jar (insulator), silicon chip (semiconductor), aluminum foil (conductor)."},
                    ],
                    "check": {
                        "prompt": "Show what you know about charge.",
                        "questions": [
                            {"q": "Which particle carries a negative charge?", "options": ["electron", "proton", "neutron"], "answer": "electron", "explain": "Electrons are negative; protons are positive; neutrons are neutral."},
                            {"q": "Why is copper used for electrical wire?", "options": ["It is a good conductor — electrons flow easily", "It is an insulator", "It holds a static charge"], "answer": "It is a good conductor — electrons flow easily", "explain": "Copper's loosely held outer electrons flow readily, making it an excellent conductor."},
                            {"q": "Which material is an insulator?", "options": ["rubber", "copper", "aluminum"], "answer": "rubber", "explain": "Rubber binds its electrons tightly — that is why it jackets wires and insulates tools."},
                            {"q": "Electric current is, at the atomic level, the flow of…", "options": ["electrons", "protons", "neutrons"], "answer": "electrons", "explain": "Electrons are the mobile particles that move through a conductor."},
                        ],
                    },
                },
                {
                    "slug": "current-amperes",
                    "title": "Current and the Ampere",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Measuring the flow of charge.",
                    "learn": [
                        {"type": "p", "text": "ELECTRIC CURRENT is the rate at which charge flows past a point. Its unit is the AMPERE (A) — one ampere means one COULOMB of charge (about 6.24 × 10¹⁸ electrons) passing per second."},
                        {"type": "p", "text": "Current = charge ÷ time: I = Q / t. A larger current means more charge moving each second — more work being done, and more heat in the wire."},
                        {"type": "list", "items": [
                            "Current is measured with an AMMETER connected IN SERIES (in the path of the flow).",
                            "Conventional current is drawn flowing from + to − outside the source; electrons actually drift the other way — engineers keep the + to − convention.",
                            "Batteries and most electronics use DIRECT CURRENT (DC), one steady direction. Utility power alternates direction 60 times per second in North America — ALTERNATING CURRENT (AC).",
                        ]},
                        {"type": "example", "title": "Worked example", "text": "A charge of 30 coulombs flows through a wire in 10 seconds. Current = 30 C ÷ 10 s = 3 A."},
                        {"type": "activity", "title": "Reason about scale", "text": "A phone charger may deliver about 2 A; a hair dryer draws about 12 A; a lightning bolt can carry tens of thousands of amps for a split second. Why must thick wire be used for big currents? (More current = more heat; thin wire would overheat.)"},
                    ],
                    "check": {
                        "prompt": "Show what you know about current.",
                        "questions": [
                            {"q": "What is electric current?", "options": ["the rate of charge flow, measured in amperes", "the pressure pushing charge, measured in volts", "the opposition to flow, measured in ohms"], "answer": "the rate of charge flow, measured in amperes", "explain": "Current is charge per time (I = Q/t); the ampere measures it."},
                            {"q": "A charge of 60 coulombs flows in 15 seconds. What is the current?", "options": ["4 A", "0.25 A", "60 A"], "answer": "4 A", "explain": "I = Q/t = 60 ÷ 15 = 4 A."},
                            {"q": "How is an ammeter connected to measure current?", "options": ["in series with the circuit", "in parallel across the source", "it is never connected"], "answer": "in series with the circuit", "explain": "The current must flow THROUGH the ammeter, so it goes in series."},
                            {"q": "Household utility power in North America alternates direction 60 times per second. What do we call that?", "options": ["alternating current (AC)", "direct current (DC)", "static current"], "answer": "alternating current (AC)", "explain": "Utility mains are AC; batteries deliver steady DC."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "ohms-law-circuits",
            "title": "Voltage, Resistance, and Ohm's Law",
            "summary": "The pressure, the friction, and the law that ties them together.",
            "order": 2,
            "lessons": [
                {
                    "slug": "voltage-resistance-ohms-law",
                    "title": "Voltage, Resistance, and Ohm's Law",
                    "order": 3,
                    "minutes": 22,
                    "summary": "V = IR — the most used formula in electrical work.",
                    "learn": [
                        {"type": "p", "text": "Two more ideas complete the picture. VOLTAGE (V), measured in volts, is the electrical \"pressure\" — the potential energy per unit of charge that pushes current around the circuit. RESISTANCE (R), measured in ohms (Ω), is the opposition to flow — narrow wire, long runs, and loads all resist."},
                        {"type": "p", "text": "OHM'S LAW ties them together: V = I × R. Voltage equals current times resistance. Rearranged: I = V/R and R = V/I. If you know any two, you can find the third."},
                        {"type": "example", "title": "Find the current", "text": "A 12 V battery drives a 4 Ω resistor. I = V/R = 12 ÷ 4 = 3 A."},
                        {"type": "example", "title": "Find the resistance", "text": "A device draws 2 A from 120 V. R = V/I = 120 ÷ 2 = 60 Ω."},
                        {"type": "example", "title": "Find the voltage", "text": "A current of 0.5 A flows through an 8 Ω resistor. V = I × R = 0.5 × 8 = 4 V."},
                        {"type": "activity", "title": "The Ohm's Law triangle", "text": "Cover the quantity you want in the triangle V over I·R: to find V multiply, to find I or R divide. Practice: at 120 V, a 15 A circuit can supply a load of R = 120 ÷ 15 = 8 Ω minimum."},
                    ],
                    "check": {
                        "prompt": "Show what you know about Ohm's Law.",
                        "questions": [
                            {"q": "A 12 V battery drives a 4 Ω resistor. What current flows?", "options": ["3 A", "48 A", "0.33 A"], "answer": "3 A", "explain": "I = V/R = 12 ÷ 4 = 3 A."},
                            {"q": "A device draws 2 A from 120 V. What is its resistance?", "options": ["60 Ω", "240 Ω", "0.017 Ω"], "answer": "60 Ω", "explain": "R = V/I = 120 ÷ 2 = 60 Ω."},
                            {"q": "What voltage pushes 0.5 A through an 8 Ω resistor?", "options": ["4 V", "16 V", "8.5 V"], "answer": "4 V", "explain": "V = I × R = 0.5 × 8 = 4 V."},
                            {"q": "Which statement about voltage is correct?", "options": ["It is the electrical pressure that pushes current", "It is the rate of charge flow", "It opposes current flow"], "answer": "It is the electrical pressure that pushes current", "explain": "Voltage is potential energy per charge — the push. Resistance opposes; current flows."},
                        ],
                    },
                },
                {
                    "slug": "series-circuits",
                    "title": "Series Circuits",
                    "order": 4,
                    "minutes": 22,
                    "summary": "One path, shared current, additive resistance.",
                    "learn": [
                        {"type": "p", "text": "In a SERIES circuit there is exactly ONE path for current. Components are connected end to end, like old-style string lights. Three rules govern series circuits:"},
                        {"type": "list", "items": [
                            "The current is the SAME everywhere in the loop.",
                            "The total resistance is the SUM of all resistances: R_total = R₁ + R₂ + R₃…",
                            "The source voltage is SPLIT across the components (each drop follows Ohm's Law), and the drops add up to the source voltage.",
                        ]},
                        {"type": "p", "text": "Consequence: if one component opens (a burnt-out bulb, a loose connection), the whole loop stops — current has no path. That is why series strings of lights go dark when one bulb fails."},
                        {"type": "example", "title": "Worked example", "text": "A 24 V battery powers two resistors in series: 2 Ω and 6 Ω. R_total = 2 + 6 = 8 Ω. Current: I = 24 ÷ 8 = 3 A — the same 3 A through both resistors. Voltage across the 2 Ω: V = 3 × 2 = 6 V. Across the 6 Ω: V = 3 × 6 = 18 V. Check: 6 + 18 = 24 V. ✓"},
                        {"type": "activity", "title": "Battery bank math", "text": "Four 1.5 V batteries in series give 4 × 1.5 = 6 V total. Series adds voltage while current stays the same — which is why tools use series packs for higher voltage."},
                    ],
                    "check": {
                        "prompt": "Show what you know about series circuits.",
                        "questions": [
                            {"q": "What is true about current in a series circuit?", "options": ["it is the same everywhere in the loop", "it splits between components", "it is zero after the first resistor"], "answer": "it is the same everywhere in the loop", "explain": "With one path, the same current flows through every component."},
                            {"q": "A 24 V battery feeds 2 Ω and 6 Ω in series. What is the total current?", "options": ["3 A", "12 A", "8 A"], "answer": "3 A", "explain": "R_total = 8 Ω; I = 24 ÷ 8 = 3 A."},
                            {"q": "In the same circuit, what is the voltage across the 6 Ω resistor?", "options": ["18 V", "6 V", "24 V"], "answer": "18 V", "explain": "V = I × R = 3 × 6 = 18 V. (The 2 Ω takes 6 V; 18 + 6 = 24 V.)"},
                            {"q": "Why does one burnt-out bulb darken an old-style series string?", "options": ["The open bulb breaks the only current path", "The bulb becomes a better conductor", "Voltage doubles everywhere"], "answer": "The open bulb breaks the only current path", "explain": "Series = one path. An open component stops current for the whole loop."},
                        ],
                    },
                },
                {
                    "slug": "parallel-circuits",
                    "title": "Parallel Circuits",
                    "order": 5,
                    "minutes": 22,
                    "summary": "Branch paths, shared voltage, additive currents — how houses are wired.",
                    "learn": [
                        {"type": "p", "text": "In a PARALLEL circuit the components sit on separate BRANCHES between the same two points. Household wiring is parallel — every outlet and light gets the full supply voltage, and one device failing does not kill the others."},
                        {"type": "list", "items": [
                            "The voltage is the SAME across every branch (full source voltage).",
                            "The total current is the SUM of the branch currents: I_total = I₁ + I₂ + I₃…",
                            "The total resistance is LESS than the smallest branch resistance: 1/R_total = 1/R₁ + 1/R₂ + 1/R₃…",
                        ]},
                        {"type": "example", "title": "Worked example: two branches", "text": "A 12 V battery feeds two parallel resistors: 12 Ω and 6 Ω. Branch currents: I₁ = 12 ÷ 12 = 1 A; I₂ = 12 ÷ 6 = 2 A. Total current = 1 + 2 = 3 A. Total resistance: 1/R = 1/12 + 1/6 = 1/12 + 2/12 = 3/12 → R = 12/3 = 4 Ω. Check: V/I = 12 ÷ 3 = 4 Ω ✓. Note 4 Ω < 6 Ω — parallel always lowers total resistance."},
                        {"type": "example", "title": "Why not everything in series?", "text": "Run every lamp in series and adding a lamp raises total resistance, dimming every lamp — and one failure kills all. Parallel keeps each lamp at full voltage and independent. That is why the code requires parallel wiring for branch circuits."},
                        {"type": "activity", "title": "Rule check", "text": "Three 9 Ω resistors in parallel: 1/R = 1/9 + 1/9 + 1/9 = 3/9 → R = 3 Ω. Total current from 27 V would be 27 ÷ 3 = 9 A — three times what one resistor would draw. Adding parallel branches always INCREASES total current."},
                    ],
                    "check": {
                        "prompt": "Show what you know about parallel circuits.",
                        "questions": [
                            {"q": "Which statement is true for a parallel circuit?", "options": ["every branch gets the full source voltage", "every branch gets a share of the voltage", "one open branch stops everything"], "answer": "every branch gets the full source voltage", "explain": "Parallel branches connect across the same two points, so each sees full voltage."},
                            {"q": "A 12 V source feeds 12 Ω and 6 Ω branches in parallel. What is the total current?", "options": ["3 A", "1.5 A", "18 A"], "answer": "3 A", "explain": "1 A + 2 A = 3 A total (each branch follows Ohm's Law)."},
                            {"q": "What is the total resistance of a 12 Ω and a 6 Ω resistor in parallel?", "options": ["4 Ω", "18 Ω", "9 Ω"], "answer": "4 Ω", "explain": "1/R = 1/12 + 1/6 = 3/12, so R = 4 Ω — less than the smaller resistor."},
                            {"q": "When you add another branch to a parallel circuit, total current…", "options": ["increases", "decreases", "stays the same"], "answer": "increases", "explain": "Each new branch adds its own current; total resistance drops, so more current flows."},
                        ],
                    },
                },
                {
                    "slug": "power-energy",
                    "title": "Power and Energy",
                    "order": 6,
                    "minutes": 22,
                    "summary": "P = VI — sizing loads, reading bills, understanding watts and kilowatt-hours.",
                    "learn": [
                        {"type": "p", "text": "ELECTRIC POWER is the rate at which a device uses energy, measured in WATTS (W). The master formula: P = V × I (power = voltage × current)."} ,
                        {"type": "list", "items": [
                            "P = V × I lets you size circuits: a 120 V circuit with a 15 A breaker can supply up to 120 × 15 = 1,800 W.",
                            "Rearranged: I = P/V. A 1,500 W heater on 120 V draws 1,500 ÷ 120 = 12.5 A — near the limit of a 15 A circuit.",
                            "ENERGY is power used over time. Utilities bill in KILOWATT-HOURS (kWh): 1 kWh = 1,000 W running for 1 hour.",
                        ]},
                        {"type": "example", "title": "Worked example: energy bill", "text": "A 100 W bulb runs 10 hours: energy = 100 W × 10 h = 1,000 Wh = 1 kWh. At $0.15/kWh that bulb costs $0.15 for the evening."},
                        {"type": "example", "title": "Worked example: breaker math", "text": "On a 120 V / 15 A circuit (1,800 W max), can you run a 1,200 W microwave and a 900 W toaster together? 1,200 + 900 = 2,100 W > 1,800 W — no. The breaker should trip rather than let the wire overheat."},
                        {"type": "activity", "title": "Load survey", "text": "Read the wattage labels of three appliances at home (or online). Compute each one's current at 120 V with I = P/V, and total the watts you would use if all ran at once on one circuit."},
                    ],
                    "check": {
                        "prompt": "Show what you know about power and energy.",
                        "questions": [
                            {"q": "A 120 V appliance draws 5 A. What power does it use?", "options": ["600 W", "24 W", "125 W"], "answer": "600 W", "explain": "P = V × I = 120 × 5 = 600 W."},
                            {"q": "How much current does a 1,500 W heater draw at 120 V?", "options": ["12.5 A", "1.5 A", "180,000 A"], "answer": "12.5 A", "explain": "I = P/V = 1,500 ÷ 120 = 12.5 A."},
                            {"q": "A 100 W bulb runs for 10 hours. How much energy does it use?", "options": ["1 kWh", "100 kWh", "0.1 kWh"], "answer": "1 kWh", "explain": "100 W × 10 h = 1,000 Wh = 1 kWh."},
                            {"q": "A 120 V circuit is protected by a 15 A breaker. What is the maximum safe load?", "options": ["1,800 W", "120 W", "15 W"], "answer": "1,800 W", "explain": "120 × 15 = 1,800 W. Exceeding it risks tripping or overheating."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "safety-and-code",
            "title": "Safety and Code",
            "summary": "The habits and rules that keep electricians alive.",
            "order": 3,
            "lessons": [
                {
                    "slug": "electrical-safety",
                    "title": "Electrical Safety",
                    "order": 7,
                    "minutes": 22,
                    "summary": "Shock, its causes, and the practices that prevent it.",
                    "learn": [
                        {"type": "p", "text": "Shock happens when your body becomes part of the circuit. Current enters at one contact and exits at another — often hand to hand, or hand to ground through your feet. What hurts is CURRENT through your body, not voltage by itself."},
                        {"type": "list", "items": [
                            "Even small currents matter: about 1 mA is felt; 10–20 mA can make muscles grip so you cannot let go; roughly 100 mA through the heart region can be lethal.",
                            "Body resistance varies — dry skin may be tens of thousands of ohms, but wet skin or a cut can drop it to a few hundred, multiplying the current: I = V/R.",
                            "Dry conditions, insulated tools, and never touching metal parts reduce risk; water is a danger multiplier — that is why GFCIs are required near sinks and outdoors.",
                        ]},
                        {"type": "example", "title": "The master rule", "text": "Treat every conductor as LIVE until you have verified it is dead. Verify with a tester, lock it out, tag it — then work. This one habit prevents nearly every serious shock."},
                        {"type": "p", "text": "Safe-work practices: de-energize and verify before touching; use lockout/tagout (LOTO) so nobody re-energizes while you work; wear the right PPE (insulated gloves where warranted, safety glasses); keep one hand free when testing live gear; and use GFCI protection anywhere water is near."},
                        {"type": "activity", "title": "Write the LOTO sequence", "text": "Put these in order: verify dead; notify others; tag the disconnect; lock it out; shut it down; try to start (it must not). Correct: notify → shutdown → lockout → tagout → verify dead → try-start. That is the standard LOTO order."},
                    ],
                    "check": {
                        "prompt": "Show what you know about electrical safety.",
                        "questions": [
                            {"q": "What actually injures a person in an electric shock?", "options": ["the current through the body", "the voltage alone", "the color of the wire"], "answer": "the current through the body", "explain": "Current is the danger; voltage only matters because it drives current."},
                            {"q": "Why is wet skin so much more dangerous?", "options": ["Water lowers body resistance, so more current flows at the same voltage", "Water adds voltage", "Water cools the circuit"], "answer": "Water lowers body resistance, so more current flows at the same voltage", "explain": "Lower resistance at fixed voltage means higher current (I = V/R) — and current is what hurts."},
                            {"q": "What is the correct first habit before touching any conductor?", "options": ["assume it is live and verify it is dead first", "grab it quickly", "wear gloves only"], "answer": "assume it is live and verify it is dead first", "explain": "Treat everything as live, then prove it dead with a tester before contact."},
                            {"q": "Lockout/tagout (LOTO) exists to…", "options": ["stop someone from re-energizing a circuit you are working on", "make circuits run faster", "replace breakers"], "answer": "stop someone from re-energizing a circuit you are working on", "explain": "LOTO physically locks and labels the disconnect so no one can turn power back on while you work."},
                        ],
                    },
                },
                {
                    "slug": "grounding-code",
                    "title": "Grounding and the Electrical Code",
                    "order": 8,
                    "minutes": 22,
                    "summary": "Why ground exists, what GFCI does, and why code is law.",
                    "learn": [
                        {"type": "p", "text": "GROUNDING connects metal parts that should never carry current — appliance frames, junction boxes, conduit — to the earth (ground). If a hot wire faults to a metal frame, the ground gives the current a low-resistance path back to the source, which makes the breaker trip fast instead of leaving the frame live and deadly."},
                        {"type": "list", "items": [
                            "GROUNDED conductor (neutral) and EQUIPMENT GROUNDING conductor are different jobs: one carries normal current; the other carries fault current only.",
                            "GFCI (ground-fault circuit interrupter) compares current leaving and returning; if even ~5 mA is missing (leaking through you), it opens in milliseconds — faster than a breaker.",
                            "THE CODE (in the U.S., the National Electrical Code, NFPA 70) is a minimum-safety standard adopted into law by states and localities. It governs wire sizing, breaker sizing, box fill, GFCI locations, clearances, and much more.",
                        ]},
                        {"type": "example", "title": "Ground saves a life", "text": "A frayed hot wire touches the metal case of a dryer. Ungrounded: the case becomes live at 120 V — touching it and ground shocks you. Grounded: fault current flows to ground, the breaker trips, and the hazard is removed in a fraction of a second."},
                        {"type": "example", "title": "Where GFCI is required", "text": "Kitchens, bathrooms, laundry, garages, basements, and outdoor receptacles must have GFCI protection because water and wet locations make shocks far more likely."},
                        {"type": "p", "text": "Code is not bureaucracy — every rule traces to an injury or a fire. Work without a permit and inspection where required is not just illegal; it skips the check that catches life-safety mistakes."},
                        {"type": "activity", "title": "Read the labels", "text": "Look at receptacles in your home: which ones have TEST/RESET buttons (GFCI)? Which are near water? Check the panel: which breakers protect kitchens and bathrooms (often GFCI or on GFCI-protected circuits)?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about grounding and code.",
                        "questions": [
                            {"q": "What is the main job of the equipment grounding conductor?", "options": ["carry fault current so the breaker trips fast", "carry the normal load current", "store electricity"], "answer": "carry fault current so the breaker trips fast", "explain": "Grounding gives fault current a safe, low-resistance path that trips the overcurrent device quickly."},
                            {"q": "How does a GFCI protect people?", "options": ["It senses a tiny difference between outgoing and returning current and opens the circuit in milliseconds", "It limits voltage to 5 V", "It makes the breaker bigger"], "answer": "It senses a tiny difference between outgoing and returning current and opens the circuit in milliseconds", "explain": "Missing current means it is leaking somewhere — possibly through a person — and the GFCI cuts power almost instantly."},
                            {"q": "Which locations typically REQUIRE GFCI protection?", "options": ["kitchens, bathrooms, and outdoor receptacles", "only industrial plants", "bedrooms and closets"], "answer": "kitchens, bathrooms, and outdoor receptacles", "explain": "Wet and outdoor locations are where shock risk is highest, so code mandates GFCI there."},
                            {"q": "Why does electrical work require permits and inspections?", "options": ["so a qualified inspector catches life-safety mistakes", "to slow down electricians", "to raise material prices"], "answer": "so a qualified inspector catches life-safety mistakes", "explain": "Inspection is a safety check on real installs — wiring mistakes cause fires and shocks, and code exists to prevent them."},
                        ],
                    },
                },
            ],
        },
    ],
}
