"""
Help Guide — context-sensitive guidance for every route in the platform.
Provides role-aware help content, tips, and related links.  Falls back to
LLM-generated guidance when no pre-written content matches the route.
"""

import logging
from typing import Optional

logger = logging.getLogger("lcewai.help_guide")

# ── Help content per route pattern (longest match wins) ───────────────────────

_ROUTE_HELP: dict = {
    # ── Public routes ──────────────────────────────────────────────────────────
    "/": {
        "title": "Home / Landing",
        "summary": "Welcome to W.A.I. — the Workforce Apprentice Institute.",
        "details": [
            "Browse featured courses, community highlights, and creator profiles.",
            "Use the navigation bar to explore Help Center, Courses, Community, Creators, and Plans.",
            "Sign in or create an account to access the full platform.",
        ],
        "tips": {
            "student": "Start by exploring Courses to see available training paths.",
            "instructor": "Sign in to access your instructor dashboard and manage labs.",
            "admin": "Sign in to access admin tools and user management.",
            "executive_admin": "Sign in for full system oversight and executive commands.",
        },
        "related": ["/courses", "/help-center", "/plans"],
        "common_tasks": ["/register", "/login"],
    },
    "/login": {
        "title": "Sign In",
        "summary": "Log in to your W.A.I. account.",
        "details": [
            "Enter your email and password to sign in.",
            "Use 'Forgot password?' to reset your credentials.",
            "New here? Use the 'Create Account' link to register.",
        ],
        "tips": {
            "student": "After login you'll land on your student dashboard.",
            "instructor": "After login you'll land on your instructor dashboard.",
        },
        "related": ["/register", "/forgot-password"],
        "common_tasks": [],
    },
    "/register": {
        "title": "Create Account",
        "summary": "Register for a new W.A.I. account.",
        "details": [
            "You must be at least 13 years old to create an account.",
            "You must agree to the Terms of Service and Privacy Policy.",
            "Use a strong password (at least 8 characters).",
            "After registration you'll be logged in automatically.",
        ],
        "tips": {
            "student": "Welcome! After registering, explore your dashboard and start with Courses.",
            "instructor": "Instructor accounts are created by admins. Use the login page if you already have one.",
        },
        "related": ["/login", "/terms", "/privacy"],
        "common_tasks": [],
    },
    "/forgot-password": {
        "title": "Forgot Password",
        "summary": "Reset your password via email.",
        "details": [
            "Enter your registered email address.",
            "Check your inbox for a password reset link.",
            "The link expires after 1 hour.",
        ],
        "tips": {},
        "related": ["/login", "/reset-password"],
        "common_tasks": [],
    },
    "/help-center": {
        "title": "Help Center",
        "summary": "Resource hub for housing, legal, food, jobs, education, and health.",
        "details": [
            "Browse six resource categories: Housing, Legal Help, Food & Essentials, Jobs & Training, Education, Health & Wellness.",
            "Each card links to detailed information and community resources.",
            "Use the navigation bar to explore more platform features.",
        ],
        "tips": {
            "student": "The Help Center provides community resources beyond the platform.",
            "instructor": "Refer students here for non-academic support resources.",
        },
        "related": ["/more", "/more/litigation", "/courses"],
        "common_tasks": [],
    },
    "/terms": {
        "title": "Terms of Service",
        "summary": "Platform terms and conditions.",
        "details": [
            "Outlines acceptable use, account responsibilities, and legal disclaimers.",
            "By using the platform you agree to these terms.",
            "Contact the Help Center with questions.",
        ],
        "tips": {},
        "related": ["/privacy", "/help-center"],
        "common_tasks": [],
    },
    "/privacy": {
        "title": "Privacy Policy",
        "summary": "How we collect, use, and protect your data.",
        "details": [
            "We collect only essential data: name, email, course progress.",
            "We do not sell your personal data.",
            "You have GDPR rights: access, export, delete your data.",
        ],
        "tips": {},
        "related": ["/terms", "/settings"],
        "common_tasks": ["/settings"],
    },
    "/courses": {
        "title": "Courses",
        "summary": "Browse available training courses and programs.",
        "details": [
            "View all available courses organized by category.",
            "Click a course to see modules and learning objectives.",
            "Sign in to track your progress and earn credentials.",
        ],
        "tips": {
            "student": "Start with introductory courses and work your way up.",
            "instructor": "Review course content to align with your teaching.",
        },
        "related": ["/modules", "/certificates"],
        "common_tasks": [],
    },
    "/community": {
        "title": "Community",
        "summary": "Connect with other W.A.I. members.",
        "details": [
            "Explore community discussions, events, and member profiles.",
            "Share your journey and learn from others.",
            "Follow community guidelines — be respectful and supportive.",
        ],
        "tips": {},
        "related": ["/creators", "/leaderboard"],
        "common_tasks": [],
    },
    "/creators": {
        "title": "Creators",
        "summary": "Discover content creators and their work.",
        "details": [
            "Browse creator profiles and their published content.",
            "Follow creators whose work aligns with your interests.",
            "Creators can publish courses, labs, and portfolio pieces.",
        ],
        "tips": {
            "instructor": "Consider publishing your own content as a creator.",
        },
        "related": ["/community", "/social/publish"],
        "common_tasks": [],
    },
    "/plans": {
        "title": "Plans & Pricing",
        "summary": "Membership and subscription options.",
        "details": [
            "Compare available membership tiers and their benefits.",
            "Subscribe to access premium features and content.",
            "Free tier provides access to core courses and labs.",
        ],
        "tips": {
            "student": "Start with free tier — upgrade when you need premium features.",
            "instructor": "Premium plans include instructor tools and analytics.",
        },
        "related": ["/subscribe", "/store", "/donate"],
        "common_tasks": ["/subscribe"],
    },
    "/internships": {
        "title": "Internships",
        "summary": "Work-based learning opportunities.",
        "details": [
            "Browse available internship positions and apprenticeships.",
            "Submit applications through the platform.",
            "Track your application status from your dashboard.",
        ],
        "tips": {
            "student": "Internships are a great way to gain real-world experience.",
            "instructor": "Recommend qualified students for internship opportunities.",
        },
        "related": ["/modules", "/labs"],
        "common_tasks": [],
    },
    "/more": {
        "title": "M.O.R.E. Hub",
        "summary": "Michael Oliver Resource Exchange — community services hub.",
        "details": [
            "Access community resources: housing, legal, food, jobs, education, health.",
            "Chat with M.O.R.E. department representatives.",
            "Litigation tool available for legal document assistance.",
        ],
        "tips": {},
        "related": ["/more/litigation", "/more/chat", "/help-center"],
        "common_tasks": ["/more/litigation", "/more/chat"],
    },
    "/more/litigation": {
        "title": "Litigation Weapon",
        "summary": "Legal document assistance and plain-language explanations.",
        "details": [
            "Upload or describe legal documents for plain-language explanation.",
            "Get help understanding legal terms, letters, and court papers.",
            "Not a substitute for legal representation.",
        ],
        "tips": {},
        "related": ["/more", "/help-center"],
        "common_tasks": [],
    },

    # ── Authenticated routes ───────────────────────────────────────────────────
    "/dashboard": {
        "title": "Student Dashboard",
        "summary": "Your personal learning hub.",
        "details": [
            "View your current modules, recent activity, and progress.",
            "Quick-access buttons for key actions: continue learning, view labs, check credentials.",
            "XP and leaderboard show your standing in the community.",
        ],
        "tips": {
            "student": "Check your dashboard daily to track progress and see new assignments.",
            "instructor": "You'll be redirected to your instructor dashboard.",
            "admin": "You'll be redirected to the admin dashboard.",
        },
        "related": ["/modules", "/labs", "/competencies"],
        "common_tasks": ["/modules", "/labs", "/ai"],
    },
    "/dashboard/student": {
        "title": "Student Dashboard",
        "summary": "Your personal learning hub.",
        "details": [
            "Same as /dashboard — your main landing page after login.",
            "Shows modules in progress, completed credentials, and XP.",
        ],
        "tips": {
            "student": "Use this as your home base for all learning activities.",
        },
        "related": ["/modules", "/labs", "/competencies"],
        "common_tasks": ["/modules", "/labs", "/ai"],
    },
    "/dashboard/instructor": {
        "title": "Instructor Dashboard",
        "summary": "Manage your teaching and student oversight.",
        "details": [
            "View your classes, student rosters, and lab submissions.",
            "Grade labs, provide feedback, and track student progress.",
            "Create and manage lab assignments.",
        ],
        "tips": {
            "instructor": "Grade labs promptly to keep students moving forward.",
        },
        "related": ["/instructor/labs", "/attendance", "/incidents"],
        "common_tasks": ["/instructor/labs", "/attendance"],
    },
    "/dashboard/admin": {
        "title": "Admin Dashboard",
        "summary": "Platform administration and user management.",
        "details": [
            "Manage users, cohorts, and role assignments.",
            "View platform analytics and audit logs.",
            "Configure system settings and compliance tracking.",
        ],
        "tips": {
            "admin": "Use the admin tools for user management and system configuration.",
        },
        "related": ["/admin/users", "/admin/analytics", "/admin/audit"],
        "common_tasks": ["/admin/users", "/admin/tools"],
    },
    "/dashboard/exec": {
        "title": "Executive System",
        "summary": "Executive-level system oversight and commands.",
        "details": [
            "Full system oversight: user management, analytics, audit logs.",
            "Executive commands: staff meetings, pipeline processing, batch publishing.",
            "Sage session monitoring and system health checks.",
        ],
        "tips": {
            "executive_admin": "Use staff meetings to delegate across the persona network.",
        },
        "related": ["/admin/system", "/admin/sage-audit"],
        "common_tasks": [],
    },
    "/settings": {
        "title": "Settings",
        "summary": "Manage your account settings and preferences.",
        "details": [
            "Update your profile: name and email address.",
            "Change your password (minimum 8 characters).",
            "Privacy tools: export your data (GDPR) or delete your account.",
            "Re-affirm consent to updated terms if needed.",
        ],
        "tips": {
            "student": "Keep your profile updated so instructors can identify you.",
            "instructor": "Ensure your contact email is correct for student communications.",
        },
        "related": ["/privacy", "/terms"],
        "common_tasks": [],
    },
    "/modules": {
        "title": "Curriculum / Modules",
        "summary": "Browse all learning modules and courses.",
        "details": [
            "View all available modules organized by subject and level.",
            "Click a module to see its lessons, labs, and assessments.",
            "Track completion status for enrolled modules.",
        ],
        "tips": {
            "student": "Modules build on each other — complete prerequisites first.",
            "instructor": "Review module content to align your lab assignments.",
        },
        "related": ["/modules/:slug", "/labs", "/certificates"],
        "common_tasks": [],
    },
    "/labs": {
        "title": "Workforce Labs",
        "summary": "Hands-on lab exercises and assignments.",
        "details": [
            "Browse available lab exercises by category and difficulty.",
            "Submit completed labs for instructor review.",
            "Track your lab completion status and grades.",
        ],
        "tips": {
            "student": "Labs are hands-on — take your time and follow the instructions carefully.",
            "instructor": "Review lab submissions and provide timely feedback.",
        },
        "related": ["/labs/:slug", "/modules", "/competencies"],
        "common_tasks": [],
    },
    "/competencies": {
        "title": "Competencies",
        "summary": "Skill tracking and competency assessments.",
        "details": [
            "View the competency framework and your current skill levels.",
            "Assess your proficiency across different skill areas.",
            "Identify gaps and find modules to address them.",
        ],
        "tips": {
            "student": "Use competencies to identify areas for improvement.",
            "instructor": "Use competency data to tailor your instruction.",
        },
        "related": ["/modules", "/labs", "/adaptive"],
        "common_tasks": [],
    },
    "/certificates": {
        "title": "Certificates",
        "summary": "View and download your earned certificates.",
        "details": [
            "View all certificates you've earned.",
            "Download certificates as PDF for sharing.",
            "Verify certificate authenticity through the verification system.",
        ],
        "tips": {
            "student": "Share your certificates on LinkedIn and your portfolio.",
        },
        "related": ["/credentials", "/portfolio", "/modules"],
        "common_tasks": [],
    },
    "/credentials": {
        "title": "Credentials",
        "summary": "Digital credentials and verified achievements.",
        "details": [
            "View your digital credentials and verified skills.",
            "Share credentials via link or embed.",
            "Credentials are blockchain-verified for authenticity.",
        ],
        "tips": {
            "student": "Credentials are portable — add them to your resume and portfolio.",
        },
        "related": ["/certificates", "/portfolio"],
        "common_tasks": [],
    },
    "/portfolio": {
        "title": "Portfolio",
        "summary": "Your personal portfolio of work and achievements.",
        "details": [
            "Showcase your projects, labs, and credentials.",
            "Customize your public portfolio page.",
            "Share your portfolio link with potential employers.",
        ],
        "tips": {
            "student": "Keep your portfolio updated — it's your professional showcase.",
            "instructor": "Review student portfolios to assess their body of work.",
        },
        "related": ["/p/:slug", "/credentials", "/certificates"],
        "common_tasks": [],
    },
    "/ai": {
        "title": "AI Tutor",
        "summary": "AI-powered tutoring and learning assistance.",
        "details": [
            "Chat with the AI tutor for help with course material.",
            "Available modes: Tutor, Scripture, Quiz Generator, Explain, NEC Lookup, Blueprint, Ancestral Sage.",
            "Sage mode offers depth, intensity, and cultural focus controls.",
        ],
        "tips": {
            "student": "Use AI Tutor when you're stuck on a concept — it's available 24/7.",
            "instructor": "The AI Tutor supplements your instruction, not replaces it.",
        },
        "related": ["/modules", "/labs", "/council"],
        "common_tasks": [],
    },
    "/adaptive": {
        "title": "Adaptive Learning",
        "summary": "Personalized learning path based on your progress.",
        "details": [
            "AI-driven adaptive learning that adjusts to your pace.",
            "Reviews your strengths and weaknesses to recommend content.",
            "Optimizes your learning path for maximum efficiency.",
        ],
        "tips": {
            "student": "Trust the adaptive path — it's designed to fill your knowledge gaps.",
        },
        "related": ["/modules", "/competencies", "/ai"],
        "common_tasks": [],
    },
    "/compliance": {
        "title": "Compliance Tracking",
        "summary": "Track compliance requirements and training mandates.",
        "details": [
            "View compliance requirements for your program.",
            "Track your progress toward meeting each requirement.",
            "See deadlines and completion status at a glance.",
        ],
        "tips": {
            "student": "Check compliance regularly to ensure you're meeting all requirements.",
            "instructor": "Monitor class compliance and follow up with students at risk.",
        },
        "related": ["/compliance/:slug", "/modules"],
        "common_tasks": [],
    },
    "/attendance": {
        "title": "Attendance",
        "summary": "Track and manage attendance records.",
        "details": [
            "View attendance records for your classes.",
            "Mark attendance for sessions (instructor).",
            "View attendance reports and trends.",
        ],
        "tips": {
            "instructor": "Take attendance at the start of each session.",
        },
        "related": ["/incidents", "/dashboard/instructor"],
        "common_tasks": [],
    },
    "/incidents": {
        "title": "Incident Reporting",
        "summary": "Report and track incidents.",
        "details": [
            "Report safety concerns, policy violations, or other incidents.",
            "Track the status of reported incidents.",
            "Admin review and resolution workflow.",
        ],
        "tips": {
            "student": "Report any safety concerns or policy violations immediately.",
            "instructor": "Follow up on reported incidents in a timely manner.",
        },
        "related": ["/attendance", "/compliance"],
        "common_tasks": [],
    },
    "/leaderboard": {
        "title": "XP Leaderboard",
        "summary": "Community leaderboard ranked by experience points.",
        "details": [
            "See how you rank against other learners.",
            "Earn XP by completing modules, labs, and assessments.",
            "Top performers are recognized in the community.",
        ],
        "tips": {
            "student": "Consistent progress is the best way to climb the leaderboard.",
        },
        "related": ["/modules", "/labs", "/community"],
        "common_tasks": [],
    },
    "/palace": {
        "title": "Members' Palace",
        "summary": "Exclusive member space with premium features.",
        "details": [
            "Access premium content and member-only resources.",
            "Connect with other premium members.",
            "Exclusive events and opportunities.",
        ],
        "tips": {
            "student": "Premium membership unlocks additional resources and support.",
        },
        "related": ["/plans", "/subscribe", "/elder-council"],
        "common_tasks": [],
    },
    "/elder-council": {
        "title": "Elder Council",
        "summary": "Council of 24 Elders — wisdom and guidance.",
        "details": [
            "Access the collective wisdom of the Elder Council.",
            "Submit questions for council consideration.",
            "Review council guidance and teachings.",
        ],
        "tips": {},
        "related": ["/palace", "/council", "/ai"],
        "common_tasks": [],
    },
    "/council": {
        "title": "Council (Sage)",
        "summary": "Orchestrator chat with the full persona network.",
        "details": [
            "Chat with the AI orchestrator that coordinates all personas.",
            "Get responses informed by the full WAI persona network.",
            "Advanced use: route to specific personas.",
        ],
        "tips": {
            "student": "The Council combines all persona knowledge for comprehensive answers.",
        },
        "related": ["/ai", "/elder-council"],
        "common_tasks": [],
    },
    "/store": {
        "title": "Store",
        "summary": "Purchase courses, tools, and merchandise.",
        "details": [
            "Browse available products and courses for purchase.",
            "Secure checkout via payment processor.",
            "View your purchase history.",
        ],
        "tips": {},
        "related": ["/subscribe", "/donate", "/payment/history"],
        "common_tasks": [],
    },
    "/subscribe": {
        "title": "Subscribe",
        "summary": "Manage your membership subscription.",
        "details": [
            "Choose a membership tier that fits your needs.",
            "Monthly and annual billing options.",
            "Cancel or change your plan anytime.",
        ],
        "tips": {
            "student": "Start with the free tier and upgrade when you need more.",
        },
        "related": ["/plans", "/store", "/donate"],
        "common_tasks": [],
    },
    "/donate": {
        "title": "Donate",
        "summary": "Support W.A.I. with a donation.",
        "details": [
            "One-time or recurring donation options.",
            "Your contribution supports free education and community resources.",
            "Tax-deductible where applicable.",
        ],
        "tips": {},
        "related": ["/subscribe", "/store"],
        "common_tasks": [],
    },
    "/social/publish": {
        "title": "Social Publisher",
        "summary": "Create and publish social media content.",
        "details": [
            "Write and schedule social media posts.",
            "Publish to connected platforms.",
            "Track engagement and reach.",
        ],
        "tips": {},
        "related": ["/more", "/community"],
        "common_tasks": [],
    },
    "/app/more": {
        "title": "M.O.R.E. Hub (Authenticated)",
        "summary": "Full M.O.R.E. platform with all features.",
        "details": [
            "Access all M.O.R.E. department services.",
            "Chat with department representatives.",
            "Manage your M.O.R.E. profile and activity.",
        ],
        "tips": {},
        "related": ["/more", "/more/chat", "/more/admin"],
        "common_tasks": ["/more/chat"],
    },
    "/more/chat": {
        "title": "M.O.R.E. Chat",
        "summary": "Chat with M.O.R.E. department representatives.",
        "details": [
            "Select a department to chat with.",
            "Get help with housing, legal, food, jobs, education, or health.",
            "Chat history is saved for your reference.",
        ],
        "tips": {},
        "related": ["/more", "/more/admin", "/more/ops"],
        "common_tasks": [],
    },
    "/more/admin": {
        "title": "M.O.R.E. Admin",
        "summary": "Administer M.O.R.E. department operations.",
        "details": [
            "Manage department representatives and their availability.",
            "View chat transcripts and analytics.",
            "Configure M.O.R.E. system settings.",
        ],
        "tips": {},
        "related": ["/more", "/more/ops", "/admin"],
        "common_tasks": [],
    },
    "/more/ops": {
        "title": "M.O.R.E. Operations",
        "summary": "M.O.R.E. operational tools and reporting.",
        "details": [
            "Operational dashboards and metrics.",
            "Resource allocation and tracking.",
            "Community impact reporting.",
        ],
        "tips": {},
        "related": ["/more/admin", "/more"],
        "common_tasks": [],
    },
    "/admin/users": {
        "title": "User Management",
        "summary": "Manage platform users and roles.",
        "details": [
            "View all users, search by name or email.",
            "Assign roles: student, instructor, admin.",
            "Associate users with cohorts.",
            "Reset passwords and manage account status.",
        ],
        "tips": {
            "admin": "Use careful judgment when assigning admin roles.",
            "executive_admin": "Full control over all user accounts including other admins.",
        },
        "related": ["/admin/analytics", "/admin/audit"],
        "common_tasks": [],
    },
    "/admin/tools": {
        "title": "Admin Tools",
        "summary": "System administration tools and utilities.",
        "details": [
            "Database management tools.",
            "System configuration and settings.",
            "Maintenance utilities.",
        ],
        "tips": {
            "admin": "Some tools can affect all users — use with caution.",
        },
        "related": ["/admin/system", "/admin/users"],
        "common_tasks": [],
    },
    "/admin/analytics": {
        "title": "Analytics",
        "summary": "Platform analytics and reporting.",
        "details": [
            "User growth and engagement metrics.",
            "Course completion and progress analytics.",
            "Revenue and subscription reports.",
        ],
        "tips": {
            "admin": "Export reports for external analysis.",
        },
        "related": ["/admin/audit", "/admin/users"],
        "common_tasks": [],
    },
    "/admin/audit": {
        "title": "Audit Log",
        "summary": "System-wide audit trail of all actions.",
        "details": [
            "View all administrative actions and changes.",
            "Filter by user, action type, and date range.",
            "Critical for security review and compliance.",
        ],
        "tips": {
            "admin": "Review audit logs regularly for suspicious activity.",
        },
        "related": ["/admin/analytics", "/admin/users"],
        "common_tasks": [],
    },
    "/admin/system": {
        "title": "Executive System",
        "summary": "Executive-level system commands and configuration.",
        "details": [
            "Staff meeting: convene the full persona network.",
            "Pipeline processing: route content through the intent pipeline.",
            "Batch publishing: publish pending content across platforms.",
            "System health monitoring and configuration.",
        ],
        "tips": {
            "executive_admin": "Staff meetings delegate tasks across the WAI persona network. Use them for complex coordination.",
        },
        "related": ["/admin/sage-audit", "/admin/audit"],
        "common_tasks": [],
    },
    "/admin/sage-audit": {
        "title": "Sage Sessions",
        "summary": "Audit and review Sage AI interactions.",
        "details": [
            "View all Sage (Ancestral Sage) chat sessions.",
            "Review user interactions for quality and safety.",
            "Monitor Sage mode usage and integrity checks.",
        ],
        "tips": {
            "executive_admin": "Regularly review Sage sessions to ensure alignment with institutional values.",
        },
        "related": ["/admin/system", "/ai"],
        "common_tasks": [],
    },
    "/avatar-setup": {
        "title": "Avatar Setup",
        "summary": "Customize your profile avatar.",
        "details": [
            "Choose or upload a profile avatar.",
            "Customize avatar appearance.",
            "Your avatar appears on your profile and in the community.",
        ],
        "tips": {},
        "related": ["/settings", "/portfolio"],
        "common_tasks": [],
    },
    "/playlist/dashboard": {
        "title": "Playlist Dashboard",
        "summary": "Manage your curated playlists.",
        "details": [
            "View and manage your content playlists.",
            "Track playlist performance and engagement.",
            "Submit playlists for public listing.",
        ],
        "tips": {},
        "related": [],
        "common_tasks": [],
    },
    "/payment/history": {
        "title": "Payment History",
        "summary": "View your payment and subscription history.",
        "details": [
            "View all past payments and transactions.",
            "Download receipts and invoices.",
            "Manage payment methods.",
        ],
        "tips": {},
        "related": ["/subscribe", "/store", "/admin/payments"],
        "common_tasks": [],
    },
    "/admin/payments": {
        "title": "Admin Payments",
        "summary": "Manage platform payments and refunds.",
        "details": [
            "View all platform transactions.",
            "Process refunds and adjustments.",
            "Revenue reports and reconciliation.",
        ],
        "tips": {
            "admin": "Process refunds promptly per the refund policy.",
        },
        "related": ["/payment/history", "/admin/analytics"],
        "common_tasks": [],
    },
}

