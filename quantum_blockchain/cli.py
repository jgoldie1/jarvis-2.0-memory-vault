"""
cli.py – Unified command-line entry point for the quantum blockchain.

Usage examples (paste-ready)
-----------------------------
    # Initialise a new blockchain + wallet
    python -m quantum_blockchain.cli init --ledger ledger.json --wallet wallet.json

    # Mine a block
    python -m quantum_blockchain.cli mine --ledger ledger.json --wallet wallet.json

    # Balance check
    python -m quantum_blockchain.cli balance --ledger ledger.json --address <ADDR>

    # Full backup (ledger + encrypted wallet + signed snapshot)
    python -m quantum_blockchain.cli backup --ledger ledger.json --wallet wallet.json \\
        --passphrase "vault-pass" --backup-dir backups/ --snapshot-dir snapshots/

    # Verify a backup or snapshot
    python -m quantum_blockchain.cli verify --backup backups/ledger_*.json
    python -m quantum_blockchain.cli verify --snapshot snapshots/snapshot_*.json \\
        --wallet wallet.json

    # Restore from ledger backup
    python -m quantum_blockchain.cli restore --backup backups/ledger_*.json \\
        --ledger ledger.json --wallet wallet.json \\
        --wallet-backup backups/wallet_*.enc --passphrase "vault-pass"

    # Restore from signed snapshot
    python -m quantum_blockchain.cli restore --snapshot snapshots/snapshot_*.json \\
        --ledger ledger.json --wallet wallet.json --passphrase "vault-pass"

    # Export marketplace data
    python -m quantum_blockchain.cli export --data-dir golden_era_marketplace/fintech/ \\
        --archive exports/marketplace.json --wallet wallet.json

    # Import marketplace data
    python -m quantum_blockchain.cli import --archive exports/marketplace.json \\
        --data-dir golden_era_marketplace/fintech/ --wallet wallet.json

    # Start a peer node
    python -m quantum_blockchain.cli node --ledger ledger.json --wallet wallet.json \\
        --host 0.0.0.0 --port 8765

    # Sync from a peer
    python -m quantum_blockchain.cli sync --peer http://192.168.1.10:8765 \\
        --ledger ledger.json
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_blockchain(ledger: str, difficulty: int = 4):
    from quantum_blockchain.blockchain import Blockchain

    bc = Blockchain(ledger_path=ledger, difficulty=difficulty)
    if Path(ledger).exists():
        bc.load_ledger()
    return bc


def _load_wallet(wallet_path: str):
    from quantum_blockchain.wallet import WalletManager

    wm = WalletManager(wallet_path)
    if Path(wallet_path).exists():
        wm.load()
    return wm


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> None:
    from quantum_blockchain.blockchain import Blockchain
    from quantum_blockchain.wallet import WalletManager

    bc = Blockchain(ledger_path=args.ledger)
    bc.save_ledger()
    print(f"[init] Ledger created: {args.ledger}")

    wm = WalletManager(args.wallet)
    wallet = wm.create()
    print(f"[init] Wallet created : {args.wallet}")
    print(f"       Address        : {wallet['address']}")


def cmd_mine(args: argparse.Namespace) -> None:
    bc = _load_blockchain(args.ledger)
    wm = _load_wallet(args.wallet)
    block = bc.mine_block(miner_address=wm.address, reward=50.0)
    bc.save_ledger()
    print(f"[mine] Block #{block.index} mined  hash={block.hash[:16]}…")
    print(f"       Balance of {wm.address}: {bc.get_balance(wm.address)}")


def cmd_balance(args: argparse.Namespace) -> None:
    bc = _load_blockchain(args.ledger)
    bal = bc.get_balance(args.address)
    print(f"[balance] {args.address} = {bal}")


def cmd_backup(args: argparse.Namespace) -> None:
    from quantum_blockchain.recovery import RecoveryManager

    bc = _load_blockchain(args.ledger)
    wm = _load_wallet(args.wallet)
    rm = RecoveryManager(
        bc, wm, backup_dir=args.backup_dir,
        snapshot_dir=args.snapshot_dir,
    )
    result = rm.full_backup(passphrase=args.passphrase)
    print("[backup] Complete:")
    for k, v in result.items():
        print(f"         {k}: {v}")


def cmd_verify(args: argparse.Namespace) -> None:
    if args.backup:
        from quantum_blockchain.blockchain import Blockchain

        bc = Blockchain(ledger_path=args.backup)
        ok = bc.verify_backup(args.backup)
        print(f"[verify] Ledger backup {'✓ valid' if ok else '✗ INVALID'}: {args.backup}")
    if args.snapshot:
        wm = _load_wallet(args.wallet)
        from quantum_blockchain.snapshot import ChainSnapshot

        ok, _ = ChainSnapshot.load_and_verify(args.snapshot, wm.secret_bytes)
        print(f"[verify] Snapshot {'✓ valid' if ok else '✗ INVALID'}: {args.snapshot}")


def cmd_restore(args: argparse.Namespace) -> None:
    from quantum_blockchain.recovery import RecoveryManager

    bc = _load_blockchain(args.ledger)
    wm = _load_wallet(args.wallet)
    rm = RecoveryManager(bc, wm)

    if args.backup:
        ok = rm.restore_from_ledger(
            args.backup,
            passphrase=args.passphrase or "",
            wallet_backup=args.wallet_backup,
            wallet_output=args.wallet,
        )
    elif args.snapshot:
        ok = rm.restore_from_snapshot(
            args.snapshot,
            passphrase=args.passphrase or "",
            wallet_backup=args.wallet_backup,
            wallet_output=args.wallet,
            ledger_output=args.ledger,
        )
    else:
        print("[restore] Supply --backup or --snapshot")
        sys.exit(1)

    print(f"[restore] {'✓ success' if ok else '✗ FAILED'}")


def cmd_export(args: argparse.Namespace) -> None:
    from quantum_blockchain.marketplace_export import MarketplaceExporter

    secret = None
    if args.wallet and Path(args.wallet).exists():
        wm = _load_wallet(args.wallet)
        secret = wm.secret_bytes

    exp = MarketplaceExporter(args.data_dir, secret_key=secret)
    archive = exp.export(args.archive)
    print(f"[export] Archive written: {archive}")


def cmd_import(args: argparse.Namespace) -> None:
    from quantum_blockchain.marketplace_export import MarketplaceExporter

    secret = None
    if args.wallet and Path(args.wallet).exists():
        wm = _load_wallet(args.wallet)
        secret = wm.secret_bytes

    ok = MarketplaceExporter.restore(args.archive, args.data_dir, secret_key=secret)
    print(f"[import] {'✓ restored' if ok else '✗ FAILED (signature mismatch?)'}")


def cmd_node(args: argparse.Namespace) -> None:
    from quantum_blockchain.peer_sync import PeerNode

    bc = _load_blockchain(args.ledger)
    wm = _load_wallet(args.wallet)
    node = PeerNode(bc, wm, host=args.host, port=args.port)
    node.start()
    print(f"[node] Listening on {node.url}  (Ctrl-C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        node.stop()
        print("[node] Stopped.")


def cmd_sync(args: argparse.Namespace) -> None:
    from quantum_blockchain.peer_sync import PeerClient

    bc = _load_blockchain(args.ledger)
    client = PeerClient(args.peer, bc)
    if not client.health_check():
        print(f"[sync] Peer {args.peer} is unreachable.")
        sys.exit(1)
    updated = client.sync_chain()
    print(f"[sync] Chain {'updated ✓' if updated else 'already up-to-date'}  "
          f"blocks={len(bc.chain)}")


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="quantum_blockchain",
        description="All American Marketplace – quantum blockchain CLI",
    )
    sub = p.add_subparsers(dest="command")

    # init
    s = sub.add_parser("init", help="Initialise ledger and wallet")
    s.add_argument("--ledger", default="ledger.json")
    s.add_argument("--wallet", default="wallet.json")

    # mine
    s = sub.add_parser("mine", help="Mine pending transactions")
    s.add_argument("--ledger", default="ledger.json")
    s.add_argument("--wallet", default="wallet.json")

    # balance
    s = sub.add_parser("balance", help="Show balance for address")
    s.add_argument("--ledger", default="ledger.json")
    s.add_argument("--address", required=True)

    # backup
    s = sub.add_parser("backup", help="Full backup (ledger + wallet + snapshot)")
    s.add_argument("--ledger", default="ledger.json")
    s.add_argument("--wallet", default="wallet.json")
    s.add_argument("--passphrase", required=True)
    s.add_argument("--backup-dir", default="backups/")
    s.add_argument("--snapshot-dir", default="snapshots/")

    # verify
    s = sub.add_parser("verify", help="Verify a backup or snapshot")
    s.add_argument("--backup", default=None)
    s.add_argument("--snapshot", default=None)
    s.add_argument("--wallet", default="wallet.json")

    # restore
    s = sub.add_parser("restore", help="Restore from backup or snapshot")
    s.add_argument("--ledger", default="ledger.json")
    s.add_argument("--wallet", default="wallet.json")
    s.add_argument("--backup", default=None)
    s.add_argument("--snapshot", default=None)
    s.add_argument("--wallet-backup", default=None)
    s.add_argument("--passphrase", default=None)

    # export
    s = sub.add_parser("export", help="Export marketplace data")
    s.add_argument("--data-dir", default="golden_era_marketplace/fintech/")
    s.add_argument("--archive", required=True)
    s.add_argument("--wallet", default=None)

    # import
    s = sub.add_parser("import", help="Import marketplace data")
    s.add_argument("--archive", required=True)
    s.add_argument("--data-dir", default="golden_era_marketplace/fintech/")
    s.add_argument("--wallet", default=None)

    # node
    s = sub.add_parser("node", help="Run a peer node")
    s.add_argument("--ledger", default="ledger.json")
    s.add_argument("--wallet", default="wallet.json")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765)

    # sync
    s = sub.add_parser("sync", help="Sync chain from a peer")
    s.add_argument("--peer", required=True)
    s.add_argument("--ledger", default="ledger.json")

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "init": cmd_init,
        "mine": cmd_mine,
        "balance": cmd_balance,
        "backup": cmd_backup,
        "verify": cmd_verify,
        "restore": cmd_restore,
        "export": cmd_export,
        "import": cmd_import,
        "node": cmd_node,
        "sync": cmd_sync,
    }

    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
