from __future__ import annotations

import json
import os
from typing import Any

from quantum_blockchain.core.block import Block
from quantum_blockchain.core.crypto_utils import verify_transaction
from quantum_blockchain.core.transaction import Transaction


class Blockchain:
    def __init__(
        self,
        difficulty: int = 2,
        reward: float = 50.0,
        storage_path: str = "data/chain.json",
    ) -> None:
        self.difficulty = difficulty
        self.reward = reward
        self.storage_path = storage_path
        self.pending_transactions: list[Transaction] = []
        self.chain: list[Block] = []
        self.load_or_create()

    def create_genesis_block(self) -> None:
        self.chain = [Block(0, [], "0")]

    def latest_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, tx: Transaction) -> None:
        if not tx.sender or not tx.receiver:
            raise ValueError("Transaction must include sender and receiver.")
        if tx.amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        if tx.sender != "NETWORK" and not verify_transaction(tx):
            raise ValueError("Invalid transaction signature.")
        self.pending_transactions.append(tx)

    def mine_pending_transactions(self, miner_address: str) -> Block:
        reward_tx = Transaction(
            sender="NETWORK",
            receiver=miner_address,
            amount=self.reward,
            memo="Mining Reward",
            status="APPROVED",
        )

        block_transactions = self.pending_transactions + [reward_tx]
        new_block = Block(
            index=len(self.chain),
            transactions=block_transactions,
            previous_hash=self.latest_block().calculate_hash(),
        )

        target = "0" * self.difficulty
        while not new_block.calculate_hash().startswith(target):
            new_block.nonce += 1

        for tx in block_transactions:
            tx.status = "APPROVED"

        self.chain.append(new_block)
        self.pending_transactions = []
        self.save_chain()
        return new_block

    def get_balance(self, address: str) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address:
                    balance -= tx.amount
                if tx.receiver == address:
                    balance += tx.amount
        return balance

    def is_valid(self) -> bool:
        if not self.chain:
            return False

        for index in range(1, len(self.chain)):
            current = self.chain[index]
            previous = self.chain[index - 1]

            if current.previous_hash != previous.calculate_hash():
                return False

            if not current.calculate_hash().startswith("0" * self.difficulty):
                return False

        return True

    def save_chain(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data: list[dict[str, Any]] = []
        for block in self.chain:
            item = block.to_dict()
            item["hash"] = block.calculate_hash()
            data.append(item)
        with open(self.storage_path, "w", encoding="utf-8") as file_handle:
            json.dump(data, file_handle, indent=2)

    def load_or_create(self) -> None:
        if not os.path.exists(self.storage_path):
            self.create_genesis_block()
            self.save_chain()
            return

        with open(self.storage_path, "r", encoding="utf-8") as file_handle:
            raw_chain = json.load(file_handle)

        self.chain = []
        for item in raw_chain:
            txs = [Transaction(**tx) for tx in item["transactions"]]
            block = Block(
                index=item["index"],
                transactions=txs,
                previous_hash=item["previous_hash"],
                nonce=item["nonce"],
                timestamp=item["timestamp"],
            )
            self.chain.append(block)

        if not self.chain:
            self.create_genesis_block()
            self.save_chain()
