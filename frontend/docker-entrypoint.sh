#!/bin/sh
set -e

echo "===================================================="
echo "🚀 INITIALIZING SYSTEM CLEAN SCRUB RUNTIME WORKER"
echo "===================================================="

# Strip trailing paths or slashes from backend URL strings
BACKEND_URL="${BACKEND_URL:-http://localhost:8080}"
BACKEND_URL="${BACKEND_URL%/}"

BACKEND_HOST=$(echo "$BACKEND_URL" | sed 's|^https\?://||' | cut -d'/' -f1)

export BACKEND_URL
export BACKEND_HOST

# Dynamically map incoming execution port variables passed by Railway
TARGET_PORT=${PORT:-8080}
echo "System targeting binding port: $TARGET_PORT"

# Clean up any un-serialized manifest cache variables if they exist
if [ -f "/app/memory/project_state.json.tmp" ]; then
    rm -f /app/memory/project_state.json.tmp
fi

echo "Launching production FastAPI engine loop..."
exec uvicorn backend.server:app --host 0.0.0.0 --port "$TARGET_PORT"
