"""
Update all email addresses across the codebase to map to the 4 Gmail inboxes.

Mapping:
  oldthug957@gmail.com  ←  privacy, delon/exec, admin
  souppoetry@gmail.com  ←  student, support
  poetgames@gmail.com   ←  noreply, internships
  poetgames3@gmail.com  ←  ads
"""
import os

REPLACEMENTS = [
    # --- @wai-institute.org ---
    ("delon@wai-institute.org",           "oldthug957@gmail.com"),
    ("privacy@wai-institute.org",         "oldthug957@gmail.com"),
    ("internships@wai-institute.org",     "poetgames@gmail.com"),
    ("ads@wai-institute.org",             "poetgames3@gmail.com"),
    ("noreply@wai-institute.org",         "poetgames@gmail.com"),

    # --- @wai-institute.com ---
    ("admin@wai-institute.com",           "oldthug957@gmail.com"),
    ("support@wai-institute.com",         "souppoetry@gmail.com"),
    ("noreply@wai-institute.com",         "poetgames@gmail.com"),
    ("legal@wai-institute.com",           "oldthug957@gmail.com"),
    ("licensing@wai-institute.com",       "oldthug957@gmail.com"),
    ("technical-support@wai-institute.com", "souppoetry@gmail.com"),

    # --- @morehelpcenteral.com ---
    ("delon@morehelpcenteral.com",        "oldthug957@gmail.com"),
]

# Also update RESEND_FROM "W.A.I. <noreply@wai-institute.org>" -> "W.A.I. <poetgames@gmail.com>"
RESEND_FROM_OLD = '"W.A.I. <noreply@wai-institute.org>"'
RESEND_FROM_NEW = '"W.A.I. <poetgames@gmail.com>"'



EXCLUDE_DIRS = {'.git', '__pycache__', 'node_modules', '.pytest_cache', '.claude', 'evidence_bundle', 'handbooks', 'scripts'}

changed_files = set()

def should_skip(path):
    parts = path.replace('\\', '/').split('/')
    for ed in EXCLUDE_DIRS:
        if ed in parts:
            return True
    return path.endswith('.png') or path.endswith('.jpg') or '.git' in parts

BASE = r"C:\Users\lenovo\ancestral-sage-debug"

for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for fname in files:
        ext = os.path.splitext(fname)[1]
        if ext not in ('.py', '.jsx', '.js', '.md', '.json', '.yml', '.yaml', '.toml', '.html', '.sh', '.txt', '.env.example'):
            continue
        if fname == '.env' and 'evidence_bundle' not in root:
            continue  # skip .env files (gitignored anyway, live creds)
        path = os.path.join(root, fname)
        if should_skip(path):
            continue

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                content = f.read()
            except:
                continue

        original = content
        for old, new in REPLACEMENTS:
            if old in content:
                content = content.replace(old, new)

        if RESEND_FROM_OLD in content:
            content = content.replace(RESEND_FROM_OLD, RESEND_FROM_NEW)

        if content != original:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            changed_files.add(path)
            print(f"  UPDATED: {path}")

print(f"\n{len(changed_files)} files updated.")
for f in sorted(changed_files):
    print(f"  {f}")
