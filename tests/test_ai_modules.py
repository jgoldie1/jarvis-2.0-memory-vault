import importlib.util
import json
import sys
import tempfile
from pathlib import Path


def import_from_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_curve_update_stats():
    path = Path("golden_era_marketplace/ai/curve/curve_ai.py")
    mod = import_from_path(path, "curve_ai")
    assert hasattr(mod, "update_stats")
    assert isinstance(mod.update_stats(), dict)


def test_stubb_update_stats():
    path = Path("golden_era_marketplace/ai/stubb/stubb_ai.py")
    mod = import_from_path(path, "stubb_ai")
    assert hasattr(mod, "update_stats")
    assert isinstance(mod.update_stats(), dict)


def test_lyons_update_stats():
    path = Path("golden_era_marketplace/ai/lyons/lyons_ai.py")
    mod = import_from_path(path, "lyons_ai")
    assert hasattr(mod, "update_stats")
    assert isinstance(mod.update_stats(), dict)


def test_save_wallets_creates_backup():
    path = Path("recovery/save_wallets.py")
    mod = import_from_path(path, "save_wallets")
    assert hasattr(mod, "save_wallets")

    with tempfile.TemporaryDirectory() as tmp:
        dest = mod.save_wallets(backups_dir=Path(tmp))
        assert dest.is_dir()
        wallet_file = dest / "wallet.json"
        tx_file = dest / "transactions.json"
        assert wallet_file.exists()
        assert tx_file.exists()
        wallet = json.loads(wallet_file.read_text())
        assert "balance" in wallet
        txs = json.loads(tx_file.read_text())
        assert "transactions" in txs

        # Verify backup content matches source fintech files
        source_wallet = json.loads(Path("golden_era_marketplace/fintech/wallet.json").read_text())
        source_txs = json.loads(Path("golden_era_marketplace/fintech/transactions.json").read_text())
        assert wallet == source_wallet
        assert txs == source_txs
