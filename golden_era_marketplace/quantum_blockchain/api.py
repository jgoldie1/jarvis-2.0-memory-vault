"""Flask API layer for the Quantum Blockchain – All American Marketplace.

Endpoints
---------
GET /status
    Returns the current node status: chain length, difficulty, mining reward,
    number of pending transactions, and chain validity.

GET /chain
    Returns the full serialised blockchain (every block and its transactions).

GET /balance/<address>
    Returns the confirmed coin balance for the given wallet address.

Usage
-----
    python -m golden_era_marketplace.quantum_blockchain.api

    or via gunicorn:
    gunicorn 'golden_era_marketplace.quantum_blockchain.api:create_app()'
"""

from __future__ import annotations

from flask import Flask, jsonify

from .blockchain import Blockchain

# Module-level singleton – shared across all requests in the same process.
_blockchain: Blockchain = Blockchain()


def get_blockchain() -> Blockchain:
    """Return the shared blockchain instance (replaceable in tests)."""
    return _blockchain


def create_app(blockchain: Blockchain | None = None) -> Flask:
    """Application factory.

    Args:
        blockchain: Optional blockchain instance to use (useful for testing).
    """
    app = Flask(__name__)

    bc = blockchain if blockchain is not None else get_blockchain()

    @app.route("/status", methods=["GET"])
    def status():
        """Return node status information."""
        return jsonify(
            {
                "status": "running",
                "chain_length": len(bc.chain),
                "difficulty": bc.DIFFICULTY,
                "mining_reward": bc.MINING_REWARD,
                "pending_transactions": len(bc.pending_transactions),
                "is_valid": bc.is_valid(),
            }
        )

    @app.route("/chain", methods=["GET"])
    def chain():
        """Return the full blockchain."""
        return jsonify(bc.to_dict())

    @app.route("/balance/<address>", methods=["GET"])
    def balance(address: str):
        """Return the confirmed balance for *address*."""
        return jsonify(
            {
                "address": address,
                "balance": bc.get_balance(address),
            }
        )

    return app


if __name__ == "__main__":  # pragma: no cover
    app = create_app()
    # Bind to localhost by default; run behind a reverse proxy in production.
    app.run(host="127.0.0.1", port=5003, debug=False)
