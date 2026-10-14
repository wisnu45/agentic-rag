"""Authenticated AES-256-GCM encryption for files stored by the application."""
import base64
import binascii
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import get_settings

NONCE_LENGTH = 12
MAGIC = b"ARAG1"


class StorageEncryptionError(Exception):
    """Raised when encrypted storage is not configured or data cannot be encrypted."""


def _get_cipher() -> AESGCM:
    key_text = get_settings().file_encryption_key.strip()
    if not key_text:
        raise StorageEncryptionError(
            "FILE_ENCRYPTION_KEY is required. Generate a random 32-byte URL-safe Base64 key and configure it in .env."
        )
    try:
        key = base64.urlsafe_b64decode(key_text.encode("ascii"))
    except (ValueError, UnicodeEncodeError, binascii.Error) as exc:
        raise StorageEncryptionError("FILE_ENCRYPTION_KEY must be URL-safe Base64.") from exc
    if len(key) != 32:
        raise StorageEncryptionError("FILE_ENCRYPTION_KEY must decode to exactly 32 bytes for AES-256.")
    return AESGCM(key)


def encrypt_file(data: bytes) -> bytes:
    """Encrypt bytes with AES-256-GCM and prepend a version marker and nonce."""
    cipher = _get_cipher()
    nonce = os.urandom(NONCE_LENGTH)
    return MAGIC + nonce + cipher.encrypt(nonce, data, MAGIC)


def decrypt_file(payload: bytes) -> bytes:
    """Decrypt an encrypted payload; never return unauthenticated plaintext."""
    if len(payload) < len(MAGIC) + NONCE_LENGTH + 16 or not payload.startswith(MAGIC):
        raise StorageEncryptionError("Encrypted file header is invalid or file is not encrypted.")
    cipher = _get_cipher()
    nonce_start = len(MAGIC)
    nonce = payload[nonce_start:nonce_start + NONCE_LENGTH]
    ciphertext = payload[nonce_start + NONCE_LENGTH:]
    try:
        return cipher.decrypt(nonce, ciphertext, MAGIC)
    except Exception as exc:
        raise StorageEncryptionError("File authentication failed; key or stored data may be incorrect.") from exc
