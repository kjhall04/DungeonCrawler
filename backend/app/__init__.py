from flask import Flask
from backend.app.routes import auth_routes
from dotenv import load_dotenv
import os

def create_app():
    """Create and configure the flask app."""
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

    # Register blueprints
    app.register_blueprint(auth_routes)

    return app