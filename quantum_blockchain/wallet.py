from __future__ import annotations

import base64
import json
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptedWallet:
    def __init__(self, password: str) -> None:
        self._password = password
        self._salt: bytes = os.urandom(16)
        self._key: bytes = self._derive_key(password, self._salt)
        self._fernet = Fernet(self._key)

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def encrypt(self, data: dict[str, object]) -> bytes:
        return self._fernet.encrypt(json.dumps(data).encode())

    def decrypt(self, token: bytes) -> dict[str, object]:
        result: dict[str, object] = json.loads(self._fernet.decrypt(token).decode())
        return result

    def save(self, path: str, data: dict[str, object]) -> None:
        token = self.encrypt(data)
        payload = {
            "salt": base64.urlsafe_b64encode(self._salt).decode(),
            "token": token.decode(),
        }
        with open(path, "w") as f:
            json.dump(payload, f)

    def load(self, path: str) -> dict[str, object]:
        with open(path) as f:
            payload: dict[str, object] = json.load(f)
        salt = base64.urlsafe_b64decode(str(payload["salt"]))
        token = str(payload["token"]).encode()
        key = self._derive_key(self._password, salt)
        fernet = Fernet(key)
        result: dict[str, object] = json.loads(fernet.decrypt(token).decode())
        return result
