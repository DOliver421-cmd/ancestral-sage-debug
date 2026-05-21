@echo off
:: ============================================================
:: WAI-Institute / M.O.R.E. Help Center — HOME BACKUP SERVER
:: ============================================================
:: This script starts the full backend on your home PC.
:: When Railway goes down, this takes over as the live server.
::
:: SETUP (one-time, ~15 minutes):
::
:: 1. Install Python 3.11+  →  https://python.org/downloads
::    During install: check "Add Python to PATH"
::
:: 2. Install dependencies:
::    cd backend
::    pip install -r requirements.txt
::
:: 3. Copy backend\.env from Railway (or create one with same vars)
::    Required vars:  MONGO_URL, DB_NAME, JWT_SECRET, ANTHROPIC_API_KEY
::    Add these:      SERVE_FRONTEND=1
::                    BACKUP_ORIGIN=https://YOUR-TUNNEL.trycloudflare.com
::                    MONGO_BACKUP_URL=mongodb+srv://... (Atlas URI — optional)
::
:: 4. Build the React frontend:
::    cd frontend
::    npm install
::    npm run build
::
:: 5. Install Cloudflare Tunnel (free, no port forwarding needed):
::    Download cloudflared.exe from:
::    https://github.com/cloudflare/cloudflared/releases/latest
::    Put cloudflared.exe in the same folder as this script.
::
:: 6. Run this script. It will:
::    a. Start the FastAPI backend on port 8001
::    b. Start a Cloudflare tunnel
::    c. Print the public URL — share it with users during outages
::
:: DURING AN OUTAGE:
::    Double-click this file. Wait ~30 seconds.
::    The URL printed in the console is your live backup address.
::    Users go to: https://YOUR-TUNNEL.trycloudflare.com
::
:: ============================================================

setlocal EnableDelayedExpansion

echo.
echo  ============================================================
echo   WAI-INSTITUTE BACKUP SERVER — Starting up...
echo  ============================================================
echo.

:: Set working directory to script location
cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org/downloads
    echo         Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

:: Check backend directory
if not exist "backend\server.py" (
    echo [ERROR] Cannot find backend\server.py
    echo         Run this script from the project root directory.
    pause
    exit /b 1
)

:: Check .env
if not exist "backend\.env" (
    echo [WARNING] backend\.env not found.
    echo           Copy your Railway environment variables to backend\.env
    echo           Required: MONGO_URL, DB_NAME, JWT_SECRET, ANTHROPIC_API_KEY
    echo           Add:      SERVE_FRONTEND=1
    echo.
)

:: Set home server environment overrides
set SERVE_FRONTEND=1
set PORT=8001

:: Start backend in a new window
echo [1/2] Starting FastAPI backend on port 8001...
start "WAI Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"

:: Wait for backend to initialize
echo       Waiting for backend to start (10 seconds)...
timeout /t 10 /nobreak >nul

:: Start Cloudflare tunnel
if exist "cloudflared.exe" (
    echo [2/2] Starting Cloudflare tunnel...
    echo.
    echo  ============================================================
    echo   Your backup server URL will appear below.
    echo   Share this URL with users when Railway is down.
    echo   It looks like: https://xxxx-xx-xx-xxx.trycloudflare.com
    echo  ============================================================
    echo.
    cloudflared tunnel --url http://localhost:8001
) else (
    echo [2/2] Cloudflare tunnel not found (cloudflared.exe missing).
    echo       Your server is running locally at: http://localhost:8001
    echo.
    echo       To expose it to the internet (FREE):
    echo       1. Download cloudflared.exe from:
    echo          https://github.com/cloudflare/cloudflared/releases/latest
    echo       2. Place cloudflared.exe in this folder
    echo       3. Run this script again
    echo.
    echo       OR use ngrok (free tier):
    echo          ngrok http 8001
    echo.
    pause
)
