from flask import Flask
from backend.app.routes import auth_routes
from backend.app.game_api import game_api
from dotenv import load_dotenv
import os

def create_app():
    """Create and configure the flask app."""
    load_dotenv()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'public'),
        static_url_path="/"
    )
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

    # Secure session settings
    app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Prevent CSRF in cross-site contexts

    # Register blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(game_api)

    return app