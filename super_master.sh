#!/bin/bash

echo "================================="
echo "SUPER MASTER SYSTEM v2"
echo "================================="

BASE=~/mycolo
PORT=5000

mkdir -p $BASE
cd $BASE

echo "Creating folders..."
for F in backend frontend database ai scripts logs optimization rendering quantum holographic analysis; do
    mkdir -p $F
done

echo "Setting up Python environment..."
python3 -m venv venv 2>/dev/null
source venv/bin/activate
pip install flask flask-cors >/dev/null 2>&1

echo "Creating backend server..."
cat > backend/server.py << 'PYEOF'
from flask import Flask, jsonify, send_from_directory
app = Flask(__name__, static_folder="../frontend")

@app.route('/')
def home():
    return send_from_directory("../frontend", "index.html")

@app.route('/health')
def health():
    return jsonify({"status":"online"})

@app.route('/ai')
def ai():
    return jsonify({"ai":"active"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
PYEOF

echo "Creating frontend..."
cat > frontend/index.html << 'HTMLEOF'
<html>
<head><title>Lyons Tech AI</title></head>
<body>
<h1>Lyons Tech AI System</h1>
<button onclick="ai()">AI</button>
<p id="out"></p>
<script>
function ai(){
 fetch('/ai')
 .then(r=>r.json())
 .then(d=>{ document.getElementById("out").innerText = d.ai })
}
</script>
</body>
</html>
HTMLEOF

echo "Creating run script..."
cat > run.sh << 'RUNE'
#!/bin/bash
cd ~/mycolo
source venv/bin/activate
python backend/server.py
RUNE

chmod +x run.sh

echo "Stopping old servers..."
pkill -f server.py >/dev/null 2>&1

echo "Starting server..."
nohup python backend/server.py > logs/server.log 2>&1 &

sleep 3

echo "Opening port 5000 publicly..."
gh codespace ports visibility 5000:public >/dev/null 2>&1

echo ""
echo "================================="
echo "SYSTEM READY"
echo "================================="
echo "Use this link to open the website:"
echo "https://5000-$(hostname).preview.app.github.dev"
