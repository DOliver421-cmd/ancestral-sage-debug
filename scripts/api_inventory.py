#!/usr/bin/env python3
"""Build the complete MoreHelp API inventory from the running app's route table.

Usage: JWT_SECRET=local-test-secret PYTHONPATH=backend python3 scripts/api_inventory.py
Output: scripts/api_inventory.json  (method, full path, router module, auth deps)
"""
import ast
import importlib
import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("JWT_SECRET", "local-test-secret")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/wai_institute")

server_src = (BACKEND / "server.py").read_text(encoding="utf-8")
tree = ast.parse(server_src)

# Pull (module_name, mount_prefix) from the _ADDITIONAL_API_ROUTER_MODULES tuple.
mounts = []
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == "_ADDITIONAL_API_ROUTER_MODULES":
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    for elt in node.value.elts:
                        if isinstance(elt, (ast.Tuple, ast.List)) and len(elt.elts) == 2:
                            name = elt.elts[0].value if isinstance(elt.elts[0], ast.Constant) else None
                            prefix = elt.elts[1].value if isinstance(elt.elts[1], ast.Constant) else ""
                            if name:
                                mounts.append((name, prefix))

# Inline routers registered on api_router in server.py are covered by
# enumerating the app directly when import succeeds; the script imports each
# modular router and also imports server to read the final app if possible.

routes = []
seen = set()


def add_router(mod, module_name, prefix):  # noqa: C901
    router = getattr(mod, "router", None)
    if router is None:
        routes.append({"method": "*", "path": f"(no router attr in {module_name})", "module": module_name, "auth": [], "error": "no router"})
        return
    for route in router.routes:
        # Newer FastAPI wraps included routers in opaque wrapper objects that
        # carry no .path of their own — recurse into the wrapped router.
        # Wrapper classes vary by version (_IncludedRouter, include_context on
        # Mount/APIRouter copies, nested .routes). Handle every shape.
        inc = getattr(route, "include_context", None)
        if inc is not None:
            add_router(type("Mod", (), {"router": inc.included_router}), module_name, prefix + (getattr(inc, "prefix", "") or ""))
            continue
        wrapped = getattr(route, "included_router", None)
        if wrapped is not None:
            add_router(type("Mod", (), {"router": wrapped}), module_name, prefix + (getattr(route, "prefix", "") or ""))
            continue
        if not hasattr(route, "path"):
            if getattr(route, "routes", None):
                add_router(type("Mod", (), {"router": route}), module_name, prefix)
            continue
        for m in sorted(getattr(route, "methods", ["*"]) or ["*"]):
            full = (prefix + route.path) or "/"
            key = (m, full)
            if key in seen:
                continue
            seen.add(key)
            deps = []
            dep = getattr(route, "dependant", None)
            for d in dep.dependencies if dep else []:
                deps.append(getattr(d.call, "__name__", str(d.call)))
            routes.append({
                "method": m, "path": full, "module": module_name,
                "auth": deps, "name": getattr(route, "name", None),
            })


for name, prefix in mounts:
    try:
        mod = importlib.import_module(f"routers.{name}")
    except Exception as exc:  # noqa: BLE001
        routes.append({"method": "*", "path": f"(module import failed: routers.{name})", "module": name, "auth": [], "error": repr(exc)})
        continue
    add_router(mod, f"routers.{name}", prefix)

# Also capture the inline app routes (server.py's own handlers + ai_router).
def _add_app_route(route, prefix=""):
    # Newer FastAPI: included routers appear as opaque wrapper objects whose
    # wrapped router carries the child routes. Wrapper shapes vary by version —
    # handle include_context, included_router, and nested .routes.
    inc = getattr(route, "include_context", None)
    if inc is not None:
        sub = getattr(inc, "included_router", None)
        if sub is not None:
            for r in getattr(sub, "routes", []) or []:
                _add_app_route(r, prefix + (getattr(inc, "prefix", "") or ""))
        return
    wrapped = getattr(route, "included_router", None)
    if wrapped is not None:
        for r in getattr(wrapped, "routes", []) or []:
            _add_app_route(r, prefix + (getattr(route, "prefix", "") or ""))
        return
    # Mounts / nested routers: carry the mount path into the child prefix.
    sub = getattr(route, "routes", None)
    if sub:
        for r in sub:
            _add_app_route(r, prefix + (getattr(route, "path", "") or ""))
        return
    if not hasattr(route, "path"):
        return
    for m in sorted(getattr(route, "methods", ["*"]) or ["*"]):
        full = (prefix + route.path) or "/"
        key = (m, full)
        if key in seen:
            continue
        seen.add(key)
        deps = []
        dep = getattr(route, "dependant", None)
        for d in dep.dependencies if dep else []:
            deps.append(getattr(d.call, "__name__", str(d.call)))
        routes.append({
            "method": m, "path": full, "module": "server.inline",
            "auth": deps, "name": getattr(route, "name", None),
        })

try:
    import server as _server
    app = getattr(_server, "app", None) or getattr(_server, "application", None)
    for route in app.routes:
        _add_app_route(route)
except Exception as exc:  # noqa: BLE001
    routes.append({"method": "*", "path": "(server app import failed)", "module": "server", "auth": [], "error": repr(exc)})

routes.sort(key=lambda r: (r["method"], r["path"]))
out = Path(__file__).resolve().parent / "api_inventory.json"
out.write_text(json.dumps({"total": len(routes), "routes": routes}, indent=2), encoding="utf-8")

from collections import Counter
print(f"INVENTORY: {len(routes)} routes -> {out}")
for m, c in Counter(r["method"] for r in routes).most_common():
    print(f"  {m}: {c}")