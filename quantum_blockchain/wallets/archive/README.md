# All American Marketplace — Archived Wallets Backup

This folder holds **archived / retired wallet files** exported by `backup.sh`.

## Purpose

Archive wallets that are no longer in active use but must be retained for:
- Historical transaction verification
- Audit purposes
- Recovery of old funds

## Security Guidelines

- **Never commit** real private keys or mnemonics to version control.
- Files here must remain **chmod 600**.
- Label each archived wallet with the date it was retired:
  `wallet_2024-01-15_retired.json`

## Archive a Wallet

```bash
# Move an active wallet to archive (run from blockchain root):
mv wallets/active/wallet_old.json wallets/archive/wallet_$(date +%Y-%m-%d)_retired.json
chmod 600 wallets/archive/*
```
