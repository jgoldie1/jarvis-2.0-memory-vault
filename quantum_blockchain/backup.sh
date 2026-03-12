#!/bin/bash
# ==============================================================================
# backup.sh — All American Marketplace Quantum Blockchain
# Exports: source code, chain data, configs, and wallets to a timestamped archive
# Usage:  bash backup.sh [OUTPUT_DIR]
# Offline-capable. No editor steps required.
# ==============================================================================
set -euo pipefail

# ── Configurable paths ──────────────────────────────────────────────────────
BLOCKCHAIN_ROOT="${BLOCKCHAIN_ROOT:-/home/theallamericanmarketplace/aam_clean/quantum_blockchain}"
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
OUTPUT_DIR="${1:-$HOME/aam_backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_NAME="aam_backup_${TIMESTAMP}"
BACKUP_DIR="${OUTPUT_DIR}/${BACKUP_NAME}"
HASH_FILE="${OUTPUT_DIR}/${BACKUP_NAME}.sha256"
ARCHIVE="${OUTPUT_DIR}/${BACKUP_NAME}.tar.gz"

# ── Helpers ──────────────────────────────────────────────────────────────────
log()  { echo "[$(date -u +%H:%M:%SZ)] $*"; }
die()  { echo "ERROR: $*" >&2; exit 1; }

# ── Pre-flight checks ────────────────────────────────────────────────────────
command -v sha256sum >/dev/null 2>&1 || command -v shasum >/dev/null 2>&1 || \
    die "sha256sum / shasum not found — install coreutils"
command -v tar >/dev/null 2>&1 || die "tar not found"

log "Starting AAM backup → ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}"

# ── 1. Source code ───────────────────────────────────────────────────────────
log "Backing up source code from ${REPO_ROOT} ..."
mkdir -p "${BACKUP_DIR}/source"
rsync -a --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
      --exclude='node_modules' --exclude='venv' --exclude='.venv' \
      "${REPO_ROOT}/" "${BACKUP_DIR}/source/" 2>/dev/null || \
  cp -r "${REPO_ROOT}" "${BACKUP_DIR}/source/"

# ── 2. Chain data ────────────────────────────────────────────────────────────
log "Backing up chain data ..."
mkdir -p "${BACKUP_DIR}/chain_data"
for dir in \
    "${BLOCKCHAIN_ROOT}/data" \
    "${BLOCKCHAIN_ROOT}/blocks" \
    "${BLOCKCHAIN_ROOT}/chainstate" \
    "${BLOCKCHAIN_ROOT}/ledger"; do
    if [ -d "$dir" ]; then
        cp -r "$dir" "${BACKUP_DIR}/chain_data/"
        log "  ✅ Copied chain dir: $(basename "$dir")"
    else
        log "  ⚠️  Chain dir not found (skipping): $dir"
    fi
done

# ── 3. Configs ───────────────────────────────────────────────────────────────
log "Backing up configs ..."
mkdir -p "${BACKUP_DIR}/configs"
for item in \
    "${BLOCKCHAIN_ROOT}/.env" \
    "${BLOCKCHAIN_ROOT}/config.json" \
    "${BLOCKCHAIN_ROOT}/config.yaml" \
    "${BLOCKCHAIN_ROOT}/requirements.txt" \
    "${REPO_ROOT}/requirements.txt" \
    "${BLOCKCHAIN_ROOT}/quantum_node_config.json" \
    "${BLOCKCHAIN_ROOT}/api_config.json"; do
    if [ -f "$item" ]; then
        cp "$item" "${BACKUP_DIR}/configs/"
        log "  ✅ Copied config: $(basename "$item")"
    fi
done
# Copy entire configs/ sub-directory if present
if [ -d "${BLOCKCHAIN_ROOT}/configs" ]; then
    cp -r "${BLOCKCHAIN_ROOT}/configs" "${BACKUP_DIR}/configs/blockchain_configs"
fi

# ── 4. Wallets ───────────────────────────────────────────────────────────────
log "Backing up wallets ..."
mkdir -p "${BACKUP_DIR}/wallets/active"
mkdir -p "${BACKUP_DIR}/wallets/archive"

