"""
Encryption utilities for storing sensitive data like database passwords.
Uses Fernet symmetric encryption.
"""
import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import get_settings

settings = get_settings()


def _get_fernet() -> Fernet:
    """
    Get Fernet instance using the encryption key from settings.
    The key is hashed to ensure it's exactly 32 bytes for Fernet.
    """
    # Hash the key to get exactly 32 bytes, then base64 encode for Fernet
    key_bytes = hashlib.sha256(settings.encryption_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_value(plain_text: str) -> str:
    """Encrypt a string value and return base64-encoded ciphertext."""
    fernet = _get_fernet()
    encrypted = fernet.encrypt(plain_text.encode())
    return encrypted.decode()


def decrypt_value(encrypted_text: str) -> str:
    """Decrypt a base64-encoded ciphertext and return plain text."""
    fernet = _get_fernet()
    decrypted = fernet.decrypt(encrypted_text.encode())
    return decrypted.decode()

