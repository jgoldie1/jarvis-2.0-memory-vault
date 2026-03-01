#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MARKET_DIR="${WORKSPACE_ROOT}/golden_era_marketplace"
JARVIS_DIR="${WORKSPACE_ROOT}/Jarvis_os"
VENV_DIR="${WORKSPACE_ROOT}/venv"
PORT="8000"

SOURCE_IMAGES=""
INSTALL_DEPS=false
PROCESS_IMAGES=false
START_SERVER=false
START_JARVIS=false

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --workspace <path>      Override workspace root (default: script directory)
  --source-images <path>  Copy images from source directory into marketplace images/
  --install-deps          Create venv and install Python dependencies
  --process-images        Resize images to 1024x1024 into images_processed/
  --start-server          Start marketplace HTTP server on --port (default 8000)
  --start-jarvis          Start Jarvis main.py in background
  --port <number>         Port for local HTTP server (default: 8000)
  --all                   Run install/process/start-server/start-jarvis
  --help                  Show this help message

Example:
  $(basename "$0") --all --source-images ~/workspaces/source_images
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      WORKSPACE_ROOT="$2"
      shift 2
      ;;
    --source-images)
      SOURCE_IMAGES="$2"
      shift 2
      ;;
    --install-deps)
      INSTALL_DEPS=true
      shift
      ;;
    --process-images)
      PROCESS_IMAGES=true
      shift
      ;;
    --start-server)
      START_SERVER=true
      shift
      ;;
    --start-jarvis)
      START_JARVIS=true
      shift
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --all)
      INSTALL_DEPS=true
      PROCESS_IMAGES=true
      START_SERVER=true
      START_JARVIS=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

MARKET_DIR="${WORKSPACE_ROOT}/golden_era_marketplace"
JARVIS_DIR="${WORKSPACE_ROOT}/Jarvis_os"
VENV_DIR="${WORKSPACE_ROOT}/venv"

echo "================================="
echo "MASTER WORKSPACE BOOTSTRAP"
echo "================================="
echo "Workspace: ${WORKSPACE_ROOT}"

mkdir -p "${WORKSPACE_ROOT}"

echo "[1/7] Creating directories..."
mkdir -p \
  "${MARKET_DIR}/images" \
  "${MARKET_DIR}/images_processed" \
  "${MARKET_DIR}/css" \
  "${MARKET_DIR}/js" \
  "${MARKET_DIR}/ai/curve" \
  "${MARKET_DIR}/ai/stubb" \
  "${MARKET_DIR}/ai/lyons" \
  "${MARKET_DIR}/fintech" \
  "${MARKET_DIR}/marketplace" \
  "${MARKET_DIR}/streaming" \
  "${MARKET_DIR}/holographic" \
  "${MARKET_DIR}/quantum" \
  "${MARKET_DIR}/engine" \
  "${MARKET_DIR}/metaverse"

mkdir -p \
  "${JARVIS_DIR}/jarvis.2.0" \
  "${JARVIS_DIR}/kimi" \
  "${JARVIS_DIR}/copilot" \
  "${JARVIS_DIR}/conversation" \
  "${JARVIS_DIR}/audio" \
  "${JARVIS_DIR}/vision" \
  "${JARVIS_DIR}/pip_hologram"

echo "[2/7] Creating placeholder files..."
touch "${JARVIS_DIR}/main.py"
touch "${JARVIS_DIR}/config.py"
touch "${MARKET_DIR}/css/style.css"
touch "${MARKET_DIR}/js/app.js"

if [[ ! -f "${MARKET_DIR}/index.html" ]]; then
  cat > "${MARKET_DIR}/index.html" <<'EOF'
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Golden Era Marketplace</title>
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <h1>Golden Era Marketplace</h1>
  <p>Workspace bootstrap completed.</p>
  <script src="js/app.js"></script>
</body>
</html>
EOF
fi

if [[ ! -s "${JARVIS_DIR}/main.py" ]]; then
  cat > "${JARVIS_DIR}/main.py" <<'EOF'
from pathlib import Path

if __name__ == "__main__":
    workspace = Path(__file__).resolve().parents[1]
    print(f"Jarvis OS running from: {workspace}")
