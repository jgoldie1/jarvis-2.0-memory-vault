# All American Marketplace — Chain Snapshots

This folder holds **signed chain data snapshots** produced by `backup.sh`.

## File Naming Convention

```
chain_snapshot_<TIMESTAMP>.tar.gz       — compressed chain export
chain_snapshot_<TIMESTAMP>.tar.gz.sha256 — SHA-256 checksum
chain_snapshot_<TIMESTAMP>.tar.gz.sig   — GPG detached signature (if available)
```

## Verify a Snapshot

```bash
# SHA-256 check:
sha256sum --check chain_snapshot_20240115T120000Z.tar.gz.sha256

# GPG signature check (requires signer's public key imported):
gpg --verify chain_snapshot_20240115T120000Z.tar.gz.sig \
             chain_snapshot_20240115T120000Z.tar.gz
```

## Create a Snapshot Manually

```bash
# From the blockchain root:
SNAP="snapshots/chain_snapshot_$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
tar -czf "$SNAP" --exclude='.git' -C /home/theallamericanmarketplace/aam_clean quantum_blockchain/
sha256sum "$SNAP" > "${SNAP}.sha256"
gpg --batch --yes --detach-sign "$SNAP"   # optional
echo "Snapshot ready: $SNAP"
```

## Import Snapshot on Recovery Machine

```bash
tar -xzf chain_snapshot_<TIMESTAMP>.tar.gz -C /home/theallamericanmarketplace/aam_clean/
```
