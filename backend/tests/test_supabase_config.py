import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_supabase_module_initializes_without_env(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    import app.core.supabase as supabase_module

    importlib.reload(supabase_module)

    assert supabase_module.is_supabase_available() is False
    assert supabase_module.get_supabase_client() is None


def test_supabase_module_initializes_with_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    import app.core.supabase as supabase_module

    importlib.reload(supabase_module)

    assert supabase_module.is_supabase_available() is True
