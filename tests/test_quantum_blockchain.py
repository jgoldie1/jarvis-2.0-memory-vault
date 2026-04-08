from __future__ import annotations

import json
import os
import pathlib

import pytest

from quantum_blockchain import (
    Blockchain,
    EncryptedWallet,
    MarketplaceExporter,
    PeerSync,
    RecoveryManager,
    SignedSnapshot,
)
from quantum_blockchain.blockchain import Block
from quantum_blockchain.cli import create_parser
from quantum_blockchain.cli import main as cli_main

# ---------------------------------------------------------------------------
# Block tests
# ---------------------------------------------------------------------------


def test_block_creation() -> None:
    bc = Blockchain()
    b = bc.chain[0]
    assert isinstance(b, Block)


def test_block_index() -> None:
    bc = Blockchain()
    assert bc.chain[0].index == 0


def test_block_has_hash() -> None:
    bc = Blockchain()
    assert len(bc.chain[0].hash) == 64


def test_block_previous_hash_genesis() -> None:
    bc = Blockchain()
    assert bc.chain[0].previous_hash == "0"


def test_block_data_genesis() -> None:
    bc = Blockchain()
    assert bc.chain[0].data == {"genesis": True}


# ---------------------------------------------------------------------------
# Blockchain tests
# ---------------------------------------------------------------------------


def test_blockchain_init_has_genesis() -> None:
    bc = Blockchain()
    assert len(bc.chain) == 1


def test_blockchain_add_block() -> None:
    bc = Blockchain()
    block = bc.add_block({"msg": "hello"})
    assert block.index == 1
    assert len(bc.chain) == 2


def test_blockchain_add_multiple_blocks() -> None:
    bc = Blockchain()
    for i in range(3):
        bc.add_block({"i": i})
    assert len(bc.chain) == 4


def test_blockchain_is_valid() -> None:
    bc = Blockchain()
    bc.add_block({"x": 1})
    assert bc.is_valid()


def test_blockchain_invalid_after_tamper() -> None:
    bc = Blockchain()
    bc.add_block({"x": 1})
    bc.chain[1].data = {"x": 999}
    assert not bc.is_valid()


def test_blockchain_to_dict() -> None:
    bc = Blockchain()
    bc.add_block({"a": 1})
    d = bc.to_dict()
    assert isinstance(d, list)
    assert len(d) == 2


def test_blockchain_to_dict_keys() -> None:
    bc = Blockchain()
    d = bc.to_dict()
    assert "hash" in d[0]
    assert "index" in d[0]


def test_blockchain_chain_linkage() -> None:
    bc = Blockchain()
    bc.add_block({"k": "v"})
    assert bc.chain[1].previous_hash == bc.chain[0].hash


# ---------------------------------------------------------------------------
# EncryptedWallet tests
# ---------------------------------------------------------------------------


def test_wallet_encrypt_decrypt() -> None:
    w = EncryptedWallet("secret")
    data: dict[str, object] = {"key": "value"}
    token = w.encrypt(data)
    assert w.decrypt(token) == data


def test_wallet_encrypt_returns_bytes() -> None:
    w = EncryptedWallet("pass")
    token = w.encrypt({"a": 1})
    assert isinstance(token, bytes)


def test_wallet_save_load(tmp_path: pathlib.Path) -> None:
    path = str(tmp_path / "wallet.json")
    w = EncryptedWallet("demo")
    data: dict[str, object] = {"addr": "0xABC"}
    w.save(path, data)
    loaded = w.load(path)
    assert loaded["addr"] == "0xABC"


def test_wallet_save_creates_file(tmp_path: pathlib.Path) -> None:
    path = str(tmp_path / "w.json")
    w = EncryptedWallet("pw")
    w.save(path, {"x": 1})
    assert os.path.exists(path)


def test_wallet_different_passwords_same_data(tmp_path: pathlib.Path) -> None:
    path = str(tmp_path / "w.json")
    w1 = EncryptedWallet("pass1")
    data: dict[str, object] = {"secret": "value"}
    w1.save(path, data)
    loaded = w1.load(path)
    assert loaded == data


# ---------------------------------------------------------------------------
# SignedSnapshot tests
# ---------------------------------------------------------------------------


def test_snapshot_sign_contains_signature() -> None:
    snap = SignedSnapshot("key")
    signed = snap.sign({"a": 1})
    assert "__signature__" in signed


def test_snapshot_verify_valid() -> None:
    snap = SignedSnapshot("key")
    signed = snap.sign({"a": 1})
    assert snap.verify(signed)


def test_snapshot_verify_invalid() -> None:
    snap = SignedSnapshot("key")
    signed = snap.sign({"a": 1})
    signed["a"] = 999
    assert not snap.verify(signed)


def test_snapshot_verify_missing_signature() -> None:
    snap = SignedSnapshot("key")
    assert not snap.verify({"a": 1})


def test_snapshot_save_load(tmp_path: pathlib.Path) -> None:
    path = str(tmp_path / "snap.json")
    snap = SignedSnapshot("mykey")
    data: dict[str, object] = {"blocks": 5}
    snap.save(path, data)
    loaded = snap.load(path)
    assert snap.verify(loaded)


