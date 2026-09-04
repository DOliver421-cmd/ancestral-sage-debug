#!/usr/bin/env python3
"""Match frontend API call sites against the backend route inventory.

Usage: python3 scripts/api_frontend_match.py
Output: three lists —
  1. FRONTEND CALLS WITH NO BACKEND ROUTE  (broken features; method known)
  2. /api/ LITERALS WITH NO ROUTE FOR ANY METHOD (unknown-method call sites)
  3. BACKEND ROUTES NEVER REFERENCED BY THE FRONTEND (candidate hidden/dead)

Prefix handling: the shared client in `frontend/src/lib/api.js` is created
with `baseURL: "/api"`, so real call sites look like `api.get("/admin/users")`
(unprefixed) or `fetch("/api/...")` (prefixed). Both spellings name the same
endpoint, so every comparison normalizes by stripping a leading "/api".
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend" / "src"
INV = ROOT / "scripts" / "api_inventory.json"


def strip_api(path: str) -> str:
    """'/api/admin/users' -> '/admin/users'; '/admin/users' unchanged."""
    p = path.strip()
    if p == "/api":
        return "/"
    if p.startswith("/api/"):
        return p[4:]
    return p


def seg_re(seg: str) -> str:
    """A URL segment becomes a regex fragment. '{user_id}', ':id' and
    template-literal '${id}' segments all match any single path segment."""
    if seg.startswith("{") and seg.endswith("}"):
        return "[^/]+"
    if seg.startswith(":"):
        return "[^/]+"
    if "${" in seg:
        return "[^/]+"
    return re.escape(seg)


def backend_matcher(method: str, path: str):
    parts = strip_api(path).strip("/").split("/")
    pattern = "^/" + "/".join(seg_re(p) for p in parts) + "$"
    return re.compile(pattern)


# ── Load inventory ───────────────────────────────────────────────────────────
inv = json.loads(INV.read_text(encoding="utf-8"))["routes"]
BY_METHOD = {}
for r in inv:
    BY_METHOD.setdefault(r["method"], []).append((backend_matcher(r["method"], r["path"]), r["path"]))
ALL_BY_METHOD = {m: [b for b, _ in ps] for m, ps in BY_METHOD.items()}
ALL_ANY_METHOD = [b for ps in BY_METHOD.values() for b, _ in ps]
RAW_PATHS = [r["path"] for r in inv]


def route_exists(method: str, path: str) -> bool:
    norm = strip_api(path.split("?", 1)[0])
    if method and method in ALL_BY_METHOD:
        if any(p.match(norm) for p in ALL_BY_METHOD[method]):
            return True
    # fall back to any-method match when method unknown OR exact method missing
    return any(p.match(norm) for p in ALL_ANY_METHOD)


def mask_templates(text: str) -> str:
    """Replace every ${...} expression (balanced braces) with '${_}' so that
    quotes or backticks INSIDE the expression don't truncate a captured URL.
    """
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "$" and i + 1 < n and text[i + 1] == "{":
            depth = 1
            j = i + 2
            while j < n and depth > 0:
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                j += 1
            out.append("${_}")
            i = j
        else:
            out.append(ch)
            i += 1
    return "".join(out)


# ── Scan frontend for call sites ────────────────────────────────────────────
# api.get("/path") | axios.post("/path") | client.patch(`/path/${id}`) | ...
CALL_RE = re.compile(
    r"\b(?:api|axios|client|http)\s*\.\s*(get|post|patch|put|delete|head)\s*\(\s*([`'\"])([^`'\"]+?)\2"
)
FETCH_RE = re.compile(r"\bfetch\s*\(\s*([`'\"])([^`'\"]+?)\1")
LITERAL_RE = re.compile(r"([`'\"])(/api/[^`'\"]+?)\1")
METHOD_HINT_RE = re.compile(r"method\s*:\s*[`'\"](\w+)[`'\"]")

calls = {}   # (method|None, path) -> {files}
literals = set()

for f in FE.rglob("*"):
    if f.suffix not in (".js", ".jsx", ".ts", ".tsx"):
        continue
    raw = f.read_text(encoding="utf-8", errors="replace")
    text = mask_templates(raw)
    rel = str(f.relative_to(ROOT))
    for m in CALL_RE.finditer(text):
        meth, path = m.group(1).upper(), m.group(3).strip()
        if path.startswith("/"):
            calls.setdefault((meth, path), set()).add(rel)
    for m in FETCH_RE.finditer(text):
        path = m.group(2).strip()
        if not path.startswith("/"):
            continue
        hint = METHOD_HINT_RE.search(text[m.end():m.end() + 160])
        calls.setdefault((hint.group(1).upper() if hint else None, path), set()).add(rel)
    for m in LITERAL_RE.finditer(text):
        literals.add((m.group(2), rel))

# ── Report 1: known-method calls with no backend route ──────────────────────
print("=" * 72)
print("1. FRONTEND CALLS WITH NO BACKEND ROUTE (method known) — broken")
print("=" * 72)
broken = sorted(
    ((m, p), files) for (m, p), files in calls.items()
    if m and not route_exists(m, p) and p.startswith("/")
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
missing = sorted({p for p, _ in literals if not route_exists(None, p)})
if not missing:
    print("  none")
for p in missing:
    print(f"  {p}")

# ── Report 3: backend routes the frontend never references ──────────────────
print()
print("=" * 72)
print("3. BACKEND ROUTES NEVER REFERENCED BY FRONTEND (candidate hidden/dead)")
print("=" * 72)
referenced_paths = {p for (_, p) in calls} | {p for p, _ in literals}


def referenced(path: str) -> bool:
    """True if any frontend reference matches this route's normalized shape."""
    want = strip_api(path).strip("/").split("/")
    for rp in referenced_paths:
        have = strip_api(rp.split("?", 1)[0]).strip("/").split("/")
        if len(have) != len(want):
            continue
        if all(
            a == b or "${" in a or a.startswith("{") or a.startswith(":")
            or b.startswith("{")
            for a, b in zip(have, want)
        ):
            return True
    return False


never = sorted((r["method"], r["path"], r.get("module", "")) for r in inv if not referenced(r["path"]))
print(f"  {len(never)} routes never referenced (of {len(inv)} total)")
for m, p, mod in never:
    print(f"  {m:6s} {p}   [{mod}]")

print()
print("SUMMARY:",
      f"{len(broken)} broken method-known calls,",
      f"{len(missing)} unmatched /api literals,",
      f"{len(never)} never-referenced backend routes")
