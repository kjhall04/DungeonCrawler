import json
from pathlib import Path

from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from backend.app.auth import create_account, login
from backend.app.db import supabase
from backend.app.game_action import (
    build_enemy_for_room,
    get_movement_actions,
    get_skill_actions,
    handle_combat_action,
    handle_descend_action,
    handle_heal_action,
    handle_move_action,
    persist_game_state,
    render_game,
)
from backend.game.dungeon import Dungeon
from backend.game.player import Player

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DESCRIPTIONS_FILE = DATA_DIR / "descriptions.json"

auth_routes = Blueprint('auth', __name__)
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

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
        
        # Store the user_id in the session
        session['user_id'] = result['user_id']
        return redirect(url_for('auth.title_animation'))
    
    return render_template('login.html')

@auth_routes.route('/logout', methods=['GET'])
def logout_route():
    """Log out the current user."""
    session.pop('user_id', None)
    return redirect(url_for('auth.login_route'))

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
        save_slot = int(request.form.get('save_slot'))
        action = request.form.get('action')

        if action == 'delete':
            # Delete the selected save slot
            supabase.table('player_saves').delete().eq('user_id', user_id).eq('save_slot', save_slot).execute()
            return redirect(url_for('auth.select_save'))

        if action == 'select':
            # Handle save slot selection
            session['save_slot'] = save_slot

            # Redirect to the character creation route for new saves
            response = supabase.table('player_saves').select('*').eq('user_id', user_id).eq('save_slot', save_slot).execute()

            if not response or not response.data or len(response.data) == 0:
                return redirect(url_for('auth.create_character', step=1))

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
    
    # Load the player and dungeon
    player = Player.load_or_create_player(user_id, save_slot)
    dungeon = Dungeon.load_from_db(user_id=user_id, save_slot=save_slot)

    if not player or  not dungeon:
        return redirect(url_for('auth.select_save'))
    
    if not persist_game_state(player, dungeon, user_id, save_slot):
        return redirect(url_for('auth.select_save'))

    return redirect(url_for('auth.game_action', saved='true'))
    
@auth_routes.route('/create_character', methods=['GET', 'POST'])
def create_character():
    """Handle player creation with a story sequence."""
    user_id = session.get('user_id')
    save_slot = session.get('save_slot')
    if not user_id or save_slot is None:
        return redirect(url_for('auth.select_save'))

    # Load the story sequence from descriptions.json
    with open(DESCRIPTIONS_FILE, 'r', encoding='utf-8') as file:
        descriptions = json.load(file)

    story = descriptions.get('player_creation', {})

    name_step = 4
    class_step = 6
    final_step = 9
    step = int(request.args.get('step', 1))

    if step == 1:
        session.pop('player_name', None)
        session.pop('player_class', None)
        session.pop('step', 1)

    player_name = session.get('player_name', '')
    player_class = session.get('player_class','')

    if request.method == 'POST':
        # Name step
        if step == name_step:
            name = request.form.get('name', '').strip()
            if not name:
                return render_template('create_character.html', story=story, step=step, show_name_input=True, 
                                       player_name=player_name, player_class=player_class, show_class_choice=False)

            session['player_name'] = name
            return redirect(url_for('auth.create_character', step=step + 1))

        # Class step
        elif step == class_step:
            player_class = request.form.get('class', '').strip()
            if not player_class:
                return render_template('create_character.html', story=story, step=step, show_name_input=False, 
                                       show_class_choice=True, player_name=player_name, player_class=player_class)

            session['player_class'] = player_class
            return redirect(url_for('auth.create_character', step=class_step + 1))

        # Final step: create the player
        elif step == final_step:
            name = session.get('player_name')
            player_class = session.get('player_class')

            if not name or not player_class:
                return redirect(url_for('auth.create_character', step=1))  # Reset if missing

            player = Player(name=name, player_class=player_class, save_slot=save_slot)
            dungeon_response = supabase.table('dungeons').select('*').eq('user_id', user_id).eq('save_slot', save_slot).execute()
            if not dungeon_response.data:
                dungeon = Dungeon(width=10, height=10, num_rooms=5, floor_level=1)
                dungeon.generate()
            else:
                dungeon = Dungeon.load_from_db(user_id=user_id, save_slot=save_slot)

            player.player_location = dungeon.start_location[0]
            if not persist_game_state(player, dungeon, user_id, save_slot):
                return redirect(url_for('auth.select_save'))

            return redirect(url_for('game_api.load_save', save_slot=save_slot))

        elif request.form.get('continue') == 'true':
            return redirect(url_for('auth.create_character', step=step + 1))

    # Determine dynamic behavior
    show_name_input = (step == name_step)
    show_class_choice = (step == class_step)

    return render_template(
        'create_character.html',
        story=story,
        step=step,
        show_name_input=show_name_input,
        show_class_choice=show_class_choice,
        player_name=player_name,
        player_class=player_class
    )

@auth_routes.route('/inventory', methods=['GET'])
def inventory():
    """Display the player's inventory."""
    return redirect(url_for('auth.game_action'))

