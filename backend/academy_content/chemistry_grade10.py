"""Chemistry — Grade 10 (full published course)."""

CHEMISTRY_GRADE_10 = {
    "slug": "chemistry-grade-10",
    "title": "Chemistry",
    "summary": "Atomic structure, the periodic table, and chemical reactions.",
    "description": (
        "This high-school chemistry course introduces the nature of matter, atomic structure, "
        "periodic trends, bonding, stoichiometry, and common reaction types. "
        "Students balance equations, predict products, and connect chemistry to real-world technology."
    ),
    "subject": "science",
    "subject_label": "Science",
    "track": "scholar",
    "tracks": ["scholar", "builder"],
    "grades": ["10", "11", "12"],
    "grade_label": "Grades 10–12",
    "status": "published",
    "audience": "High-school students in the Scholar track; Builder-track students interested in technical chemistry.",
    "est_hours": 30,
    "passing_score": 80,
    "learning_objectives": [
        "Describe the structure of the atom and the roles of subatomic particles.",
        "Use the periodic table to predict properties of elements.",
        "Write and name chemical formulas and compounds.",
        "Balance chemical equations using the law of conservation of mass.",
        "Classify reaction types and predict products.",
    ],
    "units": [
        {
            "slug": "atomic-structure-and-periodic-table",
            "title": "Atomic Structure and the Periodic Table",
            "summary": "Atoms, isotopes, electron configuration, and periodic trends.",
            "order": 1,
            "lessons": [
                {
                    "slug": "atomic-structure",
                    "title": "Atomic Structure",
                    "order": 1,
                    "minutes": 20,
                    "summary": "Protons, neutrons, electrons, and isotopes.",
                    "learn": [
                        {"type": "p", "text": "An atom is the smallest unit of an element that keeps the element's identity. The nucleus holds protons (positive) and neutrons (neutral). Electrons (negative) move around the nucleus in energy levels."},
                        {"type": "list", "items": [
                            "Atomic number = number of protons.",
                            "Mass number = protons + neutrons.",
                            "Isotopes have the same protons but different neutrons.",
                            "Electrons occupy shells; the outermost shell holds valence electrons.",
                        ]},
                        {"type": "example", "title": "Carbon-12 and Carbon-14", "text": "Carbon always has 6 protons. Carbon-12 has 6 neutrons. Carbon-14 has 8 neutrons. Both are carbon; they are isotopes."},
                        {"type": "activity", "title": "Draw an atom", "text": "Draw a neutral sodium atom (Na): 11 protons, 12 neutrons, 11 electrons. Label the nucleus and shells."},
                    ],
                    "check": {
                        "prompt": "Show what you know about atomic structure.",
                        "questions": [
                            {"q": "What particle determines the element's identity?", "options": ["proton", "neutron", "electron"], "answer": "proton", "explain": "The number of protons (atomic number) defines the element."},
                            {"q": "If an atom has 6 protons and 6 neutrons, what is its mass number?", "options": ["12", "6", "0"], "answer": "12", "explain": "Mass number = protons + neutrons = 6 + 6 = 12."},
                            {"q": "Isotopes have the same number of…", "options": ["protons", "neutrons", "electrons"], "answer": "protons", "explain": "Isotopes share the same atomic number (protons) but differ in neutrons."},
                        ],
                    },
                },
                {
                    "slug": "periodic-table-trends",
                    "title": "Periodic Table Trends",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Groups, periods, and trends in atomic properties.",
                    "learn": [
                        {"type": "p", "text": "The periodic table arranges elements by increasing atomic number. Elements in the same group (column) have similar chemical properties because they have the same number of valence electrons."},
                        {"type": "list", "items": [
                            "Groups = columns; periods = rows.",
                            "Metals are on the left, nonmetals on the right.",
                            "Atomic radius increases down a group.",
                            "Electronegativity increases across a period.",
                        ]},
                        {"type": "example", "title": "Group 1: Alkali metals", "text": "Lithium, sodium, potassium. Each has 1 valence electron. They are soft, reactive metals that explode in water."},
                    ],
                    "check": {
                        "prompt": "Show what you know about periodic trends.",
                        "questions": [
                            {"q": "Elements in the same group have the same number of…", "options": ["valence electrons", "protons", "neutrons"], "answer": "valence electrons", "explain": "Group number (for main group elements) equals the number of valence electrons."},
                            {"q": "Which is a property of metals?", "options": ["good conductors of electricity", "brittle solids", "poor conductors"], "answer": "good conductors of electricity", "explain": "Metals are typically shiny, malleable, and conduct electricity well."},
                        ],
                    },
                },
                {
                    "slug": "chemical-bonding",
                    "title": "Chemical Bonding",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Ionic, covalent, and metallic bonds.",
                    "learn": [
                        {"type": "p", "text": "Atoms bond to achieve full outer electron shells. Ionic bonds form when electrons transfer (metal + nonmetal). Covalent bonds form when electrons are shared (nonmetal + nonmetal)."},
                        {"type": "list", "items": [
                            "Ionic: electron transfer → ions → electrostatic attraction.",
                            "Covalent: electron sharing → molecules.",
                            "Metallic: 'sea of electrons' around metal cations.",
                        ]},
                        {"type": "example", "title": "NaCl", "text": "Sodium gives up 1 electron to become Na+. Chlorine gains 1 electron to become Cl-. Opposite charges attract, forming an ionic bond."},
                    ],
                    "check": {
                        "prompt": "Show what you know about chemical bonding.",
                        "questions": [
                            {"q": "Which bond involves electron transfer?", "options": ["ionic", "covalent", "metallic"], "answer": "ionic", "explain": "Ionic bonds form when electrons transfer from a metal to a nonmetal."},
                            {"q": "A molecule of water (H₂O) is held together by…", "options": ["covalent bonds", "ionic bonds", "metallic bonds"], "answer": "covalent bonds", "explain": "Oxygen and hydrogen share electrons covalently."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "reactions-and-stoichiometry",
            "title": "Reactions and Stoichiometry",
            "summary": "Balancing equations and predicting products.",
            "order": 2,
            "lessons": [
                {
                    "slug": "balancing-equations",
                    "title": "Balancing Chemical Equations",
                    "order": 4,
                    "minutes": 20,
                    "summary": "Law of conservation of mass and coefficients.",
                    "learn": [
                        {"type": "p", "text": "Atoms are never created or destroyed in a chemical reaction. A balanced equation shows the same number of each type of atom on both sides. Coefficients (the numbers in front of formulas) adjust quantities."},
                        {"type": "example", "title": "Balance H₂ + O₂ → H₂O", "text": "Left: 2 H, 2 O. Right: 2 H, 1 O. Put coefficient 2 before H₂O: 2H + O₂ → 2H₂O. Now: 4 H, 2 O on each side."},
                        {"type": "activity", "title": "Balance three equations", "text": "Balance these: C + O₂ → CO₂; Mg + HCl → MgCl₂ + H₂; Al + O₂ → Al₂O₃."},
                    ],
                    "check": {
                        "prompt": "Show what you know about balancing equations.",
                        "questions": [
                            {"q": "What law requires equations to be balanced?", "options": ["conservation of mass", "conservation of energy", "gravity"], "answer": "conservation of mass", "explain": "Mass is neither created nor destroyed in a chemical reaction."},
                            {"q": "In the equation 2H₂ + O₂ → 2H₂O, the coefficient 2 in front of H₂ means…", "options": ["two molecules of H₂", "two atoms of hydrogen", "two atoms of oxygen"], "answer": "two molecules of H₂", "explain": "Coefficients count molecules, not individual atoms."},
                        ],
                    },
                },
                {
                    "slug": "types-of-reactions",
                    "title": "Types of Chemical Reactions",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Synthesis, decomposition, single replacement, double replacement, combustion.",
                    "learn": [
                        {"type": "p", "text": "Chemists classify reactions by pattern. Synthesis (A + B → AB) builds compounds. Decomposition (AB → A + B) breaks them apart. Single replacement swaps elements; double replacement swaps partners. Combustion burns fuel in oxygen."},
                        {"type": "list", "items": [
                            "Synthesis: 2H₂ + O₂ → 2H₂O.",
                            "Decomposition: 2H₂O₂ → 2H₂O + O₂.",
                            "Single replacement: Zn + 2HCl → ZnCl₂ + H₂.",
                            "Double replacement: AgNO₃ + NaCl → AgCl + NaNO₃.",
                        ]},
                        {"type": "example", "title": "Combustion", "text": "CH₄ + 2O₂ → CO₂ + 2H₂O. Methane burns in oxygen to produce carbon dioxide and water."},
                    ],
                    "check": {
                        "prompt": "Show what you know about reaction types.",
                        "questions": [
                            {"q": "Which reaction type has two reactants forming one product?", "options": ["synthesis", "decomposition", "combustion"], "answer": "synthesis", "explain": "Synthesis means combining simpler substances into a more complex one."},
                            {"q": "A reaction where one compound breaks into simpler substances is…", "options": ["decomposition", "synthesis", "single replacement"], "answer": "decomposition", "explain": "Decomposition is the breaking down of a compound into simpler parts."},
                        ],
                    },
                },
                {
                    "slug": "stoichiometry-basics",
                    "title": "Stoichiometry Basics",
                    "order": 6,
                    "minutes": 20,
                    "summary": "Mole ratios and mass-mass calculations.",
                    "learn": [
                        {"type": "p", "text": "Stoichiometry uses mole ratios from a balanced equation to calculate how much reactant is needed or product is formed. The steps: balance the equation, convert to moles, use the ratio, convert to desired units."},
                        {"type": "example", "title": "Mass-mass problem", "text": "How many grams of water form from 4 g of H₂? 2H₂ + O₂ → 2H₂O. Moles H₂ = 4 g ÷ 2 g/mol = 2 mol. Ratio 2 mol H₂ → 2 mol H₂O. Mass = 2 mol × 18 g/mol = 36 g."},
                    ],
                    "check": {
                        "prompt": "Show what you know about stoichiometry basics.",
                        "questions": [
                            {"q": "What does stoichiometry calculate?", "options": ["amounts of reactants and products", "speed of a reaction", "color of a flame"], "answer": "amounts of reactants and products", "explain": "Stoichiometry uses mole ratios to find quantities in reactions."},
                            {"q": "In a balanced equation, the coefficients give the…", "options": ["mole ratio", "mass ratio", "volume ratio"], "answer": "mole ratio", "explain": "Coefficients represent the relative number of moles for each substance."},
                        ],
                    },
                },
            ],
        },
    ],
}
