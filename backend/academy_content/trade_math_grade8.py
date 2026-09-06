"""Trade Mathematics — Grade 8 (full published course)."""

TRADE_MATH_GRADE_8 = {
    "slug": "trade-math-grade-8",
    "title": "Trade Mathematics — Grade 8",
    "summary": "Measurement, geometry, and estimating for the trades.",
    "description": (
        "This Builder-track math course applies measurement, fractions, decimals, "
        "and geometry to real trades work. Students calculate perimeters, areas, "
        "and volumes; convert units; read tape measures; and estimate material quantities."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "builder",
    "tracks": ["builder"],
    "grades": ["8"],
    "grade_label": "Grade 8",
    "status": "published",
    "audience": "Grade 8 Builder-track students; practical math for hands-on careers.",
    "est_hours": 20,
    "passing_score": 80,
    "learning_objectives": [
        "Read and use a standard tape measure.",
        "Convert between fractions, decimals, and percentages.",
        "Calculate perimeter, area, and volume for common shapes.",
        "Estimate material quantities for small projects.",
        "Apply the Pythagorean theorem on the job site.",
    ],
    "units": [
        {
            "slug": "measurement-and-conversions",
            "title": "Measurement and Conversions",
            "summary": "Fractions, decimals, percentages, and units.",
            "order": 1,
            "lessons": [
                {
                    "slug": "tape-measure-and-fractions",
                    "title": "The Tape Measure and Fractions",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Read inches in halves, fourths, eighths, and sixteenths.",
                    "learn": [
                        {"type": "p", "text": "Tape measures are marked in inches, with smaller marks for fractions. An inch is divided into halves, fourths, eighths, and sixteenths. The longest marks are half inches; the shortest are sixteenths."},
                        {"type": "list", "items": [
                            "16 sixteenths = 1 inch.",
                            "8 eighths = 1 inch.",
                            "4 fourths = 1 inch.",
                            "2 halves = 1 inch.",
                        ]},
                        {"type": "activity", "title": "Tape measure practice", "text": "Measure five boards or books in inches. Record each measurement in inches and fractions. Convert any fraction to sixteenths."},
                    ],
                    "check": {
                        "prompt": "Show what you know about tape measures.",
                        "questions": [
                            {"q": "How many sixteenths are in one inch?", "options": ["16", "8", "4"], "answer": "16", "explain": "A standard tape divides each inch into 16 equal parts."},
                            {"q": "Which is larger: 3/8 inch or 1/4 inch?", "options": ["3/8 inch", "1/4 inch", "they are equal"], "answer": "3/8 inch", "explain": "3/8 = 6/16, 1/4 = 4/16. 6/16 > 4/16."},
                        ],
                    },
                },
                {
                    "slug": "converting-units",
                    "title": "Converting Units",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Customary and metric conversions for the trades.",
                    "learn": [
                        {"type": "p", "text": "Tradespeople convert units daily. Inches to feet, feet to yards, ounces to pounds, Celsius to Fahrenheit. The key is knowing the conversion factor and multiplying or dividing."},
                        {"type": "list", "items": [
                            "12 inches = 1 foot.",
                            "3 feet = 1 yard.",
                            "16 ounces = 1 pound.",
                            "°F = °C × 9/5 + 32.",
                        ]},
                        {"type": "example", "title": "Convert 48 inches to feet", "text": "48 ÷ 12 = 4 feet."},
                        {"type": "activity", "title": "Convert five measurements", "text": "Convert: 36 inches to feet; 5 feet to inches; 64 ounces to pounds; 2 yards to feet; 25°C to Fahrenheit."},
                    ],
                    "check": {
                        "prompt": "Show what you know about unit conversion.",
                        "questions": [
                            {"q": "How many feet are in 24 inches?", "options": ["2", "24", "12"], "answer": "2", "explain": "24 ÷ 12 = 2 feet."},
                            {"q": "Convert 2 yards to feet.", "options": ["6", "2", "24"], "answer": "6", "explain": "2 × 3 = 6 feet."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "geometry-and-estimating",
            "title": "Geometry and Estimating",
            "summary": "Area, volume, and practical estimating.",
            "order": 2,
            "lessons": [
                {
                    "slug": "area-and-perimeter",
                    "title": "Area and Perimeter",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Find perimeter and area of rectangles and triangles.",
                    "learn": [
                        {"type": "p", "text": "Perimeter is the distance around a shape. Area is the amount of surface inside. For a rectangle: Perimeter = 2(length + width). Area = length × width. For a triangle: Area = ½ × base × height."},
                        {"type": "example", "title": "Room flooring", "text": "A room is 12 ft by 10 ft. Area = 12 × 10 = 120 sq ft. You need 120 sq ft of flooring plus 10% extra for waste: 132 sq ft total."},
                        {"type": "activity", "title": "Measure a room", "text": "Measure the perimeter and area of a room in your home. Calculate how many tiles (12 in × 12 in) you would need, adding 10% waste."},
                    ],
                    "check": {
                        "prompt": "Show what you know about area and perimeter.",
                        "questions": [
                            {"q": "What is the area of a 9 ft by 12 ft room?", "options": ["108 sq ft", "42 sq ft", "21 sq ft"], "answer": "108 sq ft", "explain": "9 × 12 = 108 square feet."},
                            {"q": "What is the perimeter of a square with 5 ft sides?", "options": ["20 ft", "25 ft", "10 ft"], "answer": "20 ft", "explain": "4 × 5 = 20 feet."},
                        ],
                    },
                },
                {
                    "slug": "volume-and-estimating",
                    "title": "Volume and Estimating",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Cubic measurements and material estimates.",
                    "learn": [
                        {"type": "p", "text": "Volume measures space inside a 3D shape. A rectangular prism: V = length × width × height. Contractors use volume to order concrete, gravel, or insulation."},
                        {"type": "list", "items": [
                            "Volume of a box: l × w × h.",
                            "Volume of a cylinder: π × r² × height.",
                            "Always add 5–10% overage for waste.",
                            "Bulk materials are often ordered by the cubic yard.",
                        ]},
                        {"type": "example", "title": "Concrete slab", "text": "Slab: 20 ft × 10 ft × 0.5 ft = 100 cubic feet. 27 cubic feet per cubic yard: 100 ÷ 27 ≈ 3.7 cubic yards. Order 4 cubic yards with waste."},
                    ],
                    "check": {
                        "prompt": "Show what you know about volume and estimating.",
                        "questions": [
                            {"q": "What is the volume of a 2 ft × 3 ft × 4 ft box?", "options": ["24 cubic feet", "9 cubic feet", "18 cubic feet"], "answer": "24 cubic feet", "explain": "2 × 3 × 4 = 24 cubic feet."},
                            {"q": "How many cubic feet in a cubic yard?", "options": ["27", "9", "3"], "answer": "27", "explain": "3 ft × 3 ft × 3 ft = 27 cubic feet per cubic yard."},
                        ],
                    },
                },
            ],
        },
    ],
}
