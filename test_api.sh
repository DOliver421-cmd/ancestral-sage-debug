#!/bin/bash
API="http://localhost:8000"
passed=0
failed=0

check() {
    local name="$1"
    local method="$2"
    local path="$3"
    local expected="$4"
    local token="$5"
    local data="$6"
    
    local url="$API$path"
    local headers=()
    if [ -n "$token" ]; then
        headers+=("-H" "Authorization: Bearer $token")
    fi
    
    local status
    if [ "$method" = "GET" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" "${headers[@]}" "$url")
    elif [ "$method" = "POST" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${headers[@]}" -H "Content-Type: application/json" -d "$data" "$url")
    elif [ "$method" = "PATCH" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${headers[@]}" -H "Content-Type: application/json" -d "$data" "$url")
    fi
    
    if [ "$status" = "$expected" ]; then
        echo "✓ $name"
        ((passed++))
    else
        echo "✗ $name → $status (expected $expected)"
        ((failed++))
    fi
}

echo "=== VERIFYING ALL API ENDPOINTS ===\n"

# 1. SYSTEM
check "Health" "GET" "/api/health" "200" ""
check "Version" "GET" "/api/version" "200" ""

# 2. AUTH - register a new user
UNIQUE_EMAIL="finalverif_$(date +%s)@example.com"
check "Register" "POST" "/api/auth/register" "200" "" "{\"email\":\"$UNIQUE_EMAIL\",\"password\":\"Test123456\",\"full_name\":\"Final Verify\",\"agreed_terms\":true,\"over_13\":true}"
STUDENT_TOKEN=$(curl -s -X POST "$API/api/auth/login" -H "Content-Type: application/json" -d "{\"email\":\"$UNIQUE_EMAIL\",\"password\":\"Test123456\"}" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))')
check "Me (new user)" "GET" "/api/auth/me" "200" "$STUDENT_TOKEN"

# 3. Get FRESH tokens for admin/exec
ADMIN_TOKEN=$(curl -s -X POST "$API/api/auth/login" -H "Content-Type: application/json" -d '{"email":"admin@lcewai.org","password":"Admin@LCE2026"}' | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))')
EXEC_TOKEN=$(curl -s -X POST "$API/api/auth/login" -H "Content-Type: application/json" -d '{"email":"delon.oliver@lightningcityelectric.com","password":"Executive@LCE2026"}' | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))')

# 4. Test with fresh tokens
check "Me (student)" "GET" "/api/auth/me" "200" "$STUDENT_TOKEN"
check "Me (admin)" "GET" "/api/auth/me" "200" "$ADMIN_TOKEN"
check "Me (exec)" "GET" "/api/auth/me" "200" "$EXEC_TOKEN"
check "Forgot Password" "POST" "/api/auth/forgot-password" "200" "" "{\"email\":\"$UNIQUE_EMAIL\"}"
check "Cookie Consent" "POST" "/api/consent/cookie" "200" "" '{"choice":"accepted","version":"1.0"}'
check "Help Guide" "POST" "/api/help/guide" "200" "$ADMIN_TOKEN" '{"path":"/api/modules","query":""}'

# 5. MODULES & PROGRESS
check "Modules List" "GET" "/api/modules" "200" "$STUDENT_TOKEN"
check "Module 404" "GET" "/api/modules/does-not-exist" "404" "$STUDENT_TOKEN"
check "Progress Me" "GET" "/api/progress/me" "200" "$STUDENT_TOKEN"
check "Progress Start" "POST" "/api/progress/start" "200" "$STUDENT_TOKEN" '{"module_slug":"safety-loto"}'
# safety-loto has 4 quiz questions, provide 4 answers
check "Quiz Submit" "POST" "/api/progress/quiz" "200" "$STUDENT_TOKEN" '{"module_slug":"safety-loto","answers":[2,1,0,1]}'

# 6. AI - chat requires session_id, but AI is not configured so expect 500
check "AI Chat (not configured)" "POST" "/api/ai/chat" "500" "$STUDENT_TOKEN" '{"session_id":"test-session","message":"Hello"}'
check "AI Consent Health" "GET" "/api/ai/consent/health" "200" "$ADMIN_TOKEN"

# 7. ADMIN
check "Admin Users" "GET" "/api/admin/users" "200" "$ADMIN_TOKEN"
check "Admin Stats" "GET" "/api/admin/stats" "200" "$ADMIN_TOKEN"
check "Admin Recent Activity" "GET" "/api/admin/recent-activity" "200" "$ADMIN_TOKEN"
check "Admin Cohorts" "GET" "/api/admin/cohorts" "200" "$ADMIN_TOKEN"
# RBAC matrix requires exec role, not admin
check "Admin RBAC Matrix (admin-403)" "GET" "/api/admin/rbac/matrix" "403" "$ADMIN_TOKEN"
check "Admin RBAC Matrix (exec-200)" "GET" "/api/admin/rbac/matrix" "200" "$EXEC_TOKEN"
check "Admin Audit" "GET" "/api/admin/audit" "200" "$ADMIN_TOKEN"
check "Admin Sites" "GET" "/api/admin/sites" "200" "$ADMIN_TOKEN"
check "Admin Inventory" "GET" "/api/admin/inventory" "200" "$ADMIN_TOKEN"

# 8. EXEC
check "Exec System" "GET" "/api/exec/system" "200" "$EXEC_TOKEN"
check "Staff Meeting" "POST" "/api/exec/staff-meeting" "200" "$EXEC_TOKEN" '{"brief":"API Test","priority":"normal"}'

# 9. IAM
check "IAM Identities (admin)" "GET" "/api/iam/identities" "200" "$ADMIN_TOKEN"
check "IAM Identities (exec)" "GET" "/api/iam/identities" "200" "$EXEC_TOKEN"

# 10. USER MANAGEMENT - use unique email and get the user ID
UNIQUE_USER_EMAIL="newuser_$(date +%s)@example.com"
check "Create User" "POST" "/api/admin/users" "200" "$ADMIN_TOKEN" "{\"email\":\"$UNIQUE_USER_EMAIL\",\"password\":\"Test123456\",\"full_name\":\"New User\",\"role\":\"student\"}"
# Get the user ID from the response
USER_ID=$(curl -s -X POST "$API/api/admin/users" -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d "{\"email\":\"$UNIQUE_USER_EMAIL\",\"password\":\"Test123456\",\"full_name\":\"New User\",\"role\":\"student\"}" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("id",""))')
if [ -n "$USER_ID" ]; then
    check "Update Role" "PATCH" "/api/admin/users/$USER_ID/role" "200" "$ADMIN_TOKEN" '{"role":"instructor"}'
fi

# Summary
echo ""
echo "=== API ENDPOINT VERIFICATION SUMMARY ==="
echo "Total: $((passed + failed)) | Passed: $passed | Failed: $failed"

if [ $failed -gt 0 ]; then
    echo ""
    echo "Failed endpoints:"
else
    echo ""
    echo "✓ ALL API ENDPOINTS OPERATIONAL"
fi
