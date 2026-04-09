# Quantum Blockchain Recovery Guide

## Project Path
/home/theallamericanmarketplace/aam_clean/quantum_blockchain

## What This System Is
This project is the local blockchain operating core for the All American Marketplace system.

## Recovery Priority Order
1. Restore source code and scripts
2. Restore wallets and keys
3. Restore chain data
4. Start local node
5. Start API
6. Restore marketplace-facing services

## Backup Creation
Run:
./backup.sh

This creates:
- a compressed backup archive in backups/
- a sha256 checksum file in backups/

## Backup Verification
Run:
./verify_backup.sh <archive.tar.gz> <archive.sha256>

## Restore On A Clean Machine
1. Copy the backup archive to the new machine
2. Run:
   ./restore.sh <archive.tar.gz> <target_directory>
3. Enter the restored directory
4. Install dependencies:
   python3 -m pip install -r requirements.txt
5. Start node:
   python3 run_node.py
6. Start API:
   python3 api.py

## Critical Files
- core/
- contracts/
- data/chain.json
- wallets/
- run_node.py
- api.py
- requirements.txt

## Notes
Keep multiple copies of backups in different locations.
Verify each backup after creation.
Protect wallet private keys carefully.
