#!/usr/bin/env bash
#
# daytona-dev.sh — hot-reload dev mode for the Daytona workspace.
#
# Starts Mongo + the FastAPI backend (API only, on :8080) and the CRA dev
# server (on :3000). The dev SPA calls the backend at http://localhost:8080
# (both ports are forwarded by Daytona), so /api works with no CORS and no
# rebuild. Edit backend/*.py or frontend/src/* and see changes live.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

mkdir -p /data/db
mongod --dbpath /data/db --bind_ip 127.0.0.1 --fork --logpath /var/log/mongod.log || true

# Backend API (--reload for hot reload), SPA served separately by CRA.
cd "$REPO_ROOT/backend"
SERVE_FRONTEND=0 PORT=8080 MONGO_URL=mongodb://localhost:27017/wai \
  nohup uvicorn server:app --host 0.0.0.0 --port 8080 --reload \
  > /var/log/backend.log 2>&1 & disown

echo "Backend API:  http://localhost:8080  (docs at /docs)"
echo "Dev SPA:      http://localhost:3000"
echo "Backend log:  tail -f /var/log/backend.log"

cd "$REPO_ROOT/frontend"
REACT_APP_BACKEND_URL=http://localhost:8080 npm start
