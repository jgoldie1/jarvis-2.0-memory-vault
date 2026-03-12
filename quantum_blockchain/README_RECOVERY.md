# README_RECOVERY.md — All American Marketplace Blockchain
## Disaster Recovery & Restore Guide

> **Goal:** Get the system back online from a backup archive on a clean machine.  
> **Design:** Offline-capable. Paste-ready terminal commands. No editor steps.  
> **Recovery order:** Node → API → Marketplace features

---

## Table of Contents

1. [What You Need](#1-what-you-need)
2. [Quick-Start Recovery (3 steps)](#2-quick-start-recovery-3-steps)
3. [Step 1 — Node: System & Python Setup](#step-1--node-system--python-setup)
4. [Step 2 — API: Restore Code & Configs](#step-2--api-restore-code--configs)
5. [Step 3 — Marketplace: Wallets & Fintech Data](#step-3--marketplace-wallets--fintech-data)
6. [Verifying Your Backup Before Restore](#6-verifying-your-backup-before-restore)
7. [Creating a Fresh Backup](#7-creating-a-fresh-backup)
8. [Signing Chain Snapshots](#8-signing-chain-snapshots)
9. [Environment Variables Reference](#9-environment-variables-reference)
10. [Troubleshooting](#10-troubleshooting)
11. [Security Checklist](#11-security-checklist)

---

## 1. What You Need

| Item | Details |
|------|---------|
| **Backup archive** | `aam_backup_<TIMESTAMP>.tar.gz` |
| **Hash manifest** | `aam_backup_<TIMESTAMP>.sha256` (alongside archive) |
| **OS** | Ubuntu 22.04 LTS / Debian 11+ / macOS 12+ |
| **Python** | 3.9 or newer |
| **Tools** | `tar`, `sha256sum`, `rsync`, `bash` |
| **Optional** | `gpg` (for signature verification), `git` |

---

## 2. Quick-Start Recovery (3 steps)

Copy and paste these three commands on the recovery machine:

```bash
# 1. Verify the backup first
bash verify_backup.sh aam_backup_<TIMESTAMP>.tar.gz

# 2. Restore everything (node → API → marketplace)
bash restore.sh aam_backup_<TIMESTAMP>.tar.gz /home/theallamericanmarketplace/aam_clean

# 3. Start the stack (see Step 3 below for individual services)
source /home/theallamericanmarketplace/aam_clean/quantum_blockchain/venv/bin/activate
```

---

## Step 1 — Node: System & Python Setup

This is always done **first**. The node is the foundation everything else depends on.

### 1a. Install system packages (Ubuntu/Debian)

```bash
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv \
    tar rsync curl wget git gpg coreutils
```

### 1b. Install system packages (macOS with Homebrew)

```bash
brew update
brew install python@3.11 rsync gnupg coreutils
```

### 1c. Create the project directory

```bash
sudo mkdir -p /home/theallamericanmarketplace/aam_clean/quantum_blockchain
sudo chown -R "$USER":"$USER" /home/theallamericanmarketplace/aam_clean
```

### 1d. Set up Python virtual environment

```bash
cd /home/theallamericanmarketplace/aam_clean/quantum_blockchain
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### 1e. Install Python dependencies

```bash
pip install -r /home/theallamericanmarketplace/aam_clean/quantum_blockchain/requirements.txt
```

> If you don't yet have `requirements.txt`, use the one from the backup:
> ```bash
> pip install Flask gunicorn requests Pillow pyttsx3 gTTS SpeechRecognition \
>     opencv-python-headless cryptography pycryptodome mnemonic \
>     pydantic python-dotenv
> ```

### 1f. Restore chain data

```bash
# Chain data is restored automatically by restore.sh.
# To do it manually from a snapshot:
SNAP="aam_backup_<TIMESTAMP>/snapshots/chain_snapshot_<TIMESTAMP>.tar.gz"
sha256sum --check "${SNAP}.sha256"
tar -xzf "$SNAP" -C /home/theallamericanmarketplace/aam_clean/
```

---

## Step 2 — API: Restore Code & Configs

Done **after** the node is up. The API layer sits on top of chain data.

### 2a. Restore source code

```bash
# restore.sh handles this automatically.
# Manual alternative:
rsync -a aam_backup_<TIMESTAMP>/source/ \
    /home/theallamericanmarketplace/aam_clean/quantum_blockchain/source/
```

### 2b. Restore config files

```bash
cp aam_backup_<TIMESTAMP>/configs/.env \
   /home/theallamericanmarketplace/aam_clean/quantum_blockchain/.env
cp aam_backup_<TIMESTAMP>/configs/config.json \
   /home/theallamericanmarketplace/aam_clean/quantum_blockchain/
chmod 600 /home/theallamericanmarketplace/aam_clean/quantum_blockchain/.env
```

### 2c. Start the API server

```bash
cd /home/theallamericanmarketplace/aam_clean/quantum_blockchain/source
source ../venv/bin/activate
gunicorn --bind 0.0.0.0:5000 --workers 2 wsgi:app &
echo "API running on http://localhost:5000"
```

---

## Step 3 — Marketplace: Wallets & Fintech Data

Done **last**, after the node and API are confirmed running.

### 3a. Restore wallets

```bash
mkdir -p /home/theallamericanmarketplace/aam_clean/quantum_blockchain/wallets/active
mkdir -p /home/theallamericanmarketplace/aam_clean/quantum_blockchain/wallets/archive

cp -r aam_backup_<TIMESTAMP>/wallets/active/. \
    /home/theallamericanmarketplace/aam_clean/quantum_blockchain/wallets/active/
cp -r aam_backup_<TIMESTAMP>/wallets/archive/. \
    /home/theallamericanmarketplace/aam_clean/quantum_blockchain/wallets/archive/

chmod 700 /home/theallamericanmarketplace/aam_clean/quantum_blockchain/wallets/
chmod 600 /home/theallamericanmarketplace/aam_clean/quantum_blockchain/wallets/active/*  2>/dev/null || true
chmod 600 /home/theallamericanmarketplace/aam_clean/quantum_blockchain/wallets/archive/* 2>/dev/null || true
```

### 3b. Restore fintech data (marketplace)

```bash
# Fintech JSON files (wallet balances, NFTs, passport, AI stats):
cp aam_backup_<TIMESTAMP>/source/golden_era_marketplace/fintech/wallet.json \
   /home/theallamericanmarketplace/aam_clean/quantum_blockchain/source/golden_era_marketplace/fintech/
```

### 3c. Start the marketplace dashboard

```bash
cd /home/theallamericanmarketplace/aam_clean/quantum_blockchain/source/golden_era_marketplace
python3 -m http.server 8000 &
echo "Marketplace dashboard at http://localhost:8000"
```

---

## 6. Verifying Your Backup Before Restore

**Always verify before restoring.** One command does it all:

```bash
bash verify_backup.sh aam_backup_<TIMESTAMP>.tar.gz
```

What it checks:

| Check | What it does |
|-------|-------------|
| Archive SHA-256 | Confirms the `.tar.gz` file isn't corrupt |
| Directory structure | Ensures `source/`, `chain_data/`, `wallets/`, etc. exist |
| Wallet presence | Lists all backed-up wallet files |
| Snapshot integrity | Verifies each snapshot's checksum and GPG sig |
| File manifest | Re-hashes every file against the recorded manifest |
| Config presence | Confirms config files were captured |

---

## 7. Creating a Fresh Backup

```bash
# From the repository root:
bash quantum_blockchain/backup.sh ~/aam_backups

# With a custom output directory:
BLOCKCHAIN_ROOT=/home/theallamericanmarketplace/aam_clean/quantum_blockchain \
    bash quantum_blockchain/backup.sh /mnt/usb_drive/backups
```

The script produces:
- `aam_backup_<TIMESTAMP>.tar.gz` — full compressed archive
- `aam_backup_<TIMESTAMP>.sha256` — SHA-256 manifest of all files

---

## 8. Signing Chain Snapshots

GPG signing is automatic when `gpg` is installed and a key exists.

### Set up GPG signing key (once)

```bash
gpg --batch --gen-key <<EOF
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: AAM Backup Signer
Name-Email: backup@allamericanmarketplace.local
Expire-Date: 2y
%no-protection
%commit
EOF
```

### Export your public key (for verification on other machines)

```bash
gpg --export --armor backup@allamericanmarketplace.local > aam_backup_pubkey.asc
# Store aam_backup_pubkey.asc alongside backups or in a safe location
```

### Import public key on recovery machine

```bash
gpg --import aam_backup_pubkey.asc
```

### Manually sign a snapshot

```bash
SNAP="quantum_blockchain/snapshots/chain_snapshot_$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
tar -czf "$SNAP" --exclude='.git' -C /home/theallamericanmarketplace/aam_clean quantum_blockchain/
sha256sum "$SNAP" > "${SNAP}.sha256"
gpg --batch --yes --detach-sign "$SNAP"
echo "Signed snapshot: $SNAP"
```

---

## 9. Environment Variables Reference

These can be set before running any script to override defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `BLOCKCHAIN_ROOT` | `/home/theallamericanmarketplace/aam_clean/quantum_blockchain` | Path to live blockchain directory |
| `REPO_ROOT` | Parent of `quantum_blockchain/` | Path to the repository root |

Example:

```bash
export BLOCKCHAIN_ROOT=/data/aam/quantum_blockchain
export REPO_ROOT=/srv/jarvis-2.0-memory-vault
bash quantum_blockchain/backup.sh /mnt/backup_drive
```

---

## 10. Troubleshooting

### `sha256sum: command not found`

```bash
# Ubuntu/Debian:
sudo apt-get install -y coreutils

# macOS (Homebrew):
brew install coreutils
# Then use gsha256sum or add to PATH:
export PATH="$(brew --prefix coreutils)/libexec/gnubin:$PATH"
```

### `venv creation failed`

```bash
# Install the venv module:
sudo apt-get install -y python3-venv
# Or use system pip directly:
pip3 install -r requirements.txt
```

### `gpg: keyring error`

```bash
mkdir -p ~/.gnupg && chmod 700 ~/.gnupg
gpg --import aam_backup_pubkey.asc
```

### Restore fails midway

The restore log is written to `/tmp/aam_restore_<TIMESTAMP>.log`.  
Check it for the exact error:

```bash
cat /tmp/aam_restore_*.log | tail -50
```

### Wallet files not found after restore

Wallet files must be copied manually if `restore.sh` can't locate them:

```bash
find /tmp/aam_restore_* -name '*.json' -path '*/wallets/*' 2>/dev/null
```

---

## 11. Security Checklist

Before going live after a restore:

- [ ] Wallet files have `chmod 600`
- [ ] Wallets directory has `chmod 700`
- [ ] `.env` file has `chmod 600`
- [ ] No private keys committed to git (`git log --all -p | grep -i private`)
- [ ] Chain snapshot GPG signature verified
- [ ] All file manifest hashes passed `verify_backup.sh`
- [ ] API server is only accessible on intended network interface
- [ ] `bandit -r source/` shows no critical security issues

---

*Last updated: 2026-03-12 | All American Marketplace Quantum Blockchain Recovery System*
