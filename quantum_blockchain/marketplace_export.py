from __future__ import annotations

import csv
import json

from quantum_blockchain.blockchain import Blockchain


class MarketplaceExporter:
    def __init__(self, blockchain: Blockchain) -> None:
        self._blockchain = blockchain

    def export_json(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self._blockchain.to_dict(), f, indent=2)

    def export_csv(self, path: str) -> None:
        chain = self._blockchain.to_dict()
        if not chain:
            return
        fieldnames = ["index", "timestamp", "previous_hash", "hash", "data"]
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for block in chain:
                writer.writerow(
                    {
                        "index": block["index"],
                        "timestamp": block["timestamp"],
                        "previous_hash": block["previous_hash"],
                        "hash": block["hash"],
                        "data": json.dumps(block["data"]),
                    }
                )

    def summary(self) -> dict[str, object]:
        chain = self._blockchain.to_dict()
        return {
            "total_blocks": len(chain),
            "is_valid": self._blockchain.is_valid(),
            "latest_hash": chain[-1]["hash"] if chain else None,
        }
