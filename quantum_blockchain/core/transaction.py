from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Transaction:
    sender: str
    receiver: str
    amount: float
    memo: str = ""
    status: str = "PENDING"
    timestamp: float | None = None
    signature: str = ""
    public_key: str = ""

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = time.time()

    def signing_payload(self) -> str:
        return (
            f"{self.sender}|{self.receiver}|{self.amount}|"
            f"{self.memo}|{self.timestamp}"
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
