"""Biology: Cells (Grade 9 Scholar) — full published course."""

BIOLOGY_GRADE_9 = {
    "slug": "biology-cells-grade-9",
    "title": "Biology: Cells — The Building Blocks of Life",
    "summary": "From cell theory to organelles to how cells get and use energy.",
    "description": (
        "Every living thing is made of cells. This course opens with the characteristics "
        "of life and cell theory, scales up through microscopes, then tours the cell: "
        "prokaryotes versus eukaryotes, the organelles of animal and plant cells, and the "
        "membrane that controls what enters and leaves. It closes with the two great "
        "energy processes — cellular respiration and photosynthesis — so students "
        "understand how cells stay alive. Scholar-track biology with Foundations-friendly "
        "explanations."
    ),
    "subject": "science",
    "subject_label": "Science",
    "track": "scholar",
    "tracks": ["scholar", "foundations", "builder", "artist"],
    "grades": ["9"],
    "grade_label": "Grade 9",
    "status": "published",
    "audience": "Grade 9 (ages 14–15), Scholar track; also a strong first high-school science for other tracks.",
    "est_hours": 16,
    "passing_score": 80,
    "learning_objectives": [
        "List the shared characteristics of living things.",
        "State the three parts of cell theory and the scientists' evidence behind it.",
        "Explain why cells are small and how microscopy revealed them.",
        "Distinguish prokaryotic cells from eukaryotic cells.",
        "Describe the structure and function of major organelles.",
        "Compare plant and animal cells.",
        "Explain how the cell membrane controls transport.",
        "Summarize cellular respiration and photosynthesis as energy processes.",
    ],
    "units": [
        {
            "slug": "what-is-life",
            "title": "What Is Life?",
            "summary": "Cell theory and the tools that revealed cells.",
            "order": 1,
            "lessons": [
                {
                    "slug": "characteristics-of-life",
                    "title": "Characteristics of Life and Cell Theory",
                    "order": 1,
                    "minutes": 20,
                    "summary": "What makes something alive — and the theory that all life is cellular.",
                    "learn": [
                        {"type": "p", "text": "Living things share key traits: they are made of cells, grow and develop, reproduce, respond to their environment, maintain internal balance (homeostasis), use energy, and — as a species over time — evolve. A rock does none of these; a bacterium does all of them."},
                        {"type": "p", "text": "CELL THEORY has three parts, built on the work of Schleiden, Schwann, and Virchow:"},
                        {"type": "list", "items": [
                            "All living things are made of one or more cells.",
                            "The cell is the basic unit of structure and function in living things.",
                            "All cells come from pre-existing cells.",
                        ]},
                        {"type": "example", "title": "Apply the test", "text": "Is a virus alive? Viruses have genes and reproduce, but only inside a host cell, and they do not use energy or maintain homeostasis on their own. Biologists debate it — which is exactly why clear criteria matter. Cells, by contrast, are unambiguous: they do all the work of life."},
                        {"type": "activity", "title": "Alive or not?", "text": "Sort a list: a seed, a flame, a mushroom, a robot, pond water. Use the traits above. A seed is alive but dormant; a flame grows but does not reproduce or respond with cells — it is not alive."},
                    ],
                    "check": {
                        "prompt": "Show what you know about the characteristics of life and cell theory.",
                        "questions": [
                            {"q": "Which is NOT a characteristic shared by living things?", "options": ["being made of metal", "responding to the environment", "using energy"], "answer": "being made of metal", "explain": "Living things are made of cells — not metal. The other two are genuine life traits."},
                            {"q": "Which statement is part of cell theory?", "options": ["All cells come from pre-existing cells.", "All cells are the same size.", "Cells can appear from nothing under the right conditions."], "answer": "All cells come from pre-existing cells.", "explain": "Virchow's contribution to cell theory: every cell arises from an existing cell."},
                            {"q": "The cell is the basic unit of…", "options": ["structure and function in living things", "energy in nonliving things", "heredity only in plants"], "answer": "structure and function in living things", "explain": "Cell theory states that the cell is the basic unit of structure and function."},
                            {"q": "A bacterium is alive because it…", "options": ["maintains homeostasis and uses energy", "is invisible", "can be grown in a lab dish"], "answer": "maintains homeostasis and uses energy", "explain": "Bacteria are cells: they respond, use energy, maintain balance, reproduce, and more — all the traits of life."},
                        ],
                    },
                },
                {
                    "slug": "microscopes-scale",
                    "title": "Microscopes and the Scale of Cells",
                    "order": 2,
                    "minutes": 20,
                    "summary": "Why we needed microscopes — and why cells stay small.",
                    "learn": [
                        {"type": "p", "text": "Most cells are far too small to see with the naked eye. Robert Hooke coined the word \"cell\" in 1665 looking at cork through a simple microscope; Anton van Leeuwenhoek later observed living single-celled organisms he called \"animalcules.\""},
                        {"type": "p", "text": "A light microscope can magnify roughly 1,000× and resolves structures like nuclei. Electron microscopes magnify far more and reveal organelles and membranes in detail."},
                        {"type": "example", "title": "Sizes", "text": "A typical animal cell is about 10–30 micrometers (µm) across — about 10,000 of them would span a centimeter. A bacterium may be 1–2 µm. Organelles are smaller still."},
                        {"type": "p", "text": "Why are cells small? As a cell grows, its volume grows faster than its surface area. The membrane must exchange nutrients and waste through that surface, so cells stay small enough for the surface to keep up — or they evolve special shapes (long, flat, or folded) to add surface area."},
                        {"type": "activity", "title": "Surface-to-volume demo", "text": "Cut a 1 cm cube of paper and a 2 cm cube. Compute surface area and volume for each. The big cube has 4× the surface but 8× the volume — its surface is struggling to feed its volume. That is why cells split instead of growing forever."},
                    ],
                    "check": {
                        "prompt": "Show what you know about microscopy and cell size.",
                        "questions": [
                            {"q": "Who first described \"cells\" while looking at cork in 1665?", "options": ["Robert Hooke", "Charles Darwin", "Gregor Mendel"], "answer": "Robert Hooke", "explain": "Hooke observed the box-like compartments in cork and named them cells."},
                            {"q": "A typical animal cell is roughly…", "options": ["10–30 micrometers across", "10–30 millimeters across", "1 centimeter across"], "answer": "10–30 micrometers across", "explain": "Animal cells are about 10–30 µm — thousands fit across a centimeter."},
                            {"q": "Why can't cells grow without limit?", "options": ["Volume outgrows surface area, so the membrane can't keep up with exchange", "They would become too heavy to move", "Nuclei cannot store more DNA"], "answer": "Volume outgrows surface area, so the membrane can't keep up with exchange", "explain": "As size increases, volume grows faster than surface area, limiting nutrient and waste exchange."},
                            {"q": "Which tool revealed organelles in detail?", "options": ["electron microscope", "magnifying glass", "telescope"], "answer": "electron microscope", "explain": "Electron microscopes have far higher resolution than light microscopes and reveal organelles and membranes."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "cell-structure",
            "title": "The Structure of Cells",
            "summary": "Prokaryotes, eukaryotes, organelles, and plant vs. animal.",
            "order": 2,
            "lessons": [
                {
                    "slug": "prokaryotic-eukaryotic",
                    "title": "Prokaryotic and Eukaryotic Cells",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Two great families of cells — with and without a nucleus.",
                    "learn": [
                        {"type": "p", "text": "The biggest divide in the living world is between cells WITH a true nucleus and those WITHOUT one."},
                        {"type": "list", "items": [
                            "PROKARYOTIC cells (bacteria and archaea) have no nucleus — their DNA floats in the cytoplasm in a region called the nucleoid. They are small, simple, and lack membrane-bound organelles.",
                            "EUKARYOTIC cells (protists, fungi, plants, animals — you!) keep their DNA inside a membrane-bound NUCLEUS and contain membrane-bound organelles such as mitochondria.",
                        ]},
                        {"type": "example", "title": "Names mean something", "text": "\"Karyon\" is Greek for kernel or nucleus. Pro- means before: prokaryotes came first and have no nucleus. Eu- means true: eukaryotes have a true nucleus."},
                        {"type": "activity", "title": "Sort the cells", "text": "Write a quick rule for each: (1) DNA in a nucleus? (2) membrane-bound organelles? If the answer is yes, the cell is eukaryotic."},
                    ],
                    "check": {
                        "prompt": "Show what you know about prokaryotes and eukaryotes.",
                        "questions": [
                            {"q": "What is the defining difference of a prokaryotic cell?", "options": ["It has no nucleus", "It has mitochondria", "It is always a plant cell"], "answer": "It has no nucleus", "explain": "Prokaryotes lack a nucleus; their DNA sits in the cytoplasm."},
                            {"q": "Which organism is made of eukaryotic cells?", "options": ["a mushroom", "E. coli bacteria", "an archaeon"], "answer": "a mushroom", "explain": "Fungi such as mushrooms are eukaryotes. Bacteria and archaea are prokaryotes."},
                            {"q": "Where is DNA kept in a eukaryotic cell?", "options": ["in the nucleus", "in the cell wall", "floating free in the cytoplasm"], "answer": "in the nucleus", "explain": "Eukaryotes enclose their DNA in a membrane-bound nucleus."},
                            {"q": "Which statement is true?", "options": ["All cells have a nucleus", "Only eukaryotes have membrane-bound organelles like mitochondria", "Prokaryotes are larger than eukaryotes"], "answer": "Only eukaryotes have membrane-bound organelles like mitochondria", "explain": "Membrane-bound organelles are a eukaryotic hallmark; prokaryotes lack them and are generally smaller."},
                        ],
                    },
                },
                {
                    "slug": "organelles",
                    "title": "Organelles: The Cell's Workstations",
                    "order": 4,
                    "minutes": 25,
                    "summary": "Tour the parts of an animal cell and the job each one does.",
                    "learn": [
                        {"type": "p", "text": "An organelle is a structure inside a cell with a specific job — like an organ in your body. Here is the tour of a typical animal cell:"},
                        {"type": "list", "items": [
                            "NUCLEUS — the control center; stores DNA and directs the cell's activities.",
                            "CELL MEMBRANE — the gatekeeper; a flexible lipid bilayer that controls what enters and leaves.",
                            "CYTOPLASM — the jelly-like fluid filling the cell where many reactions happen.",
                            "MITOCHONDRIA — the power plants; convert glucose into usable energy (ATP) through cellular respiration.",
                            "RIBOSOMES — protein factories; read RNA and build proteins (found free or on the rough ER).",
                            "ENDOPLASMIC RETICULUM (ER) — a membrane highway; rough ER (studded with ribosomes) processes proteins, smooth ER makes lipids.",
                            "GOLGI APPARATUS — the packaging and shipping center; modifies, sorts, and sends proteins where they are needed.",
                            "LYSOSOMES — the recycling crew; break down waste and worn-out parts with digestive enzymes.",
                        ]},
                        {"type": "example", "title": "Cell city analogy", "text": "Think of the cell as a city: nucleus = city hall (directs), mitochondria = power plant (energy), ribosomes = factories (proteins), ER = roads and workshops, Golgi = post office (ships packages), lysosomes = sanitation (recycling)."},
                        {"type": "activity", "title": "Job interview", "text": "For each organelle, answer: What would break if this organelle stopped working? If mitochondria stopped, the cell would run out of ATP; if Golgi stopped, proteins would never ship to their destinations."},
                    ],
                    "check": {
                        "prompt": "Show what you know about organelles.",
                        "questions": [
                            {"q": "Which organelle is the cell's control center, storing DNA?", "options": ["nucleus", "ribosome", "lysosome"], "answer": "nucleus", "explain": "The nucleus houses DNA and directs cell activities."},
                            {"q": "Which organelle produces ATP by cellular respiration?", "options": ["mitochondria", "Golgi apparatus", "nucleus"], "answer": "mitochondria", "explain": "Mitochondria convert glucose into the cell's energy currency, ATP."},
                            {"q": "Ribosomes are the cell's…", "options": ["protein factories", "recycling center", "shipping office"], "answer": "protein factories", "explain": "Ribosomes read messenger RNA and assemble proteins from amino acids."},
                            {"q": "Which organelle packages and ships proteins to their destinations?", "options": ["Golgi apparatus", "lysosome", "cell wall"], "answer": "Golgi apparatus", "explain": "The Golgi modifies, sorts, and packages proteins for delivery."},
                            {"q": "Lysosomes break down waste and worn-out parts. What cell type would have FEW of them?", "options": ["a bacterial cell", "an animal cell", "a white blood cell"], "answer": "a bacterial cell", "explain": "Prokaryotes lack membrane-bound organelles entirely — no lysosomes. (A white blood cell uses lysosomes heavily to digest invaders.)"},
                        ],
                    },
                },
                {
                    "slug": "plant-vs-animal",
                    "title": "Plant Cells vs. Animal Cells",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Three structures that set plant cells apart.",
                    "learn": [
                        {"type": "p", "text": "Plant and animal cells are both eukaryotic, so both have nuclei and mitochondria. But plant cells add three signature structures:"},
                        {"type": "list", "items": [
                            "CELL WALL — a rigid outer layer of cellulose outside the membrane that supports the cell and gives plants their shape (animals have none).",
                            "CHLOROPLASTS — organelles that capture sunlight and make glucose by photosynthesis (animals have none).",
                            "LARGE CENTRAL VACUOLE — a big storage sac for water, which also helps support the cell by pressing against the wall.",
                        ]},
                        {"type": "example", "title": "See the difference", "text": "Look at plant cells under a microscope and you can spot neat rectangular boxes (cell walls) with green dots (chloroplasts). Animal cells look rounder, with no wall and no green."},
                        {"type": "activity", "title": "Venn diagram", "text": "Draw a Venn diagram: both circles share nucleus, membrane, mitochondria, ribosomes, ER, Golgi. Plant-only side: cell wall, chloroplasts, large central vacuole. Animal-only side: small vacuoles (or none), lysosomes are more common in animals than plants."},
                    ],
                    "check": {
                        "prompt": "Show what you know about plant vs. animal cells.",
                        "questions": [
                            {"q": "Which structure is found in plant cells but NOT animal cells?", "options": ["cell wall", "nucleus", "mitochondria"], "answer": "cell wall", "explain": "The rigid cellulose cell wall is a plant-cell signature; animal cells have only the membrane."},
                            {"q": "Which organelle turns sunlight into glucose?", "options": ["chloroplast", "mitochondrion", "lysosome"], "answer": "chloroplast", "explain": "Chloroplasts perform photosynthesis, capturing light energy as chemical energy in glucose."},
                            {"q": "Why can plant cells stand tall without bones?", "options": ["The cell wall and a large water-filled vacuole provide support", "They photosynthesize", "They do not need support"], "answer": "The cell wall and a large water-filled vacuole provide support", "explain": "The rigid wall plus turgor pressure from the central vacuole holds plants up."},
                            {"q": "Which organelle do BOTH plant and animal cells use to release energy?", "options": ["mitochondria", "chloroplasts", "cell wall"], "answer": "mitochondria", "explain": "Both cell types respire — mitochondria make ATP in plants and animals alike."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "cell-processes",
            "title": "How Cells Work",
            "summary": "The membrane, respiration, and photosynthesis.",
            "order": 3,
            "lessons": [
                {
                    "slug": "membrane-transport",
                    "title": "The Cell Membrane and Transport",
                    "order": 6,
                    "minutes": 20,
                    "summary": "The gatekeeper: what gets in, what goes out, and how.",
                    "learn": [
                        {"type": "p", "text": "The cell membrane is a PHOSPHOLIPID BILAYER — two layers of fat-like molecules with proteins floating in them. It is SELECTIVELY PERMEABLE: it lets some molecules through and blocks others."},
                        {"type": "list", "items": [
                            "Small nonpolar molecules (oxygen, carbon dioxide) slip straight through the bilayer.",
                            "Water crosses through special channel proteins called aquaporins.",
                            "Ions and larger molecules (glucose) need transport proteins.",
                            "DIFFUSION moves particles from high concentration to low concentration — no energy needed (passive).",
                            "OSMOSIS is the diffusion of WATER across a membrane toward higher solute concentration.",
                            "When the cell must move things AGAINST the gradient (low → high), it uses ACTIVE TRANSPORT and spends ATP, often via protein pumps.",
                        ]},
                        {"type": "example", "title": "Real-world osmosis", "text": "A wilted plant revives after watering because water moves into root cells by osmosis. Salting a slug or curing meat works by the same physics in reverse: water leaves the cells."},
                        {"type": "activity", "title": "Gummy bear lab (safely)", "text": "Soak a gummy bear in plain water overnight — it swells (water enters by osmosis). Soak another in very salty water — it shrinks (water leaves). The membrane of the bear is not a real cell membrane, but the diffusion lesson is identical."},
                    ],
                    "check": {
                        "prompt": "Show what you know about membrane transport.",
                        "questions": [
                            {"q": "The cell membrane is described as selectively permeable because it…", "options": ["lets some substances through and blocks others", "blocks everything", "lets everything through"], "answer": "lets some substances through and blocks others", "explain": "Selective permeability is controlled passage — the membrane chooses based on size, charge, and solubility."},
                            {"q": "Diffusion moves particles from…", "options": ["high to low concentration", "low to high concentration", "random to organized"], "answer": "high to low concentration", "explain": "Particles spread out along their gradient until concentrations equalize — passive, no energy."},
                            {"q": "What is osmosis?", "options": ["the diffusion of water across a membrane", "the transport of proteins", "the breakdown of glucose"], "answer": "the diffusion of water across a membrane", "explain": "Osmosis is specifically water diffusing across a membrane toward higher solute concentration."},
                            {"q": "Moving a molecule AGAINST its concentration gradient requires…", "options": ["active transport and energy (ATP)", "no energy at all", "osmosis only"], "answer": "active transport and energy (ATP)", "explain": "Pushing molecules from low to high concentration goes against diffusion and costs cellular energy."},
                        ],
                    },
                },
                {
                    "slug": "cellular-respiration",
                    "title": "Cellular Respiration: Turning Food into Energy",
                    "order": 7,
                    "minutes": 20,
                    "summary": "How cells cash in glucose for ATP.",
                    "learn": [
                        {"type": "p", "text": "Cellular respiration is how cells release the energy stored in food. It breaks down glucose with oxygen to make ATP, the molecule cells spend like currency."},
                        {"type": "p", "text": "Overall equation: C₆H₁₂O₆ (glucose) + 6 O₂ → 6 CO₂ + 6 H₂O + ATP. You can read it as: sugar + oxygen yields carbon dioxide + water + usable energy."},
                        {"type": "list", "items": [
                            "GLYCOLYSIS — in the cytoplasm; splits glucose into two pyruvate molecules, producing a little ATP (and does not need oxygen).",
                            "KREBS CYCLE (citric acid cycle) — inside the mitochondria; processes pyruvate further, releasing carbon dioxide and electrons.",
                            "ELECTRON TRANSPORT CHAIN — in the inner mitochondrial membrane; uses those electrons to drive the big ATP payoff, with oxygen as the final electron acceptor.",
                        ]},
                        {"type": "example", "title": "Why you breathe", "text": "You inhale oxygen for one main reason: to be the final electron acceptor in the electron transport chain. You exhale carbon dioxide because it is a waste product of breaking down glucose."},
                        {"type": "activity", "title": "Energy audit", "text": "Trace one glucose molecule: where does glycolysis happen (cytoplasm), where do the Krebs cycle and electron transport chain happen (mitochondria)? Which stage needs oxygen (the chain — which is why breathing matters)?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about cellular respiration.",
                        "questions": [
                            {"q": "What is the main purpose of cellular respiration?", "options": ["to produce ATP from glucose", "to make glucose from sunlight", "to build proteins"], "answer": "to produce ATP from glucose", "explain": "Respiration releases the chemical energy in glucose and stores it as ATP."},
                            {"q": "Which molecules are the INPUTS of aerobic respiration?", "options": ["glucose and oxygen", "carbon dioxide and water", "ATP and oxygen"], "answer": "glucose and oxygen", "explain": "C₆H₁₂O₆ + O₂ are consumed; CO₂, H₂O, and ATP are produced."},
                            {"q": "Where do the Krebs cycle and electron transport chain take place?", "options": ["inside the mitochondria", "in the cytoplasm", "in the nucleus"], "answer": "inside the mitochondria", "explain": "Only glycolysis happens in the cytoplasm; the oxygen-using stages happen inside mitochondria."},
                            {"q": "Which stage of respiration requires oxygen as the final electron acceptor?", "options": ["electron transport chain", "glycolysis", "the Krebs cycle"], "answer": "electron transport chain", "explain": "Oxygen accepts electrons at the end of the chain — without it, aerobic respiration stalls."},
                        ],
                    },
                },
                {
                    "slug": "photosynthesis",
                    "title": "Photosynthesis: Capturing Sunlight",
                    "order": 8,
                    "minutes": 20,
                    "summary": "How plants build glucose from light, water, and carbon dioxide.",
                    "learn": [
                        {"type": "p", "text": "Photosynthesis is the reverse of respiration in the simplest sense: plants capture light energy and store it as chemical energy in glucose."},
                        {"type": "p", "text": "Overall equation: 6 CO₂ + 6 H₂O + light energy → C₆H₁₂O₆ + 6 O₂. Carbon dioxide and water, powered by sunlight inside chloroplasts, become glucose — and release oxygen as a byproduct."},
                        {"type": "list", "items": [
                            "LIGHT-DEPENDENT REACTIONS — in the thylakoid membranes of the chloroplast; chlorophyll absorbs light, water is split, oxygen is released, and energy-carrying molecules (ATP, NADPH) are made.",
                            "CALVIN CYCLE — in the stroma (the fluid around the thylakoids); uses ATP and NADPH to build glucose from carbon dioxide.",
                        ]},
                        {"type": "example", "title": "The planet's kitchen", "text": "Almost every ecosystem depends on photosynthesis: producers make glucose, herbivores eat producers, carnivores eat herbivores. The oxygen in every breath you have taken was released by photosynthesis."},
                        {"type": "activity", "title": "Spot the connection", "text": "Write both equations side by side. Photosynthesis: CO₂ + H₂O + light → glucose + O₂. Respiration: glucose + O₂ → CO₂ + H₂O + ATP. The outputs of one are the inputs of the other — a cycle that keeps the biosphere running."},
                    ],
                    "check": {
                        "prompt": "Show what you know about photosynthesis.",
                        "questions": [
                            {"q": "Where does photosynthesis take place in a plant cell?", "options": ["in the chloroplasts", "in the mitochondria", "in the nucleus"], "answer": "in the chloroplasts", "explain": "Chloroplasts contain chlorophyll and run the light reactions and Calvin cycle."},
                            {"q": "Which are the inputs of photosynthesis?", "options": ["carbon dioxide, water, and light", "glucose and oxygen", "ATP and NADPH"], "answer": "carbon dioxide, water, and light", "explain": "6 CO₂ + 6 H₂O + light energy produce glucose and oxygen."},
                            {"q": "What gas is released as a byproduct of photosynthesis?", "options": ["oxygen", "carbon dioxide", "nitrogen"], "answer": "oxygen", "explain": "Water is split during the light reactions and oxygen is released."},
                            {"q": "How do plants relate to animals in the energy cycle?", "options": ["Plants make glucose and oxygen that animals use for respiration; animals release CO₂ that plants use", "Plants and animals both photosynthesize", "Animals make glucose that plants eat"], "answer": "Plants make glucose and oxygen that animals use for respiration; animals release CO₂ that plants use", "explain": "Photosynthesis and respiration are complementary — each feeds the other."},
                        ],
                    },
                },
            ],
        },
    ],
}
