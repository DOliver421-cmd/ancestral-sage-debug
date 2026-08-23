"""tests/test_keyword_kb.py — Keyword KB engine + platform-AI policy guard.

Owner policy (August 2026):
  - anonymous / public visitors get NO AI (KB only)
  - customers at ANY tier get NO platform-funded AI (BYOK only, else KB)
  - platform-funded AI is admin / executive_admin staff only

Run: python3 tests/test_keyword_kb.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = FAIL = 0


def ok(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS  {name}")
    else:
        FAIL += 1
        print(f"FAIL  {name}")


# ── 1. Keyword KB engine layers ──────────────────────────────────────────────
def test_engine_layers():
    from ai import keyword_kb as kb

    inv = kb.entry_count()
    ok("KB has curated answers (>=100)", inv["answers"] >= 100)
    ok("KB has many intent patterns (>=500)", inv["intent_phrases"] >= 500)
    ok("KB has multiple categories (>=20)", inv["categories"] >= 20)
    ok("KB exposes all four layers", set(inv["layers"]) == {"exact", "token_overlap", "category", "generic"})

    # L1 exact intent
    e, layer = kb.best_match("I'm getting evicted next week")
    ok("L1 exact: eviction", e and layer == 1 and e["category"] == "housing")
    # L1 crisis (critical built-in, works even without JSON)
    e, layer = kb.best_match("I want to kill myself")
    ok("L1 exact: crisis built-in", e and layer == 1 and e["id"] == "crisis-immediate-danger")
    # L2 token overlap
    e, layer = kb.best_match("can you help me understand my rights about rent increases")
    ok("L2 overlap: rent increase", e and layer in (1, 2) and e["category"] == "housing")
    # L4 honest boundary for unmatched questions (owner policy: no fake AI).
    e, layer = kb.best_match("zxqwv plkjasd fghjkl")
    ok("L4 boundary: nonsense returns None + boundary reply", e is None and layer == 0)
    reply = kb.reply("zxqwv plkjasd fghjkl")
    ok("reply() always returns a non-empty string", isinstance(reply, str) and len(reply) > 20)
    ok("boundary never pretends to be AI", "won't pretend" in reply)
    ok("boundary explains the free path (BYOK + own key)", "BYOK" in reply and "own key" in reply)
    ok("boundary names free providers", "Groq" in reply and "Cerebras" in reply and "Gemini" in reply)
    ok("boundary routes to human support", "Help Center" in reply)

    # Platform-domain entries exist
    for q, cat in [
        ("how do I activate BYOK on this site", "byok"),
        ("what does the plus tier include", "tiers"),
        ("can I get a refund for my subscription", "payments"),
        ("how do I reset my password", "account"),
        ("what is arena", "internal"),
    ]:
        e, layer = kb.best_match(q)
        ok(f"platform match: {q!r} -> {cat}", e is not None and e.get("category") == cat)


# ── 2. Gateway platform-AI policy guard ──────────────────────────────────────
class FakeUsers:
    def __init__(self, role):
        self.role = role

    async def find_one(self, filt, proj=None):
        if not self.role:
            return None
        doc = {"id": filt.get("id", "u1"), "role": self.role}
        return {k: v for k, v in doc.items() if k in (proj or {}) or not proj}


class FakeDb:
    def __init__(self, role):
        self.users = FakeUsers(role)


def test_gateway_guard():
    import deps
    from ai import llm_gateway as G

    async def run(role):
        deps.set_db(FakeDb(role))
        r = await G.call_llm(
            system="test",
            messages=[{"role": "user", "content": "how do I reset my password"}],
            persona_label="test",
            user_id="u1",
        )
        return r

    async def main():
        # Non-staff authenticated caller (student) -> KB before any provider.
        r = await run("student")
        ok("student gets keyword KB (not platform AI)", r["provider"] == "kb_fallback" and "password" in r["text"])
        # Any customer role -> KB.
        r = await run("support_staff")
        ok("support_staff gets keyword KB", r["provider"] == "kb_fallback")
        # DB unavailable (role=None) -> fail-closed KB for authenticated caller.
        r = await run(None)
        ok("unverifiable staff status fails closed to KB", r["provider"] == "kb_fallback")
        # Admin proceeds to the platform chain (no keys here -> KB at tier 9).
        r = await run("admin")
        ok("admin reaches platform chain (kb at tier 9 without keys)", r["provider"] == "kb_fallback")
        r = await run("executive_admin")
        ok("executive_admin reaches platform chain", r["provider"] == "kb_fallback")

    asyncio.run(main())


# ── 3. Anonymous endpoints contain no LLM path ───────────────────────────────
def test_anonymous_endpoints_kb_only():
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "routers", "ai.py"), encoding="utf-8").read()
    # The anonymous helper reply function must not import/call the gateway.
    start = src.find("async def _helper_reply_free_first")
    end = src.find("def _split_short_full", start)
    helper_region = src[start:end if end != -1 else start + 2000]
    ok("helper reply has no call_llm", "call_llm" not in helper_region)
    chat_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "routers", "chat.py"), encoding="utf-8").read()
    pub_region = chat_src[chat_src.find("async def supervisor_public_chat"):chat_src.find("async def supervisor_public_chat") + 1200]
    ok("supervisor public-chat has no call_llm", "call_llm" not in pub_region)


if __name__ == "__main__":
    test_engine_layers()
    test_gateway_guard()
    test_anonymous_endpoints_kb_only()
    print(f"\n{'-' * 50}\nRESULTS: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
