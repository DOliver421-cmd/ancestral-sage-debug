#!/usr/bin/env python3
"""Match frontend API call sites against the backend route inventory.

Usage: python3 scripts/api_frontend_match.py
Output: three lists —
  1. FRONTEND CALLS WITH NO BACKEND ROUTE  (broken features; method known)
  2. FRONTEND CALLS WITH NO ROUTE (method unknown, e.g. template literals)
  3. BACKEND ROUTES NEVER REFERENCED BY THE FRONTEND (candidate hidden/dead)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend" / "src"
INV = ROOT / "scripts" / "api_inventory.json"

# ── Load inventory ───────────────────────────────────────────────────────────
inv = json.loads(INV.read_text(encoding="utf-8"))["routes"]

# Normalize a backend path: "/admin/prices/{price_id}" -> segments with a
# placeholder pattern that matches any single segment.
def seg_re(seg: str) -> str:
    if seg.startswith("{") and seg.endswith("}"):
        return "[^/]+"
    return re.escape(seg)

def backend_matcher(method: str, path: str):
    parts = path.split("/")
    pattern = "^" + "/".join(seg_re(p) for p in parts) + "$"
    return re.compile(pattern)

# method -> list of (compiled path regex, raw path)
BY_METHOD = {}
for r in inv:
    BY_METHOD.setdefault(r["method"], []).append(backend_matcher(r["method"], r["path"]))

ALL_PATTERNS = []
for meth, pats in BY_METHOD.items():
    for p in pats:
        ALL_PATTERNS.append((meth, p))

def route_exists(method: str, path: str) -> bool:
    for m, p in ALL_PATTERNS:
        if method and m != method:
            continue
        if p.match(path):
            return True
    return False

# ── Scan frontend for call sites ────────────────────────────────────────────
CALL_RE = re.compile(
    r"""\b(?:api|axios|client|http)\.(get|post|patch|put|delete|head)\s*\(\s*[`'"](\/api\/[^`'"?\s]+)"""
)
FETCH_RE = re.compile(r"""fetch\s*\(\s*[`'"](\/api\/[^`'"?\s]+)""")
LITERAL_RE = re.compile(r"""[`'"](\/api\/[^`'"?\s]+)[`'"]""")
METHOD_HINT_RE = re.compile(r"""method\s*:\s*[`'"](\w+)[`'"]""")

calls = {}          # (method|None, path) -> [files]
literals = set()

for f in FE.rglob("*"):
    if f.suffix not in (".js", ".jsx", ".ts", ".tsx"):
        continue
    text = f.read_text(encoding="utf-8", errors="replace")
    for m in CALL_RE.finditer(text):
        meth, path = m.group(1).upper(), m.group(2)
        calls.setdefault((meth, path), set()).add(str(f.relative_to(ROOT)))
    for m in FETCH_RE.finditer(text):
        path = m.group(1)
        # look for a method hint near this fetch
        tail = text[m.end():m.end() + 120]
        hint = METHOD_HINT_RE.search(tail)
        calls.setdefault((hint.group(1).upper() if hint else None, path), set()).add(
            str(f.relative_to(ROOT)))
    for m in LITERAL_RE.finditer(text):
        literals.add((m.group(1), str(f.relative_to(ROOT))))

# ── Report 1: known-method calls with no backend route ──────────────────────
print("=" * 72)
print("1. FRONTEND CALLS WITH NO BACKEND ROUTE (method known) — broken")
print("=" * 72)
broken = sorted(
    ((m, p), files) for (m, p), files in calls.items()
    if m and not route_exists(m, p) and p.startswith("/api/")
)
if not broken:
    print("  none")
for (m, p), files in broken:
    print(f"  {m:6s} {p}")
    for f in sorted(files)[:4]:
        print(f"          at {f}")

# ── Report 2: literal /api/ strings with no route at all (any method) ───────
print()
print("=" * 72)
print("2. /api/ LITERALS WITH NO ROUTE FOR ANY METHOD (incl. unknown-method)")
print("=" * 72)
missing = sorted({p for p, f in literals if not route_exists(None, p) and p.startswith("/api/")})
if not missing:
    print("  none")
for p in missing:
    print(f"  {p}")

# ── Report 3: backend routes the frontend never references ──────────────────
print()
print("=" * 72)
print("3. BACKEND ROUTES NEVER REFERENCED BY FRONTEND (candidate hidden/dead)")
print("=" * 72)
referenced_paths = {p for (m, p) in calls} | {p for p, f in literals}

def referenced(path: str) -> bool:
    for rp in referenced_paths:
        if not rp.startswith("/api/"):
            continue
        # exact or same method-agnostic segment shape
        if rp == path:
            return True
        rseg, pseg = rp.strip("/").split("/"), path.strip("/").split("/")
        if len(rseg) != len(pseg):
            continue
        if all(a == b or a.startswith("{") or b.startswith("{") for a, b in zip(rseg, pseg)):
            return True
    return False

never = sorted(
    (r["method"], r["path"], r.get("module", "")) for r in inv if not referenced(r["path"])
)
print(f"  {len(never)} routes never referenced")
for m, p, mod in never:
    print(f"  {m:6s} {p}   [{mod}]")