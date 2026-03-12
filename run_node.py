"""Demo entry-point: spin up a local quantum_blockchain node."""

from __future__ import annotations

import tempfile
from pathlib import Path

from quantum_blockchain import Blockchain, PeerNode
from quantum_blockchain.marketplace_export import export_to_json
from quantum_blockchain.recovery import RecoveryManager


def main() -> None:
    print("=== Quantum Blockchain Demo Node ===\n")

    # ── Create the blockchain ──────────────────────────────────────────────
    bc = Blockchain(difficulty=2)
    print(f"Genesis block : {bc.latest_block.hash[:20]}...")

    # ── Mine a few blocks ─────────────────────────────────────────────────
    transactions = [
        {"from": "Alice", "to": "Bob", "amount": 10.0},
        {"from": "Bob", "to": "Carol", "amount": 5.0},
        {"from": "Carol", "to": "Alice", "amount": 3.0},
    ]
    for tx in transactions:
        block = bc.add_block(tx)
        print(f"  Block {block.index:2d}    : {block.hash[:20]}...")

    print(f"\nChain valid   : {bc.is_valid()}")
    print(f"Chain length  : {len(bc.chain)}")

    # ── Peer sync demo ────────────────────────────────────────────────────
    bc2 = Blockchain(difficulty=2)
    node1 = PeerNode("node-1", bc)
    node2 = PeerNode("node-2", bc2)
    node1.connect(node2)
    node2.sync()
    print(f"\nPeer sync     : node-2 chain length = {len(node2.blockchain.chain)}")

    # ── Recovery snapshot + marketplace export ────────────────────────────
    with tempfile.TemporaryDirectory() as tmpdir:
        rm = RecoveryManager("demo-secret", Path(tmpdir))
        snapshot_path = rm.save_snapshot(bc)
        snapshot = rm.load_snapshot(snapshot_path)
        print(f"Snapshot      : {snapshot_path.name}")
        print(f"Sig verified  : {snapshot is not None}")

        export_path = Path(tmpdir) / "export.json"
        export_to_json(bc, export_path)
        print(
            f"Marketplace   : {export_path.name}"
            f" ({export_path.stat().st_size} bytes)"
        )

    print("\n=== Demo complete ===")


if __name__ == "__main__":
    main()
