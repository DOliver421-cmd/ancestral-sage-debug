"""enrichment.py — curated video enrichment for the Homeschool Academy.

Owner-curated, publicly accessible educational videos. These are NOT MoreHelp
content — every embed carries creator attribution and the on-site player is a
youtube-nocookie iframe so students never navigate away.

Placement:
    "start"            → shown at the top of the course page (and lesson 1)
    "unit:<unit-slug>" → shown above that unit's lesson list (mid-course)

Statuses:
    status "ready"   → has a real 11-char video ID; embeds today.
    status "no_id"   → creator/channel curated but no pinned video ID yet;
                       surfaces on the staff tracker as NEEDS VIDEO ID.
    status "link"    → non-YouTube resource (site/podcast/store); rendered as
                       an "Educators & Resources" link card, never an embed.

video_id values were supplied by the owner (2026-09-08). IDs flagged
`suspect: True` came from search-URL blocks and are live-checked on the staff
tracker (oEmbed) so a dead ID is visible to staff instead of a broken embed.
"""

ENRICHMENT_VIDEOS = {
    # ── Cultural & Historical Focus ──────────────────────────────────────────
    "african-kingdoms-empires": [
        {
            "video_id": "UAQaMrjySx8",
            "title": "Africa's Great Civilizations: Wealth, Governance, and Scholarship",
            "creator": "Africa's Great Civilizations (documentary)",
            "placement": "start",
            "status": "ready",
        },
    ],
    "ethnomathematics-black-pioneers": [
        {
            "video_id": "840gT_pY9b8",
            "title": "African Fractals, Architecture, and Contributions of Black STEM Pioneers",
            "creator": "Educational documentary",
            "placement": "start",
            "status": "ready",
        },
    ],
    "global-african-diaspora": [
        {
            "video_id": "5A_oIdqAZgI",
            "title": "The Haitian Revolution, Pan-Africanism, and Global Diaspora Movements",
            "creator": "Educational documentary",
            "placement": "start",
            "status": "ready",
        },
    ],
    "diaspora-mathematics-algorithms-astronomy": [
        {
            "video_id": "mGwf651YenA",
            "title": "Dogon Astronomy, Yoruba Mathematics, and African Navigation Systems",
            "creator": "Educational documentary",
            "placement": "start",
            "status": "ready",
        },
        {
            "video_id": "wXPtpXalAas",
            "title": "The Black Heroes of Mathematics",
            "creator": "Academic lecture series",
            "placement": "unit:number-systems",
            "status": "ready",
        },
        {
            "video_id": "9W9XBSUMNtA",
            "title": "The Professor Who Teaches Math With Black History",
            "creator": "Mathematical history integration",
            "placement": "unit:calendars",
            "status": "ready",
        },
    ],
    "african-philosophy-ethics": [
        {
            "video_id": "3R3m5xK7g2w",
            "title": "Ubuntu, Akan Philosophy, and Communal Epistemology",
            "creator": "Educational lecture",
            "placement": "start",
            "status": "ready",
        },
    ],
    "african-american-literature-foundations": [
        {
            "video_id": "y9gBqGk4Y5c",
            "title": "The Black Arts Movement, Harlem Renaissance, and Afrofuturism Overview",
            "creator": "Educational overview",
            "placement": "start",
            "status": "ready",
        },
    ],

    # ── K–8 Foundations ──────────────────────────────────────────────────────
    "reading-foundations-kindergarten": [
        {
            "video_id": "PXBwoJqiceI",
            "title": "Akili and the Alphabet Wall (Full Episode)",
            "creator": "Akili and Me (Ubongo)",
            "placement": "start",
            "status": "ready",
        },
        {
            "video_id": "FelSBR3-tcc",
            "title": "Akili and Me — Number Songs for Preschoolers",
            "creator": "Akili and Me (Ubongo)",
            "placement": "start",
            "status": "ready",
        },
    ],
    "reading-foundations-grade-2": [
        {
            "video_id": "AbY0HPtW9-8",
            "title": "Phonics, First Stories, and Reading Comprehension Strategies",
            "creator": "Literacy instruction",
            "placement": "start",
            "status": "ready",
        },
    ],
    "reading-foundations-grade-1": [
        {
            "video_id": "A6XwO721lOs",
            "title": "Sing and Learn All the African Countries with Bino and Fino",
            "creator": "Bino and Fino",
            "placement": "start",
            "status": "ready",
        },
    ],
    "math-grade-1": [
        {
            "video_id": "Rj95a48yn4Y",
            "title": "Count to 100 with Gracie's Corner",
            "creator": "Gracie's Corner",
            "placement": "start",
            "status": "ready",
        },
        {
            "video_id": "n-UYzQAnhqw",
            "title": "Count by Tens with Gracie's Corner",
            "creator": "Gracie's Corner",
            "placement": "start",
            "status": "ready",
        },
    ],
    "math-grade-2": [
        {
            "video_id": "au1zVXyQjW8",
            "title": "Khan Academy Core Math Progressions (Grades 1–8)",
            "creator": "Khan Academy",
            "placement": "start",
            "status": "ready",
        },
    ],
    "multiplication-division-fractions-grade-4": [
        {
            "video_id": "aT5wHuarp2g",
            "title": "Ubongo Kids — Multiplication & Division Basic Math",
            "creator": "Ubongo Kids",
            "placement": "start",
            "status": "ready",
        },
    ],
    "math-grade-5": [
        {
            "video_id": "au1zVXyQjW8",
            "title": "Khan Academy Core Math Progressions (Grades 1–8)",
            "creator": "Khan Academy",
            "placement": "start",
            "status": "ready",
        },
    ],
    "math-grade-6": [
        {
            "video_id": "au1zVXyQjW8",
            "title": "Khan Academy Core Math Progressions (Grades 1–8)",
            "creator": "Khan Academy",
            "placement": "start",
            "status": "ready",
        },
    ],
    "math-grade-8": [
        {
            "video_id": "au1zVXyQjW8",
            "title": "Khan Academy Core Math Progressions (Grades 1–8)",
            "creator": "Khan Academy",
            "placement": "start",
            "status": "ready",
        },
    ],
    "math-grade-3": [
        {
            "video_id": "Ra5YpPxKqXU",
            "title": "Akili and Me — Meet Numbers Zero to 10",
            "creator": "Akili and Me (Ubongo)",
            "placement": "start",
            "status": "ready",
        },
    ],
    "science-grade-2": [
        {
            "video_id": "jzuKbOpc9gY",
            "title": "Crash Course Kids: Science & Earth Ecosystems",
            "creator": "Crash Course Kids",
            "placement": "start",
            "status": "ready",
        },
    ],
    "science-grade-5": [
        {
            "video_id": "jzuKbOpc9gY",
            "title": "Crash Course Kids: Science & Earth Ecosystems",
            "creator": "Crash Course Kids",
            "placement": "start",
            "status": "ready",
        },
    ],
    "science-grade-8": [
        {
            "video_id": "jzuKbOpc9gY",
            "title": "Crash Course Kids: Science, Earth Ecosystems & Physics",
            "creator": "Crash Course Kids",
            "placement": "start",
            "status": "ready",
        },
    ],
    "social-studies-grade-5": [
        {
            "video_id": "Vl03q5WdC88",
            "title": "World Geography, Cultures, and Early American History",
            "creator": "Educational overview",
            "placement": "start",
            "status": "ready",
        },
    ],
    "social-studies-grade-7": [
        {
            "video_id": "Vl03q5WdC88",
            "title": "World Geography, Cultures, and Early American History",
            "creator": "Educational overview",
            "placement": "start",
            "status": "ready",
        },
    ],

    # ── Artist & Trade ───────────────────────────────────────────────────────
    "visual-arts-foundations": [
        {
            "video_id": "KY1bZ8K9VpQ",
            "title": "Elements of Art: Line, Shape, Color, Form",
            "creator": "Art instruction",
            "placement": "start",
            "status": "ready",
        },
    ],
    "digital-art-grade-9": [
        {
            "video_id": "YqQx75OPRa0",
            "title": "Graphic Design Principles & Portfolio Building",
            "creator": "Design instruction",
            "placement": "start",
            "status": "ready",
        },
    ],
    "applied-electrical-year-1": [
        {
            "video_id": "XA-u29x_1_0",
            "title": "Electrical Theory: Ohm's Law, Circuits, and Residential Wiring",
            "creator": "Trade instruction",
            "placement": "start",
            "status": "ready",
        },
    ],
    "electrical-year-2": [
        {
            "video_id": "XA-u29x_1_0",
            "title": "Electrical Theory: Ohm's Law, Circuits, and Residential Wiring",
            "creator": "Trade instruction",
            "placement": "start",
            "status": "ready",
        },
    ],
    "trade-math-grade-8": [
        {
            "video_id": "XA-u29x_1_0",
            "title": "Electrical Theory: Ohm's Law, Circuits, and Residential Wiring",
            "creator": "Trade instruction",
            "placement": "start",
            "status": "ready",
        },
    ],

    # ── Adult Education ──────────────────────────────────────────────────────
    "adult-ed-hse-social-studies": [
        {
            "video_id": "bBC-nXj3Ng4",
            "title": "US History & Civics Core Concepts Breakdown",
            "creator": "Civics instruction",
            "placement": "start",
            "status": "ready",
        },
    ],

    # ── Entrepreneurship (published courses only) ────────────────────────────
    "entrepreneurship-foundations": [
        {
            "video_id": "DoPjmoGkWZU",
            "title": "Startups, Small Business Models, and Operations Management",
            "creator": "Business instruction",
            "placement": "start",
            "status": "ready",
        },
    ],

    # ── Planned courses (embeds activate automatically when they publish) ────
    "autonomous-enterprise-black-commerce": [
        {
            "video_id": "XX1KqjbMCpA",
            "title": "Black Wall Street — The Daily Then™",
            "creator": "The Daily Then™",
            "placement": "start",
            "status": "ready",
        },
    ],
    "cooperative-economics-mutual-aid": [
        {
            "video_id": "oNZiE0vyD_Y",
            "title": "History of Mutual Aid and Cooperative Economics in Black Communities",
            "creator": "Economic history documentary",
            "placement": "start",
            "status": "ready",
        },
    ],
    "radical-wealth-literacy": [
        {
            "video_id": "HQ204yPbbj8",
            "title": "Systemic Wealth Extraction and Predatory Lending Analysis",
            "creator": "Financial literacy analysis",
            "placement": "start",
            "status": "ready",
        },
    ],
    "resistance-rebellion-counter-narrative": [
        {
        "video_id": "Nn7Zg7o8IYA",
            "title": "Maroon Societies and Organized Anti-Colonial Resistance",
            "creator": "History documentary",
            "placement": "start",
            "status": "ready",
        },
    ],
    "legalized-subjugation": [
        {
            "video_id": "0b7gLp0y9cQ",
            "title": "The Legal Mechanics of Jim Crow, Black Codes, and Structural Controls",
            "creator": "Legal history analysis",
            "placement": "start",
            "status": "ready",
        },
    ],
    "economics-of-extraction": [
        {
            "video_id": "3l3w9g8f2p1",
            "title": "Exposing the Material Reality of Global Capital Accumulation and Forced Labor",
            "creator": "Economic history analysis",
            "placement": "start",
            "status": "ready",
            "suspect": True,
        },
    ],
    "architecture-of-omission": [
        {
            "video_id": "5r4k9v8c3l0",
            "title": "Deconstructing U.S. Curriculum Omissions and Primary-Source Cross-Examination",
            "creator": "History analysis",
            "placement": "start",
            "status": "ready",
            "suspect": True,
        },
    ],
    "african-ecosystems-land-stewardship": [
        {
            "video_id": "S8pB6t_tB1w",
            "title": "Indigenous African Agricultural and Water Management Technologies",
            "creator": "Environmental science documentary",
            "placement": "start",
            "status": "ready",
        },
    ],

    # ── NEEDS VIDEO ID (creator curated, no pinned watch URL yet) ────────────
    "adult-ed-hse-ela": [
        {
            "video_id": None,
            "title": "Crash Course Literature / Critical Reading Masterclass",
            "creator": "Crash Course",
            "placement": "start",
            "status": "no_id",
        },
    ],
    "adult-ed-hse-math": [
        {
            "video_id": None,
            "title": "Math Antics — Fundamental Math Operations & Problem Solving",
            "creator": "Math Antics",
            "placement": "start",
            "status": "no_id",
        },
    ],
    "adult-ed-hse-science": [
        {
            "video_id": None,
            "title": "Amoeba Sisters & General Science Foundations",
            "creator": "Amoeba Sisters",
            "placement": "start",
            "status": "no_id",
        },
    ],
}

