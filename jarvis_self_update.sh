#!/bin/bash
echo "🌀 Starting Self-Updating Quantum Jarvis..."

BASE="$HOME/jarvis_project"
mkdir -p "$BASE/quantum" "$BASE/static/css" "$BASE/static/js" "$BASE/templates"
cd "$BASE" || { echo "Cannot cd into $BASE"; exit 1; }

# -------------------------------
# Function: create/update module if missing
# -------------------------------
create_module() {
    local file="$1"
    local content="$2"
    echo "$content" > "$file"
    echo "✅ Updated $file"
}

# -------------------------------
# Quantum Modules
# -------------------------------
create_module "quantum/renderer.py" "class QuantumRenderer:\n    def start(self):\n        return 'Quantum Renderer Running'"
create_module "quantum/hologram.py" "class QuantumHologram:\n    def start(self):\n        return 'Holographic Generator Running'"
create_module "quantum/lab_buster.py" "class QuantumLabBuster:\n    def check(self):\n        return 'Quantum Lab Buster Self-Correction Active'"
create_module "quantum/speed_engine.py" "class QuantumSpeedEngine:\n    def optimize(self):\n        return 'Quantum SpeedEngine Optimizing Performance'"

# -------------------------------
# Dynamic CSS & JS
# -------------------------------
create_module "static/css/style.css" "body { background:black; color:cyan; text-align:center; font-family:Arial; } h1 { font-size:40px; margin-top:50px; } p#status { font-size:20px; }"
create_module "static/js/app.js" "function updateStatus(){ document.getElementById('status').innerHTML='Quantum Systems Running: '+ new Date().toLocaleTimeString();} setInterval(updateStatus,1000);"

# -------------------------------
# Dynamic HTML
# -------------------------------
create_module "templates/index.html" "<!DOCTYPE html><html><head><title>Jarvis Quantum System</title><link rel='stylesheet' href='{{ url_for('static', filename='css/style.css') }}'></head><body><h1>Jarvis Quantum System</h1><p id='status'>Starting...</p><script src='{{ url_for('static', filename='js/app.js') }}'></script></body></html>"

# -------------------------------
# Flask App with self-check & API key
# -------------------------------
create_module "app.py" "from flask import Flask, render_template
from quantum.renderer import QuantumRenderer
from quantum.hologram import QuantumHologram
from quantum.lab_buster import QuantumLabBuster
from quantum.speed_engine import QuantumSpeedEngine
import os

app = Flask(__name__)
renderer = QuantumRenderer()
hologram = QuantumHologram()
lab_buster = QuantumLabBuster()
speed_engine = QuantumSpeedEngine()

API_KEY_FILE = os.path.expanduser('~/jarvis_project/writekey.txt')
API_KEY = ''
if os.path.exists(API_KEY_FILE):
    with open(API_KEY_FILE,'r') as f:
        API_KEY = f.read().strip()

@app.route('/')
def index():
    return render_template('index.html')

if __name__=='__main__':
    print(renderer.start())
    print(hologram.start())
    print(lab_buster.check())
    print(speed_engine.optimize())
    print(f'Using API Key: {API_KEY[:6]}... (hidden)')
    print('Server running on port 5000')
    app.run(host='0.0.0.0', port=5000)
"

# -------------------------------
# Install Flask
# -------------------------------
python3 -m pip install --upgrade pip
python3 -m pip install flask

# -------------------------------
# Codespaces live URL
# -------------------------------
CODESPACE="${CODESPACE_NAME:-jarvis-project}"
URL="https://${CODESPACE}-5000.app.github.dev"
echo "✅ Self-Updating Jarvis Quantum setup complete!"
echo "🌐 Your live site URL:"
echo "$URL"

# -------------------------------
# Auto-restart Flask server if crashed
# -------------------------------
while true; do
    python3 app.py
    echo "⚠️ Server crashed. Restarting in 3s..."
    sleep 3
done