# ── Admin & executive routes that inherit from parent patterns ────────────────
_ROUTE_ALIASES = {
    "/admin": "/dashboard/admin",
    "/admin/associate": "/admin/users",
    "/instructor": "/dashboard/instructor",
    "/instructor/labs": "/labs",
    "/app/helper": "/help-center",
    "/helper": "/help-center",
}


def _resolve_route(path: str) -> str:
    """Resolve a URL path to the closest help content key (longest match wins)."""
    path = path.rstrip("/") or "/"
    if path in _ROUTE_HELP:
        return path
    if path in _ROUTE_ALIASES:
        return _ROUTE_ALIASES[path]
    # Try prefix matching for parameterized routes
    candidates = sorted(_ROUTE_HELP.keys(), key=len, reverse=True)
    for key in candidates:
        if path.startswith(key.rstrip("/")):
            return key
    return "/"


def get_help_for(role: str, path: str, query: Optional[str] = None) -> dict:
    """Return structured help content for a given role and URL path.
    Falls back to generic guidance when no pre-written content exists."""
    resolved_key = _resolve_route(path)
    entry = _ROUTE_HELP.get(resolved_key)

    if not entry:
        return {
            "title": path.strip("/").replace("-", " ").title() or "Home",
            "summary": "Help content coming soon for this page.",
            "details": ["Explore the page to discover its features."],
            "tips": {},
            "related": [],
            "common_tasks": [],
        }

    role_tip = entry["tips"].get(role, entry["tips"].get("student", ""))
    result = {
        "title": entry["title"],
        "summary": entry["summary"],
        "details": entry["details"],
        "tip": role_tip,
        "related": entry.get("related", []),
        "common_tasks": entry.get("common_tasks", []),
    }

    # If there's a search query, filter details for relevance
    if query:
        q = query.lower()
        result["details"] = [d for d in result["details"] if q in d.lower()]
        if not result["details"]:
            result["details"] = [f'No results found for "{query}". Try browsing the page directly.']

    return result
