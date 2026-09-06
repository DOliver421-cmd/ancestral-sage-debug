"""academy_content — WAI Institute Homeschool Academy curriculum data.

Structured, seed-driven content for the Academy. Content lives HERE, not in
React components or route handlers, so courses/lessons can be added by editing
data and letting the startup seed (seed_academy.seed_academy) upsert it into
db.academy_courses.

Schema (per course):
    slug, title, summary, description, subject, subject_label,
    track (primary), tracks (which tracks may take it), grades (list of
    grade strings incl "K"), grade_label, status ("published" | "planned"),
    audience, est_hours, learning_objectives [], passing_score (default 80),
    units [{slug, title, summary, order, lessons [
        {slug, title, order, minutes, summary,
         learn: [{type: "p"|"list"|"example"|"tip"|"activity", ...}],
         check: {prompt, questions: [
            {q, options[], answer (EXACT option string), explain}]}}]}]

Rules honored:
  * "published" courses contain real, complete instructional content.
  * "planned" courses are honest catalog entries (no lessons, never rendered
    as complete).
  * answers are stored as the exact option string; graders resolve the index,
    so a misplaced option can never silently shift the correct answer.
"""

from .reading_grade1 import READING_GRADE_1
from .math_grade4 import MATH_GRADE_4
from .math_grade7 import MATH_GRADE_7
from .biology_grade9 import BIOLOGY_GRADE_9
from .electrical_year1 import ELECTRICAL_YEAR_1

PUBLISHED_COURSES = [
    READING_GRADE_1,
    MATH_GRADE_4,
    MATH_GRADE_7,
    BIOLOGY_GRADE_9,
    ELECTRICAL_YEAR_1,
]

# ── Planned catalog (honest placeholders — status "planned", zero lessons).
# These register the full K–12 architecture without pretending content exists.
def _planned(slug, title, summary, description, subject, subject_label, track,
             tracks, grades, grade_label, audience="", est_hours=0):
    return {
        "slug": slug,
        "title": title,
        "summary": summary,
        "description": description,
        "subject": subject,
        "subject_label": subject_label,
        "track": track,
        "tracks": tracks,
        "grades": grades,
        "grade_label": grade_label,
        "status": "planned",
        "audience": audience,
        "est_hours": est_hours,
        "passing_score": 80,
        "learning_objectives": [],
        "units": [],
    }


