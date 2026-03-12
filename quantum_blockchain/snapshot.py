"""Signed blockchain snapshots using HMAC-SHA256."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any


def create_snapshot(chain_data: list[Any], secret_key: str) -> dict[str, Any]:
    """Create a signed snapshot dict from a serialisable chain list."""
    payload = json.dumps(chain_data, sort_keys=True).encode()
    signature = hmac.new(secret_key.encode(), payload, hashlib.sha256).hexdigest()
    return {
        "timestamp": time.time(),
        "chain": chain_data,
        "signature": signature,
    }


def verify_snapshot(snapshot: dict[str, Any], secret_key: str) -> bool:
    """Return True if the snapshot's HMAC signature is valid."""
    chain_data = snapshot.get("chain", [])
    expected_sig = snapshot.get("signature", "")
    payload = json.dumps(chain_data, sort_keys=True).encode()
    computed_sig = hmac.new(secret_key.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed_sig, str(expected_sig))
