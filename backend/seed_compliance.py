"""Compliance modules content (OSHA 10, NFPA 70E, PPE, LOTO Cert) — separate track from core curriculum."""

COMPLIANCE_MODULES = [
    {
        "slug": "osha-10-electrical",
        "track": "compliance",
        "order": 101,
        "title": "OSHA 10 — Electrical Industry Awareness",
        "summary": "10-hour OSHA general industry awareness adapted for electrical apprentices. Covers hazards, PPE, machine guarding, materials handling, and worker rights.",
        "objectives": [
            "Identify the four primary electrical workplace hazards (shock, arc flash, falls, materials)",
            "Describe employer and employee responsibilities under OSHA",
            "Apply hazard recognition to a typical jobsite walk-down",
            "Know your right to refuse unsafe work",
        ],
        "safety": [
            "Always report unsafe conditions to your supervisor in writing",
            "Never bypass an interlock or safety device",
            "Stop work if you feel unsafe — it is your right",
        ],
        "tools": ["OSHA 1910 reference", "Jobsite checklist"],
        "scripture": {"ref": "Proverbs 24:6", "text": "Surely you need guidance to wage war, and victory is won through many advisers."},
        "tasks": [
            "Complete the OSHA 10 hazard recognition worksheet",
            "Walk a job site (or photo set) and identify five hazards",
            "Pass the awareness quiz at 70%+",
        ],
        "competencies": ["safety-ppe", "professionalism"],
        "hours": 10,
        "expires_months": 36,
    },
    {
        "slug": "nfpa-70e-awareness",
        "track": "compliance",
        "order": 102,
        "title": "NFPA 70E — Workplace Electrical Safety",
        "summary": "Awareness training on the Standard for Electrical Safety in the Workplace: arc flash boundaries, PPE categories, and energized work permits.",
        "objectives": [
            "Read and interpret an NFPA 70E arc flash label",
            "Match PPE categories 1–4 to hazard analysis results",
            "Understand when an energized work permit is required",
            "Recognize the role of qualified vs unqualified persons",
        ],
        "safety": [
            "Never enter an arc flash boundary without arc-rated PPE",
            "Energized work is the exception — de-energize whenever possible",
        ],
        "tools": ["NFPA 70E reference card", "Arc flash label set"],
        "scripture": {"ref": "1 Corinthians 14:40", "text": "But everything should be done in a fitting and orderly way."},
        "tasks": [
            "Decode three sample arc flash labels",
            "Complete a PPE category selection exercise",
            "Pass the awareness quiz",
        ],
        "competencies": ["safety-ppe"],
        "hours": 6,
        "expires_months": 12,
    },
    {
        "slug": "ppe-fitting",
        "track": "compliance",
        "order": 103,
        "title": "PPE Selection, Fit & Maintenance",
        "summary": "Hands-on PPE training: Class 0 gloves with leather protectors, arc-rated clothing, eye protection, and inspection schedules.",
        "objectives": [
            "Select correct PPE class for a given hazard",
            "Properly inspect, fit, and don rubber insulating gloves",
            "Maintain a personal PPE log with inspection dates",
        ],
        "safety": [
            "Inspect gloves before every use — visual + air test",
            "Re-test rubber gloves every 6 months",
        ],
        "tools": ["Class 0 gloves & protectors", "Glove air-test kit", "Safety glasses", "Arc-rated long sleeve"],
        "scripture": {"ref": "Ephesians 6:11", "text": "Put on the full armor of God, so that you can take your stand."},
        "tasks": [
            "Inspect and air-test a pair of rubber gloves",
            "Don full PPE within 90 seconds",
            "Submit your dated PPE inspection log",
        ],
        "competencies": ["safety-ppe", "tools-equipment"],
        "hours": 4,
        "expires_months": 12,
    },
    {
        "slug": "loto-certification",
        "track": "compliance",
        "order": 104,
        "title": "Lockout/Tagout — Certification",
        "summary": "Full LOTO certification: written procedure, group LOTO, energy-isolation devices, and verification practices for industrial settings.",
        "objectives": [
            "Write a LOTO procedure for a multi-source machine",
            "Execute group LOTO with multi-lock hasp",
            "Perform test-verify-test on every isolation point",
        ],
        "safety": [
            "One worker, one lock, one key — always",
            "Group LOTO requires a primary authorized employee",
            "Re-LOTO after every shift change",
        ],
        "tools": ["Padlocks (color-coded)", "Multi-lock hasps", "Tags", "Voltage tester"],
        "scripture": {"ref": "Proverbs 22:3", "text": "The prudent see danger and take refuge."},
        "tasks": [
            "Write a LOTO procedure for a panelboard with two feeds",
            "Lead a group LOTO with two partners",
            "Pass the certification quiz at 80%+",
        ],
        "competencies": ["safety-ppe", "professionalism"],
        "hours": 6,
        "expires_months": 6,
    },
]


