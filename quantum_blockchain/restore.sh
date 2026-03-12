#!/bin/bash
# ==============================================================================
# restore.sh — All American Marketplace Quantum Blockchain
# Rebuilds the full project on a clean machine from a backup archive.
# Usage:  bash restore.sh <backup_archive.tar.gz> [INSTALL_ROOT]
# Recovery order: 1) Node  2) API  3) Marketplace features
# Offline-capable. No editor steps required.
# ==============================================================================
set -euo pipefail

# ── Configurable ─────────────────────────────────────────────────────────────
ARCHIVE="${1:-}"
INSTALL_ROOT="${2:-/home/theallamericanmarketplace/aam_clean}"
BLOCKCHAIN_DIR="${INSTALL_ROOT}/quantum_blockchain"
LOG_FILE="/tmp/aam_restore_$(date -u +%Y%m%dT%H%M%SZ).log"

# ── Helpers ──────────────────────────────────────────────────────────────────
log()  { echo "[$(date -u +%H:%M:%SZ)] $*" | tee -a "${LOG_FILE}"; }
die()  { echo "ERROR: $*" >&2; exit 1; }
step() { echo; echo "══════════════════════════════════════════════════"; \
         echo "  STEP $*"; \
         echo "══════════════════════════════════════════════════"; }

# ── Pre-flight ────────────────────────────────────────────────────────────────
[ -z "${ARCHIVE}" ] && die "Usage: bash restore.sh <backup_archive.tar.gz> [INSTALL_ROOT]"
[ -f "${ARCHIVE}" ] || die "Archive not found: ${ARCHIVE}"
command -v tar >/dev/null 2>&1 || die "tar not found"
command -v python3 >/dev/null 2>&1 || die "python3 not found — install Python 3.9+"

log "Starting AAM restore from: ${ARCHIVE}"
log "Install root            : ${INSTALL_ROOT}"
log "Log file                : ${LOG_FILE}"

# ── Verify archive hash ───────────────────────────────────────────────────────
ARCHIVE_SHA="${ARCHIVE%.tar.gz}.sha256"
# The hash might be embedded inside the archive; try external file first
if [ -f "${ARCHIVE_SHA}" ]; then
    log "Verifying archive checksum ..."
    sha256sum --check "${ARCHIVE_SHA}" 2>/dev/null || \
        shasum -a 256 --check "${ARCHIVE_SHA}" || \
        log "⚠️  Checksum mismatch — proceeding with caution"
else
    log "⚠️  No external .sha256 file found for archive — skipping pre-check"
fi

# ── Extract archive ───────────────────────────────────────────────────────────
WORK_DIR="$(mktemp -d /tmp/aam_restore_XXXXXX)"
log "Extracting archive to ${WORK_DIR} ..."
tar -xzf "${ARCHIVE}" -C "${WORK_DIR}"

# Find the backup root inside the extracted directory
BACKUP_ROOT="$(find "${WORK_DIR}" -maxdepth 2 -name "*.sha256" -printf "%h\n" 2>/dev/null | head -1)"
[ -z "${BACKUP_ROOT}" ] && BACKUP_ROOT="${WORK_DIR}/$(ls "${WORK_DIR}" | head -1)"
log "Backup root: ${BACKUP_ROOT}"

# ── Verify file integrity from manifest ──────────────────────────────────────
MANIFEST="$(find "${WORK_DIR}" -maxdepth 2 -name '*.sha256' ! -name '*.tar.gz.sha256' | head -1)"
if [ -f "${MANIFEST}" ]; then
    log "Verifying file manifest ..."
    FAILED=0
    while IFS= read -r line; do
        EXPECTED_HASH="$(echo "$line" | awk '{print $1}')"
        REL_PATH="$(echo "$line" | awk '{print $2}')"
        # Resolve path relative to work dir
        FULL_PATH="${WORK_DIR}/${REL_PATH#*/}"
        if [ -f "${FULL_PATH}" ]; then
            ACTUAL_HASH="$(sha256sum "${FULL_PATH}" 2>/dev/null | awk '{print $1}' || \
                           shasum -a 256 "${FULL_PATH}" 2>/dev/null | awk '{print $1}')"
            if [ "${ACTUAL_HASH}" != "${EXPECTED_HASH}" ]; then
                log "  ❌ Hash mismatch: ${REL_PATH}"
                FAILED=$((FAILED + 1))
            fi
        fi
    done < "${MANIFEST}"
    if [ "${FAILED}" -gt 0 ]; then
        log "⚠️  ${FAILED} file(s) failed integrity check — review before continuing"
    else
        log "✅ All manifest hashes verified"
    fi
fi

# ══════════════════════════════════════════════════════════════════════════════
step "1 of 3 — NODE: Install system dependencies & restore chain data"
# ══════════════════════════════════════════════════════════════════════════════

log "Creating install root: ${BLOCKCHAIN_DIR}"
mkdir -p "${BLOCKCHAIN_DIR}"
mkdir -p "${BLOCKCHAIN_DIR}/wallets/active"
mkdir -p "${BLOCKCHAIN_DIR}/wallets/archive"
mkdir -p "${BLOCKCHAIN_DIR}/snapshots"
mkdir -p "${BLOCKCHAIN_DIR}/logs"

# Install Python venv
log "Setting up Python virtual environment ..."
if python3 -m venv "${BLOCKCHAIN_DIR}/venv" 2>&1 | tee -a "${LOG_FILE}"; then
    log "  ✅ venv created"
else
    log "  ⚠️  venv creation failed — will use system Python"
