"""pytest bootstrap — loads /app/frontend/.env so tests can read REACT_APP_BACKEND_URL.

Also exposes BASE_URL as an env var if the test files ever fall back to it.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# conftest.py is at /app/backend/tests/conftest.py.
# parents[0] = /app/backend/tests
# parents[1] = /app/backend
# parents[2] = /app  ← repo root, contains backend/ and frontend/
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "backend" / ".env")
load_dotenv(ROOT / "frontend" / ".env")

# Guarantee REACT_APP_BACKEND_URL is set; fall back to localhost if neither file
# provided it (CI environments, etc.).
if not os.environ.get("REACT_APP_BACKEND_URL"):
    os.environ["REACT_APP_BACKEND_URL"] = "http://localhost:8001"
