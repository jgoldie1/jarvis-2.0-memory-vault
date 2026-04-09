"""Core blockchain implementation."""

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
    timestamp: float
    data: Any
    previous_hash: str
    nonce: int = 0
    hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """Compute the SHA-256 hash of this block."""
        block_string = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "data": self.data,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
            },
            sort_keys=True,
        )
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine(self, difficulty: int = 2) -> None:
        """Proof-of-work: find a nonce so the hash starts with *difficulty* zeros."""
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()


class Blockchain:
    """An append-only chain of :class:`Block` objects."""

    def __init__(self, difficulty: int = 2) -> None:
        self.difficulty = difficulty
        self.chain: list[Block] = []
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        genesis = Block(
            index=0,
            timestamp=time.time(),
            data="Genesis Block",
            previous_hash="0",
        )
        genesis.mine(self.difficulty)
        self.chain.append(genesis)

    @property
    def last_block(self) -> Block:
        """Return the most recently added block."""
        return self.chain[-1]

    def add_block(self, data: Any) -> Block:
        """Mine a new block and append it to the chain."""
        block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            data=data,
            previous_hash=self.last_block.hash,
        )
        block.mine(self.difficulty)
        self.chain.append(block)
        return block

    def is_valid(self) -> bool:
        """Return True if every block's hash and linkage are intact."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current.calculate_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

    def to_dict(self) -> list[dict[str, Any]]:
        """Serialise the chain to a list of plain dictionaries."""
        return [
            {
                "index": b.index,
                "timestamp": b.timestamp,
                "data": b.data,
                "previous_hash": b.previous_hash,
                "nonce": b.nonce,
                "hash": b.hash,
            }
            for b in self.chain
        ]
