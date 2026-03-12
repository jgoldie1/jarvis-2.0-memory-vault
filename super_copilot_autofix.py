#!/usr/bin/env python3
"""Super Copilot Auto-Fix

Self-healing workflow for `golden_era_marketplace`.
"""

import argparse
import importlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

PACKAGE_MAP = {
    "Pillow": "PIL",
    "Flask": "flask",
    "pyttsx3": "pyttsx3",
    "gTTS": "gtts",
    "SpeechRecognition": "speech_recognition",
    "opencv-python": "cv2",
    "requests": "requests",
}

REQUIRED_FOLDERS = [
    "golden_era_marketplace/css",
    "golden_era_marketplace/js",
    "golden_era_marketplace/images",
    "golden_era_marketplace/images_processed",
    "golden_era_marketplace/fintech",
    "golden_era_marketplace/ai/curve",
    "golden_era_marketplace/ai/stubb",
    "golden_era_marketplace/ai/lyons",
]

DEFAULT_STYLE_CSS = (
    "body{margin:0;background:black;color:white;font-family:Arial,sans-serif;}"
    "\nimg{max-width:100%;height:auto;}\n"
)

DEFAULT_APP_JS = """console.log('dashboard loaded');\n"""

DEFAULT_INDEX_HTML = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Golden Era Marketplace</title>
  <link rel=\"stylesheet\" href=\"css/style.css\" />
</head>
<body>
  <main>
    <h1>Golden Era Marketplace</h1>
    <p>Self-healed dashboard scaffold is active.</p>
    <img src=\"images_processed/saturn.jpg\" alt=\"Saturn\" />
  </main>
  <script src=\"js/app.js\"></script>
