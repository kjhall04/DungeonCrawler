from flask import Flask
from backend.app.routes import auth_routes

def create_app():
    """Create and configure the flask app."""
    app = Flask(__name__)
    app.secret_key = 'Sp@c3_M@r1n3'

    # Register blueprints
    app.register_blueprint(auth_routes)

    return app