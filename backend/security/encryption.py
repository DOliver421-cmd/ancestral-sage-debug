"""
Data Encryption Module

Encrypts sensitive data at rest: bank accounts, API keys, tax IDs, etc.
Uses Fernet (AES-128 in CBC mode with HMAC authentication).
"""

import os
from cryptography.fernet import Fernet, InvalidToken
import logging

logger = logging.getLogger(__name__)


class DataEncryption:
    """Encrypt/decrypt sensitive data at rest"""

    def __init__(self, encryption_key: str = None):
        """
        Initialize with encryption key.

        Args:
            encryption_key: 32-byte base64-encoded key (or env var ENCRYPTION_KEY)

        Usage:
            # Production: set ENCRYPTION_KEY env var
            cipher = DataEncryption()

            # Testing: provide key directly
            cipher = DataEncryption(key)
        """
        self.key = encryption_key or os.environ.get("ENCRYPTION_KEY")

        if not self.key:
            raise ValueError(
                "ENCRYPTION_KEY not set. Generate with: "
                "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

        try:
            self.cipher = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
        except Exception as e:
            raise ValueError(f"Invalid ENCRYPTION_KEY format: {e}")

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext to ciphertext"""
        if not plaintext:
            return None

        try:
            ciphertext = self.cipher.encrypt(plaintext.encode())
            return ciphertext.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError("Encryption failed")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext to plaintext"""
        if not ciphertext:
            return None

        try:
            plaintext = self.cipher.decrypt(ciphertext.encode())
            return plaintext.decode()
        except InvalidToken:
            logger.error("Decryption failed: invalid token (wrong key?)")
            raise ValueError("Decryption failed: invalid token")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed")

    def encrypt_field(self, value: str, field_name: str = None) -> str:
        """Encrypt a field, with optional field name for logging"""
        try:
            return self.encrypt(value)
        except Exception as e:
            logger.error(f"Failed to encrypt {field_name or 'field'}: {e}")
            raise

    def decrypt_field(self, encrypted_value: str, field_name: str = None) -> str:
        """Decrypt a field, with optional field name for logging"""
        try:
            return self.decrypt(encrypted_value)
        except Exception as e:
            logger.error(f"Failed to decrypt {field_name or 'field'}: {e}")
            raise


# Singleton instance (initialized on first use)
_cipher_instance = None


def get_cipher() -> DataEncryption:
    """Get global cipher instance"""
    global _cipher_instance
    if not _cipher_instance:
        _cipher_instance = DataEncryption()
    return _cipher_instance


# Helper functions
def encrypt(value: str) -> str:
    """Convenience function: encrypt a value"""
    return get_cipher().encrypt(value)


def decrypt(value: str) -> str:
    """Convenience function: decrypt a value"""
    return get_cipher().decrypt(value)


# Field encryption handlers
class EncryptedFields:
    """Maps of which document fields should be encrypted"""

    PAYOUT_ACCOUNTS = {"bankAccount", "bankRoutingNumber", "accountHolderName"}
    USERS = {"ssn", "taxId"}
    API_KEYS = {"stripeSecretKey", "paypalSecret", "apiToken"}
    CONFIG = {"databasePassword", "emailPassword", "slackToken"}


def encrypt_payout_account(account_dict: dict) -> dict:
    """Encrypt sensitive payout account fields"""
    cipher = get_cipher()
    encrypted = account_dict.copy()

    for field in EncryptedFields.PAYOUT_ACCOUNTS:
        if field in encrypted and encrypted[field]:
            encrypted[field] = cipher.encrypt_field(
                encrypted[field],
                field_name=f"payout_account.{field}"
            )

    return encrypted


def decrypt_payout_account(account_dict: dict) -> dict:
    """Decrypt sensitive payout account fields"""
    cipher = get_cipher()
    decrypted = account_dict.copy()

    for field in EncryptedFields.PAYOUT_ACCOUNTS:
        if field in decrypted and decrypted[field]:
            try:
                decrypted[field] = cipher.decrypt_field(
                    decrypted[field],
                    field_name=f"payout_account.{field}"
                )
            except ValueError:
                # Field might not be encrypted yet (during migration)
                pass

    return decrypted


def mask_sensitive_field(value: str, field_type: str = "account") -> str:
    """
    Mask sensitive fields for display (last 4 digits/chars visible).

    Args:
        value: The full value
        field_type: "account", "ssn", "card", "token", etc.

    Returns:
        Masked value
    """
    if not value:
        return None

    if field_type == "account":
        return f"****{value[-4:]}"  # Last 4 digits of account
    elif field_type == "ssn":
        return f"***-**-{value[-4:]}"  # Last 4 digits
    elif field_type == "card":
        return f"****{value[-4:]}"  # Last 4 digits of card
    elif field_type == "token":
        return f"{value[:4]}...{value[-4:]}"  # First and last 4 chars
    else:
        return f"***{value[-1:]}"  # Just last character


# MongoDB encryption at application level (for queries)
def build_encrypted_filter(field: str, plaintext: str) -> dict:
    """
    Build a MongoDB filter with encrypted value.

    Usage:
        # Find user by encrypted SSN
        filter_query = build_encrypted_filter("ssn", "123-45-6789")
        user = await db.users.find_one(filter_query)
    """
    encrypted = encrypt(plaintext)
    return {field: encrypted}
