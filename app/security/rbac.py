"""app/security/rbac.py — Centralized RBAC policy matrix.

Defines roles, permissions, inheritance, and route-level access control.
This is the single authoritative source for all role-based decisions.

Roles (in ascending privilege order):
  guest        — unauthenticated / anonymous
  student      — authenticated free-tier learner
  instructor   — authenticated educator
  admin        — platform administrator
  executive_admin — full system authority

Feature tiers (commercial):
  free         — M.O.R.E. Help Center only, no AI, no legal tools
  premium      — Full AI, legal tools, dashboards, TTS/STT
  executive    — All premium features + system controls

sage_tier (Sage AI depth):
  basic        — Gate 1 only (automated safety filter)
  advanced     — Gates 1-3 (full safety escalation pipeline)
"""
from __future__ import annotations

from enum import IntEnum, auto
from typing import Dict, FrozenSet, Literal, Optional, Set

# ── Role hierarchy ──────────────────────────────────────────────────────────────

class RoleLevel(IntEnum):
    GUEST           = 0
    STUDENT         = 1
    INSTRUCTOR      = 2
    ADMIN           = 3
    EXECUTIVE_ADMIN = 4


ROLE_LEVELS: Dict[str, RoleLevel] = {
    "guest":           RoleLevel.GUEST,
    "student":         RoleLevel.STUDENT,
    "instructor":      RoleLevel.INSTRUCTOR,
    "admin":           RoleLevel.ADMIN,
    "executive_admin": RoleLevel.EXECUTIVE_ADMIN,
}

# Canonical rank mapping (int — matches existing ROLE_RANK in config.py)
ROLE_RANK: Dict[str, int] = {
    "guest":           0,
    "student":         1,
    "instructor":      2,
    "admin":           3,
    "executive_admin": 4,
}

# ── Feature tier hierarchy ──────────────────────────────────────────────────────

class FeatureTier(IntEnum):
    FREE      = 0
    PREMIUM   = 1
    EXECUTIVE = 2


FEATURE_TIER_LEVELS: Dict[str, FeatureTier] = {
    "free":      FeatureTier.FREE,
    "premium":   FeatureTier.PREMIUM,
    "executive": FeatureTier.EXECUTIVE,
}

# Sage AI depth tier
SageTier = Literal["basic", "advanced"]
SAGE_TIER_RANK: Dict[str, int] = {"basic": 0, "advanced": 1}

# ── Permission catalogue ────────────────────────────────────────────────────────
# Every discrete capability the system can grant or deny.
# Naming convention: domain.action

