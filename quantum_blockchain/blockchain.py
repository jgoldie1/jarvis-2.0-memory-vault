"""
blockchain.py – Core blockchain engine.

Features (existing build):
  * Block with SHA-256 hash chaining
  * Signed transactions (HMAC-SHA256)
  * Proof-of-work mining
  * Balance ledger
  * Ternary contract states  (PENDING / ACTIVE / TERMINATED)
  * Persistent ledger (JSON)
  * Wallet file generation
  * Backup / verify / restore workflow
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Ternary contract states
# ---------------------------------------------------------------------------

class TernaryContractState(str, Enum):
    """Three-valued contract lifecycle."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    TERMINATED = "TERMINATED"


# ---------------------------------------------------------------------------
# Signed transaction
# ---------------------------------------------------------------------------

class SignedTransaction:
    """A transaction signed with an HMAC-SHA256 key."""

    def __init__(
        self,
        sender: str,
        recipient: str,
        amount: float,
        contract_state: TernaryContractState = TernaryContractState.PENDING,
    ) -> None:
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.contract_state = contract_state
        self.timestamp = time.time()
        self.signature: Optional[str] = None

    def sign(self, secret_key: bytes) -> None:
        """Compute HMAC-SHA256 signature over the transaction payload."""
        payload = self._payload_bytes()
        self.signature = hmac.new(secret_key, payload, hashlib.sha256).hexdigest()

    def verify(self, secret_key: bytes) -> bool:
        """Return True if the stored signature matches the payload."""
        if self.signature is None:
            return False
        payload = self._payload_bytes()
        expected = hmac.new(secret_key, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, self.signature)

    def _payload_bytes(self) -> bytes:
        return (
            f"{self.sender}:{self.recipient}:{self.amount:.8f}:"
            f"{self.contract_state.value}:{self.timestamp:.6f}"
        ).encode()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "contract_state": self.contract_state.value,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignedTransaction":
        tx = cls(
            sender=data["sender"],
            recipient=data["recipient"],
            amount=data["amount"],
            contract_state=TernaryContractState(data["contract_state"]),
        )
        tx.timestamp = data["timestamp"]
        tx.signature = data.get("signature")
        return tx


# ---------------------------------------------------------------------------
# Block
# ---------------------------------------------------------------------------

class Block:
    """A single block in the chain."""

    def __init__(
        self,
        index: int,
        transactions: List[SignedTransaction],
        previous_hash: str,
        nonce: int = 0,
    ) -> None:
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.timestamp = time.time()
        self.hash: str = self._compute_hash()

    # ------------------------------------------------------------------
    def _compute_hash(self) -> str:
        block_str = json.dumps(self._header_dict(), sort_keys=True)
        return hashlib.sha256(block_str.encode()).hexdigest()

    def _header_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
        }

    def rehash(self) -> str:
        self.hash = self._compute_hash()
        return self.hash

    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        d = self._header_dict()
        d["hash"] = self.hash
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        txs = [SignedTransaction.from_dict(t) for t in data.get("transactions", [])]
        blk = cls(
            index=data["index"],
            transactions=txs,
            previous_hash=data["previous_hash"],
            nonce=data["nonce"],
        )
        blk.timestamp = data["timestamp"]
        blk.hash = data["hash"]
        return blk


# ---------------------------------------------------------------------------
# Blockchain
# ---------------------------------------------------------------------------

