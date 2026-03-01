#!/usr/bin/env bash
set -euo pipefail

# Ultimate Marketplace Full Setup
# Adds self-healing scaffolding, image processing, AI placeholders,
# Three.js preview scaffold, logging, and optional watch loop.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="$ROOT_DIR/self_heal.log"

usage(){
  cat <<EOF
Usage: $0 [--install-deps] [--process-images] [--watch] [--interval N] [--port P] [--source-images DIR]

Options:
  --install-deps     Install Python dependencies needed (Pillow/Flask/etc.)
  --process-images   Resize/normalize images into golden_era_marketplace/images_processed
  --watch            Run continuous self-healing loop (safe mode)
  --interval N       Watch interval seconds (default 45)
  --port P           HTTP preview port (default 8000)
  --source-images D  Directory with source images to copy from
EOF
}

INSTALL_DEPS=false
PROCESS_IMAGES=false
WATCH=false
INTERVAL=45
PORT=8000
SOURCE_IMAGES=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-deps) INSTALL_DEPS=true; shift ;;
    --process-images) PROCESS_IMAGES=true; shift ;;
    --watch) WATCH=true; shift ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --source-images) SOURCE_IMAGES="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

log(){
  printf "%s %s\n" "$(date --iso-8601=seconds)" "$*" | tee -a "$LOGFILE"
}

ensure_folders(){
  folders=(
    "golden_era_marketplace"
    "golden_era_marketplace/images"
    "golden_era_marketplace/images_processed"
    "golden_era_marketplace/css"
    "golden_era_marketplace/js"
    "golden_era_marketplace/fintech"
    "golden_era_marketplace/ai/curve"
    "golden_era_marketplace/ai/stubb"
    "golden_era_marketplace/ai/lyons"
  )
  for f in "${folders[@]}"; do
    if [[ ! -d "$ROOT_DIR/$f" ]]; then
      mkdir -p "$ROOT_DIR/$f"
      log "Created folder: $f"
    fi
  done
}

ensure_files(){
  # index with Three.js scaffold and image warning hook
  IDX="$ROOT_DIR/golden_era_marketplace/index.html"
  if [[ ! -f "$IDX" ]]; then
    cat > "$IDX" <<'HTML'
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Golden Era Marketplace — Preview</title>
  <link rel="stylesheet" href="css/style.css" />
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r152/three.min.js"></script>
</head>
<body>
  <main>
    <h1>All-American Holographic Marketplace</h1>
    <div id="preview">
      <canvas id="three-canvas" style="width:100%;height:400px;display:block;background:#000"></canvas>
    </div>
    <p>AI stats: <span id="ai-stats">loading...</span></p>
    <img src="images_processed/saturn.jpg" alt="Saturn" />
  </main>
  <script src="js/app.js"></script>
  <script>
    // Minimal three.js placeholder scene
    try {
      const canvas = document.getElementById('three-canvas');
      const renderer = new THREE.WebGLRenderer({canvas});
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth/canvas.clientHeight, 0.1, 1000);
      camera.position.z = 2;
      const geometry = new THREE.BoxGeometry(1,1,1);
      const material = new THREE.MeshNormalMaterial();
      const cube = new THREE.Mesh(geometry, material);
      scene.add(cube);
      function animate(){
        requestAnimationFrame(animate);
        cube.rotation.x += 0.01; cube.rotation.y += 0.01;
        renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
        renderer.render(scene, camera);
      }
      animate();
    } catch(e) { console.warn('three.js not available', e); }
  </script>
</body>
</html>
HTML
    log "Created file: golden_era_marketplace/index.html"
  fi

  CSS="$ROOT_DIR/golden_era_marketplace/css/style.css"
  if [[ ! -f "$CSS" ]]; then
    cat > "$CSS" <<'CSS'
