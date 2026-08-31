# WAI-Institute — Poor Righteous Teacher persona package

import hashlib as _hashlib
import pathlib as _pathlib

# Canonical system prompt loaded from prt_prompt.md — the authoritative text
_PRT_PROMPT_PATH = _pathlib.Path(__file__).parent / "prt_prompt.md"
PRT_SYSTEM_PROMPT: str = _PRT_PROMPT_PATH.read_text(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# HASH INTEGRITY — run `python3 -c "from wai_institute.personas.prt import compute_prt_hash; print(compute_prt_hash())"` from backend dir after editing prt_prompt.md and paste below.
# ─────────────────────────────────────────────────────────────────────────────

PRT_SYSTEM_PROMPT_HASH_EXPECTED = "2679e47ee1403fd4e70c52919e3a19dab264990b7bf90756808196864107072a"


def compute_prt_hash() -> str:
    return _hashlib.sha256(PRT_SYSTEM_PROMPT.encode("utf-8")).hexdigest()


def verify_prt_integrity() -> bool:
    return compute_prt_hash() == PRT_SYSTEM_PROMPT_HASH_EXPECTED
