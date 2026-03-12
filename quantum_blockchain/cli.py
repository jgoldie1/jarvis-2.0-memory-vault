from __future__ import annotations

import argparse
import json

from quantum_blockchain.blockchain import Blockchain


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quantum Blockchain CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Print chain length")
    subparsers.add_parser("validate", help="Check chain validity")

    add_parser = subparsers.add_parser("add", help="Add a block")
    add_parser.add_argument(
        "--data",
        nargs="+",
        metavar="key=value",
        help="Block data as key=value pairs",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)

    bc = Blockchain()

    if args.command == "status":
        print(f"Chain length: {len(bc.chain)}")
    elif args.command == "validate":
        valid = bc.is_valid()
        print(f"Chain valid: {valid}")
    elif args.command == "add":
        data: dict[str, object] = {}
        if args.data:
            for item in args.data:
                key, _, value = item.partition("=")
                data[key] = value
        block = bc.add_block(data)
        print(f"Added block {block.index}: {json.dumps(block.data)}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