# ── Educator & resource links (Class C — attribution cards, never embeds) ────
EDUCATOR_RESOURCES = [
    {"name": "Casual Geographic (Mamadou)", "role": "Zoology & Earth Science",
     "url": "https://www.youtube.com/@CasualGeographic", "status": "link"},
    {"name": "Mike Likes Science", "role": "Science & STEM music education",
     "url": "https://www.youtube.com/@mike.likes.science", "status": "link"},
    {"name": "Kids Black History", "role": "Foundational Black history for kids",
     "url": "https://www.youtube.com/@kidsblackhistory", "status": "link"},
    {"name": "Gracie's Corner", "role": "Early literacy & numeracy music",
     "url": "https://www.youtube.com/@GraciesCorner", "status": "link"},
    {"name": "Learning with Ms. Houston", "role": "Early childhood foundations",
     "url": "https://www.youtube.com/@LearningwithMsHouston", "status": "link"},
    {"name": "Hey! It's Mr. J", "role": "PE, motor skills & SEL for young learners",
     "url": "https://www.youtube.com/@heyitsmr.j", "status": "link"},
    {"name": "Dr. Raven Baxter (Raven the Science Maven)", "role": "STEM communication",
     "url": "https://www.youtube.com/@raventhesciencemaven", "status": "link"},
    {"name": "Akil Parker — All This Math / Histematics", "role": "Mathematics through Black history",
     "url": "https://www.knarrative.com/course/histematics", "status": "link"},
    {"name": "Dr. Anika Prather", "role": "Black intellectual history",
     "url": "https://billofrightsinstitute.org/videos/anna-julia-cooper-with-anika-prather-black-intellectuals-series-5/", "status": "link"},
    {"name": "Dr. Brigitte Fielder — Lifting Their Voices", "role": "Black women writers & literary analysis",
     "url": "https://taughtbyliterature.squarespace.com/lifting-their-voices-video-series", "status": "link"},
    {"name": "Dr. Jessica Gordon Nembhard", "role": "Black cooperatives & economic history",
     "url": "https://www.youtube.com/results?search_query=Jessica+Gordon+Nembhard+Black+cooperatives", "status": "link"},
    {"name": "Dr. Boyce Watkins", "role": "Financial literacy & wealth",
     "url": "https://www.youtube.com/results?search_query=Boyce+Watkins+financial+literacy+wealth", "status": "link"},
    {"name": "Dr. Erica Jordan-Thomas", "role": "Career & entrepreneurship education",
     "url": "https://ericajordanthomas.com/", "status": "link"},
    {"name": "Dr. Nadia Bennett — Community, Calling & The Climb", "role": "Leadership",
     "url": "https://www.exitinterviewpodcast.com/community-calling-the-climb-with-dr-nadia-a-bennett/", "status": "link"},
    {"name": "Art With Trista", "role": "Elements of art & Black artist-inspired projects",
     "url": "https://www.teacherspayteachers.com/store/art-with-trista/teacher-tools/art/art-history", "status": "link"},
    {"name": "Black Art Research Space — Willis 'Bing' Davis", "role": "Contemporary Black art & design",
     "url": "https://www.blackartistresearchspace.com/willisbingdavis", "status": "link"},
    {"name": "The Educators (podcast)", "role": "Black male educators in conversation",
     "url": "https://podcasts.apple.com/us/podcast/the-educators/id1476325562", "status": "link"},
]


