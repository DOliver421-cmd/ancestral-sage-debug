#!/usr/bin/env python3
"""Count the real mounted API surface of the MoreHelp backend.

FastAPI's app.routes holds flat APIRoute objects, but this app mounts its
routers through middleware/access-control wrappers, so the real routes are
nested inside starlette's _IncludedRouter. A naive len(app.routes) reports
only the wrapper count and looks like the app has ~0 API endpoints.

This walks the tree and prints unique /api paths plus route-method entries.
"""
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def walk(routes, seen=None):
    """Yield every real route, descending through nested routers."""
    if seen is None:
        seen = set()
    for r in routes or []:
        if id(r) in seen:
            continue
        seen.add(id(r))
        # Nested router (FastAPI/starlette _IncludedRouter) — descend.
        inner = getattr(r, "original_router", None)
        if inner is not None:
            yield from walk(getattr(inner, "routes", []), seen)
            continue
        yield r


def main() -> int:
    import server  # noqa: E402  (import after sys.path setup)

    methods_by_path = defaultdict(set)
    for r in walk(server.app.routes):
        path = getattr(r, "path", None)
        if not path or not isinstance(path, str):
            continue
        if not path.startswith("/api"):
            continue
        methods = {m for m in (getattr(r, "methods", None) or set())
                   if m not in ("HEAD", "OPTIONS")}
        if not methods:
            continue
        methods_by_path[path].update(methods)

    total_methods = sum(len(m) for m in methods_by_path.values())
    print(f"UNIQUE_PATHS  {len(methods_by_path)}")
    print(f"METHOD_ENTRIES {total_methods}")

    if "--list" in sys.argv:
        for p in sorted(methods_by_path):
            print(f"{','.join(sorted(methods_by_path[p])):<28} {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
