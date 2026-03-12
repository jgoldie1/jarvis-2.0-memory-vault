"""Encrypted wallet with Fernet/PBKDF2 backup and restore."""

from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_SALT_LEN = 16
_KDF_ITERATIONS = 100_000


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a URL-safe base64-encoded 32-byte key from *password* and *salt*."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


class Wallet:
    """A simple wallet identified by an *address* with a *balance*."""

    def __init__(self, address: str, balance: float = 0.0) -> None:
        self.address = address
        self.balance = balance

    def backup(self, path: str, password: str) -> None:
        """Encrypt and write wallet data to *path* using *password*."""
        salt = os.urandom(_SALT_LEN)
        key = _derive_key(password, salt)
        fernet = Fernet(key)
        plaintext = f"{self.address}:{self.balance}".encode()
        token = fernet.encrypt(plaintext)
        with open(path, "wb") as fh:
            fh.write(salt + token)

    @classmethod
    def restore(cls, path: str, password: str) -> Wallet:
        """Decrypt wallet data from *path* using *password* and return a new Wallet."""
        with open(path, "rb") as fh:
            raw = fh.read()
        salt = raw[:_SALT_LEN]
        token = raw[_SALT_LEN:]
        key = _derive_key(password, salt)
        fernet = Fernet(key)
        plaintext = fernet.decrypt(token).decode()
        address, balance_str = plaintext.split(":", 1)
        return cls(address=address, balance=float(balance_str))
