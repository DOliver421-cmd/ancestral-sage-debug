#!/bin/sh
set -e
BACKEND_URL="${BACKEND_URL:-http://localhost:8080}"
BACKEND_URL="${BACKEND_URL%/}"
BACKEND_HOST=$(echo "$BACKEND_URL" | sed 's|^https\?://||' | cut -d'/' -f1)
export BACKEND_URL
export BACKEND_HOST
TARGET_PORT=${PORT:-8080}
exec uvicorn backend.server:app --host 0.0.0.0 --port "$TARGET_PORT"
