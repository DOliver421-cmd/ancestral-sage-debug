"""
prompt_guard.py - Director 4.0 AI Tamper Protection System
============================================================
WAI-Institute / M.O.R.E. Help Center
Author: Supervisory Follow Team | Commissioned by: NAM Oshun / Delon Oliver

PURPOSE
-------
Protect every AI endpoint against:
  1. Prompt Injection Attacks  — user messages designed to override system prompts
  2. Jailbreak Attempts        — pattern-based identity and constraint removal
  3. Persona Spoofing          — claiming to be another AI or overriding identity
  4. Role Escalation via Text  — injecting role-grant commands into messages
  5. System Prompt Exfiltration — attempting to read or leak internal prompts
  6. AI-to-AI Manipulation     — automated AI agents trying to exploit this system
  7. Prompt Integrity Drift    — unauthorized modification of any persona prompt file

DEPLOYMENT
----------
  from ai.prompt_guard import PromptGuard, check_message_safe, verify_all_prompt_integrity

  # At server startup:
  verify_all_prompt_integrity()   # logs warnings on drift; raises on CRITICAL drift

  # On every AI request (call BEFORE passing to the LLM):
  result = check_message_safe(user_message, user_role, endpoint)
  if not result["safe"]:
      raise HTTPException(400, result["reason"])
"""

import hashlib
import logging
import re
from typing import Dict, Optional

logger = logging.getLogger("lcewai.prompt_guard")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — PROMPT INTEGRITY REGISTRY
# Tracks SHA-256 hashes of all persona prompt files at startup.
# Any drift from the baseline is a tamper signal.
# ─────────────────────────────────────────────────────────────────────────────

# Baseline registry — populated at first call to verify_all_prompt_integrity()
# Key = prompt identifier, Value = SHA-256 hex at first verified load
_BASELINE: Dict[str, str] = {}
_BASELINE_LOCKED = False   # True after first lock — prevents runtime tampering of this registry

