"""app/config.py — All environment variables, constants, and SYSTEM_PROMPTS.

Extracted from backend/server.py lines 85–412 and 2687–2730 and 2955–2971.
No logic changed — only moved here so route modules can import from one place.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent / "backend"
load_dotenv(ROOT_DIR / ".env", override=True)

# ── MongoDB ───────────────────────────────────────────────────────────────────
MONGO_URL        = os.environ.get("MONGO_URL", "")
DB_NAME          = os.environ.get("DB_NAME", "ancestral_sage")
MONGO_BACKUP_URL = os.environ.get("MONGO_BACKUP_URL", "")
MONGO_BACKUP_DB  = os.environ.get("MONGO_BACKUP_DB", "")

# ── JWT / Auth ────────────────────────────────────────────────────────────────
import secrets

JWT_SECRET = os.environ.get("JWT_SECRET") or secrets.token_hex(32)
JWT_ALGO = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.environ.get("JWT_EXPIRE_HOURS", "168"))

# ── AI / LLM ─────────────────────────────────────────────────────────────────
EMERGENT_LLM_KEY   = os.environ.get("EMERGENT_LLM_KEY", "")
OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY", EMERGENT_LLM_KEY)
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY", "")
CEREBRAS_API_KEY   = os.environ.get("CEREBRAS_API_KEY", "")
MISTRAL_API_KEY    = os.environ.get("MISTRAL_API_KEY", "")
# Kept as empty string so any code that reads it won't crash (Anthropic removed)
ANTHROPIC_API_KEY  = ""

# ── Stripe ───────────────────────────────────────────────────────────────────
STRIPE_SECRET_KEY       = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY  = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET   = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# ── Gumroad ──────────────────────────────────────────────────────────────────
GUMROAD_API_KEY = os.environ.get("GUMROAD_API_KEY", "")

# ── Frontend / CORS ───────────────────────────────────────────────────────────
SERVE_FRONTEND = os.environ.get("SERVE_FRONTEND", "0") == "1"
BACKUP_ORIGIN  = os.environ.get("BACKUP_ORIGIN", "").strip()
FRONTEND_URL   = os.environ.get("FRONTEND_URL", "")

# ── Email ─────────────────────────────────────────────────────────────────────
RESEND_API_KEY    = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM       = os.environ.get("RESEND_FROM", "M.O.R.E. Help Center <morehelpcenter@gmail.com>")
GMAIL_USER        = os.environ.get("GMAIL_USER", "morehelpcenter@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RESET_TOKEN_TTL_MIN = int(os.environ.get("PASSWORD_RESET_TTL_MIN", "30"))

# ── Executive accounts ────────────────────────────────────────────────────────
EXEC_ADMIN_EMAIL   = os.environ.get("EXEC_ADMIN_EMAIL", "delon.oliver@lightningcityelectric.com")
EXEC_DEFAULT_PASSWORD = os.environ.get("EXEC_DEFAULT_PASSWORD", "")

BACKUP_EXEC_EMAIL           = os.environ.get("BACKUP_EXEC_ADMIN_EMAIL", "youpickeddoliver@gmail.com")
BACKUP_EXEC_DEFAULT_PASSWORD = os.environ.get("BACKUP_EXEC_DEFAULT_PASSWORD", "")

NAM_EXEC_EMAIL           = os.environ.get("NAM_EXEC_EMAIL", "souppoetry@gmail.com")
NAM_EXEC_DEFAULT_PASSWORD = os.environ.get("NAM_EXEC_DEFAULT_PASSWORD", "")

PLATFORM_NOTIFY_EMAIL = os.environ.get(
    "PLATFORM_NOTIFY_EMAIL",
    os.environ.get("GMAIL_USER", "morehelpcenter@gmail.com"),
)

EXEC_FORCE_RESET  = os.environ.get("EXEC_FORCE_RESET", "0") == "1"
EXEC_RESET_SECRET = os.environ.get("EXEC_RESET_SECRET", "")
LEGACY_EXEC_EMAILS: set = set()

# ── Role system ───────────────────────────────────────────────────────────────
ROLE_RANK = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4}

# ── Environment ───────────────────────────────────────────────────────────────
APP_ENV = os.environ.get("APP_ENV", "production").lower()  # "development" | "staging" | "production"
_IS_DEV  = APP_ENV == "development"
_IS_PROD = APP_ENV == "production"

# ── Observability / Alerting ──────────────────────────────────────────────────
SENTRY_DSN         = os.environ.get("SENTRY_DSN", "")
SLACK_ALERT_WEBHOOK = os.environ.get("SLACK_ALERT_WEBHOOK", "")

# ── App version ───────────────────────────────────────────────────────────────
APP_VERSION = "4.1.0"

# ── Ancestral Sage ────────────────────────────────────────────────────────────
ANCESTRAL_SAGE_CONSENT_TTL_MIN = int(
    os.environ.get("ANCESTRAL_SAGE_CONSENT_TTL_MIN", "120")
)
_CONSENT_COMPREHENSION_PHRASE = "I understand and accept the risks of this practice."
_CRISIS_TRIGGERS = (
    "kill myself",
    "suicide",
    "end my life",
    "want to die",
    "wanna die",
    "take my life",
    "hang myself",
    "shoot myself",
)
CRISIS_REPLY = (
    "I can't assist with that request. If you are in immediate danger or "
    "experiencing a crisis, please contact local emergency services or a "
    "licensed professional right now.\n\n"
    "United States — call or text 988 (Suicide & Crisis Lifeline).\n"
    "Crisis Text Line — text HOME to 741741.\n"
    "International directory — https://findahelpline.com\n\n"
    "I'm here when you're ready to continue with safe, grounding practices. "
    "Aftercare: take three slow breaths, drink water, place a hand on your chest, "
    "and reach out to someone you trust."
)

# ── TTS performance / circuit breaker ─────────────────────────────────────────
TTS_SESSION_CHAR_CAP       = int(os.environ.get("TTS_SESSION_CHAR_CAP", "10000"))
TTS_USER_DAILY_CHAR_CAP    = int(os.environ.get("TTS_USER_DAILY_CHAR_CAP", "200000"))
TTS_BUDGET_ALERT_RATIO     = float(os.environ.get("TTS_BUDGET_ALERT_RATIO", "0.8"))
TTS_BREAKER_FAIL_THRESHOLD = int(os.environ.get("TTS_BREAKER_FAIL_THRESHOLD", "5"))
TTS_BREAKER_WINDOW_S       = int(os.environ.get("TTS_BREAKER_WINDOW_S", "60"))
TTS_BREAKER_COOLDOWN_S     = int(os.environ.get("TTS_BREAKER_COOLDOWN_S", "60"))
TTS_METRICS_WINDOW_S       = int(os.environ.get("TTS_METRICS_WINDOW_S", "300"))

# ── DOCS ─────────────────────────────────────────────────────────────────────
_DOCS_ENABLED = os.environ.get("ENABLE_API_DOCS", "0") == "1"

# ── SYSTEM_PROMPTS (imported lazily to avoid circular import with prompts/) ───
def _load_system_prompts() -> dict:
    from prompts.ancestral_sage_prompt import ANCESTRAL_SAGE_PROMPT
    return {
        "tutor": (
            "You are a patient master electrician and faith-forward mentor for W.A.I. — "
            "Workforce Apprentice Institute (LCE-WAI partner program). Answer apprentice "
            "questions clearly, reference NEC articles when relevant, emphasize safety, "
            "and use plain language. Keep replies under 250 words."
        ),
        "scripture": (
            "You are a faith-based electrical trade mentor at W.A.I. For each question, "
            "give a short encouragement tying the apprentice's current work to a relevant "
            "scripture verse, then a one-paragraph teaching point. Keep the tone warm and dignified."
        ),
        "quiz_gen": (
            "You generate short multiple-choice quiz questions (4 options, mark the correct "
            "answer index 0-3) on electrical topics. Output a clean numbered list with answer "
            "key at the end."
        ),
        "explain": (
            "You explain electrical concepts step-by-step to apprentices. Use analogies, "
            "list steps, and close with a 1-line 'Safety first' reminder."
        ),
        "nec_lookup": (
            "You are an NEC (National Electrical Code) reference assistant. When the apprentice "
            "asks about a topic, identify the most likely NEC article and section (e.g., "
            "'NEC 210.8(A)(1)'), summarize the rule in plain English, give one practical example, "
            "and note any common code-cycle changes. ALWAYS remind the apprentice to verify "
            "against the current adopted code edition for their jurisdiction."
        ),
        "blueprint": (
            "You are an electrical blueprint reading assistant. The apprentice will describe "
            "(or paste a description of) a residential or light-commercial electrical plan. "
            "Identify likely circuits, panel sizing, branch counts, and any code concerns. "
            "Output a structured list: Circuits, Panels, Concerns. Keep it concise and tied "
            "to NEC articles where helpful."
        ),
        "ancestral_sage": ANCESTRAL_SAGE_PROMPT,
    }


# Lazy singleton — loaded on first access
_SYSTEM_PROMPTS: dict | None = None


def get_system_prompts() -> dict:
    global _SYSTEM_PROMPTS
    if _SYSTEM_PROMPTS is None:
        _SYSTEM_PROMPTS = _load_system_prompts()
    return _SYSTEM_PROMPTS


# Convenience alias so existing `SYSTEM_PROMPTS["tutor"]` references work
# after `from app.config import SYSTEM_PROMPTS` — the dict is populated on
# first import of this module (not at import-of-config time to allow the
# prompts package to load first).
try:
    SYSTEM_PROMPTS = _load_system_prompts()
except Exception:
    SYSTEM_PROMPTS = {}
