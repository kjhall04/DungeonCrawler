import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

BASE_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = BASE_DIR / ".env"


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def create_app():
    """Create and configure the flask app."""
    load_dotenv(ENV_FILE)
    from backend.app.game_api import game_api
    from backend.app.routes import auth_routes, limiter

    debug_enabled = _env_flag("FLASK_DEBUG")
    is_production = os.getenv("VERCEL_ENV") == "production" or os.getenv("FLASK_ENV") == "production"

    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "public"),
        static_url_path="/"
    )
    app.config.update(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev-secret-key"),
        SESSION_COOKIE_SECURE=is_production,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        TEMPLATES_AUTO_RELOAD=debug_enabled,
    )
    app.debug = debug_enabled

    app.register_blueprint(auth_routes)
    app.register_blueprint(game_api)
    limiter.init_app(app)

    return app
