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

from .oral_histories_ancestral_foundations import ORAL_HISTORIES_ANCESTRAL_FOUNDATIONS
from .pan_african_diasporic_literature import PAN_AFRICAN_DIASPORIC_LITERATURE
from .black_political_thought import BLACK_POLITICAL_THOUGHT
from .afrofuturism_sustainable_architecture import AFROFUTURISM_SUSTAINABLE_ARCHITECTURE
from .visual_arts_black_diaspora import VISUAL_ARTS_BLACK_DIASPORA
from .ethnomusicology_roots_black_music import ETHNOMUSICOLOGY_ROOTS_BLACK_MUSIC
from .health_equity_food_sovereignty import HEALTH_EQUITY_FOOD_SOVEREIGNTY
from .indigenous_astronomy_maritime_navigation import INDIGENOUS_ASTRONOMY_MARITIME_NAVIGATION
from .prose_of_liberation import PROSE_OF_LIBERATION
from .african_indigenous_governance import AFRICAN_INDIGENOUS_GOVERNANCE
from .data_analysis_algorithmic_bias import DATA_ANALYSIS_ALGORITHMIC_BIAS
from .tek_african_botanical_medicine import TEK_AFRICAN_BOTANICAL_MEDICINE
from .cradles_of_civilization import CRADLES_OF_CIVILIZATION
from .maroon_societies_alliances import MAROON_SOCIETIES_ALLIANCES
from .atlantic_world_resistance_reconstruction import ATLANTIC_WORLD_RESISTANCE_RECONSTRUCTION
from .storytelling_diaspora_k2 import STORYTELLING_DIASPORA_K2
from .patterns_beadwork_african_math_k2 import PATTERNS_BEADWORK_AFRICAN_MATH_K2
from .reading_grade1 import READING_GRADE_1
from .math_grade4 import MATH_GRADE_4
from .math_grade7 import MATH_GRADE_7
from .biology_grade9 import BIOLOGY_GRADE_9
from .electrical_year1 import ELECTRICAL_YEAR_1
from .reading_foundations_kindergarten import READING_FOUNDATIONS_KINDERGARTEN
from .reading_foundations_grade_2 import READING_FOUNDATIONS_GRADE_2
from .math_grade3 import MATH_GRADE_3
from .math_grade5 import MATH_GRADE_5
from .math_grade6 import MATH_GRADE_6
from .math_grade8 import MATH_GRADE_8
from .science_grade5 import SCIENCE_GRADE_5
from .social_studies_grade_7 import SOCIAL_STUDIES_GRADE_7
from .algebra_1_grade_9 import ALGEBRA_1_GRADE_9
from .visual_arts_foundations import VISUAL_ARTS_FOUNDATIONS
from .math_grade1 import MATH_GRADE_1
from .math_grade2 import MATH_GRADE_2
from .science_grade2 import SCIENCE_GRADE_2
from .ela_grade5 import ELA_GRADE_5
from .social_studies_grade5 import SOCIAL_STUDIES_GRADE_5
from .science_grade8 import SCIENCE_GRADE_8
from .chemistry_grade10 import CHEMISTRY_GRADE_10
from .world_literature_grade10 import WORLD_LITERATURE_GRADE_10
from .electrical_year2 import ELECTRICAL_YEAR_2
from .trade_math_grade8 import TRADE_MATH_GRADE_8
from .digital_art_grade9 import DIGITAL_ART_GRADE_9
from .adult_ed_hse_math import ADULT_ED_HSE_MATH
from .adult_ed_hse_ela import ADULT_ED_HSE_ELA
from .adult_ed_hse_science import ADULT_ED_HSE_SCIENCE
from .adult_ed_hse_social_studies import ADULT_ED_HSE_SOCIAL_STUDIES
from .life_skills_foundations import LIFE_SKILLS_FOUNDATIONS
from .womens_life_skills import WOMENS_LIFE_SKILLS
from .mens_life_skills import MENS_LIFE_SKILLS
from .leadership_foundations import LEADERSHIP_FOUNDATIONS
from .career_workforce import CAREER_WORKFORCE
from .entrepreneurship_foundations import ENTREPRENEURSHIP_FOUNDATIONS
from .african_kingdoms import AFRICAN_KINGDOMS
from .african_american_literature import AFRICAN_AMERICAN_LITERATURE
from .ethnomathematics_stem import ETHNOMATHEMATICS_STEM
from .global_african_diaspora import GLOBAL_AFRICAN_DIASPORA
from .diaspora_mathematics import DIASPORA_MATHEMATICS
from .african_philosophy_ethics import AFRICAN_PHILOSOPHY_ETHICS
from .architecture_of_omission import ARCHITECTURE_OF_OMISSION
from .handbook_elementary import HANDBOOK_ELEMENTARY
from .handbook_middle import HANDBOOK_MIDDLE
from .handbook_high import HANDBOOK_HIGH
from .handbook_adult import HANDBOOK_ADULT
from .math_kindergarten import MATH_KINDERGARTEN
from .science_kindergarten import SCIENCE_KINDERGARTEN
from .social_studies_kindergarten import SOCIAL_STUDIES_KINDERGARTEN
from .science_grade1 import SCIENCE_GRADE_1
from .social_studies_grade1 import SOCIAL_STUDIES_GRADE_1
from .social_studies_grade2 import SOCIAL_STUDIES_GRADE_2
from .ela_grade3 import ELA_GRADE_3
from .science_grade3 import SCIENCE_GRADE_3
from .social_studies_grade3 import SOCIAL_STUDIES_GRADE_3
from .ela_grade4 import ELA_GRADE_4
from .science_grade4 import SCIENCE_GRADE_4
from .social_studies_grade4 import SOCIAL_STUDIES_GRADE_4
from .ela_grade6 import ELA_GRADE_6
from .science_grade6 import SCIENCE_GRADE_6
from .ela_grade7 import ELA_GRADE_7
from .science_grade7 import SCIENCE_GRADE_7
from .math_grade11 import MATH_GRADE_11
from .ela_grade12 import ELA_GRADE_12
from .math_grade12 import MATH_GRADE_12
from .ela_grade11 import ELA_GRADE_11
from .science_grade11 import SCIENCE_GRADE_11
from .social_studies_grade11 import SOCIAL_STUDIES_GRADE_11
from .science_grade12 import SCIENCE_GRADE_12
from .social_studies_grade12 import SOCIAL_STUDIES_GRADE_12
from .ascension_protocols import ASCENSION_PROTOCOLS
from .cooperative_economics_mutual_aid import COOPERATIVE_ECONOMICS_MUTUAL_AID
from .legalized_subjugation import LEGALIZED_SUBJUGATION
from .radical_wealth_literacy import RADICAL_WEALTH_LITERACY
from .african_ecosystems_land_stewardship import AFRICAN_ECOSYSTEMS_LAND_STEWARDSHIP
from .resistance_rebellion_counter_narrative import RESISTANCE_REBELLION_COUNTER_NARRATIVE
from .economics_of_extraction import ECONOMICS_OF_EXTRACTION

