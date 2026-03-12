#!/bin/bash

echo "==================================="
echo " GOLDEN ERA MARKETPLACE"
echo " BACKUP VERIFICATION SYSTEM"
echo "==================================="

BASE=~/golden_era_marketplace
BACKUP_DIR=$BASE/backups

echo "Checking backup directory..."
if [ ! -d "$BACKUP_DIR" ]; then
  echo "WARNING: Backup directory not found at $BACKUP_DIR"
  echo "Run superbash.sh to initialize the system."
  exit 1
fi

echo "Scanning backups..."
BACKUP_COUNT=$(find "$BACKUP_DIR" -maxdepth 1 -type f -print0 | xargs -0 -n1 echo 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT" -eq 0 ]; then
  echo "WARNING: No backup files found in $BACKUP_DIR"
  exit 1
fi

if [ "$BACKUP_COUNT" -eq 1 ]; then
  echo "Found 1 backup file."
else
  echo "Found $BACKUP_COUNT backup files."
fi

echo ""
echo "Backup details:"
ls -lh "$BACKUP_DIR"

echo ""
echo "==================================="
echo " BACKUP VERIFICATION COMPLETE"
echo "==================================="
