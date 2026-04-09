"""42 tests for the quantum_blockchain package."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from quantum_blockchain.blockchain import Block, Blockchain
from quantum_blockchain.marketplace_export import export_to_json, import_from_json
from quantum_blockchain.peer_sync import PeerSync
from quantum_blockchain.recovery import RecoveryManager
from quantum_blockchain.snapshot import sign_snapshot, verify_snapshot
from quantum_blockchain.wallet import Wallet

# ---------------------------------------------------------------------------
# Blockchain tests (15)
# ---------------------------------------------------------------------------


def test_blockchain_creates_genesis_block() -> None:
    chain = Blockchain(difficulty=1)
    assert len(chain.chain) == 1


def test_genesis_block_has_zero_index() -> None:
    chain = Blockchain(difficulty=1)
    assert chain.chain[0].index == 0


def test_genesis_block_previous_hash() -> None:
    chain = Blockchain(difficulty=1)
    assert chain.chain[0].previous_hash == "0"


def test_genesis_block_hash_not_empty() -> None:
    chain = Blockchain(difficulty=1)
    assert chain.chain[0].hash != ""


def test_blockchain_add_block_increases_length() -> None:
    chain = Blockchain(difficulty=1)
    chain.add_block("tx1")
    assert len(chain.chain) == 2


def test_blockchain_add_block_returns_block() -> None:
    chain = Blockchain(difficulty=1)
    blk = chain.add_block("tx1")
    assert isinstance(blk, Block)


def test_blockchain_last_block() -> None:
    chain = Blockchain(difficulty=1)
    blk = chain.add_block("tx1")
    assert chain.last_block is blk


def test_block_hash_matches_calculate() -> None:
    chain = Blockchain(difficulty=1)
    blk = chain.last_block
    assert blk.hash == blk.calculate_hash()


def test_blockchain_is_valid_true() -> None:
    chain = Blockchain(difficulty=1)
    chain.add_block("tx1")
    assert chain.is_valid() is True


def test_blockchain_is_valid_after_tamper() -> None:
    chain = Blockchain(difficulty=1)
    chain.add_block("tx1")
    chain.chain[1].data = "tampered"
    assert chain.is_valid() is False


def test_block_mine_satisfies_difficulty() -> None:
    chain = Blockchain(difficulty=2)
    blk = chain.last_block
    assert blk.hash.startswith("00")


def test_blockchain_to_dict_returns_list() -> None:
    chain = Blockchain(difficulty=1)
    result = chain.to_dict()
    assert isinstance(result, list)


def test_blockchain_to_dict_length() -> None:
    chain = Blockchain(difficulty=1)
    chain.add_block("tx1")
    assert len(chain.to_dict()) == 2


def test_block_index_sequential() -> None:
    chain = Blockchain(difficulty=1)
    chain.add_block("tx1")
    chain.add_block("tx2")
    for i, blk in enumerate(chain.chain):
        assert blk.index == i


def test_multiple_blocks_valid() -> None:
    chain = Blockchain(difficulty=1)
    for i in range(5):
        chain.add_block(f"tx{i}")
    assert chain.is_valid() is True


# ---------------------------------------------------------------------------
# Wallet tests (10)
# ---------------------------------------------------------------------------


def test_wallet_creates_with_address() -> None:
    w = Wallet("addr1")
    assert w.address == "addr1"


def test_wallet_creates_with_balance() -> None:
    w = Wallet("addr1", balance=42.5)
    assert w.balance == 42.5


def test_wallet_default_balance() -> None:
    w = Wallet("addr1")
    assert w.balance == 0.0


def test_wallet_backup_creates_file(tmp_path: Path) -> None:
    w = Wallet("addr1", balance=10.0)
    backup_file = str(tmp_path / "wallet.bak")
    w.backup(backup_file, "secret")
    assert os.path.exists(backup_file)


def test_wallet_restore_address(tmp_path: Path) -> None:
    w = Wallet("addr_test", balance=5.0)
    backup_file = str(tmp_path / "wallet.bak")
    w.backup(backup_file, "pass123")
    restored = Wallet.restore(backup_file, "pass123")
    assert restored.address == "addr_test"


def test_wallet_restore_balance(tmp_path: Path) -> None:
    w = Wallet("addr_test", balance=99.9)
    backup_file = str(tmp_path / "wallet.bak")
    w.backup(backup_file, "pass123")
    restored = Wallet.restore(backup_file, "pass123")
    assert restored.balance == pytest.approx(99.9)


def test_wallet_backup_not_plaintext(tmp_path: Path) -> None:
    w = Wallet("addr_secret", balance=1.0)
    backup_file = str(tmp_path / "wallet.bak")
    w.backup(backup_file, "pass")
    raw = Path(backup_file).read_bytes()
    assert b"addr_secret" not in raw


def test_wallet_wrong_password_raises(tmp_path: Path) -> None:
    w = Wallet("addr1", balance=1.0)
    backup_file = str(tmp_path / "wallet.bak")
    w.backup(backup_file, "correct")
    with pytest.raises(Exception):
        Wallet.restore(backup_file, "wrong")


def test_wallet_backup_file_has_salt(tmp_path: Path) -> None:
    w = Wallet("addr1", balance=0.0)
    backup_file = str(tmp_path / "wallet.bak")
    w.backup(backup_file, "pass")
    size = os.path.getsize(backup_file)
    assert size > 16


def test_wallet_restore_returns_wallet_instance(tmp_path: Path) -> None:
    w = Wallet("addr1", balance=1.0)
    backup_file = str(tmp_path / "wallet.bak")
    w.backup(backup_file, "pass")
    restored = Wallet.restore(backup_file, "pass")
    assert isinstance(restored, Wallet)


# ---------------------------------------------------------------------------
# Snapshot tests (6)
# ---------------------------------------------------------------------------


def test_sign_snapshot_returns_string() -> None:
    sig = sign_snapshot({"key": "value"}, "secret")
    assert isinstance(sig, str)


def test_verify_snapshot_valid() -> None:
    data: dict[str, Any] = {"block": 1}
    sig = sign_snapshot(data, "my_secret")
    assert verify_snapshot(data, "my_secret", sig) is True


def test_verify_snapshot_invalid() -> None:
    data: dict[str, Any] = {"block": 1}
    assert verify_snapshot(data, "my_secret", "bad_signature") is False


def test_sign_snapshot_deterministic() -> None:
    data = {"a": 1, "b": 2}
    sig1 = sign_snapshot(data, "key")
    sig2 = sign_snapshot(data, "key")
    assert sig1 == sig2


def test_verify_snapshot_wrong_secret() -> None:
    data: dict[str, Any] = {"block": 1}
    sig = sign_snapshot(data, "right_secret")
    assert verify_snapshot(data, "wrong_secret", sig) is False


def test_sign_snapshot_hex_length() -> None:
    sig = sign_snapshot("hello", "key")
    assert len(sig) == 64


# ---------------------------------------------------------------------------
# Recovery manager tests (5)
# ---------------------------------------------------------------------------


def test_recovery_manager_creates_dir(tmp_path: Path) -> None:
    recovery_dir = str(tmp_path / "rec")
    RecoveryManager(recovery_dir)
    assert os.path.isdir(recovery_dir)


def test_recovery_manager_save_creates_file(tmp_path: Path) -> None:
    rm = RecoveryManager(str(tmp_path / "rec"))
    rm.save("snap1", {"data": 42})
    assert (tmp_path / "rec" / "snap1.json").exists()


def test_recovery_manager_load_returns_data(tmp_path: Path) -> None:
    rm = RecoveryManager(str(tmp_path / "rec"))
    rm.save("snap1", {"key": "value"})
    loaded = rm.load("snap1")
    assert loaded == {"key": "value"}


def test_recovery_manager_list_backups(tmp_path: Path) -> None:
    rm = RecoveryManager(str(tmp_path / "rec"))
    rm.save("alpha", {})
    rm.save("beta", {})
    names = rm.list_backups()
    assert "alpha" in names and "beta" in names


def test_recovery_manager_list_empty(tmp_path: Path) -> None:
    rm = RecoveryManager(str(tmp_path / "rec"))
    assert rm.list_backups() == []


# ---------------------------------------------------------------------------
# Marketplace export tests (3)
# ---------------------------------------------------------------------------


def test_export_creates_file(tmp_path: Path) -> None:
    path = str(tmp_path / "export.json")
    export_to_json({"item": "sword"}, path)
    assert os.path.exists(path)


def test_import_returns_data(tmp_path: Path) -> None:
    path = str(tmp_path / "export.json")
    export_to_json({"item": "shield"}, path)
    data = import_from_json(path)
    assert data == {"item": "shield"}


def test_export_import_roundtrip(tmp_path: Path) -> None:
    original: list[dict[str, Any]] = [
        {"id": 1, "name": "axe"},
        {"id": 2, "name": "bow"},
    ]
    path = str(tmp_path / "items.json")
    export_to_json(original, path)
    loaded = import_from_json(path)
    assert loaded == original


# ---------------------------------------------------------------------------
# Peer sync tests (3)
# ---------------------------------------------------------------------------


def test_peer_sync_add_peer() -> None:
    ps = PeerSync()
    ps.add_peer("peer1")
    assert "peer1" in ps.peers


def test_peer_sync_remove_peer() -> None:
    ps = PeerSync()
    ps.add_peer("peer1")
    ps.remove_peer("peer1")
    assert "peer1" not in ps.peers


def test_peer_sync_broadcast() -> None:
    ps = PeerSync()
    ps.add_peer("peer1")
    ps.add_peer("peer2")
    result = ps.broadcast({"tx": "data"})
    assert result["peers"] == 2
    assert result["status"] == "broadcast"
