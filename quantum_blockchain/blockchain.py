"""Core blockchain implementation with proof-of-work mining."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Block:
    """A single block in the blockchain."""

    index: int
    data: Any
    previous_hash: str
    timestamp: float = field(default_factory=time.time)
    nonce: int = 0
    hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Compute the SHA-256 hash of this block."""
        block_str = json.dumps(
            {
                "index": self.index,
                "data": self.data,
                "previous_hash": self.previous_hash,
                "timestamp": self.timestamp,
                "nonce": self.nonce,
            },
            sort_keys=True,
        )
        return hashlib.sha256(block_str.encode()).hexdigest()

    def mine(self, difficulty: int) -> None:
        """Mine the block by incrementing nonce until hash meets difficulty."""
        prefix = "0" * difficulty
        while not self.hash.startswith(prefix):
            self.nonce += 1
            self.hash = self.compute_hash()


class Blockchain:
    """A simple proof-of-work blockchain."""

    def __init__(self, difficulty: int = 2) -> None:
        self.difficulty = difficulty
        self.chain: list[Block] = []
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        genesis = Block(index=0, data="Genesis Block", previous_hash="0")
        genesis.mine(self.difficulty)
        self.chain.append(genesis)

    @property
    def latest_block(self) -> Block:
        """Return the most recently added block."""
        return self.chain[-1]

    def add_block(self, data: Any) -> Block:
        """Create, mine, and append a new block with the given data."""
        block = Block(
            index=len(self.chain),
            data=data,
            previous_hash=self.latest_block.hash,
        )
        block.mine(self.difficulty)
        self.chain.append(block)
        return block

    def is_valid(self) -> bool:
        """Verify hash integrity and linkage of the entire chain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current.compute_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True
