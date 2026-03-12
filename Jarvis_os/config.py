"""Jarvis OS configuration."""

from pathlib import Path

# Repository root
ROOT = Path(__file__).resolve().parent.parent

# Marketplace paths
MARKETPLACE_DIR = ROOT / "golden_era_marketplace"
FINTECH_DIR = MARKETPLACE_DIR / "fintech"
AI_DIR = MARKETPLACE_DIR / "ai"

# Server settings
FLASK_PORT = 5000
COPILOT_PORT = 5002
STATIC_SERVER_PORT = 8000

# Copilot settings
COPILOT_INTERVAL_SECONDS = 10
COPILOT_TTS_ENABLED = False

# AI module names
AI_MODULES = ["curve", "stubb", "lyons", "ai_tutor"]

# Fintech settings
MAX_TRANSACTIONS = 200
