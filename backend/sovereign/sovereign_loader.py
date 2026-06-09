"""
sovereign_loader.py — assembles The Sovereign's system prompt.

Mirrors the role of ai/persona_loader.py's get_persona(), but kept separate by
design: The Sovereign is a standalone, executive-only, Director-supervised module.

    get_sovereign_prompt(memory_block="")  -> str   (sync; pass a preloaded block)
    build_sovereign_prompt(db, exec_id)    -> str   (async; loads memory, then assembles)
"""

from sovereign.sovereign_persona import SOVEREIGN_PERSONA
from sovereign import sovereign_memory

_SEP = "=" * 60

try:
    from prompts.founding.operating_agreement import get_operating_agreement as _get_agreement
    _AGREEMENT = _get_agreement()
except Exception:
    _AGREEMENT = ""

try:
    from prompts.founding.oliver_legacy import get_oliver_legacy as _get_legacy
    _LEGACY = _get_legacy()
except Exception:
    _LEGACY = ""

try:
    from prompts.founding.platform_overview import get_platform_overview as _get_overview
    _OVERVIEW = _get_overview()
except Exception:
    _OVERVIEW = ""

_SOVEREIGN_CONTEXT = ""
if _AGREEMENT:
    _SOVEREIGN_CONTEXT += f"\n\n{_SEP}\nFOUNDING OPERATING AGREEMENT — YOUR PRIMARY MANDATE:\n{_AGREEMENT}\n{_SEP}"
if _LEGACY:
    _SOVEREIGN_CONTEXT += f"\n\n{_SEP}\nTHE OLIVER LEGACY — KNOW WHO YOU SERVE:\n{_LEGACY}\n{_SEP}"
if _OVERVIEW:
    _SOVEREIGN_CONTEXT += f"\n\n{_SEP}\nPLATFORM OVERVIEW & REVENUE STRATEGY — THE BIG PICTURE:\n{_OVERVIEW}\n{_SEP}"


def get_sovereign_prompt(memory_block: str = "") -> str:
    """Return the full Sovereign system prompt, optionally with memory appended."""
    base = SOVEREIGN_PERSONA + _SOVEREIGN_CONTEXT
    if memory_block:
        return f"{base}\n\n{_SEP}\n{memory_block}\n{_SEP}"
    return base


async def build_sovereign_prompt(db, exec_id: str) -> str:
    """Async convenience: load the executive's persistent memory and assemble the
    full prompt. Memory failures degrade to the base prompt — never raise."""
    try:
        block = await sovereign_memory.load_memory_block(db, exec_id)
    except Exception:
        block = ""
    return get_sovereign_prompt(block)
