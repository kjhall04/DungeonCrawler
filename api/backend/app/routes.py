from flask import Blueprint, request, session, redirect, render_template, url_for, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from backend.app.auth import create_account, login
from backend.app.db import supabase
from backend.game.player import Player
from backend.game.dungeon import Dungeon
from backend.game.enemy import Enemy
import json
import random as rand

auth_routes = Blueprint('auth', __name__)
limiter = Limiter(get_remote_address)

ENEMY_SPAWN_CHANCE = 0.9

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
    
    # Save the player and dungeon state
    player.save_player_data(user_id, save_slot)
    response = supabase.table('player_saves').select('id').eq('user_id', user_id).eq('save_slot', save_slot).execute()
    if not response.data:
        return redirect(url_for('auth.select_save'))  # Handle error if player save is not found
    player_save_id = response.data[0]['id']

    dungeon.save_to_db(player_save_id, user_id=user_id, save_slot=save_slot)

    return redirect(url_for('auth.game_action', saved=True))
    
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
            player.save_player_data(user_id, save_slot)
            response = supabase.table('player_saves').select('id').eq('user_id', user_id).eq('save_slot', save_slot).execute()
            if not response.data:
                return redirect(url_for('auth.select_save'))  # Handle error if player save is not found
            player_save_id = response.data[0]['id']

            # Only generate and save a new dungeon if one does not exist for this save
            dungeon_response = supabase.table('dungeons').select('*').eq('user_id', user_id).eq('save_slot', save_slot).execute()
            if not dungeon_response.data:
                dungeon = Dungeon(width=10, height=10, num_rooms=5, floor_level=1)
                dungeon.generate()
                player.player_location = dungeon.start_location[0]
                player.save_player_data(user_id, save_slot)
                dungeon.save_to_db(player_save_id, user_id=user_id, save_slot=save_slot)
            else:
                # Load the existing dungeon and set player location to start if needed
                dungeon = Dungeon.load_from_db(user_id=user_id, save_slot=save_slot)
                player.player_location = dungeon.start_location[0]
                player.save_player_data(user_id, save_slot)

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
    user_id = session.get('user_id')
    save_slot = session.get('save_slot')
    if not user_id or save_slot is None:
        return redirect(url_for('auth.login_route'))

    player = Player.load_or_create_player(user_id, save_slot)
    inventory_data = player.get_inventory()

    return render_template('game.html', inventory=inventory_data, narrative=None, interaction=None, actions=[])

