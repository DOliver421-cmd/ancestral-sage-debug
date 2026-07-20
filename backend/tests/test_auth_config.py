import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))


def test_jwt_secret_has_fallback_when_missing(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    import app.config as config
    config = importlib.reload(config)
    assert isinstance(config.JWT_SECRET, str) and len(config.JWT_SECRET) > 0
