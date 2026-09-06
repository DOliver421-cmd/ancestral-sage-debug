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

PUBLISHED_COURSES = [
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
