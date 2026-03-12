"""Recovery manager: persist and retrieve named JSON snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RecoveryManager:
    """Save and load named recovery snapshots as JSON files."""

    def __init__(self, recovery_dir: str = ".recovery") -> None:
        self.recovery_dir = Path(recovery_dir)
        self.recovery_dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, data: Any) -> None:
        """Write *data* as JSON to a file named *name* inside the recovery directory."""
        path = self.recovery_dir / f"{name}.json"
        path.write_text(json.dumps(data, indent=2))

    def load(self, name: str) -> Any:
        """Read and return the JSON data stored under *name*."""
        path = self.recovery_dir / f"{name}.json"
        return json.loads(path.read_text())

    def list_backups(self) -> list[str]:
        """Return the names (without extension) of all saved snapshots."""
        return sorted(p.stem for p in self.recovery_dir.glob("*.json"))
