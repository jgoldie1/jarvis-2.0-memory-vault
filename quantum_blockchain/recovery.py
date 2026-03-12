"""
recovery.py – **Automatic chain-integrity validation on restore**.

Provides a high-level ``RecoveryManager`` that ties together ledger
backups, encrypted wallet backups, and signed snapshots into a
single, recovery-first workflow.  All operations are offline-capable.

Paste-ready usage
-----------------
    from quantum_blockchain.recovery import RecoveryManager
    rm = RecoveryManager(blockchain, wallet_manager, snapshot_dir="snaps/")
    rm.full_backup(passphrase="vault-pass")

    # Later, on a fresh machine:
    rm.full_restore(passphrase="vault-pass", snapshot_secret=wallet.secret_bytes)
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from quantum_blockchain.blockchain import Blockchain
from quantum_blockchain.snapshot import ChainSnapshot
from quantum_blockchain.wallet import WalletManager


class RecoveryManager:
    """Orchestrate backup, verify, and restore in a single interface."""

    def __init__(
        self,
        blockchain: Blockchain,
        wallet_manager: WalletManager,
        backup_dir: Path | str = "backups/",
        snapshot_dir: Path | str = "snapshots/",
    ) -> None:
        self.blockchain = blockchain
        self.wallet_manager = wallet_manager
        self.backup_dir = Path(backup_dir)
        self.snapshot_dir = Path(snapshot_dir)

    # ------------------------------------------------------------------
    # Full backup
    # ------------------------------------------------------------------

    def full_backup(self, passphrase: str) -> dict:
        """
        Perform a complete backup:
          1. Save the live ledger.
          2. Create an encrypted wallet backup.
          3. Create a signed chain snapshot.

        Returns paths to all created artefacts.
        """
        ts = int(time.time())
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        # 1. Ledger backup (plain JSON – for fast restore)
        ledger_backup = self.backup_dir / f"ledger_{ts}.json"
        self.blockchain.backup(ledger_backup)

        # 2. Encrypted wallet backup
        wallet_backup = self.backup_dir / f"wallet_{ts}.enc"
        self.wallet_manager.backup_encrypted(wallet_backup, passphrase=passphrase)

        # 3. Signed chain snapshot
        snap_path = self.snapshot_dir / f"snapshot_{ts}.json"
        ChainSnapshot(
            self.blockchain, self.wallet_manager.secret_bytes
        ).save(snap_path)

        return {
            "ledger_backup": str(ledger_backup),
            "wallet_backup": str(wallet_backup),
            "snapshot": str(snap_path),
            "timestamp": ts,
        }

    # ------------------------------------------------------------------
    # Verify
    # ------------------------------------------------------------------

    def verify_backup(self, ledger_backup: Path | str) -> bool:
        """Return True if *ledger_backup* is a valid, internally consistent chain."""
        return self.blockchain.verify_backup(ledger_backup)

    def verify_snapshot(self, snapshot_path: Path | str) -> bool:
        """Return True if the snapshot HMAC and chain hashes are both valid."""
        ok, payload = ChainSnapshot.load_and_verify(
            snapshot_path, self.wallet_manager.secret_bytes
        )
        if not ok or payload is None:
            return False
        # Deep-check block hashes
        from quantum_blockchain.blockchain import Block, Blockchain

        tmp = Blockchain(ledger_path=":memory:", difficulty=payload["difficulty"])
        tmp.chain = [Block.from_dict(b) for b in payload["chain"]]
        tmp.balances = payload["balances"]
        return tmp.is_valid()

    # ------------------------------------------------------------------
    # Full restore (with automatic integrity check)
    # ------------------------------------------------------------------

    def restore_from_ledger(
        self,
        ledger_backup: Path | str,
        passphrase: str,
        wallet_backup: Optional[Path | str] = None,
        wallet_output: Optional[Path | str] = None,
    ) -> bool:
        """
        Restore from a plain ledger backup.

        * Validates chain integrity *before* overwriting the live ledger.
        * Optionally decrypts and restores the wallet backup.
        * Returns True on success.
        """
        if not self.verify_backup(ledger_backup):
            return False
        ok = self.blockchain.restore(ledger_backup)
        if not ok:
            return False
        if wallet_backup and wallet_output:
            self.wallet_manager.restore_encrypted(
                wallet_backup, wallet_output, passphrase=passphrase
            )
        return True

    def restore_from_snapshot(
        self,
        snapshot_path: Path | str,
        passphrase: str,
        wallet_backup: Optional[Path | str] = None,
        wallet_output: Optional[Path | str] = None,
        ledger_output: Optional[Path | str] = None,
    ) -> bool:
        """
        Restore from a signed chain snapshot.

        * Verifies HMAC signature.
        * Validates block hash chain.
        * Rebuilds and saves the ledger.
        * Optionally restores the wallet.
        * Returns True on success.
        """
        dest = Path(ledger_output) if ledger_output else self.blockchain.ledger_path
        bc = ChainSnapshot.import_snapshot(
            snapshot_path,
            self.wallet_manager.secret_bytes,
            ledger_path=dest,
        )
        if bc is None:
            return False
        # Adopt the restored chain
        self.blockchain.chain = bc.chain
        self.blockchain.balances = bc.balances
        self.blockchain.difficulty = bc.difficulty

        if wallet_backup and wallet_output:
            self.wallet_manager.restore_encrypted(
                wallet_backup, wallet_output, passphrase=passphrase
            )
        return True
