from flask import Blueprint, request, jsonify, session, redirect, render_template, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from backend.app.auth import create_account, login

auth_routes = Blueprint('auth', __name__)
limiter = Limiter(get_remote_address)

@auth_routes.route('/')
def index():
    """Redirect to the login page."""
    return redirect(url_for('auth.login_route'))

@auth_routes.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login_route():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        result = login(username, password)
        if 'error' in result:
            return render_template('login.html', error=result['error'])
        
        # Store the username in the session
        session['username'] = username
        return redirect(url_for('game_api.get_player_stats'))
    
    return render_template('login.html')

@auth_routes.route('/create_account', methods=['GET', 'POST'])
def create_account_route():
    """Handle account creation."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        result = create_account(username, email, password, confirm_password)
        if 'error' in result:
            return render_template('create_account.html', error=result['error'])
        
        return redirect(url_for('auth.login_route'))
    
    return render_template('create_account.html')

@auth_routes.route('/logout', methods=['GET'])
def logout_route():
    """Log out the current user."""
    session.pop('username', None)
    return redirect(url_for('auth.login_route'))