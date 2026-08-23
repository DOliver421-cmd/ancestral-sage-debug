"""tests/test_knowledge_finder.py — Knowledge Finder: deterministic discovery.

Security rule under test (critical): the pipeline is
    access -> FILTER authorized documents -> match -> rank -> return
It must NEVER surface tier-gated, role-gated, or internal documents to an
unauthorized caller merely because the text exists in the index.

Run: python3 tests/test_knowledge_finder.py
"""

import os
import sys

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


def test_security_filtering():
    from ai.knowledge_finder import Access, search

    anon = Access()                          # public / free
    free = Access("student", "free")         # registered free
    member = Access("student", "member")
    plus = Access("student", "plus")
    staff = Access("admin", "free")

    # Internal-only documents must never surface to anyone in discovery.
    for acc in (anon, free, member, staff):
        titles = [r["title"] for r in search("arena", acc, limit=20)]
        internal_leak = [t for t in titles if "internal" in t.lower()]
        ok(f"internal docs excluded for {acc.role}/{acc.feature_tier}", not internal_leak)

    # Anonymous: only public_access documents.
    for acc in (anon, free):
        titles = [r["title"] for r in search("creator studio", acc, limit=20)]
        ok(f"studio feature hidden for {acc.role}/{acc.feature_tier}",
           not any("Creator Studio" in t or "Studio" == t for t in titles))

    # Member sees member-tier, not plus-tier feature docs.
    m_titles = [r["title"] for r in search("creator lounge", member, limit=20)]
    ok("member sees Creator Lounge (member tier)", any("Lounge" in t for t in m_titles))
    p_titles = [r["title"] for r in search("creator studio", plus, limit=20)]
    ok("plus sees Creator Studio (plus tier)", any("Creator Studio" in t for t in p_titles))

    # Staff (admin) sees tier-gated feature docs (staff access is full).
    s_titles = [r["title"] for r in search("creator studio", staff, limit=20)]
    ok("admin sees Creator Studio", any("Creator Studio" in t for t in s_titles))


def test_ranking_and_prompts():
    from ai.knowledge_finder import Access, search, upgrade_prompt, render_reply

    anon = Access()
    member = Access("student", "member")
    byok = Access("student", "free", byok=True)
    staff = Access("admin", "free")

    # Music query ranks the music doc first.
    results = search("music production", anon)
    ok("music query ranks music doc first", results and "Music" in results[0]["title"])

    # Refund query finds the refund policy.
    results = search("how do I get a refund", anon)
    ok("refund query finds refund policy", results and "Refund" in results[0]["title"])

    # Upgrade prompt: present for anonymous/member, absent for byok/staff.
    ok("anonymous gets upgrade prompt", upgrade_prompt(anon) is not None and "$3" in upgrade_prompt(anon))
    ok("member gets upgrade prompt", upgrade_prompt(member) is not None)
    ok("byok gets NO upgrade prompt", upgrade_prompt(byok) is None)
    ok("staff gets NO upgrade prompt", upgrade_prompt(staff) is None)

    # render_reply: exact curated answer wins.
    reply = render_reply("I am getting evicted", anon)
    ok("render: exact KB answer for eviction", "eviction" in reply.lower() and "rights" in reply.lower())

    # render_reply: unmatched -> related resources + prompt (never a brick wall).
    reply = render_reply("how do I build a music career with no money", anon)
    ok("render: related resources for unmatched", "knowledge base" in reply and "Music" in reply)
    ok("render: upgrade prompt included", "AI-guided" in reply)

    # render_reply: staff/byok get results without the sales prompt.
    reply = render_reply("how do I build a music career", staff)
    ok("render: staff reply has no upgrade prompt", "AI-guided" not in reply)


def test_index_inventory():
    from ai.knowledge_finder import doc_count

    inv = doc_count()
    ok("index has >=150 documents", inv["documents"] >= 150)
    ok("index has public documents", inv["public_documents"] >= 100)
    ok("index covers multiple types", len(inv["types"]) >= 5)


if __name__ == "__main__":
    test_security_filtering()
    test_ranking_and_prompts()
    test_index_inventory()
    print(f"\n{'-' * 50}\nRESULTS: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
