"""Demonstration entry-point: start a local Quantum Blockchain node."""

from __future__ import annotations

from quantum_blockchain.blockchain import Blockchain


def main() -> None:
    """Initialise the blockchain, mine a couple of blocks, and report chain health."""
    print("Initialising Quantum Blockchain node...")

    chain = Blockchain(difficulty=2)
    chain.add_block({"tx": "Alice -> Bob", "amount": 10})
    chain.add_block({"tx": "Bob -> Carol", "amount": 5})

    print(f"Chain length : {len(chain.chain)} blocks")
    print(f"Chain valid  : {chain.is_valid()}")
    for blk in chain.to_dict():
        print(f"  Block {blk['index']}: {blk['hash'][:16]}...")

    print("Node started successfully.")


if __name__ == "__main__":
    main()
