"""Regression tests for fail-closed security hardening (2026-09-03).

Covers:
  - byok.decrypt_key: a stored key that cannot be decrypted (wrong vault key,
    legacy plaintext row, empty value, unavailable vault) must yield None and
    never be handed to a provider as a bearer token.
  - legal_compliance.is_human_officer: the allow-list is authoritative — any
    authenticated role that is not listed must be denied (the previous
    `or bool(role)` let every non-empty role pass).
"""

import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cryptography.fernet import Fernet  # noqa: E402

from byok import decrypt_key  # noqa: E402
from legal_compliance import is_human_officer  # noqa: E402

import keyvault  # noqa: E402


class _User:
    def __init__(self, role, is_ai=False):
        self.role = role
        self.is_ai = is_ai
        self.actor_type = "ai" if is_ai else "human"


class _Vault:
    """Minimal Fernet-shaped vault for monkeypatching keyvault.get_fernet."""

    def __init__(self, fernet):
        self._f = fernet

    def encrypt(self, data):
        return self._f.encrypt(data)

    def decrypt(self, data):
        return self._f.decrypt(data)


# ── M3: is_human_officer allow-list is authoritative ─────────────────────────

def test_officer_gate_requires_listed_role():
    assert is_human_officer(_User("admin"), {"admin", "executive_admin"})
    assert is_human_officer(_User("executive_admin"), {"admin", "executive_admin"})


def test_officer_gate_denies_unlisted_or_missing():
    # The previous implementation returned True for ANY non-empty role.
    assert not is_human_officer(_User("student"), {"admin"})
    assert not is_human_officer(_User("instructor"), {"admin", "executive_admin"})
    assert not is_human_officer(_User("admin"), None)
    assert not is_human_officer(_User("admin"), set())
    assert not is_human_officer(None, {"admin"})
    assert not is_human_officer(_User(""), {"admin"})


def test_officer_gate_denies_ai_actors():
    assert not is_human_officer(_User("admin", is_ai=True), {"admin"})


# ── M2: decrypt_key fails closed ─────────────────────────────────────────────

@contextlib.contextmanager
def _with_vault(fernet_or_none):
    orig = keyvault.get_fernet

    def patch():
        return None if fernet_or_none is None else _Vault(fernet_or_none)

    keyvault.get_fernet = patch
    try:
        yield
    finally:
        keyvault.get_fernet = orig


def test_decrypt_key_returns_plaintext_with_matching_vault():
    k = Fernet.generate_key()
    cipher = Fernet(k).encrypt(b"sk-live-key").decode()  # stored rows are str
    with _with_vault(Fernet(k)):
        assert decrypt_key(cipher) == "sk-live-key"


def test_decrypt_key_never_returns_ciphertext_on_wrong_vault_key():
    k1 = Fernet.generate_key()
    k2 = Fernet.generate_key()
    cipher = Fernet(k1).encrypt(b"sk-secret").decode()
    with _with_vault(Fernet(k2)):
        assert decrypt_key(cipher) is None


def test_decrypt_key_skips_legacy_plaintext_rows():
    # A legacy plaintext row cannot be Fernet-decrypted: it must be skipped,
    # never echoed back as if it were a usable key.
    with _with_vault(Fernet(Fernet.generate_key())):
        assert decrypt_key("legacy-plaintext-key") is None


def test_decrypt_key_handles_empty_and_unavailable_vault():
    with _with_vault(None):
        assert decrypt_key("anything") is None
        assert decrypt_key("") is None