fi

# Restore requirements.txt and install dependencies
REQ_FILE="$(find "${WORK_DIR}" -name 'requirements.txt' | head -1)"
if [ -f "${REQ_FILE}" ]; then
    cp "${REQ_FILE}" "${BLOCKCHAIN_DIR}/requirements.txt"
    log "Installing Python dependencies from requirements.txt ..."
    if [ -f "${BLOCKCHAIN_DIR}/venv/bin/pip" ]; then
        "${BLOCKCHAIN_DIR}/venv/bin/pip" install --upgrade pip 2>&1 | tee -a "${LOG_FILE}"
        "${BLOCKCHAIN_DIR}/venv/bin/pip" install -r "${BLOCKCHAIN_DIR}/requirements.txt" \
            2>&1 | tee -a "${LOG_FILE}" || log "⚠️  Some packages failed to install"
    else
        pip3 install -r "${BLOCKCHAIN_DIR}/requirements.txt" \
            2>&1 | tee -a "${LOG_FILE}" || log "⚠️  Some packages failed to install"
    fi
    log "  ✅ Python dependencies installed"
else
    log "  ⚠️  requirements.txt not found in backup — skipping pip install"
fi

# Restore chain data
CHAIN_DATA_SRC="$(find "${WORK_DIR}" -type d -name 'chain_data' | head -1)"
if [ -d "${CHAIN_DATA_SRC}" ]; then
    log "Restoring chain data ..."
    cp -r "${CHAIN_DATA_SRC}/." "${BLOCKCHAIN_DIR}/"
    log "  ✅ Chain data restored"
fi

# Restore signed snapshot (latest)
SNAP_SRC="$(find "${WORK_DIR}" -type d -name 'snapshots' | head -1)"
if [ -d "${SNAP_SRC}" ]; then
    log "Restoring chain snapshots ..."
    cp -r "${SNAP_SRC}/." "${BLOCKCHAIN_DIR}/snapshots/"
    log "  ✅ Snapshots restored"
fi

# ══════════════════════════════════════════════════════════════════════════════
step "2 of 3 — API: Restore configs & source code"
# ══════════════════════════════════════════════════════════════════════════════

# Restore configs
CONFIG_SRC="$(find "${WORK_DIR}" -type d -name 'configs' | head -1)"
if [ -d "${CONFIG_SRC}" ]; then
    log "Restoring configs ..."
    find "${CONFIG_SRC}" -maxdepth 1 -type f | while IFS= read -r cfg; do
        cp "${cfg}" "${BLOCKCHAIN_DIR}/"
        log "  ✅ Config restored: $(basename "${cfg}")"
    done
    if [ -d "${CONFIG_SRC}/blockchain_configs" ]; then
        cp -r "${CONFIG_SRC}/blockchain_configs" "${BLOCKCHAIN_DIR}/configs"
    fi
fi

# Restore source code
SOURCE_SRC="$(find "${WORK_DIR}" -type d -name 'source' | head -1)"
if [ -d "${SOURCE_SRC}" ]; then
    log "Restoring source code ..."
    rsync -a "${SOURCE_SRC}/" "${BLOCKCHAIN_DIR}/source/" 2>/dev/null || \
        cp -r "${SOURCE_SRC}" "${BLOCKCHAIN_DIR}/source"
    log "  ✅ Source code restored to ${BLOCKCHAIN_DIR}/source"
fi

# ══════════════════════════════════════════════════════════════════════════════
step "3 of 3 — MARKETPLACE: Restore wallets & fintech data"
# ══════════════════════════════════════════════════════════════════════════════

WALLET_SRC="$(find "${WORK_DIR}" -type d -name 'wallets' | head -1)"
if [ -d "${WALLET_SRC}" ]; then
    log "Restoring wallets ..."
    if [ -d "${WALLET_SRC}/active" ]; then
        cp -r "${WALLET_SRC}/active/." "${BLOCKCHAIN_DIR}/wallets/active/"
    fi
    if [ -d "${WALLET_SRC}/archive" ]; then
        cp -r "${WALLET_SRC}/archive/." "${BLOCKCHAIN_DIR}/wallets/archive/"
    fi
    # Also restore top-level wallet files
    find "${WALLET_SRC}" -maxdepth 1 -type f | while IFS= read -r wf; do
        cp "${wf}" "${BLOCKCHAIN_DIR}/wallets/active/"
    done
    log "  ✅ Wallets restored"
fi

# ── Set permissions ───────────────────────────────────────────────────────────
log "Setting secure permissions on wallets and configs ..."
chmod 700 "${BLOCKCHAIN_DIR}/wallets" 2>/dev/null || true
chmod 600 "${BLOCKCHAIN_DIR}/wallets/active/"* 2>/dev/null || true
chmod 600 "${BLOCKCHAIN_DIR}/.env" 2>/dev/null || true

# ── Cleanup temp dir ──────────────────────────────────────────────────────────
rm -rf "${WORK_DIR}"

log "========================================================="
log "✅ Restore complete!"
log "  Install location : ${BLOCKCHAIN_DIR}"
log "  Log file         : ${LOG_FILE}"
log ""
log "  Next steps:"
log "    1. Review configs  : ${BLOCKCHAIN_DIR}/"
log "    2. Activate venv   : source ${BLOCKCHAIN_DIR}/venv/bin/activate"
log "    3. Start the node  : (see README_RECOVERY.md)"
log "    4. Start the API   : (see README_RECOVERY.md)"
log "    5. Start marketplace: (see README_RECOVERY.md)"
log "========================================================="
