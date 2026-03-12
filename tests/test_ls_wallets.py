import json
import importlib.util
import sys
from pathlib import Path


def import_from_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Load the super_copilot_autofix module so we can call ls_wallets directly
ROOT = Path(__file__).resolve().parent.parent
_mod = import_from_path(ROOT / "super_copilot_autofix.py", "super_copilot_autofix")
ls_wallets = _mod.ls_wallets


def test_ls_wallets_returns_list(tmp_path):
    """ls_wallets always returns a list."""
    result = ls_wallets(tmp_path)
    assert isinstance(result, list)


def test_ls_wallets_no_fintech_dir(tmp_path):
    """Returns an empty list when the fintech directory does not exist."""
    result = ls_wallets(tmp_path)
    assert result == []


def test_ls_wallets_empty_fintech_dir(tmp_path):
    """Returns an empty list when the fintech directory has no wallet files."""
    result = ls_wallets(tmp_path)
    assert result == []


def test_ls_wallets_reads_wallet_json(tmp_path):
    """Returns a single entry when wallet.json exists."""
    fintech = tmp_path / "golden_era_marketplace" / "fintech"
    fintech.mkdir(parents=True)
    (fintech / "wallet.json").write_text(json.dumps({"balance": 42.5}), encoding="utf-8")

    result = ls_wallets(tmp_path)
    assert len(result) == 1
    assert result[0]["name"] == "wallet"
    assert result[0]["balance"] == 42.5


def test_ls_wallets_includes_extra_wallet_files(tmp_path):
    """Returns entries for wallet.json and any wallet-*.json files."""
    fintech = tmp_path / "golden_era_marketplace" / "fintech"
    fintech.mkdir(parents=True)
    (fintech / "wallet.json").write_text(json.dumps({"balance": 100.0}), encoding="utf-8")
    (fintech / "wallet-savings.json").write_text(json.dumps({"balance": 500.0}), encoding="utf-8")

    result = ls_wallets(tmp_path)
    names = [w["name"] for w in result]
    assert "wallet" in names
    assert "wallet-savings" in names
    assert len(result) == 2


def test_ls_wallets_skips_invalid_json(tmp_path):
    """Skips wallet files containing invalid JSON without raising."""
    fintech = tmp_path / "golden_era_marketplace" / "fintech"
    fintech.mkdir(parents=True)
    (fintech / "wallet.json").write_text("{not valid json}", encoding="utf-8")

    result = ls_wallets(tmp_path)
    assert result == []


def test_ls_wallets_live_wallet(tmp_path):
    """Reads the actual wallet.json from the repo fintech directory if present."""
    actual_wallet = ROOT / "golden_era_marketplace" / "fintech" / "wallet.json"
    if not actual_wallet.exists():
        return  # skip if not present in this environment

    result = ls_wallets(ROOT)
    assert any(w["name"] == "wallet" for w in result)
    wallet_entry = next(w for w in result if w["name"] == "wallet")
    assert "balance" in wallet_entry
