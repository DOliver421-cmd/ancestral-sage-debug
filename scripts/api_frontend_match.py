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


# ── Inventory freshness guard ────────────────────────────────────────────────
# The inventory JSON is a build artifact, not source. A stale artifact produced
# dozens of false "broken feature" findings in past audits. Refuse to run
# against an inventory older than the backend source it must describe; rebuild
# it first with:  python3 scripts/api_inventory.py  (api_inventory.py sets its
# own safe local defaults for the server import).
import os
import subprocess
import time

def _newest_backend_mtime() -> float:
    newest = 0.0
    for base in (ROOT / "backend" / "server.py", ROOT / "backend" / "routers"):
        if base.is_dir():
            for f in base.rglob("*.py"):
                newest = max(newest, f.stat().st_mtime)
        elif base.exists():
            newest = max(newest, base.stat().st_mtime)
    return newest

_INV_MTIME = INV.stat().st_mtime if INV.exists() else 0.0
_SRC_MTIME = _newest_backend_mtime()
if _INV_MTIME < _SRC_MTIME:
    _age_h = (_SRC_MTIME - _INV_MTIME) / 3600.0
    print(
        f"STALE INVENTORY: scripts/api_inventory.json predates backend source "
        f"by {_age_h:.1f}h. Rebuilding from the live app...",
        file=sys.stderr,
    )
    _sub = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "api_inventory.py")],
        capture_output=True, text=True,
    )
    if _sub.returncode != 0 or not INV.exists() or INV.stat().st_mtime < _SRC_MTIME:
        print(_sub.stderr[-2000:], file=sys.stderr)
        sys.exit(
            "api_inventory.json is stale and could not be rebuilt automatically. "
            "Run: python3 scripts/api_inventory.py"
        )
    print("inventory rebuilt OK", file=sys.stderr)

# ── Load inventory ───────────────────────────────────────────────────────────
inv = json.loads(INV.read_text(encoding="utf-8"))["routes"]
BY_METHOD = {}
for r in inv:
    BY_METHOD.setdefault(r["method"], []).append((backend_matcher(r["method"], r["path"]), r["path"]))
ALL_BY_METHOD = {m: [b for b, _ in ps] for m, ps in BY_METHOD.items()}
ALL_ANY_METHOD = [b for ps in BY_METHOD.values() for b, _ in ps]
RAW_PATHS = [r["path"] for r in inv]


def route_exists(method: str, path: str) -> bool:
    """Normalize a frontend call path into a concrete candidate and test it
    against the backend regex inventory.

    Masked template-literal segments need two different treatments:
      * '/admin/users/${_}'  — the '${_}' IS the segment (an interpolated id)
        and must stay, so it matches backend '{uid}' wildcards.
      * '/admin/courses${_}' — the '${_}' is glue from an interpolated query
        suffix ('/admin/courses${filter}') and must be stripped, or the
        literal prefix can never match the backend's '/admin/courses'.
    """
    norm = strip_api(path.split("?", 1)[0])
    segs = []
    for s in norm.strip("/").split("/"):
        if not s:
            continue
        if s == "${_}":
            segs.append(s)            # whole-segment interpolation — keep
        elif s.endswith("${_}"):
            segs.append(s[: -len("${_}")])  # glued suffix — strip
        else:
            segs.append(s)
    norm = "/" + "/".join(segs) if segs else "/"
    # Collapse runs of whole-segment '${_}' wildcards into ONE wildcard: a
    # frontend action-router URL like '/aawab/agents/${id}/${action}' matches a
    # backend endpoint '/aawab/agents/{agent_id}/{action}' whose last segment
    # is a single wildcard holding the action name.
    collapsed = []
    for s in segs:
        if s == "${_}" and collapsed and collapsed[-1] == "${_}":
            continue
        collapsed.append(s)
    norm_c = "/" + "/".join(collapsed) if collapsed else "/"
    if method and method in ALL_BY_METHOD:
        if any(p.match(norm) for p in ALL_BY_METHOD[method]):
            return True
        if any(p.match(norm_c) for p in ALL_BY_METHOD[method]):
            return True
    # fall back to any-method match when method unknown OR exact method missing
    if any(p.match(norm) for p in ALL_ANY_METHOD):
        return True
    if any(p.match(norm_c) for p in ALL_ANY_METHOD):
        return True
    # Last resort: frontend action-router '/aawab/admin/agents/${id}/${action}'
    # where the final ${_} is a literal action name picked from a fixed set
    # (revoke/override/...). The backend spells each action as its own route
    # with a literal last segment — one segment MORE than the frontend path.
    # Accept a backend route whose first len(frontend) segments match the
    # frontend's collapsed segments (wildcard↔wildcard or literal equality)
    # and whose remaining tail is literal-only.
    if collapsed:
        n = len(collapsed)
        for r in inv:
            bsegs = strip_api(r["path"].split("?", 1)[0]).strip("/").split("/")
            if len(bsegs) <= n or not bsegs:
                continue
            tail = bsegs[n:]
            if any(("{" in s and "}" in s) or "${" in s or s.startswith(":") for s in tail):
                continue  # tail must be literal (a concrete action name)
            ok = True
            for f, b in zip(collapsed, bsegs[:n]):
                if f == "${_}" or b.startswith("{") or b.startswith(":"):
                    continue
                if f != b:
                    ok = False
                    break
            if ok:
                return True
    return False


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
