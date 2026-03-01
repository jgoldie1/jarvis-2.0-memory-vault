#!/bin/bash

echo "Starting Jarvis Ultimate Flask Setup..."

# Create folders
mkdir -p ~/jarvis_project/quantum
mkdir -p ~/jarvis_project/static/css
mkdir -p ~/jarvis_project/static/js
mkdir -p ~/jarvis_project/templates

cd ~/jarvis_project || exit

# 1️⃣ Quantum Renderer
cat << 'PY' > quantum/renderer.py
class QuantumRenderer:
    def start(self):
        return "Quantum Renderer Running"
PY

# 2️⃣ Quantum Hologram
cat << 'PY' > quantum/hologram.py
class QuantumHologram:
    def start(self):
        return "Holographic Generator Running"
PY

# 3️⃣ CSS
cat << 'CSS' > static/css/style.css
body { background:black; color:cyan; text-align:center; font-family:Arial; }
h1 { font-size:40px; margin-top:50px; }
CSS

# 4️⃣ JS
cat << 'JS' > static/js/app.js
function updateStatus(){
    document.getElementById("status").innerHTML = "Quantum Systems Running";
}
setInterval(updateStatus, 2000);
JS

# 5️⃣ HTML template
cat << 'HTML' > templates/index.html
<!DOCTYPE html>
<html>
<head>
<title>Jarvis Quantum System</title>
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
<h1>Jarvis Quantum System</h1>
<p id="status">Starting...</p>
<script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>
</html>
HTML

# 6️⃣ Flask server
cat << 'PY' > app.py
from flask import Flask, render_template
from quantum.renderer import QuantumRenderer
from quantum.hologram import QuantumHologram

app = Flask(__name__)

renderer = QuantumRenderer()
hologram = QuantumHologram()

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    print(renderer.start())
    print(hologram.start())
    print("Server running on port 5000")
    app.run(host="0.0.0.0", port=5000)
PY

# 7️⃣ Install Flask
python3 -m pip install --upgrade pip
python3 -m pip install flask

echo "✅ Flask Jarvis Setup Complete!"
echo "Run: python3 app.py"
