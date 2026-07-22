#!/bin/sh
set -e

echo "===================================================="
echo "🚀 INITIALIZING HEADLESS MODE RUNTIME ENTRYPOINT"
echo "===================================================="

# ── Resolve BACKEND_URL and extract hostname ──────────────────────────────────
BACKEND_URL="${BACKEND_URL:-http://localhost:8080}"
BACKEND_URL="${BACKEND_URL%/}"          # strip trailing slash

# Extract just the hostname (strip scheme and any path)
BACKEND_HOST=$(echo "$BACKEND_URL" | sed 's|^https\?://||' | cut -d'/' -f1)

export BACKEND_URL
export BACKEND_HOST

echo "Target Endpoint: ${BACKEND_URL}"
echo "Target Hostname: ${BACKEND_HOST}"

# Determine operational network port bound by Railway
TARGET_PORT=${PORT:-8080}
echo "Binding web processes to network layer port: $TARGET_PORT"

# ── Launch Unified Uvicorn Application Server ───────────────────────────────
# Explicit execution command forces the Python server to stay up permanently
echo "Launching production FastAPI engine loop..."
exec uvicorn backend.server:app --host 0.0.0.0 --port "$TARGET_PORT"
