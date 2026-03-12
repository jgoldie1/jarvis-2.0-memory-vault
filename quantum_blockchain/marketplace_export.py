"""
marketplace_export.py – **Marketplace data export and restore**.

Exports the full state of the marketplace (products, orders, AI stats,
fintech records) to a portable JSON archive, optionally signed with the
wallet secret.  Can be imported on any node for a complete restore.

Paste-ready usage
-----------------
    from quantum_blockchain.marketplace_export import MarketplaceExporter
    exp = MarketplaceExporter("golden_era_marketplace/fintech/",
                              secret_key=wallet.secret_bytes)
    archive = exp.export("exports/marketplace_20260312.json")

    # Restore on another node:
    MarketplaceExporter.restore(archive, "golden_era_marketplace/fintech/",
                                 secret_key=wallet.secret_bytes)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# MarketplaceExporter
# ---------------------------------------------------------------------------

class MarketplaceExporter:
    """
    Export and restore marketplace data directories.

    The export format is:
    {
      "version": 1,
      "exported_at": <unix timestamp>,
      "signature": "<hmac-sha256-hex>",
      "files": {
          "<relative path>": <parsed JSON content or raw string>,
          ...
      }
    }
    """

    VERSION = 1
    # File extensions that are parsed as JSON; others stored as raw text.
    JSON_EXTENSIONS = {".json"}

    def __init__(
        self,
        data_dir: Path | str,
        secret_key: Optional[bytes] = None,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.secret_key = secret_key

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export(self, archive_path: Path | str) -> Path:
        """
        Collect all files under *data_dir*, sign the archive, and write it
        to *archive_path*.
        """
        dest = Path(archive_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        files = self._collect_files()
        signature = self._sign_files(files) if self.secret_key else None

        doc: Dict[str, Any] = {
            "version": self.VERSION,
            "exported_at": time.time(),
            "signature": signature,
            "source_dir": str(self.data_dir),
            "files": files,
        }
        dest.write_text(json.dumps(doc, indent=2))
        return dest

    def _collect_files(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        if not self.data_dir.exists():
            return result
        for fp in sorted(self.data_dir.rglob("*")):
            if not fp.is_file():
                continue
            rel = str(fp.relative_to(self.data_dir))
            if fp.suffix in self.JSON_EXTENSIONS:
                try:
                    result[rel] = json.loads(fp.read_text())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    result[rel] = fp.read_text(errors="replace")
            else:
                result[rel] = fp.read_text(errors="replace")
        return result

    def _sign_files(self, files: Dict[str, Any]) -> str:
        canonical = json.dumps(files, sort_keys=True, separators=(",", ":"))
        return hmac.new(
            self.secret_key,  # type: ignore[arg-type]
            canonical.encode(),
            hashlib.sha256,
        ).hexdigest()

    # ------------------------------------------------------------------
    # Verify
    # ------------------------------------------------------------------

    @staticmethod
    def verify_archive(
        archive_path: Path | str,
        secret_key: bytes,
    ) -> bool:
        """Return True if the stored HMAC matches the files payload."""
        doc = json.loads(Path(archive_path).read_text())
        stored = doc.get("signature")
        if stored is None:
            return False
        canonical = json.dumps(
            doc["files"], sort_keys=True, separators=(",", ":")
        )
        expected = hmac.new(
            secret_key,
            canonical.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, stored)

    # ------------------------------------------------------------------
    # Restore
    # ------------------------------------------------------------------

    @staticmethod
    def restore(
        archive_path: Path | str,
        output_dir: Path | str,
        secret_key: Optional[bytes] = None,
    ) -> bool:
        """
        Restore all files from *archive_path* into *output_dir*.

        If *secret_key* is provided, the archive signature is verified
        before writing any files.  Returns True on success.
        """
        if secret_key and not MarketplaceExporter.verify_archive(
            archive_path, secret_key
        ):
            return False

        doc = json.loads(Path(archive_path).read_text())
        base = Path(output_dir)
        base.mkdir(parents=True, exist_ok=True)

        for rel, content in doc["files"].items():
            dest = base / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, (dict, list)):
                dest.write_text(json.dumps(content, indent=2))
            else:
                dest.write_text(str(content))
        return True
