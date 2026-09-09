"""Science Grade 11 — Physics Foundations (published core)."""
SCIENCE_GRADE_11 = {
    "slug": "science-grade-11",
    "title": "Science — Grade 11",
    "summary": "Physics: motion, forces, energy, waves, and modern applications.",
    "description": "Grade 11 physics builds from motion and forces to energy, waves, and electricity — with labs that honor Black physicists' contributions.",
    "subject": "science",
    "subject_label": "Science",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["11"],
    "grade_label": "Grade 11",
    "status": "published",
    "audience": "Grade 11 (ages 16-17)",
    "est_hours": 24,
    "passing_score": 80,
    "learning_objectives": [
        "Describe motion with graphs and equations.",
        "Apply Newton's laws and conservation of energy.",
        "Explain waves, sound, light, and simple circuits.",
    ],
    "units": [
        {"slug": "motion-forces", "title": "Motion and Forces", "summary": "Kinematics and dynamics.", "order": 1, "lessons": [
            {"slug": "kinematics-grade11", "title": "Kinematics", "order": 1, "minutes": 18, "summary": "Position, velocity, acceleration.", "learn": [{"type": "p", "text": "Kinematics describes motion. Position vs time graphs show where; velocity is slope; acceleration is rate of change of velocity. Constant acceleration gives the familiar equations."}], "check": {"prompt": "Kinematics.", "questions": [{"q": "Slope of position-time graph is", "options": ["velocity", "mass", "charge"], "answer": "velocity", "explain": "Rise over run = displacement over time."}]}},
            {"slug": "newton-laws-grade11", "title": "Newton's Laws", "order": 2, "minutes": 18, "summary": "Forces and motion.", "learn": [{"type": "p", "text": "Newton's three laws: inertia, F=ma, and action-reaction. Forces are vectors — direction matters. Free-body diagrams make the analysis clear."}], "check": {"prompt": "Newton.", "questions": [{"q": "F=ma is Newton's", "options": ["second law", "first law", "third law"], "answer": "second law", "explain": "Second law relates force and acceleration."}]}},
        ]},
        {"slug": "energy-waves-circuits-grade11", "title": "Energy, Waves, and Circuits", "summary": "Conservation and applications.", "order": 2, "lessons": [
            {"slug": "energy-grade11", "title": "Energy and Work", "order": 3, "minutes": 18, "summary": "Conservation of energy.", "learn": [{"type": "p", "text": "Energy is conserved — it changes form. Kinetic plus potential is constant without friction. Work is force through distance; power is work per time."}], "check": {"prompt": "Energy.", "questions": [{"q": "Without friction, total mechanical energy", "options": ["is conserved", "disappears", "doubles each second"], "answer": "is conserved", "explain": "Conservation law."}]}},
            {"slug": "waves-light-grade11", "title": "Waves and Light", "order": 4, "minutes": 18, "summary": "Sound and optics basics.", "learn": [{"type": "p", "text": "Waves carry energy. Frequency sets pitch (sound) and color (light). Reflection, refraction, and diffraction explain everyday optics."}], "check": {"prompt": "Waves.", "questions": [{"q": "Higher frequency means", "options": ["higher pitch / bluer light", "no change", "only louder"], "answer": "higher pitch / bluer light", "explain": "Frequency determines tone and color."}]}},
            {"slug": "circuits-grade11", "title": "Simple Circuits", "order": 5, "minutes": 18, "summary": "Current, voltage, resistance.", "learn": [{"type": "p", "text": "A simple circuit needs a source, conductors, and a load. Ohm's law V=IR and power P=VI govern design. Black inventors like Lewis Latimer advanced filament and lighting technology."}], "check": {"prompt": "Circuits.", "questions": [{"q": "Ohm's law is", "options": ["V=IR", "F=ma", "E=mc^2"], "answer": "V=IR", "explain": "Voltage equals current times resistance."}]}},
        ]},
    ],
}
