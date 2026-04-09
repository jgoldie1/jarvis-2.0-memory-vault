#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: ./restore.sh <archive.tar.gz> <target_directory>"
  exit 1
fi

ARCHIVE="$1"
TARGET_DIR="$2"

if [ ! -f "$ARCHIVE" ]; then
  echo "Archive not found: $ARCHIVE"
  exit 1
fi

mkdir -p "$TARGET_DIR"

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

echo "Extracting archive..."
tar -xzf "$ARCHIVE" -C "$TEMP_DIR"

mapfile -t EXTRACTED_DIRS < <(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d)

if [ "${#EXTRACTED_DIRS[@]}" -eq 0 ]; then
  echo "Could not locate extracted backup directory."
  exit 1
fi

if [ "${#EXTRACTED_DIRS[@]}" -gt 1 ]; then
  echo "Warning: multiple top-level directories found in archive; using the first one."
fi

EXTRACTED_DIR="${EXTRACTED_DIRS[0]}"

echo "Restoring files to $TARGET_DIR ..."
cp -r "$EXTRACTED_DIR"/. "$TARGET_DIR"/

echo "Restore complete."
echo "Next steps:"
echo "1. cd $TARGET_DIR"
echo "2. python3 -m pip install -r requirements.txt"
echo "3. python3 run_node.py"
