"""Command-line interface for quantum_blockchain."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .blockchain import Blockchain
from .marketplace_export import export_to_json
from .recovery import RecoveryManager
from .wallet import load_wallet, save_wallet


def _cmd_init(args: argparse.Namespace) -> None:
    bc = Blockchain(difficulty=args.difficulty)
    print(f"Blockchain initialised. Genesis hash: {bc.latest_block.hash}")


def _cmd_add(args: argparse.Namespace) -> None:
    bc = Blockchain(difficulty=args.difficulty)
    block = bc.add_block(args.data)
    print(f"Added block {block.index}: {block.hash}")


def _cmd_validate(args: argparse.Namespace) -> None:  # noqa: ARG001
    bc = Blockchain()
    valid = bc.is_valid()
    print(f"Blockchain valid: {valid}")
    sys.exit(0 if valid else 1)


def _cmd_export(args: argparse.Namespace) -> None:
    bc = Blockchain()
    export_to_json(bc, Path(args.output))
    print(f"Exported to {args.output}")


def _cmd_snapshot(args: argparse.Namespace) -> None:
    bc = Blockchain(difficulty=args.difficulty)
    rm = RecoveryManager(args.secret_key, Path(args.recovery_dir))
    path = rm.save_snapshot(bc)
    print(f"Snapshot saved: {path}")


def _cmd_wallet_save(args: argparse.Namespace) -> None:
    data = {"address": args.address, "balance": 0.0}
    save_wallet(data, args.password, Path(args.file))
    print(f"Wallet saved to {args.file}")


def _cmd_wallet_load(args: argparse.Namespace) -> None:
    wallet = load_wallet(args.password, Path(args.file))
    print(f"Wallet: {wallet}")


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="quantum-blockchain",
        description="Quantum Blockchain CLI",
    )
    sub = parser.add_subparsers(dest="command")

    init_p = sub.add_parser("init", help="Initialise a new blockchain")
    init_p.add_argument("--difficulty", type=int, default=2)
    init_p.set_defaults(func=_cmd_init)

    add_p = sub.add_parser("add", help="Add a block")
    add_p.add_argument("data", help="Block data string")
    add_p.add_argument("--difficulty", type=int, default=2)
    add_p.set_defaults(func=_cmd_add)

    val_p = sub.add_parser("validate", help="Validate blockchain integrity")
    val_p.set_defaults(func=_cmd_validate)

    exp_p = sub.add_parser("export", help="Export blockchain to JSON")
    exp_p.add_argument("output", help="Output file path")
    exp_p.set_defaults(func=_cmd_export)

    snap_p = sub.add_parser("snapshot", help="Save a signed recovery snapshot")
    snap_p.add_argument("secret_key", help="HMAC secret key")
    snap_p.add_argument("--difficulty", type=int, default=2)
    snap_p.add_argument("--recovery-dir", default="recovery")
    snap_p.set_defaults(func=_cmd_snapshot)

    ws_p = sub.add_parser("wallet-save", help="Save an encrypted wallet")
    ws_p.add_argument("address", help="Wallet address")
    ws_p.add_argument("password", help="Encryption password")
    ws_p.add_argument("file", help="Output file path")
    ws_p.set_defaults(func=_cmd_wallet_save)

    wl_p = sub.add_parser("wallet-load", help="Load an encrypted wallet")
    wl_p.add_argument("password", help="Decryption password")
    wl_p.add_argument("file", help="Wallet file path")
    wl_p.set_defaults(func=_cmd_wallet_load)

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