class Permission:
    # ── Authentication & account
    AUTH_REGISTER        = "auth.register"
    AUTH_LOGIN           = "auth.login"
    AUTH_SELF_READ       = "auth.self.read"
    AUTH_SELF_EDIT       = "auth.self.edit"
    AUTH_SELF_DELETE     = "auth.self.delete"
    AUTH_CHANGE_PASSWORD = "auth.change_password"
    AUTH_SESSIONS_READ   = "auth.sessions.read"
    AUTH_SESSIONS_REVOKE = "auth.sessions.revoke"
    AUTH_RECOVERY        = "auth.recovery"

    # ── Learning modules
    MODULES_READ         = "modules.read"
    MODULES_PROGRESS     = "modules.progress"
    MODULES_QUIZ         = "modules.quiz"

    # ── Labs
    LABS_READ            = "labs.read"
    LABS_SUBMIT          = "labs.submit"
    LABS_REVIEW          = "labs.review"        # instructor+
    LABS_AI_FEEDBACK     = "labs.ai_feedback"   # premium

    # ── Credentials & portfolio
    CREDENTIALS_READ     = "credentials.read"
    CREDENTIALS_VERIFY   = "credentials.verify"
    PORTFOLIO_READ       = "portfolio.read"
    PORTFOLIO_WRITE      = "portfolio.write"

    # ── M.O.R.E. community (FREE tier allowed)
    COMMUNITY_READ       = "community.read"
    COMMUNITY_POST       = "community.post"
    COMMUNITY_NEED       = "community.need"
    COMMUNITY_CHAT       = "community.chat"
    COMMUNITY_FLAG       = "community.flag"
    COMMUNITY_MODERATE   = "community.moderate"  # admin+

    # ── AI — gated by feature tier
    AI_CHAT              = "ai.chat"             # premium
    AI_ORCHESTRATOR      = "ai.orchestrator"     # premium
    AI_SCHOLAR           = "ai.scholar"          # premium
    AI_HELPER            = "ai.helper"           # FREE (public helper endpoint)
    AI_DIRECTOR          = "ai.director"         # admin+
    AI_REVENUE_DIRECTOR  = "ai.revenue_director" # admin+
    AI_SAGE_CREATE       = "ai.sage.create"      # admin+
    AI_CIPHER            = "ai.cipher"           # admin+
    AI_ORACLE            = "ai.oracle"           # admin+
    AI_AMBASSADOR        = "ai.ambassador"       # admin+
    AI_ARCHITECT         = "ai.architect"        # admin+
    AI_MEMORY_READ       = "ai.memory.read"      # admin+
    AI_MEMORY_WRITE      = "ai.memory.write"     # executive_admin

    # ── TTS / Voice
    TTS_SAGE             = "tts.sage"            # premium
    TTS_DIRECTOR         = "tts.director"        # admin+
    TTS_CIPHER           = "tts.cipher"          # admin+
    TTS_ELEVENLABS       = "tts.elevenlabs"      # executive_admin

    # ── Legal tools (PREMIUM-ONLY, consent required)
    LEGAL_GUIDE_READ     = "legal.guide.read"    # premium + consent
    LEGAL_GUIDE_SUBMIT   = "legal.guide.submit"  # premium + consent

    # ── Payments
    PAYMENTS_READ        = "payments.read"
    PAYMENTS_CHECKOUT    = "payments.checkout"
    PAYMENTS_PORTAL      = "payments.portal"
    PAYMENTS_WEBHOOK     = "payments.webhook"    # system (no auth)

    # ── Analytics
    ANALYTICS_SELF       = "analytics.self"
    ANALYTICS_PLATFORM   = "analytics.platform"  # admin+

    # ── Notifications
    NOTIFICATIONS_READ   = "notifications.read"
    NOTIFICATIONS_MARK   = "notifications.mark"

    # ── Attendance & compliance
    ATTENDANCE_SELF      = "attendance.self"
    ATTENDANCE_ROSTER    = "attendance.roster"   # instructor+
    COMPLIANCE_READ      = "compliance.read"
    COMPLIANCE_QUIZ      = "compliance.quiz"

    # ── Incidents
    INCIDENTS_READ       = "incidents.read"      # instructor+
    INCIDENTS_CREATE     = "incidents.create"
    INCIDENTS_RESOLVE    = "incidents.resolve"   # instructor+

    # ── Admin (admin+)
    ADMIN_USERS_READ     = "admin.users.read"
    ADMIN_USERS_WRITE    = "admin.users.write"
    ADMIN_USERS_ROLE     = "admin.users.role"
    ADMIN_USERS_TIER     = "admin.users.tier"
    ADMIN_USERS_DELETE   = "admin.users.delete"
    ADMIN_PLATFORM       = "admin.platform"
    ADMIN_AUDIT_READ     = "admin.audit.read"
    ADMIN_PRICES         = "admin.prices"
    ADMIN_DISCOUNTS      = "admin.discounts"
    ADMIN_PAYMENTS_LIST  = "admin.payments.list"
    ADMIN_BROADCAST      = "admin.broadcast"
    ADMIN_FLAGS          = "admin.flags"
    ADMIN_MFA_CONFIG     = "admin.mfa.config"
    ADMIN_IP_WHITELIST   = "admin.ip_whitelist"
    ADMIN_RBAC_MATRIX    = "admin.rbac.matrix"
    ADMIN_GATEWAY        = "admin.gateway"
    ADMIN_AI_COSTS       = "admin.ai_costs"
    ADMIN_SAGE_AUDIT     = "admin.sage.audit"
    ADMIN_SAGE_CAP       = "admin.sage.cap"
    ADMIN_SITES          = "admin.sites"
    ADMIN_COHORTS        = "admin.cohorts"
    ADMIN_BULK_USERS     = "admin.bulk_users"

    # ── Supervisor (admin+)
    SUPERVISOR_DASHBOARD = "supervisor.dashboard"
    SUPERVISOR_CONTENT   = "supervisor.content"
    SUPERVISOR_BACKUP    = "supervisor.backup"
    SUPERVISOR_SAGE      = "supervisor.sage"
    SUPERVISOR_SYSTEM    = "supervisor.system"

    # ── Auditor (admin+)
    AUDITOR_READ         = "auditor.read"
    AUDITOR_WRITE        = "auditor.write"

    # ── Executive (executive_admin only)
    EXEC_DASHBOARD       = "exec.dashboard"
    EXEC_SCOUT           = "exec.scout"
    EXEC_AUDIO           = "exec.audio"
    EXEC_MERCH           = "exec.merch"
    EXEC_PERSONAS        = "exec.personas"
    EXEC_PRODUCTS        = "exec.products"
    EXEC_STAFF_MEETING   = "exec.staff_meeting"
    EXEC_PIPELINE        = "exec.pipeline"
    EXEC_ANALYTICS       = "exec.analytics"
    EXEC_OVERRIDE        = "exec.override"      # break-glass

    # ── Revenue / API-as-a-Service
    REVENUE_API_KEYS     = "revenue.api_keys"
    REVENUE_COURSES      = "revenue.courses"
    REVENUE_WORKSPACE    = "revenue.workspace"
    REVENUE_VERIFY       = "revenue.verify"
    REVENUE_COMPLIANCE   = "revenue.compliance"
    REVENUE_RESUME       = "revenue.resume"

    # ── Adaptive
    ADAPTIVE_READ        = "adaptive.read"


# ── Role → Permission mapping ───────────────────────────────────────────────────
# Each role gets the listed permissions PLUS all permissions from roles below it.

