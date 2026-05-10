import os
import re
import hashlib

BACKEND_DIR = "backend"
REQ_FILE = os.path.join(BACKEND_DIR, "requirements.txt")
PROMPT_FILE = os.path.join(BACKEND_DIR, "prompts", "ancestral_sage_prompt.py")

print("\n=== BACKEND DOCTOR v3: FULL AUTO‑REPAIR ===\n")

# ============================================================
# 1) DEPENDENCY FIXES
# ============================================================

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

with open(REQ_FILE, "r", encoding="utf-8") as f:
    reqs = f.read()

installed = set()
req_lines = reqs.splitlines()
for line in req_lines:
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    pkg = line.split("==")[0].strip()
    if pkg:
        installed.add(pkg.lower())

print("\nPackages in requirements.txt:", installed)

mapping = {
    "jwt": "PyJWT==2.8.0",
    "passlib": "passlib==1.7.4",
    "pymongo": "pymongo==4.5.0",
    "motor": "motor==3.3.1",
    "fastapi": "fastapi==0.110.0",
    "uvicorn": "uvicorn[standard]==0.25.0",
    "email_validator": "email-validator==2.3.0",
    "python_jose": "python-jose==3.3.0",
    "openai": "openai==1.99.9",
}

missing = []
for imp in imports:
    pkg = mapping.get(imp)
    if pkg and pkg.split("==")[0].lower() not in installed:
        missing.append(pkg)

print("\nMissing packages:", missing)

if missing:
    print("\n=== APPLYING FIXES TO requirements.txt ===")
    with open(REQ_FILE, "a", encoding="utf-8") as f:
        for pkg in missing:
            f.write(f"\n{pkg}\n")
            print("Added:", pkg)

# ============================================================
# 2) PROMPT FILE FIXES
# ============================================================

print("\n=== CHECKING ancestral_sage_prompt.py ===")

if not os.path.exists(PROMPT_FILE):
    print(f"ERROR: Prompt file not found at {PROMPT_FILE}")
    exit(1)

with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    prompt_src = f.read()

changed = False

# ------------------------------------------------------------
# Ensure RESTRICTED_EDUCATIONAL_FALLBACK exists
# ------------------------------------------------------------
if "RESTRICTED_EDUCATIONAL_FALLBACK" not in prompt_src:
    fallback_block = '''
# Fallback used when hash integrity fails or persona is restricted
RESTRICTED_EDUCATIONAL_FALLBACK = """
Your request cannot be answered in unrestricted mode.
This fallback provides a safe, educational-only explanation instead.
"""
'''
    prompt_src += "\n" + fallback_block
    print("Added RESTRICTED_EDUCATIONAL_FALLBACK")
    changed = True

# ------------------------------------------------------------
# Ensure compute_sage_prompt_hash exists
# ------------------------------------------------------------
if "def compute_sage_prompt_hash" not in prompt_src:
    hash_func_block = '''
def compute_sage_prompt_hash():
    """Return the SHA-256 hash of the canonical Ancestral Sage prompt."""
    return hashlib.sha256(ANCESTRAL_SAGE_PROMPT.encode("utf-8")).hexdigest()
'''
    prompt_src += "\n" + hash_func_block
    print("Added compute_sage_prompt_hash()")
    changed = True

# ------------------------------------------------------------
# Recompute and update ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED
# ------------------------------------------------------------
m = re.search(
    r'ANCESTRAL_SAGE_PROMPT\s*=\s*("""(?:.|\n)*?""")',
    prompt_src,
    re.MULTILINE,
)

if m:
    prompt_literal = m.group(1)
    try:
        prompt_value = eval(prompt_literal)
        computed_hash = hashlib.sha256(prompt_value.encode("utf-8")).hexdigest()
        print("Computed prompt hash:", computed_hash)

        prompt_src, n = re.subn(
            r'ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED\s*=\s*".*?"',
            f'ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED = "{computed_hash}"',
            prompt_src,
        )

        if n > 0:
            print("Updated ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED")
            changed = True
        else:
            prompt_src += f'\nANCESTRAL_SAGE_PROMPT_HASH_EXPECTED = "{computed_hash}"\n'
            print("Inserted ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED")
            changed = True

    except Exception as e:
        print("ERROR computing hash:", e)

else:
    print("ERROR: Could not locate ANCESTRAL_SAGE_PROMPT")

# ------------------------------------------------------------
# Save file if changed
# ------------------------------------------------------------
if changed:
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write(prompt_src)
    print("Saved updated ancestral_sage_prompt.py")
else:
    print("No changes needed")

print("\n=== BACKEND DOCTOR v3 COMPLETE ===\n")
