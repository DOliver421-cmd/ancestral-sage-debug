"""Visual Arts Foundations — Grades 3–5 (full published course)."""

VISUAL_ARTS_FOUNDATIONS = {
    "slug": "visual-arts-foundations",
    "title": "Visual Arts Foundations",
    "summary": "Line, shape, color, and composition for young artists.",
    "description": (
        "Visual Arts Foundations introduces young artists to the elements of art "
        "through hands-on drawing, painting, and collage. Students explore line, "
        "shape, color, texture, and composition while looking at art from many "
        "cultures. Each lesson ends with a creative project and a reflection check."
    ),
    "subject": "art",
    "subject_label": "Arts",
    "track": "artist",
    "tracks": ["artist"],
    "grades": ["3", "4", "5"],
    "grade_label": "Grades 3–5",
    "status": "published",
    "audience": "Grades 3–5 (ages 8–11), Artist track; open to any young creator.",
    "est_hours": 16,
    "passing_score": 80,
    "learning_objectives": [
        "Identify the elements of art in real artworks.",
        "Use line, shape, and color to compose a balanced picture.",
        "Mix colors using the primary/secondary color system.",
        "Create texture with different materials and techniques.",
        "Compare artworks from different cultures.",
        "Describe personal artwork using art vocabulary.",
    ],
    "units": [
        {
            "slug": "elements-of-art",
            "title": "Elements of Art",
            "summary": "Line, shape, and color.",
            "order": 1,
            "lessons": [
                {
                    "slug": "line-and-shape",
                    "title": "Line and Shape",
                    "order": 1,
                    "minutes": 15,
                    "summary": "Use different lines to build shapes.",
                    "learn": [
                        {"type": "p", "text": "Lines can be straight, curved, thick, thin, wavy, or zigzag. Shapes are made by enclosing lines. Geometric shapes have exact names; organic shapes are free and flowing."},
                        {"type": "list", "items": [
                            "Straight lines: vertical, horizontal, diagonal.",
                            "Curved lines: wavy, circular, spiral.",
                            "Shapes: circle, square, triangle, rectangle, oval.",
                            "Organic shapes: clouds, leaves, puddles.",
                        ]},
                        {"type": "activity", "title": "Line drawing", "text": "Fill a page using only straight lines. Then fill another page using only curved lines. Which page feels calm? Which feels energetic?"},
                    ],
                    "check": {
                        "prompt": "Show what you know about line and shape.",
                        "questions": [
                            {"q": "Which is a geometric shape?", "options": ["square", "cloud", "leaf"], "answer": "square", "explain": "Squares have straight sides and exact names."},
                            {"q": "A wavy line is…", "options": ["curved", "straight", "broken"], "answer": "curved", "explain": "Wavy lines curve back and forth."},
                            {"q": "Organic shapes are…", "options": ["free and flowing", "exact and named", "always round"], "answer": "free and flowing", "explain": "Organic shapes are natural and irregular."},
                        ],
                    },
                },
                {
                    "slug": "color-mixing",
                    "title": "Color Mixing",
                    "order": 2,
                    "minutes": 15,
                    "summary": "Mix primary colors to make secondary colors.",
                    "learn": [
                        {"type": "p", "text": "The primary colors are red, yellow, and blue. Mix two primaries to make a secondary: red + yellow = orange, yellow + blue = green, blue + red = purple."},
                        {"type": "list", "items": [
                            "Primary: red, yellow, blue.",
                            "Secondary: orange, green, purple.",
                            "Add white to make tints.",
                            "Add black to make shades.",
                        ]},
                        {"type": "activity", "title": "Color wheel", "text": "Paint a color wheel with the three primaries in a triangle. Mix the secondaries between them."},
                    ],
                    "check": {
                        "prompt": "Show what you know about color mixing.",
                        "questions": [
                            {"q": "Which is a primary color?", "options": ["blue", "green", "orange"], "answer": "blue", "explain": "Red, yellow, and blue are the primary colors."},
                            {"q": "Red + yellow makes…", "options": ["orange", "green", "purple"], "answer": "orange", "explain": "Red and yellow mix to make orange."},
                            {"q": "Blue + red makes…", "options": ["purple", "green", "orange"], "answer": "purple", "explain": "Blue and red mix to make purple."},
                        ],
                    },
                },
                {
                    "slug": "composition",
                    "title": "Composition",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Arrange elements to create a balanced picture.",
                    "learn": [
                        {"type": "p", "text": "Composition is how you arrange elements in a picture. Balance means the visual weight feels even. You can create balance with symmetry or with an off-center arrangement that still feels steady."},
                        {"type": "list", "items": [
                            "Rule of thirds: divide the picture into nine parts.",
                            "Place the most important part near an intersection.",
                            "Contrast (light vs dark, big vs small) creates interest.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about composition.",
                        "questions": [
                            {"q": "Composition is…", "options": ["how elements are arranged", "the colors used", "the size of the canvas"], "answer": "how elements are arranged", "explain": "Composition is the arrangement of visual elements."},
                            {"q": "The rule of thirds divides the picture into…", "options": ["nine parts", "four parts", "three parts"], "answer": "nine parts", "explain": "The rule of thirds uses a 3×3 grid."},
                        ],
                    },
                },
            ],
        },
    ],
}