COMPLIANCE_QUIZZES = {
    "osha-10-electrical": [
        {"q": "OSHA 10 covers approximately how many hours of safety training?", "options": ["4", "10", "30", "40"], "answer": 1},
        {"q": "Workers have the right to:", "options": ["Refuse unsafe work", "Skip PPE if uncomfortable", "Ignore signage", "Bypass interlocks"], "answer": 0},
        {"q": "Reporting unsafe conditions should be:", "options": ["Avoided to keep peace", "Done in writing to a supervisor", "Anonymous only", "Postponed to weekly meetings"], "answer": 1},
        {"q": "The four main electrical workplace hazards include:", "options": ["Shock, arc flash, falls, materials", "Noise, dust, heat, cold", "Lifting, slipping, eyes, ears", "Solvents, fumes, gas, fire"], "answer": 0},
    ],
    "nfpa-70e-awareness": [
        {"q": "NFPA 70E PPE categories are numbered:", "options": ["0–3", "1–4", "1–10", "A–F"], "answer": 1},
        {"q": "Arc-rated clothing is rated in:", "options": ["PSI", "cal/cm²", "kV", "Amps"], "answer": 1},
        {"q": "Energized work requires:", "options": ["A signed permit", "Two electricians", "Daylight only", "No special procedure"], "answer": 0},
        {"q": "A qualified person under NFPA 70E:", "options": ["Anyone with a hard hat", "Has training and demonstrated competency on the equipment", "Holds any electrician's license", "Is the supervisor"], "answer": 1},
    ],
    "ppe-fitting": [
        {"q": "Rubber insulating gloves should be air-tested:", "options": ["Once a year", "Before every use", "Only if wet", "After being dropped"], "answer": 1},
        {"q": "Class 0 rubber gloves are rated for max use voltage of:", "options": ["500V", "1,000V", "7,500V", "17,000V"], "answer": 1},
        {"q": "Leather protectors are worn:", "options": ["Inside rubber gloves", "Outside rubber gloves", "Instead of rubber gloves", "Only in cold weather"], "answer": 1},
        {"q": "ANSI Z87.1 is the standard for:", "options": ["Hard hats", "Eye protection", "Footwear", "Hearing protection"], "answer": 1},
    ],
    "loto-certification": [
        {"q": "Group LOTO uses:", "options": ["One shared lock", "Multi-lock hasps so each worker applies their own lock", "Tags only", "No locks"], "answer": 1},
        {"q": "Test-verify-test means:", "options": ["Test with a known-good tester before and after a known-live source", "Test three times in a row", "Three different testers", "Test only after work is complete"], "answer": 0},
        {"q": "After a shift change, LOTO should be:", "options": ["Left in place by previous shift", "Removed and reapplied by the new worker", "Tagged out only", "Not required"], "answer": 1},
        {"q": "An energy-isolation device must be:", "options": ["Only valves", "Only breakers", "Capable of being locked in the safe position", "Color-coded yellow"], "answer": 2},
    ],
}
