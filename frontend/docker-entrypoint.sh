#!/bin/sh
set -e

# ── Resolve BACKEND_URL and extract hostname ──────────────────────────────────
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
BACKEND_URL="${BACKEND_URL%/}"          # strip trailing slash

# Extract just the hostname (strip scheme and any path)
# e.g. https://ancestral-sage-debug-production.up.railway.app → ancestral-sage-debug-production.up.railway.app
BACKEND_HOST=$(echo "$BACKEND_URL" | sed 's|^https\?://||' | cut -d'/' -f1)

export BACKEND_URL
export BACKEND_HOST

echo "nginx proxy: /api/ → ${BACKEND_URL}/api/  (Host: ${BACKEND_HOST})"

# ── Write nginx config from template ─────────────────────────────────────────
# Substitutes only ${BACKEND_URL} and ${BACKEND_HOST}.
# All other nginx variables ($uri, $remote_addr, etc.) are left intact.
envsubst '${BACKEND_URL} ${BACKEND_HOST}' \
    < /etc/nginx/templates/default.conf.template \
    > /etc/nginx/conf.d/default.conf

exec "$@"
