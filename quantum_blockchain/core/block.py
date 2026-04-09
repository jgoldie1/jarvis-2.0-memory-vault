from __future__ import annotations

import hashlib
import json
import time
from typing import Any


class Block:
    def __init__(
        self,
        index: int,
        transactions: list[Any],
        previous_hash: str,
        nonce: int = 0,
        timestamp: float | None = None,
    ) -> None:
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.timestamp = timestamp if timestamp is not None else time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
        }

    def calculate_hash(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