body{margin:0;background:black;color:white;font-family:Arial,sans-serif}
img{max-width:100%;height:auto}
CSS
    log "Created file: golden_era_marketplace/css/style.css"
  fi

  JS="$ROOT_DIR/golden_era_marketplace/js/app.js"
  if [[ ! -f "$JS" ]]; then
    cat > "$JS" <<'JS'
console.log('Marketplace preview loaded');
// Pull simple AI stats from JSON (if available)
fetch('/fintech/ai_stats.json').then(r=>r.json()).then(j=>{
  document.getElementById('ai-stats').innerText = JSON.stringify(j);
}).catch(()=>{});
JS
    log "Created file: golden_era_marketplace/js/app.js"
  fi

  # fintech defaults
  for f in wallet.json transactions.json ai_stats.json; do
    dest="$ROOT_DIR/golden_era_marketplace/fintech/$f"
    if [[ ! -f "$dest" ]]; then
      case "$f" in
        wallet.json) echo '{"balance":0}' > "$dest" ;;
        transactions.json) echo '{"transactions":[]}' > "$dest" ;;
        ai_stats.json) echo '{"curve":0,"stubb":0,"lyons":0}' > "$dest" ;;
      esac
      log "Created fintech file: $f"
    fi
  done

  # AI placeholder modules
  for ai in curve stubb lyons; do
    mod="$ROOT_DIR/golden_era_marketplace/ai/$ai/${ai}_ai.py"
    if [[ ! -f "$mod" ]]; then
      cat > "$mod" <<PY
def update_stats():
    return {"$ai": 0}
PY
      log "Created AI module: $mod"
    fi
  done
}

process_images(){
  # Uses Pillow via python to resize into images_processed
  python3 - <<PY || { log "Image processing failed"; return 1; }
from pathlib import Path
from PIL import Image
root=Path('$ROOT_DIR')/ 'golden_era_marketplace'
src = Path('$SOURCE_IMAGES') if '$SOURCE_IMAGES' != '' else root / 'images'
dst = root / 'images_processed'
dst.mkdir(parents=True, exist_ok=True)
if not src.exists():
    print('no-src')
    raise SystemExit
count=0
for p in src.iterdir():
    if not p.is_file():
        continue
    if p.suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):
        continue
    out=dst/p.name
    try:
        with Image.open(p) as im:
            im=im.convert('RGB')
            im.thumbnail((1024,1024))
            im.save(out, optimize=True, quality=85)
        count+=1
    except Exception as e:
        print('failed', p, e)
print('processed', count)
PY
  if [[ $? -eq 0 ]]; then
    log "Processed images into golden_era_marketplace/images_processed"
  else
    log "process_images: python script returned non-zero"
  fi
}

install_deps(){
  log "Installing Python dependencies (may take a while)..."
  pkgs=(Pillow Flask pyttsx3 gTTS SpeechRecognition opencv-python requests)
  for p in "${pkgs[@]}"; do
    if ! python3 -c "import importlib; importlib.import_module('$p')" 2>/dev/null; then
      python3 -m pip install --upgrade "$p" || log "Failed to pip install $p"
    else
      log "Dependency present: $p"
    fi
  done
}

start_server(){
  cd "$ROOT_DIR/golden_era_marketplace"
  # run simple http server in background
  nohup python3 -m http.server "$PORT" >/dev/null 2>&1 &
  log "Started HTTP server on port $PORT"
}

heal_cycle(){
  log "Starting healing cycle"
  ensure_folders
  ensure_files
  if [[ "$INSTALL_DEPS" == true ]]; then
    install_deps
  fi
  if [[ "$PROCESS_IMAGES" == true ]]; then
    process_images || true
  fi
  log "Healing cycle complete"
}

# Run one cycle, or loop when --watch
heal_cycle

if [[ "$WATCH" == true ]]; then
  log "Entering watch loop (interval=$INTERVAL seconds). Ctrl-C to stop."
  while true; do
    sleep "$INTERVAL"
    heal_cycle
  done
fi

start_server

log "Setup script finished — preview: http://localhost:$PORT"

exit 0