WALLET_SOURCES=(
    "${BLOCKCHAIN_ROOT}/wallets"
    "${BLOCKCHAIN_ROOT}/wallet"
    "${REPO_ROOT}/golden_era_marketplace/fintech/wallet.json"
    "${REPO_ROOT}/quantum_blockchain/wallets"
)
for src in "${WALLET_SOURCES[@]}"; do
    if [ -d "$src" ]; then
        cp -r "$src/." "${BACKUP_DIR}/wallets/active/"
        log "  ✅ Copied wallet dir: $src"
    elif [ -f "$src" ]; then
        cp "$src" "${BACKUP_DIR}/wallets/active/"
        log "  ✅ Copied wallet file: $(basename "$src")"
    fi
done

# ── 5. Snapshots ─────────────────────────────────────────────────────────────
log "Backing up existing chain snapshots ..."
mkdir -p "${BACKUP_DIR}/snapshots"
SNAPSHOT_DIRS=(
    "${BLOCKCHAIN_ROOT}/snapshots"
    "${REPO_ROOT}/quantum_blockchain/snapshots"
)
for sdir in "${SNAPSHOT_DIRS[@]}"; do
    if [ -d "$sdir" ]; then
        cp -r "$sdir/." "${BACKUP_DIR}/snapshots/"
        log "  ✅ Copied snapshots: $sdir"
    fi
done

# ── 6. Signed chain snapshot (live export) ───────────────────────────────────
log "Creating signed chain snapshot ..."
SNAP_FILE="${BACKUP_DIR}/snapshots/chain_snapshot_${TIMESTAMP}.tar.gz"

if [ -d "${BLOCKCHAIN_ROOT}" ]; then
    tar -czf "${SNAP_FILE}" -C "$(dirname "${BLOCKCHAIN_ROOT}")" \
        "$(basename "${BLOCKCHAIN_ROOT}")" 2>/dev/null || \
        tar -czf "${SNAP_FILE}" --exclude='.git' \
            -C "${BLOCKCHAIN_ROOT}" . 2>/dev/null || true
else
    log "  ⚠️  BLOCKCHAIN_ROOT not found — snapshot skipped: ${BLOCKCHAIN_ROOT}"
fi

# Sign with GPG if available, otherwise use SHA256
if command -v gpg >/dev/null 2>&1 && [ -f "${SNAP_FILE}" ]; then
    gpg --batch --yes --detach-sign "${SNAP_FILE}" && \
        log "  ✅ GPG signature written: ${SNAP_FILE}.sig" || \
        log "  ⚠️  GPG signing failed — falling back to SHA256 only"
fi
if [ -f "${SNAP_FILE}" ]; then
    sha256sum "${SNAP_FILE}" > "${SNAP_FILE}.sha256" 2>/dev/null || \
        shasum -a 256 "${SNAP_FILE}" > "${SNAP_FILE}.sha256"
    log "  ✅ SHA256 written: ${SNAP_FILE}.sha256"
fi

# ── 7. Build manifest & hash file (relative paths) ───────────────────────────
log "Generating SHA-256 manifest ..."
(
    cd "${BACKUP_DIR}"
    find . -type f | sort | while IFS= read -r f; do
        sha256sum "$f" 2>/dev/null || shasum -a 256 "$f"
    done
) > "${HASH_FILE}"
log "  ✅ Manifest: ${HASH_FILE}"

# ── 8. Compress entire backup ────────────────────────────────────────────────
log "Compressing backup archive ..."
tar -czf "${ARCHIVE}" -C "${OUTPUT_DIR}" "${BACKUP_NAME}" "${BACKUP_NAME}.sha256"
log "  ✅ Archive: ${ARCHIVE}"

# Save checksum of the archive itself (used by verify_backup.sh check 1)
ARCHIVE_CHECKSUM_FILE="${ARCHIVE}.sha256"
sha256sum "${ARCHIVE}" 2>/dev/null > "${ARCHIVE_CHECKSUM_FILE}" || \
    shasum -a 256 "${ARCHIVE}" > "${ARCHIVE_CHECKSUM_FILE}"
log "  ✅ Archive checksum: ${ARCHIVE_CHECKSUM_FILE}"

log "========================================================="
log "Backup complete!"
log "  Archive : ${ARCHIVE}"
log "  Manifest: ${HASH_FILE}"
log "  Verify  : bash verify_backup.sh ${ARCHIVE}"
log "========================================================="
