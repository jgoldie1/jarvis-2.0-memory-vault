from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field


@dataclass
class Block:
    index: int
    timestamp: float
    data: dict[str, object]
    previous_hash: str
    hash: str = field(default="")


class Blockchain:
    def __init__(self) -> None:
        self.chain: list[Block] = []
        genesis = Block(
            index=0,
            timestamp=time.time(),
            data={"genesis": True},
            previous_hash="0",
        )
        genesis.hash = self._compute_hash(genesis)
        self.chain.append(genesis)

    def add_block(self, data: dict[str, object]) -> Block:
        previous = self.chain[-1]
        block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            data=data,
            previous_hash=previous.hash,
        )
        block.hash = self._compute_hash(block)
        self.chain.append(block)
        return block

    def is_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != self._compute_hash(current):
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

    def _compute_hash(self, block: Block) -> str:
        block_string = json.dumps(
            {
                "index": block.index,
                "timestamp": block.timestamp,
                "data": block.data,
                "previous_hash": block.previous_hash,
            },
            sort_keys=True,
        )
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self) -> list[dict[str, object]]:
        return [
            {
                "index": b.index,
                "timestamp": b.timestamp,
                "data": b.data,
                "previous_hash": b.previous_hash,
                "hash": b.hash,
            }
            for b in self.chain
        ]
