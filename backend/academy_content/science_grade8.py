"""Science — Grade 8 (full published course)."""

SCIENCE_GRADE_8 = {
    "slug": "science-grade-8",
    "title": "Science — Grade 8",
    "summary": "Newton's laws, energy, and waves.",
    "description": (
        "Eighth-grade science is the bridge to high-school physics and chemistry. "
        "Students master Newton's laws of motion, explore energy forms and transformations, "
        "and investigate wave properties and the electromagnetic spectrum. "
        "Each lesson uses real-world examples, diagrams, and hands-on investigations."
    ),
    "subject": "science",
    "subject_label": "Science",
    "track": "foundations",
    "tracks": ["foundations", "builder", "artist", "scholar"],
    "grades": ["8"],
    "grade_label": "Grade 8",
    "status": "published",
    "audience": "Grade 8 (ages 13–14), Foundations track.",
    "est_hours": 22,
    "passing_score": 80,
    "learning_objectives": [
        "Apply Newton's three laws of motion.",
        "Explain the relationship between force, mass, and acceleration.",
        "Describe potential and kinetic energy and their transformations.",
        "Investigate wave properties: wavelength, frequency, and amplitude.",
        "Understand the electromagnetic spectrum and its applications.",
    ],
    "units": [
        {
            "slug": "forces-and-motion",
            "title": "Forces and Motion",
            "summary": "Newton's laws, speed, and acceleration.",
            "order": 1,
            "lessons": [
                {
                    "slug": "newtons-first-law",
                    "title": "Newton's First Law: Inertia",
                    "order": 1,
                    "minutes": 18,
                    "summary": "Objects at rest stay at rest; objects in motion stay in motion.",
                    "learn": [
                        {"type": "p", "text": "Newton's First Law is also called the law of inertia. Inertia is the tendency of an object to resist changes in motion. An object at rest stays at rest, and an object in motion keeps moving at the same speed and direction — unless a net force acts on it."},
                        {"type": "example", "title": "Car example", "text": "When a car stops suddenly, you lurch forward. Your body was in motion, and the seat belt applies a force to stop you. Without a seat belt, inertia keeps you moving."},
                        {"type": "activity", "title": "Coin drop", "text": "Place a coin on a card over a cup. Snap the card away quickly. The coin drops into the cup because of inertia."},
                    ],
                    "check": {
                        "prompt": "Show what you know about Newton's First Law.",
                        "questions": [
                            {"q": "Inertia is…", "options": ["the tendency to resist changes in motion", "the force of gravity", "the speed of an object"], "answer": "the tendency to resist changes in motion", "explain": "Inertia is the resistance to changes in motion."},
                            {"q": "When a car stops suddenly, why do you move forward?", "options": ["inertia", "gravity", "friction"], "answer": "inertia", "explain": "Your body keeps moving because of inertia."},
                        ],
                    },
                },
                {
                    "slug": "newtons-second-law",
                    "title": "Newton's Second Law: F = ma",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Force equals mass times acceleration.",
                    "learn": [
                        {"type": "p", "text": "Newton's Second Law shows how force, mass, and acceleration are related: F = ma. If you increase force, acceleration increases. If you increase mass, acceleration decreases."},
                        {"type": "example", "title": "Push a toy car", "text": "Push a toy car with a gentle force and it accelerates slowly. Push harder and it accelerates more. Add a heavy book to the car and the same push gives less acceleration."},
                        {"type": "list", "items": [
                            "Force is measured in newtons (N).",
                            "Mass is measured in kilograms (kg).",
                            "Acceleration is measured in meters per second squared (m/s²).",
                            "F = ma means force equals mass times acceleration.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about Newton's Second Law.",
                        "questions": [
                            {"q": "If you double the force on the same mass, acceleration…", "options": ["doubles", "halves", "stays the same"], "answer": "doubles", "explain": "F = ma: with constant mass, force and acceleration are directly proportional."},
                            {"q": "If you increase mass with the same force, acceleration…", "options": ["decreases", "increases", "stays the same"], "answer": "decreases", "explain": "More mass means more inertia, so the same force produces less acceleration."},
                            {"q": "Force is measured in…", "options": ["newtons", "kilograms", "meters"], "answer": "newtons", "explain": "The SI unit of force is the newton (N)."},
                        ],
                    },
                },
                {
                    "slug": "newtons-third-law",
                    "title": "Newton's Third Law: Action and Reaction",
                    "order": 3,
                    "minutes": 15,
                    "summary": "Forces come in pairs.",
                    "learn": [
                        {"type": "p", "text": "Newton's Third Law says: For every action force, there is an equal and opposite reaction force. Forces always come in pairs. When you push on a wall, the wall pushes back on you with the same amount of force."},
                        {"type": "example", "title": "Rocket launch", "text": "A rocket engine pushes hot gases down (action). The gases push the rocket up (reaction). The forces are equal and opposite, but because the rocket is much lighter, it accelerates more."},
                    ],
                    "check": {
                        "prompt": "Show what you know about Newton's Third Law.",
                        "questions": [
                            {"q": "When you jump, you push down on Earth. What does Earth do?", "options": ["pushes you up with equal force", "does not push back", "pushes you down harder"], "answer": "pushes you up with equal force", "explain": "Action and reaction forces are equal and opposite."},
                            {"q": "Why does a balloon fly around when you let the air out?", "options": ["air pushes forward, balloon goes backward", "the air is lighter", "magic"], "answer": "air pushes forward, balloon goes backward", "explain": "The air pushes out (action) and the balloon is pushed forward (reaction)."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "energy-and-waves",
            "title": "Energy and Waves",
            "summary": "Forms of energy, transformations, and wave properties.",
            "order": 2,
            "lessons": [
                {
                    "slug": "potential-and-kinetic-energy",
                    "title": "Potential and Kinetic Energy",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Energy stored and energy in motion.",
                    "learn": [
                        {"type": "p", "text": "Energy is the ability to do work. Kinetic energy is energy of motion — a rolling ball or flying bird. Potential energy is stored energy — a stretched rubber band or a ball held high above the ground."},
                        {"type": "example", "title": "Pendulum", "text": "A pendulum at the highest point has maximum potential energy. At the lowest point it has maximum kinetic energy. Energy transforms back and forth as it swings."},
                        {"type": "list", "items": [
                            "Kinetic: motion, heat, sound, light when moving.",
                            "Potential: gravitational, elastic, chemical.",
                            "Energy is conserved — it changes forms but is never lost.",
                        ]},
                    ],
                    "check": {
                        "prompt": "Show what you know about energy forms.",
                        "questions": [
                            {"q": "A ball at the top of a hill has mostly…", "options": ["potential energy", "kinetic energy", "thermal energy"], "answer": "potential energy", "explain": "Height above the ground gives gravitational potential energy."},
                            {"q": "A moving car has mostly…", "options": ["kinetic energy", "potential energy", "chemical energy"], "answer": "kinetic energy", "explain": "Kinetic energy is the energy of motion."},
                        ],
                    },
                },
                {
                    "slug": "wave-properties",
                    "title": "Wave Properties",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Wavelength, frequency, amplitude, and the electromagnetic spectrum.",
                    "learn": [
                        {"type": "p", "text": "Waves carry energy without moving matter. They have wavelength (distance between crests), frequency (crests per second), and amplitude (height from rest). Sound waves, light waves, and water waves all share these properties."},
                        {"type": "list", "items": [
                            "Wavelength: distance between two matching points on a wave.",
                            "Frequency: how many crests pass a point each second (Hz).",
                            "Amplitude: wave height, related to energy.",
                            "Electromagnetic spectrum: radio, microwaves, infrared, visible light, ultraviolet, X-rays, gamma rays.",
                        ]},
                        {"type": "example", "title": "Rope wave", "text": "Shake a rope up and down. The distance between peaks is wavelength. How fast peaks pass a point is frequency. Higher frequency means more energy."},
                    ],
                    "check": {
                        "prompt": "Show what you know about waves.",
                        "questions": [
                            {"q": "Which property is the distance between wave crests?", "options": ["wavelength", "frequency", "amplitude"], "answer": "wavelength", "explain": "Wavelength measures the distance between repeating points on a wave."},
                            {"q": "Higher frequency means…", "options": ["more energy", "less energy", "longer wavelength"], "answer": "more energy", "explain": "Higher-frequency waves carry more energy."},
                        ],
                    },
                },
            ],
        },
    ],
}
