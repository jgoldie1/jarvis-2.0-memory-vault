from __future__ import annotations

import hashlib
import hmac
import json


class SignedSnapshot:
    def __init__(self, secret_key: str) -> None:
        self._secret_key = secret_key.encode()

    def _compute_signature(self, data: dict[str, object]) -> str:
        payload = json.dumps(data, sort_keys=True).encode()
        return hmac.new(self._secret_key, payload, hashlib.sha256).hexdigest()

    def sign(self, data: dict[str, object]) -> dict[str, object]:
        signature = self._compute_signature(data)
        return {**data, "__signature__": signature}

    def verify(self, signed_data: dict[str, object]) -> bool:
        signature = signed_data.get("__signature__")
        if not isinstance(signature, str):
            return False
        data = {k: v for k, v in signed_data.items() if k != "__signature__"}
        expected = self._compute_signature(data)
        return hmac.compare_digest(signature, expected)

    def save(self, path: str, data: dict[str, object]) -> None:
        signed = self.sign(data)
        with open(path, "w") as f:
            json.dump(signed, f)

    def load(self, path: str) -> dict[str, object]:
        with open(path) as f:
            result: dict[str, object] = json.load(f)
        return result
