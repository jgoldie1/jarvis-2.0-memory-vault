"""Tests for the Quantum Blockchain and its Flask API."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from golden_era_marketplace.quantum_blockchain.blockchain import Block, Blockchain
from golden_era_marketplace.quantum_blockchain.api import create_app


# ---------------------------------------------------------------------------
# Blockchain unit tests
# ---------------------------------------------------------------------------


def test_genesis_block_exists():
    bc = Blockchain()
    assert len(bc.chain) == 1
    assert bc.chain[0].index == 0
    assert bc.chain[0].previous_hash == "0" * 64


def test_add_transaction_returns_next_index():
    bc = Blockchain()
    idx = bc.add_transaction("alice", "bob", 5.0)
    assert idx == 1


def test_add_transaction_negative_amount_raises():
    bc = Blockchain()
    with pytest.raises(ValueError):
        bc.add_transaction("alice", "bob", -1.0)


def test_mine_creates_new_block():
    bc = Blockchain()
    bc.add_transaction("alice", "bob", 10.0)
    block = bc.mine_pending_transactions("miner1")
    assert block.index == 1
    assert len(bc.chain) == 2
    assert bc.pending_transactions == []


def test_mined_block_hash_meets_difficulty():
    bc = Blockchain()
    bc.add_transaction("alice", "bob", 1.0)
    block = bc.mine_pending_transactions("miner1")
    assert block.hash.startswith("0" * bc.DIFFICULTY)


def test_miner_receives_reward():
    bc = Blockchain()
    bc.mine_pending_transactions("miner1")
    balance = bc.get_balance("miner1")
    assert balance == bc.MINING_REWARD


def test_get_balance_after_transactions():
    bc = Blockchain()
    bc.add_transaction("miner-reward", "alice", 50.0)
    bc.mine_pending_transactions("miner1")
    assert bc.get_balance("alice") == 50.0


def test_get_balance_unknown_address_is_zero():
    bc = Blockchain()
    assert bc.get_balance("nobody") == 0.0


def test_chain_is_valid_after_mining():
    bc = Blockchain()
    bc.add_transaction("alice", "bob", 3.0)
    bc.mine_pending_transactions("miner1")
    assert bc.is_valid() is True


def test_tampered_chain_is_invalid():
    bc = Blockchain()
    bc.add_transaction("alice", "bob", 3.0)
    bc.mine_pending_transactions("miner1")
    # Tamper with a transaction in block 1
    bc.chain[1].transactions[0]["amount"] = 999.0
    assert bc.is_valid() is False


def test_block_to_dict_contains_required_keys():
    block = Block(index=0, transactions=[], previous_hash="0" * 64)
    d = block.to_dict()
    for key in ("index", "timestamp", "transactions", "previous_hash", "nonce", "hash"):
        assert key in d


# ---------------------------------------------------------------------------
# Flask API tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def client():
    bc = Blockchain()
    # Pre-mine one block so /balance has something to query
    bc.add_transaction("genesis-funder", "alice", 100.0)
    bc.mine_pending_transactions("test-miner")
    app = create_app(blockchain=bc)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c, bc


def test_status_endpoint(client):
    c, bc = client
    rv = c.get("/status")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == "running"
    assert data["chain_length"] == len(bc.chain)
    assert data["difficulty"] == bc.DIFFICULTY
    assert data["mining_reward"] == bc.MINING_REWARD
    assert isinstance(data["pending_transactions"], int)
    assert data["is_valid"] is True


def test_chain_endpoint(client):
    c, bc = client
    rv = c.get("/chain")
    assert rv.status_code == 200
    data = rv.get_json()
    assert "chain" in data
    assert "length" in data
    assert data["length"] == len(bc.chain)
    assert isinstance(data["chain"], list)
    # Each block should have the required keys
    for block in data["chain"]:
        for key in ("index", "hash", "previous_hash", "transactions", "nonce", "timestamp"):
            assert key in block


def test_balance_endpoint_known_address(client):
    c, bc = client
    rv = c.get("/balance/alice")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["address"] == "alice"
    assert data["balance"] == 100.0


def test_balance_endpoint_miner(client):
    c, bc = client
    rv = c.get("/balance/test-miner")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["address"] == "test-miner"
    assert data["balance"] == bc.MINING_REWARD


def test_balance_endpoint_unknown_address(client):
    c, bc = client
    rv = c.get("/balance/nobody")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["address"] == "nobody"
    assert data["balance"] == 0.0
