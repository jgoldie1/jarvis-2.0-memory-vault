#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ $# -lt 2 ]; then
  echo "Usage: ./verify_backup.sh <archive.tar.gz> <archive.sha256>"
  exit 1
fi

ARCHIVE="$1"
HASH_FILE="$2"

if [ ! -f "$ARCHIVE" ]; then
  echo "Archive not found: $ARCHIVE"
  exit 1
fi

if [ ! -f "$HASH_FILE" ]; then
  echo "Hash file not found: $HASH_FILE"
  exit 1
fi

echo "Verifying backup integrity..."
sha256sum -c "$HASH_FILE"

echo "Backup verified successfully."
