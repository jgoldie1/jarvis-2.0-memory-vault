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

LATEST_BACKUP=$(ls -t "$BACKUP_DIR" | head -n 1)

if [ -z "$LATEST_BACKUP" ]; then
  echo "No backup files found in $BACKUP_DIR"
  exit 1
fi

echo "Restoring from backup: $LATEST_BACKUP"
tar -xzf "$BACKUP_DIR/$LATEST_BACKUP" -C "$BASE"

echo "Restore complete from $LATEST_BACKUP"