</body>
</html>
"""

DEFAULT_JSON_FILES: Dict[str, Any] = {
    "golden_era_marketplace/fintech/wallet.json": {"balance": 0},
    "golden_era_marketplace/fintech/transactions.json": {"transactions": []},
    "golden_era_marketplace/fintech/ai_status.json": {
        "curve": 0,
        "stubb": 0,
        "lyons": 0,
    },
}

DEFAULT_AI_MODULES = {
    "golden_era_marketplace/ai/curve/curve_ai.py": """def update_stats():
    return {\"curve\": 0}
""",
    "golden_era_marketplace/ai/stubb/stubb_ai.py": """def update_stats():
    return {\"stubb\": 0}
""",
    "golden_era_marketplace/ai/lyons/lyons_ai.py": """def update_stats():
    return {\"lyons\": 0}
""",
}


def ensure_folders(root: Path) -> int:
    created = 0
    for rel in REQUIRED_FOLDERS:
        target = root / rel
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created folder: {target}")
            created += 1
    return created


def ensure_text_file(
    path: Path, content: str, overwrite_invalid_placeholder: bool = True
) -> bool:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"✅ Created file: {path}")
        return True

    if overwrite_invalid_placeholder:
        current = path.read_text(encoding="utf-8", errors="ignore").strip()
        if current in {"# Placeholder", "", "# placeholder"}:
            path.write_text(content, encoding="utf-8")
            print(f"✅ Repaired placeholder file: {path}")
            return True
    return False


def ensure_json_file(path: Path, default_payload: dict) -> bool:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default_payload, indent=2), encoding="utf-8")
        print(f"✅ Created JSON: {path}")
        return True

    try:
        json.loads(path.read_text(encoding="utf-8"))
        return False
    except Exception:
        path.write_text(json.dumps(default_payload, indent=2), encoding="utf-8")
        print(f"✅ Repaired invalid JSON: {path}")
        return True


def ensure_core_files(root: Path) -> int:
    changes = 0
    changes += int(
        ensure_text_file(root / "golden_era_marketplace/index.html", DEFAULT_INDEX_HTML)
    )
    changes += int(
        ensure_text_file(
            root / "golden_era_marketplace/css/style.css", DEFAULT_STYLE_CSS
        )
    )
    changes += int(
        ensure_text_file(root / "golden_era_marketplace/js/app.js", DEFAULT_APP_JS)
    )

    for rel, payload in DEFAULT_JSON_FILES.items():
        changes += int(ensure_json_file(root / rel, payload))
    for rel, code in DEFAULT_AI_MODULES.items():
        changes += int(ensure_text_file(root / rel, code))
    return changes


def install_packages(packages: list[str]) -> None:
    for pkg in packages:
        import_name = PACKAGE_MAP.get(pkg, pkg)
        try:
            importlib.import_module(import_name)
        except Exception:
            print(f"📦 Installing missing package: {pkg}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
            print(f"✅ Installed: {pkg}")


def _replace_image_paths(content: str) -> tuple[str, int]:
    patterns = [
        r"(?P<q>['\"])images/(?P<name>[^'\"\s]+)(?P=q)",
        r"(?P<q>['\"])/images/(?P<name>[^'\"\s]+)(?P=q)",
    ]
    total = 0
    updated = content
    for pattern in patterns:
        updated, count = re.subn(
            pattern, r"\g<q>images_processed/\g<name>\g<q>", updated
        )
        total += count
    return updated, total


def repair_paths_and_warnings(root: Path) -> int:
    changed_files = 0
    market = root / "golden_era_marketplace"
    targets = [market / "index.html"]
    targets.extend((market / "js").glob("*.js"))
    targets.extend((market / "css").glob("*.css"))

    for path in targets:
        if not path.exists() or not path.is_file():
            continue
        original = path.read_text(encoding="utf-8", errors="ignore")
        updated, replacements = _replace_image_paths(original)
        file_changed = replacements > 0
        if file_changed:
            print(f"✅ Updated {replacements} image path(s) in {path}")

        if path.name == "index.html":
            warning_snippet = (
                "\n<script>\n"
                "document.querySelectorAll('img').forEach((img) => {\n"
                "  img.addEventListener('error', () => {\n"
                "    console.warn('[copilot-autofix] Missing image:', img.getAttribute('src'));\n"
                "  });\n"
                "});\n"
                "</script>\n"
            )
            if "[copilot-autofix] Missing image:" not in updated:
                if "</body>" in updated:
                    updated = updated.replace("</body>", f"{warning_snippet}</body>")
                else:
                    updated += warning_snippet
                file_changed = True
                print(f"✅ Added missing-image warning hook in {path}")

        if file_changed:
            path.write_text(updated, encoding="utf-8")
            changed_files += 1

    return changed_files


def copy_images(root: Path, source: Path) -> int:
    if not source.exists() or not source.is_dir():
        print(f"⚠️ Source images directory missing: {source}")
        return 0

    destination = root / "golden_era_marketplace/images"
    destination.mkdir(parents=True, exist_ok=True)
    copied = 0

    for item in source.iterdir():
        if not item.is_file() or item.suffix.lower() not in {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        }:
            continue
        target = destination / item.name
        if not target.exists() or item.stat().st_mtime > target.stat().st_mtime:
            target.write_bytes(item.read_bytes())
            copied += 1

    if copied > 0:
        print(f"✅ Copied {copied} image(s) into {destination}")
    return copied


def process_images(root: Path, resize: tuple[int, int] = (1024, 1024)) -> int:
    try:
        from PIL import Image
    except Exception:
        print("⚠️ Pillow is unavailable; skipping image processing.")
        return 0

    src = root / "golden_era_marketplace/images"
    dst = root / "golden_era_marketplace/images_processed"
    dst.mkdir(parents=True, exist_ok=True)
    processed = 0

    if not src.exists():
        return 0

    for file_path in src.iterdir():
        if not file_path.is_file() or file_path.suffix.lower() not in {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        }:
            continue
        out_path = dst / file_path.name
        try:
            with Image.open(file_path) as img:
                converted = img.convert("RGBA")
                converted = converted.resize(resize)
                converted.save(out_path)
            processed += 1
        except Exception as exc:
            print(f"⚠️ Failed to process {file_path.name}: {exc}")

    if processed > 0:
        print(f"✅ Processed {processed} image(s) to {dst}")
    return processed


def start_server(root: Path, port: int = 8000):
    market = root / "golden_era_marketplace"
    market.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)], cwd=str(market)
    )
    print(f"✅ Server started: http://localhost:{port} (PID {process.pid})")
    return process


def healing_cycle(root: Path, args: argparse.Namespace) -> None:
    ensure_folders(root)
    ensure_core_files(root)
    repair_paths_and_warnings(root)

    if args.install_deps:
        install_packages(args.packages)

    if args.source_images:
        copy_images(root, args.source_images)

    if args.process_images:
        process_images(root)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copilot self-healing for Golden Era Marketplace"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install missing Python dependencies",
    )
    parser.add_argument(
        "--process-images",
        action="store_true",
        help="Resize and normalize marketplace images",
    )
    parser.add_argument(
        "--start-server",
        action="store_true",
        help="Run python HTTP server after healing",
    )
    parser.add_argument("--watch", action="store_true", help="Keep healing in a loop")
    parser.add_argument(
        "--interval", type=int, default=45, help="Watch interval in seconds"
    )
    parser.add_argument(
        "--source-images", type=Path, help="Optional source image folder"
    )
    parser.add_argument(
        "--packages",
        nargs="*",
        default=list(PACKAGE_MAP.keys()),
        help="Package list to validate",
    )
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    healing_cycle(root, args)

    if args.watch:
        try:
            print(
                f"🔁 Self-healing loop active (every {args.interval}s). Ctrl-C to stop."
            )
            while True:
                time.sleep(args.interval)
                healing_cycle(root, args)
        except KeyboardInterrupt:
            print("Stopped self-healing loop.")

    server_process = None
    if args.start_server:
        server_process = start_server(root, args.port)

    if server_process:
        try:
            server_process.wait()
        except KeyboardInterrupt:
            server_process.terminate()
            print("Server stopped.")


if __name__ == "__main__":
    main()