PLANNED_COURSES = [
    # Foundations — K–2
    _planned("reading-foundations-kindergarten", "Reading Foundations — Kindergarten",
             "Letter recognition, phonemic awareness, and first sounds.",
             "Kindergarten reading foundations: print awareness, letter names and sounds, rhyming, and blending first CVC words. Curriculum in development.",
             "ela", "English Language Arts", "foundations", ["foundations", "builder", "artist", "scholar"],
             ["K"], "Kindergarten"),
    _planned("reading-foundations-grade-2", "Reading Foundations — Grade 2",
             "Fluent decoding, vocabulary, and comprehension of short texts.",
             "Second-grade reading: multisyllable words, prefixes and suffixes, fluency, and comprehension strategies. Curriculum in development.",
             "ela", "English Language Arts", "foundations", ["foundations", "builder", "artist", "scholar"],
             ["2"], "Grade 2"),
    _planned("math-grade-1", "Mathematics — Grade 1",
             "Addition and subtraction within 20, place value, and shapes.",
             "First-grade math: counting and place value to 120, addition and subtraction facts within 20, and basic geometry. Curriculum in development.",
             "math", "Mathematics", "foundations", ["foundations", "builder", "artist", "scholar"],
             ["1"], "Grade 1"),
    _planned("math-grade-2", "Mathematics — Grade 2",
             "Place value to 1,000, addition/subtraction fluency, and measurement.",
             "Second-grade math: three-digit place value, fluency with addition and subtraction, money, time, and measurement. Curriculum in development.",
             "math", "Mathematics", "foundations", ["foundations", "builder", "artist", "scholar"],
             ["2"], "Grade 2"),
    _planned("science-grade-2", "Science — Grade 2",
             "Plants and animals, matter, and earth's surface.",
             "Second-grade science: life cycles and habitats, properties of matter, and landforms and water. Curriculum in development.",
             "science", "Science", "foundations", ["foundations", "builder", "artist", "scholar"],
             ["2"], "Grade 2"),
    # Foundations — 3–5
    _planned("math-grade-5", "Mathematics — Grade 5",
             "Decimals, fractions with unlike denominators, volume, and graphing.",
             "Fifth-grade math: decimals, fraction operations, volume, and coordinate graphing. Curriculum in development.",
             "math", "Mathematics", "foundations", ["foundations", "builder", "artist", "scholar"],
             ["5"], "Grade 5"),
    _planned("ela-grade-5", "English Language Arts — Grade 5",
             "Reading across genres, text evidence, and clear writing.",
             "Fifth-grade ELA: informational and literary reading, citing evidence, and structured writing. Curriculum in development.",
             "ela", "English Language Arts", "foundations", ["foundations", "builder", "artist", "scholar"],
             ["5"], "Grade 5"),
    _planned("science-grade-5", "Science — Grade 5",
             "Matter and energy, ecosystems, and earth systems.",
             "Fifth-grade science: structure of matter, energy flow in ecosystems, and earth's systems. Curriculum in development.",
             "science", "Science", "foundations", ["foundations", "builder", "artist", "scholar"],
             ["5"], "Grade 5"),
    _planned("social-studies-grade-5", "Social Studies — Grade 5",
             "American history and civics foundations.",
             "Fifth-grade social studies: early American history, founding documents, and civic principles. Curriculum in development.",
             "social_studies", "Social Studies", "foundations", ["foundations", "builder", "artist", "scholar"],
             ["5"], "Grade 5"),
    # Foundations — 6–8
    _planned("math-grade-8", "Mathematics — Grade 8",
             "Linear equations, functions, exponents, and the Pythagorean theorem.",
             "Eighth-grade math: linear relationships, functions, irrational numbers, and geometry including the Pythagorean theorem. Curriculum in development.",
             "math", "Mathematics", "foundations", ["foundations", "builder", "artist", "scholar"],
             ["8"], "Grade 8"),
    _planned("science-grade-8", "Science — Grade 8",
             "Forces and motion, energy, and waves.",
             "Eighth-grade science: Newton's laws, energy transformations, and wave behavior — the bridge to high-school physics. Curriculum in development.",
             "science", "Science", "foundations", ["foundations", "builder", "artist", "scholar"],
             ["8"], "Grade 8"),
    _planned("social-studies-grade-7", "Social Studies — Grade 7",
             "World geography and global cultures.",
             "Seventh-grade social studies: world regions, cultures, trade, and human-environment interaction. Curriculum in development.",
             "social_studies", "Social Studies", "foundations", ["foundations", "builder", "artist", "scholar"],
             ["7"], "Grade 7"),
    # Scholar — 9–12
    _planned("algebra-1-grade-9", "Algebra 1",
             "Linear and quadratic expressions, equations, and functions.",
             "Scholar-track Algebra 1: linear and quadratic functions, systems of equations, exponents, and modeling. Curriculum in development.",
             "math", "Mathematics", "scholar", ["scholar", "foundations", "builder"],
             ["9"], "Grade 9"),
    _planned("chemistry-grade-10", "Chemistry",
             "Atomic structure, the periodic table, and chemical reactions.",
             "Scholar-track Chemistry: matter, atomic theory, bonding, stoichiometry, and reactions. Curriculum in development.",
             "science", "Science", "scholar", ["scholar", "builder"],
             ["10", "11", "12"], "Grades 10–12"),
    _planned("world-literature-grade-10", "World Literature",
             "Reading and writing across global literary traditions.",
             "Scholar-track ELA: world literature, literary analysis, and academic writing. Curriculum in development.",
             "ela", "English Language Arts", "scholar", ["scholar"],
             ["10"], "Grade 10"),
    # Builder / Trade
    _planned("applied-electrical-year-2", "Applied Electrical Engineering — Year 2",
             "AC power, wiring methods, and residential systems.",
             "Year 2 of the electrical pathway: alternating current, wiring methods and materials, residential branch circuits, and code application. Curriculum in development.",
             "trade", "Trade & Applied Skills", "builder", ["builder"],
             ["10", "11", "12"], "Grades 10–12"),
    _planned("trade-math-grade-8", "Trade Mathematics — Grade 8",
             "Measurement, geometry, and estimation for the trades.",
             "Builder-track math: precision measurement, fractions and decimals on the job, geometry for layout, and estimating. Curriculum in development.",
             "math", "Mathematics", "builder", ["builder"],
             ["8"], "Grade 8"),
    # Artist
    _planned("visual-arts-foundations", "Visual Arts Foundations",
             "Line, shape, color, and composition for young artists.",
             "Artist-track foundations: drawing and painting basics, color theory, and looking at art across cultures. Curriculum in development.",
             "art", "Arts", "artist", ["artist"],
             ["3", "4", "5"], "Grades 3–5"),
    _planned("digital-art-grade-9", "Digital Art and Design",
             "Creating and communicating with digital tools.",
             "Artist-track digital art: image tools, design principles, portfolio building, and creative careers. Curriculum in development.",
             "art", "Arts", "artist", ["artist"],
             ["9", "10", "11", "12"], "Grades 9–12"),
]

ACADEMY_COURSES = PUBLISHED_COURSES + PLANNED_COURSES

TRACKS = [
    {
        "key": "foundations",
        "name": "Foundations",
        "grades": "K–8",
        "blurb": "Core academics — English, Math, Science, Social Studies — mastery-paced for elementary and middle school.",
    },
    {
        "key": "builder",
        "name": "Builder / Trade",
        "grades": "6–12",
        "blurb": "Real skills for real work: trade math and science plus hands-on trade pathways such as applied electrical engineering.",
    },
    {
        "key": "artist",
        "name": "Artist",
        "grades": "K–12",
        "blurb": "Creative disciplines developed with academic rigor — visual, performing, and digital arts.",
    },
    {
        "key": "scholar",
        "name": "Scholar",
        "grades": "9–12",
        "blurb": "College-preparatory academics for high school students aiming at higher education and advanced study.",
    },
]

SUBJECTS = [
    {"key": "ela", "name": "English Language Arts"},
    {"key": "math", "name": "Mathematics"},
    {"key": "science", "name": "Science"},
    {"key": "social_studies", "name": "Social Studies"},
    {"key": "trade", "name": "Trade & Applied Skills"},
    {"key": "art", "name": "Arts"},
]
