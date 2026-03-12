#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$PROJECT_DIR/backups/$STAMP"
ARCHIVE="$PROJECT_DIR/backups/quantum_blockchain_$STAMP.tar.gz"
HASH_FILE="$PROJECT_DIR/backups/quantum_blockchain_$STAMP.sha256"

mkdir -p "$BACKUP_DIR"

echo "Creating manifest..."
cat > "$BACKUP_DIR/MANIFEST.txt" << MANIFEST
Backup Timestamp: $STAMP
Project Path: $PROJECT_DIR
Includes:
- core/
- contracts/
- data/
- wallets/
- api.py
- run_node.py
- requirements.txt
- backup.sh
- restore.sh
- verify_backup.sh
- docs/
- recovery/
MANIFEST

echo "Copying project files..."
[ -d core ] && cp -r core "$BACKUP_DIR/"
[ -d contracts ] && cp -r contracts "$BACKUP_DIR/"
[ -d data ] && cp -r data "$BACKUP_DIR/"
[ -d wallets ] && cp -r wallets "$BACKUP_DIR/"
[ -d docs ] && cp -r docs "$BACKUP_DIR/"
[ -d recovery ] && cp -r recovery "$BACKUP_DIR/"

[ -f api.py ] && cp api.py "$BACKUP_DIR/"
[ -f run_node.py ] && cp run_node.py "$BACKUP_DIR/"
[ -f requirements.txt ] && cp requirements.txt "$BACKUP_DIR/"
[ -f README_RECOVERY.md ] && cp README_RECOVERY.md "$BACKUP_DIR/"
[ -f backup.sh ] && cp backup.sh "$BACKUP_DIR/"
[ -f restore.sh ] && cp restore.sh "$BACKUP_DIR/"
[ -f verify_backup.sh ] && cp verify_backup.sh "$BACKUP_DIR/"

echo "Creating archive..."
tar -czf "$ARCHIVE" -C "$PROJECT_DIR/backups" "$STAMP"

echo "Cleaning up staging directory..."
rm -rf "$BACKUP_DIR"

echo "Generating checksum..."
if command -v sha256sum &>/dev/null; then
    sha256sum "$ARCHIVE" > "$HASH_FILE"
elif command -v shasum &>/dev/null; then
    shasum -a 256 "$ARCHIVE" > "$HASH_FILE"
else
    echo "Warning: no sha256 utility found; skipping checksum." >&2
fi

echo "Backup complete:"
echo "$ARCHIVE"
echo "$HASH_FILE"
