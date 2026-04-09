"""Simple peer-to-peer sync helper."""

from __future__ import annotations

from typing import Any


class PeerSync:
    """Maintain a list of peer addresses and broadcast data to them."""

    def __init__(self) -> None:
        self.peers: list[str] = []

    def add_peer(self, address: str) -> None:
        """Add *address* if it is not already in the peer list."""
        if address not in self.peers:
            self.peers.append(address)

    def remove_peer(self, address: str) -> None:
        """Remove *address* from the peer list (no-op if absent)."""
        self.peers = [p for p in self.peers if p != address]

    def broadcast(self, data: Any) -> dict[str, Any]:
        """Return a summary dict describing the broadcast payload."""
        return {"peers": len(self.peers), "data": data, "status": "broadcast"}
