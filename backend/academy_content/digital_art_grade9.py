"""Digital Art and Design — Grade 9 (full published course)."""

DIGITAL_ART_GRADE_9 = {
    "slug": "digital-art-grade-9",
    "title": "Digital Art and Design",
    "summary": "Image tools, design principles, and portfolio building.",
    "description": (
        "Artist-track digital art teaches the craft of creating and communicating "
        "with digital tools. Students learn industry-standard software basics, "
        "composition and color theory, typography, and how to document work for a portfolio."
    ),
    "subject": "art",
    "subject_label": "Arts",
    "track": "artist",
    "tracks": ["artist"],
    "grades": ["9", "10", "11", "12"],
    "grade_label": "Grades 9–12",
    "status": "published",
    "audience": "Artist-track students; beginners through intermediate digital creators.",
    "est_hours": 22,
    "passing_score": 80,
    "learning_objectives": [
        "Use core raster and vector tools to create images.",
        "Apply design principles: balance, contrast, hierarchy, and unity.",
        "Choose and combine colors using color theory.",
        "Select and pair typefaces for digital layouts.",
        "Prepare and present a polished portfolio of original work.",
    ],
    "units": [
        {
            "slug": "tools-and-composition",
            "title": "Tools and Composition",
            "summary": "Software basics, layers, and visual balance.",
            "order": 1,
            "lessons": [
                {
                    "slug": "raster-and-vector-basics",
                    "title": "Raster and Vector Basics",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Understand pixels vs. paths and when to use each.",
                    "learn": [
                        {"type": "p", "text": "Digital images fall into two families. Raster images (photos, paintings) are made of pixels — tiny colored squares. Vector images (logos, icons) are made of mathematical paths and can be scaled without losing quality."},
                        {"type": "list", "items": [
                            "Raster: Photoshop, GIMP, Procreate.",
                            "Vector: Illustrator, Inkscape, Affinity Designer.",
                            "Resolution: 72 PPI for web, 300 PPI for print.",
                            "Scaling raster too far causes pixelation.",
                        ]},
                        {"type": "example", "title": "When to choose each", "text": "A photograph is raster. A business logo should be vector so it can appear on a business card and a billboard without blurring."},
                        {"type": "activity", "title": "Create a canvas", "text": "Open a raster program and a vector program. Create a 1000 × 1000 canvas in each. Name and save both files."},
                    ],
                    "check": {
                        "prompt": "Show what you know about raster and vector.",
                        "questions": [
                            {"q": "Which image type is made of pixels?", "options": ["raster", "vector", "both"], "answer": "raster", "explain": "Raster images are grids of colored pixels."},
                            {"q": "Which is best for a scalable logo?", "options": ["vector", "raster", "photograph"], "answer": "vector", "explain": "Vectors scale cleanly because they are based on math, not pixels."},
                        ],
                    },
                },
                {
                    "slug": "composition-and-balance",
                    "title": "Composition and Balance",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Rule of thirds, focal points, and visual weight.",
                    "learn": [
                        {"type": "p", "text": "Good composition guides the viewer's eye. The rule of thirds divides the frame into nine equal parts. Place key subjects along the lines or at intersections for a stronger image."},
                        {"type": "list", "items": [
                            "Rule of thirds: avoid dead-center placement.",
                            "Focal point: the first place the eye lands.",
                            "Visual weight: dark and bright areas feel heavier.",
                            "Balance: distribute weight so the image feels stable.",
                        ]},
                        {"type": "example", "title": "Horizon placement", "text": "A landscape with the horizon in the top third emphasizes land; in the bottom third it emphasizes sky."},
                    ],
                    "check": {
                        "prompt": "Show what you know about composition.",
                        "questions": [
                            {"q": "The rule of thirds divides a frame into…", "options": ["9 equal parts", "4 parts", "3 parts"], "answer": "9 equal parts", "explain": "Two vertical and two horizontal lines create nine sections."},
                            {"q": "Where should the focal point often be placed?", "options": ["near a rule-of-thirds intersection", "exact center", "top left corner always"], "answer": "near a rule-of-thirds intersection", "explain": "Off-center placement tends to create dynamic, interesting compositions."},
                        ],
                    },
                },
                {
                    "slug": "color-theory",
                    "title": "Color Theory",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Hue, saturation, value, and harmony.",
                    "learn": [
                        {"type": "p", "text": "Color has three properties: hue (red, blue, etc.), saturation (intensity), and value (lightness or darkness). Color harmony uses relationships on the color wheel."},
                        {"type": "list", "items": [
                            "Primary colors: red, yellow, blue.",
                            "Secondary colors: green, orange, purple.",
                            "Complementary: opposite on the wheel (red/green).",
                            "Analogous: next to each other (blue, blue-green, green).",
                        ]},
                        {"type": "activity", "title": "Palette maker", "text": "Pick a subject and create a complementary color palette. Make a small digital swatch sheet showing the colors."},
                    ],
                    "check": {
                        "prompt": "Show what you know about color theory.",
                        "questions": [
                            {"q": "Which pair is complementary?", "options": ["blue and orange", "blue and green", "red and orange"], "answer": "blue and orange", "explain": "Complementary colors sit opposite each other on the color wheel."},
                            {"q": "Value refers to…", "options": ["lightness or darkness", "hue name", "saturation"], "answer": "lightness or darkness", "explain": "Value is how light or dark a color is."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "design-and-portfolio",
            "title": "Design and Portfolio",
            "summary": "Typography, layout, and presenting finished work.",
            "order": 2,
            "lessons": [
                {
                    "slug": "typography-and-layout",
                    "title": "Typography and Layout",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Choose fonts, create hierarchy, and design readable layouts.",
                    "learn": [
                        {"type": "p", "text": "Typography is the art of arranging type. Readability matters more than decoration. Pair fonts by contrast (serif with sans serif) rather than similarity. Use size, weight, and spacing to create hierarchy."},
                        {"type": "list", "items": [
                            "Serif fonts: Times, Georgia — good for long text.",
                            "Sans-serif fonts: Helvetica, Arial — clean for screens.",
                            "Hierarchy: bigger = more important.",
                            "Line spacing: 1.2 to 1.5 for body text.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about typography.",
                        "questions": [
                            {"q": "Which font type is often used for long body text in books?", "options": ["serif", "sans-serif", "script"], "answer": "serif", "explain": "Serifs guide the eye along lines of text, improving readability."},
                            {"q": "What does hierarchy in typography mean?", "options": ["showing importance through size and weight", "using only one font", "writing in all caps"], "answer": "showing importance through size and weight", "explain": "Hierarchy helps readers scan and understand information quickly."},
                        ],
                    },
                },
                {
                    "slug": "portfolio-presentation",
                    "title": "Portfolio Presentation",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Curate, caption, and present a portfolio.",
                    "learn": [
                        {"type": "p", "text": "A portfolio shows your best work and your range. Quality beats quantity. Choose pieces that show growth and skill. Include captions explaining your process and intent."},
                        {"type": "list", "items": [
                            "Curate 8–12 strong pieces.",
                            "Include at least one project from each technique you learned.",
                            "Write a one-sentence description for each piece.",
                            "Present in a clean PDF or online gallery.",
                        ]},
                        {"type": "activity", "title": "Portfolio draft", "text": "Select your three best pieces. For each, write a caption stating title, medium, tools, and what you wanted to express."},
                    ],
                    "check": {
                        "prompt": "Show what you know about portfolio presentation.",
                        "questions": [
                            {"q": "A portfolio should emphasize…", "options": ["quality over quantity", "quantity over quality", "random selection"], "answer": "quality over quantity", "explain": "Fewer polished pieces communicate more than many rough ones."},
                            {"q": "What should a portfolio caption include?", "options": ["title, medium, and intent", "only the date", "the artist's biography"], "answer": "title, medium, and intent", "explain": "Captions give viewers context for the work."},
                        ],
                    },
                },
            ],
        },
    ],
}
