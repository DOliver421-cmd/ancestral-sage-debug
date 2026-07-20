#!/bin/bash
set -e

# Docker entrypoint script that:
# 1. Handles PORT environment variable with fallback to 8080
# 2. Properly passes signals (SIGTERM, SIGINT) to Python for graceful shutdown
# 3. Launches uvicorn as PID 1 so it receives signals directly

PORT=${PORT:-8080}

echo "Starting Ancestral Sage backend on port $PORT..."
echo "PYTHONPATH: $PYTHONPATH"
echo "SERVE_FRONTEND: $SERVE_FRONTEND"

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$PORT"
