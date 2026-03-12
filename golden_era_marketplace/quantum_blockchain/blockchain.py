"""Quantum Blockchain core for the All American Marketplace.

Provides a simple proof-of-work blockchain with:
- Genesis block creation
- Block mining (SHA-256 PoW)
- Pending transaction pool
- Per-address balance calculation
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional


class Block:
    """A single block in the chain."""

    def __init__(
        self,
        index: int,
        transactions: List[Dict[str, Any]],
        previous_hash: str,
        nonce: int = 0,
        timestamp: Optional[float] = None,
    ) -> None:
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        block_string = json.dumps(
            {
                "index": self.index,
                "transactions": self.transactions,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
                "timestamp": self.timestamp,
            },
            sort_keys=True,
        )
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }


class Blockchain:
    """Proof-of-work blockchain with transaction support.

    Attributes:
        difficulty: Number of leading zeros required in a valid block hash.
        mining_reward: Coins awarded to the miner on each block.
    """

    DIFFICULTY = 3
    MINING_REWARD = 10.0
    MINER_ADDRESS = "miner-reward"

    def __init__(self) -> None:
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        self._create_genesis_block()

    # ------------------------------------------------------------------
    # Chain construction
    # ------------------------------------------------------------------

    def _create_genesis_block(self) -> None:
        genesis = Block(
            index=0,
            transactions=[],
            previous_hash="0" * 64,
            nonce=0,
            timestamp=0.0,
        )
        self.chain.append(genesis)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    def add_transaction(self, sender: str, recipient: str, amount: float) -> int:
        """Queue a transaction and return the index of the next block."""
        if amount <= 0:
            raise ValueError("Transaction amount must be positive.")
        self.pending_transactions.append(
            {"sender": sender, "recipient": recipient, "amount": amount}
        )
        return self.last_block.index + 1

    # ------------------------------------------------------------------
    # Mining
    # ------------------------------------------------------------------

    def mine_pending_transactions(self, miner_address: str) -> Block:
        """Mine all pending transactions into a new block."""
        # Add mining reward transaction
        reward_tx = {
            "sender": self.MINER_ADDRESS,
            "recipient": miner_address,
            "amount": self.MINING_REWARD,
        }
        transactions = self.pending_transactions + [reward_tx]

        new_block = Block(
            index=len(self.chain),
            transactions=transactions,
            previous_hash=self.last_block.hash,
        )
        new_block = self._proof_of_work(new_block)
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    def _proof_of_work(self, block: Block) -> Block:
        prefix = "0" * self.DIFFICULTY
        while not block.hash.startswith(prefix):
            block.nonce += 1
            block.hash = block._compute_hash()
        return block

    # ------------------------------------------------------------------
    # Balances
    # ------------------------------------------------------------------

    def get_balance(self, address: str) -> float:
        """Return the confirmed balance for *address* by scanning the chain."""
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("recipient") == address:
                    balance += tx["amount"]
                if tx.get("sender") == address:
                    balance -= tx["amount"]
        return round(balance, 8)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def is_valid(self) -> bool:
        """Return True if every block hash is consistent and the chain is linked."""
        prefix = "0" * self.DIFFICULTY
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current._compute_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
            if not current.hash.startswith(prefix):
                return False
        return True

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "length": len(self.chain),
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": self.pending_transactions,
        }