_GUEST_PERMISSIONS: FrozenSet[str] = frozenset({
    Permission.AUTH_REGISTER,
    Permission.AUTH_LOGIN,
    Permission.AI_HELPER,          # public helper is free
    Permission.COMMUNITY_READ,     # read-only M.O.R.E.
    Permission.CREDENTIALS_VERIFY, # public credential verify
    Permission.PAYMENTS_WEBHOOK,   # Stripe webhook (system)
})

_STUDENT_PERMISSIONS: FrozenSet[str] = frozenset({
    Permission.AUTH_SELF_READ,
    Permission.AUTH_SELF_EDIT,
    Permission.AUTH_SELF_DELETE,
    Permission.AUTH_CHANGE_PASSWORD,
    Permission.AUTH_SESSIONS_READ,
    Permission.AUTH_SESSIONS_REVOKE,
    Permission.AUTH_RECOVERY,
    Permission.MODULES_READ,
    Permission.MODULES_PROGRESS,
    Permission.MODULES_QUIZ,
    Permission.LABS_READ,
    Permission.LABS_SUBMIT,
    Permission.CREDENTIALS_READ,
    Permission.PORTFOLIO_READ,
    Permission.PORTFOLIO_WRITE,
    Permission.COMMUNITY_POST,
    Permission.COMMUNITY_NEED,
    Permission.COMMUNITY_CHAT,
    Permission.COMMUNITY_FLAG,
    Permission.NOTIFICATIONS_READ,
    Permission.NOTIFICATIONS_MARK,
    Permission.ATTENDANCE_SELF,
    Permission.COMPLIANCE_READ,
    Permission.COMPLIANCE_QUIZ,
    Permission.INCIDENTS_CREATE,
    Permission.PAYMENTS_READ,
    Permission.PAYMENTS_CHECKOUT,
    Permission.PAYMENTS_PORTAL,
    Permission.ANALYTICS_SELF,
    Permission.REVENUE_API_KEYS,
    Permission.REVENUE_COURSES,
    Permission.REVENUE_WORKSPACE,
    Permission.REVENUE_RESUME,
    Permission.ADAPTIVE_READ,
    # Premium-gated: AI_CHAT, TTS_SAGE, LEGAL_GUIDE_* added by tier check
})

_INSTRUCTOR_PERMISSIONS: FrozenSet[str] = frozenset({
    Permission.LABS_REVIEW,
    Permission.LABS_AI_FEEDBACK,
    Permission.ATTENDANCE_ROSTER,
    Permission.INCIDENTS_READ,
    Permission.INCIDENTS_RESOLVE,
    Permission.REVENUE_VERIFY,
    Permission.REVENUE_COMPLIANCE,
    Permission.ADMIN_COHORTS,      # instructors can see cohorts
})

_ADMIN_PERMISSIONS: FrozenSet[str] = frozenset({
    Permission.AI_DIRECTOR,
    Permission.AI_REVENUE_DIRECTOR,
    Permission.AI_SAGE_CREATE,
    Permission.AI_CIPHER,
    Permission.AI_ORACLE,
    Permission.AI_AMBASSADOR,
    Permission.AI_ARCHITECT,
    Permission.AI_MEMORY_READ,
    Permission.TTS_DIRECTOR,
    Permission.TTS_CIPHER,
    Permission.ADMIN_USERS_READ,
    Permission.ADMIN_USERS_WRITE,
    Permission.ADMIN_USERS_ROLE,
    Permission.ADMIN_USERS_TIER,
    Permission.ADMIN_USERS_DELETE,
    Permission.ADMIN_PLATFORM,
    Permission.ADMIN_AUDIT_READ,
    Permission.ADMIN_PRICES,
    Permission.ADMIN_DISCOUNTS,
    Permission.ADMIN_PAYMENTS_LIST,
    Permission.ADMIN_BROADCAST,
    Permission.ADMIN_FLAGS,
    Permission.ADMIN_MFA_CONFIG,
    Permission.ADMIN_IP_WHITELIST,
    Permission.ADMIN_RBAC_MATRIX,
    Permission.ADMIN_GATEWAY,
    Permission.ADMIN_AI_COSTS,
    Permission.ADMIN_SAGE_AUDIT,
    Permission.ADMIN_SAGE_CAP,
    Permission.ADMIN_SITES,
    Permission.ADMIN_BULK_USERS,
    Permission.SUPERVISOR_DASHBOARD,
    Permission.SUPERVISOR_CONTENT,
    Permission.SUPERVISOR_BACKUP,
    Permission.SUPERVISOR_SAGE,
    Permission.SUPERVISOR_SYSTEM,
    Permission.AUDITOR_READ,
    Permission.AUDITOR_WRITE,
    Permission.ANALYTICS_PLATFORM,
    Permission.EXEC_PIPELINE,      # admins can run pipeline
    Permission.COMMUNITY_MODERATE,
})

