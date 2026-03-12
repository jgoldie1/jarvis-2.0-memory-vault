"""
test_quantum_blockchain.py – Tests for the quantum_blockchain package.

Covers:
  * blockchain core (blocks, hashing, mining, balances, contract states, ledger)
  * wallet generation and encrypted backups
  * signed chain snapshots
  * recovery with automatic integrity validation
  * marketplace data export and restore
  * peer node synchronisation
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quantum_blockchain.blockchain import (
    Block,
    Blockchain,
    SignedTransaction,
    TernaryContractState,
)
from quantum_blockchain.marketplace_export import MarketplaceExporter
from quantum_blockchain.recovery import RecoveryManager
from quantum_blockchain.snapshot import ChainSnapshot
from quantum_blockchain.wallet import WalletManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def wallet(tmp_dir: Path) -> WalletManager:
    wm = WalletManager(tmp_dir / "wallet.json")
    wm.create()
    return wm


@pytest.fixture()
def blockchain(tmp_dir: Path) -> Blockchain:
    bc = Blockchain(ledger_path=tmp_dir / "ledger.json", difficulty=1)
    return bc


# ---------------------------------------------------------------------------
# Ternary contract states
# ---------------------------------------------------------------------------

class TestTernaryContractState:
    def test_three_states_exist(self):
        assert TernaryContractState.PENDING.value == "PENDING"
        assert TernaryContractState.ACTIVE.value == "ACTIVE"
        assert TernaryContractState.TERMINATED.value == "TERMINATED"

    def test_roundtrip_from_string(self):
        for s in ("PENDING", "ACTIVE", "TERMINATED"):
            assert TernaryContractState(s).value == s


# ---------------------------------------------------------------------------
# Signed transaction
# ---------------------------------------------------------------------------

class TestSignedTransaction:
    def test_sign_and_verify(self):
        key = b"test-secret"
        tx = SignedTransaction("Alice", "Bob", 10.0)
        tx.sign(key)
        assert tx.verify(key)

    def test_wrong_key_fails(self):
        key = b"correct-key"
        tx = SignedTransaction("Alice", "Bob", 10.0)
        tx.sign(key)
        assert not tx.verify(b"wrong-key")

    def test_unsigned_verify_false(self):
        tx = SignedTransaction("Alice", "Bob", 10.0)
        assert not tx.verify(b"any-key")

    def test_serialisation_roundtrip(self):
        key = b"roundtrip"
        tx = SignedTransaction("Alice", "Bob", 5.0, TernaryContractState.ACTIVE)
        tx.sign(key)
        d = tx.to_dict()
        tx2 = SignedTransaction.from_dict(d)
        assert tx2.verify(key)
        assert tx2.sender == "Alice"
        assert tx2.amount == 5.0
        assert tx2.contract_state == TernaryContractState.ACTIVE


# ---------------------------------------------------------------------------
# Block
# ---------------------------------------------------------------------------

class TestBlock:
    def test_hash_deterministic(self):
        b = Block(0, [], "0" * 64)
        h1 = b._compute_hash()
        h2 = b._compute_hash()
        assert h1 == h2

    def test_hash_changes_on_nonce(self):
        b = Block(0, [], "0" * 64, nonce=0)
        h0 = b._compute_hash()
        b.nonce = 1
        assert b._compute_hash() != h0

    def test_serialisation_roundtrip(self):
        tx = SignedTransaction("A", "B", 1.0)
        b = Block(1, [tx], "prev")
        b2 = Block.from_dict(b.to_dict())
        assert b2.hash == b.hash
        assert b2.index == 1
        assert b2.previous_hash == "prev"


# ---------------------------------------------------------------------------
# Blockchain – core
# ---------------------------------------------------------------------------

class TestBlockchain:
    def test_genesis_block_exists(self, blockchain: Blockchain):
        assert len(blockchain.chain) == 1
        assert blockchain.chain[0].previous_hash == Blockchain.GENESIS_HASH

    def test_mine_block(self, blockchain: Blockchain, wallet: WalletManager):
        block = blockchain.mine_block(wallet.address)
        assert len(blockchain.chain) == 2
        assert block.hash.startswith("0" * blockchain.difficulty)

    def test_balance_after_mining(self, blockchain: Blockchain, wallet: WalletManager):
        blockchain.mine_block(wallet.address, reward=50.0)
        assert blockchain.get_balance(wallet.address) == 50.0

    def test_terminated_tx_not_applied(
        self, blockchain: Blockchain, wallet: WalletManager
    ):
        blockchain.mine_block(wallet.address, reward=100.0)
        tx = SignedTransaction(
            wallet.address, "Carol", 30.0, TernaryContractState.TERMINATED
        )
        blockchain.add_transaction(tx)
        blockchain.mine_block("miner")
        # Terminated tx should not reduce wallet balance
        assert blockchain.get_balance(wallet.address) == 100.0

    def test_chain_validity(self, blockchain: Blockchain, wallet: WalletManager):
        blockchain.mine_block(wallet.address)
        assert blockchain.is_valid()

    def test_tampering_detected(self, blockchain: Blockchain, wallet: WalletManager):
        blockchain.mine_block(wallet.address)
        blockchain.chain[1].transactions[0].amount = 9999.0
        blockchain.chain[1].rehash()  # re-hash the block itself
        # The previous_hash link is still broken for block 2 if there were one;
        # here we check that the difficulty prefix check catches a fake hash.
        assert not blockchain.is_valid()

    def test_save_and_load_ledger(self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path):
        blockchain.mine_block(wallet.address)
        blockchain.save_ledger()
        bc2 = Blockchain(ledger_path=blockchain.ledger_path, difficulty=1)
        bc2.load_ledger()
        assert len(bc2.chain) == len(blockchain.chain)
        assert bc2.is_valid()

    def test_backup_and_restore(self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path):
        blockchain.mine_block(wallet.address)
        backup = tmp_dir / "backup.json"
        blockchain.backup(backup)
        assert blockchain.verify_backup(backup)
        # Tamper the live ledger
        blockchain.chain[1].nonce = 9999
        # Restore from backup
        ok = blockchain.restore(backup)
        assert ok
        assert blockchain.is_valid()

    def test_restore_rejects_invalid_backup(self, blockchain: Blockchain, tmp_dir: Path):
        bad = tmp_dir / "bad.json"
        bad.write_text('{"chain": [], "difficulty": 1, "balances": {}}')
        assert not blockchain.restore(bad)

    def test_generate_wallet(self, tmp_dir: Path):
        wp = tmp_dir / "gen_wallet.json"
        w = Blockchain.generate_wallet(wp)
        assert w["address"].startswith("AAM-")
        assert Path(wp).exists()


# ---------------------------------------------------------------------------
# Wallet – encrypted backup
# ---------------------------------------------------------------------------

class TestWallet:
    def test_create_wallet(self, wallet: WalletManager):
        assert wallet.address.startswith("AAM-")

    def test_encrypted_backup_roundtrip(self, wallet: WalletManager, tmp_dir: Path):
        enc = tmp_dir / "wallet.enc"
        wallet.backup_encrypted(enc, passphrase="test-pass")
        assert enc.exists()
        restored_path = tmp_dir / "restored_wallet.json"
        recovered = wallet.restore_encrypted(enc, restored_path, passphrase="test-pass")
        assert recovered["address"] == wallet.address

    def test_wrong_passphrase_raises(self, wallet: WalletManager, tmp_dir: Path):
        from cryptography.fernet import InvalidToken

        enc = tmp_dir / "wallet.enc"
        wallet.backup_encrypted(enc, passphrase="correct")
        with pytest.raises(InvalidToken):
            wallet.restore_encrypted(enc, tmp_dir / "out.json", passphrase="wrong")

    def test_backup_is_binary_with_salt(self, wallet: WalletManager, tmp_dir: Path):
        enc = tmp_dir / "wallet.enc"
        wallet.backup_encrypted(enc, passphrase="p")
        raw = enc.read_bytes()
        assert len(raw) > 16  # salt(16) + ciphertext


# ---------------------------------------------------------------------------
# Signed chain snapshots
# ---------------------------------------------------------------------------

class TestChainSnapshot:
    def test_save_and_verify(self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path):
        blockchain.mine_block(wallet.address)
        snap = ChainSnapshot(blockchain, wallet.secret_bytes)
        path = snap.save(tmp_dir / "snap.json")
        ok, payload = ChainSnapshot.load_and_verify(path, wallet.secret_bytes)
        assert ok
        assert payload is not None

    def test_tampered_snapshot_fails(self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path):
        blockchain.mine_block(wallet.address)
        snap = ChainSnapshot(blockchain, wallet.secret_bytes)
        path = snap.save(tmp_dir / "snap.json")
        # Corrupt the signature
        doc = json.loads(path.read_text())
        doc["signature"] = "deadbeef" * 8
        path.write_text(json.dumps(doc))
        ok, _ = ChainSnapshot.load_and_verify(path, wallet.secret_bytes)
        assert not ok

    def test_wrong_key_fails(self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path):
        blockchain.mine_block(wallet.address)
        snap = ChainSnapshot(blockchain, wallet.secret_bytes)
        path = snap.save(tmp_dir / "snap.json")
        ok, _ = ChainSnapshot.load_and_verify(path, b"wrong-key")
        assert not ok

    def test_import_snapshot(self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path):
        blockchain.mine_block(wallet.address)
        snap = ChainSnapshot(blockchain, wallet.secret_bytes)
        path = snap.save(tmp_dir / "snap.json")
        bc2 = ChainSnapshot.import_snapshot(
            path, wallet.secret_bytes, ledger_path=tmp_dir / "ledger2.json"
        )
        assert bc2 is not None
        assert bc2.is_valid()
        assert len(bc2.chain) == len(blockchain.chain)


# ---------------------------------------------------------------------------
# Recovery with automatic integrity validation
# ---------------------------------------------------------------------------

class TestRecoveryManager:
    def test_full_backup_creates_files(
        self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path
    ):
        blockchain.mine_block(wallet.address)
        rm = RecoveryManager(
            blockchain, wallet,
            backup_dir=tmp_dir / "bk",
            snapshot_dir=tmp_dir / "sn",
        )
        result = rm.full_backup(passphrase="p@ss")
        assert Path(result["ledger_backup"]).exists()
        assert Path(result["wallet_backup"]).exists()
        assert Path(result["snapshot"]).exists()

    def test_verify_backup(self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path):
        blockchain.mine_block(wallet.address)
        rm = RecoveryManager(
            blockchain, wallet,
            backup_dir=tmp_dir / "bk",
            snapshot_dir=tmp_dir / "sn",
        )
        result = rm.full_backup(passphrase="p")
        assert rm.verify_backup(result["ledger_backup"])

    def test_verify_snapshot(self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path):
        blockchain.mine_block(wallet.address)
        rm = RecoveryManager(
            blockchain, wallet,
            backup_dir=tmp_dir / "bk",
            snapshot_dir=tmp_dir / "sn",
        )
        result = rm.full_backup(passphrase="p")
        assert rm.verify_snapshot(result["snapshot"])

    def test_restore_from_ledger(
        self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path
    ):
        blockchain.mine_block(wallet.address)
        rm = RecoveryManager(
            blockchain, wallet,
            backup_dir=tmp_dir / "bk",
            snapshot_dir=tmp_dir / "sn",
        )
        result = rm.full_backup(passphrase="p")
        # Corrupt live chain
        blockchain.chain[1].nonce = 999
        ok = rm.restore_from_ledger(result["ledger_backup"], passphrase="p")
        assert ok
        assert blockchain.is_valid()

    def test_restore_from_snapshot(
        self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path
    ):
        blockchain.mine_block(wallet.address)
        rm = RecoveryManager(
            blockchain, wallet,
            backup_dir=tmp_dir / "bk",
            snapshot_dir=tmp_dir / "sn",
        )
        result = rm.full_backup(passphrase="p")
        original_len = len(blockchain.chain)
        # Replace blockchain data with empty genesis
        blockchain.chain = blockchain.chain[:1]
        ok = rm.restore_from_snapshot(
            result["snapshot"],
            passphrase="p",
            ledger_output=str(blockchain.ledger_path),
        )
        assert ok
        assert len(blockchain.chain) == original_len


# ---------------------------------------------------------------------------
# Marketplace data export and restore
# ---------------------------------------------------------------------------

class TestMarketplaceExporter:
    def _make_data_dir(self, base: Path) -> Path:
        d = base / "fintech"
        d.mkdir()
        (d / "wallet.json").write_text(json.dumps({"balance": 100}))
        (d / "transactions.json").write_text(json.dumps({"transactions": []}))
        return d

    def test_export_creates_archive(self, tmp_dir: Path, wallet: WalletManager):
        data_dir = self._make_data_dir(tmp_dir)
        exp = MarketplaceExporter(data_dir, secret_key=wallet.secret_bytes)
        archive = exp.export(tmp_dir / "exports" / "market.json")
        assert archive.exists()
        doc = json.loads(archive.read_text())
        assert "files" in doc
        assert "wallet.json" in doc["files"]

    def test_export_signature_present(self, tmp_dir: Path, wallet: WalletManager):
        data_dir = self._make_data_dir(tmp_dir)
        exp = MarketplaceExporter(data_dir, secret_key=wallet.secret_bytes)
        archive = exp.export(tmp_dir / "market.json")
        doc = json.loads(archive.read_text())
        assert doc["signature"] is not None

    def test_verify_archive(self, tmp_dir: Path, wallet: WalletManager):
        data_dir = self._make_data_dir(tmp_dir)
        exp = MarketplaceExporter(data_dir, secret_key=wallet.secret_bytes)
        archive = exp.export(tmp_dir / "market.json")
        assert MarketplaceExporter.verify_archive(archive, wallet.secret_bytes)

    def test_verify_rejects_tampered(self, tmp_dir: Path, wallet: WalletManager):
        data_dir = self._make_data_dir(tmp_dir)
        exp = MarketplaceExporter(data_dir, secret_key=wallet.secret_bytes)
        archive = exp.export(tmp_dir / "market.json")
        doc = json.loads(archive.read_text())
        doc["files"]["wallet.json"]["balance"] = 9999
        archive.write_text(json.dumps(doc))
        assert not MarketplaceExporter.verify_archive(archive, wallet.secret_bytes)

    def test_restore_roundtrip(self, tmp_dir: Path, wallet: WalletManager):
        data_dir = self._make_data_dir(tmp_dir)
        exp = MarketplaceExporter(data_dir, secret_key=wallet.secret_bytes)
        archive = exp.export(tmp_dir / "market.json")
        restore_dir = tmp_dir / "restored"
        ok = MarketplaceExporter.restore(archive, restore_dir, secret_key=wallet.secret_bytes)
        assert ok
        assert (restore_dir / "wallet.json").exists()

    def test_restore_without_key(self, tmp_dir: Path):
        data_dir = self._make_data_dir(tmp_dir)
        exp = MarketplaceExporter(data_dir, secret_key=None)
        archive = exp.export(tmp_dir / "market.json")
        restore_dir = tmp_dir / "restored_nokey"
        ok = MarketplaceExporter.restore(archive, restore_dir, secret_key=None)
        assert ok


# ---------------------------------------------------------------------------
# Peer node synchronisation
# ---------------------------------------------------------------------------

class TestPeerSync:
    def test_health_check(self, blockchain: Blockchain, wallet: WalletManager):
        from quantum_blockchain.peer_sync import PeerClient, PeerNode

        node = PeerNode(blockchain, wallet, host="127.0.0.1", port=0)
        # Use a free port
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()

        node.port = port
        node.start()
        try:
            client = PeerClient(f"http://127.0.0.1:{port}", blockchain)
            assert client.health_check()
        finally:
            node.stop()

    def test_sync_chain_longest_wins(
        self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path
    ):
        from quantum_blockchain.peer_sync import PeerClient, PeerNode
        import socket

        # Build a longer chain on the "server" side
        server_bc = Blockchain(ledger_path=tmp_dir / "server_ledger.json", difficulty=1)
        server_bc.mine_block(wallet.address)
        server_bc.mine_block(wallet.address)

        server_wm = WalletManager(tmp_dir / "server_wallet.json")
        server_wm.create()

        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()

        node = PeerNode(server_bc, server_wm, host="127.0.0.1", port=port)
        node.start()
        try:
            # Local blockchain has only genesis
            client_bc = Blockchain(
                ledger_path=tmp_dir / "client_ledger.json", difficulty=1
            )
            client = PeerClient(f"http://127.0.0.1:{port}", client_bc)
            updated = client.sync_chain()
            assert updated
            assert len(client_bc.chain) == len(server_bc.chain)
        finally:
            node.stop()

    def test_sync_chain_not_updated_if_shorter(
        self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path
    ):
        from quantum_blockchain.peer_sync import PeerClient, PeerNode
        import socket

        # Server has only genesis (shorter than client)
        server_bc = Blockchain(ledger_path=tmp_dir / "server_ledger.json", difficulty=1)
        server_wm = WalletManager(tmp_dir / "server_wallet.json")
        server_wm.create()

        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()

        node = PeerNode(server_bc, server_wm, host="127.0.0.1", port=port)
        node.start()
        try:
            # Client has more blocks
            blockchain.mine_block(wallet.address)
            client = PeerClient(f"http://127.0.0.1:{port}", blockchain)
            updated = client.sync_chain()
            assert not updated
        finally:
            node.stop()

    def test_submit_transaction(
        self, blockchain: Blockchain, wallet: WalletManager, tmp_dir: Path
    ):
        from quantum_blockchain.peer_sync import PeerClient, PeerNode
        import socket

        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()

        node = PeerNode(blockchain, wallet, host="127.0.0.1", port=port)
        node.start()
        try:
            tx = SignedTransaction("Alice", "Bob", 5.0)
            tx.sign(wallet.secret_bytes)
            client = PeerClient(f"http://127.0.0.1:{port}", blockchain)
            ok = client.submit_transaction(tx.to_dict())
            assert ok
            assert len(blockchain.pending_transactions) == 1
        finally:
            node.stop()
