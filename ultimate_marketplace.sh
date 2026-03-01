#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-run}"

cd "$ROOT_DIR"

if [[ ! -x "$ROOT_DIR/ultimate_dashboard.sh" ]]; then
  chmod +x "$ROOT_DIR/ultimate_dashboard.sh"
fi

exec "$ROOT_DIR/ultimate_dashboard.sh" "$MODE"