def videos_for(slug: str) -> list:
    """Embeddable-ready enrichment list for a course slug (may be empty)."""
    return [dict(v, course_slug=slug) for v in ENRICHMENT_VIDEOS.get(slug, [])]


def all_resources() -> list:
    return [dict(r) for r in EDUCATOR_RESOURCES]


def validate_enrichment(course_slugs: set, unit_slugs_by_course: dict) -> list:
    """Validate the enrichment mapping against the real course catalog.

    Returns human-readable problems; empty = valid. Checks:
      * every mapped course slug exists in the catalog,
      * every video has a shape-valid ID unless status is no_id/link,
      * every "unit:" placement targets a real unit of that course.
    """
    import re
    problems = []
    for slug, videos in ENRICHMENT_VIDEOS.items():
        if slug not in course_slugs:
            problems.append(f"enrichment: unknown course slug {slug!r}")
            continue
        unit_slugs = {u["slug"] for u in unit_slugs_by_course.get(slug, [])}
        for v in videos:
            if v.get("status") in ("no_id", "link"):
                continue
            vid = v.get("video_id")
            if not vid or not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
                problems.append(f"enrichment: {slug} video {v.get('title')!r} needs a valid 11-char video_id")
            placement = v.get("placement", "start")
            if placement.startswith("unit:") and placement[5:] not in unit_slugs:
                problems.append(f"enrichment: {slug} video {v.get('title')!r} targets unknown unit {placement!r}")
    return problems
