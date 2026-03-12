from __future__ import annotations

from typing import Any

from quantum_blockchain.blockchain import Block, Blockchain


class PeerSync:
    def __init__(self, blockchain: Blockchain) -> None:
        self._blockchain = blockchain
        self._peers: dict[str, list[dict[str, object]]] = {}

    def add_peer(self, peer_id: str, chain_data: list[dict[str, object]]) -> None:
        self._peers[peer_id] = chain_data

    def sync(self) -> bool:
        best_chain: list[Any] | None = None
        best_length = len(self._blockchain.chain)

        for chain_data in self._peers.values():
            if len(chain_data) > best_length and self._is_valid_chain(chain_data):
                best_length = len(chain_data)
                best_chain = chain_data

        if best_chain is not None:
            self._blockchain.chain = [
                Block(
                    index=int(b["index"]),
                    timestamp=float(b["timestamp"]),
                    data=dict(b["data"]),
                    previous_hash=str(b["previous_hash"]),
                    hash=str(b["hash"]),
                )
                for b in best_chain
            ]
            return True
        return False

    def _is_valid_chain(self, chain_data: list[Any]) -> bool:
        tmp = Blockchain.__new__(Blockchain)
        tmp.chain = [
            Block(
                index=int(b["index"]),
                timestamp=float(b["timestamp"]),
                data=dict(b["data"]),
                previous_hash=str(b["previous_hash"]),
                hash=str(b["hash"]),
            )
            for b in chain_data
        ]
        return tmp.is_valid()

    def get_peers(self) -> list[str]:
        return list(self._peers.keys())
