"""Encrypted wallet backup using Fernet/PBKDF2."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_SALT_LENGTH = 16
_KDF_ITERATIONS = 480_000


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a password and salt using PBKDF2-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_wallet(wallet_data: dict[str, Any], password: str) -> bytes:
    """Encrypt wallet data with a password.

    Returns salt + ciphertext as a single bytes object.
    """
    salt = os.urandom(_SALT_LENGTH)
    key = _derive_key(password, salt)
    fernet = Fernet(key)
    payload = json.dumps(wallet_data).encode()
    encrypted = fernet.encrypt(payload)
    return salt + encrypted


def decrypt_wallet(data: bytes, password: str) -> dict[str, Any]:
    """Decrypt wallet data with a password.

    Raises ``cryptography.fernet.InvalidToken`` if the password is wrong.
    """
    salt = data[:_SALT_LENGTH]
    encrypted = data[_SALT_LENGTH:]
    key = _derive_key(password, salt)
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted)
    result: dict[str, Any] = json.loads(decrypted.decode())
    return result


def save_wallet(wallet_data: dict[str, Any], password: str, path: Path) -> None:
    """Encrypt wallet data and write it to *path*."""
    path.write_bytes(encrypt_wallet(wallet_data, password))


def load_wallet(password: str, path: Path) -> dict[str, Any]:
    """Read and decrypt wallet data from *path*."""
    return decrypt_wallet(path.read_bytes(), password)
