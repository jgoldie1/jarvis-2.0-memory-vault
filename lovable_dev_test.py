"""Tests for the Golden Era Marketplace Flask backend (dashboard_backend.py)."""

import json
import sys
from pathlib import Path

import pytest

# Ensure repository root is importable
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import golden_era_marketplace.dashboard_backend as backend


@pytest.fixture()
def client(tmp_path):
    """Return a Flask test client with isolated fintech data."""
    fintech_dir = tmp_path / "fintech"
    fintech_dir.mkdir()

    # Write minimal JSON fixtures
    (fintech_dir / "wallet.json").write_text(json.dumps({"balance": 100.0}))
    (fintech_dir / "nfts.json").write_text(json.dumps({"nfts": []}))
    (fintech_dir / "passport.json").write_text(
        json.dumps({"id": "p1", "name": "Test User", "country": "US"})
    )
    (fintech_dir / "ai_stats.json").write_text(
        json.dumps({"curve": 0, "stubb": 0, "lyons": 0, "ai_tutor": 0})
    )

    # Patch module-level path variables to use tmp_path
    original_wallet = backend.wallet_file
    original_nfts = backend.nfts_file
    original_passport = backend.passport_file
    original_ai_stats = backend.ai_stats_file

    backend.wallet_file = fintech_dir / "wallet.json"
    backend.nfts_file = fintech_dir / "nfts.json"
    backend.passport_file = fintech_dir / "passport.json"
    backend.ai_stats_file = fintech_dir / "ai_stats.json"

    backend.app.config["TESTING"] = True
    with backend.app.test_client() as c:
        yield c

    # Restore original paths
    backend.wallet_file = original_wallet
    backend.nfts_file = original_nfts
    backend.passport_file = original_passport
    backend.ai_stats_file = original_ai_stats


def test_wallet_endpoint(client):
    rv = client.get("/api/wallet")
    assert rv.status_code == 200
    data = rv.get_json()
    assert "balance" in data
    assert data["balance"] == 100.0


def test_nfts_endpoint(client):
    rv = client.get("/api/nfts")
    assert rv.status_code == 200
    data = rv.get_json()
    assert "nfts" in data
    assert isinstance(data["nfts"], list)


def test_passport_endpoint(client):
    rv = client.get("/api/passport")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get("name") == "Test User"


def test_ai_stats_endpoint(client):
    rv = client.get("/api/ai_stats")
    assert rv.status_code == 200
    data = rv.get_json()
    # Each known module should be present and numeric
    for module in ("curve", "stubb", "lyons", "ai_tutor"):
        assert module in data
        assert isinstance(data[module], (int, float))


def test_index_redirect(client):
    """/  returns index.html if present, else redirects to static host."""
    rv = client.get("/")
    assert rv.status_code in (200, 302)
