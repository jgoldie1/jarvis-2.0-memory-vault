from pathlib import Path
from core.crypto_utils import generate_keys

wallet_dir = Path("wallets")
wallet_dir.mkdir(parents=True, exist_ok=True)

names = ["alice", "bob", "carol", "miner"]

for name in names:
    private_pem, public_pem = generate_keys()
    private_path = wallet_dir / f"{name}_private.pem"
    private_path.write_text(private_pem, encoding="utf-8")
    private_path.chmod(0o600)
    (wallet_dir / f"{name}_public.pem").write_text(public_pem, encoding="utf-8")
    print(f"saved {name} wallet")
