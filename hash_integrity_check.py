#!/usr/bin/env python3
"""
WAI-Institute — Prompt Hash Integrity Checker
=============================================
Run this script any time you edit a persona prompt to verify
the SHA-256 hash matches the expected value embedded in the codebase.

Usage:
    python3 hash_integrity_check.py

From the backend directory:
    cd backend && python3 ../hash_integrity_check.py

Current verified hashes (as of last governance update):
    Ancestral Sage   : fbfba5fb4411c9b2bb475fcd29aabec138e52c60e12256234737a3be2f4e17a8
    Director (admin) : ead6c38a9899f5f0d71e6aa6b974138fd00a2195206de1f8af405ef0bee057ec
    Asst Director    : 967f97586e54f9c4c8c2f9d8a3639189c072a641f263a402d5a416e389009276
"""

import hashlib
import sys
import os

# ── locate backend directory ──────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")

if not os.path.isdir(BACKEND_DIR):
    # already inside backend/
    BACKEND_DIR = SCRIPT_DIR

sys.path.insert(0, BACKEND_DIR)

# ── expected hashes ───────────────────────────────────────────────────────────
EXPECTED = {
    "Ancestral Sage":       "fbfba5fb4411c9b2bb475fcd29aabec138e52c60e12256234737a3be2f4e17a8",
    "Director (admin)":     "ead6c38a9899f5f0d71e6aa6b974138fd00a2195206de1f8af405ef0bee057ec",
    "Asst Director":        "967f97586e54f9c4c8c2f9d8a3639189c072a641f263a402d5a416e389009276",
}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check() -> bool:
    print("=" * 70)
    print("  WAI-INSTITUTE  —  PROMPT HASH INTEGRITY CHECK")
    print("=" * 70)

    results = {}

    # ── Ancestral Sage ────────────────────────────────────────────────────────
    try:
        from prompts.ancestral_sage_prompt import (
            ANCESTRAL_SAGE_PROMPT,
            ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED,
            compute_sage_prompt_hash,
        )
        computed = compute_sage_prompt_hash()
        embedded = ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED
        expected = EXPECTED["Ancestral Sage"]
        ok = computed == expected == embedded
        results["Ancestral Sage"] = {
            "computed": computed,
            "embedded": embedded,
            "expected": expected,
            "ok": ok,
        }
    except Exception as e:
        results["Ancestral Sage"] = {"error": str(e), "ok": False}

    # ── Director prompts ──────────────────────────────────────────────────────
    try:
        from prompts.director_prompt import DIRECTOR_PROMPT_BY_ROLE
        for label, role_key, exp_key in [
            ("Director (admin)",  "admin",     "Director (admin)"),
            ("Asst Director",     "student",   "Asst Director"),
        ]:
            prompt   = DIRECTOR_PROMPT_BY_ROLE.get(role_key, "")
            computed = sha256(prompt)
            expected = EXPECTED[exp_key]
            ok       = computed == expected
            results[label] = {
                "computed": computed,
                "embedded": "(runtime computed)",
                "expected": expected,
                "ok": ok,
            }
    except Exception as e:
        results["Director (admin)"]  = {"error": str(e), "ok": False}
        results["Asst Director"]     = {"error": str(e), "ok": False}

    # ── print results ─────────────────────────────────────────────────────────
    all_ok = True
    for name, r in results.items():
        print()
        print(f"  {'✅ PASS' if r['ok'] else '❌ FAIL'}  {name}")
        if "error" in r:
            print(f"       ERROR  : {r['error']}")
        else:
            print(f"       computed : {r['computed']}")
            if r.get("embedded") != "(runtime computed)":
                match_sym = "✓" if r["computed"] == r["embedded"] else "✗"
                print(f"       embedded : {r['embedded']}  [{match_sym} matches computed]")
            exp_sym = "✓" if r["computed"] == r["expected"] else "✗"
            print(f"       expected : {r['expected']}  [{exp_sym} matches expected]")
        if not r["ok"]:
            all_ok = False

    print()
    print("=" * 70)
    if all_ok:
        print("  RESULT: ALL HASHES VERIFIED — prompts are unmodified.")
    else:
        print("  RESULT: INTEGRITY FAILURE — one or more prompts have changed.")
        print()
        print("  If you intentionally edited a prompt, update the expected hash:")
        print("    cd backend && python3 prompts/ancestral_sage_prompt.py")
        print("    Then paste the printed hash into:")
        print("      backend/prompts/ancestral_sage_prompt.py → ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED")
        print("      hash_integrity_check.py → EXPECTED dict above")
        print()
        print("  If you did NOT edit the prompt, a governance violation has occurred.")
        print("  The platform will automatically fall back to RESTRICTED_EDUCATIONAL_FALLBACK")
        print("  until the hash is restored or the expected value is updated by exec.")
    print("=" * 70)
    print()

    return all_ok


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
