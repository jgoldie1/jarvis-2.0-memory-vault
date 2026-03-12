"""
wallet.py – Wallet generation and **encrypted** wallet backups.

Encryption uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256)
from the ``cryptography`` package.  A passphrase-derived key is created
with PBKDF2-HMAC-SHA256 so the backup is safe to store offline.

Paste-ready usage
-----------------
    from quantum_blockchain.wallet import WalletManager
    wm = WalletManager("wallets/primary.json")
    wallet = wm.create()
    wm.backup_encrypted("backups/primary.enc", passphrase="my-secret")
    wm.restore_encrypted("backups/primary.enc", "wallets/restored.json",
                          passphrase="my-secret")
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Dict

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# ---------------------------------------------------------------------------
# Key derivation helpers
# ---------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 390_000  # NIST 2023 minimum recommendation


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Return a 32-byte URL-safe base64-encoded Fernet key."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


# ---------------------------------------------------------------------------
# WalletManager
# ---------------------------------------------------------------------------

class WalletManager:
    """Create, load, back up, and restore wallets."""

    def __init__(self, wallet_path: Path | str = "wallet.json") -> None:
        self.wallet_path = Path(wallet_path)
        self._wallet: Dict[str, str] | None = None

    # ------------------------------------------------------------------
    # Create / load
    # ------------------------------------------------------------------

    def create(self) -> Dict[str, str]:
        """Generate a new wallet and persist it to *wallet_path*."""
        address = "AAM-" + hashlib.sha256(os.urandom(32)).hexdigest()[:24].upper()
        secret = hashlib.sha256(os.urandom(32)).hexdigest()
        self._wallet = {"address": address, "secret": secret}
        self._save()
        return dict(self._wallet)

    def load(self) -> Dict[str, str]:
        """Load wallet from *wallet_path*."""
        self._wallet = json.loads(self.wallet_path.read_text())
        return dict(self._wallet)

    def _save(self) -> None:
        self.wallet_path.parent.mkdir(parents=True, exist_ok=True)
        self.wallet_path.write_text(json.dumps(self._wallet, indent=2))

    @property
    def address(self) -> str:
        if self._wallet is None:
            raise RuntimeError("No wallet loaded – call create() or load() first.")
        return self._wallet["address"]

    @property
    def secret_bytes(self) -> bytes:
        if self._wallet is None:
            raise RuntimeError("No wallet loaded – call create() or load() first.")
        return bytes.fromhex(self._wallet["secret"])

    # ------------------------------------------------------------------
    # Encrypted backup
    # ------------------------------------------------------------------

    def backup_encrypted(
        self, backup_path: Path | str, passphrase: str
    ) -> Path:
        """
        Encrypt the wallet file and write it to *backup_path*.

        File format (binary):
            [16-byte salt][ciphertext…]
        """
        if self._wallet is None:
            self.load()
        dest = Path(backup_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        salt = os.urandom(16)
        key = _derive_key(passphrase, salt)
        fernet = Fernet(key)
        plaintext = json.dumps(self._wallet).encode()
        ciphertext = fernet.encrypt(plaintext)

        dest.write_bytes(salt + ciphertext)
        return dest

    def restore_encrypted(
        self,
        backup_path: Path | str,
        output_path: Path | str,
        passphrase: str,
    ) -> Dict[str, str]:
        """
        Decrypt *backup_path* and write the recovered wallet to *output_path*.

        Raises ``ValueError`` if the passphrase is wrong or the file is
        corrupted (Fernet raises ``cryptography.fernet.InvalidToken``).
        """
        raw = Path(backup_path).read_bytes()
        salt, ciphertext = raw[:16], raw[16:]
        key = _derive_key(passphrase, salt)
        fernet = Fernet(key)
        plaintext = fernet.decrypt(ciphertext)  # raises InvalidToken on failure
        wallet = json.loads(plaintext.decode())

        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(wallet, indent=2))
        self._wallet = wallet
        return dict(wallet)