EOF
fi

echo "[3/7] Creating fintech JSON placeholders..."
echo '{}' > "${MARKET_DIR}/fintech/users.json"
echo '{}' > "${MARKET_DIR}/fintech/transactions.json"
echo '{}' > "${MARKET_DIR}/fintech/passport.json"
echo '{}' > "${MARKET_DIR}/fintech/nfts.json"
echo '{}' > "${MARKET_DIR}/fintech/ai_stats.json"

echo "[4/7] Copying images (if source provided)..."
if [[ -n "${SOURCE_IMAGES}" ]]; then
  if [[ -d "${SOURCE_IMAGES}" ]]; then
    shopt -s nullglob
    files=("${SOURCE_IMAGES}"/*)
    if [[ ${#files[@]} -gt 0 ]]; then
      cp -f "${SOURCE_IMAGES}"/* "${MARKET_DIR}/images/"
      echo "Copied ${#files[@]} file(s) from ${SOURCE_IMAGES}"
    else
      echo "No files found in ${SOURCE_IMAGES}; skipping copy."
    fi
    shopt -u nullglob
  else
    echo "Source image directory not found: ${SOURCE_IMAGES}"
    exit 1
  fi
else
  echo "No source image directory provided; skipping copy."
fi

if [[ "${INSTALL_DEPS}" == true ]]; then
  echo "[5/7] Creating venv and installing dependencies..."
  python3 -m venv "${VENV_DIR}"
  source "${VENV_DIR}/bin/activate"
  python -m pip install --upgrade pip
  python -m pip install Pillow Flask pyttsx3 gTTS SpeechRecognition opencv-python requests
else
  echo "[5/7] Dependency install skipped (use --install-deps or --all)."
fi

if [[ "${PROCESS_IMAGES}" == true ]]; then
  echo "[6/7] Processing images..."
  if [[ -d "${MARKET_DIR}/images" ]]; then
    if [[ "${INSTALL_DEPS}" == true ]]; then
      source "${VENV_DIR}/bin/activate"
    fi
    python3 - <<PY
from PIL import Image
import os

src = os.path.expanduser("${MARKET_DIR}/images")
dst = os.path.expanduser("${MARKET_DIR}/images_processed")
os.makedirs(dst, exist_ok=True)

processed = 0
for name in os.listdir(src):
    if name.lower().endswith((".png", ".jpg", ".jpeg")):
        path = os.path.join(src, name)
        out = os.path.join(dst, name)
        img = Image.open(path).convert("RGBA")
        img = img.resize((1024, 1024))
        img.save(out)
        processed += 1
        print(f"Processed: {name}")

print(f"Total processed: {processed}")
PY
  fi
else
  echo "[6/7] Image processing skipped (use --process-images or --all)."
fi

echo "[7/7] Starting services (optional)..."
if [[ "${START_SERVER}" == true ]]; then
  mkdir -p "${WORKSPACE_ROOT}/logs"
  pkill -f "python3 -m http.server ${PORT}" >/dev/null 2>&1 || true
  nohup python3 -m http.server "${PORT}" --directory "${MARKET_DIR}" > "${WORKSPACE_ROOT}/logs/marketplace_server.log" 2>&1 &
  echo "Marketplace server started on http://localhost:${PORT}"
else
  echo "Marketplace server start skipped (use --start-server or --all)."
fi

if [[ "${START_JARVIS}" == true ]]; then
  mkdir -p "${WORKSPACE_ROOT}/logs"
  pkill -f "python3 ${JARVIS_DIR}/main.py" >/dev/null 2>&1 || true
  nohup python3 "${JARVIS_DIR}/main.py" > "${WORKSPACE_ROOT}/logs/jarvis.log" 2>&1 &
  echo "Jarvis started in background."
else
  echo "Jarvis start skipped (use --start-jarvis or --all)."
fi

echo ""
echo "Bootstrap complete."
echo "Marketplace path: ${MARKET_DIR}"
echo "Jarvis path: ${JARVIS_DIR}"
echo ""
echo "Quick start:"
echo "  $(basename "$0") --all --source-images ~/workspaces/source_images"
