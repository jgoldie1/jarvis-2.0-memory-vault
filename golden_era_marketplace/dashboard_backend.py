import json
import time
import random
from flask import Flask, jsonify

app = Flask(__name__)

wallet_file = "fintech/wallet.json"
nfts_file = "fintech/nfts.json"
passport_file = "fintech/passport.json"
ai_stats_file = "fintech/ai_stats.json"

def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# Simulate AI stats updates
def update_ai_stats():
    stats = load_json(ai_stats_file)
    stats.setdefault('curve', 0)
    stats.setdefault('stubb', 0)
    stats.setdefault('lyons', 0)
    stats['curve'] += random.randint(0,5)
    stats['stubb'] += random.randint(0,5)
    stats['lyons'] += random.randint(0,5)
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
