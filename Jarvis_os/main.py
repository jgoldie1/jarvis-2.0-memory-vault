"""Jarvis OS – minimal CLI for the memory-vault system.

Supported commands::

    ls backups   List files stored in the backups directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKUPS_DIR = Path(__file__).resolve().parent.parent / "golden_era_marketplace" / "backups"


def list_backups(backups_dir: Path = BACKUPS_DIR) -> list[str]:
    """Return a sorted list of filenames inside *backups_dir*.

    Returns an empty list when the directory does not exist or is empty.
    Only regular files are included; sub-directories are ignored.
    """
    if not backups_dir.exists():
        return []
    return sorted(p.name for p in backups_dir.iterdir() if p.is_file())


def main(argv: list | None = None, backups_dir: Path = BACKUPS_DIR) -> None:
    args = argv if argv is not None else sys.argv[1:]
    cmd = " ".join(args).strip()
    if cmd == "ls backups":
        files = list_backups(backups_dir)
        if files:
            for name in files:
                print(name)
        else:
            print("(no backups found)")
    else:
        print(f"Unknown command: {cmd!r}")
        print("Usage: python -m Jarvis_os.main ls backups")
        sys.exit(1)


if __name__ == "__main__":
    main()
