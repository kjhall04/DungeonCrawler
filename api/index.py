import os
import sys

API_DIR = os.path.abspath(os.path.dirname(__file__))

if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    debug_enabled = os.getenv("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("PORT", os.getenv("FLASK_RUN_PORT", "5000")))
    app.run(host=host, port=port, debug=debug_enabled)
