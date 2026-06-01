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


def get_sovereign_prompt(memory_block: str = "") -> str:
    """Return the full Sovereign system prompt, optionally with memory appended."""
    if memory_block:
        return f"{SOVEREIGN_PERSONA}\n\n{_SEP}\n{memory_block}\n{_SEP}"
    return SOVEREIGN_PERSONA


async def build_sovereign_prompt(db, exec_id: str) -> str:
    """Async convenience: load the executive's persistent memory and assemble the
    full prompt. Memory failures degrade to the base prompt — never raise."""
    try:
        block = await sovereign_memory.load_memory_block(db, exec_id)
    except Exception:
        block = ""
    return get_sovereign_prompt(block)
