"""Simple peer-to-peer sync for blockchain nodes."""

from __future__ import annotations

import json
from typing import Any

from .blockchain import Block, Blockchain


class PeerNode:
    """Represents a network node that holds a blockchain and can sync with peers."""

    def __init__(self, node_id: str, blockchain: Blockchain) -> None:
        self.node_id = node_id
        self.blockchain = blockchain
        self.peers: list[PeerNode] = []

    def connect(self, peer: PeerNode) -> None:
        """Register a bidirectional connection to *peer*."""
        if peer not in self.peers:
            self.peers.append(peer)
        if self not in peer.peers:
            peer.peers.append(self)

    def broadcast_block(self, block: Block) -> None:
        """Send *block* to all connected peers."""
        for peer in self.peers:
            peer.receive_block(block)

    def receive_block(self, block: Block) -> bool:
        """Append *block* if it continues the local chain; return True on success."""
        if block.previous_hash == self.blockchain.latest_block.hash:
            self.blockchain.chain.append(block)
            return True
        return False

    def sync(self) -> None:
        """Replace local chain with the longest valid chain among peers."""
        longest: list[Block] = self.blockchain.chain
        for peer in self.peers:
            if len(peer.blockchain.chain) > len(longest):
                longest = peer.blockchain.chain
        if len(longest) > len(self.blockchain.chain):
            candidate = Blockchain(self.blockchain.difficulty)
            candidate.chain = longest
            if candidate.is_valid():
                self.blockchain.chain = longest

    def serialize_chain(self) -> str:
        """Return the local chain as a JSON string."""
        chain_data: list[dict[str, Any]] = [
            {
                "index": b.index,
                "data": b.data,
                "previous_hash": b.previous_hash,
                "hash": b.hash,
                "timestamp": b.timestamp,
                "nonce": b.nonce,
            }
            for b in self.blockchain.chain
        ]
        return json.dumps(chain_data)
