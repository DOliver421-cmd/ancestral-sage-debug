import os
import re
import subprocess

BACKEND_DIR = "backend"
REQ_FILE = os.path.join(BACKEND_DIR, "requirements.txt")

print("\n=== BACKEND DOCTOR: STARTING DIAGNOSTICS ===\n")

# 1. COLLECT ALL PYTHON IMPORTS
imports = set()
for root, _, files in os.walk(BACKEND_DIR):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                for line in file:
                    m = re.match(r"^\s*(import|from)\s+([a-zA-Z0-9_\.]+)", line)
                    if m:
                        imports.add(m.group(2).split(".")[0])

print("Detected imports:", imports)

# 2. LOAD REQUIREMENTS
with open(REQ_FILE, "r", encoding="utf-8") as f:
    reqs = f.read()

installed = set()
for line in reqs.splitlines():
    pkg = line.split("==")[0].strip()
    if pkg:
        installed.add(pkg.lower())

print("\nPackages in requirements.txt:", installed)

# 3. MAP COMMON IMPORT → PACKAGE NAMES
mapping = {
    "jwt": "PyJWT",
    "passlib": "passlib",
    "bcrypt": "bcrypt",
    "pymongo": "pymongo",
    "motor": "motor",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "email_validator": "email-validator",
    "python_jose": "python-jose",
}

missing = []
for imp in imports:
    pkg = mapping.get(imp)
    if pkg and pkg.lower() not in installed:
        missing.append(pkg)

print("\nMissing packages:", missing)

# 4. AUTO-FIX REQUIREMENTS
if missing:
    print("\n=== APPLYING FIXES TO requirements.txt ===")
    with open(REQ_FILE, "a", encoding="utf-8") as f:
        for pkg in missing:
            f.write(f"\n{pkg}==latest\n")
            print("Added:", pkg)

print("\n=== BACKEND DOCTOR COMPLETE ===")
