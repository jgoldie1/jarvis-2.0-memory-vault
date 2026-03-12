"""HMAC-SHA256 signed snapshots."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def sign_snapshot(data: Any, secret: str) -> str:
    """Return the HMAC-SHA256 hex digest of *data* signed with *secret*."""
    payload = json.dumps(data, sort_keys=True).encode()
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def verify_snapshot(data: Any, secret: str, signature: str) -> bool:
    """Return True if *signature* matches a freshly computed signature for *data*."""
    expected = sign_snapshot(data, secret)
    return hmac.compare_digest(expected, signature)
