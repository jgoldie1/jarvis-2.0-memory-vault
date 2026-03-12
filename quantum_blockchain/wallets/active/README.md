# All American Marketplace — Active Wallets Backup

This folder holds **active wallet files** exported by `backup.sh`.

## Contents

| File | Description |
|------|-------------|
| `wallet.json` | Main marketplace wallet (balance, address) |
| `*.keystore` | Encrypted keystore files (one per wallet) |
| `*.wif` | WIF-encoded private keys (keep offline) |
| `addresses.txt` | List of all known public addresses |

## Security Guidelines

- **Never commit** real private keys or mnemonics to version control.
- Keep this folder **chmod 700** and wallet files **chmod 600**.
- Restore these files only to a machine you control.
- After restore, rotate any keys that may have been exposed.

## Restore Wallet

```bash
# Copy wallets to their live location after running restore.sh:
cp -r ./active/* /home/theallamericanmarketplace/aam_clean/quantum_blockchain/wallets/active/
chmod 700 /home/theallamericanmarketplace/aam_clean/quantum_blockchain/wallets/
chmod 600 /home/theallamericanmarketplace/aam_clean/quantum_blockchain/wallets/active/*
```
