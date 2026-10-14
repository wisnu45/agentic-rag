import base64
import secrets
from types import SimpleNamespace

import pytest

import security


def test_encrypt_decrypt_round_trip(monkeypatch):
    key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
    monkeypatch.setattr(security, "get_settings", lambda: SimpleNamespace(file_encryption_key=key))
    plaintext = b"confidential document content"

    encrypted = security.encrypt_file(plaintext)

    assert encrypted != plaintext
    assert encrypted.startswith(security.MAGIC)
    assert security.decrypt_file(encrypted) == plaintext


def test_wrong_key_fails_authentication(monkeypatch):
    key_one = base64.urlsafe_b64encode(b"a" * 32).decode("ascii")
    key_two = base64.urlsafe_b64encode(b"b" * 32).decode("ascii")
    monkeypatch.setattr(security, "get_settings", lambda: SimpleNamespace(file_encryption_key=key_one))
    encrypted = security.encrypt_file(b"secret")
    monkeypatch.setattr(security, "get_settings", lambda: SimpleNamespace(file_encryption_key=key_two))

    with pytest.raises(security.StorageEncryptionError):
        security.decrypt_file(encrypted)


def test_encryption_requires_key(monkeypatch):
    monkeypatch.setattr(security, "get_settings", lambda: SimpleNamespace(file_encryption_key=""))
    with pytest.raises(security.StorageEncryptionError):
        security.encrypt_file(b"secret")
