#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${SCRIPT_DIR}/backups"
BACKUP_FILE="${BACKUP_DIR}/jarvis_backup_${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "================================="
echo "JARVIS MEMORY VAULT BACKUP"
echo "================================="
echo "Timestamp: $TIMESTAMP"

tar --exclude=".git" \
    --exclude="backups" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude="venv" \
    --exclude="node_modules" \
    -czf "$BACKUP_FILE" -C "$SCRIPT_DIR" .

if [ $? -eq 0 ]; then
    echo "Backup saved to: $BACKUP_FILE"
else
    echo "ERROR: Backup failed." >&2
    rm -f "$BACKUP_FILE"
    exit 1
fi
echo "================================="
