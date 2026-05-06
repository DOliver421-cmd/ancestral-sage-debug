#!/usr/bin/env bash
# Replay the curl evidence in 06_curl_password_reset_transcript.txt against
# the running preview backend.  Idempotent — creates and deletes its own
# disposable user.

set -e

API_URL="${API_URL:-$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@lcewai.org}"
ADMIN_PW="${ADMIN_PW:-Admin@LCE2026}"

echo "=== replay against $API_URL ==="

ADMIN=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PW\"}" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

EMAIL="replay-$(date +%s)@example.com"
echo "test email: $EMAIL"

CREATE=$(curl -s -X POST "$API_URL/api/admin/users" \
  -H "Authorization: Bearer $ADMIN" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"full_name\":\"Replay\",\"password\":\"Initial@1\",\"role\":\"student\"}")
UID_=$(echo "$CREATE" | python3 -c 'import sys,json;print(json.load(sys.stdin)["user"]["id"])')
echo "user id: $UID_"

echo
echo "1. forgot-password"
RESP=$(curl -s -X POST "$API_URL/api/auth/forgot-password" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\"}")
echo "   $RESP"
TOKEN=$(echo "$RESP" | python3 -c 'import sys,json;print(json.load(sys.stdin)["_dev_token"])')

echo "2. reset-password (first use, must succeed)"
curl -s -o /dev/null -w "   HTTP %{http_code}\n" \
  -X POST "$API_URL/api/auth/reset-password" \
  -H 'Content-Type: application/json' \
  -d "{\"token\":\"$TOKEN\",\"new_password\":\"Replay@2026\"}"

echo "3. login with new password"
curl -s -o /dev/null -w "   HTTP %{http_code}\n" \
  -X POST "$API_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"Replay@2026\"}"

echo "4. reset-password REUSE (must FAIL 400)"
curl -s -o /dev/null -w "   HTTP %{http_code}\n" \
  -X POST "$API_URL/api/auth/reset-password" \
  -H 'Content-Type: application/json' \
  -d "{\"token\":\"$TOKEN\",\"new_password\":\"DoesntMatter@1\"}"

echo "5. reset-password FAKE token (must FAIL 400)"
curl -s -o /dev/null -w "   HTTP %{http_code}\n" \
  -X POST "$API_URL/api/auth/reset-password" \
  -H 'Content-Type: application/json' \
  -d '{"token":"fakefakefakefakefakefakefakefake","new_password":"Whatever@1"}'

echo "6. cleanup"
curl -s -X DELETE "$API_URL/api/admin/users/$UID_" \
  -H "Authorization: Bearer $ADMIN" -o /dev/null

echo "=== done ==="