class Blockchain:
    """
    Full blockchain with:
      * proof-of-work mining
      * balance tracking
      * ternary contract state support
      * JSON ledger persistence
      * backup / verify / restore
    """

    GENESIS_HASH = "0" * 64
    DEFAULT_DIFFICULTY = 4  # leading zeros required

    def __init__(
        self,
        ledger_path: Path | str = "ledger.json",
        difficulty: int = DEFAULT_DIFFICULTY,
    ) -> None:
        self.ledger_path = Path(ledger_path)
        self.difficulty = difficulty
        self.chain: List[Block] = []
        self.pending_transactions: List[SignedTransaction] = []
        self.balances: Dict[str, float] = {}
        self._genesis()

    # ------------------------------------------------------------------
    # Genesis
    # ------------------------------------------------------------------

    def _genesis(self) -> None:
        genesis = Block(index=0, transactions=[], previous_hash=self.GENESIS_HASH)
        self.chain.append(genesis)

    # ------------------------------------------------------------------
    # Transaction helpers
    # ------------------------------------------------------------------

    def add_transaction(self, tx: SignedTransaction) -> None:
        self.pending_transactions.append(tx)

    # ------------------------------------------------------------------
    # Mining
    # ------------------------------------------------------------------

    def mine_block(self, miner_address: str, reward: float = 50.0) -> Block:
        """Mine pending transactions into a new block."""
        reward_tx = SignedTransaction(
            sender="COINBASE",
            recipient=miner_address,
            amount=reward,
            contract_state=TernaryContractState.ACTIVE,
        )
        txs = self.pending_transactions + [reward_tx]
        block = Block(
            index=len(self.chain),
            transactions=txs,
            previous_hash=self.chain[-1].hash,
        )
        block.nonce, block.hash = self._proof_of_work(block)
        self.chain.append(block)
        self.pending_transactions = []
        self._apply_balances(block)
        return block

    def _proof_of_work(self, block: Block) -> tuple[int, str]:
        prefix = "0" * self.difficulty
        block.nonce = 0
        while True:
            h = block.rehash()
            if h.startswith(prefix):
                return block.nonce, h
            block.nonce += 1

    def _apply_balances(self, block: Block) -> None:
        for tx in block.transactions:
            if tx.contract_state == TernaryContractState.TERMINATED:
                continue
            if tx.sender != "COINBASE":
                self.balances[tx.sender] = self.balances.get(tx.sender, 0.0) - tx.amount
            self.balances[tx.recipient] = self.balances.get(tx.recipient, 0.0) + tx.amount

    def get_balance(self, address: str) -> float:
        return self.balances.get(address, 0.0)

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------

    def is_valid(self) -> bool:
        """Return True if the chain is internally consistent."""
        if not self.chain:
            return False
        # Genesis block must have the canonical sentinel previous_hash
        if self.chain[0].previous_hash != self.GENESIS_HASH:
            return False
        prefix = "0" * self.difficulty
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr.previous_hash != prev.hash:
                return False
            if curr.hash != curr._compute_hash():
                return False
            if not curr.hash.startswith(prefix):
                return False
        return True

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_ledger(self) -> None:
        data = {
            "difficulty": self.difficulty,
            "balances": self.balances,
            "chain": [b.to_dict() for b in self.chain],
        }
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.write_text(json.dumps(data, indent=2))

    def load_ledger(self) -> None:
        data = json.loads(self.ledger_path.read_text())
        self.difficulty = data.get("difficulty", self.DEFAULT_DIFFICULTY)
        self.balances = data.get("balances", {})
        self.chain = [Block.from_dict(b) for b in data["chain"]]

    # ------------------------------------------------------------------
    # Backup / verify / restore
    # ------------------------------------------------------------------

    def backup(self, backup_path: Path | str) -> Path:
        """Copy the current ledger file to *backup_path*."""
        self.save_ledger()
        dest = Path(backup_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.ledger_path, dest)
        return dest

    def verify_backup(self, backup_path: Path | str) -> bool:
        """Load the backup into a temporary chain and validate it."""
        tmp = Blockchain(ledger_path=backup_path, difficulty=self.difficulty)
        try:
            tmp.load_ledger()
            return tmp.is_valid()
        except (json.JSONDecodeError, KeyError, ValueError):
            return False

    def restore(self, backup_path: Path | str) -> bool:
        """
        Replace the active ledger with *backup_path* **only** if integrity
        validation passes.  Returns True on success.
        """
        if not self.verify_backup(backup_path):
            return False
        shutil.copy2(backup_path, self.ledger_path)
        self.load_ledger()
        return True

    # ------------------------------------------------------------------
    # Wallet generation
    # ------------------------------------------------------------------

    @staticmethod
    def generate_wallet(wallet_path: Path | str) -> Dict[str, str]:
        """Create a new wallet with a random address/secret and save to JSON."""
        address = "AAM-" + hashlib.sha256(os.urandom(32)).hexdigest()[:24].upper()
        secret = hashlib.sha256(os.urandom(32)).hexdigest()
        wallet = {"address": address, "secret": secret}
        p = Path(wallet_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(wallet, indent=2))
        return wallet
