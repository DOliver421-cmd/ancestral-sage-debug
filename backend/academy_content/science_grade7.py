"""Science — Grade 7 (published core)."""

SCIENCE_GRADE_7 = {
    "slug": "science-grade-7",
    "title": "Science — Grade 7",
    "summary": "Cells, heredity, ecosystems, and Earth history.",
    "description": "Seventh-grade science integrates life science and Earth science — cells, genes, ecosystems, and deep time.",
    "subject": "science",
    "subject_label": "Science",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["7"],
    "grade_label": "Grade 7",
    "status": "published",
    "audience": "Grade 7 (ages 12–13), Foundations track.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": ["Model cell structure and function.", "Explain heredity and natural selection.", "Describe Earth history and ecosystem change."],
    "units": [
        {"slug": "cells-genes", "title": "Cells and Genes", "summary": "Units of life.", "order": 1, "lessons": [
            {"slug": "cells-and-systems-grade7", "title": "Cells and Systems", "order": 1, "minutes": 18, "summary": "Nucleus, mitochondria, chloroplasts.", "learn": [{"type": "p", "text": "Cells are basic units of life. Plant and animal cells share a nucleus and mitochondria; plants also have chloroplasts and cell walls. Cells form tissues and organs."}, {"type": "list", "items": ["Nucleus stores information.", "Mitochondria release energy.", "Chloroplasts capture sunlight in plants."]}], "check": {"prompt": "Cells.", "questions": [{"q": "Which captures sunlight in plant cells?", "options": ["chloroplast", "mitochondria", "cell wall only"], "answer": "chloroplast", "explain": "Chloroplasts hold chlorophyll for photosynthesis."}, {"q": "Cells organize into…", "options": ["tissues and organs", "only rocks", "nothing larger"], "answer": "tissues and organs", "explain": "Cells build systems."}]}},
            {"slug": "heredity-grade7", "title": "Heredity and Variation", "order": 2, "minutes": 18, "summary": "Genes and variation.", "learn": [{"type": "p", "text": "Genes are instructions passed from parents. Sexual reproduction mixes genes and creates variation; mutations add new variation."}, {"type": "list", "items": ["Genes on chromosomes code traits.", "Variation fuels natural selection.", "Environment also shapes traits."]}], "check": {"prompt": "Heredity.", "questions": [{"q": "Genes are…", "options": ["instructions passed from parents", "only learned at school", "never inherited"], "answer": "instructions passed from parents", "explain": "Genes carry hereditary information."}, {"q": "Sexual reproduction…", "options": ["mixes genes from two parents", "makes identical copies always", "never involves genes"], "answer": "mixes genes from two parents", "explain": "Mixing increases variation."}]}},
        ]},
        {"slug": "selection-earth", "title": "Selection and Earth History", "summary": "Populations and deep time.", "order": 2, "lessons": [
            {"slug": "natural-selection-grade7", "title": "Natural Selection", "order": 3, "minutes": 18, "summary": "Traits spread across generations.", "learn": [{"type": "p", "text": "Natural selection favors traits that help survival and reproduction. Over generations, helpful traits spread. Biodiversity strengthens resilience."}, {"type": "list", "items": ["Variation + competition + inheritance => selection.", "Fossils and DNA show shared ancestry."]}], "check": {"prompt": "Selection.", "questions": [{"q": "Natural selection favors…", "options": ["traits that help survival and reproduction", "only the largest individuals", "only the quietest"], "answer": "traits that help survival and reproduction", "explain": "Helpful traits spread."}, {"q": "Evidence for shared ancestry includes…", "options": ["fossils and DNA", "only legends", "only one observation"], "answer": "fossils and DNA", "explain": "Multiple lines of evidence converge."}]}},
            {"slug": "earth-history-grade7", "title": "Earth's History", "order": 4, "minutes": 15, "summary": "Deep time.", "learn": [{"type": "p", "text": "Rock layers, fossils, and dating reveal Earth's 4.6-billion-year story. Continents drift and climates shift; life and geology co-evolve."}, {"type": "list", "items": ["Older layers are usually deeper.", "Index fossils date layers.", "Plate motion builds mountains and basins."]}], "check": {"prompt": "Deep time.", "questions": [{"q": "The oldest layer is usually…", "options": ["the deepest", "the topmost", "the middle only"], "answer": "the deepest", "explain": "Superposition: deeper is generally older."}, {"q": "Evidence for plate motion includes…", "options": ["matching coasts and fossils across oceans", "only one river", "only one hill"], "answer": "matching coasts and fossils across oceans", "explain": "Distributed evidence supports tectonics."}]}},
        ]},
    ],
}
