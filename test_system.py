"""
WAI-Institute full system test — verified route paths from server.py.
Run: python test_system.py
"""

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import random
import string
from datetime import datetime

BASE = "https://ancestral-sage-backend.onrender.com/api"
V = False

results = []

def get(url, **kw):  return requests.get(url, verify=V, **kw)
def post(url, **kw): return requests.post(url, verify=V, **kw)

def check(label, resp, expected=200):
    ok = resp.status_code == expected
    results.append((label, ok, resp.status_code))
    mark = "PASS" if ok else "FAIL"
    try:    body = str(resp.json())[:100]
    except: body = resp.text[:100]
    print(f"  [{mark}] {label} ({resp.status_code}) {body}")
    return resp

def login(email, pw):
    r = post(f"{BASE}/auth/login", json={"email": email, "password": pw})
    if r.status_code == 200:
        return r.json().get("access_token"), r.json().get("user", {})
    print(f"  [FAIL] login {email} -> {r.status_code} {r.text[:80]}")
    return None, {}

def h(token): return {"Authorization": f"Bearer {token}"}

print(f"\n{'='*60}")
print(f"  WAI-Institute System Test")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}\n")

# 1. Public
print("-- 1. Public endpoints --")
check("GET /health",  get(f"{BASE}/health"))
check("GET /version", get(f"{BASE}/version"))

# 2. Auth
print("\n-- 2. Auth --")
check("Bad login -> 401", post(f"{BASE}/auth/login",
    json={"email": "fake@fake.com", "password": "wrong"}), expected=401)

# Demo accounts removed — use real credentials below.
# Replace these with actual accounts created in the live admin panel.
student_token, _ = login("", "")       # add a real student email/password
inst_token,    _ = login("", "")       # add a real instructor email/password
exec_token,    _ = login("youpickeddoliver@gmail.com", "")  # exec password

admin_token = exec_token  # exec_admin passes all admin checks

for token, label in [(student_token,"Student"),(inst_token,"Instructor"),
                     (admin_token,"Admin"),(exec_token,"Exec")]:
    print(f"  [{'PASS' if token else 'FAIL'}] {label} login")

# 3. Student
print("\n-- 3. Student endpoints --")
if student_token:
    hs = h(student_token)
    check("GET /auth/me",         get(f"{BASE}/auth/me",          headers=hs))
    check("GET /modules",         get(f"{BASE}/modules",          headers=hs))
    check("GET /labs",            get(f"{BASE}/labs",             headers=hs))
    check("GET /progress/me",     get(f"{BASE}/progress/me",      headers=hs))
    check("GET /certificates/me", get(f"{BASE}/certificates/me",  headers=hs))
    check("GET /credentials/me",  get(f"{BASE}/credentials/me",   headers=hs))
    check("GET /competencies",    get(f"{BASE}/competencies",     headers=hs))
    check("GET /compliance",      get(f"{BASE}/compliance",       headers=hs))
    check("GET /notifications/me",get(f"{BASE}/notifications/me", headers=hs))
    check("GET /xp/leaderboard",  get(f"{BASE}/xp/leaderboard",  headers=hs))
    check("GET /portfolio/me",    get(f"{BASE}/portfolio/me",     headers=hs))
    check("GET /adaptive/me",     get(f"{BASE}/adaptive/me",      headers=hs))
    check("GET /xp/me",           get(f"{BASE}/xp/me",           headers=hs))

# 4. Instructor
print("\n-- 4. Instructor endpoints --")
if inst_token:
    hi = h(inst_token)
    check("GET /incidents",              get(f"{BASE}/incidents",             headers=hi))
    check("GET /instructor/submissions", get(f"{BASE}/instructor/submissions",headers=hi))
    check("GET /instructor/lab-report",  get(f"{BASE}/instructor/lab-report", headers=hi))
    check("GET /attendance/roster",      get(f"{BASE}/attendance/roster",     headers=hi))
    check("GET /roster",                 get(f"{BASE}/roster",                headers=hi))

# 5. Admin
print("\n-- 5. Admin endpoints --")
if admin_token:
    ha = h(admin_token)
    check("GET /admin/stats",          get(f"{BASE}/admin/stats",          headers=ha))
    check("GET /admin/users",          get(f"{BASE}/admin/users",          headers=ha))
    check("GET /admin/recent-activity",get(f"{BASE}/admin/recent-activity",headers=ha))
    check("GET /admin/cohorts",        get(f"{BASE}/admin/cohorts",        headers=ha))
    check("GET /admin/audit",          get(f"{BASE}/admin/audit",          headers=ha))
    check("GET /analytics/program",    get(f"{BASE}/analytics/program",    headers=ha))
    check("GET /admin/sites",          get(f"{BASE}/admin/sites",          headers=ha))
    check("GET /admin/inventory",      get(f"{BASE}/admin/inventory",      headers=ha))
    check("GET /admin/sage/status",    get(f"{BASE}/admin/sage/status",    headers=ha))
    check("GET /admin/sage/metrics",   get(f"{BASE}/admin/sage/metrics",   headers=ha))

# 6. Exec
print("\n-- 6. Executive endpoints --")
if exec_token:
    he = h(exec_token)
    check("GET /exec/system",      get(f"{BASE}/exec/system",      headers=he))
    check("GET /admin/sage/audit", get(f"{BASE}/admin/sage/audit", headers=he))
    check("GET /ai/sage/integrity",get(f"{BASE}/ai/sage/integrity",headers=he))

# 7. M.O.R.E.
print("\n-- 7. M.O.R.E. platform --")
if student_token:
    hs = h(student_token)
    check("GET /more/posts",  get(f"{BASE}/more/posts",  headers=hs))
    check("GET /more/needs",  get(f"{BASE}/more/needs",  headers=hs))

# 8. Role boundaries
print("\n-- 8. Role boundaries --")
if student_token:
    hs = h(student_token)
    check("/admin/users blocked for student", get(f"{BASE}/admin/users",  headers=hs), expected=403)
    check("/admin/stats blocked for student", get(f"{BASE}/admin/stats",  headers=hs), expected=403)
    check("/exec/system blocked for student", get(f"{BASE}/exec/system",  headers=hs), expected=403)
    check("/incidents blocked for student",   get(f"{BASE}/incidents",    headers=hs), expected=403)

# 9. Unauthenticated
print("\n-- 9. Unauthenticated access blocked --")
check("GET /auth/me no token",     get(f"{BASE}/auth/me"),      expected=401)
check("GET /admin/users no token", get(f"{BASE}/admin/users"),  expected=401)
check("GET /exec/system no token", get(f"{BASE}/exec/system"),  expected=401)

# 10. Registration
print("\n-- 10. New user registration --")
s = "".join(random.choices(string.ascii_lowercase, k=8))
test_email = f"testuser{s}@lcewai.org"
r = post(f"{BASE}/auth/register", json={
    "full_name": "Test Apprentice",
    "email": test_email,
    "password": "TestPass123!",
})
check("POST /auth/register", r, expected=200)
new_token = r.json().get("access_token") if r.status_code == 200 else None
if new_token:
    check("New user /auth/me",    get(f"{BASE}/auth/me",    headers=h(new_token)))
    check("New user /progress/me",get(f"{BASE}/progress/me",headers=h(new_token)))

# Summary
print(f"\n{'='*60}")
total  = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
if failed:
    print("\n  Failed tests:")
    for label, ok, code in results:
        if not ok:
            print(f"    - {label}  (got HTTP {code})")
print(f"{'='*60}\n")
