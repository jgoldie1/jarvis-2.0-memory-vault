"""Command-line interface for the Quantum Blockchain node."""

from __future__ import annotations

import argparse

from quantum_blockchain.blockchain import Blockchain


def create_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(description="Quantum Blockchain CLI")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("start", help="Start blockchain node")
    subparsers.add_parser("status", help="Show blockchain status")
    return parser


def main() -> None:
    """Entry-point: parse arguments and dispatch commands."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "start":
        chain = Blockchain()
        print(f"Node started. Genesis block hash: {chain.last_block.hash[:16]}...")
    elif args.command == "status":
        print("Blockchain status: running")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