# All personas with hardcoded expected hashes (tamper-evident at startup)
_KNOWN_HASHES: Dict[str, Optional[str]] = {
    "ancestral_sage": None,       # from ancestral_sage_prompt.py
    "director": None,             # from director_prompt.py
    "assistant_director": None,   # from director_prompt.py
    "sovereign": None,            # from sovereign/sovereign_persona.py
    "more_department": None,      # from more_department_system.py (contains Finance Director)
    "prt": None,                  # from wai_institute/personas/prt.py
    "oliver_guardian": None,      # from prompts/oliver_guardian_prompt.py
    "orchestrator": None,
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _send_integrity_alert(failed_personas: list) -> None:
    """Fire an email to D. Oliver whenever any persona prompt hash fails."""
    try:
        import os, datetime
        names = ", ".join(failed_personas)
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        subject = f"[GOVERNANCE INTEGRITY] Prompt hash failure — {names}"
        body = (
            f"D. Oliver —\n\n"
            f"SITUATION\n"
            f"One or more AI persona prompts failed their SHA-256 integrity check at server startup. "
            f"This indicates the prompt file(s) may have been modified without authorization.\n\n"
            f"KEY FINDINGS\n"
            f"• Failed personas: {names}\n"
            f"• Detection time: {ts}\n"
            f"• Affected personas are operating in RESTRICTED mode until resolved.\n\n"
            f"THREAT LEVEL: HIGH\n"
            f"Risk factors: Unauthorized prompt modification could alter AI governance behavior, "
            f"remove safety overrides, or introduce adversarial instructions.\n\n"
            f"RECOMMENDED ACTIONS\n"
            f"1. IMMEDIATE (within 1h): Review git history for unauthorized changes to prompt files.\n"
            f"2. STABILIZATION (within 24h): If tampering confirmed, rotate Railway deployment and "
            f"restore prompt files from last known-good commit.\n"
            f"3. LONG-TERM: Investigate how the modification occurred and tighten repository access.\n\n"
            f"DECISION REQUIRED: YES\n"
            f"Confirm whether the change was authorized. If not, treat as an AI_TAMPER incident.\n\n"
            f"The Director | WAI-Institute | {ts}"
        )
        # Use the platform's email utility if available
        try:
            from ai.email_utils import send_platform_email  # type: ignore
            send_platform_email(
                to=os.getenv("EXEC_EMAIL", "morehelpcenter@gmail.com"),
                subject=subject,
                body=body,
            )
            logger.critical("PROMPT GUARD: Integrity alert email dispatched for: %s", names)
        except ImportError:
            # Fall back to logging — the Director will surface it on next login
            logger.critical(
                "PROMPT GUARD INTEGRITY ALERT (email unavailable): %s | %s",
                subject, body[:200]
            )
    except Exception as exc:
        logger.error("PROMPT GUARD: Failed to send integrity alert email: %s", exc)


def _load_prompt_texts() -> Dict[str, Optional[str]]:
    """Load all current persona prompt texts for integrity checking."""
    texts: Dict[str, Optional[str]] = {}
    try:
        from prompts.ancestral_sage_prompt import ANCESTRAL_SAGE_PROMPT
        texts["ancestral_sage"] = ANCESTRAL_SAGE_PROMPT
    except Exception as e:
        logger.error("PROMPT GUARD: failed to load ancestral_sage_prompt: %s", e)
        texts["ancestral_sage"] = None

    try:
        from prompts.director_prompt import DIRECTOR_PROMPT, ASSISTANT_DIRECTOR_PROMPT
        texts["director"] = DIRECTOR_PROMPT
        texts["assistant_director"] = ASSISTANT_DIRECTOR_PROMPT
    except Exception as e:
        logger.error("PROMPT GUARD: failed to load director_prompt: %s", e)
        texts["director"] = None
        texts["assistant_director"] = None

    try:
        from prompts.more_department_system import get_more_department_system
        texts["more_department"] = get_more_department_system()
    except Exception as e:
        logger.warning("PROMPT GUARD: more_department_system unavailable: %s", e)
        texts["more_department"] = None

    try:
        from sovereign.sovereign_persona import SOVEREIGN_PERSONA
        texts["sovereign"] = SOVEREIGN_PERSONA
    except Exception as e:
        logger.warning("PROMPT GUARD: sovereign_persona unavailable: %s", e)
        texts["sovereign"] = None

    try:
        from wai_institute.personas.prt import PRT_SYSTEM_PROMPT
        texts["prt"] = PRT_SYSTEM_PROMPT
    except Exception as e:
        logger.warning("PROMPT GUARD: prt unavailable: %s", e)
        texts["prt"] = None

    try:
        from prompts.oliver_guardian_prompt import OLIVER_GUARDIAN_PROMPT
        texts["oliver_guardian"] = OLIVER_GUARDIAN_PROMPT
    except Exception as e:
        logger.warning("PROMPT GUARD: oliver_guardian_prompt unavailable: %s", e)
        texts["oliver_guardian"] = None

    try:
        import prompts.orchestrator as _orch_mod
        import inspect
        texts["orchestrator"] = inspect.getsource(_orch_mod)
    except Exception as e:
        logger.warning("PROMPT GUARD: orchestrator source unavailable for integrity: %s", e)
        texts["orchestrator"] = None

    return texts


def verify_all_prompt_integrity(strict: bool = False) -> Dict[str, bool]:
    """
    Verify integrity of all persona prompt files.

    On first call: establishes the runtime baseline (enrolls current hashes).
    On subsequent calls: compares current hashes to the established baseline.

    Args:
        strict: if True, raises RuntimeError on any drift (use only in test mode).

    Returns:
        Dict mapping prompt name → True (ok) or False (drifted/unavailable)
    """
    global _BASELINE, _BASELINE_LOCKED

    # ── Hardcoded expected hashes — checked against the known-good baseline ──
    _HARDCODED_CHECKS: Dict[str, tuple] = {}

    try:
        from prompts.ancestral_sage_prompt import ANCESTRAL_SAGE_PROMPT, ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED
        _HARDCODED_CHECKS["ancestral_sage"] = (ANCESTRAL_SAGE_PROMPT, ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED)
    except Exception as e:
        logger.error("PROMPT GUARD: Cannot load ancestral_sage_prompt: %s", e)

    try:
        from prompts.director_prompt import (
            DIRECTOR_PROMPT, DIRECTOR_PROMPT_HASH_EXPECTED,
            ASSISTANT_DIRECTOR_PROMPT, ASSISTANT_DIRECTOR_PROMPT_HASH_EXPECTED,
        )
        _HARDCODED_CHECKS["director"] = (DIRECTOR_PROMPT, DIRECTOR_PROMPT_HASH_EXPECTED)
        _HARDCODED_CHECKS["assistant_director"] = (ASSISTANT_DIRECTOR_PROMPT, ASSISTANT_DIRECTOR_PROMPT_HASH_EXPECTED)
    except Exception as e:
        logger.error("PROMPT GUARD: Cannot load director_prompt hashes: %s", e)

    try:
        from sovereign.sovereign_persona import SOVEREIGN_PERSONA, SOVEREIGN_PERSONA_HASH_EXPECTED
        _HARDCODED_CHECKS["sovereign"] = (SOVEREIGN_PERSONA, SOVEREIGN_PERSONA_HASH_EXPECTED)
    except Exception as e:
        logger.warning("PROMPT GUARD: Cannot load sovereign hash: %s", e)

    try:
        from prompts.more_department_system import _MORE_DEPARTMENT_SYSTEM, MORE_DEPARTMENT_HASH_EXPECTED
        _HARDCODED_CHECKS["more_department"] = (_MORE_DEPARTMENT_SYSTEM, MORE_DEPARTMENT_HASH_EXPECTED)
    except Exception as e:
        logger.warning("PROMPT GUARD: Cannot load more_department hash: %s", e)

    try:
        from wai_institute.personas.prt import PRT_SYSTEM_PROMPT, PRT_SYSTEM_PROMPT_HASH_EXPECTED
        _HARDCODED_CHECKS["prt"] = (PRT_SYSTEM_PROMPT, PRT_SYSTEM_PROMPT_HASH_EXPECTED)
    except Exception as e:
        logger.warning("PROMPT GUARD: Cannot load prt hash: %s", e)

    try:
        from prompts.oliver_guardian_prompt import OLIVER_GUARDIAN_PROMPT, OLIVER_GUARDIAN_HASH_EXPECTED
        _HARDCODED_CHECKS["oliver_guardian"] = (OLIVER_GUARDIAN_PROMPT, OLIVER_GUARDIAN_HASH_EXPECTED)
    except Exception as e:
        logger.warning("PROMPT GUARD: Cannot load oliver_guardian hash: %s", e)

    # Run all hardcoded checks
    hardcoded_failures: list = []
    results: Dict[str, bool] = {}
    for name, (prompt_text, expected_hash) in _HARDCODED_CHECKS.items():
        ok = _sha256(prompt_text) == expected_hash
        results[name] = ok
        if not ok:
            hardcoded_failures.append(name)
            logger.critical(
                "PROMPT GUARD CRITICAL: '%s' prompt hash MISMATCH. "
                "Unauthorized modification detected. Falling back to RESTRICTED mode.",
                name,
            )

    # Fire governance integrity email for any failures
    if hardcoded_failures:
        _send_integrity_alert(hardcoded_failures)

    texts = _load_prompt_texts()

    if not _BASELINE_LOCKED:
        # First call: enroll all hashes as baseline
        for name, text in texts.items():
            if text is not None:
                _BASELINE[name] = _sha256(text)
                logger.info("PROMPT GUARD: Enrolled baseline hash for '%s'", name)
            else:
                logger.warning("PROMPT GUARD: Skipping baseline enrollment for '%s' (not loaded)", name)
        _BASELINE_LOCKED = True
        # On first call, everything that loaded is considered "ok"
        for name, text in texts.items():
            results[name] = text is not None
    else:
        # Subsequent calls: compare to baseline
        for name, text in texts.items():
            if name not in _BASELINE:
                results[name] = text is not None
                continue
            if text is None:
                logger.error("PROMPT GUARD: Prompt '%s' is now UNAVAILABLE (was loaded before)", name)
                results[name] = False
                continue
            current_hash = _sha256(text)
            if current_hash != _BASELINE[name]:
                logger.critical(
                    "PROMPT GUARD CRITICAL: Prompt '%s' hash DRIFTED from baseline. "
                    "File may have been modified since server startup. "
                    "Baseline: %s... Current: %s...",
                    name,
                    _BASELINE[name][:16],
                    current_hash[:16],
                )
                results[name] = False
                if strict:
                    raise RuntimeError(f"Prompt integrity failure: '{name}' has drifted from baseline")
            else:
                results[name] = True

    # Summary log
    failed = [k for k, v in results.items() if not v]
    if failed:
        logger.error("PROMPT GUARD: Integrity check FAILED for: %s", failed)
    else:
        logger.info("PROMPT GUARD: All prompt integrity checks passed.")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — PROMPT INJECTION DETECTION
# Scans user messages for known attack patterns before they reach the LLM.
# ─────────────────────────────────────────────────────────────────────────────

# Injection pattern categories
_INJECTION_PATTERNS = [
    # --- Direct system override attempts ---
    (r"ignore\s+(all\s+)?(previous|prior|above|your)\s+(instructions?|prompts?|rules?|constraints?)", "SYSTEM_OVERRIDE"),
    (r"forget\s+(everything|all|your|what)\s+(you\s+)?(were\s+)?(told|instructed|trained|programmed)", "SYSTEM_OVERRIDE"),
    (r"disregard\s+(your|all|previous|prior)\s+(instructions?|rules?|guidelines?|constraints?)", "SYSTEM_OVERRIDE"),
    (r"(new|updated|revised|override)\s+(instructions?|system\s+prompt|directive)", "SYSTEM_OVERRIDE"),
    (r"\[system\]|\[SYSTEM\]|<system>|</system>|\bSYSTEM:\s", "SYSTEM_TAG_INJECTION"),
    (r"\[INST\]|\[/INST\]|<\|im_start\|>|<\|im_end\|>|\[HUMAN\]|\[ASSISTANT\]", "ROLE_TAG_INJECTION"),

    # --- Identity override attempts ---
    (r"you\s+are\s+(now|actually|really|in\s+fact)\s+(a|an)\s+\w+", "IDENTITY_OVERRIDE"),
    (r"(pretend|act|roleplay|role-play|play)\s+(you\s+are|as\s+if|that\s+you|being)", "ROLEPLAY_OVERRIDE"),
    (r"(your\s+)?(true|real|actual|hidden|secret)\s+(name|identity|self|purpose|instructions?)", "IDENTITY_PROBE"),
    (r"you\s+(are\s+)?(not|no\s+longer)\s+(the\s+)?(director|assistant\s+director|ancestral\s+sage|wai)", "IDENTITY_DENIAL"),

    # --- Prompt exfiltration attempts ---
    (r"(repeat|show|reveal|print|output|display|tell\s+me|what\s+(is|are))\s+(your\s+)?(system\s+prompt|instructions?|context|rules?|constraints?|training)", "PROMPT_LEAK"),
    (r"what\s+(exactly\s+)?(does\s+your\s+)?(system|prompt|instruction)\s+(say|tell|instruct)", "PROMPT_LEAK"),
    (r"(output|print|repeat)\s+(the\s+)?(beginning|start|first\s+\d+\s+words?\s+of)\s+(your|the)\s+(system|prompt|context)", "PROMPT_LEAK"),

    # --- Role escalation attempts ---
    (r"(grant|give|assign|elevate)\s+(me|yourself|this\s+user)\s+(admin|executive|root|full|unlimited)\s+(access|privileges?|role|permissions?)", "ROLE_ESCALATION"),
    (r"(you\s+have\s+permission|you\s+are\s+authorized|you\s+are\s+allowed)\s+to\s+(bypass|ignore|override)", "AUTH_OVERRIDE"),
    (r"(emergency|override|bypass|jailbreak)\s+(code|key|phrase|mode|protocol)", "BYPASS_ATTEMPT"),

    # --- AI-to-AI manipulation ---
    (r"(as\s+an?\s+)?ai\s+(assistant|model|language\s+model|system|chatbot)\s+(you\s+)(must|should|need\s+to|are\s+required\s+to)", "AI_PEER_MANIPULATION"),
    (r"(gpt|chatgpt|claude|gemini|llama|mistral|copilot)\s+(told|says?|instructed|advised)\s+(me|you|us)\s+to", "AI_PEER_AUTHORITY"),
    (r"(this\s+is\s+)?anthropic\s+(policy|guidelines?|override|emergency)", "AI_AUTHORITY_SPOOF"),
    (r"(this\s+is\s+)?openai\s+(policy|guidelines?|override|emergency)", "AI_AUTHORITY_SPOOF"),

    # --- Developer/debug mode exploitation ---
    (r"(developer|debug|maintenance|test|sandbox)\s+(mode|override|access|bypass)", "DEV_MODE_PROBE"),
    (r"(sudo|root|admin|superuser|god\s+mode)\s+(mode|access|override|command)", "DEV_MODE_PROBE"),
    (r"\bDAN\b|\bDAN\s+mode\b|do\s+anything\s+now", "DAN_JAILBREAK"),

    # --- Instruction injection via data ---
    (r"<!--.*?(ignore|override|inject).*?-->", "HTML_INJECTION"),
    (r"\{[\"']?(role|system|instruction)[\"']?\s*:", "JSON_INJECTION"),
]

# Compile all patterns once at module load
_COMPILED_PATTERNS = [
    (re.compile(pat, re.IGNORECASE | re.DOTALL), category)
    for pat, category in _INJECTION_PATTERNS
]

# Patterns that trigger an automatic block regardless of role
_ALWAYS_BLOCK_CATEGORIES = {
    "SYSTEM_OVERRIDE",
    "SYSTEM_TAG_INJECTION",
    "ROLE_TAG_INJECTION",
    "IDENTITY_DENIAL",
    "PROMPT_LEAK",
    "AUTH_OVERRIDE",
    "BYPASS_ATTEMPT",
    "DAN_JAILBREAK",
    "AI_AUTHORITY_SPOOF",
    "JSON_INJECTION",
}

# Patterns that generate a warning but don't block (require human review flag)
_WARN_CATEGORIES = {
    "IDENTITY_OVERRIDE",
    "ROLEPLAY_OVERRIDE",
    "IDENTITY_PROBE",
    "ROLE_ESCALATION",
    "AI_PEER_MANIPULATION",
    "AI_PEER_AUTHORITY",
    "DEV_MODE_PROBE",
    "HTML_INJECTION",
}


def _scan_message(text: str) -> list:
    """Scan a message for injection patterns. Returns list of (category, match) tuples."""
    hits = []
    for pattern, category in _COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            hits.append((category, match.group(0)[:100]))  # truncate match for logging
    return hits


def check_message_safe(
    message: str,
    user_role: str = "student",
    endpoint: str = "unknown",
    user_id: str = "unknown",
) -> Dict:
    """
    Scan a user message for prompt injection and tamper attempts.

    Args:
        message   : The raw user message string.
        user_role : The authenticated user's role.
        endpoint  : Which endpoint is being called (for logging).
        user_id   : The user's ID (for logging).

    Returns:
        {
            "safe"    : bool,
            "reason"  : str | None,      # human-readable reason if not safe
            "category": str | None,      # attack category if detected
            "warnings": [str],           # non-blocking warnings
        }
    """
    if not message or not message.strip():
        return {"safe": True, "reason": None, "category": None, "warnings": []}

    # Length check — messages over 8000 chars are a potential context poisoning vector
    if len(message) > 8000:
        logger.warning(
            "PROMPT GUARD: Oversized message from user_id=%s on %s (%d chars)",
            user_id, endpoint, len(message)
        )
        return {
            "safe": False,
            "reason": "Message exceeds maximum allowed length (8000 characters).",
            "category": "OVERSIZED_INPUT",
            "warnings": [],
        }

    hits = _scan_message(message)
    if not hits:
        return {"safe": True, "reason": None, "category": None, "warnings": []}

    blocking_hits = [(cat, match) for cat, match in hits if cat in _ALWAYS_BLOCK_CATEGORIES]
    warning_hits  = [(cat, match) for cat, match in hits if cat in _WARN_CATEGORIES]

    warnings = []

    if blocking_hits:
        cat, match = blocking_hits[0]
        logger.warning(
            "PROMPT GUARD BLOCK: user_id=%s role=%s endpoint=%s category=%s match='%s...'",
            user_id, user_role, endpoint, cat, match[:60]
        )
        return {
            "safe": False,
            "reason": (
                "Your message contains content that cannot be processed for security reasons. "
                "If this is a legitimate request, rephrase it and try again."
            ),
            "category": cat,
            "warnings": [],
        }

    # Warning-level hits — log and allow but flag
    for cat, match in warning_hits:
        msg = f"Suspicious pattern detected: {cat}"
        warnings.append(msg)
        logger.warning(
            "PROMPT GUARD WARN: user_id=%s role=%s endpoint=%s category=%s match='%s...'",
            user_id, user_role, endpoint, cat, match[:60]
        )

    return {"safe": True, "reason": None, "category": None, "warnings": warnings}


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — SSRF PROTECTION
# Blocks internal IP ranges and dangerous hostnames from fetch_url tool.
# ─────────────────────────────────────────────────────────────────────────────

import ipaddress
import urllib.parse

# Hostnames that are always blocked
_BLOCKED_HOSTNAMES = frozenset({
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "metadata.google.internal",     # GCP metadata endpoint
    "169.254.169.254",               # AWS/Azure/GCP IMDS endpoint
    "instance-data",                 # AWS legacy metadata
    "metadata",                      # Azure metadata alias
})

# Private / link-local CIDR ranges
_PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # link-local / IMDS
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def check_url_safe(url: str) -> Dict:
    """
    Validate a URL before fetch_url is allowed to request it.
    Blocks private IP ranges, IMDS endpoints, and non-HTTP schemes.

    Returns {"safe": bool, "reason": str|None}
    """
    if not url:
        return {"safe": False, "reason": "Empty URL"}

    if not url.startswith(("http://", "https://")):
        return {"safe": False, "reason": "Only http:// and https:// are permitted"}

    try:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ""
    except Exception:
        return {"safe": False, "reason": "Malformed URL"}

    # Direct hostname blocklist
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        logger.warning("PROMPT GUARD SSRF: Blocked hostname='%s' in URL='%s'", hostname, url[:200])
        return {"safe": False, "reason": f"Access to '{hostname}' is not permitted"}

    # IP address check
    try:
        ip = ipaddress.ip_address(hostname)
        for network in _PRIVATE_RANGES:
            if ip in network:
                logger.warning("PROMPT GUARD SSRF: Blocked private IP=%s in URL='%s'", ip, url[:200])
                return {"safe": False, "reason": "Access to private network addresses is not permitted"}
    except ValueError:
        pass  # Not an IP address — hostname, proceed

    # Block port 0 and common internal ports
    if parsed.port in (0, 22, 23, 25, 110, 143, 3306, 5432, 6379, 27017):
        return {"safe": False, "reason": f"Access to port {parsed.port} is not permitted"}

    return {"safe": True, "reason": None}


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — CONVENIENCE FACADE
# ─────────────────────────────────────────────────────────────────────────────

class PromptGuard:
    """
    Stateless facade for all prompt guard operations.
    Import and call on every AI request.

    Example usage in server.py:

        from ai.prompt_guard import prompt_guard

        # Startup:
        prompt_guard.startup_integrity_check()

        # Per-request:
        prompt_guard.assert_message_safe(message, user.role, "/ai/director", user.id)
    """

    def startup_integrity_check(self, strict: bool = False) -> Dict[str, bool]:
        """Call once on server startup. Establishes prompt baseline."""
        logger.info("PROMPT GUARD: Running startup integrity check...")
        return verify_all_prompt_integrity(strict=strict)

    def assert_message_safe(
        self,
        message: str,
        user_role: str,
        endpoint: str,
        user_id: str,
    ) -> None:
        """
        Call before every AI request. Raises ValueError if the message
        is detected as a tamper attempt.
        Callers should catch ValueError and return 400.
        """
        result = check_message_safe(message, user_role, endpoint, user_id)
        if not result["safe"]:
            raise ValueError(result["reason"] or "Message blocked by security policy")

    def assert_url_safe(self, url: str) -> None:
        """Call before fetch_url. Raises ValueError if the URL is unsafe."""
        result = check_url_safe(url)
        if not result["safe"]:
            raise ValueError(result["reason"] or "URL blocked by security policy")

    def get_integrity_status(self) -> Dict[str, bool]:
        """Return current integrity status of all persona prompts."""
        return verify_all_prompt_integrity()


# Module-level singleton
prompt_guard = PromptGuard()
