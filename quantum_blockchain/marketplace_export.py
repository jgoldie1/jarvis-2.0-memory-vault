"""Export and import blockchain data in JSON format for marketplace use."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .blockchain import Blockchain


def export_to_json(blockchain: Blockchain, path: Path) -> None:
    """Serialise *blockchain* to a JSON file at *path*."""
    data: dict[str, Any] = {
        "blocks": [
            {
                "index": b.index,
                "data": b.data,
                "hash": b.hash,
                "previous_hash": b.previous_hash,
                "timestamp": b.timestamp,
                "nonce": b.nonce,
            }
            for b in blockchain.chain
        ],
        "length": len(blockchain.chain),
        "valid": blockchain.is_valid(),
    }
    path.write_text(json.dumps(data, indent=2))


def import_from_json(path: Path) -> dict[str, Any]:
    """Read and return the exported blockchain dict from *path*."""
    result: dict[str, Any] = json.loads(path.read_text())
    return result
