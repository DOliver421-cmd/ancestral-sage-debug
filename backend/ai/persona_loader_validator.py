"""
persona_loader_validator.py - Director 4.0
============================================
Startup validation ensuring all 12 personas load correctly
with no naming mismatches, missing entries, or broken imports.

Run standalone:
  cd backend
  python -m ai.persona_loader_validator

Or import and call validate_personas() programmatically.
"""

from ai.persona_loader import load_personas

REQUIRED_PERSONAS = [
    "director",
    "assistant_director",
    "ancestral_sage",
    "savant_scholar",
    "apprentice",
    "revenue_director",
    "wai_success_engine",
    "product_designer",
    "risk_officer",
    "strategic_navigator",
    "confidentiality_sentinel",
    "elder_council",
]


def validate_personas() -> dict:
    """
    Load all personas and validate completeness.

    Returns:
        {
            "loaded":  [list of loaded persona keys],
            "missing": [list of any missing required personas],
            "valid":   bool — True only if no personas are missing,
            "prompt_lengths": {key: len(prompt)} for size audit,
        }
    """
    try:
        personas = load_personas()
    except Exception as exc:
        return {
            "loaded":   [],
            "missing":  REQUIRED_PERSONAS,
            "valid":    False,
            "error":    str(exc),
        }

    loaded_keys = list(personas.keys())
    missing = [p for p in REQUIRED_PERSONAS if p not in personas]

    prompt_lengths = {k: len(v) for k, v in personas.items()}

    return {
        "loaded":         loaded_keys,
        "missing":        missing,
        "valid":          len(missing) == 0,
        "prompt_lengths": prompt_lengths,
    }


def assert_valid() -> None:
    """Raise RuntimeError if any required persona is missing."""
    result = validate_personas()
    if not result["valid"]:
        raise RuntimeError(
            f"Persona validation FAILED — missing: {result['missing']}"
        )


if __name__ == "__main__":
    import json
    result = validate_personas()
    print(json.dumps(result, indent=2))
    if result["valid"]:
        print("\n✓ All personas loaded successfully.")
    else:
        print(f"\n✗ MISSING: {result['missing']}")
        raise SystemExit(1)
