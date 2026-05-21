#!/bin/sh
set -e

# ── Substitute BACKEND_URL in the nginx config template ──────────────────────
# Using the explicit variable list form of envsubst so that nginx variables
# like $uri, $host, $remote_addr are left untouched in the output config.

# Default: same-origin (should not happen in production, but prevents a broken
# nginx config if BACKEND_URL is somehow omitted from Railway env vars).
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

# Strip trailing slash so proxy_pass URLs are well-formed
BACKEND_URL="${BACKEND_URL%/}"

export BACKEND_URL

echo "nginx proxy: /api/ → ${BACKEND_URL}/api/"

envsubst '${BACKEND_URL}' \
    < /etc/nginx/templates/default.conf.template \
    > /etc/nginx/conf.d/default.conf

exec "$@"
