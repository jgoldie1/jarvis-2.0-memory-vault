#!/usr/bin/env python3
"""recovery/save_wallets.py

Saves a timestamped backup of the fintech wallet and transactions data to
recovery/backups/<timestamp>/.  Safe to run at any time; existing fintech
data is never modified.

Usage::

    python3 recovery/save_wallets.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Paths are resolved relative to the repository root so the script works
# whether it is invoked from the root or from the recovery/ sub-directory.
_SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = _SCRIPT_DIR.parent
FINTECH = ROOT / "golden_era_marketplace" / "fintech"
BACKUPS = _SCRIPT_DIR / "backups"

WALLET_FILE = FINTECH / "wallet.json"
TX_FILE = FINTECH / "transactions.json"


def load_json(path: Path, default: Any) -> Any:
    """Load a JSON file, returning *default* if the file is missing or invalid."""
    try:
        if not path.exists():
            print(f"[warn] {path} not found – using default value", file=sys.stderr)
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[warn] Could not parse {path}: {exc}", file=sys.stderr)
        return default


def save_wallets(backups_dir: Path = BACKUPS) -> Path:
    """Read wallet/transactions and write a timestamped backup.

    Returns the directory that was created for this backup.
    """
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = backups_dir / ts
    dest.mkdir(parents=True, exist_ok=True)

    wallet = load_json(WALLET_FILE, {"balance": 0})
    transactions = load_json(TX_FILE, {"transactions": []})

    wallet_dest = dest / "wallet.json"
    tx_dest = dest / "transactions.json"

    wallet_dest.write_text(json.dumps(wallet, indent=2), encoding="utf-8")
    tx_dest.write_text(json.dumps(transactions, indent=2), encoding="utf-8")

    balance = wallet.get("balance", "n/a") if isinstance(wallet, dict) else "n/a"
    tx_count = len(transactions.get("transactions", [])) if isinstance(transactions, dict) else 0
    print(f"[ok] Wallet backup saved to {dest}")
    print(f"     balance={balance}  transactions={tx_count}")
    return dest


if __name__ == "__main__":
    save_wallets()
