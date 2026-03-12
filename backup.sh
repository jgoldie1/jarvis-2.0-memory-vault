#!/bin/bash
# =====================================================
# JARVIS 2.0 MEMORY VAULT - BACKUP SCRIPT
# Backs up critical project data with timestamps
# Rotates old backups to keep disk usage in check
# =====================================================

set -euo pipefail

# -------------------------
# Configuration
# -------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backups"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
ARCHIVE_NAME="jarvis_backup_${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_NAME}"
KEEP_LAST=5   # number of most-recent backups to retain
LOG="${BACKUP_DIR}/backup.log"

# Directories and files to include in the backup
BACKUP_TARGETS=(
    "golden_era_marketplace/ai"
    "golden_era_marketplace/fintech"
    "golden_era_marketplace/css"
    "golden_era_marketplace/js"
    "golden_era_marketplace/index.html"
    "Jarvis_os"
    "notes"
    "requirements.txt"
)

# -------------------------
# Setup
# -------------------------
mkdir -p "${BACKUP_DIR}"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "${LOG}"
}

log "=== Backup started: ${ARCHIVE_NAME} ==="

# -------------------------
# Collect targets that exist
# -------------------------
existing_targets=()
for target in "${BACKUP_TARGETS[@]}"; do
    full_path="${SCRIPT_DIR}/${target}"
    if [ -e "${full_path}" ]; then
        existing_targets+=("${target}")
        log "  Including: ${target}"
    else
        log "  Skipping (not found): ${target}"
    fi
done

if [ "${#existing_targets[@]}" -eq 0 ]; then
    log "ERROR: No backup targets found. Aborting."
    exit 1
fi

# -------------------------
# Create compressed archive
# -------------------------
log "Creating archive: ${ARCHIVE_PATH}"
tar -czf "${ARCHIVE_PATH}" -C "${SCRIPT_DIR}" "${existing_targets[@]}"

# -------------------------
# Verify archive
# -------------------------
if tar -tzf "${ARCHIVE_PATH}" > /dev/null 2>&1; then
    SIZE="$(du -sh "${ARCHIVE_PATH}" | cut -f1)"
    log "Archive verified successfully (${SIZE})."
else
    log "ERROR: Archive verification failed!"
    rm -f "${ARCHIVE_PATH}"
    exit 1
fi

# -------------------------
# Rotate old backups
# -------------------------
log "Rotating old backups (keeping last ${KEEP_LAST})..."
mapfile -t old_backups < <(
    ls -1t "${BACKUP_DIR}"/jarvis_backup_*.tar.gz 2>/dev/null | tail -n "+$((KEEP_LAST + 1))" || true
)
if [ "${#old_backups[@]}" -gt 0 ]; then
    for old in "${old_backups[@]}"; do
        log "  Removing: $(basename "${old}")"
        rm -f "${old}"
    done
fi

log "=== Backup complete: ${ARCHIVE_NAME} ==="
echo ""
echo "✅ Backup saved to: ${ARCHIVE_PATH}"
echo "📂 All backups:     ${BACKUP_DIR}"
