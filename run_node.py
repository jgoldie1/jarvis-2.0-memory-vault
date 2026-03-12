from __future__ import annotations

import tempfile

from quantum_blockchain import (
    Blockchain,
    EncryptedWallet,
    MarketplaceExporter,
    PeerSync,
    RecoveryManager,
    SignedSnapshot,
)


def main() -> None:
    # 1. Create blockchain and add blocks
    bc = Blockchain()
    bc.add_block({"tx": "Alice->Bob", "amount": 10})
    bc.add_block({"tx": "Bob->Carol", "amount": 5})
    bc.add_block({"tx": "Carol->Dave", "amount": 2})

    # 2. Encrypted wallet
    wallet = EncryptedWallet("demo")
    wallet_data: dict[str, object] = {"address": "0xDEADBEEF", "balance": 100}
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as wf:
        wallet_path = wf.name
    wallet.save(wallet_path, wallet_data)
    loaded_wallet = wallet.load(wallet_path)
    assert loaded_wallet["address"] == "0xDEADBEEF"

    # 3. Signed snapshot
    snap = SignedSnapshot("demo-key")
    signed = snap.sign({"block_count": len(bc.chain)})
    assert snap.verify(signed)

    # 4. Recovery manager
    rm = RecoveryManager("/tmp/qb_demo_backups")
    backup_path = rm.backup(bc)
    restored = rm.restore(backup_path)
    assert len(restored.chain) == len(bc.chain)

    # 5. Marketplace exporter
    exporter = MarketplaceExporter(bc)
    summary = exporter.summary()
    print(f"Summary: {summary}")

    # 6. Peer sync
    longer_bc = Blockchain()
    for i in range(5):
        longer_bc.add_block({"peer_tx": f"tx_{i}"})
    ps = PeerSync(bc)
    ps.add_peer("peer-1", longer_bc.to_dict())
    updated = ps.sync()
    print(f"Sync updated chain: {updated}")

    print("Node demo complete.")


if __name__ == "__main__":
    main()
