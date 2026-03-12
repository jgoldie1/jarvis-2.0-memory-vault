from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from quantum_blockchain.blockchain import Block, Blockchain


class RecoveryManager:
    def __init__(self, backup_dir: str = "backups") -> None:
        self._backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)

    def backup(self, blockchain: Blockchain) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"backup_{timestamp}.json"
        path = os.path.join(self._backup_dir, filename)
        with open(path, "w") as f:
            json.dump(blockchain.to_dict(), f)
        return path

    def restore(self, path: str) -> Blockchain:
        with open(path) as f:
            chain_data: list[Any] = json.load(f)
        bc = Blockchain.__new__(Blockchain)
        bc.chain = [
            Block(
                index=int(b["index"]),
                timestamp=float(b["timestamp"]),
                data=dict(b["data"]),
                previous_hash=str(b["previous_hash"]),
                hash=str(b["hash"]),
            )
            for b in chain_data
        ]
        return bc

    def list_backups(self) -> list[str]:
        return sorted(
            os.path.join(self._backup_dir, f)
            for f in os.listdir(self._backup_dir)
            if f.endswith(".json")
        )
