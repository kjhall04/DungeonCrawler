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
        template_folder=os.path.join(base_dir, 'frontend/templates'),
        static_folder=os.path.join(base_dir, 'frontend/static')
    )
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

    # Register blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(game_api)

    return app