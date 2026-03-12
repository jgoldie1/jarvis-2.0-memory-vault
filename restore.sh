#!/bin/bash

echo "==================================="
echo " GOLDEN ERA MARKETPLACE RESTORE"
echo " RESTORING FROM BACKUP"
echo "==================================="

BASE=~/golden_era_marketplace
BACKUP_DIR="$BASE/backups"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "No backups directory found at $BACKUP_DIR"
  exit 1
fi

LATEST_BACKUP=""
LATEST_MTIME=0
for f in "$BACKUP_DIR"/*.tar.gz; do
  [ -f "$f" ] || continue
  mtime=$(stat -c '%Y' "$f" 2>/dev/null || stat -f '%m' "$f" 2>/dev/null)
  if [ "$mtime" -gt "$LATEST_MTIME" ]; then
    LATEST_MTIME="$mtime"
    LATEST_BACKUP="$f"
  fi
done

if [ -z "$LATEST_BACKUP" ]; then
  echo "No backup files found in $BACKUP_DIR"
  exit 1
fi

echo "Verifying backup archive: $LATEST_BACKUP"
if ! tar -tzf "$LATEST_BACKUP" > /dev/null 2>&1; then
  echo "Backup archive is corrupt or invalid: $LATEST_BACKUP"
  exit 1
fi

echo "Restoring from backup: $LATEST_BACKUP"
if ! tar -xzf "$LATEST_BACKUP" -C "$BASE"; then
  echo "Restore failed from $LATEST_BACKUP"
  exit 1
fi

echo "Restore complete from $LATEST_BACKUP"
