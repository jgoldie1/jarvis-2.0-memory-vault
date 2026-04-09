#!/bin/bash
# verify_backup.sh - Verify a backup archive against its SHA256 hash file
# Usage: ./verify_backup.sh <archive.tar.gz> <archive.sha256>

set -euo pipefail

ARCHIVE="${1:-}"
HASHFILE="${2:-}"

if [[ -z "$ARCHIVE" || -z "$HASHFILE" ]]; then
    echo "Usage: $0 <archive.tar.gz> <archive.sha256>" >&2
    exit 1
fi

if [[ ! -f "$ARCHIVE" ]]; then
    echo "ERROR: Archive not found: $ARCHIVE" >&2
    exit 1
fi

if [[ ! -f "$HASHFILE" ]]; then
    echo "ERROR: Hash file not found: $HASHFILE" >&2
    exit 1
fi

# Read expected hash (supports plain hash or 'hash  filename' format from sha256sum)
EXPECTED_HASH="$(awk '{print $1}' "$HASHFILE")"

if [[ -z "$EXPECTED_HASH" ]]; then
    echo "ERROR: Hash file is empty or malformed: $HASHFILE" >&2
    exit 1
fi

# Compute actual hash of the archive
ACTUAL_HASH="$(sha256sum "$ARCHIVE" | awk '{print $1}')"

if [[ "$ACTUAL_HASH" == "$EXPECTED_HASH" ]]; then
    echo "OK: $ARCHIVE verified successfully."
    exit 0
else
    echo "FAIL: Hash mismatch for $ARCHIVE" >&2
    echo "  Expected: $EXPECTED_HASH" >&2
    echo "  Actual:   $ACTUAL_HASH" >&2
    exit 1
fi
