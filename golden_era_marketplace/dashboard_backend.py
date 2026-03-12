import json
import random
from pathlib import Path

from flask import Flask, jsonify, redirect, send_file

app = Flask(__name__)

# Use paths relative to this file so endpoints work regardless of CWD
BASE = Path(__file__).resolve().parent
FINTECH_DIR = BASE / "fintech"
wallet_file = FINTECH_DIR / "wallet.json"
nfts_file = FINTECH_DIR / "nfts.json"
passport_file = FINTECH_DIR / "passport.json"
ai_stats_file = FINTECH_DIR / "ai_stats.json"

# Static server host (frontend preview)
STATIC_HOST = "http://127.0.0.1:8000"


def load_json(path: Path):
    try:
        if not Path(path).exists():
            return {}
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_json(path: Path, data):
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        # swallow errors but log to stdout for visibility
        print(f"Failed to write JSON to {path}")


@app.route("/")
def index():
    index_path = BASE / "index.html"
    if index_path.exists():
        return send_file(index_path)
    return redirect(STATIC_HOST)


@app.route("/redirect")
def redirect_to_static():
    return redirect(STATIC_HOST)


# Simulate AI stats updates
def update_ai_stats():
    stats = load_json(ai_stats_file)
    stats.setdefault('curve', 0)
    stats.setdefault('stubb', 0)
    stats.setdefault('lyons', 0)
    stats['curve'] += random.randint(0, 5)
    stats['stubb'] += random.randint(0, 5)
    stats['lyons'] += random.randint(0, 5)
    save_json(ai_stats_file, stats)
    return stats


@app.route("/api/wallet")
def wallet():
    return jsonify(load_json(wallet_file))


@app.route("/api/nfts")
def nfts():
    return jsonify(load_json(nfts_file))


@app.route("/api/passport")
def passport():
    return jsonify(load_json(passport_file))


@app.route("/api/ai_stats")
def ai_stats():
    return jsonify(update_ai_stats())


if __name__ == "__main__":
    app.run(port=5000)
