import importlib.util
import sys
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
