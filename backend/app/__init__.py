from flask import Flask
from backend.app.routes import auth_routes
from backend.app.game_api import game_api
from dotenv import load_dotenv
import os

def create_app():
    """Create and configure the flask app."""
    load_dotenv()
    app = Flask(__name__, template_folder='../../frontend/templates', static_folder='../../frontend/static')
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

    # Register blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(game_api)

    return app