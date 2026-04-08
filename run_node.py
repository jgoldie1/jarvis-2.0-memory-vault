#!/usr/bin/env python3
"""run_node.py — Jarvis 2.0 Memory Vault demo node.

Loads all Golden Era Marketplace AI modules, runs one stats cycle,
updates the fintech JSON files, and prints a live summary.

Usage::

    python3 run_node.py

Optional flags:
    --serve     also start the Flask dashboard on port 5000
    --cycles N  run N update cycles (default: 1; 0 = loop until Ctrl-C)
    --interval SECS  seconds between cycles when looping (default: 10)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKET = ROOT / "golden_era_marketplace"
FINTECH = MARKET / "fintech"
AI_DIR = MARKET / "ai"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("run_node")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_ai_module(name: str):
    """Import *name*_ai.py from the marketplace AI directory."""
    path = AI_DIR / name / f"{name}_ai.py"
    if not path.exists():
        log.warning("AI module not found: %s", path)
        return None
    spec = importlib.util.spec_from_file_location(f"ai_{name}", str(path))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    except Exception as exc:  # pragma: no cover
        log.error("Failed to load AI module %s: %s", name, exc)
        return None


def _discover_ai_names() -> list[str]:
    if AI_DIR.is_dir():
        names = sorted(d.name for d in AI_DIR.iterdir() if d.is_dir())
        if names:
            return names
    return ["curve", "stubb", "lyons"]


def _read_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class Node:
    """Minimal Jarvis 2.0 node that collects AI stats and updates fintech data."""

    def __init__(self) -> None:
        self.ai_names = _discover_ai_names()
        self.modules = {name: _load_ai_module(name) for name in self.ai_names}
        loaded = sum(1 for m in self.modules.values() if m is not None)
        log.info("Node ready — %d/%d AI modules loaded: %s",
                 loaded, len(self.ai_names), ", ".join(self.ai_names))

    def collect_stats(self) -> dict:
        stats: dict = {}
        for name, mod in self.modules.items():
            if mod and hasattr(mod, "update_stats"):
                try:
                    result = mod.update_stats()
                    if isinstance(result, dict):
                        stats.update(result)
                    else:
                        stats[name] = result
                except Exception as exc:
                    log.warning("update_stats() failed for %s: %s", name, exc)
                    stats[name] = 0
            else:
                stats[name] = 0
        return stats

    def cycle(self) -> dict:
        stats = self.collect_stats()
        _write_json(FINTECH / "ai_stats.json", stats)
        wallet = _read_json(FINTECH / "wallet.json", {"balance": 0})
        _write_json(FINTECH / "wallet.json", wallet)
        log.info("Cycle complete — AI stats: %s | wallet balance: %s",
                 stats, wallet.get("balance", 0))
        return {"ai_stats": stats, "wallet": wallet}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Jarvis 2.0 Memory Vault — demo node runner",
    )
    parser.add_argument(
        "--serve", action="store_true",
        help="Start the Flask dashboard on port 5000 after running cycles",
    )
    parser.add_argument(
        "--cycles", type=int, default=1, metavar="N",
        help="Number of update cycles to run (0 = loop forever)",
    )
    parser.add_argument(
        "--interval", type=float, default=10.0, metavar="SECS",
        help="Seconds between cycles when running more than one cycle",
    )
    return parser.parse_args(argv)


def _start_flask_server() -> None:  # pragma: no cover
    backend = MARKET / "dashboard_backend.py"
    if not backend.exists():
        log.warning("dashboard_backend.py not found; skipping --serve")
        return
    spec = importlib.util.spec_from_file_location("dashboard_backend", str(backend))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    log.info("Starting Flask dashboard on http://localhost:5000 (Ctrl-C to stop)")
    mod.app.run(port=5000)


def main(argv=None) -> int:
    args = _parse_args(argv)
    node = Node()

    if args.cycles == 0:
        # loop forever
        log.info("Entering continuous loop (Ctrl-C to stop, interval=%.1fs)", args.interval)
        try:
            while True:
                node.cycle()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            log.info("Stopped.")
    else:
        for i in range(args.cycles):
            if i > 0:
                time.sleep(args.interval)
            node.cycle()

    if args.serve:  # pragma: no cover
        _start_flask_server()

    return 0


if __name__ == "__main__":
    sys.exit(main())