PUBLISHED_COURSES = [
    AFROFUTURISM_SUSTAINABLE_ARCHITECTURE,
    VISUAL_ARTS_BLACK_DIASPORA,
    ETHNOMUSICOLOGY_ROOTS_BLACK_MUSIC,
    HEALTH_EQUITY_FOOD_SOVEREIGNTY,
    INDIGENOUS_ASTRONOMY_MARITIME_NAVIGATION,
    PAN_AFRICAN_DIASPORIC_LITERATURE,
    PROSE_OF_LIBERATION,
    AFRICAN_INDIGENOUS_GOVERNANCE,
    BLACK_POLITICAL_THOUGHT,
    DATA_ANALYSIS_ALGORITHMIC_BIAS,
    TEK_AFRICAN_BOTANICAL_MEDICINE,
    CRADLES_OF_CIVILIZATION,
    MAROON_SOCIETIES_ALLIANCES,
    ATLANTIC_WORLD_RESISTANCE_RECONSTRUCTION,
    ORAL_HISTORIES_ANCESTRAL_FOUNDATIONS,
    STORYTELLING_DIASPORA_K2,
    PATTERNS_BEADWORK_AFRICAN_MATH_K2,
    READING_GRADE_1,
    MATH_GRADE_4,
    MATH_GRADE_7,
    BIOLOGY_GRADE_9,
    ELECTRICAL_YEAR_1,
    READING_FOUNDATIONS_KINDERGARTEN,
    READING_FOUNDATIONS_GRADE_2,
    MATH_GRADE_3,
    MATH_GRADE_5,
    MATH_GRADE_6,
    MATH_GRADE_8,
    SCIENCE_GRADE_5,
    SOCIAL_STUDIES_GRADE_7,
    ALGEBRA_1_GRADE_9,
    VISUAL_ARTS_FOUNDATIONS,
    MATH_GRADE_1,
    MATH_GRADE_2,
    SCIENCE_GRADE_2,
    ELA_GRADE_5,
    SOCIAL_STUDIES_GRADE_5,
    SCIENCE_GRADE_8,
    CHEMISTRY_GRADE_10,
    WORLD_LITERATURE_GRADE_10,
    ELECTRICAL_YEAR_2,
    TRADE_MATH_GRADE_8,
    DIGITAL_ART_GRADE_9,
    ADULT_ED_HSE_MATH,
    ADULT_ED_HSE_ELA,
    ADULT_ED_HSE_SCIENCE,
    ADULT_ED_HSE_SOCIAL_STUDIES,
    LIFE_SKILLS_FOUNDATIONS,
    WOMENS_LIFE_SKILLS,
    MENS_LIFE_SKILLS,
    LEADERSHIP_FOUNDATIONS,
    CAREER_WORKFORCE,
    ENTREPRENEURSHIP_FOUNDATIONS,
    AFRICAN_KINGDOMS,
    AFRICAN_AMERICAN_LITERATURE,
    ETHNOMATHEMATICS_STEM,
    GLOBAL_AFRICAN_DIASPORA,
    DIASPORA_MATHEMATICS,
    AFRICAN_PHILOSOPHY_ETHICS,
    ARCHITECTURE_OF_OMISSION,
    LEGALIZED_SUBJUGATION,
    AFRICAN_ECOSYSTEMS_LAND_STEWARDSHIP,
    RESISTANCE_REBELLION_COUNTER_NARRATIVE,
    ECONOMICS_OF_EXTRACTION,
    RADICAL_WEALTH_LITERACY,
    COOPERATIVE_ECONOMICS_MUTUAL_AID,
    # ── Gap-fill: missing K-12 core curriculum (2026-09-09 audit) ──
    MATH_KINDERGARTEN,
    SCIENCE_KINDERGARTEN,
    SOCIAL_STUDIES_KINDERGARTEN,
    SCIENCE_GRADE_1,
    SOCIAL_STUDIES_GRADE_1,
    SOCIAL_STUDIES_GRADE_2,
    ELA_GRADE_3,
    SCIENCE_GRADE_3,
    SOCIAL_STUDIES_GRADE_3,
    ELA_GRADE_4,
    SCIENCE_GRADE_4,
    SOCIAL_STUDIES_GRADE_4,
    ELA_GRADE_6,
    SCIENCE_GRADE_6,
    ELA_GRADE_7,
    SCIENCE_GRADE_7,
    MATH_GRADE_11,
    ELA_GRADE_11,
    SCIENCE_GRADE_11,
    SOCIAL_STUDIES_GRADE_11,
    ELA_GRADE_12,
    MATH_GRADE_12,
    SCIENCE_GRADE_12,
    SOCIAL_STUDIES_GRADE_12,
    ASCENSION_PROTOCOLS,
    # Free student handbooks (ebook-style guides, catalog placement)
    HANDBOOK_ELEMENTARY,
    HANDBOOK_MIDDLE,
    HANDBOOK_HIGH,
    HANDBOOK_ADULT,
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
    # ── Business & Entrepreneurship: Counter-Narrative & Economic Autonomy ──
    _planned(
        "autonomous-enterprise-black-commerce",
        "Autonomous Enterprise: History and Mechanics of Black Commerce",
        "Independent commerce built under structural disadvantage — from commerce under chattel slavery and Black Wall Street ecosystems to modern cooperative and digital ventures.",
        "Analyzes capital generation, localized supply chains, and self-determined market creation, including the targeted destruction of prosperous Black commercial districts and modern digital sovereignty strategies; capstone is a complete autonomous business plan.",
        "entrepreneurship", "Entrepreneurship", "entrepreneurship", ["entrepreneurship", "scholar"],
        ["10", "11", "12"], "Grades 10–12", est_hours=24),
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
    {
        "key": "adult_ed",
        "name": "Adult Education",
        "grades": "Adult",
        "blurb": "High-school equivalency preparation and practical academics for adult learners.",
    },
    {
        "key": "life_skills",
        "name": "Life Skills",
        "grades": "Adult",
        "blurb": "Independent living, workplace skills, and personal development for adults.",
    },
    {
        "key": "leadership",
        "name": "Leadership",
        "grades": "Adult",
        "blurb": "Leadership training for workplace and community roles.",
    },
    {
        "key": "career",
        "name": "Career / Workforce",
        "grades": "Adult",
        "blurb": "Career exploration, job skills, and professional development for the modern workforce.",
    },
    {
        "key": "entrepreneurship",
        "name": "Entrepreneurship",
        "grades": "Adult",
        "blurb": "Start and grow a business with practical training in opportunity, operations, finance, and strategy.",
    },
]

SUBJECTS = [
    {"key": "ela", "name": "English Language Arts"},
    {"key": "math", "name": "Mathematics"},
    {"key": "science", "name": "Science"},
    {"key": "social_studies", "name": "Social Studies"},
    {"key": "trade", "name": "Trade & Applied Skills"},
    {"key": "art", "name": "Arts"},
    {"key": "adult_ed", "name": "Adult Education"},
    {"key": "life_skills", "name": "Life Skills"},
    {"key": "leadership", "name": "Leadership"},
    {"key": "career", "name": "Career / Workforce"},
    {"key": "entrepreneurship", "name": "Entrepreneurship"},
]
