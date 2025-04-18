from flask import Blueprint, request, session, redirect, render_template, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from backend.app.auth import create_account, login
from backend.app.db import supabase
import json

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
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Check for empty fields
        if not username or not password:
            return render_template('login.html', error='Both username and password are required', 
                                   username=username)

        result = login(username, password)
        if 'error' in result:
            return render_template('login.html', error=result['error'], 
                                   username=username)
        
        # Store the username in the session
        session['username'] = username
        return redirect(url_for('auth.title_animation'))
    
    return render_template('login.html')

@auth_routes.route('/create_account', methods=['GET', 'POST'])
def create_account_route():
    """Handle account creation."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Check for empty fields
        if not username or not email or not password or not confirm_password:
            return render_template('create_account.html', error='All fields are required', 
                                   username=username, email=email)

        result = create_account(username, email, password, confirm_password)
        if 'error' in result:
            return render_template('create_account.html', error=result['error'], 
                                   username=username, email=email)
        
        return redirect(url_for('auth.login_route'))
    
    return render_template('create_account.html')

@auth_routes.route('/logout', methods=['GET'])
def logout_route():
    """Log out the current user."""
    session.pop('username', None)
    return redirect(url_for('auth.login_route'))

@auth_routes.route('/title_animation', methods=['GET'])
def title_animation():
    """Display the title animation page."""
    return render_template('title_animation.html')

@auth_routes.route('/select_save', methods=['GET', 'POST'])
def select_save():
    """Handle save slot selection."""
    username = session.get('username')

    if not username:
        return redirect(url_for('auth.login_route'))

    if request.method == 'POST':
        # Get the selected save slot
        save_slot = request.form.get('save_slot')

        # Redirect to the game with the selected save slot
        return redirect(url_for('game_api.load_save', save_slot=save_slot))

    # Fetch save slots for the user
    save_slots = get_save_slots(username)

    if len(save_slots) < 3:
        for slot in range(1, 4):
            if not any(s['slot'] == slot for s in save_slots):
                save_slots.append({'slot': slot, 'used': False})

    save_slots = sorted(save_slots, key=lambda x: x['slot'])
    
    return render_template('select_save.html', save_slots=save_slots)


def get_save_slots(username):
    """Fetch save slots for the user."""
    response = supabase.table('player_saves').select('*').eq('username', username).execute()

    if not response.data:
        response.data = []

    used_slots = {int(save['save_slot']): save for save in response.data}
    save_slots = []

    for slot in used_slots:
        if slot in used_slots:
            save_slots.append({
                'slot': slot,
                'used': True,
                'name': used_slots[slot]['name'],
                'class': used_slots[slot]['player_class'],
                'floor': used_slots[slot]['dungeon_floor']
            })
        else:
            save_slots.append({'slot': slot, 'used': False})

    return save_slots