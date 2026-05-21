#!/usr/bin/env bash
# ============================================================
# WAI-Institute / M.O.R.E. Help Center — HOME BACKUP SERVER
# Linux / macOS / WSL version
# ============================================================
# Same as start_backup_server.bat but for bash environments.
# Run: chmod +x start_backup_server.sh && ./start_backup_server.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " ============================================================"
echo "  WAI-INSTITUTE BACKUP SERVER — Starting up..."
echo " ============================================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found. Install Python 3.11+ first."
    exit 1
fi

# Check backend
if [ ! -f "backend/server.py" ]; then
    echo "[ERROR] backend/server.py not found. Run from project root."
    exit 1
fi

# Export home-server env overrides
export SERVE_FRONTEND=1
export PORT=8001

# Start backend
echo "[1/2] Starting FastAPI backend on port 8001..."
cd "$SCRIPT_DIR/backend"
python3 -m uvicorn server:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!
echo "      Backend PID: $BACKEND_PID"
echo "      Waiting 10 seconds for startup..."
sleep 10

cd "$SCRIPT_DIR"

# Start Cloudflare tunnel
if command -v cloudflared &>/dev/null; then
    echo "[2/2] Starting Cloudflare tunnel..."
    echo ""
    echo " ============================================================"
    echo "  Your backup URL appears below. Share it during outages."
    echo "  Format: https://xxxx-xx-xx-xxx.trycloudflare.com"
    echo " ============================================================"
    echo ""
    cloudflared tunnel --url http://localhost:8001
elif [ -f "./cloudflared" ]; then
    echo "[2/2] Starting Cloudflare tunnel (local binary)..."
    ./cloudflared tunnel --url http://localhost:8001
else
    echo "[2/2] cloudflared not found."
    echo "      Server is live at: http://localhost:8001"
    echo ""
    echo "      To get a public URL (free):"
    echo "      curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared"
    echo "      chmod +x cloudflared"
    echo "      ./cloudflared tunnel --url http://localhost:8001"
    echo ""
    echo "      OR: ngrok http 8001"
    echo ""
    wait $BACKEND_PID
fi
