from flask import Blueprint, request, session, redirect, render_template, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from backend.app.auth import create_account, login
from backend.app.db import supabase
from backend.game.player import Player
from backend.game.dungeon import Dungeon
from backend.game.enemy import Enemy
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
            return render_template('login.html', error='Both user_id and password are required', 
                                   username=username)

        result = login(username, password)
        if 'error' in result:
            return render_template('login.html', error=result['error'], 
                                   username=username)
        
        # Store the user_id in the session
        session['user_id'] = result['user_id']
        return redirect(url_for('auth.title_animation'))
    
    return render_template('login.html')

@auth_routes.route('/create_account', methods=['GET', 'POST'])
def create_account_route():
    """Handle account creation."""
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Check for empty fields
        if not user_id or not email or not password or not confirm_password:
            return render_template('create_account.html', error='All fields are required', 
                                   user_id=user_id, email=email)

        result = create_account(user_id, email, password, confirm_password)
        if 'error' in result:
            return render_template('create_account.html', error=result['error'], 
                                   user_id=user_id, email=email)
        
        return redirect(url_for('auth.login_route'))
    
    return render_template('create_account.html')

@auth_routes.route('/logout', methods=['GET'])
def logout_route():
    """Log out the current user."""
    session.pop('user_id', None)
    return redirect(url_for('auth.login_route'))

@auth_routes.route('/title_animation', methods=['GET'])
def title_animation():
    """Display the title animation page."""
    return render_template('title_animation.html')

@auth_routes.route('/select_save', methods=['GET', 'POST'])
def select_save():
    """Handle save slot selection."""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login_route'))

    if request.method == 'POST':
        # Get the selected save slot
        save_slot = int(request.form.get('save_slot'))
        session['save_slot'] = save_slot

        # Redirect to the game with the selected save slot
        return redirect(url_for('game_api.load_save', save_slot=save_slot))

    # Fetch save slots for the user
    save_slots = get_save_slots(user_id)

    if len(save_slots) < 3:
        for slot in range(1, 4):
            if not any(s['slot'] == slot for s in save_slots):
                save_slots.append({'slot': slot, 'used': False})

    save_slots = sorted(save_slots, key=lambda x: x['slot'])
    
    return render_template('select_save.html', save_slots=save_slots)


def get_save_slots(user_id):
    """Fetch save slots for the user."""
    response = supabase.table('player_saves').select('*').eq('user_id', user_id).execute()

    if not response.data:
        response.data = []

    used_slots = {int(save['save_slot']): save for save in response.data}
    save_slots = []

    for slot in range(1, 4):
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

@auth_routes.route('/save_game', methods=['POST'])
def save_game():
    """Save the current game state."""
    user_id = session.get('user_id')
    save_slot = session.get('save_slot')
    if not user_id or save_slot is None:
        return redirect(url_for('auth.login_route'))
    
@auth_routes.route('/create_character', methods=['GET', 'POST'])
def create_character():
    """Handle player creation with a story sequence."""
    user_id = session.get('user_id')
    save_slot = session.get('save_slot')
    if not user_id or save_slot is None:
        return redirect(url_for('auth.select_save'))
    
    # Load the story sequence from descriptions.json
    with open('api/backend/data/descriptions.json', 'r') as file:
        descriptions = json.load(file)

    story = descriptions.get('player_creation', {})
    
    name_step = 4
    class_step = 6
    final_step = 7
    step = int(request.args.get('step', 1))

    if request.method == 'POST':
        # Name step
        if step == name_step:
            name = request.form.get('name', '').strip()
            if not name:
                error = 'Please enter a name'
                return render_template('create_character.html', story=story, step=step, error=error, show_name_input=True)
            
            session['player_name'] = name
            return redirect(url_for('auth.create_character', step=step+1))
        
        # Class step
        elif step == class_step:
            player_class = request.form.get('class', '').strip()
            if not player_class:
                error = 'Please select a class.'
                return render_template('create_character.html', story=story, step=step, error=error, show_class_choice=True)

            session['player_class'] = player_class
            return redirect(url_for('auth.create_character', step=step+1))
        
        # Final step: create the player
        elif step == final_step:
            name = session.get('player_name')
            player_class = session.get('player_class')

            if not name or not player_class:
                return redirect(url_for('auth.create_character', step=1)) # Reset if wrong or no info
            
            player = Player(name=name, player_class=player_class, save_slot=save_slot,)
            player.save_player_data(user_id)

            return redirect(url_for('game_api.load_save', save_slot=save_slot))

        # All other steps, just proceed
        return redirect(url_for('auth.create_character', step=step+1))
    
    # Determince dynamic behavior for the next step
    show_name_input = (step == name_step)
    show_class_choice = (step == class_step)
    player_name = session.get('player_name', '')

    return render_template(
        'create_character.html',
        story=story,
        step=step,
        show_name_input=show_name_input,
        show_class_choice=show_class_choice,
        player_name=player_name
    )

@auth_routes.route('/game_action', methods=['POST'])
def game_action():
    """Handle player actions in the game."""
    user_id = session.get('user_id')
    save_slot = session.get('save_slot')
    if not user_id or save_slot is None:
        return redirect(url_for('auth.login_route'))
    
    player = Player.load_or_create_player(user_id, save_slot)
    dungeon = Dungeon.load_from_db(player_save_id=save_slot)

    # Get the player's action
    action = request.form.get('action')

    # Initialize game state
    game_state = {
        'narrative': dungeon.get_room_description(player, "descriptions"),
        'interaction': None,
        'actions': [
            {'label': 'Move North', 'value': 'move_north'},
            {'label': 'Move East', 'value': 'move_east'},
            {'label': 'Move South', 'value': 'move_south'},
            {'label': 'Move West', 'value': 'move_west'},
        ]
    }

    # Handle player actions
    if action.startswith('move_'):
        direction = action.split('_')[1]
        if player.move(direction, dungeon):
            game_state['narrative'] = dungeon.get_room_description(player, "descriptions")
        else:
            game_state['narrative'] = "You can't move in that direction."

    elif action == 'attack':
        enemy = Enemy.create_enemy("goblin", dungeon)
        attack_result = player.attack_enemy(enemy, skill_name="slash")
        game_state['narrative'] = attack_result

    elif action == 'heal':
        if player.heal():
            game_state['narrative'] = "You used a health potion and restored some health."
        else:
            game_state['narrative'] = "You don't have any health potions left."

    elif action == 'inventory':
        return redirect(url_for('auth.inventory'))

    # Save the updated player and dungeon state
    player.save_player_data(user_id)
    dungeon.save_to_db(player_save_id=player.dungeon_floor)

    # Render the game page with the updated state
    return render_template(
        'game.html',
        narrative=game_state['narrative'],
        interaction=game_state['interaction'],
        actions=game_state['actions']
    )