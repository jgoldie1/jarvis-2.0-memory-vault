"""Recovery manager: persists and restores signed blockchain snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .blockchain import Blockchain
from .snapshot import create_snapshot, verify_snapshot


class RecoveryManager:
    """Saves and loads signed snapshots of a :class:`Blockchain`."""

    def __init__(self, secret_key: str, recovery_dir: Path | None = None) -> None:
        self.secret_key = secret_key
        self.recovery_dir = recovery_dir or Path("recovery")
        self.recovery_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, blockchain: Blockchain) -> Path:
        """Serialise *blockchain*, sign it, and write a JSON snapshot file."""
        chain_data = [
            {
                "index": b.index,
                "data": b.data,
                "previous_hash": b.previous_hash,
                "hash": b.hash,
                "timestamp": b.timestamp,
                "nonce": b.nonce,
            }
            for b in blockchain.chain
        ]
        snapshot = create_snapshot(chain_data, self.secret_key)
        ts = int(snapshot["timestamp"])
        snapshot_file = self.recovery_dir / f"snapshot_{ts}.json"
        snapshot_file.write_text(json.dumps(snapshot, indent=2))
        return snapshot_file

    def load_snapshot(self, path: Path) -> dict[str, Any] | None:
        """Load and verify a snapshot file; returns None if invalid."""
        try:
            snapshot: dict[str, Any] = json.loads(path.read_text())
            if verify_snapshot(snapshot, self.secret_key):
                return snapshot
            return None
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def list_snapshots(self) -> list[Path]:
        """Return a sorted list of snapshot file paths in the recovery dir."""
        return sorted(self.recovery_dir.glob("snapshot_*.json"))