_EXECUTIVE_PERMISSIONS: FrozenSet[str] = frozenset({
    Permission.AI_MEMORY_WRITE,
    Permission.TTS_ELEVENLABS,
    Permission.EXEC_DASHBOARD,
    Permission.EXEC_SCOUT,
    Permission.EXEC_AUDIO,
    Permission.EXEC_MERCH,
    Permission.EXEC_PERSONAS,
    Permission.EXEC_PRODUCTS,
    Permission.EXEC_STAFF_MEETING,
    Permission.EXEC_ANALYTICS,
    Permission.EXEC_OVERRIDE,
    Permission.ADMIN_RBAC_MATRIX,  # can also reset matrix
})


def _build_cumulative(
    *layers: FrozenSet[str],
) -> FrozenSet[str]:
    result: Set[str] = set()
    for layer in layers:
        result |= layer
    return frozenset(result)


# Cumulative permission sets (each role includes all roles below it)
ROLE_PERMISSIONS: Dict[str, FrozenSet[str]] = {
    "guest": _GUEST_PERMISSIONS,
    "student": _build_cumulative(
        _GUEST_PERMISSIONS,
        _STUDENT_PERMISSIONS,
    ),
    "instructor": _build_cumulative(
        _GUEST_PERMISSIONS,
        _STUDENT_PERMISSIONS,
        _INSTRUCTOR_PERMISSIONS,
    ),
    "admin": _build_cumulative(
        _GUEST_PERMISSIONS,
        _STUDENT_PERMISSIONS,
        _INSTRUCTOR_PERMISSIONS,
        _ADMIN_PERMISSIONS,
    ),
    "executive_admin": _build_cumulative(
        _GUEST_PERMISSIONS,
        _STUDENT_PERMISSIONS,
        _INSTRUCTOR_PERMISSIONS,
        _ADMIN_PERMISSIONS,
        _EXECUTIVE_PERMISSIONS,
    ),
}

# ── Feature tier → Permission additions ────────────────────────────────────────
# These permissions are ADDED on top of role permissions when the user has
# the required feature tier.

TIER_PERMISSION_GRANTS: Dict[str, FrozenSet[str]] = {
    "free": frozenset({
        # No AI, no legal tools — explicitly empty for documentation clarity
    }),
    "premium": frozenset({
        Permission.AI_CHAT,
        Permission.AI_ORCHESTRATOR,
        Permission.AI_SCHOLAR,
        Permission.TTS_SAGE,
        Permission.LEGAL_GUIDE_READ,
        Permission.LEGAL_GUIDE_SUBMIT,
        Permission.LABS_AI_FEEDBACK,
    }),
    "executive": frozenset({
        # Executive tier has everything premium has, plus system controls
        Permission.AI_CHAT,
        Permission.AI_ORCHESTRATOR,
        Permission.AI_SCHOLAR,
        Permission.TTS_SAGE,
        Permission.LEGAL_GUIDE_READ,
        Permission.LEGAL_GUIDE_SUBMIT,
        Permission.LABS_AI_FEEDBACK,
        Permission.TTS_ELEVENLABS,
    }),
}

# ── Route → required (role, tier, permissions) matrix ─────────────────────────
# Format: route_pattern → {"min_role": str, "min_tier": str, "permissions": set,
#                          "require_consent": bool}

RoutePolicy = Dict[str, object]

