import importlib.util
import sys
from pathlib import Path


def import_jarvis_main():
    path = Path("Jarvis_os/main.py")
    spec = importlib.util.spec_from_file_location("jarvis_main", str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules["jarvis_main"] = module
    spec.loader.exec_module(module)
    return module


def test_list_backups_missing_dir():
    mod = import_jarvis_main()
    result = mod.list_backups(Path("/tmp/does_not_exist_jarvis_abc"))
    assert result == []


def test_list_backups_empty_dir(tmp_path):
    mod = import_jarvis_main()
    result = mod.list_backups(tmp_path)
    assert result == []


def test_list_backups_with_files(tmp_path):
    (tmp_path / "backup_20260312.json").write_text("{}")
    (tmp_path / "backup_20260311.json").write_text("{}")
    # sub-directories should not be listed
    (tmp_path / "subdir").mkdir()
    mod = import_jarvis_main()
    result = mod.list_backups(tmp_path)
    assert result == ["backup_20260311.json", "backup_20260312.json"]


def test_list_backups_returns_sorted(tmp_path):
    for name in ["c.json", "a.json", "b.json"]:
        (tmp_path / name).write_text("{}")
    mod = import_jarvis_main()
    result = mod.list_backups(tmp_path)
    assert result == sorted(result)


def test_list_backups_default_dir_exists():
    """The tracked backups directory must exist in the repository."""
    mod = import_jarvis_main()
    assert mod.BACKUPS_DIR.is_dir(), f"Expected backups dir at {mod.BACKUPS_DIR}"


def test_main_ls_backups(tmp_path, capsys):
    (tmp_path / "snap.json").write_text("{}")
    mod = import_jarvis_main()
    mod.main(["ls", "backups"], backups_dir=tmp_path)
    captured = capsys.readouterr()
    assert "snap.json" in captured.out


def test_main_ls_backups_empty(tmp_path, capsys):
    mod = import_jarvis_main()
    mod.main(["ls", "backups"], backups_dir=tmp_path)
    captured = capsys.readouterr()
    assert "(no backups found)" in captured.out


def test_main_unknown_command_exits(capsys):
    import pytest

    mod = import_jarvis_main()
    with pytest.raises(SystemExit) as exc_info:
        mod.main(["unknown"])
    assert exc_info.value.code == 1
