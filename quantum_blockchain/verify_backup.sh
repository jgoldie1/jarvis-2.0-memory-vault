#!/bin/bash
# ==============================================================================
# verify_backup.sh — All American Marketplace Quantum Blockchain
# Verifies backup archive integrity: checksums, structure, and wallet presence.
# Usage:  bash verify_backup.sh <backup_archive.tar.gz>
# Offline-capable. No editor steps required.
# ==============================================================================
set -euo pipefail

ARCHIVE="${1:-}"
PASS=0
FAIL=0
WARN=0

# ── Helpers ──────────────────────────────────────────────────────────────────
ok()   { echo "  ✅ PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "  ❌ FAIL: $*"; FAIL=$((FAIL + 1)); }
warn() { echo "  ⚠️  WARN: $*"; WARN=$((WARN + 1)); }
log()  { echo "[$(date -u +%H:%M:%SZ)] $*"; }
sep()  { echo "──────────────────────────────────────────────────────"; }

[ -z "${ARCHIVE}" ] && { echo "Usage: bash verify_backup.sh <backup_archive.tar.gz>"; exit 1; }
[ -f "${ARCHIVE}" ] || { echo "ERROR: Archive not found: ${ARCHIVE}"; exit 1; }

log "Verifying backup: ${ARCHIVE}"
sep

# ── 1. Archive hash ───────────────────────────────────────────────────────────
echo "[ CHECK 1 ] Archive file integrity"
ARCHIVE_SHA="${ARCHIVE}.sha256"
if [ -f "${ARCHIVE_SHA}" ]; then
    if sha256sum --check "${ARCHIVE_SHA}" >/dev/null 2>&1 || \
       shasum -a 256 --check "${ARCHIVE_SHA}" >/dev/null 2>&1; then
        ok "Archive SHA-256 matches: $(basename "${ARCHIVE_SHA}")"
    else
        fail "Archive SHA-256 MISMATCH — archive may be corrupt or tampered"
    fi
else
    warn "No external .sha256 file found alongside archive"
fi
sep

# ── 2. Extract & inspect ──────────────────────────────────────────────────────
WORK_DIR="$(mktemp -d /tmp/aam_verify_XXXXXX)"
log "Extracting to temp dir: ${WORK_DIR}"
tar -xzf "${ARCHIVE}" -C "${WORK_DIR}" || { fail "tar extraction failed"; exit 1; }

BACKUP_ROOT="$(ls "${WORK_DIR}" | head -1)"
BACKUP_PATH="${WORK_DIR}/${BACKUP_ROOT}"
[ -d "${BACKUP_PATH}" ] || BACKUP_PATH="${WORK_DIR}"

echo
echo "[ CHECK 2 ] Required directory structure"
REQUIRED_DIRS=("source" "chain_data" "configs" "wallets" "snapshots")
for d in "${REQUIRED_DIRS[@]}"; do
    if [ -d "${BACKUP_PATH}/${d}" ]; then
        ok "Directory present: ${d}/"
    else
        warn "Directory missing: ${d}/"
    fi
done
sep

echo "[ CHECK 3 ] Wallet backup presence"
WALLET_DIR="${BACKUP_PATH}/wallets"
if [ -d "${WALLET_DIR}" ]; then
    WALLET_COUNT="$(find "${WALLET_DIR}" -type f | wc -l)"
    if [ "${WALLET_COUNT}" -gt 0 ]; then
        ok "Wallet files found: ${WALLET_COUNT} file(s)"
        find "${WALLET_DIR}" -type f | while IFS= read -r wf; do
            echo "     └── $(basename "${wf}")"
        done
    else
        warn "Wallet directory exists but contains no files"
    fi
else
    warn "No wallets directory found in backup"
fi
sep

echo "[ CHECK 4 ] Chain snapshot presence & signature"
SNAP_DIR="${BACKUP_PATH}/snapshots"
if [ -d "${SNAP_DIR}" ]; then
    SNAP_COUNT="$(find "${SNAP_DIR}" -name '*.tar.gz' | wc -l)"
    if [ "${SNAP_COUNT}" -gt 0 ]; then
        ok "Chain snapshot(s) found: ${SNAP_COUNT}"
        find "${SNAP_DIR}" -name '*.tar.gz' | while IFS= read -r snap; do
            echo "     └── $(basename "${snap}")"
            # Verify snapshot's own SHA256
            SHA_FILE="${snap}.sha256"
            if [ -f "${SHA_FILE}" ]; then
                if sha256sum --check "${SHA_FILE}" >/dev/null 2>&1 || \
                   shasum -a 256 --check "${SHA_FILE}" >/dev/null 2>&1; then
                    ok "  Snapshot checksum valid: $(basename "${snap}")"
                else
                    fail "  Snapshot checksum mismatch: $(basename "${snap}")"
                fi
            else
                warn "  No .sha256 found for snapshot: $(basename "${snap}")"
            fi
            # Check for GPG signature
            if [ -f "${snap}.sig" ]; then
                ok "  GPG signature present: $(basename "${snap}").sig"
                if command -v gpg >/dev/null 2>&1; then
                    if gpg --verify "${snap}.sig" "${snap}" >/dev/null 2>&1; then
                        ok "  GPG signature valid"
                    else
                        warn "  GPG signature could not be verified (key may not be imported)"
                    fi
                else
                    warn "  gpg not available — skipping signature verification"
                fi
            else
                warn "  No GPG signature (.sig) for snapshot: $(basename "${snap}")"
            fi
        done
    else
        warn "No chain snapshot .tar.gz files found in snapshots/"
    fi
else
    warn "No snapshots directory found in backup"
fi
sep

echo "[ CHECK 5 ] File manifest hash verification"
MANIFEST="$(find "${WORK_DIR}" -maxdepth 2 -name '*.sha256' ! -name '*.tar.gz.sha256' | head -1)"
if [ -f "${MANIFEST}" ]; then
    TOTAL=0
    MATCH=0
    MISMATCH=0
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        EXPECTED_HASH="$(echo "$line" | awk '{print $1}')"
        RAW_PATH="$(echo "$line" | awk '{print $2}')"
        # Strip leading "./" — paths are relative to the backup root directory
        REL_PATH="${RAW_PATH#./}"
        FULL_PATH="${BACKUP_PATH}/${REL_PATH}"
        TOTAL=$((TOTAL + 1))
        if [ -f "${FULL_PATH}" ]; then
            ACTUAL_HASH="$(sha256sum "${FULL_PATH}" 2>/dev/null | awk '{print $1}' || \
                           shasum -a 256 "${FULL_PATH}" 2>/dev/null | awk '{print $1}')"
            if [ "${ACTUAL_HASH}" = "${EXPECTED_HASH}" ]; then
                MATCH=$((MATCH + 1))
            else
                MISMATCH=$((MISMATCH + 1))
                fail "Hash mismatch: ${REL_PATH}"
            fi
        fi
    done < "${MANIFEST}"
    if [ "${MISMATCH}" -eq 0 ]; then
        ok "All ${MATCH}/${TOTAL} manifest hashes verified"
    else
        fail "${MISMATCH} file(s) failed hash verification"
    fi
else
    warn "No manifest .sha256 file found in backup root"
fi
sep

echo "[ CHECK 6 ] Config files"
CONFIGS_DIR="${BACKUP_PATH}/configs"
if [ -d "${CONFIGS_DIR}" ]; then
    CFG_COUNT="$(find "${CONFIGS_DIR}" -type f | wc -l)"
    ok "Config files present: ${CFG_COUNT} file(s)"
else
    warn "No configs directory found in backup"
fi
sep

echo "[ CHECK 7 ] Source code"
SOURCE_DIR="${BACKUP_PATH}/source"
if [ -d "${SOURCE_DIR}" ]; then
    SRC_COUNT="$(find "${SOURCE_DIR}" -type f | wc -l)"
    ok "Source files present: ${SRC_COUNT} file(s)"
else
    warn "No source directory found in backup"
fi
sep

# ── Cleanup ───────────────────────────────────────────────────────────────────
rm -rf "${WORK_DIR}"

# ── Summary ───────────────────────────────────────────────────────────────────
echo
echo "======================================================"
echo "  VERIFICATION SUMMARY"
echo "======================================================"
echo "  ✅ Passed : ${PASS}"
echo "  ⚠️  Warnings: ${WARN}"
echo "  ❌ Failed : ${FAIL}"
echo "======================================================"
if [ "${FAIL}" -gt 0 ]; then
    echo "  ❌ BACKUP IS NOT CLEAN — review failures above"
    exit 1
elif [ "${WARN}" -gt 0 ]; then
    echo "  ⚠️  Backup has warnings — review before relying on restore"
    exit 0
else
    echo "  ✅ Backup verified successfully"
    exit 0
fi
