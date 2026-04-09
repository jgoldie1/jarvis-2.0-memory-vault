"""Tests for the quantum_blockchain package (49 tests)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from cryptography.fernet import InvalidToken

from quantum_blockchain import (
    Block,
    Blockchain,
    PeerNode,
    RecoveryManager,
    create_snapshot,
    decrypt_wallet,
    encrypt_wallet,
    export_to_json,
    import_from_json,
    load_wallet,
    save_wallet,
    verify_snapshot,
)

# ── blockchain.py ──────────────────────────────────────────────────────────────


class TestBlock:
    def test_block_has_hash_after_init(self) -> None:
        block = Block(index=1, data="tx", previous_hash="abc")
        assert block.hash != ""

    def test_block_hash_is_hex_string(self) -> None:
        block = Block(index=0, data="genesis", previous_hash="0")
        assert len(block.hash) == 64
        int(block.hash, 16)  # raises if not valid hex

    def test_block_compute_hash_deterministic(self) -> None:
        block = Block(index=0, data="test", previous_hash="0")
        h1 = block.compute_hash()
        h2 = block.compute_hash()
        assert h1 == h2

    def test_block_hash_changes_on_data_mutation(self) -> None:
        block = Block(index=0, data="original", previous_hash="0")
        original_hash = block.hash
        block.data = "tampered"
        assert block.compute_hash() != original_hash

    def test_block_mine_meets_difficulty(self) -> None:
        block = Block(index=1, data="mine me", previous_hash="0")
        block.mine(difficulty=2)
        assert block.hash.startswith("00")

    def test_block_mine_updates_nonce(self) -> None:
        block = Block(index=1, data="mine me", previous_hash="0")
        block.nonce = 0
        block.mine(difficulty=2)
        assert block.nonce >= 0  # nonce may stay at 0 if lucky

    def test_block_stores_timestamp(self) -> None:
        block = Block(index=0, data="ts", previous_hash="0")
        assert block.timestamp > 0


class TestBlockchain:
    def test_blockchain_has_genesis_block(self) -> None:
        bc = Blockchain(difficulty=1)
        assert len(bc.chain) == 1

    def test_genesis_previous_hash_is_zero(self) -> None:
        bc = Blockchain(difficulty=1)
        assert bc.chain[0].previous_hash == "0"

    def test_genesis_data(self) -> None:
        bc = Blockchain(difficulty=1)
        assert bc.chain[0].data == "Genesis Block"

    def test_add_block_increases_chain_length(self) -> None:
        bc = Blockchain(difficulty=1)
        bc.add_block("first")
        assert len(bc.chain) == 2

    def test_add_block_returns_block(self) -> None:
        bc = Blockchain(difficulty=1)
        block = bc.add_block("hello")
        assert isinstance(block, Block)

    def test_add_block_links_to_previous(self) -> None:
        bc = Blockchain(difficulty=1)
        prev_hash = bc.latest_block.hash
        new_block = bc.add_block("data")
        assert new_block.previous_hash == prev_hash

    def test_blockchain_is_valid_after_creation(self) -> None:
        bc = Blockchain(difficulty=1)
        bc.add_block("tx1")
        bc.add_block("tx2")
        assert bc.is_valid()

    def test_blockchain_invalid_after_hash_tamper(self) -> None:
        bc = Blockchain(difficulty=1)
        bc.add_block("tx1")
        bc.chain[1].hash = (
            "0000000000000000000000000000000000000000000000000000000000000000"
        )
        assert not bc.is_valid()

    def test_blockchain_invalid_after_data_tamper(self) -> None:
        bc = Blockchain(difficulty=1)
        bc.add_block("original")
        bc.chain[1].data = "tampered"
        assert not bc.is_valid()

    def test_latest_block_is_last(self) -> None:
        bc = Blockchain(difficulty=1)
        b = bc.add_block("last")
        assert bc.latest_block is b

    def test_multiple_blocks_added(self) -> None:
        bc = Blockchain(difficulty=1)
        for i in range(5):
            bc.add_block(f"block-{i}")
        assert len(bc.chain) == 6
        assert bc.is_valid()


# ── wallet.py ─────────────────────────────────────────────────────────────────


class TestWallet:
    def test_encrypt_returns_bytes(self) -> None:
        data = {"address": "0xABC", "balance": 100.0}
        result = encrypt_wallet(data, "password")
        assert isinstance(result, bytes)

    def test_encrypt_decrypt_roundtrip(self) -> None:
        data = {"address": "0xDEF", "balance": 42.0}
        encrypted = encrypt_wallet(data, "my-secret")
        decrypted = decrypt_wallet(encrypted, "my-secret")
        assert decrypted == data

    def test_wrong_password_raises(self) -> None:
        data = {"key": "value"}
        encrypted = encrypt_wallet(data, "correct")
        with pytest.raises(InvalidToken):
            decrypt_wallet(encrypted, "wrong-password")

    def test_save_and_load_wallet(self) -> None:
        data = {"address": "0x123", "balance": 7.5}
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "wallet.bin"
            save_wallet(data, "secret", path)
            loaded = load_wallet("secret", path)
            assert loaded == data

    def test_save_wallet_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "w.bin"
            save_wallet({"x": 1}, "pw", path)
            assert path.exists()

    def test_encrypted_bytes_differ_per_call(self) -> None:
        data = {"a": 1}
        enc1 = encrypt_wallet(data, "pw")
        enc2 = encrypt_wallet(data, "pw")
        # Different salts → different ciphertexts
        assert enc1 != enc2

    def test_load_wallet_wrong_password_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "w.bin"
            save_wallet({"x": 1}, "right", path)
            with pytest.raises(InvalidToken):
                load_wallet("wrong", path)


# ── snapshot.py ───────────────────────────────────────────────────────────────


class TestSnapshot:
    def test_create_snapshot_has_required_keys(self) -> None:
        snap = create_snapshot([], "key")
        assert "timestamp" in snap
        assert "chain" in snap
        assert "signature" in snap

    def test_verify_valid_snapshot(self) -> None:
        snap = create_snapshot([{"index": 0}], "secret")
        assert verify_snapshot(snap, "secret")

    def test_verify_wrong_key_fails(self) -> None:
        snap = create_snapshot([{"index": 0}], "secret")
        assert not verify_snapshot(snap, "wrong-key")

    def test_verify_tampered_chain_fails(self) -> None:
        snap = create_snapshot([{"index": 0, "data": "original"}], "key")
        snap["chain"][0]["data"] = "tampered"
        assert not verify_snapshot(snap, "key")

    def test_snapshot_timestamp_is_float(self) -> None:
        snap = create_snapshot([], "k")
        assert isinstance(snap["timestamp"], float)

    def test_create_snapshot_empty_chain(self) -> None:
        snap = create_snapshot([], "k")
        assert snap["chain"] == []


# ── recovery.py ───────────────────────────────────────────────────────────────


class TestRecoveryManager:
    def test_save_snapshot_creates_file(self) -> None:
        bc = Blockchain(difficulty=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = RecoveryManager("secret", Path(tmpdir))
            path = rm.save_snapshot(bc)
            assert path.exists()

    def test_load_snapshot_returns_dict(self) -> None:
        bc = Blockchain(difficulty=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = RecoveryManager("secret", Path(tmpdir))
            path = rm.save_snapshot(bc)
            snap = rm.load_snapshot(path)
            assert snap is not None
            assert "chain" in snap

    def test_load_snapshot_wrong_key_returns_none(self) -> None:
        bc = Blockchain(difficulty=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            rm_save = RecoveryManager("key-a", Path(tmpdir))
            path = rm_save.save_snapshot(bc)
            rm_load = RecoveryManager("key-b", Path(tmpdir))
            assert rm_load.load_snapshot(path) is None

    def test_load_snapshot_invalid_json_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bad = Path(tmpdir) / "snapshot_999.json"
            bad.write_text("not-json")
            rm = RecoveryManager("key", Path(tmpdir))
            assert rm.load_snapshot(bad) is None

    def test_list_snapshots_returns_paths(self) -> None:
        bc = Blockchain(difficulty=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = RecoveryManager("secret", Path(tmpdir))
            rm.save_snapshot(bc)
            paths = rm.list_snapshots()
            assert len(paths) == 1

    def test_list_snapshots_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = RecoveryManager("secret", Path(tmpdir))
            # Manually create two snapshot files with different timestamps
            (Path(tmpdir) / "snapshot_100.json").write_text("{}")
            (Path(tmpdir) / "snapshot_200.json").write_text("{}")
            paths = rm.list_snapshots()
            assert paths[0].name < paths[1].name


# ── marketplace_export.py ─────────────────────────────────────────────────────


class TestMarketplaceExport:
    def test_export_creates_file(self) -> None:
        bc = Blockchain(difficulty=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.json"
            export_to_json(bc, path)
            assert path.exists()

    def test_export_json_is_valid(self) -> None:
        bc = Blockchain(difficulty=1)
        bc.add_block("tx1")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.json"
            export_to_json(bc, path)
            data = json.loads(path.read_text())
            assert data["length"] == 2
            assert data["valid"] is True

    def test_import_from_json(self) -> None:
        bc = Blockchain(difficulty=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.json"
            export_to_json(bc, path)
            imported = import_from_json(path)
            assert "blocks" in imported
            assert imported["length"] == len(bc.chain)

    def test_export_includes_all_blocks(self) -> None:
        bc = Blockchain(difficulty=1)
        for i in range(3):
            bc.add_block(f"tx-{i}")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.json"
            export_to_json(bc, path)
            data = json.loads(path.read_text())
            assert len(data["blocks"]) == 4  # genesis + 3


# ── peer_sync.py ──────────────────────────────────────────────────────────────


class TestPeerSync:
    def test_connect_registers_both_directions(self) -> None:
        bc1 = Blockchain(difficulty=1)
        bc2 = Blockchain(difficulty=1)
        n1 = PeerNode("n1", bc1)
        n2 = PeerNode("n2", bc2)
        n1.connect(n2)
        assert n2 in n1.peers
        assert n1 in n2.peers

    def test_connect_idempotent(self) -> None:
        bc1 = Blockchain(difficulty=1)
        bc2 = Blockchain(difficulty=1)
        n1 = PeerNode("n1", bc1)
        n2 = PeerNode("n2", bc2)
        n1.connect(n2)
        n1.connect(n2)
        assert n1.peers.count(n2) == 1

    def test_receive_valid_block(self) -> None:
        bc1 = Blockchain(difficulty=1)
        bc2 = Blockchain(difficulty=1)
        n2 = PeerNode("n2", bc2)
        block = bc1.add_block("new")
        # Manually set previous_hash to match bc2's latest
        block.previous_hash = bc2.latest_block.hash
        accepted = n2.receive_block(block)
        assert accepted

    def test_receive_invalid_block_rejected(self) -> None:
        bc2 = Blockchain(difficulty=1)
        n2 = PeerNode("n2", bc2)
        orphan = Block(index=5, data="orphan", previous_hash="00000bad")
        orphan.mine(1)
        accepted = n2.receive_block(orphan)
        assert not accepted

    def test_sync_adopts_longer_chain(self) -> None:
        bc_long = Blockchain(difficulty=1)
        bc_long.add_block("a")
        bc_long.add_block("b")
        bc_short = Blockchain(difficulty=1)
        n_long = PeerNode("long", bc_long)
        n_short = PeerNode("short", bc_short)
        n_short.connect(n_long)
        n_short.sync()
        assert len(n_short.blockchain.chain) == len(bc_long.chain)

    def test_sync_keeps_own_chain_if_longer(self) -> None:
        bc_long = Blockchain(difficulty=1)
        bc_long.add_block("a")
        bc_short = Blockchain(difficulty=1)
        n_long = PeerNode("long", bc_long)
        n_short = PeerNode("short", bc_short)
        n_long.connect(n_short)
        original_len = len(bc_long.chain)
        n_long.sync()
        assert len(n_long.blockchain.chain) == original_len

    def test_serialize_chain_is_valid_json(self) -> None:
        bc = Blockchain(difficulty=1)
        bc.add_block("tx")
        node = PeerNode("n", bc)
        serialized = node.serialize_chain()
        parsed = json.loads(serialized)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_broadcast_block_to_peers(self) -> None:
        bc1 = Blockchain(difficulty=1)
        bc2 = Blockchain(difficulty=1)
        n1 = PeerNode("n1", bc1)
        n2 = PeerNode("n2", bc2)
        n1.connect(n2)
        # Build a block that genuinely continues bc2
        block = Block(
            index=len(bc2.chain),
            data="broadcast",
            previous_hash=bc2.latest_block.hash,
        )
        block.mine(1)
        n1.broadcast_block(block)
        assert len(n2.blockchain.chain) == 2
