#!/usr/bin/env python3
"""run_node.py – Entry point for the Jarvis marketplace node.

Performs a quick health-check of the Golden Era Marketplace node:
- Ensures required directories and JSON files are present.
- Imports the copilot helper to verify the module loads correctly.
- Prints a ready message and exits cleanly.

Run once to bootstrap the workspace, then use ultimate_copilot.py to
start the long-running server and AI cycle.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKET = ROOT / "golden_era_marketplace"
FINTECH = MARKET / "fintech"

REQUIRED_DIRS = [
    MARKET / "css",
    MARKET / "js",
    MARKET / "images",
    MARKET / "images_processed",
    FINTECH,
    MARKET / "ai" / "curve",
    MARKET / "ai" / "stubb",
    MARKET / "ai" / "lyons",
]

DEFAULT_JSON: dict[str, object] = {
    str(FINTECH / "wallet.json"): {"balance": 0},
    str(FINTECH / "transactions.json"): {"transactions": []},
    str(FINTECH / "ai_stats.json"): {"curve": 0, "stubb": 0, "lyons": 0},
}


def _ensure_dirs() -> None:
    for d in REQUIRED_DIRS:
        d.mkdir(parents=True, exist_ok=True)


def _ensure_json_files() -> None:
    for path_str, default in DEFAULT_JSON.items():
        p = Path(path_str)
        if not p.exists():
            p.write_text(json.dumps(default, indent=2), encoding="utf-8")


def _check_copilot_import() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "ultimate_copilot", str(ROOT / "ultimate_copilot.py")
    )
    if spec is None:
        print("WARNING: Could not locate ultimate_copilot.py", file=sys.stderr)
        return
    mod = importlib.util.module_from_spec(spec)
    # Execute only up to module-level definitions (no side effects from main()).
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore[union-attr]


def main() -> None:
    print("🚀 Jarvis node initializing…")
    _ensure_dirs()
    _ensure_json_files()
    _check_copilot_import()
    print("✅ Node ready.")


if __name__ == "__main__":
    main()