@auth_routes.route('/game_action', methods=['GET', 'POST'])
def game_action():
    user_id = session.get('user_id')
    save_slot = session.get('save_slot')
    if not user_id or save_slot is None:
        return redirect(url_for('auth.login_route'))

    player = Player.load_or_create_player(user_id, save_slot)
    dungeon = Dungeon.load_from_db(user_id=user_id, save_slot=save_slot)
    if dungeon is None:
        return redirect(url_for('auth.select_save'))

    action = request.form.get('action')
    saved = request.args.get('saved', False)

    # --- Enemy state management ---
    enemy_data = session.get('enemy')
    enemy = None
    if enemy_data:
        enemy = Enemy.create_enemy(enemy_data['name'], dungeon)
        enemy.health = enemy_data['health']
        enemy.defense = enemy_data['defense']
        enemy.max_health = enemy_data['max_health']
        enemy.skills = enemy_data['skills']

    # --- Helper: get movement actions ---
    def get_movement_actions():
        all_directions = ['north', 'south', 'east', 'west']
        valid_directions = dungeon.get_valid_directions(player.player_location)
        actions = [
            {
                'label': f"Move {direction.capitalize()}",
                'value': f"move_{direction}" if direction in valid_directions else None,
                'enabled': direction in valid_directions
            }
            for direction in all_directions
        ]
        # Add descend button if at exit
        if str(player.player_location) == str(dungeon.exit_location[0]):
            actions.append({
                'label': "Descend to the Next Floor",
                'value': "descend_next_floor",
                'enabled': True,
                'is_descend': True  # Custom flag for template
            })
        return actions

    # --- Helper: get skill actions ---
    def get_skill_actions():
        return [
            {'label': f"{skill['name'].capitalize()} (Damage: {skill['damage']})", 'value': f"skill_{skill['name']}"}
            for skill in player.skills
        ] + [{'label': "Heal", 'value': "heal"}]

    # --- Room entry or after save ---
    if not action or saved:
        # Spawn enemy if not already present
        if not enemy and rand.random() < ENEMY_SPAWN_CHANCE:
            floor_key = f"floor_{dungeon.floor_level}"
            with open('api/backend/data/enemies.json', 'r') as file:
                enemies_data = json.load(file)[floor_key]
            enemy_name = rand.choice(list(enemies_data.keys()))
            enemy = Enemy.create_enemy(enemy_name, dungeon)
            session['enemy'] = {
                'name': enemy.name,
                'health': enemy.health,
                'max_health': enemy.max_health,
                'defense': enemy.defense,
                'skills': enemy.skills
            }
        elif not enemy:
            session.pop('enemy', None)

        if enemy:
            narrative = get_enemy_narration(enemy, dungeon, player)
            actions = get_skill_actions()
        else:
            narrative = dungeon.get_room_description(player)
            actions = get_movement_actions()

        return render_template(
            'game.html',
            narrative=narrative,
            interaction=None,
            actions=actions,
            health=player.health,
            max_health=player.max_health,
            inventory=player.get_inventory(),
            saved=saved,
            enemy=enemy,
            player_defense=player.defense
        )

    # --- Combat actions ---
    interaction = None
    if action and action.startswith('skill_') and enemy:
        skill_name = action[len('skill_'):]
        interaction = player.attack_enemy(enemy, skill_name)
        if enemy.health <= 0:
            interaction += f" {enemy.name} is defeated!"
            session.pop('enemy', None)
            enemy = None
        else:
            # Enemy attacks back
            enemy_attack = enemy.attack_player(player)
            interaction += f" {enemy.name} uses {enemy_attack['skill_used']} and deals {enemy_attack['damage_dealt']} damage! (Your HP: {player.health})"
            session['enemy'] = {
                'name': enemy.name,
                'health': enemy.health,
                'max_health': enemy.max_health,
                'defense': enemy.defense,
                'skills': enemy.skills
            }

    elif action == 'heal':
        if player.heal():
            interaction = "You used a health potion and restored some health."
        else:
            interaction = "You don't have any health potions left."
        # Enemy attacks after heal
        if enemy:
            enemy_attack = enemy.attack_player(player)
            interaction += f" {enemy.name} uses {enemy_attack['skill_used']} and deals {enemy_attack['damage_dealt']} damage! (Your HP: {player.health})"
            session['enemy'] = {
                'name': enemy.name,
                'health': enemy.health,
                'max_health': enemy.max_health,
                'defense': enemy.defense,
                'skills': enemy.skills
            }

    # --- Movement ---
    elif action and action.startswith('move_'):
        direction = action.split('_')[1]
        valid_directions = dungeon.get_valid_directions(player.player_location)
        if direction in valid_directions:
            if player.move(direction, dungeon):
                session.pop('enemy', None)
                # Save state immediately after movement
                player.save_player_data(user_id, save_slot)
                response = supabase.table('player_saves').select('id').eq('user_id', user_id).eq('save_slot', save_slot).execute()
                if not response.data:
                    return redirect(url_for('auth.select_save'))
                player_save_id = response.data[0]['id']
                dungeon.save_to_db(player_save_id=player_save_id, user_id=user_id, save_slot=save_slot)
                # Enemy spawn handled on next GET/POST
                narrative = dungeon.get_room_description(player)
                actions = get_movement_actions()
                return render_template(
                    'game.html',
                    narrative=narrative,
                    interaction=None,
                    actions=actions,
                    health=player.health,
                    max_health=player.max_health,
                    inventory=player.get_inventory(),
                    saved=saved,
                    enemy=None,
                    player_defense=player.defense
                )
        interaction = "Invalid direction."

    # --- Descend to next floor ---
    elif action == 'descend_next_floor':
        player.dungeon_floor += 1
        dungeon = Dungeon(width=10, height=10, num_rooms=5, floor_level=player.dungeon_floor)
        dungeon.generate()
        player.player_location = dungeon.start_location[0]
        player.save_player_data(user_id, save_slot)
        response = supabase.table('player_saves').select('id').eq('user_id', user_id).eq('save_slot', save_slot).execute()
        if not response.data:
            return redirect(url_for('auth.select_save'))
        player_save_id = response.data[0]['id']
        dungeon.save_to_db(player_save_id, user_id=user_id, save_slot=save_slot)
        actions = get_movement_actions()
        return render_template(
            'game.html',
            narrative=dungeon.room_descriptions.get(str(dungeon.start_location[0]), "You descend to the next floor."),
            interaction=None,
            actions=actions,
            health=player.health,
            max_health=player.max_health,
            inventory=player.get_inventory(),
            saved=saved,
            enemy=None,
            player_defense=player.defense
        )

    elif action == 'inventory':
        return redirect(url_for('auth.inventory'))

    # --- Final action rendering ---
    if enemy:
        narrative = interaction if interaction else get_enemy_narration(enemy, dungeon, player)
        actions = get_skill_actions()
    else:
        narrative = interaction if interaction else dungeon.get_room_description(player)
        actions = get_movement_actions()

    # Save state
    player.save_player_data(user_id, save_slot)
    response = supabase.table('player_saves').select('id').eq('user_id', user_id).eq('save_slot', save_slot).execute()
    if not response.data:
        return redirect(url_for('auth.select_save'))
    player_save_id = response.data[0]['id']
    dungeon.save_to_db(player_save_id=player_save_id, user_id=user_id, save_slot=save_slot)

    return render_template(
        'game.html',
        narrative=narrative,
        interaction=None,
        actions=actions,
        health=player.health,
        max_health=player.max_health,
        inventory=player.get_inventory(),
        saved=saved,
        enemy=enemy,
        player_defense=player.defense
    )

def get_enemy_narration(enemy, dungeon, player):
    """Load the enemy encounter narration from descriptions.json."""
    try:
        with open('api/backend/data/descriptions.json', 'r') as file:
            descriptions_data = json.load(file)
        floor_key = f"floor_{dungeon.floor_level}"
        enemy_key = enemy.name
        enemy_description = descriptions_data[floor_key]["enemies"][enemy_key]
        return rand.choice(list(enemy_description.values()))
    except Exception:
        return f"A {enemy.name} appears!"  # Fallback narration if loading fails