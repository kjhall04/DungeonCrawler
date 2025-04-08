from flask import Blueprint, request, jsonify, session, redirect, render_template, url_for
from backend.app.auth import create_account, login

auth_routes = Blueprint('auth', __name__)

@auth_routes.route('/login', methods=['GET', 'POST'])
def login_route():
    """Handle user login."""
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password= data.get('password')

        result = login(username, password)
        if 'error' in result:
            return jsonify(result), 400
        
        # Store the username in the session
        session['username'] = username
        return jsonify(result)
    
    return render_template('login.html')

@auth_routes.route('/create_account', methods=['POST', 'GET'])
def create_account_route():
    """Handle account creation."""
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        result = create_account(username, password)
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
    
    return render_template('create_account.html')

@auth_routes.route('/logout', methods=['GET'])
def logout_route():
    """Log out the current user."""
    session.pop('username', None)
    return redirect(url_for('auth.login_route'))