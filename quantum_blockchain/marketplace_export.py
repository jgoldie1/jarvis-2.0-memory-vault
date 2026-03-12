"""Marketplace JSON export and import utilities."""

from __future__ import annotations

import json
from typing import Any


def export_to_json(data: Any, path: str) -> None:
    """Serialise *data* to a pretty-printed JSON file at *path*."""
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def import_from_json(path: str) -> Any:
    """Read and return the JSON content of the file at *path*."""
    with open(path) as fh:
        return json.load(fh)
