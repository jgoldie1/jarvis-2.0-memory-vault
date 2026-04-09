#!/usr/bin/env python3
"""Ultimate Python Copilot

Lightweight co-pilot that:
- periodically queries local AI modules for stats
- updates fintech JSONs (wallet, transactions, ai_stats)
- provides a minimal Flask HTTP API to surface live stats
- optional TTS notifications (pyttsx3)
- logs all actions to `ultimate_copilot.log`

Run from the repository root. Designed to be safe and non-destructive.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import random
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

try:
    from flask import Flask, jsonify, request
except Exception:  # pragma: no cover - flask may be missing
    Flask = None  # type: ignore

LOG = Path("ultimate_copilot.log")
ROOT = Path.cwd()
MARKET = ROOT / "golden_era_marketplace"
FINTECH = MARKET / "fintech"
AI_DIR = MARKET / "ai"

logging.basicConfig(
    filename=str(LOG),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def safe_load_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logging.exception("Failed to load JSON %s", path)
        return default


def safe_write_json(path: Path, payload: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        logging.exception("Failed to write JSON %s", path)


def import_ai_module(mod_path: Path, name: str):
    if not mod_path.exists():
        logging.warning("AI module missing: %s", mod_path)
        return None
    try:
        spec = importlib.util.spec_from_file_location(name, str(mod_path))
        if spec is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return module
    except Exception:
        logging.exception("Failed to import AI module %s", mod_path)
        return None


class UltimateCopilot:
    def __init__(self, interval: int = 10, tts: bool = False):
        self.interval = interval
        self.running = False
        self.tts_enabled = tts
        self.ai_names = [d.name for d in (AI_DIR.glob("*")) if d.is_dir()]
        if not self.ai_names:
            # fallback to known names
            self.ai_names = ["curve", "stubb", "lyons"]

        self.ai_modules: Dict[str, Any] = {}
        self._load_ai_modules()

    def _load_ai_modules(self):
        for name in self.ai_names:
            path = AI_DIR / name / f"{name}_ai.py"
            mod = import_ai_module(path, f"ai_{name}")
            if mod:
                self.ai_modules[name] = mod
            else:
                self.ai_modules[name] = None

    def _call_update_stats(self, name: str):
        mod = self.ai_modules.get(name)
        if not mod:
            return {name: 0}
        try:
            if hasattr(mod, "update_stats"):
                return mod.update_stats()
            return {name: 0}
        except Exception:
            logging.exception("AI module %s errored", name)
            return {name: 0}

    def _update_ai_stats(self):
        stats = {}
        for name in self.ai_modules:
            stats.update(self._call_update_stats(name))
        ai_stats_path = FINTECH / "ai_stats.json"
        safe_write_json(ai_stats_path, stats)
        logging.info("Updated ai_stats: %s", stats)
        return stats

    def _update_fintech(self):
        wallet_path = FINTECH / "wallet.json"
        tx_path = FINTECH / "transactions.json"

        wallet = safe_load_json(wallet_path, {"balance": 0})
        txs = safe_load_json(tx_path, {"transactions": []})

        # Simulate small random activity
        change = round(random.uniform(-5.0, 10.0), 2)
        wallet["balance"] = round(wallet.get("balance", 0) + change, 2)

        if abs(change) > 0.01:
            entry = {
                "time": datetime.utcnow().isoformat() + "Z",
                "amount": change,
                "desc": random.choice(["coffee", "nft-sale", "tip", "refund", "mint"]),
            }
            txs.setdefault("transactions", []).insert(0, entry)
            # keep recent 200
            txs["transactions"] = txs["transactions"][:200]

        safe_write_json(wallet_path, wallet)
        safe_write_json(tx_path, txs)
        logging.info(
            "Updated wallet: %s, txs: %d", wallet, len(txs.get("transactions", []))
        )
        return wallet, txs

    def _speak(self, text: str):
        if not self.tts_enabled:
            return
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception:
            logging.exception("TTS failed")

    def cycle(self):
        stats = self._update_ai_stats()
        wallet, txs = self._update_fintech()
        # notify on low balance
        if wallet.get("balance", 0) < 0:
            msg = f"Alert: Negative balance {wallet['balance']}"
            logging.warning(msg)
            self._speak(msg)
        return {"ai": stats, "wallet": wallet, "transactions": txs}

    def start(self):
        if self.running:
            return
        self.running = True

        def _loop():
            logging.info("UltimateCopilot loop starting (interval=%s)", self.interval)
            while self.running:
                try:
                    self.cycle()
                except Exception:
                    logging.exception("Cycle failed")
                time.sleep(self.interval)

        t = threading.Thread(target=_loop, daemon=True)
        t.start()

    def stop(self):
        self.running = False


app = Flask(__name__) if Flask else None
copilot = UltimateCopilot(interval=10, tts=False)


if app:
    # Simple API key support: if ULTIMATE_API_KEY env var is set, require it in
    # header 'X-API-Key' for sensitive endpoints. Also add CORS header for local
    # frontend polling.
    import os

    API_KEY = os.environ.get("ULTIMATE_API_KEY")

    def require_key():
        if not API_KEY:
            return True
        key = request.headers.get("X-API-Key") or request.args.get("api_key")
        return key == API_KEY

    def json_response(payload, status=200):
        resp = jsonify(payload)
        resp.status_code = status
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    @app.route("/api/stats")
    def api_stats():
        if not require_key():
            return json_response({"ok": False, "message": "unauthorized"}, 401)
        ai = safe_load_json(FINTECH / "ai_stats.json", {})
        wallet = safe_load_json(FINTECH / "wallet.json", {"balance": 0})
        txs = safe_load_json(FINTECH / "transactions.json", {"transactions": []})
        return json_response({"ai": ai, "wallet": wallet, "transactions": txs})

    @app.route("/api/trigger", methods=["POST"])
    def api_trigger():
        if not require_key():
            return json_response({"ok": False, "message": "unauthorized"}, 401)
        data = request.get_json(silent=True) or {}
        action = data.get("action", "tick")
        if action == "tick":
            result = copilot.cycle()
            return json_response({"ok": True, "result": result})
        return json_response({"ok": False, "message": "unknown action"}, 400)


def main(run_server: bool = True):
    copilot.start()
    logging.info("UltimateCopilot started")
    if run_server and app:
        # run Flask in a thread so main remains interactive
        def _run():
            app.run(host="0.0.0.0", port=5002)

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping UltimateCopilot")
        copilot.stop()


if __name__ == "__main__":
    main(run_server=True)
