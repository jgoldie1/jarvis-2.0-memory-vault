





#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

cd "$ROOT_DIR"

MODE="${1:-run}"

case "$MODE" in
  heal)
    echo "🔧 Running Copilot self-heal pass..."
    "$PYTHON_BIN" super_copilot_autofix.py --install-deps --process-images
    ;;
  watch)
    echo "🔁 Running Copilot self-heal loop..."
    "$PYTHON_BIN" super_copilot_autofix.py --install-deps --process-images --watch --interval 45
    ;;
  run)
    echo "🚀 Healing marketplace and starting dashboard server..."
    "$PYTHON_BIN" super_copilot_autofix.py --install-deps --process-images
    "$PYTHON_BIN" super_copilot_autofix.py --start-server --port 8000
    ;;
  *)
    echo "Usage: $0 [run|heal|watch]"
    exit 1
    ;;
esac