ROUTE_POLICIES: Dict[str, RoutePolicy] = {
    # ── Public / Guest
    "POST /auth/register":              {"min_role": "guest",           "min_tier": "free"},
    "POST /auth/login":                 {"min_role": "guest",           "min_tier": "free"},
    "POST /auth/forgot-password":       {"min_role": "guest",           "min_tier": "free"},
    "POST /auth/reset-password":        {"min_role": "guest",           "min_tier": "free"},
    "POST /auth/recovery-status":       {"min_role": "guest",           "min_tier": "free"},
    "POST /ai/helper":                  {"min_role": "guest",           "min_tier": "free"},
    "POST /consent/cookie":             {"min_role": "guest",           "min_tier": "free"},
    "POST /revenue/verify-credential":  {"min_role": "guest",           "min_tier": "free"},
    "GET /credentials/{key}/manifest.json": {"min_role": "guest",      "min_tier": "free"},
    "GET /credentials/assertion/{id}.json": {"min_role": "guest",      "min_tier": "free"},
    "GET /verify/{code}":               {"min_role": "guest",           "min_tier": "free"},
    "GET /revenue/courses/public":      {"min_role": "guest",           "min_tier": "free"},
    "GET /revenue/api-keys/tiers":      {"min_role": "guest",           "min_tier": "free"},
    "POST /payments/webhook":           {"min_role": "guest",           "min_tier": "free"},
    "GET /":                            {"min_role": "guest",           "min_tier": "free"},
    "GET /health":                      {"min_role": "guest",           "min_tier": "free"},
    "GET /version":                     {"min_role": "guest",           "min_tier": "free"},
    "GET /community/read":              {"min_role": "guest",           "min_tier": "free"},
    "GET /prices/public":               {"min_role": "guest",           "min_tier": "free"},
    "POST /bug-report":                 {"min_role": "guest",           "min_tier": "free"},

    # ── Student (free tier)
    "GET /auth/me":                     {"min_role": "student",         "min_tier": "free"},
    "PATCH /auth/me":                   {"min_role": "student",         "min_tier": "free"},
    "DELETE /auth/account":             {"min_role": "student",         "min_tier": "free"},
    "GET /auth/account/export":         {"min_role": "student",         "min_tier": "free"},
    "POST /auth/change-password":       {"min_role": "student",         "min_tier": "free"},
    "GET /auth/sessions":               {"min_role": "student",         "min_tier": "free"},
    "DELETE /auth/sessions/{id}":       {"min_role": "student",         "min_tier": "free"},
    "DELETE /auth/sessions":            {"min_role": "student",         "min_tier": "free"},
    "GET /modules":                     {"min_role": "student",         "min_tier": "free"},
    "GET /modules/{slug}":              {"min_role": "student",         "min_tier": "free"},
    "GET /progress/me":                 {"min_role": "student",         "min_tier": "free"},
    "POST /progress/start":             {"min_role": "student",         "min_tier": "free"},
    "POST /progress/quiz":              {"min_role": "student",         "min_tier": "free"},
    "GET /labs":                        {"min_role": "student",         "min_tier": "free"},
    "GET /labs/{slug}":                 {"min_role": "student",         "min_tier": "free"},
    "POST /labs/{slug}/submit":         {"min_role": "student",         "min_tier": "free"},
    "GET /labs/submissions/me":         {"min_role": "student",         "min_tier": "free"},
    "GET /credentials/me":              {"min_role": "student",         "min_tier": "free"},
    "GET /certificates/me":             {"min_role": "student",         "min_tier": "free"},
    "GET /portfolio/me":                {"min_role": "student",         "min_tier": "free"},
    "POST /portfolio/publish":          {"min_role": "student",         "min_tier": "free"},
    "GET /portfolio/public/{slug}":     {"min_role": "student",         "min_tier": "free"},
    "GET /xp/me":                       {"min_role": "student",         "min_tier": "free"},
    "GET /xp/leaderboard":              {"min_role": "student",         "min_tier": "free"},
    "GET /more/posts":                  {"min_role": "student",         "min_tier": "free"},
    "POST /more/post":                  {"min_role": "student",         "min_tier": "free"},
    "POST /more/need":                  {"min_role": "student",         "min_tier": "free"},
    "GET /more/needs":                  {"min_role": "student",         "min_tier": "free"},
    "POST /more/chat/send":             {"min_role": "student",         "min_tier": "free"},
    "GET /more/chat/{id}":              {"min_role": "student",         "min_tier": "free"},
    "POST /more/flag":                  {"min_role": "student",         "min_tier": "free"},
    "GET /notifications/me":            {"min_role": "student",         "min_tier": "free"},
    "POST /notifications/{id}/read":    {"min_role": "student",         "min_tier": "free"},
    "POST /notifications/read-all":     {"min_role": "student",         "min_tier": "free"},
    "POST /attendance":                 {"min_role": "student",         "min_tier": "free"},
    "GET /attendance/me":               {"min_role": "student",         "min_tier": "free"},
    "GET /compliance":                  {"min_role": "student",         "min_tier": "free"},
    "GET /compliance/{slug}":           {"min_role": "student",         "min_tier": "free"},
    "POST /compliance/{slug}/quiz":     {"min_role": "student",         "min_tier": "free"},
    "POST /incidents":                  {"min_role": "student",         "min_tier": "free"},
    "GET /payments/products":           {"min_role": "student",         "min_tier": "free"},
    "POST /payments/checkout":          {"min_role": "student",         "min_tier": "free"},
    "GET /payments/portal":             {"min_role": "student",         "min_tier": "free"},
    "GET /payments/history":            {"min_role": "student",         "min_tier": "free"},
    "GET /adaptive/me":                 {"min_role": "student",         "min_tier": "free"},
    "GET /revenue/api-keys":            {"min_role": "student",         "min_tier": "free"},
    "POST /revenue/api-keys":           {"min_role": "student",         "min_tier": "free"},
    "DELETE /revenue/api-keys/{hash}":  {"min_role": "student",         "min_tier": "free"},
    "GET /revenue/api-keys/stats":      {"min_role": "student",         "min_tier": "free"},
    "GET /revenue/resume/preview":      {"min_role": "student",         "min_tier": "free"},
    "POST /revenue/courses/license":    {"min_role": "student",         "min_tier": "free"},
    "GET /revenue/courses/my-licenses": {"min_role": "student",         "min_tier": "free"},

    # ── AI consent (required before premium AI)
    "POST /ai/consent":                 {"min_role": "student",         "min_tier": "free"},
    "GET /ai/consent/health":           {"min_role": "guest",           "min_tier": "free"},
    "POST /ai/sage/resolve_mode":       {"min_role": "student",         "min_tier": "free"},
    "GET /ai/sage/integrity":           {"min_role": "student",         "min_tier": "free"},
    "GET /ai/history/{session_id}":     {"min_role": "student",         "min_tier": "free"},

    # ── PREMIUM-ONLY routes
    "POST /ai/chat":                    {"min_role": "student",         "min_tier": "premium", "permissions": {Permission.AI_CHAT}},
    "POST /ai/orchestrator":            {"min_role": "student",         "min_tier": "premium", "permissions": {Permission.AI_ORCHESTRATOR}},
    "POST /ai/scholar":                 {"min_role": "student",         "min_tier": "premium", "permissions": {Permission.AI_SCHOLAR}},
    "POST /ai/sage/tts":                {"min_role": "student",         "min_tier": "premium", "permissions": {Permission.TTS_SAGE}},
    "POST /ai/sage/elevenlabs/tts":     {"min_role": "student",         "min_tier": "premium", "permissions": {Permission.TTS_SAGE}},
    "GET /pricing":                     {"min_role": "student",         "min_tier": "free"},
    "GET /ai/orchestrator/integrity":   {"min_role": "student",         "min_tier": "premium"},
    "GET /ai/scholar/integrity":        {"min_role": "admin",           "min_tier": "premium"},
    "POST /help/guide":                 {"min_role": "student",         "min_tier": "premium"},

    # ── LEGAL TOOLS (PREMIUM + consent required)
    # Both legal guide features require premium tier AND explicit consent
    "POST /legal/guide":                {"min_role": "student",         "min_tier": "premium", "require_consent": True, "permissions": {Permission.LEGAL_GUIDE_SUBMIT}},
    "GET /legal/guide":                 {"min_role": "student",         "min_tier": "premium", "require_consent": True, "permissions": {Permission.LEGAL_GUIDE_READ}},

    # ── Instructor+
    "GET /attendance/roster":           {"min_role": "instructor",      "min_tier": "free"},
    "GET /incidents":                   {"min_role": "instructor",      "min_tier": "free"},
    "POST /incidents/{id}/resolve":     {"min_role": "instructor",      "min_tier": "free"},
    "GET /instructor/submissions":      {"min_role": "instructor",      "min_tier": "free"},
    "POST /instructor/submissions/{id}/review": {"min_role": "instructor", "min_tier": "free"},
    "POST /labs/submissions/{id}/ai-feedback": {"min_role": "instructor", "min_tier": "premium"},
    "GET /instructor/lab-report":       {"min_role": "instructor",      "min_tier": "free"},
    "GET /competencies":                {"min_role": "instructor",      "min_tier": "free"},
    "GET /roster":                      {"min_role": "instructor",      "min_tier": "free"},
    "GET /revenue/employer/verify-batch": {"min_role": "instructor",   "min_tier": "free"},
    "GET /revenue/employer/compliance": {"min_role": "instructor",      "min_tier": "free"},
    "GET /portfolio/export.pdf":        {"min_role": "instructor",      "min_tier": "free"},
    "GET /certificates/{slug}.pdf":     {"min_role": "instructor",      "min_tier": "free"},
    "GET /credentials/transcript.pdf":  {"min_role": "instructor",      "min_tier": "free"},

    # ── Admin+
    "GET /admin/users":                 {"min_role": "admin",           "min_tier": "free"},
    "POST /admin/users":                {"min_role": "admin",           "min_tier": "free"},
    "GET /admin/users/{uid}":           {"min_role": "admin",           "min_tier": "free"},
    "PATCH /admin/users/{uid}":         {"min_role": "admin",           "min_tier": "free"},
    "DELETE /admin/users/{uid}":        {"min_role": "admin",           "min_tier": "free"},
    "PATCH /admin/users/{uid}/role":    {"min_role": "admin",           "min_tier": "free"},
    "PATCH /admin/users/{uid}/tier":    {"min_role": "admin",           "min_tier": "free"},
    "GET /admin/audit":                 {"min_role": "admin",           "min_tier": "free"},
    "GET /admin/audit/export":          {"min_role": "admin",           "min_tier": "free"},
    "GET /admin/prices":                {"min_role": "admin",           "min_tier": "free"},
    "POST /admin/prices":               {"min_role": "admin",           "min_tier": "free"},
    "PATCH /admin/prices/{id}":         {"min_role": "admin",           "min_tier": "free"},
    "DELETE /admin/prices/{id}":        {"min_role": "admin",           "min_tier": "free"},
    "GET /admin/ai-costs":              {"min_role": "admin",           "min_tier": "free"},
    "GET /admin/platform/flags":        {"min_role": "admin",           "min_tier": "free"},
    "PATCH /admin/platform/flags":      {"min_role": "admin",           "min_tier": "free"},
    "GET /admin/rbac/matrix":           {"min_role": "admin",           "min_tier": "free"},
    "PATCH /admin/rbac/matrix":         {"min_role": "admin",           "min_tier": "free"},
    "GET /admin/mfa/config":            {"min_role": "admin",           "min_tier": "free"},
    "PATCH /admin/mfa/config":          {"min_role": "admin",           "min_tier": "free"},
    "GET /admin/access/ipwhitelist":    {"min_role": "admin",           "min_tier": "free"},
    "POST /admin/access/ipwhitelist":   {"min_role": "admin",           "min_tier": "free"},
    "DELETE /admin/access/ipwhitelist/{id}": {"min_role": "admin",     "min_tier": "free"},
    "POST /more/admin/queue/{t}/{id}/approve": {"min_role": "admin",   "min_tier": "free"},
    "POST /more/admin/queue/{t}/{id}/reject":  {"min_role": "admin",   "min_tier": "free"},
    "GET /more/admin/flags":            {"min_role": "admin",           "min_tier": "free"},
    "GET /more/admin/moderation-log":   {"min_role": "admin",           "min_tier": "free"},
    "GET /more/admin/moderation-stats": {"min_role": "admin",           "min_tier": "free"},
    "GET /analytics/platform":          {"min_role": "admin",           "min_tier": "free"},
    "POST /admin/broadcast":            {"min_role": "admin",           "min_tier": "free"},
    "POST /ai/director":                {"min_role": "admin",           "min_tier": "free"},
    "POST /ai/director/upload":         {"min_role": "admin",           "min_tier": "free"},
    "GET /ai/director/greeting":        {"min_role": "student",         "min_tier": "free"},
    "GET /ai/director/pulse":           {"min_role": "admin",           "min_tier": "free"},
    "POST /ai/director/tts":            {"min_role": "admin",           "min_tier": "free"},
    "POST /ai/revenue-director":        {"min_role": "admin",           "min_tier": "free"},
    "POST /ai/revenue-director/tts":    {"min_role": "admin",           "min_tier": "free"},
    "POST /ai/sage/create":             {"min_role": "admin",           "min_tier": "free"},
    "POST /ai/ambassador":              {"min_role": "admin",           "min_tier": "free"},
    "POST /ai/architect":               {"min_role": "admin",           "min_tier": "free"},
    "POST /ai/cipher":                  {"min_role": "admin",           "min_tier": "free"},
    "POST /ai/oracle":                  {"min_role": "admin",           "min_tier": "free"},
    "GET /ai/memory/{persona}":         {"min_role": "admin",           "min_tier": "free"},
    "GET /ai/memory":                   {"min_role": "executive_admin", "min_tier": "free"},
    "POST /ai/memory/policy":           {"min_role": "executive_admin", "min_tier": "free"},
    "DELETE /ai/memory/policy/{p}/{id}": {"min_role": "executive_admin","min_tier": "free"},
    "POST /ai/cipher/tts":              {"min_role": "admin",           "min_tier": "free"},
    "GET /supervisor/dashboard":        {"min_role": "admin",           "min_tier": "free"},
    "GET /supervisor/escalations":      {"min_role": "admin",           "min_tier": "free"},
    "POST /supervisor/escalations/{id}/resolve": {"min_role": "admin", "min_tier": "free"},
    "POST /supervisor/escalations":     {"min_role": "admin",           "min_tier": "free"},
    "GET /supervisor/greeter/config":   {"min_role": "admin",           "min_tier": "free"},
    "PATCH /supervisor/greeter/config": {"min_role": "admin",           "min_tier": "free"},
    "GET /supervisor/visitor-flow":     {"min_role": "admin",           "min_tier": "free"},
    "PATCH /supervisor/visitor-flow":   {"min_role": "admin",           "min_tier": "free"},
    "POST /supervisor/content/{t}/{id}/approve": {"min_role": "admin", "min_tier": "free"},
    "POST /supervisor/content/{t}/{id}/reject":  {"min_role": "admin", "min_tier": "free"},
    "GET /supervisor/backup/status":    {"min_role": "admin",           "min_tier": "free"},
    "POST /supervisor/backup/switch-provider": {"min_role": "admin",   "min_tier": "free"},
    "POST /supervisor/backup/reset-gateway": {"min_role": "admin",     "min_tier": "free"},
    "GET /supervisor/backup/free-matrix": {"min_role": "admin",        "min_tier": "free"},
    "POST /supervisor/backup/emergency-broadcast": {"min_role": "admin","min_tier": "free"},
    "GET /supervisor/sage/sessions":    {"min_role": "admin",           "min_tier": "free"},
    "POST /supervisor/sage/sessions/{id}/flag": {"min_role": "admin",  "min_tier": "free"},
    "GET /supervisor/system/continuity-check": {"min_role": "admin",   "min_tier": "free"},
    "GET /auditor/summary":             {"min_role": "admin",           "min_tier": "free"},
    "GET /auditor/ledger":              {"min_role": "admin",           "min_tier": "free"},
    "POST /auditor/ledger":             {"min_role": "admin",           "min_tier": "free"},
    "PATCH /auditor/ledger/{id}":       {"min_role": "admin",           "min_tier": "free"},
    "GET /auditor/report":              {"min_role": "admin",           "min_tier": "free"},
    "GET /auditor/debt":                {"min_role": "admin",           "min_tier": "free"},
    "GET /auditor/risks":               {"min_role": "admin",           "min_tier": "free"},
    "GET /admin/users/{uid}/sessions":  {"min_role": "executive_admin", "min_tier": "free"},
    "DELETE /admin/users/{uid}/sessions": {"min_role": "executive_admin","min_tier": "free"},
    "POST /admin/users/bulk":           {"min_role": "admin",           "min_tier": "free"},
    "GET /admin/users/{uid}/audit":     {"min_role": "admin",           "min_tier": "free"},
    "POST /admin/users/{uid}/elevated-role": {"min_role": "executive_admin","min_tier": "free"},
    "GET /admin/users/{uid}/elevated-role":  {"min_role": "admin",     "min_tier": "free"},
    "DELETE /admin/users/{uid}/elevated-role": {"min_role": "executive_admin","min_tier": "free"},
    "PATCH /admin/users/{uid}/sage-tier": {"min_role": "admin",        "min_tier": "free"},
    "POST /exec/pipeline/process":      {"min_role": "admin",           "min_tier": "free"},
    "POST /exec/pipeline/process-batch": {"min_role": "admin",         "min_tier": "free"},
    "GET /revenue/sovereign/workspaces": {"min_role": "admin",          "min_tier": "free"},
    "POST /revenue/sovereign/workspace": {"min_role": "admin",          "min_tier": "free"},

    # ── Executive only
    "GET /exec/dashboard":              {"min_role": "executive_admin", "min_tier": "free"},
    "POST /exec/scout/run":             {"min_role": "executive_admin", "min_tier": "free"},
    "GET /exec/scout/leads":            {"min_role": "executive_admin", "min_tier": "free"},
    "GET /exec/scout/status":           {"min_role": "executive_admin", "min_tier": "free"},
    "POST /exec/scout/match-all":       {"min_role": "executive_admin", "min_tier": "free"},
    "POST /exec/scout/craft-response":  {"min_role": "executive_admin", "min_tier": "free"},
    "POST /ai/cipher/generate-audio":   {"min_role": "executive_admin", "min_tier": "free"},
    "GET /exec/audio/{id}":             {"min_role": "student",         "min_tier": "free"},
    "GET /exec/audio":                  {"min_role": "executive_admin", "min_tier": "free"},
    "POST /exec/merch/create":          {"min_role": "executive_admin", "min_tier": "free"},
    "GET /exec/merch":                  {"min_role": "executive_admin", "min_tier": "free"},
    "GET /exec/analytics":              {"min_role": "executive_admin", "min_tier": "free"},
    "GET /exec/personas":               {"min_role": "executive_admin", "min_tier": "free"},
    "POST /exec/personas/{name}/evolve": {"min_role": "executive_admin","min_tier": "free"},
    "POST /exec/personas/{name}/activate": {"min_role": "executive_admin","min_tier": "free"},
    "POST /exec/personas/{name}/deactivate": {"min_role": "executive_admin","min_tier": "free"},
    "POST /exec/checkout/conversion":   {"min_role": "executive_admin", "min_tier": "free"},
    "GET /exec/products":               {"min_role": "executive_admin", "min_tier": "free"},
    "POST /exec/products/create":       {"min_role": "executive_admin", "min_tier": "free"},
    "POST /exec/products/publish-all":  {"min_role": "executive_admin", "min_tier": "free"},
    "GET /exec/staff-meetings":         {"min_role": "executive_admin", "min_tier": "free"},
    "POST /exec/staff-meeting":         {"min_role": "executive_admin", "min_tier": "free"},
    "POST /exec/panel/override":        {"min_role": "executive_admin", "min_tier": "free"},
    "GET /exec/system":                 {"min_role": "executive_admin", "min_tier": "free"},
}


