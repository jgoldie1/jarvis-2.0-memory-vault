"""Jarvis OS – entry point.

Bootstraps the Golden Era Marketplace system:
  1. Validates the marketplace directory structure (self-heal).
  2. Launches the UltimateCopilot background agent.
  3. Starts the Flask dashboard backend.
"""

import sys
from pathlib import Path

# Ensure the repository root is on the path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Jarvis_os.config import (  # noqa: E402
    COPILOT_INTERVAL_SECONDS,
    COPILOT_TTS_ENABLED,
    FLASK_PORT,
)


def main() -> None:
    """Start the Jarvis OS stack."""
    print("🚀 Jarvis OS starting …")

    # 1. Self-heal the marketplace directory structure
    try:
        import super_copilot_autofix as healer

        healer.ensure_folders(ROOT)
        healer.ensure_core_files(ROOT)
        healer.repair_paths_and_warnings(ROOT)
        print("✅ Marketplace structure validated.")
    except Exception as exc:  # pragma: no cover
        print(f"⚠️  Self-heal step failed: {exc}")

    # 2. Start the background copilot agent
    try:
        from ultimate_copilot import UltimateCopilot

        copilot = UltimateCopilot(
            interval=COPILOT_INTERVAL_SECONDS,
            tts=COPILOT_TTS_ENABLED,
        )
        copilot.start()
        print(f"✅ UltimateCopilot running (interval={COPILOT_INTERVAL_SECONDS}s).")
    except Exception as exc:  # pragma: no cover
        print(f"⚠️  Copilot start failed: {exc}")

    # 3. Start the Flask backend
    try:
        import golden_era_marketplace.dashboard_backend as backend

        print(f"✅ Dashboard backend launching on port {FLASK_PORT} …")
        backend.app.run(host="0.0.0.0", port=FLASK_PORT)
    except Exception as exc:  # pragma: no cover
        print(f"⚠️  Dashboard backend failed to start: {exc}")


if __name__ == "__main__":
    main()
