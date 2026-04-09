import hashlib
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path


VERIFY_SCRIPT = Path(__file__).parent.parent / "verify_backup.sh"


def _make_archive_and_hash(tmp_dir: str) -> tuple[str, str]:
    """Create a tar.gz archive and matching sha256 hash file, return their paths."""
    content_file = os.path.join(tmp_dir, "data.txt")
    with open(content_file, "w") as f:
        f.write("jarvis backup test content")

    archive_path = os.path.join(tmp_dir, "backup.tar.gz")
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(content_file, arcname="data.txt")

    digest = hashlib.sha256(Path(archive_path).read_bytes()).hexdigest()
    hash_path = os.path.join(tmp_dir, "backup.sha256")
    with open(hash_path, "w") as f:
        f.write(digest + "\n")

    return archive_path, hash_path


def test_verify_backup_valid():
    with tempfile.TemporaryDirectory() as tmp:
        archive, hashfile = _make_archive_and_hash(tmp)
        result = subprocess.run(
            ["bash", str(VERIFY_SCRIPT), archive, hashfile],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout


def test_verify_backup_wrong_hash():
    with tempfile.TemporaryDirectory() as tmp:
        archive, _ = _make_archive_and_hash(tmp)
        bad_hash = os.path.join(tmp, "bad.sha256")
        with open(bad_hash, "w") as f:
            f.write("0" * 64 + "\n")
        result = subprocess.run(
            ["bash", str(VERIFY_SCRIPT), archive, bad_hash],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "FAIL" in result.stderr


def test_verify_backup_missing_archive():
    with tempfile.TemporaryDirectory() as tmp:
        _, hashfile = _make_archive_and_hash(tmp)
        result = subprocess.run(
            ["bash", str(VERIFY_SCRIPT), os.path.join(tmp, "missing.tar.gz"), hashfile],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "ERROR" in result.stderr


def test_verify_backup_no_args():
    result = subprocess.run(
        ["bash", str(VERIFY_SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Usage" in result.stderr


def test_verify_backup_sha256sum_format():
    """Hash file in 'hash  filename' format (output of sha256sum) should also work."""
    with tempfile.TemporaryDirectory() as tmp:
        archive, _ = _make_archive_and_hash(tmp)
        digest = hashlib.sha256(Path(archive).read_bytes()).hexdigest()
        hash_path = os.path.join(tmp, "backup_full.sha256")
        with open(hash_path, "w") as f:
            f.write(f"{digest}  {archive}\n")
        result = subprocess.run(
            ["bash", str(VERIFY_SCRIPT), archive, hash_path],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout
