"""Regression tests for the startup encryption-vault initialization.

Root cause: keyvault.init(db) is the only code path that can load a persisted
Fernet secret from MongoDB or auto-generate + persist one. It was never called
from the server startup sequence, so get_fernet() could only ever read
PROVIDER_KEY_ENCRYPTION_SECRET from the environment. A deployment without that
env var ended up with _FERNET is None, and every provider-key / BYOK save was
refused with HTTP 503 "encryption_unavailable".
"""
import asyncio
import inspect
import re
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _server_source() -> str:
    return (BACKEND / "server.py").read_text(encoding="utf-8")


# A stable, valid Fernet key representing an already-persisted secret in MongoDB.
from cryptography.fernet import Fernet  # noqa: E402

_SECRET = Fernet.generate_key().decode()


class _FakeCollection:
    def __init__(self):
        self.saved = None

    async def find_one(self, _query):
        return {"_id": "fernet_secret", "value": _SECRET}

    async def update_one(self, _query, update, upsert=False):
        self.saved = update["$set"].get("value")


class _FakeDB:
    def __init__(self):
        self.platform_config = _FakeCollection()
        self.user_byok_keys = _FakeCollection()


class TestKeyvaultIsInitializedAtStartup:
    def test_server_source_awaits_keyvault_init(self):
        """server.py must actually await keyvault.init(...) during startup."""
        src = _server_source()
        assert re.search(r"await\s+_?keyvault\.init\s*\(", src), (
            "server.py never awaits keyvault.init(...) — the MongoDB-persisted / "
            "auto-generated encryption secret path is dead and provider-key saves "
            "will be refused whenever PROVIDER_KEY_ENCRYPTION_SECRET is unset."
        )

    def test_keyvault_init_is_inside_the_startup_impl(self):
        """The call must live in _on_startup_impl, not somewhere unreachable."""
        src = _server_source()
        start = src.find("async def _on_startup_impl(")
        assert start != -1, "_on_startup_impl not found in server.py"
        body = src[start : start + 20000]
        assert re.search(r"await\s+_?keyvault\.init\s*\(", body), (
            "keyvault.init() is not called inside _on_startup_impl()."
        )

    def test_init_failure_is_non_fatal(self):
        """A vault problem must not take the whole server down at boot."""
        src = _server_source()
        idx = src.find("keyvault.init(db)")
        assert idx != -1
        window = src[max(0, idx - 600) : idx + 400]
        assert "except Exception" in window, (
            "keyvault.init() must be wrapped in try/except so a vault failure "
            "does not abort startup."
        )


class TestKeyvaultResolvesWithoutEnvVar:
    def test_get_fernet_uses_persisted_secret_when_env_absent(self, monkeypatch):
        """With no env var set, init() must still yield a working Fernet."""
        import keyvault

        monkeypatch.delenv("PROVIDER_KEY_ENCRYPTION_SECRET", raising=False)
        monkeypatch.setattr(keyvault, "_FERNET", None)
        monkeypatch.setattr(keyvault, "_SOURCE", "uninitialized")

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(keyvault.init(_FakeDB()))
        finally:
            loop.close()

        assert keyvault.get_fernet() is not None, (
            "keyvault.init() must resolve a cipher with no env var set."
        )
        assert keyvault.source() in ("mongodb", "generated")
        # Round-trip: what we save must be readable.
        token = keyvault.get_fernet().encrypt(b"sk-live-test-key")
        assert keyvault.get_fernet().decrypt(token) == b"sk-live-test-key"


class TestSaveByokKeyRefusesLoudly:
    def test_byok_save_raises_when_no_cipher(self, monkeypatch):
        """The refusal must stay loud — never silently store plaintext."""
        import byok
        import keyvault

        monkeypatch.delenv("PROVIDER_KEY_ENCRYPTION_SECRET", raising=False)
        monkeypatch.setattr(keyvault, "_FERNET", None)
        monkeypatch.setattr(keyvault, "_SOURCE", "unavailable")

        loop = asyncio.new_event_loop()
        try:
            with pytest.raises(ValueError) as exc:
                loop.run_until_complete(
                    byok.save_byok_key(
                        _FakeDB(), "user-1", "groq", "gsk-should-never-be-plain"
                    )
                )
            assert "encryption_unavailable" in str(exc.value)
        finally:
            loop.close()

    def test_byok_save_succeeds_after_init_without_env_var(self, monkeypatch):
        """The user-visible outcome: keys save once startup initialized the vault."""
        import byok
        import keyvault

        monkeypatch.delenv("PROVIDER_KEY_ENCRYPTION_SECRET", raising=False)
        monkeypatch.setattr(keyvault, "_FERNET", None)
        monkeypatch.setattr(keyvault, "_SOURCE", "uninitialized")

        loop = asyncio.new_event_loop()
        try:
            db = _FakeDB()
            loop.run_until_complete(keyvault.init(db))

            saved = {}
            user_keys = db.user_byok_keys

            async def _update_one(_q, update, upsert=False):
                saved.update(update["$set"])

            user_keys.update_one = _update_one  # type: ignore[assignment]

            result = loop.run_until_complete(
                byok.save_byok_key(db, "user-1", "groq", "gsk-live-abc123")
            )
        finally:
            loop.close()

        assert result, "save_byok_key returned nothing"
        # Stored value must be ciphertext, not the plaintext key.
        assert saved["encrypted_key"] != "gsk-live-abc123"
        assert "gsk-live-" not in saved["encrypted_key"]
        # And it must round-trip back to the original.
        assert byok.decrypt_key(saved["encrypted_key"]) == "gsk-live-abc123"


def test_init_is_async_and_takes_db():
    import keyvault

    sig = inspect.signature(keyvault.init)
    assert inspect.iscoroutinefunction(keyvault.init)
    assert list(sig.parameters) == ["db"]