# ---------------------------------------------------------------------------
# RecoveryManager tests
# ---------------------------------------------------------------------------


def test_recovery_backup_creates_file(tmp_path: pathlib.Path) -> None:
    rm = RecoveryManager(str(tmp_path / "backups"))
    bc = Blockchain()
    path = rm.backup(bc)
    assert os.path.exists(path)


def test_recovery_restore(tmp_path: pathlib.Path) -> None:
    rm = RecoveryManager(str(tmp_path / "backups"))
    bc = Blockchain()
    bc.add_block({"x": 1})
    path = rm.backup(bc)
    restored = rm.restore(path)
    assert len(restored.chain) == len(bc.chain)


def test_recovery_restore_valid_chain(tmp_path: pathlib.Path) -> None:
    rm = RecoveryManager(str(tmp_path / "backups"))
    bc = Blockchain()
    bc.add_block({"y": 2})
    path = rm.backup(bc)
    restored = rm.restore(path)
    assert restored.is_valid()


def test_recovery_list_backups(tmp_path: pathlib.Path) -> None:
    rm = RecoveryManager(str(tmp_path / "backups"))
    bc = Blockchain()
    rm.backup(bc)
    rm.backup(bc)
    backups = rm.list_backups()
    assert len(backups) == 2


def test_recovery_list_backups_empty(tmp_path: pathlib.Path) -> None:
    rm = RecoveryManager(str(tmp_path / "backups2"))
    assert rm.list_backups() == []


# ---------------------------------------------------------------------------
# MarketplaceExporter tests
# ---------------------------------------------------------------------------


def test_exporter_export_json(tmp_path: pathlib.Path) -> None:
    bc = Blockchain()
    bc.add_block({"item": "sword"})
    exp = MarketplaceExporter(bc)
    path = str(tmp_path / "chain.json")
    exp.export_json(path)
    with open(path) as f:
        data = json.load(f)
    assert len(data) == 2


def test_exporter_export_csv(tmp_path: pathlib.Path) -> None:
    bc = Blockchain()
    bc.add_block({"item": "shield"})
    exp = MarketplaceExporter(bc)
    path = str(tmp_path / "chain.csv")
    exp.export_csv(path)
    assert os.path.exists(path)


def test_exporter_summary_block_count() -> None:
    bc = Blockchain()
    bc.add_block({"a": 1})
    exp = MarketplaceExporter(bc)
    summary = exp.summary()
    assert summary["total_blocks"] == 2


def test_exporter_summary_valid() -> None:
    bc = Blockchain()
    exp = MarketplaceExporter(bc)
    assert exp.summary()["is_valid"] is True


def test_exporter_summary_latest_hash() -> None:
    bc = Blockchain()
    exp = MarketplaceExporter(bc)
    summary = exp.summary()
    assert summary["latest_hash"] == bc.chain[-1].hash


# ---------------------------------------------------------------------------
# PeerSync tests
# ---------------------------------------------------------------------------


def test_peersync_add_peer() -> None:
    bc = Blockchain()
    ps = PeerSync(bc)
    ps.add_peer("peer-1", bc.to_dict())
    assert "peer-1" in ps.get_peers()


def test_peersync_get_peers_empty() -> None:
    bc = Blockchain()
    ps = PeerSync(bc)
    assert ps.get_peers() == []


def test_peersync_sync_adopts_longer_chain() -> None:
    bc = Blockchain()
    longer = Blockchain()
    for i in range(3):
        longer.add_block({"i": i})
    ps = PeerSync(bc)
    ps.add_peer("peer-1", longer.to_dict())
    updated = ps.sync()
    assert updated is True
    assert len(bc.chain) == len(longer.chain)


def test_peersync_sync_no_update_shorter() -> None:
    bc = Blockchain()
    bc.add_block({"x": 1})
    shorter = Blockchain()
    ps = PeerSync(bc)
    ps.add_peer("peer-1", shorter.to_dict())
    updated = ps.sync()
    assert updated is False


def test_peersync_get_peers_after_multiple_adds() -> None:
    bc = Blockchain()
    ps = PeerSync(bc)
    ps.add_peer("a", bc.to_dict())
    ps.add_peer("b", bc.to_dict())
    assert sorted(ps.get_peers()) == ["a", "b"]


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_cli_parser_creates() -> None:
    parser = create_parser()
    assert parser is not None


def test_cli_status(capsys: pytest.CaptureFixture[str]) -> None:
    cli_main(["status"])
    captured = capsys.readouterr()
    assert "Chain length" in captured.out


def test_cli_validate(capsys: pytest.CaptureFixture[str]) -> None:
    cli_main(["validate"])
    captured = capsys.readouterr()
    assert "Chain valid" in captured.out


def test_cli_add(capsys: pytest.CaptureFixture[str]) -> None:
    cli_main(["add", "--data", "key=value"])
    captured = capsys.readouterr()
    assert "Added block" in captured.out


def test_cli_no_command(capsys: pytest.CaptureFixture[str]) -> None:
    cli_main([])
    captured = capsys.readouterr()
    assert len(captured.out) > 0 or len(captured.err) > 0
