"""
peer_sync.py – **Simple peer-node synchronisation**.

Each peer exposes a minimal HTTP API:
  GET  /chain          → JSON chain export
  GET  /snapshot       → latest signed snapshot
  POST /submit_tx      → add a signed transaction

``PeerNode`` runs a lightweight ``http.server``-based server (no external
deps) in a background thread.  ``PeerClient`` pulls the chain from a
remote peer and merges it if it is longer *and* valid.

Paste-ready usage
-----------------
    # Start a local peer node:
    from quantum_blockchain.peer_sync import PeerNode
    node = PeerNode(blockchain, wallet_manager, host="0.0.0.0", port=8765)
    node.start()

    # Sync from a remote peer:
    from quantum_blockchain.peer_sync import PeerClient
    client = PeerClient("http://192.168.1.10:8765", blockchain)
    updated = client.sync_chain()
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional

from quantum_blockchain.blockchain import Block, Blockchain
from quantum_blockchain.snapshot import ChainSnapshot
from quantum_blockchain.wallet import WalletManager


# ---------------------------------------------------------------------------
# HTTP request handler
# ---------------------------------------------------------------------------

def _make_handler(
    blockchain: Blockchain, wallet_manager: WalletManager
) -> type:
    """Return a request-handler class bound to the given blockchain."""

    class _Handler(BaseHTTPRequestHandler):
        _bc = blockchain
        _wm = wallet_manager

        def log_message(self, fmt: str, *args: Any) -> None:  # silence default log
            pass

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/chain":
                data = json.dumps(
                    {
                        "difficulty": self._bc.difficulty,
                        "balances": self._bc.balances,
                        "chain": [b.to_dict() for b in self._bc.chain],
                    }
                ).encode()
                self._respond(200, data)

            elif self.path == "/snapshot":
                snap = ChainSnapshot(self._bc, self._wm.secret_bytes)
                data = json.dumps(snap.signed_dict()).encode()
                self._respond(200, data)

            elif self.path == "/health":
                self._respond(200, b'{"status":"ok"}')

            else:
                self._respond(404, b'{"error":"not found"}')

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/submit_tx":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                try:
                    tx_data = json.loads(body.decode())
                    from quantum_blockchain.blockchain import SignedTransaction
                    tx = SignedTransaction.from_dict(tx_data)
                    self._bc.add_transaction(tx)
                    self._respond(200, b'{"status":"accepted"}')
                except (json.JSONDecodeError, KeyError, ValueError):
                    self._respond(400, b'{"error":"invalid transaction"}')
            else:
                self._respond(404, b'{"error":"not found"}')

        def _respond(self, code: int, body: bytes) -> None:
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return _Handler


# ---------------------------------------------------------------------------
# PeerNode
# ---------------------------------------------------------------------------

class PeerNode:
    """
    Lightweight HTTP node that exposes the blockchain over the local network.
    Runs in a daemon thread; safe to call ``start()`` / ``stop()`` from any
    thread.
    """

    def __init__(
        self,
        blockchain: Blockchain,
        wallet_manager: WalletManager,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        self.blockchain = blockchain
        self.wallet_manager = wallet_manager
        self.host = host
        self.port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start serving in a background daemon thread."""
        handler = _make_handler(self.blockchain, self.wallet_manager)
        self._server = HTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Shut down the server."""
        if self._server:
            self._server.shutdown()
            self._server = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


# ---------------------------------------------------------------------------
# PeerClient
# ---------------------------------------------------------------------------

class PeerClient:
    """
    Pull the chain from a remote peer and merge (longest-valid-chain rule).
    """

    def __init__(
        self,
        peer_url: str,
        blockchain: Blockchain,
        timeout: int = 10,
    ) -> None:
        self.peer_url = peer_url.rstrip("/")
        self.blockchain = blockchain
        self.timeout = timeout

    def _get(self, path: str) -> Optional[Dict[str, Any]]:
        url = self.peer_url + path
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, json.JSONDecodeError, OSError):
            return None

    def health_check(self) -> bool:
        """Return True if the peer responds to /health."""
        result = self._get("/health")
        return result is not None and result.get("status") == "ok"

    def sync_chain(self) -> bool:
        """
        Fetch remote chain and replace local chain if remote is longer
        *and* passes integrity validation.

        Returns True if the local chain was updated.
        """
        data = self._get("/chain")
        if not data:
            return False

        remote_blocks = [Block.from_dict(b) for b in data.get("chain", [])]
        if len(remote_blocks) <= len(self.blockchain.chain):
            return False  # local is at least as long

        # Validate remote chain before adopting it
        tmp = Blockchain(
            ledger_path=self.blockchain.ledger_path,
            difficulty=data.get("difficulty", self.blockchain.difficulty),
        )
        tmp.chain = remote_blocks
        tmp.balances = data.get("balances", {})
        if not tmp.is_valid():
            return False

        self.blockchain.chain = remote_blocks
        self.blockchain.balances = tmp.balances
        self.blockchain.difficulty = tmp.difficulty
        self.blockchain.save_ledger()
        return True

    def submit_transaction(self, tx_dict: Dict[str, Any]) -> bool:
        """
        POST a signed transaction to the remote peer.

        Returns True if the peer accepted it.
        """
        url = self.peer_url + "/submit_tx"
        body = json.dumps(tx_dict).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode())
                return result.get("status") == "accepted"
        except (urllib.error.URLError, json.JSONDecodeError, OSError):
            return False
