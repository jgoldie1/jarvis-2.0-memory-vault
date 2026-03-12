"""
snapshot.py – **Signed chain snapshots**.

A snapshot is a JSON export of the entire chain signed with
HMAC-SHA256.  The signature is embedded in the file so that any
consumer can verify authenticity before importing.

Paste-ready usage
-----------------
    from quantum_blockchain.snapshot import ChainSnapshot
    snap = ChainSnapshot(chain, secret_key=wallet.secret_bytes)
    path = snap.save("snapshots/snap_001.json")

    # Verify later:
    ok, chain_data = ChainSnapshot.load_and_verify(path, secret_key=...)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from quantum_blockchain.blockchain import Blockchain


# ---------------------------------------------------------------------------
# ChainSnapshot
# ---------------------------------------------------------------------------

class ChainSnapshot:
    """Produce and verify cryptographically signed chain snapshots."""

    VERSION = 1

    def __init__(
        self,
        blockchain: Blockchain,
        secret_key: bytes,
    ) -> None:
        self.blockchain = blockchain
        self.secret_key = secret_key

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def save(self, path: Path | str) -> Path:
        """Serialise the chain, sign it, and write to *path*."""
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        payload = self._build_payload()
        signature = self._sign(payload)

        doc: Dict[str, Any] = {
            "version": self.VERSION,
            "created_at": time.time(),
            "signature": signature,
            "payload": payload,
        }
        dest.write_text(json.dumps(doc, indent=2))
        return dest

    def _build_payload(self) -> Dict[str, Any]:
        return {
            "difficulty": self.blockchain.difficulty,
            "balances": self.blockchain.balances,
            "chain": [b.to_dict() for b in self.blockchain.chain],
        }

    def _sign(self, payload: Dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hmac.new(
            self.secret_key,
            canonical.encode(),
            hashlib.sha256,
        ).hexdigest()

    def signed_dict(self) -> Dict[str, Any]:
        """Return a ``{signature, payload}`` dict without writing to disk."""
        payload = self._build_payload()
        return {"signature": self._sign(payload), "payload": payload}

    # ------------------------------------------------------------------
    # Verify / load
    # ------------------------------------------------------------------

    @staticmethod
    def load_and_verify(
        path: Path | str,
        secret_key: bytes,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Load a snapshot and verify its HMAC signature.

        Returns ``(True, payload_dict)`` on success,
        ``(False, None)`` if the signature does not match.
        """
        doc = json.loads(Path(path).read_text())
        payload = doc["payload"]
        stored_sig = doc["signature"]

        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected = hmac.new(
            secret_key,
            canonical.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, stored_sig):
            return False, None
        return True, payload

    # ------------------------------------------------------------------
    # Import verified snapshot into a Blockchain instance
    # ------------------------------------------------------------------

    @staticmethod
    def import_snapshot(
        path: Path | str,
        secret_key: bytes,
        ledger_path: Path | str = "ledger_restored.json",
    ) -> Optional[Blockchain]:
        """
        Verify the snapshot at *path*, reconstruct a Blockchain, validate
        chain integrity, then save the ledger to *ledger_path*.

        Returns the Blockchain on success, None if verification fails.
        """
        from quantum_blockchain.blockchain import Block  # avoid circular

        ok, payload = ChainSnapshot.load_and_verify(path, secret_key)
        if not ok or payload is None:
            return None

        bc = Blockchain(ledger_path=ledger_path, difficulty=payload["difficulty"])
        bc.chain = [Block.from_dict(b) for b in payload["chain"]]
        bc.balances = payload["balances"]

        if not bc.is_valid():
            return None

        bc.save_ledger()
        return bc