# ── Public check functions ─────────────────────────────────────────────────────

def has_permission(role: str, permission: str) -> bool:
    """Return True if the given role has the specified permission."""
    return permission in ROLE_PERMISSIONS.get(role, frozenset())


def role_meets_minimum(user_role: str, min_role: str) -> bool:
    """Return True if user_role is >= min_role in the hierarchy."""
    return ROLE_RANK.get(user_role, 0) >= ROLE_RANK.get(min_role, 0)


def tier_meets_minimum(user_tier: str, min_tier: str) -> bool:
    """Return True if user_tier is >= min_tier in the feature hierarchy."""
    return FEATURE_TIER_LEVELS.get(user_tier, FeatureTier.FREE) >= FEATURE_TIER_LEVELS.get(min_tier, FeatureTier.FREE)


def effective_permissions(role: str, feature_tier: str) -> FrozenSet[str]:
    """Return the full set of permissions for a role + feature tier combination."""
    base = ROLE_PERMISSIONS.get(role, frozenset())
    extra = TIER_PERMISSION_GRANTS.get(feature_tier, frozenset())
    return base | extra


def get_route_policy(method: str, path: str) -> Optional[RoutePolicy]:
    """Look up the policy for a method+path combination."""
    key = f"{method.upper()} {path}"
    return ROUTE_POLICIES.get(key)
