# memory-vault
AI memory, code, and project vault

## Copilot Auto-Fix (Golden Era Marketplace)

Run a full self-heal pass (folders/files, broken image paths, JSON/AI placeholders, deps, optional image processing):

```bash
python3 super_copilot_autofix.py --install-deps --process-images
```

Start the marketplace server after healing:

```bash
python3 super_copilot_autofix.py --start-server --port 8000
```

Run in continuous self-healing mode:

```bash
python3 super_copilot_autofix.py --install-deps --process-images --watch --interval 45
```

One-command bootstrap:

```bash
chmod +x setup_marketplace.sh
./setup_marketplace.sh
```




