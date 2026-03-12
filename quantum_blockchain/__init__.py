"""
quantum_blockchain – All American Marketplace blockchain package.

Modules
-------
blockchain          Core chain: blocks, proof-of-work, signed transactions,
                    balances, ternary contract states, saved ledger.
wallet              Wallet generation and *encrypted* wallet backups.
snapshot            Signed chain snapshots.
recovery            Restore with automatic chain-integrity validation.
marketplace_export  Marketplace data export and restore.
peer_sync           Simple peer-node synchronisation (HTTP-based).
cli                 Unified command-line entry point.
"""

from quantum_blockchain.blockchain import (  # noqa: F401
    Block,
    Blockchain,
    SignedTransaction,
    TernaryContractState,
)

__all__ = [
    "Block",
    "Blockchain",
    "SignedTransaction",
    "TernaryContractState",
]