@auth_routes.route('/game_action', methods=['GET', 'POST'])
def game_action():
    user_id = session.get('user_id')
    save_slot = session.get('save_slot')
    if not user_id or save_slot is None:
        return redirect(url_for('auth.login_route'))

    player = Player.load_or_create_player(user_id, save_slot)
    dungeon = Dungeon.load_from_db(user_id=user_id, save_slot=save_slot)
    if not player or dungeon is None:
        return redirect(url_for('auth.select_save'))

    action = request.form.get('action')
    saved = str(request.args.get('saved', '')).lower() == 'true'

    # --- Enemy state management ---
    enemy, enemy_description = build_enemy_for_room(dungeon, player.player_location)
    if enemy:
        enemy_description = dungeon.room_enemy_descriptions.get(str(player.player_location))
        narrative = enemy_description or f"A {enemy.name} appears!"

    just_defeated_enemy = session.pop('just_defeated_enemy', False)  

    # --- Room entry or after save ---
    if not action or saved:
        if just_defeated_enemy:
            narrative = dungeon.get_room_description(player)
            actions = get_movement_actions(player, dungeon)
            return render_game(
                player, dungeon,
                narrative=narrative,
                actions=actions,
                saved=saved,
                enemy=None,
                enemy_description=None
            )
        if enemy:
            dungeon.room_enemies[str(player.player_location)] = {
                "name": enemy.name,
                "health": enemy.health,
                "max_health": enemy.max_health,
                "defense": enemy.defense,
                "skills": enemy.skills,
                "loot": enemy.loot,
            }
            narrative = enemy_description or f"A {enemy.name} appears!"
            actions = get_skill_actions(player)
        else:
            narrative = dungeon.get_room_description(player)
            actions = get_movement_actions(player, dungeon)
        if not persist_game_state(player, dungeon, user_id, save_slot):
            return redirect(url_for('auth.select_save'))
        return render_game(
            player, dungeon,
            narrative=narrative,
            actions=actions,
            saved=saved,
            enemy=enemy,
            enemy_description=enemy_description
        )

    # --- Combat actions ---
    if action and action.startswith('skill_') and enemy:
        result = handle_combat_action(player, dungeon, enemy, enemy_description, action, user_id, save_slot, saved)
        if isinstance(result, tuple):
            # Enemy not defeated, continue combat
            _, interaction = result
            narrative = interaction if interaction else (enemy_description or f"A {enemy.name} appears!")
            actions = get_skill_actions(player)
            return render_game(
                player, dungeon,
                narrative=narrative,
                actions=actions,
                saved=saved,
                enemy=enemy,
                enemy_description=enemy_description,
                interaction=interaction
            )
        else:
            # Enemy defeated, result is a render_template response
            return result

    # --- Healing action ---
    elif action == 'heal':
        interaction = handle_heal_action(player, enemy)
        if enemy:
            dungeon.room_enemies[str(player.player_location)] = {
                "name": enemy.name,
                "health": enemy.health,
                "max_health": enemy.max_health,
                "defense": enemy.defense,
                "skills": enemy.skills,
                "loot": enemy.loot,
            }
        if not persist_game_state(player, dungeon, user_id, save_slot):
            return redirect(url_for('auth.select_save'))
        narrative = interaction if interaction else (enemy_description or f"A {enemy.name} appears!")
        actions = get_skill_actions(player)
        return render_game(
            player, dungeon,
            narrative=narrative,
            actions=actions,
            saved=saved,
            enemy=enemy,
            enemy_description=enemy_description,
            interaction=interaction
        )

    # --- Movement actions ---
    elif action and action.startswith('move_'):
        direction = action.split('_')[1]
        move_result = handle_move_action(player, dungeon, direction, user_id, save_slot, saved)
        if move_result:
            return move_result
        else:
            # Invalid direction
            narrative = "Invalid direction."
            actions = get_movement_actions(player, dungeon)
            return render_game(
                player, dungeon,
                narrative=narrative,
                actions=actions,
                saved=saved
            )

    # --- Descend action ---
    elif action == 'descend_next_floor':
        return handle_descend_action(player, user_id, save_slot, saved)

    # --- Inventory action ---
    elif action == 'inventory':
        return redirect(url_for('auth.inventory'))
    
    # --- After Combat action ---
    elif action == 'continue_after_event':
        # Advance to the next state, e.g., show room description after enemy defeated
        narrative = dungeon.get_room_description(player)
        actions = get_movement_actions(player, dungeon)
        return render_game(
            player, dungeon,
            narrative=narrative,
            actions=actions,
            saved=saved,
            enemy=None,
            enemy_description=None,
        )

    # --- Final action rendering ---
    if enemy:
        narrative = enemy_description or f"A {enemy.name} appears!"
        actions = get_skill_actions(player)
    else:
        narrative = dungeon.get_room_description(player)
        actions = get_movement_actions(player, dungeon)

    if not persist_game_state(player, dungeon, user_id, save_slot):
        return redirect(url_for('auth.select_save'))

    return render_game(
        player, dungeon,
        narrative=narrative,
        actions=actions,
        saved=saved,
        enemy=enemy,
        enemy_description=enemy_description
    )
