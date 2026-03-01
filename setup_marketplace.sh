#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$ROOT_DIR"

python3 super_copilot_autofix.py --install-deps --process-images
python3 super_copilot_autofix.py --start-server --port 8000